#!/usr/bin/env python3
"""Compare sce_sys directory entries."""
import struct

def get_sce_sys_info(img_path):
    with open(img_path, 'rb') as f:
        # Get geometry from boot sector
        boot = f.read(512)
        bps_shift = boot[108]
        spc_shift = boot[109]
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        
        bps = 1 << bps_shift
        spc = 1 << spc_shift
        
        # Root is always at cluster 4
        root_offset = (heap_offset + (4 - 2) * spc) * bps
        f.seek(root_offset)
        root_data = f.read(spc * bps)  # Read entire root cluster
    
    i = 0
    while i < len(root_data):
        entry = root_data[i:i+32]
        if not entry[0]:
            break
        if entry[0] == 0x85:
            se = root_data[i+32:i+64] if i+32 < len(root_data) else None
            if se and se[0] == 0xc0:
                name_bytes = b''
                sec_count = entry[1]
                for k in range(sec_count - 1):
                    name_offset = i + 64 + k * 32
                    if name_offset + 32 <= len(root_data):
                        name_entry = root_data[name_offset:name_offset+32]
                        if name_entry[0:1] == b'\xc1':
                            name_bytes += name_entry[2:32]
                
                name = name_bytes.decode('utf-16-le', errors='ignore').rstrip('\x00')
                if name == 'sce_sys':
                    size = struct.unpack('<Q', se[8:16])[0]
                    cluster = struct.unpack('<I', se[20:24])[0]
                    flags = se[1]
                    return {
                        'size': size,
                        'cluster': cluster,
                        'flags': flags,
                        'nofatchain': bool(flags & 0x02),
                        'entry_hex': entry.hex(),
                        'stream_hex': se.hex()
                    }
            i += 32 * (entry[1] + 1)
        else:
            i += 32
    
    return None

o = get_sce_sys_info('PPSA17221-official.exfat')
g = get_sce_sys_info('okaythiswillworkright_v2.exfat')

print('Official sce_sys:')
if o:
    for k, v in o.items():
        print(f'  {k}: {v}')
else:
    print('  NOT FOUND')

print()
print('Generated sce_sys:')
if g:
    for k, v in g.items():
        print(f'  {k}: {v}')
else:
    print('  NOT FOUND')

if o and g:
    print()
    print('COMPARISON:')
    size_match = 'MATCH' if o['size'] == g['size'] else 'DIFFER'
    flags_match = 'MATCH' if o['flags'] == g['flags'] else 'DIFFER'
    nofat_match = 'MATCH' if o['nofatchain'] == g['nofatchain'] else 'DIFFER'
    
    print(f"Size: {o['size']} vs {g['size']} - {size_match}")
    print(f"Flags: 0x{o['flags']:02x} vs 0x{g['flags']:02x} - {flags_match}")
    print(f"NoFatChain: {o['nofatchain']} vs {g['nofatchain']} - {nofat_match}")
    print(f"Cluster: {o['cluster']} vs {g['cluster']}")
