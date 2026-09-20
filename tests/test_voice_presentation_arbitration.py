from __future__ import annotations

import json
import shutil
import subprocess
import unicodedata
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
PRESENTATION_SCHEMA_VERSION = "slice0-presentation-arbitration-v1"
TYPED_TEXT = "Hi — I'm here."
SPOKEN_TEXT = "hi — i'm here"


class _RenderProvenance(NamedTuple):
    schema_version: str; fixture_set_version: str; source: str; model_id: str; review_status: str


def _provenance() -> _RenderProvenance:
    return _RenderProvenance("slice0-rendered-response-v1", FIXTURE.provenance.fixture_set_version, "synthetic-local", "none", "reviewed")


def _outcome(state: str, reason: str, priority: int, choice: str, summary: str, allowed: bool, job_id: str) -> TerminalOutcome:
    return TerminalOutcome(state, reason, 0, priority, choice, summary, allowed, 0, _provenance(), job_id)


def _rendered(response_id: str, outcome: TerminalOutcome) -> dict[str, object]:
    rendered = render_response(
        outcome,
        constraints=PresentationConstraints(response_id),
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


def _rendered_response() -> dict[str, object]:
    return _rendered("response-voice-turn-001", _outcome("chitchat", "rendered", 1, "safe", TYPED_TEXT, True, "no-tool-turn"))


def _canceled_renderer_identity() -> dict[str, object]:
    return _rendered("response-canceled-001", _outcome("canceled", "canceled", 0, "canceled", "", False, "canceled-turn"))


def _semantic_key(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return "".join(character for character in normalized if character.isalnum())


def _parity_hash(typed_text: str, spoken_text: str) -> str:
    canonical = json.dumps(
        {"semantics": _semantic_key(typed_text) + "|" + _semantic_key(spoken_text)},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return scoped_hash(
        canonical,
        scope="presentation-parity",
        schema_version=PRESENTATION_SCHEMA_VERSION,
    )


def _driver_input() -> dict[str, object]:
    return {
        "sessionId": FIXTURE.session_id,
        "turnId": FIXTURE.turn_id,
        "schemaVersion": FIXTURE.schema_version,
        "transcript": FIXTURE.transcript,
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
        "canceledResponse": _canceled_renderer_identity(),
        "candidate": {
            "responseId": "response-voice-turn-001",
            "turnId": FIXTURE.turn_id,
            "typedText": TYPED_TEXT,
            "spokenText": SPOKEN_TEXT,
            "semanticParityHash": _parity_hash(TYPED_TEXT, SPOKEN_TEXT),
            "channel": "textAndSpeech",
            "priority": 1,
            "turnEpoch": 0,
            "source": "response",
            "terminalState": "rendered",
            "accessibility": {
                "screenReaderText": TYPED_TEXT,
                "captionsAvailable": True,
            },
        },
        "activeUser": {
            "responseId": "active-user-interruption-001",
            "typedText": "I am talking now",
            "spokenText": "I am talking now",
            "semanticParityHash": _parity_hash("I am talking now", "I am talking now"),
        },
        "canceled": {
            "responseId": "response-canceled-001",
            "typedText": "This canceled output must stay silent",
            "spokenText": "This canceled output must stay silent",
            "semanticParityHash": _parity_hash(
                "This canceled output must stay silent",
                "This canceled output must stay silent",
            ),
        },
    }


DRIVER = r'''
import type { ProcessingBoundary } from "../ports/audio.js";
import type { ResponseCandidate } from "../state/arbitration.js";
import { PresentationArbiter } from "../state/arbitration.js";
import { ConversationTurn } from "../state/ConversationTurn.js";

const input = JSON.parse(__INPUT_JSON__) as Record<string, any>;
const boundary: ProcessingBoundary = "localOnly";

const terminal = ConversationTurn.open({
  sessionId: input.sessionId,
  turnId: input.turnId,
  turnEpoch: 0,
  processingBoundary: boundary,
}).transcribe({
  transcript: input.transcript,
  processingBoundary: boundary,
  cloudConsent: false,
  schemaVersion: input.schemaVersion,
}).route({ decision: input.route }).finish({ response: input.response });
const terminalSnapshot = terminal.snapshot;
const rendered = terminalSnapshot.boundResponse;
if (rendered === null) throw new Error("the terminal turn did not bind a rendered response");

const valid: ResponseCandidate = {
  ...input.candidate,
  responseId: rendered.responseId,
  typedText: rendered.text,
  turnEpoch: terminalSnapshot.turnEpoch,
};

function openAt(epoch: number): PresentationArbiter {
  return PresentationArbiter.open({
    sessionId: input.sessionId,
    currentTurnEpoch: epoch,
    activeStreamId: null,
  });
}

function rejectWith(changes: Record<string, unknown>) {
  const arbiter = openAt(valid.turnEpoch);
  const candidate = { ...valid, ...changes } as ResponseCandidate;
  return { decision: arbiter.submit(candidate), snapshot: arbiter.snapshot };
}

const validArbiter = openAt(valid.turnEpoch);
const validDecision = validArbiter.submit(valid);

const slowOutput: ResponseCandidate = {
  ...valid,
  responseId: "stale-slow-response-001",
  source: "slowPath",
};
const overlapArbiter = openAt(valid.turnEpoch);
const slowDecision = overlapArbiter.submit(slowOutput);
const ordinarySecond: ResponseCandidate = { ...valid, responseId: "ordinary-second-001" };
const ordinaryDecision = overlapArbiter.submit(ordinarySecond);
const snapshotAfterOrdinary = overlapArbiter.snapshot;
const activeUser: ResponseCandidate = {
  ...valid,
  ...input.activeUser,
  priority: 100,
  source: "activeUser",
};
const activeUserDecision = overlapArbiter.submit(activeUser);

console.log(JSON.stringify({
  integration: {
    turnStatus: terminalSnapshot.status,
    ephemeralTranscript: terminalSnapshot.ephemeralTranscript,
    renderedResponseId: rendered.responseId,
    renderedText: rendered.text,
    rendererChannel: rendered.channel,
  },
  valid: {
    candidate: valid,
    decision: validDecision,
    snapshot: validArbiter.snapshot,
  },
  parity: {
    emptyTyped: rejectWith({ typedText: "" }),
    emptySpoken: rejectWith({ spokenText: "" }),
    mismatch: rejectWith({
      spokenText: "A different meaning entirely",
      semanticParityHash: valid.semanticParityHash,
    }),
    rawValues: rejectWith({
      rawTranscript: input.transcript,
      rawAudio: "processing-only-audio-canary",
    }),
  },
  accessibility: {
    emptyScreenReaderText: rejectWith({
      accessibility: { ...valid.accessibility, screenReaderText: "" },
    }),
    captionsUnavailable: rejectWith({
      accessibility: { ...valid.accessibility, captionsAvailable: false },
    }),
    inaccessibleChannel: rejectWith({
      channel: "speech",
      accessibility: { ...valid.accessibility, captionsAvailable: false },
    }),
  },
  bounds: {
    typedTooLong: rejectWith({
      typedText: "x".repeat(241),
      semanticParityHash: input.overlongTypedHash,
    }),
    spokenTooLong: rejectWith({
      spokenText: "x".repeat(241),
      semanticParityHash: input.overlongSpokenHash,
    }),
  },
  oneStream: {
    slowDecision,
    ordinaryDecision,
    snapshot: snapshotAfterOrdinary,
  },
  activeUser: {
    decision: activeUserDecision,
    snapshot: overlapArbiter.snapshot,
  },
  stale: rejectWith({ turnEpoch: valid.turnEpoch - 1 }),
  canceled: (() => {
    const arbiter = openAt(valid.turnEpoch);
    const candidate = {
      ...valid,
      ...input.canceled,
      turnEpoch: valid.turnEpoch,
      priority: 100,
      terminalState: "canceled",
    } as ResponseCandidate;
    return { decision: arbiter.submit(candidate), snapshot: arbiter.snapshot };
  })(),
  privacySnapshot: validArbiter.snapshot,
}));
'''


def _behavior() -> dict[str, object]:
    scratch = ROOT / "edge" / ".voice-arbitration-red"
    if scratch.exists():
        shutil.rmtree(scratch)
    source = scratch / "driver.ts"
    output = scratch / "compiled"
    source.parent.mkdir(parents=True)
    encoded_input = json.dumps(
        json.dumps(
            _driver_input()
            | {
                "overlongTypedHash": _parity_hash("x" * 241, SPOKEN_TEXT),
                "overlongSpokenHash": _parity_hash(TYPED_TEXT, "x" * 241),
            },
            sort_keys=True,
        ),
        sort_keys=True,
    )
    source.write_text(
        DRIVER.replace("__INPUT_JSON__", encoded_input),
        encoding="utf-8",
    )
    try:
        compiled = subprocess.run(
            [
                "tsc", ".voice-arbitration-red/driver.ts", "--outDir", str(output),
                "--target", "es2022", "--module", "nodenext", "--moduleResolution", "nodenext",
                "--strict", "--skipLibCheck",
            ],
            cwd=ROOT / "edge", text=True, capture_output=True, timeout=60, check=False,
        )
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr
        executable = output / ".voice-arbitration-red" / "driver.js"
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


def _section(name: str) -> dict[str, object]:
    value = _behavior()[name]
    assert isinstance(value, dict)
    return value


def _decision(action: str, active: str | None, reason: str | None = None, superseded: str | None = None) -> dict[str, object]:
    return {"action": action, "activeStreamId": active, "rejectionReason": reason, "supersededStreamId": superseded}


def _snapshot(active: str | None) -> dict[str, object]:
    return {"sessionId": FIXTURE.session_id, "currentTurnEpoch": 0, "activeStreamId": active}


def test_edge_arbitration_stays_strict_and_dependency_free() -> None:
    compiler = json.loads((ROOT / "edge/tsconfig.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "edge/package.json").read_text(encoding="utf-8"))
    assert "state/**/*.ts" in compiler["include"]
    assert compiler["compilerOptions"]["strict"] is True
    assert "dependencies" not in manifest and "devDependencies" not in manifest


def test_valid_renderer_candidate_carries_parity_and_accessibility() -> None:
    value = _section("valid")
    integration = _section("integration")
    candidate = value["candidate"]
    decision = value["decision"]
    assert isinstance(candidate, dict) and isinstance(decision, dict)
    assert integration == {
        "turnStatus": "Terminal",
        "ephemeralTranscript": None,
        "renderedResponseId": "response-voice-turn-001",
        "renderedText": TYPED_TEXT,
        "rendererChannel": "text",
    }
    assert candidate["responseId"] == "response-voice-turn-001"
    assert candidate["typedText"] == TYPED_TEXT
    assert candidate["spokenText"] == SPOKEN_TEXT
    assert candidate["semanticParityHash"] == _parity_hash(TYPED_TEXT, SPOKEN_TEXT)
    assert candidate["channel"] == "textAndSpeech"
    assert candidate["priority"] == 1
    assert candidate["turnEpoch"] == 0
    assert candidate["accessibility"] == {
        "screenReaderText": TYPED_TEXT, "captionsAvailable": True,
    }
    assert decision == _decision("present", "response-voice-turn-001")
    assert value["snapshot"] == _snapshot("response-voice-turn-001")


def test_typed_spoken_parity_fails_closed_without_raw_values() -> None:
    value = _section("parity")
    expected = _decision("reject", None, "parity-mismatch")
    assert value["emptyTyped"]["decision"] == expected
    assert value["emptySpoken"]["decision"] == expected
    assert value["mismatch"]["decision"] == expected
    raw = value["rawValues"]["decision"]
    assert isinstance(raw, dict)
    assert raw["action"] == "reject" and raw["activeStreamId"] is None
    assert raw["rejectionReason"] == "processing-value-rejected"


def test_accessibility_metadata_and_channel_combinations_fail_closed() -> None:
    value = _section("accessibility")
    expected = _decision("reject", None, "inaccessible-presentation")
    assert value["emptyScreenReaderText"]["decision"] == expected
    assert value["captionsUnavailable"]["decision"] == expected
    assert value["inaccessibleChannel"]["decision"] == expected


def test_typed_and_spoken_payload_bounds_fail_closed() -> None:
    value = _section("bounds")
    expected = _decision("reject", None, "presentation-too-long")
    assert value["typedTooLong"]["decision"] == expected
    assert value["spokenTooLong"]["decision"] == expected


def test_second_ordinary_submission_never_overlaps_the_active_stream() -> None:
    value = _section("oneStream")
    slow = value["slowDecision"]
    ordinary = value["ordinaryDecision"]
    assert slow == _decision("present", "stale-slow-response-001")
    assert ordinary == _decision("reject", "stale-slow-response-001", "stream-active")
    assert value["snapshot"] == _snapshot("stale-slow-response-001")


def test_active_user_speech_supersedes_stale_slow_output() -> None:
    value = _section("activeUser")
    assert value["decision"] == _decision("supersede", "active-user-interruption-001", superseded="stale-slow-response-001")
    assert value["snapshot"] == _snapshot("active-user-interruption-001")


def test_stale_turn_epoch_is_rejected_before_presentation() -> None:
    value = _section("stale")
    assert value["decision"] == _decision("reject", None, "stale-turn-epoch")
    assert value["snapshot"]["activeStreamId"] is None


def test_canceled_renderer_output_cannot_become_audible() -> None:
    value = _section("canceled")
    assert value["decision"] == _decision("reject", None, "canceled-response")
    assert value["snapshot"]["activeStreamId"] is None


def test_arbiter_snapshot_retains_no_raw_transcript_or_audio() -> None:
    snapshot = json.dumps(_behavior()["privacySnapshot"], sort_keys=True)
    assert FIXTURE.transcript not in snapshot
    assert "transcript" not in snapshot.lower()
    assert "audio" not in snapshot.lower()
    assert "canary" not in snapshot.lower()
