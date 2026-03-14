#!/usr/bin/env python3
"""Compare file sizes in official vs test image."""
import struct

def list_files(path, name):
    with open(path, 'rb') as f:
        boot = f.read(512)
        
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        root_cluster = struct.unpack('<I', boot[96:100])[0]
        spc_shift = boot[109]
        spc = 1 << spc_shift
        cluster_size = spc * 512
        
        root_offset = heap_offset * 512 + (root_cluster - 2) * cluster_size
        
        f.seek(root_offset)
        root_data = f.read(cluster_size * 4)
        
        print(f"\n{name.upper()}:")
        print("=" * 60)
        
        offset = 0
        entry_num = 0
        
        while offset < len(root_data) and entry_num < 30:
            entry = root_data[offset:offset+32]
            if len(entry) < 32:
                break
            
            entry_type = entry[0]
            
            if entry_type == 0x00:
                break
            elif entry_type == 0x85:
                file_size = struct.unpack('<Q', entry[24:32])[0]
                print(f"[{entry_num:2}] FILE size={file_size:12} bytes")
            elif entry_type >= 0xC0:
                pass  # Skip continuation
            
            offset += 32
            entry_num += 1

list_files('PPSA17221-official.exfat', 'Official')
list_files('test-official-match.exfat', 'Test (Generated)')
