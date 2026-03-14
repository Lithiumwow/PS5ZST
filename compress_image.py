#!/usr/bin/env python3
"""Compress exFAT image to .zst - streams large files efficiently with progress"""

import sys
import time
from pathlib import Path

try:
    import zstandard as z
except ImportError:
    print("ERROR: zstandard not installed")
    sys.exit(1)

# Accept command-line arguments
if len(sys.argv) < 2:
    print("Usage: python compress_image.py <input.exfat> [output.exfat.zst]")
    print("Example: python compress_image.py PPSA17221.exfat PPSA17221.exfat.zst")
    sys.exit(1)

img_path = Path(sys.argv[1])
zst_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(str(img_path) + ".zst")

if not img_path.exists():
    print(f"ERROR: {img_path} not found")
    sys.exit(1)

total_size = img_path.stat().st_size
size_gb = total_size / (1 << 30)
print(f"Compressing {size_gb:.2f} GB to .zst (level 3)...")
print()

# Stream compression for large files with progress
cctx = z.ZstdCompressor(level=3)
chunk_size = 1024 * 1024 * 100  # 100MB chunks
bytes_read = 0
start_time = time.time()

with open(img_path, 'rb') as f_in:
    with open(zst_path, 'wb') as f_out:
        with cctx.stream_writer(f_out) as writer:
            while True:
                chunk = f_in.read(chunk_size)
                if not chunk:
                    break
                
                writer.write(chunk)
                bytes_read += len(chunk)
                
                # Show progress every 500MB
                if bytes_read % (1024 * 1024 * 500) < chunk_size:
                    elapsed = time.time() - start_time
                    speed_mbps = (bytes_read / (1 << 20)) / elapsed if elapsed > 0 else 0
                    percent = 100 * bytes_read / total_size
                    remaining_bytes = total_size - bytes_read
                    eta_secs = remaining_bytes / (1 << 20) / speed_mbps if speed_mbps > 0 else 0
                    eta_mins = eta_secs / 60
                    
                    read_gb = bytes_read / (1 << 30)
                    print(f"  [{percent:5.1f}%] {read_gb:.2f} GB read | {speed_mbps:7.1f} MB/s | ETA: {eta_mins:5.1f} min")

# Calculate ratio
compressed_size = zst_path.stat().st_size
original_size = img_path.stat().st_size
ratio = 100 * compressed_size / original_size
comp_gb = compressed_size / (1 << 30)
orig_gb = original_size / (1 << 30)

print(f"✓ Compression complete!")
print(f"  Original:   {orig_gb:.2f} GB")
print(f"  Compressed: {comp_gb:.2f} GB")
print(f"  Ratio:      {ratio:.1f}%")
print(f"  Output:     {zst_path}")
