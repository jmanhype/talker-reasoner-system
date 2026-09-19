from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from talk_reasoner.machinery import exercise_transition, parse_all_oracles, parse_invariant_ids, transition_case

ROOT = Path(__file__).parents[2]
ORACLE_DIRECTORY = ROOT / "design" / "machines"
DOMAIN_RENDER = ROOT / "design" / "domain.modelith.md"
REPORT_FIXTURE = ROOT / "tests" / "e2e" / "fixtures" / "m0-report.json"
FORBIDDEN_LIVE_IMPORTS = {
    "network": {"requests", "httpx", "aiohttp", "socket"},
    "credential-store": {"keyring", "vault"},
    "durable-service": {"redis", "psycopg", "asyncpg", "sqlalchemy"},
    "remote-tool": {"magg", "contextforge", "dagger", "treg"},
    "semantic-memory": {"letta", "mem0", "cognee", "graphiti"},
}
GATE_COMMANDS = {
    "modelith_lint": ["modelith", "lint", "design/domain.modelith.yaml", "--completeness", "error"],
    "machinery_lint": ["machinery", "lint", "design/machines"],
    "machinery_check": ["machinery", "check", "design"],
}


def _run(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60, check=False)
    return {
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-4:],
        "stderr_tail": completed.stderr.strip().splitlines()[-4:],
    }


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def _live_dependency_classes() -> list[str]:
    roots_by_path = {path: _import_roots(path) for path in list((ROOT / "talk_reasoner").rglob("*.py")) + list((ROOT / "tests").rglob("*.py"))}
    return sorted(
        dependency_class
        for dependency_class, forbidden in FORBIDDEN_LIVE_IMPORTS.items()
        if any(roots & forbidden for roots in roots_by_path.values())
    )


def _version(command: list[str]) -> str:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=30, check=True)
    return completed.stdout.strip().splitlines()[-1]


def _collected_test_inventory() -> tuple[int, int]:
    collection = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--collect-only"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    count = sum(line.startswith(("tests/", "./tests/")) and "::" in line for line in collection.stdout.splitlines())
    return collection.returncode, count


def _all_transitions_conform(oracles: dict[str, tuple[Any, ...]]) -> bool:
    results = [exercise_transition(transition_case(machine_name, row.stable_id)) for machine_name, rows in oracles.items() for row in rows]
    rows = [row for machine_rows in oracles.values() for row in machine_rows]
    return all(result.next_state == row.target and tuple(result.actions) == tuple(row.actions) for result, row in zip(results, rows, strict=True))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_complete_offline_m0_gate_emits_exact_pass_report() -> None:
    started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    commands = {name: _run(command) for name, command in GATE_COMMANDS.items()}
    oracles = parse_all_oracles(ORACLE_DIRECTORY)
    invariants = parse_invariant_ids(DOMAIN_RENDER)
    transitions = [row for rows in oracles.values() for row in rows]
    collection_exit_code, collected_test_count = _collected_test_inventory()
    live_dependency_classes = _live_dependency_classes()
    ended_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    conditions = {
        "gates_green": all(result["exit_code"] == 0 for result in commands.values()),
        "seven_files": len(oracles) == 7 and len(list(ORACLE_DIRECTORY.glob("*.oracle.md"))) == 7,
        "sixty_two_unique": len(transitions) == 62 and len({row.stable_id for row in transitions}) == 62,
        "thirty_six_invariants": len(invariants) == 36 and len(set(invariants)) == 36,
        "all_transitions_conform": _all_transitions_conform(oracles),
        "complete_suite_collected": collection_exit_code == 0 and collected_test_count == 328,
        "no_live_dependencies": not live_dependency_classes,
    }
    report = {
        "schema_version": "trs-m0-offline-report-v1",
        "machine_names": list(oracles),
        "oracle_file_count": len(oracles),
        "transition_count": len(transitions),
        "invariant_count": len(invariants),
        "collected_test_count": collected_test_count,
        "live_dependency_classes": live_dependency_classes,
        "conditions": conditions,
        "tool_versions": {
            "modelith": _version(["modelith", "--version"]),
            "machinery": _version(["machinery", "--version"]),
        },
        "configuration_hashes": {
            str(path.relative_to(ROOT)): _sha256(path)
            for path in (
                ROOT / "design" / "domain.modelith.yaml",
                ROOT / "config" / "routing" / "slice0-v1.json",
                ROOT / "config" / "actions" / "slice0-v1.json",
            )
        },
        "commands": commands,
        "utc_window": {"started_at": started_at, "ended_at": ended_at},
        "decision": "pass" if all(conditions.values()) else "hold",
    }
    expected = json.loads(REPORT_FIXTURE.read_text(encoding="utf-8"))
    assert {key: report[key] for key in expected} == expected
    print(json.dumps(report, indent=2, sort_keys=True))
    assert report["decision"] == "pass", json.dumps({"report": report, "expected": expected}, indent=2)
