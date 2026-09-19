from __future__ import annotations

import base64
import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, NamedTuple, Never

FIXTURE_SCHEMA_VERSION = "slice0-fixture-v1"
CONTEXT_SCHEMA_VERSION = "slice0-context-v1"
EVENT_SCHEMA_VERSION = "slice0-event-v1"
ROUTES = frozenset(("chitchat", "needs_tools", "unclear"))
VALIDATIONS = frozenset(("accepted", "rejected", "clarification_required"))
TERMINAL_STATES = frozenset(("rendered", "blocked", "failed", "canceled", "downgraded"))
EVENT_TYPES = frozenset(("fixture", "route", "job", "proposal", "action", "validation", "policy", "confirmation", "lifecycle", "state", "response", "report", "integrity"))
TERMINAL_EVENT_STATUSES = frozenset(("completed", "canceled", "downgraded", "failed", "rendered"))
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
VERSION_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
CREDENTIAL_PATTERNS = (re.compile(r"(?i)(api[_-]?key|password|passwd|secret|bearer\s+|access[_-]?token|authorization)"), re.compile(r"AKIA[0-9A-Z]{16}"), re.compile(r"sk-[A-Za-z0-9_-]{16,}"))


class ContractError(ValueError):
    """A fixture or ledger value violates a local contract."""


class Consent(NamedTuple):
    routing: bool; reasoner: bool; high_risk_action: bool
class BoundedContext(NamedTuple):
    schema_version: str; max_entries: int; state: Mapping[str, Any]
class ExpectedOutcome(NamedTuple):
    route: str; validation: str; terminal_state: str
class TimingPolicy(NamedTuple):
    max_latency_ms: int; interrupt_after_ms: int | None = None
class Provenance(NamedTuple):
    fixture_set_version: str; source: str; review_status: str


@dataclass(frozen=True, slots=True)
class Fixture:
    schema_version: str; fixture_id: str; fixture_version: str; session_id: str; turn_id: str
    consent: Consent; transcript: str; bounded_context: BoundedContext; expected: ExpectedOutcome
    provenance: Provenance; test_purpose: str
    timing: TimingPolicy | None = None


class FixtureCorpus(NamedTuple):
    schema_version: str
    fixtures: tuple[Fixture, ...]


@dataclass(frozen=True, slots=True)
class LedgerEvent:
    schema_version: str; event_type: str; event_version: str; event_id: int
    session_id: str; turn_id: str; turn_epoch: int; input_hash: str
    content_length: int; media_type: str; consent_version: str; policy_version: str
    status: str; rejection_reason: str | None; latency_ms: int
    action_hash: str | None; prior_event_id: int | None; prior_event_hash: str | None
    event_chain_hash: str | None
    job_id: str | None = None

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EventLedger:
    events: tuple[LedgerEvent, ...]
    head_hash: str | None = None

    def __post_init__(self) -> None:
        if self.head_hash is None and self.events: object.__setattr__(self, "head_hash", self.events[-1].event_chain_hash)

    @classmethod
    def empty(cls) -> EventLedger:
        return cls(events=(), head_hash=None)

    @property
    def event_count(self) -> int:
        return len(self.events)


class AppendReceipt(NamedTuple):
    ledger: EventLedger; event: LedgerEvent; chain_hash: str


@dataclass(frozen=True, slots=True)
class LedgerVerification:
    valid_chain: bool; event_count: int; gaps: tuple[int, ...]
    invalid_prior_hashes: tuple[int, ...]; duplicate_terminal_states: tuple[str, ...]
    mutations: tuple[int, ...]


def _fail(path: Path, field: str, detail: str) -> Never:
    raise ContractError(f"{path}: invalid {field}: {detail}")


def _read_object(path: Path) -> dict[str, Any]:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ContractError(f"{path}: invalid JSON object: duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError):
        _fail(path, "JSON", "unreadable or malformed JSON")
    if not isinstance(value, dict):
        _fail(path, "JSON object", "root must be an object")
    return value


def _object(path: Path, value: Any, field: str, required: set[str], optional: set[str] = frozenset()) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(path, field, "must be an object")
    if missing := required - set(value):
        _fail(path, field, f"missing {sorted(missing)}")
    if unknown := set(value) - required - optional:
        _fail(path, field, f"unknown {sorted(unknown)}")
    return value


def _text(path: Path, value: Any, field: str, *, minimum: int = 1, maximum: int = 512) -> str:
    if not isinstance(value, str) or not minimum <= len(value) <= maximum:
        _fail(path, field, f"must be a string of length {minimum}..{maximum}")
    return value


def _identifier(path: Path, value: Any, field: str) -> str:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        _fail(path, field, "must match a lowercase deterministic ID pattern")
    return value


def _version(path: Path, value: Any, field: str, *, semver: bool = False) -> str:
    if not isinstance(value, str) or not (SEMVER_PATTERN if semver else VERSION_PATTERN).fullmatch(value):
        _fail(path, field, "invalid version format")
    return value


def _boolean(path: Path, value: Any, field: str) -> bool:
    if type(value) is not bool:
        _fail(path, field, "must be a boolean")
    return value


def _integer(path: Path, value: Any, field: str, *, minimum: int = 0, maximum: int = 2_147_483_647) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        _fail(path, field, f"must be an integer in {minimum}..{maximum}")
    return value


def _contains_credentials(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if isinstance(key, str) and (found := _contains_credentials(key)): return found
            if (found := _contains_credentials(child)): return found
    elif isinstance(value, str):
        for pattern in CREDENTIAL_PATTERNS:
            if pattern.search(value):
                return "redacted credential-like value"
    return None


def _bounded_state(path: Path, value: Any, max_entries: int) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        _fail(path, "bounded_context.state", "must be an object")
    state = value
    if len(state) > max_entries:
        _fail(path, "bounded_context.state", f"unbounded context: {len(state)} entries exceeds {max_entries}")
    if (found := _contains_credentials(state)):
        _fail(path, "bounded_context.state", f"credential pattern detected: {found!r}")
    for key, child in state.items():
        if not isinstance(key, str) or not key or len(key) > 64: _fail(path, "bounded_context.state", "state keys must be bounded strings")
        if isinstance(child, (dict, list)):
            if len(child) > 4: _fail(path, "bounded_context.state", "nested containers may contain at most four values")
            for grandchild in child.values() if isinstance(child, dict) else child:
                if isinstance(grandchild, (dict, list)): _fail(path, "bounded_context.state", "state depth is limited to two levels")
        elif isinstance(child, str) and len(child) > 256: _fail(path, "bounded_context.state", "state string values must be at most 256 characters")
    return MappingProxyType(state)


def load_fixture(path: Path) -> Fixture:
    """Parse and strictly validate one versioned JSON fixture."""
    record = _read_object(path)
    required = {"schema_version", "fixture_id", "fixture_version", "session_id", "turn_id", "consent", "transcript", "bounded_context", "expected", "provenance", "test_purpose"}
    _object(path, record, "fixture", required, {"timing"})
    schema = _text(path, record["schema_version"], "schema_version")
    if schema != FIXTURE_SCHEMA_VERSION:
        _fail(path, "schema_version", f"unsupported schema_version {schema!r}; expected {FIXTURE_SCHEMA_VERSION!r}")
    if (found := _contains_credentials(record)):
        _fail(path, "credential", f"credential pattern detected: {found!r}")
    consent_data = _object(path, record["consent"], "consent", {"routing", "reasoner", "high_risk_action"})
    consent = Consent(*(_boolean(path, consent_data[field], f"consent.{field}") for field in ("routing", "reasoner", "high_risk_action")))
    context_data = _object(path, record["bounded_context"], "bounded_context", {"schema_version", "max_entries", "state"})
    context_schema = _version(path, context_data["schema_version"], "bounded_context.schema_version")
    if context_schema != CONTEXT_SCHEMA_VERSION:
        _fail(path, "bounded_context.schema_version", f"expected {CONTEXT_SCHEMA_VERSION!r}")
    max_entries = _integer(path, context_data["max_entries"], "bounded_context.max_entries", minimum=1, maximum=8)
    context = BoundedContext(context_schema, max_entries, _bounded_state(path, context_data["state"], max_entries))
    expected_data = _object(path, record["expected"], "expected", {"route", "validation", "terminal_state"})
    expected = ExpectedOutcome(*(_text(path, expected_data[field], f"expected.{field}") for field in ("route", "validation", "terminal_state")))
    for value, field, allowed in ((expected.route, "route", ROUTES), (expected.validation, "validation", VALIDATIONS), (expected.terminal_state, "terminal_state", TERMINAL_STATES)):
        if value not in allowed:
            _fail(path, f"expected.{field}", f"must be one of {sorted(allowed)}")
    timing: TimingPolicy | None = None
    if "timing" in record:
        timing_data = _object(path, record["timing"], "timing", {"max_latency_ms"}, {"interrupt_after_ms"})
        interrupt = timing_data.get("interrupt_after_ms")
        timing = TimingPolicy(
            _integer(path, timing_data["max_latency_ms"], "timing.max_latency_ms", minimum=1),
            None if interrupt is None else _integer(path, interrupt, "timing.interrupt_after_ms", minimum=1),
        )
    provenance_data = _object(path, record["provenance"], "provenance", {"fixture_set_version", "source", "review_status"})
    provenance = Provenance(
        _version(path, provenance_data["fixture_set_version"], "provenance.fixture_set_version"),
        _text(path, provenance_data["source"], "provenance.source", maximum=64),
        _version(path, provenance_data["review_status"], "provenance.review_status"),
    )
    if provenance.source != "synthetic-local":
        _fail(path, "provenance.source", "Slice 0 fixtures must be synthetic and local")
    return Fixture(schema, _identifier(path, record["fixture_id"], "fixture_id"),
                   _version(path, record["fixture_version"], "fixture_version", semver=True),
                   _identifier(path, record["session_id"], "session_id"), _identifier(path, record["turn_id"], "turn_id"),
                   consent, _text(path, record["transcript"], "transcript", maximum=256), context, expected, provenance,
                   _text(path, record["test_purpose"], "test_purpose", minimum=12, maximum=256), timing)


def load_fixture_corpus(paths: Iterable[Path]) -> FixtureCorpus:
    """Load, deduplicate, order, and route-balance a complete fixture corpus."""
    loaded: list[Fixture] = []
    fixture_ids: set[str] = set()
    for path in paths:
        fixture = load_fixture(path)
        if fixture.fixture_id in fixture_ids:
            raise ContractError(f"duplicate fixture_id {fixture.fixture_id!r} in corpus")
        fixture_ids.add(fixture.fixture_id)
        loaded.append(fixture)
    counts = {route: sum(item.expected.route == route for item in loaded) for route in ROUTES}
    if len(loaded) < 18 or any(counts[route] < 6 for route in ROUTES):
        raise ContractError(f"incomplete fixture corpus: expected at least 6 per route, got {counts}")
    return FixtureCorpus(FIXTURE_SCHEMA_VERSION, tuple(sorted(loaded, key=lambda item: item.fixture_id)))


def scoped_hash(content: str | bytes, *, scope: str, schema_version: str) -> str:
    """Return a stable SHA-256 over canonical metadata plus the supplied content."""
    if not scope or not schema_version:
        raise ContractError("scope and schema_version must be non-empty")
    try:
        normalized, encoding = (content.decode("utf-8"), "utf8") if isinstance(content, bytes) else (content, "utf8")
    except UnicodeDecodeError:
        normalized, encoding = base64.b64encode(content).decode("ascii"), "base64"
    envelope = {"content": normalized, "content_encoding": encoding, "schema_version": schema_version, "scope": scope}
    canonical = json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def canonical_event_bytes(event: LedgerEvent) -> bytes:
    """Serialize the chain-independent event body to deterministic JSON bytes."""
    body = {key: value for key, value in event.to_mapping().items() if key != "event_chain_hash"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _event_error(field: str, detail: str) -> Never:
    raise ContractError(f"invalid LedgerEvent.{field}: {detail}")


def _validate_event(event: LedgerEvent) -> None:
    checks = (
        (event.schema_version == EVENT_SCHEMA_VERSION, "schema_version", f"expected {EVENT_SCHEMA_VERSION!r}"),
        (event.event_type in EVENT_TYPES, "event_type", f"must be one of {sorted(EVENT_TYPES)}"),
        (bool(SEMVER_PATTERN.fullmatch(event.event_version)), "event_version", "must use semantic versioning"),
        (type(event.event_id) is int and event.event_id > 0, "event_id", "must be a positive integer"),
        (event.event_type not in {"action", "proposal", "lifecycle"} or event.job_id is not None,
         "job_id", f"required for {event.event_type} events"),
        (type(event.turn_epoch) is int and event.turn_epoch >= 0, "turn_epoch", "must be non-negative"),
        (bool(HASH_PATTERN.fullmatch(event.input_hash)), "input_hash", "must link to a scoped input hash"),
        (event.event_type != "action" or event.action_hash is not None, "action_hash", "required for action events"),
        (event.action_hash is None or bool(HASH_PATTERN.fullmatch(event.action_hash)), "action_hash", "must be SHA-256 or None"),
        (type(event.content_length) is int and event.content_length >= 0, "content_length", "must be non-negative"),
        (isinstance(event.media_type, str) and bool(re.fullmatch(r"[a-z0-9]+/[a-z0-9.+-]+", event.media_type)),
         "media_type", "must be bounded"),
        (isinstance(event.status, str) and bool(VERSION_PATTERN.fullmatch(event.status)), "status", "must be bounded"),
        (event.rejection_reason is None or bool(event.rejection_reason), "rejection_reason", "must be non-empty or None"),
        (type(event.latency_ms) is int and event.latency_ms >= 0, "latency_ms", "must be non-negative"),
        (event.prior_event_id is None or (type(event.prior_event_id) is int and event.prior_event_id > 0),
         "prior_event_id", "must be positive or None"),
        (event.prior_event_hash is None or bool(HASH_PATTERN.fullmatch(event.prior_event_hash)),
         "prior_event_hash", "must be SHA-256 or None"),
    )
    for valid, field, detail in checks:
        if not valid:
            _event_error(field, detail)
    for field in ("session_id", "turn_id", "job_id", "consent_version", "policy_version", "event_chain_hash"):
        value = getattr(event, field)
        valid = value is None or (isinstance(value, str) and (
            ID_PATTERN.fullmatch(value) if field in {"session_id", "turn_id", "job_id"}
            else VERSION_PATTERN.fullmatch(value) if field in {"consent_version", "policy_version"}
            else HASH_PATTERN.fullmatch(value)
        ))
        if not valid:
            _event_error(field, "must be a bounded identifier/version/hash or None")


def append_event(ledger: EventLedger, event: LedgerEvent) -> AppendReceipt:
    """Validate and immutably append one event, returning the extended ledger."""
    _validate_event(event)
    expected_id = ledger.event_count + 1
    if event.event_id != expected_id:
        _event_error("event_id", f"must be {expected_id}")
    if event.event_chain_hash is not None:
        _event_error("event_chain_hash", "must be unset before appending")
    if expected_id == 1:
        if event.prior_event_id is not None or event.prior_event_hash is not None:
            _event_error("prior_event_id", "the first event cannot have prior-chain metadata")
    else:
        tail = ledger.events[-1]
        if event.prior_event_id != tail.event_id:
            _event_error("prior_event_id", f"must be {tail.event_id}")
        if event.prior_event_hash != tail.event_chain_hash:
            _event_error("prior_event_hash", "does not match ledger head")
    chain_hash = scoped_hash(canonical_event_bytes(event), scope="event-chain", schema_version=event.schema_version)
    stored = replace(event, event_chain_hash=chain_hash)
    updated = EventLedger(ledger.events + (stored,), chain_hash)
    return AppendReceipt(updated, stored, chain_hash)


def verify_ledger(ledger: EventLedger) -> LedgerVerification:
    """Verify order, links, terminal uniqueness, stored hashes, and mutations."""
    gaps: list[int] = []
    invalid_prior_hashes: list[int] = []
    mutations: list[int] = []
    terminal: dict[tuple[str, str, str, str], int] = {}
    duplicate_terminal_states: list[str] = []
    previous: LedgerEvent | None = None
    actual_ids = {event.event_id for event in ledger.events}
    gaps.extend(expected_id for expected_id in range(1, len(ledger.events) + 1) if expected_id not in actual_ids)
    for expected_id, event in enumerate(ledger.events, start=1):
        expected_prior_id = None if expected_id == 1 else expected_id - 1
        expected_prior_hash = None if previous is None else previous.event_chain_hash
        if event.prior_event_id != expected_prior_id or event.prior_event_hash != expected_prior_hash:
            invalid_prior_hashes.append(event.event_id)
        expected_hash = scoped_hash(canonical_event_bytes(event), scope="event-chain", schema_version=event.schema_version)
        if event.event_chain_hash != expected_hash:
            mutations.append(event.event_id)
        if event.status in TERMINAL_EVENT_STATUSES:
            key = (event.session_id, event.turn_id, event.job_id or "", event.status)
            if key in terminal:
                duplicate_terminal_states.append(f"event:{event.event_id}:{event.status}")
            terminal[key] = event.event_id
        previous = event
    if ledger.events and ledger.head_hash != ledger.events[-1].event_chain_hash:
        last_id = ledger.events[-1].event_id
        if last_id not in mutations:
            mutations.append(last_id)
    valid = not any((gaps, invalid_prior_hashes, duplicate_terminal_states, mutations))
    return LedgerVerification(valid, len(ledger.events), tuple(gaps), tuple(invalid_prior_hashes),
                              tuple(duplicate_terminal_states), tuple(mutations))
