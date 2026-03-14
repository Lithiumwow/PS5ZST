#!/usr/bin/env python3
"""Extract and show file names and sizes from directory entries."""
import struct

def extract_filenames(path, name):
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
        entry_num = 0
        current_file = None
        current_size = 0
        
        while offset < len(root_data) and entry_num < 100:
            entry = root_data[offset:offset+32]
            if len(entry) < 32:
                break
            
            entry_type = entry[0]
            
            if entry_type == 0x00:
                if current_file:
                    print(f"  {current_file}: {current_size} bytes")
                break
            elif entry_type == 0x85:
                if current_file:
                    print(f"  {current_file}: {current_size} bytes")
                current_size = struct.unpack('<Q', entry[24:32])[0]
                current_file = None
            elif entry_type == 0xC0:  # Stream Extension
                pass
            elif entry_type == 0xC1:  # File name continuation
                if current_file is None:
                    current_file = ""
                # Next 30 bytes are UTF-16LE filename
                name_data = entry[2:32]
                try:
                    chars = name_data.decode('utf-16-le', errors='ignore').split('\x00')[0]
                    current_file += chars
                except:
                    pass
            
            offset += 32
            entry_num += 1

extract_filenames('PPSA17221-official.exfat', 'OFFICIAL')
extract_filenames('test-official-match.exfat', 'TEST (generated)')
