---
id: TRS-g7go
title: "E2e: verify the complete M1 architecture gate"
status: in_progress
priority: 1
type: task
labels: [e2e, capstone, architecture]
parent: TRS-w8ah
created_at: 2026-09-19T20:12:27Z
created_by: speed
updated_at: 2026-09-19T20:26:54Z
content_hash: "sha256:2b38a70fd37edc8701b6f43640160a1d524f8fac386b5f31faae06945056db02"
was_blocked_by: [TRS-m4b1, TRS-h8kc]
assignee: dev-TRS-g7go
follows: [TRS-m4b1, TRS-h8kc]
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
## Implementation Evidence

PROOF:

### CI/Test Results
Commands run:
- `pytest -q -s tests/e2e/test_m1_architecture_gate.py` -> exit 0: 1 passed.
- `pytest -q` -> exit 0: 330 passed.
- `machinery check design --impl .` -> exit 0, 0 blocking findings.
- `pvg verify tests/e2e/test_m1_architecture_gate.py tests/e2e/fixtures/m1-report.json tests/e2e/fixtures/m0-report.json tests/e2e/test_m0_offline_gate.py --include-tests --format=text` -> exit 0.
- `pvg gates --changed c0dbefe` -> exit 0: PASS, 0 warnings.
- `git diff --check` -> exit 0.

Summary: complete M1 architecture gate emits decision `pass` with 19 resolved imports, 5 allowed edges, 4 explicit baselined/ratcheted edges, 8 Python files, 2 TS files, 12 scanned test files, 7 machines, 62 transitions, 36 invariants, 330 collected tests, and zero live dependency classes.

### Final M1 Report
```json
{
  "allowed_edges_verified": 5,
  "baseline_edge_count": 4,
  "collected_test_count": 330,
  "commands": {
    "machinery_check_impl": {
      "command": "machinery check design --impl .",
      "exit_code": 0,
      "output": "== Gc-carrier  invariant carrier reconciliation ==\n  note   relational layers not opted in: policy, integrity, isolation\n  checked: 36 invariants declared, 86 preserves references, 36 carried by preserves\n  ok\n== G2-c4  Architecture Contract ==\n  warn   dependency cycle among trs.reasoning, trs.routing closes only through baseline edges (trs.reasoning -> trs.routing -> trs.reasoning); this is ratchet debt to burn down, not declared intent; the cycle disappears with the baselined edge\n  checked: 11 boundaries, 13 externals, 24 allow rules, 60 transitive pairs, 11 deny rules, 4 baseline rules, 16 provided keys, 3 consumed keys, 4 no_path assertions, 11 boundaries with exposes, 26 dsl elements, 11 boundaries bound to dsl, 14 mitigation rows, 27 dependencies with mitigation rows\n== G3-machine  machines + oracle ==\n  checked: 7 machines, 62 transitions, 7 oracles fresh, 51 named units covered\n  ok\n== Gx-trace  cross-layer traceability ==\n  warn   invariant 'action-schema-fail-closed' is carried by preserves but realized by no machine unit or relational layer; its enforcement rests on the prose tables and the tests they name (map it in a machine matrix or a relational layer)\n  warn   invariant 'hot-state-minimized' is carried by preserves but realized by no machine unit or relational layer; its enforcement rests on the prose tables and the tests they name (map it in a machine matrix or a relational layer)\n  warn   invariant 'hot-state-ttl' is carried by preserves but realized by no machine unit or relational layer; its enforcement rests on the prose tables and the tests they name (map it in a machine matrix or a relational layer)\n  warn   invariant 'model-boundaries-explicit' is carried by preserves but realized by no machine unit or relational layer; its enforcement rests on the prose tables and the tests they name (map it in a machine matrix or a relational layer)\n  warn   invariant 'policy-three-outcomes' is carried by preserves but realized by no machine unit or relational layer; its enforcement rests on the prose tables and the tests they name (map it in a machine matrix or a relational layer)\n  warn   invariant 'talker-no-authority' is carried by preserves but realized by no machine unit or relational layer; its enforcement rests on the prose tables and the tests they name (map it in a machine matrix or a relational layer)\n  warn   invariant 'transcriber-no-authority' is carried by preserves but realized by no machine unit or relational layer; its enforcement rests on the prose tables and the tests they name (map it in a machine matrix or a relational layer)\n  checked: 16 entities, 6 lifecycle machines traced, 1 operational machines, 6 lifecycle entities with machines, 6 placement rows with machines, 2 placement rows waived, 1 build mode declared, 1 toolchain section present, 1 state-migration section present, 29 invariants enforced, 29 invariants unit-backed (guard/action/actor), 7 invariants attested only (prose)\n== Gb-plan  build plan structure ==\n  checked: 1 plans, 9 milestones, 9 DoD-bearing milestones, 1 closed milestones, 1 skeleton citations\n  ok\n== Ga-accept  milestone acceptance evidence ==\n  note   commit binding not checked: no --commit and no MACHINERY_COMMIT; CI is expected to pass the reviewed commit\n  checked: 1 plan documents, 9 declared milestones, 1 closed milestones, 1 acceptance files, 1 DoD ids bound, 1 closed milestones with accepted evidence\n  ok\n== G4-import  code respects the contract ==\n  note   ratchet snapshot 2026-09-19, 0 day(s) old\n  checked: 3 dirs pruned by contract ignore, 2 ts files checked, 19 imports resolved, 2 files ignored by contract, 8 python files checked, 12 test files skipped, 5 edges verified, 4 baselined edges, 4 ratcheted edges\n  ok\n== Gt-tests  oracle ids in the test suite ==\n  checked: 12 test files scanned, 7 machines, 62 oracle rows, 7 machines covered by conformance parse\n  ok\n\n0 blocking (ERROR/DRIFT) finding(s)\n",
      "output_tail": [
        "  ok",
        "== Gt-tests  oracle ids in the test suite ==",
        "  checked: 12 test files scanned, 7 machines, 62 oracle rows, 7 machines covered by conformance parse",
        "  ok",
        "",
        "0 blocking (ERROR/DRIFT) finding(s)"
      ]
    }
  },
  "conditions": {
    "allowed_edges": true,
    "edge_dependency_free": true,
    "exact_denominators": true,
    "explicit_debt": true,
    "gate_green": true,
    "imports_resolved": true,
    "no_live_dependencies": true,
    "oracle_tests_scanned": true,
    "python_and_ts_checked": true,
    "suite_collected": true
  },
  "configuration_hashes": {
    "design/ARCHITECTURE.md": "5f128d047392eb171ce5d75a332784fa88a07cc8f6ff3da981fb75a6401fdf3c",
    "design/ratchet.json": "3abdd92afe5b1634e25112901bb248e934810ea7fe4709de81ee17636f8f6576",
    "edge/package.json": "04190bd79af8a2a806f1c6a91b3cf1dcdc58c0999b9ae4bc54ff3d074b371740"
  },
  "decision": "pass",
  "imports_resolved": 19,
  "invariant_count": 36,
  "live_dependency_classes": [],
  "machine_count": 7,
  "python_files_checked": 8,
  "ratcheted_edge_count": 4,
  "schema_version": "trs-m1-architecture-report-v1",
  "test_files_scanned": 12,
  "tool_versions": {
    "machinery": "machinery version v0.3.11",
    "modelith": "modelith version 0.4.0"
  },
  "transition_count": 62,
  "ts_files_checked": 2,
  "utc_window": {
    "ended_at": "2026-09-19T20:26:31.943289Z",
    "started_at": "2026-09-19T20:26:31.442958Z"
  }
}
```

### Commit
- Branch: `story/TRS-g7go`
- SHA: `ab27e09208a987a00fd16cb782e693a1054a7a27`
- Diff: 4 files, 160 insertions, 2 deletions.

### AC Verification
| AC | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Exact implementation-wide command exits green | PASS | Report command is `machinery check design --impl .`; exit 0; 0 blocking. |
| 2 | Nonzero Python/TS imports | PASS | 19 imports resolved, including 2 TS files. |
| 3 | Gt scans suite/oracles | PASS | 12 test files, 7 machines, 62 rows. |
| 4 | Four reviewed ratchet edges exact | PASS | Report and test compare all four edges and six offender files. |
| 5 | Edge package dependency-free | PASS | Private manifest has no dependencies/devDependencies. |
| 6 | No live dependencies | PASS | `live_dependency_classes=[]`. |
| 7 | Complete suite | PASS | 330/330. |
| 8 | Versioned report decision pass | PASS | Report includes hashes, versions, UTC window, denominators, conditions, and decision pass. |

### pvg verify
- `VERIFY: PASSED`.

LEARNINGS:
- E2e files need `Path(__file__).parents[2]` to reach the repository root from `tests/e2e/`.
- One implementation-wide gate can prove Python and TypeScript boundaries without a Node package install.
- Extracting metric parsing and small predicate helpers kept the capstone below complexity thresholds.

### OBSERVATIONS
- `machinery check` still reports the reviewed non-blocking baseline cycle between routing and reasoning; this is intentionally explicit M1 debt.

## nd_contract
status: delivered

### evidence
- Final SHA `ab27e09208a987a00fd16cb782e693a1054a7a27`.
- Full suite 330/330; target M1 gate 1/1.
- Required architecture and quality gates green.

### proof
- [x] AC #1 through AC #8 verified above.

## nd_contract
status: in_progress

### evidence
- Claimed final M1 architecture capstone on 2026-09-19.
- Base epic SHA: c0dbefeea0c03a96a623b5564a508849230abbf4

### proof
- [ ] Emit exact M1 architecture report with implementation-wide denominators and decision pass.

## History
- 2026-09-19T20:12:27Z dep_added: blocked_by TRS-m4b1
- 2026-09-19T20:12:27Z dep_added: blocked_by TRS-h8kc
- 2026-09-19T20:19:01Z dep_removed: was_blocked_by TRS-m4b1
- 2026-09-19T20:21:03Z dep_removed: was_blocked_by TRS-h8kc
- 2026-09-19T20:21:25Z status: open -> in_progress
- 2026-09-19T20:21:25Z auto-follows: linked to predecessor TRS-m4b1
- 2026-09-19T20:21:25Z auto-follows: linked to predecessor TRS-h8kc
- 2026-09-19T20:21:25Z claimed by dev-TRS-g7go
- 2026-09-19T20:26:54Z status: in_progress -> in_progress

## Links
- Parent: [[TRS-w8ah]]
- Was blocked by: [[TRS-m4b1]], [[TRS-h8kc]]
- Follows: [[TRS-m4b1]], [[TRS-h8kc]]

## Comments
