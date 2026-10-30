#!/usr/bin/env bash
set -euo pipefail
worktree="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export STOPOTS_RUNTIME="${STOPOTS_RUNTIME:-$(dirname "$worktree")/.runtime}"
export PYTHONPATH="$worktree/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$(dirname "$worktree")/.runtime/venv-desktop/bin/python" -m stopots_v2.desktop "$@"
