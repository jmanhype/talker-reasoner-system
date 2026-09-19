from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Literal, NamedTuple, Protocol

from talk_reasoner.actions import ActionCatalog, ActionProposal, ConsentRecord, ConfirmationRecord, FixtureState, PolicyDecision, PolicyDefinition, ValidatedAction, ValidationDecision, action_hash, policy_event, preflight_policy, validation_event
from talk_reasoner.contracts import EVENT_SCHEMA_VERSION, EventLedger, Fixture, LedgerEvent, append_event, scoped_hash
from talk_reasoner.routing import RoutingDecision
from talk_reasoner.transports import REQUEST_SCHEMA_VERSION, MonotonicClock, ReasonerProposal, ReasonerRequest, ReasonerTransport, TransportContractError, validate_proposal
JOB_SCHEMA_VERSION = "slice0-job-v1"
STALE_TTL_SECONDS = 30.0
JobState = Literal["pending", "running", "waiting_confirmation", "completed", "canceled", "downgraded", "failed"]
JOB_STATES = ("pending", "running", "waiting_confirmation", "completed", "canceled", "downgraded", "failed")
TERMINAL_JOB_STATES = frozenset(("completed", "canceled", "downgraded", "failed"))
LEGAL_JOB_TRANSITIONS = MappingProxyType({"pending": frozenset(("running", "failed")), "running": frozenset(("waiting_confirmation", "completed", "canceled", "downgraded", "failed")),
                                           "waiting_confirmation": frozenset(("completed", "canceled", "downgraded", "failed")), "completed": frozenset(), "canceled": frozenset(), "downgraded": frozenset(), "failed": frozenset()})
TerminalReason = Literal["completed", "proposal_invalid", "validation_failed", "policy_failed", "canceled_by_user", "turn_superseded", "stale_ttl_expired", "result_age_expired", "material_intent_changed", "unsafe_presentation", "downgraded"]
class JobRouteError(ValueError): """A non-slow route attempted to create reasoner work."""
class JobStateError(ValueError): """A requested lifecycle transition is illegal or unevaluable."""
class ActionValidator(Protocol):
    def __call__(self, proposal: ActionProposal, *, catalog: ActionCatalog, consent: ConsentRecord, state: FixtureState) -> ValidationDecision: ...
class PolicyEngine(Protocol):
    def __call__(self, action: ValidatedAction, *, policy: PolicyDefinition) -> PolicyDecision: ...
@dataclass(frozen=True, slots=True)
class JobRequest:
    schema_version: str; fixture: Fixture; decision: RoutingDecision; catalog: ActionCatalog; consent: ConsentRecord; state: FixtureState; turn_epoch: int; maximum_result_age_seconds: float; ledger: EventLedger
@dataclass(frozen=True, slots=True)
class ReasonerJobIdentity:
    schema_version: str; job_id: str; session_id: str; turn_id: str; turn_epoch: int; input_hash: str; catalog_hash: str; catalog_version: str; policy_version: str; thresholds_version: str; routing_policy_hash: str; fixture_set_version: str
@dataclass(frozen=True, slots=True)
class JobTiming:
    pending_at: float; running_at: float; stale_expires_at: float; proposal_received_at: float | None = None; result_expires_at: float | None = None; terminal_at: float | None = None
@dataclass(frozen=True, slots=True)
class ReasonerJob:
    schema_version: str; state: JobState; identity: ReasonerJobIdentity; timing: JobTiming
    proposal: ReasonerProposal | None; validated_actions: tuple[ValidatedAction, ...]; policy: PolicyDefinition
    waiting_action_hashes: frozenset[str]; confirmed_action_hashes: frozenset[str]; used_confirmation_hashes: frozenset[str]
    terminal_reason: TerminalReason | None; cancel_requested: bool; safe_summary: str | None; ledger: EventLedger
class Run(NamedTuple): pass
class Complete(NamedTuple): proposal: ReasonerProposal
class ConfirmAction(NamedTuple): confirmation: ConfirmationRecord
class Cancel(NamedTuple): pass
class TurnAdvanced(NamedTuple): turn_epoch: int
class MaterialIntentChanged(NamedTuple): intent_hash: str
class Expire(NamedTuple): kind: Literal["stale_ttl", "result_age"]
class UnsafePresentation(NamedTuple): reason: str
class Downgrade(NamedTuple): safe_summary: str
class TerminalOutcome(NamedTuple):
    state: JobState; terminal_reason: TerminalReason; turn_epoch: int; response_priority: int; response_choice: str; safe_summary: str; normal_result_allowed: bool; latency_ms: int; provenance: object; job_id: str


def legal_job_transition(current: JobState, target: JobState) -> bool:
    """Return whether the fixed async state machine permits one transition."""
    if current not in JOB_STATES or target not in JOB_STATES: raise JobStateError("unknown job state")
    return target in LEGAL_JOB_TRANSITIONS[current]


def _identity(request: JobRequest) -> ReasonerJobIdentity:
    return ReasonerJobIdentity(JOB_SCHEMA_VERSION, f"job-{request.decision.input_hash[:20]}", request.fixture.session_id,
                               request.fixture.turn_id, request.turn_epoch, request.decision.input_hash, request.catalog.catalog_hash,
                               request.catalog.catalog_version, request.catalog.policy.policy_version, request.decision.thresholds_version,
                               request.decision.policy_hash, request.fixture.provenance.fixture_set_version)


def _validate_request(request: JobRequest) -> ReasonerJobIdentity:
    if request.schema_version != REQUEST_SCHEMA_VERSION or request.decision.route != "needs_tools": raise JobRouteError("only needs_tools may start a reasoner job")
    identity = _identity(request); expected_hash = scoped_hash(request.fixture.transcript, scope="fixture-input", schema_version=request.fixture.schema_version)
    if request.decision.input_hash != expected_hash or request.fixture.session_id != request.state.session_id: raise JobRouteError("route, fixture, and state identities do not align")
    now = datetime.now(timezone.utc)
    active_consent = (request.consent.granted_at.tzinfo is not None and request.consent.expires_at.tzinfo is not None
                      and request.consent.granted_at <= now < request.consent.expires_at
                      and request.consent.session_id == request.fixture.session_id
                      and request.consent.policy_version == request.catalog.policy.policy_version)
    if not request.fixture.consent.reasoner or not active_consent or request.turn_epoch < 0: raise JobRouteError("reasoner consent or turn epoch is invalid")
    if request.maximum_result_age_seconds <= 0: raise JobStateError("maximum result age must be positive")
    return identity


def _event(ledger: EventLedger, identity: ReasonerJobIdentity, event_type: str, status: str, at: float,
           pending_at: float, input_hash: str, *, content: bytes = b"", action_hash: str | None = None,
           reason: str | None = None) -> tuple[EventLedger, LedgerEvent]:
    tail = ledger.events[-1] if ledger.events else None
    event = LedgerEvent(EVENT_SCHEMA_VERSION, event_type, "1.0.0", ledger.event_count + 1, identity.session_id,
                        identity.turn_id, identity.turn_epoch, input_hash, len(content), "application/json", "consent-v1",
                        identity.policy_version, status, reason, max(0, round((at - pending_at) * 1000)), action_hash,
                        None if tail is None else tail.event_id, None if tail is None else tail.event_chain_hash, None, identity.job_id)
    receipt = append_event(ledger, event); return receipt.ledger, receipt.event


def _job(request: JobRequest, identity: ReasonerJobIdentity, timing: JobTiming, ledger: EventLedger, **changes: object) -> ReasonerJob:
    base = ReasonerJob(JOB_SCHEMA_VERSION, "running", identity, timing, None, (), request.catalog.policy, frozenset(), frozenset(), frozenset(), None, False, None, ledger)
    return replace(base, **changes) if changes else base


def _terminal(job: ReasonerJob, state: JobState, reason: TerminalReason, clock: MonotonicClock,
              *, action_hash: str | None = None, summary: str | None = None, cancel: bool = False) -> ReasonerJob:
    if not legal_job_transition(job.state, state): raise JobStateError(f"illegal transition {job.state} -> {state}")
    at = clock.now()
    digest = job.identity.input_hash if state != "completed" else scoped_hash(json.dumps({"job_id": job.identity.job_id, "state": state, "reason": reason}, sort_keys=True, separators=(",", ":")), scope="terminal-output", schema_version=JOB_SCHEMA_VERSION)
    action_hash = action_hash or (job.validated_actions[-1].action_hash if job.validated_actions else None)
    ledger, _ = _event(job.ledger, job.identity, "lifecycle", state, at, job.timing.pending_at, digest, content=summary.encode("utf-8") if summary else b"", action_hash=action_hash, reason=reason)
    return replace(job, state=state, terminal_reason=reason, cancel_requested=job.cancel_requested or cancel, safe_summary=summary, timing=replace(job.timing, terminal_at=at), ledger=ledger)


async def start_reasoner_job(request: JobRequest, *, transport: ReasonerTransport, validator: ActionValidator,
                             policy: PolicyEngine, clock: MonotonicClock) -> ReasonerJob:
    """Run one validated offline proposal without blocking the event loop."""
    identity = _validate_request(request); started = clock.now(); timing = JobTiming(started, started, started + STALE_TTL_SECONDS)
    ledger, _ = _event(request.ledger, identity, "job", "pending", started, started, identity.input_hash)
    ledger, _ = _event(ledger, identity, "job", "running", started, started, identity.input_hash)
    job = _job(request, identity, timing, ledger)
    wire = ReasonerRequest(REQUEST_SCHEMA_VERSION, identity.job_id, identity.session_id, identity.turn_id, identity.turn_epoch, identity.input_hash, identity.catalog_hash, identity.policy_version)
    try:
        proposal = await transport.propose(wire); validate_proposal(proposal, wire, request.catalog)
    except (TransportContractError, ValueError, TypeError):
        return _terminal(job, "failed", "proposal_invalid", clock)
    received = clock.now(); timing = replace(timing, proposal_received_at=received, result_expires_at=received + request.maximum_result_age_seconds)
    job = _job(request, identity, timing, ledger, proposal=proposal)
    ledger, _ = _event(ledger, identity, "proposal", "validated", received, started, proposal.input_hash, content=proposal.candidate_answer.encode("utf-8"))
    accepted: list[ValidatedAction] = []; waiting: set[str] = set()
    try:
        for item in proposal.actions:
            validation = validator(item, catalog=request.catalog, consent=request.consent, state=request.state)
            receipt = append_event(ledger, validation_event(validation, event_id=ledger.event_count + 1,
                                   prior_event_id=ledger.events[-1].event_id, prior_event_hash=ledger.head_hash))
            ledger = receipt.ledger
            if validation.accepted is None:
                intermediate = _job(request, identity, timing, ledger, proposal=proposal)
                return _terminal(intermediate, "failed", "validation_failed", clock, action_hash=action_hash(item.arguments, catalog_version=item.catalog_version))
            accepted.append(validation.accepted)
            decision = policy(validation.accepted, policy=request.catalog.policy)
            ledger = append_event(ledger, policy_event(decision, validation.accepted, event_id=ledger.event_count + 1,
                                  prior_event_id=ledger.events[-1].event_id, prior_event_hash=ledger.head_hash)).ledger
            if decision.outcome == "rejected":
                intermediate = _job(request, identity, timing, ledger, proposal=proposal, validated_actions=tuple(accepted))
                return _terminal(intermediate, "failed", "policy_failed", clock, action_hash=validation.accepted.action_hash)
            if decision.outcome == "confirmation_required": waiting.add(validation.accepted.action_hash)
    except (ValueError, TypeError) as error:
        raise JobStateError(f"validator or policy failed closed: {error}") from error
    job = _job(request, identity, timing, ledger, proposal=proposal, validated_actions=tuple(accepted), waiting_action_hashes=frozenset(waiting))
    if waiting:
        ledger, _ = _event(ledger, identity, "lifecycle", "waiting_confirmation", received, started, proposal.input_hash, action_hash=next(iter(waiting)))
        return replace(job, state="waiting_confirmation", ledger=ledger)
    return _terminal(job, "completed", "completed", clock, summary="A validated local proposal is ready.")


def _confirmation_digest(confirmation: object) -> str:
    values = {key: value.isoformat() if isinstance(value, datetime) else value for key, value in confirmation._asdict().items()}
    return scoped_hash(json.dumps(values, sort_keys=True, separators=(",", ":"), default=str), scope="action-confirmation", schema_version=JOB_SCHEMA_VERSION)


def advance_reasoner_job(job: ReasonerJob, stimulus: object, *, clock: MonotonicClock) -> ReasonerJob:
    """Apply exactly one legal lifecycle stimulus and never replace a terminal job."""
    if job.schema_version != JOB_SCHEMA_VERSION or job.state not in JOB_STATES: raise JobStateError("unknown job contract")
    if job.state in TERMINAL_JOB_STATES: return job
    now = clock.now()
    if now < job.timing.pending_at:
        raise JobStateError("monotonic clock moved backwards")
    if now >= job.timing.stale_expires_at: return _terminal(job, "canceled", "stale_ttl_expired", clock, cancel=True)
    if job.timing.result_expires_at is not None and now >= job.timing.result_expires_at: return _terminal(job, "canceled", "result_age_expired", clock, cancel=True)
    if isinstance(stimulus, Run): return _running(job, clock)
    if isinstance(stimulus, Complete): return _terminal(replace(job, proposal=stimulus.proposal), "completed", "completed", clock, summary="A validated local proposal is ready.")
    if isinstance(stimulus, Cancel): return _terminal(job, "canceled", "canceled_by_user", clock, cancel=True)
    if isinstance(stimulus, TurnAdvanced):
        if stimulus.turn_epoch <= job.identity.turn_epoch: raise JobStateError("turn epoch did not advance")
        return _terminal(job, "canceled", "turn_superseded", clock, cancel=True)
    if isinstance(stimulus, MaterialIntentChanged):
        if len(stimulus.intent_hash) != 64 or any(character not in "0123456789abcdef" for character in stimulus.intent_hash): raise JobStateError("material intent hash is invalid")
        return _terminal(job, "canceled", "material_intent_changed", clock, cancel=True)
    if isinstance(stimulus, Expire):
        reason: TerminalReason = "stale_ttl_expired" if stimulus.kind == "stale_ttl" else "result_age_expired"
        return _terminal(job, "canceled", reason, clock, cancel=True)
    if isinstance(stimulus, UnsafePresentation): return _presentation_downgrade(job, clock, stimulus.reason, "unsafe_presentation")
    if isinstance(stimulus, Downgrade): return _presentation_downgrade(job, clock, stimulus.safe_summary, "downgraded")
    if isinstance(stimulus, ConfirmAction): return _confirm(job, stimulus.confirmation, clock)
    raise JobStateError("unsupported job stimulus")


def _running(job: ReasonerJob, clock: MonotonicClock) -> ReasonerJob:
    if not legal_job_transition(job.state, "running"): raise JobStateError(f"illegal transition {job.state} -> running")
    at = clock.now(); ledger, _ = _event(job.ledger, job.identity, "job", "running", at, job.timing.pending_at, job.identity.input_hash)
    return replace(job, state="running", timing=replace(job.timing, running_at=at), ledger=ledger)


def _presentation_downgrade(job: ReasonerJob, clock: MonotonicClock, summary: str, reason: TerminalReason) -> ReasonerJob:
    if not 8 <= len(summary) <= 160: raise JobStateError("downgrade summary must be bounded")
    return _terminal(job, "downgraded", reason, clock, summary=summary)


def _confirm(job: ReasonerJob, confirmation: object, clock: MonotonicClock) -> ReasonerJob:
    if job.state != "waiting_confirmation": raise JobStateError(f"illegal transition {job.state} -> completed")
    digest = _confirmation_digest(confirmation)
    if digest in job.used_confirmation_hashes: return _terminal(job, "failed", "policy_failed", clock)
    action_hash = getattr(confirmation, "action_hash", "")
    matches = [item for item in job.validated_actions if item.action_hash == action_hash]
    if not matches or action_hash not in job.waiting_action_hashes: return _terminal(job, "failed", "policy_failed", clock)
    decision = preflight_policy(matches[0], policy=job.policy, confirmation=confirmation)
    if decision.outcome == "rejected": return _terminal(job, "failed", "policy_failed", clock, action_hash=action_hash)
    ledger, _ = _event(job.ledger, job.identity, "confirmation", "allowed_without_confirmation", clock.now(), job.timing.pending_at, job.identity.input_hash, action_hash=action_hash)
    confirmed = job.confirmed_action_hashes | {action_hash}; waiting = job.waiting_action_hashes - {action_hash}
    updated = replace(job, waiting_action_hashes=waiting, confirmed_action_hashes=confirmed, used_confirmation_hashes=job.used_confirmation_hashes | {digest}, ledger=ledger)
    if waiting: return updated
    return _terminal(updated, "completed", "completed", clock, action_hash=action_hash, summary="The confirmed local proposal is ready; no tool was executed.")


def job_terminal_summary(job: ReasonerJob) -> TerminalOutcome:
    """Return only a safe terminal presentation contract for a finished job."""
    if job.state not in TERMINAL_JOB_STATES or job.terminal_reason is None: raise JobStateError("terminal summary requires a terminal job")
    choices = {"completed": "validated_non_action_summary", "canceled": "silent", "downgraded": "bounded_non_action_summary", "failed": "safe_recovery_choice"}
    summaries = {"completed": job.safe_summary or "A validated local response is ready.", "canceled": "Canceled work will not interrupt.",
                 "downgraded": job.safe_summary or "Slow work was set aside; it can be resumed later.", "failed": "Slow work could not complete safely; retry or rephrase."}
    priorities = {"completed": 2, "canceled": 0, "downgraded": 1, "failed": 1}
    terminal_at = job.timing.terminal_at or job.timing.proposal_received_at or job.timing.pending_at
    return TerminalOutcome(job.state, job.terminal_reason, job.identity.turn_epoch, priorities[job.state], choices[job.state],
                           summaries[job.state], job.state == "completed", max(0, round((terminal_at - job.timing.pending_at) * 1000)),
                           None if job.proposal is None else job.proposal.provenance, job.identity.job_id)
