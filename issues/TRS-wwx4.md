---
id: TRS-wwx4
title: "E2e: prove the M2 voice-turn lifecycle"
status: open
priority: 1
type: task
created_at: 2026-09-20T00:01:53Z
created_by: speed
updated_at: 2026-09-20T00:01:55Z
content_hash: "sha256:1ebabf55ac3e121c94c9018394744e762e68dd6110c7120c203a67fece249f53"
parent: TRS-pvv1
blocked_by: [TRS-ji8y]
labels: [capstone, hard-tdd]
was_blocked_by: [TRS-6rrt, TRS-fcji]
---

## Description
## Context (Embedded)

M2 has three implementation stories:

1. the offline VoiceSession/ConversationTurn walking skeleton;
2. complete turn transition and epoch-cancellation breadth;
3. typed/spoken parity, accessibility, and one-stream presentation arbitration.

This capstone is the final M2 evaluator. It must prove those pieces work together through one real local user journey and one interrupted slow-path journey.

## USER INTENT

An evaluator can run one command and know that the offline voice session, turn lifecycle, privacy release, accessibility presentation, and arbitration behavior satisfy the complete M2 gate.

## Goal

Run the full M2 gate and emit one versioned report with exact machine/test denominators, privacy results, arbitration results, and decision `pass`.

## Non-goals

- No new production behavior.
- No live voice/model/durable/tool dependency.
- No design-artifact edits.

## OUT OF SCOPE

- Fixing a failed implementation story: return that story to rework.
- Live routing benchmark/reconnect testing: M3.

## DIFF BUDGET

- About 2 test/report files, under 300 changed LOC.

## Boundary Map

PRODUCES:
- `tests/e2e/test_m2_voice_turn_gate.py` -> `test_complete_m2_voice_turn_gate_emits_pass_report() -> None`, exercising real local session, turn, reasoner-job, renderer, and arbiter components.
- `tests/e2e/fixtures/m2-report.json` -> frozen expected report shape with exact M2 denominators and decision `pass`.

CONSUMES:
- TRS-6rrt: `edge/state/VoiceSession.ts`
  spec: session lifecycle and processing-only release operations.
- TRS-6rrt: `edge/state/ConversationTurn.ts`
  spec: non-tool route/finish behavior and terminal release.
- TRS-ji8y: `edge/state/ConversationTurn.ts`
  spec: complete slow-path, cancellation, confirmation-wait, and epoch operations.
- TRS-fcji: `edge/state/arbitration.ts`
  spec: `PresentationArbiter.submit(candidate: ResponseCandidate) -> ArbitrationDecision`.
- (existing): `talk_reasoner/jobs.py`
  spec: `advance_reasoner_job(job: ReasonerJob, stimulus: object, *, clock: MonotonicClock) -> ReasonerJob`.
- (existing): `talk_reasoner/rendering.py`
  spec: `render_response(outcome: TerminalOutcome, *, constraints: PresentationConstraints) -> RenderedResponse`.

## Acceptance Criteria

1. The E2e journey opens one session and closes it after all turns are terminal.
2. One non-tool turn reaches a clean typed/spoken response and releases its ephemeral transcript.
3. One needs-tools turn reaches waiting-for-confirmation behavior without executing a tool.
4. Advancing that turn epoch terminalizes it, supersedes slow work, and prevents stale normal output.
5. The presentation arbiter proves active user priority, one active stream, accessibility metadata, and typed/spoken parity.
6. Privacy canaries prove no raw transcript appears in terminal state, presentation output, or the report.
7. The report cites exact denominators for all 3 `VOIC-*` rows and all 12 `CONV-*` rows and records decision `pass`; any failure records `hold` and fails the test.
8. Full suite plus machinery, machine lint/oracle, and Modelith gates pass.

## Testing Requirements

- E2e tests ONLY for this story. No unit tests and no new production module.
- No mocks of any kind. Local deterministic fixtures/clocks/subprocesses are allowed.
- Commands:
  - `pytest -q -s tests/e2e/test_m2_voice_turn_gate.py`
  - `pytest -q`
  - `machinery check design --impl .`
  - `machinery lint design/machines`
  - `machinery oracle design/machines`
  - `modelith lint design/domain.modelith.yaml --completeness error`

## MANDATORY SKILLS

- pvg: story governance.
- machinery: final M2 oracle/architecture gate.

## Delivery Requirements

- Paste the complete M2 report JSON.
- Paste targeted and full-suite summaries.
- Record the final commit SHA.

## nd_contract
status: new

### evidence
- Created as the mandatory final M2 capstone.

### proof
- [ ] Pending implementation and completion evidence.


## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-20T00:01:54Z dep_added: blocked_by TRS-6rrt
- 2026-09-20T00:01:54Z dep_added: blocked_by TRS-ji8y
- 2026-09-20T00:01:54Z dep_added: blocked_by TRS-fcji
- 2026-09-20T00:26:07Z dep_removed: was_blocked_by TRS-6rrt
- 2026-09-20T00:43:13Z dep_removed: was_blocked_by TRS-fcji

## Links
- Parent: [[TRS-pvv1]]
- Blocked by: [[TRS-ji8y]]
- Was blocked by: [[TRS-6rrt]], [[TRS-fcji]]

## Comments
