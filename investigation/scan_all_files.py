#!/usr/bin/env python3
"""Recursively find all files in subdirectories."""
import struct
import sys

def read_directory(img_path, cluster_num, heap_offset, bps, spc):
    """Read and parse a directory cluster."""
    bytes_per_cluster = bps * spc
    sector_offset = heap_offset + (cluster_num - 2) * spc
    byte_offset = sector_offset * bps
    
    try:
        with open(img_path, 'rb') as f:
            f.seek(byte_offset)
            data = f.read(bytes_per_cluster)
    except:
        return []
    
    entries = []
    i = 0
    
    while i + 32 <= len(data):
        entry = data[i:i+32]
        type_code = entry[0]
        
        if not type_code:  # End of directory
            break
        
        # Skip secondary entries (handled with primary)
        if type_code < 0x81:
            i += 32
            continue
        
        # File or Directory entry
        if type_code == 0x85:
            se_count = entry[1]
            attr = struct.unpack('<H', entry[4:6])[0]
            is_dir = bool(attr & 0x10)
            
            # Read Stream Extension (next entry)
            if i + 32 < len(data):
                stream_ext = data[i+32:i+64]
                if stream_ext[0] == 0xC0:
                    flags = stream_ext[1]
                    nofatchain = bool(flags & 0x02)
                    data_size = struct.unpack('<Q', stream_ext[8:16])[0]
                    first_cluster = struct.unpack('<I', stream_ext[20:24])[0]
                    
                    # Read File Name entries
                    name_bytes = b''
                    for k in range(se_count - 1):  # -1 for stream ext
                        name_offset = i + 64 + k * 32
                        if name_offset + 32 <= len(data):
                            name_entry = data[name_offset:name_offset+32]
                            if name_entry[0] == 0xC1:
                                name_bytes += name_entry[2:32]
                    
                    # Decode name
                    name = name_bytes.decode('utf-16-le', errors='ignore').rstrip('\x00')
                    
                    entries.append({
                        'name': name,
                        'cluster': first_cluster,
                        'size': data_size,
                        'nofatchain': nofatchain,
                        'flags': flags,
                        'is_dir': is_dir,
                    })
            
            # Skip past all secondary entries
            i += 32 * (se_count + 1)
        else:
            i += 32
    
    return entries

def scan_all_files(img_path, cluster_num, heap_offset, bps, spc, prefix=''):
    """Recursively scan all directories."""
    all_files = []
    
    try:
        entries = read_directory(img_path, cluster_num, heap_offset, bps, spc)
    except:
        return all_files
    
    for entry in entries:
        full_name = prefix + entry['name']
        
        # Check if this file uses clusters in the bad range
        if 9430 <= entry['cluster'] <= 36004:
            print(f"FOUND: {full_name}")
            print(f"  Cluster: {entry['cluster']}, Size: {entry['size']}, NoFatChain: {entry['nofatchain']}")
        
        all_files.append(entry)
        
        # Recurse into subdirectories
        if entry['is_dir'] and entry['name'] not in ['.', '..']:
            all_files.extend(scan_all_files(img_path, entry['cluster'], heap_offset, bps, spc, full_name + '/'))
    
    return all_files

# Setup
with open('PPSA17221-official.exfat', 'rb') as f:
    f.seek(108)
    bps_shift = ord(f.read(1))
    spc_shift = ord(f.read(1))
    f.seek(88)
    heap_offset = struct.unpack('<I', f.read(4))[0]
    f.seek(96)
    root_cluster = struct.unpack('<I', f.read(4))[0]

bps = 1 << bps_shift
spc = 1 << spc_shift

print("SCANNING FOR FILES IN CLUSTER RANGE 9430-36004:")
print("=" * 70)

all_files = scan_all_files('PPSA17221-official.exfat', root_cluster, heap_offset, bps, spc)

print(f"\nTotal files/dirs found: {len(all_files)}")
