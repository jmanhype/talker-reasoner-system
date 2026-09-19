---
id: TRS-8k9t
title: "M0 walking skeleton: enforce all machinery oracles offline"
status: in_progress
priority: 1
type: feature
labels: [hard-tdd, walking-skeleton, red-approved]
parent: TRS-h031
created_at: 2026-09-19T18:16:58Z
created_by: speed
updated_at: 2026-09-19T19:20:07Z
content_hash: "sha256:324b36b847b83932e1ee7e63c817b3d23858ea97ef80e7fe6caa9254da450f23"
blocks: [TRS-n5pa]
assignee: dev-TRS-8k9t
---

## Description
## Context (Embedded)

Milestone M0 from `design/BUILD.md` turns the committed machinery design into an executable offline test gate. Slice 0 already has 164 passing tests, but it does not yet parse or enforce the seven generated transition oracles or explicitly run all 36 Modelith invariant properties.

The user need is to prove that the designed state machines and invariants govern the existing deterministic contracts before live voice or any remote dependency is authorized.

This is a **hard-TDD RED/GREEN story**. The RED developer writes the tests first and commits them with the literal marker `tdd-red`. The GREEN implementer makes those unchanged tests pass.

## Non-goals

- No live model, durable store, remote tool gateway, or memory platform.
- No TypeScript edge implementation.
- No architecture/package extraction; M1 owns that.
- No change to Slice 0 business behavior unless a failing oracle exposes a real contract defect.

## OUT OF SCOPE

- Live model adapters: deferred to the live voice milestone.
- Durable state: deferred to M4.
- Live tool discovery/execution: deferred to later milestones.
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
7. The implementation has no network import, credential read, subprocess call, durable dependency, or semantic-memory dependency.
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

## Acceptance Criteria


## Design


## Notes
### OBSERVATIONS (diagnostic transparency)
- `machinery check design --impl .` was an initial diagnostic mis-scan over `.venv`; it produced 462 boundary-mapping errors and was not treated as a project result. The story's literal command, `machinery check design`, exited 0 with 0 blocking findings.
- `machinery check design --impl tests` exited 1 with exactly two expected G4 errors because `tests/` is intentionally outside contract boundaries; its Gt section still verified 8 test files, 7 machines, and 62/62 oracle rows covered by conformance parse.
- `machinery check design` emitted seven non-blocking Gx carrier warnings for invariants attested through prose/tests rather than machine units: `action-schema-fail-closed`, `hot-state-minimized`, `hot-state-ttl`, `model-boundaries-explicit`, `policy-three-outcomes`, `talker-no-authority`, and `transcriber-no-authority`. Blocking count remained zero; these are covered by the RED property tests and remain GREEN obligations.
## Implementation Evidence (DELIVERED)

PROOF:

### CI/Test Results
Commands run:
- `pytest -q tests/test_machinery_oracles.py` -> exit 0: **73 passed**.
- `pytest -q --ignore=tests/test_machinery_oracles.py --ignore=tests/test_machinery_invariants.py` -> exit 0: **164 passed**.
- `pytest -q tests/test_machinery_invariants.py` -> exit 1: **64 passed, 25 failed**; combined unchanged RED suite is 237 passed / 25 failed.
- `pvg verify src/talk_reasoner/machinery.py src/talk_reasoner/actions.py src/talk_reasoner/contracts.py src/talk_reasoner/jobs.py src/talk_reasoner/cli.py --format=text` -> exit 0: **VERIFY PASSED (5 files, 0 issues)**.
- `machinery check design` -> exit 0: **0 blocking findings**.
- `pvg story verify-tdd --base 630386c` -> PASS at commit `7a238e50d95cb97675f9db199efbec2f857e55d3`.

Summary: GREEN production work is committed and the complete oracle suite plus all pre-existing tests pass. The remaining 25 failures are all frozen-RED authoring defects or contradictions with the pre-existing suite, not absent machinery behavior. RED files are byte-for-byte unchanged from `2f8052000499280480a0103901582dc709642f11`.

### Commit
- Branch: `story/TRS-8k9t`
- Commit SHA: `7a238e50d95cb97675f9db199efbec2f857e55d3`
- RED SHA unchanged: `2f8052000499280480a0103901582dc709642f11`

RED-DISPUTE: tests/test_machinery_invariants.py -- five authorized-repair classes are required; no RED assertion may be weakened semantically.
1. The file imports `action(job_id, **changes)` and `confirmation(arguments, **changes)` from `test_jobs`, then calls them as `action(action_name, arguments)` and `confirmation()`. This causes 20 of the 25 failures (`TypeError` or wrong action name). Repair with local adapter wrappers while preserving every invalid-case assertion.
2. `p_action_no_credentials` calls `json.dumps` directly on `MappingProxyType`; use a JSON default that materializes mappings. The intended credential assertion is unchanged.
3. Unknown risk expects `apply_policy` to raise, but the committed pre-existing `test_routing.py::test_threshold_boundaries_and_invalid_calibration_fail_safe[unknown]` requires the documented invalid fallback to `unclear`. Repair RED to assert that exact fail-closed fallback, not a raise.
4. Duplicate-terminal expects `append_event` to raise, but committed `test_contracts.py::test_ledger_verifies_detects_integrity_defects` requires append to succeed and `verify_ledger` to report the duplicate. Repair RED to assert verification fails closed after append.
5. `test_reasoner_route_guard...` rejects valid fail-closed outcomes: for `input hash is bound`, the implementation returns a failed job and the test still raises; for expired reasoner consent, `_validate_request` now correctly raises `JobRouteError`, which the test forbids. Accept either fail-closed rejection outcome for each falsified clause.

### AC Verification
| AC | Status | Evidence |
|---|---|---|
| 1 | PASS | RED unchanged and TDD guard passes. |
| 2-4 | PASS | All 73 oracle/parser/conformance tests pass, including 62/62 transitions. |
| 5 | BLOCKED BY RED-DISPUTE | Parser passes exact 36 ids; 25 property tests expose authoring defects above. |
| 6 | BLOCKED BY RED-DISPUTE | Guard tests are present; five defect classes above require authorized repair. |
| 7 | PASS | Production has only local imports/dependencies; offline executor passes oracle suite. |
| 8 | PASS for required design gates | `machinery check design`: 0 blocking. |
| 9 | PARTIAL | Existing suite 164/164; unchanged combined suite 237 pass / 25 disputed failures. |

LEARNINGS:
- The RED author reused `test_jobs` helpers without adapting their signatures; GREEN exposed this immediately once the production module existed.
- Two RED expectations contradicted committed Slice-0 behavior: unknown-risk fallback and append-then-verify ledger integrity.
- Production fixes for no-action consent, provenance enforcement, complete schema bounds, and minimized event rejection were legitimate and kept all 164 old tests green.

## nd_contract
status: delivered

### evidence
- GREEN WIP commit `7a238e50d95cb97675f9db199efbec2f857e55d3`.
- Oracle suite 73/73; existing suite 164/164; disputed invariant suite 64/89.
- RED SHA unchanged and hard-TDD guard passes.

### proof
- [x] Oracle parser and all 62 transition conformance rows pass unchanged.
- [x] Existing 164-test suite remains green.
- [ ] 36-invariant property suite requires the five exact PM-authorized RED repairs listed above.

## nd_contract
status: in_progress

### evidence
- GREEN phase claimed after RED approval on 2026-09-19.
- Frozen RED commit: 2f8052000499280480a0103901582dc709642f11.

### proof
- [ ] GREEN implementation must make the unchanged RED suite pass.

## nd_contract
status: red-approved

### evidence
- RED tests approved via pvg story approve-red on 2026-09-19. Design RED gate: design gate green (machinery check design; design-side gates only (no staged gate list; impl gates run at pvg gates and the seal); design.machinery=on); 62 oracle stable id(s) covered by tests.

### proof
- [ ] GREEN developer must implement against the approved RED tests without modifying them.


## nd_contract
status: delivered

### evidence
- RED commit 2f8052000499280480a0103901582dc709642f11.
- Required design gate: exit 0, 0 blocking findings; seven non-blocking warnings recorded above.
- RED tests: 162 intended failures; existing tests: 164 passed.

### proof
- [x] AC #1: RED evidence complete and ready for PM RED review.
- [ ] AC #2 through AC #9: pending GREEN as itemized in the full delivery evidence.

## Implementation Evidence

Commands run:
- `pytest -q tests/test_machinery_oracles.py tests/test_machinery_invariants.py` -> intended RED, 162 failed; all failures: `talk_reasoner.machinery is missing`.
- `pytest -q --ignore=tests/test_machinery_oracles.py --ignore=tests/test_machinery_invariants.py` -> 164 passed.
- `modelith lint design/domain.modelith.yaml --completeness error` -> exit 0.
- `machinery lint design/machines` -> exit 0.
- `machinery oracle design/machines` -> exit 0.
- `machinery check design` -> exit 0, 0 blocking findings.
- `pvg verify tests/test_machinery_oracles.py tests/test_machinery_invariants.py --include-tests --format=text` -> PASSED.
- `pvg story verify-tdd --base 630386c` -> PASS.

Summary: RED complete. 62/62 stable ids and 36/36 invariants are covered by 162 intentionally failing tests; existing suite is 164/164 green; changed LOC is 899. GREEN remains pending.

Commit SHA: 2f8052000499280480a0103901582dc709642f11

## nd_contract
status: delivered

### evidence
- RED commit 2f8052000499280480a0103901582dc709642f11 on story/TRS-8k9t.
- Commands and results are listed under `## Implementation Evidence`.
- RED coverage: 62/62 oracle rows and 36/36 invariant properties.

### proof
- [x] AC #1: RED tests committed with `tdd-red` and all 162 failures identify missing `talk_reasoner.machinery`.
- [ ] AC #2 through AC #9: pending GREEN implementation/acceptance as itemized in the full RED evidence table above.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

PROOF:

### CI/Test Results
- Commands run:
  - `pytest -q tests/test_machinery_oracles.py tests/test_machinery_invariants.py` -> exit 1 (intended RED): **162 failed in 1.59s**; all 162 failures are `AssertionError: talk_reasoner.machinery is missing`.
  - `pytest -q --ignore=tests/test_machinery_oracles.py --ignore=tests/test_machinery_invariants.py` -> exit 0: **164 passed in 1.98s**.
  - `python3 -m compileall -q tests/test_machinery_oracles.py tests/test_machinery_invariants.py` -> exit 0.
  - `modelith lint design/domain.modelith.yaml --completeness error` -> exit 0: 0 errors, 0 warnings.
  - `machinery lint design/machines` -> exit 0: 0 error/drift findings across 7 machines.
  - `machinery oracle design/machines` -> exit 0: 62 rows regenerated across 7 oracle files.
  - `machinery check design` -> exit 0: 0 blocking ERROR/DRIFT findings.
  - `machinery check design --impl tests` (diagnostic RED coverage check) -> exit 1: Gt-tests **checked 8 test files, 7 machines, 62 oracle rows, 7 machines covered by conformance parse**; the two errors are the expected G4 result of pointing G4 at only the contract-ignored `tests/` tree.
  - `pvg verify tests/test_machinery_oracles.py tests/test_machinery_invariants.py --include-tests --format=text` -> exit 0: **VERIFY: PASSED (2 files scanned, 0 issues)**.
  - `git diff --check` -> exit 0.
- Summary: RED phase complete; target RED suite is 0 passing / 162 intentionally failing, and all failures name the absent production module. Existing suite remains 164/164 green. GREEN is intentionally not run or claimed.
- Coverage: oracle stable-id coverage 62/62; invariant-id property coverage 36/36; changed test diff 899 inserted LOC across 2 files.
- Key output: `162 failed in 1.59s`; unique failure classes were exactly `assert None is not None` and `AssertionError: talk_reasoner.machinery is missing`.

### Commit
- Branch: `story/TRS-8k9t`
- SHA: `2f8052000499280480a0103901582dc709642f11`
- RED marker: commit subject `test(TRS-8k9t): tdd-red -- lock 62 oracle rows and 36 invariants`
- Diff: 2 files changed, 899 insertions(+), within the under-900 changed-LOC budget.

### Stable-ID Coverage (denominator 62)
| Machine | Covered | Stable IDs | Test |
|---|---:|---|---|
| conversationTurn | 12/12 | CONV-02965d CONV-f9f25b CONV-87aef6 CONV-73bae3 CONV-53ecad CONV-5d0019 CONV-a756c5 CONV-7c39be CONV-7f7105 CONV-8fadcf CONV-dab39a CONV-04c2c7 | `test_transition_conformance_parses_and_exercises_every_oracle_row` |
| eventLedger | 9/9 | EVEN-c2c520 EVEN-5feeb7 EVEN-098b63 EVEN-0d5972 EVEN-e9be49 EVEN-f230e3 EVEN-a0faaa EVEN-d90d1d EVEN-379e68 | `test_transition_conformance_parses_and_exercises_every_oracle_row` |
| memoryRecord | 9/9 | MEMO-0697b6 MEMO-ef809c MEMO-814928 MEMO-914d7a MEMO-c8e66c MEMO-b8a59c MEMO-9faf38 MEMO-d9f286 MEMO-8862c9 | `test_transition_conformance_parses_and_exercises_every_oracle_row` |
| reasonerJob | 14/14 | REAS-bc3e49 REAS-5dc4da REAS-974bde REAS-1559cc REAS-f1a17d REAS-c3c792 REAS-0c1f49 REAS-97e8bd REAS-c567aa REAS-0766c3 REAS-0cd65a REAS-345901 REAS-79c30e REAS-b46837 | `test_transition_conformance_parses_and_exercises_every_oracle_row` |
| toolCatalog | 4/4 | TCAT-563b02 TCAT-3a38e4 TCAT-97dc90 TCAT-675b21 | `test_transition_conformance_parses_and_exercises_every_oracle_row` |
| toolExecution | 11/11 | TEXE-6c80b2 TEXE-9297f7 TEXE-8688ba TEXE-0d301e TEXE-49dba9 TEXE-b9c795 TEXE-e18dac TEXE-34eda4 TEXE-782b09 TEXE-a8cfa2 TEXE-30e3a5 | `test_transition_conformance_parses_and_exercises_every_oracle_row` |
| voiceSession | 3/3 | VOIC-305554 VOIC-e62d1f VOIC-32ea66 | `test_transition_conformance_parses_and_exercises_every_oracle_row` |
| **Total** | **62/62** | all committed oracle ids whole-token/parsed at runtime | conformance test |

### Invariant Coverage (denominator 36)
| Invariant ID | Property function | Executing test | Status |
|---|---|---|---|
| `session-processing-boundary` | `p_session_processing_boundary` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `raw-input-ephemeral` | `p_raw_input_ephemeral` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `route-fail-closed` | `p_route_fail_closed` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `transcriber-no-authority` | `p_transcriber_no_authority` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `job-staleness-bounded` | `p_job_staleness_bounded` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `canceled-work-silent` | `p_canceled_work_silent` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `router-no-authority` | `p_router_no_authority` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `slow-path-only-after-route` | `p_slow_path_only_after_route` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `reasoner-proposes-only` | `p_reasoner_proposes_only` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `proposal-identity-bound` | `p_proposal_identity_bound` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `contract-fail-closed` | `p_contract_fail_closed` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `action-schema-fail-closed` | `p_action_schema_fail_closed` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `action-no-credentials` | `p_action_no_credentials` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `catalog-version-pinned` | `p_catalog_version_pinned` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `policy-before-execution` | `p_policy_before_execution` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `policy-three-outcomes` | `p_policy_three_outcomes` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `confirmation-exact-and-expiring` | `p_confirmation_exact_and_expiring` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `confirmation-single-use` | `p_confirmation_single_use` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `catalog-reviewed-before-active` | `p_catalog_reviewed_before_active` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `runtime-cannot-mutate-capability` | `p_runtime_cannot_mutate_capability` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `tool-schema-provenance` | `p_tool_schema_provenance` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `tool-allowlist-only` | `p_tool_allowlist_only` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `credential-isolation` | `p_credential_isolation` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `tool-output-filtered` | `p_tool_output_filtered` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `tool-result-not-sole-truth` | `p_tool_result_not_sole_truth` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `hot-state-minimized` | `p_hot_state_minimized` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `hot-state-ttl` | `p_hot_state_ttl` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `ledger-append-only` | `p_ledger_append_only` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `ledger-minimized` | `p_ledger_minimized` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `ledger-integrity-fail-closed` | `p_ledger_integrity_fail_closed` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `response-filtered` | `p_response_filtered` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `memory-provenance-bound` | `p_memory_provenance_bound` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `memory-not-sole-truth` | `p_memory_not_sole_truth` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `memory-deletable` | `p_memory_deletable` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `talker-no-authority` | `p_talker_no_authority` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| `model-boundaries-explicit` | `p_model_boundaries_explicit` | `test_each_canonical_invariant_has_and_executes_a_real_property` | RED-covered |
| **Total** | **36/36** | exact registry plus 36 parameterized executions | RED-covered |

### AC Verification
| AC # | Requirement | RED status | Evidence |
|---|---|---|---|
| 1 | RED tests committed first with `tdd-red`, fail for the right reason, and are locked before implementation | PASS | Commit `2f8052000499280480a0103901582dc709642f11`; 162 failures all identify absent `talk_reasoner.machinery`; `pvg story verify-tdd --base 630386c` passes. |
| 2 | Oracle loader parser contract | RED tests authored | Parser/positive/error tests are present; implementation pending GREEN. |
| 3 | Runtime-parse all seven oracle files | RED tests authored | 7 filenames and 62 stable ids are enumerated and parsed from committed files at runtime. |
| 4 | Cover all 62 stable ids | PASS at RED-exit coverage | Gt-tests reports 62 oracle rows and 7 machines covered by conformance parse. |
| 5 | Parse and execute all 36 invariant ids | RED tests authored | Exact 36-id registry and parameterized executable property map are present. |
| 6 | Conjunctive guard and actor tests | RED tests authored | Independent-clause parameterized tests and real local actor tests are present. |
| 7 | Offline-only machinery implementation | PENDING GREEN | RED dependency-scan tests are present; no production module exists yet. |
| 8 | Modelith/machinery gates green | PASS for design | Literal `machinery check design` exits 0 with 0 blocking findings. |
| 9 | Complete existing suite green | PASS for existing tests | Existing suite: 164 passed; new RED suite intentionally fails until GREEN. |

### pvg verify
- `VERIFY: PASSED (2 files scanned, 0 issues)`.

LEARNINGS:
- The initial worker draft had one sibling-test import defect (`tests.test_contracts`) that disguised one failure as a package import error; the RED suite now forces every failure through the absent `talk_reasoner.machinery` assertion.
- Formatting-only compaction reduced 974 inserted lines to 899 without deleting any oracle id, invariant property, parameterized guard clause, or actor test.
- Pointing G4 at `tests/` alone cannot be green because tests are deliberately outside contract boundaries; use literal `machinery check design` for design status and the Gt section of the tests diagnostic for oracle coverage.

### OBSERVATIONS (unrelated)
- None.

## nd_contract
status: delivered

### evidence
- RED commit `2f8052000499280480a0103901582dc709642f11` on `story/TRS-8k9t`.
- Intended RED: 162 failed; every failure is `talk_reasoner.machinery is missing`.
- Existing suite: 164 passed.
- Design gates: modelith lint, machinery lint, machinery oracle, and machinery check design all exited 0.
- Coverage: 62/62 stable ids, 36/36 invariant properties, 899 changed LOC.

### proof
- [x] AC #1: RED tests are committed with `tdd-red`, fail only for missing machinery support, and are ready for RED approval/locking.
- [ ] AC #2: GREEN implementation must satisfy the oracle parser contract.
- [ ] AC #3: GREEN implementation must runtime-load all seven oracle files.
- [ ] AC #4: RED-exit coverage is complete at 62/62; GREEN must make conformance pass.
- [ ] AC #5: RED-exit coverage is complete at 36/36; GREEN must make properties pass.
- [ ] AC #6: GREEN must make guard-falsification and actor tests pass.
- [ ] AC #7: GREEN must keep the implementation offline-only.
- [ ] AC #8: GREEN must retain green design gates.
- [ ] AC #9: GREEN must make the complete suite pass, including the existing 164 tests.

## History
- 2026-09-19T18:16:58Z dep_added: blocks TRS-n5pa
- 2026-09-19T18:18:02Z status: open -> in_progress
- 2026-09-19T18:18:02Z claimed by dev-TRS-8k9t
- 2026-09-19T19:05:03Z status: in_progress -> in_progress
- 2026-09-19T19:08:07Z status: in_progress -> open
- 2026-09-19T19:08:24Z status: open -> in_progress
- 2026-09-19T19:08:24Z claimed by dev-TRS-8k9t

## Links
- Parent: [[TRS-h031]]
- Blocks: [[TRS-n5pa]]

## Comments
