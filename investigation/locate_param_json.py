#!/usr/bin/env python3
"""Find param.json in sce_sys/ and compare between images."""

import struct

def probe_exfat(exfat_path):
    """Quick probe of exFAT geometry."""
    with open(exfat_path, 'rb') as f:
        f.seek(0)
        boot = f.read(512)
        
        bps_shift = boot[108]
        spc_shift = boot[109]
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        root_cluster = struct.unpack('<I', boot[96:100])[0]
        
        bytes_per_sector = 1 << bps_shift
        sectors_per_cluster = 1 << spc_shift
        cluster_size = bytes_per_sector * sectors_per_cluster
        
        return heap_offset, root_cluster, cluster_size, bytes_per_sector

def read_dir_cluster(exfat_path, cluster_num):
    """Read data from a specific cluster."""
    heap_offset, _, cluster_size, bytes_per_sector = probe_exfat(exfat_path)
    
    offset = (heap_offset + (cluster_num - 2) * (cluster_size // bytes_per_sector)) * bytes_per_sector
    
    with open(exfat_path, 'rb') as f:
        f.seek(offset)
        return f.read(cluster_size)

def find_sce_sys_in_root(exfat_path):
    """Find sce_sys directory cluster in root."""
    heap_offset, root_cluster, cluster_size, bytes_per_sector = probe_exfat(exfat_path)
    
    root_offset = (heap_offset + (root_cluster - 2) * (cluster_size // bytes_per_sector)) * bytes_per_sector
    
    with open(exfat_path, 'rb') as f:
        f.seek(root_offset)
        dirents = f.read(cluster_size)
        
        for i in range(0, len(dirents) - 64, 32):
            entry = dirents[i:i+32]
            if entry[0] == 0x00:
                break
            if (entry[0] & 0x80) == 0:
                continue
            
            type_code = entry[0] & 0x7F
            if type_code == 0x85:  # FILE/DIR
                attr = entry[4]
                if attr & 0x10:  # Directory
                    # Check next entry for name
                    name_e = dirents[i+32:i+64]
                    if (name_e[0] & 0x80) and (name_e[0] & 0x7F) == 0xC1:
                        name_len = name_e[3]
                        try:
                            name = name_e[2:2+name_len*2].decode('utf-16le')
                            if name == 'sce_sys':
                                cluster = struct.unpack('<I', entry[20:24])[0]
                                return cluster
                        except:
                            pass
    
    return None

def find_param_json_in_dir(exfat_path, dir_cluster):
    """Find param.json in a directory cluster."""
    dirents = read_dir_cluster(exfat_path, dir_cluster)
    
    for i in range(0, len(dirents) - 64, 32):
        entry = dirents[i:i+32]
        if entry[0] == 0x00:
            break
        if (entry[0] & 0x80) == 0:
            continue
        
        type_code = entry[0] & 0x7F
        if type_code == 0x85:  # FILE
            stream_e = dirents[i+32:i+64]
            if not ((stream_e[0] & 0x80) and (stream_e[0] & 0x7F) == 0xC0):
                continue
            
            name_e = dirents[i+64:i+96]
            if not ((name_e[0] & 0x80) and (name_e[0] & 0x7F) == 0xC1):
                continue
            
            name_len = name_e[3]
            try:
                name = name_e[2:2+name_len*2].decode('utf-16le')
                if name == 'param.json':
                    return (entry.hex(), stream_e.hex(), name_e.hex(), name)
            except:
                pass
    
    return None

# Check official
print("OFFICIAL IMAGE:")
sce_sys_cluster = find_sce_sys_in_root('PPSA17221-official.exfat')
if sce_sys_cluster:
    print(f"  sce_sys cluster: {sce_sys_cluster}")
    result = find_param_json_in_dir('PPSA17221-official.exfat', sce_sys_cluster)
    if result:
        file_hex, stream_hex, name_hex, name = result
        print(f"  param.json found: {name}")
        print(f"    FILE:   {file_hex}")
        print(f"    STREAM: {stream_hex}")
        print(f"    NAME:   {name_hex}")
    else:
        print("  param.json NOT FOUND")
else:
    print("  sce_sys NOT FOUND")

print("\nGENERATED IMAGE:")
sce_sys_cluster = find_sce_sys_in_root('test-ps5-final.exfat')
if sce_sys_cluster:
    print(f"  sce_sys cluster: {sce_sys_cluster}")
    result = find_param_json_in_dir('test-ps5-final.exfat', sce_sys_cluster)
    if result:
        file_hex, stream_hex, name_hex, name = result
        print(f"  param.json found: {name}")
        print(f"    FILE:   {file_hex}")
        print(f"    STREAM: {stream_hex}")
        print(f"    NAME:   {name_hex}")
    else:
        print("  param.json NOT FOUND")
else:
    print("  sce_sys NOT FOUND")
