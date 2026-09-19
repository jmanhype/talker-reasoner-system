#!/bin/sh
set -eu

if [ ! -x .venv/bin/python ] || ! .venv/bin/python -m pytest --version >/dev/null 2>&1; then
    uv venv --clear --python "${PYTHON:-$(command -v python3.12)}" .venv
    uv pip install --offline --python .venv/bin/python 'pytest>=9,<10'
fi
