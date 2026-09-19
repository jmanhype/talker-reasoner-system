# Generated transition oracle: `voiceSession`

Generated from `VoiceSession.machine.json` by `machinery oracle`. DO NOT EDIT BY HAND.
<!-- machinery-version: v0.3.11 -->
Single source of truth for the hard-TDD transition tests: one transition row is one
test case. Key tests on the STABLE id, not the row number; row numbers renumber when
the design changes, stable ids do not.

## State entry / exit actions

| state | kind | entry | exit |
|---|---|---|---|
| Active | atomic | - | - |
| Degraded | atomic | - | - |
| Closed | final | - | - |

## Transitions

| test id | stable id | source | trigger | guard | target | actions |
|---|---|---|---|---|---|---|
| T-VOIC-01 | VOIC-305554 | Active | on:degrade | - | Degraded | markSessionDegraded |
| T-VOIC-02 | VOIC-e62d1f | Active | on:close | - | Closed | releaseProcessingOnlyValues |
| T-VOIC-03 | VOIC-32ea66 | Degraded | on:close | - | Closed | releaseProcessingOnlyValues |

Total transitions (test cases): 3
