---
id: TRS-74z8
title: "Route typed fixtures through calibrated three-route policy"
status: closed
priority: 1
type: feature
labels: [slice-0, accepted]
parent: TRS-pf94
created_at: 2026-09-19T05:29:37Z
created_by: speed
updated_at: 2026-09-19T14:14:39Z
content_hash: "sha256:9816773878aff0a738600a2da816c30a2897a2fca69ada9850a8f36f5e92b7ac"
was_blocked_by: [TRS-0daa]
assignee: dev-TRS-74z8
follows: [TRS-0daa, TRS-zpo4]
closed_at: 2026-09-19T14:14:39Z
close_reason: "Accepted: independently reran story/full suites (14/14 and 28/28), compilation, pvg verify, static boundary scan, and hash checks. Routing is local/deterministic, exactly three routes, threshold-guarded, fully reported, and privacy-safe."
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
## Implementation Evidence

Commands run:
- git add config src/talk_reasoner/routing.py tests/test_routing.py
- git commit -m "feat(TRS-74z8): add calibrated three-route policy"

### CI/Test Results
- Story commit: d4714b8
- Worktree clean after commit.
- Independent full suite before commit: 28/28 passed.

Summary: accepted implementation snapshot committed on story/TRS-74z8 at d4714b8.

Commit SHA: d4714b8

### AC Verification
- [x] All eight TRS-74z8 AC are covered by committed files and independent 28/28 suite.

## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/talker-reasoner-system/.claude/worktrees/dev-TRS-74z8
git diff --check
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m pytest tests/test_routing.py
.venv/bin/python -m pytest
pvg verify config/routing/slice0-v1.json src/talk_reasoner/routing.py tests/test_routing.py --include-tests --check-mocks --format=text
```

Independent coordinator results:

- `git diff --check`: exit 0.
- Compilation: exit 0.
- Story tests: 14/14 passed.
- Full suite: 28/28 passed.
- `pvg verify`: exit 0.
- Static scan found no production network/reasoner/job/tool imports; only the test’s forbidden-import assertion matched.
- Frozen corpus report: 18/18 correct; confusion matrix 6/6 diagonal with zero off-diagonal; missed `needs_tools` 0/6; false wakeups 0/6; unclear precision 1.0; route event chain valid for 18 events.

### CI/Test Results

```text
tests/test_routing.py: 14 passed
full suite: 28 passed
pvg verify: 0 issues
```

Summary: implemented deterministic local three-route classification, versioned threshold policy, boundary and safety fallback behavior, exact route reports/denominators/confusion metrics, and privacy-safe route events without any reasoner, network, tool, or memory boundary.

Commit SHA: 21dd9fe6b073b9c536a65ca3b97df2892d465b5c6b3409a632c954293972a7cd

This is the three-file delivery-manifest SHA-256 before the Git commit; the worktree commit is appended below.

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Exact probability shape and routing metadata | PASS | Typed `RoutingDecision`; 14 story tests. |
| 2. Deterministic local scoring; no network/model/tools | PASS | Determinism and forbidden-boundary tests. |
| 3. Versioned thresholds and guarded fallbacks | PASS | Policy loader/apply-policy tests; only three routes. |
| 4. Boundary and invalid-calibration cases cannot bypass policy | PASS | Exact 0.90/0.80 boundary tests and invalid/risk cases. |
| 5. Complete stratified report with denominators and versions | PASS | Full corpus report and test assertions. |
| 6. Frozen corpus 18/18, zero missed work/wakeups | PASS | Independent reported metrics and integration test. |
| 7. Reasoner boundary absent | PASS | Static import assertion and source scan. |
| 8. Hash-scoped privacy-safe route events | PASS | 18-event chain verification and privacy test. |


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-19T05:29:37Z dep_added: blocked_by TRS-0daa
- 2026-09-19T05:29:38Z dep_added: blocks TRS-ndv6
- 2026-09-19T05:29:38Z dep_added: blocks TRS-f7sm
- 2026-09-19T05:29:38Z dep_added: blocks TRS-osl5
- 2026-09-19T13:41:58Z dep_removed: was_blocked_by TRS-0daa
- 2026-09-19T13:44:31Z status: open -> in_progress
- 2026-09-19T13:44:31Z auto-follows: linked to predecessor TRS-0daa
- 2026-09-19T13:44:31Z claimed by dev-TRS-74z8
- 2026-09-19T14:13:37Z status: in_progress -> in_progress
- 2026-09-19T14:13:37Z auto-follows: linked to predecessor TRS-zpo4
- 2026-09-19T14:14:39Z status: in_progress -> closed
- 2026-09-19T14:14:39Z dep_removed: no_longer_blocks TRS-ndv6
- 2026-09-19T14:14:39Z dep_removed: no_longer_blocks TRS-f7sm
- 2026-09-19T14:14:39Z dep_removed: no_longer_blocks TRS-osl5

## Links
- Parent: [[TRS-pf94]]
- Was blocked by: [[TRS-0daa]]
- Follows: [[TRS-0daa]], [[TRS-zpo4]]

## Comments
