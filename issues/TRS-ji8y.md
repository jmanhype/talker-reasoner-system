---
id: TRS-ji8y
title: "Guard M2 slow-path turns under epoch cancellation"
status: open
priority: 1
type: task
created_at: 2026-09-20T00:01:53Z
created_by: speed
updated_at: 2026-09-20T00:49:38Z
content_hash: "sha256:fe1e28a4fbed98540cc2d3ca71d039eac176930970dc153e4759c44c03de062c"
parent: TRS-pvv1
blocks: [TRS-wwx4]
labels: [hard-tdd, red-approved]
was_blocked_by: [TRS-6rrt]
assignee: dev-TRS-ji8y
follows: [TRS-6rrt, TRS-fcji]
---

## Description
## Context (Embedded)

The M2 skeleton owns a complete non-tool turn. This story completes the ConversationTurn transition breadth for slow work, confirmation waiting, cancellation, and epoch supersession.

The existing slow-work engine exposes:

```python
advance_reasoner_job(job: ReasonerJob, stimulus: object, *, clock: MonotonicClock) -> ReasonerJob
job_terminal_summary(job: ReasonerJob) -> TerminalOutcome
```

`TurnAdvanced(turn_epoch: int)` is the existing reasoner-job stimulus for a superseded epoch. The ConversationTurn implementation must remain the edge owner and must never execute a tool or import the Action Governor/Tool Gateway.

## USER INTENT

When the operator interrupts, changes topic, or cancels while slow work is pending, the old turn terminalizes immediately and its slow work can no longer surface as a normal response.

## Goal

Implement every remaining ConversationTurn route, cancellation, confirmation-wait, epoch-advance, and terminal transition with guard-clause tests.

## Non-goals

- No live interruption transport.
- No new reasoner behavior or tool execution.
- No changes to the committed machine/oracle files.

## OUT OF SCOPE

- Audio/response overlap priority: the parallel arbitration story owns presentation timing.
- Final M2 report: the E2e capstone owns it.

## DIFF BUDGET

- About 3 source/test files, under 450 changed LOC.

## Boundary Map

PRODUCES:
- `edge/state/ConversationTurn.ts` -> complete legal-transition operations for needs-tools routing, epoch advance, cancellation, confirmation wait, and terminal release.
- `tests/test_voice_turn_transitions.py` -> parser-driven/guard-clause coverage for every row named below.

CONSUMES:
- TRS-6rrt: `edge/state/VoiceSession.ts`
  spec: live session status, processing boundary, and close/release operations.
- TRS-6rrt: `edge/state/ConversationTurn.ts`
  spec: `transcribe`, route binding, `finish`, and terminal release contract.
- (existing): `talk_reasoner/jobs.py`
  spec: `advance_reasoner_job(job: ReasonerJob, stimulus: object, *, clock: MonotonicClock) -> ReasonerJob` and `job_terminal_summary(job: ReasonerJob) -> TerminalOutcome`.

## Acceptance Criteria

1. `CONV-87aef6` proves only a valid `needs_tools` route enters SlowPath.
2. `CONV-53ecad` proves Routed cancellation terminalizes and cancels slow work.
3. `CONV-5d0019` proves SlowPath epoch advance terminalizes and supersedes old work.
4. `CONV-a756c5` proves exact policy confirmation is required before AwaitingConfirmation.
5. `CONV-7c39be` proves SlowPath cancellation terminalizes and cancels slow work.
6. `CONV-7f7105` proves AwaitingConfirmation epoch advance terminalizes and supersedes old work.
7. `CONV-8fadcf` proves AwaitingConfirmation cancellation terminalizes and cancels slow work.
8. `CONV-04c2c7` proves Responding cancellation terminalizes and cannot render a normal result afterward.
9. `CONV-f9f25b` proves Receiving cancellation terminalizes before routing.
10. Every conjunctive guard has one falsified-clause test; an invalid route can never enter SlowPath.
11. Every terminal path releases the ephemeral transcript and carries only scoped hashes.

## Testing Requirements

- RED first: failing tests keyed by every whole oracle token above.
- Unit and integration tests: MANDATORY, no mocks. A local deterministic `ReasonerJob`/clock fixture is allowed; no network or tool execution.
- Commands:
  - `pytest -q tests/test_voice_turn_transitions.py`
  - `pytest -q`
  - `machinery check design --impl .`

## MANDATORY SKILLS

- pvg: story governance.
- machinery: oracle and architecture traceability.

## Delivery Requirements

- Paste RED evidence and final summaries.
- Enumerate every cited oracle row in the AC table.
- Record changed-file hashes.

## nd_contract
status: new

### evidence
- Created from the complete committed ConversationTurn oracle after the M2 skeleton.

### proof
- [ ] Pending RED/GREEN implementation.


## Acceptance Criteria


## Design


## Notes


## nd_contract
status: red-approved

### evidence
- RED tests approved via pvg story approve-red on 2026-09-19. Design RED gate: design gate green (machinery check design; design-side gates only (no staged gate list; impl gates run at pvg gates and the seal); design.machinery=on); 9 oracle stable id(s) covered by tests.

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
cd /Users/Shared/HermesWorkspace/talker-reasoner-system/.claude/worktrees/dev-TRS-ji8y
pytest -q tests/test_voice_turn_transitions.py
git diff --check
git status --short --branch
shasum -a 256 tests/test_voice_turn_transitions.py
machinery check design --impl .
```

### CI/Test Results

```text
targeted RED suite: 12 failed, 2 passed in 5.08s
RED cause: ConversationTurn lacks cancel, advanceEpoch, and awaitConfirmation operations
two passes: oracle parser coverage and existing Python reasoner cancellation/epoch contract
git diff --check: PASS
machinery check design --impl .: 0 blocking findings; 15 test files; 7 machines; 62 oracle rows
```

Summary: genuine executable RED covering all nine story-cited ConversationTurn rows, each falsified needs-tools/confirmation guard clause, real Python reasoner cancellation/epoch integration, and terminal privacy release. No production implementation was added.

Commit SHA: 1b68032d8842b31965154fc72081b70fe13776cc

### AC Verification

| RED requirement | Result | Evidence |
|---|---|---|
| CONV-f9f25b | FAIL as intended | Missing cancel operation |
| CONV-87aef6 | FAIL as intended | Missing needs-tools SlowPath operation |
| CONV-53ecad | FAIL as intended | Missing routed cancellation |
| CONV-5d0019 | FAIL as intended | Missing epoch advance |
| CONV-a756c5 | FAIL as intended | Missing confirmation wait |
| CONV-7c39be | FAIL as intended | Missing slow-path cancellation |
| CONV-7f7105 | FAIL as intended | Missing awaiting epoch advance |
| CONV-8fadcf | FAIL as intended | Missing awaiting cancellation |
| CONV-04c2c7 | FAIL as intended | Missing responding cancellation |
| Guard clause falsification | PASS | All named clauses represented |
| Existing design gate | PASS | Machinery 0 blocking |

## nd_contract
status: delivered

### evidence
- RED commit SHA: `1b68032d8842b31965154fc72081b70fe13776cc`.
- Test SHA-256: `7072dd7b6ed64d659ee385eb5a359116085613ca1a922477344789400efafa65`.
- Independent RED result: 12 failed, 2 passed.
- Independent machinery result: 0 blocking.

### proof
- [x] RED tests authored and committed.
- [x] RED failures are missing production operations.
- [x] Existing reasoner contract and oracle coverage verified.
- [x] Ready for RED approval and GREEN dispatch.


## History
- 2026-09-20T00:01:54Z dep_added: blocked_by TRS-6rrt
- 2026-09-20T00:01:54Z dep_added: blocks TRS-wwx4
- 2026-09-20T00:26:07Z dep_removed: was_blocked_by TRS-6rrt
- 2026-09-20T00:43:35Z status: open -> in_progress
- 2026-09-20T00:43:35Z auto-follows: linked to predecessor TRS-6rrt
- 2026-09-20T00:43:35Z claimed by dev-TRS-ji8y
- 2026-09-20T00:49:37Z status: in_progress -> in_progress
- 2026-09-20T00:49:37Z auto-follows: linked to predecessor TRS-fcji
- 2026-09-20T00:49:38Z status: in_progress -> open

## Links
- Parent: [[TRS-pvv1]]
- Blocks: [[TRS-wwx4]]
- Was blocked by: [[TRS-6rrt]]
- Follows: [[TRS-6rrt]], [[TRS-fcji]]

## Comments
