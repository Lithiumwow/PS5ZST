#!/usr/bin/env python3
"""Final verification of generated test image."""
import struct

official = 'PPSA17221-official.exfat'
test_img = 'test-game.exfat'

def get_geometry(path):
    with open(path, 'rb') as f:
        boot = f.read(512)
    return {
        'cluster_size': (1 << boot[109]) * 512,
        'root_cluster': struct.unpack('<I', boot[96:100])[0],
        'fat_offset': struct.unpack('<I', boot[80:84])[0],
        'heap_offset': struct.unpack('<I', boot[88:92])[0],
    }

off = get_geometry(official)
test = get_geometry(test_img)

print("FINAL VERIFICATION: Test Image vs Official")
print("=" * 60)
for key in off:
    match = "✓" if off[key] == test[key] else "✗"
    print(f"{key:20} | Official: {off[key]:6} | Test: {test[key]:6} | {match}")
print("=" * 60)

if all(off[k] == test[k] for k in off):
    print("✓✓✓ READY FOR PS5 TESTING! ✓✓✓")
else:
    print("✗ Geometry mismatch")
