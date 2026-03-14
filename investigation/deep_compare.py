#!/usr/bin/env python3
"""Deep byte-by-byte comparison of critical sections."""

import struct

def compare_boot_sector():
    """Compare first 512 bytes (boot sector)."""
    with open('PPSA17221-official.exfat', 'rb') as f_official, \
         open('test-ps5-final.exfat', 'rb') as f_gen:
        
        boot_official = f_official.read(512)
        boot_gen = f_gen.read(512)
        
        print("BOOT SECTOR COMPARISON (512 bytes):")
        print("=" * 70)
        
        diffs = []
        for i in range(512):
            if boot_official[i] != boot_gen[i]:
                diffs.append((i, boot_official[i], boot_gen[i]))
        
        if not diffs:
            print("[OK] BOOT SECTOR: PERFECT MATCH")
        else:
            print(f"[DIFF] BOOT SECTOR: {len(diffs)} differences found:")
            for offset, official_byte, gen_byte in diffs:
                print(f"  Offset {offset:3d} (0x{offset:03x}): Official=0x{official_byte:02x}, Generated=0x{gen_byte:02x}")

def compare_vbr_region():
    """Compare extended boot sectors (sectors 1-11)."""
    with open('PPSA17221-official.exfat', 'rb') as f_official, \
         open('test-ps5-final.exfat', 'rb') as f_gen:
        
        f_official.seek(512)
        vbr_official = f_official.read(512 * 11)
        
        f_gen.seek(512)
        vbr_gen = f_gen.read(512 * 11)
        
        print("\n\nVBR REGION COMPARISON (sectors 1-11, 5632 bytes):")
        print("=" * 70)
        
        diffs = []
        for i in range(len(vbr_official)):
            if vbr_official[i] != vbr_gen[i]:
                diffs.append(i)
        
        if not diffs:
            print("[OK] VBR REGION: PERFECT MATCH")
        else:
            print(f"[DIFF] VBR REGION: {len(diffs)} byte differences")
            # Show first few sectors that differ
            sectors_with_diffs = set(d // 512 for d in diffs)
            print(f"  Sectors with differences: {sorted(sectors_with_diffs)}")

def compare_fat_region():
    """Compare FAT (Fixed size: 576 sectors starting at sector 128)."""
    with open('PPSA17221-official.exfat', 'rb') as f_official, \
         open('test-ps5-final.exfat', 'rb') as f_gen:
        
        f_official.seek(128 * 512)
        fat_official = f_official.read(576 * 512)
        
        f_gen.seek(128 * 512)
        fat_gen = f_gen.read(576 * 512)
        
        print("\n\nFAT COMPARISON (576 sectors):")
        print("=" * 70)
        
        if fat_official == fat_gen:
            print("[OK] FAT REGION: PERFECT MATCH")
        else:
            # Find differences
            diffs = []
            for i in range(0, len(fat_official), 4):
                if fat_official[i:i+4] != fat_gen[i:i+4]:
                    official_val = struct.unpack('<I', fat_official[i:i+4])[0]
                    gen_val = struct.unpack('<I', fat_gen[i:i+4])[0]
                    entry_num = i // 4
                    diffs.append((entry_num, official_val, gen_val))
            
            print(f"[DIFF] FAT REGION: {len(diffs)} entry differences")
            # Show first 20 differences
            for entry_num, official_val, gen_val in diffs[:20]:
                print(f"  FAT[{entry_num}]: Official=0x{official_val:08x}, Generated=0x{gen_val:08x}")
            if len(diffs) > 20:
                print(f"  ... and {len(diffs)-20} more")

def compare_sce_sys_param():
    """Compare sce_sys directory structure."""
    with open('PPSA17221-official.exfat', 'rb') as f_official, \
         open('test-ps5-final.exfat', 'rb') as f_gen:
        
        # Get geometry
        f_official.seek(108)
        bps_shift_o = ord(f_official.read(1))
        spc_shift_o = ord(f_official.read(1))
        f_official.seek(88)
        heap_offset_o = struct.unpack('<I', f_official.read(4))[0]
        
        f_gen.seek(108)
        bps_shift_g = ord(f_gen.read(1))
        spc_shift_g = ord(f_gen.read(1))
        f_gen.seek(88)
        heap_offset_g = struct.unpack('<I', f_gen.read(4))[0]
        
        bps_o = 1 << bps_shift_o
        spc_o = 1 << spc_shift_o
        csize_o = bps_o * spc_o
        
        bps_g = 1 << bps_shift_g
        spc_g = 1 << spc_shift_g
        csize_g = bps_g * spc_g
        
        print("\n\nPARAM.JSON DIRECTORY ENTRY COMPARISON:")
        print("=" * 70)
        
        # Find sce_sys in root and look for param.json
        # Read root cluster 4
        root_offset_o = (heap_offset_o + (4 - 2) * spc_o) * bps_o
        root_offset_g = (heap_offset_g + (4 - 2) * spc_g) * bps_g
        
        f_official.seek(root_offset_o)
        root_o = f_official.read(csize_o)
        
        f_gen.seek(root_offset_g)
        root_g = f_gen.read(csize_g)
        
        if root_o[:100] == root_g[:100]:
            print("[OK] First 100 bytes of root directory: MATCH")
        else:
            print("[DIFF] First 100 bytes of root directory: DIFFER")
            print(f"  Official: {root_o[:100].hex()}")
            print(f"  Generated: {root_g[:100].hex()}")

compare_boot_sector()
compare_vbr_region()
compare_fat_region()
compare_sce_sys_param()

print("\n\n" + "=" * 70)
print("SUMMARY: Check details above to identify source of differences")
"""
Deep structure comparison of exFAT images.
Analyzes boot sector checksums, directory entries, FAT structure, etc.
"""

import struct
import sys

def analyze_boot_sector(path, offset=0):
    """Detailed boot sector analysis."""
    with open(path, 'rb') as f:
        f.seek(offset)
        boot = f.read(512)
    
    print(f"\n{'='*70}")
    print(f"BOOT SECTOR @ offset {offset}: {path}")
    print(f"{'='*70}")
    
    # Signature
    print(f"Signature (510-511): {boot[510:512].hex()} {'OK' if boot[510:512] == b'\\x55\\xAA' else 'BAD'}")
    
    # Jump boot
    print(f"Jump Boot (0-2): {boot[0:3].hex()}")
    
    # OEM
    print(f"OEM (3-10): {boot[3:11]}")
    
    # Sectors per cluster
    spc = boot[13]
    print(f"Sectors per cluster (13): {spc}")
    
    # Reserved Sector Count
    reserved = struct.unpack('<H', boot[14:16])[0]
    print(f"Reserved Sector Count (14-15): {reserved}")
    
    # Must be zero
    mbz = struct.unpack('<I', boot[16:20])[0]
    print(f"MustBeZero (16-19): 0x{mbz:08x} {'OK' if mbz == 0 else 'BAD'}")
    
    # Sector size
    sector_size = struct.unpack('<H', boot[11:13])[0]
    print(f"Sector Size (11-12): {sector_size}")
    
    # Partition offset
    part_off = struct.unpack('<Q', boot[64:72])[0]
    print(f"Partition Offset (64-71): {part_off}")
    
    # Volume length
    vol_len = struct.unpack('<Q', boot[72:80])[0]
    print(f"Volume Length sectors (72-79): {vol_len} ({vol_len * sector_size / (1<<30):.2f} GB)")
    
    # FAT offset
    fat_off = struct.unpack('<I', boot[80:84])[0]
    print(f"FAT Offset (80-83): {fat_off} sectors")
    
    # FAT length
    fat_len = struct.unpack('<I', boot[84:88])[0]
    print(f"FAT Length (84-87): {fat_len} sectors")
    
    # Cluster heap offset
    heap_off = struct.unpack('<I', boot[88:92])[0]
    print(f"Cluster Heap Offset (88-91): {heap_off} sectors")
    
    # Cluster count  
    cluster_cnt = struct.unpack('<I', boot[92:96])[0]
    print(f"Cluster Count (92-95): {cluster_cnt}")
    
    # Root cluster
    root_clust = struct.unpack('<I', boot[96:100])[0]
    print(f"Root Cluster (96-99): {root_clust}")
    
    # Serial number
    serial = struct.unpack('<I', boot[100:104])[0]
    print(f"Serial Number (100-103): 0x{serial:08x}")
    
    # FS Revision
    fs_rev = struct.unpack('<H', boot[104:106])[0]
    print(f"FileSystem Revision (104-105): 0x{fs_rev:04x}")
    
    # Boot flags
    boot_flags = struct.unpack('<H', boot[106:108])[0]
    print(f"Boot Flags (106-107): 0x{boot_flags:04x}")
    
    # Media type
    media = boot[109]
    print(f"Media Type (109): 0x{media:02x} {'OK' if media == 0xF8 else 'BAD (should be 0xF8)'}")
    
    # Boot code region (120-509)
    bootcode = boot[120:509]
    if bootcode == b'\x00' * (509-120):
        print(f"Boot Code (120-508): All zeros")
    else:
        nonzero_count = sum(1 for b in bootcode if b != 0)
        print(f"Boot Code (120-508): {nonzero_count} non-zero bytes")
    
    # Boot sector checksum region
    print(f"\nBoot Checksum Region (Sector 0, extended VBR sectors 1-11):")
    # The checksum is computed over bytes 0-511 and repeated in sectors 1-11
    return boot, cluster_cnt

def analyze_extended_vbr(path, sector):
    """Analyze extended boot sectors."""
    with open(path, 'rb') as f:
        f.seek(sector * 512)
        data = f.read(512)
    
    print(f"\nExtended VBR @ sector {sector}:")
    print(f"  Signature (510-511): {data[510:512].hex()}")
    if data[510:512] == b'\x55\xAA':
        print(f"  OK - Valid signature")
    else:
        print(f"  BAD - INVALID signature")

def analyze_fat(path, boot_data, offset=0):
    """Analyze FAT structure."""
    sector_size = struct.unpack('<H', boot_data[11:13])[0]
    fat_off_sector = struct.unpack('<I', boot_data[80:84])[0]
    fat_len_sectors = struct.unpack('<I', boot_data[84:88])[0]
    
    print(f"\n{'='*70}")
    print(f"FAT @ sector {fat_off_sector} ({fat_len_sectors} sectors) in {path}")
    print(f"{'='*70}")
    
    with open(path, 'rb') as f:
        f.seek(offset + fat_off_sector * sector_size)
        fat_data = f.read(min(16 * 4, fat_len_sectors * sector_size))  # read first 16 entries
    
    for i in range(min(16, len(fat_data) // 4)):
        val = struct.unpack('<I', fat_data[i*4:(i+1)*4])[0]
        desc = ""
        if i == 0:
            desc = " (media byte)" if val == 0xFFFFFFF8 else f" (WRONG! should be 0xFFFFFFF8)"
        elif i == 1:
            desc = " (reserved)" if val == 0xFFFFFFFF else " (reserved)"
        elif val == 0:
            desc = " (free)"
        elif val == 0xFFFFFFFF:
            desc = " (end-of-chain)"
        print(f"  FAT[{i:2d}] = 0x{val:08x}{desc}")

def analyze_root_dir(path, boot_data, offset=0):
    """Analyze root directory entries."""
    sector_size = struct.unpack('<H', boot_data[11:13])[0]
    heap_off_sector = struct.unpack('<I', boot_data[88:92])[0]
    root_cluster = struct.unpack('<I', boot_data[96:100])[0]
    cluster_size = struct.unpack('<I', boot_data[13:14])[0] * sector_size
    
    print(f"\n{'='*70}")
    print(f"ROOT DIRECTORY in {path}")
    print(f"  Heap offset: {heap_off_sector} sectors, Root cluster: {root_cluster}")
    print(f"{'='*70}")
    
    with open(path, 'rb') as f:
        # Root is at cluster root_cluster in the heap
        root_offset = offset + heap_off_sector * sector_size + (root_cluster - 2) * cluster_size
        f.seek(root_offset)
        root_data = f.read(512)  # read first 512 bytes of root
    
    entry_idx = 0
    pos = 0
    while pos < len(root_data) and entry_idx < 10:
        entry_type = root_data[pos]
        
        if entry_type == 0x00:
            print(f"  [{entry_idx}] End of directory")
            break
        else:
            type_desc = {
                0x81: 'Allocation Bitmap',
                0x82: 'Upcase Table',
                0x83: 'Volume Label',
                0x85: 'File',
                0xC0: 'Stream Extension',
                0xC1: 'File Name'
            }.get(entry_type, f'Unknown(0x{entry_type:02x})')
            
            # For file entries, show name length
            if entry_type == 0x85:
                name_len = root_data[pos+30]
                print(f"  [{entry_idx}] {type_desc:20} (name length: {name_len})")
            elif entry_type == 0xC0:
                flags = root_data[pos+1]
                print(f"  [{entry_idx}] {type_desc:20} (flags: 0x{flags:02x})")
            else:
                checksum = struct.unpack('<H', root_data[pos+2:pos+4])[0]
                print(f"  [{entry_idx}] {type_desc:20} (checksum: 0x{checksum:04x})")
        
        pos += 32
        entry_idx += 1

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <official_image> <python_image>")
        sys.exit(1)
    
    official = sys.argv[1]
    python_img = sys.argv[2]
    
    print(f"\nComparing exFAT structures...")
    
    # Analyze official
    boot_off, cluster_cnt_off = analyze_boot_sector(official)
    analyze_extended_vbr(official, 1)
    analyze_fat(official, boot_off)
    analyze_root_dir(official, boot_off)
    
    # Analyze Python
    boot_py, cluster_cnt_py = analyze_boot_sector(python_img)
    analyze_extended_vbr(python_img, 1)
    analyze_fat(python_img, boot_py)
    analyze_root_dir(python_img, boot_py)

if __name__ == '__main__':
    main()
