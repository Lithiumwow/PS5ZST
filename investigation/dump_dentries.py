#!/usr/bin/env python3
"""
Dump raw directory entry bytes to identify invalid fields.
"""
import struct
import sys

def dump_dentries(image_path):
    print(f"Directory Entry Dump: {image_path}\n")
    
    with open(image_path, 'rb') as f:
        # Get geometry
        boot = f.read(512)
        heap_off = struct.unpack('<I', boot[88:92])[0]
        root_cluster = struct.unpack('<I', boot[96:100])[0]
        bps_shift = boot[108]
        spc_shift = boot[109]
        
        bps = 1 << bps_shift
        spc = 1 << spc_shift
        cs = bps * spc
        
        # Seek to root directory
        root_off = heap_off * bps + (root_cluster - 2) * cs
        f.seek(root_off)
        
        # Read first few entries
        entries = []
        for i in range(20):
            entry_data = f.read(32)
            if len(entry_data) < 32:
                break
            entries.append((i, entry_data))
        
        # Display
        for idx, data in entries:
            etype = data[0]
            
            if etype == 0x00:
                print(f"[{idx}] EOD")
                break
            elif etype == 0x81:
                print(f"[{idx}] ALLOCATION BITMAP (0x81)")
                print(f"      Flags: {hex(data[1])}")
                cluster = struct.unpack('<I', data[20:24])[0]
                size = struct.unpack('<Q', data[24:32])[0]
                print(f"      Cluster: {cluster}, Size: {size} bytes")
            elif etype == 0x82:
                print(f"[{idx}] UPCASE TABLE (0x82)")
                checksum = struct.unpack('<I', data[4:8])[0]
                cluster = struct.unpack('<I', data[20:24])[0]
                size = struct.unpack('<Q', data[24:32])[0]
                print(f"      Checksum: {hex(checksum)}")
                print(f"      Cluster: {cluster}, Size: {size} bytes ({size // (1<<10)} KiB)")
            elif etype == 0x83:
                print(f"[{idx}] VOLUME LABEL (0x83)")
                char_count = data[1]
                label_bytes = data[2:2+char_count*2]
                try:
                    label = label_bytes.decode('utf-16-le')
                    print(f"      Label: '{label}'")
                except:
                    print(f"      Label: {label_bytes.hex()}")
            elif etype == 0x85:
                print(f"[{idx}] FILE ENTRY (0x85)")
                sec_count = data[1]
                checksum = struct.unpack('<H', data[2:4])[0]
                print(f"      SecondaryCount: {sec_count}")
                print(f"      SetChecksum: {hex(checksum)}")
                attr = struct.unpack('<H', data[4:6])[0]
                print(f"      Attributes: {hex(attr)}")
                
                # Timestamps
                ctime = struct.unpack('<H', data[8:10])[0]
                cdate = struct.unpack('<H', data[10:12])[0]
                print(f"      CreateTime: {hex(ctime)}, CreateDate: {hex(cdate)}")
                
                # Try to parse next entries for this file
                if sec_count > 0 and idx + 1 < len(entries):
                    next_data = entries[idx+1][1]
                    if next_data[0] == 0xC0:  # Stream extension
                        print(f"      [Secondary] STREAM EXTENSION (0xC0)")
                        flags = next_data[1]
                        print(f"        Flags: {hex(flags)} (binary: {bin(flags)})")
                        name_len = next_data[3]
                        name_hash = struct.unpack('<H', next_data[4:6])[0]
                        print(f"        NameLen: {name_len}, NameHash: {hex(name_hash)}")
                        
                        valid_data_len = struct.unpack('<Q', next_data[8:16])[0]
                        data_cluster = struct.unpack('<I', next_data[20:24])[0]
                        data_len = struct.unpack('<Q', next_data[24:32])[0]
                        print(f"        ValidDataLength: {valid_data_len}")
                        print(f"        DataCluster: {data_cluster}")
                        print(f"        DataLength: {data_len}")
            elif etype == 0xC0:
                continue  # Skip, already printed
            elif etype == 0xC1:
                print(f"[{idx}] FILE NAME (0xC1)")
                name_bytes = data[2:32]
                try:
                    # Try to find null terminator
                    name_part = name_bytes.split(b'\x00\x00')[0]
                    if name_part:
                        name = name_part.decode('utf-16-le', errors='ignore')
                        print(f"      Name part: '{name}'")
                except:
                    pass
            else:
                print(f"[{idx}] UNKNOWN TYPE {hex(etype)}")
            
            print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python dump_dentries.py <image.exfat>")
        sys.exit(1)
    
    dump_dentries(sys.argv[1])
