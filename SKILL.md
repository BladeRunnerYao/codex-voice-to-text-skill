---
name: voice-to-text
description: Start, stop, install, or troubleshoot a local macOS push-to-talk voice-to-text dictation service using the right Command key and whisper.cpp. Use when the user says "start voice to text", "stop voice to text", asks for local Whisper dictation, or wants the background transcription service managed.
metadata:
  short-description: Local Whisper push-to-talk dictation
---

# Voice To Text

Use this skill to manage the local macOS push-to-talk dictation daemon.

## Commands

- Install runtime dependencies and default model: `scripts/install.sh`
- Start the background service: `scripts/start.sh`
- Stop the background service: `scripts/stop.sh`
- Check status and recent logs: `scripts/status.sh`
- Install Python dependencies into the skill venv: `scripts/install_deps.sh`
- Download a GGML model: `scripts/download_model.sh tiny`

Run scripts from this skill directory:

```bash
cd /Users/yao/.codex/skills/voice-to-text
scripts/start.sh
```

## Behavior

- Hold the right Command key to start recording.
- The daemon plays a start sound when recording begins.
- Release the right Command key to stop recording.
- The daemon plays an end sound, transcribes with local Whisper, copies the text to the clipboard, and pastes it into the active app.
- The default model is `tiny` with GPU/Metal attempted first. This is the safest low-latency default for Apple Silicon hotkey dictation. Use `small` for better accuracy if GPU/latency is acceptable.
- The default language mode is auto-detect, tuned for Simplified Chinese, English, German, and Spanish dictation.

## Requirements

- Homebrew `whisper-cpp` must be installed. `scripts/install.sh` installs it when Homebrew is available.
- A GGML Whisper model must exist at `models/ggml-tiny.bin` by default. `scripts/install.sh` downloads `tiny`; `scripts/download_model.sh small` downloads the more accurate optional model.
- macOS may prompt for Microphone and Accessibility permissions for the terminal/Codex process. Microphone is needed for recording; Accessibility is needed for global hotkeys and paste automation.
- The visual waveform overlay uses macOS Cocoa via PyObjC, not Tkinter.

## Configuration

Environment variables accepted by `voice_to_text.py`:

- `VTT_MODEL_PATH`: absolute model path. Default: `models/ggml-tiny.bin`.
- `VTT_WHISPER_BIN`: whisper.cpp binary. Default: auto-detect `whisper-cli`, `whisper-cpp`, or Homebrew paths.
- `VTT_LANGUAGE`: language hint. Default: `auto`.
- `VTT_INITIAL_PROMPT`: optional Whisper prompt. Default: `Dictation may be in Simplified Chinese, English, German, or Spanish.`
- `VTT_PASTE`: `1` to paste into the active app, `0` to only copy to clipboard. Default: `1`.
- `VTT_SAMPLE_RATE`: recording sample rate. Default: `16000`.
- `VTT_USE_GPU`: `1` to allow whisper.cpp Metal/GPU. Default: `1`. If Metal fails, the daemon retries on CPU automatically.
- `VTT_BEEP`: `1` to play prompt sounds, `0` to disable prompt sounds. Default: `1`.
- `VTT_BEEP_VOLUME`: start/stop/done/error sound volume for `afplay`. Default: `0.25`.
- `VTT_SIMPLIFY_CHINESE`: `1` to convert Traditional Chinese output to Simplified Chinese. Default: `1`.

## Troubleshooting

### Hotkey not responding (right Command key does nothing)

Check status first: `bash scripts/status.sh`. If the log says `Accessibility trusted: False`, follow these steps:

1. Open Accessibility settings:
   ```bash
   open "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_Accessibility"
   ```
2. Click the **+** button, press **Cmd+Shift+G**, paste the path:
   ```
   /Users/yao/.claude/skills/voice-to-text/.venv/bin/python
   ```
3. Click **Open**, ensure the checkbox is toggled on.
4. Restart the service:
   ```bash
   bash scripts/stop.sh && sleep 2 && bash scripts/start.sh
   ```
5. Verify with `bash scripts/status.sh` — should show `Accessibility trusted: True`.

This permission persists across reboots. Only needs re-granting if the venv is rebuilt (e.g., `scripts/install_deps.sh`).

### Recording fails

Grant Microphone permission in System Settings > Privacy & Security > Microphone, then restart the service.

### Model file missing

Download a GGML model from `https://ggml.ggerganov.com/` into `models/`.
