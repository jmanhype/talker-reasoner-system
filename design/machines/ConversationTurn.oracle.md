# Generated transition oracle: `conversationTurn`

Generated from `ConversationTurn.machine.json` by `machinery oracle`. DO NOT EDIT BY HAND.
<!-- machinery-version: v0.3.11 -->
Single source of truth for the hard-TDD transition tests: one transition row is one
test case. Key tests on the STABLE id, not the row number; row numbers renumber when
the design changes, stable ids do not.

## State entry / exit actions

| state | kind | entry | exit |
|---|---|---|---|
| Receiving | atomic | - | - |
| Routed | atomic | - | - |
| SlowPath | atomic | - | - |
| AwaitingConfirmation | atomic | - | - |
| Responding | atomic | - | - |
| Terminal | final | - | - |

## Transitions

| test id | stable id | source | trigger | guard | target | actions |
|---|---|---|---|---|---|---|
| T-CONV-01 | CONV-02965d | Receiving | on:transcribe | transcriptValidAndBoundaryConsented | Routed | hashTranscriptAndRetainEphememeral |
| T-CONV-02 | CONV-f9f25b | Receiving | on:cancel | - | Terminal | cancelTurnAndSlowWork |
| T-CONV-03 | CONV-87aef6 | Routed | on:route | routeIsNeedsToolsAndValid | SlowPath | bindRouteToTurn |
| T-CONV-04 | CONV-73bae3 | Routed | on:route | - | Responding | bindRouteToTurn |
| T-CONV-05 | CONV-53ecad | Routed | on:cancel | - | Terminal | cancelTurnAndSlowWork |
| T-CONV-06 | CONV-5d0019 | SlowPath | on:advanceEpoch | - | Terminal | cancelTurnAndSlowWork |
| T-CONV-07 | CONV-a756c5 | SlowPath | on:awaitConfirmation | policyRequiresExactConfirmation | AwaitingConfirmation | - |
| T-CONV-08 | CONV-7c39be | SlowPath | on:cancel | - | Terminal | cancelTurnAndSlowWork |
| T-CONV-09 | CONV-7f7105 | AwaitingConfirmation | on:advanceEpoch | - | Terminal | cancelTurnAndSlowWork |
| T-CONV-10 | CONV-8fadcf | AwaitingConfirmation | on:cancel | - | Terminal | cancelTurnAndSlowWork |
| T-CONV-11 | CONV-dab39a | Responding | on:finish | - | Terminal | releaseProcessingOnlyValues |
| T-CONV-12 | CONV-04c2c7 | Responding | on:cancel | - | Terminal | cancelTurnAndSlowWork |

Total transitions (test cases): 12
