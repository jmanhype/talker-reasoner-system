# Experience and Interface Design — Talker-Reasoner System MVP

Status: Discovery & Framing draft for story `TRS-zpo4`
Primary sources: story requirements and
`docs/sources/whole-system-2026-09-19.md`

This document describes the first local fixture slice and staged target voice
experience; it does not authorize live audio, external inference, credentials,
or memory services.

## 1. Experience principles

1. One coherent voice at a time; never overlap PersonaPlex, TTS, or tool output.
2. The fast loop continues while the reasoner works.
3. Uncertainty produces clarification or rejection, never silent guessing.
4. High-risk actions require policy preflight and scoped confirmation.
5. Users receive clean answers; schemas and tool errors remain operator-facing.
6. Stale jobs are canceled or downgraded, never emitted as normal output.
7. Raw prompt/audio is ephemeral; provenance is structured metadata.

## 2. Personas and critical journeys

### Speaker journeys

| Journey | Experience |
| --- | --- |
| Fast | `chitchat` renders an immediate short reply; the reasoner stays asleep. |
| Slow work | `needs_tools` permits one short filler, then starts an async job. Validation and policy run before a clean terminal response. |
| Confirmation | A high-risk proposal asks one exact yes/no question and waits for scoped affirmative consent. |
| Unclear | The system asks one useful clarification and invokes no tools. |
| Stale/interrupted | The user may keep talking or cancel; the old job is canceled or downgraded and cannot interrupt as a normal result. |

Every terminal state records route, lifecycle, policy, provenance, response, and
latency evidence.

### Operator / evaluator

Wants deterministic local proof before spending on live infrastructure.
The operator selects a versioned fixture set, runs the local
routing/action/event/render pipeline, compares expected and actual outcomes,
verifies event/privacy fields, and reviews a metric report with explicit
pass/kill decisions.

### Privacy reviewer

Wants to prove minimization and consent without reading raw content.

The reviewer inspects the fixed schema, confirms only approved metadata is
persistent, and traces confirmed action through route, proposal, validation,
policy, and response events.

## 3. Interface stages

Stages are Slice 0 fixtures/clean text, PersonaPlex voice, Voxtral Realtime plus
Jev routing, one reasoner plus clean TTS, durable events, then one governed
memory platform; each later stage needs consent, privacy review, and a gate.

PersonaPlex context injection remains later; Slice 0 uses clean rendering. The
talker is not a tool-caller, Voxtral Small proposals do not execute, Voxtral
Realtime transcribes, and Jev routes.

## 4. Slice-0 fixture interface

Fixtures are versioned records, not ad hoc strings. Each identifies:

fixture/schema IDs, session/turn IDs, routing/reasoner/high-risk consent flags,
in-memory transcript, bounded context/state, expected route/validation/terminal
state, optional timing or interruption instruction, provenance, and test purpose.

Fixture text must not contain credentials, live personal data, or secret gist
content; the evaluator never copies raw text to the ledger.

### Example conceptual shape

```json
{"schema_version":"1","fixture_id":"needs_tools_afternoon_state",
 "session_id":"fixture-session-01","turn_id":"turn-007",
 "consent":{"routing":true,"reasoner":true,"high_risk_action":false},
 "transcript":"Save a preference for afternoon meetings.",
 "expected":{"route":"needs_tools","validation":"accepted","terminal_state":"rendered"}}
```

Serialization language is an implementation decision; schema stability, typed
validation, and expected outcomes are mandatory.

## 5. Routing experience contract

The first interface exposes exactly three routes.

| Route | User experience | Reasoner behavior | Tools |
| --- | --- | --- | --- |
| `chitchat` | Immediate short conversational reply | Not invoked | None |
| `needs_tools` | Short optional filler, then clean terminal response | One async reasoner job | Proposals validated; no direct execution |
| `unclear` | One actionable clarification | Not invoked until clarified | None |

Calibration is part of the interface. Router output includes all three
probabilities, selected label, confidence, policy version, and decision
thresholds. A low-confidence work guess is not silently upgraded to execution;
it becomes `unclear` or a guarded clarification.

## 6. Slow-path and interruption experience

The fast path continues while a slow job runs. The user may speak, backchannel,
change topic, or explicitly cancel.

### User-visible behavior

- **Pending/running:** at most one short filler; no repeated progress chatter.
- **Waiting for confirmation:** one precise question, exact target and effect,
  and a safe negative path.
- **Completed:** one clean result, ordered by user relevance.
- **Canceled:** no late interruption; optionally a terse status only if the
  user asks.
- **Downgraded:** render a bounded non-action result or offer to resume when
  current conversation state permits.
- **Failed:** honest, non-technical failure message and one safe recovery
  action; never fabricate tool output.

Internal states are `pending`, `running`, `waiting_confirmation`, `completed`,
`canceled`, `downgraded`, and `failed`. A job is stale on turn-epoch mismatch,
scoped TTL expiry (`30 seconds` default), explicit cancellation, or material
intent change; stale output cannot enter the renderer as a normal result.

## 7. Policy and confirmation experience

Policy preflight runs before execution and before a consequential confirmation.
High-risk categories include external messaging, booking, payment, deletion,
private-data disclosure, and code execution.

### Confirmation copy requirements

The question must state the action and target, human-readable arguments,
one-time scope, consequence/irreversibility, and affirmative/negative choices.

Acceptable pattern:

> Send the approved summary to Alex by email now? Reply yes to send it, or no
> to cancel.

Ambient words, unrelated “yes,” stale confirmation, changed arguments, expired
TTL, or a different target must not execute the action. A declined or expired
request renders a clear cancellation and records the reason.

## 8. Response renderer contract

The renderer is the sole user-facing text boundary for slow-path results.

**Input:** terminal job state, validated answer or failure status, channel,
priority, turn epoch, presentation/accessibility constraints, and provenance.
### Output

One clean speech-first response, concise status when needed, and stable
response/timing metadata. It must not contain schemas, raw model output, stack
traces, credentials, tool logs, hidden prompts, or unrelated private context.

Slice 0 supports structured text output. A later clean-TTS story converts the
same renderer contract to speech. PersonaPlex context injection is deferred and
must not be used as the first result path.

## 9. Error and recovery states

Unknown route asks for another phrasing; invalid action states that the details
do not fit; unconfirmed risk refuses to proceed; stale work stays silent or is
set aside; reasoner failure offers a safe retry; renderer conflict arbitrates by
turn priority; and event failure disables the affected path. Each state records
calibration, rejection reason, cancellation epoch, failure, response choice, or
last valid hash without raw prompt content.

Error copy should be short, specific, honest, and oriented to the next safe
choice. It must not disclose private context merely to appear helpful.

## 10. Accessibility and inclusivity

- Typed input, screen-reader/TTS-friendly responses, accessible confirmations,
  varied dialect/terse fixtures, easy interruption/cancellation, and inclusive
  latency budgets are first-class requirements.

## 11. Operator observability experience

The one-pass report covers fixture versions/counts, route confusion and
calibration, false wakeups/missed work, validation and policy correctness,
terminal jobs, p50/p95/p99 timing, response acceptance, privacy/provenance,
event integrity, and an explicit pass/hold/rollback/kill decision.

Metrics are unacceptable without denominators, fixture versions, UTC run
window, and route stratification.

## 12. User-perspective definition of done

- A reviewer can trace fixture-to-response and explain the route.
- Ordinary conversation never wakes the reasoner.
- Work yields a validated result, clarification, or safe rejection.
- High-risk work cannot progress without confirmation.
- Slow results never collide with active conversation.
- No raw prompt/audio is retained; Slice 0 is local and network-free.

## 13. Design-to-stories inputs

Story themes: fixture/route coverage, router calibration, clarification context,
async lifecycle, policy confirmation, renderer filtering, operator report, and
raw-content ephemerality.
