#!/usr/bin/env python3
"""Verify 2GB test image matches official."""
import struct

official = 'PPSA17221-official.exfat'
test_img = 'test-official-match.exfat'

def get_geometry(path):
    with open(path, 'rb') as f:
        boot = f.read(512)
    return {
        'cluster_size': (1 << boot[109]) * 512,
        'root_cluster': struct.unpack('<I', boot[96:100])[0],
        'fat_offset': struct.unpack('<I', boot[80:84])[0],
        'heap_offset': struct.unpack('<I', boot[88:92])[0],
        'total_clusters': struct.unpack('<I', boot[92:96])[0],
    }

off = get_geometry(official)
test = get_geometry(test_img)

print("=" * 70)
print("GEOMETRY VERIFICATION: 2GB Test vs Official")
print("=" * 70)

all_match = True
for key in sorted(off.keys()):
    match = off[key] == test[key]
    all_match = all_match and match
    status = "✓" if match else "✗"
    print(f"{key:20} | Official: {off[key]:8} | Test: {test[key]:8} | {status}")

print("=" * 70)

if all_match:
    print("\n✓✓✓ PERFECT MATCH! Ready for PS5 testing! ✓✓✓\n")
else:
    print("\n✗ Some differences detected\n")
