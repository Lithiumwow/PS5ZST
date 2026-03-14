#!/usr/bin/env python3
import struct

def find_param_offset(fname):
    """Find the raw offset of param.json directory entry"""
    with open(fname, 'rb') as f:
        boot = f.read(512)
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        cluster_size = 32768
        
        # Find sce_sys directory cluster
        root_offset = heap_offset * 512 + (4 - 2) * cluster_size
        f.seek(root_offset)
        root_data = f.read(cluster_size * 2)
        
        sce_sys_cluster = None
        offset = 0
        entry_num = 0
        
        while offset < len(root_data) and entry_num < 100:
            entry = root_data[offset:offset+32]
            if entry[0] == 0x85:
                next_entry = root_data[offset+32:offset+64]
                if next_entry[0] == 0xC0:
                    name_entry = root_data[offset+64:offset+96]
                    if name_entry[0] == 0xC1:
                        name_data = name_entry[2:32]
                        try:
                            name = name_data.decode('utf-16-le', errors='ignore').split('\x00')[0]
                            if 'sce_sys' in name:
                                sce_sys_cluster = struct.unpack('<I', next_entry[20:24])[0]
                        except:
                            pass
            offset += 32
            entry_num += 1
        
        # Now find param.json in sce_sys
        if sce_sys_cluster:
            sce_sys_offset = heap_offset * 512 + (sce_sys_cluster - 2) * cluster_size
            f.seek(sce_sys_offset)
            sce_sys_data = f.read(cluster_size * 4)
            
            offset = 0
            entry_num = 0
            while offset < len(sce_sys_data) and entry_num < 200:
                entry = sce_sys_data[offset:offset+32]
                if entry[0] == 0x00:
                    break
                elif entry[0] == 0x85:
                    next_entry = sce_sys_data[offset+32:offset+64] if offset+64 <= len(sce_sys_data) else b''
                    if len(next_entry) >= 32 and next_entry[0] == 0xC0:
                        name_entry = sce_sys_data[offset+64:offset+96] if offset+96 <= len(sce_sys_data) else b''
                        if len(name_entry) >= 32 and name_entry[0] == 0xC1:
                            name_data = name_entry[2:32]
                            try:
                                name = name_data.decode('utf-16-le', errors='ignore').split('\x00')[0]
                                if 'param' in name.lower():
                                    # Return all 3 entries (File, StreamExt, FileName)
                                    return {
                                        'file_entry': entry,
                                        'stream_entry': next_entry,
                                        'name_entry': name_entry,
                                        'offset': sce_sys_offset + offset
                                    }
                            except:
                                pass
                offset += 32
                entry_num += 1
        
    return None

print("=== Generated Image ===")
gen = find_param_offset('test-official-match.exfat')
if gen:
    print(f"File entry: {gen['file_entry'].hex()}")
    print(f"Stream ext: {gen['stream_entry'].hex()}")
    print(f"Name entry: {gen['name_entry'].hex()}")
    print(f"Offset: {hex(gen['offset'])}")

print("\n=== Official Image ===")
off = find_param_offset('PPSA17221-official.exfat')
if off:
    print(f"File entry: {off['file_entry'].hex()}")
    print(f"Stream ext: {off['stream_entry'].hex()}")
    print(f"Name entry: {off['name_entry'].hex()}")
    print(f"Offset: {hex(off['offset'])}")

if gen and off:
    print("\n=== DIFFERENCES ===")
    fe_match = gen['file_entry'] == off['file_entry']
    se_match = gen['stream_entry'] == off['stream_entry']
    ne_match = gen['name_entry'] == off['name_entry']
    print(f"File entry: {'MATCH' if fe_match else 'DIFFER'}")
    print(f"Stream ext: {'MATCH' if se_match else 'DIFFER'}")
    print(f"Name entry: {'MATCH' if ne_match else 'DIFFER'}")
