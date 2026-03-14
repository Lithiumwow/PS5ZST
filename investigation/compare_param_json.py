#!/usr/bin/env python3
"""Find and compare param.json entries in both images."""

import struct

def find_param_json_entry(exfat_path):
    """Find param.json in root directory and return surrounding entries."""
    with open(exfat_path, 'rb') as f:
        # Read boot sector
        f.seek(0)
        boot = f.read(512)
        
        bps_shift = boot[108]
        spc_shift = boot[109]
        fat_offset = struct.unpack('<I', boot[80:84])[0]
        fat_length = struct.unpack('<I', boot[84:88])[0]
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        root_cluster = struct.unpack('<I', boot[96:100])[0]
        
        bytes_per_sector = 1 << bps_shift
        sectors_per_cluster = 1 << spc_shift
        cluster_size = bytes_per_sector * sectors_per_cluster
        
        # Calculate root directory offset
        root_offset = (heap_offset + (root_cluster - 2) * sectors_per_cluster) * bytes_per_sector
        
        # Read root directory
        f.seek(root_offset)
        dirents = f.read(cluster_size)
        
        # Find param.json
        for i in range(0, len(dirents) - 96, 32):
            entry = dirents[i:i+32]
            entry_type = entry[0]
            
            if entry_type == 0x00:
                break
            
            if (entry_type & 0x80) == 0:
                continue
            
            type_code = entry_type & 0x7F
            
            # Look for FILE entry followed by STREAM + FILENAME containing "param"
            if type_code == 0x85:  # FILE
                next_entry = dirents[i+32:i+64]
                next_type = next_entry[0] & 0x7F if (next_entry[0] & 0x80) else -1
                
                if next_type == 0xC0:  # Has Stream Extension
                    name_entry = dirents[i+64:i+96]
                    name_type = name_entry[0] & 0x7F if (name_entry[0] & 0x80) else -1
                    
                    if name_type == 0xC1:  # Has Filename
                        name_len = name_entry[3]
                        name_data = name_entry[2:2+(name_len*2)]
                        try:
                            name = name_data.decode('utf-16le')
                            if 'param' in name.lower():
                                return (entry, next_entry, name_entry, name)
                        except:
                            pass
    
    return None

result = find_param_json_entry('PPSA17221-official.exfat')
if result:
    file_entry, stream_entry, name_entry, name = result
    print("OFFICIAL IMAGE - param.json entries:")
    print(f"  Filename: {name}")
    print(f"\n  FILE ENTRY (bytes):")
    print(f"    {file_entry.hex()}")
    print(f"\n  FILE ENTRY (fields):")
    print(f"    Type: 0x{file_entry[0]:02x}")
    print(f"    Attr: 0x{file_entry[4]:02x}")
    print(f"    Create: {file_entry[8:12].hex()}")
    print(f"    Modify: {file_entry[12:16].hex()}")
    print(f"    Access: {file_entry[16:20].hex()}")
    file_size = struct.unpack('<Q', file_entry[8:16])[0]
    print(f"    File size: {file_size}")
    first_cluster = struct.unpack('<I', file_entry[20:24])[0]
    print(f"    First cluster: {first_cluster}")
    
    print(f"\n  STREAM EXTENSION (bytes):")
    print(f"    {stream_entry.hex()}")
    print(f"\n  STREAM EXTENSION (fields):")
    print(f"    Type: 0x{stream_entry[0]:02x}")
    print(f"    Flags: 0x{stream_entry[1]:02x}")
    print(f"    Name_len: {stream_entry[3]}")
    data_len = struct.unpack('<Q', stream_entry[8:16])[0]
    valid_len = struct.unpack('<Q', stream_entry[16:24])[0]
    first_cluster_s = struct.unpack('<I', stream_entry[20:24])[0]
    print(f"    Data length: {data_len}")
    print(f"    Valid length: {valid_len}")
    print(f"    First cluster: {first_cluster_s}")
    
    print(f"\n  FILENAME ENTRY (bytes):")
    print(f"    {name_entry.hex()}")
else:
    print("param.json NOT FOUND in official image")

print("\n" + "="*70 + "\n")

result2 = find_param_json_entry('test-ps5-final.exfat')
if result2:
    file_entry, stream_entry, name_entry, name = result2
    print("GENERATED IMAGE - param.json entries:")
    print(f"  Filename: {name}")
    print(f"\n  FILE ENTRY (bytes):")
    print(f"    {file_entry.hex()}")
    print(f"\n  FILE ENTRY (fields):")
    print(f"    Type: 0x{file_entry[0]:02x}")
    print(f"    Attr: 0x{file_entry[4]:02x}")
    print(f"    Create: {file_entry[8:12].hex()}")
    print(f"    Modify: {file_entry[12:16].hex()}")
    print(f"    Access: {file_entry[16:20].hex()}")
    file_size = struct.unpack('<Q', file_entry[8:16])[0]
    print(f"    File size: {file_size}")
    first_cluster = struct.unpack('<I', file_entry[20:24])[0]
    print(f"    First cluster: {first_cluster}")
    
    print(f"\n  STREAM EXTENSION (bytes):")
    print(f"    {stream_entry.hex()}")
    print(f"\n  STREAM EXTENSION (fields):")
    print(f"    Type: 0x{stream_entry[0]:02x}")
    print(f"    Flags: 0x{stream_entry[1]:02x}")
    print(f"    Name_len: {stream_entry[3]}")
    data_len = struct.unpack('<Q', stream_entry[8:16])[0]
    valid_len = struct.unpack('<Q', stream_entry[16:24])[0]
    first_cluster_s = struct.unpack('<I', stream_entry[20:24])[0]
    print(f"    Data length: {data_len}")
    print(f"    Valid length: {valid_len}")
    print(f"    First cluster: {first_cluster_s}")
    
    print(f"\n  FILENAME ENTRY (bytes):")
    print(f"    {name_entry.hex()}")
else:
    print("param.json NOT FOUND in generated image")

# Compare
if result and result2:
    print("\n" + "="*70)
    print("COMPARISON:")
    file1, stream1, name1, _ = result
    file2, stream2, name2, _ = result2
    
    if file1 == file2:
        print("✓ FILE ENTRY: IDENTICAL")
    else:
        print("✗ FILE ENTRY: DIFFERS")
        print(f"  Official:  {file1.hex()}")
        print(f"  Generated: {file2.hex()}")
    
    if stream1 == stream2:
        print("✓ STREAM ENTRY: IDENTICAL")
    else:
        print("✗ STREAM ENTRY: DIFFERS")
        print(f"  Official:  {stream1.hex()}")
        print(f"  Generated: {stream2.hex()}")
    
    if name1 == name2:
        print("✓ FILENAME ENTRY: IDENTICAL")
    else:
        print("✗ FILENAME ENTRY: DIFFERS")
        print(f"  Official:  {name1.hex()}")
        print(f"  Generated: {name2.hex()}")
