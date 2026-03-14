import struct

def find_sce_sys_cluster(img_path):
    """Find sce_sys cluster number from root directory."""
    with open(img_path, 'rb') as f:
        boot = f.read(512)
        root_cluster = struct.unpack('<I', boot[96:100])[0]
        bps_shift = boot[108]
        spc_shift = boot[109]
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        
        bps = 1 << bps_shift
        spc = 1 << spc_shift
        
        # Read root directory
        root_offset = (heap_offset + (root_cluster - 2) * spc) * bps
        f.seek(root_offset)
        root_data = f.read(spc * bps)
        
        # Find sce_sys
        i = 0
        while i < len(root_data) and root_data[i] != 0:
            if root_data[i] == 0x85:  # File/dir entry
                se = root_data[i+32:i+64]
                if se[0] == 0xc0:  # File data entry
                    sce_sys_cluster = struct.unpack('<I', se[20:24])[0]
                    name_bytes = b''
                    se_count = root_data[i+1]
                    for k in range(se_count - 1):
                        ne_off = i + 64 + k * 32
                        if ne_off + 32 <= len(root_data):
                            ne = root_data[ne_off:ne_off+32]
                            if ne[0] == 0xc1:
                                name_bytes += ne[2:32]
                    
                    name = name_bytes.decode('utf-16-le', errors='ignore').rstrip('\x00')
                    if name == 'sce_sys':
                        return sce_sys_cluster
                
                i += 32 * (root_data[i+1] + 1)
            else:
                i += 32
    
    return None

def dump_flags(img_path, cluster, label):
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
        
        print(f"\n{label} - sce_sys directory flags:\n")
        print(f"{'File':<30} {'Flags':<10} {'Size':<12}")
        print("-" * 52)
        
        i = 0
        while i < len(data) and data[i] != 0:  # Stop at end marker
            entry = data[i:i+32]
            
            if entry[0] == 0x85:  # File/dir entry
                se_count = entry[1]
                # Read secondary entry to get flags
                if i + 32 < len(data):
                    se = data[i+32:i+64]
                    if se[0] == 0xc0:  # File data entry
                        flags = se[1]
                        size = struct.unpack('<Q', se[8:16])[0]
                        
                        # Read name from next secondary entries
                        name_bytes = b''
                        for k in range(se_count - 1):
                            ne_off = i + 64 + k * 32
                            if ne_off + 32 <= len(data):
                                ne = data[ne_off:ne_off+32]
                                if ne[0] == 0xc1:
                                    name_bytes += ne[2:32]
                        
                        try:
                            name = name_bytes.decode('utf-16-le', errors='ignore').rstrip('\x00')
                        except:
                            name = "???"
                        
                        flags_str = f"0x{flags:02x}"
                        if flags & 0x01:
                            flags_str += " (ALLOC"
                        if flags & 0x02:
                            flags_str += "|NOFATCHAIN"
                        if flags & 0x01:
                            flags_str += ")"
                        
                        print(f"{name:<30} {flags_str:<10} {size:>11}")
                
                # Skip all entries for this file/dir
                i += 32 * (se_count + 1)
            else:
                i += 32

# Compare
print("=" * 52)
dump_flags('PPSA17221-official.exfat', 53678, "OFFICIAL")

# Find and dump fixed version
sce_sys_cluster = find_sce_sys_cluster('fixed_contiguous.exfat')
if sce_sys_cluster:
    print(f"\nFound sce_sys at cluster {sce_sys_cluster}")
    dump_flags('fixed_contiguous.exfat', sce_sys_cluster, "FIXED")
else:
    print("ERROR: Could not find sce_sys cluster in fixed image")
