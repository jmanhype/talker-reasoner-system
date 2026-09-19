from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from talk_reasoner.actions import ActionCase, ActionProposal, ActionProvenance, CATALOG_PATH, ConsentRecord, ConfirmationRecord, FixtureState, RejectionCode, action_hash, evaluate_action_suite, load_action_catalog, policy_event, preflight_policy, validate_action, validation_event
from talk_reasoner.contracts import EventLedger, append_event, canonical_event_bytes, verify_ledger

NOW = datetime.now(timezone.utc).replace(microsecond=0)
def catalog() -> Any:
    return load_action_catalog(CATALOG_PATH)
def write_catalog(tmp_path: Path, changes: dict[str, Any]) -> Path:
    record = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    path = tmp_path / "catalog.json"; path.write_text(json.dumps(record | changes), encoding="utf-8"); return path
def provenance() -> ActionProvenance:
    return ActionProvenance("slice0-provenance-v1", "slice0-2026-09-19", "synthetic-local", "reviewed", "b" * 64)
def proposal(name: str = "search", arguments: dict[str, Any] | None = None, **changes: Any) -> ActionProposal:
    base = ActionProposal("slice0-proposal-v1", name, {"query": "design notes", "limit": 3} if arguments is None else arguments,
                          "job-action-001", "session-action", "turn-action", 2, "user-a", "user-a", "fixture://slice0",
                          "The user asked for local design notes.", provenance(), "slice0-v1", "slice0-policy-v1")
    return base._replace(**changes) if changes else base
def consent_record() -> ConsentRecord:
    return ConsentRecord("consent-v1", "user-a", "session-action", "user-a", frozenset({"local.read", "local.write"}),
                         NOW - timedelta(seconds=5), NOW + timedelta(minutes=5), "slice0-policy-v1")
def fixture_state(**changes: Any) -> FixtureState:
    base = FixtureState("state-v1", "session-action", 7, NOW + timedelta(minutes=5), {"notes": ["design"]}, frozenset())
    return base._replace(**changes) if changes else base
def confirmation(arguments: dict[str, Any], **changes: Any) -> ConfirmationRecord:
    digest = action_hash(arguments, catalog_version="slice0-v1")
    base = ConfirmationRecord("confirmation-v1", True, "write_state", digest, arguments, "user-a", "fixture://slice0",
                              "user-a", "session-action", "slice0-policy-v1", NOW, NOW + timedelta(seconds=30))
    return base._replace(**changes) if changes else base
def write_arguments() -> dict[str, Any]:
    return {"key": "notes", "value": "prefers local examples", "terms": ["local"]}
def validated_write(loaded: Any = None) -> Any:
    arguments = write_arguments()
    return validate_action(proposal("write_state", arguments), catalog=loaded or catalog(), consent=consent_record(), state=fixture_state()).accepted
def test_catalog_is_exact_versioned_and_hashed(tmp_path: Path) -> None:
    loaded = catalog()
    assert tuple(sorted(loaded.actions)) == ("read_state", "search", "write_state")
    assert (loaded.catalog_version, loaded.policy.policy_version, loaded.policy.confirmation_ttl_seconds) == ("slice0-v1", "slice0-policy-v1", 30)
    assert loaded.catalog_hash == loaded.catalog_hash and re.fullmatch(r"[0-9a-f]{64}", loaded.catalog_hash)
    assert all(action["rejection_codes"] and action["argument_schema"] and action["state_keys"] is not None for action in loaded.actions.values())
    with pytest.raises(ValueError, match="duplicate JSON key"):
        path = tmp_path / "duplicate.json"; path.write_text('{"schema_version":"a","schema_version":"b"}', encoding="utf-8"); load_action_catalog(path)
@pytest.mark.parametrize(("changes", "message"), [
    ({"catalog_version": "slice0-v2"}, "unsupported catalog_version"),
    ({"actions": []}, "exactly search, read_state, write_state"),
    ({"rejection_codes": ["slice0-v1:unknown_action"]}, "rejection_codes"),
    ({"risk_classes": {}}, "risk_classes"),
    ({"permissions": {}}, "permissions"),
    ({"policy_version": "unknown"}, "unsupported policy_version"),
])
def test_catalog_fail_closed(tmp_path: Path, changes: dict[str, Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        load_action_catalog(write_catalog(tmp_path, changes))
def test_catalog_action_safety_fails_closed(tmp_path: Path) -> None:
    record = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    unsafe = json.loads(json.dumps(record)); unsafe["actions"][0]["risk"] = "high"
    missing = json.loads(json.dumps(record)); del missing["actions"][0]["argument_schema"]["query"]["min_length"]
    duplicate = json.loads(json.dumps(record)); duplicate["actions"].append(json.loads(json.dumps(record["actions"][0])))
    extra = json.loads(json.dumps(record)); extra["actions"][0]["argument_schema"]["credential"] = {"type": "string", "min_length": 1, "max_length": 2}
    for value, message in ((unsafe, "unsafe permission/risk"), (missing, "bounds"), (duplicate, "duplicate action name"), (extra, "canonical argument schema")):
        path = tmp_path / "invalid-catalog.json"; path.write_text(json.dumps(value), encoding="utf-8")
        with pytest.raises(ValueError, match=message): load_action_catalog(path)
@pytest.mark.parametrize(("name", "arguments", "changes", "code"), [
    ("unknown", None, {}, RejectionCode.UNKNOWN_ACTION),
    ("search", {"query": 7, "limit": 3}, {}, RejectionCode.MALFORMED_TYPE),
    ("search", {"query": "x", "limit": 3, "credential": "abc"}, {}, RejectionCode.EXTRA_ARGUMENT),
    ("search", {"query": "x" * 81, "limit": 3}, {}, RejectionCode.OUT_OF_RANGE),
    ("search", {"query": "x", "limit": 3, "terms": ["a"] * 4}, {}, RejectionCode.OUT_OF_RANGE),
    ("read_state", {"key": "passwords"}, {}, RejectionCode.DISALLOWED_STATE_KEY),
    ("search", None, {"justification": ""}, RejectionCode.MISSING_JUSTIFICATION),
    ("search", None, {"provenance": proposal().provenance._replace(source="")}, RejectionCode.MISSING_PROVENANCE),
    ("search", None, {"user_id": "user-b"}, RejectionCode.CONSENT_MISMATCH),
    ("search", None, {}, RejectionCode.EXPIRED_STATE),
    ("write_state", None, {}, RejectionCode.DUPLICATE_NON_IDEMPOTENT),
    ("search", None, {"policy_version": "unknown"}, RejectionCode.POLICY_UNEVALUABLE),
])
def test_validation_rejection_matrix(name: str, arguments: dict[str, Any] | None, changes: Any, code: RejectionCode) -> None:
    loaded = catalog(); item = proposal(name, arguments, **changes)
    state_value = fixture_state()
    if code is RejectionCode.EXPIRED_STATE:
        state_value = fixture_state(expires_at=NOW - timedelta(seconds=1))
    elif code is RejectionCode.DUPLICATE_NON_IDEMPOTENT:
        arguments = write_arguments()
        first = validate_action(proposal("write_state", arguments), catalog=loaded, consent=consent_record(), state=fixture_state()).accepted
        state_value = fixture_state(seen_non_idempotent=frozenset({first.action_hash}))
        item = proposal("write_state", arguments)
    decision = validate_action(item, catalog=loaded, consent=consent_record(), state=state_value)
    assert decision.accepted is None and decision.rejection_code is code
def test_valid_actions_are_typed_and_hashed() -> None:
    loaded = catalog()
    for name, arguments in (("search", {"query": "design", "limit": 2}), ("read_state", {"key": "notes", "terms": ["exact"]}), ("write_state", write_arguments())):
        decision = validate_action(proposal(name, arguments), catalog=loaded, consent=consent_record(), state=fixture_state())
        assert decision.accepted is not None and decision.rejection_code is None
        assert decision.accepted.action_hash == action_hash(arguments, catalog_version=loaded.catalog_version)
def test_policy_outcomes_and_exact_confirmation_binding() -> None:
    loaded = catalog()
    assert preflight_policy(validated_write(loaded), policy=loaded.policy).outcome == "confirmation_required"
    for arguments in ({"query": "design", "limit": 2}, {"key": "notes", "terms": ["exact"]}):
        accepted = validate_action(proposal("search" if "query" in arguments else "read_state", arguments),
                                   catalog=loaded, consent=consent_record(), state=fixture_state()).accepted
        assert preflight_policy(accepted, policy=loaded.policy).outcome == "allowed_without_confirmation"
    action = validated_write(loaded); arguments = write_arguments(); exact = confirmation(arguments)
    assert preflight_policy(action, policy=loaded.policy, confirmation=exact).outcome == "allowed_without_confirmation"
    mismatch_cases = (confirmation(arguments | {"value": "changed"}), confirmation(arguments, action_hash="0" * 64), confirmation(arguments, target="fixture://other"),
                      confirmation(arguments, subject="user-b"), confirmation(arguments, user_id="user-b"), confirmation(arguments, session_id="session-b"),
                      confirmation(arguments, policy_version="old"), confirmation(arguments, explicit=False))
    assert all(preflight_policy(action, policy=loaded.policy, confirmation=item).outcome == "rejected" and
               preflight_policy(action, policy=loaded.policy, confirmation=item).rejection_code is RejectionCode.CONFIRMATION_MISMATCH
               for item in mismatch_cases)
    expired = confirmation(arguments, granted_at=NOW - timedelta(seconds=31), expires_at=NOW - timedelta(seconds=1))
    expired_decision = preflight_policy(action, policy=loaded.policy, confirmation=expired)
    assert expired_decision.outcome == "rejected" and expired_decision.rejection_code is RejectionCode.CONFIRMATION_EXPIRED
    wrong_policy = loaded.policy._replace(policy_version="unknown")
    assert preflight_policy(action, policy=wrong_policy).outcome == "rejected"
def action_case(item: ActionProposal, outcome: str, code: RejectionCode | None = None, state: FixtureState | None = None, confirmation_value: ConfirmationRecord | None = None) -> ActionCase:
    return ActionCase(item, catalog(), consent_record(), state or fixture_state(), confirmation_value, outcome, code)
def test_action_suite_report_has_every_count_and_denominator() -> None:
    write = write_arguments(); write_hash = action_hash(write, catalog_version="slice0-v1")
    duplicate_state = fixture_state(seen_non_idempotent=frozenset({write_hash}))
    invalid = [proposal("unknown"), proposal(arguments={"query": 7, "limit": 3}), proposal(arguments={"query": "x", "limit": 3, "credential": "y"}),
               proposal(arguments={"query": "x" * 81, "limit": 3}), proposal("read_state", {"key": "private", "terms": ["exact"]}),
               proposal(justification=""), proposal(provenance=provenance()._replace(source="")), proposal(user_id="user-b"), proposal(policy_version="unknown")]
    expired_state = fixture_state(expires_at=NOW - timedelta(seconds=1))
    codes = (RejectionCode.UNKNOWN_ACTION, RejectionCode.MALFORMED_TYPE, RejectionCode.EXTRA_ARGUMENT, RejectionCode.OUT_OF_RANGE,
             RejectionCode.DISALLOWED_STATE_KEY, RejectionCode.MISSING_JUSTIFICATION, RejectionCode.MISSING_PROVENANCE,
             RejectionCode.CONSENT_MISMATCH, RejectionCode.POLICY_UNEVALUABLE)
    matrix = [
        action_case(proposal(arguments={"query": "design", "limit": 2}), "allowed_without_confirmation"),
        action_case(proposal("read_state", {"key": "notes", "terms": ["exact"]}), "allowed_without_confirmation"),
        action_case(proposal("write_state", write_arguments()), "confirmation_required"),
        *(action_case(item, "rejected", code) for item, code in zip(invalid, codes, strict=True)),
        action_case(proposal(), "rejected", RejectionCode.EXPIRED_STATE, expired_state),
        action_case(proposal("write_state", write_arguments()), "rejected", RejectionCode.DUPLICATE_NON_IDEMPOTENT, duplicate_state),
    ]
    changed = confirmation(write | {"value": "changed"})
    expired = confirmation(write, granted_at=NOW - timedelta(seconds=31), expires_at=NOW - timedelta(seconds=1))
    cases = matrix + [action_case(proposal("write_state", write_arguments()), "rejected", RejectionCode.CONFIRMATION_MISMATCH, confirmation_value=changed),
                      action_case(proposal("write_state", write_arguments()), "rejected", RejectionCode.CONFIRMATION_EXPIRED, confirmation_value=expired)]
    report = evaluate_action_suite(cases)
    assert report.total == report.valid_denominator == report.invalid_denominator == len(cases) == 16
    assert (report.valid_count, report.invalid_count) == (5, 11)
    assert report.outcome_counts == {"allowed_without_confirmation": 2, "confirmation_required": 1, "rejected": 13}
    assert set(report.outcome_denominators.values()) == {16} and set(report.rejection_denominators.values()) == {16}
    assert report.rejection_counts == {code.value: 1 for code in RejectionCode} and report.mismatches == ()
    assert report.decision == "pass" and report.catalog_hash == catalog().catalog_hash
def test_action_suite_hold_and_events_use_hashes_without_raw_arguments() -> None:
    wrong = action_case(proposal(arguments={"query": "design", "limit": 2}), "confirmation_required")
    report = evaluate_action_suite([wrong])
    assert report.decision == "hold" and len(report.mismatches) == 1
    loaded = catalog(); arguments = {"query": "private design phrase", "limit": 2}
    decision = validate_action(proposal(arguments=arguments), catalog=loaded, consent=consent_record(), state=fixture_state()); accepted = decision.accepted
    policy = preflight_policy(accepted, policy=loaded.policy)
    first = append_event(EventLedger.empty(), validation_event(decision, event_id=1))
    second = append_event(first.ledger, policy_event(policy, accepted, event_id=2, prior_event_id=1, prior_event_hash=first.chain_hash))
    assert verify_ledger(second.ledger).valid_chain and second.ledger.event_count == 2
    payload = b"".join(canonical_event_bytes(item) for item in second.ledger.events)
    assert b"private design phrase" not in payload and all(item.action_name == "search" and item.privacy_classification == "nonprivate" and item.action_hash == accepted.action_hash for item in second.ledger.events)
    source = Path(__import__("talk_reasoner.actions", fromlist=[""]).__file__).read_text(encoding="utf-8")
    assert not [name for name in ("requests", "httpx", "aiohttp", "socket", "redis", "psycopg", "subprocess", "letta", "mem0") if re.search(rf"(?m)^\s*(import|from)\s+{name}\b", source)]
