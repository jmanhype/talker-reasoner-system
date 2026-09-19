# Architecture — Talker-Reasoner System MVP

Status: Discovery & Framing draft for story `TRS-zpo4`
Canonical machinery architecture: `design/ARCHITECTURE.md`
Source of record: `docs/sources/whole-system-2026-09-19.md`
Scope: local typed-fixture vertical slice plus staged target architecture
## 1. Architectural decision

Build a contract-first local pipeline before enabling any live component:

```text
fixtures -> 3-route policy -> one async reasoner -> validation/preflight
         -> append-only hash-scoped events -> clean renderer
```

The first implementation is deterministic and local: no network, credentials,
raw prompt/audio persistence, or external tool execution. This isolates safety
and contract decisions from target voice-stack timing and operations.

## 2. Fixed model boundaries

1. PersonaPlex/Moshi is not a native tool-calling model; it is the talker and
   must not receive schemas or execution authority.
2. Voxtral Small may emit structured `tool_calls`, but it does not execute
   tools; proposals still pass validation and the executor boundary.
3. Voxtral Realtime is transcription-oriented, not the reasoner or executor.
4. Jev routes; it does not execute tools and has no action authority.

No adapter, prompt, integration, or optimization story may weaken them.

## 3. Target and first-slice components

| Boundary | Target / first slice | Never does |
| --- | --- | --- |
| Audio Gateway | Target audio/session/interruption; absent in Slice 0 | Reason or execute |
| Transcription | Target Voxtral Realtime; fixture transcript locally | Tool calling or routing |
| Routing | Target Jev decision; local calibrated fixture policy | Execute tools |
| Talker | Target PersonaPlex response; deferred | Tools, memory, or planning |
| Job Manager | Async reasoner work; local test state machine | Call tools directly |
| Reasoner | One direct reasoner; local proposal source locally | Execute tools or render final speech |
| Validator + Policy | Required allowlist/schema/risk/consent checks | Contact external services or execute |
| Tool Executor | Target validated actions with server credentials; deferred | Expose secrets to models |
| State + Memory | Target Redis and one governed memory platform; absent | Bypass audit or become sole truth |
| Event Ledger | Target Postgres; local append-only hash chain | Store raw prompt/audio |
| Renderer + Observability | Required clean text/report contract | PersonaPlex injection or invented metrics |

## 4. First-slice data flow

| Route | Flow |
| --- | --- |
| `chitchat` | Load fixture, hash transcript in memory, apply policy, render fast response, append route/response events. Reasoner stays asleep. |
| `needs_tools` | Create an async job with IDs, bounded context, consent, state/catalog/policy versions and no credentials. Parse one structured proposal, validate every action, preflight policy, append lifecycle events, then render only an allowed clean result. Slice 0 does not execute tools. |
| `unclear` | Apply policy, generate one bounded clarification, append events, and invoke neither reasoner nor tools. |

## 5. Routing contract

Router output:

```json
{"schema_version":"1","labels":{"chitchat":0.02,"needs_tools":0.96,"unclear":0.02},
 "selected_label":"needs_tools","confidence":0.96,"route":"needs_tools",
 "risk":"low","thresholds_version":"slice0-v1"}
```

Initial thresholds:

- `chitchat` requires selected-label confidence `>= 0.90`;
- `needs_tools` requires selected-label confidence `>= 0.80`;
- all missing/invalid calibration or unevaluable-risk cases route to `unclear`.

Thresholds are versioned data. Reports must show values adjacent to boundaries
and sensitivity. Unsafe intent may force a guarded path, but safety is not an
additional user-visible route.

## 6. Reasoner and action contracts

A valid proposal contains job/turn/session IDs, a candidate user answer, ordered
typed actions or a no-action marker, justified state updates, confidence and
uncertainty, input/catalog hashes, model or fixture provenance, and a refusal
reason when applicable. It never contains credentials, hidden prompts,
unrestricted arguments, or an executed-result claim.

Slice 0 declares a versioned catalog conceptually based on:

| Action | Local behavior | Checks |
| --- | --- | --- |
| `search` | Deterministic local fixture result; no web | Allowed scope, query type/length, result bound |
| `read_state` | Read only fixture state | Allowed key and read scope |
| `write_state` | Record validated intended write; no durable platform write | Allowed key, typed value, range, justification |

Every catalog entry declares canonical name/schema, argument/result types,
permission and risk, ranges/cardinalities/state keys, idempotency and
reversibility, provenance/consent requirements, and rejection codes.

Validation fails closed for unknown names, extra privileged arguments, malformed
types, out-of-range values, missing justification, missing provenance, consent
mismatch, expired state, duplicate non-idempotent proposals, or policy that
cannot be evaluated.

Multi-tool execution, chaining, code execution, payments, messaging, calendar,
CRM, database mutation, and web fetching are deferred. A later executor remains
a separate server-side boundary and remains the only component that can touch
credentials.

## 7. Asynchronous slow-path architecture

The fast path never waits for the reasoner. A slow job carries an immutable ID,
originating turn epoch, cancellation state, monotonic timestamps, 30-second
stale TTL, maximum result age, terminal reason, response priority, and
hash-scoped links to route/proposal/validation/policy/output events.

Transitions: `pending -> running -> waiting_confirmation -> completed`, with
`pending -> failed`, and running or waiting jobs becoming `canceled`,
`downgraded`, or `failed`.

Cancellation or downgrade is required on explicit cancellation, superseded turn
epoch, TTL/age expiry, material intent change, irrecoverable validation/policy
failure, or unsafe presentation.

Cancel means no normal-result rendering. Downgrade means only a bounded,
non-action summary or resume offer can render. Confirmation cannot be reused
after cancellation or argument changes.

## 8. Policy preflight and confirmation

Policy runs before execution and consequential confirmation. Inputs are action
name, canonical arguments, risk, consent, permission, privacy classification,
reversibility, scope, identity, and catalog version.

Outcomes are `allowed_without_confirmation` only for narrowly scoped low-risk
local actions, `confirmation_required`, or `rejected`.

High-risk categories include external send, booking, payment, deletion,
private-data disclosure, and code execution. Confirmation must match the exact
action hash, canonical arguments, subject/target, user/session, policy version,
and active TTL. Confirmation events record consent evidence and expiry; they do
not record raw prompts.

The reasoner can neither grant permission nor bypass preflight. Jev and
PersonaPlex cannot confirm or execute actions. Voxtral Small structured output,
if ever enabled, remains a proposal and is subject to the same path.

## 9. Privacy, provenance, and event ledger

Raw prompts, raw model requests/responses, hidden instructions, and raw audio
are processing inputs only. They must be released when the local run or target
turn ends and must not be copied into fixtures, logs, errors, traces, memory,
metrics, or persistent stores.

Events may retain schema/type/version; event/session/turn/job IDs and turn
epoch; content hash, length, and media type; consent and policy versions; route
calibration and threshold versions; model or fixture provenance; action name,
argument hash, status, latency, and cost class; validation/policy result and
rejection reason; necessary state key/value hash and classification; response
ID/channel/state/latency; and prior-event chain metadata.

They must not retain raw prompt/audio, credentials, full hidden prompts,
unreviewed private tool output, or unhashed sensitive arguments. A future
service cannot weaken this contract.

Event types cover fixture, route, job/proposal, validation, policy,
confirmation, terminal state, state change, response, report, and integrity.

Every event is append-only. Updates and deletes are implementation errors.
Each event links to the scoped hash of its input and, where applicable, the
canonical action proposal. Chain integrity is computed over a canonical event
body excluding the stored chain field; the exact canonicalization algorithm is
fixed by the implementation story and remains stable for the fixture set.

The verifier must detect missing IDs, ordering gaps, invalid prior hashes,
duplicate terminal states, and mutations. A broken chain disables the affected
action path rather than allowing unaudited work.

## 10. Security, storage, and memory staging

Slice 0 permits only bounded in-memory fixture state and a versioned local event
ledger. Redis, Postgres, Mem0, Cognee, Zep/Graphiti, and Letta are deferred; no
memory platform may become the sole copy of important state. Future adoption
needs privacy/retention review, provenance, replay, deletion, ownership, and
measured justification.

Authorization occurs at validator/policy/executor boundaries, never from model
confidence. Credentials are absent in Slice 0 and later remain only in the
server-side executor. Typed schema/range/scope checks fail closed; transcripts
and tool text are untrusted and cannot alter policy, catalog, consent,
thresholds, or channels. The system uses one reasoner, a fixed catalog, append-only
provenance, filtered rendering, and fail-closed ledger/policy errors.

## 11. Observability and metrics

All metrics include fixture-set version, route denominators, UTC window, and
configuration hashes. No metric may be fabricated or inferred from a missing
event.

Quality metrics are routing/per-route accuracy, missed work, false wakeups,
unclear precision, validation/policy correctness, and target-only tool success.
Latency metrics are router, reasoner, response, and route-to-render
p50/p95/p99 plus interruption/cancellation. Privacy/integrity metrics are raw
record count, provenance completeness, and valid-chain ratio.

Use `docs/BUSINESS.md` §7 thresholds. Missing denominators mean “not evaluated”;
stratification cannot be blended away; rollback forces `needs_tools` to guarded
`unclear`; privacy/validation/policy/integrity failures are hard stops; timing
is monotonic and excludes unrelated UI time.

## 12. Deployment and testing strategy

Tests cover fixture schemas; all routes and thresholds; valid/invalid actions
and rejection codes; confirmation accept/decline/expire/change; stale
cancellation/downgrade; renderer filtering; append/hash-chain verification; zero
raw prompt/audio persistence; and zero network/credential access. Invalid router
or reasoner output, ambiguous validation, unavailable policy, stale results,
renderer conflict, ledger failure, state mismatch, and missing consent all fail
closed. Later live adapters reuse these tests and require consent, data mapping,
credential isolation, latency baseline, and rollback.

## 13. Story constraints

Derived stories must name a schema/boundary, use typed outcomes and negative
tests, emit provenance, prove raw-content non-persistence, avoid unauthorized
network/credentials, report metric versions/denominators, preserve model
boundaries, and add no live/service dependency to Slice 0.
