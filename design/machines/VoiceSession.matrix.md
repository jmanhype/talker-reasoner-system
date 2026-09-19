# VoiceSession named-unit contract

| name | kind | signature | contract (pre / post) | maps to | test type | fixture |
|---|---|---|---|---|---|---|
| `markSessionDegraded` | action | `(ctx) -> ctx` | records degraded status and operator signal without changing boundary | `VoiceSession.degrade`; invariant `session-processing-boundary` | unit | fake clock and in-memory session |
| `releaseProcessingOnlyValues` | action | `(ctx) -> ctx` | removes raw audio/transcript references and records terminal metadata only | `VoiceSession.close`; invariant `raw-input-ephemeral` | integration | in-memory buffers with canaries |

## Failure catalog

| failure | detection | transition | recovery | mitigation or residual |
|---|---|---|---|---|
| PersonaPlex or live dependency unavailable | dependency health event | Active -> Degraded | close or continue only with guarded fallback | fast/slow paths remain fail-closed |
| processing-only value remains after close | close action postcondition | Active -> Closed | close fails until release check passes | privacy canary and zero-retention gate |

