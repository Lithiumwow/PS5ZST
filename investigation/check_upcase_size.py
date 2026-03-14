#!/usr/bin/env python3
import struct

official = 'PPSA17221-official.exfat'
updated = 'PPSA17221-updated.exfat'

def check_upcase_size(path):
    with open(path, 'rb') as f:
        boot = f.read(512)
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        root_cluster = struct.unpack('<I', boot[96:100])[0]
        spc_shift = boot[109]
        spc = 1 << spc_shift
        cluster_size = spc * 512
        
        # Read root directory
        root_offset = heap_offset * 512 + (root_cluster - 2) * cluster_size
        f.seek(root_offset)
        root_data = f.read(cluster_size)
        
        # Find upcase entry
        offset = 0
        while offset < len(root_data):
            entry = root_data[offset:offset+32]
            if entry[0] == 0x82:  # Upcase table
                size = struct.unpack('<Q', entry[24:32])[0]
                return size, cluster_size, (size + cluster_size - 1) // cluster_size
            offset += 32
    return None, None, None

off_size, off_cs, off_clusters = check_upcase_size(official)
upd_size, upd_cs, upd_clusters = check_upcase_size(updated)

print(f"UPCASE TABLE SIZE COMPARISON:")
print(f"  Official: {off_size} bytes ({off_clusters} clusters)")
print(f"  Updated:  {upd_size} bytes ({upd_clusters} clusters)")
