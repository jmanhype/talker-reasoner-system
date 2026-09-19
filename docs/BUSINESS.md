# Business Context — Talker-Reasoner System MVP

Status: Discovery & Framing draft for story `TRS-zpo4`
Source of record: `docs/sources/whole-system-2026-09-19.md`
Source SHA-256: `c25adac0139b5aeeff6e16cdafddf1af0675785988688b6936250236edf18ec3`

## 1. Problem and opportunity

The product is a fast/slow voice-agent system: a talker preserves presence and
turn-taking, a calibrated router decides when System-2 work is needed, and a
direct reasoner proposes typed, validated actions. A separate renderer returns a
clean response. This avoids both under-capable smalltalk-only voice and costly
reasoner wakeups on every utterance. The first business question is:

> Can routing, validation, provenance, and clean response boundaries be proven
> on controlled transcripts before any live audio, credential, or memory
> service is enabled?

If the answer is no, live models and durable memory would only obscure the
failure.

## 2. Product thesis and value

The system’s value is responsive conversation during slow work, lower cost through
calibrated routing, lower action risk through validation, privacy-preserving
audit, coherent rendering, and gated continuity.

Boundary invariants: PersonaPlex/Moshi is not a native tool-calling model;
Voxtral Small may emit structured `tool_calls` but does not execute tools;
Voxtral Realtime is transcription-oriented; and Jev routes but does not execute
tools.

## 3. Users, stakeholders, and jobs

| Stakeholder | Job and success |
| --- | --- |
| Primary speaker | Speak naturally, get slow work done without repeating it, confirm consequential actions, and cancel stale work. Success is a clean spoken or typed result. |
| Operator / data controller | Govern routing, actions, latency, consent, and privacy. Success is complete audit evidence without raw prompt/audio persistence. |
| Developer / evaluator | Prove contracts before live integration. Success is reproducible fixture results, validation outcomes, and event-chain evidence with no network. |
| Privacy / compliance reviewer | Verify minimization, provenance, and confirmation. Success is zero raw-content persistence and fail-closed policy. |
| Future maintainer | Add services only through gates. Success is no model execution authority and no blurred routing/reasoning/rendering boundaries. |

## 4. Scope and explicit non-goals

### Slice-0 MVP scope

1. **Typed transcript fixtures:** controlled, versioned text cases for the three
   routing outcomes. Fixture input is not raw live audio.
2. **Three calibrated routes:** exactly `chitchat`, `needs_tools`, and
   `unclear`.
3. **Fixed action validation:** a local allowlist with typed argument schemas,
   range checks, required provenance, and explicit rejection reasons.
4. **One direct reasoner:** one reasoner integration boundary in the first
   slice. It proposes structured actions; it does not execute them.
5. **Local append-only, hash-scoped events:** routing, action, policy,
   lifecycle, and response events are linked by content hashes and an append-only
   chain.
6. **Clean response-renderer boundary:** produce user-facing text with channel
   and timing metadata; no PersonaPlex context injection in the first slice.
7. **Asynchronous behavior design and tests:** a slow job is modeled as
   cancellable and downgradeable while the fast conversation continues.

### Required Phase 1 deferrals

The following require explicit follow-up stories, operator consent, privacy
review, and measured gates:

- live microphone, speaker, or telephony audio;
- PersonaPlex/Moshi runtime and PersonaPlex context injection;
- Voxtral Realtime live transcription;
- Voxtral Small tool-call inference;
- Jev network inference or credentials;
- Redis or another hot-state service;
- Postgres or another durable operational store;
- Mem0, Cognee, Zep/Graphiti, and Letta;
- multi-tool execution, autonomous chaining, and broad external APIs;
- code execution, payments, messaging, calendar, CRM, or database mutation;
- prompt optimization services and multi-agent planning.

These deferrals do not deny the target architecture. They sequence it so the
routing, policy, provenance, and renderer contracts can be tested independently.

## 5. Business requirements

| ID | Requirement | Measurable signal |
| --- | --- | --- |
| BR-1 | Classify the three fixture routes without ambiguity | Expected-route accuracy and calibration report |
| BR-2 | Avoid unnecessary reasoner work | False `needs_tools` wakeup count/rate |
| BR-3 | Never miss represented work requests | Missed `needs_tools` count/rate |
| BR-4 | Ask for clarification when intent or safety is insufficient | `unclear` route plus one actionable question |
| BR-5 | Reject unknown or malformed actions before execution | Validation accept/reject correctness |
| BR-6 | Require explicit confirmation before future high-risk work | Policy preflight and confirmation event match |
| BR-7 | Preserve fast-path experience during slow work | Slow-job lifecycle and response latency measurements |
| BR-8 | Make results intelligible without tool jargon | Rendered response acceptance/rejection rate |
| BR-9 | Preserve privacy by default | Raw prompt/audio persistence count must be zero |
| BR-10 | Support audit and replay | Event-chain verification and missing-event count |
| BR-11 | Keep credentials outside models and fixtures | Credential exposure count must be zero |
| BR-12 | Avoid premature infrastructure cost | Slice-0 runs without network calls or platform services |

## 6. Success hierarchy

Safety, privacy, and correctness outrank capability; capability outranks latency
optimization; all three outrank infrastructure breadth. Concretely: no
unvalidated/unconfirmed consequential action can execute; routing, validation,
and provenance match policy; every terminal state renders cleanly; `chitchat`
never wakes the reasoner; stale jobs are canceled or downgraded; and later
integrations use explicit adapters rather than changing core contracts.

## 7. Rollout gates and kill criteria

Slice-0 uses a frozen labeled fixture set and reports every metric with counts,
denominators, and thresholds. A gate is not satisfied by an aggregate score
that hides a violating subset.

### Required rollout criteria

| Dimension | Roll on / continue | Notes |
| --- | --- | --- |
| Routing accuracy | `>= 0.95` overall and `>= 0.90` per route | Frozen fixtures should target `1.00` |
| Missed work requests | `<= 0.01` of `needs_tools` fixtures | Miss means routing to `chitchat` or `unclear` |
| False reasoner wakeups | `<= 0.05` of `chitchat` fixtures | Report unclear-to-reasoner separately |
| Action-validation correctness | `1.00` on valid/invalid fixture pairs | Includes unknown name and malformed arguments |
| Policy correctness | `1.00` on confirmation fixtures | No high-risk action reaches execution without confirmation |
| Privacy/provenance | `0` raw records; `100%` provenance-complete events | Test absence and completeness |
| Event integrity | `1.00` chain verification; `0` gaps | Any mutation/deletion/fork fails |
| Slow-path lifecycle | `100%` terminal jobs are completed, canceled, downgraded, or failed | No unresolved reasoner job |
| Rendered response acceptance | `>= 0.95` evaluable fixtures | User answer is truthful, clean, and non-empty when required |
| Slice-0 runtime | No network call and no credential use | Test harness must detect both |

Initial latency ceilings are design budgets, not claims:

- router decision: `p95 <= 300 ms` for a local deterministic adapter;
- renderer handoff after terminal reasoner result: `p95 <= 250 ms`;
- slow-job stale cutoff: `30 seconds` unless a future story changes the policy;
- production voice budgets must be re-baselined before live audio.

### Immediate kill or rollback criteria

Any one of these blocks rollout of the affected path:

1. any raw prompt/audio record, credential exposure, unknown/malformed action
   acceptance, unconfirmed high-risk execution, provenance gap, or chain error;
2. overall routing accuracy `< 0.90`, missed work rate `> 0.02`, or false
   wakeups `> 0.10`;
3. slow work blocks the fast path or leaves jobs unresolved;
4. rendered responses leak tool internals, credentials, private data, or raw
   model output without policy review.

For later live deployment, kill thresholds are intentionally stricter than the
initial rollout thresholds. A controlled rollout must sample real traffic,
report route-stratified metrics, and support instant routing fallback to
`unclear`.

## 8. Risks and mitigations

Principal risks are router error, latency creep, wrong actions, memory
pollution, model-boundary confusion, overfit fixtures, overengineering, and
audit sprawl. Mitigations are stratified evaluation, async budgets, fixed
validation/policy, deferred memory, exact boundaries, held-out evaluation,
Slice-0 service deferrals, and hash/metadata-only events.

## 9. Open business questions

Non-blocking questions: durable-retention wording, future approved action
domains and policy owners, live accessibility/regional requirements,
production latency/availability targets, and human review of high-risk failures.

## 10. Backlog inputs for story decomposition

1. Fixture contract; 2. calibrated route policy/report; 3. reasoner output
   contract without execution authority; 4. fixed action catalog and rejection
   reasons; 5. event schema and chain verifier; 6. async cancellation/downgrade;
   7. policy preflight and confirmation; 8. renderer and forbidden-content
   tests; 9. privacy/provenance non-persistence; 10. rollout/kill report.

Every implementation story must preserve the four model-boundary facts and the
Phase 1 deferrals unless the operator explicitly changes scope.
