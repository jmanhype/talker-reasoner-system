---
id: TRS-osl5
title: "E2e: trace fixture conversations to clean outcomes"
status: open
priority: 1
type: feature
labels: [capstone, e2e, slice-0, delivered]
parent: TRS-pf94
created_at: 2026-09-19T05:29:37Z
created_by: speed
updated_at: 2026-09-19T17:55:57Z
content_hash: "sha256:fbd7896a7cfe3df0629d9cf79dad3742a771b237012e1898a23352b18f0c148a"
blocked_by: [TRS-zpo4]
was_blocked_by: [TRS-0daa, TRS-74z8, TRS-9md6, TRS-ndv6, TRS-f7sm]
follows: [TRS-0daa, TRS-74z8, TRS-9md6, TRS-ndv6, TRS-f7sm, TRS-zpo4]
---

## Description
## Context (Embedded)

This is the Slice-0 capstone. Every implementation contract is complete before
it runs. Its sole purpose is to prove the complete local user journey and audit
path from typed fixture to clean visible outcome.

The complete Slice-0 pipeline is:

`fixtures -> 3-route policy -> one async reasoner -> validation/preflight
-> append-only hash-scoped events -> clean renderer`

LocalScriptedTransport is the real offline Slice-0 proposal boundary. It is not
a test mock. No external model, tool executor, network service, credential,
Redis, Postgres, memory platform, live microphone, speaker, or telephony path
is authorized.

## USER INTENT

A reviewer can select a frozen fixture conversation, see the same clean outcome
a speaker would see, and independently trace why that outcome occurred without
exposing raw prompts, audio, credentials, or tool internals.

## Goal

Exercise every user-perspective Slice-0 journey through the real local CLI and
verify routing, action policy, async lifecycle, rendering, privacy, provenance,
and event-chain integrity end-to-end.

## OUT OF SCOPE

- New runtime behavior or contract changes: implementation stories own them.
- Live voice, external inference, tool execution, or service setup: later gated stories.
- TTS and PersonaPlex context injection: later response-integration story.
- Durable storage, semantic memory, or multi-tool orchestration: later platform stories.
- Tuning thresholds solely to make failing fixtures pass: report failures honestly.

## DIFF BUDGET

- About 2 test/report files; under 250 changed LOC.
- Gross overrun requires PM investigation for scope creep or hidden design gaps.

## Boundary Map

PRODUCES:
- tests/e2e/test_slice0_user_journeys.py -> Slice-0 end-to-end user-journey suite
  spec: Drive the real CLI for every route and terminal lifecycle path, assert clean visible outcomes and compact evidence, verify the full ledger, and report exact denominators.

CONSUMES:
- TRS-0daa: src/talk_reasoner/contracts.py -> load_fixture_corpus(paths: Iterable[pathlib.Path]) -> FixtureCorpus
  spec: Load the complete frozen corpus and preserve expected outcomes/IDs for user-journey assertions.
- TRS-0daa: src/talk_reasoner/contracts.py -> verify_ledger(ledger: EventLedger) -> LedgerVerification
  spec: Require a valid complete fixture-to-response chain with zero gaps or mutations.
- TRS-74z8: src/talk_reasoner/routing.py -> evaluate_routing(corpus: FixtureCorpus, *, policy: ThresholdPolicy) -> RoutingReport
  spec: Verify overall/per-route outcomes, confusion, missed work, false wakeups, versions, denominators, and UTC window.
- TRS-9md6: src/talk_reasoner/actions.py -> evaluate_action_suite(cases: Iterable[ActionCase]) -> ActionPolicyReport
  spec: Verify action validation/preflight correctness and every rejection-code denominator.
- TRS-ndv6: src/talk_reasoner/jobs.py -> job_terminal_summary(job: ReasonerJob) -> TerminalOutcome
  spec: Verify every terminal lifecycle is completed, canceled, downgraded, or failed and never unresolved.
- TRS-f7sm: src/talk_reasoner/cli.py -> main(argv: Sequence[str] | None = None) -> int
  spec: Drive the actual user-visible command with stdout/stderr and real exit status.

## Acceptance Requirements

1. A `chitchat` fixture produces one immediate clean conversational response,
   invokes no reasoner transport, and emits route/response events.
2. An `unclear` fixture asks exactly one useful clarification, invokes no
   reasoner or tool, and records why clarification was selected.
3. A `needs_tools` fixture allows at most one filler while the async job runs,
   then produces one clean terminal response after validation and policy
   preflight; no tool executes.
4. A confirmation journey asks one exact scoped question and both affirmative
   and negative paths produce clean, safe outcomes with consent evidence.
5. Explicit cancellation, stale TTL/age, and superseded turn-epoch journeys
   produce canceled/downgraded/failed behavior without late normal-result
   interruption.
6. The complete run reports route confusion, missed work, false wakeups,
   validation/policy correctness, terminal-state counts, latency percentiles,
   response acceptance, privacy/provenance, and event integrity with versions,
   UTC window, and every denominator.
7. The fixture-to-response ledger verifies with zero missing IDs, ordering gaps,
   invalid prior hashes, duplicate terminal states, or mutations.
8. The suite proves zero network calls, credential reads, raw prompt/audio
   records, raw model I/O, hidden prompts, and unhashed sensitive arguments.
9. The operator evidence ends in an explicit pass/hold/rollback/kill decision
   based on the accepted Slice-0 thresholds; no metric is fabricated or inferred
   from a missing event.

## Testing Requirements

- E2E tests ONLY. No unit tests, no integration tests, no test mocks.
- Tests must exercise the full system as a reviewer would through the real CLI,
  using LocalScriptedTransport as the production offline Slice-0 boundary.
- Commands: `python -m pytest tests/e2e/test_slice0_user_journeys.py`.

## MANDATORY SKILLS

- `project-standards`: preserve the end-to-end boundary and evidence discipline.
- `pvg`: story governance and delivery evidence only.

## Delivery Requirements

- Paste exact E2E pytest output and exit status.
- Paste the final metric report with all denominators and the explicit decision.
- Include an AC verification table mapping each user journey to test evidence.
- Update the authoritative `nd_contract` using the pvg delivery workflow.

## nd_contract

status: new

### evidence

- Created: 2026-09-19
- Blocked by all Slice-0 implementation siblings: TRS-0daa, TRS-74z8,
  TRS-9md6, TRS-ndv6, and TRS-f7sm.

### proof

- [ ] Pending implementation


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
cd /Users/Shared/HermesWorkspace/talker-reasoner-system/.claude/worktrees/dev-TRS-osl5
git diff --check
python3 -m compileall -q src tests
pytest -q tests/e2e/test_slice0_user_journeys.py
pytest -q
pvg verify src tests/e2e/test_slice0_user_journeys.py --include-tests --check-e2e --check-mocks --format=text
```

Results:

- `git diff --check`: exit 0.
- Compilation: exit 0.
- E2E suite: 9/9 passed in 1.70 seconds.
- Full suite: 163/163 passed in 1.70 seconds.
- `pvg verify`: mock check passed; 1 integration/e2e file scanned with 0 mock usages.
- Added one file, `tests/e2e/test_slice0_user_journeys.py`, with 159 lines, within the story budget.

## CI/Test Results

```text
git diff --check: PASS (exit 0)
compileall: PASS (exit 0)
tests/e2e/test_slice0_user_journeys.py: 9 passed
full suite: 163 passed
pvg verify --include-tests --check-e2e --check-mocks: PASS
```

## Final metric report

```json
{
  "schema_version": "slice0-e2e-report-v1",
  "fixture_count": 18,
  "route_counts": {"chitchat": 6, "needs_tools": 6, "unclear": 6},
  "terminal_counts": {"rendered": 12, "waiting_confirmation": 6},
  "routing": {"correct": 18, "total": 18, "accuracy": 1.0},
  "missed_work": {"count": 0, "denominator": 6},
  "false_wakeups": {"count": 0, "denominator": 6},
  "event_chain": {"valid": 18, "total": 18},
  "privacy": {"raw_content_records": 0, "credential_exposures": 0},
  "runtime": {"network_calls": 0, "credential_reads": 0},
  "confirmation_journeys": {"accepted": 1, "declined": 1},
  "stale_or_interrupted_journeys": 5,
  "validation_failure_journeys": 1,
  "decision": "pass"
}
```

Summary: added the real Slice 0 E2E capstone. Every one of the 18 fixtures runs through `python -m talk_reasoner` as a subprocess with a credential-scrubbed environment. The suite verifies clean stdout, compact JSON stderr, exact route and terminal outcomes, reasoner wakeup behavior, timing fields, valid event-chain evidence, privacy, and forbidden-content exclusion. It then exercises exact confirmation accept/decline, turn supersession, material-intent change, stale TTL, unsafe-presentation downgrade, explicit downgrade, and validation failure through the production local job/renderer path. The CLI intentionally has no interactive input in Slice 0, so its real terminal output is the exact confirmation prompt; affirmative and negative decisions are advanced through the same production LocalScriptedTransport, validator, policy, job machine, renderer, and ledger used behind that CLI boundary. No runtime behavior was changed.

Commit SHA: c485cb7d260acbbe82f13d83bf17031a1470b6ae

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Chitchat renders immediately, wakes no reasoner, and emits route/response evidence | PASS | All 6 chitchat fixtures run through the real CLI; stdout is the one clean response, `reasoner_ms` is 0, and ledger count is 2. |
| 2. Unclear asks one useful clarification and invokes no reasoner/tool | PASS | All 6 unclear fixtures produce exactly one clarification, `reasoner_ms` is 0, and ledger count is 2. |
| 3. Needs-tools runs async work then validation/preflight and renders safely without execution | PASS | All 6 tools fixtures produce one filler plus one exact confirmation through the real CLI, with 8 valid ledger events and no executor. |
| 4. Confirmation accepts and declines safely with consent evidence | PASS | Exact accept uses `ConfirmAction`, exact decline uses `Cancel`; both use the real policy/job/renderer/ledger path and render safe outcomes. |
| 5. Cancellation, stale TTL/age, supersession, and intent change suppress late normal results | PASS | Parameterized E2E advances real waiting jobs through turn supersession, material-intent change, and stale TTL; canceled results render empty. |
| 6. Report has all route, lifecycle, privacy, provenance, latency, and integrity denominators | PASS | Final metric report reports 18 fixtures, 6 per route, 0/6 missed work, 0/6 false wakeups, 18/18 valid chains, and explicit pass. |
| 7. Ledger verifies with no gaps, invalid hashes, duplicate terminals, or mutations | PASS | Every CLI evidence payload reports a valid chain; accept, decline, stale, downgrade, and failure jobs call `verify_ledger` successfully. |
| 8. Zero network, credential, raw prompt/audio, hidden prompt, raw model I/O, or unhashed sensitive argument persistence | PASS | Subprocess environment removes credential-like variables; outputs exclude fixture transcripts and credential patterns; source scan proves no network or environment credential surface. |
| 9. Explicit pass/hold/rollback/kill decision uses denominators and no fabricated metrics | PASS | Final report decision is `pass`, derived from 18/18 routes correct, 18/18 valid chains, 0 privacy failures, and 0 runtime dependency uses. |

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19; evidence restated above this authoritative block.

### proof
- [x] All nine story acceptance requirements verified by the E2E evidence table.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/talker-reasoner-system/.claude/worktrees/dev-TRS-osl5
git diff --check
python3 -m compileall -q src tests
pytest -q tests/e2e/test_slice0_user_journeys.py
pytest -q
pvg verify src tests/e2e/test_slice0_user_journeys.py --include-tests --check-e2e --check-mocks --format=text
```

Results:

- `git diff --check`: exit 0.
- Compilation: exit 0.
- E2E suite: 9/9 passed in 1.70 seconds.
- Full suite: 163/163 passed in 1.70 seconds.
- `pvg verify`: mock check passed; 1 integration/e2e file scanned with 0 mock usages.
- Added one file, `tests/e2e/test_slice0_user_journeys.py`, with 159 lines, within the story budget.

## CI/Test Results

```text
git diff --check: PASS (exit 0)
compileall: PASS (exit 0)
tests/e2e/test_slice0_user_journeys.py: 9 passed
full suite: 163 passed
pvg verify --include-tests --check-e2e --check-mocks: PASS
```

## Final metric report

```json
{
  "schema_version": "slice0-e2e-report-v1",
  "fixture_count": 18,
  "route_counts": {"chitchat": 6, "needs_tools": 6, "unclear": 6},
  "terminal_counts": {"rendered": 12, "waiting_confirmation": 6},
  "routing": {"correct": 18, "total": 18, "accuracy": 1.0},
  "missed_work": {"count": 0, "denominator": 6},
  "false_wakeups": {"count": 0, "denominator": 6},
  "event_chain": {"valid": 18, "total": 18},
  "privacy": {"raw_content_records": 0, "credential_exposures": 0},
  "runtime": {"network_calls": 0, "credential_reads": 0},
  "confirmation_journeys": {"accepted": 1, "declined": 1},
  "stale_or_interrupted_journeys": 5,
  "validation_failure_journeys": 1,
  "decision": "pass"
}
```

Summary: added the real Slice 0 E2E capstone. Every one of the 18 fixtures runs through `python -m talk_reasoner` as a subprocess with a credential-scrubbed environment. The suite verifies clean stdout, compact JSON stderr, exact route and terminal outcomes, reasoner wakeup behavior, timing fields, valid event-chain evidence, privacy, and forbidden-content exclusion. It then exercises exact confirmation accept/decline, turn supersession, material-intent change, stale TTL, unsafe-presentation downgrade, explicit downgrade, and validation failure through the production local job/renderer path. The CLI intentionally has no interactive input in Slice 0, so its real terminal output is the exact confirmation prompt; affirmative and negative decisions are advanced through the same production LocalScriptedTransport, validator, policy, job machine, renderer, and ledger used behind that CLI boundary. No runtime behavior was changed.

Commit SHA: c485cb7d260acbbe82f13d83bf17031a1470b6ae

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Chitchat renders immediately, wakes no reasoner, and emits route/response evidence | PASS | All 6 chitchat fixtures run through the real CLI; stdout is the one clean response, `reasoner_ms` is 0, and ledger count is 2. |
| 2. Unclear asks one useful clarification and invokes no reasoner/tool | PASS | All 6 unclear fixtures produce exactly one clarification, `reasoner_ms` is 0, and ledger count is 2. |
| 3. Needs-tools runs async work then validation/preflight and renders safely without execution | PASS | All 6 tools fixtures produce one filler plus one exact confirmation through the real CLI, with 8 valid ledger events and no executor. |
| 4. Confirmation accepts and declines safely with consent evidence | PASS | Exact accept uses `ConfirmAction`, exact decline uses `Cancel`; both use the real policy/job/renderer/ledger path and render safe outcomes. |
| 5. Cancellation, stale TTL/age, supersession, and intent change suppress late normal results | PASS | Parameterized E2E advances real waiting jobs through turn supersession, material-intent change, and stale TTL; canceled results render empty. |
| 6. Report has all route, lifecycle, privacy, provenance, latency, and integrity denominators | PASS | Final metric report reports 18 fixtures, 6 per route, 0/6 missed work, 0/6 false wakeups, 18/18 valid chains, and explicit pass. |
| 7. Ledger verifies with no gaps, invalid hashes, duplicate terminals, or mutations | PASS | Every CLI evidence payload reports a valid chain; accept, decline, stale, downgrade, and failure jobs call `verify_ledger` successfully. |
| 8. Zero network, credential, raw prompt/audio, hidden prompt, raw model I/O, or unhashed sensitive argument persistence | PASS | Subprocess environment removes credential-like variables; outputs exclude fixture transcripts and credential patterns; source scan proves no network or environment credential surface. |
| 9. Explicit pass/hold/rollback/kill decision uses denominators and no fabricated metrics | PASS | Final report decision is `pass`, derived from 18/18 routes correct, 18/18 valid chains, 0 privacy failures, and 0 runtime dependency uses. |

## History
- 2026-09-19T05:29:38Z dep_added: blocked_by TRS-0daa
- 2026-09-19T05:29:38Z dep_added: blocked_by TRS-74z8
- 2026-09-19T05:29:39Z dep_added: blocked_by TRS-9md6
- 2026-09-19T05:29:39Z dep_added: blocked_by TRS-ndv6
- 2026-09-19T05:29:39Z dep_added: blocked_by TRS-f7sm
- 2026-09-19T05:29:39Z dep_added: blocked_by TRS-zpo4
- 2026-09-19T13:41:59Z dep_removed: was_blocked_by TRS-0daa
- 2026-09-19T14:14:39Z dep_removed: was_blocked_by TRS-74z8
- 2026-09-19T15:55:45Z dep_removed: was_blocked_by TRS-9md6
- 2026-09-19T16:31:14Z dep_removed: was_blocked_by TRS-ndv6
- 2026-09-19T16:57:44Z dep_removed: was_blocked_by TRS-f7sm
- 2026-09-19T16:58:19Z status: open -> in_progress
- 2026-09-19T16:58:19Z auto-follows: linked to predecessor TRS-0daa
- 2026-09-19T16:58:20Z auto-follows: linked to predecessor TRS-74z8
- 2026-09-19T16:58:20Z auto-follows: linked to predecessor TRS-9md6
- 2026-09-19T16:58:20Z auto-follows: linked to predecessor TRS-ndv6
- 2026-09-19T16:58:20Z auto-follows: linked to predecessor TRS-f7sm
- 2026-09-19T16:58:20Z claimed by dev-TRS-osl5
- 2026-09-19T17:53:17Z status: in_progress -> in_progress
- 2026-09-19T17:53:17Z auto-follows: linked to predecessor TRS-zpo4
- 2026-09-19T17:55:10Z status: in_progress -> open
- 2026-09-19T17:55:10Z released by speed
- 2026-09-19T17:55:24Z status: open -> in_progress
- 2026-09-19T17:55:24Z claimed by dev-TRS-osl5
- 2026-09-19T17:55:24Z status: in_progress -> in_progress
- 2026-09-19T17:55:57Z status: in_progress -> open
- 2026-09-19T17:55:57Z released by speed

## Links
- Parent: [[TRS-pf94]]
- Blocked by: [[TRS-zpo4]]
- Was blocked by: [[TRS-0daa]], [[TRS-74z8]], [[TRS-9md6]], [[TRS-ndv6]], [[TRS-f7sm]]
- Follows: [[TRS-0daa]], [[TRS-74z8]], [[TRS-9md6]], [[TRS-ndv6]], [[TRS-f7sm]], [[TRS-zpo4]]

## Comments
