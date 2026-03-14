#!/usr/bin/env python3
"""Extract and analyze param.json from both official and generated exFAT images."""

import struct
import os

def find_param_json_clusters(exfat_path):
    """Find where param.json is stored in the exFAT image."""
    with open(exfat_path, 'rb') as f:
        # Read boot sector
        f.seek(0)
        boot = f.read(512)
        
        bps_shift = boot[108]
        spc_shift = boot[109]
        fat_offset = struct.unpack('<I', boot[48:52])[0]
        fat_length = struct.unpack('<I', boot[52:56])[0]
        heap_offset = struct.unpack('<I', boot[56:60])[0]
        root_cluster = struct.unpack('<I', boot[60:64])[0]
        
        bytes_per_sector = 1 << bps_shift
        sectors_per_cluster = 1 << spc_shift
        cluster_size = bytes_per_sector * sectors_per_cluster
        
        print(f"\nGeometry:")
        print(f"  Cluster size: {cluster_size} bytes")
        print(f"  Root cluster: {root_cluster}")
        print(f"  FAT offset: {fat_offset} sectors")
        print(f"  Heap offset: {heap_offset} sectors")
        
        # Find root directory
        root_offset = (heap_offset + (root_cluster - 2) * sectors_per_cluster) * bytes_per_sector
        print(f"  Root offset: {root_offset}")
        
        # Read root directory to find param.json
        f.seek(root_offset)
        dirents = f.read(cluster_size)
        
        print(f"\nSearching for param.json in root directory...")
        
        param_clusters = []
        param_size = 0
        param_valid_len = 0
        found_file = False
        found_stream = False
        
        for i in range(0, len(dirents), 32):
            entry = dirents[i:i+32]
            if len(entry) < 32:
                break
            
            entry_type = entry[0]
            if entry_type == 0x00:
                break
            if (entry_type & 0x80) == 0:
                continue
            
            type_code = entry_type & 0x7F
            
            # Check for filename entry
            if type_code == 0xC1:  # Filename
                # Extract filename from entry (UTF-16 encoding)
                name_entry = dirents[i:i+32]
                name_len = name_entry[30]
                name_data = name_entry[2:2+(name_len*2)]
                try:
                    name = name_data.decode('utf-16le')
                    if 'param' in name.lower():
                        print(f"  Found filename entry: '{name}' at offset {root_offset + i}")
                except:
                    pass
            
            # Check for file entry
            if type_code == 0x85:  # File
                name_len = entry[30]
                first_cluster = struct.unpack('<I', entry[20:24])[0]
                file_size = struct.unpack('<Q', entry[16:24])[0]
                valid_len = struct.unpack('<Q', entry[24:32])[0]
                
                # Look back for filename
                if i >= 32:
                    prev_entry = dirents[i-32:i]
                    if len(prev_entry) >= 32:
                        prev_type = prev_entry[0]
                        if (prev_type & 0x7F) == 0xC1:
                            name_data = prev_entry[2:2+(name_len*2)]
                            try:
                                name = name_data.decode('utf-16le')
                                if name.lower().endswith('.json') and 'param' in name.lower():
                                    print(f"\n✓ Found param.json file entry:")
                                    print(f"  First cluster: {first_cluster}")
                                    print(f"  File size: {file_size} bytes")
                                    print(f"  Valid data length: {valid_len} bytes")
                                    param_clusters.append(first_cluster)
                                    param_size = file_size
                                    param_valid_len = valid_len
                                    found_file = True
                            except:
                                pass
            
            # Check for stream extension
            if type_code == 0xC0:  # Stream extension
                data_len = struct.unpack('<Q', entry[8:16])[0]
                valid_len = struct.unpack('<Q', entry[16:24])[0]
                start_cluster = struct.unpack('<I', entry[20:24])[0]
                
                if found_file:
                    print(f"  Stream extension data_len: {data_len}, valid_len: {valid_len}, start_cluster: {start_cluster}")
                    found_stream = True
        
        if found_file and param_clusters:
            # Extract the file data
            print(f"\nExtracting param.json data...")
            cluster_offset = (heap_offset + (param_clusters[0] - 2) * sectors_per_cluster) * bytes_per_sector
            print(f"  Data cluster offset: {cluster_offset}")
            
            f.seek(cluster_offset)
            param_data = f.read(min(param_size, 10000))  # Read first 10KB
            
            print(f"\nFirst 500 bytes of param.json:")
            print(param_data[:500])
            print(f"\nAs text (first 300 chars):")
            try:
                print(param_data[:300].decode('utf-8', errors='replace'))
            except:
                print("(not text)")
            
            return param_data
        
        return None

print("="*60)
print("OFFICIAL IMAGE (OSFMount)")
print("="*60)
official_data = find_param_json_clusters('PPSA17221-official.exfat')

print("\n\n" + "="*60)
print("GENERATED IMAGE (Python)")
print("="*60)
generated_data = find_param_json_clusters('test-ps5-final.exfat')

if official_data and generated_data:
    print("\n" + "="*60)
    print("COMPARISON")
    print("="*60)
    
    if official_data == generated_data:
        print("✓ param.json data is IDENTICAL")
    else:
        print("✗ param.json data DIFFERS")
        print(f"  Official size: {len(official_data)}")
        print(f"  Generated size: {len(generated_data)}")
        
        # Find first difference
        min_len = min(len(official_data), len(generated_data))
        for i in range(min_len):
            if official_data[i] != generated_data[i]:
                print(f"  First difference at byte {i}:")
                print(f"    Official: 0x{official_data[i]:02x}")
                print(f"    Generated: 0x{generated_data[i]:02x}")
                break
