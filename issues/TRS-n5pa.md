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
updated_at: 2026-09-19T19:30:26Z
content_hash: "sha256:ed96d308cd0d5da96486d1042d459aaae3daadb4bd08ca045cc0670b9fb133a1"
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
## Implementation Evidence (DELIVERED)

PROOF:

### CI/Test Results
Commands run:
- `pytest -q -s tests/e2e/test_m0_offline_gate.py` -> exit 0: **1 passed in 0.41s**.
- `pytest -q` -> exit 0: **327 passed in 2.48s**.
- `pvg verify tests/e2e/test_m0_offline_gate.py tests/e2e/fixtures/m0-report.json --include-tests --format=text` -> exit 0.
- `pvg gates --changed 7715096` -> exit 0: **GATES PASS (0 warnings, 0 skipped; design PASS)**.
- `machinery check design` -> exit 0: **0 blocking findings**.
- `git diff --check` -> exit 0.

Summary: the complete offline M0 gate passes. It inventories and exercises the exact seven machines, 62 transitions, 36 invariants, 327 tests, zero live dependency classes, and emits decision `pass`.

Coverage:
- Machines/oracle files: 7/7.
- Unique transitions exercised: 62/62.
- Invariant properties: 36/36.
- Repository tests: 327/327.
- Live dependency classes: 0.

### Commit
- Branch: `story/TRS-n5pa`
- SHA: `1c616a6762b63c11ffaa5b563ae28d55ed3d19dc`
- Base: `771509656cf7bc4bc343c31a86a0a224c6b5bb4d`
- Diff: 2 files, 154 insertions, within the under-250 LOC budget.

### Final M0 Report
```json
{
  "collected_test_count": 327,
  "commands": {
    "machinery_check": {
      "command": "machinery check design",
      "exit_code": 0,
      "stderr_tail": [],
      "stdout_tail": [
        "  checked: 1 plans, 9 milestones, 9 DoD-bearing milestones, 1 skeleton citations",
        "  ok",
        "",
        "0 blocking (ERROR/DRIFT) finding(s)"
      ]
    },
    "machinery_lint": {
      "command": "machinery lint design/machines",
      "exit_code": 0,
      "stderr_tail": [],
      "stdout_tail": [
        "== VoiceSession.machine.json: 3 states ==",
        "  ok",
        "",
        "0 error/drift finding(s) across 7 machine(s)"
      ]
    },
    "modelith_lint": {
      "command": "modelith lint design/domain.modelith.yaml --completeness error",
      "exit_code": 0,
      "stderr_tail": [],
      "stdout_tail": [
        "design/domain.modelith.yaml:",
        "  ok",
        "",
        "0 error(s), 0 warning(s)"
      ]
    }
  },
  "conditions": {
    "all_transitions_conform": true,
    "complete_suite_collected": true,
    "gates_green": true,
    "no_live_dependencies": true,
    "seven_files": true,
    "sixty_two_unique": true,
    "thirty_six_invariants": true
  },
  "configuration_hashes": {
    "config/actions/slice0-v1.json": "ccbf5e14fb1bc3a2f7d13e8365ef00cb6178f7e4a8c8058cd509acace9f58adc",
    "config/routing/slice0-v1.json": "b893d4df476803121c022215cb8e80412b6db44794c8160b6edb3a7b3669d90f",
    "design/domain.modelith.yaml": "b6bb2335ef317075f1ab72655c90864003cf5953a51251f4ba9500839b8d84b4"
  },
  "decision": "pass",
  "invariant_count": 36,
  "live_dependency_classes": [],
  "machine_names": [
    "conversationTurn",
    "eventLedger",
    "memoryRecord",
    "reasonerJob",
    "toolCatalog",
    "toolExecution",
    "voiceSession"
  ],
  "oracle_file_count": 7,
  "schema_version": "trs-m0-offline-report-v1",
  "tool_versions": {
    "machinery": "machinery version v0.3.11",
    "modelith": "modelith version 0.4.0"
  },
  "transition_count": 62,
  "utc_window": {
    "ended_at": "2026-09-19T19:30:02.568987Z",
    "started_at": "2026-09-19T19:30:02.233873Z"
  }
}
```

### AC Verification
| AC | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Exactly seven fresh oracle files | PASS | Report `oracle_file_count=7`; machinery lint/check exit 0 and enforce freshness. |
| 2 | Exactly 62 unique stable ids | PASS | Report `transition_count=62`; all transitions conform. |
| 3 | Exactly 36 invariant properties | PASS | Report `invariant_count=36`; all parse in canonical order. |
| 4 | Modelith completeness lint | PASS | Embedded command exit 0, 0 errors/warnings. |
| 5 | Machinery lint | PASS | Embedded command exit 0, 0 error/drift findings. |
| 6 | Machinery design check | PASS | Embedded and external commands exit 0 with 0 blocking findings. |
| 7 | Complete Python suite | PASS | External full suite: 327/327; report inventory count: 327. |
| 8 | No live dependencies | PASS | Report `live_dependency_classes=[]`. Local deterministic CLI subprocesses are explicitly allowed by the story. |
| 9 | Versioned report with hashes, UTC window, denominators, decision | PASS | Final report above includes tool versions, config hashes, UTC window, exact denominators, and `decision: pass`. |

### pvg verify
- `VERIFY: PASSED`.

LEARNINGS:
- The capstone can prove full-suite inventory without recursive execution by using `pytest --collect-only` and then running the complete suite as the delivery command.
- Namespacing configuration hashes by repository-relative path avoids collisions between routing/action files both named `slice0-v1.json`.
- Extracting the collection inventory and transition loop kept the E2E function below the complexity threshold.

### OBSERVATIONS (unrelated)
- None.

## nd_contract
status: delivered

### evidence
- Final SHA `1c616a6762b63c11ffaa5b563ae28d55ed3d19dc`.
- Target gate: 1 passed; full suite: 327 passed.
- Required deterministic gates: all exit 0; pvg gates reports 0 warnings.

### proof
- [x] AC #1 through AC #9 verified above.

## nd_contract
status: in_progress

### evidence
- Claimed final M0 capstone after accepted/merged TRS-8k9t.
- Base epic SHA: 771509656cf7bc4bc343c31a86a0a224c6b5bb4d.

### proof
- [ ] Implement offline E2E gate and frozen report contract.

## History
- 2026-09-19T18:16:58Z dep_added: blocked_by TRS-8k9t
- 2026-09-19T19:25:21Z dep_removed: was_blocked_by TRS-8k9t
- 2026-09-19T19:25:21Z status: open -> in_progress
- 2026-09-19T19:25:21Z auto-follows: linked to predecessor TRS-8k9t
- 2026-09-19T19:25:21Z claimed by dev-TRS-n5pa
- 2026-09-19T19:25:22Z status: in_progress -> open
- 2026-09-19T19:27:05Z status: open -> in_progress
- 2026-09-19T19:27:05Z claimed by dev-TRS-n5pa

## Links
- Parent: [[TRS-h031]]
- Was blocked by: [[TRS-8k9t]]
- Follows: [[TRS-8k9t]]

## Comments

### 2026-09-19T19:25:22Z speed
loop: reset orphaned in_progress to open (no developer worktree found; prior session presumed dead)
