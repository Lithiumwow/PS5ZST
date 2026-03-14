#!/usr/bin/env python3
import struct
import sys

def compare_images(official, generated):
    print("="*80)
    print("COMPREHENSIVE EXFAT COMPARISON")
    print("="*80)
    
    with open(official, 'rb') as f_off, open(generated, 'rb') as f_gen:
        off_boot = f_off.read(512)
        gen_boot = f_gen.read(512)
        
        print("\n[1] BOOT SECTOR COMPARISON")
        print("-" * 80)
        
        checks = [
            ("Signature (0-2)", off_boot[0:3], gen_boot[0:3]),
            ("OEM Name (3-10)", off_boot[3:11], gen_boot[3:11]),
            ("Bytes per sector shift (109)", off_boot[109:110], gen_boot[109:110]),
            ("Sectors per cluster shift (108)", off_boot[108:109], gen_boot[108:109]),
            ("Number of FATs (105)", off_boot[105:106], gen_boot[105:106]),
            ("Drive select (106)", off_boot[106:107], gen_boot[106:107]),
            ("Media descriptor (107)", off_boot[107:108], gen_boot[107:108]),
            ("Reserved1 (6-7)", off_boot[6:8], gen_boot[6:8]),
            ("Boot sector backup (0x50)", struct.unpack('<I', off_boot[0x50:0x54])[0], struct.unpack('<I', gen_boot[0x50:0x54])[0]),
            ("FAT offset (80-83)", struct.unpack('<I', off_boot[80:84])[0], struct.unpack('<I', gen_boot[80:84])[0]),
            ("FAT length (84-87)", struct.unpack('<I', off_boot[84:88])[0], struct.unpack('<I', gen_boot[84:88])[0]),
            ("Heap offset (88-91)", struct.unpack('<I', off_boot[88:92])[0], struct.unpack('<I', gen_boot[88:92])[0]),
            ("Volume serial (108-111)", struct.unpack('<I', off_boot[108:112])[0], struct.unpack('<I', gen_boot[108:112])[0]),
            ("Filesystem revision (42-43)", struct.unpack('<H', off_boot[42:44])[0], struct.unpack('<H', gen_boot[42:44])[0]),
            ("Total sectors (48-55)", struct.unpack('<Q', off_boot[48:56])[0], struct.unpack('<Q', gen_boot[48:56])[0]),
            ("Root cluster (44-47)", struct.unpack('<I', off_boot[44:48])[0], struct.unpack('<I', gen_boot[44:48])[0]),
            ("FSInfo sector (56-59)", struct.unpack('<I', off_boot[56:60])[0], struct.unpack('<I', gen_boot[56:60])[0]),
            ("Backup boot sector (60-63)", struct.unpack('<I', off_boot[60:64])[0], struct.unpack('<I', gen_boot[60:64])[0]),
        ]
        
        all_match = True
        for name, off_val, gen_val in checks:
            if isinstance(off_val, bytes):
                match = off_val == gen_val
                print(f"  {name:40} {'✓' if match else '✗'}")
                if not match:
                    print(f"    Official:  {off_val.hex()}")
                    print(f"    Generated: {gen_val.hex()}")
                    all_match = False
            else:
                match = off_val == gen_val
                print(f"  {name:40} {'✓' if match else '✗'}")
                if not match:
                    print(f"    Official:  {off_val}")
                    print(f"    Generated: {gen_val}")
                    all_match = False
        
        print("\n[2] FAT STRUCTURE COMPARISON")
        print("-" * 80)
        
        off_fat_offset = struct.unpack('<I', off_boot[80:84])[0]
        gen_fat_offset = struct.unpack('<I', gen_boot[80:84])[0]
        
        f_off.seek(off_fat_offset * 512)
        off_fat = f_off.read(512)
        f_gen.seek(gen_fat_offset * 512)
        gen_fat = f_gen.read(512)
        
        print("  First 16 FAT entries comparison:")
        fat_match = True
        for i in range(16):
            off_entry = struct.unpack('<I', off_fat[i*4:(i+1)*4])[0]
            gen_entry = struct.unpack('<I', gen_fat[i*4:(i+1)*4])[0]
            match = off_entry == gen_entry
            
            print(f"    FAT[{i:2d}]: {hex(off_entry):12} vs {hex(gen_entry):12} {'✓' if match else '✗'}")
            if not match:
                fat_match = False
        
        print("\n[3] ROOT DIRECTORY COMPARISON")
        print("-" * 80)
        
        off_heap = struct.unpack('<I', off_boot[88:92])[0]
        gen_heap = struct.unpack('<I', gen_boot[88:92])[0]
        cluster_size = 32768
        
        # Read root directories
        f_off.seek(off_heap * 512 + (4 - 2) * cluster_size)
        off_root_data = f_off.read(256)  # First 256 bytes
        
        f_gen.seek(gen_heap * 512 + (4 - 2) * cluster_size)
        gen_root_data = f_gen.read(256)  # First 256 bytes
        
        print("  First 256 bytes of root directory:")
        print(f"    Official: {off_root_data[:16].hex()}...")
        print(f"    Generated: {gen_root_data[:16].hex()}...")
        
        # Count directory entries of each type
        def count_entries(data):
            counts = {'FILE': 0, 'DIR': 0, 'STREAM': 0, 'NAME': 0, 'VOL': 0}
            offset = 0
            while offset < len(data):
                et = data[offset]
                if et == 0x00:
                    break
                elif et == 0x85:
                    counts['FILE'] += 1
                elif et == 0x83:
                    counts['VOL'] += 1
                elif et == 0xC0:
                    counts['STREAM'] += 1
                elif et == 0xC1:
                    counts['NAME'] += 1
                offset += 32
            return counts
        
        off_counts = count_entries(off_root_data)
        gen_counts = count_entries(gen_root_data)
        
        print(f"\n  Entry type counts (first 256 bytes):")
        for etype in ['VOL', 'FILE', 'STREAM', 'NAME']:
            off_c = off_counts.get(etype, 0)
            gen_c = gen_counts.get(etype, 0)
            match = off_c == gen_c
            print(f"    {etype:6} Official: {off_c:3}  Generated: {gen_c:3}  {'✓' if match else '✗'}")
        
        print("\n[4] ALLOCATION BITMAP COMPARISON")
        print("-" * 80)
        
        f_off.seek(off_heap * 512 + (2 - 2) * cluster_size)
        off_bitmap = f_off.read(512)
        
        f_gen.seek(gen_heap * 512 + (2 - 2) * cluster_size)
        gen_bitmap = f_gen.read(512)
        
        print(f"  First 64 bytes of bitmap:")
        print(f"    Official:  {off_bitmap[:64].hex()}")
        print(f"    Generated: {gen_bitmap[:64].hex()}")
        print(f"    Match: {'✓' if off_bitmap[:64] == gen_bitmap[:64] else '✗'}")
        
        print("\n[5] KEY DIFFERENCES")
        print("-" * 80)
        
        # Known differences
        off_serial = struct.unpack('<I', off_boot[108:112])[0]
        gen_serial = struct.unpack('<I', gen_boot[108:112])[0]
        print(f"  Volume Serial: Official={hex(off_serial)}, Generated={hex(gen_serial)}")
        print(f"    (Difference expected: generated is timestamp-based)")
        
        print("\n" + "="*80)

if __name__ == '__main__':
    compare_images('PPSA17221-official.exfat', 'test-fat-system-fixed.exfat')
