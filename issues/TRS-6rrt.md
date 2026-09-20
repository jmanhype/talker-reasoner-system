---
id: TRS-6rrt
title: "Close one local voice turn through the M2 skeleton"
status: in_progress
priority: 1
type: task
created_at: 2026-09-20T00:01:53Z
created_by: speed
updated_at: 2026-09-20T00:02:54Z
content_hash: "sha256:dd6e61516b792d15eb802b90cb1dcd416389c03fad3dfc7c173e6cdead7d8c57"
parent: TRS-pvv1
blocks: [TRS-ji8y, TRS-fcji, TRS-wwx4]
labels: [walking-skeleton, hard-tdd]
assignee: dev-TRS-6rrt
---

## Description
## Context (Embedded)

M2 starts the real offline voice-edge behavioral layer. The repository already has:

- `edge/ports/audio.ts` with `ProcessingBoundary`, `AudioSessionStatus`, `AudioSessionSnapshot`, and `AudioSessionPort`;
- `talk_reasoner.contracts.scoped_hash(content: str | bytes, *, scope: str, schema_version: str) -> str`;
- `talk_reasoner.routing.classify(fixture: Fixture, *, policy: ThresholdPolicy) -> RoutingDecision`;
- `talk_reasoner.rendering.render_response(outcome: TerminalOutcome, *, constraints: PresentationConstraints) -> RenderedResponse`.

There is still no executable VoiceSession or ConversationTurn implementation. This walking skeleton must establish the end-to-end offline pattern with one non-tool turn before later stories cover slow-path and arbitration breadth.

## USER INTENT

A single operator can open an offline voice session, submit one typed transcript-like fixture input, receive a clean non-tool response, and close the session knowing the transcript was released rather than persisted.

## Goal

Implement the first real VoiceSession and ConversationTurn state objects and a regression test that runs one complete local non-tool turn through session/transcript/route/response/close.

## Non-goals

- No live audio, network, model, durable store, or tool execution.
- No reasoner job integration.
- No slow-path confirmation semantics.

## OUT OF SCOPE

- All `SlowPath` and `AwaitingConfirmation` behavior: the next story owns the remaining transition breadth.
- Audio/response overlap arbitration and accessibility parity: a parallel follow-up story owns that concern.
- Final M2 report: the E2e capstone owns it.

## DIFF BUDGET

- About 5 source/test/config files, under 500 changed LOC.

## Boundary Map

PRODUCES:
- `edge/state/VoiceSession.ts` -> typed `VoiceSession` state operations for `degrade`, `close`, and processing-only release.
- `edge/state/ConversationTurn.ts` -> typed `ConversationTurn` operations for `transcribe`, non-tool route binding, `finish`, and terminal release.
- `tests/test_voice_edge_contracts.py` -> executable oracle-driven skeleton tests citing the rows named below.

CONSUMES:
- (existing): `edge/ports/audio.ts`
  spec: `ProcessingBoundary = "localOnly" | "consentedCloud"` and `AudioSessionSnapshot` fields.
- (existing): `talk_reasoner/contracts.py`
  spec: `scoped_hash(content: str | bytes, *, scope: str, schema_version: str) -> str`.
- (existing): `talk_reasoner/routing.py`
  spec: `classify(fixture: Fixture, *, policy: ThresholdPolicy) -> RoutingDecision`.
- (existing): `talk_reasoner/rendering.py`
  spec: `render_response(outcome: TerminalOutcome, *, constraints: PresentationConstraints) -> RenderedResponse`.

## Acceptance Criteria

1. `VOIC-305554` proves Active --on:degrade--> Degraded with `markSessionDegraded`.
2. `VOIC-e62d1f` proves Active --on:close--> Closed with `releaseProcessingOnlyValues`.
3. `VOIC-32ea66` proves Degraded --on:close--> Closed with `releaseProcessingOnlyValues`.
4. `CONV-02965d` proves transcript validation plus boundary consent before Routed, with a scoped input hash and retained ephemeral value only inside the live turn.
5. `CONV-73bae3` proves a valid non-needs-tools route binds the turn to Responding.
6. `CONV-dab39a` proves finish terminalizes Responding and releases the ephemeral transcript.
7. Duplicate start, degraded restart, and Closed mutations fail or are idempotent exactly as the machine ignores specify; no silent new session is created.
8. The implementation imports no network, credential, durable-service, audio-device, model, or execution dependency.

## Testing Requirements

- RED first: write failing tests keyed by the whole oracle tokens above before implementation.
- Unit/contract tests must execute the real TypeScript state module, not merely grep source.
- Strict TypeScript checking must include the new `edge/state/**/*.ts` files.
- Integration tests: MANDATORY, no mocks; deterministic local compilation/execution and existing Python fixture contracts are allowed.
- Commands:
  - `pytest -q tests/test_voice_edge_contracts.py`
  - `pytest -q`
  - `machinery check design --impl .`

## MANDATORY SKILLS

- pvg: story governance.
- machinery: oracle traceability and architecture gate.

## Delivery Requirements

- Paste RED evidence and final test summaries.
- Record changed-file hashes.
- Include an AC verification table.

## nd_contract
status: new

### evidence
- Created as the M2 walking skeleton from the committed VoiceSession and ConversationTurn machines.

### proof
- [ ] Pending RED/GREEN implementation.


## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-20T00:01:54Z dep_added: blocks TRS-ji8y
- 2026-09-20T00:01:54Z dep_added: blocks TRS-fcji
- 2026-09-20T00:01:54Z dep_added: blocks TRS-wwx4
- 2026-09-20T00:02:54Z status: open -> in_progress
- 2026-09-20T00:02:54Z claimed by dev-TRS-6rrt

## Links
- Parent: [[TRS-pvv1]]
- Blocks: [[TRS-ji8y]], [[TRS-fcji]], [[TRS-wwx4]]

## Comments
