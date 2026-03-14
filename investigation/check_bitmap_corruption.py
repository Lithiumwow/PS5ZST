#!/usr/bin/env python3
"""Check if allocation bitmap matches actual file allocation."""

import struct
import math

def analyze_allocation_bitmap(img_path, label):
    print(f"\n{'='*70}")
    print(f"ALLOCATION BITMAP ANALYSIS: {label}")
    print('='*70)
    
    with open(img_path, 'rb') as f:
        boot = f.read(512)
        
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        root_cluster = struct.unpack('<I', boot[96:100])[0]
        bps_shift = boot[108]
        spc_shift = boot[109]
        
        bps = 1 << bps_shift  # 512
        spc = 1 << spc_shift  # 64
        cluster_size = bps * spc
        
        # Read root directory to find allocation bitmap
        root_offset = (heap_offset + (root_cluster - 2) * spc) * bps
        f.seek(root_offset)
        root_data = f.read(spc * bps)
        
        # Find ALLOC_BITMAP entry (type 0x81)
        bitmap_cluster = None
        bitmap_size = None
        
        i = 0
        while i < len(root_data) and root_data[i] != 0:
            if root_data[i] == 0x81:  # Allocation bitmap
                if i + 32 < len(root_data):
                    se = root_data[i+32:i+64]
                    bitmap_size = struct.unpack('<Q', se[8:16])[0]
                    bitmap_cluster = struct.unpack('<I', se[20:24])[0]
                    print(f"[Found Bitmap]")
                    print(f"  Cluster: {bitmap_cluster}")
                    print(f"  Size: {bitmap_size} bytes = {bitmap_size * 8} bits")
                print(f"\nBitmap Content (first 512 bytes):")
                print(f"  Cluster offset: {bitmap_cluster}")
                
                # Read bitmap data
                bitmap_offset = (heap_offset + (bitmap_cluster - 2) * spc) * bps
                f.seek(bitmap_offset)
                bitmap_data = f.read(512)
                
                # Analyze bitmap
                total_data_clusters = 65524
                bytes_needed = math.ceil(total_data_clusters / 8)
                print(f"  Total data clusters: {total_data_clusters}")
                print(f"  Bytes needed for bitmap: {bytes_needed}")
                
                # Count set bits
                set_bits = sum(bin(b).count('1') for b in bitmap_data)
                print(f"\n[Bitmap Statistics]")
                print(f"  Bits set (clusters marked as used): {set_bits}")
                print(f"  Bits clear (clusters free): {total_data_clusters - set_bits}")
                
                # Show first 16 bytes in hex
                print(f"\n[First 16 Bytes in Hex]")
                hex_str = ' '.join(f'{b:02x}' for b in bitmap_data[:16])
                print(f"  {hex_str}")
                
                # Check specific clusters we know about
                # Cluster 2 (bitmap): bit 0
                # Cluster 3 (upcase): bit 1  
                # Cluster 4 (root): bit 2
                print(f"\n[System Clusters Status]")
                for cluster_num in [2, 3, 4]:
                    byte_idx = cluster_num // 8
                    bit_idx = cluster_num % 8
                    if byte_idx < len(bitmap_data):
                        bit_val = (bitmap_data[byte_idx] >> bit_idx) & 1
                        print(f"  Cluster {cluster_num}: {'SET ✓' if bit_val else 'CLEAR ✗'}")
                
                # Check if bitmap itself appears reasonable
                # Should have mostly 1s at start (used clusters) then 0s
                first_half = bitmap_data[:256]
                second_half = bitmap_data[256:512]
                
                ones_first = sum(bin(b).count('1') for b in first_half)
                ones_second = sum(bin(b).count('1') for b in second_half)
                
                print(f"\n[Bitmap Distribution]")
                print(f"  First 256 bytes (bits 0-2047): {ones_first} bits set")
                print(f"  Second 256 bytes (bits 2048-4095): {ones_second} bits set")
                
                if ones_first > 4000:
                    print(f"  ⚠ WARNING: First half has suspiciously many 1s (should be ~1700)")
                if ones_second < 100:
                    print(f"  ✓ Good: Second half is mostly clear (free clusters)")
                
                break
            
            i += 32
        
        if not bitmap_cluster:
            print("ERROR: Could not find allocation bitmap in root directory!")

# Compare
analyze_allocation_bitmap('PPSA17221-official.exfat', 'OFFICIAL')
analyze_allocation_bitmap('fixed_contiguous.exfat', 'FIXED')
