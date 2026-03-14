#!/usr/bin/env python3
"""
Deep directory entry validation - checks checksums and entry structure.
"""

import struct
import sys
from pathlib import Path

DENTRY_TYPE_FILE       = 0x85
DENTRY_TYPE_STREAM_EXT = 0xC0
DENTRY_TYPE_FILE_NAME  = 0xC1

def compute_checksum(data: bytes) -> int:
    """Compute exFAT directory entry checksum per spec §6.3.1.
    
    SetChecksum is computed over:
    - Bytes 0-1 of File Entry
    - Bytes 4-31 of File Entry (with bytes 2-3 set to 0, which we skip)
    - All bytes of Stream Extension
    - All bytes of File Name entries
    """
    csum = 0
    for i, b in enumerate(data):
        if i in (2, 3):  # Skip SetChecksum field itself
            continue
        csum = ((csum << 31) | (csum >> 1)) & 0xFFFFFFFF
        csum = (csum + b) & 0xFFFFFFFF
    return csum & 0xFFFF

def validate_directory_entries(image_path):
    """Validate all directory entries in the image."""
    with open(image_path, 'rb') as f:
        # Read boot sector for geometry
        boot = f.read(512)
        heap_offset = struct.unpack('<I', boot[88:92])[0]
        root_cluster = struct.unpack('<I', boot[96:100])[0]
        bps_shift = boot[108]
        spc_shift = boot[109]
        
        bps = 1 << bps_shift
        spc = 1 << spc_shift
        cs = bps * spc
        
        print(f"Heap offset: sector {heap_offset}")
        print(f"Root cluster: {root_cluster}")
        print(f"Cluster size: {cs} bytes\n")
        
        # Read root directory
        root_offset = heap_offset * bps + (root_cluster - 2) * cs
        
        print(f"=== Root Directory Entries ===")
        f.seek(root_offset)
        root_data = f.read(min(cs, 4096))  # Read first 4 KiB of root
        
        errors = []
        
        # Parse entries
        entry_num = 0
        i = 0
        while i < len(root_data) - 32:
            dentry = root_data[i:i+32]
            dtype = dentry[0]
            
            if dtype == 0x00:  # EOD
                print(f"Entry {entry_num}: EOD")
                break
            elif dtype == 0x81:  # Bitmap
                print(f"Entry {entry_num}: Allocation Bitmap (0x81) ✓")
                i += 32
                entry_num += 1
            elif dtype == 0x82:  # Upcase
                print(f"Entry {entry_num}: Upcase Table (0x82) ✓")
                i += 32
                entry_num += 1
            elif dtype == 0x83:  # Volume label
                print(f"Entry {entry_num}: Volume Label (0x83) ✓")
                i += 32
                entry_num += 1
            elif dtype == 0x85:  # File entry
                sec_count = dentry[1]
                # SetChecksum at bytes 2-3
                stored_checksum = struct.unpack('<H', dentry[2:4])[0]
                
                # Read all secondary entries for this file set
                all_data = dentry
                for _ in range(sec_count):
                    i += 32
                    if i + 32 <= len(root_data):
                        all_data += root_data[i:i+32]
                
                # Compute checksum over full File Entry + secondaries
                # (with bytes 2-3 skipped in the computation)
                computed_checksum = compute_checksum(all_data)
                
                # Get filename from stream extension
                stream_ext = all_data[32:64]
                name_len = stream_ext[3]
                
                if stream_ext[0] == DENTRY_TYPE_STREAM_EXT:
                    print(f"Entry {entry_num}: File {name_len} chars")
                    if stored_checksum == computed_checksum:
                        print(f"  ✓ SetChecksum valid: {hex(stored_checksum)}")
                    else:
                        msg = f"  ✗ SetChecksum MISMATCH: stored={hex(stored_checksum)}, computed={hex(computed_checksum)}"
                        print(msg)
                        errors.append((entry_num, msg))
                
                i += 32
                entry_num += 1
            else:
                if dtype in (0xC0, 0xC1):
                    print(f"Entry {entry_num}: Secondary (0x{hex(dtype)[2:].upper()})")
                else:
                    print(f"Entry {entry_num}: Unknown type 0x{hex(dtype)[2:].upper()}")
                i += 32
                entry_num += 1
        
        print(f"\n=== Summary ===")
        if errors:
            print(f"✗ Found {len(errors)} checksum errors:")
            for entry_num, msg in errors:
                print(f"  {msg}")
            return False
        else:
            print(f"✓ All directory entry checksums valid")
            return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python check_dentries.py <image.exfat>")
        sys.exit(1)
    
    success = validate_directory_entries(sys.argv[1])
    sys.exit(0 if success else 1)
