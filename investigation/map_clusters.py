#!/usr/bin/env python3
"""Map clusters 2-10 to see what's actually allocated."""

import struct

def check_clusters(img_path, label):
    print(f"\n{'='*70}")
    print(f"CLUSTER LAYOUT: {label}")
    print('='*70)
    
    with open(img_path, 'rb') as f:
        boot = f.read(512)
        
        bps_shift = boot[108]
        spc_shift = boot[109]
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        
        bps = 1 << bps_shift
        spc = 1 << spc_shift
        offset_per_cluster = spc * bps
        
        print(f"Cluster layout (offset in bytes from heap):\n")
        
        for cluster in range(2, 12):
            cluster_offset = (heap_offset + (cluster - 2) * spc) * bps
            f.seek(cluster_offset)
            
            # Read first 64 bytes
            data = f.read(64)
            
            # Check for patterns
            hex_preview = ' '.join(f'{b:02x}' for b in data[:32])
            
            # Determine content type by first byte
            first_byte = data[0]
            
            if first_byte == 0x83:
                content = "VOLUME_LABEL"
            elif first_byte == 0x81:
                content = "ALLOC_BITMAP"
            elif first_byte == 0x82:
                content = "UPCASE_TABLE"
            elif first_byte == 0x85:
                content = "FILE/DIR entry"
            elif first_byte == 0xff:
                content = "All 0xFF (unused/end)"
            elif first_byte == 0x00:
                content = "All zeros (empty)"
            else:
                # Check if it looks like file/directory data
                content = f"0x{first_byte:02x} (possible data)"
            
            print(f"Cluster {cluster:2d} (byte offset {cluster_offset:>10d}): {content}")
            print(f"           {hex_preview}")

check_clusters('PPSA17221-official.exfat', 'OFFICIAL')
check_clusters('fixed_contiguous.exfat', 'FIXED')
