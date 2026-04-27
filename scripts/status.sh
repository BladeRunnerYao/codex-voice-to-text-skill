#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$ROOT/voice-to-text.log"
LABEL="com.codex.voice-to-text"
GUI_TARGET="gui/$(id -u)"

if launchctl print "$GUI_TARGET/$LABEL" >/dev/null 2>&1; then
  echo "voice-to-text is loaded as $LABEL"
  launchctl print "$GUI_TARGET/$LABEL" | awk '/pid =|state =|last exit code =/ { print }'
else
  echo "voice-to-text is not loaded"
fi

if [ -f "$LOG_FILE" ]; then
  echo
  echo "Recent logs:"
  tail -n 40 "$LOG_FILE"
fi
