#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: $0 <source_c_file> [output_elf]"
  echo "Example: $0 decompress_ps5.c ZSTDecompressionPS5.elf"
  exit 1
fi

SRC_FILE="$1"
OUT_FILE="${2:-ZSTDecompressionPS5.elf}"
SDK_WORK="/tmp/ps5sdk_build"

if [ ! -f "$SRC_FILE" ]; then
  echo "ERROR: source file not found: $SRC_FILE"
  exit 1
fi

mkdir -p "$SDK_WORK"
cd "$SDK_WORK"

if [ ! -x "$SDK_WORK/sdk/ps5-payload-sdk/bin/prospero-clang" ]; then
  echo "Downloading ps5-payload-sdk..."
  rm -rf "$SDK_WORK/sdk"
  wget -q https://github.com/ps5-payload-dev/sdk/releases/latest/download/ps5-payload-sdk.zip
  unzip -q -o ps5-payload-sdk.zip -d sdk
fi

SDK_BIN="$SDK_WORK/sdk/ps5-payload-sdk/bin/prospero-clang"
if [ ! -x "$SDK_BIN" ]; then
  echo "ERROR: prospero-clang not found after SDK download"
  exit 1
fi

echo "Building: $OUT_FILE"
"$SDK_BIN" "$SRC_FILE" -O2 -Wall -o "$OUT_FILE"

echo "Done."
file "$OUT_FILE"
