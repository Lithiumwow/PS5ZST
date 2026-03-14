#!/usr/bin/env python3
"""Check FAT region integrity"""
import struct

def check_fat_integrity(fname):
    print(f"\n{fname}:")
    print("-" * 60)
    with open(fname, 'rb') as f:
        boot = f.read(512)
        fat_offset = struct.unpack('<I', boot[80:84])[0]
        fat_length = struct.unpack('<I', boot[84:88])[0]
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        total_sectors = struct.unpack('<Q', boot[48:56])[0]
        
        print(f"FAT offset:     {fat_offset} sectors")
        print(f"FAT length:     {fat_length} sectors")
        print(f"Heap offset:    {heap_offset} sectors")
        print(f"Total sectors:  {total_sectors}")
        print(f"FAT ends at:    {fat_offset + fat_length} sectors")
        
        # Check if FAT region fits
        if fat_offset + fat_length > heap_offset:
            print(f"✗ ERROR: FAT extends past heap! ({fat_offset} + {fat_length} = {fat_offset + fat_length} > {heap_offset})")
        else:
            print(f"✓ FAT region fits before heap")
        
        # Read FAT and check structure
        f.seek(fat_offset * 512)
        fat_data = f.read(min(4096, fat_length * 512))
        
        print(f"\nFAT region size: {len(fat_data)} bytes")
        print(f"First 32 FAT entries:")
        
        valid_entries = 0
        for i in range(32):
            if i * 4 >= len(fat_data):
                break
            entry = struct.unpack('<I', fat_data[i*4:(i+1)*4])[0]
            print(f"  FAT[{i}] = {hex(entry)}")
            if entry in [0x0, 0xFFFFFFFF, 0xFFFFFFF8]:
                valid_entries += 1
        
        print(f"\nValid reserved entries: {valid_entries}/5")

check_fat_integrity('PPSA17221-official.exfat')
check_fat_integrity('test-ps5-final.exfat')
check_fat_integrity('test-fixed-fat.exfat')
