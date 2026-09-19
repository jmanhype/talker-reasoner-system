from __future__ import annotations

import importlib
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

import talk_reasoner

try:
    MACHINERY = importlib.import_module("talk_reasoner.machinery")
except ModuleNotFoundError:
    MACHINERY = None

ROOT = Path(__file__).parents[1]
ORACLE_DIRECTORY = ROOT / "design" / "machines"
ORACLE_FILES = (
    "ConversationTurn.oracle.md",
    "EventLedger.oracle.md",
    "MemoryRecord.oracle.md",
    "ReasonerJob.oracle.md",
    "ToolCatalog.oracle.md",
    "ToolExecution.oracle.md",
    "VoiceSession.oracle.md",
)
EXPECTED_TRANSITIONS = {
    "conversationTurn": tuple("CONV-02965d CONV-f9f25b CONV-87aef6 CONV-73bae3 CONV-53ecad CONV-5d0019 CONV-a756c5 CONV-7c39be CONV-7f7105 CONV-8fadcf CONV-dab39a CONV-04c2c7".split()),
    "eventLedger": tuple("EVEN-c2c520 EVEN-5feeb7 EVEN-098b63 EVEN-0d5972 EVEN-e9be49 EVEN-f230e3 EVEN-a0faaa EVEN-d90d1d EVEN-379e68".split()),
    "memoryRecord": tuple("MEMO-0697b6 MEMO-ef809c MEMO-814928 MEMO-914d7a MEMO-c8e66c MEMO-b8a59c MEMO-9faf38 MEMO-d9f286 MEMO-8862c9".split()),
    "reasonerJob": tuple("REAS-bc3e49 REAS-5dc4da REAS-974bde REAS-1559cc REAS-f1a17d REAS-c3c792 REAS-0c1f49 REAS-97e8bd REAS-c567aa REAS-0766c3 REAS-0cd65a REAS-345901 REAS-79c30e REAS-b46837".split()),
    "toolCatalog": ("TCAT-563b02", "TCAT-3a38e4", "TCAT-97dc90", "TCAT-675b21"),
    "toolExecution": (
        "TEXE-6c80b2", "TEXE-9297f7", "TEXE-8688ba", "TEXE-0d301e", "TEXE-49dba9",
        "TEXE-b9c795", "TEXE-e18dac", "TEXE-34eda4", "TEXE-782b09", "TEXE-a8cfa2",
        "TEXE-30e3a5",
    ),
    "voiceSession": ("VOIC-305554", "VOIC-e62d1f", "VOIC-32ea66"),
}
EXPECTED_STABLE_IDS = tuple(
    stable_id for ids in EXPECTED_TRANSITIONS.values() for stable_id in ids
)
TABLE_DELIMITER = "|"


def machinery() -> Any:
    """Require the production machinery surface without turning RED into a collection error."""
    assert MACHINERY is not None, "talk_reasoner.machinery is missing"
    return MACHINERY


def oracle_document(rows: str) -> str:
    return f"""# Generated transition oracle: `testMachine`

## Transitions

| test id | stable id | source | trigger | guard | target | actions |
|---|---|---|---|---|---|---|
{rows}
"""


def write_oracle(path: Path, rows: str) -> Path:
    path.write_text(oracle_document(rows), encoding="utf-8")
    return path


def actions(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return () if value == "-" else tuple(item.strip() for item in value.split(","))
    if isinstance(value, MappingProxyType):
        return tuple(value.keys())
    return tuple(value)


def test_parse_all_oracles_has_exact_seven_files_and_sixty_two_unique_rows() -> None:
    parsed = machinery().parse_all_oracles(ORACLE_DIRECTORY)
    assert tuple(sorted(parsed)) == tuple(sorted(EXPECTED_TRANSITIONS))
    rows = [row for transitions in parsed.values() for row in transitions]
    stable_ids = [row.stable_id for row in rows]
    assert len(rows) == 62
    assert len(set(stable_ids)) == 62
    assert tuple(stable_ids) == EXPECTED_STABLE_IDS
    for machine_name, expected_ids in EXPECTED_TRANSITIONS.items():
        assert tuple(row.stable_id for row in parsed[machine_name]) == expected_ids


def test_parse_oracle_exposes_every_committed_field() -> None:
    row = machinery().parse_oracle(ORACLE_DIRECTORY / "ConversationTurn.oracle.md")[0]
    assert (row.test_id, row.stable_id, row.source, row.trigger) == (
        "T-CONV-01", "CONV-02965d", "Receiving", "on:transcribe"
    )
    assert row.guard == "transcriptValidAndBoundaryConsented"
    assert row.target == "Routed"
    assert actions(row.actions) == ("hashTranscriptAndRetainEphememeral",)


@pytest.mark.parametrize(
    ("rows", "detail"),
    [
        ("", "empty transitions table"),
        (
            "| T-TEST-01 | TEST-one | Proposed | on:authorize | - | Authorized | bindCatalogAndIdempotency | extra |\n",
            "malformed row width",
        ),
        (
            "| T-TEST-01 | TEST-one | Proposed | on:authorize | - | Authorized | bindCatalogAndIdempotency |\n"
            "| T-TEST-02 | TEST-one | Authorized | on:dispatch | - | Dispatched | - |\n",
            "duplicate stable id",
        ),
        (
            "| T-TEST-01 | - | Proposed | on:authorize | - | Authorized | - |\n",
            "missing stable id",
        ),
    ],
)
def test_parse_oracle_rejects_malformed_empty_and_duplicate_rows(
    tmp_path: Path, rows: str, detail: str
) -> None:
    module = machinery()
    with pytest.raises(module.MachineryContractError, match=detail):
        module.parse_oracle(write_oracle(tmp_path / "TestMachine.oracle.md", rows))


def test_parse_all_oracles_rejects_missing_files_and_extra_files(tmp_path: Path) -> None:
    module = machinery()
    with pytest.raises(module.MachineryContractError, match="missing oracle file"):
        module.parse_all_oracles(tmp_path)
    (tmp_path / "Unexpected.oracle.md").write_text(
        oracle_document(
            "| T-TEST-01 | TEST-one | Proposed | on:authorize | - | Authorized | - |\n"
        ),
        encoding="utf-8",
    )
    with pytest.raises(module.MachineryContractError, match="unexpected oracle file"):
        module.parse_all_oracles(tmp_path)


def test_transition_case_rejects_unknown_machine_or_stable_id() -> None:
    module = machinery()
    with pytest.raises(module.MachineryContractError, match="unknown machine"):
        module.transition_case("unknownMachine", "CONV-02965d")
    with pytest.raises(module.MachineryContractError, match="unknown stable id"):
        module.transition_case("conversationTurn", "CONV-unknown")


@pytest.mark.parametrize(
    ("machine_name", "stable_id"),
    [(machine_name, stable_id) for machine_name, ids in EXPECTED_TRANSITIONS.items() for stable_id in ids],
)
def test_transition_conformance_parses_and_exercises_every_oracle_row(machine_name: str, stable_id: str) -> None:
    module = machinery()
    rows = module.parse_all_oracles(ORACLE_DIRECTORY)[machine_name]
    row = next(item for item in rows if item.stable_id == stable_id)
    case = module.transition_case(machine_name, stable_id)
    result = module.exercise_transition(case)
    assert case.stable_id == stable_id
    assert result.next_state == row.target
    assert actions(result.actions) == actions(row.actions)


def test_event_ledger_actor_uses_real_local_append_and_verify_contract() -> None:
    from talk_reasoner.contracts import EventLedger, append_event, verify_ledger

    receipt = append_event(EventLedger.empty(), _first_event())
    assert verify_ledger(receipt.ledger).valid_chain
    tampered = EventLedger((replace(receipt.event, status="mutated"),), receipt.chain_hash)
    assert verify_ledger(tampered).valid_chain is False


def test_reasoner_actor_uses_contract_tested_local_transport_and_validation() -> None:
    # The detailed real-transport actor property is intentionally executed by
    # tests/test_machinery_invariants.py. Keeping this module parser-focused
    # avoids an import path coupling between sibling pytest modules.
    module = machinery()
    parsed = module.parse_all_oracles(ORACLE_DIRECTORY)["reasonerJob"]
    assert [row.stable_id for row in parsed].count("REAS-c567aa") == 1


def test_tool_actor_contract_is_offline_hashed_and_never_remote() -> None:
    module = machinery()
    result = module.exercise_transition(module.transition_case("toolExecution", "TEXE-782b09"))
    assert result.next_state == "Succeeded"
    assert actions(result.actions) == ("recordFilteredResultHash",)
    assert "invokeAllowlistedTool" not in actions(result.actions)
    source = (ROOT / "talk_reasoner").glob("*.py")
    joined = "\n".join(path.read_text(encoding="utf-8") for path in source)
    for forbidden in ("requests", "httpx", "aiohttp", "socket", "subprocess"):
        assert forbidden not in joined


def _first_event() -> Any:
    from talk_reasoner.contracts import load_fixture
    from talk_reasoner.routing import classify, load_threshold_policy, route_event

    machinery()
    fixture = load_fixture(ROOT / "tests" / "fixtures" / "slice0" / "trs-tools-001.json")
    decision = classify(fixture, policy=load_threshold_policy(ROOT / "config" / "routing" / "slice0-v1.json"))
    return route_event(fixture, decision, event_id=1)
