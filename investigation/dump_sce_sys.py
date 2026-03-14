import struct

def dump_directory(img_path, cluster, max_entries=50):
    with open(img_path, 'rb') as f:
        boot = f.read(512)
        bps_shift = boot[108]
        spc_shift = boot[109]
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        
        bps = 1 << bps_shift  # 512
        spc = 1 << spc_shift  # 64
        cluster_size = bps * spc  # 32KB
        
        offset = (heap_offset + (cluster - 2) * spc) * bps
        f.seek(offset)
        data = f.read(cluster_size)
        
        print(f"Dumping directory at cluster {cluster} (offset {offset:#x})")
        print(f"First 1024 bytes (hex):\n")
        
        for i in range(0, min(1024, len(data)), 32):
            entry = data[i:i+32]
            hex_str = ' '.join(f'{b:02x}' for b in entry)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in entry)
            print(f"{i:04d}: {hex_str}  {ascii_str}")

# Official image
print("=== OFFICIAL IMAGE ===")
dump_directory('PPSA17221-official.exfat', 53678)

print("\n" + "="*80)
print("=== GENERATED IMAGE ===")
dump_directory('okaythiswillworkright_v2.exfat', 1734)
