from __future__ import annotations

import json
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from talk_reasoner.contracts import load_fixture, scoped_hash
from talk_reasoner.jobs import Cancel, TurnAdvanced, advance_reasoner_job, job_terminal_summary
from talk_reasoner.machinery import parse_oracle
from talk_reasoner.rendering import PresentationConstraints, render_response
from talk_reasoner.routing import classify, load_threshold_policy


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from test_jobs import JOB_ID, TransportClock, waiting_job  # noqa: E402


SLOW_FIXTURE = load_fixture(ROOT / "tests/fixtures/slice0/trs-tools-001.json")
FAST_FIXTURE = load_fixture(ROOT / "tests/fixtures/slice0/trs-chitchat-001.json")
POLICY = load_threshold_policy(ROOT / "config/routing/slice0-v1.json")
SLOW_DECISION = classify(SLOW_FIXTURE, policy=POLICY)
FAST_DECISION = classify(FAST_FIXTURE, policy=POLICY)
ACTION_HASH = waiting_job().validated_actions[0].action_hash
CITED_ROWS = frozenset({
    "CONV-f9f25b", "CONV-87aef6", "CONV-53ecad", "CONV-5d0019", "CONV-a756c5",
    "CONV-7c39be", "CONV-7f7105", "CONV-8fadcf", "CONV-04c2c7",
})


def _route(decision: object) -> dict[str, object]:
    return {
        "selectedLabel": getattr(decision, "selected_label"),
        "route": getattr(decision, "route"),
        "confidence": getattr(decision, "confidence"),
        "risk": getattr(decision, "risk"),
        "thresholdsVersion": getattr(decision, "thresholds_version"),
        "policyHash": getattr(decision, "policy_hash"),
        "inputHash": getattr(decision, "input_hash"),
        "fallbackReason": getattr(decision, "fallback_reason"),
    }


def _driver_input() -> dict[str, object]:
    return {
        "jobId": JOB_ID,
        "actionHash": ACTION_HASH,
        "slow": {
            "sessionId": SLOW_FIXTURE.session_id,
            "turnId": SLOW_FIXTURE.turn_id,
            "transcript": SLOW_FIXTURE.transcript,
            "schemaVersion": SLOW_FIXTURE.schema_version,
            "route": _route(SLOW_DECISION),
            "inputHash": scoped_hash(
                SLOW_FIXTURE.transcript,
                scope="fixture-input",
                schema_version=SLOW_FIXTURE.schema_version,
            ),
        },
        "fast": {
            "sessionId": FAST_FIXTURE.session_id,
            "turnId": FAST_FIXTURE.turn_id,
            "transcript": FAST_FIXTURE.transcript,
            "schemaVersion": FAST_FIXTURE.schema_version,
            "route": _route(FAST_DECISION),
            "inputHash": scoped_hash(
                FAST_FIXTURE.transcript,
                scope="fixture-input",
                schema_version=FAST_FIXTURE.schema_version,
            ),
        },
    }


DRIVER = r'''
import type { ProcessingBoundary } from "../ports/audio.js";
import type { RouteDecision } from "../state/ConversationTurn.js";
import { ConversationTurn } from "../state/ConversationTurn.js";

const input = JSON.parse(__INPUT_JSON__) as Record<string, any>;
const boundary: ProcessingBoundary = "localOnly";

function attempt(operation: () => unknown): { threw: boolean } {
  try { operation(); return { threw: false }; } catch { return { threw: true }; }
}

function open(name: "slow" | "fast", epoch = 0): ConversationTurn {
  const fixture = input[name];
  return ConversationTurn.open({
    sessionId: fixture.sessionId,
    turnId: fixture.turnId,
    turnEpoch: epoch,
    processingBoundary: boundary,
  });
}

function routed(name: "slow" | "fast"): ConversationTurn {
  const fixture = input[name];
  return open(name).transcribe({
    transcript: fixture.transcript,
    processingBoundary: boundary,
    cloudConsent: false,
    schemaVersion: fixture.schemaVersion,
  });
}

function snapshot(value: ConversationTurn): Record<string, unknown> {
  return value.snapshot as unknown as Record<string, unknown>;
}

function invalidRoute(change: Record<string, unknown>) {
  const turn = routed("slow");
  const decision = { ...input.slow.route, ...change } as RouteDecision;
  return { before: snapshot(turn), route: attempt(() => turn.route({ decision })), after: snapshot(turn) };
}

const receivingCancel = open("slow").cancel({ jobId: input.jobId });
const routedCancel = routed("slow").cancel({ jobId: input.jobId });
const slow = routed("slow").route({ decision: input.slow.route });
const slowCancel = slow.cancel({ jobId: input.jobId });
const slowAdvanced = slow.advanceEpoch({ jobId: input.jobId, turnEpoch: 1 });
const awaiting = slow.awaitConfirmation({
  policyOutcome: "confirmation_required",
  actionHash: input.actionHash,
});
const awaitingCancel = awaiting.cancel({ jobId: input.jobId });
const awaitingAdvanced = awaiting.advanceEpoch({ jobId: input.jobId, turnEpoch: 1 });
const responding = routed("fast").route({ decision: input.fast.route });
const respondingCancel = responding.cancel({ jobId: null });
const finishAfterCancel = attempt(() => respondingCancel.finish({
  response: {
    responseId: "response-after-cancel", text: "must not render", channel: "text",
    priority: 1, turnEpoch: 1, latencyMs: 0, provenance: { source: "synthetic-local" },
  },
}));

console.log(JSON.stringify({
  receivingCancel: snapshot(receivingCancel),
  routedCancel: snapshot(routedCancel),
  slow: snapshot(slow),
  slowCancel: snapshot(slowCancel),
  slowAdvanced: snapshot(slowAdvanced),
  awaiting: snapshot(awaiting),
  awaitingCancel: snapshot(awaitingCancel),
  awaitingAdvanced: snapshot(awaitingAdvanced),
  respondingCancel: snapshot(respondingCancel),
  finishAfterCancel,
  routeGuards: {
    routeNotNeedsTools: invalidRoute({ route: "chitchat" }),
    selectedLabelMismatch: invalidRoute({ selectedLabel: "chitchat" }),
    confidenceOutOfRange: invalidRoute({ confidence: 2 }),
    riskInvalid: invalidRoute({ risk: "unknown" }),
    thresholdsVersionDrift: invalidRoute({ thresholdsVersion: "slice0-v2" }),
    policyHashInvalid: invalidRoute({ policyHash: "0".repeat(64) }),
    inputHashMismatch: invalidRoute({ inputHash: "0".repeat(64) }),
  },
  confirmationGuards: {
    policyNotRequired: (() => {
      const turn = routed("slow").route({ decision: input.slow.route });
      return {
        before: snapshot(turn),
        await: attempt(() => turn.awaitConfirmation({
          policyOutcome: "allowed_without_confirmation", actionHash: input.actionHash,
        })),
        after: snapshot(turn),
      };
    })(),
    actionHashMissing: (() => {
      const turn = routed("slow").route({ decision: input.slow.route });
      return {
        before: snapshot(turn),
        await: attempt(() => turn.awaitConfirmation({
          policyOutcome: "confirmation_required", actionHash: null,
        })),
        after: snapshot(turn),
      };
    })(),
  },
}));
'''


@lru_cache(maxsize=1)
def _behavior() -> dict[str, object]:
    scratch = ROOT / "edge" / ".voice-turn-red"
    if scratch.exists():
        shutil.rmtree(scratch)
    source = scratch / "driver.ts"
    output = scratch / "compiled"
    source.parent.mkdir(parents=True)
    encoded_input = json.dumps(json.dumps(_driver_input(), sort_keys=True), sort_keys=True)
    source.write_text(DRIVER.replace("__INPUT_JSON__", encoded_input), encoding="utf-8")
    try:
        compiled = subprocess.run(
            [
                "tsc", "driver.ts", "--outDir", str(output), "--target", "es2022",
                "--module", "nodenext", "--moduleResolution", "nodenext", "--strict", "--skipLibCheck",
            ],
            cwd=scratch, text=True, capture_output=True, timeout=60, check=False,
        )
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr
        executable = output / ".voice-turn-red" / "driver.js"
        run = subprocess.run(
            ["node", str(executable)], cwd=ROOT / "edge", text=True,
            capture_output=True, timeout=30, check=False,
        )
        assert run.returncode == 0, run.stdout + run.stderr
        value: object = json.loads(run.stdout)
        assert isinstance(value, dict)
        return value
    finally:
        shutil.rmtree(scratch)


def _snapshot(name: str) -> dict[str, object]:
    value = _behavior()[name]
    assert isinstance(value, dict)
    return value


def _assert_terminal(value: dict[str, object], *, epoch: int, reason: str, stimulus: str) -> None:
    assert value["status"] == "Terminal" and value["turnEpoch"] == epoch
    assert value["ephemeralTranscript"] is None and value["boundResponse"] is None
    assert value["terminalReason"] == reason
    assert value["cancellationIntent"] == {
        "jobId": JOB_ID, "stimulus": stimulus, "turnEpoch": epoch,
    }


def test_red_cites_exactly_the_remaining_conversation_turn_rows() -> None:
    rows = parse_oracle(ROOT / "design/machines/ConversationTurn.oracle.md")
    assert {row.stable_id for row in rows if row.stable_id in CITED_ROWS} == CITED_ROWS


def test_conv_f9f25b_receiving_cancel_terminalizes_before_routing() -> None:
    value = _snapshot("receivingCancel")
    _assert_terminal(value, epoch=1, reason="canceled_by_user", stimulus="cancel")
    assert value["inputHash"] is None and value["boundRoute"] is None


def test_conv_87aef6_only_valid_needs_tools_route_enters_slow_path() -> None:
    value = _snapshot("slow")
    assert value["status"] == "SlowPath" and value["ephemeralTranscript"] == SLOW_FIXTURE.transcript
    assert value["inputHash"] == SLOW_DECISION.input_hash
    assert value["boundRoute"] == _route(SLOW_DECISION)


def test_conv_53ecad_routed_cancel_releases_transcript_and_cancels_work() -> None:
    value = _snapshot("routedCancel")
    _assert_terminal(value, epoch=1, reason="canceled_by_user", stimulus="cancel")
    assert value["inputHash"] == SLOW_DECISION.input_hash


def test_conv_5d0019_slow_path_epoch_advance_supersedes_old_work() -> None:
    _assert_terminal(
        _snapshot("slowAdvanced"), epoch=1, reason="turn_superseded", stimulus="turnAdvanced",
    )


def test_conv_a756c5_exact_policy_confirmation_enters_awaiting_confirmation() -> None:
    value = _snapshot("awaiting")
    assert value["status"] == "AwaitingConfirmation"
    assert value["awaitingActionHash"] == ACTION_HASH
    assert value["ephemeralTranscript"] == SLOW_FIXTURE.transcript


def test_conv_7c39be_slow_path_cancel_terminalizes_and_cancels_work() -> None:
    _assert_terminal(_snapshot("slowCancel"), epoch=1, reason="canceled_by_user", stimulus="cancel")


def test_conv_7f7105_awaiting_epoch_advance_supersedes_old_work() -> None:
    _assert_terminal(
        _snapshot("awaitingAdvanced"), epoch=1, reason="turn_superseded", stimulus="turnAdvanced",
    )


def test_conv_8fadcf_awaiting_cancel_terminalizes_and_cancels_work() -> None:
    _assert_terminal(_snapshot("awaitingCancel"), epoch=1, reason="canceled_by_user", stimulus="cancel")


def test_conv_04c2c7_responding_cancel_blocks_normal_rendering() -> None:
    behavior = _behavior()
    value = _snapshot("respondingCancel")
    assert value["status"] == "Terminal" and value["ephemeralTranscript"] is None
    assert value["terminalReason"] == "canceled_by_user"
    assert behavior["finishAfterCancel"] == {"threw": True}
    assert value["boundResponse"] is None


def test_route_guard_falsifies_each_needs_tools_clause() -> None:
    guards = _behavior()["routeGuards"]
    assert isinstance(guards, dict)
    for case in guards.values():
        assert isinstance(case, dict)
        assert case["before"]["status"] == "Routed"
        assert case["route"] == {"threw": True}
        assert case["after"]["status"] == "Routed" and case["after"]["boundRoute"] is None


def test_confirmation_guard_falsifies_policy_and_action_hash_clauses() -> None:
    guards = _behavior()["confirmationGuards"]
    assert isinstance(guards, dict)
    for case in guards.values():
        assert isinstance(case, dict)
        assert case["before"]["status"] == "SlowPath"
        assert case["await"] == {"threw": True}
        assert case["after"]["status"] == "SlowPath" and case["after"]["awaitingActionHash"] is None


def test_terminal_paths_release_raw_transcript_and_retain_only_scoped_values() -> None:
    names = (
        "receivingCancel", "routedCancel", "slowCancel", "slowAdvanced",
        "awaitingCancel", "awaitingAdvanced", "respondingCancel",
    )
    evidence = json.dumps([_snapshot(name) for name in names], sort_keys=True)
    assert SLOW_FIXTURE.transcript not in evidence and FAST_FIXTURE.transcript not in evidence
    assert "afternoon meetings" not in evidence and "candidate_answer" not in evidence
    assert SLOW_DECISION.input_hash in evidence and FAST_DECISION.input_hash in evidence


def test_local_reasoner_cancel_and_epoch_stimuli_remain_silent() -> None:
    canceled = advance_reasoner_job(waiting_job(), Cancel(), clock=TransportClock())
    superseded = advance_reasoner_job(waiting_job(), TurnAdvanced(1), clock=TransportClock())
    assert (canceled.state, canceled.terminal_reason) == ("canceled", "canceled_by_user")
    assert (superseded.state, superseded.terminal_reason) == ("canceled", "turn_superseded")
    for job in (canceled, superseded):
        outcome = job_terminal_summary(job)
        assert outcome.normal_result_allowed is False
        assert render_response(
            outcome, constraints=PresentationConstraints("response-canceled"),
        ).text == ""
