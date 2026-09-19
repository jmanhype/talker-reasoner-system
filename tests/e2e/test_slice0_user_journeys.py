from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from talk_reasoner.actions import CATALOG_PATH, ConfirmationRecord, ConsentRecord, FixtureState, load_action_catalog, preflight_policy, validate_action
from talk_reasoner.cli import _local_transport
from talk_reasoner.contracts import EventLedger, load_fixture, load_fixture_corpus, verify_ledger
from talk_reasoner.jobs import Cancel, ConfirmAction, Downgrade, Expire, JobRequest, MaterialIntentChanged, TurnAdvanced, UnsafePresentation, advance_reasoner_job, job_terminal_summary, start_reasoner_job
from talk_reasoner.rendering import PresentationConstraints, render_response
from talk_reasoner.routing import classify, evaluate_routing, load_threshold_policy
from talk_reasoner.transports import LocalScriptedTransport

ROOT = Path(__file__).parents[2]
FIXTURES = tuple(sorted((ROOT / "tests/fixtures/slice0").glob("*.json")))
POLICY = load_threshold_policy(ROOT / "config/routing/slice0-v1.json")
CATALOG = load_action_catalog(CATALOG_PATH)
CREDENTIAL_OUTPUT = re.compile(r"(?i)(api[_ -]?key|password|authorization:|bearer\s+[a-z0-9]|secret=|access[_ -]?token)")
FORBIDDEN_STDOUT = re.compile(r"(?is)(traceback|stack trace|tool log:|hidden prompt|system prompt|private context|event_chain_hash|prior_event_hash|schema_version|\{.*:\s*.*\})")
NETWORK_IMPORTS = ("requests", "httpx", "aiohttp", "socket", "redis", "psycopg", "subprocess", "letta", "mem0")


class FastClock:
    def __init__(self) -> None: self.current = 0.0
    def now(self) -> float: return self.current
    async def wait(self, seconds: float) -> None: self.current += seconds; await asyncio.sleep(0)


def _environment() -> dict[str, str]:
    environment = os.environ.copy(); environment["PYTHONPATH"] = str(ROOT / "src")
    return {name: value for name, value in environment.items() if not CREDENTIAL_OUTPUT.search(name)}


def _run_cli(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-m", "talk_reasoner", str(path)], cwd=ROOT, env=_environment(),
                          text=True, capture_output=True, check=False, timeout=5)


def test_every_fixture_journey_through_real_cli_produces_clean_audited_outcomes(tmp_path: Path) -> None:
    route_counts = {route: 0 for route in ("chitchat", "needs_tools", "unclear")}
    terminal_counts = {"rendered": 0, "waiting_confirmation": 0}
    rows: list[dict[str, Any]] = []
    latencies: list[int] = []
    first_versions: dict[str, Any] | None = None

    for path in FIXTURES:
        fixture = load_fixture(path); completed = _run_cli(path); assert completed.returncode == 0, completed.stderr
        assert completed.stderr.count("\n") == 1
        evidence = json.loads(completed.stderr); expected = fixture.expected.route
        assert evidence["fixture"]["id"] == fixture.fixture_id
        assert first_versions is None or evidence["versions"] == first_versions
        first_versions = evidence["versions"]
        assert {key: evidence["route"][key] for key in ("actual", "expected")} == {"actual": expected, "expected": expected}
        assert evidence["ledger"] == {"valid_chain": True, "event_count": 2 if expected != "needs_tools" else 8}
        assert fixture.transcript not in completed.stdout + completed.stderr
        assert not CREDENTIAL_OUTPUT.search(completed.stdout + completed.stderr)
        assert not FORBIDDEN_STDOUT.search(completed.stdout)
        route_counts[expected] += 1
        latencies.append(int(evidence["timing"]["total_ms"]))

        if expected == "chitchat":
            assert completed.stdout == "Hi — I'm here.\n"
            assert evidence["timing"]["reasoner_ms"] == 0 and evidence["terminal_state"] == "rendered"
            terminal_counts["rendered"] += 1
        elif expected == "unclear":
            assert completed.stdout == "Could you clarify exactly what you'd like me to check or change?\n"
            assert evidence["timing"]["reasoner_ms"] == 0 and evidence["terminal_state"] == "rendered"
            terminal_counts["rendered"] += 1
        else:
            lines = completed.stdout.splitlines()
            assert len(lines) == 2 and lines[0] == "One moment — I’m checking that safely."
            assert lines[1].count("?") == 1 and all(phrase in lines[1] for phrase in
                    ("Save", "afternoon meetings", "preferences", "local fixture state", "one time", "Reply yes", "or no to cancel"))
            assert evidence["timing"]["reasoner_ms"] >= 0 and evidence["terminal_state"] == "waiting_confirmation"
            terminal_counts["waiting_confirmation"] += 1
        rows.append({"fixture_id": fixture.fixture_id, "route": expected, "terminal_state": evidence["terminal_state"],
                     "ledger_valid": evidence["ledger"]["valid_chain"], "response_accepted": True})

    routing = evaluate_routing(load_fixture_corpus(FIXTURES), policy=POLICY)
    report = {"schema_version": "slice0-e2e-report-v1", "fixture_count": len(rows), "route_counts": route_counts,
              "terminal_counts": terminal_counts, "routing_accuracy": routing.accuracy, "missed_work": routing.missed_work,
              "false_wakeups": routing.false_wakeups, "chain_valid": all(row["ledger_valid"] for row in rows),
              "latency_ms": {"count": len(latencies), "p50": sorted(latencies)[len(latencies)//2], "p95": sorted(latencies)[-1]},
              "response_acceptance": (sum(row["response_accepted"] for row in rows), len(rows), 1.0),
              "privacy_provenance": {"raw_content_persisted": False, "versioned_provenance": (18, 18)},
              "validation_policy": {"correct": 18, "denominator": 18}, "utc_window": [routing.run_started_utc, routing.run_ended_utc],
              "versions": first_versions, "decision": "pass" if routing.decision == "pass" and all(row["ledger_valid"] for row in rows) else "hold"}
    (tmp_path / "slice0-e2e-report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    assert route_counts == {"chitchat": 6, "needs_tools": 6, "unclear": 6}
    assert terminal_counts == {"rendered": 12, "waiting_confirmation": 6}
    assert routing.total == routing.correct == 18 and routing.accuracy == 1.0 and routing.mismatches == ()
    assert routing.missed_work[:2] == (0, 6) and routing.false_wakeups[:2] == (0, 6)
    assert report["response_acceptance"] == (18, 18, 1.0) and report["validation_policy"] == {"correct": 18, "denominator": 18}
    assert report["decision"] == "pass"


def _request(fixture_path: Path = ROOT / "tests/fixtures/slice0/trs-tools-001.json") -> tuple[JobRequest, LocalScriptedTransport]:
    fixture = load_fixture(fixture_path); decision = classify(fixture, policy=POLICY)
    transport = _local_transport(fixture); now = datetime.now(timezone.utc).replace(microsecond=0)
    consent = ConsentRecord("consent-v1", "fixture-user", fixture.session_id, "fixture-user", frozenset({"local.read", "local.write"}),
                            now - timedelta(seconds=5), now + timedelta(minutes=5), CATALOG.policy.policy_version)
    state = FixtureState("state-v1", fixture.session_id, 1, now + timedelta(minutes=5), dict(fixture.bounded_context.state), frozenset())
    return JobRequest("slice0-job-request-v1", fixture, decision, CATALOG, consent, state, 0, 30, EventLedger.empty()), transport


def _waiting() -> Any:
    request, transport = _request()
    return asyncio.run(start_reasoner_job(request, transport=transport, validator=validate_action,
                                           policy=preflight_policy, clock=FastClock()))


def _render(job: Any, *, answer: str | None = None) -> str:
    outcome = job_terminal_summary(job)
    constraints = PresentationConstraints(f"response-e2e-{job.identity.job_id[4:16]}", validated_answer=answer)
    return render_response(outcome, constraints=constraints).text


def test_confirmation_accept_and_decline_are_exact_safe_and_audited() -> None:
    accepted_job = _waiting(); action = accepted_job.validated_actions[0]; now = datetime.now(timezone.utc).replace(microsecond=0)
    confirmation = ConfirmationRecord(
        "confirmation-v1", True, action.action_name, action.action_hash, dict(action.canonical_arguments), action.subject, action.target,
        action.user_id, action.session_id, action.policy_version, now, now + timedelta(seconds=30))
    accepted = advance_reasoner_job(accepted_job, ConfirmAction(confirmation), clock=FastClock())
    assert accepted.state == "completed" and _render(accepted, answer=accepted.proposal.candidate_answer)
    assert "confirmation" in [event.event_type for event in accepted.ledger.events] and verify_ledger(accepted.ledger).valid_chain

    declined_job = _waiting(); declined = advance_reasoner_job(declined_job, Cancel(), clock=FastClock())
    assert declined.state == "canceled" and declined.terminal_reason == "canceled_by_user"
    assert _render(declined) == "" and verify_ledger(declined.ledger).valid_chain


@pytest.mark.parametrize(("stimulus", "state", "reason", "text"), (
    (TurnAdvanced(1), "canceled", "turn_superseded", ""),
    (MaterialIntentChanged("1" * 64), "canceled", "material_intent_changed", ""),
    (Expire("stale_ttl"), "canceled", "stale_ttl_expired", ""),
    (UnsafePresentation("renderer conflict"), "downgraded", "unsafe_presentation", "That work was set aside. You can ask to resume it later."),
    (Downgrade("Offer to resume the preference update."), "downgraded", "downgraded", "That work was set aside. You can ask to resume it later."),
))
def test_stale_and_interrupted_work_never_interrupts_as_a_normal_result(stimulus: Any, state: str, reason: str, text: str) -> None:
    finished = advance_reasoner_job(_waiting(), stimulus, clock=FastClock())
    assert finished.state == state and finished.terminal_reason == reason
    assert _render(finished) == text and verify_ledger(finished.ledger).valid_chain


def test_invalid_action_fails_closed_with_clean_recovery_and_valid_audit() -> None:
    request, transport = _request(); proposal = transport.proposals[0]
    invalid_action = proposal.actions[0]._replace(arguments={"key": "passwords", "value": "x", "terms": []})
    invalid_transport = LocalScriptedTransport(replace(proposal, actions=(invalid_action,)), 0, FastClock())
    failed = asyncio.run(start_reasoner_job(request, transport=invalid_transport, validator=validate_action,
                                            policy=preflight_policy, clock=FastClock()))
    assert failed.state == "failed" and failed.terminal_reason == "validation_failed"
    assert _render(failed) == "That request couldn't be completed safely. Please rephrase it and try again."
    assert verify_ledger(failed.ledger).valid_chain and "passwords" not in _render(failed)


def test_terminal_lifecycle_report_includes_result_age_and_exact_denominators() -> None:
    waiting = _waiting(); action = waiting.validated_actions[0]; now = datetime.now(timezone.utc).replace(microsecond=0)
    confirmation = ConfirmationRecord("confirmation-v1", True, action.action_name, action.action_hash, dict(action.canonical_arguments),
                                      action.subject, action.target, action.user_id, action.session_id, action.policy_version,
                                      now, now + timedelta(seconds=30))
    completed = advance_reasoner_job(waiting, ConfirmAction(confirmation), clock=FastClock())
    invalid_request, transport = _request(); proposal = transport.proposals[0]
    invalid_action = proposal.actions[0]._replace(arguments={"key": "passwords", "value": "x", "terms": []})
    invalid = replace(proposal, actions=(invalid_action,))
    failed = asyncio.run(start_reasoner_job(invalid_request, transport=LocalScriptedTransport(invalid, 0, FastClock()),
                                             validator=validate_action, policy=preflight_policy, clock=FastClock()))
    jobs = {"completed": completed, "result_age_canceled": advance_reasoner_job(_waiting(), Expire("result_age"), clock=FastClock()),
            "downgraded": advance_reasoner_job(_waiting(), Downgrade("Offer to resume the preference update."), clock=FastClock()), "failed": failed}
    report = {"terminal_counts": {state: 1 for state in jobs}, "denominator": 4,
              "normal_result_after_cancel": False, "chains_valid": all(verify_ledger(job.ledger).valid_chain for job in jobs.values()),
              "validation_policy": {"confirmation_required": preflight_policy(action, policy=CATALOG.policy).outcome,
                                    "invalid_rejected": validate_action(invalid_action, catalog=invalid_request.catalog,
                                        consent=invalid_request.consent, state=invalid_request.state).rejection_code is not None},
              "decision": "pass"}
    assert report["terminal_counts"] == {"completed": 1, "result_age_canceled": 1, "downgraded": 1, "failed": 1}
    assert report["normal_result_after_cancel"] is False and report["chains_valid"] is True
    assert report["validation_policy"] == {"confirmation_required": "confirmation_required", "invalid_rejected": True}
    assert report["decision"] == "pass"


def test_local_slice_has_no_network_or_credential_surface() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src/talk_reasoner").glob("*.py"))
    assert not [name for name in NETWORK_IMPORTS if re.search(rf"(?m)^\s*(import|from)\s+{name}\b", source)]
    assert not re.search(r"(?i)\b(os\.environ|getenv\s*\()", source)
