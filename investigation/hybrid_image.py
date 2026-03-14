#!/usr/bin/env python3
"""
Create hybrid test image: Official boot sector + Python file data.
This isolates whether the issue is boot geometry or file content.
"""

import shutil
import sys

def create_hybrid(official, python_img, output):
    """Copy official boot sector (0-11 sectors) to Python image."""
    print(f"Creating hybrid image...")
    print(f"  Boot from: {official}")
    print(f"  Data from: {python_img}")
    print(f"  Output:    {output}")
    
    # Copy Python image as base
    shutil.copy(python_img, output)
    
    # Read official boot sectors (0-11, 12 sectors = 6144 bytes)
    with open(official, 'rb') as f:
        boot_data = f.read(12 * 512)
    
    # Write official boot sectors to output
    with open(output, 'r+b') as f:
        f.seek(0)
        f.write(boot_data)
    
    print(f"Done. Test this image on PS5 to isolate boot vs. data issues.")

if __name__ == '__main__':
    create_hybrid('PPSA17221-official.exfat', 'PPSA17221-fixed.exfat', 'PPSA17221-hybrid.exfat')
