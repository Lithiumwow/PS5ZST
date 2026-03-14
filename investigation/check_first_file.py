#!/usr/bin/env python3
import struct

f = open('test-original-case.exfat', 'rb')
boot = f.read(512)
heap_offset = struct.unpack('<I', boot[88:92])[0]
cluster_size = 32768

root_offset = heap_offset * 512 + (4 - 2) * cluster_size
f.seek(root_offset)
root_data = f.read(cluster_size * 2)

sce_sys_cluster = None
offset = 0
while offset < len(root_data):
    entry = root_data[offset:offset+32]
    if entry[0] == 0x85:
        next_entry = root_data[offset+32:offset+64]
        if next_entry[0] == 0xC0:
            name = root_data[offset+64:offset+96][2:32].decode('utf-16-le', errors='ignore').split('\x00')[0]
            if 'sce_sys' in name:
                sce_sys_cluster = struct.unpack('<I', next_entry[20:24])[0]
                break
    offset += 32

if sce_sys_cluster:
    sce_sys_offset = heap_offset * 512 + (sce_sys_cluster - 2) * cluster_size
    f.seek(sce_sys_offset)
    first_entry = f.read(32)
    next_entry = f.read(32)
    name_entry = f.read(32)
    
    print('First file in sce_sys subdirectory:')
    print(f'  Entry type: {hex(first_entry[0])}')
    print(f'  Name entry type follows: {hex(name_entry[0])}')
    name_text = name_entry[2:32].decode("utf-16-le", errors="ignore").split(chr(0))[0]
    print(f'  Name: {name_text}')
    
    # Check if first entry is actually a directory
    attr = struct.unpack('<H', first_entry[4:6])[0]
    is_dir = bool(attr & 0x0010)
    print(f'  Is directory? {is_dir}')
    print(f'  File attributes: {hex(attr)}')
