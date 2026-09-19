---
id: TRS-g7go
title: "E2e: verify the complete M1 architecture gate"
status: open
priority: 1
type: task
labels: [e2e, capstone, architecture]
parent: TRS-w8ah
created_at: 2026-09-19T20:12:27Z
created_by: speed
updated_at: 2026-09-19T20:12:57Z
content_hash: "sha256:c49af99ace380702cdf4879ef29b6ea62c5dfe8aa1762caa7db488c0342f6c24"
blocked_by: [TRS-h8kc]
was_blocked_by: [TRS-m4b1]
---

## Description

## Description
## Context (Embedded)

M1 has two implementation stories: the Python implementation-wide architecture gate and the dependency-free TypeScript edge skeleton. This capstone is the final M1 evaluator check. It must prove the real implementation root, import graph, oracle tests, baselined debt, and edge package work together without live dependencies.

## USER INTENT

An evaluator can run one offline M1 gate and know that Python and TypeScript are bound to the declared C4 boundaries, every oracle test remains enforced, every current exception is ratcheted, and no live audio/model/tool dependency was introduced.

## Goal

Run the complete implementation-wide M1 gate and emit one versioned report with exact import/test/baseline/dependency denominators and decision `pass`.

## Non-goals

- No new parser, runtime behavior, adapter, or package dependency.
- No M2 voice-loop implementation.
- No generated design-artifact edits.

## OUT OF SCOPE

- Fixing architecture debt found by the capstone: return the owning story to rework.
- Refactoring complexity warnings inherited from M0: track separately.

## DIFF BUDGET

- About 2 test/report files, under 200 changed LOC.

## Boundary Map

PRODUCES:

- `tests/e2e/test_m1_architecture_gate.py` -> `test_complete_m1_architecture_gate_emits_pass_report() -> None`, invoking real local `machinery check design --impl .`, inventorying the suite and dependencies, validating ratchet/edge shape, and emitting the final report.
- `tests/e2e/fixtures/m1-report.json` -> frozen expected report shape with import/test/baseline/dependency denominators and decision `pass`.

CONSUMES:

- `TRS-m4b1`: `design/ARCHITECTURE.md` -> implementation-relative Architecture Contract and explicit baseline rules.
- `TRS-m4b1`: `design/ratchet.json` -> generated offender snapshot.
- `TRS-h8kc`: `edge/package.json` -> private dependency-free `@talk-reasoner/edge` manifest.
- `TRS-h8kc`: `edge/ports/audio.ts` -> strict typed audio-session port exports.
- (existing): `talk_reasoner/machinery.py` -> `parse_all_oracles(directory: pathlib.Path) -> dict[str, tuple[OracleTransition, ...]]`.

## Acceptance Requirements

1. The capstone invokes the exact command `machinery check design --impl .`; it must exit 0 with zero blocking findings.
2. G4 reports nonzero resolved imports, includes the TypeScript edge import graph, and reports no empty-check error.
3. Gt scans at least 11 real test files and covers all 7 machines / 62 oracle rows.
4. The generated ratchet contains exactly the four reviewed M1 baseline edges and their current offender files.
5. The edge package remains private and dependency-free.
6. The implementation scan finds zero network, credential-store, durable-service, remote-tool, or semantic-memory dependency imports; local deterministic CLI subprocesses remain allowed.
7. The complete suite passes with all prior M0 tests plus the M1 tests; expected total is 330 unless a PM-approved repair changes the denominator, in which case the frozen report must be updated in the same accepted change.
8. The final report includes schema version, UTC window, tool versions/configuration hashes, imports resolved, edges verified, baseline count, scanned test count, machine/transition/invariant counts, live dependency classes, and explicit `decision: pass`. Any failed condition emits `hold` and fails the test.

## Testing Requirements

- E2E tests ONLY. No unit tests and no new production module.
- No mocks of any kind.
- Local deterministic subprocess invocation of `machinery` and `pytest --collect-only` is allowed.
- Commands:
  - `pytest -q -s tests/e2e/test_m1_architecture_gate.py`
  - `pytest -q`
  - `machinery check design --impl .`

## MANDATORY SKILLS

- `c4`: final G4/Gt interpretation.
- `machinery`: deterministic architecture gate.

## Delivery Requirements

- Paste the complete final M1 report JSON.
- Paste targeted and full-suite summaries.
- Paste exact G4/Gt/ratchet counts.
- Record the final commit SHA.

## nd_contract
status: new

### evidence
- Created as the mandatory final M1 capstone.

### proof
- [ ] Pending implementation.

## Acceptance Requirements


## Design


## Notes


## History
- 2026-09-19T20:12:27Z dep_added: blocked_by TRS-m4b1
- 2026-09-19T20:12:27Z dep_added: blocked_by TRS-h8kc

## Links
- Parent: [[TRS-w8ah]]
- Blocked by: [[TRS-m4b1]], [[TRS-h8kc]]

## Comments

## Context (Embedded)

M1 has two implementation stories: the Python implementation-wide architecture gate and the dependency-free TypeScript edge skeleton. This capstone is the final M1 evaluator check. It must prove the real implementation root, import graph, oracle tests, baselined debt, and edge package work together without live dependencies.

## USER INTENT

An evaluator can run one offline M1 gate and know that Python and TypeScript are bound to the declared C4 boundaries, every oracle test remains enforced, every current exception is ratcheted, and no live audio/model/tool dependency was introduced.

## Goal

Run the complete implementation-wide M1 gate and emit one versioned report with exact import/test/baseline/dependency denominators and decision `pass`.

## Non-goals

- No new parser, runtime behavior, adapter, or package dependency.
- No M2 voice-loop implementation.
- No generated design-artifact edits.

## OUT OF SCOPE

- Fixing architecture debt found by the capstone: return the owning story to rework.
- Refactoring complexity warnings inherited from M0: track separately.

## DIFF BUDGET

- About 2 test/report files, under 200 changed LOC.

## Boundary Map

PRODUCES:

- `tests/e2e/test_m1_architecture_gate.py` -> `test_complete_m1_architecture_gate_emits_pass_report() -> None`, invoking real local `machinery check design --impl .`, inventorying the suite and dependencies, validating ratchet/edge shape, and emitting the final report.
- `tests/e2e/fixtures/m1-report.json` -> frozen expected report shape with import/test/baseline/dependency denominators and decision `pass`.

CONSUMES:

- `TRS-m4b1`: `design/ARCHITECTURE.md` -> implementation-relative Architecture Contract and explicit baseline rules.
- `TRS-m4b1`: `design/ratchet.json` -> generated offender snapshot.
- `TRS-h8kc`: `edge/package.json` -> private dependency-free `@talk-reasoner/edge` manifest.
- `TRS-h8kc`: `edge/ports/audio.ts` -> strict typed audio-session port exports.
- (existing): `talk_reasoner/machinery.py` -> `parse_all_oracles(directory: pathlib.Path) -> dict[str, tuple[OracleTransition, ...]]`.

## Acceptance Criteria

1. The capstone invokes the exact command `machinery check design --impl .`; it must exit 0 with zero blocking findings.
2. G4 reports nonzero resolved imports, includes the TypeScript edge import graph, and reports no empty-check error.
3. Gt scans at least 11 real test files and covers all 7 machines / 62 oracle rows.
4. The generated ratchet contains exactly the four reviewed M1 baseline edges and their current offender files.
5. The edge package remains private and dependency-free.
6. The implementation scan finds zero network, credential-store, durable-service, remote-tool, or semantic-memory dependency imports; local deterministic CLI subprocesses remain allowed.
7. The complete suite passes with all prior M0 tests plus the M1 tests; expected total is 330 unless a PM-approved repair changes the denominator, in which case the frozen report must be updated in the same accepted change.
8. The final report includes schema version, UTC window, tool versions/configuration hashes, imports resolved, edges verified, baseline count, scanned test count, machine/transition/invariant counts, live dependency classes, and explicit `decision: pass`. Any failed condition emits `hold` and fails the test.

## Testing Requirements

- E2E tests ONLY. No unit tests and no new production module.
- No mocks of any kind.
- Local deterministic subprocess invocation of `machinery` and `pytest --collect-only` is allowed.
- Commands:
  - `pytest -q -s tests/e2e/test_m1_architecture_gate.py`
  - `pytest -q`
  - `machinery check design --impl .`

## Skills To Use

- `c4`: final G4/Gt interpretation.
- `machinery`: deterministic architecture gate.

## Delivery Requirements

- Paste the complete final M1 report JSON.
- Paste targeted and full-suite summaries.
- Paste exact G4/Gt/ratchet counts.
- Record the final commit SHA.

## nd_contract
status: new

### evidence
- Created as the mandatory final M1 capstone.

### proof
- [ ] Pending implementation.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T20:12:27Z dep_added: blocked_by TRS-m4b1
- 2026-09-19T20:12:27Z dep_added: blocked_by TRS-h8kc
- 2026-09-19T20:19:01Z dep_removed: was_blocked_by TRS-m4b1

## Links
- Parent: [[TRS-w8ah]]
- Blocked by: [[TRS-h8kc]]
- Was blocked by: [[TRS-m4b1]]

## Comments
