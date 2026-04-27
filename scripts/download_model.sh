#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL="${1:-tiny}"
mkdir -p "$ROOT/models"

case "$MODEL" in
  tiny|base|small|medium|large-v3)
    FILE="ggml-$MODEL.bin"
    URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/$FILE"
    ;;
  *)
    echo "Unsupported model: $MODEL"
    echo "Supported: tiny, base, small, medium, large-v3"
    exit 2
    ;;
esac

OUT="$ROOT/models/$FILE"
if [ -f "$OUT" ] && [ "$(wc -c < "$OUT")" -gt 1000000 ]; then
  echo "Model already exists: $OUT"
  exit 0
fi

curl -L --fail "$URL" -o "$OUT"
echo "Downloaded model: $OUT"
