#!/usr/bin/env python3
"""Deep structure verification."""
import struct

official = 'PPSA17221-official.exfat'
updated = 'PPSA17221-updated.exfat'

def cmp_regions(name, path1, path2, offset, size):
    """Compare binary regions."""
    with open(path1, 'rb') as f:
        f.seek(offset)
        data1 = f.read(size)
    with open(path2, 'rb') as f:
        f.seek(offset)
        data2 = f.read(size)
    
    match = data1 == data2
    diff_bytes = sum(1 for a, b in zip(data1, data2) if a != b)
    size_kb = size / 1024
    
    status = "✓" if match else "✗"
    print(f"{name:30} | Offset: {offset:7} | Size: {size_kb:6.1f}KB | {status} ({diff_bytes} diffs)" if not match else f"{name:30} | Offset: {offset:7} | Size: {size_kb:6.1f}KB | {status}")
    return match

print("BINARY REGION COMPARISON:")
print("=" * 100)

all_match = True
all_match &= cmp_regions("Boot Sector (primary VBR)", official, updated, 0, 512)
all_match &= cmp_regions("Backup VBR", official, updated, 512, 512)
all_match &= cmp_regions("OEM Parameters sector", official, updated, 4608, 512)
all_match &= cmp_regions("Checksum sector", official, updated, 5632, 512)
all_match &= cmp_regions("FAT Table", official, updated, 128*512, 576*512)
all_match &= cmp_regions("Allocation Bitmap (cluster 2)", official, updated, 393216, 32768)
all_match &= cmp_regions("Upcase Table (cluster 3)", official, updated, 425984, 32768)
all_match &= cmp_regions("Root Directory (cluster 4)", official, updated, 458752, 32768)

print("=" * 100)
if all_match:
    print("✓ ALL CRITICAL REGIONS MATCH!")
else:
    print("✗ Some regions differ - investigating...")
