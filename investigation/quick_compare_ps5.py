#!/usr/bin/env python3
import struct

official = 'PPSA17221-official.exfat'
generated = 'test-ps5-final.exfat'

with open(official, 'rb') as f, open(generated, 'rb') as g:
    off_boot = f.read(512)
    gen_boot = g.read(512)
    
    print("KEY GEOMETRY PARAMETERS:")
    print("-" * 60)
    
    params = [
        ("FAT offset", struct.unpack('<I', off_boot[80:84])[0], struct.unpack('<I', gen_boot[80:84])[0]),
        ("FAT length (sectors)", struct.unpack('<I', off_boot[84:88])[0], struct.unpack('<I', gen_boot[84:88])[0]),
        ("Heap offset", struct.unpack('<I', off_boot[88:92])[0], struct.unpack('<I', gen_boot[88:92])[0]),
        ("Total sectors", struct.unpack('<Q', off_boot[48:56])[0], struct.unpack('<Q', gen_boot[48:56])[0]),
        ("Root cluster", struct.unpack('<I', off_boot[44:48])[0], struct.unpack('<I', gen_boot[44:48])[0]),
        ("Filesystem revision", struct.unpack('<H', off_boot[42:44])[0], struct.unpack('<H', gen_boot[42:44])[0]),
        ("Bytes/sector shift", off_boot[109], gen_boot[109]),
        ("Sectors/cluster shift", off_boot[108], gen_boot[108]),
    ]
    
    all_match = True
    for name, off_val, gen_val in params:
        match = off_val == gen_val
        symbol = "✓" if match else "✗"
        print(f"{name:30} {symbol} Official: {off_val:10} Generated: {gen_val:10}")
        if not match:
            all_match = False
    
    print("\n" + "=" * 60)
    print("FAT ENTRIES:")
    print("-" * 60)
    
    f.seek(128 * 512)  # FAT starts at sector 128
    off_fat = f.read(64)
    
    g.seek(128 * 512)  # FAT starts at sector 128
    gen_fat = g.read(64)
    
    for i in range(4):
        off_entry = struct.unpack('<I', off_fat[i*4:(i+1)*4])[0]
        gen_entry = struct.unpack('<I', gen_fat[i*4:(i+1)*4])[0]
        match = off_entry == gen_entry
        symbol = "✓" if match else "✗"
        print(f"FAT[{i}] {symbol} Official: {hex(off_entry):12} Generated: {hex(gen_entry):12}")
        if not match:
            all_match = False
    
    print("\n" + "=" * 60)
    if all_match:
        print("✓✓✓ PERFECT MATCH - Ready for PS5! ✓✓✓")
    else:
        print("✗ Differences found - see above")
