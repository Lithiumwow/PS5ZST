#!/usr/bin/env python3
"""Check what cluster numbers we're assigning in the actual write."""

import struct

def analyze_root_directory(img_path, label):
    """Read root directory from boot sector's root cluster."""
    print(f"\n{'='*70}")
    print(f"ROOT DIRECTORY CONTENT: {label}")
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
        
        print(f"\nRoot cluster from boot sector: {root_cluster}")
        print(f"Root offset: {root_offset} bytes")
        
        f.seek(root_offset)
        root_data = f.read(spc * bps)
        
        # Parse entries
        print(f"\n[Root Directory Entries]:\n")
        i = 0
        entry_num = 0
        
        while i < len(root_data) and root_data[i] != 0 and entry_num < 10:
            entry_type = root_data[i]
            
            type_map = {
                0x81: "ALLOC_BITMAP",
                0x82: "UPCASE_TABLE",
                0x83: "FILE/DIR (0x83)",
                0x85: "FILE (0x85)",
            }
            type_name = type_map.get(entry_type, f"0x{entry_type:02x}")
            
            secondary_count = root_data[i+1] if entry_type in [0x81, 0x82, 0x85, 0x83] else 0
            
            print(f"Entry {entry_num} @ offset {i}:")
            print(f"  Type: {type_name} (0x{entry_type:02x})")
            print(f"  Secondary count: {secondary_count}")
            
            # If it has a secondary entry immediately following, show it
            if i + 32 < len(root_data) and entry_type in [0x81, 0x82, 0x85, 0x83]:
                se = root_data[i+32:i+64]
                print(f"  Secondary entry type: 0x{se[0]:02x}")
                
                # If it looks like file data entry
                if se[0] == 0xc0:
                    size = struct.unpack('<Q', se[8:16])[0]
                    cluster = struct.unpack('<I', se[20:24])[0]
                    print(f"    Size: {size}")
                    print(f"    Cluster: {cluster}")
            
            print()
            
            # Move to next entry group
            if entry_type in [0x81, 0x82, 0x85, 0x83]:
                i += 32 * (secondary_count + 1)
            else:
                i += 32
            
            entry_num += 1

analyze_root_directory('PPSA17221-official.exfat', 'OFFICIAL')
analyze_root_directory('fixed_contiguous.exfat', 'FIXED')
