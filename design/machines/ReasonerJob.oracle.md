# Generated transition oracle: `reasonerJob`

Generated from `ReasonerJob.machine.json` by `machinery oracle`. DO NOT EDIT BY HAND.
<!-- machinery-version: v0.3.11 -->
Single source of truth for the hard-TDD transition tests: one transition row is one
test case. Key tests on the STABLE id, not the row number; row numbers renumber when
the design changes, stable ids do not.

## State entry / exit actions

| state | kind | entry | exit |
|---|---|---|---|
| Pending | atomic | - | - |
| Running | atomic | - | - |
| WaitingConfirmation | atomic | - | - |
| Completed | final | - | - |
| Canceled | final | - | - |
| Downgraded | final | - | - |
| Failed | final | - | - |

## Transitions

| test id | stable id | source | trigger | guard | target | actions |
|---|---|---|---|---|---|---|
| T-REAS-01 | REAS-bc3e49 | Pending | on:run | routeIsNeedsToolsAndFresh | Running | - |
| T-REAS-02 | REAS-5dc4da | Pending | on:cancel | - | Canceled | recordCanceledByUser |
| T-REAS-03 | REAS-974bde | Pending | on:fail | - | Failed | recordFailClosedReason |
| T-REAS-04 | REAS-1559cc | Running | on:cancel | - | Canceled | recordCanceledByUser |
| T-REAS-05 | REAS-f1a17d | Running | on:downgrade | - | Downgraded | recordSafeDowngrade |
| T-REAS-06 | REAS-c3c792 | Running | on:fail | - | Failed | recordFailClosedReason |
| T-REAS-07 | REAS-0c1f49 | Running | after:STALE_TTL | - | Canceled | recordStaleTtlExpired |
| T-REAS-08 | REAS-97e8bd | Running | onDone:requestReasonerProposal | proposalRequiresConfirmation | WaitingConfirmation | bindProposalAndWaitingActions |
| T-REAS-09 | REAS-c567aa | Running | onDone:requestReasonerProposal | - | Completed | bindProposalAndComplete |
| T-REAS-10 | REAS-0766c3 | Running | onError:requestReasonerProposal | - | Failed | recordFailClosedReason |
| T-REAS-11 | REAS-0cd65a | WaitingConfirmation | on:complete | allExactConfirmationsSatisfied | Completed | consumeConfirmations |
| T-REAS-12 | REAS-345901 | WaitingConfirmation | on:cancel | - | Canceled | recordCanceledByUser |
| T-REAS-13 | REAS-79c30e | WaitingConfirmation | on:downgrade | - | Downgraded | recordSafeDowngrade |
| T-REAS-14 | REAS-b46837 | WaitingConfirmation | on:fail | - | Failed | recordFailClosedReason |

Total transitions (test cases): 14
