from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, NamedTuple

from talk_reasoner.contracts import EVENT_SCHEMA_VERSION, LedgerEvent, scoped_hash

CATALOG_PATH = Path(__file__).parents[1] / "config" / "actions" / "slice0-v1.json"
CATALOG_SCHEMA_VERSION = "slice0-action-catalog-v1"; ACTION_SCHEMA_VERSION = "slice0-action-v1"; PROPOSAL_SCHEMA_VERSION = "slice0-proposal-v1"
POLICY_SCHEMA_VERSION = "slice0-action-policy-v1"; STATE_SCHEMA_VERSION = "state-v1"; PROVENANCE_SCHEMA_VERSION = "slice0-provenance-v1"
CONSENT_VERSION = "consent-v1"; CONFIRMATION_VERSION = "confirmation-v1"; FIXED_ACTIONS = frozenset(("search", "read_state", "write_state"))
EXPECTED_ARGUMENTS = {"search": {"query", "limit", "terms"}, "read_state": {"key", "terms"}, "write_state": {"key", "value", "terms"}}
POLICY_OUTCOMES = ("allowed_without_confirmation", "confirmation_required", "rejected"); frozen = dataclass(frozen=True, slots=True)
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ActionPolicyError(ValueError):
    """A fixed action catalog or policy definition cannot be safely evaluated."""


_REJECTION_VALUES = tuple(f"slice0-v1:{name}" for name in ("unknown_action", "malformed_type", "extra_argument", "out_of_range", "disallowed_state_key", "missing_justification", "missing_provenance", "consent_mismatch", "expired_state", "duplicate_non_idempotent", "policy_unevaluable", "confirmation_mismatch", "confirmation_expired"))
RejectionCode = Enum("RejectionCode", {value.rsplit(":", 1)[1].upper(): value for value in _REJECTION_VALUES})


class PolicyDefinition(NamedTuple):
    catalog_version: str; policy_version: str; confirmation_ttl_seconds: int; permissions: Mapping[str, Mapping[str, Any]]; risk_classes: Mapping[str, Mapping[str, Any]]; policy_hash: str
class ActionCatalog(NamedTuple):
    schema_version: str; catalog_version: str; actions: Mapping[str, Mapping[str, Any]]; policy: PolicyDefinition; rejection_codes: frozenset[RejectionCode]; catalog_hash: str
class ActionProvenance(NamedTuple):
    schema_version: str; fixture_set_version: str; source: str; review_status: str; input_hash: str
class ActionProposal(NamedTuple):
    schema_version: str; action_name: str; arguments: Mapping[str, Any]; job_id: str; session_id: str; turn_id: str; turn_epoch: int; user_id: str; subject: str; target: str; justification: str; provenance: ActionProvenance; catalog_version: str; policy_version: str
class ConsentRecord(NamedTuple):
    version: str; user_id: str; session_id: str; subject: str; scopes: frozenset[str]; granted_at: datetime; expires_at: datetime; policy_version: str
class FixtureState(NamedTuple):
    schema_version: str; session_id: str; state_version: int; expires_at: datetime; values: Mapping[str, Any]; seen_non_idempotent: frozenset[str]
class ConfirmationRecord(NamedTuple):
    version: str; explicit: bool; action_name: str; action_hash: str; arguments: Mapping[str, Any]; subject: str; target: str; user_id: str; session_id: str; policy_version: str; granted_at: datetime; expires_at: datetime
class ValidatedAction(NamedTuple):
    schema_version: str; action_name: str; canonical_arguments: Mapping[str, Any]; action_hash: str; definition: Mapping[str, Any]; job_id: str; session_id: str; turn_id: str; turn_epoch: int; user_id: str; subject: str; target: str; justification: str; consent_version: str; state_version: int; catalog_version: str; policy_version: str
class ValidationDecision(NamedTuple):
    proposal: ActionProposal; accepted: ValidatedAction | None; rejection_code: RejectionCode | None
class PolicyDecision(NamedTuple):
    outcome: str; rejection_code: RejectionCode | None
class ActionCase(NamedTuple):
    proposal: ActionProposal; catalog: ActionCatalog; consent: ConsentRecord; state: FixtureState; confirmation: ConfirmationRecord | None; expected_outcome: str; expected_rejection_code: RejectionCode | None
class ActionMismatch(NamedTuple):
    case: ActionCase; actual_outcome: str; actual_rejection_code: RejectionCode | None
class ActionPolicyReport(NamedTuple):
    schema_version: str; catalog_version: str; catalog_hash: str; policy_version: str; policy_hash: str; total: int; valid_count: int; invalid_count: int; valid_denominator: int; invalid_denominator: int; outcome_counts: Mapping[str, int]; outcome_denominators: Mapping[str, int]; rejection_counts: Mapping[str, int]; rejection_denominators: Mapping[str, int]; mismatches: tuple[ActionMismatch, ...]; decision: Literal["pass", "hold"]


@frozen
class ActionLedgerEvent(LedgerEvent):
    action_name: str | None = None; privacy_classification: str | None = None

def _error(detail: str) -> None: raise ActionPolicyError(detail)
def _canonical(value: Mapping[str, Any]) -> bytes: return json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
def action_hash(arguments: Mapping[str, Any], *, catalog_version: str) -> str:
    """Hash canonical arguments under the fixed catalog scope."""
    if not isinstance(arguments, Mapping) or not isinstance(catalog_version, str):
        _error("action arguments and catalog version must be typed")
    try:
        payload = _canonical(arguments)
    except (TypeError, ValueError) as error:
        raise ActionPolicyError("action arguments are not canonical JSON") from error
    return scoped_hash(payload, scope="action-arguments", schema_version=catalog_version)
def _unique(path: Path, pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, _ in pairs:
        if key in result: _error(f"{path}: duplicate JSON key {key!r}")
        result[key] = None
    return result | dict(pairs)
def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=lambda pairs: _unique(path, pairs))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ActionPolicyError(f"{path}: unreadable action catalog: {error}") from error
    if not isinstance(value, dict): _error(f"{path}: catalog root must be an object")
    return value
def _exact(value: Any, fields: set[str], label: str) -> dict[str, Any]: return value if isinstance(value, dict) and set(value) == fields else _error(f"{label} fields must be exactly {sorted(fields)}")
def _integer(value: Any, label: str, minimum: int = 0, maximum: int = 2_147_483_647) -> int:
    if type(value) is not int or not minimum <= value <= maximum: _error(f"{label} must be an integer in {minimum}..{maximum}")
    return value
def _boolean(value: Any, label: str) -> bool: return value if type(value) is bool else _error(f"{label} must be a boolean")
def _text(value: Any, label: str) -> str: return value if isinstance(value, str) and value else _error(f"{label} must be a non-empty string")
def _schema(value: Any, label: str) -> Mapping[str, Any]:
    fields = {"type", "optional", "min_length", "max_length", "minimum", "maximum", "min_items", "max_items", "items", "allowed_values"}
    if not isinstance(value, dict) or value.get("type") not in {"string", "integer", "array"} or set(value) - fields: _error(f"{label} must be a typed bounded schema")
    kind = value["type"]; lower, upper = {"string": ("min_length", "max_length"), "integer": ("minimum", "maximum"), "array": ("min_items", "max_items")}[kind]
    if (lower not in value or upper not in value) and "allowed_values" not in value: _error(f"{label} requires complete bounds")
    if lower in value and upper not in value: _error(f"{label}.{upper} is required when {lower} is present")
    if upper in value and lower not in value and "allowed_values" not in value: _error(f"{label}.{lower} is required when {upper} is present")
    if lower in value: _integer(value[lower], f"{label}.{lower}"); _integer(value[upper], f"{label}.{upper}")
    if type(value.get("optional", False)) is not bool or (kind == "array" and value.get("items") != "string"): _error(f"{label} optional/items type is invalid")
    if not isinstance(value.get("allowed_values", []), list) or not all(isinstance(item, str) for item in value.get("allowed_values", [])): _error(f"{label}.allowed_values must be strings")
    return value
def _codes(values: Any, label: str, complete: bool = False) -> frozenset[RejectionCode]:
    if not isinstance(values, list): _error(f"{label} must be an array")
    try: result = frozenset(RejectionCode(value) for value in values)
    except ValueError as error: raise ActionPolicyError(f"{label} contains an unsupported rejection code") from error
    if (complete and result != frozenset(RejectionCode)) or (not complete and not result): _error(f"{label} has an invalid stable-code set")
    return result
def load_action_catalog(path: Path) -> ActionCatalog:
    """Parse and fail closed on any unsafe or incomplete fixed action catalog."""
    record = _read(path)
    top = _exact(record, {"schema_version", "catalog_version", "policy_version", "confirmation_ttl_seconds", "rejection_codes", "permissions", "risk_classes", "actions"}, "catalog")
    if top["schema_version"] != CATALOG_SCHEMA_VERSION: _error("unsupported action catalog schema_version")
    if top["catalog_version"] != "slice0-v1": _error("unsupported catalog_version")
    if top["policy_version"] != "slice0-policy-v1": _error("unsupported policy_version")
    codes = _codes(top["rejection_codes"], "rejection_codes", complete=True)
    expected_permissions = {"local.read": {"allowed_risks": ["low"], "allowed_scopes": ["fixture-search", "fixture-state-read"]}, "local.write": {"allowed_risks": ["medium"], "allowed_scopes": ["fixture-state-write"]}}
    expected_risks = {"low": {"requires_confirmation": False, "allows_private": False, "allows_irreversible": False}, "medium": {"requires_confirmation": True, "allows_private": False, "allows_irreversible": False}}
    permissions, risks = top["permissions"], top["risk_classes"]
    if permissions != expected_permissions or risks != expected_risks: _error("permissions or risk_classes are not the fixed safe Slice-0 definitions")
    ttl = _integer(top["confirmation_ttl_seconds"], "confirmation_ttl_seconds", minimum=1, maximum=300)
    if not isinstance(top["actions"], list): _error("actions must be an array")
    actions: dict[str, Mapping[str, Any]] = {}
    action_fields = {"name", "schema_version", "permission", "risk", "privacy", "scope", "result_type", "idempotency", "reversible", "requires_provenance", "required_consent", "state_keys", "bounds", "argument_schema", "rejection_codes"}
    for raw in top["actions"]:
        data = _exact(raw, action_fields, "action"); name = _text(data["name"], "action.name")
        if name in actions or data["schema_version"] != ACTION_SCHEMA_VERSION: _error(f"duplicate action name or unsupported schema_version: {name}")
        permission, risk, scope = _text(data["permission"], "permission"), _text(data["risk"], "risk"), _text(data["scope"], "scope")
        if permission not in permissions or risk not in permissions[permission]["allowed_risks"] or scope not in permissions[permission]["allowed_scopes"]: _error(f"unsafe permission/risk/scope combination for {name}")
        if data["privacy"] != "nonprivate" or not _boolean(data["reversible"], "reversible"): _error(f"unsafe privacy/reversibility combination for {name}")
        for field in ("idempotency", "requires_provenance"): _boolean(data[field], field)
        if not data["requires_provenance"]: _error(f"action {name}: reviewed actions must require provenance")
        if set(data["argument_schema"]) != EXPECTED_ARGUMENTS[name]: _error(f"action {name}: canonical argument schema fields are incomplete")
        if not isinstance(data["state_keys"], list) or not all(isinstance(key, str) for key in data["state_keys"]): _error(f"action {name}: state_keys must be a string array")
        if not isinstance(data["bounds"], dict) or not data["bounds"] or any(_integer(value, "bound") < 0 for value in data["bounds"].values()): _error(f"action {name}: bounds are invalid")
        if not _codes(data["rejection_codes"], f"action {name}.rejection_codes") <= codes: _error(f"action {name}: rejection codes are invalid")
        _text(data["result_type"], "result_type"); _text(data["required_consent"], "required_consent")
        schemas = {field: _schema(item, f"action {name}.{field}") for field, item in data["argument_schema"].items()}
        actions[name] = MappingProxyType(dict(data, argument_schema=MappingProxyType(schemas)))
    if set(actions) != FIXED_ACTIONS: _error(f"fixed catalog actions must be exactly search, read_state, write_state; got {sorted(actions)}")
    policy_record = {"schema_version": POLICY_SCHEMA_VERSION, "catalog_version": top["catalog_version"], "policy_version": top["policy_version"], "confirmation_ttl_seconds": ttl, "permissions": permissions, "risk_classes": risks}
    policy_hash = hashlib.sha256(_canonical(policy_record)).hexdigest()
    policy = PolicyDefinition(top["catalog_version"], top["policy_version"], ttl, MappingProxyType(permissions), MappingProxyType(risks), policy_hash)
    return ActionCatalog(top["schema_version"], top["catalog_version"], MappingProxyType(actions), policy, codes, hashlib.sha256(_canonical(record)).hexdigest())
def _aware(value: datetime) -> bool: return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None
def _reject(proposal: ActionProposal, code: RejectionCode) -> ValidationDecision: return ValidationDecision(proposal, None, code)
def _valid_identity(proposal: ActionProposal, consent: ConsentRecord, state: FixtureState) -> bool:
    now = datetime.now(timezone.utc)
    return proposal.schema_version == PROPOSAL_SCHEMA_VERSION and consent.version == CONSENT_VERSION and state.schema_version == STATE_SCHEMA_VERSION and proposal.user_id == consent.user_id and proposal.session_id == consent.session_id and proposal.subject == consent.subject and state.session_id == proposal.session_id and consent.policy_version == proposal.policy_version and _aware(consent.granted_at) and _aware(consent.expires_at) and consent.granted_at <= now < consent.expires_at
def _valid_provenance(value: ActionProvenance) -> bool:
    return value.schema_version == PROVENANCE_SCHEMA_VERSION and bool(value.fixture_set_version) and value.source == "synthetic-local" and value.review_status == "reviewed" and bool(HASH_PATTERN.fullmatch(value.input_hash))
def _typed(arguments: Mapping[str, Any], definition: Mapping[str, Any]) -> RejectionCode | None:
    if not isinstance(arguments, Mapping): return RejectionCode.MALFORMED_TYPE
    schemas = definition["argument_schema"]
    if set(arguments) - set(schemas): return RejectionCode.EXTRA_ARGUMENT
    bounds = {"string": ("min_length", "max_length", str, len), "integer": ("minimum", "maximum", int, lambda value: value), "array": ("min_items", "max_items", list, len)}
    for field, schema in schemas.items():
        if field not in arguments:
            if not schema.get("optional", False): return RejectionCode.MALFORMED_TYPE
            continue
        lower, upper, expected, measure = bounds[schema["type"]]; value = arguments[field]
        if expected is int and type(value) is not int or expected is not int and not isinstance(value, expected): return RejectionCode.MALFORMED_TYPE
        if schema.get("allowed_values") and value not in schema["allowed_values"]: return RejectionCode.DISALLOWED_STATE_KEY
        if schema["type"] == "string" and "allowed_values" in schema and lower not in schema: continue
        if not schema[lower] <= measure(value) <= schema[upper]: return RejectionCode.OUT_OF_RANGE
        if expected is list and any(not isinstance(item, str) for item in value): return RejectionCode.MALFORMED_TYPE
    return None
def validate_action(proposal: ActionProposal, *, catalog: ActionCatalog, consent: ConsentRecord,
                    state: FixtureState) -> ValidationDecision:
    """Validate one proposal without executing it or granting permission."""
    if proposal.action_name not in catalog.actions: return _reject(proposal, RejectionCode.UNKNOWN_ACTION)
    now = datetime.now(timezone.utc)
    if (proposal.schema_version != PROPOSAL_SCHEMA_VERSION or proposal.catalog_version != catalog.catalog_version or proposal.policy_version != catalog.policy.policy_version): return _reject(proposal, RejectionCode.POLICY_UNEVALUABLE)
    if not _aware(state.expires_at) or state.expires_at <= now: return _reject(proposal, RejectionCode.EXPIRED_STATE)
    if not isinstance(proposal.justification, str) or not 8 <= len(proposal.justification) <= 256:
        return _reject(proposal, RejectionCode.MISSING_JUSTIFICATION)
    definition = catalog.actions[proposal.action_name]
    if definition["requires_provenance"] and not _valid_provenance(proposal.provenance): return _reject(proposal, RejectionCode.MISSING_PROVENANCE)
    if not _valid_identity(proposal, consent, state) or not isinstance(consent.scopes, frozenset) or definition["required_consent"] not in consent.scopes: return _reject(proposal, RejectionCode.CONSENT_MISMATCH)
    failure = _typed(proposal.arguments, definition)
    if failure is not None: return _reject(proposal, failure)
    digest = action_hash(proposal.arguments, catalog_version=catalog.catalog_version)
    if not definition["idempotency"] and digest in state.seen_non_idempotent: return _reject(proposal, RejectionCode.DUPLICATE_NON_IDEMPOTENT)
    accepted = ValidatedAction(PROPOSAL_SCHEMA_VERSION, proposal.action_name, MappingProxyType(dict(proposal.arguments)), digest, definition,
                               proposal.job_id, proposal.session_id, proposal.turn_id, proposal.turn_epoch, proposal.user_id, proposal.subject,
                               proposal.target, proposal.justification, consent.version, state.state_version, catalog.catalog_version, proposal.policy_version)
    return ValidationDecision(proposal, accepted, None)
def _policy_reject(code: RejectionCode) -> PolicyDecision: return PolicyDecision("rejected", code)
def preflight_policy(action: ValidatedAction, *, policy: PolicyDefinition,
                     confirmation: ConfirmationRecord | None = None) -> PolicyDecision:
    """Return one of exactly three policy outcomes and never execute an action."""
    definition = action.definition
    permission, risk = policy.permissions.get(definition["permission"]), policy.risk_classes.get(definition["risk"])
    unsafe = action.catalog_version != policy.catalog_version or action.policy_version != policy.policy_version or action.action_name not in FIXED_ACTIONS or permission is None or risk is None
    unsafe = unsafe or definition["risk"] not in permission["allowed_risks"] or definition["scope"] not in permission["allowed_scopes"] or definition["privacy"] == "private" and not risk["allows_private"] or not definition["reversible"] and not risk["allows_irreversible"]
    if unsafe: return _policy_reject(RejectionCode.POLICY_UNEVALUABLE)
    if confirmation is None: return PolicyDecision("confirmation_required" if risk["requires_confirmation"] else "allowed_without_confirmation", None)
    now = datetime.now(timezone.utc)
    exact = (confirmation.version, confirmation.action_name, confirmation.action_hash, confirmation.subject, confirmation.target, confirmation.user_id, confirmation.session_id, confirmation.policy_version)
    expected = (CONFIRMATION_VERSION, action.action_name, action.action_hash, action.subject, action.target, action.user_id, action.session_id, action.policy_version)
    if exact != expected or not confirmation.explicit: return _policy_reject(RejectionCode.CONFIRMATION_MISMATCH)
    try: arguments_match, ttl = _canonical(confirmation.arguments) == _canonical(action.canonical_arguments), (confirmation.expires_at - confirmation.granted_at).total_seconds()
    except (TypeError, ValueError): return _policy_reject(RejectionCode.CONFIRMATION_MISMATCH)
    if not _aware(confirmation.granted_at) or not _aware(confirmation.expires_at) or confirmation.granted_at > now or not 0 < ttl <= policy.confirmation_ttl_seconds: return _policy_reject(RejectionCode.CONFIRMATION_MISMATCH)
    if not arguments_match: return _policy_reject(RejectionCode.CONFIRMATION_MISMATCH)
    if now >= confirmation.expires_at: return _policy_reject(RejectionCode.CONFIRMATION_EXPIRED)
    return PolicyDecision("allowed_without_confirmation", None)
def evaluate_action_suite(cases: Iterable[ActionCase]) -> ActionPolicyReport:
    """Evaluate typed cases end-to-end with exact outcome/code denominators."""
    materialized = tuple(cases)
    if not materialized: _error("action suite denominator must be greater than zero")
    if len({(case.catalog.catalog_version, case.catalog.catalog_hash, case.catalog.policy.policy_version, case.catalog.policy.policy_hash) for case in materialized}) != 1: _error("action suite catalog and policy versions must be uniform")
    outcomes = {outcome: 0 for outcome in POLICY_OUTCOMES}
    rejections = {code.value: 0 for code in RejectionCode}
    mismatches: list[ActionMismatch] = []
    valid = invalid = 0
    for case in materialized:
        validation = validate_action(case.proposal, catalog=case.catalog, consent=case.consent, state=case.state)
        if validation.accepted is None:
            invalid += 1; actual = "rejected"; code = validation.rejection_code
        else:
            valid += 1
            policy_decision = preflight_policy(validation.accepted, policy=case.catalog.policy, confirmation=case.confirmation)
            actual = policy_decision.outcome; code = policy_decision.rejection_code
        outcomes[actual] += 1
        if code is not None: rejections[code.value] += 1
        if actual != case.expected_outcome or code != case.expected_rejection_code:
            mismatches.append(ActionMismatch(case, actual, code))
    catalog = materialized[0].catalog; total = len(materialized)
    return ActionPolicyReport("slice0-action-report-v1", catalog.catalog_version, catalog.catalog_hash, catalog.policy.policy_version, catalog.policy.policy_hash,
                              total, valid, invalid, total, total, MappingProxyType(outcomes), MappingProxyType({outcome: total for outcome in POLICY_OUTCOMES}),
                              MappingProxyType(rejections), MappingProxyType({code: total for code in rejections}), tuple(mismatches), "pass" if not mismatches else "hold")
def _action_event(action_name: str, action_hash_value: str | None, event_type: str, status: str,
                  proposal: ActionProposal | ValidatedAction, code: RejectionCode | None, event_id: int,
                  prior_event_id: int | None, prior_event_hash: str | None, policy_version: str) -> ActionLedgerEvent:
    """Build privacy-preserving action evidence; callers append it to the ledger."""
    arguments = proposal.arguments if isinstance(proposal, ActionProposal) else proposal.canonical_arguments
    privacy = "unknown" if isinstance(proposal, ActionProposal) else proposal.definition["privacy"]
    input_hash = scoped_hash(_canonical({"action_name": action_name, "action_hash": action_hash_value}), scope="action-input", schema_version=PROPOSAL_SCHEMA_VERSION)
    return ActionLedgerEvent(EVENT_SCHEMA_VERSION, event_type, "1.0.0", event_id, proposal.session_id, proposal.turn_id, proposal.turn_epoch, input_hash,
                             len(_canonical(arguments)), "application/json", CONSENT_VERSION, policy_version, status, None if code is None else code.value,
                             0, action_hash_value, prior_event_id, prior_event_hash, None, proposal.job_id, action_name, privacy)
def validation_event(decision: ValidationDecision, *, event_id: int, prior_event_id: int | None = None,
                     prior_event_hash: str | None = None) -> ActionLedgerEvent:
    """Build a validation event carrying action identity/hash but never raw arguments."""
    accepted = decision.accepted
    return _action_event(decision.proposal.action_name, None if accepted is None else accepted.action_hash, "validation", "validated" if accepted else "rejected",
                         accepted if accepted else decision.proposal, decision.rejection_code, event_id, prior_event_id, prior_event_hash, decision.proposal.policy_version)
def policy_event(decision: PolicyDecision, action: ValidatedAction, *, event_id: int, prior_event_id: int | None = None,
                 prior_event_hash: str | None = None) -> ActionLedgerEvent:
    """Build a policy event with an exact outcome and stable rejection taxonomy."""
    return _action_event(action.action_name, action.action_hash, "policy", decision.outcome, action, decision.rejection_code,
                         event_id, prior_event_id, prior_event_hash, action.policy_version)
