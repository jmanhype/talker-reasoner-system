# ReasonerJob named-unit contract

| name | kind | signature | contract (pre / post) | maps to | test type | fixture |
|---|---|---|---|---|---|---|
| `routeIsNeedsToolsAndFresh` | guard | `(ctx, evt) -> bool` | true iff originating turn route is valid needsTools and epoch is current | invariants `slow-path-only-after-route`, `job-staleness-bounded` | unit | routing and epoch fixtures |
| `requestReasonerProposal` | actor | `(input) -> ReasonerProposal` | returns exactly one schema-valid proposal for the bound request; no execution authority | C4 `reasoning -> external.reasoner`; invariants `reasoner-proposes-only`, `proposal-identity-bound` | integration | LocalScriptedTransport, then consented real adapter |
| `proposalRequiresConfirmation` | guard | `(proposal) -> bool` | true iff any validated action policy outcome is confirmation required | invariant `policy-before-execution` | unit | action policy fixtures |
| `bindProposalAndWaitingActions` | action | `(ctx, evt) -> ctx` | binds proposal hash and exact waiting action hashes without granting permission | invariants `proposal-identity-bound`, `catalog-version-pinned` | unit | typed proposal |
| `bindProposalAndComplete` | action | `(ctx, evt) -> ctx` | binds proposal and marks only validated non-action or fully allowed work complete | invariants `policy-before-execution`, `response-filtered` | integration | local validation/policy suite |
| `recordFailClosedReason` | action | `(ctx, evt) -> ctx` | records one stable terminal reason and emits ledger metadata | invariant `contract-fail-closed` | unit | invalid proposal fixtures |
| `allExactConfirmationsSatisfied` | guard | `(ctx, evt) -> bool` | true iff every waiting hash has an unused, exact, unexpired confirmation | invariants `confirmation-exact-and-expiring`, `confirmation-single-use` | unit | confirmation matrix |
| `consumeConfirmations` | action | `(ctx, evt) -> ctx` | marks exact confirmations used and never reuses their hashes | invariant `confirmation-single-use` | integration | duplicate confirmation test |
| `recordCanceledByUser` | action | `(ctx, evt) -> ctx` | records operator cancellation and suppresses normal rendering | invariant `canceled-work-silent` | integration | cancellation fixture |
| `recordStaleTtlExpired` | action | `(ctx) -> ctx` | records stale TTL terminal reason | invariant `job-staleness-bounded` | integration | fake monotonic clock |
| `recordSafeDowngrade` | action | `(ctx, evt) -> ctx` | records bounded non-action summary only | invariants `canceled-work-silent`, `response-filtered` | unit | unsafe presentation fixture |

## Failure catalog

| failure | detection | transition | recovery | mitigation or residual |
|---|---|---|---|---|
| reasoner timeout | `STALE_TTL` | Running -> Canceled | user may retry with a new turn | 30 second bound and no late render |
| transport error | invoke onError | Running -> Failed | safe retry or rephrase | no tool dispatch |
| malformed proposal | actor validation | Running -> Failed | use fixture or clarification | fail-closed contract |
| confirmation expired | complete guard | WaitingConfirmation -> Failed | ask for new exact confirmation | confirmation TTL |
| presentation unsafe | downgrade event | Running/WaitingConfirmation -> Downgraded | bounded non-action summary | no raw output render |

