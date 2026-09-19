from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import MappingProxyType
from typing import IO, NamedTuple

from talk_reasoner.actions import CATALOG_PATH, ActionProposal, ActionProvenance, ConsentRecord, FixtureState, load_action_catalog, preflight_policy, validate_action
from talk_reasoner.contracts import EVENT_SCHEMA_VERSION, EventLedger, Fixture, LedgerEvent, append_event, load_fixture, scoped_hash, verify_ledger
from talk_reasoner.jobs import JobRequest, TerminalOutcome, job_terminal_summary, start_reasoner_job
from talk_reasoner.rendering import PresentationConstraints, RenderError, RenderedResponse, render_response
from talk_reasoner.routing import CALIBRATION_VERSION, classify, load_threshold_policy, route_event
from talk_reasoner.transports import LocalScriptedTransport, MonotonicClock, ReasonerProposal, ReasonerProvenance, ReasonerTransport

CLI_EVIDENCE_VERSION = "slice0-cli-evidence-v1"
RESPONSE_SCHEMA_VERSION = "slice0-cli-response-v1"
ROUTING_POLICY_PATH = Path(__file__).parents[2] / "config" / "routing" / "slice0-v1.json"

class CLIResult(NamedTuple):
    exit_status: int; response_id: str; route: str; terminal_state: str; ledger_valid: bool; ledger_event_count: int; evidence: MappingProxyType[str, object]

def _failed(error: str, stderr: IO[str]) -> CLIResult:
    stderr.write(json.dumps({"schema_version": CLI_EVIDENCE_VERSION, "error": error}, separators=(",", ":")) + "\n")
    return CLIResult(2, "response-fail-closed", "unevaluable", "failed", False, 0, MappingProxyType({"error": error}))

class _FailClosedParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)

def _response_event(ledger: EventLedger, response: RenderedResponse, state: str, route_latency_ms: int, job_id: str | None,
                    action_hash: str | None, fixture: Fixture, policy_version: str, rejection_reason: str | None) -> EventLedger:
    prior = ledger.events[-1]; digest = scoped_hash(json.dumps({"response_id": response.response_id, "state": state}, sort_keys=True, separators=(",", ":")), scope="response-output", schema_version=RESPONSE_SCHEMA_VERSION)
    event = LedgerEvent(EVENT_SCHEMA_VERSION, "response", "1.0.0", ledger.event_count + 1, fixture.session_id, fixture.turn_id, response.turn_epoch,
                        digest, len(response.text.encode()), "text/plain", "consent-v1", policy_version, state,
                        rejection_reason, response.latency_ms + route_latency_ms,
                        action_hash, prior.event_id, prior.event_chain_hash, None, job_id)
    return append_event(ledger, event).ledger

async def run_fixture(fixture: Fixture, *, transport: ReasonerTransport, clock: MonotonicClock,
                      stdout: IO[str], stderr: IO[str]) -> CLIResult:
    """Route one typed fixture to one clean response and compact operator evidence."""
    started = clock.now(); route_latency = 0
    try:
        routing_policy = load_threshold_policy(ROUTING_POLICY_PATH); catalog = load_action_catalog(CATALOG_PATH)
        decision = classify(fixture, policy=routing_policy); route_latency = max(0, round((clock.now() - started) * 1000))
        ledger = append_event(EventLedger.empty(), route_event(fixture, decision, event_id=1)).ledger
        if decision.route == "needs_tools":
            now = datetime.now(timezone.utc); consent = ConsentRecord("consent-v1", "fixture-user", fixture.session_id, "fixture-user", frozenset({"local.read", "local.write"}), now - timedelta(seconds=5), now + timedelta(minutes=5), catalog.policy.policy_version)
            state = FixtureState("state-v1", fixture.session_id, 1, now + timedelta(minutes=5), dict(fixture.bounded_context.state), frozenset())
            request = JobRequest("slice0-job-request-v1", fixture, decision, catalog, consent, state, 0, 30, ledger)
            job = await start_reasoner_job(request, transport=transport, validator=validate_action, policy=preflight_policy, clock=clock)
            if job.state == "waiting_confirmation":
                action = job.validated_actions[0]; terminal_at = job.timing.proposal_received_at or job.timing.pending_at
                outcome = TerminalOutcome(job.state, "policy_failed", job.identity.turn_epoch, 2, "confirmation", job.proposal.candidate_answer if job.proposal else "", False,
                                          max(0, round((terminal_at - job.timing.pending_at) * 1000)), job.proposal.provenance if job.proposal else fixture.provenance, job.identity.job_id)
                constraints = PresentationConstraints(f"response-{job.identity.input_hash[:20]}", validated_action=action)
            else:
                outcome = job_terminal_summary(job); action = job.validated_actions[0] if job.validated_actions else None
                outcome = outcome._replace(provenance=fixture.provenance) if outcome.provenance is None else outcome
                constraints = PresentationConstraints(f"response-{job.identity.input_hash[:20]}", validated_answer=job.proposal.candidate_answer if outcome.state == "completed" and job.proposal else None)
            render_started = clock.now(); response = render_response(outcome, constraints=constraints); render_ms = max(0, round((clock.now() - render_started) * 1000))
            ledger = _response_event(job.ledger, response, outcome.state, route_latency, None, action.action_hash if action else None,
                                     fixture, catalog.policy.policy_version, outcome.terminal_reason if outcome.state == "failed" else None)
            reasoner_ms = outcome.latency_ms; user_output = "One moment — I’m checking that safely.\n" + (response.text + "\n" if response.text else "")
        else:
            outcome = TerminalOutcome(decision.route, decision.route, 0, 2, decision.route, decision.route, decision.route == "chitchat", route_latency, fixture.provenance, f"fast-{decision.input_hash[:20]}")
            render_started = clock.now(); response = render_response(outcome, constraints=PresentationConstraints(f"response-{decision.input_hash[:20]}"))
            render_ms = max(0, round((clock.now() - render_started) * 1000))
            ledger = _response_event(ledger, response, "rendered", route_latency, None, None, fixture, catalog.policy.policy_version, None)
            reasoner_ms = 0; user_output = response.text + "\n" if response.text else ""
        report = verify_ledger(ledger); total_ms = max(0, round((clock.now() - started) * 1000))
        terminal_state = outcome.state if decision.route == "needs_tools" else "rendered"
        evidence = {"schema_version": CLI_EVIDENCE_VERSION, "fixture": {"id": fixture.fixture_id, "version": fixture.fixture_version, "set_version": fixture.provenance.fixture_set_version},
                    "route": {"actual": decision.route, "expected": fixture.expected.route, "policy_hash": decision.policy_hash},
                    "versions": {"thresholds": decision.thresholds_version, "calibration": CALIBRATION_VERSION, "catalog": catalog.catalog_version,
                                 "catalog_hash": catalog.catalog_hash, "policy": catalog.policy.policy_version, "policy_hash": catalog.policy.policy_hash},
                    "terminal_state": terminal_state, "ledger": {"valid_chain": report.valid_chain, "event_count": report.event_count},
                    "response": {"id": response.response_id, "channel": response.channel, "priority": response.priority, "turn_epoch": response.turn_epoch,
                                 "latency_ms": response.latency_ms, "provenance": dict(response.provenance)},
                    "timing": {"route_ms": route_latency, "reasoner_ms": reasoner_ms, "render_ms": render_ms, "total_ms": total_ms}, "response_id": response.response_id}
        if not report.valid_chain: return _failed("ledger_invalid", stderr)
        stdout.write(user_output)
        stderr.write(json.dumps(evidence, separators=(",", ":"), sort_keys=True) + "\n")
        return CLIResult(0, response.response_id, decision.route, terminal_state, True, report.event_count, MappingProxyType(evidence))
    except (OSError, ValueError, TypeError, RenderError) as error:
        return _failed("renderer_invalid" if isinstance(error, RenderError) else "fixture_policy_or_ledger_invalid", stderr)

def main(argv: Sequence[str] | None = None) -> int:
    """Run the local fixture CLI and fail closed without exposing raw internals."""
    parser = _FailClosedParser(prog="python -m talk_reasoner"); parser.add_argument("fixture", type=Path)
    try:
        arguments = parser.parse_args(argv)
    except ValueError:
        return _failed("usage_invalid", sys.stderr).exit_status
    try:
        fixture = load_fixture(arguments.fixture); return asyncio.run(run_fixture(fixture, transport=_local_transport(fixture), clock=_WallClock(), stdout=sys.stdout, stderr=sys.stderr)).exit_status
    except (OSError, ValueError):
        return _failed("invalid_fixture", sys.stderr).exit_status

class _WallClock:
    def now(self) -> float: return datetime.now(timezone.utc).timestamp()
    async def wait(self, seconds: float) -> None: await asyncio.sleep(seconds)

def _local_transport(fixture: Fixture) -> LocalScriptedTransport:
    catalog = load_action_catalog(CATALOG_PATH); decision = classify(fixture, policy=load_threshold_policy(ROUTING_POLICY_PATH)); job_id = f"job-{decision.input_hash[:20]}"
    provenance = ActionProvenance("slice0-provenance-v1", fixture.provenance.fixture_set_version, "synthetic-local", "reviewed", decision.input_hash)
    action = ActionProposal("slice0-proposal-v1", "write_state", {"key": "preferences", "value": "afternoon meetings", "terms": ["meeting"]},
                            job_id, fixture.session_id, fixture.turn_id, 0, "fixture-user", "fixture-user", "fixture://slice0",
                            "The fixture asks for one reviewed local write.", provenance, catalog.catalog_version, catalog.policy.policy_version)
    proposal = ReasonerProposal("slice0-reasoner-proposal-v1", job_id, fixture.session_id, fixture.turn_id, 0,
                                "Your local request is ready for confirmation.", (action,), None, {}, 0.94, 0.05,
                                decision.input_hash, catalog.catalog_hash, catalog.policy.policy_version,
                                ReasonerProvenance("slice0-reasoner-provenance-v1", fixture.provenance.fixture_set_version, "local-scripted-transport", "slice0-local-v1", "reviewed"))
    return LocalScriptedTransport(proposal, 0, _WallClock())
