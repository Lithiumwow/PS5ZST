#!/usr/bin/env python3
import struct

exfat = 'test-official-match.exfat'

with open(exfat, 'rb') as f:
    boot = f.read(512)
    heap_offset = struct.unpack('<I', boot[88:92])[0]
    spc_shift = boot[109]
    cluster_size = (1 << spc_shift) * 512
    
    # Read root directory
    root_offset = heap_offset * 512 + (4 - 2) * cluster_size
    print(f'heap_offset={hex(heap_offset)} spc_shift={spc_shift} cluster_size={cluster_size}')
    print(f'Root directory at offset {hex(root_offset)}, clusters 4-5\n')
    
    f.seek(root_offset)
    root_data = f.read(cluster_size * 2)
    
    print('Root directory entries:')
    offset = 0
    entry_num = 0
    while offset < len(root_data) and entry_num < 50:
        entry = root_data[offset:offset+32]
        entry_type = entry[0]
        
        if entry_type == 0x00:
            print(f'[{entry_num}] EOD')
            break
        elif entry_type == 0x81:
            print(f'[{entry_num}] FILE entry (type={hex(entry_type)})')
        elif entry_type == 0x85:
            print(f'[{entry_num}] DIR entry (type={hex(entry_type)})')
        elif entry_type == 0xc0:
            stream = struct.unpack('>I', entry[20:24])[0]
            size = struct.unpack('<Q', entry[24:32])[0]
            print(f'[{entry_num}] Stream Extension: cluster={stream}, size={size}')
        elif entry_type == 0xc1:
            name_data = entry[2:32]
            try:
                name = name_data.decode('utf-16-le', errors='ignore').split('\x00')[0]
                print(f'[{entry_num}] Name: "{name}"')
            except:
                print(f'[{entry_num}] Name entry (decode error)')
        else:
            print(f'[{entry_num}] UNKNOWN type={hex(entry_type)} / data={entry.hex()}')
        
        offset += 32
        entry_num += 1
