---
id: TRS-n5pa
title: "E2e: verify the complete offline M0 machinery gate"
status: in_progress
priority: 1
type: feature
labels: [e2e, capstone]
parent: TRS-h031
created_at: 2026-09-19T18:16:58Z
created_by: speed
updated_at: 2026-09-19T19:25:21Z
content_hash: "sha256:1d88f51fb80396278b7c1256f3fb022b3fc97c29c2d337716229b50e34c8d0cd"
was_blocked_by: [TRS-8k9t]
assignee: dev-TRS-n5pa
follows: [TRS-8k9t]
---

## Description
## Context (Embedded)

The M0 walking-skeleton story adds parser-driven conformance for all 62 machinery oracle rows and explicit properties for all 36 Modelith invariants. This capstone is the final offline gate for epic TRS-h031. It must prove the complete milestone from an operator/evaluator perspective without adding runtime behavior.

## USER INTENT

An evaluator can run one offline M0 gate and know that the canonical domain model, C4 architecture contract, seven state machines, 62 oracle rows, 36 invariant properties, and complete Python test suite are mutually consistent and free of live dependencies.

## Goal

Run the complete M0 gate end to end and emit one versioned report with exact denominators and an explicit pass/hold/rollback/kill decision.

## OUT OF SCOPE

- New parser or transition implementation: TRS-8k9t owns it.
- Live voice, live model inference, credentials, durable stores, remote tools, or semantic memory: later milestones.
- Architecture extraction or G4 import enforcement: M1.
- Modifying generated machinery artifacts.

## DIFF BUDGET

- About 2 test/report files, under 250 changed LOC.

## Boundary Map

PRODUCES:

- `tests/e2e/test_m0_offline_gate.py` -> end-to-end offline M0 gate suite
  Runs the real local verifier and asserts exact machine, transition, oracle, invariant, architecture, test-count, and dependency-exclusion denominators.
- `tests/e2e/fixtures/m0-report.json` -> frozen expected M0 report shape
  Records schema version, seven machine names, 62 oracle rows, 36 invariant ids, zero live dependency classes, and the only valid decision `pass`.

CONSUMES:

- TRS-8k9t: `src/talk_reasoner/machinery.py` -> `parse_all_oracles(directory: pathlib.Path) -> dict[str, tuple[OracleTransition, ...]]`
- TRS-8k9t: `src/talk_reasoner/machinery.py` -> `parse_invariant_ids(path: pathlib.Path) -> tuple[str, ...]`
- TRS-8k9t: `src/talk_reasoner/machinery.py` -> `exercise_transition(case: TransitionCase) -> TransitionResult`
- (existing): `design/BUILD.md` -> M0 milestone and gate requirements.
- (existing): `design/ARCHITECTURE.md` -> Architecture Contract and deferred dependency rules.

## Acceptance Requirements

1. The E2e suite proves exactly seven machine oracle files are present and fresh.
2. The report denominator proves exactly 62 unique stable ids, with no missing or extra id.
3. The report denominator proves exactly 36 invariant properties, with no missing or extra id.
4. The gate proves `modelith lint design/domain.modelith.yaml --completeness error` exits 0.
5. The gate proves `machinery lint design/machines` exits 0.
6. The gate proves `machinery check design` exits 0 with no blocking findings.
7. The gate proves the complete Python suite passes with every prior Slice 0 and M0 test included.
8. Source and test scans prove M0 has no network, credential, subprocess, durable-service, remote-tool, or semantic-memory dependency.
9. The final report includes configuration hashes or tool versions, UTC window, every denominator above, and an explicit `decision: pass`; any failure must produce `hold` and fail the suite.

## Testing Requirements

- E2E tests ONLY. No unit tests and no new production module.
- No mocks of any kind.
- The test may invoke local deterministic CLI binaries (`modelith` and `machinery`) as subprocesses because those binaries are the real dependencies under test.
- Full pytest command:
  - `pytest -q`
- Targeted command:
  - `pytest -q tests/e2e/test_m0_offline_gate.py`

## MANDATORY SKILLS

- `pvg`: story governance only.
- `machinery`: deterministic design gates.

## Delivery Requirements

- Paste exact target E2e output and full-suite output.
- Paste the final M0 report with every denominator and decision.
- Include an AC verification table.
- Record the final commit SHA.

## nd_contract

status: new

### evidence

- Created as the mandatory final capstone of epic TRS-h031.
- Blocked by TRS-8k9t so the walking skeleton lands first.

### proof

- [ ] Pending implementation.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T18:16:58Z dep_added: blocked_by TRS-8k9t
- 2026-09-19T19:25:21Z dep_removed: was_blocked_by TRS-8k9t
- 2026-09-19T19:25:21Z status: open -> in_progress
- 2026-09-19T19:25:21Z auto-follows: linked to predecessor TRS-8k9t
- 2026-09-19T19:25:21Z claimed by dev-TRS-n5pa

## Links
- Parent: [[TRS-h031]]
- Was blocked by: [[TRS-8k9t]]
- Follows: [[TRS-8k9t]]

## Comments
