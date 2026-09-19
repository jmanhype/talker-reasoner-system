---
id: TRS-ndv6
title: "Run async reasoner proposals through local transport"
status: closed
priority: 1
type: feature
labels: [async, slice-0, accepted]
parent: TRS-pf94
created_at: 2026-09-19T05:29:37Z
created_by: speed
updated_at: 2026-09-19T16:31:15Z
content_hash: "sha256:1840b01df8c60f934da787e8aa54d2f3410ff5044a7a333425c95f6559ba23dd"
was_blocked_by: [TRS-74z8, TRS-9md6]
assignee: dev-TRS-ndv6
follows: [TRS-74z8, TRS-9md6, TRS-0daa]
closed_at: 2026-09-19T16:31:14Z
close_reason: "Accepted: independently reran compilation, story/full suites (58/58 and 110/110), pvg verify, git diff check, static dependency scan, transition-matrix review, LOC/budget checks, and hashes. Async slow-path behavior and terminal immutability are verified with no network, execution, credentials, or external services."
led_to: [TRS-f7sm]
---

## Description
## Context (Embedded)

The slow path must not block conversation. A `needs_tools` fixture creates one
async reasoner job with immutable identity and provenance. The local reasoner
transport is deliberately deterministic and offline in Slice 0: it is the real
Slice-0 proposal-source boundary, not a test mock and not an external inference
adapter.

A valid proposal contains job/turn/session IDs, candidate user answer, ordered
typed actions or a no-action marker, justified state updates, confidence and
uncertainty, input/catalog hashes, model or fixture provenance, and a refusal
reason when applicable. It never contains credentials, hidden prompts,
unrestricted arguments, or an executed-result claim.

Job states are exactly `pending`, `running`, `waiting_confirmation`,
`completed`, `canceled`, `downgraded`, and `failed`. Legal progress is
`pending -> running -> waiting_confirmation -> completed`, with
`pending -> failed`; running or waiting work may become `canceled`,
`downgraded`, or `failed`.

The stale TTL is `30 seconds`, using an injectable monotonic clock. Jobs carry
originating turn epoch, cancellation state, monotonic timestamps, maximum result
age, terminal reason, response priority, and hash-scoped event links.

## USER INTENT

The speaker can keep talking while slow work runs, cancel or supersede it, and
never have a stale or invalid result interrupt the conversation as a normal
answer.

## Goal

Run one async local proposal through validation and policy preflight, manage
its lifecycle, and record hash-scoped job/proposal/terminal events without
executing any tool.

## OUT OF SCOPE

- Network reasoner inference, model credentials, or a live model adapter:
  later explicit integration story.
- Tool execution, multi-tool chaining, or autonomous planning: deferred beyond Slice 0.
- Rendering filler, confirmation, result, cancellation, downgrade, or failure:
  downstream renderer/CLI story.
- Durable job storage or restart recovery: later Postgres/platform story.
- Real-time audio interruption transport: later live voice story.

## DIFF BUDGET

- About 6 source/test files; under 475 changed LOC.
- Gross overrun requires PM investigation for scope creep or hidden design gaps.

## Boundary Map

PRODUCES:
- src/talk_reasoner/transports.py -> class LocalScriptedTransport
  spec: Offline deterministic ReasonerTransport with injectable logical delay/proposal records; it never opens sockets, reads credentials, executes tools, or fabricates an executed result.
- src/talk_reasoner/transports.py -> async propose(self, request: ReasonerRequest) -> ReasonerProposal
  spec: Return one strictly typed proposal after the configured logical delay, including provenance and no executed-result claim.
- src/talk_reasoner/jobs.py -> async start_reasoner_job(request: JobRequest, *, transport: ReasonerTransport, validator: ActionValidator, policy: PolicyEngine, clock: MonotonicClock) -> ReasonerJob
  spec: Create immutable identity/epoch, enter pending/running without blocking the caller, obtain one proposal, validate every action, preflight policy, and return a lifecycle-complete or waiting-confirmation job.
- src/talk_reasoner/jobs.py -> async advance_reasoner_job(job: ReasonerJob, stimulus: JobStimulus, *, clock: MonotonicClock) -> ReasonerJob
  spec: Apply only legal state transitions for confirmation, cancellation, epoch supersession, TTL/age expiry, material intent change, validation/policy failure, completion, or downgrade.
- src/talk_reasoner/jobs.py -> job_terminal_summary(job: ReasonerJob) -> TerminalOutcome
  spec: Return terminal state, reason, turn epoch, priority, validated non-action summary or recovery choice, latency evidence, and provenance; cancel prevents a normal-result outcome.
- tests/test_jobs.py -> async lifecycle, interruption, and provenance tests
  source: covers completion, waiting confirmation, cancellation, downgrade, failure, TTL/age, epoch mismatch, and fast-loop responsiveness.

CONSUMES:
- TRS-0daa: src/talk_reasoner/contracts.py -> append_event(ledger: EventLedger, event: LedgerEvent) -> AppendReceipt
  spec: Append job/proposal/validation/policy/terminal events with hashes and IDs, never raw prompts or proposal text.
- TRS-74z8: src/talk_reasoner/routing.py -> classify(fixture: Fixture, *, policy: ThresholdPolicy) -> RoutingDecision
  spec: Supply the exact route, confidence, risk, threshold version, and input hash that scopes the job.
- TRS-9md6: src/talk_reasoner/actions.py -> validate_action(proposal: ActionProposal, *, catalog: ActionCatalog, consent: ConsentRecord, state: FixtureState) -> ValidationDecision
  spec: Validate every proposed action before waiting confirmation or completion; reject fail-closed proposals.
- TRS-9md6: src/talk_reasoner/actions.py -> preflight_policy(action: ValidatedAction, *, policy: PolicyDefinition, confirmation: ConfirmationRecord | None = None) -> PolicyDecision
  spec: Decide allowed_without_confirmation, confirmation_required, or rejected before any terminal result is accepted.

## Acceptance Requirements

1. Only a `needs_tools` RoutingDecision can start a reasoner job; `chitchat`
   and `unclear` produce no job and never call the transport.
2. `start_reasoner_job` is asynchronous and returns control to the caller while
   the local transport is logically delayed; tests prove another coroutine can
   make progress without waiting for proposal completion.
3. The local transport is deterministic, offline, injectably clock-controlled,
   and returns exactly one typed proposal or typed refusal with provenance.
4. Every proposed action passes the upstream validator and policy preflight
   before `waiting_confirmation` or `completed`; malformed proposals and
   unevaluable policy produce `failed`, never an executed or normal result.
5. Legal transitions and no other transitions are enforced. Terminal states
   are exactly the seven states above and cannot be overwritten by a late result.
6. Explicit cancellation, superseded turn epoch, `30 seconds` stale TTL,
   maximum-age expiry, material intent change, irrecoverable validation/policy
   failure, and unsafe presentation force cancel, downgrade, or fail.
7. Canceled work can never render as a normal result. Downgrade carries only a
   bounded non-action summary or resume offer. Confirmation cannot be reused
   after cancellation, expiry, or argument change.
8. Job, proposal, validation, policy, and terminal events use immutable IDs,
   monotonic timing, turn epoch, scoped input/action hashes, catalog/policy
   versions, and prior-chain links; they omit raw prompts and model I/O.
9. No tool, executor, network socket, credential, Redis, Postgres, or memory
   platform is imported or invoked.

## Testing Requirements

- Unit tests: legal/illegal transition matrix, terminal reason selection, stale
  TTL/age calculations, and immutable job identity.
- Integration tests: MANDATORY (no test mocks). Use LocalScriptedTransport as
  the real offline Slice-0 adapter with an injectable logical clock; cover a
  concurrent fast coroutine, proposal validation, confirmation waiting, and every
  interruption/terminal path.
- E2E tests: not in this story; the blocked capstone owns user-journey coverage.
- Commands: `python -m pytest tests/test_jobs.py`.

## MANDATORY SKILLS

- `project-standards`: async typing, state-machine discipline, and deterministic tests.
- `pvg`: story governance and delivery evidence only.

## Delivery Requirements

- Paste exact pytest output and exit status.
- Include the tested transition matrix and terminal-state counts.
- Include an AC verification table with file/test evidence.
- Update the authoritative `nd_contract` using the pvg delivery workflow.

## nd_contract

status: new

### evidence

- Created: 2026-09-19
- Depends on contracts from TRS-0daa, TRS-74z8, and TRS-9md6.

### proof

- [ ] Pending implementation


## Acceptance Criteria


## Design


## Notes


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-19.

### proof
- [x] Story closed after accepted label was applied.


## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/talker-reasoner-system/.claude/worktrees/dev-TRS-ndv6
git diff --check
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m pytest tests/test_jobs.py
.venv/bin/python -m pytest
pvg verify src/talk_reasoner/transports.py src/talk_reasoner/jobs.py tests/test_jobs.py --format=text
```

Independent coordinator results:

- `git diff --check`: exit 0.
- Compilation: exit 0.
- Story tests: 58/58 passed.
- Full suite: 110/110 passed.
- `pvg verify`: passed with 3 files scanned and zero issues.
- Diff budget: 474 changed LOC, one under the 475 LOC ceiling.
- Static dependency scan found no production network, subprocess, storage-platform, or memory-platform dependency; the only forbidden-name match is the test’s negative-import assertion.
- Transition matrix covers 49 state combinations: 11 legal and 38 illegal.

### CI/Test Results

```text
tests/test_jobs.py: 58 passed
full suite: 110 passed
pvg verify: PASSED (3 files scanned, 0 issues)
```

Summary: implemented deterministic offline local transport, asynchronous reasoner proposal jobs, exact legal transition enforcement, terminal-state immutability, validation and policy preflight, cancellation/supersession/TTL/age/intent/presentation handling, bounded downgrade behavior, and hash-scoped privacy-preserving job/proposal/decision/terminal ledger events.

Commit SHA: 9e959f3

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Only `needs_tools` starts transport | PASS | Route-boundary test. |
| 2. Async slow path yields to fast loop | PASS | Concurrent-clock test. |
| 3. Deterministic offline typed transport | PASS | LocalScriptedTransport tests. |
| 4. Every action validates and preflights before terminal completion | PASS | Validation/policy tests. |
| 5. Exact transition matrix and immutable terminal states | PASS | 49-combination matrix tests. |
| 6. Interruption, supersession, TTL, age, intent, failure, and presentation paths are safe | PASS | Transition/stimulus tests. |
| 7. Canceled cannot render normal result; downgrade/confirmation safe | PASS | Terminal behavior tests. |
| 8. Immutable identities and hash-scoped private events | PASS | Ledger test. |
| 9. No prohibited dependencies or execution | PASS | Static scan and full suite. |


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-19T05:29:38Z dep_added: blocked_by TRS-74z8
- 2026-09-19T05:29:38Z dep_added: blocked_by TRS-9md6
- 2026-09-19T05:29:38Z dep_added: blocks TRS-f7sm
- 2026-09-19T05:29:39Z dep_added: blocks TRS-osl5
- 2026-09-19T14:14:39Z dep_removed: was_blocked_by TRS-74z8
- 2026-09-19T15:55:45Z dep_removed: was_blocked_by TRS-9md6
- 2026-09-19T15:56:07Z status: open -> in_progress
- 2026-09-19T15:56:07Z auto-follows: linked to predecessor TRS-74z8
- 2026-09-19T15:56:07Z auto-follows: linked to predecessor TRS-9md6
- 2026-09-19T15:56:07Z claimed by dev-TRS-ndv6
- 2026-09-19T16:29:54Z status: in_progress -> in_progress
- 2026-09-19T16:29:54Z auto-follows: linked to predecessor TRS-0daa
- 2026-09-19T16:31:14Z status: in_progress -> closed
- 2026-09-19T16:31:14Z dep_removed: no_longer_blocks TRS-f7sm
- 2026-09-19T16:31:14Z dep_removed: no_longer_blocks TRS-osl5

## Links
- Parent: [[TRS-pf94]]
- Was blocked by: [[TRS-74z8]], [[TRS-9md6]]
- Follows: [[TRS-74z8]], [[TRS-9md6]], [[TRS-0daa]]
- Led to: [[TRS-f7sm]]

## Comments
