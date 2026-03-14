#!/usr/bin/env python3
"""Deep dive into param.json directory entries and file metadata."""

import struct

def extract_root_dirents(exfat_path):
    """Extract and print all root directory entries, highlighting param.json."""
    with open(exfat_path, 'rb') as f:
        # Read boot sector
        f.seek(0)
        boot = f.read(512)
        
        bps_shift = boot[108]
        spc_shift = boot[109]
        fat_offset = struct.unpack('<I', boot[80:84])[0]  # Correct offset
        fat_length = struct.unpack('<I', boot[84:88])[0]  # Correct offset
        heap_offset = struct.unpack('<I', boot[88:92])[0]  # Correct offset
        root_cluster = struct.unpack('<I', boot[96:100])[0]  # Correct offset
        
        bytes_per_sector = 1 << bps_shift
        sectors_per_cluster = 1 << spc_shift
        cluster_size = bytes_per_sector * sectors_per_cluster
        
        # Calculate root directory offset
        root_offset = (heap_offset + (root_cluster - 2) * sectors_per_cluster) * bytes_per_sector
        
        print(f"Geometry: cluster_size={cluster_size}, root_cluster={root_cluster}")
        print(f"Root directory at byte offset: {root_offset}")
        print()
        
        # Read root directory
        f.seek(root_offset)
        dirents = f.read(cluster_size)
        
        entry_index = 0
        param_json_entries = []
        
        for i in range(0, len(dirents), 32):
            entry = dirents[i:i+32]
            if len(entry) < 32:
                break
            
            entry_type = entry[0]
            if entry_type == 0x00:
                print(f"Entry {entry_index}: EOD marker")
                break
            
            if (entry_type & 0x80) == 0:
                entry_index += 1
                continue
            
            type_code = entry_type & 0x7F
            
            # Parse based on type
            if type_code == 0x85:  # FILE
                print(f"\nEntry {entry_index}: FILE")
                print(f"  Attributes: 0x{entry[4]:02x}")
                print(f"  Create time: {struct.unpack('<I', entry[8:12])[0]:08x}")
                print(f"  Last modified: {struct.unpack('<I', entry[12:16])[0]:08x}")
                print(f"  Last accessed: {struct.unpack('<I', entry[16:20])[0]:08x}")
                file_size = struct.unpack('<Q', entry[8:16])[0]
                print(f"  File size: {file_size}")
                first_cluster = struct.unpack('<I', entry[20:24])[0]
                print(f"  First cluster: {first_cluster}")
                print(f"  GeneralSecondaryFlags: 0x{entry[4]:02x}")
                
                # Check for param.json
                # Look next entry for filename
                if i + 32 < len(dirents):
                    next_entry = dirents[i+32:i+64]
                    if next_entry[0] & 0x80:
                        next_type = next_entry[0] & 0x7F
                        if next_type == 0xC0:  # Stream extension
                            print(f"  -> followed by Stream Extension")
                            # Look for filename after stream
                            if i + 64 < len(dirents):
                                name_entry = dirents[i+64:i+96]
                                if name_entry[0] & 0x80:
                                    if (name_entry[0] & 0x7F) == 0xC1:
                                        name_len = name_entry[30]
                                        name_data = name_entry[2:2+(name_len*2)]
                                        try:
                                            name = name_data.decode('utf-16le')
                                            print(f"  -> Filename: '{name}'")
                                            if 'param' in name.lower():
                                                param_json_entries.append((entry_index, entry))
                                        except:
                                            pass
            
            elif type_code == 0xC0:  # STREAM EXTENSION
                print(f"\nEntry {entry_index}: STREAM EXTENSION")
                print(f"  General Secondary Flags: 0x{entry[1]:02x}")
                print(f"  Name Length: {entry[3]}")
                data_len = struct.unpack('<Q', entry[8:16])[0]
                valid_len = struct.unpack('<Q', entry[16:24])[0]
                first_cluster = struct.unpack('<I', entry[20:24])[0]
                print(f"  Data Length: {data_len}")
                print(f"  Valid Data Length: {valid_len}")
                print(f"  First Cluster: {first_cluster}")
                print(f"  Raw bytes [0-32]: {entry.hex()}")
            
            elif type_code == 0xC1:  # FILE NAME
                print(f"\nEntry {entry_index}: FILENAME")
                print(f"  General Secondary Flags: 0x{entry[1]:02x}")
                print(f"  Name Length: {entry[3]}")
                name_len = entry[3]
                name_data = entry[2:2+(name_len*2)]
                try:
                    name = name_data.decode('utf-16le')
                    print(f"  Filename: '{name}'")
                    print(f"  Name hash: 0x{struct.unpack('<H', entry[4:6])[0]:04x}")
                except:
                    print(f"  (decode error)")
            
            elif type_code == 0x83:  # Volume label
                print(f"\nEntry {entry_index}: VOLUME LABEL")
                label_len = entry[1]
                label_data = entry[2:2+(label_len*2)]
                try:
                    label = label_data.decode('utf-16le')
                    print(f"  Label: '{label}'")
                except:
                    pass
            
            elif type_code == 0x81:  # Allocation bitmap
                print(f"\nEntry {entry_index}: ALLOCATION BITMAP")
                first_cluster = struct.unpack('<I', entry[20:24])[0]
                size = struct.unpack('<Q', entry[8:16])[0]
                print(f"  Size: {size} bytes")
                print(f"  First cluster: {first_cluster}")
            
            elif type_code == 0x82:  # Upcase table
                print(f"\nEntry {entry_index}: UPCASE TABLE")
                first_cluster = struct.unpack('<I', entry[20:24])[0]
                checksum = struct.unpack('<I', entry[4:8])[0]
                size = struct.unpack('<Q', entry[8:16])[0]
                print(f"  Size: {size} bytes")
                print(f"  Checksum: 0x{checksum:08x}")
                print(f"  First cluster: {first_cluster}")
            
            entry_index += 1
        
        return param_json_entries

print("=" * 70)
print("OFFICIAL IMAGE (OSFMount)")
print("=" * 70)
official_param = extract_root_dirents('PPSA17221-official.exfat')

print("\n\n" + "=" * 70)
print("GENERATED IMAGE (Python)")
print("=" * 70)
generated_param = extract_root_dirents('test-ps5-final.exfat')
