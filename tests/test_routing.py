from __future__ import annotations

import json
import math
import re
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from talk_reasoner.contracts import EventLedger, append_event, canonical_event_bytes, load_fixture, load_fixture_corpus, scoped_hash, verify_ledger
from talk_reasoner.routing import CALIBRATION_VERSION, BoundarySensitivity, Calibration, apply_policy, classify, evaluate_routing, load_threshold_policy, route_event

FIXTURES = Path(__file__).parent / "fixtures" / "slice0"
PATHS = sorted(FIXTURES.glob("*.json"))
POLICY_PATH = Path(__file__).parents[1] / "config" / "routing" / "slice0-v1.json"
ROUTES = ("chitchat", "needs_tools", "unclear")


def write_policy(tmp_path: Path, **changes: Any) -> Path:
    record: dict[str, Any] = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    path = tmp_path / "policy.json"; path.write_text(json.dumps(record | changes), encoding="utf-8"); return path
def test_versioned_policy_loads_and_invalid_policies_fail_closed(tmp_path: Path) -> None:
    policy = load_threshold_policy(POLICY_PATH)
    values = (policy.thresholds_version, policy.chitchat_confidence_min, policy.needs_tools_confidence_min, policy.invalid_fallback_route, policy.safety_fallback_route)
    assert values == ("slice0-v1", 0.90, 0.80, "unclear", "unclear")
    assert re.fullmatch(r"[0-9a-f]{64}", policy.policy_hash)
    for changes in (
        {"chitchat_confidence_min": 0.80, "needs_tools_confidence_min": 0.90},
        {"chitchat_confidence_min": 1.01, "needs_tools_confidence_min": 0.80},
        {"invalid_fallback_route": "needs_tools"},
        {"thresholds_version": "slice0-v2", "chitchat_confidence_min": 0.89},
        {"schema_version": "unknown-v2"},
    ):
        with pytest.raises(ValueError, match="policy"):
            load_threshold_policy(write_policy(tmp_path, **changes))

    path = tmp_path / "duplicate.json"; path.write_text('{"schema_version":"a","schema_version":"b"}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        load_threshold_policy(path)

def test_classify_is_deterministic_and_probability_shape_is_exact() -> None:
    policy = load_threshold_policy(POLICY_PATH)
    fixture = load_fixture(FIXTURES / "trs-chitchat-001.json")
    first = classify(fixture, policy=policy); assert first == classify(fixture, policy=policy)
    assert tuple(first.probabilities) == ROUTES
    assert all(value >= 0 for value in first.probabilities.values())
    assert math.isclose(sum(first.probabilities.values()), 1.0, abs_tol=1e-9)
    assert (first.selected_label, first.route, first.confidence) == ("chitchat", "chitchat", first.probabilities["chitchat"])
    assert first.risk == "low" and first.thresholds_version == policy.thresholds_version
    assert first.input_hash == scoped_hash(fixture.transcript, scope="fixture-input", schema_version=fixture.schema_version)
    assert not hasattr(first, "transcript")

@pytest.mark.parametrize(
    ("calibration", "risk", "selected", "route"),
    [
        (Calibration(0.900000, 0.09, 0.01), "low", "chitchat", "chitchat"),
        (Calibration(0.899999, 0.09, 0.010001), "low", "chitchat", "unclear"),
        (Calibration(0.09, 0.800000, 0.11), "low", "needs_tools", "needs_tools"),
        (Calibration(0.09, 0.799999, 0.110001), "low", "needs_tools", "unclear"),
        (Calibration(0.99, 0.005, 0.005), "high", "chitchat", "unclear"),
        (Calibration(-0.01, 0.50, 0.50), "low", "unclear", "unclear"),
        (Calibration(0.50, 0.50, 0.00), "low", "unclear", "unclear"),
        (Calibration(0.34, 0.33, 0.33), "unknown", "unclear", "unclear"),
    ],
)
def test_threshold_boundaries_and_invalid_calibration_fail_safe(calibration: Calibration, risk: str, selected: str, route: str) -> None:
    outcome = apply_policy(calibration, risk, policy=load_threshold_policy(POLICY_PATH))
    assert outcome.selected_label == selected and outcome.route == route
    if outcome.route != outcome.selected_label:
        assert outcome.fallback_reason in {"threshold", "safety", "invalid"}
def test_safety_and_unevaluable_consent_force_guarded_unclear() -> None:
    policy = load_threshold_policy(POLICY_PATH)
    loaded = load_fixture(FIXTURES / "trs-tools-001.json")
    unsafe = classify(replace(loaded, transcript="Please send the private report now"), policy=policy)
    no_reasoner_consent = classify(replace(loaded, consent=loaded.consent._replace(reasoner=False)), policy=policy)
    no_routing_consent = classify(replace(loaded, consent=loaded.consent._replace(routing=False)), policy=policy)
    assert unsafe.route == "unclear" and unsafe.risk == "high"
    assert unsafe.selected_label != "unclear" and unsafe.probabilities[unsafe.selected_label] >= 0.80
    assert all(decision.route == "unclear" for decision in (unsafe, no_reasoner_consent, no_routing_consent))
    assert no_reasoner_consent.risk == no_routing_consent.risk == "unevaluable"

def test_complete_corpus_report_metrics_and_boundary_sensitivity() -> None:
    corpus = load_fixture_corpus(PATHS)
    policy = load_threshold_policy(POLICY_PATH)
    report = evaluate_routing(corpus, policy=policy)
    assert report.total == 18 and report.correct == 18 and report.accuracy == 1.0
    balanced = {"chitchat": 6, "needs_tools": 6, "unclear": 6}
    assert report.expected_counts == report.selected_counts == balanced
    assert all(metric.denominator == 6 and metric.accuracy == 1.0 for metric in report.per_route.values())
    assert report.missed_work == report.false_wakeups == (0, 6, 0.0)
    assert report.unclear_precision == (6, 6, 1.0)
    assert report.confusion == {expected: {selected: int(expected == selected) * 6 for selected in ROUTES} for expected in ROUTES}
    assert report.boundary_sensitivity["chitchat"] == BoundarySensitivity(6, 0, 0, 6)
    assert report.boundary_sensitivity["needs_tools"] == BoundarySensitivity(6, 2, 0, 6)
    assert report.fixture_set_version == "slice0-2026-09-19"
    assert report.thresholds_version == policy.thresholds_version and report.policy_hash == policy.policy_hash
    assert report.decision == "pass"
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT.*Z", report.run_started_utc)
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT.*Z", report.run_ended_utc)
    assert report.mismatches == () and len(report.boundary_cases) == 12 and len(report.decisions) == 18
def test_route_events_are_private_hash_scoped_and_chain_verified() -> None:
    corpus = load_fixture_corpus(PATHS)
    policy = load_threshold_policy(POLICY_PATH)
    ledger = EventLedger.empty()
    events = []
    for fixture in corpus.fixtures:
        decision = classify(fixture, policy=policy)
        event = route_event(fixture, decision, event_id=ledger.event_count + 1,
                            prior_event_id=ledger.events[-1].event_id if ledger.events else None, prior_event_hash=ledger.head_hash)
        receipt = append_event(ledger, event)
        ledger = receipt.ledger
        events.append(receipt.event)

    verification = verify_ledger(ledger)
    assert verification.valid_chain and verification.event_count == 18
    event_bytes = b"".join(canonical_event_bytes(event) for event in events)
    assert all((event.calibration_version, event.thresholds_version, event.thresholds_hash) == (CALIBRATION_VERSION, policy.thresholds_version, policy.policy_hash) for event in events)
    assert all(event.input_hash == scoped_hash(fixture.transcript, scope="fixture-input", schema_version=fixture.schema_version)
               for event, fixture in zip(events, corpus.fixtures, strict=True))
    assert all(fixture.transcript.encode() not in event_bytes for fixture in corpus.fixtures)
    assert b'"transcript"' not in event_bytes and b'"raw_content"' not in event_bytes
def test_routing_module_has_no_reasoner_or_network_boundary() -> None:
    source = Path(__import__("talk_reasoner.routing", fromlist=[""]).__file__).read_text(encoding="utf-8")
    assert not [name for name in ("requests", "httpx", "aiohttp", "socket", "redis", "psycopg", "reasoner", "job", "tool") if re.search(rf"(?m)^\s*(import|from)\s+{name}\b", source)]
