#!/usr/bin/env python3
"""Check Stream Extension entry details."""
import struct

def check_stream_ext(path, name):
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
        
        print(f"\n{name}:")
        print("=" * 70)
        
        offset = 0
        file_count = 0
        
        while offset < len(root_data) and file_count < 8:
            entry = root_data[offset:offset+32]
            if len(entry) < 32:
                break
            
            entry_type = entry[0]
            
            if entry_type == 0x00:
                break
            elif entry_type == 0x85:
                # File entry - next should be Stream Extension
                next_entry = root_data[offset+32:offset+64]
                if next_entry[0] == 0xC0:  # Stream Extension
                    flags = next_entry[1]
                    valid_len = struct.unpack('<Q', next_entry[8:16])[0]
                    data_len = struct.unpack('<Q', next_entry[24:32])[0]
                    print(f"File #{file_count}: flags=0x{flags:02X}, ValidLen={valid_len}, DataLen={data_len}")
                    file_count += 1
            
            offset += 32

check_stream_ext('PPSA17221-official.exfat', 'OFFICIAL')
check_stream_ext('test-official-match.exfat', 'TEST (generated)')
