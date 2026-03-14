#!/usr/bin/env python3
"""Check if bad FAT entries are actually supposed to be 0x0."""
import struct

bad_entries = [9430, 9674, 9924, 10169, 13609, 13852, 14081, 14330, 14568, 14778, 16177, 16415, 16987, 17307, 17647, 23903, 28575, 35466, 35732, 36004]

print("CHECKING FAT ENTRIES IN BOTH IMAGES:")
print("=" * 70)

with open('PPSA17221-official.exfat', 'rb') as f_official, \
     open('test-ps5-final.exfat', 'rb') as f_gen:
    
    for entry_num in bad_entries[:10]:  # First 10
        # Read from official 
        f_official.seek(128 * 512 + entry_num * 4)
        official_val = struct.unpack('<I', f_official.read(4))[0]
        
        # Read from generated
        f_gen.seek(128 * 512 + entry_num * 4)
        gen_val = struct.unpack('<I', f_gen.read(4))[0]
        
        # Check clusters before and after for pattern
        f_official.seek(128 * 512 + (entry_num-1) * 4)
        before_o = struct.unpack('<I', f_official.read(4))[0]
        f_official.seek(128 * 512 + (entry_num+1) * 4)
        after_o = struct.unpack('<I', f_official.read(4))[0]
        
        f_gen.seek(128 * 512 + (entry_num-1) * 4)
        before_g = struct.unpack('<I', f_gen.read(4))[0]
        f_gen.seek(128 * 512 + (entry_num+1) * 4)
        after_g = struct.unpack('<I', f_gen.read(4))[0]
        
        print(f"\nFAT[{entry_num}]:")
        print(f"  Before (official): 0x{before_o:08x}")
        print(f"  Current Official : 0x{official_val:08x}")
        print(f"  Current Generated: 0x{gen_val:08x}")
        print(f"  After (official) : 0x{after_o:08x}")
        
        if official_val != 0x0:
            print(f"  ^^ UNEXPECTED! Official has non-zero value!")
        if gen_val != 0x0:
            print(f"  ^^ ERROR! Generated has non-zero value!")

print("\n\n" + "=" * 70)
print("CONCLUSION: If all official values are 0x0, then 0x0 is CORRECT for NoFatChain files")
