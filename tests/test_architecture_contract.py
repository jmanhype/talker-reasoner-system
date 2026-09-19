from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_implementation_wide_machinery_gate_resolves_imports_and_tests() -> None:
    completed = subprocess.run(
        ["machinery", "check", "design", "--impl", "."],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "nothing checked" not in output.casefold()
    assert "0 blocking (ERROR/DRIFT) finding(s)" in output
    g4 = re.search(r"checked:.*?(\d+) imports? resolved.*?(\d+) edges? verified", output, re.S)
    gt = re.search(r"checked:.*?(\d+) test files? scanned.*?(\d+) oracle rows", output, re.S)
    assert g4 is not None and int(g4.group(1)) >= 18 and int(g4.group(2)) >= 5, output
    assert gt is not None and int(gt.group(1)) >= 8 and int(gt.group(2)) == 62, output
    assert "7 machines covered by conformance parse" in output
