#!/usr/bin/env bash
set -euo pipefail
worktree="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_root="$(dirname -- "$worktree")"
export UV_CACHE_DIR="$task_root/.runtime/uv-cache"
export PIP_CACHE_DIR="$task_root/.runtime/pip-cache"
export PLAYWRIGHT_BROWSERS_PATH="$task_root/.runtime/browsers"
export UV_PYTHON_DOWNLOADS=never
export TMPDIR="$task_root/.runtime/tmp"
mkdir -p "$TMPDIR"
[[ -x "$task_root/.runtime/venv/bin/python" ]] || uv venv --python /usr/bin/python3 "$task_root/.runtime/venv"
uv pip sync --python "$task_root/.runtime/venv/bin/python" "$worktree/requirements-lab.lock"
exec "$worktree/scripts/lab.sh" doctor
