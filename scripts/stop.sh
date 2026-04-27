#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.codex.voice-to-text"
PLIST="$ROOT/$LABEL.plist"
GUI_TARGET="gui/$(id -u)"

if launchctl print "$GUI_TARGET/$LABEL" >/dev/null 2>&1; then
  launchctl bootout "$GUI_TARGET" "$PLIST"
  echo "voice-to-text stopped and unloaded"
else
  echo "voice-to-text is not loaded"
fi
rm -f "$ROOT/voice-to-text.pid"
