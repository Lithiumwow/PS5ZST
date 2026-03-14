#!/usr/bin/env python3
"""Identify files in official image that use FAT chains (not NoFatChain)."""
import struct

def parse_directory(img_path, cluster_num, heap_offset, bps, spc, bps_shift):
    """Parse a directory cluster and list files."""
    bytes_per_cluster = bps * spc
    offset = (heap_offset + (cluster_num - 2) * spc)  * bps
    
    with open(img_path, 'rb') as f:
        f.seek(offset)
        data = f.read(bytes_per_cluster)
    
    entries = []
    i = 0
    while i < len(data):
        # Read 32-byte directory entry
        for j in range(32):
            entry = data[i:i+32]
            if not entry[0]:  # End of directory
                return entries
            
            type_code = entry[0]
            if type_code < 0x81:  # Skip unused
                i += 32
                continue
            
            # File or Directory entry (0x85)
            if type_code == 0x85:
                se_count = entry[1]  # Secondary Entry Count
                # Next entries should be Stream Extension
                next_entry = data[i+32:i+64] if i+32 < len(data) else None
                if next_entry and next_entry[0] == 0xC0:
                    flags = next_entry[1]
                    nofatchain = bool(flags & 0x02)
                    data_size = struct.unpack('<Q', next_entry[8:16])[0]
                    first_cluster = struct.unpack('<I', next_entry[20:24])[0]
                    
                    # Read File Name entries
                    name_bytes = b''
                    for k in range(se_count - 1):  # -1 for stream ext
                        name_entry = data[i+32+32+k*32:i+32+32+k*32+32] if i+32+32+k*32 < len(data) else b''
                        if name_entry and name_entry[0] == 0xC1:
                            # Extract UTF-16LE name
                            name_bytes += name_entry[2:32]
                    
                    # Decode name
                    name = name_bytes.decode('utf-16-le', errors='ignore').rstrip('\x00')
                    
                    entries.append({
                        'name': name,
                        'cluster': first_cluster,
                        'size': data_size,
                        'nofatchain': nofatchain,
                        'flags': flags,
                    })
                
                # Skip the secondary entries
                i += 32 * (se_count + 1)
            else:
                i += 32
    
    return entries

# Open official image
with open('PPSA17221-official.exfat', 'rb') as f:
    f.seek(108)
    bps_shift = ord(f.read(1))
    spc_shift = ord(f.read(1))
    
    f.seek(88)
    heap_offset = struct.unpack('<I', f.read(4))[0]
    
    f.seek(96)
    root_cluster = struct.unpack('<I', f.read(4))[0]

bps = 1 << bps_shift
spc = 1 << spc_shift

print("FILES WITHOUT NOFATCHAIN (using regular FAT chains):")
print("=" * 70)

entries = parse_directory('PPSA17221-official.exfat', root_cluster, heap_offset, bps, spc, bps_shift)

files_without_nofat = []
for entry in entries:
    if not entry['nofatchain']:
        files_without_nofat.append(entry)
        print(f"  {entry['name']}")
        print(f"    Cluster: {entry['cluster']}, Size: {entry['size']} bytes, Flags: 0x{entry['flags']:02x}")

if not files_without_nofat:
    print("  [NONE - all files use NoFatChain]")
    
print(f"\nTotal files without NoFatChain: {len(files_without_nofat)}")
print(f"Total files/dirs: {len(entries)}")
