#!/usr/bin/env bash
set -euo pipefail
worktree="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_root="$(dirname -- "$worktree")"
export STOPOTS_RUNTIME="$task_root/.runtime"
export PLAYWRIGHT_BROWSERS_PATH="$STOPOTS_RUNTIME/browsers"
export PYTHONPATH="$worktree/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$STOPOTS_RUNTIME/venv/bin/python" -m stopots_v2 "$@"
