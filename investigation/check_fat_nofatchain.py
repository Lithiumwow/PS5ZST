#!/usr/bin/env python3
import struct

def check_fat_for_nofatchain_files(fname):
    """Check FAT entries for files marked with NoFatChain"""
    print(f"\n=== {fname} ===")
    with open(fname, 'rb') as f:
        boot = f.read(512)
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        fat_offset = struct.unpack('<I', boot[80:84])[0]
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
                    name = root_data[offset+64:offset+96][2:32].decode('utf-16-le', errors='ignore').split('\x00')[0]
                    if name == 'sce_sys':
                        sce_sys_cluster = struct.unpack('<I', next_entry[20:24])[0]
                        break
            offset += 32
        
        if sce_sys_cluster:
            sce_sys_offset = heap_offset * 512 + (sce_sys_cluster - 2) * cluster_size
            f.seek(sce_sys_offset)
            sce_sys_data = f.read(cluster_size * 4)
            
            print("FAT entries for NoFatChain files:")
            offset = 0
            while offset < len(sce_sys_data):
                entry = sce_sys_data[offset:offset+32]
                if entry[0] == 0x00:
                    break
                elif entry[0] == 0x85:
                    next_entry = sce_sys_data[offset+32:offset+64]
                    if len(next_entry) >= 32 and next_entry[0] == 0xC0:
                        flags = next_entry[1]
                        no_fat_chain = bool(flags & 0x02)
                        
                        if no_fat_chain:
                            cluster = struct.unpack('<I', next_entry[20:24])[0]
                            
                            # Read FAT entry
                            fat_byte_offset = fat_offset * 512 + cluster * 4
                            f.seek(fat_byte_offset)
                            fat_entry = struct.unpack('<I', f.read(4))[0]
                            
                            name_entry = sce_sys_data[offset+64:offset+96]
                            if len(name_entry) >= 32 and name_entry[0] == 0xC1:
                                name = name_entry[2:32].decode('utf-16-le', errors='ignore').split('\x00')[0]
                                print(f"  {name:25} cluster={cluster:5} FAT={hex(fat_entry)}")
                offset += 32

check_fat_for_nofatchain_files('test-original-case.exfat')
check_fat_for_nofatchain_files('PPSA17221-official.exfat')
