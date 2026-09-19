---
id: TRS-pf94
title: "Whole-system Talker-Reasoner MVP"
status: closed
priority: 1
type: epic
created_at: 2026-09-19T04:41:13Z
created_by: speed
updated_at: 2026-09-19T18:01:36Z
content_hash: "sha256:11eb8d51675fa682d04a21b85221d1510984f5da7583e055aa6235d46ed3020a"
closed_at: 2026-09-19T18:01:36Z
close_reason: "All stories accepted"
labels: [accepted]
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
- 2026-09-19T18:01:36Z status: open -> closed

## Links


## Comments
