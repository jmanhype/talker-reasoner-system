---
id: TRS-pf94
title: "Whole-system Talker-Reasoner MVP"
status: open
priority: 1
type: epic
created_at: 2026-09-19T04:41:13Z
created_by: speed
updated_at: 2026-09-19T04:41:13Z
content_hash: "sha256:9f26ae395023d532866d9534cd0ba94af595b6066ac4230abf014d643a9efd86"
---

## Description
## Description
Build the operator’s fifth-source fast/slow voice-agent system as a project
independent from wangp-dspy: PersonaPlex/Moshi talker, Voxtral Realtime
transcription, Jev calibrated routing, direct tool-calling reasoner, staged
hot state and durable events, and deferred semantic memory.

## Epic Outcomes
- A typed, testable first slice routes transcript fixtures without live voice,
  external inference, credentials, or durable memory services.
- The talker never receives tool schemas or execution authority.
- The reasoner proposes validated, allowlisted actions but never executes them
  directly.
- Every routing/action decision is measured and recorded through a hash-scoped
  append-only event contract.
- Later Redis, Postgres, Mem0, Cognee, Zep, and Letta adoption requires explicit
  measured gates and privacy/retention review.

## OUT OF SCOPE
- Treating PersonaPlex/Moshi as a native tool-calling model.
- Confusing Voxtral Realtime with Voxtral Small.
- Enabling all memory systems in the first slice.
- Unconsented network inference or raw prompt/audio persistence.

## Acceptance Criteria
1. Discovery/design documents define the first vertical slice and boundaries.
2. Follow-up stories are individually testable and dependency-ordered.
3. The first implementation uses local typed fixtures and no live endpoint.

## Design
Source of record: docs/sources/whole-system-2026-09-19.md.

## Skills To Use
- `pvg` for backlog and story governance.

## nd_contract
status: new

### evidence
- Project initialized at /Users/Shared/HermesWorkspace/talker-reasoner-system.
- Source document SHA-256:
  c25adac0139b5aeeff6e16cdafddf1af0675785988688b6936250236edf18ec3.

### proof
- [ ] Pending discovery/design and derived backlog.

## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments
