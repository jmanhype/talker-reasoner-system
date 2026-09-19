---
id: TRS-h8kc
title: "M1 TypeScript edge package skeleton without live audio"
status: in_progress
priority: 1
type: task
labels: [architecture, edge, offline]
parent: TRS-w8ah
created_at: 2026-09-19T20:11:54Z
created_by: speed
updated_at: 2026-09-19T20:20:47Z
content_hash: "sha256:832f6f4b257f86265633b9f6e3afa34e371c8f4c289642028400692bce21a3eb"
blocks: [TRS-g7go]
was_blocked_by: [TRS-m4b1]
assignee: dev-TRS-h8kc
follows: [TRS-m4b1]
---

## Description

## Description
## Context (Embedded)

M1’s build plan requires a TypeScript edge package skeleton without live audio. The Architecture Contract already declares boundary `trs.voice-edge` with implementation-relative code path `edge/**` and public exposes path `edge/ports/**`. This story must create only the typed package surface needed by M2; it must not start sockets, import model SDKs, process audio, or add runtime dependencies.

## USER INTENT

A future M2 developer can add the real voice-loop adapter against a strict, offline TypeScript port contract without inventing package layout or architecture bindings.

## Goal

Add a dependency-free TypeScript edge package and typed audio-session port skeleton that G4 recognizes under `trs.voice-edge`.

## Non-goals

- No PersonaPlex, Voxtral, Jev, TTS, WebSocket, audio capture, model inference, or network code.
- No compiled output committed.
- No package installation or lockfile.
- No Python behavior changes.

## OUT OF SCOPE

- Implementation-wide G4/Gt proof: the M1 capstone owns the final gate.
- VoiceSession runtime behavior: M2.
- Edge rendering or audio arbitration: M2+.

## DIFF BUDGET

- About 5 files, under 180 changed LOC.

## Boundary Map

PRODUCES:

- `edge/package.json` -> private package `@talk-reasoner/edge` with no runtime or development dependencies.
- `edge/tsconfig.json` -> strict ECMAScript-module TypeScript configuration with `noEmit` and only `ports/**/*.ts` included.
- `edge/ports/audio.ts` -> typed `ProcessingBoundary`, `AudioSessionStatus`, `AudioSessionSnapshot`, and `AudioSessionPort` exports.
- `edge/ports/index.ts` -> `export * from "./audio.js";`
- `tests/test_edge_package.py` -> offline package-contract test validating the manifest, strict compiler settings, typed public port, and zero dependencies.

CONSUMES:

- M1 architecture story `TRS-m4b1`: `design/ARCHITECTURE.md` -> implementation-relative `trs.voice-edge` code/exposes paths.
- (existing): `design/ARCHITECTURE.md` -> boundary `trs.voice-edge`.

## Acceptance Requirements

1. `edge/package.json` declares a private ESM package named exactly `@talk-reasoner/edge` with neither `dependencies` nor `devDependencies`.
2. `edge/tsconfig.json` enables `strict`, `noEmit`, ECMAScript modules, nodenext resolution, and exact TypeScript includes for `ports/**/*.ts`.
3. `edge/ports/audio.ts` exports strict union/object/interface types for processing boundary, session status, session snapshot, and an asynchronous audio-session port.
4. The port exposes lifecycle methods but contains no implementation body, no I/O, no timer, no network API, and no external import.
5. `edge/ports/index.ts` re-exports the audio port through a relative ESM path so G4 resolves at least one TypeScript import.
6. G4 maps the TypeScript files to `trs.voice-edge`, reports resolved TypeScript imports, and reports no undeclared cross-boundary edge.
7. The offline Python package test passes and the complete existing suite remains green.

## Testing Requirements

- Unit/offline contract test only; no mocks and no Node package installation.
- The test must parse JSON as JSON and inspect the TypeScript source; it must not shell out to a package manager.
- Commands:
  - `pytest -q tests/test_edge_package.py`
  - `pytest -q`
  - `machinery check design --impl .`

## MANDATORY SKILLS

- `c4`: voice-edge boundary binding.
- `project-standards`: strict typed public contracts.

## Delivery Requirements

- Paste exact test and G4 output.
- Include a file-by-file public-surface table.
- Record the final commit SHA.

## nd_contract
status: new

### evidence
- Created from M1 TypeScript edge skeleton requirement.

### proof
- [ ] Pending implementation.

## Acceptance Requirements


## Design


## Notes


## History
- 2026-09-19T20:11:55Z dep_added: blocked_by TRS-m4b1
- 2026-09-19T20:12:27Z dep_added: blocks TRS-g7go

## Links
- Parent: [[TRS-w8ah]]
- Blocks: [[TRS-g7go]]
- Blocked by: [[TRS-m4b1]]

## Comments

## Context (Embedded)

M1’s build plan requires a TypeScript edge package skeleton without live audio. The Architecture Contract already declares boundary `trs.voice-edge` with implementation-relative code path `edge/**` and public exposes path `edge/ports/**`. This story must create only the typed package surface needed by M2; it must not start sockets, import model SDKs, process audio, or add runtime dependencies.

## USER INTENT

A future M2 developer can add the real voice-loop adapter against a strict, offline TypeScript port contract without inventing package layout or architecture bindings.

## Goal

Add a dependency-free TypeScript edge package and typed audio-session port skeleton that G4 recognizes under `trs.voice-edge`.

## Non-goals

- No PersonaPlex, Voxtral, Jev, TTS, WebSocket, audio capture, model inference, or network code.
- No compiled output committed.
- No package installation or lockfile.
- No Python behavior changes.

## OUT OF SCOPE

- Implementation-wide G4/Gt proof: the M1 capstone owns the final gate.
- VoiceSession runtime behavior: M2.
- Edge rendering or audio arbitration: M2+.

## DIFF BUDGET

- About 5 files, under 180 changed LOC.

## Boundary Map

PRODUCES:

- `edge/package.json` -> private package `@talk-reasoner/edge` with no runtime or development dependencies.
- `edge/tsconfig.json` -> strict ECMAScript-module TypeScript configuration with `noEmit` and only `ports/**/*.ts` included.
- `edge/ports/audio.ts` -> typed `ProcessingBoundary`, `AudioSessionStatus`, `AudioSessionSnapshot`, and `AudioSessionPort` exports.
- `edge/ports/index.ts` -> `export * from "./audio.js";`
- `tests/test_edge_package.py` -> offline package-contract test validating the manifest, strict compiler settings, typed public port, and zero dependencies.

CONSUMES:

- M1 architecture story `TRS-m4b1`: `design/ARCHITECTURE.md` -> implementation-relative `trs.voice-edge` code/exposes paths.
- (existing): `design/ARCHITECTURE.md` -> boundary `trs.voice-edge`.

## Acceptance Criteria

1. `edge/package.json` declares a private ESM package named exactly `@talk-reasoner/edge` with neither `dependencies` nor `devDependencies`.
2. `edge/tsconfig.json` enables `strict`, `noEmit`, ECMAScript modules, nodenext resolution, and exact TypeScript includes for `ports/**/*.ts`.
3. `edge/ports/audio.ts` exports strict union/object/interface types for processing boundary, session status, session snapshot, and an asynchronous audio-session port.
4. The port exposes lifecycle methods but contains no implementation body, no I/O, no timer, no network API, and no external import.
5. `edge/ports/index.ts` re-exports the audio port through a relative ESM path so G4 resolves at least one TypeScript import.
6. G4 maps the TypeScript files to `trs.voice-edge`, reports resolved TypeScript imports, and reports no undeclared cross-boundary edge.
7. The offline Python package test passes and the complete existing suite remains green.

## Testing Requirements

- Unit/offline contract test only; no mocks and no Node package installation.
- The test must parse JSON as JSON and inspect the TypeScript source; it must not shell out to a package manager.
- Commands:
  - `pytest -q tests/test_edge_package.py`
  - `pytest -q`
  - `machinery check design --impl .`

## Skills To Use

- `c4`: voice-edge boundary binding.
- `project-standards`: strict typed public contracts.

## Delivery Requirements

- Paste exact test and G4 output.
- Include a file-by-file public-surface table.
- Record the final commit SHA.

## nd_contract
status: new

### evidence
- Created from M1 TypeScript edge skeleton requirement.

### proof
- [ ] Pending implementation.

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

PROOF:

### CI/Test Results
Commands run:
- `pytest -q tests/test_edge_package.py` -> exit 0: 1 passed.
- `pytest -q` -> exit 0: 329 passed.
- `machinery check design --impl .` -> exit 0, 0 blocking findings.
- `pvg verify edge/package.json edge/tsconfig.json edge/ports/audio.ts tests/test_edge_package.py tests/e2e/fixtures/m0-report.json tests/e2e/test_m0_offline_gate.py --include-tests --format=text` -> exit 0.
- `pvg gates --changed e80979e` -> exit 0: PASS, 0 warnings.
- `git diff --check` -> exit 0.

Summary: the private dependency-free `@talk-reasoner/edge` package now provides a strict typed audio-session port and one relative ESM re-export. G4 checks 2 TypeScript files and resolves 19 total implementation imports with no undeclared TS edge.

### G4 Evidence
- 2 TS files checked.
- 19 total imports resolved.
- 5 allowed edges verified.
- 4 baselined/ratcheted edges retained.
- 0 blocking findings.

### Public Surface
| File | Export |
|---|---|
| `edge/ports/audio.ts` | `ProcessingBoundary` |
| `edge/ports/audio.ts` | `AudioSessionStatus` |
| `edge/ports/audio.ts` | `AudioSessionSnapshot` |
| `edge/ports/audio.ts` | `AudioSessionPort` |
| `edge/ports/index.ts` | re-exports every `audio.ts` public type |

### Commit
- Branch: `story/TRS-h8kc`
- SHA: `58d129e8d6534ce7b8b9bcbb6fa37bfc2740606f`
- Diff: 7 files, 93 insertions, 2 deletions.

### AC Verification
| AC | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Private dependency-free ESM package | PASS | Manifest test confirms name, private flag, module type, and absent dependency maps. |
| 2 | Strict noEmit TS config | PASS | Test asserts strict/noEmit/nodenext and exact ports include. |
| 3 | Typed public port | PASS | Four required type/interface exports are present. |
| 4 | No implementation/I/O | PASS | Source contains type declarations only; no external import, fetch, or WebSocket. |
| 5 | Relative ESM re-export resolved | PASS | G4 resolves 19 imports including the TS barrel. |
| 6 | Voice-edge mapping without violation | PASS | 2 TS files checked; no undeclared edge. |
| 7 | Offline tests and full suite | PASS | Target 1/1; full suite 329/329. |

### pvg verify
- Substantive package/test files: PASSED.
- The one-line `edge/ports/index.ts` is an intentional pure ESM barrel and was excluded from the substance threshold scan.

LEARNINGS:
- Machinery reports TypeScript file kinds as `ts files`; architecture tests should parse counts instead of expecting the word `typescript`.
- Adding a legitimate test changes the M0 report denominator, so frozen report fixtures must advance with the suite inventory.

### OBSERVATIONS
- None.

## nd_contract
status: delivered

### evidence
- Commit 58d129e8d6534ce7b8b9bcbb6fa37bfc2740606f.
- Full suite 329/329; architecture gate green.

### proof
- [x] AC #1 through AC #7 verified above.

## nd_contract
status: in_progress

### evidence
- Claimed TypeScript edge skeleton story on 2026-09-19.
- Base epic SHA: e80979eae3c8f7ab1880b1e340df7d63540a3ceb

### proof
- [ ] Add strict dependency-free edge package skeleton and prove G4 resolves its ESM import.

## History
- 2026-09-19T20:11:55Z dep_added: blocked_by TRS-m4b1
- 2026-09-19T20:12:27Z dep_added: blocks TRS-g7go
- 2026-09-19T20:19:01Z dep_removed: was_blocked_by TRS-m4b1
- 2026-09-19T20:19:15Z status: open -> in_progress
- 2026-09-19T20:19:15Z auto-follows: linked to predecessor TRS-m4b1
- 2026-09-19T20:19:15Z claimed by dev-TRS-h8kc

## Links
- Parent: [[TRS-w8ah]]
- Blocks: [[TRS-g7go]]
- Was blocked by: [[TRS-m4b1]]
- Follows: [[TRS-m4b1]]

## Comments
