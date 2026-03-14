#!/usr/bin/env python3
"""Extract bitmap and upcase cluster addresses from root directory."""

import struct

def extract_metadata_clusters(img_path, label):
    print(f"\n{'='*70}")
    print(f"METADATA CLUSTER ADDRESSES: {label}")
    print('='*70)
    
    with open(img_path, 'rb') as f:
        boot = f.read(512)
        
        bps_shift = boot[108]
        spc_shift = boot[109]
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        root_cluster = struct.unpack('<I', boot[96:100])[0]
        
        bps = 1 << bps_shift
        spc = 1 << spc_shift
        
        root_offset = (heap_offset + (root_cluster - 2) * spc) * bps
        
        f.seek(root_offset)
        root_data = f.read(spc * bps)
        
        print(f"\nRoot cluster: {root_cluster}")
        print(f"\n[Root Directory Entries (parsing correctly)]:\n")
        
        # Entry 0: Volume label (32 bytes) - type 0x83
        if root_data[0] == 0x83:
            char_count = root_data[1]
            name_data = root_data[2:2 + char_count * 2]
            name = name_data.decode('utf-16-le')
            print(f"Entry 0 (bytes 0-31): VOLUME LABEL")
            print(f"  Char count: {char_count}")
            print(f"  Name: '{name}'")
            print()
        
        # Entry 1: Alloc bitmap (32 bytes) - type 0x81
        if root_data[32] == 0x81:
            print(f"Entry 1 (bytes 32-63): ALLOC_BITMAP")
            alloc_bitmap_entry = root_data[32:64]
            bitmap_size = struct.unpack('<Q', alloc_bitmap_entry[8:16])[0]
            bitmap_cluster = struct.unpack('<I', alloc_bitmap_entry[20:24])[0]
            print(f"  Size field: {bitmap_size}")
            print(f"  Cluster: {bitmap_cluster}")
            print(f"  Bitmap data should be at cluster {bitmap_cluster}")
            print()
        
        # Entry 2: Upcase table (32 bytes) - type 0x82
        if root_data[64] == 0x82:
            print(f"Entry 2 (bytes 64-95): UPCASE_TABLE")
            upcase_entry = root_data[64:96]
            upcase_size = struct.unpack('<Q', upcase_entry[8:16])[0]
            upcase_cluster = struct.unpack('<I', upcase_entry[20:24])[0]
            print(f"  Size field: {upcase_size}")
            print(f"  Cluster: {upcase_cluster}")
            print(f"  Upcase data should be at cluster {upcase_cluster}")
            print()
        
        # List some file entries
        print(f"[File/Dir entries starting at byte 96]:")
        i = 96
        file_count = 0
        while i < len(root_data) and file_count < 5:
            if root_data[i] == 0x85:  # FILE entry
                entry = root_data[i:i+32]
                se_count = entry[1]
                se =root_data[i+32:i+64]
                if se[0] == 0xc0:
                    size = struct.unpack('<Q', se[8:16])[0]
                    cluster = struct.unpack('<I', se[20:24])[0]
                    
                    # Get name
                    name_bytes = b''
                    for k in range(se_count - 1):
                        ne_off = i + 64 + k * 32
                        if ne_off + 32 <= len(root_data):
                            ne = root_data[ne_off:ne_off+32]
                            if ne[0] == 0xc1:
                                name_bytes += ne[2:32]
                    
                    name = name_bytes.decode('utf-16-le', errors='ignore').rstrip('\x00')
                    print(f"  {name:30s} cluster={cluster:6d} size={size:10d}")
                    
                    i += 32 * (se_count + 1)
                    file_count += 1
                else:
                    i += 32
            elif root_data[i] == 0x00:
                break
            else:
                i += 32

extract_metadata_clusters('PPSA17221-official.exfat', 'OFFICIAL')
extract_metadata_clusters('fixed_contiguous.exfat', 'FIXED')
