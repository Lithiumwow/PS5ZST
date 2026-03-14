#!/usr/bin/env python3
import struct

def check_first_cluster_of_dir(fname):
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
        
        print("Subdirectories and their FirstCluster:")
        while offset < len(root_data):
            entry = root_data[offset:offset+32]
            if entry[0] == 0x00:
                break
            elif entry[0] == 0x85:  # File/Dir entry
                attr = struct.unpack('<H', entry[4:6])[0]
                is_dir = bool(attr & 0x0010)
                
                if is_dir:
                    next_entry = root_data[offset+32:offset+64]
                    if len(next_entry) >= 32 and next_entry[0] == 0xC0:
                        # Get FirstClusterOfFile from Stream Extension
                        first_cluster = struct.unpack('<I', next_entry[20:24])[0]
                        
                        # Get FirstClusterOfFile field - in Stream Extension it's the same location
                        # But let's verify the structure
                        name_entry = root_data[offset+64:offset+96]
                        if len(name_entry) >= 32 and name_entry[0] == 0xC1:
                            name_data = name_entry[2:32]
                            try:
                                name = name_data.decode('utf-16-le', errors='ignore').split('\x00')[0]
                                
                                # For directories, FirstClusterOfFile points to the directory stream
                                size = struct.unpack('<Q', next_entry[24:32])[0]
                                
                                print(f"  {name:20} cluster={first_cluster:5} size={size:10}")
                                
                                # Now read the first entry in that directory
                                dir_offset = heap_offset * 512 + (first_cluster - 2) * cluster_size
                                f.seek(dir_offset)
                                dir_data = f.read(96)  # Read first 3 entries
                                
                                print(f"    First bytes of dir stream: {dir_data[:96].hex()}")
                                
                                # Check if directory stream starts with valid entries
                                first_entry_type = dir_data[0]
                                print(f"    First entry type: {hex(first_entry_type)}")
                                
                            except Exception as e:
                                print(f"    Error: {e}")
            offset += 32

check_first_cluster_of_dir('test-original-case.exfat')
check_first_cluster_of_dir('PPSA17221-official.exfat')
