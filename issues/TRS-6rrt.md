---
id: TRS-6rrt
title: "Close one local voice turn through the M2 skeleton"
status: open
priority: 1
type: task
created_at: 2026-09-20T00:01:53Z
created_by: speed
updated_at: 2026-09-20T00:10:21Z
content_hash: "sha256:4f4e3f38c814c5acc40496fe3c4495e16c267d468283cbfc65174aa447a07403"
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
## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/talker-reasoner-system/.claude/worktrees/dev-TRS-6rrt
pytest -q tests/test_voice_edge_contracts.py
git diff --check
git status --short --branch
git show --stat --oneline HEAD
shasum -a 256 tests/test_voice_edge_contracts.py
machinery check design --impl .
```

### CI/Test Results

```text
targeted RED suite: 8 failed in 2.48s
failure causes: missing edge/state/VoiceSession.ts, missing edge/state/ConversationTurn.ts, and missing state/**/*.ts strict inclusion
git diff --check: PASS
machinery check design --impl .: 0 blocking findings; 13 test files; 7 machines; 62 oracle rows
```

Summary: RED evidence formatting repair for the delivery-proof parser. The authoritative RED commit remains `ebdb66b3707943a3e1ecbf58a55980b63aeb142d`; the test hash remains `dbe561717a4adebfbce3b7eab24ee7605c96f50488d12c04919519e59f5a3003`.

Commit SHA: ebdb66b3707943a3e1ecbf58a55980b63aeb142d

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| RED tests authored | PASS | `tests/test_voice_edge_contracts.py`, 313 lines |
| Genuine executable RED | PASS | 8 failed through strict TypeScript compilation/Node driver |
| No production implementation | PASS | RED commit changes only the test file |
| Design remains valid | PASS | Machinery gate reports 0 blocking findings |

## nd_contract
status: delivered

### evidence
- RED commit SHA: `ebdb66b3707943a3e1ecbf58a55980b63aeb142d`.
- Targeted RED result: 8 failed.
- Machinery result: 0 blocking findings.

### proof
- [x] RED artifact complete.
- [x] Ready for RED approval.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

RED author: `/root/dev_vk_mfn6`.

Commands run independently by the coordinator:

```bash
cd /Users/Shared/HermesWorkspace/talker-reasoner-system/.claude/worktrees/dev-TRS-6rrt
pytest -q tests/test_voice_edge_contracts.py
git diff --check
git status --short --branch
git show --stat --oneline HEAD
shasum -a 256 tests/test_voice_edge_contracts.py
machinery check design --impl .
```

### CI/Test Results

```text
pytest -q tests/test_voice_edge_contracts.py:
FFFFFFFF                                                               [100%]
8 failed in 2.48s

RED causes:
- edge/tsconfig.json include lacks state/**/*.ts
- edge/state/VoiceSession.ts does not exist
- edge/state/ConversationTurn.ts does not exist

git diff --check: PASS
machinery check design --impl .:
0 blocking (ERROR/DRIFT) finding(s)
13 test files scanned
7 machines / 62 oracle rows covered by conformance parse
```

Summary: this is a genuine hard-TDD RED artifact. The tests execute a generated strict TypeScript driver through `tsc` and Node, so failures come from missing real state modules rather than source grep assertions. Production implementation was deliberately absent.

Commit SHA: ebdb66b3707943a3e1ecbf58a55980b63aeb142d

Test SHA-256: dbe561717a4adebfbce3b7eab24ee7605c96f50488d12c04919519e59f5a3003

### AC Verification

| RED requirement | Result | Evidence |
|---|---|---|
| Tests cite named VOIC rows | PASS | VOIC-305554, VOIC-e62d1f, VOIC-32ea66 present |
| Tests cite skeleton CONV rows | PASS | CONV-02965d, CONV-73bae3, CONV-dab39a present |
| Negative boundary/guard cases included | PASS | Empty/credential transcript, unconsented cloud, early route, hash mismatch, restart/closed mutations |
| Tests execute real intended TypeScript behavior | PASS | Strict tsc driver plus Node execution |
| Genuine RED | PASS | 8 failures from missing modules/config |
| Production intentionally not implemented | PASS | Only test file changed |
| Design gate remains green | PASS | Machinery implementation check 0 blocking |

## nd_contract
status: delivered

### evidence
- RED commit SHA: `ebdb66b3707943a3e1ecbf58a55980b63aeb142d`.
- Test SHA-256: `dbe561717a4adebfbce3b7eab24ee7605c96f50488d12c04919519e59f5a3003`.
- Independent RED result: 8 failed.
- Independent machinery result: 0 blocking findings.

### proof
- [x] RED tests authored and committed.
- [x] RED failures are contract failures, not environment accidents.
- [x] No production implementation was added.
- [x] Ready for RED approval and GREEN dispatch.


## History
- 2026-09-20T00:01:54Z dep_added: blocks TRS-ji8y
- 2026-09-20T00:01:54Z dep_added: blocks TRS-fcji
- 2026-09-20T00:01:54Z dep_added: blocks TRS-wwx4
- 2026-09-20T00:02:54Z status: open -> in_progress
- 2026-09-20T00:02:54Z claimed by dev-TRS-6rrt
- 2026-09-20T00:10:05Z status: in_progress -> in_progress
- 2026-09-20T00:10:21Z status: in_progress -> open

## Links
- Parent: [[TRS-pvv1]]
- Blocks: [[TRS-ji8y]], [[TRS-fcji]], [[TRS-wwx4]]

## Comments
