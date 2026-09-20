from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_edge_package_is_strict_offline_and_boundary_mapped() -> None:
    manifest = json.loads((ROOT / "edge/package.json").read_text(encoding="utf-8"))
    compiler = json.loads((ROOT / "edge/tsconfig.json").read_text(encoding="utf-8"))
    audio = (ROOT / "edge/ports/audio.ts").read_text(encoding="utf-8")
    index = (ROOT / "edge/ports/index.ts").read_text(encoding="utf-8")

    assert manifest["name"] == "@talk-reasoner/edge"
    assert manifest["private"] is True and manifest["type"] == "module"
    assert "dependencies" not in manifest and "devDependencies" not in manifest
    options = compiler["compilerOptions"]
    assert options["strict"] is True and options["noEmit"] is True
    assert options["module"] == options["moduleResolution"] == "nodenext"
    assert compiler["include"] == ["ports/**/*.ts", "state/**/*.ts"]
    for token in (
        "export type ProcessingBoundary",
        "export type AudioSessionStatus",
        "export interface AudioSessionSnapshot",
        "export interface AudioSessionPort",
    ):
        assert token in audio
    assert "WebSocket" not in audio and "fetch(" not in audio and "import " not in audio
    assert index == 'export * from "./audio.js";\n'

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
    imports = re.search(r"checked:.*?(\d+) imports? resolved", output, re.S)
    assert imports is not None and int(imports.group(1)) >= 19, output
    ts_files = re.search(r"checked:.*?(\d+) ts files? checked", output, re.S)
    assert ts_files is not None and int(ts_files.group(1)) >= 2, output
