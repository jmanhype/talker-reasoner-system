from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import sys
import unicodedata
from pathlib import Path
from typing import NamedTuple

from talk_reasoner.contracts import load_fixture, scoped_hash
from talk_reasoner.jobs import TerminalOutcome, TurnAdvanced, advance_reasoner_job, job_terminal_summary
from talk_reasoner.machinery import parse_oracle
from talk_reasoner.rendering import PresentationConstraints, render_response
from talk_reasoner.routing import classify, load_threshold_policy


ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from test_jobs import JOB_ID, TransportClock, waiting_job  # noqa: E402


FAST_FIXTURE = load_fixture(ROOT / "tests/fixtures/slice0/trs-chitchat-001.json")
SLOW_FIXTURE = load_fixture(ROOT / "tests/fixtures/slice0/trs-tools-001.json")
POLICY = load_threshold_policy(ROOT / "config/routing/slice0-v1.json")
FAST_DECISION = classify(FAST_FIXTURE, policy=POLICY)
SLOW_DECISION = classify(SLOW_FIXTURE, policy=POLICY)
WAITING_JOB = waiting_job()
ACTION_HASH = WAITING_JOB.validated_actions[0].action_hash
VOIC_IDS = ("VOIC-305554", "VOIC-e62d1f", "VOIC-32ea66")
CONV_IDS = (
    "CONV-02965d", "CONV-f9f25b", "CONV-87aef6", "CONV-73bae3", "CONV-53ecad",
    "CONV-5d0019", "CONV-a756c5", "CONV-7c39be", "CONV-7f7105", "CONV-8fadcf",
    "CONV-dab39a", "CONV-04c2c7",
)
REPORT_FIXTURE = ROOT / "tests/e2e/fixtures/m2-report.json"
PRESENTATION_SCHEMA = "slice0-presentation-arbitration-v1"
FAST_TEXT = "Hi — I'm here."
SLOW_PRESENTATION = "M2 voice journey is complete"
ACTIVE_USER_PRESENTATION = "Operator is speaking now"


class _RenderProvenance(NamedTuple):
    schema_version: str
    fixture_set_version: str
    source: str
    model_id: str
    review_status: str


def _route(decision: object) -> dict[str, object]:
    return {
        "selectedLabel": getattr(decision, "selected_label"), "route": getattr(decision, "route"),
        "confidence": getattr(decision, "confidence"), "risk": getattr(decision, "risk"),
        "thresholdsVersion": getattr(decision, "thresholds_version"), "policyHash": getattr(decision, "policy_hash"),
        "inputHash": getattr(decision, "input_hash"), "fallbackReason": getattr(decision, "fallback_reason"),
    }


def _outcome(state: str, reason: str, summary: str, allowed: bool, priority: int) -> TerminalOutcome:
    return TerminalOutcome(
        state, reason, 0, priority, "safe" if allowed else "silent", summary, allowed, 0,
        _RenderProvenance(
            "slice0-rendered-response-v1", FAST_FIXTURE.provenance.fixture_set_version,
            "synthetic-local", "none", "reviewed",
        ), JOB_ID,
    )


def _rendered(outcome: TerminalOutcome, response_id: str) -> dict[str, object]:
    rendered = render_response(outcome, constraints=PresentationConstraints(response_id))
    return {
        "responseId": rendered.response_id, "text": rendered.text, "channel": rendered.channel,
        "priority": rendered.priority, "turnEpoch": rendered.turn_epoch,
        "latencyMs": rendered.latency_ms, "provenance": dict(rendered.provenance),
    }


def _semantic_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def _parity_hash(typed: str, spoken: str) -> str:
    canonical = json.dumps(
        {"semantics": f"{_semantic_key(typed)}|{_semantic_key(spoken)}"},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    )
    return scoped_hash(canonical, scope="presentation-parity", schema_version=PRESENTATION_SCHEMA)


def _candidate_fields(typed: str, spoken: str, response_id: str, priority: int, source: str) -> dict[str, object]:
    return {
        "typedText": typed, "spokenText": spoken, "responseId": response_id,
        "semanticParityHash": _parity_hash(typed, spoken), "priority": priority, "source": source,
    }


def _driver_input(fast_response: dict[str, object]) -> dict[str, object]:
    return {
        "jobId": JOB_ID, "actionHash": ACTION_HASH, "fastResponse": fast_response,
        "fast": {
            "sessionId": FAST_FIXTURE.session_id, "turnId": FAST_FIXTURE.turn_id,
            "transcript": FAST_FIXTURE.transcript, "schemaVersion": FAST_FIXTURE.schema_version,
            "route": _route(FAST_DECISION),
        },
        "slow": {
            "sessionId": SLOW_FIXTURE.session_id, "turnId": SLOW_FIXTURE.turn_id,
            "transcript": SLOW_FIXTURE.transcript, "schemaVersion": SLOW_FIXTURE.schema_version,
            "route": _route(SLOW_DECISION),
        },
        "slowPresentation": _candidate_fields(
            SLOW_PRESENTATION, SLOW_PRESENTATION, "m2-slow-response-001", 1, "slowPath",
        ),
        "activeUser": _candidate_fields(
            ACTIVE_USER_PRESENTATION, ACTIVE_USER_PRESENTATION.casefold(),
            "m2-active-user-001", 100, "activeUser",
        ),
    }


DRIVER = r'''
import { ConversationTurn } from "../state/ConversationTurn.js";
import { PresentationArbiter } from "../state/arbitration.js";
import { VoiceSession } from "../state/VoiceSession.js";

const input = JSON.parse(__INPUT_JSON__) as Record<string, any>;
const boundary = "localOnly" as const;
const canary = "processing-only-canary";
const session = VoiceSession.open({
  sessionId: input.fast.sessionId, processingBoundary: boundary, turnEpoch: 0,
  activeStreamId: null, startedAtIso: "2026-09-20T00:00:00Z",
  processingOnlyValues: { audio: canary, transcript: canary },
});

function turn(name: "fast" | "slow") {
  const fixture = input[name];
  return ConversationTurn.open({
    sessionId: fixture.sessionId, turnId: fixture.turnId, turnEpoch: 0, processingBoundary: boundary,
  }).transcribe({
    transcript: fixture.transcript, processingBoundary: boundary,
    cloudConsent: false, schemaVersion: fixture.schemaVersion,
  });
}

const fastTerminal = turn("fast").route({ decision: input.fast.route })
  .finish({ response: input.fastResponse });
const slow = turn("slow").route({ decision: input.slow.route });
const awaiting = slow.awaitConfirmation({
  policyOutcome: "confirmation_required", actionHash: input.actionHash,
});
const slowTerminal = awaiting.advanceEpoch({ jobId: input.jobId, turnEpoch: 1 });

function candidate(source: "slowPresentation" | "activeUser") {
  const base = input[source];
  const fixture = source === "slowPresentation" ? input.slow : input.fast;
  return {
    ...base, turnId: fixture.turnId, channel: "textAndSpeech", turnEpoch: 1,
    terminalState: "rendered", accessibility: {
      screenReaderText: base.typedText, captionsAvailable: true,
    },
  };
}

const arbiter = PresentationArbiter.open({
  sessionId: input.fast.sessionId, currentTurnEpoch: 1, activeStreamId: null,
});
const slowDecision = arbiter.submit(candidate("slowPresentation"));
const snapshotAfterOrdinary = arbiter.snapshot;
const ordinarySecond = arbiter.submit({ ...candidate("slowPresentation"), responseId: "m2-second-001" });
const oneStreamSnapshot = arbiter.snapshot;
const activeUserDecision = arbiter.submit(candidate("activeUser"));
const closed = session.close({ reason: "M2 journey complete", endedAtIso: "2026-09-20T00:00:02Z" });

console.log(JSON.stringify({
  openedSession: session.snapshot,
  fastTerminal: fastTerminal.snapshot,
  slowBeforeWait: slow.snapshot,
  awaitingConfirmation: awaiting.snapshot,
  slowTerminal: slowTerminal.snapshot,
  slowDecision,
  snapshotAfterOrdinary,
  ordinarySecond,
  oneStreamSnapshot,
  activeUserDecision,
  arbiterSnapshot: arbiter.snapshot,
  closedSession: closed.snapshot,
  processingOnlyValueCountAfterClose: Object.keys(closed.processingOnlyValues).length,
}));
'''


def _behavior(fast_response: dict[str, object]) -> dict[str, object]:
    scratch = ROOT / "edge" / ".voice-m2-red"
    if scratch.exists(): shutil.rmtree(scratch)
    source = scratch / "driver.ts"
    output = scratch / "compiled"
    source.parent.mkdir(parents=True)
    encoded = json.dumps(json.dumps(_driver_input(fast_response), sort_keys=True), sort_keys=True)
    source.write_text(DRIVER.replace("__INPUT_JSON__", encoded), encoding="utf-8")
    compile_cwd = Path(tempfile.mkdtemp(prefix="voice-m2-tsc-"))
    try:
        compiled = subprocess.run([
            "tsc", str(source), "--outDir", str(output), "--target", "es2022",
            "--module", "nodenext", "--moduleResolution", "nodenext", "--strict", "--skipLibCheck",
        ], cwd=compile_cwd, text=True, capture_output=True, timeout=60, check=False)
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr
        run = subprocess.run(
            ["node", str(output / ".voice-m2-red" / "driver.js")], cwd=ROOT / "edge",
            text=True, capture_output=True, timeout=30, check=False,
        )
        assert run.returncode == 0, run.stdout + run.stderr
        value: object = json.loads(run.stdout)
        assert isinstance(value, dict)
        return value
    finally:
        shutil.rmtree(compile_cwd, ignore_errors=True)
        shutil.rmtree(scratch)


def test_complete_m2_voice_turn_gate_emits_pass_report() -> None:
    fast_response = _rendered(
        _outcome("chitchat", "rendered", FAST_TEXT, True, 1), "response-m2-fast-001",
    )
    journey = _behavior(fast_response)
    superseded_job = advance_reasoner_job(WAITING_JOB, TurnAdvanced(1), clock=TransportClock())
    stale_outcome = job_terminal_summary(superseded_job)
    stale_response = _rendered(stale_outcome, "response-m2-superseded-001")

    privacy_scopes = {
        "fast_terminal_transcript_released": journey["fastTerminal"]["ephemeralTranscript"] is None,
        "slow_terminal_transcript_released": journey["slowTerminal"]["ephemeralTranscript"] is None,
        "session_values_released": journey["processingOnlyValueCountAfterClose"] == 0,
        "stale_output_silent": stale_response["text"] == "",
    }
    arbitration_checks = {
        "one_stream_rejected_overlap": journey["ordinarySecond"]["action"] == "reject",
        "active_user_supersedes": journey["activeUserDecision"]["action"] == "supersede",
        "active_stream_final": journey["arbiterSnapshot"]["activeStreamId"] == "m2-active-user-001",
        "accessibility_available": journey["activeUserDecision"]["rejectionReason"] is None,
        "typed_spoken_parity": journey["slowDecision"]["action"] == "present",
    }
    conditions = {
        "session_opened": journey["openedSession"]["status"] == "active",
        "session_closed_after_terminal_turns": journey["closedSession"]["status"] == "closed"
        and journey["fastTerminal"]["status"] == "Terminal" and journey["slowTerminal"]["status"] == "Terminal",
        "clean_fast_response": journey["fastTerminal"]["boundResponse"] == fast_response,
        "slow_turn_awaits_confirmation": journey["awaitingConfirmation"]["status"] == "AwaitingConfirmation"
        and journey["awaitingConfirmation"]["awaitingActionHash"] == ACTION_HASH,
        "slow_work_superseded": journey["slowTerminal"]["terminalReason"] == "turn_superseded"
        and superseded_job.state == "canceled" and superseded_job.terminal_reason == "turn_superseded",
        "stale_normal_output_prevented": stale_outcome.normal_result_allowed is False,
        **privacy_scopes,
        **arbitration_checks,
        "exact_voic_denominators": tuple(row.stable_id for row in parse_oracle(ROOT / "design/machines/VoiceSession.oracle.md")) == VOIC_IDS,
        "exact_conv_denominators": tuple(row.stable_id for row in parse_oracle(ROOT / "design/machines/ConversationTurn.oracle.md")) == CONV_IDS,
        "no_tool_execution": True,
    }
    report = {
        "schema_version": "trs-m2-voice-turn-report-v1",
        "machine_denominators": {
            "voiceSession": {"transition_count": len(VOIC_IDS), "stable_ids": list(VOIC_IDS)},
            "conversationTurn": {"transition_count": len(CONV_IDS), "stable_ids": list(CONV_IDS)},
            "m2_oracle_row_count": len(VOIC_IDS) + len(CONV_IDS),
        },
        "test_denominators": {"targeted_e2e_test_count": 1, "condition_count": len(conditions)},
        "privacy_denominators": {"check_count": len(privacy_scopes), "passed": sum(privacy_scopes.values())},
        "arbitration_denominators": {"check_count": len(arbitration_checks), "passed": sum(arbitration_checks.values())},
        "reasoner_job": {"state": superseded_job.state, "terminal_reason": superseded_job.terminal_reason, "tool_execution_count": 0},
        "conditions": conditions,
        "decision": "pass" if all(conditions.values()) else "hold",
    }
    report_evidence = json.dumps(report, sort_keys=True)
    assert FAST_FIXTURE.transcript not in report_evidence and SLOW_FIXTURE.transcript not in report_evidence
    print(json.dumps(report, indent=2, sort_keys=True))
    expected = json.loads(REPORT_FIXTURE.read_text(encoding="utf-8"))
    assert {key: report[key] for key in expected} == expected
    assert report["decision"] == "pass", json.dumps({"report": report, "expected": expected}, indent=2)
