# Talker-Reasoner System

Separate Paivot-governed project for the operator’s fifth-source architecture:
PersonaPlex/Moshi as the real-time talker, Voxtral Realtime for transcription,
Jev as the calibrated router, a direct tool-calling reasoner for System 2, and
staged hot state / durable events / semantic memory.

This project is intentionally independent from `wangp-dspy`. It must not treat
PersonaPlex or Moshi as a native tool-calling model, must not confuse Voxtral
Realtime with Voxtral Small, and must not enable durable memory platforms in
the first vertical slice.

## Source of record

- Operator synthesis: `docs/sources/whole-system-2026-09-19.md`
- Canonical C4 and machinery architecture: `design/ARCHITECTURE.md`
- Original research session: Codex thread
  `01a0b607-e9df-7d90-8a3e-3193b5d35b32`
- Public VAOS precursor gist:
  <https://gist.github.com/jmanhype/5aefd67d9e67b37a8b408abdab39b6d3>

## First slice

Typed transcript fixtures → three-label calibrated routing
(`chitchat`, `needs_tools`, `unclear`) → fixed action validation → one direct
tool-calling reasoner → append-only hash-scoped events. Live voice, external
inference, Redis, Postgres, Mem0, Cognee, Zep, and Letta require later explicit
stories and consent.
