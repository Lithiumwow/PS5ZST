#!/usr/bin/env python3
"""Check if param.json is in the exFAT image."""
import struct

exfat = 'test-official-match.exfat'

with open(exfat, 'rb') as f:
    # Read boot sector
    boot = f.read(512)
    
    heap_offset = struct.unpack('<I', boot[88:92])[0]
    root_cluster = struct.unpack('<I', boot[96:100])[0]
    spc_shift = boot[109]
    spc = 1 << spc_shift
    cluster_size = spc * 512
    
    # Seek to root directory
    root_offset = heap_offset * 512 + (root_cluster - 2) * cluster_size
    
    # Read multiple clusters to get all root entries
    f.seek(root_offset)
    root_data = f.read(cluster_size * 4)  # Read 4 clusters of root
    
    # Search for param.json in directory entries
    found = False
    offset = 0
    entry_count = 0
    while offset < len(root_data) and entry_count < 1000:
        entry = root_data[offset:offset+32]
        if len(entry) < 32:
            break
        
        entry_type = entry[0]
        
        if entry_type == 0x00:  # End of directory
            break
        elif entry_type == 0x85:  # File entry
            # Next entry should be name continuation
            if offset + 32 < len(root_data):
                next_entry = root_data[offset+32:offset+64]
                if next_entry[0] >= 0xC0:  # Continuation entry
                    name_len_entries = next_entry[0] & 0x3F
                    # Extract name from continuation entries
                    name_data = b''
                    for i in range(1, name_len_entries + 1):
                        cont_offset = offset + i*32
                        if cont_offset + 32 <= len(root_data):
                            cont_entry = root_data[cont_offset:cont_offset+32]
                            name_data += cont_entry[2:32]  # 30 bytes per continuation
                    
                    # Decode UTF-16LE name
                    try:
                        name = name_data.split(b'\x00\x00')[0].decode('utf-16-le', errors='ignore')
                        if 'param' in name.lower():
                            print(f"Found: {name} (at offset {offset})")
                            found = True
                    except:
                        pass
        
        offset += 32
        entry_count += 1

if not found:
    print("param.json NOT found in root directory!")
    print("This explains the PS5 error.")
