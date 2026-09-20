---
id: TRS-fcji
title: "Arbitrate one M2 response stream with accessibility metadata"
status: in_progress
priority: 1
type: task
created_at: 2026-09-20T00:01:53Z
created_by: speed
updated_at: 2026-09-20T00:43:13Z
content_hash: "sha256:2237054fea23fd05ac62b4a3c91fee936a9ce36a4b7c8cb511b39d31f79f62c2"
parent: TRS-pvv1
blocks: [TRS-wwx4]
labels: [hard-tdd, red-approved]
was_blocked_by: [TRS-6rrt]
assignee: dev-TRS-fcji
follows: [TRS-6rrt]
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
## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/talker-reasoner-system/.claude/worktrees/dev-TRS-fcji
pytest -q tests/test_voice_presentation_arbitration.py
pytest -q
tsc -p edge
machinery check design --impl .
machinery lint design/machines
machinery oracle design/machines
modelith lint design/domain.modelith.yaml --completeness error
pvg story verify-tdd --base ca61f46
pvg gates edge/state/arbitration.ts
pvg verify edge/state/arbitration.ts --format=text
git diff --check
```

### CI/Test Results

```text
targeted arbitration suite: 10 passed in 4.89s
full suite: 348 passed in 11.02s
strict TypeScript compile: exit 0
machinery implementation gate: 0 blocking findings; 5 TS files; 21 imports; 5 edges; 14 test files; 62 oracle rows
machinery machine lint/oracle: 0 error/drift; 7 machines; 62 rows
modelith completeness: 0 errors, 0 warnings
hard-TDD verify: 3 commits checked; 0 unauthorized test edits
scoped pvg gates: PASS, 0 warnings/skips
scoped pvg verify: PASSED, 1 file, 0 issues
git diff --check: PASS
precise implementation secret-value scan: PASS
```

### PM-authorized harness repair and budget adjudication

The GREEN worker identified a deterministic snapshot-order contradiction and additive milestone denominators. PM authorization was recorded before edits:

- capture the one-stream snapshot before active-user supersession;
- update M0/M1 inventory baselines to 348 tests, 14 scanned test files, and 5 TypeScript files;
- adjudicate the combined 616-line RED-plus-GREEN overrun because the original budget omitted the 423-line executable harness.

The test repair commit carries `[test-edit-authorized]`; hard-TDD verification passes.

Summary: the dependency-free TypeScript PresentationArbiter enforces typed/spoken semantic parity, bounded payloads, screen-reader text and caption availability, one active stream, active-user supersession, stale-epoch rejection, canceled-output rejection, and privacy-safe snapshots without retaining raw transcript/audio.

Commit SHA: d0c268aa6dee5036bff9f744153aae8aa865ccd8

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Candidate shape/parity/channel/priority/epoch/accessibility | PASS | Valid renderer-backed candidate test |
| 2. Parity fail-closed/no raw values | PASS | Empty, mismatch, and raw-value guards |
| 3. Accessibility metadata fail-closed | PASS | Missing screen-reader text, unavailable captions, inaccessible channel |
| 4. One active stream | PASS | Ordinary second submission rejected without overlap |
| 5. Active user outranks stale slow output | PASS | Active-user submission supersedes stale stream |
| 6. Stale epoch rejected | PASS | Current-epoch comparison |
| 7. Canceled output cannot become audible | PASS | Canceled terminal state rejected |
| 8. No raw retention/live dependency | PASS | Privacy snapshot and architecture/import gates |

## nd_contract
status: delivered

### evidence
- RED commit: `a2ffaa67c1c5bd49d7c731254bb5835e6de7a08e`.
- Authorized test repair: `b2465b7cb53b6893fd14da1705d324f9823260f1`.
- GREEN commit: `d0c268aa6dee5036bff9f744153aae8aa865ccd8`.
- Full suite: 348 passed.

### proof
- [x] AC #1 through #8 verified with executable tests and coordinator reruns.
- [x] Hard-TDD RED/authorized-repair/GREEN history passes.
- [x] No live dependency or raw processing value retained.


## PM Test-Edit and Budget Authorization

Authorized sanctioned repair for TRS-fcji RED/GREEN:

1. In `tests/test_voice_presentation_arbitration.py`, capture `overlapArbiter.snapshot` after the ordinary second submission and before active-user supersession. Emit that captured value in the `oneStream` section. The unchanged no-argument property is later read for the post-supersession state and cannot deterministically represent two different active streams at once.
2. Advance M0/M1 collected-test denominator from 338 to 348, M1 scanned test files from 13 to 14, and M1 TypeScript files from 4 to 5. These are additive consequences of the approved RED file and required arbiter module.
3. Adjudicate the story budget overrun: the original “under 450 changed LOC” estimate did not account for the 423-line executable TypeScript compiler/Node RED harness. Authorize this story’s combined 616-line RED-plus-GREEN change because it remains two files, adds no dependency, and implements the full stated accessibility/arbitration AC; future M2 stories should budget executable harness + implementation separately.

The test repair must use `[test-edit-authorized]` in its commit subject and must not weaken any assertion.


## nd_contract
status: red-approved

### evidence
- RED tests approved via pvg story approve-red on 2026-09-19. Design RED gate: design gate green (machinery check design; design-side gates only (no staged gate list; impl gates run at pvg gates and the seal); design.machinery=on); story references no oracle stable ids, id-coverage not applicable.

### proof
- [ ] GREEN developer must implement against the approved RED tests without modifying them.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/talker-reasoner-system/.claude/worktrees/dev-TRS-fcji
pytest -q tests/test_voice_presentation_arbitration.py
git diff --check
git status --short --branch
shasum -a 256 tests/test_voice_presentation_arbitration.py
machinery check design --impl .
```

### CI/Test Results

```text
targeted RED suite: 9 failed, 1 passed in 3.77s
RED cause: edge/state/arbitration.ts does not exist
the one pass checks the existing strict/dependency-free edge configuration
git diff --check: PASS
machinery check design --impl .: 0 blocking findings; 14 test files; 7 machines; 62 oracle rows
```

Summary: genuine executable RED for accessibility, typed/spoken parity, one-stream arbitration, active-user priority, stale epoch rejection, cancellation, bounds, and privacy. Tests invoke the real Python renderer, accepted ConversationTurn API, and intended strict TypeScript arbiter through compiler/Node; they do not merely grep source.

Commit SHA: a2ffaa67c1c5bd49d7c731254bb5835e6de7a08e

### AC Verification

| RED requirement | Result | Evidence |
|---|---|---|
| Valid candidate shape | FAIL as intended | Missing arbiter module |
| Parity and raw-value guards | FAIL as intended | Missing arbiter module |
| Accessibility/channel guards | FAIL as intended | Missing arbiter module |
| Bounds | FAIL as intended | Missing arbiter module |
| One active stream | FAIL as intended | Missing arbiter module |
| Active-user priority | FAIL as intended | Missing arbiter module |
| Stale epoch rejection | FAIL as intended | Missing arbiter module |
| Cancellation rejection | FAIL as intended | Missing arbiter module |
| Privacy snapshot | FAIL as intended | Missing arbiter module |
| Existing design remains green | PASS | Machinery gate 0 blocking |

## nd_contract
status: delivered

### evidence
- RED commit SHA: `a2ffaa67c1c5bd49d7c731254bb5835e6de7a08e`.
- Test SHA-256: `1a8905ac3400f2d38725c6e39f1f3c1f9ac50a9a0ddeb2d80728a73a6b738c5f`.
- Independent RED result: 9 failed, 1 passed.
- Independent machinery result: 0 blocking findings.

### proof
- [x] RED tests authored and committed.
- [x] RED failures are intentional missing-contract failures.
- [x] No production implementation added.
- [x] Ready for RED approval and GREEN dispatch.


## History
- 2026-09-20T00:01:54Z dep_added: blocked_by TRS-6rrt
- 2026-09-20T00:01:54Z dep_added: blocks TRS-wwx4
- 2026-09-20T00:26:07Z dep_removed: was_blocked_by TRS-6rrt
- 2026-09-20T00:26:52Z status: open -> in_progress
- 2026-09-20T00:26:52Z auto-follows: linked to predecessor TRS-6rrt
- 2026-09-20T00:26:52Z claimed by dev-TRS-fcji
- 2026-09-20T00:33:37Z status: in_progress -> in_progress
- 2026-09-20T00:33:38Z status: in_progress -> open
- 2026-09-20T00:33:48Z status: open -> in_progress
- 2026-09-20T00:33:48Z claimed by dev-TRS-fcji

## Links
- Parent: [[TRS-pvv1]]
- Blocks: [[TRS-wwx4]]
- Was blocked by: [[TRS-6rrt]]
- Follows: [[TRS-6rrt]]

## Comments
