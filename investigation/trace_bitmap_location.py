#!/usr/bin/env python3
"""Precise bitmap write location check."""

import struct

def trace_bitmap_allocation(img_path, label):
    print(f"\n{'='*70}")
    print(f"BITMAP ALLOCATION TRACE: {label}")
    print('='*70)
    
    with open(img_path, 'rb') as f:
        boot = f.read(512)
        
        bps_shift = boot[108]
        spc_shift = boot[109]
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        root_cluster = struct.unpack('<I', boot[96:100])[0]
        
        bps = 1 << bps_shift
        spc = 1 << spc_shift
        
        print(f"\n[Boot Sector]")
        print(f"  Bytes per sector: {bps}")
        print(f"  Sectors per cluster: {spc}")
        print(f"  Heap offset: {heap_offset} sectors = {heap_offset * bps} bytes")
        print(f"  Root cluster: {root_cluster}")
        
        # Calculate expected cluster locations
        print(f"\n[Expected Allocation]")
        print(f"  Cluster 2: Bitmap (1 cluster)")
        print(f"  Clusters 3-8: Upcase Table (6 clusters)")
        print(f"  Cluster 9+: Root Directory and Files")
        
        # Read root directory
        root_offset = (heap_offset + (root_cluster - 2) * spc) * bps
        print(f"\n[Root Directory Location]")
        print(f"  Cluster: {root_cluster}")
        print(f"  Offset: {root_offset} bytes = 0x{root_offset:x}")
        
        f.seek(root_offset)
        root_data = f.read(spc * bps)
        
        # Parse root entries
        print(f"\n[Root Directory Entries]")
        i = 0
        entry_count = 0
        while i < len(root_data) and root_data[i] != 0 and entry_count < 5:
            entry = root_data[i:i+32]
            entry_type = entry[0]
            
            type_names = {
                0x83: "VOLUME_LABEL",
                0x81: "ALLOC_BITMAP",
                0x82: "UPCASE_TABLE",
                0x85: "FILE",
                0xff: "END_OF_DIRECTORY"
            }
            
            type_name = type_names.get(entry_type, f"0x{entry_type:02x}")
            
            if entry_type in [0x81, 0x82, 0x85]:
                se = root_data[i+32:i+64]
                size = struct.unpack('<Q', se[8:16])[0]
                cluster = struct.unpack('<I', se[20:24])[0]
                
                print(f"\n  [{entry_count}] Type: {type_name}")
                print(f"      Size: {size} bytes")
                print(f"      Cluster: {cluster}")
                
                if entry_type == 0x81:  # ALLOC_BITMAP
                    # Calculate where this cluster's data should be
                    cluster_offset = (heap_offset + (cluster - 2) * spc) * bps
                    print(f"      Data offset: {cluster_offset} bytes = 0x{cluster_offset:x}")
                    
                    # Read first 64 bytes of the bitmap
                    f.seek(cluster_offset)
                    bitmap_data = f.read(64)
                    print(f"      First 64 bytes: {' '.join(f'{b:02x}' for b in bitmap_data)}")
                    
                    # Analyze the pattern
                    if bitmap_data[:4] == b'\x00\x00\x00\x00':
                        print(f"      ✗ Bitmap starts with zeros (suspicious)")
                    elif all(b == 0 for b in bitmap_data):
                        print(f"      ✗ Bitmap is all zeros (definitely wrong)")
                    else:
                        ones = sum(bin(b).count('1') for b in bitmap_data)
                        print(f"      ✓ Bitmap has {ones} bits set in first 64 bytes")
            
            if entry_type == 0x85:  # FILE/DIR
                name_bytes = b''
                se_count = entry[1]
                for k in range(se_count - 1):
                    ne_off = i + 64 + k * 32
                    if ne_off + 32 <= len(root_data):
                        ne = root_data[ne_off:ne_off+32]
                        if ne[0] == 0xc1:
                            name_bytes += ne[2:32]
                
                name = name_bytes.decode('utf-16-le', errors='ignore').rstrip('\x00')
                if name:
                    print(f"      Name: {name}")
                
                i += 32 * (entry[1] + 1)
            else:
                i += 32
            
            entry_count += 1

trace_bitmap_allocation('PPSA17221-official.exfat', 'OFFICIAL')
trace_bitmap_allocation('fixed_contiguous.exfat', 'FIXED')
