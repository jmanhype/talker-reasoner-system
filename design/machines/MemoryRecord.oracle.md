# Generated transition oracle: `memoryRecord`

Generated from `MemoryRecord.machine.json` by `machinery oracle`. DO NOT EDIT BY HAND.
<!-- machinery-version: v0.3.11 -->
Single source of truth for the hard-TDD transition tests: one transition row is one
test case. Key tests on the STABLE id, not the row number; row numbers renumber when
the design changes, stable ids do not.

## State entry / exit actions

| state | kind | entry | exit |
|---|---|---|---|
| Candidate | atomic | - | - |
| Approved | atomic | - | - |
| Active | atomic | - | - |
| Superseded | atomic | - | - |
| Rejected | final | - | - |
| Deleted | final | - | - |

## Transitions

| test id | stable id | source | trigger | guard | target | actions |
|---|---|---|---|---|---|---|
| T-MEMO-01 | MEMO-0697b6 | Candidate | on:approve | provenanceConsentAndReviewComplete | Approved | recordApprovalEvidence |
| T-MEMO-02 | MEMO-ef809c | Candidate | on:approve | - | Rejected | recordMemoryRejection |
| T-MEMO-03 | MEMO-814928 | Candidate | on:delete | - | Deleted | deleteFromPrimaryAndBackups |
| T-MEMO-04 | MEMO-914d7a | Approved | on:activate | memoryPlatformDeletionTestPassed | Active | recordActivation |
| T-MEMO-05 | MEMO-c8e66c | Approved | on:delete | - | Deleted | deleteFromPrimaryAndBackups |
| T-MEMO-06 | MEMO-b8a59c | Active | on:recall | - | Active | recordBoundedRecallWithProvenance |
| T-MEMO-07 | MEMO-9faf38 | Active | on:supersede | - | Superseded | recordSuccessorAndProvenance |
| T-MEMO-08 | MEMO-d9f286 | Active | on:delete | - | Deleted | deleteFromPrimaryAndBackups |
| T-MEMO-09 | MEMO-8862c9 | Superseded | on:delete | - | Deleted | deleteFromPrimaryAndBackups |

Total transitions (test cases): 9
