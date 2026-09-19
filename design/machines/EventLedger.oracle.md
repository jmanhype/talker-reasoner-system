# Generated transition oracle: `eventLedger`

Generated from `EventLedger.machine.json` by `machinery oracle`. DO NOT EDIT BY HAND.
<!-- machinery-version: v0.3.11 -->
Single source of truth for the hard-TDD transition tests: one transition row is one
test case. Key tests on the STABLE id, not the row number; row numbers renumber when
the design changes, stable ids do not.

## State entry / exit actions

| state | kind | entry | exit |
|---|---|---|---|
| Valid | atomic | - | - |
| Appending | atomic | - | - |
| Verifying | atomic | - | - |
| Broken | final | - | - |

## Transitions

| test id | stable id | source | trigger | guard | target | actions |
|---|---|---|---|---|---|---|
| T-EVEN-01 | EVEN-c2c520 | Valid | on:append | eventIsMinimizedAndChained | Appending | prepareNextEvent |
| T-EVEN-02 | EVEN-5feeb7 | Valid | on:verify | - | Verifying | - |
| T-EVEN-03 | EVEN-098b63 | Appending | after:LEDGER_WRITE_TIMEOUT | - | Broken | recordLedgerWriteFailure |
| T-EVEN-04 | EVEN-0d5972 | Appending | onDone:appendCanonicalEvent | - | Valid | advanceHeadHash |
| T-EVEN-05 | EVEN-e9be49 | Appending | onError:appendCanonicalEvent | - | Broken | recordLedgerWriteFailure |
| T-EVEN-06 | EVEN-f230e3 | Verifying | after:LEDGER_WRITE_TIMEOUT | - | Broken | recordIntegrityFailure |
| T-EVEN-07 | EVEN-a0faaa | Verifying | onDone:verifyEventChain | chainHasNoGapsOrMutations | Valid | recordVerificationPass |
| T-EVEN-08 | EVEN-d90d1d | Verifying | onDone:verifyEventChain | - | Broken | recordIntegrityFailure |
| T-EVEN-09 | EVEN-379e68 | Verifying | onError:verifyEventChain | - | Broken | recordIntegrityFailure |

Total transitions (test cases): 9
