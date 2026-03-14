#!/usr/bin/env python3
"""Generate 2GB exFAT matching official specs."""

from pathlib import Path
from mkexfat import ExFATWriter
import time

source = Path("PPSA17221-app")
output = Path("test-official-match.exfat")

print(f"Generating 2GB exFAT from {source}...")
print(f"This will match the official geometry exactly.\n")

start = time.time()
writer = ExFATWriter(
    output, 
    source, 
    label="EXFAT",
    cluster_size=32768,
    min_size=2 * (1 << 30)  # Force 2GB
)
writer.build()
elapsed = time.time() - start

print(f"\n✓ Created: {output}")
print(f"  Time: {elapsed:.1f}s")
print(f"  Size: {output.stat().st_size / (1<<30):.2f} GB")
