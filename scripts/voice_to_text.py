#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import os
import queue
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np
import pyperclip
import sounddevice as sd
from ApplicationServices import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt
from pynput import keyboard
from scipy.io import wavfile


ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = ROOT / "tmp"
TMP_DIR.mkdir(exist_ok=True)

SAMPLE_RATE = int(os.environ.get("VTT_SAMPLE_RATE", "16000"))
MODEL_PATH = Path(os.environ.get("VTT_MODEL_PATH", ROOT / "models" / "ggml-tiny.bin"))
LANGUAGE = os.environ.get("VTT_LANGUAGE", "auto")
PASTE = os.environ.get("VTT_PASTE", "1") != "0"
USE_GPU = os.environ.get("VTT_USE_GPU", "1") == "1"

recording = threading.Event()
busy = threading.Event()
audio_queue: queue.Queue[np.ndarray] = queue.Queue()
frames: list[np.ndarray] = []
stream: sd.InputStream | None = None
overlay_proc: subprocess.Popen[str] | None = None
last_overlay_emit = 0.0


def log(message: str) -> None:
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{stamp}] {message}", flush=True)


def beep(name: str) -> None:
    sounds = {
        "start": "/System/Library/Sounds/Ping.aiff",
        "stop": "/System/Library/Sounds/Ping.aiff",
        "done": "/System/Library/Sounds/Pop.aiff",
        "error": "/System/Library/Sounds/Basso.aiff",
    }
    subprocess.run(["afplay", sounds[name]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def start_overlay() -> None:
    global overlay_proc
    if overlay_proc and overlay_proc.poll() is None:
        return
    script = ROOT / "scripts" / "voice_overlay.py"
    overlay_proc = subprocess.Popen(
        [sys.executable, "-u", str(script)],
        stdin=subprocess.PIPE,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def stop_overlay() -> None:
    global overlay_proc
    if not overlay_proc:
        return
    try:
        if overlay_proc.stdin:
            overlay_proc.stdin.close()
        overlay_proc.wait(timeout=1.0)
    except Exception:
        overlay_proc.terminate()
    finally:
        overlay_proc = None


def send_overlay_level(audio: np.ndarray) -> None:
    global last_overlay_emit
    if not overlay_proc or overlay_proc.poll() is not None or not overlay_proc.stdin:
        return
    now = time.monotonic()
    if now - last_overlay_emit < 0.033:
        return
    last_overlay_emit = now
    rms = float(np.sqrt(np.mean(np.square(audio.astype(np.float32)))))
    try:
        overlay_proc.stdin.write(f"{rms:.5f}\n")
        overlay_proc.stdin.flush()
    except Exception:
        pass


def find_whisper_bin() -> str:
    configured = os.environ.get("VTT_WHISPER_BIN")
    candidates = [
        configured,
        shutil.which("whisper-cli"),
        shutil.which("whisper-cpp"),
        "/opt/homebrew/bin/whisper-cli",
        "/opt/homebrew/bin/whisper-cpp",
        "/usr/local/bin/whisper-cli",
        "/usr/local/bin/whisper-cpp",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    raise RuntimeError("Could not find whisper.cpp binary. Install it with: brew install whisper-cpp")


def audio_callback(indata: np.ndarray, frames_count: int, time_info, status) -> None:
    if status:
        log(f"Audio status: {status}")
    if recording.is_set():
        audio_queue.put(indata.copy())
        send_overlay_level(indata)


def start_recording() -> None:
    global frames, stream
    if busy.is_set() or recording.is_set():
        return
    frames = []
    while not audio_queue.empty():
        audio_queue.get_nowait()
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        callback=audio_callback,
    )
    stream.start()
    start_overlay()
    recording.set()
    log("Recording started")
    threading.Thread(target=beep, args=("start",), daemon=True).start()


def stop_recording() -> None:
    global stream
    if not recording.is_set():
        return
    recording.clear()
    threading.Thread(target=beep, args=("stop",), daemon=True).start()
    time.sleep(0.15)
    if stream is not None:
        stream.stop()
        stream.close()
        stream = None
    stop_overlay()
    while not audio_queue.empty():
        frames.append(audio_queue.get_nowait())
    if not frames:
        log("No audio captured")
        return
    audio = np.concatenate(frames, axis=0).reshape(-1)
    threading.Thread(target=transcribe_and_paste, args=(audio,), daemon=True).start()


def run_whisper(whisper_bin: str, wav_path: Path, out_base: Path, model_path: Path, use_gpu: bool) -> subprocess.CompletedProcess[str]:
    cmd = [
        whisper_bin,
        "-m",
        str(model_path),
        "-f",
        str(wav_path),
        "-otxt",
        "-of",
        str(out_base),
        "-nt",
        "-l",
        LANGUAGE,
    ]
    if not use_gpu:
        cmd.insert(1, "-ng")
    log(f"Transcribing with whisper.cpp ({model_path.name}, {'GPU' if use_gpu else 'CPU'})")
    return subprocess.run(cmd, text=True, capture_output=True)


def transcribe_and_paste(audio: np.ndarray) -> None:
    busy.set()
    try:
        if not MODEL_PATH.exists():
            raise RuntimeError(f"Missing model file: {MODEL_PATH}")
        whisper_bin = find_whisper_bin()
        audio_i16 = np.clip(audio, -1.0, 1.0)
        audio_i16 = (audio_i16 * 32767).astype(np.int16)
        with tempfile.TemporaryDirectory(dir=TMP_DIR) as work:
            wav_path = Path(work) / "speech.wav"
            out_base = Path(work) / "speech"
            wavfile.write(wav_path, SAMPLE_RATE, audio_i16)
            result = run_whisper(whisper_bin, wav_path, out_base, MODEL_PATH, USE_GPU)
            if result.returncode != 0 and USE_GPU:
                log("GPU transcription failed; retrying on CPU")
                result = run_whisper(whisper_bin, wav_path, out_base, MODEL_PATH, False)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip())
            text_path = out_base.with_suffix(".txt")
            text = text_path.read_text(encoding="utf-8").strip()
        if not text:
            log("No speech recognized")
            return
        pyperclip.copy(text)
        log(f"Transcribed: {text}")
        if PASTE:
            subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        threading.Thread(target=beep, args=("done",), daemon=True).start()
    except Exception as exc:
        log(f"ERROR: {exc}")
        threading.Thread(target=beep, args=("error",), daemon=True).start()
    finally:
        busy.clear()


def on_press(key) -> None:
    if key in (keyboard.Key.cmd_r, keyboard.Key.cmd):
        try:
            start_recording()
        except Exception as exc:
            log(f"ERROR starting recording: {exc}")
            threading.Thread(target=beep, args=("error",), daemon=True).start()


def on_release(key) -> None:
    if key in (keyboard.Key.cmd_r, keyboard.Key.cmd):
        try:
            stop_recording()
        except Exception as exc:
            log(f"ERROR stopping recording: {exc}")
            threading.Thread(target=beep, args=("error",), daemon=True).start()


def shutdown(signum, frame) -> None:
    log("Shutting down")
    try:
        if recording.is_set():
            stop_recording()
    finally:
        sys.exit(0)


def main() -> None:
    trusted = AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True})
    log("voice-to-text daemon ready. Hold right Command to dictate.")
    log(f"Model: {MODEL_PATH}")
    log(f"GPU first: {USE_GPU}")
    log(f"Accessibility trusted: {trusted}")
    if not trusted:
        log("Grant Accessibility permission to this Python.app, then run stop voice to text and start voice to text.")
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    main()
