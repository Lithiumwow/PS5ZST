#!/usr/bin/env python3
"""Find and compare param.json in both images."""
import struct

def find_file_in_image(img_path, filename, root_cluster=4, heap_offset=768, bps_shift=9, spc_shift=6):
    """Find a file in the directory tree and return its data."""
    bps = 1 << bps_shift
    spc = 1 << spc_shift
    cluster_size = bps * spc
    
    def read_directory(cluster_num):
        offset = (heap_offset + (cluster_num - 2) * spc) * bps
        with open(img_path, 'rb') as f:
            f.seek(offset)
            return f.read(cluster_size)
    
    def parse_dir(cluster_num, path=''):
        dir_data = read_directory(cluster_num)
        entries = []
        i = 0
        while i + 32 <= len(dir_data):
            entry = dir_data[i:i+32]
            type_code = entry[0]
            
            if not type_code:
                break
            
            if type_code < 0x81:
                i += 32
                continue
            
            if type_code == 0x85:
                se_count = entry[1]
                attr = struct.unpack('<H', entry[4:6])[0]
                is_dir = bool(attr & 0x10)
                
                if i + 32 < len(dir_data):
                    stream_ext = dir_data[i+32:i+64]
                    if stream_ext[0] == 0xC0:
                        data_size = struct.unpack('<Q', stream_ext[8:16])[0]
                        first_cluster = struct.unpack('<I', stream_ext[20:24])[0]
                        
                        name_bytes = b''
                        for k in range(se_count - 1):
                            name_offset = i + 64 + k * 32
                            if name_offset + 32 <= len(dir_data):
                                name_entry = dir_data[name_offset:name_offset+32]
                                if name_entry[0] == 0xC1:
                                    name_bytes += name_entry[2:32]
                        
                        name = name_bytes.decode('utf-16-le', errors='ignore').rstrip('\x00')
                        full_path = path + '/' + name if path else name
                        
                        if name == filename:
                            return ('found', first_cluster, data_size)
                        
                        if is_dir and name not in ['.', '..']:
                            result = parse_dir(first_cluster, full_path)
                            if result and result[0] == 'found':
                                return result
                
                i += 32 * (se_count + 1)
            else:
                i += 32
        
        return None
    
    return parse_dir(root_cluster)

print("LOOKING FOR param.json...")
print("=" * 70)

# Find in official
result_o = find_file_in_image('PPSA17221-official.exfat', 'param.json')
if result_o and result_o[0] == 'found':
    _, cluster_o, size_o = result_o
    print(f"Official: Cluster {cluster_o}, Size {size_o} bytes")
else:
    print("Official: NOT FOUND")

# Find in fixed
result_g = find_file_in_image('test-ps5-fixed.exfat', 'param.json')
if result_g and result_g[0] == 'found':
    _, cluster_g, size_g = result_g
    print(f"Fixed:    Cluster {cluster_g}, Size {size_g} bytes")
else:
    print("Fixed:    NOT FOUND")

if result_o and result_g and result_o[0] == 'found' and result_g[0] == 'found':
    _, cluster_o, size_o = result_o
    _, cluster_g, size_g = result_g
    
    print(f"\nCluster match: {cluster_o == cluster_g}")
    print(f"Size match: {size_o == size_g}")
