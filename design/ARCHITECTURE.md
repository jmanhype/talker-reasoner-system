# Architecture: staged Talker Reasoner System

Status: Machinery Phase 2 draft for the staged hybrid target
Model source: `design/domain.modelith.yaml`
C4 source: `design/workspace.dsl`

## 1. Phase 0 frame

Build a **single-operator, staged fast/slow voice agent**. Slice 0 is deterministic and local: typed fixture transcripts, three-label routing, one reasoner proposal, action validation, policy preflight, append-only hash-scoped events, and a clean renderer. Live PersonaPlex, hosted Voxtral, Jev, Redis, Postgres, semantic memory, MAGG, Context Forge, Dagger, and Treg are explicit later phases behind privacy, health, budget, and authorization gates.

The target implementation uses a **TypeScript voice/audio edge** and a **Python model, routing, policy, reasoner, ledger, and tool core**. This is a greenfield design beside an existing Python Slice 0 implementation; the existing contracts are evidence, not a constraint that prevents extracting the intended boundaries.

## 2. Architectural decisions

1. **Split fast and slow paths.** PersonaPlex owns realtime conversation. The reasoner is asynchronous and can only produce a typed proposal.
2. **Separate model responsibilities.** PersonaPlex talks, Voxtral Realtime transcribes, Jev routes, and the direct reasoner proposes. No model owns permission or execution.
3. **Fail closed.** Invalid calibration, schema, consent, policy, ledger integrity, renderer conflict, or stale result state blocks the action path.
4. **Minimize data first.** Raw audio and raw transcripts are processing-only. Persistent events store scoped hashes, lengths, classifications, versions, and bounded metadata.
5. **Stage durable state.** Fixture state is first. Redis hot state and Postgres events enter only after local privacy and replay gates.
6. **Separate catalog from execution.** The runtime can read an active reviewed catalog; only the admin plane can change it.
7. **Separate MAGG planes.** A human/controller admin plane manages MCP servers and kits. The voice runtime can list, inspect, health-check, and proxy only allowlisted tools.
8. **Isolate credentials.** Only the server-side Tool Gateway and its downstream executor adapters can hold execution credentials.
9. **Use clean TTS first.** PersonaPlex text/audio injection is deferred until routing, tool, and collision behavior are stable.

## 3. C4 views

The source of truth is `design/workspace.dsl`. It defines:

- a **system context view**: operator, Talker Reasoner System, PersonaPlex, Voxtral, Jev, reasoner, MAGG, Context Forge, Dagger, Treg, local MCP, Postgres, Redis, memory, TTS, and observability;
- a **container view**: Voice Edge, Routing Service, Reasoner Coordinator, Action Governor, Tool Catalog, Tool Gateway, Response Renderer, Event Ledger, Hot State, Memory Governor, and Observability.

`structurizr-cli` 2025.11.09 exported both views successfully to `design/diagrams/structurizr-Context.mmd` and `design/diagrams/structurizr-Containers.mmd`.

## 4. Boundary responsibilities

| Boundary | Owns | Must not do |
|---|---|---|
| `voiceEdge` | Typed and spoken input, audio/session transport, one-stream voice arbitration, turn epochs, interruption, accessibility channel metadata, ephemeral transcript handoff | Validate actions, grant consent, execute tools, overlap PersonaPlex with clean TTS, or store raw audio |
| `routing` | Versioned calibration, thresholds, risk classification, fail-closed route | Execute tools, confirm actions, or render slow answers |
| `reasoning` | Async job lifecycle, one typed reasoner proposal, cancellation and staleness | Bypass Action Governor or claim execution |
| `actionGovernor` | Schema/scope validation, policy preflight, exact confirmation, consent checks | Contact external tools or hold credentials |
| `toolCatalog` | Reviewed versioned action definitions, schemas, permissions, risks, bounds | Mutate from RuntimePlane or omit provenance |
| `toolGateway` | Allowlisted execution, credential isolation, output filtering, result hashes | Accept unvalidated model proposals |
| `renderer` | Bounded safe response text/audio, priority, cancellation | Expose private tool output or hidden prompts |
| `eventLedger` | Append-only chain, integrity verification, minimized audit metadata | Store raw transcripts/audio or permit mutation |
| `hotState` | TTL-bound live session snapshot | Become durable truth or hold unfiltered content |
| `memoryGovernor` | Later governed memory lifecycle, provenance, recall, deletion | Run in Slice 0 or become sole truth |
| `observability` | Versioned denominators, latency, privacy, integrity, and replay metrics | Fabricate metrics or copy raw content |

## 5. Modelith action ownership

| Modelith action | Owning C4 element |
|---|---|
| `VoiceSession.start`, `VoiceSession.degrade`, `VoiceSession.close` | `voiceEdge` |
| `ConversationTurn.transcribe`, `ConversationTurn.advanceEpoch`, `ConversationTurn.cancel`, `ConversationTurn.finish` | `voiceEdge` |
| `ConversationTurn.route`, `RoutingDecision.decide` | `routing` |
| `ReasonerJob.create`, `ReasonerJob.run`, `ReasonerJob.waitForConfirmation`, `ReasonerJob.complete`, `ReasonerJob.cancel`, `ReasonerJob.downgrade`, `ReasonerJob.fail`, `ReasonerProposal.submit`, `ActionProposal.propose` | `reasoning` |
| `ValidatedAction.validate`, `PolicyDecision.preflight`, `Confirmation.grant`, `Confirmation.consume`, `Confirmation.expire` | `actionGovernor` |
| `ToolCatalog.review`, `ToolCatalog.activate`, `ToolCatalog.retire`, `ToolDefinition.define` | `toolCatalog` through the operator-only admin path |
| `ToolExecution.authorize`, `ToolExecution.dispatch`, `ToolExecution.complete`, `ToolExecution.fail`, `ToolExecution.timeout` | `toolGateway` |
| `HotState.write`, `HotState.expire` | `hotState` |
| `LedgerEvent.append`, `LedgerEvent.verify` | `eventLedger` |
| `Response.render`, `Response.block`, `Response.cancel` | `renderer` |
| `MemoryRecord.propose`, `MemoryRecord.approve`, `MemoryRecord.recall`, `MemoryRecord.supersede`, `MemoryRecord.delete` | `memoryGovernor` |

## 6. Interface and boundary contracts

| Producer | Consumer | Shape | Errors | Idempotency |
|---|---|---|---|---|
| `voiceEdge` | `routing` | `ConversationTurn.turnId`, `turnEpoch`, ephemeral transcript, `inputHash`, bounded context hash | `transcript_invalid`, `context_expired` | Retry safe by `turnId` plus epoch |
| `routing` | `reasoning` | `RoutingDecision.selectedLabel=needsTools`, labels, confidence, risk, versions | `route_invalid`, `needs_tools_not_authorized` | Exactly one job per `turnId` plus epoch |
| `routing` | `renderer` | Chitchat or unclear bounded response request | `render_policy_invalid` | Idempotent by route event hash |
| `reasoning` | `actionGovernor` | One `ReasonerProposal`, action proposals, hashes, provenance, bounded confidence | `proposal_invalid`, `identity_mismatch` | Exactly once per job attempt; replay rejected |
| `actionGovernor` | `toolGateway` | `ValidatedAction.actionHash`, canonical argument hash, human-readable action/target/effect, irreversibility, one-time scope, expiry, policy outcome | `confirmation_required`, `policy_rejected` | Idempotency key is action hash plus catalog version |
| `toolCatalog` | `actionGovernor` | Immutable active catalog version, schemas, policy, hash | `catalog_retired`, `hash_mismatch` | Read-only immutable version |
| `toolGateway` | `reasoning`/`renderer` | Filtered result hash, bounded result, status, latency class | `tool_failed`, `timeout`, `output_unsafe` | Executor idempotency key plus action hash |
| `renderer` | `voiceEdge` | Bounded text, channel, priority, terminal state, provenance | `render_blocked`, `result_stale` | Render exactly once per response priority |
| `eventLedger` | `postgres` | Canonical minimized `LedgerEvent` with chain fields | `ledger_write_failed`, `chain_broken` | Event ID is unique and append-only |
| `hotState` | `redis` | Minimized snapshot with TTL | `snapshot_expired`, `state_unavailable` | Write by session and snapshot version |
| admin operator | `toolCatalog` | Reviewed catalog version and hash | `review_incomplete` | Atomic catalog version activation |
| admin operator | MAGG admin surface | Named server or kit mutation with review evidence | `admin_forbidden`, `magg_unavailable` | Server name plus versioned kit hash |

All inter-process schemas are JSON or MCP typed objects. Errors use stable rejection-code enums. Unknown error values are treated as `contract-fail-closed`.

## 7. Dependency mitigation posture

| dependency | failure modes | deployment mitigation | residual behavior the FSM must handle | bound | operator signal |
|---|---|---|---|---|---|
| `personaplex` | WSS disconnect, session lock, audio degradation, reconnect race | local single session; supervised process; reconnect delay longer than lock release | fast path degrades or closes; no tool path activation | one active session; reconnect backoff bounded | `personaplex_session_degraded` and reconnect metric |
| `voxtral` | stream dropout, transcription latency, cloud outage | local capture continues; hosted use explicit consent; fallback unclear route | routing receives missing/partial transcript and fails closed | transcription timeout and maximum partial transcript age | `transcription_degraded`, `transcript_timeout` |
| `jev` | timeout, invalid calibration, unevaluable risk | versioned calibration, cached policy, offline fixture mode | route becomes unclear; reasoner does not wake | routing p95 budget; zero invalid calibration accepted | `router_invalid_calibration`, `router_timeout` |
| `reasoner` | timeout, malformed proposal, refusal, model outage | one direct transport, typed proposal schema, fixture replay | job fails or downgrades; no action executes | job stale TTL 30 seconds first slice | `reasoner_invalid_proposal`, `reasoner_timeout` |
| `magg` | unavailable, tool-list drift, malicious schema/result, admin/runtime confusion | read-only runtime surface, prefixes, fixed kit, JWT, admin plane separation | list/proxy fails; execution rejected; no capability mutation | runtime tool list hash; proxy timeout | `magg_runtime_denied`, `magg_tool_drift` |
| `contextForge` | endpoint unavailable, auth failure, upstream drift | deferred until redeployed and health-checked; allowlist behind MAGG | capability unavailable and rejected | health check and tool schema hash | `contextforge_unreachable`, `gateway_tool_drift` |
| `dagger` | container/runtime failure, build timeout, resource exhaustion | separate 3090/Docker scheduler, narrow test/lint allowlist, cancellation | execution fails or times out; no partial-result rendering | per-action timeout and one concurrent execution first | `dagger_timeout`, `dagger_execution_failed` |
| `treg` | spend, duplicate charge, unavailable provider, credential failure | deferred; catalog search first; BYOK preference; budget ceiling and confirmation | billable execution rejected before dispatch | per-call, per-session, and daily spend caps | `treg_budget_exceeded`, `treg_provider_failed` |
| `localMcp` | process death, schema drift, query leakage | one local read-only process; fixed schema; output classifier | tool fails; no raw output retained | process health check and query/result size bounds | `local_tool_unhealthy`, `local_tool_output_blocked` |
| `postgres` | unavailable, slow write, conflict, backup failure | single local instance first; WAL backup; append-only constraints | event append fails and action path disables | ledger append timeout; nightly backup verification | `ledger_write_failed`, `ledger_backup_failed` |
| `redis` | unavailable, eviction, TTL failure, data leak | local instance; key namespace; TTL; privacy canary | hot path degrades to bounded local context | snapshot TTL and max memory | `hot_state_unavailable`, `hot_state_ttl_violation` |
| `memoryPlatform` | poisoning, provenance loss, deletion failure, recall latency | deferred; approval gate; provenance; backup deletion test | recall omitted; memory candidate rejected | recall timeout and zero undeleted canaries | `memory_recall_failed`, `memory_deletion_failed` |
| `tts` | latency, service unavailable, unsafe audio overlap | clean TTS after renderer; audio gate; cancellation | slow response not spoken | TTS p95 and maximum queue age | `tts_timeout`, `audio_collision_detected` |
| `hotState` | TTL miss, oversized snapshot, privacy leak | bounded keys, hashed values, TTL, memory cap | fast path uses context-free safe fallback | finite TTL and maximum serialized bytes | `hot_state_policy_violation` |

## 8. Technology adoption closure

| Technology | Closure members brought into the architecture | Evidence and residual risk |
|---|---|---|
| PersonaPlex | Python model process, WSS edge, one-session lock, GPU scheduler, voice prompt store, audio gate | Repository carries an MIT license file. OpenSSF Scorecard scan unavailable on 2026-09-19. Single-session lock and GPU residency are hard operational constraints. |
| Voxtral Realtime | Streaming client, consent boundary, ephemeral buffer, partial-transcript timer, local/cloud policy | Hosted processing leaves the local network. Provider/model behavior must be tested per deployment. Scorecard not applicable to a hosted service. |
| Jev | API credential in executor-side config only, calibrated routing schema, versioned thresholds, fallback policy | External proprietary service; no public Scorecard candidate. Availability and calibration must be measured. |
| Direct reasoner | Provider adapter or local GPU process, typed schema, timeout, fixture replay, provenance | Reasoner can propose only. Exact model selection remains an open decision with measured quality, latency, privacy, and cost evidence. |
| MAGG | AGPL service, admin/runtime separation, JWT keys, kit files, mounted MCP processes, health checks | AGPL-3.0 requires legal review before network-facing use. Scorecard unavailable on 2026-09-19. Scopes are informational, so policy enforcement stays in this system. |
| Context Forge | Service deployment, auth, upstream MCP proxies, admin UI, health checks | Historical endpoint no longer resolves. Deferred until redeployed and health-checked. Scorecard unavailable. |
| Dagger | Docker runtime, module cache, GPU/CPU scheduling, artifact storage, narrow pipeline allowlist | OpenSSF Scorecard 5.2 on 2026-09-14. Real container execution is deferred behind policy and confirmation. |
| Treg | Account token, prepaid balance, provider credentials, billing alerts, tool catalog, MCP surface | License metadata is nonstandard and Scorecard unavailable. Billable execution deferred; catalog search may be tested first. |
| Redis | Local stateful service, persistence/backup policy if enabled, TTL policy, key namespace, memory cap | OpenSSF Scorecard 6.9 on 2026-09-14. Enters only after local privacy gate. |
| PostgreSQL | Local database, WAL archive, backup/restore job, retention/deletion procedure, migrations | OpenSSF Scorecard 6.1 on 2026-09-14. Local storage still requires canary and deletion tests. |
| Memory platform | Candidate platform service, primary memory store, derived indexes, backups, deletion path, provenance store | Deferred. No platform is authorized. Scorecard was unavailable for the observed Mem0 repository path on this date. |

## 9. Persistence and placement

| component | machine placement | persistence | concurrency serialization |
|---|---|---|---|
| `ConversationTurn` | in-memory actor/task per live turn in Phase 3 | Slice 0 immutable fixture; later only scoped hashes in Event Ledger | one task per turn; epoch compare-and-cancel |
| `ReasonerJob` | Python async state machine | Slice 0 immutable records plus ledger events; later Postgres job event stream | `jobId` single-writer and legal-transition check |
| `ToolCatalog` | catalog lifecycle machine, but runtime use is an immutable lookup | reviewed JSON now; later Postgres version table | atomic immutable activation; no runtime writes |
| `ValidatedAction`/`PolicyDecision` | part of `ReasonerJob` machine (no machine: derived immutable records serialized with the owning job) | derived immutable records and ledger events | serialized with owning job |
| `ToolExecution` | Python operational machine in Phase 3 | executor record and ledger events; result hash only | idempotency key plus action hash |
| `EventLedger` | Python integrity machine | Slice 0 local immutable chain; later append-only Postgres | event ID sequence and chain hash |
| `HotState` | (no machine: TTL store contract enforced by bounded schema and periodic expiry) | Redis TTL snapshot | session snapshot version compare-and-set |
| `MemoryRecord` | Python lifecycle machine in later phase | deferred memory platform plus Event Ledger provenance | memory ID and version |

## 10. Event-contract table

Enumeration sources: `design/domain.modelith.yaml` entities/actions/scenarios, `docs/ARCHITECTURE.md` Slice 0 flows, and `src/talk_reasoner` contracts. No runtime broker exists yet; `delivery` names the target mechanism and the first implementation remains in-process/append-only unless a queue is explicitly added.

| event | producer | consumer | payload | delivery | ordering | dedupe key |
|---|---|---|---|---|---|---|
| `TRANSCRIPT_NORMALIZED` | `voiceEdge` | `routing` | ConversationTurn.turnId, turnEpoch, inputHash, contentLength, mediaType | exactly-once-effect (in-process turn queue) | per turn FIFO | turnId + turnEpoch |
| `ROUTE_DECIDED` | `routing` | `eventLedger` | RoutingDecision.selectedLabel, confidence, risk, versions | at-least-once (append-only ledger) | per session FIFO | turnId + policyVersion + route hash |
| `SLOW_JOB_REQUESTED` | `routing` | `reasoning` | ConversationTurn IDs, RoutingDecision inputHash, catalogHash | exactly-once-effect (job manager) | per turn FIFO | jobId |
| `FAST_RESPONSE_REQUESTED` | `routing` | `renderer` | route hash, bounded response policy | exactly-once-effect | per turn FIFO | turnId + route hash |
| `PROPOSAL_RECEIVED` | `reasoning` | `actionGovernor` | ReasonerProposal inputHash, catalogHash, policyVersion, provenance | exactly-once-effect | per job FIFO | jobId + proposal hash |
| `JOB_LIFECYCLE_CHANGED` | `reasoning` | `eventLedger` | ReasonerJob.status, TerminalReason, latency class | at-least-once (ledger) | per job FIFO | jobId + status + monotonic time |
| `ACTION_VALIDATED` | `actionGovernor` | `eventLedger` | ValidatedAction.actionHash, catalogVersion, privacy class | at-least-once (ledger) | proposal order | actionHash + validation version |
| `POLICY_DECIDED` | `actionGovernor` | `eventLedger` | PolicyDecision.outcome, rejectionCode, policyVersion | at-least-once (ledger) | action order | actionHash + policyVersion |
| `CONFIRMATION_REQUESTED` | `actionGovernor` | `renderer` | actionHash, human-readable action/target/effect, irreversibility, one-time scope, expiry | at-most-once presentation | highest priority per turn | actionHash + confirmation request version |
| `CONFIRMATION_RECORDED` | `renderer` | `actionGovernor` | Confirmation.actionHash, explicit flag, granted/expiry metadata | exactly-once-effect | per action FIFO | confirmationHash |
| `ACTION_AUTHORIZED` | `actionGovernor` | `toolGateway` | ValidatedAction.actionHash, ToolCatalog version, idempotencyKey | exactly-once-effect | per job action order | actionHash + idempotencyKey |
| `TOOL_RESULT_FILTERED` | `toolGateway` | `reasoning` | resultHash, bounded result, status, latency/cost class | exactly-once-effect | per execution FIFO | executionId |
| `EXECUTION_AUDITED` | `toolGateway` | `eventLedger` | ToolExecution.executionId, resultHash, status | at-least-once (ledger) | per execution FIFO | executionId + event type |
| `RESPONSE_RENDERED` | `renderer` | `eventLedger` | Response.responseId, channel, state, priority, latency | at-least-once (ledger) | per turn FIFO | responseId |
| `TURN_TERMINALIZED` | `voiceEdge` | `eventLedger` | ConversationTurn.turnId, turnEpoch, terminal state | at-least-once (ledger) | per turn last | turnId + turnEpoch |
| `CHAIN_VERIFIED` | `eventLedger` | `observability` | LedgerEvent.eventId, head hash, valid-chain flag | at-least-once | monotonic verification | verification run ID |
| `MEMORY_CANDIDATE_APPROVED` | `memoryGovernor` | `eventLedger` | MemoryRecord.memoryId, contentHash, provenance | at-least-once (ledger) | memory ID FIFO | memoryId + version |

## 11. NFR record

### Security

- Operator authentication is required for admin and confirmation surfaces.
- Runtime policy authorization is enforced by Action Governor and Tool Gateway, never MAGG scopes or model confidence.
- Credentials exist only in server-side executor configuration and are never included in prompts, proposals, ledger events, memory, or responses.
- MCP tool descriptions and results are untrusted input. The runtime cannot mutate the catalog or MAGG capability surface.
- All external execution uses exact action hashes, typed schemas, allowlists, bounded arguments, and confirmation TTLs.

### Capacity and latency

- First live target: one operator, one PersonaPlex session, one active reasoner job.
- Slice 0 tests are local and must remain under their fixture latency bounds.
- Target live budgets are recorded as design budgets, not claims: PersonaPlex loop remains independent; local deterministic routing p95 budget is 300 milliseconds, matching BUSINESS.md section 7; renderer handoff after a terminal result has a 250 millisecond p95 budget; slow jobs use a 30-second stale TTL initially; renderer suppresses stale work even if the reasoner later completes.
- GPU scheduling is mandatory before co-locating PersonaPlex, local Voxtral, or a local reasoner.

### Privacy

- Raw audio, raw transcript, raw model request/response, hidden prompts, and unfiltered tool output are processing-only.
- Persistent fields are minimized, hashed, classified, versioned, and chained.
- Hosted Voxtral or any cloud reasoner requires explicit consent and a `DataBoundary=consentedCloud`.
- Privacy canary tests must inspect logs, Redis, Postgres, memory, backups, errors, metrics, and rendered output before external tool activation.

### Observability

- Every metric reports schema/version, configuration hash, denominator, UTC window, and missing-evaluation policy.
- Alert on invalid calibration, policy bypass, chain break, raw-content persistence, hot-state TTL violation, budget breach, and capability-surface mutation attempt.
- Replay tests reconstruct routing, validation, policy, terminal state, and response decisions from ledger events.

### Accessibility and audio presentation

- Typed input and speech output are equivalent input channels; neither may bypass routing, policy, or audit.
- The renderer supplies accessible, screen-reader-friendly text with channel and priority metadata.
- `voiceEdge` owns a one-active-audio-stream arbiter. PersonaPlex, clean TTS, and any later audio source compete for the arbiter; confirmation and active user speech take precedence over stale slow-path output.
- Confirmation prompts must state action, target, human-readable effect, one-time scope, reversibility, affirmative choice, and safe negative choice. Ambient agreement, changed arguments, another target, or expiry cannot confirm.
- GPU co-residency and process scheduling must be explicitly approved before PersonaPlex, local transcription, and a local reasoner run together.

## 12. Staged rollout

| Stage | Adds | Entry gate | Rollback |
|---|---|---|---|
| M0 walking skeleton | Existing typed fixture routing, proposal, validation, policy, ledger, renderer tests | Current 110-test suite and privacy/integrity tests green | Revert to fixture set |
| M1 live voice loop | PersonaPlex, local capture, Voxtral or consented cloud transcription, Jev | 300-utterance routing benchmark, 30-second stability/reconnect test, consent boundary | Force all routes to unclear and stop live capture |
| M2 durable state | Redis hot state, Postgres event ledger | privacy canary, TTL/deletion, backup/restore, replay | in-memory fixture ledger |
| M3 read-only tools | MAGG runtime plane, fixed catalog, one local read-only MCP tool | capability red-team, schema provenance, output filter | disable tool gateway |
| M4 federated read tools | Context Forge behind MAGG after redeploy | health check, schema hash, no mutation allowlist | remove Context Forge server from kit |
| M5 deterministic execution | Dagger test/lint/build allowlist | GPU/container scheduler, cancellation, timeout, audit | disable Dagger tool definition |
| M6 billable tools | Treg catalog and one low-cost provider | budget, confirmation, cost alert, duplicate-charge tests | disable Treg definition and revoke spend |
| M7 governed memory | Memory Governor and selected platform | provenance, deletion, backup, recall quality, consent | read-only memory or disable platform |

## Architecture Contract

```yaml
contract_version: 2
boundaries:
  - id: trs.voice-edge
    kind: component
    element: voiceEdge
    code: ["src/edge/**", "src/voice_edge/**"]
    exposes: ["src/edge/ports/**"]
    provides: ["audio-session", "turn-epoch"]
    consumes: ["response-render"]
  - id: trs.routing
    kind: component
    element: routing
    code: ["src/talk_reasoner/routing.py", "src/routing/**"]
    modules: ["talk_reasoner.routing"]
    exposes: ["src/talk_reasoner/routing.py", "src/routing/*.py"]
    provides: ["route-decision"]
  - id: trs.reasoning
    kind: component
    element: reasoning
    code: ["src/talk_reasoner/jobs.py", "src/talk_reasoner/transports.py", "src/reasoning/**"]
    modules: ["talk_reasoner.jobs", "talk_reasoner.transports"]
    exposes: ["src/talk_reasoner/jobs.py", "src/talk_reasoner/transports.py", "src/reasoning/*.py"]
    provides: ["reasoner-job", "reasoner-proposal"]
    consumes: ["action-validation"]
  - id: trs.action-governor
    kind: component
    element: actionGovernor
    code: ["src/talk_reasoner/actions.py", "src/governor/**"]
    modules: ["talk_reasoner.actions"]
    exposes: ["src/talk_reasoner/actions.py", "src/governor/*.py"]
    provides: ["action-validation", "action-policy"]
    consumes: ["tool-execution"]
  - id: trs.tool-catalog
    kind: component
    element: toolCatalog
    code: ["config/actions/**", "src/catalog/**"]
    exposes: ["src/catalog/reader.py", "src/catalog/admin.py"]
    provides: ["tool-catalog"]
  - id: trs.tool-gateway
    kind: component
    element: toolGateway
    code: ["src/tool_gateway/**"]
    exposes: ["src/tool_gateway/execute.py", "src/tool_gateway/filter.py"]
    provides: ["tool-execution", "filtered-tool-result"]
  - id: trs.renderer
    kind: component
    element: renderer
    code: ["src/renderer/**", "src/talk_reasoner/rendering.py", "src/talk_reasoner/cli.py", "src/talk_reasoner/__main__.py"]
    exposes: ["src/renderer/present.py"]
    provides: ["response-render"]
  - id: trs.event-ledger
    kind: component
    element: eventLedger
    code: ["src/talk_reasoner/contracts.py", "src/ledger/**"]
    modules: ["talk_reasoner.contracts"]
    exposes: ["src/talk_reasoner/contracts.py", "src/ledger/*.py"]
    provides: ["audit-ledger", "event-integrity"]
  - id: trs.hot-state
    kind: component
    element: hotState
    code: ["src/state/hot/**"]
    exposes: ["src/state/hot/snapshot.py"]
    provides: ["hot-session-state"]
  - id: trs.memory-governor
    kind: component
    element: memoryGovernor
    code: ["src/memory/**"]
    exposes: ["src/memory/governor.py"]
    provides: ["governed-memory"]
  - id: trs.observability
    kind: component
    element: observability
    code: ["src/observability/**"]
    exposes: ["src/observability/metrics.py"]
    provides: ["metrics-and-replay"]
externals:
  - id: external.personaplex
    element: personaplex
    imports: ["talk_reasoner.adapters.personaplex", "edge.adapters.personaplex"]
  - id: external.voxtral
    element: voxtral
    imports: ["talk_reasoner.adapters.voxtral", "edge.adapters.voxtral"]
  - id: external.jev
    element: jev
    imports: ["talk_reasoner.adapters.jev"]
  - id: external.reasoner
    element: reasoner
    imports: ["talk_reasoner.adapters.reasoner"]
  - id: external.magg
    element: magg
    imports: ["tool_gateway.adapters.magg"]
  - id: external.contextforge
    element: contextForge
    imports: ["tool_gateway.adapters.contextforge"]
  - id: external.dagger
    element: dagger
    imports: ["tool_gateway.adapters.dagger"]
  - id: external.treg
    element: treg
    imports: ["tool_gateway.adapters.treg"]
  - id: external.localmcp
    element: localMcp
    imports: ["tool_gateway.adapters.localmcp"]
  - id: external.postgres
    element: postgres
    imports: ["psycopg", "asyncpg", "sqlalchemy"]
  - id: external.redis
    element: redis
    imports: ["redis", "fakeredis"]
  - id: external.memory
    element: memoryPlatform
    imports: ["mem0", "cognee", "graphiti", "letta"]
  - id: external.tts
    element: tts
    imports: ["tool_gateway.adapters.tts", "edge.adapters.tts"]
ignore:
  - ".venv/**"
  - ".claude/**"
  - "tests/**"
  - "docs/**"
  - "design/**"
  - "scripts/**"
  - "src/talk_reasoner/__init__.py"
  - "src/talk_reasoner/machinery.py"
dependency_rules:
  allow:
    - trs.voice-edge -> trs.routing
    - trs.routing -> trs.reasoning
    - trs.voice-edge -> trs.renderer
    - trs.voice-edge -> trs.hot-state
    - trs.voice-edge -> external.personaplex
    - trs.voice-edge -> external.voxtral
    - trs.voice-edge -> external.tts
    - trs.routing -> trs.event-ledger
    - trs.routing -> external.jev
    - trs.reasoning -> trs.action-governor
    - trs.reasoning -> trs.event-ledger
    - trs.reasoning -> external.reasoner
    - trs.action-governor -> trs.tool-catalog
    - trs.action-governor -> trs.tool-gateway
    - trs.action-governor -> trs.event-ledger
    - trs.tool-gateway -> trs.event-ledger
    - trs.tool-gateway -> external.magg
    - trs.tool-gateway -> external.localmcp
    - trs.renderer -> trs.event-ledger
    - trs.event-ledger -> trs.observability
    - trs.event-ledger -> external.postgres
    - trs.hot-state -> external.redis
    - trs.memory-governor -> trs.event-ledger
    - trs.memory-governor -> external.memory
  deny:
    - "trs.* -> external.magg"
    - "trs.* -> external.contextforge"
    - "trs.* -> external.dagger"
    - "trs.* -> external.treg"
    - "trs.* -> external.memory"
    - "trs.voice-edge -> trs.action-governor"
    - "trs.voice-edge -> trs.tool-gateway"
    - "trs.routing -> trs.tool-gateway"
    - "trs.reasoning -> external.memory"
    - "trs.tool-gateway -> external.reasoner"
    - "trs.event-ledger -> trs.*"
  assert:
    - no_path: trs.reasoning -> external.memory
    - no_path: trs.tool-gateway -> trs.reasoning
    - no_path: trs.event-ledger -> trs.action-governor
    - no_path: trs.hot-state -> trs.reasoning
  notes:
    - "The explicit tool-gateway edges override broad deny globs."
    - "MAGG, Context Forge, Dagger, Treg, and memory are deferred and may only be reached through Tool Gateway or Memory Governor."
```
