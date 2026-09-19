---
id: TRS-h031
title: "Machinery M0 oracle walking skeleton"
status: closed
priority: 1
type: epic
created_at: 2026-09-19T18:16:57Z
created_by: speed
updated_at: 2026-09-19T19:31:09Z
content_hash: "sha256:fc7db0f83927ca138aa7e56e9e94582dc1b89bff6b8fcaf5682bd14064cb4987"
closed_at: 2026-09-19T19:31:08Z
close_reason: "All M0 stories accepted; offline machinery and capstone gates are green."
labels: [accepted]
---

## Description
## Description

Milestone M0 from `design/BUILD.md`: prove that the committed machinery design governs the existing offline Python contracts before any live voice, durable store, MCP, Dagger, Treg, or memory platform is enabled.

## Epic Outcomes

- All seven committed transition oracles are parsed as the authoritative test specification.
- Every one of the 62 stable oracle ids is exercised by a passing parser-driven test.
- Every one of the 36 Modelith invariant ids has an explicit property or contract test.
- The existing local Slice 0 behavior remains intact and offline.
- `modelith`, `machinery`, and the complete Python suite are green together.

## OUT OF SCOPE

- Live audio or PersonaPlex runtime.
- Hosted or local Voxtral, Jev network inference, or external reasoner calls.
- Redis, PostgreSQL, Mem0, Cognee, Zep, Graphiti, or Letta.
- MAGG, Context Forge, Dagger, Treg, local MCP execution, or tool dispatch.
- TypeScript edge implementation and architecture/package extraction.
- Any credential, network call, raw prompt persistence, or semantic memory write.

## Acceptance Requirements

1. The M0 walking-skeleton story delivers parser-driven oracle and invariant coverage.
2. The M0 E2e capstone runs the complete offline gate with exact denominators.
3. No M0 story enables a live or durable dependency.

## Design

- Source design: `design/BUILD.md` section 9, milestone M0.
- Domain source: `design/domain.modelith.yaml`.
- Machines and oracles: `design/machines/*.machine.json` and `design/machines/*.oracle.md`.
- Architecture source: `design/ARCHITECTURE.md`.

## MANDATORY SKILLS

- `pvg` for story governance.
- `machinery` and `modelith` gates where required.

## nd_contract

status: new

### evidence

- Created from committed architecture commit `630386c` and machinery design.
- Design gate at creation: `machinery check design` reported 0 blocking findings.

### proof

- [ ] AC #1: M0 walking-skeleton story delivered and accepted.
- [ ] AC #2: M0 E2e capstone delivered and accepted.
- [ ] AC #3: No live or durable dependency is imported or enabled.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T19:31:09Z status: open -> closed

## Links


## Comments
