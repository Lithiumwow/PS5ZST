#!/usr/bin/env python3
"""Check FAT allocation for upcase table."""
import struct

official = 'PPSA17221-official.exfat'

with open(official, 'rb') as f:
    # Read boot sector
    boot = f.read(512)
    
    fat_offset = struct.unpack('<I', boot[80:84])[0]  
    fat_len = struct.unpack('<I', boot[84:88])[0]
    heap_offset = struct.unpack('<I', boot[88:92])[0]
    root_cluster = struct.unpack('<I', boot[96:100])[0]
    
    print(f"FAT starts at sector {fat_offset}, length {fat_len} sectors")
    print(f"Heap starts at sector {heap_offset}")
    print(f"Root cluster: {root_cluster}")
    print()
    
    # Read FAT table
    f.seek(fat_offset * 512)
    fat_data = f.read(fat_len * 512)
    
    def read_fat_entry(cluster):
        return struct.unpack('<I', fat_data[cluster*4:(cluster+1)*4])[0]
    
    print("FAT chain for clusters 2-10:")
    for cluster in range(2, 11):
        entry = read_fat_entry(cluster)
        if entry == 0:
            print(f"  Cluster {cluster}: 0x00000000 (unallocated)")
        elif entry == 0xFFFFFFF8:
            print(f"  Cluster {cluster}: 0xFFFFFFF8 (media)")
        elif entry == 0xFFFFFFFF:
            print(f"  Cluster {cluster}: 0xFFFFFFFF (end-of-chain)")
        elif entry == 0xFFFFFFF7:
            print(f"  Cluster {cluster}: 0xFFFFFFF7 (bad)")
        else:
            print(f"  Cluster {cluster}: → cluster {entry}")
