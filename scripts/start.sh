#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$ROOT/voice-to-text.log"
VENV="$ROOT/.venv"
LABEL="com.codex.voice-to-text"
PLIST="$ROOT/$LABEL.plist"
GUI_TARGET="gui/$(id -u)"

if launchctl print "$GUI_TARGET/$LABEL" >/dev/null 2>&1; then
  echo "voice-to-text is already loaded as $LABEL"
  exit 0
fi

if [ ! -x "$VENV/bin/python" ]; then
  "$ROOT/scripts/install_deps.sh"
fi

mkdir -p "$ROOT/models" "$ROOT/tmp"

MODEL_PATH="${VTT_MODEL_PATH:-$ROOT/models/ggml-tiny.bin}"
if [ ! -f "$MODEL_PATH" ]; then
  echo "Missing Whisper model: $MODEL_PATH"
  echo "Download one first, for example:"
  echo "curl -L https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin -o '$MODEL_PATH'"
  exit 2
fi

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$VENV/bin/python</string>
    <string>$ROOT/scripts/voice_to_text.py</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <false/>
  <key>StandardOutPath</key>
  <string>$LOG_FILE</string>
  <key>StandardErrorPath</key>
  <string>$LOG_FILE</string>
  <key>WorkingDirectory</key>
  <string>$ROOT</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>VTT_BEEP</key>
    <string>0</string>
  </dict>
  <key>LimitLoadToSessionType</key>
  <string>Aqua</string>
</dict>
</plist>
PLIST

launchctl bootstrap "$GUI_TARGET" "$PLIST"
launchctl kickstart -k "$GUI_TARGET/$LABEL"
echo "voice-to-text loaded as $LABEL"
echo "Logs: $LOG_FILE"
