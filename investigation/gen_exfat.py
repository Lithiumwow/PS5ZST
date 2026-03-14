#!/usr/bin/env python3
"""Generate exFAT image for testing."""

from pathlib import Path
from mkexfat import ExFATWriter

source = Path("PPSA17221-app")
output = Path("PPSA17221-updated.exfat")

print(f"Generating exFAT from {source}...")
writer = ExFATWriter(output, source, label="EXFAT", cluster_size=32768, min_size=2 * (1 << 30))
writer.build()
print(f"✓ Created: {output}")
