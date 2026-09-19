---
id: TRS-do2n
title: "E2e: trace fixture conversations to clean outcomes"
status: open
priority: 1
type: feature
labels: [capstone, e2e, slice-0]
parent: TRS-pf94
created_at: 2026-09-19T05:25:58Z
created_by: speed
updated_at: 2026-09-19T05:25:58Z
content_hash: "sha256:79bec0543f6af06beeb7abd822700a76808ea946aa55447fe8d499280257a736"
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
- TRS-r6uo: src/talk_reasoner/contracts.py -> load_fixture_corpus(paths: Iterable[pathlib.Path]) -> FixtureCorpus
  spec: Load the complete frozen corpus and preserve expected outcomes/IDs for user-journey assertions.
- TRS-r6uo: src/talk_reasoner/contracts.py -> verify_ledger(ledger: EventLedger) -> LedgerVerification
  spec: Require a valid complete fixture-to-response chain with zero gaps or mutations.
- TRS-wqbs: src/talk_reasoner/routing.py -> evaluate_routing(corpus: FixtureCorpus, *, policy: ThresholdPolicy) -> RoutingReport
  spec: Verify overall/per-route outcomes, confusion, missed work, false wakeups, versions, denominators, and UTC window.
- TRS-hjbd: src/talk_reasoner/actions.py -> evaluate_action_suite(cases: Iterable[ActionCase]) -> ActionPolicyReport
  spec: Verify action validation/preflight correctness and every rejection-code denominator.
- TRS-pmd9: src/talk_reasoner/jobs.py -> job_terminal_summary(job: ReasonerJob) -> TerminalOutcome
  spec: Verify every terminal lifecycle is completed, canceled, downgraded, or failed and never unresolved.
- TRS-owap: src/talk_reasoner/cli.py -> main(argv: Sequence[str] | None = None) -> int
  spec: Drive the actual user-visible command with stdout/stderr and real exit status.

## Acceptance Criteria

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

## Skills To Use

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
- Blocked by all Slice-0 implementation siblings: TRS-r6uo, TRS-wqbs,
  TRS-hjbd, TRS-pmd9, and TRS-owap.

### proof

- [ ] Pending implementation


## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[TRS-pf94]]

## Comments
