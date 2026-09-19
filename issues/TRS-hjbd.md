---
id: TRS-hjbd
title: "Guard fixed local actions with fail-closed validation"
status: open
priority: 1
type: feature
labels: [slice-0]
parent: TRS-pf94
created_at: 2026-09-19T05:25:58Z
created_by: speed
updated_at: 2026-09-19T05:27:54Z
content_hash: "sha256:ccf99d22f1e374bb9e2b511864beb6a66128234482ed5639ea2696d747258d92"
blocked_by: [TRS-r6uo]
blocks: [TRS-pmd9, TRS-owap, TRS-do2n]
---

## Description
## Context (Embedded)

Slice 0 has a fixed local action catalog and a fail-closed validator/preflight
boundary. The reasoner may propose actions; it can never grant permission or
execute them. Jev and PersonaPlex cannot confirm or execute actions. Voxtral
Small structured output, if ever enabled later, remains a proposal subject to
this same path.

The only Slice-0 catalog names are:

- `search`: deterministic local fixture result; no web;
- `read_state`: read only fixture state;
- `write_state`: record a validated intended write; no durable platform write.

Every catalog entry declares canonical name/schema, argument/result types,
permission and risk, ranges/cardinalities/state keys, idempotency and
reversibility, provenance/consent requirements, and rejection codes.

Policy outcomes are exactly:

- `allowed_without_confirmation`, only for narrowly scoped low-risk local work;
- `confirmation_required`;
- `rejected`.

High-risk categories remain external send, booking, payment, deletion,
private-data disclosure, and code execution. Those actions are not added in
Slice 0; policy behavior is exercised with the fixed local catalog and typed
test cases. No tool executor exists.

## USER INTENT

Before any action authority exists, malformed, unknown, out-of-scope, or
insufficiently consented proposals must fail closed with a stable reason, and
consequential work must require an exact scoped confirmation.

## Goal

Validate every local proposal against a versioned catalog and run policy
preflight with a complete rejection taxonomy and hashed event evidence.

## OUT OF SCOPE

- Executing `search`, `read_state`, or `write_state`: Slice 0 records validated
  intent only and has no executor.
- Adding external messaging, booking, payment, deletion, private-data
  disclosure, code execution, or web fetching: later explicit consent/gated story.
- Reasoner transport or async lifecycle: downstream async-job story.
- Rendering rejection/confirmation copy for a user: downstream renderer/CLI story.
- Redis, Postgres, or durable memory writes: later platform story.

## DIFF BUDGET

- About 5 source/test/config files; under 425 changed LOC.
- Gross overrun requires PM investigation for scope creep or hidden design gaps.

## Boundary Map

PRODUCES:
- src/talk_reasoner/actions.py -> load_action_catalog(path: pathlib.Path) -> ActionCatalog
  spec: Parse and validate a versioned fixed catalog; fail closed on duplicate names, unsafe risk/permission combinations, missing schemas/ranges/consent requirements, or unsupported rejection codes.
- src/talk_reasoner/actions.py -> validate_action(proposal: ActionProposal, *, catalog: ActionCatalog, consent: ConsentRecord, state: FixtureState) -> ValidationDecision
  spec: Validate canonical name, typed arguments, ranges/cardinalities/state keys, justification, provenance, consent, expiry, and duplicate non-idempotent proposals; return accepted action or stable rejection code without executing anything.
- src/talk_reasoner/actions.py -> preflight_policy(action: ValidatedAction, *, policy: PolicyDefinition, confirmation: ConfirmationRecord | None = None) -> PolicyDecision
  spec: Return exactly allowed_without_confirmation, confirmation_required, or rejected after checking risk, consent, permission, privacy classification, reversibility, scope, identity, catalog version, and confirmation hash/arguments/target/user/session/policy/TTL.
- src/talk_reasoner/actions.py -> evaluate_action_suite(cases: Iterable[ActionCase]) -> ActionPolicyReport
  spec: Emit valid/invalid counts, policy outcome counts, every rejection-code count, catalog/policy version/hash, denominators, and exact pass/hold decision.
- config/actions/slice0-v1.json -> fixed action catalog and policy definitions
  fields: schema_version, catalog_version, actions, permissions, risk_classes, policy_version, confirmation_ttl_seconds, rejection_codes.
- tests/test_actions.py -> validator, preflight, taxonomy, and event tests
  source: covers valid and malformed proposals, every rejection family, confirmation match/mismatch/expiry, and hashed provenance.

CONSUMES:
- TRS-r6uo: src/talk_reasoner/contracts.py -> scoped_hash(content: str | bytes, *, scope: str, schema_version: str) -> str
  spec: Hash canonical action arguments and provenance without persisting raw sensitive values.
- TRS-r6uo: src/talk_reasoner/contracts.py -> append_event(ledger: EventLedger, event: LedgerEvent) -> AppendReceipt
  spec: Append validation and policy events with action name, argument hash, status, rejection reason, consent/policy versions, and no raw arguments.

## Acceptance Requirements

1. The catalog contains exactly `search`, `read_state`, and `write_state`, each
   with a canonical schema, result type, permission/risk, bounds, state scope,
   idempotency/reversibility, provenance/consent requirement, and rejection codes.
2. `validate_action` accepts only known, well-typed, in-range, justified,
   provenance-complete, consent-matching, non-expired proposals and rejects all
   other input.
3. Validation fails closed at least for unknown name, malformed type, extra
   privileged argument, out-of-range value/cardinality, disallowed key,
   missing justification, missing provenance, consent mismatch, expired state,
   duplicate non-idempotent proposal, and unevaluable policy.
4. Rejection codes are a stable versioned taxonomy, never free-form strings,
   and every invalid fixture family maps to exactly one primary code.
5. `preflight_policy` returns only the three exact outcomes above. It emits
   `confirmation_required` before any consequential confirmation and `rejected`
   when consent/policy cannot be evaluated.
6. Confirmation matching requires exact action hash, canonical arguments,
   subject/target, user/session, policy version, and active TTL. Ambient yes,
   stale confirmation, changed arguments, changed target, and expiry all fail.
7. Validation/policy reports include counts and denominators by outcome and
   rejection code plus catalog/policy versions and hashes.
8. No action executes, contacts a service, reads credentials, or records raw
   sensitive arguments; event fields carry hashes/classification instead.

## Testing Requirements

- Unit tests: each catalog check, each rejection code, each policy outcome, and
  each confirmation mismatch/expiry condition.
- Integration tests: MANDATORY (no mocks). Evaluate a typed valid/invalid action
  suite end-to-end through validation, preflight, event append, and report
  generation using only local in-memory data.
- E2E tests: not in this story; the blocked capstone owns user-journey coverage.
- Commands: `python -m pytest tests/test_actions.py`.

## MANDATORY SKILLS

- `project-standards`: typed fail-closed validation and negative-test discipline.
- `pvg`: story governance and delivery evidence only.

## Delivery Requirements

- Paste exact pytest output and exit status.
- Include the rejection-taxonomy matrix and outcome counts/denominators.
- Include an AC verification table with file/test evidence.
- Update the authoritative `nd_contract` using the pvg delivery workflow.

## nd_contract

status: new

### evidence

- Created: 2026-09-19
- Depends on hash/event contracts from TRS-r6uo.

### proof

- [ ] Pending implementation

## Context (Embedded)

Slice 0 has a fixed local action catalog and a fail-closed validator/preflight
boundary. The reasoner may propose actions; it can never grant permission or
execute them. Jev and PersonaPlex cannot confirm or execute actions. Voxtral
Small structured output, if ever enabled later, remains a proposal subject to
this same path.

The only Slice-0 catalog names are:

- `search`: deterministic local fixture result; no web;
- `read_state`: read only fixture state;
- `write_state`: record a validated intended write; no durable platform write.

Every catalog entry declares canonical name/schema, argument/result types,
permission and risk, ranges/cardinalities/state keys, idempotency and
reversibility, provenance/consent requirements, and rejection codes.

Policy outcomes are exactly:

- `allowed_without_confirmation`, only for narrowly scoped low-risk local work;
- `confirmation_required`;
- `rejected`.

High-risk categories remain external send, booking, payment, deletion,
private-data disclosure, and code execution. Those actions are not added in
Slice 0; policy behavior is exercised with the fixed local catalog and typed
test cases. No tool executor exists.

## USER INTENT

Before any action authority exists, malformed, unknown, out-of-scope, or
insufficiently consented proposals must fail closed with a stable reason, and
consequential work must require an exact scoped confirmation.

## Goal

Validate every local proposal against a versioned catalog and run policy
preflight with a complete rejection taxonomy and hashed event evidence.

## OUT OF SCOPE

- Executing `search`, `read_state`, or `write_state`: Slice 0 records validated
  intent only and has no executor.
- Adding external messaging, booking, payment, deletion, private-data
  disclosure, code execution, or web fetching: later explicit consent/gated story.
- Reasoner transport or async lifecycle: downstream async-job story.
- Rendering rejection/confirmation copy for a user: downstream renderer/CLI story.
- Redis, Postgres, or durable memory writes: later platform story.

## DIFF BUDGET

- About 5 source/test/config files; under 425 changed LOC.
- Gross overrun requires PM investigation for scope creep or hidden design gaps.

## Boundary Map

PRODUCES:
- src/talk_reasoner/actions.py -> load_action_catalog(path: pathlib.Path) -> ActionCatalog
  spec: Parse and validate a versioned fixed catalog; fail closed on duplicate names, unsafe risk/permission combinations, missing schemas/ranges/consent requirements, or unsupported rejection codes.
- src/talk_reasoner/actions.py -> validate_action(proposal: ActionProposal, *, catalog: ActionCatalog, consent: ConsentRecord, state: FixtureState) -> ValidationDecision
  spec: Validate canonical name, typed arguments, ranges/cardinalities/state keys, justification, provenance, consent, expiry, and duplicate non-idempotent proposals; return accepted action or stable rejection code without executing anything.
- src/talk_reasoner/actions.py -> preflight_policy(action: ValidatedAction, *, policy: PolicyDefinition, confirmation: ConfirmationRecord | None = None) -> PolicyDecision
  spec: Return exactly allowed_without_confirmation, confirmation_required, or rejected after checking risk, consent, permission, privacy classification, reversibility, scope, identity, catalog version, and confirmation hash/arguments/target/user/session/policy/TTL.
- src/talk_reasoner/actions.py -> evaluate_action_suite(cases: Iterable[ActionCase]) -> ActionPolicyReport
  spec: Emit valid/invalid counts, policy outcome counts, every rejection-code count, catalog/policy version/hash, denominators, and exact pass/hold decision.
- config/actions/slice0-v1.json -> fixed action catalog and policy definitions
  fields: schema_version, catalog_version, actions, permissions, risk_classes, policy_version, confirmation_ttl_seconds, rejection_codes.
- tests/test_actions.py -> validator, preflight, taxonomy, and event tests
  source: covers valid and malformed proposals, every rejection family, confirmation match/mismatch/expiry, and hashed provenance.

CONSUMES:
- TRS-r6uo: src/talk_reasoner/contracts.py -> scoped_hash(content: str | bytes, *, scope: str, schema_version: str) -> str
  spec: Hash canonical action arguments and provenance without persisting raw sensitive values.
- TRS-r6uo: src/talk_reasoner/contracts.py -> append_event(ledger: EventLedger, event: LedgerEvent) -> AppendReceipt
  spec: Append validation and policy events with action name, argument hash, status, rejection reason, consent/policy versions, and no raw arguments.

## Acceptance Criteria

1. The catalog contains exactly `search`, `read_state`, and `write_state`, each
   with a canonical schema, result type, permission/risk, bounds, state scope,
   idempotency/reversibility, provenance/consent requirement, and rejection codes.
2. `validate_action` accepts only known, well-typed, in-range, justified,
   provenance-complete, consent-matching, non-expired proposals and rejects all
   other input.
3. Validation fails closed at least for unknown name, malformed type, extra
   privileged argument, out-of-range value/cardinality, disallowed key,
   missing justification, missing provenance, consent mismatch, expired state,
   duplicate non-idempotent proposal, and unevaluable policy.
4. Rejection codes are a stable versioned taxonomy, never free-form strings,
   and every invalid fixture family maps to exactly one primary code.
5. `preflight_policy` returns only the three exact outcomes above. It emits
   `confirmation_required` before any consequential confirmation and `rejected`
   when consent/policy cannot be evaluated.
6. Confirmation matching requires exact action hash, canonical arguments,
   subject/target, user/session, policy version, and active TTL. Ambient yes,
   stale confirmation, changed arguments, changed target, and expiry all fail.
7. Validation/policy reports include counts and denominators by outcome and
   rejection code plus catalog/policy versions and hashes.
8. No action executes, contacts a service, reads credentials, or records raw
   sensitive arguments; event fields carry hashes/classification instead.

## Testing Requirements

- Unit tests: each catalog check, each rejection code, each policy outcome, and
  each confirmation mismatch/expiry condition.
- Integration tests: MANDATORY (no mocks). Evaluate a typed valid/invalid action
  suite end-to-end through validation, preflight, event append, and report
  generation using only local in-memory data.
- E2E tests: not in this story; the blocked capstone owns user-journey coverage.
- Commands: `python -m pytest tests/test_actions.py`.

## Skills To Use

- `project-standards`: typed fail-closed validation and negative-test discipline.
- `pvg`: story governance and delivery evidence only.

## Delivery Requirements

- Paste exact pytest output and exit status.
- Include the rejection-taxonomy matrix and outcome counts/denominators.
- Include an AC verification table with file/test evidence.
- Update the authoritative `nd_contract` using the pvg delivery workflow.

## nd_contract

status: new

### evidence

- Created: 2026-09-19
- Depends on hash/event contracts from TRS-r6uo.

### proof

- [ ] Pending implementation


## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T05:25:58Z dep_added: blocked_by TRS-r6uo
- 2026-09-19T05:25:59Z dep_added: blocks TRS-pmd9
- 2026-09-19T05:25:59Z dep_added: blocks TRS-owap
- 2026-09-19T05:26:00Z dep_added: blocks TRS-do2n

## Links
- Parent: [[TRS-pf94]]
- Blocks: [[TRS-pmd9]], [[TRS-owap]], [[TRS-do2n]]
- Blocked by: [[TRS-r6uo]]

## Comments
