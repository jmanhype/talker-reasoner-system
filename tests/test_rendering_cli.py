from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from talk_reasoner.actions import ActionProposal, ActionProvenance, CATALOG_PATH, ConsentRecord, FixtureState, load_action_catalog, validate_action
from talk_reasoner.contracts import load_fixture
from talk_reasoner.jobs import TerminalOutcome
from talk_reasoner.rendering import PresentationConstraints, RenderError, render_response
from talk_reasoner.cli import run_fixture
from talk_reasoner.routing import load_threshold_policy, classify
from talk_reasoner.transports import LocalScriptedTransport, NoAction, ReasonerProposal, ReasonerProvenance

ROOT = Path(__file__).parents[1]
FIXTURE = load_fixture(ROOT / "tests/fixtures/slice0/trs-tools-001.json")
CATALOG = load_action_catalog(CATALOG_PATH)
POLICY = load_threshold_policy(ROOT / "config/routing/slice0-v1.json")
DECISION = classify(FIXTURE, policy=POLICY)
NOW = datetime.now(timezone.utc).replace(microsecond=0)

class Clock:
    def __init__(self) -> None: self.current = 0.0
    def now(self) -> float: return self.current
    async def wait(self, seconds: float) -> None: self.current += seconds; await asyncio.sleep(0)

def constraints(**changes: Any) -> PresentationConstraints:
    base = PresentationConstraints(response_id="response-stable-001")
    return base._replace(**changes) if changes else base

def outcome(state: str, summary: str = "A validated local response is ready.") -> TerminalOutcome:
    reason = "waiting_confirmation" if state == "waiting_confirmation" else state
    return TerminalOutcome(state, reason, 4, 2, "safe", summary, state == "completed", 12,
                           ReasonerProvenance("slice0-reasoner-provenance-v1", FIXTURE.provenance.fixture_set_version,
                                              "local-scripted-transport", "slice0-local-v1", "reviewed"), "job-stable-001")

def action(name: str = "write_state", arguments: dict[str, Any] | None = None) -> ActionProposal:
    values = arguments or {"key": "preferences", "value": "afternoon meetings", "terms": ["meeting"]}
    return ActionProposal("slice0-proposal-v1", name, values, f"job-{DECISION.input_hash[:20]}", FIXTURE.session_id, FIXTURE.turn_id, 0,
                          "fixture-user", "fixture-user", "fixture://slice0", "The fixture requests one local write.",
                          ActionProvenance("slice0-provenance-v1", FIXTURE.provenance.fixture_set_version, "synthetic-local", "reviewed", DECISION.input_hash),
                          CATALOG.catalog_version, CATALOG.policy.policy_version)

def validated() -> Any:
    consent = ConsentRecord("consent-v1", "fixture-user", FIXTURE.session_id, "fixture-user", frozenset({"local.read", "local.write"}),
                            NOW - timedelta(seconds=5), NOW + timedelta(minutes=5), CATALOG.policy.policy_version)
    state = FixtureState("state-v1", FIXTURE.session_id, 1, NOW + timedelta(minutes=5), dict(FIXTURE.bounded_context.state), frozenset())
    return validate_action(action(), catalog=CATALOG, consent=consent, state=state).accepted

def proposal(candidate: str = "Your preference is ready to save.", name: str = "write_state",
             arguments: dict[str, Any] | None = None) -> ReasonerProposal:
    accepted = action(name, arguments)
    return ReasonerProposal("slice0-reasoner-proposal-v1", f"job-{DECISION.input_hash[:20]}", FIXTURE.session_id, FIXTURE.turn_id, 0,
                            candidate, (accepted,), None, {}, 0.94, 0.05, DECISION.input_hash, CATALOG.catalog_hash,
                            CATALOG.policy.policy_version, ReasonerProvenance("slice0-reasoner-provenance-v1", FIXTURE.provenance.fixture_set_version,
                            "local-scripted-transport", "slice0-local-v1", "reviewed"))

def no_action_proposal(fixture: Any, decision: Any) -> ReasonerProposal:
    return ReasonerProposal("slice0-reasoner-proposal-v1", f"job-{decision.input_hash[:20]}", fixture.session_id, fixture.turn_id, 0,
                            "A reviewed local result is ready.", (), NoAction("No action is required."), {}, 0.94, 0.05,
                            decision.input_hash, CATALOG.catalog_hash, CATALOG.policy.policy_version,
                            ReasonerProvenance("slice0-reasoner-provenance-v1", fixture.provenance.fixture_set_version,
                            "local-scripted-transport", "slice0-local-v1", "reviewed"))

@pytest.mark.parametrize("state", ("chitchat", "unclear", "completed", "waiting_confirmation", "canceled", "downgraded", "failed"))
def test_renderer_covers_every_state_with_clean_copy(state: str) -> None:
    rendered = render_response(outcome(state), constraints=constraints(validated_action=validated() if state == "waiting_confirmation" else None))
    assert rendered.response_id == "response-stable-001" and rendered.channel == "text"
    assert rendered.priority == 2 and rendered.turn_epoch == 4 and rendered.latency_ms == 12
    assert rendered.provenance["source"] == "local-scripted-transport"
    if state == "canceled": assert rendered.text == ""
    elif state == "failed": assert rendered.text == "That request couldn't be completed safely. Please rephrase it and try again."
    else: assert rendered.text

def test_confirmation_names_exact_safe_choices() -> None:
    rendered = render_response(outcome("waiting_confirmation", "confirmation"), constraints=constraints(validated_action=validated()))
    text = rendered.text
    assert text.count("?") == 1
    for phrase in ("Save", "preferences", "afternoon meetings", "meeting", "your local fixture state", "one time", "reversible",
                   "no tool will run", "Reply yes", "or no to cancel"):
        assert phrase in text

@pytest.mark.parametrize("unsafe", (
    "schema_version is slice0", "raw model output follows", "Traceback and stack trace", "api_key=secret",
    "tool log: local execution", "hidden prompt instructions", "unrelated private context", "event body ledger_event",
    "unreviewed private tool output", "{\"answer\":\"private\"}",
))
def test_renderer_rejects_forbidden_content(unsafe: str) -> None:
    with pytest.raises(RenderError): render_response(outcome("completed", unsafe), constraints=constraints())

def test_renderer_rejects_empty_or_ambiguous_state() -> None:
    with pytest.raises(RenderError): render_response(outcome("completed", ""), constraints=constraints())
    with pytest.raises(RenderError): render_response(outcome("running"), constraints=constraints())


def test_downgrade_is_bounded_and_unknown_targets_fail_closed() -> None:
    rendered = render_response(outcome("downgraded", "Send the private email now."), constraints=constraints())
    assert rendered.text == "That work was set aside. You can ask to resume it later."
    outside = validated()._replace(target="network://example")
    with pytest.raises(RenderError): render_response(outcome("waiting_confirmation"), constraints=constraints(validated_action=outside))

def test_cli_fast_routes_do_not_wake_reasoner() -> None:
    transport = LocalScriptedTransport(proposal(), 0, Clock())
    for name, expected in (("trs-chitchat-001.json", "chitchat"), ("trs-unclear-001.json", "unclear")):
        fixture = load_fixture(ROOT / "tests/fixtures/slice0" / name); out: list[str] = []; err: list[str] = []
        result = asyncio.run(run_fixture(fixture, transport=transport, clock=Clock(), stdout=_Sink(out), stderr=_Sink(err)))
        assert result.exit_status == 0 and result.route == expected and result.terminal_state == "rendered"
        assert transport.call_count == 0 and len(out) == 1
        if expected == "unclear": assert "?" in out[0]
        evidence = json.loads(err[-1]); assert evidence["route"]["actual"] == expected and evidence["ledger"]["valid_chain"]
        assert FIXTURE.transcript not in "".join(out) + "".join(err)

def test_cli_slow_path_renders_completed_waiting_and_failed() -> None:
    cases = (("Your local result is ready.", "completed"), ("Your preference can be saved.", "waiting_confirmation"))
    for candidate, state in cases:
        out: list[str] = []; err: list[str] = []
        script = proposal(candidate) if state == "waiting_confirmation" else proposal(candidate, "search", {"query": "local preference", "limit": 2, "terms": ["fixture"]})
        result = asyncio.run(run_fixture(FIXTURE, transport=LocalScriptedTransport(script, 0, Clock()), clock=Clock(), stdout=_Sink(out), stderr=_Sink(err)))
        assert result.exit_status == 0 and result.route == "needs_tools" and result.terminal_state == state
        assert 1 <= len(out) <= 2
        assert candidate in " ".join(out) if state == "completed" else "Reply yes" in " ".join(out)
        evidence = json.loads(err[-1]); assert evidence["versions"]["catalog"] and evidence["ledger"]["valid_chain"]
    bad = proposal().actions[0]._replace(arguments={"key": "passwords", "value": "x", "terms": []})
    invalid = replace(proposal(), actions=(bad,)); out: list[str] = []; err: list[str] = []
    result = asyncio.run(run_fixture(FIXTURE, transport=LocalScriptedTransport(invalid, 0, Clock()), clock=Clock(), stdout=_Sink(out), stderr=_Sink(err)))
    assert result.exit_status == 0 and result.terminal_state == "failed" and "try again" in out[-1]

@pytest.mark.parametrize("path", sorted((ROOT / "tests/fixtures/slice0").glob("*.json")))
def test_cli_runs_every_fixture_with_real_local_components(path: Path) -> None:
    fixture = load_fixture(path); policy = load_threshold_policy(ROOT / "config/routing/slice0-v1.json"); decision = classify(fixture, policy=policy)
    script = no_action_proposal(fixture, decision) if decision.route == "needs_tools" else proposal()
    out: list[str] = []; err: list[str] = []
    result = asyncio.run(run_fixture(fixture, transport=LocalScriptedTransport(script, 0, Clock()), clock=Clock(), stdout=_Sink(out), stderr=_Sink(err)))
    evidence = json.loads(err[-1])
    assert result.exit_status == 0 and evidence["route"]["actual"] == fixture.expected.route
    assert result.terminal_state == ("completed" if decision.route == "needs_tools" else "rendered")
    assert evidence["ledger"]["valid_chain"] and fixture.transcript not in "".join(out) + "".join(err)

def test_renderer_and_cli_have_no_network_or_execution_imports() -> None:
    import re
    for name in ("requests", "httpx", "aiohttp", "socket", "subprocess"):
        for path in (ROOT / "src/talk_reasoner/rendering.py", ROOT / "src/talk_reasoner/cli.py"):
            assert not re.search(rf"(?m)^\s*(import|from)\s+{name}\b", path.read_text(encoding="utf-8"))

def test_cli_fail_closed_for_renderer_error_and_invalid_fixture() -> None:
    out: list[str] = []; err: list[str] = []
    unsafe = proposal("raw model output", "search", {"query": "local preference", "limit": 2, "terms": ["fixture"]})
    result = asyncio.run(run_fixture(FIXTURE, transport=LocalScriptedTransport(unsafe, 0, Clock()), clock=Clock(), stdout=_Sink(out), stderr=_Sink(err)))
    assert result.exit_status == 2 and "raw model output" not in "".join(out) + "".join(err)
    assert json.loads(err[-1])["error"] == "renderer_invalid"
    from talk_reasoner.cli import main
    assert main([str(ROOT / "tests/fixtures/slice0/missing.json")]) == 2


def test_cli_usage_error_is_compact_fail_closed_evidence(capsys: pytest.CaptureFixture[str]) -> None:
    from talk_reasoner.cli import main
    assert main([]) == 2
    captured = capsys.readouterr(); evidence = json.loads(captured.err)
    assert captured.out == "" and evidence["error"] == "usage_invalid"


def test_module_main_reaches_real_local_confirmation(capsys: pytest.CaptureFixture[str]) -> None:
    from talk_reasoner.cli import main
    assert main([str(ROOT / "tests/fixtures/slice0/trs-tools-001.json")]) == 0
    captured = capsys.readouterr(); evidence = json.loads(captured.err)
    assert "Reply yes" in captured.out and evidence["terminal_state"] == "waiting_confirmation"

class _Sink:
    def __init__(self, lines: list[str]) -> None: self.lines = lines
    def write(self, value: str) -> int: self.lines.append(value); return len(value)
    def flush(self) -> None: pass
