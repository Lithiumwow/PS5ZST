#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
  echo "Usage: $0 <game_folder> <output_folder> [level]"
  echo "Example: $0 PPSA17221-app PPSA17221-compressed 3"
  exit 1
fi

GAME_DIR="$1"
OUT_DIR="$2"
LEVEL="${3:-3}"

if [ ! -d "$GAME_DIR" ]; then
  echo "ERROR: game folder not found: $GAME_DIR"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required in WSL"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPRESS_PY="$PROJECT_ROOT/zstd_deploy/compress_pkg.py"

if [ ! -f "$COMPRESS_PY" ]; then
  echo "ERROR: compress_pkg.py not found at $COMPRESS_PY"
  exit 1
fi

python3 "$COMPRESS_PY" "$GAME_DIR" "$OUT_DIR" --level "$LEVEL"

echo "Done."
echo "Output folder: $OUT_DIR"
echo "Manifest: $OUT_DIR/manifest.txt"
