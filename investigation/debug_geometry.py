#!/usr/bin/env python3
"""Debug allocation order and bitmap_clusters value."""

import sys
sys.path.insert(0, '.')

from pathlib import Path
from mkexfat import ExFATWriter

src = Path("PPSA17221-app")

# Create writer (without writing yet) to see the geometry  
writer = ExFATWriter(Path("dummy.img"), src, label="OSFIMG", cluster_size=32768, min_size=2)

print(f"ExFATGeom Details:")
print(f"  bitmap_clusters: {writer.g.bitmap_clusters}")
print(f"  upcase_clusters: {writer.g.upcase_clusters}")
print(f"  total_clusters: {writer.g.total_clusters}")
print(f"  cluster_size: {writer.g.cluster_size}")
print(f"  file_clusters sum: {sum(len(c) for e in [] for c in [])}")  # placeholder

print(f"\nExpected First Cluster: 2")
print(f"Expected Cluster Allocation:")
print(f"  Clusters 2-{2 + writer.g.bitmap_clusters - 1}: Bitmap ({writer.g.bitmap_clusters} clusters)")
print(f"  Clusters {2 + writer.g.bitmap_clusters}-{2 + writer.g.bitmap_clusters + writer.g.upcase_clusters - 1}: Upcase ({writer.g.upcase_clusters} clusters)")
print(f"  Cluster {2 + writer.g.bitmap_clusters + writer.g.upcase_clusters}+: Root and Files")
