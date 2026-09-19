# EventLedger named-unit contract

| name | kind | signature | contract (pre / post) | maps to | test type | fixture |
|---|---|---|---|---|---|---|
| `eventIsMinimizedAndChained` | guard | `(ctx, evt) -> bool` | true iff event has no raw/credential content and carries exact prior ID/hash | invariants `ledger-minimized`, `ledger-append-only` | property | canary event corpus |
| `prepareNextEvent` | action | `(ctx, evt) -> ctx` | assigns next monotonic event ID and canonical body without mutating history | invariant `ledger-append-only` | unit | local chain |
| `appendCanonicalEvent` | actor | `(input) -> AppendReceipt` | appends exactly once by event ID; fails on duplicate or mutation | C4 `eventLedger -> postgres`; invariant `ledger-append-only` | integration | local EventLedger then real Postgres |
| `advanceHeadHash` | action | `(ctx, evt) -> ctx` | stores returned head hash and event count | invariant `ledger-append-only` | integration | local EventLedger |
| `recordLedgerWriteFailure` | action | `(ctx, evt) -> ctx` | records bounded failure metadata and disables affected action path | invariant `ledger-integrity-fail-closed` | integration | fault-injected append |
| `verifyEventChain` | actor | `(input) -> LedgerVerification` | verifies IDs, prior hashes, terminal uniqueness, and mutation absence | invariant `ledger-integrity-fail-closed` | integration | valid and mutated chains |
| `chainHasNoGapsOrMutations` | guard | `(result) -> bool` | true iff valid chain is true and gap/mutation/duplicate sets are empty | invariant `ledger-integrity-fail-closed` | unit | verification fixtures |
| `recordVerificationPass` | action | `(ctx, evt) -> ctx` | records last verified event and valid-chain evidence | invariant `ledger-integrity-fail-closed` | unit | local chain |
| `recordIntegrityFailure` | action | `(ctx, evt) -> ctx` | records failure class and offending event IDs without raw content | invariants `ledger-minimized`, `ledger-integrity-fail-closed` | integration | broken chain fixture |

## Failure catalog

| failure | detection | transition | recovery | mitigation or residual |
|---|---|---|---|---|
| append timeout | invoke after | Appending -> Broken | fail affected action and alert | no unaudited work |
| Postgres unavailable | append onError | Appending -> Broken | rollback to local ledger only after gate | action path disabled |
| chain mutation | verify guard/onDone fallback | Verifying -> Broken | forensic recovery from immutable copy | action path disabled |
| raw-content canary in event | append guard | Valid remains Valid | reject event and alert | zero raw persistence |

