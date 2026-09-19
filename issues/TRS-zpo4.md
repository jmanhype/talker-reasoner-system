---
id: TRS-zpo4
title: "Run D&F for the whole-system Talker-Reasoner MVP"
status: in_progress
priority: 1
type: task
parent: TRS-pf94
created_at: 2026-09-19T04:41:13Z
created_by: speed
updated_at: 2026-09-19T04:42:09Z
content_hash: "sha256:c4b09234df6cb96ef2b9daddd20640dcc0711e672a5bee0aef3f8119d9108358"
assignee: dev-TRS-zpo4
---

## Description
## Context (Embedded)

This is a new project, not a wangp-dspy story. The operator’s fifth source is
the authoritative initial architecture:

- PersonaPlex/Moshi is the low-latency full-duplex talker.
- Voxtral Realtime transcribes speech.
- Jev provides calibrated three-label routing: chitchat, needs_tools, unclear.
- A direct tool-calling reasoner handles System-2 work.
- A response renderer returns clean speech first; PersonaPlex context injection
  is deferred because prior VAOS work exposed text_prompt, burst-injection, and
  audio-collision failures.
- Hot state, durable events, and semantic memory are staged, not all enabled at
  once.

Source: docs/sources/whole-system-2026-09-19.md.

## USER INTENT

Turn the fifth-source architecture into an executable project plan without
starting with the full production stack.

## Goal

Create docs/BUSINESS.md, docs/DESIGN.md, and docs/ARCHITECTURE.md for Paivot
Discovery & Framing. These documents must support a later adversarial backlog
review and decomposition into implementation stories.

## Required Content

1. Define the thin MVP: typed transcript fixtures, calibrated three-route
   classifier, fixed action validator, one direct reasoner, local append-only
   event ledger, and clean response-renderer boundary.
2. Define target-state components and explicit Phase 1 deferrals: live audio,
   PersonaPlex, Voxtral, Jev network inference, Redis, Postgres, Mem0, Cognee,
   Zep, Letta, and multi-tool execution.
3. Preserve model boundaries:
   - PersonaPlex/Moshi is not a native tool-calling model.
   - Voxtral Small may emit structured tool_calls but does not execute tools.
   - Voxtral Realtime is transcription-oriented.
   - Jev routes; it does not execute tools.
4. Define privacy and provenance: raw prompts/audio are ephemeral by default;
   persistent records use hashes, lengths, media types, consent, tool names,
   statuses, latency, and rejection reason.
5. Define asynchronous slow-path behavior: the talker loop continues, stale jobs
   can be canceled/downgraded, and results pass through the response renderer.
6. Define policy preflight and confirmation for future high-risk tools.
7. Define rollout/kill metrics for routing accuracy, false wakeups, latency,
   validation correctness, privacy, tool success, and response latency.

## OUT OF SCOPE

- Python implementation.
- Credentials or live external calls.
- Durable memory service setup.
- Editing wangp-dspy or its Worktree WD-dd81.
- Publishing the secret Jev gist contents.

## DIFF BUDGET

- ~4 files, under 600 changed LOC.

## Boundary Map

PRODUCES:
- docs/BUSINESS.md -> project intent, users, value, risks, and success hierarchy
- docs/DESIGN.md -> staged user/system experience and interface boundaries
- docs/ARCHITECTURE.md -> components, contracts, security/privacy, and metrics

CONSUMES:
- docs/sources/whole-system-2026-09-19.md -> authoritative fifth-source
  architecture and build sequence

## Acceptance Criteria

1. All three D&F documents exist and are self-contained.
2. They define a thin local-fixture first slice and explicitly defer live voice,
   external inference, and memory platforms.
3. They preserve the four model-boundary facts listed above.
4. They define asynchronous slow-path, response-rendering, policy, privacy, and
   provenance behavior.
5. They contain measurable rollout/kill criteria suitable for story ACs.
6. `git diff --check` passes.

## Testing Requirements

- Docs-only story: no placeholder unit tests.
- Verification: `git diff --check`.
- PM review must compare every model-boundary claim against the source document.

## Skills To Use

- `pvg` for story governance.

## Delivery Requirements

- Paste git diff --check output.
- Include an AC verification table.
- Record hashes for the three D&F documents.

## nd_contract
status: new

### evidence
- Created from the fifth operator-provided source after project separation.

### proof
- [ ] Pending implementation

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T04:42:09Z status: open -> in_progress
- 2026-09-19T04:42:09Z claimed by dev-TRS-zpo4

## Links
- Parent: [[TRS-pf94]]

## Comments
