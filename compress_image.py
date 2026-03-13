#!/usr/bin/env python3
"""Compress exFAT image to .zst"""

import sys
from pathlib import Path

try:
    import zstandard as z
except ImportError:
    print("ERROR: zstandard not installed")
    sys.exit(1)

# Accept command-line arguments
if len(sys.argv) < 2:
    print("Usage: python compress_image.py <input.exfat> [output.exfat.zst]")
    print("Example: python compress_image.py PPSA17221-osfmount.exfat PPSA17221-osfmount.exfat.zst")
    sys.exit(1)

img_path = Path(sys.argv[1])
zst_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(str(img_path) + ".zst")

if not img_path.exists():
    print(f"ERROR: {img_path} not found")
    sys.exit(1)

size_gb = img_path.stat().st_size / (1 << 30)
print(f"Compressing {size_gb:.2f} GB to .zst (level 3)...")

data = img_path.read_bytes()
compressed = z.ZstdCompressor(level=3).compress(data)
zst_path.write_bytes(compressed)

ratio = 100 * len(compressed) / len(data)
comp_gb = len(compressed) / (1 << 30)
print(f"✓ Compressed: {comp_gb:.2f} GB ({ratio:.1f}%)")
