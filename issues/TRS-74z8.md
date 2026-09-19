---
id: TRS-74z8
title: "Route typed fixtures through calibrated three-route policy"
status: open
priority: 1
type: feature
labels: [slice-0]
parent: TRS-pf94
created_at: 2026-09-19T05:29:37Z
created_by: speed
updated_at: 2026-09-19T05:29:37Z
content_hash: "sha256:e3e0e4987e1665ba4883c0c21e323673bf50a911c6c16d7951a2110dec1419fe"
blocked_by: [TRS-0daa]
blocks: [TRS-ndv6, TRS-f7sm, TRS-osl5]
---

## Description
## Context (Embedded)

Slice 0 needs a deterministic local stand-in for the future Jev calibrated
router. It must preserve the Jev boundary--routing only, with no tool
authority--while producing the same shape of decision evidence needed by later
live adapters.

The only user-visible routes are exactly:

- `chitchat`: immediate short reply; reasoner remains asleep.
- `needs_tools`: one optional short filler, then an async reasoner job.
- `unclear`: one actionable clarification; no reasoner invocation.

Initial versioned thresholds for `slice0-v1`:

- selected `chitchat` requires confidence `>= 0.90`;
- selected `needs_tools` requires confidence `>= 0.80`;
- missing, invalid, or unevaluable calibration/risk routes to `unclear`;
- unsafe intent is forced to a guarded `unclear` path; safety is not a fourth
  user-visible route.

Model boundaries and deferrals remain fixed: no PersonaPlex/Moshi schemas or
execution authority, no Voxtral Realtime routing, no Voxtral Small execution,
no Jev network call, credentials, external inference, tools, memory, Redis, or
Postgres.

## USER INTENT

Ordinary conversation should not wake expensive System-2 work, represented work
should not be missed, and uncertain or unsafe input should produce a useful
clarification rather than silent guessing.

## Goal

The routing evaluator returns one deterministic decision per typed fixture and
emits a route-stratified report with exact denominators after applying the
versioned calibrated policy.

## OUT OF SCOPE

- Network calls to Jev and credential handling: later explicit integration story.
- Action validation, policy preflight, or confirmation: downstream action story.
- Starting or managing reasoner jobs: downstream async-job story.
- Rendering the reply or clarification to a user: downstream CLI story.
- Expanding beyond three user-visible routes: later architecture decision.

## DIFF BUDGET

- About 4 source/test/config files; under 350 changed LOC.
- Gross overrun requires PM investigation for scope creep or hidden design gaps.

## Boundary Map

PRODUCES:
- src/talk_reasoner/routing.py -> classify(fixture: Fixture, *, policy: ThresholdPolicy) -> RoutingDecision
  spec: Deterministically classify one typed fixture and return all three probabilities, selected_label, confidence, exact route, risk, and thresholds_version.
- src/talk_reasoner/routing.py -> load_threshold_policy(path: pathlib.Path) -> ThresholdPolicy
  spec: Parse and validate one versioned threshold policy; fail closed on missing labels, invalid bounds, or threshold ambiguity.
- src/talk_reasoner/routing.py -> evaluate_routing(corpus: FixtureCorpus, *, policy: ThresholdPolicy) -> RoutingReport
  spec: Classify every fixture in deterministic order and emit overall/per-route counts, denominators, confusion, missed work, false wakeups, boundary cases, configuration hash, and pass/hold decision.
- config/routing/slice0-v1.json -> versioned threshold policy
  fields: schema_version, thresholds_version, chitchat_confidence_min, needs_tools_confidence_min, invalid_fallback_route, safety_fallback_route.
- tests/test_routing.py -> routing and calibration tests
  source: covers all corpus fixtures, exact boundaries, invalid policy/calibration, safety fallback, and no-reasoner proof.

CONSUMES:
- TRS-0daa: src/talk_reasoner/contracts.py -> load_fixture(path: pathlib.Path) -> Fixture
  spec: Use typed validated fixture records; do not parse raw ad hoc strings.
- TRS-0daa: src/talk_reasoner/contracts.py -> load_fixture_corpus(paths: Iterable[pathlib.Path]) -> FixtureCorpus
  spec: Use deterministic ordered corpus input for exact route denominators.
- TRS-0daa: src/talk_reasoner/contracts.py -> append_event(ledger: EventLedger, event: LedgerEvent) -> AppendReceipt
  spec: Append a route event containing calibration/threshold versions and scoped transcript hash, never raw transcript text.

## Acceptance Requirements

1. `RoutingDecision` always contains non-negative probabilities for exactly
   `chitchat`, `needs_tools`, and `unclear`, sums to `1.0` within explicit
   tolerance, plus `selected_label`, `confidence`, `route`, `risk`, and
   `thresholds_version`.
2. The local deterministic classifier scores every fixture without network,
   credentials, model invocation, or tool execution and yields identical output
   for repeated runs.
3. Versioned policy data enforces `chitchat >= 0.90`, `needs_tools >= 0.80`,
   fallback to `unclear` on threshold failure, and guarded `unclear` on unsafe
   or unevaluable risk without adding a fourth route.
4. Tests include cases immediately above and below both thresholds and prove
   a high-scoring wrong/invalid calibration cannot bypass policy.
5. The report gives overall and per-route accuracy, confusion matrix, missed
   `needs_tools` count/rate, false `needs_tools` wakeups on `chitchat`,
   unclear precision, total/per-route denominators, fixture-set version,
   thresholds version/hash, and UTC run window.
6. On the frozen corpus, expected route accuracy is `1.00`, missed work is
   `0`, and false reasoner wakeups are `0`; any mismatch is reported, never
   blended away.
7. The reasoner boundary is absent from this story: no transport is imported,
   constructed, or callable from routing code.
8. Route events use the upstream scoped transcript hash and contain no raw
   transcript, hidden prompt, credential, or model request/response.

## Testing Requirements

- Unit tests: probability shape, threshold boundaries, safety fallback, policy
  validation, and deterministic repeatability.
- Integration tests: MANDATORY (no mocks). Evaluate the complete typed corpus,
  verify every expected outcome and report denominator, and inspect emitted route
  event metadata.
- E2E tests: not in this story; the blocked capstone owns user-journey coverage.
- Commands: `python -m pytest tests/test_routing.py`.

## MANDATORY SKILLS

- `project-standards`: typed contracts and deterministic test discipline.
- `pvg`: story governance and delivery evidence only.

## Delivery Requirements

- Paste exact pytest output and exit status.
- Include the complete route confusion matrix and counts/denominators.
- Include an AC verification table with file/test evidence.
- Update the authoritative `nd_contract` using the pvg delivery workflow.

## nd_contract

status: new

### evidence

- Created: 2026-09-19
- Depends on typed fixture/event contracts from TRS-0daa.

### proof

- [ ] Pending implementation


## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T05:29:37Z dep_added: blocked_by TRS-0daa
- 2026-09-19T05:29:38Z dep_added: blocks TRS-ndv6
- 2026-09-19T05:29:38Z dep_added: blocks TRS-f7sm
- 2026-09-19T05:29:38Z dep_added: blocks TRS-osl5

## Links
- Parent: [[TRS-pf94]]
- Blocks: [[TRS-ndv6]], [[TRS-f7sm]], [[TRS-osl5]]
- Blocked by: [[TRS-0daa]]

## Comments
