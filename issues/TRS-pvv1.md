---
id: TRS-pvv1
title: "M2 voice session and turn contracts"
status: open
priority: 1
type: task
created_at: 2026-09-20T00:01:53Z
created_by: speed
updated_at: 2026-09-20T00:01:53Z
content_hash: "sha256:09c97762a7ea8c330ea97f73d4656f2b6d1bdc7ee19e44ce8d24d445fff89060"
---

## Description
## Description

Implement milestone M2 from `design/BUILD.md`: the offline VoiceSession and ConversationTurn behavioral layer, including typed/spoken parity, one active audio-stream arbiter, accessibility metadata, turn-epoch cancellation, ephemeral transcript release, and renderer arbitration.

This milestone remains entirely local and deterministic. It adds no live PersonaPlex, Voxtral, Jev, durable store, tool execution, network inference, credential, or semantic-memory dependency.

## Epic Outcomes

- A single-operator voice session follows the authoritative VoiceSession machine.
- A turn follows the authoritative ConversationTurn machine from typed transcript through routing, slow-path wait, cancellation or response, and terminal release.
- Raw transcript values are processing-only and disappear on terminal or session closure.
- Typed and spoken presentation carry the same bounded semantic payload and explicit accessibility metadata.
- One audio/response stream may be active at a time; active user speech outranks stale slow-path output.
- Advancing a turn epoch cancels or downgrades superseded slow work.
- All `VOIC-*` and `CONV-*` oracle rows are covered by real tests, not prose claims.

## OUT OF SCOPE

- Live audio capture or playback: M3.
- PersonaPlex, Voxtral, or Jev adapters: M3.
- Redis, PostgreSQL, Mem0, Cognee, Zep, or Letta: M4/M8 or later.
- Tool catalog, tool execution, MAGG, Dagger, Treg, or Context Forge: M5+.
- Changing the seven committed machine definitions or oracle stable ids.

## Acceptance Criteria

1. `VOIC-305554`, `VOIC-e62d1f`, and `VOIC-32ea66` pass through executable behavior.
2. Every `CONV-*` row in `design/machines/ConversationTurn.oracle.md` passes through executable behavior.
3. Privacy canaries prove raw transcript release on terminal and session closure.
4. Renderer arbitration proves one active stream and stale slow-path output cannot overlap active user speech.
5. The complete suite, `machinery check design --impl .`, `machinery lint design/machines`, `machinery oracle design/machines`, and `modelith lint design/domain.modelith.yaml --completeness error` pass.

## Design

- Source milestone: `design/BUILD.md` section 9, M2.
- Session authority: `design/machines/VoiceSession.machine.json`.
- Turn authority: `design/machines/ConversationTurn.machine.json`.
- Architecture boundary: `trs.voice-edge` in `design/ARCHITECTURE.md`.
- Existing edge port: `edge/ports/audio.ts`.

## MANDATORY SKILLS

- pvg: story governance.
- machinery: oracle and architecture gates.

## nd_contract
status: new

### evidence
- Created from accepted M1 commit `f7bc6e0` and the committed M2 build plan.

### proof
- [ ] Pending M2 implementation and capstone evidence.


## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments
