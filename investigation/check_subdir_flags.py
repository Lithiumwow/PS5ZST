#!/usr/bin/env python3
import struct

def check_subdir_flags(fname):
    print(f'\n=== {fname} ===')
    with open(fname, 'rb') as f:
        boot = f.read(512)
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        cluster_size = 32768
        
        # Read root directory
        root_offset = heap_offset * 512 + (4 - 2) * cluster_size
        f.seek(root_offset)
        root_data = f.read(cluster_size * 2)
        
        offset = 0
        entry_num = 0
        
        print("Root entries with directory info:")
        while offset < len(root_data) and entry_num < 100:
            entry = root_data[offset:offset+32]
            if entry[0] == 0x00:
                break
            elif entry[0] == 0x85:  # File/Dir entry
                # Get file attributes (bytes 4-5, little endian)
                attr = struct.unpack('<H', entry[4:6])[0]
                is_dir = bool(attr & 0x0010)  # FILE_ATTR_DIRECTORY = 0x0010
                
                next_entry = root_data[offset+32:offset+64]
                if len(next_entry) >= 32 and next_entry[0] == 0xC0:
                    name_entry = root_data[offset+64:offset+96]
                    if len(name_entry) >= 32 and name_entry[0] == 0xC1:
                        name_data = name_entry[2:32]
                        try:
                            name = name_data.decode('utf-16-le', errors='ignore').split('\x00')[0]
                            first_cluster = struct.unpack('<I', next_entry[20:24])[0]
                            dir_marker = "(DIR)" if is_dir else "(FILE)"
                            print(f"  {name:30} {dir_marker:6} cluster={first_cluster} attr={hex(attr)}")
                        except:
                            pass
            offset += 32
            entry_num += 1

check_subdir_flags('test-original-case.exfat')
check_subdir_flags('PPSA17221-official.exfat')
