#!/usr/bin/env python3
import struct

def _name_hash(enc_name):
    h = 0
    for i in range(0, len(enc_name), 2):
        char = struct.unpack('<H', enc_name[i:i+2])[0]
        h = ((h << 15) | (h >> 1)) & 0xFFFF
        h = (h + char) & 0xFFFF
    return h

# Test param.json
name = 'param.json'
hash_orig = _name_hash(name.encode('utf-16-le'))
print(f'Hash("param.json" original case) = {hex(hash_orig)}')
print(f'Generated image (uppercase version) had: 0xd99a')
print(f'Generated image (new/original case) should have: {hex(hash_orig)}')
print(f'Official image had: 0xafaa')

# Now check the new image
with open('test-original-case.exfat', 'rb') as f:
    boot = f.read(512)
    heap_offset = struct.unpack('<I', boot[88:92])[0]
    cluster_size = 32768
    
    # Find sce_sys
    root_offset = heap_offset * 512 + (4 - 2) * cluster_size
    f.seek(root_offset)
    root_data = f.read(cluster_size * 2)
    
    offset = 0
    sce_sys_cluster = None
    while offset < len(root_data):
        entry = root_data[offset:offset+32]
        if entry[0] == 0x85:
            next_entry = root_data[offset+32:offset+64]
            if len(next_entry) >= 32 and next_entry[0] == 0xC0:
                name_entry = root_data[offset+64:offset+96]
                if len(name_entry) >= 32 and name_entry[0] == 0xC1:
                    name_data = name_entry[2:32]
                    try:
                        n = name_data.decode('utf-16-le', errors='ignore').split('\x00')[0]
                        if 'sce_sys' in n:
                            sce_sys_cluster = struct.unpack('<I', next_entry[20:24])[0]
                            break
                    except:
                        pass
        offset += 32
    
    if sce_sys_cluster:
        sce_sys_offset = heap_offset * 512 + (sce_sys_cluster - 2) * cluster_size
        f.seek(sce_sys_offset)
        sce_sys_data = f.read(cluster_size * 4)
        
        offset = 0
        while offset < len(sce_sys_data):
            entry = sce_sys_data[offset:offset+32]
            if entry[0] == 0x00:
                break
            elif entry[0] == 0x85:
                next_entry = sce_sys_data[offset+32:offset+64]
                if len(next_entry) >= 32 and next_entry[0] == 0xC0:
                    name_entry = sce_sys_data[offset+64:offset+96]
                    if len(name_entry) >= 32 and name_entry[0] == 0xC1:
                        name_data = name_entry[2:32]
                        try:
                            n = name_data.decode('utf-16-le', errors='ignore').split('\x00')[0]
                            if 'param' in n.lower():
                                stored_hash = struct.unpack('<H', next_entry[4:6])[0]
                                print(f'\nNew image param.json hash: {hex(stored_hash)}')
                                print(f'Expected (original case): {hex(hash_orig)}')
                                print(f'Match: {stored_hash == hash_orig}')
                        except:
                            pass
            offset += 32
