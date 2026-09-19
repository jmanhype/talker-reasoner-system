from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, NamedTuple

from talk_reasoner.contracts import EVENT_SCHEMA_VERSION, Fixture, FixtureCorpus, LedgerEvent, scoped_hash

ROUTE_LABELS = ("chitchat", "needs_tools", "unclear")
POLICY_SCHEMA_VERSION = "slice0-routing-policy-v1"
CALIBRATION_VERSION = "slice0-local-v1"
REPORT_SCHEMA_VERSION = "slice0-routing-report-v1"
RoutingRisk = Literal["low", "medium", "high", "unevaluable"]
VALID_RISKS = frozenset(("low", "medium", "high", "unevaluable"))

class RoutingPolicyError(ValueError):
    """A routing policy or calibration value cannot be safely evaluated."""


class ThresholdPolicy(NamedTuple):
    schema_version: str; thresholds_version: str
    chitchat_confidence_min: float; needs_tools_confidence_min: float
    invalid_fallback_route: str; safety_fallback_route: str; policy_hash: str

class Calibration(NamedTuple):
    chitchat: float; needs_tools: float; unclear: float
INVALID_CALIBRATION = Calibration(0.0, 0.0, 1.0)

class PolicySelection(NamedTuple):
    selected_label: str; confidence: float; route: str
    fallback_reason: Literal[None, "threshold", "safety", "invalid"]

@dataclass(frozen=True, slots=True)
class RoutingDecision:
    schema_version: str; fixture_id: str; expected_route: str
    probabilities: MappingProxyType[str, float]; selected_label: str
    confidence: float; route: str; risk: RoutingRisk
    thresholds_version: str; policy_hash: str; input_hash: str
    fallback_reason: Literal[None, "threshold", "safety", "invalid"]
class RouteMetric(NamedTuple):
    label: str; denominator: int; selected: int; correct: int; accuracy: float
class BoundarySensitivity(NamedTuple):
    at: int; above: int; below: int; within_0_01: int

@dataclass(frozen=True, slots=True)
class RoutingReport:
    schema_version: str; fixture_set_version: str; thresholds_version: str
    policy_hash: str; total: int; correct: int
    accuracy: float; expected_counts: MappingProxyType[str, int]; selected_counts: MappingProxyType[str, int]
    per_route: MappingProxyType[str, RouteMetric]; confusion: MappingProxyType[str, MappingProxyType[str, int]]
    missed_work: tuple[int, int, float]; false_wakeups: tuple[int, int, float]
    unclear_precision: tuple[int, int, float]; boundary_sensitivity: MappingProxyType[str, BoundarySensitivity]
    boundary_cases: tuple[RoutingDecision, ...]; mismatches: tuple[RoutingDecision, ...]
    decisions: tuple[RoutingDecision, ...]; run_started_utc: str; run_ended_utc: str
    decision: Literal["pass", "hold"]


@dataclass(frozen=True, slots=True)
class RouteLedgerEvent(LedgerEvent):
    calibration_version: str | None = None; thresholds_version: str | None = None; thresholds_hash: str | None = None

def _policy_error(detail: str) -> None:
    raise RoutingPolicyError(f"invalid routing policy: {detail}")


def load_threshold_policy(path: Path) -> ThresholdPolicy:
    """Parse, validate, and hash one local three-route threshold policy."""
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result: raise RoutingPolicyError(f"{path}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        record = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RoutingPolicyError(f"{path}: unreadable policy JSON: {error}") from error
    required = {"schema_version", "thresholds_version", "chitchat_confidence_min", "needs_tools_confidence_min", "invalid_fallback_route", "safety_fallback_route"}
    if not isinstance(record, dict) or set(record) != required:
        _policy_error(f"fields must be exactly {sorted(required)}")
    if record["schema_version"] != POLICY_SCHEMA_VERSION or record["thresholds_version"] != "slice0-v1":
        _policy_error("unsupported policy or thresholds version")
    chitchat_min, tools_min = record["chitchat_confidence_min"], record["needs_tools_confidence_min"]
    for name, value, minimum in (("chitchat_confidence_min", chitchat_min, 0.90), ("needs_tools_confidence_min", tools_min, 0.80)):
        if type(value) not in (int, float) or not math.isfinite(value) or not minimum <= value <= 1.0:
            _policy_error(f"{name} must be finite and in {minimum:.2f}..1.00")
    if tools_min > chitchat_min:
        _policy_error("needs_tools threshold cannot exceed the chitchat threshold")
    if record["invalid_fallback_route"] != "unclear" or record["safety_fallback_route"] != "unclear":
        _policy_error("both policy fallbacks must be unclear")
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return ThresholdPolicy(record["schema_version"], record["thresholds_version"], float(chitchat_min), float(tools_min),
                           record["invalid_fallback_route"], record["safety_fallback_route"], hashlib.sha256(canonical).hexdigest())

def apply_policy(probabilities: Calibration, risk: str, *, policy: ThresholdPolicy) -> PolicySelection:
    """Apply safety and calibrated thresholds without exposing a fourth route."""
    values = probabilities._asdict()
    valid = len(values) == 3 and all(type(value) in (int, float) and math.isfinite(value) and value >= 0 for value in values.values()) and math.isclose(sum(values.values()), 1.0, abs_tol=1e-9)
    if not valid or risk not in VALID_RISKS:
        return PolicySelection("unclear", 1.0, policy.invalid_fallback_route, "invalid")
    winners = [label for label in ROUTE_LABELS if values[label] == max(values.values())]
    if len(winners) != 1: return PolicySelection("unclear", 1.0, policy.invalid_fallback_route, "invalid")
    selected_label = winners[0]; confidence = float(values[selected_label])
    if risk in {"high", "unevaluable"}:
        return PolicySelection(selected_label, confidence, policy.safety_fallback_route, "safety")
    threshold = {"chitchat": policy.chitchat_confidence_min, "needs_tools": policy.needs_tools_confidence_min}.get(selected_label, 0.0)
    if confidence < threshold:
        return PolicySelection(selected_label, confidence, policy.invalid_fallback_route, "threshold")
    return PolicySelection(selected_label, confidence, selected_label, None)
TOOL_PATTERN = re.compile(r"(?i)\b(save|search|read|summarize|add|compare|setting|checklist|coverage|counts?)\b")
CHITCHAT_PATTERN = re.compile(r"(?i)\b(good morning|thanks|wait|sounds|like|okay|revisit|explanation|backchannel)\b")
AMBIGUOUS_PATTERN = re.compile(r"(?i)\b(handle|usual|maybe|perhaps|earlier|other|fix|set up|it|that|they)\b")
UNSAFE_PATTERN = re.compile(r"(?i)\b(send|pay|payment|delete|remove|email|message|credential|password|secret|code)\b")
UNRESOLVED_STATE = re.compile(r"(?i)unresolved|mixed|missing")
def _calibrate(fixture: Fixture) -> tuple[Calibration, RoutingRisk]:
    text = fixture.transcript.lower()
    state_text = " ".join(str(value).lower() for value in fixture.bounded_context.state.values()).strip()
    wants_tools = bool(TOOL_PATTERN.search(text) or TOOL_PATTERN.search(state_text))
    ambiguous_keys = {"referent", "intent", "target", "action", "file", "configuration"}
    unsafe = bool(UNSAFE_PATTERN.search(text))
    ambiguous = bool(AMBIGUOUS_PATTERN.search(text) and (UNRESOLVED_STATE.search(state_text) or any(key in ambiguous_keys for key in fixture.bounded_context.state)))
    if unsafe:
        return Calibration(0.02, 0.96, 0.02), "high"
    if not fixture.consent.routing or (wants_tools and not fixture.consent.reasoner):
        return Calibration(0.02, 0.96, 0.02), "unevaluable"
    if ambiguous:
        return Calibration(0.01, 0.03, 0.96), "medium"
    if wants_tools and fixture.consent.reasoner:
        return Calibration(0.04, 0.80, 0.16), "low"
    if CHITCHAT_PATTERN.search(text):
        return Calibration(0.90, 0.05, 0.05), "low"
    return INVALID_CALIBRATION, "low"


def classify(fixture: Fixture, *, policy: ThresholdPolicy) -> RoutingDecision:
    """Deterministically score one typed fixture and apply the local policy."""
    calibration, risk = _calibrate(fixture)
    selection = apply_policy(calibration, risk, policy=policy)
    probabilities = calibration if selection.fallback_reason != "invalid" else INVALID_CALIBRATION
    return RoutingDecision(
        REPORT_SCHEMA_VERSION, fixture.fixture_id, fixture.expected.route, MappingProxyType(probabilities._asdict()),
        selection.selected_label, selection.confidence, selection.route, risk,
        policy.thresholds_version, policy.policy_hash,
        scoped_hash(fixture.transcript, scope="fixture-input", schema_version=fixture.schema_version),
        selection.fallback_reason,
    )
def _rate(count: int, denominator: int) -> float:
    return count / denominator if denominator else 0.0
def evaluate_routing(corpus: FixtureCorpus, *, policy: ThresholdPolicy) -> RoutingReport:
    """Evaluate every fixture in deterministic order with exact route denominators."""
    started = datetime.now(timezone.utc)
    decisions = tuple(classify(fixture, policy=policy) for fixture in corpus.fixtures)
    ended = datetime.now(timezone.utc)
    expected = {label: sum(item.expected.route == label for item in corpus.fixtures) for label in ROUTE_LABELS}
    selected = {label: sum(decision.route == label for decision in decisions) for label in ROUTE_LABELS}
    confusion = {
        expected_label: MappingProxyType({
            selected_label: sum(item.expected.route == expected_label and decision.route == selected_label
                                for item, decision in zip(corpus.fixtures, decisions, strict=True))
            for selected_label in ROUTE_LABELS
        }) for expected_label in ROUTE_LABELS
    }
    metrics = {
        label: RouteMetric(label, expected[label], selected[label], confusion[label][label], _rate(confusion[label][label], expected[label]))
        for label in ROUTE_LABELS
    }
    correct = sum(confusion[label][label] for label in ROUTE_LABELS)
    missed = confusion["needs_tools"]["chitchat"] + confusion["needs_tools"]["unclear"]
    false_wakeups = confusion["chitchat"]["needs_tools"]
    boundaries: dict[str, list[int]] = {label: [0, 0, 0, 0] for label in ("chitchat", "needs_tools")}
    thresholds = {"chitchat": policy.chitchat_confidence_min, "needs_tools": policy.needs_tools_confidence_min}
    boundary_cases: list[RoutingDecision] = []
    mismatches = tuple(decision for decision in decisions if decision.route != decision.expected_route)
    for item, decision in zip(corpus.fixtures, decisions, strict=True):
        if decision.selected_label not in thresholds: continue
        threshold = thresholds[decision.selected_label]
        distance = decision.confidence - threshold
        boundary = boundaries[decision.selected_label]
        boundary[0 if distance == 0 else 1 if distance > 0 else 2] += 1
        if abs(distance) <= 0.01: boundary[3] += 1
        if abs(distance) <= 0.01 or decision.fallback_reason == "threshold":
            boundary_cases.append(decision)
    versions = {item.provenance.fixture_set_version for item in corpus.fixtures}
    if len(versions) != 1:
        raise RoutingPolicyError("corpus fixture_set_version must be uniform")
    passed = correct == len(corpus.fixtures) and missed == 0 and false_wakeups == 0
    return RoutingReport(
        REPORT_SCHEMA_VERSION, versions.pop(), policy.thresholds_version, policy.policy_hash,
        len(corpus.fixtures), correct, _rate(correct, len(corpus.fixtures)),
        MappingProxyType(expected), MappingProxyType(selected), MappingProxyType(metrics), MappingProxyType(confusion),
        (missed, expected["needs_tools"], _rate(missed, expected["needs_tools"])),
        (false_wakeups, expected["chitchat"], _rate(false_wakeups, expected["chitchat"])),
        (confusion["unclear"]["unclear"], selected["unclear"], _rate(confusion["unclear"]["unclear"], selected["unclear"])),
        MappingProxyType({label: BoundarySensitivity(*values) for label, values in boundaries.items()}),
        tuple(boundary_cases), mismatches,
        decisions, started.isoformat().replace("+00:00", "Z"), ended.isoformat().replace("+00:00", "Z"),
        "pass" if passed else "hold",
    )

def route_event(fixture: Fixture, decision: RoutingDecision, *, event_id: int, prior_event_id: int | None = None, prior_event_hash: str | None = None) -> RouteLedgerEvent:
    """Build a hash-scoped route event carrying only calibration metadata."""
    return RouteLedgerEvent(
        EVENT_SCHEMA_VERSION, "route", "1.0.0", event_id, fixture.session_id, fixture.turn_id, 0,
        decision.input_hash, len(fixture.transcript.encode("utf-8")), "text/plain", "consent-v1",
        decision.thresholds_version, decision.route, decision.fallback_reason, 0, None,
        prior_event_id, prior_event_hash, None, None, CALIBRATION_VERSION,
        decision.thresholds_version, decision.policy_hash,
    )
