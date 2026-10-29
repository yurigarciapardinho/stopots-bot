#!/usr/bin/env bash
set -euo pipefail
worktree="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_root="$(dirname -- "$worktree")"
export UV_CACHE_DIR="$task_root/.runtime/uv-cache"
export PIP_CACHE_DIR="$task_root/.runtime/pip-cache"
export PLAYWRIGHT_BROWSERS_PATH="$task_root/.runtime/browsers"
export TMPDIR="$task_root/.runtime/tmp"
mkdir -p "$TMPDIR"
if [[ "${1:-}" == "testar" ]]; then
    cd "$worktree"
    exec "$task_root/.runtime/venv/bin/python" -m pytest -q tests/lab
fi
exec "$task_root/.runtime/venv/bin/python" "$worktree/tools/stopots_lab.py" "${@:-doctor}"
