---
id: TRS-m4b1
title: "M1 architecture gate: resolve implementation imports and ratchet debt"
status: open
priority: 1
type: task
labels: [architecture, integration]
parent: TRS-w8ah
created_at: 2026-09-19T20:11:24Z
created_by: speed
updated_at: 2026-09-19T20:11:24Z
content_hash: "sha256:bab76f112c882e5969782d805939f0bb68694f5a2fe2563b2eccac2ec4ac6439"
---

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


## History


## Links
- Parent: [[TRS-w8ah]]

## Comments
