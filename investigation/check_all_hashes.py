#!/usr/bin/env python3
import struct

def _name_hash(enc_name_upper: bytes) -> int:
    """exFAT name hash"""
    h = 0
    for i in range(0, len(enc_name_upper), 2):
        char = struct.unpack('<H', enc_name_upper[i:i+2])[0]
        h = ((h << 15) | (h >> 1)) & 0xFFFF
        h = (h + char) & 0xFFFF
    return h

def _encode_name(name: str) -> bytes:
    return name.encode('utf-16-le')

def extract_sce_sys_files(fname):
    """Extract all files in sce_sys directory"""
    with open(fname, 'rb') as f:
        boot = f.read(512)
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        cluster_size = 32768
        
        # Find sce_sys cluster
        root_offset = heap_offset * 512 + (4 - 2) * cluster_size
        f.seek(root_offset)
        root_data = f.read(cluster_size * 2)
        
        sce_sys_cluster = None
        offset = 0
        while offset < len(root_data):
            entry = root_data[offset:offset+32]
            if entry[0] == 0x85:
                next_entry = root_data[offset+32:offset+64]
                if len(next_entry) >= 32 and next_entry[0] == 0xC0:
                    name_entry = root_data[offset+64:offset+96]
                    if len(name_entry) >= 32 and name_entry[0] == 0xC1:
                        name_data = name_entry[2:32]
                        name = name_data.decode('utf-16-le', errors='ignore').split('\x00')[0]
                        if 'sce_sys' in name:
                            sce_sys_cluster = struct.unpack('<I', next_entry[20:24])[0]
                            break
            offset += 32
        
        if sce_sys_cluster:
            sce_sys_offset = heap_offset * 512 + (sce_sys_cluster - 2) * cluster_size
            f.seek(sce_sys_offset)
            sce_sys_data = f.read(cluster_size * 4)
            
            files = []
            offset = 0
            while offset < len(sce_sys_data):
                entry = sce_sys_data[offset:offset+32]
                if entry[0] == 0x00:
                    break
                elif entry[0] == 0x85:
                    next_entry = sce_sys_data[offset+32:offset+64] if offset+64 <= len(sce_sys_data) else b''
                    if len(next_entry) >= 32 and next_entry[0] == 0xC0:
                        name_entry = sce_sys_data[offset+64:offset+96] if offset+96 <= len(sce_sys_data) else b''
                        if len(name_entry) >= 32 and name_entry[0] == 0xC1:
                            name_data = name_entry[2:32]
                            name = name_data.decode('utf-16-le', errors='ignore').split('\x00')[0]
                            
                            # Extract stored hash from Stream Extension
                            stored_hash = struct.unpack('<H', next_entry[4:6])[0]
                            
                            # Compute hash with uppercase
                            computed_hash_upper = _name_hash(_encode_name(name.upper()))
                            
                            # Compute hash with original case
                            computed_hash_orig = _name_hash(_encode_name(name))
                            
                            files.append({
                                'name': name,
                                'stored_hash': stored_hash,
                                'computed_upper': computed_hash_upper,
                                'computed_orig': computed_hash_orig
                            })
                offset += 32
            
            return files
    
    return []

print("=== GENERATED IMAGE ===")
gen_files = extract_sce_sys_files('test-official-match.exfat')
for f in gen_files[:10]:  # First 10 files
    match_upper = "✓" if f['stored_hash'] == f['computed_upper'] else "✗"
    match_orig = "✓" if f['stored_hash'] == f['computed_orig'] else "✗"
    print(f"{f['name']:20} stored={hex(f['stored_hash']):6} upper={hex(f['computed_upper']):6}{match_upper} orig={hex(f['computed_orig']):6}{match_orig}")

print("\n=== OFFICIAL IMAGE ===")
off_files = extract_sce_sys_files('PPSA17221-official.exfat')
for f in off_files[:10]:  # First 10 files
    match_upper = "✓" if f['stored_hash'] == f['computed_upper'] else "✗"
    match_orig = "✓" if f['stored_hash'] == f['computed_orig'] else "✗"
    print(f"{f['name']:20} stored={hex(f['stored_hash']):6} upper={hex(f['computed_upper']):6}{match_upper} orig={hex(f['computed_orig']):6}{match_orig}")
