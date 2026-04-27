#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required to install whisper-cpp."
  echo "Install Homebrew first: https://brew.sh/"
  exit 2
fi

if ! command -v whisper-cli >/dev/null 2>&1; then
  brew install whisper-cpp
fi

"$ROOT/scripts/install_deps.sh"
"$ROOT/scripts/download_model.sh" tiny

echo "voice-to-text install complete."
echo "Run: $ROOT/scripts/start.sh"
