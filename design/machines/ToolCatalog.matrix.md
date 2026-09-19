# ToolCatalog named-unit contract

| name | kind | signature | contract (pre / post) | maps to | test type | fixture |
|---|---|---|---|---|---|---|
| `upsertDraftDefinition` | action | `(ctx, evt) -> ctx` | adds or replaces one definition only in Draft and recomputes draft hash | invariants `runtime-cannot-mutate-capability`, `tool-schema-provenance` | unit | reviewed definition fixture |
| `schemasProvenanceAndPolicyComplete` | guard | `(ctx) -> bool` | true iff every definition has schema hashes, provenance, permission, risk, scope, bounds, and rejection codes | invariants `catalog-reviewed-before-active`, `tool-schema-provenance` | property | generated catalog fixtures |
| `catalogHashIsImmutable` | guard | `(ctx, evt) -> bool` | true iff reviewed hash equals activation hash and policy version binds | invariant `catalog-version-pinned` | unit | catalog hash mutation fixture |
| `recordCatalogRetirement` | action | `(ctx) -> ctx` | records retired version without deleting audit history | invariant `runtime-cannot-mutate-capability` | unit | active catalog fixture |

## Failure catalog

| failure | detection | transition | recovery | mitigation or residual |
|---|---|---|---|---|
| incomplete tool schema or provenance | review guard | Draft remains Draft | admin completes definition | runtime cannot activate |
| active catalog hash drift | activation guard | Reviewed remains Reviewed | publish a new version | no silent drift |
| malicious runtime requests definition change | state-specific ignore | Active ignores define | reject and alert | capability-surface red-team |

