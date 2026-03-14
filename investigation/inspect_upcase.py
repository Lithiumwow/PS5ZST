#!/usr/bin/env python3
"""Check if upcase is actually written in the official image."""
import struct

official = 'PPSA17221-official.exfat'

with open(official, 'rb') as f:
    # Read boot sector
    boot = f.read(512)
    
    spc_shift = boot[109]
    spc = 1 << spc_shift
    cluster_size = spc * 512
    heap_offset_sectors = struct.unpack('<I', boot[88:92])[0]
    
    # Cluster 3 should be upcase table (starts at heap_offset + (3-2)*cluster_size)
    # Actually, cluster 2 is bitmap, cluster 3 should start at:
    offset_cluster_3 = heap_offset_sectors * 512 + 1 * cluster_size  # (3-2)=1 cluster past heap start
    
    print(f"Cluster size: {cluster_size} bytes")
    print(f"Heap starts at sector {heap_offset_sectors}")
    print(f"Cluster 2 (bitmap) at offset {heap_offset_sectors * 512}")
    print(f"Cluster 3 (upcase?) at offset {offset_cluster_3}")
    print()
    
    # Check what's actually in cluster 3
    f.seek(offset_cluster_3)
    cluster_3_data = f.read(1024)  # Read first 1KB
    
    print("First 256 bytes of Cluster 3:")
    print(cluster_3_data[:256].hex())
    print()
    
    # Upcase table typically starts with a header or is mostly data
    # Check if it looks like directory entries instead
    print("Checking if cluster 3 looks like directory entries or upcase...")
    if cluster_3_data[:1] in [b'\x03', b'\x05', b'\x81', b'\x82', b'\x83', b'\x84', b'\x85', b'\x86']:
        print(f"  → Looks like directory entry type: 0x{cluster_3_data[0]:02X}")
        print(f"  → This suggests root directory starts at cluster 3, not upcase!")
    else:
        non_zero = sum(1 for b in cluster_3_data if b != 0)
        print(f"  → Non-zero bytes: {non_zero}/1024")
        if non_zero == 0:
            print(f"  → Cluster 3 is all zeros!")
