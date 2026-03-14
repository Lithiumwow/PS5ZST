#!/usr/bin/env python3
"""
Deep exFAT validation - checks every critical field and structure.
"""

import struct
import sys
from pathlib import Path

def validate_deep(image_path):
    """Run comprehensive exFAT validation against PS5 expectations."""
    print(f"Deep validation of: {image_path}\n")
    
    with open(image_path, 'rb') as f:
        # Read both boot sectors
        boot_main = f.read(512)
        boot_backup = f.read(512 * 11)  # Skip to backup
        f.seek(12 * 512)
        boot_backup_read = f.read(512)
        
        boot = boot_main
        
        print("=== BOOT SECTOR ===")
        print(f"Signature (0-2): {boot[0:3].hex()} {'✓' if boot[0:3] == b'\\xEB\\x76\\x90' else '✗'}")
        print(f"OEM (3-10): {boot[3:11]} {'✓' if boot[3:11] == b'EXFAT   ' else '✗'}")
        print(f"MustBeZero (11-63): {boot[11:64].count(0)}/53 bytes zero {'✓' if boot[11:64].count(0) == 53 else '✗'}")
        
        part_offset = struct.unpack('<Q', boot[64:72])[0]
        vol_len = struct.unpack('<Q', boot[72:80])[0]
        fat_offset = struct.unpack('<I', boot[80:84])[0]
        fat_len = struct.unpack('<I', boot[84:88])[0]
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        cluster_count = struct.unpack('<I', boot[92:96])[0]
        root_cluster = struct.unpack('<I', boot[96:100])[0]
        vol_sn = struct.unpack('<I', boot[100:104])[0]
        fs_rev = struct.unpack('<HB', boot[104:107])
        vol_flags = struct.unpack('<H', boot[106:108])[0]
        bps_shift = boot[108]
        spc_shift = boot[109]
        num_fats = boot[110]
        drive_select = boot[111]
        percent_in_use = boot[112]
        
        bps = 1 << bps_shift
        spc = 1 << spc_shift
        cs = bps * spc
        
        print(f"\nPartitionOffset: {part_offset} {'✓ (must be 0)' if part_offset == 0 else '✗'}")
        print(f"VolumeLength: {vol_len} sectors ({vol_len * 512 / (1<<30):.2f} GB)")
        print(f"FatOffset: {fat_offset} {'✓ (24)' if fat_offset == 24 else '? (expected 24)'}")
        print(f"FatLength: {fat_len} sectors")
        print(f"HeapOffset: {heap_offset} sectors")
        print(f"ClusterCount: {cluster_count}")
        print(f"RootDirectoryCluster: {root_cluster}")
        print(f"VolumeSerialNumber: {hex(vol_sn)}")
        print(f"FileSystemRevision: {fs_rev}")
        print(f"VolumeFlags: {hex(vol_flags)} {'✓ (0)' if vol_flags == 0 else '✗'}")
        print(f"BytesPerSectorShift: {bps_shift} → {bps} bytes ✓")
        print(f"SectorsPerClusterShift: {spc_shift} → {spc} sectors → {cs} bytes")
        print(f"NumberOfFats: {num_fats} {'✓ (must be 1)' if num_fats == 1 else '✗'}")
        print(f"DriveSelect: {hex(drive_select)} {'✓ (0x80)' if drive_select == 0x80 else '?'}")
        print(f"PercentInUse: {hex(percent_in_use)}")
        
        # Bytes 113-119
        reserved1 = boot[113:120]
        print(f"Reserved1 (113-119): {reserved1.count(0)}/7 bytes zero {'✓' if reserved1 == b'\\x00'*7 else '✗'}")
        
        # Boot code (120-509)
        bootcode = boot[120:510]
        print(f"BootCode (120-509): {bootcode.count(0)}/390 bytes zero {'(mostly zero)' if bootcode.count(0) > 350 else '(NOT mostly zero)'}")
        
        boot_sig = struct.unpack('<H', boot[510:512])[0]
        print(f"BootSignature (510-511): {hex(boot_sig)} {'✓ (0xAA55)' if boot_sig == 0xAA55 else '✗'}")
        
        # Check VBR checksum (stored in sector 11)
        print(f"\n=== VBR CHECKSUM ===")
        f.seek(11 * 512)
        csum_sector = f.read(512)
        stored_csum = struct.unpack('<I', csum_sector[0:4])[0]
        
        # Compute VBR checksum over sectors 0-10 (skip bytes 106-107 in sector 0)
        vbr_data = boot_main + boot[512:11*512]
        csum = 0
        for i, b in enumerate(vbr_data):
            if i in (106, 107):  # Skip checksum field location
                continue
            csum = ((csum << 31) | (csum >> 1)) & 0xFFFFFFFF
            csum = (csum + b) & 0xFFFFFFFF
        
        computed_csum = csum & 0xFFFFFFFF
        print(f"Stored checksum: {hex(stored_csum)}")
        print(f"Computed checksum: {hex(computed_csum)}")
        print(f"VBR Checksum valid: {'✓' if stored_csum == computed_csum else '✗ MISMATCH'}")
        
        # Check all 128 entries in checksum sector are identical
        all_csums = []
        for i in range(128):
            cs = struct.unpack('<I', csum_sector[i*4:(i+1)*4])[0]
            all_csums.append(cs)
        
        if len(set(all_csums)) == 1:
            print(f"Checksum sector: ✓ All 128 entries identical")
        else:
            print(f"Checksum sector: ✗ Entries differ! Unique values: {len(set(all_csums))}")
        
        # Check backup VBR
        print(f"\n=== BACKUP VBR ===")
        if boot_backup_read[0:3] == b'\\xEB\\x76\\x90':
            print(f"Backup VBR signature: ✓")
        else:
            print(f"Backup VBR signature: ✗ {boot_backup_read[0:3].hex()}")
        
        if boot_backup_read == boot_main:
            print(f"Backup VBR matches main: ✓")
        else:
            print(f"Backup VBR matches main: ✗ Data differs")
        
        # Check FAT
        print(f"\n=== FAT TABLE ===")
        f.seek(fat_offset * bps)
        fat = f.read(min(32, fat_len * bps))
        
        fat0 = struct.unpack('<I', fat[0:4])[0]
        fat1 = struct.unpack('<I', fat[4:8])[0]
        fat2 = struct.unpack('<I', fat[8:12])[0]
        fat3 = struct.unpack('<I', fat[12:16])[0]
        
        print(f"FAT[0]: {hex(fat0)} {'✓ (0xFFFFFFF8)' if fat0 == 0xFFFFFFF8 else '✗'}")
        print(f"FAT[1]: {hex(fat1)} {'✓ (0xFFFFFFFF)' if fat1 == 0xFFFFFFFF else '✗'}")
        print(f"FAT[2] (bitmap): {hex(fat2)} {'✓ (EOC)' if fat2 == 0xFFFFFFFF else '✗'}")
        print(f"FAT[3] (upcase): {hex(fat3)} {'✓ (EOC)' if fat3 == 0xFFFFFFFF else '✗'}")
        
        # Check root directory
        print(f"\n=== ROOT DIRECTORY ===")
        root_offset = heap_offset * bps + (root_cluster - 2) * cs
        print(f"Root at byte offset: {root_offset} (cluster {root_cluster})")
        
        f.seek(root_offset)
        root = f.read(min(512, cs))
        
        # Entries
        e0_type = root[0]
        e1_type = root[32]
        e2_type = root[64]
        e3_type = root[96]
        
        print(f"Entry 0 type: {hex(e0_type)} {'✓ (0x81 bitmap)' if e0_type == 0x81 else '?'}")
        print(f"Entry 1 type: {hex(e1_type)} {'✓ (0x82 upcase)' if e1_type == 0x82 else '?'}")
        print(f"Entry 2 type: {hex(e2_type)} {'✓ (0x83 label)' if e2_type == 0x83 else '?'}")
        print(f"Entry 3 type: {hex(e3_type)} {'✓ (0x85 file)' if e3_type == 0x85 else '?'}")
        
        # Check Stream Extension in file entry
        if e3_type == 0x85:
            sec_count = root[33]  # Entry 3, byte 1
            print(f"Entry 3 SecondaryCount: {sec_count}")
            
            if e3_type > 32 and len(root) > 64:
                se_type = root[64]  # Should be entry's first secondary
                print(f"Entry 3 first secondary type: {hex(se_type)} {'✓ (0xC0)' if se_type == 0xC0 else '✗'}")
        
        # Check for corruption patterns
        print(f"\n=== CORRUPTION CHECK ===")
        # Check if key offsets make sense
        if fat_offset < 24:
            print(f"✗ CRITICAL: FAT starts before boot region ends!")
        else:
            print(f"✓ FAT offset after boot region")
        
        if heap_offset <= fat_offset + fat_len:
            print(f"✗ CRITICAL: Heap overlaps with FAT!")
        else:
            print(f"✓ Heap does not overlap FAT")
        
        if cluster_count <= 0:
            print(f"✗ CRITICAL: Invalid cluster count!")
        else:
            print(f"✓ Cluster count valid: {cluster_count}")
        
        if root_cluster < 2:
            print(f"✗ CRITICAL: Root cluster {root_cluster} < 2!")
        else:
            print(f"✓ Root cluster valid: {root_cluster}")
        
        print(f"\n=== SUMMARY ===")
        critical_issues = [
            fat_offset < 24,
            heap_offset <= fat_offset + fat_len,
            cluster_count <= 0,
            root_cluster < 2,
            num_fats != 1,
            boot_sig != 0xAA55,
            stored_csum != computed_csum
        ]
        
        if any(critical_issues):
            print(f"✗ CRITICAL ISSUES FOUND - Image may not mount on PS5")
            return False
        else:
            print(f"✓ All critical checks passed")
            print(f"Note: If PS5 still rejects with 0x00000016, issue may be in:")
            print(f"  - Deep directory structure validation")
            print(f"  - Specific field byte ordering or encoding")
            print(f"  - PS5-specific exFAT extensions we don't know about")
            return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python deep_validate_exfat.py <image.exfat>")
        sys.exit(1)
    
    success = validate_deep(sys.argv[1])
    sys.exit(0 if success else 1)
