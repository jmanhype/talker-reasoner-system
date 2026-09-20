---
id: TRS-wwx4
title: "E2e: prove the M2 voice-turn lifecycle"
status: closed
priority: 1
type: task
created_at: 2026-09-20T00:01:53Z
created_by: speed
updated_at: 2026-09-20T01:11:54Z
content_hash: "sha256:efba5ac497feeb699578ae08e8fd2882ec0decd91f40a4e4a4630cd4738001e6"
parent: TRS-pvv1
labels: [capstone, hard-tdd, red-approved, delivered, accepted]
was_blocked_by: [TRS-6rrt, TRS-fcji, TRS-ji8y]
assignee: dev-TRS-wwx4
follows: [TRS-6rrt, TRS-fcji, TRS-ji8y]
closed_at: 2026-09-20T01:11:54Z
close_reason: "Accepted: independently reran the real local M2 E2e journey, full 363-test suite, strict TypeScript compile, machinery implementation/machine/oracle/Modelith gates, hard-TDD verification, scoped gates/verify, and diff checks. The frozen report has 18/18 conditions true, 4/4 privacy checks, 5/5 arbitration checks, exact 3 VOIC + 12 CONV denominators, zero tool executions, and decision pass."
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


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/talker-reasoner-system/.claude/worktrees/dev-TRS-wwx4
pytest -q -s tests/e2e/test_m2_voice_turn_gate.py
pytest -q
tsc -p edge
machinery check design --impl .
machinery lint design/machines
machinery oracle design/machines
modelith lint design/domain.modelith.yaml --completeness error
pvg story verify-tdd --base 3e69e71
pvg gates tests/e2e/test_m2_voice_turn_gate.py tests/e2e/fixtures/m2-report.json
pvg verify tests/e2e/test_m2_voice_turn_gate.py tests/e2e/fixtures/m2-report.json --include-tests --format=text
git diff --check
```

### CI/Test Results

```text
targeted M2 E2e gate: 1 passed in 0.95s
full suite: 363 passed in 12.17s
strict TypeScript compile: exit 0
machinery implementation gate: 0 blocking findings; 5 TS files; 21 imports; 5 edges; 16 test files; 62 oracle rows
machinery machine lint/oracle: 0 error/drift; 7 machines; 62 rows
modelith completeness: 0 errors, 0 warnings
hard-TDD verify: 2 commits checked; 0 unauthorized test edits
scoped pvg gates: PASS, 0 warnings/skips
scoped pvg verify: PASSED, 1 file, 0 issues
git diff --check: PASS
```

### Final M2 report

```text
schema: trs-m2-voice-turn-report-v1
VOIC rows: 3
CONV rows: 12
M2 oracle rows: 15
conditions: 18/18 true
privacy checks: 4/4
arbitration checks: 5/5
reasoner job: canceled / turn_superseded
tool executions: 0
decision: pass
```

The frozen report records session open/close, clean fast response, waiting confirmation, epoch supersession, stale-output silence, transcript/session release, one active stream, active-user priority, accessibility, typed/spoken parity, exact denominators, and no tool execution.

Commit SHA: 5a2fa827033cbc4561e08a698e7709d3261884bd

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. One session opened/closed after terminal turns | PASS | Journey condition true |
| 2. Non-tool clean response/release | PASS | Journey + privacy checks |
| 3. Needs-tools waits confirmation without execution | PASS | Job/report |
| 4. Epoch supersedes slow work and blocks stale normal output | PASS | Canceled `turn_superseded`, silent stale render |
| 5. Arbiter priority/one-stream/accessibility/parity | PASS | 5/5 arbitration checks |
| 6. Privacy canaries | PASS | 4/4, no raw transcript in report |
| 7. Exact 3 VOIC + 12 CONV denominators and decision pass | PASS | Frozen report |
| 8. Full gates | PASS | 363 tests + all machinery/Modelith checks |

## nd_contract
status: delivered

### evidence
- RED commit: `b1802615ab3eebc2b3e63373cdf581c93b0bb1ab`.
- GREEN/seal commit: `5a2fa827033cbc4561e08a698e7709d3261884bd`.
- Report SHA-256: `018671e1f4d840b16b0dbb48d5b815b90afc938b9925ed1df449577848cb58c3`.
- Full suite: 363 passed.

### proof
- [x] AC #1 through #8 verified by real local E2e execution and coordinator reruns.
- [x] No mocks, live adapters, network, credentials, durable stores, or tool execution.
- [x] M2 final decision is pass with exact denominators.


## PM Test-Edit Authorization

Authorize the TRS-wwx4 GREEN completion repair required by its approved E2e test:

- add the missing frozen `tests/e2e/fixtures/m2-report.json` from the real passing journey;
- advance M0/M1 collected-test denominator from 362 to 363;
- advance M1 scanned-test-file denominator from 15 to 16.

The commit subject must include `[test-edit-authorized]`. No oracle assertion may be weakened.

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
cd /Users/Shared/HermesWorkspace/talker-reasoner-system/.claude/worktrees/dev-TRS-wwx4
pytest -q -s tests/e2e/test_m2_voice_turn_gate.py
git diff --check
git status --short --branch
shasum -a 256 tests/e2e/test_m2_voice_turn_gate.py
machinery check design --impl .
```

### CI/Test Results

```text
targeted M2 E2e RED: 1 failed in 0.82s
journey report emitted decision=pass with all 18 conditions true
RED cause: tests/e2e/fixtures/m2-report.json is intentionally absent
git diff --check: PASS
machinery check design --impl .: 0 blocking findings; 16 test files; 7 machines; 62 oracle rows
```

Summary: genuine capstone RED. The real local journey already proves the integrated behavior, but the frozen final report contract is missing, so the gate correctly fails rather than claiming completion without evidence.

Commit SHA: b1802615ab3eebc2b3e63373cdf581c93b0bb1ab

### AC Verification

| RED requirement | Result | Evidence |
|---|---|---|
| Real E2e journey | PASS | Strict TS state modules, Python renderer, deterministic reasoner job, cancellation, and arbiter execute |
| Exact VOIC/CONV denominators | PASS | 3 + 12 stable ids parsed and reported |
| Privacy conditions | PASS | 4/4 |
| Arbitration conditions | PASS | 5/5 |
| Final report contract | FAIL as intended | Missing frozen M2 fixture |
| Design gate | PASS | Machinery 0 blocking |

## nd_contract
status: delivered

### evidence
- RED commit SHA: `b1802615ab3eebc2b3e63373cdf581c93b0bb1ab`.
- Test SHA-256: `da66adc51c823a6e7d7f28da86f25a49ee55d4f1f6914b444cf45eccc1f284fd`.
- Independent RED result: 1 failed.
- Independent machinery result: 0 blocking.

### proof
- [x] RED E2e test authored and committed.
- [x] Journey behavior observed before final report contract exists.
- [x] Missing report fixture is the sole RED failure.
- [x] Ready for RED approval and GREEN fixture/gate completion.


## History
- 2026-09-20T00:01:54Z dep_added: blocked_by TRS-6rrt
- 2026-09-20T00:01:54Z dep_added: blocked_by TRS-ji8y
- 2026-09-20T00:01:54Z dep_added: blocked_by TRS-fcji
- 2026-09-20T00:26:07Z dep_removed: was_blocked_by TRS-6rrt
- 2026-09-20T00:43:13Z dep_removed: was_blocked_by TRS-fcji
- 2026-09-20T00:59:32Z dep_removed: was_blocked_by TRS-ji8y
- 2026-09-20T00:59:53Z status: open -> in_progress
- 2026-09-20T00:59:53Z auto-follows: linked to predecessor TRS-6rrt
- 2026-09-20T00:59:53Z auto-follows: linked to predecessor TRS-fcji
- 2026-09-20T00:59:53Z auto-follows: linked to predecessor TRS-ji8y
- 2026-09-20T00:59:53Z claimed by dev-TRS-wwx4
- 2026-09-20T01:05:35Z status: in_progress -> in_progress
- 2026-09-20T01:05:36Z status: in_progress -> open
- 2026-09-20T01:05:57Z status: open -> in_progress
- 2026-09-20T01:05:57Z claimed by dev-TRS-wwx4
- 2026-09-20T01:11:53Z status: in_progress -> in_progress
- 2026-09-20T01:11:54Z status: in_progress -> closed

## Links
- Parent: [[TRS-pvv1]]
- Was blocked by: [[TRS-6rrt]], [[TRS-fcji]], [[TRS-ji8y]]
- Follows: [[TRS-6rrt]], [[TRS-fcji]], [[TRS-ji8y]]

## Comments
