---
type: decision
scope: system
project: talker-reasoner-system
status: active
created: 2026-09-19
---

# Staged Hybrid Talker Reasoner Architecture

## Context
The system must combine PersonaPlex, Voxtral Realtime, Jev, a direct reasoner, governed tools, memory, and audit without treating historical integration notes or installed tools as authorization.

## Decision
Use a staged hybrid architecture: deterministic local contracts first, then one live operator voice loop, minimized Redis/Postgres state, read-only MAGG/tool discovery, one local allowlisted tool, then deferred Context Forge, Dagger, Treg, and governed memory. Keep model, routing, validation, policy, execution, rendering, state, and memory boundaries separate.

## Alternatives
An all-at-once integration was rejected because MAGG scopes are informational, Context Forge is not currently reachable, Dagger executes containers, Treg spends money, and historical gists do not prove current operability. A permanent fixture-only system was rejected because it cannot meet the target voice-agent outcome.

## Trade-offs
The staged path delays capability but preserves privacy, auditability, policy control, rollback, and diagnosability. Canonical artifacts live in design/.
