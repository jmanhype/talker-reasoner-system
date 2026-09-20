---
id: TRS-ji8y
title: "Guard M2 slow-path turns under epoch cancellation"
status: open
priority: 1
type: task
created_at: 2026-09-20T00:01:53Z
created_by: speed
updated_at: 2026-09-20T00:01:55Z
content_hash: "sha256:b37c73e95e53f9323f3086ba86c63d24ef67f7b586e19946742846c6197fa9da"
parent: TRS-pvv1
blocked_by: [TRS-6rrt]
blocks: [TRS-wwx4]
labels: [hard-tdd]
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


## History
- 2026-09-20T00:01:54Z dep_added: blocked_by TRS-6rrt
- 2026-09-20T00:01:54Z dep_added: blocks TRS-wwx4

## Links
- Parent: [[TRS-pvv1]]
- Blocks: [[TRS-wwx4]]
- Blocked by: [[TRS-6rrt]]

## Comments
