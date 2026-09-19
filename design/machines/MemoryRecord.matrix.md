# MemoryRecord named-unit contract

| name | kind | signature | contract (pre / post) | maps to | test type | fixture |
|---|---|---|---|---|---|---|
| `provenanceConsentAndReviewComplete` | guard | `(ctx) -> bool` | true iff content provenance, consent, and review evidence are complete | invariant `memory-provenance-bound` | unit | memory provenance fixtures |
| `recordApprovalEvidence` | action | `(ctx, evt) -> ctx` | records reviewer, consent version, and origin event hash | invariant `memory-provenance-bound` | integration | EventLedger fixture |
| `recordMemoryRejection` | action | `(ctx, evt) -> ctx` | records rejection reason without storing raw candidate content | invariant `ledger-minimized` | unit | malformed candidate |
| `memoryPlatformDeletionTestPassed` | guard | `(ctx) -> bool` | true iff primary, derived, and backup deletion tests pass for this record class | invariant `memory-deletable` | integration | disposable memory platform plus backup fixture |
| `recordActivation` | action | `(ctx, evt) -> ctx` | marks the record active with version and platform provenance | invariant `memory-not-sole-truth` | integration | disposable memory platform |
| `recordBoundedRecallWithProvenance` | action | `(ctx, evt) -> ctx` | records bounded recall result and provenance without exposing unrelated memory | invariants `memory-provenance-bound`, `response-filtered` | integration | recall corpus |
| `recordSuccessorAndProvenance` | action | `(ctx, evt) -> ctx` | links successor record and preserves superseded history | invariant `memory-not-sole-truth` | integration | versioned memory fixture |
| `deleteFromPrimaryAndBackups` | action | `(ctx) -> ctx` | deletes primary, derived, and backup copies and records deletion evidence | invariant `memory-deletable` | integration | privacy canary across primary and backup |

## Failure catalog

| failure | detection | transition | recovery | mitigation or residual |
|---|---|---|---|---|
| missing provenance or consent | approve guard | Candidate -> Rejected | recreate candidate with provenance | no memory activation |
| deletion test failure | activate guard | Approved remains Approved | block activation | memory remains deferred |
| recall timeout or low relevance | recall actor/action contract | Active remains Active | omit memory context | response unaffected |
| backup deletion failure | delete action | Deleted transition is blocked in implementation | retry deletion and alert | canary must not persist |

