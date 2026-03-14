#!/usr/bin/env python3
"""Debug checksum calculation for param.json."""
import struct

def _dir_checksum(dentries: bytes, skip_bytes=None) -> int:
    """Checksum over directory entries (optionally skip specific bytes)."""
    if skip_bytes is None:
        skip_bytes = [2, 3]
    
    csum = 0
    for i, b in enumerate(dentries):
        if i in skip_bytes:
            continue
        csum = ((csum << 31) | (csum >> 1)) & 0xFFFFFFFF
        csum = (csum + b) & 0xFFFFFFFF
    return csum & 0xFFFF

# Read param.json entries from both images
def read_entry(img_path, location):
    with open(img_path, 'rb') as f:
        f.seek(location)
        return f.read(96)  # File entry + stream ext + name

# From our earlier findings:
# Official: offset 480 in sce_sys (cluster 53678), offset=768*512 + (53678-2)*64*512
# Generated: offset 576 in sce_sys (cluster 1734), offset=768*512 + (1734-2)*64*512

# Actually, let's use simpler calculation: sce_sys cluster directly
def get_param_entry_from_sce_sys(img_path, sce_sys_cluster):
    """Read param.json entry from sce_sys directory."""
    heap_offset = 768
    bps = 512
    spc = 64
    offset = (heap_offset + (sce_sys_cluster - 2) * spc) * bps
    
    with open(img_path, 'rb') as f:
        f.seek(offset)
        sce_sys_dir = f.read(32 * 1024)  # Read first 32KB of sce_sys
    
    # Find param.json (there's an offset from earlier test)
    # We know from earlier: Official at offset 480, Generated at offset 576
    # Let's search for it
    i = 0
    while i + 96 <= len(sce_sys_dir):
        entry = sce_sys_dir[i:i+32]
        if entry[0] == 0x85:  # File entry
            # Check if name is param.json by reading secondary
            se = sce_sys_dir[i+32:i+64]
            if se[0] == 0xc0:  # Stream extension
                # Read name
                name_bytes = b''
                sec_count = entry[1]
                for k in range(sec_count - 1):
                    name_entry = sce_sys_dir[i+64+k*32:i+64+k*32+32]
                    if name_entry[0] == 0xc1:
                        name_bytes += name_entry[2:32]
                
                name = name_bytes.decode('utf-16-le', errors='ignore').rstrip('\x00')
                if name == 'param.json':
                    return sce_sys_dir[i:i+96], i
            
            sec_count = entry[1]
            i += 32 * (sec_count + 1)
        else:
            i += 32
    return None, None

print("CHECKSUM ANALYSIS:")
print("=" * 80)

# Get entries
entry_o, offset_o = get_param_entry_from_sce_sys('PPSA17221-official.exfat', 53678)
entry_g, offset_g = get_param_entry_from_sce_sys('okaythiswillworkright.exfat', 1734)

if entry_o and entry_g:
    print(f"Official param.json at offset {offset_o} in sce_sys:")
    print(f"  Bytes 0-3: {entry_o[0:4].hex()} (type=0x{entry_o[0]:02x}, count={entry_o[1]}, checksum=0x{struct.unpack('<H', entry_o[2:4])[0]:04x})")
    
    # Extract file entry and secondaries
    fe_o = entry_o[0:32]
    all_sec_o = entry_o[32:96]
    
    # Compute checksum different ways
    print(f"\n  Testing checksum calculation methods:")
    
    # Method 1: Skip bytes 2-3 in full data (current implementation)
    c1_o = _dir_checksum(entry_o, skip_bytes=[2, 3])
    print(f"    Method 1 (skip 2-3 in full): 0x{c1_o:04x}")
    
    # Method 2: Skip bytes 2-3 in fe[4:] + secondaries
    c2_o = _dir_checksum(bytes(fe_o[4:]) + all_sec_o, skip_bytes=[])
    print(f"    Method 2 (fe[4:] + sec): 0x{c2_o:04x}")
    
    # Method 3: Skip bytes 2-3 but compute over fe + all_secondary
    fe_trimmed = bytes(fe_o[0:2]) + bytes(fe_o[4:32])
    c3_o = _dir_checksum(fe_trimmed + all_sec_o, skip_bytes=[])
    print(f"    Method 3 (fe[0:2]+fe[4:] + sec): 0x{c3_o:04x}")
    
    print(f"\n  Official stored checksum: 0x{struct.unpack('<H', entry_o[2:4])[0]:04x}")
    
    print(f"\nGenerated param.json at offset {offset_g} in sce_sys:")
    print(f"  Bytes 0-3: {entry_g[0:4].hex()} (type=0x{entry_g[0]:02x}, count={entry_g[1]}, checksum=0x{struct.unpack('<H', entry_g[2:4])[0]:04x})")
    
    fe_g = entry_g[0:32]
    all_sec_g = entry_g[32:96]
    
    c1_g = _dir_checksum(entry_g, skip_bytes=[2, 3])
    c2_g = _dir_checksum(bytes(fe_g[4:]) + all_sec_g, skip_bytes=[])
    c3_g = _dir_checksum(bytes(fe_g[0:2]) + bytes(fe_g[4:32]) + all_sec_g, skip_bytes=[])
    
    print(f"    Method 1 (skip 2-3 in full): 0x{c1_g:04x}")
    print(f"    Method 2 (fe[4:] + sec): 0x{c2_g:04x}")
    print(f"    Method 3 (fe[0:2]+fe[4:] + sec): 0x{c3_g:04x}")
    
    print(f"\n  Generated stored checksum: 0x{struct.unpack('<H', entry_g[2:4])[0]:04x}")
    
    # Extract stored checksum (repeated 128 times in sector 11)
    stored_csum = struct.unpack('<I', csum_sector[0:4])[0]
    
    # Compute VBR checksum (skip bytes 106-107)
    csum = 0
    for i, b in enumerate(vbr_data):
        if i in (106, 107):
            continue
        csum = ((csum << 31) | (csum >> 1)) & 0xFFFFFFFF
        csum = (csum + b) & 0xFFFFFFFF
    
    computed_csum = csum & 0xFFFFFFFF
    
    print(f"Stored checksum:   {hex(stored_csum)}")
    print(f"Computed checksum: {hex(computed_csum)}")
    print(f"Match: {stored_csum == computed_csum}")
    
    # Show what bytes 106-107 actually are
    print(f"\nBytes 106-107 (VolumeFlags) in boot sector: {vbr_data[106:108].hex()}")
    
    # Check extended boot sector signatures
    print(f"\nExtended boot sector end markers (@bytes 510-511):")
    for i in range(1, 9):
        offset = i * 512 + 510
        sig = struct.unpack('<H', vbr_data[offset:offset+2])[0]
        print(f"  Sector {i}: {hex(sig)}")
    
    # Check if the difference is consistent
    delta = (computed_csum - stored_csum) & 0xFFFFFFFF
    print(f"\nDelta (computed - stored): {hex(delta)}")
    
    # Try computing with different exclusion patterns
    print(f"\n=== Testing different exclusion patterns ===")
    
    # Attempt 1: No exclusion
    csum_no_skip = 0
    for b in vbr_data:
        csum_no_skip = ((csum_no_skip << 31) | (csum_no_skip >> 1)) & 0xFFFFFFFF
        csum_no_skip = (csum_no_skip + b) & 0xFFFFFFFF
    print(f"Checksum with NO skip: {hex(csum_no_skip & 0xFFFFFFFF)}")
    
    # Attempt 2: Just sector 0 skipped bytes
    csum_sector0_skip = 0
    for i, b in enumerate(vbr_data):
        if i in (106, 107):
            continue
        csum_sector0_skip = ((csum_sector0_skip << 31) | (csum_sector0_skip >> 1)) & 0xFFFFFFFF
        csum_sector0_skip = (csum_sector0_skip + b) & 0xFFFFFFFF
    print(f"Checksum with sector 0 skip (106-107): {hex(csum_sector0_skip & 0xFFFFFFFF)}")
    
    # Check if values are stored in little-endian but computed in big-endian or vice versa
    swapped = struct.pack('>I', stored_csum)
    print(f"\nStored checksum bytes: {csum_sector[0:4].hex()}")
    print(f"  As little-endian: {hex(stored_csum)}")
    print(f"  As big-endian: {hex(struct.unpack('<I', struct.pack('>I', stored_csum))[0])}")
