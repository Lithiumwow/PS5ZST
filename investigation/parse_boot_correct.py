#!/usr/bin/env python3
"""Correctly parse exFAT boot sector using proper offsets."""

import struct

def parse_exfat_boot(data):
    """Parse exFAT boot sector according to actual spec offsets."""
    print("\nExFAT Boot Sector Fields:")
    print(f"  [0-2] Jump Boot: {data[0:3].hex()}")
    print(f"  [3-10] OEM Name: {data[3:11]}")
    print(f"  [64-72] PartitionOffset: {struct.unpack('<Q', data[64:72])[0]}")
    print(f"  [72-80] VolumeLength (sectors): {struct.unpack('<Q', data[72:80])[0]}")
    print(f"  [80-84] FAT Region Offset (sectors): {struct.unpack('<I', data[80:84])[0]}")
    print(f"  [84-88] FAT Length (sectors): {struct.unpack('<I', data[84:88])[0]}")
    print(f"  [88-92] Cluster Heap Offset (sectors): {struct.unpack('<I', data[88:92])[0]}")
    print(f"  [92-96] Cluster Count: {struct.unpack('<I', data[92:96])[0]}")
    print(f"  [96-100] First Cluster of Root: {struct.unpack('<I', data[96:100])[0]}")
    print(f"  [100-104] Serial Number: 0x{struct.unpack('<I', data[100:104])[0]:08x}")
    print(f"  [104-106] FS Revision: {data[104]}.{data[105]:02d}")
    print(f"  [106-108] Volume Flags: 0x{struct.unpack('<H', data[106:108])[0]:04x}")
    print(f"  [108] Bytes/Sector Shift: {data[108]}")
    print(f"  [109] Sectors/Cluster Shift: {data[109]}")
    print(f"  [110] Number of FATs: {data[110]}")
    print(f"  [111] Drive Select: 0x{data[111]:02x}")
    print(f"  [112] Percent in Use: {data[112]}")
    print(f"  [510-512] Boot Signature: {data[510:512].hex()}")

with open('PPSA17221-official.exfat', 'rb') as f:
    data = f.read(512)
    print("="*60)
    print("OFFICIAL IMAGE (OSFMount)")
    print("="*60)
    parse_exfat_boot(data)

with open('test-ps5-final.exfat', 'rb') as f:
    data = f.read(512)
    print("\n" + "="*60)
    print("GENERATED IMAGE (Python)")
    print("="*60)
    parse_exfat_boot(data)
