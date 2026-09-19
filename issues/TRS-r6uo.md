---
id: TRS-r6uo
title: "Prove typed fixture-ledger contracts locally"
status: open
priority: 1
type: feature
labels: [walking-skeleton, slice-0]
parent: TRS-pf94
created_at: 2026-09-19T05:25:40Z
created_by: speed
updated_at: 2026-09-19T05:25:40Z
content_hash: "sha256:84a898b60057b093263f06cd0f0c91fb52acde8f7189000971b5594dbd095a0f"
blocks: [TRS-wqbs, TRS-hjbd, TRS-do2n]
---

## Description
## Context (Embedded)

This is the first implementation story for the independent Talker-Reasoner
System. Slice 0 is local, deterministic, and network-free. It proves typed
fixtures plus provenance before routing, reasoner, policy, or rendering work.

Authoritative constraints:

- Routes are exactly `chitchat`, `needs_tools`, and `unclear`.
- PersonaPlex/Moshi is not a native tool-calling model.
- Voxtral Small may emit structured `tool_calls` but never executes tools.
- Voxtral Realtime is transcription-oriented.
- Jev routes but never executes tools.
- No live audio, external inference, credentials, Redis, Postgres, Mem0,
  Cognee, Zep/Graphiti, Letta, or tool execution is authorized.
- Raw prompts, raw model requests/responses, hidden instructions, and raw
  audio never enter the fixture ledger or event ledger.

Fixture records are versioned values, not ad hoc strings. They identify
fixture/schema IDs, session/turn IDs, consent flags, in-memory transcript,
bounded context/state, expected outcome, optional timing/interruption,
provenance, and test purpose. Event records retain IDs, turn epoch, content
hash/length/media type, consent and policy versions, status, rejection reason,
latency, and prior-chain metadata--never raw content.

## USER INTENT

Give the evaluator a frozen, typed corpus and an auditable append-only chain so
every later routing, action, job, and response claim can be reproduced without
live audio, external services, credentials, or private raw-content retention.

## Goal

Establish the local fixture and event contracts as one independently testable
foundation, including canonical serialization, hash scoping, append-only
behavior, and integrity verification.

## OUT OF SCOPE

- Routing or calibration: deliberately deferred to the downstream routing story.
- Action validation/preflight: deliberately deferred to the action-policy story.
- Reasoner jobs or transports: deliberately deferred to the async-job story.
- User-facing rendering or CLI orchestration: deliberately deferred to the CLI story.
- Live voice, external inference, storage, and memory platforms: never in Slice 0.

## DIFF BUDGET

- About 7 source/test/config files plus fixture records; under 600 changed LOC.
- Gross overrun requires PM investigation for scope creep or hidden design gaps.

## Boundary Map

PRODUCES:
- src/talk_reasoner/contracts.py -> load_fixture(path: pathlib.Path) -> Fixture
  spec: Parse one JSON fixture into a frozen typed Fixture; reject unknown schema_version, duplicate IDs, invalid routes/states, missing consent/provenance, credentials, or unbounded context.
- src/talk_reasoner/contracts.py -> load_fixture_corpus(paths: Iterable[pathlib.Path]) -> FixtureCorpus
  spec: Load and validate a frozen corpus with deterministic ordering and at least 6 fixtures for each of chitchat, needs_tools, and unclear.
- src/talk_reasoner/contracts.py -> scoped_hash(content: str | bytes, *, scope: str, schema_version: str) -> str
  spec: Return a stable hex SHA-256 over canonical scope/schema metadata plus content; identical input is deterministic and raw content is not retained.
- src/talk_reasoner/contracts.py -> canonical_event_bytes(event: LedgerEvent) -> bytes
  spec: Return deterministic canonical JSON bytes for chain computation, excluding the stored event chain field.
- src/talk_reasoner/contracts.py -> append_event(ledger: EventLedger, event: LedgerEvent) -> AppendReceipt
  spec: Validate event ID/order, append immutably, link scoped input/action hashes and prior event hash, and return the stored event plus chain hash.
- src/talk_reasoner/contracts.py -> verify_ledger(ledger: EventLedger) -> LedgerVerification
  spec: Report valid chain, event count, gaps, invalid prior hashes, duplicate terminal states, and mutations; any integrity defect makes valid_chain false.
- tests/fixtures/slice0/ -> versioned typed JSON fixture corpus
  fields: schema_version, fixture_id, session_id, turn_id, consent, transcript, bounded_context, expected, provenance, test_purpose.
- tests/test_contracts.py -> fixture and ledger contract tests
  source: covers valid corpus loading plus malformed fixtures, hash determinism, canonical serialization, tampering, gaps, and duplicate terminals.

CONSUMES:
- (none -- leaf story)

## Acceptance Criteria

1. The versioned corpus contains at least 18 valid fixtures with at least 6
   expected for each exact route: `chitchat`, `needs_tools`, and `unclear`.
2. Fixture loading performs strict typed validation of IDs, schema/fixture
   versions, session/turn identity, consent flags, bounded state, expected
   outcome, provenance, and test purpose; duplicate or malformed records fail
   closed with actionable errors.
3. `scoped_hash` is deterministic for identical content and metadata, differs
   when scope, schema version, or content changes, and never stores raw content.
4. Event serialization is canonical and stable for the fixture set. Every event
   carries schema/type/version, event/session/turn/job IDs where applicable,
   turn epoch, scoped input hash, length/media metadata, consent/policy
   versions, status/rejection reason, latency, and prior-chain metadata.
5. The append-only ledger detects missing IDs, ordering gaps, invalid prior
   hashes, duplicate terminal states, and mutations; a broken chain returns a
   failing verification rather than allowing unaudited work.
6. Public functions and data models have complete Python type annotations and
   immutable public data where practical.
7. Integration verification loads the complete corpus, appends representative
   route/action/lifecycle/response events, and verifies the resulting ledger.
8. Tests prove zero credential patterns, zero raw transcript copies in ledger
   bytes, zero network calls, and zero platform-service dependencies.

## Testing Requirements

- Unit tests: fixture schema acceptance/rejection, hash scoping, canonical JSON,
  and event receipts.
- Integration tests: MANDATORY (no mocks). Load every fixture file, exercise a
  representative multi-event ledger, serialize and verify it, and inspect bytes
   for forbidden raw-content fields.
- E2E tests: not in this story; the blocked capstone owns user-journey coverage.
- Commands: `python -m pytest tests/test_contracts.py`.

## Skills To Use

- `project-standards`: preserve typed public contracts and test discipline.
- `pvg`: story governance and delivery evidence only.

## Delivery Requirements

- Paste exact pytest output and exit status.
- Include an AC verification table with file/test evidence.
- Show a corpus count by expected route and a successful ledger verification.
- Update the authoritative `nd_contract` using the pvg delivery workflow.

## nd_contract

status: new

### evidence

- Created: 2026-09-19
- Derived from accepted TRS-zpo4 D&F and TRS-pf94.

### proof

- [ ] Pending implementation


## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T05:25:58Z dep_added: blocks TRS-wqbs
- 2026-09-19T05:25:58Z dep_added: blocks TRS-hjbd
- 2026-09-19T05:25:59Z dep_added: blocks TRS-do2n

## Links
- Parent: [[TRS-pf94]]
- Blocks: [[TRS-wqbs]], [[TRS-hjbd]], [[TRS-do2n]]

## Comments
