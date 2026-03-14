#!/usr/bin/env python3
import struct

def check_fat_entry(fname, cluster):
    """Check FAT entry for a cluster"""
    with open(fname, 'rb') as f:
        boot = f.read(512)
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        fat_offset = struct.unpack('<I', boot[80:84])[0]
        
        # FAT is in sectors, starting at fat_offset
        fat_byte_offset = fat_offset * 512 + cluster * 4
        f.seek(fat_byte_offset)
        entry = struct.unpack('<I', f.read(4))[0]
        
        return hex(entry)

print("=== GENERATED IMAGE ===")
param_cluster_gen = 53705
print(f"param.json cluster {param_cluster_gen}:")
print(f"  FAT entry: {check_fat_entry('test-original-case.exfat', param_cluster_gen)}")

print("\n=== OFFICIAL IMAGE ===")
param_cluster_off = 53702
print(f"param.json cluster {param_cluster_off}:")
print(f"  FAT entry: {check_fat_entry('PPSA17221-official.exfat', param_cluster_off)}")

print("\nIn exFAT:")
print("  0xFFFFFFFE = bad cluster")
print("  0xFFFFFFFF = end of chain / last allocated cluster")
