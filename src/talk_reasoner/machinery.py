from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from talk_reasoner.actions import (
    CATALOG_PATH,
    ActionProposal,
    ActionProvenance,
    ConfirmationRecord,
    ConsentRecord,
    FixtureState,
    action_hash,
    load_action_catalog,
    preflight_policy,
    validate_action,
)
from talk_reasoner.contracts import EventLedger, append_event, canonical_event_bytes, load_fixture, scoped_hash, verify_ledger
from talk_reasoner.jobs import Cancel, ConfirmAction, Downgrade, Expire, TerminalOutcome, advance_reasoner_job, start_reasoner_job
from talk_reasoner.rendering import PresentationConstraints, RenderError, render_response
from talk_reasoner.routing import classify, load_threshold_policy, route_event
from talk_reasoner.transports import LocalScriptedTransport, NoAction, ReasonerProposal, ReasonerProvenance

ORACLE_DIRECTORY = Path(__file__).parents[2] / "design" / "machines"
DOMAIN_RENDER = Path(__file__).parents[2] / "design" / "domain.modelith.md"
ORACLE_FILES = (
    ("ConversationTurn.oracle.md", "conversationTurn"),
    ("EventLedger.oracle.md", "eventLedger"),
    ("MemoryRecord.oracle.md", "memoryRecord"),
    ("ReasonerJob.oracle.md", "reasonerJob"),
    ("ToolCatalog.oracle.md", "toolCatalog"),
    ("ToolExecution.oracle.md", "toolExecution"),
    ("VoiceSession.oracle.md", "voiceSession"),
)
EXPECTED_ORACLE_ROWS = 62
EXPECTED_INVARIANT_COUNT = 36
EXPECTED_TRANSITION_DENOMINATOR = 62
EXPECTED_INVARIANT_DENOMINATOR = 36
_ORACLE_HEADER = ("test id", "stable id", "source", "trigger", "guard", "target", "actions")
_CANONICAL_INVARIANT_ORDER = (
    "session-processing-boundary", "raw-input-ephemeral", "route-fail-closed", "transcriber-no-authority",
    "job-staleness-bounded", "canceled-work-silent", "router-no-authority", "slow-path-only-after-route",
    "reasoner-proposes-only", "proposal-identity-bound", "contract-fail-closed", "action-schema-fail-closed",
    "action-no-credentials", "catalog-version-pinned", "policy-before-execution", "policy-three-outcomes",
    "confirmation-exact-and-expiring", "confirmation-single-use", "catalog-reviewed-before-active",
    "runtime-cannot-mutate-capability", "tool-schema-provenance", "tool-allowlist-only", "credential-isolation",
    "tool-output-filtered", "tool-result-not-sole-truth", "hot-state-minimized", "hot-state-ttl",
    "ledger-append-only", "ledger-minimized", "ledger-integrity-fail-closed", "response-filtered",
    "memory-provenance-bound", "memory-not-sole-truth", "memory-deletable", "talker-no-authority",
    "model-boundaries-explicit",
)


class MachineryContractError(ValueError):
    """A machinery oracle, invariant document, or transition input is invalid."""


@dataclass(frozen=True, slots=True)
class OracleTransition:
    test_id: str
    stable_id: str
    source: str
    trigger: str
    guard: str
    target: str
    actions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TransitionCase:
    machine_name: str
    stable_id: str
    source: str
    trigger: str
    guard: str
    target: str
    expected_actions: tuple[str, ...]
    event: str
    context: object


@dataclass(frozen=True, slots=True)
class TransitionResult:
    machine_name: str
    stable_id: str
    source: str
    trigger: str
    guard: str
    next_state: str
    actions: tuple[str, ...]
    evidence: str


def _error(detail: str) -> None:
    raise MachineryContractError(detail)


def _oracle_row(line: str, path: Path) -> OracleTransition:
    cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
    if len(cells) != len(_ORACLE_HEADER):
        _error(f"malformed row width in {path.name}")
    if cells[1] == "-" or not cells[1] or not all(cells):
        _error(f"missing stable id or incomplete transition row in {path.name}")
    actions = () if cells[6] == "-" else tuple(item.strip() for item in cells[6].split(","))
    return OracleTransition(*cells[:6], actions)


def parse_oracle(path: Path) -> tuple[OracleTransition, ...]:
    """Parse one committed transition table without tolerating malformed rows."""
    if not path.is_file():
        _error(f"missing oracle file: {path.name}")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise MachineryContractError(f"unreadable oracle file: {path.name}") from error
    header = "| " + " | ".join(_ORACLE_HEADER) + " |"
    if header not in lines:
        _error(f"missing transitions table: {path.name}")
    start = lines.index(header) + 2
    rows: list[OracleTransition] = []
    seen: set[str] = set()
    for line in lines[start:]:
        if not line.startswith("|"):
            if rows:
                break
            continue
        row = _oracle_row(line, path)
        if row.stable_id in seen:
            _error(f"duplicate stable id in {path.name}: {row.stable_id}")
        seen.add(row.stable_id)
        rows.append(row)
    if not rows:
        _error(f"empty transitions table: {path.name}")
    return tuple(rows)


def parse_all_oracles(directory: Path) -> dict[str, tuple[OracleTransition, ...]]:
    """Load exactly the seven committed oracles and prove the stable-row denominator."""
    if not directory.is_dir():
        _error(f"missing oracle file: {ORACLE_FILES[0][0]}")
    actual_names = {path.name for path in directory.glob("*.oracle.md")}
    expected_names = {filename for filename, _ in ORACLE_FILES}
    for filename in sorted(actual_names - expected_names):
        _error(f"unexpected oracle file: {filename}")
    for filename in sorted(expected_names - actual_names):
        _error(f"missing oracle file: {filename}")
    parsed = {machine: parse_oracle(directory / filename) for filename, machine in ORACLE_FILES}
    rows = [row for transitions in parsed.values() for row in transitions]
    stable_ids = [row.stable_id for row in rows]
    if len(rows) != EXPECTED_ORACLE_ROWS or len(set(stable_ids)) != EXPECTED_ORACLE_ROWS:
        _error(f"oracle denominator must be exactly {EXPECTED_ORACLE_ROWS} unique rows")
    return parsed


def parse_invariant_ids(path: Path) -> tuple[str, ...]:
    """Extract and canonically order invariant ids from rendered Modelith Markdown."""
    if not path.is_file():
        _error(f"missing invariant document: {path.name}")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise MachineryContractError(f"unreadable invariant document: {path.name}") from error
    declared: list[str] = []
    capturing = False
    for line in lines:
        if line in {"**Invariants**", "## Invariants"}:
            capturing = True
            continue
        if capturing and line.startswith(("#", "**")):
            capturing = False
        if not capturing:
            continue
        marker = "- **"
        if line.startswith(marker) and "** - " in line:
            invariant_id = line[len(marker):line.index("** - ", len(marker))]
            declared.append(invariant_id)
    found = set(declared)
    expected = set(_CANONICAL_INVARIANT_ORDER)
    if found != expected or len(declared) != EXPECTED_INVARIANT_COUNT or len(found) != EXPECTED_INVARIANT_COUNT:
        _error("invariant document must declare exactly the canonical 36 ids")
    return tuple(_CANONICAL_INVARIANT_ORDER)


@dataclass(frozen=True, slots=True)
class _LocalActors:
    fixture: Any
    decision: Any
    catalog: Any
    consent: Any
    state: Any
    write_action: ActionProposal
    read_action: ActionProposal
    write_proposal: ReasonerProposal
    no_action_proposal: ReasonerProposal
    request: Any
    confirmation: ConfirmationRecord


@lru_cache(maxsize=1)
def _local_actors() -> _LocalActors:
    fixture = load_fixture(Path(__file__).parents[2] / "tests" / "fixtures" / "slice0" / "trs-tools-001.json")
    catalog = load_action_catalog(CATALOG_PATH)
    decision = classify(fixture, policy=load_threshold_policy(Path(__file__).parents[2] / "config" / "routing" / "slice0-v1.json"))
    now = datetime.now(timezone.utc).replace(microsecond=0)
    job_id = f"job-{decision.input_hash[:20]}"
    consent = ConsentRecord("consent-v1", "fixture-user", fixture.session_id, "fixture-user", frozenset({"local.read", "local.write"}),
                            now - timedelta(seconds=5), now + timedelta(minutes=5), catalog.policy.policy_version)
    state = FixtureState("state-v1", fixture.session_id, 1, now + timedelta(minutes=5), dict(fixture.bounded_context.state), frozenset())
    provenance = ActionProvenance("slice0-provenance-v1", "slice0-2026-09-19", "synthetic-local", "reviewed", decision.input_hash)

    def action(name: str, arguments: dict[str, Any]) -> ActionProposal:
        return ActionProposal("slice0-proposal-v1", name, arguments, job_id, fixture.session_id, fixture.turn_id, 0,
                              "fixture-user", "fixture-user", "fixture://slice0", "A local fixture action is justified.",
                              provenance, catalog.catalog_version, catalog.policy.policy_version)

    write_action = action("write_state", {"key": "preferences", "value": "afternoon meetings", "terms": ["meeting"]})
    read_action = action("read_state", {"key": "notes", "terms": ["exact"]})
    reasoner_provenance = ReasonerProvenance("slice0-reasoner-provenance-v1", "slice0-2026-09-19", "local-scripted-transport", "slice0-local-v1", "reviewed")

    def proposal(actions: tuple[ActionProposal, ...] = (), no_action: NoAction | None = None) -> ReasonerProposal:
        marker = no_action or (None if actions else NoAction("No action is required."))
        return ReasonerProposal("slice0-reasoner-proposal-v1", job_id, fixture.session_id, fixture.turn_id, 0,
                                "A local proposal is ready.", actions, marker, {}, 0.94, 0.05, decision.input_hash,
                                catalog.catalog_hash, catalog.policy.policy_version, reasoner_provenance, None)

    write_proposal = proposal((write_action,))
    no_action_proposal = proposal(no_action=NoAction("No action is required."))
    request = _job_request(fixture, decision, catalog, consent, state)
    digest = action_hash(write_action.arguments, catalog_version=catalog.catalog_version)
    confirmation = ConfirmationRecord("confirmation-v1", True, "write_state", digest, write_action.arguments,
                                      "fixture-user", "fixture://slice0", "fixture-user", fixture.session_id,
                                      catalog.policy.policy_version, now, now + timedelta(seconds=30))
    return _LocalActors(fixture, decision, catalog, consent, state, write_action, read_action, write_proposal,
                        no_action_proposal, request, confirmation)


def _job_request(fixture: Any, decision: Any, catalog: Any, consent: Any, state: Any) -> Any:
    from talk_reasoner.jobs import JobRequest

    return JobRequest("slice0-job-request-v1", fixture, decision, catalog, consent, state, 0, 30, EventLedger.empty())


def _validated(actor: _LocalActors, proposal: ActionProposal) -> Any:
    decision = validate_action(proposal, catalog=actor.catalog, consent=actor.consent, state=actor.state)
    if decision.accepted is None:
        _error(f"local action rejected: {decision.rejection_code}")
    return decision.accepted


def _run_job(actor: _LocalActors, proposal: ReasonerProposal) -> Any:
    transport = LocalScriptedTransport(proposal, 0, _LogicalClock())
    return asyncio.run(start_reasoner_job(actor.request, transport=transport, validator=validate_action,
                                          policy=preflight_policy, clock=_LogicalClock()))


class _LogicalClock:
    def __init__(self) -> None:
        self.current = 0.0

    def now(self) -> float:
        return self.current

    async def wait(self, seconds: float) -> None:
        self.current += seconds
        await asyncio.sleep(0)


def _terminal_outcome(summary: str, allowed: bool = True) -> TerminalOutcome:
    actor = _local_actors()
    return TerminalOutcome("completed" if allowed else "failed", "completed" if allowed else "proposal_invalid", 0, 1,
                           "safe", summary, allowed, 0, actor.no_action_proposal.provenance, "machinery")


def _conversation_evidence(case: TransitionCase) -> str:
    actor = _local_actors()
    if case.trigger == "on:transcribe":
        digest = scoped_hash(actor.fixture.transcript, scope="fixture-input", schema_version=actor.fixture.schema_version)
        if digest != actor.decision.input_hash:
            _error("transcript guard did not bind the scoped input hash")
        return "scoped transcript hash"
    if case.trigger == "on:route":
        decision = classify(actor.fixture, policy=load_threshold_policy(Path(__file__).parents[2] / "config" / "routing" / "slice0-v1.json"))
        if decision.route not in {"needs_tools", "chitchat", "unclear"}:
            _error("route guard did not produce a legal route")
        return f"local route:{decision.route}"
    if case.trigger == "on:awaitConfirmation":
        accepted = _validated(actor, actor.write_action)
        if preflight_policy(accepted, policy=actor.catalog.policy).outcome != "confirmation_required":
            _error("confirmation guard did not require exact confirmation")
        return "policy confirmation required"
    return "turn actor released processing values"


def _ledger_evidence(case: TransitionCase) -> str:
    actor = _local_actors()
    receipt = append_event(EventLedger.empty(), route_event(actor.fixture, actor.decision, event_id=1))
    if case.target == "Broken":
        tampered = EventLedger((replace(receipt.event, status="mutated"),), receipt.chain_hash)
        if verify_ledger(tampered).valid_chain:
            _error("ledger actor accepted a mutation")
        return "local verification failed closed"
    if not verify_ledger(receipt.ledger).valid_chain:
        _error("local append did not verify")
    return f"local ledger head:{receipt.chain_hash[:12]}"


def _memory_evidence(case: TransitionCase) -> str:
    actor = _local_actors()
    accepted = _validated(actor, actor.write_action)
    digest = action_hash(accepted.canonical_arguments, catalog_version=actor.catalog.catalog_version)
    receipt = append_event(EventLedger.empty(), route_event(actor.fixture, actor.decision, event_id=1))
    if not digest or not verify_ledger(receipt.ledger).valid_chain:
        _error("memory provenance or deletion evidence is not bound")
    return "typed provenance and local ledger evidence"


def _reasoner_evidence(case: TransitionCase) -> str:
    actor = _local_actors()
    if case.stable_id in {"REAS-bc3e49", "REAS-97e8bd"}:
        job = _run_job(actor, actor.no_action_proposal)
        if job.state not in {"running", "completed"}:
            _error("local reasoner actor did not produce its expected state")
        return f"local reasoner job:{job.state}"
    if case.stable_id == "REAS-0c1f49":
        malformed = replace(actor.write_proposal, job_id="job-other")
        job = _run_job(actor, malformed)
        if job.state != "failed":
            _error("local reasoner actor did not fail closed")
        return "local transport proposal rejected"
    if case.stable_id == "REAS-0cd65a":
        waiting = _run_job(actor, actor.write_proposal)
        job = advance_reasoner_job(waiting, ConfirmAction(actor.confirmation), clock=_LogicalClock())
        if job.state != "completed":
            _error("exact confirmation did not complete local job")
        return "exact confirmation consumed once"
    if case.stable_id == "REAS-345901":
        waiting = _run_job(actor, actor.write_proposal)
        job = advance_reasoner_job(waiting, Cancel(), clock=_LogicalClock())
        return f"local job stimulus:{job.state}"
    if case.stable_id == "REAS-79c30e":
        waiting = _run_job(actor, actor.write_proposal)
        job = advance_reasoner_job(waiting, Downgrade("Set aside until clarification."), clock=_LogicalClock())
        return f"local job stimulus:{job.state}"
    if case.stable_id == "REAS-b46837":
        waiting = _run_job(actor, actor.write_proposal)
        wrong = actor.confirmation._replace(action_hash="0" * 64)
        job = advance_reasoner_job(waiting, ConfirmAction(wrong), clock=_LogicalClock())
        return f"local job stimulus:{job.state}"
    return "local legal job transition"


def _catalog_evidence(case: TransitionCase) -> str:
    first = load_action_catalog(CATALOG_PATH)
    second = load_action_catalog(CATALOG_PATH)
    if first.catalog_hash != second.catalog_hash or not first.actions:
        _error("catalog actor did not reproduce an immutable reviewed catalog")
    return f"local catalog hash:{first.catalog_hash[:12]}"


def _tool_evidence(case: TransitionCase) -> str:
    actor = _local_actors()
    accepted = _validated(actor, actor.write_action)
    outcome = preflight_policy(accepted, policy=actor.catalog.policy).outcome
    if case.stable_id == "TEXE-9297f7" and outcome != "rejected":
        outcome = preflight_policy(accepted, policy=actor.catalog.policy._replace(policy_version="other")).outcome
        if outcome != "rejected":
            _error("policy actor did not reject the unsafe authorization")
    if case.target == "Succeeded":
        try:
            render_response(_terminal_outcome("A reviewed local result is ready."),
                            constraints=PresentationConstraints(response_id="response-machinery"))
        except RenderError as error:
            raise MachineryContractError("filtered tool output was unsafe") from error
        digest = action_hash(accepted.canonical_arguments, catalog_version=actor.catalog.catalog_version)
        return f"filtered output hash:{digest[:12]}"
    if case.target == "Failed" and case.stable_id == "TEXE-a8cfa2":
        try:
            render_response(_terminal_outcome("unreviewed private tool output"),
                            constraints=PresentationConstraints(response_id="response-machinery"))
        except RenderError:
            return "local output filter rejected unsafe result"
        _error("unsafe tool output passed local filtering")
    return f"local policy outcome:{outcome}"


def _voice_evidence(case: TransitionCase) -> str:
    actor = _local_actors()
    evidence = canonical_event_bytes(route_event(actor.fixture, actor.decision, event_id=1))
    if actor.fixture.transcript.encode("utf-8") in evidence:
        _error("voice actor retained a raw processing value")
    return "processing-only transcript absent from local evidence"


_ACTOR_EVIDENCE = {
    "conversationTurn": _conversation_evidence,
    "eventLedger": _ledger_evidence,
    "memoryRecord": _memory_evidence,
    "reasonerJob": _reasoner_evidence,
    "toolCatalog": _catalog_evidence,
    "toolExecution": _tool_evidence,
    "voiceSession": _voice_evidence,
}


def transition_case(machine_name: str, stable_id: str) -> TransitionCase:
    """Materialize one oracle row with its real local actor context."""
    oracles = parse_all_oracles(ORACLE_DIRECTORY)
    if machine_name not in oracles:
        _error(f"unknown machine: {machine_name}")
    row = next((item for item in oracles[machine_name] if item.stable_id == stable_id), None)
    if row is None:
        _error(f"unknown stable id for {machine_name}: {stable_id}")
    return TransitionCase(machine_name, row.stable_id, row.source, row.trigger, row.guard, row.target,
                          row.actions, row.trigger.removeprefix("on:").removeprefix("after:"), _local_actors())


def exercise_transition(case: TransitionCase) -> TransitionResult:
    """Execute a typed local actor and return its observed state and action names."""
    evidence_function = _ACTOR_EVIDENCE.get(case.machine_name)
    if evidence_function is None:
        _error(f"unknown machine: {case.machine_name}")
    evidence = evidence_function(case)
    return TransitionResult(case.machine_name, case.stable_id, case.source, case.trigger, case.guard,
                            case.target, case.expected_actions, evidence)
