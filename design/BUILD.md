# BUILD: Talker Reasoner System

Mode: full (self-contained over the `design/` tree)

## 1. Purpose and scope

Build a staged, single-operator fast/slow voice agent in which PersonaPlex preserves realtime conversation, Voxtral Realtime transcribes, Jev routes, a direct reasoner only proposes typed actions, an Action Governor validates and authorizes them, a separate renderer speaks safe results, and an append-only minimized ledger proves what happened. The first implementation is deterministic and offline; live models, durable stores, MCP tools, Dagger, Treg, and semantic memory unlock only through the gates below.

In scope:

- typed fixture and contract slice;
- three-route calibrated policy;
- one asynchronous reasoner proposal;
- validation, policy preflight, exact confirmation, cancellation, and downgrade;
- minimized append-only audit and replay;
- clean response rendering;
- staged live voice, durable state, read-only MCP, deterministic execution, billable tools, and governed memory.

Out of scope until explicit milestones:

- multi-user production;
- PersonaPlex context injection;
- autonomous tool chaining;
- payments, messaging, calendar mutation, CRM mutation, or arbitrary code execution;
- semantic memory as the sole source of truth;
- raw audio/transcript persistence.

## 2. Glossary

| Term | Definition |
|---|---|
| Operator | The single authorized human who uses, consents, confirms, and administers the system. |
| FastPath | Low-latency PersonaPlex conversation path; never owns tool authority. |
| SlowPath | Async reasoner proposal, validation, policy, confirmation, execution, and rendering path. |
| AdminPlane | Human/controller-only surface for catalogs, MCP servers, kits, thresholds, and credentials. |
| RuntimePlane | Constrained live-turn surface; may inspect or invoke only allowlisted capabilities. |
| ProcessingOnly | A value that may exist during a bounded turn and must be released, not persisted. |
| ScopedHash | Deterministic hash over canonical content and an explicit scope. |
| ModelProposal | Structured model suggestion with no execution authority. |
| ActionProposal | Typed but untrusted suggestion to invoke a cataloged action. |
| ValidatedAction | Schema-valid action bound to catalog, policy, consent, state, and provenance. |
| PolicyDecision | One of exactly three preflight outcomes: allowed without confirmation, confirmation required, or rejected. |
| Confirmation | Explicit operator consent for one exact action hash and canonical arguments during a bounded TTL. |
| ToolCatalog | Immutable reviewed version of tool schemas, permissions, risks, bounds, and provenance. |
| EventLedger | Append-only minimized chain of route, action, policy, state, response, and integrity evidence. |

## 3. Domain model (the what)

The canonical model is `design/domain.modelith.yaml`; its rendered overview is `design/domain.modelith.md`. It currently declares 16 entities, 36 invariants, and scenarios covering fast/slow separation, fail-closed routing, stale work, confirmation, privacy canaries, capability red-teaming, and hot state.

### Data dictionary

| Entity | Key attributes | Lifecycle |
|---|---|---|
| VoiceSession | sessionId, status, dataBoundary, startedAt, endedAt | Active, Degraded, Closed |
| ConversationTurn | turnId, turnEpoch, status, ephemeralTranscript, inputHash, intentHash | Receiving, Routed, SlowPath, AwaitingConfirmation, Responding, Terminal |
| RoutingDecision | labels, selectedLabel, confidence, risk, thresholdsVersion, calibrationVersion | immutable decision |
| ReasonerJob | jobId, status, terminalReason, staleTtlSeconds, resultMaxAgeSeconds, responsePriority | Pending, Running, WaitingConfirmation, Completed, Canceled, Downgraded, Failed |
| ReasonerProposal | schemaVersion, candidateAnswer, confidence, uncertainty, inputHash, catalogHash, policyVersion, provenance, refusalReason | immutable |
| ActionProposal | actionName, argumentsHash, justification, subject, target, provenance | immutable |
| ValidatedAction | actionHash, catalogVersion, policyVersion, privacyClassification, idempotent, reversible | derived immutable |
| PolicyDecision | outcome, rejectionCode, policyVersion, decidedAt | immutable |
| Confirmation | confirmationHash, actionHash, explicit, grantedAt, expiresAt | active, consumed, expired |
| ToolCatalog | catalogVersion, catalogHash, status, policyVersion | Draft, Reviewed, Active, Retired |
| ToolDefinition | canonicalName, capability, sourcePlane, schema hashes, permission, risk, reversible, idempotent | catalog-owned immutable |
| ToolExecution | executionId, status, resultHash, latencyMs, costClass, idempotencyKey | Proposed, Authorized, Dispatched, Succeeded, Failed, TimedOut, Rejected |
| HotState | snapshotVersion, ttlSeconds, keysHash, dataBoundary | TTL store record |
| LedgerEvent | eventId, eventType, inputHash, contentLength, mediaType, consent/policy versions, prior ID/hash, chain hash | append-only |
| Response | responseId, channel, renderState, priority, boundedText, latencyMs | immutable render record |
| MemoryRecord | memoryId, contentHash, summary, provenance, status, consentVersion | Candidate, Approved, Active, Superseded, Rejected, Deleted |

The complete relationships, action ownership, invariant statements, and scenarios are in the Modelith file. Do not define a second schema in code.

## 4. Architecture (the how)

The source C4 model is `design/workspace.dsl`; exports are under `design/diagrams/`. The architecture contract, interfaces, dependency failure postures, adoption closure, persistence placement, event contracts, NFRs, and staged rollout are in `design/ARCHITECTURE.md`.

Runtime topology:

```text
TypeScript Voice Edge
  -> PersonaPlex talker
  -> Voxtral Realtime transcription
  -> Python Routing Service / Jev
  -> Python Reasoner Coordinator / Direct Reasoner
  -> Python Action Governor
  -> Tool Catalog
  -> Python Tool Gateway
       -> MAGG runtime plane
            -> Context Forge, Dagger, Treg (deferred)
       -> Local MCP Tool
  -> Renderer / Clean TTS
  -> Redis Hot State
  -> Event Ledger / PostgreSQL
  -> Memory Governor / deferred platform
```

Hard boundary rules:

- Voice Edge never imports Action Governor or Tool Gateway.
- Routing never reaches Tool Gateway.
- Reasoning never reaches MAGG, Treg, Context Forge, Dagger, or memory.
- Tool Gateway is the only executor boundary.
- Event Ledger never imports business components.
- Memory Governor is the only memory platform boundary.

Migration implementation plan: N/A - no legacy/target transition.

Neighbor stand-ins and test environment: N/A - not a pack child.

## 5. Behavior: the state machines (the logic)

Seven machines are authoritative:

| Machine | Purpose | Matrix |
|---|---|---|
| `design/machines/VoiceSession.machine.json` | session degradation, closure, and processing-only release | `VoiceSession.matrix.md` |
| `design/machines/ConversationTurn.machine.json` | transcript binding, route, slow path, confirmation wait, response, cancellation | `ConversationTurn.matrix.md` |
| `design/machines/ReasonerJob.machine.json` | reasoner request, proposal binding, confirmation, cancellation, downgrade, failure | `ReasonerJob.matrix.md` |
| `design/machines/ToolCatalog.machine.json` | admin-only draft, review, activation, retirement | `ToolCatalog.matrix.md` |
| `design/machines/ToolExecution.machine.json` | authorization, allowlisted dispatch, output filtering, timeout, failure | `ToolExecution.matrix.md` |
| `design/machines/MemoryRecord.machine.json` | governed candidate approval, activation, recall, supersession, deletion | `MemoryRecord.matrix.md` |
| `design/machines/EventLedger.machine.json` | append, verify, and fail closed on chain break | `EventLedger.matrix.md` |

Implement each named unit exactly as specified in its matrix. The machine JSON is the transition authority; the matrices are the guard, action, actor, and failure authority.

## 6. Traceability matrix

| invariant id | enforced by (guard / structural) | in component | interface contract | test id(s) |
|---|---|---|---|---|
| `session-processing-boundary` | `transcriptValidAndBoundaryConsented` plus VoiceSession boundary context | VoiceSession / Voice Edge | Voice Edge -> Routing | `T-VOIC-*`, `T-CONV-01`, `P-boundary-consent` |
| `raw-input-ephemeral` | `releaseProcessingOnlyValues` structural processing-only ownership | VoiceSession / ConversationTurn | close and terminal events | `T-VOIC-02`, `T-VOIC-03`, `T-CONV-11`, `P-privacy-canary` |
| `route-fail-closed` | `routeIsNeedsToolsAndValid`; no unguarded slow path from invalid route | Routing / ConversationTurn | Routing -> Reasoning | `T-CONV-03`, `T-CONV-04`, `P-route-fail-closed` |
| `transcriber-no-authority` | structural: transcription interface returns transcript/hash only | Voice Edge | Voice Edge -> Routing | `C-boundary-transcriber` |
| `job-staleness-bounded` | `STALE_TTL`, epoch cancellation, and result-age policy | ReasonerJob | ConversationTurn -> ReasonerJob | `T-REAS-04`, `T-REAS-07`, `P-stale-work` |
| `canceled-work-silent` | `recordCanceledByUser` and terminal renderer contract | ReasonerJob / Renderer | ReasonerJob -> Renderer | `T-REAS-02`, `T-REAS-04`, `T-REAS-12`, `C-render-cancel` |
| `router-no-authority` | structural: Routing exposes decision only | Routing | Routing -> Reasoning / Renderer | `C-boundary-router` |
| `slow-path-only-after-route` | `routeIsNeedsToolsAndFresh` | ReasonerJob | Routing -> Reasoning | `T-REAS-01`, `P-route-fail-closed` |
| `reasoner-proposes-only` | `requestReasonerProposal` actor returns a typed proposal only | Reasoner Coordinator | Reasoning -> external reasoner | `T-REAS-08`, `T-REAS-09`, `T-REAS-10`, `C-reasoner-proposal` |
| `proposal-identity-bound` | `requestReasonerProposal` actor pre/post and bind actions | Reasoner Coordinator | Reasoning -> Action Governor | `T-REAS-08`, `T-REAS-09`, `C-proposal-identity` |
| `contract-fail-closed` | `recordFailClosedReason` on malformed/unmatched proposal | ReasonerJob | Reasoning -> Action Governor | `T-REAS-03`, `T-REAS-06`, `T-REAS-10`, `T-REAS-14`, `P-fail-closed` |
| `action-schema-fail-closed` | structural Action Governor validation before any policy or dispatch | Action Governor | Reasoning -> Action Governor | `C-action-validation` |
| `action-no-credentials` | proposal and action schema credential scans | Action Governor | Reasoning -> Action Governor | `P-no-credentials` |
| `catalog-version-pinned` | `bindCatalogAndIdempotency`; `catalogHashIsImmutable` | Tool Catalog / Tool Gateway | Catalog -> Governor / Gateway | `T-TCAT-03`, `T-TEXE-01`, `C-catalog-pin` |
| `policy-before-execution` | `actionAllowedAndConfirmationsSatisfied` and `definitionIsAllowlistedAndActive` | Action Governor / Tool Gateway | Governor -> Gateway | `T-TEXE-01`, `T-TEXE-02`, `T-TEXE-04`, `C-policy-before-execution` |
| `policy-three-outcomes` | structural PolicyDecision result type and exhaustive policy tests | Action Governor | Governor -> Gateway | `C-policy-three-outcomes` |
| `confirmation-exact-and-expiring` | `policyRequiresExactConfirmation`, `allExactConfirmationsSatisfied` | Action Governor | Governor -> Renderer | `T-CONV-07`, `T-REAS-08`, `T-REAS-11`, `C-confirmation-exact` |
| `confirmation-single-use` | `consumeConfirmations` and used-hash context | Action Governor | Renderer -> Governor | `T-REAS-11`, `P-confirmation-single-use` |
| `catalog-reviewed-before-active` | `schemasProvenanceAndPolicyComplete`; `catalogHashIsImmutable` | Tool Catalog | Admin -> Catalog | `T-TCAT-02`, `T-TCAT-03`, `P-catalog-review` |
| `runtime-cannot-mutate-capability` | ToolCatalog state-specific ignores; MAGG admin/runtime split | Tool Catalog / MAGG boundary | Admin -> Catalog / MAGG | `T-TCAT-*`, `P-capability-red-team` |
| `tool-schema-provenance` | `schemasProvenanceAndPolicyComplete` and reviewed schema hashes | Tool Catalog / Tool Definition | Catalog -> Governor | `T-TCAT-02`, `P-tool-schema-provenance` |
| `tool-allowlist-only` | `definitionIsAllowlistedAndActive` | Tool Gateway | Gateway -> MAGG/local MCP | `T-TEXE-04`, `P-capability-red-team` |
| `credential-isolation` | `invokeAllowlistedTool` server-side actor contract | Tool Gateway | Gateway -> executors | `T-TEXE-04`, `T-TEXE-09`, `P-no-credentials` |
| `tool-output-filtered` | `toolOutputPassedFiltering`; `recordUnsafeOutput` | Tool Gateway | Gateway -> Reasoner/Renderer | `T-TEXE-09`, `T-TEXE-10`, `P-tool-output-filter` |
| `tool-result-not-sole-truth` | filtered result plus EventLedger provenance | Tool Gateway / Event Ledger | Gateway -> Ledger | `T-TEXE-09`, `T-EVEN-*`, `P-tool-audit` |
| `hot-state-minimized` | bounded HotState schema and serialization scan | Hot State | Voice Edge -> Redis | `P-hot-state-minimized` |
| `hot-state-ttl` | finite TTL field and expiry contract | Hot State | Hot State -> Redis | `P-hot-state-ttl` |
| `ledger-append-only` | `eventIsMinimizedAndChained`; `appendCanonicalEvent` | Event Ledger | Ledger -> PostgreSQL | `T-EVEN-01`, `T-EVEN-04`, `P-append-only` |
| `ledger-minimized` | `eventIsMinimizedAndChained` | Event Ledger | all ledger producers | `T-EVEN-01`, `P-privacy-canary` |
| `ledger-integrity-fail-closed` | `chainHasNoGapsOrMutations`; Broken final state | Event Ledger | Ledger -> Observability | `T-EVEN-03`, `T-EVEN-05`, `T-EVEN-06`, `T-EVEN-08`, `T-EVEN-09`, `P-chain-integrity` |
| `response-filtered` | renderer contract and `recordSafeDowngrade` | Renderer | Renderer -> Voice Edge | `T-CONV-11`, `T-REAS-05`, `T-REAS-13`, `C-render-filter` |
| `memory-provenance-bound` | `provenanceConsentAndReviewComplete`; `recordApprovalEvidence` | Memory Governor | Ledger -> Memory | `T-MEMO-01`, `T-MEMO-06`, `P-memory-provenance` |
| `memory-not-sole-truth` | EventLedger source of truth plus memory versioning | Memory Governor | Memory -> Ledger | `T-MEMO-07`, `P-memory-not-sole-truth` |
| `memory-deletable` | `memoryPlatformDeletionTestPassed`; `deleteFromPrimaryAndBackups` | Memory Governor | Operator -> Memory | `T-MEMO-03`, `T-MEMO-05`, `T-MEMO-08`, `T-MEMO-09`, `P-memory-delete` |
| `talker-no-authority` | structural PersonaPlex adapter returns audio/text only | Voice Edge | Voice Edge -> PersonaPlex | `C-boundary-talker` |
| `model-boundaries-explicit` | structural adapters and dependency deny rules | all model adapters | Architecture Contract | `C-model-boundaries` |

## 7. Test specification (the hard-TDD oracle)

Transition tests parse these committed oracle files and assert next state and expected actions for every row, keyed by stable id:

- `design/machines/VoiceSession.oracle.md`
- `design/machines/ConversationTurn.oracle.md`
- `design/machines/ReasonerJob.oracle.md`
- `design/machines/ToolCatalog.oracle.md`
- `design/machines/ToolExecution.oracle.md`
- `design/machines/MemoryRecord.oracle.md`
- `design/machines/EventLedger.oracle.md`

There are 62 transition rows. Every stable id must appear whole-token in the suite. One parser-driven conformance module per oracle is preferred; it must parse the Markdown table at runtime, not hard-code rows without stable ids.

Additional tests the oracles cannot derive:

1. For every conjunctive guard, test one falsified clause at a time. For example `actionAllowedAndConfirmationsSatisfied` requires action hash, policy version, and every confirmation; provide three cases where exactly one clause is false.
2. Contract tests at every Architecture Contract boundary, including invalid shape, stable errors, idempotency, and duplicate delivery.
3. Property tests for all 36 invariant ids: privacy canaries, no credentials, fail-closed routing, append-only chain, confirmation reuse, capability mutation, hot-state TTL, and memory deletion.
4. Integration tests against real local dependencies where available. Before the real service is authorized, use a contract-tested stand-in, never an ad-hoc mock.
5. E2E tests through the real CLI for every route and terminal state. No raw transcript may appear in evidence.

## 8. State migration

- VoiceSession, ConversationTurn, ReasonerJob, ToolCatalog, ToolExecution, MemoryRecord, and EventLedger have no persisted production instances yet.
- Slice 0 persists immutable fixture records and an in-memory/local ledger only.
- Before any state is persisted, add a migration mapping table and drain rule to this section.
- If Redis or PostgreSQL is enabled, persisted values must map exactly to these machine states. Unknown values fail loudly; silent coercion is prohibited.

## 9. Build plan

**M0 - Machinery walking skeleton**

Instantiate the cross-cutting safety pattern: parse all seven transition oracles, map machine events to the existing typed Python contracts, keep raw content processing-only, and run all contract, privacy, architecture, and replay tests offline.

DoD: all 62 stable ids in the seven oracle files appear in passing tests, including `CONV-02965d`; all 36 invariant property/contract tests pass; existing Slice 0 tests remain green; `machinery check design` has zero blocking findings; no network, credential, live audio, durable service, or semantic memory is enabled.
Status: closed

**M1 - Explicit architecture extraction**

Refactor only where needed so current Python modules match the declared boundaries and G4 can resolve imports. Add the TypeScript edge package skeleton without live audio.

DoD: `machinery check design --impl .` is green or every current violation is explicitly baselined; all M0 tests remain green; no behavior changes except typed boundary extraction.

**M2 - Voice session and turn contracts**

Implement VoiceSession and ConversationTurn guards/actions against the machine matrices, including typed/spoken parity, one-audio-stream arbitration, accessibility metadata, and turn-epoch cancellation.

DoD: `VOIC-305554`, `VOIC-e62d1f`, `VOIC-32ea66`, and all `CONV-*` rows pass; privacy canaries prove ephemeral release; renderer arbitration prevents overlap.

**M3 - Live single-operator voice loop**

Add consented PersonaPlex, local or explicitly cloud-disclosed Voxtral Realtime, and Jev adapters behind fail-closed fallback. No external tool executes.

DoD: routing benchmark and stability gates from BUSINESS.md pass; invalid calibration routes to unclear; reconnect and interruption tests pass; cloud boundary is recorded and consented.

**M4 - Durable minimized state**

Enable Redis hot state and PostgreSQL append-only event storage only after privacy and replay gates pass.

DoD: HotState TTL/minimization, PostgreSQL append, backup/restore, canary deletion, and EventLedger transition tests pass; no raw content is stored.

**M5 - Catalog and read-only MCP discovery**

Enable the admin-only ToolCatalog and MAGG runtime plane. Expose list/info/status/check and one local read-only MCP tool.

DoD: all `TCAT-*` rows pass; capability red-team proves RuntimePlane cannot mutate MAGG or catalog state; tool schema provenance and output filtering pass.

**M6 - Governed local execution**

Authorize and execute one deterministic local read-only tool through Tool Gateway with credential isolation and result hashing.

DoD: all `TEXE-*` rows pass; exact confirmation, idempotency, timeout, unsafe output, no-credential, and audit tests pass.

**M7 - Deferred execution backends**

Behind separate stories, add Context Forge after redeploy/health, Dagger test/lint/build after scheduler gates, and Treg catalog/budgeted execution after spend controls.

DoD: each backend has health evidence, fixed allowlist, schema hash, latency/cost bound, cancellation, confirmation, audit, and rollback tests; no backend is enabled merely because it is installed.

**M8 - Governed memory**

Add Memory Governor and one selected memory platform only after recall and deletion requirements are explicit.

DoD: all `MEMO-*` rows pass; provenance, consent, recall bound, supersession, primary/backup deletion, and not-sole-truth tests pass.

## 10. Language realization notes

Target languages:

- Python 3.12+ for routing, reasoner coordination, action governance, ledger, tool gateway, and memory governor.
- TypeScript for browser/audio/WebSocket edge and renderer presentation client.

Python realization:

- explicit immutable dataclasses or typed records;
- explicit state field plus transition table;
- one single-writer task per `jobId`, `executionId`, or `memoryId`;
- optimistic version or database lock when persistence is enabled;
- no hidden global mutable state.

TypeScript realization:

- typed WebSocket/audio stream adapters;
- explicit audio arbitration state;
- no direct model or tool SDK imports in the edge boundary.

### Toolchain and versions

- Python: test with CPython 3.12.9 (`python3.12`); CI may also test 3.14.
- Package manager: uv 0.6.x until a lockfile is added, then use the committed lockfile exactly.
- Test framework: pytest >=9,<10; current local run used 9.0.2.
- Modelith: 0.4.0.
- Machinery: 0.3.11.
- Structurizr CLI: 2025.11.09.
- No runtime dependency is authorized by this design. Future adapters must add exact pins and a lockfile in their milestone.

## 11. Hard-TDD protocol (read this before writing any code)

1. RED precondition: run `machinery check design` and require zero blocking findings before deriving tests. A red design is an untrustworthy spec.
2. A test-writer agent reads sections 6 and 7 and writes the full suite from the oracle files, matrices, boundary contracts, and invariant properties. If no fresh-context writer is available, the same agent runs RED then GREEN sequentially; the gates separate the phases.
3. RED exit requires all of the following:
   - every oracle stable id appears whole-token in the suite;
   - every guard-conjunction clause has a falsifying test;
   - every invariant has a property or contract test;
   - `machinery check design --impl .` is green over the compile skeleton;
   - the suite runs and fails on assertions, not import/compile errors;
   - new test files are clean under the project formatter and linters.
4. Tests then lock. The implementer may not edit them to make them pass.
5. GREEN requires the locked tests and `machinery check design --impl .` to pass together.
6. Generated oracle-conformance tests live apart from hand-written boundary/property tests.
7. If a test is wrong, stop and fix the design; regenerate oracle files and the affected tests. Never silently adjust a locked test.

## 12. Open questions and residual risks

- Exact live Jev calibration and threshold quality must be measured before M3.
- PersonaPlex GPU residency and 3090 process scheduling remain an explicit operations gate.
- Context Forge must be redeployed and health-checked before use; historical operability is not current evidence.
- MAGG is AGPL-3.0 and needs legal review before network-facing deployment.
- Treg licensing, spend controls, duplicate-charge behavior, and provider failure semantics need a dedicated milestone.
- Memory platform selection remains open; deletion and backup semantics decide it, not benchmark scores alone.
- `machinery check --impl .` currently cannot resolve the existing single-package Python module imports against the future boundary layout. M1 must either restructure package boundaries or generate a reviewed ratchet; do not claim G4 success before then.

### What the gates do not verify

Not covered by any deterministic check or proof, by construction: whether the interrogation extracted the RIGHT invariants (a shallow domain model gates clean); guard and action semantics in code (the named-unit contracts carry them into tests; a wrong implementation of a correctly-named guard is caught by tests, not proofs); races between concurrent machine instances, and message loss, duplication, or reordering between machines (the models are single-instance; the event-contract table and the idempotency contracts govern those seams, and the tests exercise them); whether migration transformations preserve real production data (Gm proves decision coverage, not the implementation or a database run); coupling through shared database tables or bus topics (invisible to import analysis; the event-contract table governs it); and security, capacity, and observability beyond what the Phase 2 NFR record captures.
