---
id: TRS-h8kc
title: "M1 TypeScript edge package skeleton without live audio"
status: open
priority: 1
type: task
labels: [architecture, edge, offline]
parent: TRS-w8ah
created_at: 2026-09-19T20:11:54Z
created_by: speed
updated_at: 2026-09-19T20:11:54Z
content_hash: "sha256:7593effb9c2eb59d0ac5977a069d77de82a45a9a1a57fb3ed56abb9fb8de2479"
blocked_by: [TRS-m4b1]
blocks: [TRS-g7go]
---

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


## History
- 2026-09-19T20:11:55Z dep_added: blocked_by TRS-m4b1
- 2026-09-19T20:12:27Z dep_added: blocks TRS-g7go

## Links
- Parent: [[TRS-w8ah]]
- Blocks: [[TRS-g7go]]
- Blocked by: [[TRS-m4b1]]

## Comments
