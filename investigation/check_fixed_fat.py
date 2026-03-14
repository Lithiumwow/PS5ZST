#!/usr/bin/env python3
import struct

fname = 'test-fixed-fat.exfat'
print(f"Checking {fname}...")

with open(fname, 'rb') as f:
    boot = f.read(512)
    heap_offset = struct.unpack('<I', boot[88:92])[0]
    fat_offset = struct.unpack('<I', boot[80:84])[0]
    
    # Check FAT entry for param.json (cluster 53705)
    cluster = 53705
    fat_byte_offset = fat_offset * 512 + cluster * 4
    f.seek(fat_byte_offset)
    entry = struct.unpack('<I', f.read(4))[0]
    
    print(f"param.json cluster {cluster}: FAT entry = {hex(entry)}")
    
    if entry == 0x0:
        print("✓ CORRECT! FAT entry is 0x0 as expected for NoFatChain")
    else:
        print(f"✗ WRONG! Expected 0x0, got {hex(entry)}")
