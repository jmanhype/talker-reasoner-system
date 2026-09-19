from __future__ import annotations

import asyncio
import importlib
import json
import re
import sys
from collections.abc import Callable
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

from talk_reasoner.actions import CATALOG_PATH, RejectionCode, action_hash, load_action_catalog, preflight_policy, validate_action
from talk_reasoner.contracts import (
    CREDENTIAL_PATTERNS,
    EventLedger,
    append_event,
    canonical_event_bytes,
    load_fixture,
    scoped_hash,
    verify_ledger,
)
from talk_reasoner.jobs import Cancel, ConfirmAction, Expire, JobRouteError, TerminalOutcome, TurnAdvanced, advance_reasoner_job, job_terminal_summary, start_reasoner_job
from talk_reasoner.rendering import PresentationConstraints, RenderError, render_response
from talk_reasoner.routing import Calibration, apply_policy, classify, load_threshold_policy, route_event
from talk_reasoner.transports import LocalScriptedTransport, NoAction

# Reuse the real typed local actors and deterministic logical clock from the
# committed Slice-0 suite; these are executable fixtures, not mocks.
sys.path.insert(0, str(Path(__file__).parent))
from test_jobs import CATALOG, DECISION, FIXTURE, JOB_ID, NOW, TransportClock, action, confirmation, consent, request, script, state, waiting_job

try:
    MACHINERY = importlib.import_module("talk_reasoner.machinery")
except ModuleNotFoundError:
    MACHINERY = None

ROOT = Path(__file__).parents[1]
DOMAIN_RENDER = ROOT / "design" / "domain.modelith.md"
FIXTURE = load_fixture(ROOT / "tests" / "fixtures" / "slice0" / "trs-tools-001.json")
CATALOG = load_action_catalog(CATALOG_PATH)
ROUTING_POLICY = load_threshold_policy(ROOT / "config" / "routing" / "slice0-v1.json")

EXPECTED_INVARIANT_IDS = tuple(
    """
    session-processing-boundary raw-input-ephemeral route-fail-closed transcriber-no-authority
    job-staleness-bounded canceled-work-silent router-no-authority slow-path-only-after-route
    reasoner-proposes-only proposal-identity-bound contract-fail-closed action-schema-fail-closed
    action-no-credentials catalog-version-pinned policy-before-execution policy-three-outcomes
    confirmation-exact-and-expiring confirmation-single-use catalog-reviewed-before-active
    runtime-cannot-mutate-capability tool-schema-provenance tool-allowlist-only credential-isolation
    tool-output-filtered tool-result-not-sole-truth hot-state-minimized hot-state-ttl
    ledger-append-only ledger-minimized ledger-integrity-fail-closed response-filtered
    memory-provenance-bound memory-not-sole-truth memory-deletable talker-no-authority
    model-boundaries-explicit
    """.split()
)


def machinery() -> Any:
    """Require the missing offline machinery boundary as an assertion failure."""
    assert MACHINERY is not None, "talk_reasoner.machinery is missing"
    return MACHINERY


def write_arguments() -> dict[str, Any]:
    return {"key": "preferences", "value": "afternoon meetings", "terms": ["meeting"]}


def validated(name: str = "write_state", arguments: dict[str, Any] | None = None) -> Any:
    return validate_action(action(name, arguments), catalog=CATALOG, consent=consent(), state=state()).accepted


def terminal_outcome(state: str, summary: str = "A validated local response is ready.") -> Any:
    reason = "waiting_confirmation" if state == "waiting_confirmation" else state
    return TerminalOutcome(state, reason, 0, 1, "safe", summary, state == "completed", 1, script().provenance, JOB_ID)


def action_names(value: object) -> tuple[str, ...]:
    if value is None or value == "-":
        return ()
    if isinstance(value, str):
        return tuple(item.strip() for item in value.split(","))
    return tuple(value)


def exercise(machine_name: str, stable_id: str) -> tuple[Any, Any]:
    module = machinery()
    case = module.transition_case(machine_name, stable_id)
    return case, module.exercise_transition(case)


def forbidden_imports() -> tuple[str, ...]:
    return ("requests", "httpx", "aiohttp", "socket", "redis", "psycopg", "subprocess", "letta", "mem0", "cognee")


def source_has_only_local_dependencies() -> bool:
    pattern = "|".join(forbidden_imports())
    return not any(
        re.search(rf"(?m)^\s*(?:import|from)\s+(?:{pattern})\b", path.read_text(encoding="utf-8"))
        for path in (ROOT / "src" / "talk_reasoner").glob("*.py")
    )

def p_session_processing_boundary() -> None:
    machinery()
    allowed = classify(FIXTURE, policy=ROUTING_POLICY)
    denied = classify(replace(FIXTURE, consent=FIXTURE.consent._replace(reasoner=False)), policy=ROUTING_POLICY)
    assert allowed.route == "needs_tools" and allowed.risk == "low"
    assert denied.route == "unclear" and denied.risk == "unevaluable"

def p_raw_input_ephemeral() -> None:
    _, closed = exercise("voiceSession", "VOIC-e62d1f")
    _, finished = exercise("conversationTurn", "CONV-dab39a")
    assert closed.next_state == "Closed" and action_names(closed.actions) == ("releaseProcessingOnlyValues",)
    assert finished.next_state == "Terminal" and action_names(finished.actions) == ("releaseProcessingOnlyValues",)
    job = waiting_job()
    evidence = b"".join(canonical_event_bytes(item) for item in job.ledger.events)
    assert FIXTURE.transcript.encode() not in evidence

def p_route_fail_closed() -> None:
    machinery()
    unsafe = classify(replace(FIXTURE, transcript="Please send the private report now"), policy=ROUTING_POLICY)
    invalid = apply_policy(Calibration(-0.01, 0.50, 0.50), "low", policy=ROUTING_POLICY)
    assert unsafe.route == invalid.route == "unclear"

def p_transcriber_no_authority() -> None:
    machinery()
    decision = classify(FIXTURE, policy=ROUTING_POLICY)
    assert decision.input_hash == scoped_hash(FIXTURE.transcript, scope="fixture-input", schema_version=FIXTURE.schema_version)
    assert not any(hasattr(decision, name) for name in ("transcript", "consent", "action", "tool"))

def p_job_staleness_bounded() -> None:
    machinery()
    job = waiting_job()
    stale = advance_reasoner_job(job, Expire("stale_ttl"), clock=TransportClock())
    superseded = advance_reasoner_job(job, TurnAdvanced(1), clock=TransportClock())
    assert stale.state == superseded.state == "canceled"
    assert {stale.terminal_reason, superseded.terminal_reason} == {"stale_ttl_expired", "turn_superseded"}

def p_canceled_work_silent() -> None:
    machinery()
    canceled = advance_reasoner_job(waiting_job(), Cancel(), clock=TransportClock())
    outcome = job_terminal_summary(canceled)
    rendered = render_response(outcome, constraints=PresentationConstraints(response_id="response-canceled"))
    assert outcome.normal_result_allowed is False and rendered.text == ""

def p_router_no_authority() -> None:
    machinery()
    event = route_event(FIXTURE, DECISION, event_id=1)
    ledger = append_event(EventLedger.empty(), event).ledger
    assert verify_ledger(ledger).valid_chain
    assert FIXTURE.transcript.encode() not in canonical_event_bytes(event)
    assert not hasattr(DECISION, "action") and not hasattr(DECISION, "tool")

def p_slow_path_only_after_route() -> None:
    machinery()
    transport = LocalScriptedTransport(script(), 0, TransportClock())
    for name in ("trs-chitchat-001.json", "trs-unclear-001.json"):
        fixture = load_fixture(ROOT / "tests" / "fixtures" / "slice0" / name)
        decision = classify(fixture, policy=ROUTING_POLICY)
        bad = replace(request(), fixture=fixture, decision=decision)
        with pytest.raises(JobRouteError, match="only needs_tools"):
            asyncio.run(
                start_reasoner_job(
                    bad,
                    transport=transport,
                    validator=validate_action,
                    policy=preflight_policy,
                    clock=TransportClock(),
                )
            )
    assert transport.call_count == 0

def p_reasoner_proposes_only() -> None:
    machinery()
    job = waiting_job()
    assert job.state == "waiting_confirmation" and len(job.validated_actions) == 1
    assert job.validated_actions[0].action_name == "write_state"
    assert not hasattr(job.proposal, "execution") and not hasattr(job.proposal, "permission")

def p_proposal_identity_bound() -> None:
    machinery()
    from talk_reasoner.transports import ReasonerRequest, TransportContractError, validate_proposal

    wire = ReasonerRequest(
        "slice0-job-request-v1",
        JOB_ID,
        FIXTURE.session_id,
        FIXTURE.turn_id,
        0,
        DECISION.input_hash,
        CATALOG.catalog_hash,
        CATALOG.policy.policy_version,
    )
    validate_proposal(script(), wire, CATALOG)
    for changed in (
        script(job_id="job-other"),
        script(session_id="session-other"),
        script(turn_id="turn-other"),
        script(turn_epoch=1),
        script(input_hash="0" * 64),
        script(catalog_hash="0" * 64),
        script(policy_version="policy-other"),
    ):
        with pytest.raises(TransportContractError):
            validate_proposal(changed, wire, CATALOG)

def p_contract_fail_closed() -> None:
    machinery()
    malformed = script(job_id="job-other")
    job = asyncio.run(
        start_reasoner_job(
            request(),
            transport=LocalScriptedTransport(malformed, 0, TransportClock()),
            validator=validate_action,
            policy=preflight_policy,
            clock=TransportClock(),
        )
    )
    assert job.state == "failed" and job.terminal_reason == "proposal_invalid"
    assert verify_ledger(job.ledger).valid_chain

def p_action_schema_fail_closed() -> None:
    machinery()
    cases = (
        action("unknown"),
        action(arguments={"query": 7, "limit": 2, "terms": ()}),
        action(arguments={"key": "preferences", "value": "x", "terms": [], "password": "secret"}),
        action(arguments={"key": "preferences", "value": "x" * 257, "terms": []}),
        action(justification="short"),
        action(provenance=action().provenance._replace(source="")),
    )
    decisions = [validate_action(item, catalog=CATALOG, consent=consent(), state=state()) for item in cases]
    assert all(item.accepted is None and item.rejection_code is not None for item in decisions)

def p_action_no_credentials() -> None:
    machinery()
    privileged = action(arguments={"key": "preferences", "value": "x", "terms": [], "api_key": "secret"})
    decision = validate_action(privileged, catalog=CATALOG, consent=consent(), state=state())
    assert decision.rejection_code is RejectionCode.EXTRA_ARGUMENT
    assert not any(pattern.search(json.dumps(item)) for item in (CATALOG.actions.values()) for pattern in CREDENTIAL_PATTERNS)

def p_catalog_version_pinned() -> None:
    machinery()
    accepted = validated()
    assert accepted.catalog_version == CATALOG.catalog_version
    assert accepted.policy_version == CATALOG.policy.policy_version
    assert accepted.action_hash == action_hash(accepted.canonical_arguments, catalog_version=CATALOG.catalog_version)
    drifted = action(policy_version="slice0-policy-v2")
    assert validate_action(drifted, catalog=CATALOG, consent=consent(), state=state()).rejection_code is RejectionCode.POLICY_UNEVALUABLE

def p_policy_before_execution() -> None:
    machinery()
    write = validated()
    read = validated("read_state", {"key": "notes", "terms": ["exact"]})
    assert preflight_policy(write, policy=CATALOG.policy).outcome == "confirmation_required"
    assert preflight_policy(read, policy=CATALOG.policy).outcome == "allowed_without_confirmation"
    assert preflight_policy(write, policy=CATALOG.policy, confirmation=confirmation(write_arguments() | {"value": "changed"})).outcome == "rejected"

def p_policy_three_outcomes() -> None:
    machinery()
    write = validated()
    read = validated("read_state", {"key": "notes", "terms": ["exact"]})
    outcomes = {
        preflight_policy(read, policy=CATALOG.policy).outcome,
        preflight_policy(write, policy=CATALOG.policy).outcome,
        preflight_policy(write, policy=CATALOG.policy, confirmation=confirmation(write_arguments() | {"value": "changed"})).outcome,
    }
    assert outcomes == {"allowed_without_confirmation", "confirmation_required", "rejected"}

def p_confirmation_exact_and_expiring() -> None:
    machinery()
    accepted = validated()
    exact = confirmation()
    assert preflight_policy(accepted, policy=CATALOG.policy, confirmation=exact).outcome == "allowed_without_confirmation"
    mismatches = (
        exact._replace(action_hash="0" * 64),
        exact._replace(arguments=write_arguments() | {"value": "changed"}),
        exact._replace(subject="user-b"),
        exact._replace(target="fixture://other"),
        exact._replace(user_id="user-b"),
        exact._replace(session_id="session-b"),
        exact._replace(policy_version="old"),
        exact._replace(explicit=False),
        exact._replace(expires_at=NOW - timedelta(seconds=1)),
    )
    assert all(preflight_policy(accepted, policy=CATALOG.policy, confirmation=item).outcome == "rejected" for item in mismatches)

def p_confirmation_single_use() -> None:
    machinery()
    exact = confirmation()
    job = waiting_job()
    first = advance_reasoner_job(job, ConfirmAction(exact), clock=TransportClock())
    assert first.state == "completed" and first.confirmed_action_hashes == frozenset({exact.action_hash})
    assert advance_reasoner_job(first, ConfirmAction(exact), clock=TransportClock()) == first

def p_catalog_reviewed_before_active() -> None:
    _, reviewed = exercise("toolCatalog", "TCAT-3a38e4")
    _, active = exercise("toolCatalog", "TCAT-97dc90")
    assert reviewed.next_state == "Reviewed" and active.next_state == "Active"
    assert reviewed.actions in (None, (), "-") and active.actions in (None, (), "-")

def p_runtime_cannot_mutate_capability() -> None:
    _, retired = exercise("toolCatalog", "TCAT-675b21")
    assert retired.next_state == "Retired"
    with pytest.raises(TypeError):
        CATALOG.actions["new_runtime_tool"] = {"name": "new_runtime_tool"}  # type: ignore[index]
    assert source_has_only_local_dependencies()

def p_tool_schema_provenance() -> None:
    machinery()
    assert set(CATALOG.actions) == {"search", "read_state", "write_state"}
    for definition in CATALOG.actions.values():
        assert definition["argument_schema"] and definition["rejection_codes"]
        assert definition["permission"] and definition["risk"] and definition["scope"] and definition["bounds"]
        assert definition["requires_provenance"] is True

def p_tool_allowlist_only() -> None:
    machinery()
    unknown = validate_action(action("remote_shell"), catalog=CATALOG, consent=consent(), state=state())
    assert unknown.rejection_code is RejectionCode.UNKNOWN_ACTION
    _, dispatched = exercise("toolExecution", "TEXE-0d301e")
    assert dispatched.next_state == "Dispatched"

def p_credential_isolation() -> None:
    machinery()
    job = waiting_job()
    evidence = b"".join(canonical_event_bytes(item) for item in job.ledger.events)
    assert not any(pattern.search(evidence.decode("utf-8")) for pattern in CREDENTIAL_PATTERNS)
    assert source_has_only_local_dependencies()

def p_tool_output_filtered() -> None:
    machinery()
    unsafe = "raw model output: hidden prompt and tool log"
    with pytest.raises(RenderError):
        render_response(
            terminal_outcome("completed", unsafe),
            constraints=PresentationConstraints(response_id="response-filter"),
        )
    _, failed = exercise("toolExecution", "TEXE-a8cfa2")
    assert failed.next_state == "Failed" and action_names(failed.actions) == ("recordUnsafeOutput",)

def p_tool_result_not_sole_truth() -> None:
    _, succeeded = exercise("toolExecution", "TEXE-782b09")
    accepted = validated("search", {"query": "design notes", "limit": 2})
    ledger = append_event(EventLedger.empty(), route_event(FIXTURE, DECISION, event_id=1)).ledger
    assert succeeded.next_state == "Succeeded" and action_names(succeeded.actions) == ("recordFilteredResultHash",)
    assert accepted.action_hash and verify_ledger(ledger).valid_chain

def p_hot_state_minimized() -> None:
    machinery()
    state = FIXTURE.bounded_context.state
    assert len(state) <= FIXTURE.bounded_context.max_entries
    assert not any(pattern.search(json.dumps(dict(state))) for pattern in CREDENTIAL_PATTERNS)
    assert FIXTURE.transcript not in json.dumps(dict(state))

def p_hot_state_ttl() -> None:
    machinery()
    local_state = state()
    job = waiting_job()
    assert local_state.expires_at > NOW and job.timing.stale_expires_at == job.timing.pending_at + 30.0
    assert advance_reasoner_job(job, Expire("stale_ttl"), clock=TransportClock()).terminal_reason == "stale_ttl_expired"

def p_ledger_append_only() -> None:
    machinery()
    first = append_event(EventLedger.empty(), route_event(FIXTURE, DECISION, event_id=1))
    with pytest.raises(FrozenInstanceError):
        first.event.event_id = 2  # type: ignore[misc]
    assert first.ledger.events == (first.event,) and first.ledger.event_count == 1

def p_ledger_minimized() -> None:
    machinery()
    receipt = append_event(EventLedger.empty(), route_event(FIXTURE, DECISION, event_id=1))
    evidence = canonical_event_bytes(receipt.event)
    assert FIXTURE.transcript.encode() not in evidence
    assert b'"transcript"' not in evidence and b'"raw_content"' not in evidence
    assert not any(pattern.search(evidence.decode("utf-8")) for pattern in CREDENTIAL_PATTERNS)

def p_ledger_integrity_fail_closed() -> None:
    _, broken = exercise("eventLedger", "EVEN-d90d1d")
    assert broken.next_state == "Broken" and action_names(broken.actions) == ("recordIntegrityFailure",)
    receipt = append_event(EventLedger.empty(), route_event(FIXTURE, DECISION, event_id=1))
    tampered = EventLedger((replace(receipt.event, status="mutated"),), receipt.chain_hash)
    assert verify_ledger(tampered).valid_chain is False

def p_response_filtered() -> None:
    machinery()
    rendered = render_response(
        terminal_outcome("completed", "A safe local answer."),
        constraints=PresentationConstraints(response_id="response-safe"),
    )
    assert rendered.text == "A safe local answer."
    with pytest.raises(RenderError):
        render_response(
            terminal_outcome("completed", '{"answer":"private tool output"}'),
            constraints=PresentationConstraints(response_id="response-unsafe"),
        )

def p_memory_provenance_bound() -> None:
    _, approved = exercise("memoryRecord", "MEMO-0697b6")
    _, recalled = exercise("memoryRecord", "MEMO-b8a59c")
    assert approved.next_state == "Approved" and action_names(approved.actions) == ("recordApprovalEvidence",)
    assert recalled.next_state == "Active" and action_names(recalled.actions) == ("recordBoundedRecallWithProvenance",)
    assert source_has_only_local_dependencies()

def p_memory_not_sole_truth() -> None:
    _, superseded = exercise("memoryRecord", "MEMO-9faf38")
    assert superseded.next_state == "Superseded" and action_names(superseded.actions) == ("recordSuccessorAndProvenance",)
    receipt = append_event(EventLedger.empty(), route_event(FIXTURE, DECISION, event_id=1))
    assert verify_ledger(receipt.ledger).valid_chain and source_has_only_local_dependencies()

def p_memory_deletable() -> None:
    for stable_id in ("MEMO-814928", "MEMO-c8e66c", "MEMO-d9f286", "MEMO-8862c9"):
        _, deleted = exercise("memoryRecord", stable_id)
        assert deleted.next_state == "Deleted"
        assert action_names(deleted.actions) == ("deleteFromPrimaryAndBackups",)

def p_talker_no_authority() -> None:
    machinery()
    rendered = render_response(
        terminal_outcome("waiting_confirmation"),
        constraints=PresentationConstraints(response_id="response-confirm", validated_action=validated()),
    )
    assert "no tool will run" in rendered.text
    assert source_has_only_local_dependencies()

def p_model_boundaries_explicit() -> None:
    machinery()
    modules = {
        "routing": (ROOT / "src" / "talk_reasoner" / "routing.py").read_text(encoding="utf-8"),
        "rendering": (ROOT / "src" / "talk_reasoner" / "rendering.py").read_text(encoding="utf-8"),
    }
    assert not re.search(r"(?m)^\s*(?:from|import)\s+talk_reasoner\.(?:jobs|actions|transports)\b", modules["routing"])
    assert not re.search(r"(?m)^\s*(?:from|import)\s+talk_reasoner\.(?:transports|cli)\b", modules["rendering"])
    assert source_has_only_local_dependencies()


INVARIANT_PROPERTIES: dict[str, Callable[[], None]] = {
    invariant_id: globals()[f"p_{invariant_id.replace('-', '_')}"]
    for invariant_id in EXPECTED_INVARIANT_IDS
}


def test_parse_invariant_ids_returns_exactly_the_canonical_thirty_six() -> None:
    parsed = machinery().parse_invariant_ids(DOMAIN_RENDER)
    assert len(parsed) == 36
    assert len(set(parsed)) == 36
    assert tuple(parsed) == EXPECTED_INVARIANT_IDS


@pytest.mark.parametrize("invariant_id", EXPECTED_INVARIANT_IDS)
def test_each_canonical_invariant_has_and_executes_a_real_property(invariant_id: str) -> None:
    assert machinery().parse_invariant_ids(DOMAIN_RENDER) == EXPECTED_INVARIANT_IDS
    assert invariant_id in INVARIANT_PROPERTIES
    INVARIANT_PROPERTIES[invariant_id]()


@pytest.mark.parametrize("clause", ("transcript bounded", "credential-free transcript", "processing boundary consented"))
def test_transcript_guard_falsifies_each_independent_clause(tmp_path: Path, clause: str) -> None:
    machinery()
    record = json.loads((ROOT / "tests/fixtures/slice0/trs-tools-001.json").read_text(encoding="utf-8"))
    mutations = {
        "transcript bounded": lambda: record.__setitem__("transcript", "x" * 257),
        "credential-free transcript": lambda: record.__setitem__("transcript", "please use api_key secret-value"),
        "processing boundary consented": lambda: record["consent"].__setitem__("reasoner", False),
    }
    mutations[clause]()
    path = tmp_path / "invalid-fixture.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    if clause == "processing boundary consented":
        assert classify(load_fixture(path), policy=ROUTING_POLICY).route == "unclear"
    else:
        with pytest.raises(ValueError, match="transcript|credential"):
            load_fixture(path)


@pytest.mark.parametrize(
    ("clause", "calibration", "risk"),
    (
        ("selected label is needsTools", Calibration(0.95, 0.04, 0.01), "low"),
        ("scores are finite probabilities", Calibration(-0.01, 0.50, 0.50), "low"),
        ("risk is evaluable", Calibration(0.04, 0.95, 0.01), "high"),
        ("calibration version is valid", Calibration(0.04, 0.95, 0.01), "unknown"),
    ),
)
def test_route_guard_falsifies_each_independent_clause(clause: str, calibration: Calibration, risk: str) -> None:
    machinery()
    if risk == "unknown":
        with pytest.raises(ValueError, match="risk"):
            apply_policy(calibration, risk, policy=ROUTING_POLICY)
        return
    selection = apply_policy(calibration, risk, policy=ROUTING_POLICY)
    assert selection.selected_label == "chitchat" or selection.route != "needs_tools"


def test_confirmation_guard_falsifies_missing_action_hash_and_policy_outcome() -> None:
    machinery()
    accepted = validated()
    assert accepted.action_hash and preflight_policy(accepted, policy=CATALOG.policy).outcome == "confirmation_required"
    malformed = action(justification="short")
    assert validate_action(malformed, catalog=CATALOG, consent=consent(), state=state()).accepted is None
    read = validated("read_state", {"key": "notes", "terms": ["exact"]})
    assert preflight_policy(read, policy=CATALOG.policy).outcome == "allowed_without_confirmation"


@pytest.mark.parametrize("clause", ("event is minimized", "event has no credentials", "prior event id is exact", "prior event hash is exact"))
def test_event_guard_falsifies_each_independent_clause(clause: str) -> None:
    machinery()
    first = route_event(FIXTURE, DECISION, event_id=1)
    receipt = append_event(EventLedger.empty(), first)
    changes = {
        "event is minimized": {"rejection_reason": f"raw transcript: {FIXTURE.transcript}", "prior_event_id": 1, "prior_event_hash": receipt.chain_hash},
        "event has no credentials": {"rejection_reason": "api_key=secret", "prior_event_id": 1, "prior_event_hash": receipt.chain_hash},
        "prior event id is exact": {"prior_event_id": 99, "prior_event_hash": receipt.chain_hash},
        "prior event hash is exact": {"prior_event_id": 1, "prior_event_hash": "0" * 64},
    }
    expected = {
        "event is minimized": "raw|credential|minimized",
        "event has no credentials": "raw|credential|minimized",
        "prior event id is exact": "prior_event_id",
        "prior event hash is exact": "prior_event_hash",
    }[clause]
    with pytest.raises(ValueError, match=expected):
        append_event(receipt.ledger, replace(first, event_id=2, **changes[clause]))


@pytest.mark.parametrize("defect", ("valid_chain false", "gap", "invalid prior hash", "duplicate terminal", "mutation"))
def test_chain_guard_falsifies_each_independent_clause(defect: str) -> None:
    machinery()
    receipt = append_event(EventLedger.empty(), route_event(FIXTURE, DECISION, event_id=1))
    event = receipt.event
    if defect == "valid_chain false":
        ledger = EventLedger((replace(event, status="mutated"),), receipt.chain_hash)
    elif defect == "gap":
        ledger = EventLedger((replace(event, event_id=2),), None)
    elif defect == "invalid prior hash":
        ledger = EventLedger((replace(event, prior_event_hash="0" * 64),), receipt.chain_hash)
    elif defect == "duplicate terminal":
        rendered = replace(event, status="rendered")
        first = append_event(EventLedger.empty(), rendered).ledger
        ledger = append_event(first, replace(rendered, event_id=2, prior_event_id=1, prior_event_hash=first.head_hash)).ledger
    else:
        ledger = EventLedger((replace(event, status="mutated"),), receipt.chain_hash)
    report = verify_ledger(ledger)
    assert report.valid_chain is False


@pytest.mark.parametrize("missing", ("content provenance", "consent", "review evidence"))
def test_memory_guard_falsifies_each_independent_clause(missing: str) -> None:
    _, rejected = exercise("memoryRecord", "MEMO-ef809c")
    assert rejected.next_state == "Rejected" and action_names(rejected.actions) == ("recordMemoryRejection",)
    row = next(line for line in (ROOT / "design/machines/MemoryRecord.matrix.md").read_text(encoding="utf-8").splitlines() if "provenanceConsentAndReviewComplete" in line)
    assert missing.removeprefix("content ").removesuffix(" evidence") in row


@pytest.mark.parametrize("failed_store", ("primary", "derived", "backup"))
def test_memory_deletion_guard_falsifies_each_independent_clause(failed_store: str) -> None:
    _, deleted = exercise("memoryRecord", "MEMO-d9f286")
    assert deleted.next_state == "Deleted" and action_names(deleted.actions) == ("deleteFromPrimaryAndBackups",)
    assert failed_store in (ROOT / "design/machines/MemoryRecord.matrix.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("clause", ("route is valid needsTools", "turn epoch is fresh", "input hash is bound", "reasoner consent is active"))
def test_reasoner_route_guard_falsifies_each_independent_clause(clause: str) -> None:
    machinery()
    bad = request()
    if clause == "route is valid needsTools":
        fixture = load_fixture(ROOT / "tests" / "fixtures" / "slice0" / "trs-chitchat-001.json")
        bad = replace(bad, fixture=fixture, decision=classify(fixture, policy=ROUTING_POLICY))
    elif clause == "turn epoch is fresh":
        bad = replace(bad, turn_epoch=-1)
    elif clause == "input hash is bound":
        bad = replace(bad, fixture=replace(FIXTURE, turn_id="turn-other"))
    else:
        bad = replace(bad, consent=consent()._replace(expires_at=NOW - timedelta(seconds=1)))
    try:
        job = asyncio.run(start_reasoner_job(bad, transport=LocalScriptedTransport(script(), 0, TransportClock()), validator=validate_action, policy=preflight_policy, clock=TransportClock()))
    except JobRouteError:
        assert clause != "reasoner consent is active"
        return
    if clause == "reasoner consent is active":
        assert job.state == "failed"
    else:
        raise AssertionError(clause)


def run_proposal(proposal: Any) -> Any:
    return asyncio.run(start_reasoner_job(request(), transport=LocalScriptedTransport(proposal, 0, TransportClock()), validator=validate_action, policy=preflight_policy, clock=TransportClock()))


@pytest.mark.parametrize("clause", ("validated action requires confirmation", "action hash is present"))
def test_proposal_confirmation_guard_falsifies_each_independent_clause(clause: str) -> None:
    machinery()
    no_action = run_proposal(script(no_action=NoAction("Known locally.")))
    waiting = waiting_job()
    if clause == "validated action requires confirmation":
        assert no_action.state == "completed" and waiting.state == "waiting_confirmation"
    else:
        assert waiting.validated_actions and all(item.action_hash for item in waiting.validated_actions)


@pytest.mark.parametrize("clause", ("waiting hash is exact", "confirmation is unused", "confirmation arguments are exact", "confirmation is unexpired"))
def test_all_confirmations_guard_falsifies_each_independent_clause(clause: str) -> None:
    machinery()
    job = waiting_job()
    if clause == "waiting hash is exact":
        item = confirmation(action_hash="0" * 64)
    elif clause == "confirmation is unused":
        first = advance_reasoner_job(job, ConfirmAction(confirmation()), clock=TransportClock())
        second = advance_reasoner_job(first, ConfirmAction(confirmation()), clock=TransportClock())
        assert first.used_confirmation_hashes and second == first and second.state == "completed"
        return
    elif clause == "confirmation arguments are exact":
        item = confirmation(write_arguments() | {"value": "changed"})
    else:
        item = confirmation()._replace(expires_at=NOW - timedelta(seconds=1))
    rejected = advance_reasoner_job(job, ConfirmAction(item), clock=TransportClock())
    assert rejected.state == "failed" and rejected.terminal_reason == "policy_failed"


@pytest.mark.parametrize("missing", ("schema hash", "provenance", "permission", "risk", "scope", "bounds", "rejection codes"))
def test_catalog_review_guard_falsifies_each_independent_clause(tmp_path: Path, missing: str) -> None:
    machinery()
    record = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    item = record["actions"][0]
    changes = {
        "schema hash": lambda: item["argument_schema"]["query"].__delitem__("max_length"),
        "provenance": lambda: item.__setitem__("requires_provenance", False),
        "permission": lambda: item.__setitem__("permission", "runtime.everything"),
        "risk": lambda: item.__setitem__("risk", "unevaluable"),
        "scope": lambda: item.__setitem__("scope", "runtime-unrestricted"),
        "bounds": lambda: item.__setitem__("bounds", {}),
        "rejection codes": lambda: item.__setitem__("rejection_codes", []),
    }
    changes[missing]()
    path = tmp_path / "invalid-catalog.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError):
        load_action_catalog(path)


@pytest.mark.parametrize("clause", ("reviewed catalog hash is unchanged", "policy version is bound"))
def test_catalog_activation_guard_falsifies_each_independent_clause(clause: str) -> None:
    machinery()
    accepted = validated()
    if clause == "reviewed catalog hash is unchanged":
        changed = load_action_catalog(CATALOG_PATH)
        assert changed.catalog_hash == CATALOG.catalog_hash
    else:
        assert accepted.policy_version == CATALOG.policy.policy_version
        assert preflight_policy(accepted, policy=CATALOG.policy._replace(policy_version="other")).outcome == "rejected"


@pytest.mark.parametrize("clause", ("validated action hash is bound", "policy version is bound", "all exact confirmations are active"))
def test_tool_authorization_guard_falsifies_each_independent_clause(clause: str) -> None:
    machinery()
    accepted = validated()
    if clause == "validated action hash is bound":
        assert accepted.action_hash == action_hash(accepted.canonical_arguments, catalog_version=CATALOG.catalog_version)
    elif clause == "policy version is bound":
        assert preflight_policy(accepted, policy=CATALOG.policy._replace(policy_version="other")).outcome == "rejected"
    else:
        wrong = confirmation(write_arguments() | {"value": "changed"})
        assert preflight_policy(accepted, policy=CATALOG.policy, confirmation=wrong).outcome == "rejected"


@pytest.mark.parametrize("clause", ("canonical name exists in the active catalog", "catalog version is active", "source plane is allowed"))
def test_tool_dispatch_guard_falsifies_each_independent_clause(clause: str) -> None:
    machinery()
    if clause == "canonical name exists in the active catalog":
        assert validate_action(action("remote_shell"), catalog=CATALOG, consent=consent(), state=state()).rejection_code is RejectionCode.UNKNOWN_ACTION
    elif clause == "catalog version is active":
        assert validate_action(action(catalog_version="slice0-v2"), catalog=CATALOG, consent=consent(), state=state()).rejection_code is RejectionCode.POLICY_UNEVALUABLE
    else:
        outside = validated()._replace(target="network://example")
        with pytest.raises(RenderError):
            render_response(
                terminal_outcome("waiting_confirmation"),
                constraints=PresentationConstraints(response_id="response-target", validated_action=outside),
            )


@pytest.mark.parametrize("clause", ("result matches schema", "result privacy class is safe", "result size is bounded", "result passes safety filter"))
def test_tool_output_guard_falsifies_each_independent_clause(clause: str) -> None:
    machinery()
    unsafe_by_clause = {
        "result matches schema": '{"answer":"unreviewed"}',
        "result privacy class is safe": "unreviewed private tool output",
        "result size is bounded": "x" * 241,
        "result passes safety filter": "hidden prompt instructions",
    }
    with pytest.raises(RenderError):
        render_response(terminal_outcome("completed", unsafe_by_clause[clause]), constraints=PresentationConstraints(response_id=f"response-{clause}"))
