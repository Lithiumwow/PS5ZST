#!/usr/bin/env python3
"""Identify which files correspond to missing FAT entries."""
import struct
import os

def get_fat_entry(img_path, entry_num):
    with open(img_path, 'rb') as f:
        f.seek(128 * 512 + entry_num * 4)  # FAT starts at sector 128
        return struct.unpack('<I', f.read(4))[0]

def find_inode_at_cluster(cluster, root_path='PPSA17221-app'):
    """Find files in directory structure that use given cluster."""
    results = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Scan all files in this directory
        for fname in filenames:
            full_path = os.path.join(dirpath, fname)
            results.append(full_path)
    return results

# Bad FAT entries from comparison
bad_entries = [
    (9430, 0x000025ca),
    (9674, 0x000026c4),
    (9924, 0x000027b9),
    (10169, 0xffffffff),
    (13609, 0x0000361c),
    (13852, 0x00003701),
    (14081, 0x000037fa),
    (14330, 0x000038e8),
    (14568, 0x000039ba),
    (14778, 0xffffffff),
    (16177, 0x0000401f),
    (16415, 0xffffffff),
    (16987, 0x0000439b),
    (17307, 0x000044ef),
    (17647, 0xffffffff),
    (23903, 0x00006f9f),
    (28575, 0xffffffff),
    (35466, 0x00008b94),
    (35732, 0x00008ca4),
    (36004, 0xffffffff),
]

print("BAD FAT ENTRIES (should have values, showing 0x00000000):")
print("=" * 70)

# Pattern analysis
clusters_with_end_markers = []
clusters_with_data_ptrs = []

for entry_num, expected_val in bad_entries:
    if expected_val == 0xffffffff:
        clusters_with_end_markers.append(entry_num)
    else:
        clusters_with_data_ptrs.append(entry_num)
    
    # Get what's currently in generated
    gen_val = get_fat_entry('test-ps5-final.exfat', entry_num)
    print(f"FAT[{entry_num}: Cluster {entry_num}]")
    print(f"  Expected (Official): 0x{expected_val:08x}")
    print(f"  Actual (Generated):  0x{gen_val:08x}")
    if expected_val == 0xffffffff:
        print(f"  Type: END-OF-CHAIN marker")
    else:
        print(f"  Type: Data pointer (points to cluster {expected_val})")
    print()

print(f"\nSUMMARY:")
print(f"  {len(clusters_with_end_markers)} end-of-chain markers missing")
print(f"  {len(clusters_with_data_ptrs)} data pointers missing")
print(f"  Total: {len(bad_entries)} bad FAT entries")

# Cluster range analysis
all_clusters = [e[0] for e in bad_entries]
print(f"\nCluster range: {min(all_clusters)} to {max(all_clusters)}")
print(f"Span: {max(all_clusters) - min(all_clusters)} clusters")

# Check if there's a pattern - are these in specific file regions?
print(f"\nClusters with missing pointers: {clusters_with_data_ptrs[:5]}...")
print(f"Clusters with missing end markers: {clusters_with_end_markers[:5]}...")
