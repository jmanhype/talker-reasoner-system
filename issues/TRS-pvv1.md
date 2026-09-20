---
id: TRS-pvv1
title: "M2 voice session and turn contracts"
status: open
priority: 1
type: epic
created_at: 2026-09-20T00:01:53Z
created_by: speed
updated_at: 2026-09-20T01:21:03Z
content_hash: "sha256:8150851cb7a3808e3ed04c17549cb45b799b0d7f8f29212e6fefce4f6cb2c2f6"
---

## Description
## Description

Implement milestone M2 from `design/BUILD.md`: the offline VoiceSession and ConversationTurn behavioral layer, including typed/spoken parity, one active audio-stream arbiter, accessibility metadata, turn-epoch cancellation, ephemeral transcript release, and renderer arbitration.

This milestone remains entirely local and deterministic. It adds no live PersonaPlex, Voxtral, Jev, durable store, tool execution, network inference, credential, or semantic-memory dependency.

## Epic Outcomes

- A single-operator voice session follows the authoritative VoiceSession machine.
- A turn follows the authoritative ConversationTurn machine from typed transcript through routing, slow-path wait, cancellation or response, and terminal release.
- Raw transcript values are processing-only and disappear on terminal or session closure.
- Typed and spoken presentation carry the same bounded semantic payload and explicit accessibility metadata.
- One audio/response stream may be active at a time; active user speech outranks stale slow-path output.
- Advancing a turn epoch cancels or downgrades superseded slow work.
- All `VOIC-*` and `CONV-*` oracle rows are covered by real tests, not prose claims.

## OUT OF SCOPE

- Live audio capture or playback: M3.
- PersonaPlex, Voxtral, or Jev adapters: M3.
- Redis, PostgreSQL, Mem0, Cognee, Zep, or Letta: M4/M8 or later.
- Tool catalog, tool execution, MAGG, Dagger, Treg, or Context Forge: M5+.
- Changing the seven committed machine definitions or oracle stable ids.

## Acceptance Criteria

1. `VOIC-305554`, `VOIC-e62d1f`, and `VOIC-32ea66` pass through executable behavior.
2. Every `CONV-*` row in `design/machines/ConversationTurn.oracle.md` passes through executable behavior.
3. Privacy canaries prove raw transcript release on terminal and session closure.
4. Renderer arbitration proves one active stream and stale slow-path output cannot overlap active user speech.
5. The complete suite, `machinery check design --impl .`, `machinery lint design/machines`, `machinery oracle design/machines`, and `modelith lint design/domain.modelith.yaml --completeness error` pass.

## Design

- Source milestone: `design/BUILD.md` section 9, M2.
- Session authority: `design/machines/VoiceSession.machine.json`.
- Turn authority: `design/machines/ConversationTurn.machine.json`.
- Architecture boundary: `trs.voice-edge` in `design/ARCHITECTURE.md`.
- Existing edge port: `edge/ports/audio.ts`.

## MANDATORY SKILLS

- pvg: story governance.
- machinery: oracle and architecture gates.

## nd_contract
status: new

### evidence
- Created from accepted M1 commit `f7bc6e0` and the committed M2 build plan.

### proof
- [ ] Pending M2 implementation and capstone evidence.


## Acceptance Criteria


## Design


## Notes
## Epic Completion Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/talker-reasoner-system
pytest -q
machinery check design --impl .
machinery lint design/machines
machinery oracle design/machines
modelith lint design/domain.modelith.yaml --completeness error
pvg gates design edge talk_reasoner config tests --seal
pvg lint --backlog
pvg rtm check
git diff --check
```

Measured completion:

- Final implementation commit: `25b54c9610c61730d751bf9c2e9aa0dbddc77c22`
- Milestone acceptance commit: `d723f2b`
- Full suite: 363/363 passed.
- M2 E2e report: 18/18 conditions true, decision `pass`.
- Privacy checks: 4/4.
- Arbitration checks: 5/5.
- VoiceSession rows: 3/3.
- ConversationTurn rows: 12/12.
- Tool executions: 0.
- Machinery implementation gate: 0 blocking findings.
- Machine lint/oracle: 0 error/drift findings across 7 machines.
- Modelith completeness: 0 errors, 0 warnings.
- Repository-owned path gates seal: PASS with inherited non-blocking complexity warnings.
- Backlog lint: PASS, 0 errors.
- RTM: 62/62 oracle requirements covered.

Note: an initial unscoped `pvg gates --seal` scanned generated `.venv` packages and `.git/hooks` samples and failed on unrelated generated code. The repository-owned path seal passes; this is a tool-scope issue, not an M2 source failure.

## nd_contract
status: accepted

### evidence
- Accepted stories: TRS-6rrt, TRS-fcji, TRS-ji8y, TRS-wwx4.
- All story branches merged into `epic/TRS-pvv1`.
- M2 status and acceptance evidence committed at `d723f2b`.

### proof
- [x] All M2 stories accepted.
- [x] All 15 M2 oracle rows exercised.
- [x] E2e decision pass.
- [x] Full suite and completion gates pass.


## History


## Links


## Comments

### 2026-09-20T00:02:33Z speed
Backlog lint review justifications: (1) duplicate canonical headings are produced when nd appends its managed empty sections after an authored self-contained body; the last nd_contract remains authoritative. (2) The two vertical-slice heuristic findings are false negatives: TRS-6rrt explicitly defines that the user can receive one clean non-tool response and close the session, and TRS-ji8y defines that a canceled or superseded turn can no longer surface as a normal response. No error findings exist; RTM covers all 62 oracle rows.
