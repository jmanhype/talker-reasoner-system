# Generated transition oracle: `toolExecution`

Generated from `ToolExecution.machine.json` by `machinery oracle`. DO NOT EDIT BY HAND.
<!-- machinery-version: v0.3.11 -->
Single source of truth for the hard-TDD transition tests: one transition row is one
test case. Key tests on the STABLE id, not the row number; row numbers renumber when
the design changes, stable ids do not.

## State entry / exit actions

| state | kind | entry | exit |
|---|---|---|---|
| Proposed | atomic | - | - |
| Authorized | atomic | - | - |
| Dispatched | atomic | - | - |
| Succeeded | final | - | - |
| Failed | final | - | - |
| TimedOut | final | - | - |
| Rejected | final | - | - |

## Transitions

| test id | stable id | source | trigger | guard | target | actions |
|---|---|---|---|---|---|---|
| T-TEXE-01 | TEXE-6c80b2 | Proposed | on:authorize | actionAllowedAndConfirmationsSatisfied | Authorized | bindCatalogAndIdempotency |
| T-TEXE-02 | TEXE-9297f7 | Proposed | on:authorize | - | Rejected | recordPolicyRejection |
| T-TEXE-03 | TEXE-8688ba | Proposed | on:fail | - | Failed | recordExecutorFailure |
| T-TEXE-04 | TEXE-0d301e | Authorized | on:dispatch | definitionIsAllowlistedAndActive | Dispatched | - |
| T-TEXE-05 | TEXE-49dba9 | Authorized | on:fail | - | Failed | recordExecutorFailure |
| T-TEXE-06 | TEXE-b9c795 | Dispatched | on:fail | - | Failed | recordExecutorFailure |
| T-TEXE-07 | TEXE-e18dac | Dispatched | on:timeout | - | TimedOut | recordExecutionTimeout |
| T-TEXE-08 | TEXE-34eda4 | Dispatched | after:EXECUTION_TIMEOUT | - | TimedOut | recordExecutionTimeout |
| T-TEXE-09 | TEXE-782b09 | Dispatched | onDone:invokeAllowlistedTool | toolOutputPassedFiltering | Succeeded | recordFilteredResultHash |
| T-TEXE-10 | TEXE-a8cfa2 | Dispatched | onDone:invokeAllowlistedTool | - | Failed | recordUnsafeOutput |
| T-TEXE-11 | TEXE-30e3a5 | Dispatched | onError:invokeAllowlistedTool | - | Failed | recordExecutorFailure |

Total transitions (test cases): 11
