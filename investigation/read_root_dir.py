#!/usr/bin/env python3
"""Read root directory to see what size upcase table is declared."""
import struct

official = 'PPSA17221-official.exfat'

with open(official, 'rb') as f:
    # Read boot sector
    boot = f.read(512)
    
    heap_offset = struct.unpack('<I', boot[88:92])[0]
    root_cluster = struct.unpack('<I', boot[96:100])[0]
    spc_shift = boot[109]
    spc = 1 << spc_shift
    cluster_size = spc * 512
    
    # Seek to root directory (cluster 4)
    # Offset = heap_start + (cluster - 2) * cluster_size
    root_offset = heap_offset * 512 + (root_cluster - 2) * cluster_size
    
    print(f"Root directory at offset: {root_offset} (cluster {root_cluster})")
    print()
    
    f.seek(root_offset)
    root_data = f.read(cluster_size)
    
    # Parse directory entries
    offset = 0
    entry_num = 0
    while offset < len(root_data):
        entry = root_data[offset:offset+32]
        if len(entry) < 32:
            break
        
        entry_type = entry[0]
        
        if entry_type == 0x00:  # End of directory
            print(f"[{entry_num}] End-of-directory")
            break
        elif entry_type == 0x03:  # Allocation bitmap
            name = "Allocation Bitmap"
            cluster = struct.unpack('<I', entry[20:24])[0]
            size = struct.unpack('<Q', entry[24:32])[0]
            print(f"[{entry_num}] {name}: cluster={cluster}, size={size} bytes")
        elif entry_type == 0x82:  # Upcase table
            name = "Upcase Table"
            cluster = struct.unpack('<I', entry[20:24])[0]
            size = struct.unpack('<Q', entry[24:32])[0]
            print(f"[{entry_num}] {name}: cluster={cluster}, size={size} bytes")
            print(f"      Declared size={size}, cluster_size={cluster_size}")
            print(f"      Clusters needed for declared size: {(size + cluster_size - 1) // cluster_size}")
        elif entry_type == 0x83:  # Volume label
            name = "Volume Label"
            size = struct.unpack('<Q', entry[24:32])[0]
            print(f"[{entry_num}] {name}: size={size}")
        elif entry_type == 0x85:  # File
            name_len = entry[30]
            print(f"[{entry_num}] File: name_len={name_len}, type=0x{entry_type:02X}")
        elif entry_type == 0x81:  # Directory
            name_len = entry[30]
            print(f"[{entry_num}] Directory: name_len={name_len}, type=0x{entry_type:02X}")
        else:
            is_continuation = (entry_type >= 0xC0)
            if is_continuation:
                print(f"[{entry_num}] Continuation entry: type=0x{entry_type:02X}")
            else:
                print(f"[{entry_num}] Unknown type: 0x{entry_type:02X}")
        
        offset += 32
        entry_num += 1
        
        if entry_num > 20:  # Safety limit
            print("... (truncated)")
            break
