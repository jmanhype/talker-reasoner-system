# Design decisions

- 2026-09-19 operator: build a staged hybrid system, not an all-at-once integration. The first slice is local and deterministic; live voice, durable stores, MCP aggregation, Dagger, and Treg require later explicit gates.
- 2026-09-19 operator: target a TypeScript voice/audio edge and a Python model, policy, reasoner, and tool core. Bun is packaging choice, not a system-wide invariant.
- 2026-09-19 operator: initial deployment is a single-operator Mac plus RTX 3090 prototype. Multi-user production is deferred.
- 2026-09-19 operator: raw audio and raw transcripts are processing-only and ephemeral by default. Persist hashed, minimized, classified metadata. Retain redacted transcripts only with explicit consent, encryption, TTL, deletion, and backup tests.
- 2026-09-19 operator: use in-memory fixture state first. Redis hot state and Postgres append-only events enter only after the local contract, routing, policy, privacy, and replay gates pass.
- 2026-09-19 operator: defer Mem0, Cognee, Zep/Graphiti, and Letta. No memory platform may become the sole copy of important state.
- 2026-09-19 operator: external tools begin as read-only discovery plus exactly one allowlisted, cheap, preferably local, non-billable tool. Treg, Context Forge mutation tools, Dagger execution, messaging, payments, and database mutation are deferred.
- 2026-09-19 operator: MAGG must expose separate admin and runtime planes. The voice reasoner may list, inspect, status-check, and proxy allowlisted tools; it may never add, remove, reload, or reconfigure MCP servers.
- 2026-09-19 operator: PersonaPlex/Moshi is the talker, Voxtral Realtime is transcription, Jev is routing, and a direct reasoner proposes actions. None of these owns execution authority.
- 2026-09-19 operator: hosted Voxtral is not local processing. Any cloud transcription requires explicit data-boundary disclosure and consent.
- 2026-09-19 operator: enable the machinery design substrate for this repository and require modelith and machinery gates before architecture handoff.

