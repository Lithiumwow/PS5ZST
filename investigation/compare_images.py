#!/usr/bin/env python3
"""
Compare two exFAT images to find differences.
"""
import struct
import sys
from pathlib import Path

def compare_images(official_path, python_path, show_details=True):
    """
    Compare official (working) vs Python (broken) exFAT images.
    """
    print(f"Comparing exFAT images:")
    print(f"  Official (working): {official_path}")
    print(f"  Python (broken):    {python_path}\n")
    
    with open(official_path, 'rb') as f_off:
        with open(python_path, 'rb') as f_py:
            # Compare boot sectors first (most critical)
            print("=" * 60)
            print("BOOT SECTOR COMPARISON (Sector 0)")
            print("=" * 60)
            
            boot_off = f_off.read(512)
            boot_py = f_py.read(512)
            
            if boot_off == boot_py:
                print("✓ Boot sectors are IDENTICAL\n")
            else:
                print("✗ Boot sectors DIFFER\n")
                
                # Show field-by-field comparison
                fields = [
                    ("JumpBoot (0-2)", 0, 3),
                    ("OEM Name (3-10)", 3, 11),
                    ("MustBeZero (11-63)", 11, 64),
                    ("PartitionOffset (64-71)", 64, 72),
                    ("VolumeLength (72-79)", 72, 80),
                    ("FatOffset (80-83)", 80, 84),
                    ("FatLength (84-87)", 84, 88),
                    ("HeapOffset (88-91)", 88, 92),
                    ("ClusterCount (92-95)", 92, 96),
                    ("RootCluster (96-99)", 96, 100),
                    ("VolumeSerial (100-103)", 100, 104),
                    ("FileSystemRev (104-105)", 104, 106),
                    ("VolumeFlags (106-107)", 106, 108),
                    ("BytesPerSectorShift (108)", 108, 109),
                    ("SectorsPerClusterShift (109)", 109, 110),
                    ("NumberOfFats (110)", 110, 111),
                    ("DriveSelect (111)", 111, 112),
                    ("PercentInUse (112)", 112, 113),
                    ("Reserved (113-119)", 113, 120),
                    ("BootCode (120-509)", 120, 510),
                    ("BootSignature (510-511)", 510, 512),
                ]
                
                for name, start, end in fields:
                    off_val = boot_off[start:end]
                    py_val = boot_py[start:end]
                    
                    if off_val == py_val:
                        print(f"  ✓ {name}: MATCH")
                    else:
                        print(f"  ✗ {name}: DIFFER")
                        print(f"      Official: {off_val.hex()}")
                        print(f"      Python:   {py_val.hex()}")
            
            # Compare VBR checksum sector
            print("\n" + "=" * 60)
            print("VBR CHECKSUM SECTOR (Sector 11)")
            print("=" * 60)
            
            f_off.seek(11 * 512)
            f_py.seek(11 * 512)
            
            csum_off = f_off.read(512)
            csum_py = f_py.read(512)
            
            csum_off_val = struct.unpack('<I', csum_off[0:4])[0]
            csum_py_val = struct.unpack('<I', csum_py[0:4])[0]
            
            print(f"Official checksum: {hex(csum_off_val)}")
            print(f"Python checksum:   {hex(csum_py_val)}")
            
            if csum_off == csum_py:
                print("✓ Checksum sectors are IDENTICAL\n")
            else:
                print("✗ Checksum sectors DIFFER\n")
            
            # Compare FAT table
            print("=" * 60)
            print("FAT TABLE (First 16 entries)")
            print("=" * 60)
            
            fat_off_sect = struct.unpack('<I', boot_off[80:84])[0]
            
            f_off.seek(fat_off_sect * 512)
            f_py.seek(fat_off_sect * 512)
            
            fat_off = f_off.read(64)
            fat_py = f_py.read(64)
            
            if fat_off == fat_py:
                print("✓ FAT entries are IDENTICAL\n")
            else:
                print("✗ FAT entries DIFFER\n")
                for i in range(16):
                    off_val = struct.unpack('<I', fat_off[i*4:(i+1)*4])[0]
                    py_val = struct.unpack('<I', fat_py[i*4:(i+1)*4])[0]
                    match = "✓" if off_val == py_val else "✗"
                    print(f"  {match} FAT[{i:2d}]: Official={hex(off_val):12s} Python={hex(py_val):12s}")
            
            # Compare root directory structure
            print("\n" + "=" * 60)
            print("ROOT DIRECTORY (First 512 bytes)")
            print("=" * 60)
            
            # Get root offset
            heap_off_sect = struct.unpack('<I', boot_off[88:92])[0]
            root_cluster = struct.unpack('<I', boot_off[96:100])[0]
            spc_shift = boot_off[109]
            spc = 1 << spc_shift
            
            root_byte_off = heap_off_sect * 512 + (root_cluster - 2) * (512 * spc)
            
            f_off.seek(root_byte_off)
            f_py.seek(root_byte_off)
            
            root_off = f_off.read(512)
            root_py = f_py.read(512)
            
            if root_off == root_py:
                print("✓ Root directory entries are IDENTICAL\n")
            else:
                print("✗ Root directory entries DIFFER\n")
                # Show first few entries
                for i in range(4):
                    e_off = root_off[i*32:(i+1)*32]
                    e_py = root_py[i*32:(i+1)*32]
                    
                    etype = e_off[0]
                    if etype == 0x00:
                        name = "EOD"
                    elif etype == 0x81:
                        name = "Bitmap"
                    elif etype == 0x82:
                        name = "Upcase"
                    elif etype == 0x83:
                        name = "Label"
                    elif etype == 0x85:
                        name = "File"
                    else:
                        name = f"Type {hex(etype)}"
                    
                    if e_off == e_py:
                        print(f"  ✓ Entry {i} ({name}): MATCH")
                    else:
                        print(f"  ✗ Entry {i} ({name}): DIFFER")
                        # Find first differing byte
                        for j in range(32):
                            if e_off[j] != e_py[j]:
                                print(f"      First diff @ byte {j}: Official={hex(e_off[j])} Python={hex(e_py[j])}")
                                print(f"      Full Official: {e_off.hex()}")
                                print(f"      Full Python:   {e_py.hex()}")
                                break

if __name__ == '__main__':
    official_path = 'PPSA17221-official.exfat'
    python_path = 'PPSA17221-diagnostic.exfat'
    
    if len(sys.argv) > 1:
        official_path = sys.argv[1]
    if len(sys.argv) > 2:
        python_path = sys.argv[2]
    
    compare_images(official_path, python_path)
