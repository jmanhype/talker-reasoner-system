# The Whole System: PersonaPlex + Jev + Slow Reasoner + Memory

The system is a **fast/slow voice-agent architecture**:

- **PersonaPlex** is the real-time conversational “talker.”
- **Voxtral Realtime** turns speech into text.
- **Jev** is the ultra-fast calibrated router.
- A **tool-calling reasoner** handles planning, retrieval, APIs, and actions.
- A **separate memory layer** stores durable user/project state.
- A **voice bridge** connects all of these without breaking the low-latency conversation.

The core idea is:

> PersonaPlex keeps talking naturally while Jev decides whether the request is simple enough to stay local or important enough to wake the slower reasoner.

---

## 1. High-Level Architecture

```text
                         ┌──────────────────────┐
                         │        USER          │
                         │   Speaking / Typing  │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │      Audio Bus       │
                         │  PCM / Opus stream   │
                         └──────────┬───────────┘
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
    ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
    │    PersonaPlex    │  │  Voxtral Realtime │  │   State Snapshot  │
    │   Fast Talker     │  │   Transcription   │  │       Redis       │
    │   Full Duplex     │  │  speech → text    │  │  Hot session data │
    └─────────┬─────────┘  └─────────┬─────────┘  └─────────┬─────────┘
              │                      │                      │
              │                      ▼                      │
              │            ┌───────────────────┐            │
              │            │        Jev        │            │
              │            │ Calibrated Router │            │
              │            └─────────┬─────────┘            │
              │                      │                      │
              │        ┌─────────────┼─────────────┐        │
              │        │             │             │        │
              │        ▼             ▼             ▼        │
              │   ┌─────────┐  ┌──────────┐  ┌─────────┐   │
              │   │ Chitchat│  │  Tools / │  │ Unclear │   │
              │   │  only   │  │ Reasoning│  │ / Risky │   │
              │   └────┬────┘  └────┬─────┘  └────┬────┘   │
              │        │            │             │        │
              ▼        │            ▼             │        ▼
        ┌────────────┐ │  ┌────────────────────┐  │  ┌────────────────┐
        │ PersonaPlex│ │  │  Tool Reasoner     │  │  │ Reasoner or    │
        │ speaks now │ │  │  - planning        │  │  │ clarification  │
        └────────────┘ │  │  - search          │  │  └────────────────┘
                       │  │  - APIs            │  │
                       │  │  - code execution  │  │
                       │  └─────────┬──────────┘  │
                       │            │             │
                       │            ▼             │
                       │  ┌────────────────────┐  │
                       │  │  Result + Update   │  │
                       │  │  - answer          │  │
                       │  │  - state changes   │  │
                       │  │  - memory writes   │  │
                       │  └─────────┬──────────┘  │
                       │            │             │
                       └────────────┴─────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Response Renderer  │
                         │  TTS or PersonaPlex  │
                         │  context injection   │
                         └──────────────────────┘
```

---

## 2. Layer-by-Layer Responsibilities

### Layer 1: User Audio

The user speaks naturally. They can interrupt, pause, backchannel, or change topics.

The system receives:

- microphone audio,
- optional typed input,
- session identifiers,
- device metadata,
- timing information.

The audio stream is fanned out to two paths:

1. PersonaPlex, for immediate conversation.
2. Voxtral Realtime, for transcription and routing.

---

### Layer 2: PersonaPlex — Fast Talker / System 1

PersonaPlex is the real-time conversational layer.

It is responsible for:

- full-duplex speech interaction,
- natural turn-taking,
- backchannel behavior,
- interruptions,
- low-latency responses,
- maintaining persona and voice,
- handling simple conversational replies.

It is **not** responsible for:

- durable memory,
- tool calls,
- planning,
- complex retrieval,
- reliable multi-step reasoning.

In this design, PersonaPlex is the voice and personality, not the brain.

#### PersonaPlex inputs

```text
live user audio
voice prompt
persona / role prompt
small hot-state snapshot
```

#### PersonaPlex outputs

```text
streamed speech audio
streamed text / inner-monologue tokens
turn-taking signals
```

The hot-state snapshot must be small. PersonaPlex should not query Postgres, Mem0, or a graph database synchronously.

---

### Layer 3: Voxtral Realtime — Transcription

Voxtral Realtime converts live speech into text.

It is not the main tool-calling layer in this design.

Its job is:

```text
audio stream → streaming transcript
```

That transcript is then passed to Jev.

This distinction matters:

- **Voxtral Realtime** is optimized for live transcription.
- **Voxtral Small** can emit native function calls from audio, but it is not the full slow reasoner in this architecture.
- The old VAOS gist also used Voxtral mainly for transcription/classification, while Letta performed actual tool calls.

---

### Layer 4: Jev — Calibrated Router / System 1.5

Jev sits between the fast talker and the slow reasoner.

It receives:

```text
transcript
recent conversation context
session state
optional user metadata
routing policy
```

It returns calibrated probabilities and routing decisions.

For the first prototype, keep the label set small:

```text
chitchat
needs_tools
unclear
```

Later, expand to labels such as:

```text
smalltalk
schedule_task
search_question
booking
memory_recall
unsafe
handoff
clarification_needed
```

#### Jev output example

```json
{
  "labels": {
    "chitchat": 0.02,
    "needs_tools": 0.96,
    "unclear": 0.02
  },
  "selected_label": "needs_tools",
  "confidence": 0.96,
  "route": "reasoner",
  "risk": "low"
}
```

Jev does not execute tools. It decides whether the reasoner should be invoked.

---

## 5. Routing Logic

The first version should use simple, explicit thresholds.

```python
if jev.selected_label == "chitchat" and jev.confidence >= 0.90:
    route = "personaplex_only"

elif jev.selected_label == "needs_tools" and jev.confidence >= 0.80:
    route = "reasoner"

elif jev.confidence < 0.60:
    route = "clarify"

elif jev.risk == "unsafe":
    route = "guardrail"

else:
    route = "reasoner"
```

The routing policy should be configurable, not hardcoded throughout the code.

### Fast path

```text
user says: “Hey, how’s it going?”
Jev says: chitchat, confidence 0.98
PersonaPlex answers alone
reasoner stays asleep
```

### Slow path

```text
user says: “Check my calendar and book the first free afternoon slot.”
Jev says: needs_tools, confidence 0.97
reasoner wakes up
reasoner calls calendar tools
reasoner writes state update
```

### Clarification path

```text
user says: “Can you handle that thing from yesterday?”
Jev says: unclear, confidence 0.42
system asks a clarifying question
```

---

# 6. Slow Reasoner — System 2

The slow reasoner is a normal tool-calling LLM or agent runtime.

For the first version, use a direct tool-calling LLM rather than Letta.

It receives:

```text
user transcript
Jev routing result
small recent-conversation window
retrieved memories
current state
available tools
safety policy
```

It returns a structured action package:

```json
{
  "user_message": "I booked Thursday at 2pm and sent the confirmation to Slack.",
  "tool_calls": [
    {
      "name": "search_calendar",
      "arguments": {
        "days_ahead": 7,
        "preferred_time": "afternoon"
      }
    },
    {
      "name": "create_booking",
      "arguments": {
        "time": "2026-09-24T14:00:00",
        "duration_minutes": 30
      }
    }
  ],
  "state_updates": [
    {
      "key": "last_booking",
      "value": "2026-09-24T14:00:00"
    }
  ],
  "memory_writes": [
    {
      "type": "fact",
      "content": "User prefers afternoon meetings.",
      "source": "user utterance"
    }
  ],
  "confidence": 0.91
}
```

The reasoner is responsible for:

- planning,
- decomposition,
- tool calls,
- search,
- APIs,
- code execution if needed,
- deciding when information is missing,
- producing a final user-facing result.

The voice bridge, not the reasoner, decides exactly how the result is spoken or injected.

---

# 7. Tool Layer

Tools should be small, typed, and auditable.

Initial tools:

```text
search
read_state
write_state
```

Later tools:

```text
calendar_search
calendar_create
email_send
slack_send
crm_lookup
database_query
code_run
web_fetch
```

Every tool call should log:

```text
tool name
input arguments
output
latency
cost
caller/session
success/failure
reason for call
```

Tools should never receive secrets directly. Credentials stay in a server-side tool executor.

---

# 8. Memory Architecture

The recommended memory design separates hot state, durable events, and semantic recall.

```text
Redis
  hot session state

Postgres
  raw events, tool calls, audit log, durable structured state

Mem0
  semantic long-term memory and user preferences
```

Optional alternatives:

```text
Cognee
  self-hosted graph memory

Zep / Graphiti
  temporal knowledge graph with provenance

Letta
  full stateful-agent runtime
```

## Redis: Hot Session State

Redis stores only what the live loop needs:

```json
{
  "session_id": "voice_123",
  "user_id": "user_42",
  "active_persona": "assistant",
  "last_user_utterance": "Book the first afternoon slot.",
  "last_route": "reasoner",
  "pending_reasoner_job": "job_777",
  "hot_preferences": [
    "User dislikes phone calls.",
    "User prefers concise answers."
  ]
}
```

This is what PersonaPlex or the response renderer can read quickly.

---

## Postgres: Source of Truth

Postgres stores immutable events:

```text
sessions
utterances
transcripts
routing_decisions
reasoner_runs
tool_calls
tool_results
state_updates
memory_writes
errors
latency_metrics
```

This gives you:

- auditing,
- debugging,
- replay,
- evaluation,
- compliance,
- recovery,
- provenance.

Do not make Mem0 or Cognee the only copy of important data.

---

## Mem0: Long-Term Semantic Memory

Mem0 stores user preferences and durable facts.

Example memory search output:

```json
{
  "memories": [
    {
      "id": "memory_123",
      "text": "User prefers afternoon meetings.",
      "score": 0.91
    },
    {
      "id": "memory_456",
      "text": "User wants confirmations through Slack.",
      "score": 0.88
    }
  ]
}
```

The reasoner consumes those memories and decides what to do.

Mem0 is not a tool executor and does not generate the final voice answer.

---

## Optional Cognee Instead of Mem0

Use Cognee if you want a self-hosted graph-based memory layer.

Cognee outputs structured context:

```json
{
  "context": [
    {
      "type": "entity",
      "name": "User 42"
    },
    {
      "type": "fact",
      "subject": "User 42",
      "relationship": "prefers",
      "object": "afternoon meetings"
    },
    {
      "type": "source",
      "text": "I prefer afternoons unless it is urgent.",
      "origin": "session_2026_09_18"
    }
  ]
}
```

Cognee is attractive if the system needs:

- self-hosting,
- entity relationships,
- project/company knowledge,
- document ingestion,
- provenance,
- graph retrieval.

The tradeoff is operational complexity.

---

## Optional Letta

Letta is useful if you want the reasoner itself to be a persistent agent with:

- memory blocks,
- archival memory,
- self-editing context,
- long-running identity,
- tool orchestration.

But in this architecture, Letta is optional.

If you use Letta, it replaces the direct reasoner plus some of the memory orchestration:

```text
Jev → Letta agent → tools → memory updates
```

If you do not use Letta:

```text
Jev → normal LLM reasoner → tools → memory service
```

For the first build, the second option is easier to debug.

---

# 9. Response Rendering

The slow reasoner’s result can be returned to the user in two ways.

## Option A: Clean TTS

The safest first version is:

```text
reasoner answer → TTS → user
```

This avoids fighting PersonaPlex’s model internals.

The system can still have PersonaPlex say a short filler while waiting:

```text
“Let me check that for you.”
```

Then the clean TTS result plays.

## Option B: PersonaPlex Context Injection

The more advanced version updates PersonaPlex’s context or inner-monologue stream.

Your previous VAOS work showed the danger:

- putting the answer in `text_prompt` does not reliably make PersonaPlex relay it,
- burst injection can degenerate,
- drip-feed token injection worked better,
- audio streams can collide,
- a server-side audio gate was needed.

So for the prototype:

```text
start with clean TTS
```

Then reintroduce PersonaPlex injection after routing and tool behavior are stable.

---

# 10. Voice Bridge

The voice bridge is the orchestration layer.

It handles:

- audio transport,
- session lifecycle,
- Voxtral streaming,
- Jev calls,
- routing,
- reasoner jobs,
- tool execution,
- state updates,
- memory writes,
- response playback,
- interruption handling,
- logging.

Conceptual components:

```text
AudioGateway
TranscriptionWorker
RoutingWorker
ReasonerWorker
ToolExecutor
MemoryService
StateStore
ResponseRenderer
EventLogger
PolicyGuardrail
```

The bridge must keep the live audio loop independent from slow reasoning.

That means reasoner work should be asynchronous:

```text
PersonaPlex continues speaking
reasoner runs in background
result arrives later
response is queued
interruption cancels or downgrades stale jobs
```

---

# 11. Safety and Policy

Every utterance should pass through a policy layer.

This includes:

- unsafe requests,
- identity handling,
- payments,
- destructive actions,
- external messages,
- private-data disclosure,
- tool permission checks.

High-risk tools should require explicit confirmation:

```text
send_email
book_meeting
make_payment
delete_record
run_code
```

Example:

```text
User: Send that to my client.
System: Should I send the summary to Alex?
User: Yes.
Tool executes.
```

---

# 12. Observability

Every turn should produce a trace:

```json
{
  "session_id": "voice_123",
  "utterance_id": "utt_456",
  "transcript": "Book the first afternoon slot.",
  "jev_result": {
    "label": "needs_tools",
    "confidence": 0.96
  },
  "route": "reasoner",
  "memory_hits": 3,
  "reasoner_latency_ms": 1800,
  "tool_calls": 2,
  "response_channel": "tts",
  "user_interrupted": false
}
```

Core metrics:

```text
transcription latency
Jev latency
routing accuracy
false reasoner wakeups
reasoner latency
tool success rate
memory precision
response latency
interruption rate
cost per session
```

---

# 13. Build Sequence

Do not build everything at once.

## Phase 1: Fast Loop Only

```text
PersonaPlex live voice conversation
```

Measure:

- latency,
- turn-taking,
- interruption,
- stability.

## Phase 2: Add Voxtral + Jev

```text
audio → Voxtral → Jev → route decision
```

Start with:

```text
chitchat
needs_tools
unclear
```

Build a labeled evaluation set.

## Phase 3: Add Reasoner

```text
needs_tools → tool-calling LLM → search tool → state write
```

Start with one or two tools only.

## Phase 4: Add Redis + Postgres

```text
Redis hot context
Postgres event log
```

Do this before adding a fancy memory product.

## Phase 5: Add Mem0 or Cognee

Add semantic memory only after the routing and reasoner paths are stable.

## Phase 6: Improve Response Integration

After the baseline works:

- PersonaPlex context updates,
- drip-feed injection,
- audio gating,
- richer interruption logic.

## Phase 7: Offline Optimization

Only after you have evaluation data, consider Cognify to tune:

- prompts,
- model choices,
- routing thresholds,
- cost/latency/quality tradeoffs.

---

# 14. What Makes This System Valuable

The key value is economic and experiential:

- PersonaPlex keeps the conversation feeling alive.
- Jev avoids waking an expensive reasoner for every utterance.
- The reasoner handles only hard or action-oriented work.
- Memory preserves continuity across sessions.
- Postgres provides auditability.
- Redis preserves low latency.
- Tool calls are explicit and safe.

In short:

```text
PersonaPlex gives presence.
Jev gives cheap judgment.
The reasoner gives capability.
Memory gives continuity.
The bridge gives control.
```

---

# 15. Main Risks

1. **Routing errors**  
   Jev may wake the reasoner too often or too rarely.

2. **Latency creep**  
   Transcription, memory retrieval, and reasoning can stack up.

3. **Audio integration complexity**  
   PersonaPlex injection and TTS collision are nontrivial.

4. **Tool correctness**  
   The reasoner may choose the wrong tool or arguments.

5. **Memory pollution**  
   Bad facts can persist if writes are not governed.

6. **Overengineering**  
   Starting with Letta, Cognee, Zep, and Mem0 together would make debugging nearly impossible.

---

# Final Recommended MVP

```text
PersonaPlex
Voxtral Realtime
Jev with 3 labels
direct tool-calling reasoner
one search tool
Redis hot state
Postgres event log
clean TTS response path
```

Do not add yet:

```text
Letta
Cognee
Zep/Graphiti
Cognify
many tools
graph memory
complex multi-agent planning
```

That thin version answers the central question:

> Can a calibrated router reliably separate conversational speech from reasoning-and-tool speech without destroying the realtime voice experience?

If yes, the system is worth expanding.