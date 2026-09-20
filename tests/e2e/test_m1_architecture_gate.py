from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from talk_reasoner.machinery import parse_all_oracles, parse_invariant_ids

ROOT = Path(__file__).parents[2]
ORACLE_DIRECTORY = ROOT / "design" / "machines"
DOMAIN_RENDER = ROOT / "design" / "domain.modelith.md"
REPORT_FIXTURE = ROOT / "tests" / "e2e" / "fixtures" / "m1-report.json"
FORBIDDEN_LIVE_IMPORTS = {
    "network": {"requests", "httpx", "aiohttp", "socket"},
    "credential-store": {"keyring", "vault"},
    "durable-service": {"redis", "psycopg", "asyncpg", "sqlalchemy"},
    "remote-tool": {"magg", "contextforge", "dagger", "treg"},
    "semantic-memory": {"letta", "mem0", "cognee", "graphiti"},
}


def _run(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60, check=False)
    output = completed.stdout + completed.stderr
    return {"command": " ".join(command), "exit_code": completed.returncode, "output": output,
            "output_tail": output.strip().splitlines()[-6:]}


def _python_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def _live_dependency_classes() -> list[str]:
    roots = [_python_roots(path) for path in (ROOT / "talk_reasoner").rglob("*.py")]
    roots.extend(_python_roots(path) for path in (ROOT / "tests").rglob("*.py"))
    for path in (ROOT / "edge").rglob("*.ts"):
        source = path.read_text(encoding="utf-8")
        roots.append({match for match in re.findall(r"(?:import|from)\s+([^'\"]+)", source)})
    return sorted(kind for kind, forbidden in FORBIDDEN_LIVE_IMPORTS.items() if any(values & forbidden for values in roots))


def _collected_tests() -> tuple[int, int]:
    completed = subprocess.run([sys.executable, "-m", "pytest", "-q", "--collect-only"], cwd=ROOT,
                               text=True, capture_output=True, timeout=60, check=False)
    count = sum(line.startswith("tests/") and "::" in line for line in completed.stdout.splitlines())
    return completed.returncode, count


def _version(command: list[str]) -> str:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=30, check=True)
    return completed.stdout.strip().splitlines()[-1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gate_metrics() -> tuple[dict[str, Any], dict[str, int], str]:
    gate = _run(["machinery", "check", "design", "--impl", "."])
    full_output = gate["output"]
    g4 = re.search(r"checked:.*?(?P<ts>\d+) ts files checked, (?P<imports>\d+) imports resolved.*?(?P<python>\d+) python files checked, (?P<skipped_tests>\d+) test files skipped, (?P<edges>\d+) edges verified, (?P<baseline>\d+) baselined edges, (?P<ratchet>\d+) ratcheted edges", full_output, re.S)
    gt = re.search(r"checked:.*?(?P<tests>\d+) test files scanned, (?P<machines>\d+) machines, (?P<rows>\d+) oracle rows", full_output, re.S)
    assert g4 is not None and gt is not None, full_output
    return gate, {key: int(value) for key, value in {**g4.groupdict(), **gt.groupdict()}.items()}, full_output


def _has_exact_explicit_debt(metrics: dict[str, int], ratchet: dict[str, Any]) -> bool:
    expected = {
        "trs.reasoning -> trs.routing": ["talk_reasoner/jobs.py"],
        "trs.renderer -> trs.action-governor": ["talk_reasoner/cli.py", "talk_reasoner/rendering.py"],
        "trs.renderer -> trs.reasoning": ["talk_reasoner/cli.py", "talk_reasoner/rendering.py"],
        "trs.renderer -> trs.routing": ["talk_reasoner/cli.py"],
    }
    return metrics["baseline"] == metrics["ratchet"] == 4 and ratchet["edges"] == expected


def _edge_manifest_is_dependency_free(manifest: dict[str, Any]) -> bool:
    return manifest["private"] is True and "dependencies" not in manifest and "devDependencies" not in manifest


def test_complete_m1_architecture_gate_emits_pass_report() -> None:
    started = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    gate, metrics, full_output = _gate_metrics()
    ratchet = json.loads((ROOT / "design/ratchet.json").read_text(encoding="utf-8"))
    oracles = parse_all_oracles(ORACLE_DIRECTORY)
    invariants = parse_invariant_ids(DOMAIN_RENDER)
    transitions = [row for rows in oracles.values() for row in rows]
    collection_exit, collected_tests = _collected_tests()
    live_dependencies = _live_dependency_classes()
    manifest = json.loads((ROOT / "edge/package.json").read_text(encoding="utf-8"))
    ended = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    conditions = {
        "gate_green": gate["exit_code"] == 0 and "0 blocking (ERROR/DRIFT) finding(s)" in full_output,
        "imports_resolved": metrics["imports"] == 21,
        "allowed_edges": metrics["edges"] == 5,
        "explicit_debt": _has_exact_explicit_debt(metrics, ratchet),
        "python_and_ts_checked": metrics["python"] == 8 and metrics["ts"] == 5,
        "oracle_tests_scanned": metrics["tests"] == 15 and metrics["machines"] == 7 and metrics["rows"] == 62,
        "exact_denominators": len(oracles) == 7 and len(transitions) == 62 and len(invariants) == 36,
        "suite_collected": collection_exit == 0 and collected_tests == 362,
        "edge_dependency_free": _edge_manifest_is_dependency_free(manifest),
        "no_live_dependencies": not live_dependencies,
    }
    report = {
        "schema_version": "trs-m1-architecture-report-v1",
        "imports_resolved": metrics["imports"],
        "allowed_edges_verified": metrics["edges"],
        "baseline_edge_count": metrics["baseline"],
        "ratcheted_edge_count": metrics["ratchet"],
        "python_files_checked": metrics["python"],
        "ts_files_checked": metrics["ts"],
        "test_files_scanned": metrics["tests"],
        "machine_count": len(oracles),
        "transition_count": len(transitions),
        "invariant_count": len(invariants),
        "collected_test_count": collected_tests,
        "live_dependency_classes": live_dependencies,
        "conditions": conditions,
        "tool_versions": {"machinery": _version(["machinery", "--version"]), "modelith": _version(["modelith", "--version"])},
        "configuration_hashes": {str(path.relative_to(ROOT)): _sha256(path) for path in (
            ROOT / "design/ARCHITECTURE.md", ROOT / "design/ratchet.json", ROOT / "edge/package.json")},
        "commands": {"machinery_check_impl": gate},
        "utc_window": {"started_at": started, "ended_at": ended},
        "decision": "pass" if all(conditions.values()) else "hold",
    }
    expected = json.loads(REPORT_FIXTURE.read_text(encoding="utf-8"))
    assert {key: report[key] for key in expected} == expected
    print(json.dumps(report, indent=2, sort_keys=True))
    assert report["decision"] == "pass", json.dumps({"report": report, "gate_output": full_output}, indent=2)
