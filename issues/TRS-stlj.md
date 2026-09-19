---
id: TRS-stlj
title: "M0 walking skeleton: enforce all machinery oracles offline"
status: open
priority: 1
type: feature
labels: [hard-tdd, walking-skeleton]
parent: TRS-d8vq
created_at: 2026-09-19T18:13:25Z
created_by: speed
updated_at: 2026-09-19T18:14:22Z
content_hash: "sha256:12f82bb3fbd9eddad8dc6d09e3cf76ac9d97ef73a3b9e5f8cef3ebcb9a6a0665"
blocks: [TRS-le6s]
---

## Description
## Context (Embedded)

Milestone M0 from `design/BUILD.md` turns the committed machinery design into an executable offline test gate. Slice 0 already has 164 passing tests, but it does not yet parse or enforce the seven generated transition oracles or explicitly run all 36 Modelith invariant properties.

The user need is to prove that the designed state machines and invariants govern the existing deterministic contracts before live voice or any live dependency is authorized.

This is a **hard-TDD RED/GREEN story**. The RED developer writes the tests first and commits them with the literal marker `tdd-red`. The GREEN implementer makes those unchanged tests pass.

## Non-goals

- No live audio, PersonaPlex, Voxtral, Jev, live model, Redis, PostgreSQL, MAGG, Context Forge, Dagger, Treg, local MCP tool, or memory platform.
- No TypeScript edge implementation.
- No architecture/package extraction; M1 owns that.
- No change to Slice 0 business behavior unless a failing oracle exposes a real contract defect.

## OUT OF SCOPE

- Live model adapters: deferred to the live voice milestone.
- Durable state: deferred to M4.
- MCP discovery/execution: deferred to M5/M6.
- Architecture import-boundary refactoring: deferred to M1 because M0 first proves the transition oracle surface.

## DIFF BUDGET

- About 5 source/test files, under 900 changed LOC.
- Gross overrun requires PM investigation for scope creep or hidden design gaps.

## Boundary Map

PRODUCES:

- `src/talk_reasoner/machinery.py` -> `parse_oracle(path: pathlib.Path) -> tuple[OracleTransition, ...]`
  Parses test id, stable id, source, trigger, guard, target, and actions from one committed `.oracle.md` table. It must reject malformed rows, duplicate stable ids, and empty tables.
- `src/talk_reasoner/machinery.py` -> `parse_all_oracles(directory: pathlib.Path) -> dict[str, tuple[OracleTransition, ...]]`
  Loads all seven committed oracle files in deterministic filename order and proves the expected count of 62 unique rows.
- `src/talk_reasoner/machinery.py` -> `parse_invariant_ids(path: pathlib.Path) -> tuple[str, ...]`
  Extracts the exact 36 invariant ids from the rendered canonical Modelith Markdown without introducing a second domain schema.
- `src/talk_reasoner/machinery.py` -> `transition_case(machine_name: str, stable_id: str) -> TransitionCase`
  Returns the real local pre-state/context/event needed to exercise one oracle row. Unknown machine or id must raise `MachineryContractError`.
- `src/talk_reasoner/machinery.py` -> `exercise_transition(case: TransitionCase) -> TransitionResult`
  Executes the case through the real local state/contract implementation and returns actual next state and action names; it must not merely echo the oracle.
- `tests/test_machinery_oracles.py` -> parser-driven transition conformance suite
  Reads every committed oracle file at runtime, obtains its `TransitionCase`, calls `exercise_transition`, and asserts the actual next state and actions equal the oracle row.
- `tests/test_machinery_invariants.py` -> explicit invariant property registry
  Contains one non-empty callable property/contract check for each exact invariant id below.

CONSUMES:

- (existing): `design/machines/*.oracle.md` -> committed transition oracle tables.
- (existing): `design/domain.modelith.md` -> canonical rendered invariant ids.
- (existing): `src/talk_reasoner/contracts.py` -> fixture, ledger, append, and verification contracts.
- (existing): `src/talk_reasoner/jobs.py` -> reasoner job legal transitions.
- (existing): `src/talk_reasoner/actions.py` -> validation and policy contracts.
- (existing): `src/talk_reasoner/rendering.py` -> renderer boundary.

## Acceptance Requirements

1. RED tests are committed first with `tdd-red`, fail for the right reason on missing machinery support, and are locked before implementation.
2. `parse_all_oracles` loads exactly seven files and 62 unique transition rows; it rejects malformed rows, duplicate stable ids, and missing files.
3. The transition suite parses each of these seven files at runtime and asserts every row's actual next state and actions:
   - `ConversationTurn.oracle.md`
   - `EventLedger.oracle.md`
   - `MemoryRecord.oracle.md`
   - `ReasonerJob.oracle.md`
   - `ToolCatalog.oracle.md`
   - `ToolExecution.oracle.md`
   - `VoiceSession.oracle.md`
4. Every one of these 62 stable ids is covered:
   CONV-02965d CONV-f9f25b CONV-87aef6 CONV-73bae3 CONV-53ecad CONV-5d0019 CONV-a756c5 CONV-7c39be CONV-7f7105 CONV-8fadcf CONV-dab39a CONV-04c2c7 EVEN-c2c520 EVEN-5feeb7 EVEN-098b63 EVEN-0d5972 EVEN-e9be49 EVEN-f230e3 EVEN-a0faaa EVEN-d90d1d EVEN-379e68 MEMO-0697b6 MEMO-ef809c MEMO-814928 MEMO-914d7a MEMO-c8e66c MEMO-b8a59c MEMO-9faf38 MEMO-d9f286 MEMO-8862c9 REAS-bc3e49 REAS-5dc4da REAS-974bde REAS-1559cc REAS-f1a17d REAS-c3c792 REAS-0c1f49 REAS-97e8bd REAS-c567aa REAS-0766c3 REAS-0cd65a REAS-345901 REAS-79c30e REAS-b46837 TCAT-563b02 TCAT-3a38e4 TCAT-97dc90 TCAT-675b21 TEXE-6c80b2 TEXE-9297f7 TEXE-8688ba TEXE-0d301e TEXE-49dba9 TEXE-b9c795 TEXE-e18dac TEXE-34eda4 TEXE-782b09 TEXE-a8cfa2 TEXE-30e3a5 VOIC-305554 VOIC-e62d1f VOIC-32ea66
5. `parse_invariant_ids` returns exactly these 36 ids, and the invariant suite executes one meaningful property/contract check for each:
   session-processing-boundary
   - raw-input-ephemeral
   - route-fail-closed
   - transcriber-no-authority
   - job-staleness-bounded
   - canceled-work-silent
   - router-no-authority
   - slow-path-only-after-route
   - reasoner-proposes-only
   - proposal-identity-bound
   - contract-fail-closed
   - action-schema-fail-closed
   - action-no-credentials
   - catalog-version-pinned
   - policy-before-execution
   - policy-three-outcomes
   - confirmation-exact-and-expiring
   - confirmation-single-use
   - catalog-reviewed-before-active
   - runtime-cannot-mutate-capability
   - tool-schema-provenance
   - tool-allowlist-only
   - credential-isolation
   - tool-output-filtered
   - tool-result-not-sole-truth
   - hot-state-minimized
   - hot-state-ttl
   - ledger-append-only
   - ledger-minimized
   - ledger-integrity-fail-closed
   - response-filtered
   - memory-provenance-bound
   - memory-not-sole-truth
   - memory-deletable
   - talker-no-authority
   - model-boundaries-explicit
6. Each conjunctive guard named in the machine matrices has at least one falsifying-clause test for each independent clause, and every actor has an integration/property test with the real local dependency or a contract-tested local stand-in.
7. The implementation has no network import, credential read, subprocess call, durable service dependency, or semantic-memory dependency.
8. `modelith lint design/domain.modelith.yaml --completeness error`, `machinery lint design/machines`, `machinery oracle design/machines`, and `machinery check design` are green with zero blocking findings.
9. The complete existing suite remains green, including the prior 164 tests.

## Testing Requirements

- RED phase: tests only; commit subject contains `tdd-red`.
- GREEN phase: implementation only; RED test files remain unchanged.
- Unit tests: malformed oracle input, duplicate/unknown ids, invariant count, and parser boundaries.
- Integration/property tests: real local transition cases, ledger verification, policy/confirmation, renderer filtering, privacy canaries, capability red-team, and tool output filtering.
- E2E tests are not in this story; the blocked M0 capstone owns the full gate.
- Commands:
  - `pytest -q tests/test_machinery_oracles.py tests/test_machinery_invariants.py`
  - `pytest -q`
  - `modelith lint design/domain.modelith.yaml --completeness error`
  - `machinery lint design/machines`
  - `machinery oracle design/machines`
  - `machinery check design`
- No mocks of any kind are permitted in the oracle integration tests.

## MANDATORY SKILLS

- `project-standards`: typed parser and contract discipline.
- `pvg`: story transitions only.
- `machinery`: oracle generation and design gates.

## Delivery Requirements

- Paste exact RED failure summary and GREEN test output.
- Paste every deterministic gate command and exit status.
- Include a stable-id coverage table with denominator 62.
- Include an invariant coverage table with denominator 36.
- Include an AC verification table.
- Record the final commit SHA.

## nd_contract

status: new

### evidence

- Created from machinery design milestone M0.
- Oracle denominator at creation: 62.
- Invariant denominator at creation: 36.

### proof

- [ ] Pending RED/GREEN implementation.

## Context (Embedded)

Milestone M0 from `design/BUILD.md` turns the committed machinery design into an executable offline test gate. Slice 0 already has 164 passing tests, but it does not yet parse or enforce the seven generated transition oracles or explicitly run all 36 Modelith invariant properties.

The user need is to prove that the designed state machines and invariants govern the existing deterministic contracts before live voice or any external service is authorized.

This is a **hard-TDD RED/GREEN story**. The RED developer writes the tests first and commits them with the literal marker `tdd-red`. The GREEN implementer makes those unchanged tests pass.

## Non-goals

- No live audio, PersonaPlex, Voxtral, Jev, external reasoner, Redis, PostgreSQL, MAGG, Context Forge, Dagger, Treg, local MCP tool, or memory platform.
- No TypeScript edge implementation.
- No architecture/package extraction; M1 owns that.
- No change to Slice 0 business behavior unless a failing oracle exposes a real contract defect.

## OUT OF SCOPE

- Live model adapters: deferred to the live voice milestone.
- Durable state: deferred to M4.
- MCP discovery/execution: deferred to M5/M6.
- Architecture import-boundary refactoring: deferred to M1 because M0 first proves the transition oracle surface.

## DIFF BUDGET

- About 5 source/test files, under 900 changed LOC.
- Gross overrun requires PM investigation for scope creep or hidden design gaps.

## Boundary Map

PRODUCES:

- `src/talk_reasoner/machinery.py` -> `parse_oracle(path: pathlib.Path) -> tuple[OracleTransition, ...]`
  Parses test id, stable id, source, trigger, guard, target, and actions from one committed `.oracle.md` table. It must reject malformed rows, duplicate stable ids, and empty tables.
- `src/talk_reasoner/machinery.py` -> `parse_all_oracles(directory: pathlib.Path) -> dict[str, tuple[OracleTransition, ...]]`
  Loads all seven committed oracle files in deterministic filename order and proves the expected count of 62 unique rows.
- `src/talk_reasoner/machinery.py` -> `parse_invariant_ids(path: pathlib.Path) -> tuple[str, ...]`
  Extracts the exact 36 invariant ids from the rendered canonical Modelith Markdown without introducing a second domain schema.
- `src/talk_reasoner/machinery.py` -> `transition_case(machine_name: str, stable_id: str) -> TransitionCase`
  Returns the real local pre-state/context/event needed to exercise one oracle row. Unknown machine or id must raise `MachineryContractError`.
- `src/talk_reasoner/machinery.py` -> `exercise_transition(case: TransitionCase) -> TransitionResult`
  Executes the case through the real local state/contract implementation and returns actual next state and action names; it must not merely echo the oracle.
- `tests/test_machinery_oracles.py` -> parser-driven transition conformance suite
  Reads every committed oracle file at runtime, obtains its `TransitionCase`, calls `exercise_transition`, and asserts the actual next state and actions equal the oracle row.
- `tests/test_machinery_invariants.py` -> explicit invariant property registry
  Contains one non-empty callable property/contract check for each exact invariant id below.

CONSUMES:

- (existing): `design/machines/*.oracle.md` -> committed transition oracle tables.
- (existing): `design/domain.modelith.md` -> canonical rendered invariant ids.
- (existing): `src/talk_reasoner/contracts.py` -> fixture, ledger, append, and verification contracts.
- (existing): `src/talk_reasoner/jobs.py` -> reasoner job legal transitions.
- (existing): `src/talk_reasoner/actions.py` -> validation and policy contracts.
- (existing): `src/talk_reasoner/rendering.py` -> renderer boundary.

## Acceptance Criteria

1. RED tests are committed first with `tdd-red`, fail for the right reason on missing machinery support, and are locked before implementation.
2. `parse_all_oracles` loads exactly seven files and 62 unique transition rows; it rejects malformed rows, duplicate stable ids, and missing files.
3. The transition suite parses each of these seven files at runtime and asserts every row's actual next state and actions:
   - `ConversationTurn.oracle.md`
   - `EventLedger.oracle.md`
   - `MemoryRecord.oracle.md`
   - `ReasonerJob.oracle.md`
   - `ToolCatalog.oracle.md`
   - `ToolExecution.oracle.md`
   - `VoiceSession.oracle.md`
4. Every one of these 62 stable ids is covered:
   CONV-02965d CONV-f9f25b CONV-87aef6 CONV-73bae3 CONV-53ecad CONV-5d0019 CONV-a756c5 CONV-7c39be CONV-7f7105 CONV-8fadcf CONV-dab39a CONV-04c2c7 EVEN-c2c520 EVEN-5feeb7 EVEN-098b63 EVEN-0d5972 EVEN-e9be49 EVEN-f230e3 EVEN-a0faaa EVEN-d90d1d EVEN-379e68 MEMO-0697b6 MEMO-ef809c MEMO-814928 MEMO-914d7a MEMO-c8e66c MEMO-b8a59c MEMO-9faf38 MEMO-d9f286 MEMO-8862c9 REAS-bc3e49 REAS-5dc4da REAS-974bde REAS-1559cc REAS-f1a17d REAS-c3c792 REAS-0c1f49 REAS-97e8bd REAS-c567aa REAS-0766c3 REAS-0cd65a REAS-345901 REAS-79c30e REAS-b46837 TCAT-563b02 TCAT-3a38e4 TCAT-97dc90 TCAT-675b21 TEXE-6c80b2 TEXE-9297f7 TEXE-8688ba TEXE-0d301e TEXE-49dba9 TEXE-b9c795 TEXE-e18dac TEXE-34eda4 TEXE-782b09 TEXE-a8cfa2 TEXE-30e3a5 VOIC-305554 VOIC-e62d1f VOIC-32ea66
5. `parse_invariant_ids` returns exactly these 36 ids, and the invariant suite executes one meaningful property/contract check for each:
   session-processing-boundary
   - raw-input-ephemeral
   - route-fail-closed
   - transcriber-no-authority
   - job-staleness-bounded
   - canceled-work-silent
   - router-no-authority
   - slow-path-only-after-route
   - reasoner-proposes-only
   - proposal-identity-bound
   - contract-fail-closed
   - action-schema-fail-closed
   - action-no-credentials
   - catalog-version-pinned
   - policy-before-execution
   - policy-three-outcomes
   - confirmation-exact-and-expiring
   - confirmation-single-use
   - catalog-reviewed-before-active
   - runtime-cannot-mutate-capability
   - tool-schema-provenance
   - tool-allowlist-only
   - credential-isolation
   - tool-output-filtered
   - tool-result-not-sole-truth
   - hot-state-minimized
   - hot-state-ttl
   - ledger-append-only
   - ledger-minimized
   - ledger-integrity-fail-closed
   - response-filtered
   - memory-provenance-bound
   - memory-not-sole-truth
   - memory-deletable
   - talker-no-authority
   - model-boundaries-explicit
6. Each conjunctive guard named in the machine matrices has at least one falsifying-clause test for each independent clause, and every actor has an integration/property test with the real local dependency or a contract-tested local stand-in.
7. The implementation has no network import, credential read, subprocess call, durable service dependency, or semantic-memory dependency.
8. `modelith lint design/domain.modelith.yaml --completeness error`, `machinery lint design/machines`, `machinery oracle design/machines`, and `machinery check design` are green with zero blocking findings.
9. The complete existing suite remains green, including the prior 164 tests.

## Testing Requirements

- RED phase: tests only; commit subject contains `tdd-red`.
- GREEN phase: implementation only; RED test files remain unchanged.
- Unit tests: malformed oracle input, duplicate/unknown ids, invariant count, and parser boundaries.
- Integration/property tests: real local transition cases, ledger verification, policy/confirmation, renderer filtering, privacy canaries, capability red-team, and tool output filtering.
- E2E tests are not in this story; the blocked M0 capstone owns the full gate.
- Commands:
  - `pytest -q tests/test_machinery_oracles.py tests/test_machinery_invariants.py`
  - `pytest -q`
  - `modelith lint design/domain.modelith.yaml --completeness error`
  - `machinery lint design/machines`
  - `machinery oracle design/machines`
  - `machinery check design`
- No mocks of any kind are permitted in the oracle integration tests.

## Skills To Use

- `project-standards`: typed parser and contract discipline.
- `pvg`: story transitions only.
- `machinery`: oracle generation and design gates.

## Delivery Requirements

- Paste exact RED failure summary and GREEN test output.
- Paste every deterministic gate command and exit status.
- Include a stable-id coverage table with denominator 62.
- Include an invariant coverage table with denominator 36.
- Include an AC verification table.
- Record the final commit SHA.

## nd_contract

status: new

### evidence

- Created from machinery design milestone M0.
- Oracle denominator at creation: 62.
- Invariant denominator at creation: 36.

### proof

- [ ] Pending RED/GREEN implementation.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T18:13:49Z dep_added: blocks TRS-le6s

## Links
- Parent: [[TRS-d8vq]]
- Blocks: [[TRS-le6s]]

## Comments
