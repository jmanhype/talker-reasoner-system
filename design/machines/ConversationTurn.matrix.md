# ConversationTurn named-unit contract

| name | kind | signature | contract (pre / post) | maps to | test type | fixture |
|---|---|---|---|---|---|---|
| `transcriptValidAndBoundaryConsented` | guard | `(ctx, evt) -> bool` | true iff transcript is bounded, credential-free, and its cloud/local boundary has consent | invariants `session-processing-boundary`, `action-no-credentials` | unit | synthetic transcripts and fake clock |
| `hashTranscriptAndRetainEphememeral` | action | `(ctx, evt) -> ctx` | sets scoped `inputHash`; transcript remains in processing-only memory | `ConversationTurn.transcribe`; invariant `raw-input-ephemeral` | integration | in-memory transcript plus canary store |
| `routeIsNeedsToolsAndValid` | guard | `(ctx, evt) -> bool` | true iff selected label, scores, risk, and calibration versions are valid and label is `needsTools` | invariant `route-fail-closed` | unit | routing fixtures |
| `bindRouteToTurn` | action | `(ctx, evt) -> ctx` | binds immutable route versions and hashes without execution authority | invariant `router-no-authority` | unit | routing fixtures |
| `policyRequiresExactConfirmation` | guard | `(ctx, evt) -> bool` | true iff policy outcome is confirmation required and action hash is present | invariants `policy-before-execution`, `confirmation-exact-and-expiring` | unit | policy fixtures |
| `cancelTurnAndSlowWork` | action | `(ctx, evt) -> ctx` | advances epoch and emits cancellation intent to the reasoner job | invariants `job-staleness-bounded`, `canceled-work-silent` | integration | local scripted transport |
| `releaseProcessingOnlyValues` | action | `(ctx) -> ctx` | removes ephemeral transcript and emits terminal metadata | invariants `raw-input-ephemeral`, `response-filtered` | integration | privacy canary |

## Failure catalog

| failure | detection | transition | recovery | mitigation or residual |
|---|---|---|---|---|
| invalid or missing transcript | transcription guard | Receiving stays guarded / no route | ask clarification | route fails closed to unclear |
| invalid calibration | route guard | Routed -> Responding guarded response | clarify or rollback | no reasoner wakeup |
| turn superseded | epoch event | SlowPath or AwaitingConfirmation -> Terminal | cancel or downgrade job | stale result cannot render |
| renderer conflict | finish action guard in implementation | Responding remains unfinished | prioritize active user audio | no overlap |
