# ToolExecution named-unit contract

| name | kind | signature | contract (pre / post) | maps to | test type | fixture |
|---|---|---|---|---|---|---|
| `actionAllowedAndConfirmationsSatisfied` | guard | `(ctx, evt) -> bool` | true iff validated action hash, policy version, and all exact confirmations are active | invariants `policy-before-execution`, `confirmation-exact-and-expiring` | unit | policy/confirmation matrix |
| `bindCatalogAndIdempotency` | action | `(ctx, evt) -> ctx` | binds immutable catalog version and idempotency key to the action hash | invariants `catalog-version-pinned`, `tool-allowlist-only` | unit | active catalog fixture |
| `recordPolicyRejection` | action | `(ctx, evt) -> ctx` | records stable policy rejection code without secrets or raw args | invariant `ledger-minimized` | unit | rejection fixtures |
| `definitionIsAllowlistedAndActive` | guard | `(ctx, evt) -> bool` | true iff canonical name exists in the active catalog and source plane is allowed | invariants `tool-allowlist-only`, `runtime-cannot-mutate-capability` | integration | active catalog plus MAGG runtime contract fake |
| `invokeAllowlistedTool` | actor | `(input) -> ToolResult` | invokes only the allowlisted adapter once per idempotency key; credentials remain server-side | C4 `toolGateway -> external.magg/localMcp`; invariants `credential-isolation`, `tool-allowlist-only` | integration | contract-tested MAGG/local MCP executor |
| `toolOutputPassedFiltering` | guard | `(result) -> bool` | true iff result matches schema, privacy class, size, and safety filter | invariant `tool-output-filtered` | property | malicious/oversized result corpus |
| `recordFilteredResultHash` | action | `(ctx, evt) -> ctx` | stores only result hash, bounded safe result, status, latency, and cost class | invariants `tool-output-filtered`, `tool-result-not-sole-truth` | integration | canary tool output |
| `recordUnsafeOutput` | action | `(ctx, evt) -> ctx` | records unsafe-output failure without raw content | invariants `tool-output-filtered`, `ledger-minimized` | integration | privacy canary |
| `recordExecutorFailure` | action | `(ctx, evt) -> ctx` | records stable failure code and bounded latency without credentials | invariant `credential-isolation` | integration | failing contract executor |
| `recordExecutionTimeout` | action | `(ctx) -> ctx` | records timeout terminal reason and cancels adapter work | invariant `contract-fail-closed` | integration | fake monotonic clock |

## Failure catalog

| failure | detection | transition | recovery | mitigation or residual |
|---|---|---|---|---|
| policy rejection | authorize guard | Proposed -> Rejected | clarify or stop | no dispatch |
| non-allowlisted tool | dispatch guard | Authorized remains Authorized | reject and alert | runtime cannot expand capability |
| provider unavailable | invoke onError | Dispatched -> Failed | bounded retry by future catalog policy | no fabricated result |
| output unsafe | filter guard | Dispatched -> Failed | filter or reject | raw output never persisted |
| execution timeout | invoke after | Dispatched -> TimedOut | cancel and report bounded failure | 10 second initial bound |

