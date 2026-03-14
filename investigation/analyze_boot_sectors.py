#!/usr/bin/env python3
"""Examine the first sectors of both exFAT images to understand their structure."""

import struct

def examine_image(path, name):
    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"{'='*60}")
    
    with open(path, 'rb') as f:
        # Check first 1024 bytes for signatures
        data = f.read(1024)
        
        print(f"First 512 bytes (boot sector):")
        print(f"  Bytes 0-2: {data[0:3].hex()} (signature)")
        print(f"  Bytes 510-511: {data[510:512].hex()} (boot sig should be 55AA)")
        
        # Check for exFAT signature
        if data[0:3] == b'EB\x90' or data[0:3] == b'EB\x3c':
            print(f"  ✓ Has boot sector signature: {data[0:3].hex()}")
        else:
            print(f"  ✗ Missing boot sector signature, got: {data[0:3].hex()}")
        
        # Parse ExFAT specific fields
        print(f"\nBoot Sector Analysis:")
        print(f"  Offset 48-52 (FAT offset): {struct.unpack('<I', data[48:52])[0]}")
        print(f"  Offset 52-56 (FAT length): {struct.unpack('<I', data[52:56])[0]}")
        print(f"  Offset 56-60 (Heap offset): {struct.unpack('<I', data[56:60])[0]}")
        print(f"  Offset 60-64 (Root cluster): {struct.unpack('<I', data[60:64])[0]}")
        print(f"  Offset 108 (BPS shift): {data[108]}")
        print(f"  Offset 109 (SCS shift): {data[109]}")
        
        # Check bytes 64-82 for the OEM ID and FS name
        print(f"\nFS Name/Version (offset 64-82):")
        print(f"  Raw: {data[64:82]}")
        try:
            print(f"  As text: {data[64:82].decode('ascii', errors='replace')}")
        except:
            pass
        
        # Check for exFAT signature at offset 82
        print(f"\nSignature check (offset 82-88):")
        print(f"  Bytes 82-88: {data[82:88]}")
        if data[82:88] == b'EXFAT':
            print(f"  ✓ ExFAT signature found")
        else:
            print(f"  ✗ ExFAT signature NOT found")

examine_image('PPSA17221-official.exfat', 'OFFICIAL (OSFMount)')
examine_image('test-ps5-final.exfat', 'GENERATED (Python)')

# Check file sizes
import os
print(f"\n{'='*60}")
print("FILE SIZES")
print(f"{'='*60}")
print(f"Official: {os.path.getsize('PPSA17221-official.exfat'):,} bytes ({os.path.getsize('PPSA17221-official.exfat')/1e9:.2f} GB)")
print(f"Generated: {os.path.getsize('test-ps5-final.exfat'):,} bytes ({os.path.getsize('test-ps5-final.exfat')/1e9:.2f} GB)")
