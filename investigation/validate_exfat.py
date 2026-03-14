#!/usr/bin/env python3
"""
Comprehensive exFAT image validator.
Checks structural validity against Microsoft exFAT specification.
"""

import struct
import sys
from pathlib import Path

def read_u32(f, offset):
    f.seek(offset)
    return struct.unpack('<I', f.read(4))[0]

def read_u16(f, offset):
    f.seek(offset)
    return struct.unpack('<H', f.read(2))[0]

def read_bytes(f, offset, length):
    f.seek(offset)
    return f.read(length)

def validate_exfat(image_path):
    """Run comprehensive exFAT validation."""
    print(f"Validating: {image_path}")
    with open(image_path, 'rb') as f:
        # Read boot sector
        boot = f.read(512)
        
        # Extract key fields
        oem = boot[3:11]
        boot_sig = struct.unpack('<H', boot[510:512])[0]
        vol_len_sects = struct.unpack('<Q', boot[72:80])[0]
        fat_offset = struct.unpack('<I', boot[80:84])[0]
        fat_length = struct.unpack('<I', boot[84:88])[0]
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        cluster_count = struct.unpack('<I', boot[92:96])[0]
        root_cluster = struct.unpack('<I', boot[96:100])[0]
        bps_shift = boot[108]
        spc_shift = boot[109]
        
        bps = 1 << bps_shift
        spc = 1 << spc_shift
        cs = bps * spc
        
        print(f"\n=== Boot Sector ===")
        print(f"OEM: {oem}")
        print(f"Boot Signature: {hex(boot_sig)} {'✓' if boot_sig == 0xAA55 else '✗ WRONG'}")
        print(f"Volume Length: {vol_len_sects} sectors ({vol_len_sects * 512 / (1<<20):.1f} MiB)")
        print(f"Bytes Per Sector: {bps} (shift={bps_shift})")
        print(f"Sectors Per Cluster: {spc} (shift={spc_shift})")
        print(f"Cluster Size: {cs} bytes ({cs // 1024} KiB)")
        print(f"FAT Offset: sector {fat_offset}, Length: {fat_length} sectors")
        print(f"Heap Offset: sector {heap_offset}")
        print(f"Total Clusters: {cluster_count}")
        print(f"Root Cluster: {root_cluster}")
        
        # Validate layout constraints
        print(f"\n=== Layout Validation ===")
        fat_end_sector = fat_offset + fat_length
        if fat_end_sector <= heap_offset:
            print(f"✓ FAT region (sectors {fat_offset}-{fat_end_sector-1}) does not overlap heap (sector {heap_offset})")
        else:
            print(f"✗ OVERLAP: FAT ends at sector {fat_end_sector} but heap starts at {heap_offset}")
        
        # Check reserved sectors not used
        if fat_offset >= 24:
            print(f"✓ FAT starts at sector {fat_offset} (after 24-sector boot VBR)")
        else:
            print(f"✗ FAT at sector {fat_offset} overlaps boot region (0-23)")
        
        # Validate root cluster number
        if root_cluster >= 2:
            print(f"✓ Root cluster {root_cluster} >= 2 (valid)")
        else:
            print(f"✗ Root cluster {root_cluster} < 2 (invalid)")
        
        # Read and validate FAT entries
        print(f"\n=== FAT Table ===")
        fat_data = read_bytes(f, fat_offset * bps, min(fat_length * bps, 512))
        fat0 = struct.unpack('<I', fat_data[0:4])[0]
        fat1 = struct.unpack('<I', fat_data[4:8])[0]
        print(f"FAT[0] (media): {hex(fat0)} {'✓' if fat0 == 0xFFFFFFF8 else '✗'}")
        print(f"FAT[1] (reserved): {hex(fat1)} {'✓' if fat1 == 0xFFFFFFFF else '✗'}")
        
        # Sample some file clusters
        if fat_length * bps >= 32:
            fat2 = struct.unpack('<I', fat_data[8:12])[0]
            fat3 = struct.unpack('<I', fat_data[12:16])[0]
            print(f"FAT[2] (bitmap): {hex(fat2)} {'✓ EOC' if fat2 == 0xFFFFFFFF else f'✗ chain {fat2}'}")
            print(f"FAT[3] (upcase): {hex(fat3)} {'✓ EOC' if fat3 == 0xFFFFFFFF else f'✗ chain {fat3}'}")
        
        # Read root directory
        print(f"\n=== Root Directory ===")
        root_offset = heap_offset * bps + (root_cluster - 2) * cs
        root_dir = read_bytes(f, root_offset, 128)
        
        dentry_types = []
        for i in range(4):
            dtype = root_dir[i * 32]
            dentry_types.append(dtype)
            if dtype == 0x00:
                print(f"Entry {i}: EOD (0x00) ✓")
                break
            elif dtype == 0x81:
                print(f"Entry {i}: Allocation Bitmap (0x81) ✓")
            elif dtype == 0x82:
                print(f"Entry {i}: Upcase Table (0x82) ✓")
            elif dtype == 0x83:
                print(f"Entry {i}: Volume Label (0x83) ✓")
            elif dtype == 0x85:
                print(f"Entry {i}: File/Dir (0x85) ✓")
            else:
                print(f"Entry {i}: TYPE {hex(dtype)}")
        
        # Check for required metadata
        has_bitmap = 0x81 in dentry_types
        has_upcase = 0x82 in dentry_types
        print(f"Has Bitmap: {has_bitmap} {'✓' if has_bitmap else '✗ MISSING'}")
        print(f"Has Upcase: {has_upcase} {'✓' if has_upcase else '✗ MISSING'}")
        
        # Allocation bitmap check
        print(f"\n=== Allocation Bitmap ===")
        bitmap_cluster = 2  # Always cluster 2
        bitmap_offset = heap_offset * bps + (bitmap_cluster - 2) * cs
        bitmap_data = read_bytes(f, bitmap_offset, min(cs, 512))
        
        # Check bitmap allocation
        if len(bitmap_data) >= 1:
            first_byte = bitmap_data[0]
            # Bit 0 = cluster 2, Bit 1 = cluster 3, etc.
            # (clusters 0-1 are reserved and have no bitmap bits)
            bit_2 = (first_byte >> 0) & 1
            bit_3 = (first_byte >> 1) & 1
            
            if bit_2:
                print(f"✓ Cluster 2 (bitmap) marked as allocated")
            else:
                print(f"✗ Cluster 2 (bitmap) NOT marked as allocated")
            
            if bit_3:
                print(f"✓ Cluster 3 (upcase) marked as allocated")
            else:
                print(f"✗ Cluster 3+ marked as allocated")
            
            print(f"  Bitmap byte 0: {hex(first_byte)} (clusters 2-9: all bits={bit_2 and bit_3})")
        
        print(f"\n=== Summary ===")
        if boot_sig == 0xAA55 and fat0 == 0xFFFFFFF8 and fat1 == 0xFFFFFFFF and has_bitmap and has_upcase:
            print("✓ Image structure appears valid")
            return True
        else:
            print("✗ Image has structural issues")
            return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python validate_exfat.py <image.exfat>")
        sys.exit(1)
    
    success = validate_exfat(sys.argv[1])
    sys.exit(0 if success else 1)
