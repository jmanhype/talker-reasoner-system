from __future__ import annotations

import asyncio
import re
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from talk_reasoner.actions import ActionProposal, ActionProvenance, CATALOG_PATH, ConsentRecord, ConfirmationRecord, FixtureState, action_hash, load_action_catalog, preflight_policy, validate_action
from talk_reasoner.contracts import EventLedger, canonical_event_bytes, load_fixture, scoped_hash, verify_ledger
from talk_reasoner.jobs import JOB_STATES, LEGAL_JOB_TRANSITIONS, Cancel, ConfirmAction, Complete, Downgrade, Expire, JobRouteError, JobStateError, JobRequest, MaterialIntentChanged, Run, TurnAdvanced, UnsafePresentation, advance_reasoner_job, job_terminal_summary, legal_job_transition, start_reasoner_job
from talk_reasoner.routing import load_threshold_policy, classify
from talk_reasoner.transports import LocalScriptedTransport, NoAction, ReasonerProposal, ReasonerProvenance

FIXTURE = load_fixture(Path(__file__).parent / "fixtures" / "slice0" / "trs-tools-001.json")
CATALOG = load_action_catalog(CATALOG_PATH)
DECISION = classify(FIXTURE, policy=load_threshold_policy(Path(__file__).parents[1] / "config" / "routing" / "slice0-v1.json"))
JOB_ID = f"job-{DECISION.input_hash[:20]}"
NOW = datetime.now(timezone.utc).replace(microsecond=0)


class ManualClock:
    def __init__(self) -> None: self.current = 0.0; self.waiting = asyncio.Event(); self.release = asyncio.Event()
    def now(self) -> float: return self.current

    async def wait(self, seconds: float) -> None: self.waiting.set(); await self.release.wait(); self.current += seconds


def provenance() -> ReasonerProvenance: return ReasonerProvenance("slice0-reasoner-provenance-v1", "slice0-2026-09-19", "local-scripted-transport", "slice0-local-v1", "reviewed")


def action(job_id: str = JOB_ID, **changes: Any) -> ActionProposal:
    base = ActionProposal("slice0-proposal-v1", "write_state", {"key": "preferences", "value": "afternoon meetings", "terms": ["meeting"]},
                          job_id, FIXTURE.session_id, FIXTURE.turn_id, 0, "fixture-user", "fixture-user", "fixture://slice0",
                          "The user asked to save an afternoon preference.", ActionProvenance("slice0-provenance-v1", "slice0-2026-09-19", "synthetic-local", "reviewed", DECISION.input_hash),
                          CATALOG.catalog_version, CATALOG.policy.policy_version)
    return base._replace(**changes) if changes else base


def script(job_id: str = JOB_ID, *, actions: tuple[ActionProposal, ...] = (), no_action: NoAction | None = None,
           refusal: str | None = None, **changes: Any) -> ReasonerProposal:
    marker = no_action if no_action is not None else None if actions else NoAction("No action is required." if refusal else "The request can be answered directly.")
    base = ReasonerProposal("slice0-reasoner-proposal-v1", job_id, FIXTURE.session_id, FIXTURE.turn_id, 0,
                            "Your afternoon preference can be saved after confirmation.", actions, marker, {}, 0.94, 0.05,
                            DECISION.input_hash, CATALOG.catalog_hash, CATALOG.policy.policy_version, provenance(), refusal)
    return replace(base, **changes) if changes else base


def consent() -> ConsentRecord: return ConsentRecord("consent-v1", "fixture-user", FIXTURE.session_id, "fixture-user", frozenset({"local.read", "local.write"}), NOW - timedelta(seconds=5), NOW + timedelta(minutes=5), CATALOG.policy.policy_version)


def state() -> FixtureState: return FixtureState("state-v1", FIXTURE.session_id, 1, NOW + timedelta(minutes=5), dict(FIXTURE.bounded_context.state), frozenset())


def request(ledger: EventLedger = EventLedger.empty()) -> JobRequest: return JobRequest("slice0-job-request-v1", FIXTURE, DECISION, CATALOG, consent(), state(), 0, 30, ledger)


def confirmation(arguments: dict[str, Any], **changes: Any) -> ConfirmationRecord:
    digest = action_hash(arguments, catalog_version=CATALOG.catalog_version)
    base = ConfirmationRecord("confirmation-v1", True, "write_state", digest, arguments, "fixture-user", "fixture://slice0",
                              "fixture-user", FIXTURE.session_id, CATALOG.policy.policy_version, NOW, NOW + timedelta(seconds=30))
    return replace(base, **changes) if changes else base


def waiting_job() -> Any: return asyncio.run(start_reasoner_job(request(), transport=LocalScriptedTransport(script(actions=(action(),)), 0, TransportClock()), validator=validate_action, policy=preflight_policy, clock=TransportClock()))


class TransportClock:
    def __init__(self) -> None: self.current = 0.0
    def now(self) -> float: return self.current

    async def wait(self, seconds: float) -> None: self.current += seconds; await asyncio.sleep(0)


def test_only_needs_tools_can_start_and_transport_stays_asleep() -> None:
    transport = LocalScriptedTransport(script(), delay_seconds=0, clock=TransportClock())
    for fixture_name in ("trs-chitchat-001.json", "trs-unclear-001.json"):
        fixture = load_fixture(Path(__file__).parent / "fixtures" / "slice0" / fixture_name)
        decision = classify(fixture, policy=load_threshold_policy(Path(__file__).parents[1] / "config" / "routing" / "slice0-v1.json"))
        bad = JobRequest("slice0-job-request-v1", fixture, decision, CATALOG, consent(), state(), 0, 30, EventLedger.empty())
        with pytest.raises(JobRouteError, match="only needs_tools"):
            asyncio.run(start_reasoner_job(bad, transport=transport, validator=validate_action, policy=preflight_policy, clock=TransportClock()))
    assert transport.call_count == 0


def test_start_yields_to_fast_loop_and_waits_for_confirmation() -> None:
    async def run() -> Any:
        clock = ManualClock(); transport = LocalScriptedTransport(script(actions=(action(),)), delay_seconds=0.05, clock=clock)
        started = asyncio.create_task(start_reasoner_job(request(), transport=transport, validator=validate_action,
                                                         policy=preflight_policy, clock=clock))
        await asyncio.sleep(0); await asyncio.wait_for(clock.waiting.wait(), 1); progressed = False

        async def fast_loop() -> None:
            nonlocal progressed; await asyncio.sleep(0); progressed = True

        await asyncio.create_task(fast_loop()); assert progressed and not started.done(); clock.release.set(); return await started

    job = asyncio.run(run()); assert job.state == "waiting_confirmation" and job.identity.job_id == JOB_ID
    assert [event.event_type for event in job.ledger.events] == ["job", "job", "proposal", "validation", "policy", "lifecycle"]
    assert [event.status for event in job.ledger.events] == ["pending", "running", "validated", "validated", "confirmation_required", "waiting_confirmation"]
    exact = confirmation({"key": "preferences", "value": "afternoon meetings", "terms": ["meeting"]})
    finished = advance_reasoner_job(job, ConfirmAction(exact), clock=TransportClock())
    assert finished.state == "completed" and finished.confirmed_action_hashes == frozenset({exact.action_hash})
    assert advance_reasoner_job(finished, ConfirmAction(exact), clock=TransportClock()) == finished


def test_no_action_completes_without_policy_or_action_authority() -> None:
    job = asyncio.run(start_reasoner_job(request(), transport=LocalScriptedTransport(script(no_action=NoAction("Already known.")), 0, TransportClock()),
                                         validator=validate_action, policy=preflight_policy, clock=TransportClock()))
    assert job.state == "completed" and job.proposal.actions == ()
    assert [event.event_type for event in job.ledger.events] == ["job", "job", "proposal", "lifecycle"]
    summary = job_terminal_summary(job); assert summary.response_choice == "validated_non_action_summary" and summary.normal_result_allowed
    assert summary.latency_ms == 0 and summary.provenance.source == "local-scripted-transport"


def test_validation_and_confirmation_policy_failures_are_terminal() -> None:
    invalid = asyncio.run(start_reasoner_job(request(), transport=LocalScriptedTransport(script(actions=(action(arguments={"key": "passwords", "value": "x", "terms": []}),)), 0, TransportClock()),
                                             validator=validate_action, policy=preflight_policy, clock=TransportClock()))
    assert invalid.state == "failed" and invalid.terminal_reason == "validation_failed"
    job = waiting_job(); changed = confirmation({"key": "preferences", "value": "morning meetings", "terms": ["meeting"]})
    rejected = advance_reasoner_job(job, ConfirmAction(changed), clock=TransportClock())
    assert rejected.state == "failed" and rejected.terminal_reason == "policy_failed"
    assert all(verify_ledger(item.ledger).valid_chain for item in (invalid, rejected))


@pytest.mark.parametrize(("state", "target", "expected"), [(current, target, target in allowed) for current, allowed in LEGAL_JOB_TRANSITIONS.items() for target in JOB_STATES])
def test_complete_legal_transition_matrix(state: str, target: str, expected: bool) -> None:
    assert legal_job_transition(state, target) is expected


def test_pending_can_run_or_fail_and_late_results_cannot_replace_terminal() -> None:
    job = waiting_job(); base = replace(job, state="pending", proposal=None, validated_actions=(), terminal_reason=None)
    running = advance_reasoner_job(base, Run(), clock=TransportClock())
    assert running.state == "running" and advance_reasoner_job(running, Complete(script()), clock=TransportClock()).state == "completed"
    with pytest.raises(JobStateError, match="illegal transition"):
        advance_reasoner_job(base, Downgrade("Resume later"), clock=TransportClock())
    canceled = advance_reasoner_job(job, Cancel(), clock=TransportClock())
    assert canceled.state == "canceled" and advance_reasoner_job(canceled, Complete(script()), clock=TransportClock()) == canceled
    summary = job_terminal_summary(canceled); assert summary.normal_result_allowed is False and summary.response_choice == "silent"


def test_interruption_expiry_and_downgrade_paths() -> None:
    job = waiting_job(); cases = ((TurnAdvanced(1), "canceled", "turn_superseded"), (MaterialIntentChanged("1" * 64), "canceled", "material_intent_changed"),
                                  (Expire("stale_ttl"), "canceled", "stale_ttl_expired"), (Expire("result_age"), "canceled", "result_age_expired"),
                                  (UnsafePresentation("renderer conflict"), "downgraded", "unsafe_presentation"), (Downgrade("Offer to resume the preference update."), "downgraded", "downgraded"))
    outcomes = [advance_reasoner_job(job, stimulus, clock=TransportClock()) for stimulus, _, _ in cases]
    assert [item.state for item in outcomes] == [expected for _, expected, _ in cases]
    assert [item.terminal_reason for item in outcomes] == [reason for _, _, reason in cases]
    assert all(not job_terminal_summary(item).normal_result_allowed or item.state == "downgraded" for item in outcomes)
    aged = replace(job, timing=replace(job.timing, result_expires_at=job.timing.result_expires_at - 31))
    assert advance_reasoner_job(aged, Expire("result_age"), clock=TransportClock()).terminal_reason == "result_age_expired"


def test_thirty_second_ttl_is_injectable_and_monotonic() -> None:
    job = waiting_job()
    assert job.timing.pending_at == 0.0 and job.timing.stale_expires_at == 30.0
    assert job.timing.result_expires_at == 30.0
    class FixedClock:
        def now(self) -> float: return 30.0
    expired = advance_reasoner_job(job, Cancel(), clock=FixedClock())
    assert expired.state == "canceled" and expired.terminal_reason == "stale_ttl_expired"
    with pytest.raises(FrozenInstanceError):
        job.identity.job_id = "changed"


def test_ledger_is_hash_scoped_private_and_versioned() -> None:
    job = waiting_job(); ledger = job.ledger; report = verify_ledger(ledger)
    assert report.valid_chain and ledger.event_count == 6 and [event.event_id for event in ledger.events] == list(range(1, 7))
    assert all(event.job_id == JOB_ID and event.turn_epoch == 0 and event.prior_event_id == expected for event, expected in zip(ledger.events, [None, *range(1, 6)], strict=True))
    assert all(re.fullmatch(r"[0-9a-f]{64}", event.input_hash) for event in ledger.events)
    assert ledger.events[-1].action_hash == job.validated_actions[0].action_hash
    payload = b"".join(canonical_event_bytes(event) for event in ledger.events)
    assert FIXTURE.transcript.encode() not in payload and job.proposal.candidate_answer.encode() not in payload
    assert b"afternoon meetings" not in payload and b'"candidate_answer"' not in payload and b'"arguments"' not in payload


def test_reasoner_boundary_is_offline_and_has_no_platform_imports() -> None:
    root = Path(__file__).parents[1] / "src" / "talk_reasoner"
    forbidden = ("requests", "httpx", "aiohttp", "socket", "redis", "psycopg", "subprocess", "letta", "mem0")
    assert not [(path.name, name) for path in (root / "transports.py", root / "jobs.py") for name in forbidden
                if re.search(rf"(?m)^\s*(import|from)\s+{name}\b", path.read_text(encoding="utf-8"))]
    assert scoped_hash("same", scope="job-input", schema_version="test") != scoped_hash("same", scope="proposal-input", schema_version="test")
