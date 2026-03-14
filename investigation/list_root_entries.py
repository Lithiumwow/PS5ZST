#!/usr/bin/env python3
"""List all entries in root directory."""

import struct

def list_root_entries(exfat_path):
    """List all root directory entries."""
    with open(exfat_path, 'rb') as f:
        f.seek(0)
        boot = f.read(512)
        
        bps_shift = boot[108]
        spc_shift = boot[109]
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        root_cluster = struct.unpack('<I', boot[96:100])[0]
        
        bytes_per_sector = 1 << bps_shift
        sectors_per_cluster = 1 << spc_shift
        cluster_size = bytes_per_sector * sectors_per_cluster
        
        # Root offset: heap_offset is in sectors, so convert properly
        # Cluster N starts at: heap_offset_sectors + (N - 2) * sectors_per_cluster
        root_offset_sectors = heap_offset + (root_cluster - 2) * sectors_per_cluster
        root_offset = root_offset_sectors * bytes_per_sector
        
        print(f"  bps_shift: {bps_shift}, spc_shift: {spc_shift}")
        print(f"  bytes_per_sector: {bytes_per_sector}, sectors_per_cluster: {sectors_per_cluster}")
        print(f"  cluster_size: {cluster_size}")
        print(f"  heap_offset: {heap_offset} sectors")
        print(f"  root_cluster: {root_cluster}")
        print(f"  root_offset_sectors: {root_offset_sectors}")
        print(f"  root_offset (bytes): {root_offset}")
        print()
        
        f.seek(root_offset)
        first_bytes = f.read(64)
        print(f"  First 64 bytes at root: {first_bytes.hex()}")
        print()
        
        f.seek(root_offset)
        dirents = f.read(cluster_size)
        
        count = 0
        for i in range(0, len(dirents), 32):
            entry = dirents[i:i+32]
            type_code = entry[0]
            
            if type_code == 0x00:
                print("  [END OF DIRECTORY]")
                break
            
            if type_code < 0x81:  # Invalid/unused entries
                continue
            
            if type_code == 0x83:
                print(f"  {count}: VOLUME_LABEL")
            elif type_code == 0x81:
                print(f"  {count}: ALLOC_BITMAP")
            elif type_code == 0x82:
                print(f"  {count}: UPCASE_TABLE")
            elif type_code == 0x85:
                attr = entry[4]
                if attr & 0x10:
                    print(f"  {count}: DIRECTORY")
                else:
                    print(f"  {count}: FILE")
            elif type_code == 0xC0:
                print(f"  {count}: STREAM_EXT")
            elif type_code == 0xC1:
                name_len = entry[3]
                try:
                    name = entry[2:2+name_len*2].decode('utf-16le')
                    print(f"  {count}: FILENAME - {name}")
                except:
                    print(f"  {count}: FILENAME - (decode error)")
            else:
                print(f"  {count}: UNKNOWN(0x{type_code:02x})")
            
            count += 1
            if count > 100:
                print("  ... (truncated after 100 entries)")
                break

print("OFFICIAL:")
list_root_entries('PPSA17221-official.exfat')

print("\nGENERATED:")
list_root_entries('test-ps5-final.exfat')
