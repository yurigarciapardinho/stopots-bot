#!/usr/bin/env bash
set -euo pipefail
test "${GITHUB_ACTIONS:-}" = true
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends libegl1 libgl1 libopengl0 libfontconfig1 libxkbcommon0 libxkbcommon-x11-0 libxcb-cursor0 libxcb-shape0 xvfb
