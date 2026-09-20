---
id: TRS-fcji
title: "Arbitrate one M2 response stream with accessibility metadata"
status: open
priority: 1
type: task
created_at: 2026-09-20T00:01:53Z
created_by: speed
updated_at: 2026-09-20T00:01:55Z
content_hash: "sha256:d0cc7c809a98018945f839d0ee4440ec946a1999e8f8a60a6f9dc0187996e7e2"
parent: TRS-pvv1
blocked_by: [TRS-6rrt]
blocks: [TRS-wwx4]
labels: [hard-tdd]
---

## Description
## Context (Embedded)

The architecture requires one coherent voice at a time. `design/ARCHITECTURE.md` says the voice edge owns one-active-audio-stream arbitration, PersonaPlex/clean TTS/later sources compete for that arbiter, and active user speech outranks stale slow-path output. `docs/DESIGN.md` also requires screen-reader/TTS-friendly responses, accessible confirmations, and easy interruption.

The existing renderer already exposes:

```python
render_response(outcome: TerminalOutcome, *, constraints: PresentationConstraints) -> RenderedResponse
```

`PresentationConstraints` currently includes `response_id`, `channel`, `screen_reader`, `max_text_length`, and optional validated action/answer values.

## USER INTENT

A spoken or typed response remains understandable and accessible without two audio streams overlapping or stale slow work interrupting the operator.

## Goal

Implement the M2 edge presentation arbiter: one active audio/response stream, typed/spoken parity, explicit accessibility metadata, active-user priority, and stale-output rejection.

## Non-goals

- No audio device I/O, WebSocket, TTS service, or PersonaPlex adapter.
- No change to renderer forbidden-content filtering.
- No durable storage of presentation content.

## OUT OF SCOPE

- Live adapter reconnection and latency benchmarks: M3.
- Final M2 report: the E2e capstone owns it.

## DIFF BUDGET

- About 4 source/test/config files, under 450 changed LOC.

## Boundary Map

PRODUCES:
- `edge/state/arbitration.ts` -> typed `AccessibilityMetadata`, `ResponseCandidate`, `ArbitrationDecision`, and `PresentationArbiter` with one-active-stream semantics.
- `edge/state/arbitration.ts` -> `PresentationArbiter.submit(candidate: ResponseCandidate) -> ArbitrationDecision`.
- `tests/test_voice_presentation_arbitration.py` -> executable overlap, accessibility, parity, priority, and privacy tests.

CONSUMES:
- TRS-6rrt: `edge/state/ConversationTurn.ts`
  spec: turn id, current epoch, terminal state, and processing-only release contract.
- (existing): `talk_reasoner/rendering.py`
  spec: `render_response(outcome: TerminalOutcome, *, constraints: PresentationConstraints) -> RenderedResponse`.
- (existing): `edge/ports/audio.ts`
  spec: `AudioSessionSnapshot.activeStreamId` and `turnEpoch`.

## Acceptance Criteria

1. A response candidate carries bounded typed text, bounded spoken text, one semantic parity hash, channel, priority, turn epoch, and accessibility metadata.
2. Typed/spoken parity rejects empty/mismatched semantic payloads and never carries raw transcript values.
3. Accessibility metadata explicitly represents screen-reader-friendly text and caption availability; inaccessible channel combinations fail closed.
4. Exactly one stream can be active per session; a second ordinary submission is rejected or superseded according to explicit priority, never overlapped.
5. Active user speech/interruption has higher priority than stale slow-path output.
6. A stale turn epoch is rejected even if its rendered text is otherwise valid.
7. A canceled response cannot become audible as a normal result.
8. The arbiter stores no raw transcript/audio and imports no network, audio-device, model, durable-store, or execution dependency.

## Testing Requirements

- RED first: failing tests for one valid candidate, each invalid accessibility/parity field, overlap, priority, stale epoch, and canceled output.
- Integration tests: MANDATORY, no mocks; invoke the real typed arbiter and the existing renderer contract.
- Commands:
  - `pytest -q tests/test_voice_presentation_arbitration.py`
  - `pytest -q`
  - `machinery check design --impl .`

## MANDATORY SKILLS

- pvg: story governance.
- machinery: architecture-boundary verification.

## Delivery Requirements

- Paste RED evidence and final summaries.
- Record changed-file hashes.
- Include an AC verification table.

## nd_contract
status: new

### evidence
- Created from the M2 accessibility, one-stream, and renderer-arbitration requirements.

### proof
- [ ] Pending RED/GREEN implementation.


## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-20T00:01:54Z dep_added: blocked_by TRS-6rrt
- 2026-09-20T00:01:54Z dep_added: blocks TRS-wwx4

## Links
- Parent: [[TRS-pvv1]]
- Blocks: [[TRS-wwx4]]
- Blocked by: [[TRS-6rrt]]

## Comments
