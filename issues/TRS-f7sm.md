---
id: TRS-f7sm
title: "Show clean CLI outcomes for every terminal slice state"
status: closed
priority: 1
type: feature
labels: [cli, integration, slice-0, accepted]
parent: TRS-pf94
created_at: 2026-09-19T05:29:37Z
created_by: speed
updated_at: 2026-09-19T16:57:45Z
content_hash: "sha256:ef5e78d29c584d10fb8f7f9c13672ae2c5e6aa4ed2104e535fbf348be351cfda"
was_blocked_by: [TRS-74z8, TRS-9md6, TRS-ndv6]
assignee: dev-TRS-f7sm
follows: [TRS-74z8, TRS-9md6, TRS-ndv6, TRS-0daa]
closed_at: 2026-09-19T16:57:44Z
close_reason: "Accepted: independently reran compilation, 44/44 story tests, 154/154 full tests, pvg verify, git diff check, real chitchat/unclear/needs-tools/invalid CLI probes, and privacy scans. Rendering is clean, bounded, privacy-safe, and correctly separates stdout from compact evidence."
---

## Description
## Context (Embedded)

The renderer is the sole user-facing text boundary for slow-path results. Slice
0 uses structured text and a visible CLI; it does not synthesize speech or
inject context into PersonaPlex.

Renderer input is terminal job state, validated answer or failure status,
channel, priority, turn epoch, presentation/accessibility constraints, and
provenance. Output is one clean speech-first response, concise status where
needed, and stable response/timing metadata.

Forbidden user-facing content includes schemas, raw model output, stack traces,
credentials, tool logs, hidden prompts, unrelated private context, internal
event bodies, and unreviewed private tool output.

Waiting confirmation must ask one exact question naming action and target,
human-readable arguments, one-time scope, consequence/irreversibility, and safe
yes/no choices. Canceled work stays silent or terse only if requested. Failed
work is honest and offers one safe recovery action without fabricating output.

## USER INTENT

A speaker receives one coherent, clean answer, clarification, confirmation, or
safe failure--never tool jargon, raw model output, a stale interruption, or an
internal debugging dump.

## Goal

Render every Slice-0 terminal outcome and expose a local CLI command that runs
one typed fixture through routing, async proposal work, validation/policy, and
clean output with visible evidence.

## OUT OF SCOPE

- TTS or audio playback: later clean-TTS story.
- PersonaPlex context injection, drip feed, or audio gating: later integration story.
- Live typed/voice input: Slice 0 consumes versioned fixtures only.
- New routing, action, or lifecycle behavior: consume the upstream contracts.
- Persistent response storage or report database: local in-memory/evidence only.

## DIFF BUDGET

- About 6 source/test files; under 425 changed LOC.
- Gross overrun requires PM investigation for scope creep or hidden design gaps.

## Boundary Map

PRODUCES:
- src/talk_reasoner/rendering.py -> render_response(outcome: TerminalOutcome, *, constraints: PresentationConstraints) -> RenderedResponse
  spec: Produce exactly one clean response plus response_id, channel, priority, turn_epoch, latency_ms, and provenance; reject forbidden/internal content and ambiguous terminal state.
- src/talk_reasoner/cli.py -> async run_fixture(fixture: Fixture, *, transport: ReasonerTransport, clock: MonotonicClock, stdout: TextIO, stderr: TextIO) -> CLIResult
  spec: Route the fixture, run the reasoner only for needs_tools, render one terminal outcome, print clean text to stdout and compact non-raw JSON evidence to stderr, and return exit status plus ledger/report references.
- src/talk_reasoner/cli.py -> main(argv: Sequence[str] | None = None) -> int
  spec: Parse one fixture path and local options, invoke run_fixture, return 0 for a normal terminal outcome and 2 for fail-closed usage/policy/ledger/render errors.
- src/talk_reasoner/__main__.py -> python -m talk_reasoner CLI entry point
  spec: Delegate to main(argv) without adding runtime behavior.
- tests/test_rendering_cli.py -> renderer and visible-outcome tests
  source: covers all routes/terminal states, forbidden-content filtering, confirmation copy, stdout/stderr separation, exit codes, and no reasoner wakeup on fast paths.

CONSUMES:
- TRS-0daa: src/talk_reasoner/contracts.py -> load_fixture(path: pathlib.Path) -> Fixture
  spec: Load one strictly validated fixture for the CLI; do not accept ad hoc raw input.
- TRS-0daa: src/talk_reasoner/contracts.py -> verify_ledger(ledger: EventLedger) -> LedgerVerification
  spec: Fail the CLI when the fixture-to-response chain is invalid or incomplete.
- TRS-74z8: src/talk_reasoner/routing.py -> classify(fixture: Fixture, *, policy: ThresholdPolicy) -> RoutingDecision
  spec: Choose chitchat, needs_tools, or unclear and provide route metadata without waking the reasoner on fast paths.
- TRS-9md6: src/talk_reasoner/actions.py -> preflight_policy(action: ValidatedAction, *, policy: PolicyDefinition, confirmation: ConfirmationRecord | None = None) -> PolicyDecision
  spec: Supply the exact policy outcome/rejection reason used to select clean confirmation, refusal, or failure copy.
- TRS-ndv6: src/talk_reasoner/jobs.py -> job_terminal_summary(job: ReasonerJob) -> TerminalOutcome
  spec: Supply only a legal terminal state/reason/priority/provenance for rendering; canceled output cannot be marked as a normal result.

## Acceptance Requirements

1. `render_response` emits exactly one response for each route and terminal
   state: chitchat, unclear, completed, waiting_confirmation, canceled,
   downgraded, and failed.
2. `chitchat` returns an immediate short reply; `unclear` asks one useful
   clarification; neither invokes the reasoner transport.
3. `needs_tools` permits at most one short filler before terminal output; the
   rendered result is concise, truthful, non-empty when required, and ordered by
   user relevance.
4. Confirmation copy states action and target, human-readable arguments,
   one-time scope, consequence/irreversibility, and explicit affirmative and
   safe negative choices.
5. Canceled work never interrupts as a normal result. Downgrade is bounded to a
   non-action summary or resume offer. Failure is honest, non-technical, and
   offers exactly one safe recovery action without inventing tool output.
6. Renderer tests prove forbidden schemas, raw model output, stack traces,
   credentials, tool logs, hidden prompts, private unrelated context, and event
   internals cannot reach stdout.
7. Every rendered response carries stable response ID, channel, priority, turn
   epoch, latency, and provenance metadata without raw prompt/audio.
8. The CLI prints only clean user-facing text to stdout and compact JSON run
   evidence to stderr; evidence includes fixture/route/policy/catalog/threshold
   versions, terminal state, event-chain result, and timing, not transcript text.
9. The CLI exits `0` for normal terminal outcomes and `2` for fail-closed
   usage, invalid fixture, policy, ledger, or renderer errors.

## Testing Requirements

- Unit tests: renderer state coverage, forbidden-content rejection, metadata
  shape, confirmation wording, and empty/ambiguous outcome failure.
- Integration tests: MANDATORY (no test mocks). Invoke the CLI with all route
   and terminal fixture cases through LocalScriptedTransport and the real local
   routing/action/job components; capture stdout/stderr and exit status.
- E2E tests: not in this story; the blocked capstone owns complete user journeys.
- Commands: `python -m pytest tests/test_rendering_cli.py`.

## MANDATORY SKILLS

- `project-standards`: typed CLI and renderer boundary discipline.
- `pvg`: story governance and delivery evidence only.

## Delivery Requirements

- Paste exact pytest output and exit status.
- Include captured stdout/stderr for one chitchat, one unclear, and one
  needs-tools terminal fixture, with private/raw content redacted if necessary.
- Include an AC verification table with file/test evidence.
- Update the authoritative `nd_contract` using the pvg delivery workflow.

## nd_contract

status: new

### evidence

- Created: 2026-09-19
- Depends on contracts from TRS-0daa, TRS-74z8, TRS-9md6, and TRS-ndv6.

### proof

- [ ] Pending implementation


## Acceptance Criteria


## Design


## Notes


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-19.

### proof
- [x] Story closed after accepted label was applied.


## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/talker-reasoner-system/.claude/worktrees/dev-TRS-f7sm
git diff --check
/opt/homebrew/bin/python -m compileall -q src tests
/opt/homebrew/bin/pytest -q tests/test_rendering_cli.py
/opt/homebrew/bin/pytest -q
pvg verify src/talk_reasoner/rendering.py src/talk_reasoner/cli.py src/talk_reasoner/__main__.py tests/test_rendering_cli.py --format=text
PYTHONPATH=src /opt/homebrew/bin/python -m talk_reasoner tests/fixtures/slice0/trs-chitchat-001.json
PYTHONPATH=src /opt/homebrew/bin/python -m talk_reasoner tests/fixtures/slice0/trs-unclear-001.json
PYTHONPATH=src /opt/homebrew/bin/python -m talk_reasoner tests/fixtures/slice0/trs-tools-001.json
```

Independent coordinator results:

- `git diff --check`: exit 0.
- Compilation: exit 0.
- Story tests: 44/44 passed.
- Full suite: 154/154 passed.
- `pvg verify`: passed with 4 files scanned and zero issues.
- Real CLI probes:
  - chitchat exit 0 and clean stdout;
  - unclear exit 0 and one clarification;
  - needs-tools exit 0 with one filler plus exact scoped confirmation;
  - invalid fixture exit 2.
- Privacy scan across captured stdout/stderr found no transcript, raw prompt, credential, password, API key, or traceback leakage.
- Diff budget: 395 changed LOC, below 425.

### CI/Test Results

```text
tests/test_rendering_cli.py: 44 passed
full suite: 154 passed
pvg verify: PASSED (4 files scanned, 0 issues)
real CLI invalid-fixture exit: 2
```

Summary: implemented clean response rendering for every Slice-0 terminal state, exact confirmation copy, bounded cancellation/downgrade/failure behavior, forbidden-content rejection, privacy-safe evidence, stdout/stderr separation, module entrypoint, and fail-closed CLI exit codes.

Commit SHA: 8057ef2

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Every render state covered cleanly | PASS | Renderer state test. |
| 2. Fast paths do not wake reasoner | PASS | Transport call-count test. |
| 3. At most one filler and concise terminal output | PASS | Slow-path CLI tests. |
| 4. Confirmation names exact scope/consequences/choices | PASS | Real needs-tools probe and test. |
| 5. Cancel/downgrade/failure copy is bounded and safe | PASS | Renderer tests. |
| 6. Forbidden content rejected | PASS | Ten-case forbidden-content test. |
| 7. Stable response metadata/provenance | PASS | Renderer and CLI evidence assertions. |
| 8. stdout clean; stderr compact privacy-safe JSON | PASS | All fixture CLI tests and independent scan. |
| 9. Exit 0 normal, exit 2 fail-closed | PASS | Real CLI probes. |


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-19T05:29:38Z dep_added: blocked_by TRS-74z8
- 2026-09-19T05:29:38Z dep_added: blocked_by TRS-9md6
- 2026-09-19T05:29:38Z dep_added: blocked_by TRS-ndv6
- 2026-09-19T05:29:39Z dep_added: blocks TRS-osl5
- 2026-09-19T14:14:39Z dep_removed: was_blocked_by TRS-74z8
- 2026-09-19T15:55:45Z dep_removed: was_blocked_by TRS-9md6
- 2026-09-19T16:31:14Z dep_removed: was_blocked_by TRS-ndv6
- 2026-09-19T16:31:37Z status: open -> in_progress
- 2026-09-19T16:31:37Z auto-follows: linked to predecessor TRS-74z8
- 2026-09-19T16:31:37Z auto-follows: linked to predecessor TRS-9md6
- 2026-09-19T16:31:37Z auto-follows: linked to predecessor TRS-ndv6
- 2026-09-19T16:31:37Z claimed by dev-TRS-f7sm
- 2026-09-19T16:56:27Z status: in_progress -> in_progress
- 2026-09-19T16:56:27Z auto-follows: linked to predecessor TRS-0daa
- 2026-09-19T16:57:44Z status: in_progress -> closed
- 2026-09-19T16:57:44Z dep_removed: no_longer_blocks TRS-osl5

## Links
- Parent: [[TRS-pf94]]
- Was blocked by: [[TRS-74z8]], [[TRS-9md6]], [[TRS-ndv6]]
- Follows: [[TRS-74z8]], [[TRS-9md6]], [[TRS-ndv6]], [[TRS-0daa]]

## Comments
