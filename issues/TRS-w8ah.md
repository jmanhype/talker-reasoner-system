---
id: TRS-w8ah
title: "Machinery M1 explicit architecture extraction"
status: closed
priority: 1
type: epic
created_at: 2026-09-19T20:10:48Z
created_by: speed
updated_at: 2026-09-19T20:27:11Z
content_hash: "sha256:24b8cee465450c813cca0d2fc926d0bc5116e53c15e23e7287bada9da121da27"
closed_at: 2026-09-19T20:27:11Z
close_reason: "All M1 architecture stories accepted; implementation-wide G4/Gt gate is green."
---

## Description
## Context

Milestone M1 from `design/BUILD.md` makes the declared architecture executable. M0 proved all 62 transition oracles and 36 invariants offline, but `machinery check design --impl .` still fails because the current Python package is nested under `src/` while the contract expects implementation-relative boundary paths, tests are globally ignored, and four actual cross-boundary edges are not yet represented. M1 also requires a TypeScript edge package skeleton without live audio.

## Goal

Make the current Python and TypeScript source layout resolve against the C4 Architecture Contract, enforce all committed oracle tests through Gt, and either eliminate or explicitly ratchet every current boundary violation while preserving all M0 behavior.

## Non-goals

- No live voice, model inference, credentials, durable stores, remote tools, or semantic memory.
- No behavior changes beyond typed package/boundary extraction.
- No M2 VoiceSession/ConversationTurn implementation.

## OUT OF SCOPE

- Live PersonaPlex, Voxtral, Jev, MAGG, Dagger, Treg, or memory adapters: later milestones.
- Runtime edge behavior or audio processing: M2+.
- Refactoring the four current architecture violations beyond an reviewed baseline unless required to make the gate green: M1 favors explicit debt over broad behavior-risking rewrites.

## DIFF BUDGET

- About 15 source/test/config files across the epic, under 600 changed LOC.
- File moves may show large rename statistics; PM reviews substantive edited lines, not pure renames.

## Acceptance Requirements

1. `machinery check design --impl .` exits 0 with zero blocking findings.
2. G4 resolves the Python and TypeScript import graphs and reports checked imports/edges rather than an empty check.
3. Gt scans the test suite and covers all committed oracle stable ids.
4. Every current cross-boundary violation is either removed or represented by an explicit reviewed baseline plus generated ratchet snapshot.
5. All M0 tests remain green.
6. A TypeScript edge package skeleton exists without live audio or runtime dependencies.

## Testing Requirements

- `pytest -q`
- `machinery check design --impl .`
- `machinery lint design/machines`
- `machinery oracle design/machines`
- `modelith lint design/domain.modelith.yaml --completeness error`
- `pvg gates --changed <story-base>`

## nd_contract
status: new

### evidence
- Created from `design/BUILD.md` Milestone M1 after M0 closure.

### proof
- [ ] Pending M1 decomposition and implementation.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T20:27:11Z status: open -> closed

## Links


## Comments
