#!/usr/bin/env python3
import struct

def check_fat_structure(fname):
    print(f"\n=== {fname} ===")
    with open(fname, 'rb') as f:
        boot = f.read(512)
        fat_offset = struct.unpack('<I', boot[80:84])[0]
        fat_length = struct.unpack('<I', boot[84:88])[0]
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        
        print(f"FAT offset (sectors): {fat_offset}")
        print(f"FAT length (sectors): {fat_length}")
        print(f"Heap offset (sectors): {heap_offset}")
        
        # Read first FAT sector
        f.seek(fat_offset * 512)
        fat_data = f.read(512)
        
        print(f"\nFirst 16 FAT entries:")
        for i in range(16):
            entry = struct.unpack('<I', fat_data[i*4:(i+1)*4])[0]
            print(f"  FAT[{i}] = {hex(entry)}")
        
        # Check for reserved clusters
        print(f"\nCluster 0: should be 0xFFFFFFF8 (media descriptor)")
        cluster0 = struct.unpack('<I', fat_data[0:4])[0]
        print(f"  Actual: {hex(cluster0)} {'✓' if cluster0 == 0xFFFFFFF8 else '✗ WRONG'}")
        
        print(f"\nCluster 1: should be 0xFFFFFFFF (reserved/EOC)")
        cluster1 = struct.unpack('<I', fat_data[4:8])[0]
        print(f"  Actual: {hex(cluster1)} {'✓' if cluster1 == 0xFFFFFFFF else '✗ WRONG'}")

check_fat_structure('test-fixed-fat.exfat')
check_fat_structure('PPSA17221-official.exfat')
