#!/usr/bin/env python3
"""Extract file list recursively from exFAT."""
import struct

def list_all_files(path, show_sizes=False):
    with open(path, 'rb') as f:
        boot = f.read(512)
        
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        spc_shift = boot[109]
        spc = 1 << spc_shift
        cluster_size = spc * 512
        
        def read_directory(dir_cluster):
            offset_bytes = heap_offset * 512 + (dir_cluster - 2) * cluster_size
            f.seek(offset_bytes)
            
            files = []
            dir_data = f.read(cluster_size * 4)  # Read up to 4 clusters
            
            offset = 0
            current_entry = None
            
            while offset < len(dir_data):
                entry = dir_data[offset:offset+32]
                if len(entry) < 32:
                    break
                
                entry_type = entry[0]
                
                if entry_type == 0x00:
                    break
                elif entry_type == 0x85:
                    # File/directory entry
                    if current_entry:
                        files.append(current_entry)
                    
                    is_dir = bool(entry[4] & 0x10)  # Directory bit
                    cluster = struct.unpack('<I', entry[20:24])[0]
                    current_entry = {
                        'type': 'dir' if is_dir else 'file',
                        'cluster': cluster,
                        'name': '',
                        'size': 0,
                    }
                elif entry_type == 0xC0:
                    # Stream extension - has actual size
                    if current_entry:
                        current_entry['size'] = struct.unpack('<Q', entry[24:32])[0]
                elif entry_type == 0xC1:
                    # Filename
                    if current_entry:
                        name_data = entry[2:32]
                        try:
                            chars = name_data.decode('utf-16-le', errors='ignore').split('\x00')[0]
                            current_entry['name'] += chars
                        except:
                            pass
                
                offset += 32
            
            if current_entry:
                files.append(current_entry)
            
            return files
        
        # Start from root (cluster 4)
        root_files = read_directory(4)
        
        def print_tree(files, prefix=''):
            for f in files:
                if f['type'] == 'dir':
                    print(f"{prefix}[DIR]  {f['name']}/")
                    # Recursively read subdirectory
                    try:
                        subfiles = read_directory(f['cluster'])
                        print_tree(subfiles, prefix + '  ')
                    except:
                        pass
                else:
                    if show_sizes:
                        print(f"{prefix}[FILE] {f['name']} ({f['size']} bytes)")
                    else:
                        print(f"{prefix}[FILE] {f['name']}")
        
        print_tree(root_files)

print("OFFICIAL:")
print("=" * 50)
list_all_files('PPSA17221-official.exfat')

print("\n\nTEST (generated):")
print("=" * 50)
list_all_files('test-official-match.exfat')
