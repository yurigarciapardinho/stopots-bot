#!/usr/bin/env bash
set -euo pipefail
worktree="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
python_path="${STOPOTS_PYTHON:-$worktree/.venv/bin/python}"
exec "$python_path" -m stopots_v2.desktop "$@"
