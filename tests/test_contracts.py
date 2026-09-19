from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from talk_reasoner.contracts import EventLedger, LedgerEvent, append_event, canonical_event_bytes, load_fixture, load_fixture_corpus, scoped_hash, verify_ledger

FIXTURES = Path(__file__).parent / "fixtures" / "slice0"
PATHS = sorted(FIXTURES.glob("*.json"))
ROUTES = ("chitchat", "needs_tools", "unclear")
CREDENTIAL_PATTERNS = (re.compile(r"(?i)(api[_-]?key|password|passwd|secret|bearer\s+|access[_-]?token|authorization)"), re.compile(r"AKIA[0-9A-Z]{16}"), re.compile(r"sk-[A-Za-z0-9_-]{16,}"))
PLATFORM_IMPORTS = ("requests", "httpx", "aiohttp", "socket", "redis", "psycopg", "letta", "mem0", "cognee")


def read_fixture(fixture_id: str) -> dict[str, Any]:
    return json.loads((FIXTURES / f"{fixture_id}.json").read_text(encoding="utf-8"))
def write_invalid(record: dict[str, Any], path: Path, **changes: Any) -> Path:
    record = dict(record) | changes
    path.write_text(json.dumps(record), encoding="utf-8")
    return path
def input_hash(value: str, *, version: str = "input-v1") -> str:
    return scoped_hash(value, scope="fixture-input", schema_version=version)
def event(event_id: int, event_type: str, session_id: str, turn_id: str, *, job_id: str | None = None,
          status: str = "recorded", action_hash: str | None = None,
          prior_event_id: int | None = None, prior_event_hash: str | None = None) -> LedgerEvent:
    sequence = event_id - 1
    return LedgerEvent(
        schema_version="slice0-event-v1", event_type=event_type, event_version="1.0.0",
        event_id=event_id, session_id=session_id, turn_id=turn_id, job_id=job_id,
        turn_epoch=sequence, input_hash=input_hash(f"{session_id}:{turn_id}:{event_type}"),
        content_length=42, media_type="text/plain", consent_version="consent-v1",
        policy_version="policy-v1", status=status, rejection_reason=None, latency_ms=12 + sequence,
        action_hash=action_hash, prior_event_id=prior_event_id,
        prior_event_hash=prior_event_hash, event_chain_hash=None,
    )
def valid_ledger() -> EventLedger:
    first = append_event(EventLedger.empty(), event(1, "route", "session-a", "turn-a", status="selected")).event
    second = append_event(EventLedger((first,)), event(2, "action", "session-a", "turn-a", job_id="job-a", status="validated", action_hash=input_hash("action", version="action-v1"), prior_event_id=1, prior_event_hash=first.event_chain_hash)).event
    third = append_event(EventLedger((first, second)), event(3, "lifecycle", "session-a", "turn-a", job_id="job-a", status="completed", prior_event_id=2, prior_event_hash=second.event_chain_hash)).event
    return append_event(EventLedger((first, second, third)), event(4, "response", "session-a", "turn-a", status="rendered", prior_event_id=3, prior_event_hash=third.event_chain_hash)).ledger


def test_valid_corpus_is_frozen_deterministic_and_balanced() -> None:
    corpus = load_fixture_corpus(PATHS)
    assert len(corpus.fixtures) >= 18
    assert {route: sum(f.expected.route == route for f in corpus.fixtures) for route in ROUTES} == {
        "chitchat": 6, "needs_tools": 6, "unclear": 6,
    }
    assert corpus.fixtures == tuple(sorted(corpus.fixtures, key=lambda item: item.fixture_id))
    with pytest.raises(Exception):
        corpus.fixtures[0].transcript = "mutated"


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"schema_version": "unknown-v9"}, "unsupported schema_version"),
        ({"fixture_id": "bad id"}, "invalid fixture_id"),
        ({"consent": {"routing": True}}, "consent"),
        ({"provenance": {"source": "synthetic-local"}}, "provenance"),
        ({"expected": dict(read_fixture("trs-chitchat-001")["expected"], route="search")}, "route"),
        ({"transcript": "here is password: hunter2"}, "credential"),
        ({"bounded_context": dict(read_fixture("trs-chitchat-001")["bounded_context"], max_entries=99)}, "bounded"),
    ],
)
def test_malformed_fixtures_fail_closed(tmp_path: Path, changes: dict[str, Any], message: str) -> None:
    path = write_invalid(read_fixture("trs-chitchat-001"), tmp_path / "invalid.json", **changes)
    with pytest.raises(ValueError, match=message):
        load_fixture(path)


def test_duplicate_fixture_ids_and_duplicate_json_keys_fail(tmp_path: Path) -> None:
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    first.write_text((FIXTURES / "trs-chitchat-002.json").read_text(encoding="utf-8"), encoding="utf-8")
    second.write_text((FIXTURES / "trs-chitchat-002.json").read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate fixture_id"):
        load_fixture_corpus([first, second])

    (tmp_path / "duplicate-key.json").write_text('{"schema_version":"a","schema_version":"b"}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"): load_fixture(tmp_path / "duplicate-key.json")


def test_scoped_hash_is_stable_and_metadata_scoped() -> None:
    first = scoped_hash("same input", scope="fixture-input", schema_version="v1")
    digest = hashlib.sha256(b'{"content":"same input","content_encoding":"utf8","schema_version":"v1","scope":"fixture-input"}').hexdigest()
    assert first == digest
    assert scoped_hash("same input", scope="fixture-input", schema_version="v1") == first
    assert scoped_hash(b"same input", scope="fixture-input", schema_version="v1") == first
    assert len(first) == 64 and first == first.lower()
    assert scoped_hash("same input", scope="event-chain", schema_version="v1") != first
    assert scoped_hash("same input", scope="fixture-input", schema_version="v2") != first
    assert scoped_hash("new input", scope="fixture-input", schema_version="v1") != first
    assert "same input" not in first


def test_canonical_event_bytes_is_sorted_compact_and_excludes_chain() -> None:
    base = event(1, "route", "session-a", "turn-a")
    stored = replace(base, event_chain_hash="0" * 64)
    assert canonical_event_bytes(base) == canonical_event_bytes(stored)
    assert canonical_event_bytes(base) == json.dumps(
        {key: value for key, value in base.to_mapping().items() if key != "event_chain_hash"},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")


def test_append_event_is_immutable_and_validates_order_and_links() -> None:
    ledger = valid_ledger()
    assert len(ledger.events) == 4 and ledger.head_hash == ledger.events[-1].event_chain_hash
    with pytest.raises(ValueError, match="event_id.*must be 5"):
        append_event(ledger, event(6, "response", "session-a", "turn-a"))
    with pytest.raises(ValueError, match="prior_event_id.*must be 4"):
        append_event(ledger, event(5, "response", "session-a", "turn-a", prior_event_id=2,
                                   prior_event_hash=ledger.head_hash))
    with pytest.raises(ValueError, match="prior_event_hash.*does not match ledger head"):
        append_event(ledger, event(5, "response", "session-a", "turn-a", prior_event_id=4,
                                   prior_event_hash="0" * 64))
    with pytest.raises(ValueError, match="action_hash"):
        append_event(ledger, event(5, "action", "session-a", "turn-a", job_id="job-b"))
    assert len(ledger.events) == 4


def test_ledger_verifies_detects_integrity_defects() -> None:
    report = verify_ledger(valid_ledger())
    assert report.valid_chain and report.event_count == 4
    assert report.gaps == report.invalid_prior_hashes == report.duplicate_terminal_states == report.mutations == ()
    events = valid_ledger().events
    gap = verify_ledger(EventLedger((events[0], events[2], events[3])))
    assert gap.valid_chain is False and gap.gaps == (2,)
    bad_prior = replace(events[1], prior_event_hash="0" * 64)
    bad_report = verify_ledger(EventLedger((events[0], bad_prior, events[2], events[3])))
    assert bad_report.valid_chain is False and bad_report.invalid_prior_hashes == (2,)
    duplicate = replace(events[3], event_id=5, prior_event_id=events[3].event_id,
                        prior_event_hash=events[3].event_chain_hash, event_chain_hash=None)
    duplicate_report = verify_ledger(append_event(EventLedger(events), duplicate).ledger)
    assert duplicate_report.valid_chain is False and duplicate_report.duplicate_terminal_states
    tampered = replace(events[1], status="mutated")
    tampered_report = verify_ledger(EventLedger((events[0], tampered, events[2], events[3])))
    assert tampered_report.valid_chain is False and tampered_report.mutations == (2,)


def test_complete_corpus_integration_proves_privacy_and_local_dependencies() -> None:
    corpus = load_fixture_corpus(PATHS)
    ledger = EventLedger.empty()
    for fixture in corpus.fixtures:
        receipt = append_event(ledger, event(
            ledger.event_count + 1, "route", fixture.session_id, fixture.turn_id,
            status="selected", prior_event_id=ledger.events[-1].event_id if ledger.events else None,
            prior_event_hash=ledger.head_hash,
        ))
        ledger = receipt.ledger
        if fixture.expected.route == "needs_tools":
            for event_type, status in (("action", "validated"), ("lifecycle", "completed"), ("response", "rendered")):
                ledger = append_event(ledger, event(
                    ledger.event_count + 1, event_type, fixture.session_id, fixture.turn_id,
                    job_id=f"job-{fixture.fixture_id}", status=status,
                    action_hash=input_hash(f"action-{fixture.fixture_id}", version="action-v1") if event_type == "action" else None,
                    prior_event_id=ledger.events[-1].event_id, prior_event_hash=ledger.head_hash,
                )).ledger
    report = verify_ledger(ledger)
    assert report.valid_chain and report.event_count == 36
    ledger_bytes = b"".join(canonical_event_bytes(item) for item in ledger.events)
    assert all(fixture.transcript.encode() not in ledger_bytes for fixture in corpus.fixtures)
    assert b'"transcript"' not in ledger_bytes and b'"raw_content"' not in ledger_bytes

    fixture_bytes = b"".join(path.read_bytes() for path in PATHS)
    assert not [pattern.pattern for pattern in CREDENTIAL_PATTERNS if pattern.search(fixture_bytes.decode())]
    source_files = list(Path(__import__("talk_reasoner.contracts", fromlist=[""]).__file__).parent.glob("*.py"))
    assert not [
        (path.name, name)
        for path in source_files
        for name in PLATFORM_IMPORTS
        if re.search(rf"(?m)^\s*(import|from)\s+{name}\b", path.read_text(encoding="utf-8"))
    ]
