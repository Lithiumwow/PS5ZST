#!/usr/bin/env python3
"""Compare param.json directory entries in both images in excruciating detail."""
import struct

def detailed_param_compare(official_file, generated_file):
    print("="*80)
    print("PARAM.JSON DETAILED COMPARISON")
    print("="*80)
    
    for fname, label in [(official_file, "OFFICIAL"), (generated_file, "GENERATED")]:
        print(f"\n{label} IMAGE: {fname}")
        print("-" * 80)
        
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
                    if next_entry[0] == 0xC0:
                        name = root_data[offset+64:offset+96][2:32].decode('utf-16-le', errors='ignore').split('\x00')[0]
                        if name == 'sce_sys':
                            sce_sys_cluster = struct.unpack('<I', next_entry[20:24])[0]
                            break
                offset += 32
            
            if not sce_sys_cluster:
                print("  ERROR: sce_sys directory not found!")
                continue
            
            sce_sys_offset = heap_offset * 512 + (sce_sys_cluster - 2) * cluster_size
            f.seek(sce_sys_offset)
            sce_sys_data = f.read(cluster_size * 4)
            
            # Find param.json
            offset = 0
            found = False
            while offset < len(sce_sys_data):
                entry = sce_sys_data[offset:offset+32]
                if entry[0] == 0x00:
                    break
                elif entry[0] == 0x85:
                    next_entry = sce_sys_data[offset+32:offset+64]
                    if next_entry[0] == 0xC0:
                        name_entry = sce_sys_data[offset+64:offset+96]
                        if name_entry[0] == 0xC1:
                            name = name_entry[2:32].decode('utf-16-le', errors='ignore').split('\x00')[0]
                            if 'param' in name.lower():
                                found = True
                                print(f"  Found param.json at sce_sys offset {hex(offset)}")
                                
                                # Print all 3 entries in detail
                                print(f"\n  FILE ENTRY (0x85):")
                                print(f"    Hex: {entry.hex()}")
                                print(f"    [0] Type: {hex(entry[0])}")
                                print(f"    [1] SecondaryCount: {entry[1]}")
                                print(f"    [2-3] SetChecksum: {hex(struct.unpack('<H', entry[2:4])[0])}")
                                print(f"    [4-5] FileAttributes: {hex(struct.unpack('<H', entry[4:6])[0])}")
                                
                                print(f"\n  STREAM EXTENSION (0xC0):")
                                print(f"    Hex: {next_entry.hex()}")
                                print(f"    [0] Type: {hex(next_entry[0])}")
                                print(f"    [1] GeneralSecondaryFlags: {hex(next_entry[1])}")
                                print(f"    [3] NameLength: {next_entry[3]}")
                                print(f"    [4-5] NameHash: {hex(struct.unpack('<H', next_entry[4:6])[0])}")
                                print(f"    [8-15] ValidDataLength: {struct.unpack('<Q', next_entry[8:16])[0]}")
                                print(f"    [20-23] FirstClusterOfFile: {struct.unpack('<I', next_entry[20:24])[0]}")
                                print(f"    [24-31] DataLength: {struct.unpack('<Q', next_entry[24:32])[0]}")
                                
                                print(f"\n  FILE NAME (0xC1):")
                                print(f"    Hex: {name_entry.hex()}")
                                print(f"    [0] Type: {hex(name_entry[0])}")
                                print(f"    [1] GeneralSecondaryFlags: {hex(name_entry[1])}")
                                print(f"    [2-32] Name data: {name_entry[2:32].hex()}")
                                
                                # Check if file data exists
                                param_cluster = struct.unpack('<I', next_entry[20:24])[0]
                                param_size = struct.unpack('<Q', next_entry[24:32])[0]
                                param_offset = heap_offset * 512 + (param_cluster - 2) * cluster_size
                                f.seek(param_offset)
                                param_file_data = f.read(min(100, param_size))
                                print(f"\n  FILE DATA CHECK:")
                                print(f"    Cluster: {param_cluster}")
                                print(f"    Size: {param_size}")
                                print(f"    Data offset in image: {hex(param_offset)}")
                                print(f"    First 50 bytes: {param_file_data[:50].hex()}")
                                
                offset += 32
            
            if not found:
                print("  ERROR: param.json not found in sce_sys!")

detailed_param_compare('PPSA17221-official.exfat', 'test-ps5-final.exfat')
