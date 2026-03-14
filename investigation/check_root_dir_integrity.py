#!/usr/bin/env python3
"""Check root directory integrity - verify all dirent entries are valid."""

import struct

def check_exfat_root_integrity(exfat_path):
    """Check if root directory structure is valid."""
    with open(exfat_path, 'rb') as f:
        # Read boot sector
        f.seek(0)
        boot = f.read(512)
        
        bps_shift = boot[108]  # Bytes per sector shift (6 = 512 bytes)
        spc_shift = boot[109]  # Sectors per cluster shift (9 = 512 clusters = 32KB)
        fat_offset = struct.unpack('<I', boot[48:52])[0]
        fat_length = struct.unpack('<I', boot[52:56])[0]
        heap_offset = struct.unpack('<I', boot[56:60])[0]
        root_cluster = struct.unpack('<I', boot[60:64])[0]
        
        bytes_per_sector = 1 << bps_shift
        sectors_per_cluster = 1 << spc_shift
        cluster_size = bytes_per_sector * sectors_per_cluster
        
        print(f"Boot sector info:")
        print(f"  Bytes/sector: {bytes_per_sector}")
        print(f"  Sectors/cluster: {sectors_per_cluster}")
        print(f"  Cluster size: {cluster_size}")
        print(f"  FAT offset: {fat_offset} sectors")
        print(f"  FAT length: {fat_length} sectors")
        print(f"  Heap offset: {heap_offset} sectors")
        print(f"  Root cluster: {root_cluster}")
        print()
        
        # Calculate root directory offset
        root_offset = (heap_offset + (root_cluster - 2) * sectors_per_cluster) * bytes_per_sector
        print(f"Root directory offset: {root_offset} bytes (cluster {root_cluster})")
        print()
        
        # Read root directory and validate entries
        f.seek(root_offset)
        dirents = f.read(cluster_size)
        
        print("Checking directory entries...")
        entry_count = 0
        valid_count = 0
        
        for i in range(0, len(dirents), 32):
            entry = dirents[i:i+32]
            if len(entry) < 32:
                break
                
            entry_type = entry[0]
            in_use = (entry_type & 0x80) != 0
            
            if entry_type == 0x00:
                print(f"  Entry {entry_count}: End of directory (0x00)")
                break
            
            if not in_use:
                entry_count += 1
                continue
            
            entry_count += 1
            type_code = entry_type & 0x7F
            
            if type_code == 0x85:  # File entry
                name_len = entry[30]
                first_cluster = struct.unpack('<I', entry[20:24])[0]
                valid_data_len = struct.unpack('<Q', entry[16:24])[0]
                print(f"  Entry {entry_count}: FILE - cluster={first_cluster}, sz={valid_data_len}")
                valid_count += 1
                
            elif type_code == 0x83:  # Directory entry
                first_cluster = struct.unpack('<I', entry[20:24])[0]
                print(f"  Entry {entry_count}: DIR - cluster={first_cluster}")
                valid_count += 1
                
            elif type_code == 0xC0:  # Stream extension
                print(f"  Entry {entry_count}: STREAM_EXT")
                
            elif type_code == 0xC1:  # File name
                print(f"  Entry {entry_count}: FILENAME")
        
        print()
        print(f"Total entries parsed: {entry_count}")
        print(f"Valid file/dir entries: {valid_count}")
        print()
        
        # Check if structure makes sense
        if entry_count > 100000:
            print("⚠ WARNING: Entry count unusually high (>100k)")
            print("  This could indicate directory corruption or invalid end marker")
        else:
            print(f"✓ Entry count reasonable: {entry_count}")

if __name__ == '__main__':
    import sys
    
    official_path = 'PPSA17221-official.exfat'
    
    print("=" * 60)
    print(f"Checking: {official_path}")
    print("=" * 60)
    check_exfat_root_integrity(official_path)
