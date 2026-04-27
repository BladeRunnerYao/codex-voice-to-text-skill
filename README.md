# Codex Voice To Text Skill

Local macOS push-to-talk dictation for Codex, powered by `whisper.cpp`.

Hold the right Command key to record. Release it to transcribe. The result is copied to the clipboard and pasted into the active app. While recording, a small waveform overlay appears near the bottom center of the screen.

By default, this skill is tuned for Simplified Chinese, English, German, and Spanish dictation. You can change the target language hint and Chinese conversion behavior with environment variables if your own workflow needs different languages.

## Requirements

- macOS on Apple Silicon or Intel Mac
- Homebrew
- Codex skills directory at `~/.codex/skills`
- Microphone permission
- Accessibility permission for the Python app used by the skill

## Install

Clone the skill into your Codex skills folder:

```bash
git clone https://github.com/BladeRunnerYao/codex-voice-to-text-skill.git ~/.codex/skills/voice-to-text
cd ~/.codex/skills/voice-to-text
scripts/install.sh
```

`scripts/install.sh` will:

- Install `whisper-cpp` with Homebrew if needed
- Create a local Python virtual environment
- Install Python dependencies
- Download the default `tiny` Whisper model

## Start

```bash
~/.codex/skills/voice-to-text/scripts/start.sh
```

The service runs as a macOS user LaunchAgent named:

```text
com.codex.voice-to-text
```

## Stop

```bash
~/.codex/skills/voice-to-text/scripts/stop.sh
```

## Status And Logs

```bash
~/.codex/skills/voice-to-text/scripts/status.sh
```

Logs are written to:

```text
~/.codex/skills/voice-to-text/voice-to-text.log
```

## Usage

1. Put your cursor in any text field.
2. Hold the right Command key.
3. Wait for the sound and the waveform overlay.
4. Speak.
5. Release the right Command key.
6. The transcribed text is copied and pasted into the active app.

## macOS Permissions

The first time you run the service, macOS may ask for permissions.

Grant Microphone permission so the service can record audio.

Grant Accessibility permission so the service can listen for the global right Command hotkey and paste the transcription. If the hotkey does nothing, open:

```text
System Settings -> Privacy & Security -> Accessibility
```

Then enable the Python app used by Homebrew. It is usually here:

```text
/opt/homebrew/Cellar/python@*/Frameworks/Python.framework/Versions/*/Resources/Python.app
```

After changing Accessibility permissions, restart the service:

```bash
~/.codex/skills/voice-to-text/scripts/stop.sh
~/.codex/skills/voice-to-text/scripts/start.sh
```

## Models

The default model is `tiny`, which is fast and works well for short dictation.

Download another model:

```bash
cd ~/.codex/skills/voice-to-text
scripts/download_model.sh small
```

Supported model names:

```text
tiny
base
small
medium
large-v3
```

Use a different model when starting:

```bash
VTT_MODEL_PATH="$HOME/.codex/skills/voice-to-text/models/ggml-small.bin" \
~/.codex/skills/voice-to-text/scripts/start.sh
```

## Configuration

Environment variables:

- `VTT_MODEL_PATH`: model path. Default: `models/ggml-tiny.bin`
- `VTT_WHISPER_BIN`: custom `whisper-cli` path
- `VTT_LANGUAGE`: language hint. Default: `auto`
- `VTT_INITIAL_PROMPT`: Whisper prompt. Default: `Dictation may be in Simplified Chinese, English, German, or Spanish.`
- `VTT_PASTE`: `1` to paste automatically, `0` to only copy. Default: `1`
- `VTT_SAMPLE_RATE`: recording sample rate. Default: `16000`
- `VTT_USE_GPU`: `1` to try Metal/GPU first. Default: `1`
- `VTT_BEEP_VOLUME`: sound effect volume. Default: `0.25`
- `VTT_SIMPLIFY_CHINESE`: `1` to convert Traditional Chinese output to Simplified Chinese. Default: `1`

If GPU transcription fails, the script retries on CPU automatically.

## Troubleshooting

If pressing right Command does nothing:

- Check Accessibility permission.
- Restart the service after granting permission.
- Run `scripts/status.sh` and inspect recent logs.

If no text is pasted:

- Make sure the cursor is in a text field.
- Check whether the text was copied to the clipboard.
- Set `VTT_PASTE=0` if you only want clipboard copy.

If the waveform overlay does not appear:

- Make sure PyObjC dependencies were installed by `scripts/install.sh`.
- Run `scripts/status.sh` and check logs.

If transcription is inaccurate:

- Download and use `small` or `medium`.
- For best speed, keep `tiny` or `base`.

## Update

```bash
cd ~/.codex/skills/voice-to-text
git pull
scripts/install.sh
scripts/stop.sh
scripts/start.sh
```
