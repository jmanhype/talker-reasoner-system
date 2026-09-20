from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import NamedTuple

from talk_reasoner.contracts import load_fixture, scoped_hash
from talk_reasoner.jobs import TerminalOutcome
from talk_reasoner.rendering import PresentationConstraints, render_response
from talk_reasoner.routing import classify, load_threshold_policy


ROOT = Path(__file__).parents[1]
FIXTURE = load_fixture(ROOT / "tests/fixtures/slice0/trs-chitchat-001.json")
POLICY = load_threshold_policy(ROOT / "config/routing/slice0-v1.json")
DECISION = classify(FIXTURE, policy=POLICY)
EXPECTED_INPUT_HASH = scoped_hash(
    FIXTURE.transcript, scope="fixture-input", schema_version=FIXTURE.schema_version
)


class _RenderProvenance(NamedTuple):
    schema_version: str
    fixture_set_version: str
    source: str
    model_id: str
    review_status: str


def _rendered_response() -> dict[str, object]:
    outcome = TerminalOutcome(
        "chitchat",
        "rendered",
        0,
        1,
        "safe",
        "Hi — I'm here.",
        True,
        0,
        _RenderProvenance(
            "slice0-rendered-response-v1",
            FIXTURE.provenance.fixture_set_version,
            "synthetic-local",
            "none",
            "reviewed",
        ),
        "no-tool-turn",
    )
    rendered = render_response(
        outcome,
        constraints=PresentationConstraints("response-voice-turn-001"),
    )
    return {
        "responseId": rendered.response_id,
        "text": rendered.text,
        "channel": rendered.channel,
        "priority": rendered.priority,
        "turnEpoch": rendered.turn_epoch,
        "latencyMs": rendered.latency_ms,
        "provenance": dict(rendered.provenance),
    }


def _driver_input() -> dict[str, object]:
    return {
        "sessionId": FIXTURE.session_id,
        "turnId": FIXTURE.turn_id,
        "startedAtIso": "2026-09-20T00:00:00Z",
        "endedAtIso": "2026-09-20T00:00:01Z",
        "schemaVersion": FIXTURE.schema_version,
        "transcript": FIXTURE.transcript,
        "expectedInputHash": EXPECTED_INPUT_HASH,
        "route": {
            "selectedLabel": DECISION.selected_label,
            "route": DECISION.route,
            "confidence": DECISION.confidence,
            "risk": DECISION.risk,
            "thresholdsVersion": DECISION.thresholds_version,
            "policyHash": DECISION.policy_hash,
            "inputHash": DECISION.input_hash,
            "fallbackReason": DECISION.fallback_reason,
        },
        "response": _rendered_response(),
    }


DRIVER = r'''
import type { ProcessingBoundary } from "../ports/audio.js";
import { VoiceSession } from "../state/VoiceSession.js";
import { ConversationTurn } from "../state/ConversationTurn.js";

const input = JSON.parse(__INPUT_JSON__) as Record<string, any>;

function attempt(operation: () => unknown): { threw: boolean } {
  try { operation(); return { threw: false }; } catch { return { threw: true }; }
}

const boundary: ProcessingBoundary = "localOnly";
const canary = "processing-only-canary";
const active = VoiceSession.open({
  sessionId: input.sessionId,
  processingBoundary: boundary,
  turnEpoch: 0,
  activeStreamId: null,
  startedAtIso: input.startedAtIso,
  processingOnlyValues: { audio: canary, transcript: canary },
});
const duplicateStart = active.start();
const degraded = active.degrade({ reason: "local dependency unavailable" });
const closedFromActive = active.close({ reason: "operator ended", endedAtIso: input.endedAtIso });
const closedFromDegraded = degraded.close({ reason: "operator ended", endedAtIso: input.endedAtIso });

const turn = ConversationTurn.open({
  sessionId: input.sessionId,
  turnId: input.turnId,
  turnEpoch: 0,
  processingBoundary: boundary,
});
const routed = turn.transcribe({
  transcript: input.transcript,
  processingBoundary: boundary,
  cloudConsent: false,
  schemaVersion: input.schemaVersion,
});
const responding = routed.route({ decision: input.route });
const terminal = responding.finish({ response: input.response });

const emptyTranscript = ConversationTurn.open({
  sessionId: input.sessionId, turnId: "turn-empty", turnEpoch: 0, processingBoundary: boundary,
});
const credentialTranscript = ConversationTurn.open({
  sessionId: input.sessionId, turnId: "turn-credential", turnEpoch: 0, processingBoundary: boundary,
});
const cloudTurn = ConversationTurn.open({
  sessionId: input.sessionId, turnId: "turn-cloud", turnEpoch: 0, processingBoundary: "consentedCloud",
});
const wrongHashTurn = ConversationTurn.open({
  sessionId: input.sessionId, turnId: "turn-wrong-hash", turnEpoch: 0, processingBoundary: boundary,
});
const wrongHashRoute = { ...input.route, inputHash: "0".repeat(64) };

console.log(JSON.stringify({
  voice: {
    active: active.snapshot,
    duplicateStartIdentity: duplicateStart === active,
    duplicateStart: duplicateStart.snapshot,
    degraded: degraded.snapshot,
    closedFromActive: closedFromActive.snapshot,
    closedFromDegraded: closedFromDegraded.snapshot,
    activeReleaseCount: Object.keys(closedFromActive.processingOnlyValues).length,
    degradedReleaseCount: Object.keys(closedFromDegraded.processingOnlyValues).length,
    degradedRestart: attempt(() => degraded.start()),
    closedStart: attempt(() => closedFromActive.start()),
    closedDegrade: attempt(() => closedFromActive.degrade({ reason: "late" })),
    closedClose: attempt(() => closedFromActive.close({ reason: "late", endedAtIso: input.endedAtIso })),
  },
  turn: {
    receiving: turn.snapshot,
    routed: routed.snapshot,
    responding: responding.snapshot,
    terminal: terminal.snapshot,
    boundRoute: responding.snapshot.boundRoute,
    boundResponse: terminal.snapshot.boundResponse,
    emptyTranscript: attempt(() => emptyTranscript.transcribe({
      transcript: "", processingBoundary: boundary, cloudConsent: false, schemaVersion: input.schemaVersion,
    })),
    credentialTranscript: attempt(() => credentialTranscript.transcribe({
      transcript: "my API key is sk-abcdefghijklmnop", processingBoundary: boundary, cloudConsent: false,
      schemaVersion: input.schemaVersion,
    })),
    cloudWithoutConsent: attempt(() => cloudTurn.transcribe({
      transcript: input.transcript, processingBoundary: "consentedCloud", cloudConsent: false,
      schemaVersion: input.schemaVersion,
    })),
    routeBeforeTranscript: attempt(() => turn.route({ decision: input.route })),
    wrongRouteHash: attempt(() => wrongHashTurn.transcribe({
      transcript: input.transcript, processingBoundary: boundary, cloudConsent: false, schemaVersion: input.schemaVersion,
    }).route({ decision: wrongHashRoute })),
  },
}));
'''


def _behavior(tmp_path: Path) -> dict[str, object]:
    scratch = ROOT / "edge" / ".voice-edge-red"
    if scratch.exists():
        shutil.rmtree(scratch)
    source = scratch / "driver.ts"
    output = scratch / "compiled"
    source.parent.mkdir(parents=True)
    encoded_input = json.dumps(json.dumps(_driver_input(), sort_keys=True))
    source.write_text(
        DRIVER.replace("__INPUT_JSON__", encoded_input),
        encoding="utf-8",
    )
    try:
        compiled = subprocess.run(
            [
                "tsc", "driver.ts", "--outDir", str(output), "--target", "es2022",
                "--module", "nodenext", "--moduleResolution", "nodenext", "--strict",
                "--skipLibCheck",
            ],
            cwd=scratch, text=True, capture_output=True, timeout=60, check=False,
        )
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr
        executable = output / ".voice-edge-red" / "driver.js"
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


def _voice(tmp_path: Path) -> dict[str, object]:
    value = _behavior(tmp_path)["voice"]
    assert isinstance(value, dict)
    return value


def _turn(tmp_path: Path) -> dict[str, object]:
    value = _behavior(tmp_path)["turn"]
    assert isinstance(value, dict)
    return value


def test_strict_tsconfig_includes_the_new_state_modules() -> None:
    compiler = json.loads((ROOT / "edge/tsconfig.json").read_text(encoding="utf-8"))
    assert "state/**/*.ts" in compiler["include"]
    assert compiler["compilerOptions"]["strict"] is True


def test_voic_305554_active_degrade_marks_degraded_without_boundary_change(tmp_path: Path) -> None:
    value = _voice(tmp_path)
    assert value["active"] == {
        "sessionId": FIXTURE.session_id, "status": "active", "processingBoundary": "localOnly",
        "turnEpoch": 0, "activeStreamId": None, "startedAtIso": "2026-09-20T00:00:00Z", "endedAtIso": None,
    }
    degraded = value["degraded"]
    assert isinstance(degraded, dict)
    assert degraded["status"] == "degraded"
    assert degraded["processingBoundary"] == "localOnly"
    assert degraded["sessionId"] == FIXTURE.session_id


def test_voic_e62d1f_active_close_releases_processing_only_values(tmp_path: Path) -> None:
    value = _voice(tmp_path)
    closed = value["closedFromActive"]
    assert isinstance(closed, dict)
    assert closed["status"] == "closed" and closed["endedAtIso"] == "2026-09-20T00:00:01Z"
    assert value["activeReleaseCount"] == 0


def test_voic_32ea66_degraded_close_releases_processing_only_values(tmp_path: Path) -> None:
    value = _voice(tmp_path)
    closed = value["closedFromDegraded"]
    assert isinstance(closed, dict)
    assert closed["status"] == "closed" and closed["endedAtIso"] == "2026-09-20T00:00:01Z"
    assert value["degradedReleaseCount"] == 0


def test_conv_02965d_transcribe_guards_hashes_and_retains_ephemeral(tmp_path: Path) -> None:
    value = _turn(tmp_path)
    routed = value["routed"]
    assert isinstance(routed, dict)
    assert routed["status"] == "Routed"
    assert routed["inputHash"] == EXPECTED_INPUT_HASH == DECISION.input_hash
    assert routed["ephemeralTranscript"] == FIXTURE.transcript
    guards = (value["emptyTranscript"], value["credentialTranscript"], value["cloudWithoutConsent"])
    assert all(isinstance(item, dict) and item["threw"] is True for item in guards)


def test_conv_73bae3_valid_non_tool_route_binds_responding(tmp_path: Path) -> None:
    value = _turn(tmp_path)
    responding = value["responding"]
    assert isinstance(responding, dict)
    assert responding["status"] == "Responding"
    route = value["boundRoute"]
    assert isinstance(route, dict)
    assert route["route"] == DECISION.route == "chitchat"
    assert route["selectedLabel"] == DECISION.selected_label
    assert route["inputHash"] == DECISION.input_hash
    assert route["policyHash"] == DECISION.policy_hash
    assert value["routeBeforeTranscript"] == {"threw": True}
    assert value["wrongRouteHash"] == {"threw": True}


def test_conv_dab39a_finish_terminalizes_and_releases_transcript(tmp_path: Path) -> None:
    value = _turn(tmp_path)
    terminal = value["terminal"]
    assert isinstance(terminal, dict)
    assert terminal["status"] == "Terminal"
    assert terminal["ephemeralTranscript"] is None
    response = value["boundResponse"]
    assert isinstance(response, dict)
    assert response["text"] == "Hi — I'm here."
    assert response["responseId"] == "response-voice-turn-001"


def test_session_restart_and_closed_mutations_do_not_create_a_new_session(tmp_path: Path) -> None:
    value = _voice(tmp_path)
    assert value["duplicateStartIdentity"] is True
    assert value["duplicateStart"] == value["active"]
    assert value["degradedRestart"] == {"threw": True}
    assert value["closedStart"] == {"threw": True}
    assert value["closedDegrade"] == {"threw": True}
    assert value["closedClose"] == {"threw": True}
