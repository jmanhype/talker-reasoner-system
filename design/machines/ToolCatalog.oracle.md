# Generated transition oracle: `toolCatalog`

Generated from `ToolCatalog.machine.json` by `machinery oracle`. DO NOT EDIT BY HAND.
<!-- machinery-version: v0.3.11 -->
Single source of truth for the hard-TDD transition tests: one transition row is one
test case. Key tests on the STABLE id, not the row number; row numbers renumber when
the design changes, stable ids do not.

## State entry / exit actions

| state | kind | entry | exit |
|---|---|---|---|
| Draft | atomic | - | - |
| Reviewed | atomic | - | - |
| Active | atomic | - | - |
| Retired | final | - | - |

## Transitions

| test id | stable id | source | trigger | guard | target | actions |
|---|---|---|---|---|---|---|
| T-TCAT-01 | TCAT-563b02 | Draft | on:define | - | Draft | upsertDraftDefinition |
| T-TCAT-02 | TCAT-3a38e4 | Draft | on:review | schemasProvenanceAndPolicyComplete | Reviewed | - |
| T-TCAT-03 | TCAT-97dc90 | Reviewed | on:activate | catalogHashIsImmutable | Active | - |
| T-TCAT-04 | TCAT-675b21 | Active | on:retire | - | Retired | recordCatalogRetirement |

Total transitions (test cases): 4
