---
id: TRS-m4b1
title: "M1 architecture gate: enforce implementation imports with explicit debt"
status: closed
priority: 1
type: task
labels: [architecture, integration, accepted]
parent: TRS-w8ah
created_at: 2026-09-19T20:11:24Z
created_by: speed
updated_at: 2026-09-19T20:19:02Z
content_hash: "sha256:8848a5edc4efefc72620b46b80765ee60a6f88f64f84eb2db4ee3eea41e1b06f"
assignee: dev-TRS-m4b1
closed_at: 2026-09-19T20:19:01Z
close_reason: "Accepted: implementation-wide G4/Gt architecture gate is green with explicit four-edge ratchet."
led_to: [TRS-h8kc]
---

## Description

## Description
## Context (Embedded)

M1 requires `machinery check design --impl .` to be green while all M0 behavior remains unchanged. Current diagnosis is exact:

- With the current nested layout `src/talk_reasoner/**`, G4 scans files but reports `nothing checked: no imports were resolved`, because the implementation-root module derivation does not match the imports `talk_reasoner.*`.
- A disposable validation using implementation-relative contract paths and `--impl src` resolved 18 imports and found four real edges:
  - `trs.renderer -> trs.action-governor` (`talk_reasoner/cli.py` and one more file)
  - `trs.renderer -> trs.reasoning` (`talk_reasoner/cli.py` and one more file)
  - `trs.renderer -> trs.routing` (`talk_reasoner/cli.py`)
  - `trs.reasoning -> trs.routing` (`talk_reasoner/jobs.py`)
- `tests/**` is currently ignored by the Architecture Contract, so Gt reports zero test files even though the M0 suite contains all 62 stable ids.

## USER INTENT

An evaluator can run one implementation-wide architecture command and know that real Python imports and oracle tests are being checked, with every current exception explicitly represented rather than silently ignored.

## Goal

Move the Python package to the repository implementation root, make the Architecture Contract implementation-relative, enable G4/Gt over the current suite, and generate an explicit baseline/ratchet for the four current violations.

## Non-goals

- No runtime behavior change.
- No live adapter or network dependency.
- No broad redesign of routing, reasoning, rendering, or CLI.
- No TypeScript work; the next story owns the edge package skeleton.

## OUT OF SCOPE

- TypeScript package files: owned by the immediately following M1 story.
- Burning down the four baselined edges: later architecture milestones unless a one-line removal is safe.
- Generated oracle edits: forbidden; oracle files are inputs only.

## DIFF BUDGET

- About 9 substantive files, under 300 substantive changed LOC.
- `git mv src/talk_reasoner talk_reasoner` is expected to appear as renames; pure rename lines do not count as substantive edits.

## Boundary Map

PRODUCES:

- `talk_reasoner/*.py` -> preserves every existing public `talk_reasoner` API and import path after moving the package from `src/talk_reasoner` to the repository root.
- `design/ARCHITECTURE.md` -> implementation-relative `code:`/`exposes:` paths, complete Python `modules:` inventories, explicit reviewed `baseline:` rules, and test visibility for Gt.
- `design/ratchet.json` -> generated offender snapshot for every baselined edge (never hand-authored).
- `.machinery.json` -> repository implementation setting accepted by machinery/pvg so `pvg gates --seal` uses the implementation root.
- `tests/test_architecture_contract.py` -> `test_implementation_wide_machinery_gate_resolves_imports_and_tests() -> None`, invoking the real local `machinery check design --impl .` command and asserting nonzero checked imports, scanned test files, and zero blocking findings.

CONSUMES:

- (existing): `talk_reasoner/machinery.py` -> `parse_all_oracles(directory: pathlib.Path) -> dict[str, tuple[OracleTransition, ...]]`
- (existing): `talk_reasoner/machinery.py` -> `parse_invariant_ids(path: pathlib.Path) -> tuple[str, ...]`
- (existing): `design/ARCHITECTURE.md` -> Architecture Contract v2 boundary and dependency-rule YAML
- (existing): `pyproject.toml` -> `[tool.pytest.ini_options] pythonpath`

## Acceptance Requirements

1. The Python package import root is `talk_reasoner/` at repository root; `src/talk_reasoner` contains no tracked Python source, and existing `talk_reasoner.*` imports continue to work without test edits.
2. Path constants in moved modules (`CATALOG_PATH`, design paths, fixture paths) resolve from the new package location.
3. Architecture Contract code/exposes paths are implementation-relative and map every tracked Python source file to exactly one declared boundary or explicit ignore entry.
4. `tests/**` is no longer globally ignored; G4 still skips test files while Gt scans the M0 suite and verifies all 62 committed stable ids by conformance parse or whole-token presence.
5. G4 resolves at least 18 Python imports and verifies at least 5 allowed edges; it must not report an empty check.
6. The four current violating edges are removed or represented by explicit reviewed `baseline:` rules and a freshly generated `design/ratchet.json`; no new unbaselined violation remains.
7. `machinery check design --impl .` exits 0 with zero blocking findings and its Gt section reports scanned test files.
8. All existing 327 tests remain green, plus the new architecture integration test.

## Testing Requirements

- Integration: real local CLI invocation only; no mocks.
- New architecture integration test must fail on zero resolved imports, zero scanned test files, nonzero blocking findings, or missing G4/Gt sections.
- Commands:
  - `pytest -q tests/test_architecture_contract.py`
  - `pytest -q`
  - `machinery baseline design --impl .` before pasting reviewed rules
  - `machinery check design --impl .`
  - `machinery lint design/machines`
  - `machinery oracle design/machines`
  - `modelith lint design/domain.modelith.yaml --completeness error`
  - `pvg gates --changed <story-base>`

## MANDATORY SKILLS

- `c4`: implementation-relative Architecture Contract and G4/Gt semantics.
- `project-standards`: typed move and path safety.

## Delivery Requirements

- Paste the baseline output naming the four edges and offender files.
- Paste the final G4/Gt `checked:` lines.
- Paste all command exit statuses and full-suite count.
- Record the final commit SHA.
- Do not edit any `*.oracle.md`, `design/formal/*`, or hand-author `design/ratchet.json`.

## nd_contract
status: new

### evidence
- Created from M1 diagnosis on 2026-09-19.

### proof
- [ ] Pending implementation.

## Acceptance Requirements


## Design


## Notes


## History
- 2026-09-19T20:11:55Z dep_added: blocks TRS-h8kc
- 2026-09-19T20:12:27Z dep_added: blocks TRS-g7go

## Links
- Parent: [[TRS-w8ah]]
- Blocks: [[TRS-h8kc]], [[TRS-g7go]]

## Comments

## Context (Embedded)

M1 requires `machinery check design --impl .` to be green while all M0 behavior remains unchanged. Current diagnosis is exact:

- With the current nested layout `src/talk_reasoner/**`, G4 scans files but reports `nothing checked: no imports were resolved`, because the implementation-root module derivation does not match the imports `talk_reasoner.*`.
- A disposable validation using implementation-relative contract paths and `--impl src` resolved 18 imports and found four real edges:
  - `trs.renderer -> trs.action-governor` (`talk_reasoner/cli.py` and one more file)
  - `trs.renderer -> trs.reasoning` (`talk_reasoner/cli.py` and one more file)
  - `trs.renderer -> trs.routing` (`talk_reasoner/cli.py`)
  - `trs.reasoning -> trs.routing` (`talk_reasoner/jobs.py`)
- `tests/**` is currently ignored by the Architecture Contract, so Gt reports zero test files even though the M0 suite contains all 62 stable ids.

## USER INTENT

An evaluator can run one implementation-wide architecture command and know that real Python imports and oracle tests are being checked, with every current exception explicitly represented rather than silently ignored.

## Goal

Move the Python package to the repository implementation root, make the Architecture Contract implementation-relative, enable G4/Gt over the current suite, and generate an explicit baseline/ratchet for the four current violations.

## Non-goals

- No runtime behavior change.
- No live adapter or network dependency.
- No broad redesign of routing, reasoning, rendering, or CLI.
- No TypeScript work; the next story owns the edge package skeleton.

## OUT OF SCOPE

- TypeScript package files: owned by the immediately following M1 story.
- Burning down the four baselined edges: later architecture milestones unless a one-line removal is safe.
- Generated oracle edits: forbidden; oracle files are inputs only.

## DIFF BUDGET

- About 9 substantive files, under 300 substantive changed LOC.
- `git mv src/talk_reasoner talk_reasoner` is expected to appear as renames; pure rename lines do not count as substantive edits.

## Boundary Map

PRODUCES:

- `talk_reasoner/*.py` -> preserves every existing public `talk_reasoner` API and import path after moving the package from `src/talk_reasoner` to the repository root.
- `design/ARCHITECTURE.md` -> implementation-relative `code:`/`exposes:` paths, complete Python `modules:` inventories, explicit reviewed `baseline:` rules, and test visibility for Gt.
- `design/ratchet.json` -> generated offender snapshot for every baselined edge (never hand-authored).
- `.machinery.json` -> repository implementation setting accepted by machinery/pvg so `pvg gates --seal` uses the implementation root.
- `tests/test_architecture_contract.py` -> `test_implementation_wide_machinery_gate_resolves_imports_and_tests() -> None`, invoking the real local `machinery check design --impl .` command and asserting nonzero checked imports, scanned test files, and zero blocking findings.

CONSUMES:

- (existing): `talk_reasoner/machinery.py` -> `parse_all_oracles(directory: pathlib.Path) -> dict[str, tuple[OracleTransition, ...]]`
- (existing): `talk_reasoner/machinery.py` -> `parse_invariant_ids(path: pathlib.Path) -> tuple[str, ...]`
- (existing): `design/ARCHITECTURE.md` -> Architecture Contract v2 boundary and dependency-rule YAML
- (existing): `pyproject.toml` -> `[tool.pytest.ini_options] pythonpath`

## Acceptance Criteria

1. The Python package import root is `talk_reasoner/` at repository root; `src/talk_reasoner` contains no tracked Python source, and existing `talk_reasoner.*` imports continue to work without test edits.
2. Path constants in moved modules (`CATALOG_PATH`, design paths, fixture paths) resolve from the new package location.
3. Architecture Contract code/exposes paths are implementation-relative and map every tracked Python source file to exactly one declared boundary or explicit ignore entry.
4. `tests/**` is no longer globally ignored; G4 still skips test files while Gt scans the M0 suite and verifies all 62 committed stable ids by conformance parse or whole-token presence.
5. G4 resolves at least 18 Python imports and verifies at least 5 allowed edges; it must not report an empty check.
6. The four current violating edges are removed or represented by explicit reviewed `baseline:` rules and a freshly generated `design/ratchet.json`; no new unbaselined violation remains.
7. `machinery check design --impl .` exits 0 with zero blocking findings and its Gt section reports scanned test files.
8. All existing 327 tests remain green, plus the new architecture integration test.

## Testing Requirements

- Integration: real local CLI invocation only; no mocks.
- New architecture integration test must fail on zero resolved imports, zero scanned test files, nonzero blocking findings, or missing G4/Gt sections.
- Commands:
  - `pytest -q tests/test_architecture_contract.py`
  - `pytest -q`
  - `machinery baseline design --impl .` before pasting reviewed rules
  - `machinery check design --impl .`
  - `machinery lint design/machines`
  - `machinery oracle design/machines`
  - `modelith lint design/domain.modelith.yaml --completeness error`
  - `pvg gates --changed <story-base>`

## Skills To Use

- `c4`: implementation-relative Architecture Contract and G4/Gt semantics.
- `project-standards`: typed move and path safety.

## Delivery Requirements

- Paste the baseline output naming the four edges and offender files.
- Paste the final G4/Gt `checked:` lines.
- Paste all command exit statuses and full-suite count.
- Record the final commit SHA.
- Do not edit any `*.oracle.md`, `design/formal/*`, or hand-author `design/ratchet.json`.

## nd_contract
status: new

### evidence
- Created from M1 diagnosis on 2026-09-19.

### proof
- [ ] Pending implementation.

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-19.

### proof
- [x] Story closed after accepted label was applied.


## PM Decision
ACCEPTED [2026-09-19]: Evidence reviewed. The root-package move preserves all behavior, G4/Gt now resolve real imports/tests, four current edges are explicitly ratcheted, and the required gate is green with 328 passing tests.

## nd_contract
status: accepted

### evidence
- Reviewed final SHA b4f5a1d893877ba07f52655fd052448a102f7433.
- Delivery proof verification passed 9/9.
- Baseline/ratchet evidence exactly matches the four diagnosed edges.

### proof
- [x] AC #1 through AC #8 verified.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

PROOF:

### CI/Test Results
Commands run:
- `pytest -q tests/test_architecture_contract.py` -> exit 0: 1 passed.
- `pytest -q` -> exit 0: 328 passed.
- `machinery baseline design --impl .` -> exit 0; generated four reviewed baseline rules and `design/ratchet.json`.
- `machinery check design --impl .` -> exit 0, 0 blocking findings.
- `modelith lint design/domain.modelith.yaml --completeness error` -> exit 0, 0 errors/warnings.
- `machinery lint design/machines` -> exit 0, 0 error/drift findings across 7 machines.
- `machinery oracle design/machines` -> exit 0, 62 rows regenerated across 7 files.
- `pvg verify <substantive changed files> --include-tests --format=text` -> exit 0: 10 files, 0 issues.
- `pvg gates --changed fee1a59` -> exit 0: PASS with 15 non-blocking warnings.
- `git diff --check` -> exit 0.

Summary: Python now imports from repository-root package `talk_reasoner`; G4 resolves 18 imports, verifies 5 allowed edges, and ratchets 4 current edges across 6 offender files. Gt scans 10 test files, 7 machines, and 62 oracle rows with conformance-parse coverage. No behavior changed.

### Architecture Baseline
`machinery baseline design --impl .` reported exactly:
- `trs.reasoning -> trs.routing` seen in `talk_reasoner/jobs.py`
- `trs.renderer -> trs.action-governor` seen in `talk_reasoner/cli.py` and `talk_reasoner/rendering.py`
- `trs.renderer -> trs.reasoning` seen in `talk_reasoner/cli.py` and `talk_reasoner/rendering.py`
- `trs.renderer -> trs.routing` seen in `talk_reasoner/cli.py`

The four rules were pasted verbatim under `dependency_rules.baseline`; `design/ratchet.json` is tool-generated and binds the same six offender files.

### Commit
- Branch: `story/TRS-m4b1`
- SHA: `b4f5a1d893877ba07f52655fd052448a102f7433`
- Diff: 23 files, 100 insertions, 45 deletions, dominated by 100%-similar renames.

### G4/Gt Evidence
- G4: 8 Python files checked, 18 imports resolved, 10 test files skipped, 5 edges verified, 4 baselined edges, 4 ratcheted edges.
- Gt: 10 test files scanned, 7 machines, 62 oracle rows, 7 machines covered by conformance parse.
- Required check: 0 blocking ERROR/DRIFT findings.

### AC Verification
| AC | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Root package preserves imports | PASS | Full suite 328/328; tracked source moved from `src/talk_reasoner` to `talk_reasoner`. |
| 2 | Path constants resolve | PASS | Catalog/routing/design/fixture paths use the new root and all tests pass. |
| 3 | Relative contract maps source | PASS | G4 maps all 8 checked Python files; 0 outside-boundary findings. |
| 4 | Gt scans suite | PASS | 10 test files, 62 rows, 7 machines covered by conformance parse. |
| 5 | G4 nonempty | PASS | 18 imports resolved and 5 allowed edges verified. |
| 6 | Four edges explicit | PASS | Four baseline rules plus generated ratchet with six offenders. |
| 7 | Required gate green | PASS | `machinery check design --impl .` exits 0 with 0 blocking findings. |
| 8 | Existing tests plus new gate | PASS | 328 passed, including prior 327 and the new architecture test. |

### pvg verify
- Substantive changed files: `VERIFY: PASSED (10 files scanned, 0 issues)`.
- The unchanged one-line package marker `talk_reasoner/__init__.py` is a pure 100%-similar rename and was not included in the substance scan.

LEARNINGS:
- Machinery G4 derives Python module names from the implementation root; a nested `src/` layout required implementation-relative paths and `--impl src`.
- Making `tests/**` visible does not cause G4 to enforce test imports; G4 skips test files while Gt scans them, so one root can support both gates.
- The existing renderer/reasoning dependency debt is now explicit and ratcheted instead of silently unresolved.

### OBSERVATIONS
- `machinery check` reports a non-blocking baseline cycle through `trs.reasoning <-> trs.routing`; this is expected ratchet debt to burn down later.
- `pvg gates` now scans moved Python modules and reports 15 inherited complexity/file-size warnings, with no new warning from the architecture test.

## nd_contract
status: delivered

### evidence
- Commit b4f5a1d893877ba07f52655fd052448a102f7433.
- Full suite 328/328; required implementation-wide architecture gate green.

### proof
- [x] AC #1 through AC #8 verified above.

## nd_contract
status: in_progress

### evidence
- Claimed M1 architecture gate story on 2026-09-19.
- Base main SHA: fee1a59dba870bc18414af7ec8a240497dd77868

### proof
- [ ] Implement implementation-wide G4/Gt architecture gate without behavior change.

## History
- 2026-09-19T20:11:55Z dep_added: blocks TRS-h8kc
- 2026-09-19T20:12:27Z dep_added: blocks TRS-g7go
- 2026-09-19T20:13:45Z status: open -> in_progress
- 2026-09-19T20:13:45Z claimed by dev-TRS-m4b1
- 2026-09-19T20:18:26Z status: in_progress -> in_progress
- 2026-09-19T20:19:01Z status: in_progress -> closed
- 2026-09-19T20:19:01Z dep_removed: no_longer_blocks TRS-h8kc
- 2026-09-19T20:19:01Z dep_removed: no_longer_blocks TRS-g7go

## Links
- Parent: [[TRS-w8ah]]
- Led to: [[TRS-h8kc]]

## Comments

### 2026-09-19T20:18:47Z speed
## nd_contract
status: delivered

### evidence
- Final architecture-gate SHA: b4f5a1d893877ba07f52655fd052448a102f7433.
- Full suite: 328 passed. Required implementation-wide architecture gate: exit 0, 0 blocking findings.
- G4/Gt: 18 imports resolved, 5 allowed edges verified, 4 baselined/ratcheted edges, 10 test files scanned, 62 oracle rows covered.

### proof
- [x] AC #1 through AC #8 verified in the Implementation Evidence block.
