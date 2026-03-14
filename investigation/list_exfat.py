#!/usr/bin/env python3
"""List files in exFAT root and first few subdirectories."""
import struct

exfat = 'test-official-match.exfat'

with open(exfat, 'rb') as f:
    boot = f.read(512)
    
    heap_offset = struct.unpack('<I', boot[88:92])[0]
    root_cluster = struct.unpack('<I', boot[96:100])[0]
    spc_shift = boot[109]
    spc = 1 << spc_shift
    cluster_size = spc * 512
    
    # Read root directory
    root_offset = heap_offset * 512 + (root_cluster - 2) * cluster_size
    
    f.seek(root_offset)
    root_data = f.read(cluster_size * 2)
    
    print("ROOT DIRECTORY ENTRIES (first 50):\n")
    offset = 0
    entry_num = 0
    
    while offset < len(root_data) and entry_num < 50:
        entry = root_data[offset:offset+32]
        if len(entry) < 32:
            break
        
        entry_type = entry[0]
        
        if entry_type == 0x00:
            print(f"[{entry_num}] END OF DIRECTORY")
            break
        elif entry_type == 0x03:
            print(f"[{entry_num}] ALLOC_BITMAP")
        elif entry_type == 0x82:
            print(f"[{entry_num}] UPCASE_TABLE")
        elif entry_type == 0x83:
            print(f"[{entry_num}] VOLUME_LABEL")
        elif entry_type == 0x81:
            flags = entry[1]
            subdir_count = struct.unpack('<H', entry[28:30])[0] if len(entry) >= 30 else 0
            print(f"[{entry_num}] DIRECTORY (flags={flags}, subdir_count={subdir_count})")
        elif entry_type == 0x85:
            file_size = struct.unpack('<Q', entry[24:32])[0]
            print(f"[{entry_num}] FILE (size={file_size} bytes)")
        elif entry_type >= 0xC0:
            char_count = entry[0] & 0x3F
            print(f"[{entry_num}] FILENAME_CONTINUATION (chars={char_count})")
        else:
            print(f"[{entry_num}] UNKNOWN TYPE 0x{entry_type:02X}")
        
        offset += 32
        entry_num += 1
