#!/usr/bin/env python3
import struct

def check_data_lengths(fname):
    print(f'\n=== {fname} ===')
    with open(fname, 'rb') as f:
        boot = f.read(512)
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        cluster_size = 32768
        
        # Find sce_sys
        root_offset = heap_offset * 512 + (4 - 2) * cluster_size
        f.seek(root_offset)
        root_data = f.read(cluster_size * 2)
        
        sce_sys_cluster = None
        offset = 0
        while offset < len(root_data):
            entry = root_data[offset:offset+32]
            if entry[0] == 0x85:
                next_entry = root_data[offset+32:offset+64]
                if len(next_entry) >= 32 and next_entry[0] == 0xC0:
                    name_entry = root_data[offset+64:offset+96]
                    if len(name_entry) >= 32 and name_entry[0] == 0xC1:
                        name = name_entry[2:32].decode('utf-16-le', errors='ignore').split('\x00')[0]
                        if name == 'sce_sys':
                            sce_sys_cluster = struct.unpack('<I', next_entry[20:24])[0]
                            break
            offset += 32
        
        if sce_sys_cluster:
            sce_sys_offset = heap_offset * 512 + (sce_sys_cluster - 2) * cluster_size
            f.seek(sce_sys_offset)
            sce_sys_data = f.read(cluster_size * 4)
            
            print("File ValidDataLength vs DataLength in sce_sys:")
            offset = 0
            entry_num = 0
            
            while offset < len(sce_sys_data) and entry_num < 200:
                entry = sce_sys_data[offset:offset+32]
                if entry[0] == 0x00:
                    break
                elif entry[0] == 0x85:
                    next_entry = sce_sys_data[offset+32:offset+64]
                    if len(next_entry) >= 32 and next_entry[0] == 0xC0:
                        # ValidDataLength is at bytes 8-15
                        valid_len = struct.unpack('<Q', next_entry[8:16])[0]
                        # DataLength is at bytes 24-31
                        data_len = struct.unpack('<Q', next_entry[24:32])[0]
                        
                        name_entry = sce_sys_data[offset+64:offset+96]
                        if len(name_entry) >= 32 and name_entry[0] == 0xC1:
                            name = name_entry[2:32].decode('utf-16-le', errors='ignore').split('\x00')[0]
                            
                            match = "✓" if valid_len == data_len else "✗ MISMATCH"
                            print(f"  {name:25} valid={valid_len:10} data={data_len:10} {match}")
                offset += 32
                entry_num += 1

check_data_lengths('test-original-case.exfat')
check_data_lengths('PPSA17221-official.exfat')
