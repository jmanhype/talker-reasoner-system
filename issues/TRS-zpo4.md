---
id: TRS-zpo4
title: "Run D&F for the whole-system Talker-Reasoner MVP"
status: closed
priority: 1
type: task
parent: TRS-pf94
created_at: 2026-09-19T04:41:13Z
created_by: speed
updated_at: 2026-09-19T04:59:53Z
content_hash: "sha256:3b8e6b2d39079472cfaf7eeb9989fbe68cbb2013d3ee1dc0901f106204ddadea"
assignee: dev-TRS-zpo4
labels: [delivered]
closed_at: 2026-09-19T04:59:53Z
close_reason: "Accepted: independently reran git diff --check, hash and line-count verification, required boundary/deferral scans, and secret-pattern scan. The three D&F documents are self-contained, preserve the four model-boundary facts, define async/policy/privacy/provenance behavior, and provide measurable gates."
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
## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/talker-reasoner-system
git diff --check
sha256sum docs/BUSINESS.md docs/DESIGN.md docs/ARCHITECTURE.md docs/sources/whole-system-2026-09-19.md
wc -l docs/BUSINESS.md docs/DESIGN.md docs/ARCHITECTURE.md
rg -n 'PersonaPlex/Moshi is not a native tool-calling|Voxtral Small|Voxtral Realtime|Jev routes|chitchat|needs_tools|unclear|Redis|Postgres|Mem0|Cognee|Zep|Letta' docs/BUSINESS.md docs/DESIGN.md docs/ARCHITECTURE.md
rg -n 'API_KEY|SECRET|TOKEN|PASSWORD' docs/BUSINESS.md docs/DESIGN.md docs/ARCHITECTURE.md
```

Independent coordinator rerun summary:

- `git diff --check`: no output, exit 0.
- D&F line count: 177 + 201 + 221 = 599, within budget.
- Required model-boundary and staged-deferral terms were present.
- Secret-pattern scan produced no matches.

### CI/Test Results

```text
git diff --check: PASS (exit 0, no output)
docs-only change: 3 files, 599 insertions
secret-pattern scan: no matches
```

Summary: created self-contained Business, Design, and Architecture D&F documents for the independent whole-system Talker-Reasoner project, preserving model boundaries and defining a thin local-fixture first slice with deferred live voice/inference/memory services, async slow path, clean response rendering, policy, privacy, provenance, and measurable rollout/kill criteria.

Commit SHA: 265bc9692ad93de6dc79675833eae5a16f479701da8dcb2812d75e8eb449304c

This is the SHA-256 of the docs delivery manifest, not a Git commit; the new project has not yet been authorized for an initial commit.

Final hashes:

```text
969b731070513a1b601b3edbbb7ccfd27a2c378e9fe3c2021df4409d5d41cb6f  docs/BUSINESS.md
a57c059fbf19900782e261b5929a77e920139fba540d4ea2f02d5a90eac0ce17  docs/DESIGN.md
8fe2a97d9794db881e96d6a75dfcfbbefbe5b85da8c7f0426bb7673d32121c38  docs/ARCHITECTURE.md
c25adac0139b5aeeff6e16cdafddf1af0675785988688b6936250236edf18ec3  docs/sources/whole-system-2026-09-19.md
```

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Three self-contained D&F documents exist | PASS | Files and SHA-256 hashes above. |
| 2. Thin local-fixture first slice; live/external/memory deferred | PASS | BUSINESS §4, DESIGN §3–4, ARCHITECTURE §1/§10; independent term scan. |
| 3. Four model-boundary facts preserved | PASS | BUSINESS §2, DESIGN §3, ARCHITECTURE §2. |
| 4. Async slow path, rendering, policy, privacy, provenance defined | PASS | DESIGN §6–9, ARCHITECTURE §7–9. |
| 5. Measurable rollout/kill criteria suitable for story ACs | PASS | BUSINESS §7, ARCHITECTURE §11. |
| 6. `git diff --check` passes | PASS | Independent rerun exit 0 with no output. |


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-18.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-19T04:42:09Z status: open -> in_progress
- 2026-09-19T04:42:09Z claimed by dev-TRS-zpo4
- 2026-09-19T04:42:09Z status: in_progress -> open
- 2026-09-19T04:42:15Z status: open -> in_progress
- 2026-09-19T04:42:15Z claimed by dev-TRS-zpo4
- 2026-09-19T04:59:03Z status: in_progress -> in_progress
- 2026-09-19T04:59:53Z status: in_progress -> closed

## Links
- Parent: [[TRS-pf94]]

## Comments

### 2026-09-19T04:42:09Z speed
loop: reset orphaned in_progress to open (no developer worktree found; prior session presumed dead)
