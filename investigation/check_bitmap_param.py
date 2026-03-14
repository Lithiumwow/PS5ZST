#!/usr/bin/env python3
import struct

def check_bitmap_for_file_clusters(fname, file_cluster, file_size):
    """Check if clusters for a file are marked as allocated in bitmap"""
    print(f"\nChecking bitmap for file at cluster {file_cluster}, size {file_size}...")
    
    with open(fname, 'rb') as f:
        boot = f.read(512)
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        spc_shift = boot[109]
        cluster_size = (1 << spc_shift) * 512
        
        # Allocation bitmap is at cluster 2
        bitmap_offset = heap_offset * 512 + (2 - 2) * cluster_size
        f.seek(bitmap_offset)
        bitmap_data = f.read(cluster_size)
        
        # Calculate which clusters this file needs
        num_clusters = (file_size + cluster_size - 1) // cluster_size
        print(f"  File needs {num_clusters} clusters")
        
        for i in range(num_clusters):
            cluster_num = file_cluster + i
            # Convert cluster number to byte offset in bitmap
            byte_offset = cluster_num // 8
            bit_offset = cluster_num % 8
            
            if byte_offset < len(bitmap_data):
                byte_val = bitmap_data[byte_offset]
                is_set = bool(byte_val & (1 << bit_offset))
                print(f"    Cluster {cluster_num}: byte[{byte_offset}] bit {bit_offset} = {is_set} {'✓' if is_set else '✗ NOT ALLOCATED'}")
            else:
                print(f"    Cluster {cluster_num}: OUT OF BOUNDS (byte {byte_offset} >= {len(bitmap_data)})")

print("=== GENERATED IMAGE ===")
check_bitmap_for_file_clusters('test-original-case.exfat', 53705, 3439)

print("\n=== OFFICIAL IMAGE ===")
check_bitmap_for_file_clusters('PPSA17221-official.exfat', 53702, 3439)
