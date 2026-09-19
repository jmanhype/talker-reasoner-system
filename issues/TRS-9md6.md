---
id: TRS-9md6
title: "Guard fixed local actions with fail-closed validation"
status: closed
priority: 1
type: feature
labels: [slice-0, delivered]
parent: TRS-pf94
created_at: 2026-09-19T05:29:37Z
created_by: speed
updated_at: 2026-09-19T15:55:44Z
content_hash: "sha256:75c930957e24fbaf79ca4c99c7eaf63f4fa5e42e57e61cca5ce3f6ab0187d8cd"
was_blocked_by: [TRS-0daa]
assignee: dev-TRS-9md6
follows: [TRS-0daa, TRS-74z8]
closed_at: 2026-09-19T15:55:44Z
close_reason: "Accepted: independently reran story/full suites (24/24 and 52/52), compilation, pvg verify, static dependency/privacy scans, LOC/budget checks, and hash verification. The compacted implementation is 421 LOC, covers every rejection and policy outcome, and executes nothing."
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
- TRS-0daa: src/talk_reasoner/contracts.py -> scoped_hash(content: str | bytes, *, scope: str, schema_version: str) -> str
  spec: Hash canonical action arguments and provenance without persisting raw sensitive values.
- TRS-0daa: src/talk_reasoner/contracts.py -> append_event(ledger: EventLedger, event: LedgerEvent) -> AppendReceipt
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
- Depends on hash/event contracts from TRS-0daa.

### proof

- [ ] Pending implementation


## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

Commands run:
- git add config/actions/slice0-v1.json src/talk_reasoner/actions.py tests/test_actions.py
- git commit -m "feat(TRS-9md6): guard fixed local actions"

### CI/Test Results
- Story commit: 51a3969
- Worktree clean after commit.
- Independent story/full suites before commit: 24/24 and 52/52 passed.

Summary: accepted compacted implementation committed on story/TRS-9md6 at 51a3969.

Commit SHA: 51a3969

### AC Verification
- [x] All eight TRS-9md6 AC are covered by committed files and independent 52/52 suite.

## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/talker-reasoner-system/.claude/worktrees/dev-TRS-9md6
git diff --check
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m pytest tests/test_actions.py
.venv/bin/python -m pytest
pvg verify src/talk_reasoner/actions.py config/actions/slice0-v1.json tests/test_actions.py --include-tests --format=text
```

Independent coordinator results:

- `git diff --check`: exit 0.
- Compilation: exit 0.
- Story tests: 24/24 passed.
- Full suite: 52/52 passed.
- `pvg verify`: passed with zero issues.
- Diff budget: 421 total changed LOC, four under the 425 LOC ceiling.
- Static scan found no production network, subprocess, storage-platform, or memory-platform dependency; the only forbidden-name match is the test’s negative-import assertion.
- Report fixture still covers all 13 rejection codes once and all outcome denominators; no raw arguments enter ledger event bytes.

### CI/Test Results

```text
tests/test_actions.py: 24 passed
full suite: 52 passed
pvg verify: PASSED, 0 issues
changed LOC: 421 / 425 maximum
```

Summary: implemented the fixed local `search`/`read_state`/`write_state` catalog, fail-closed typed validation, exact policy outcomes, stable rejection taxonomy, exact confirmation binding/TTL, complete action-suite report metrics, and privacy-preserving ledger events without executing any action or enabling any external service.

Commit SHA: 9e75200db07e174dca470b8d994ee8b101344f74436d5b612e558074ed31b63a

This is the three-file pre-commit delivery-manifest SHA-256; the actual story Git commit is appended below.

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Exact fixed catalog with complete metadata | PASS | Catalog loader and catalog-safety test. |
| 2. Only valid, bounded, justified, provenance-complete, consent-matching, non-expired proposals accepted | PASS | 24 story tests. |
| 3. Every required invalid family fails closed | PASS | Rejection matrix covers all 13 codes. |
| 4. Stable versioned one-primary-code taxonomy | PASS | `RejectionCode` and report counts. |
| 5. Exactly three policy outcomes; confirmation before consequential work | PASS | Policy tests. |
| 6. Exact confirmation bindings and active TTL required | PASS | Mismatch/expiry tests. |
| 7. Reports include all counts, denominators, versions, and hashes | PASS | Action-suite report test. |
| 8. No execution/network/credentials/raw argument persistence | PASS | Static scan and ledger privacy test. |


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-19T05:29:37Z dep_added: blocked_by TRS-0daa
- 2026-09-19T05:29:38Z dep_added: blocks TRS-ndv6
- 2026-09-19T05:29:38Z dep_added: blocks TRS-f7sm
- 2026-09-19T05:29:39Z dep_added: blocks TRS-osl5
- 2026-09-19T13:41:58Z dep_removed: was_blocked_by TRS-0daa
- 2026-09-19T14:15:02Z status: open -> in_progress
- 2026-09-19T14:15:02Z auto-follows: linked to predecessor TRS-0daa
- 2026-09-19T14:15:02Z claimed by dev-TRS-9md6
- 2026-09-19T15:54:09Z status: in_progress -> in_progress
- 2026-09-19T15:54:09Z auto-follows: linked to predecessor TRS-74z8
- 2026-09-19T15:55:44Z status: in_progress -> closed
- 2026-09-19T15:55:45Z dep_removed: no_longer_blocks TRS-ndv6
- 2026-09-19T15:55:45Z dep_removed: no_longer_blocks TRS-f7sm
- 2026-09-19T15:55:45Z dep_removed: no_longer_blocks TRS-osl5

## Links
- Parent: [[TRS-pf94]]
- Was blocked by: [[TRS-0daa]]
- Follows: [[TRS-0daa]], [[TRS-74z8]]

## Comments
