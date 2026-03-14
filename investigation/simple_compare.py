#!/usr/bin/env python3
import struct

official = 'PPSA17221-official.exfat'
python_v = 'PPSA17221-updated.exfat'

def read_boot(path):
    with open(path, 'rb') as f:
        boot = f.read(512)
    
    spc_shift = boot[109]  # SectorsPerClusterShift
    spc = 1 << spc_shift
    sector_size = 512
    cluster_size = spc * sector_size
    
    fat_offset = struct.unpack('<I', boot[80:84])[0]  
    fat_len = struct.unpack('<I', boot[84:88])[0]
    heap_offset = struct.unpack('<I', boot[88:92])[0]
    total_clusters = struct.unpack('<I', boot[92:96])[0]
    root_cluster = struct.unpack('<I', boot[96:100])[0]
    
    return {
        'spc_shift': spc_shift,
        'spc': spc,
        'cluster_size': cluster_size,
        'fat_offset': fat_offset,
        'fat_len': fat_len,
        'heap_offset': heap_offset,
        'total_clusters': total_clusters,
        'root_cluster': root_cluster,
    }

off = read_boot(official)
py = read_boot(python_v)

print("COMPARISON: Official vs Python")
print("=" * 70)
for key in off:
    match = "✓" if off[key] == py[key] else "✗"
    print(f"{key:20} | Official: {off[key]:10} | Python: {py[key]:10} | {match}")
print("=" * 70)

# Calculate what clusters are used 
print("\nCluster layout analysis:")
print(f"  Official: bitmap(2) + upcase(3..{off['root_cluster']-1}) + root({off['root_cluster']}+)")
print(f"    → {off['root_cluster'] - 2} reserved clusters before root")
print(f"\n  Python: bitmap(2) + upcase(3..{py['root_cluster']-1}) + root({py['root_cluster']}+)")
print(f"    → {py['root_cluster'] - 2} reserved clusters before root")
