#!/usr/bin/env python3
"""Compare boot sector field by field."""
import struct

official = 'PPSA17221-official.exfat'
updated = 'PPSA17221-updated.exfat'

def read_boot_fields(path):
    with open(path, 'rb') as f:
        boot = f.read(512)
    
    fields = {
        'Jump Boot (0-2)': boot[0:3],
        'OEM (3-10)': boot[3:11],
        'Bytes/Sector (11-12)': struct.unpack('<H', boot[11:13])[0],
        'Sectors/Cluster (13)': boot[13],
        'Reserved (14-15)': struct.unpack('<H', boot[14:16])[0],
        'Partition Offset (64-71)': struct.unpack('<Q', boot[64:72])[0],
        'Volume Length (72-79)': struct.unpack('<Q', boot[72:80])[0],
        'FAT Offset (80-83)': struct.unpack('<I', boot[80:84])[0],
        'FAT Length (84-87)': struct.unpack('<I', boot[84:88])[0],
        'Heap Offset (88-91)': struct.unpack('<I', boot[88:92])[0],
        'Cluster Count (92-95)': struct.unpack('<I', boot[92:96])[0],
        'Root Cluster (96-99)': struct.unpack('<I', boot[96:100])[0],
        'Volume Serial (100-103)': hex(struct.unpack('<I', boot[100:104])[0]),
        'FileSystem Revision (104-105)': boot[104:106].hex(),
        'Boot Signature (510-511)': boot[510:512].hex(),
    }
    return fields, boot

off_fields, off_boot = read_boot_fields(official)
upd_fields, upd_boot = read_boot_fields(updated)

print("BOOT SECTOR FIELD COMPARISON:")
print("=" * 80)
for key in off_fields:
    off_val = off_fields[key]
    upd_val = upd_fields[key]
    match = off_val == upd_val
    status = "✓" if match else "✗"
    print(f"{key:30} | Off: {str(off_val):20} | Upd: {str(upd_val):20} | {status}")

print("=" * 80)

# Check which fields differ
diff_fields = [k for k in off_fields if off_fields[k] != upd_fields[k]]
if diff_fields:
    print(f"\nFields that differ: {', '.join(diff_fields)}")
    print("\nNote: Volume Serial Number and timestamps are expected to differ.")
else:
    print("\n✓ All fields match!")
