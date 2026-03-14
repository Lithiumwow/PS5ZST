#!/usr/bin/env python3
import struct

def check_stream_ext_flags(fname):
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
            
            print("Stream Extension flags for files in sce_sys:")
            offset = 0
            
            while offset < len(sce_sys_data):
                entry = sce_sys_data[offset:offset+32]
                if entry[0] == 0x00:
                    break
                elif entry[0] == 0x85:
                    next_entry = sce_sys_data[offset+32:offset+64]
                    if len(next_entry) >= 32 and next_entry[0] == 0xC0:
                        # Byte 1 = GeneralSecondaryFlags
                        flags = next_entry[1]
                        alloc = bool(flags & 0x01)
                        no_fat_chain = bool(flags & 0x02)
                        
                        name_entry = sce_sys_data[offset+64:offset+96]
                        if len(name_entry) >= 32 and name_entry[0] == 0xC1:
                            name = name_entry[2:32].decode('utf-16-le', errors='ignore').split('\x00')[0]
                            print(f"  {name:25} flags={hex(flags):4} alloc={alloc} no_fat_chain={no_fat_chain}")
                offset += 32

check_stream_ext_flags('test-original-case.exfat')
check_stream_ext_flags('PPSA17221-official.exfat')
