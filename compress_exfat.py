#!/usr/bin/env python3
"""Compress exFAT image with progress tracking and reasonable settings."""

import zstandard as zst
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python compress_exfat.py <input.exfat> [level] [output.exfat.zst]")
    print("Default: level=3 (fast), output=<input>.zst")
    sys.exit(1)

input_file = sys.argv[1]
level = int(sys.argv[2]) if len(sys.argv) > 2 else 3
output_file = sys.argv[3] if len(sys.argv) > 3 else f"{input_file}.zst"

input_path = Path(input_file)
if not input_path.exists():
    print(f"Error: {input_file} not found")
    sys.exit(1)

file_size = input_path.stat().st_size
print(f"Compressing: {input_file}")
print(f"Size: {file_size / (1024**3):.2f} GB")
print(f"Level: {level}")
print(f"Output: {output_file}\n")

# Use streaming compression for large files
compressor = zst.ZstdCompressor(level=level)

bytes_processed = 0
chunk_size = 10 * 1024 * 1024  # 10 MB chunks

with open(input_file, 'rb') as fin:
    with open(output_file, 'wb') as fout:
        with compressor.stream_writer(fout) as writer:
            while True:
                chunk = fin.read(chunk_size)
                if not chunk:
                    break
                writer.write(chunk)
                bytes_processed += len(chunk)
                percent = 100.0 * bytes_processed / file_size
                bar = '#' * int(percent / 2) + '-' * (50 - int(percent / 2))
                print(f"\r[{bar}] {percent:.1f}% ({bytes_processed / (1024**3):.2f}/{file_size / (1024**3):.2f} GB)", 
                      end='', flush=True)

compressed_size = Path(output_file).stat().st_size
ratio = 100.0 * compressed_size / file_size

print(f"\n\nDone!")
print(f"Original:   {file_size / (1024**3):.2f} GB")
print(f"Compressed: {compressed_size / (1024**3):.2f} GB")
print(f"Ratio:      {ratio:.1f}%")
