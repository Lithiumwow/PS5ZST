#!/usr/bin/env python3
"""
Create exFAT images using system-installed OSFMount.com command-line tool.
Mirrors the official OSFMount approach from New-OsfExfatImage.ps1.

REQUIRES: Administrator privileges to run OSFMount.
"""

import subprocess
import sys
import time
import ctypes
from pathlib import Path

OSFMOUNT_COM = r"C:\Program Files\OSFMount\osfmount.com"

def is_admin():
    """Check if script is running as administrator."""
    try:
        return ctypes.windll.shell.IsUserAnAdmin()
    except:
        return False

def find_free_drive_letter():
    """Find first available drive letter."""
    import string
    # Try common letters from Z down to D
    for letter in reversed(string.ascii_uppercase[3:]):  # Skip A, B, C
        drive_path = Path(f"{letter}:")
        if not drive_path.exists():
            return letter
    return None

def format_volume(drive_letter, cluster_size='32K'):
    """Format drive as exFAT using format.com."""    
    drive = f"{drive_letter}:"
    cmd = [
        'format.com',  # Built-in Windows format tool
        drive,
        '/FS:exFAT',
        f'/A:{cluster_size}',
        '/Y'  # Auto-confirm
    ]
    
    print(f"Formatting {drive} as exFAT (cluster={cluster_size})...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"✗ Format failed: {result.stderr}")
        return False
    
    print(f"✓ {drive} formatted successfully")
    return True

def copy_tree(src, dst):
    """Copy directory tree to mounted drive."""
    import shutil
    print(f"Copying {src} to {dst}...")
    
    src_path = Path(src)
    dst_path = Path(dst)
    
    for item in src_path.iterdir():
        dest_item = dst_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest_item)
        else:
            shutil.copy2(item, dest_item)
    
    print(f"✓ Copied all files")
    return True

def create_exfat_with_osfmount(image_path: str, source_dir: str, size_gb: int = 2):
    """
    Create exFAT image using OSFMount command-line (osfmount.com).
    Uses the official approach from New-OsfExfatImage.ps1
    """
    image_path = Path(image_path).resolve()
    source_dir = Path(source_dir).resolve()
    
    # Check prerequisites
    if not Path(OSFMOUNT_COM).exists():
        print(f"ERROR: osfmount.com not found at {OSFMOUNT_COM}")
        return False
    
    if not source_dir.is_dir():
        print(f"ERROR: {source_dir} is not a directory")
        return False
    
    if image_path.exists():
        print(f"Removing existing image: {image_path}")
        image_path.unlink()
    
    # Create empty image file
    print(f"Creating empty image file: {image_path}")
    image_path.touch()
    
    # Find free drive letter
    drive_letter = find_free_drive_letter()
    if not drive_letter:
        print(f"ERROR: No free drive letters available")
        return False
    
    mount_point = f"{drive_letter}:"
    print(f"Using drive letter: {mount_point}\n")
    
    # Mount the image via OSFMount
    print(f"=== Step 1: Mount image ===")
    size_str = f"{size_gb}G"
    mount_cmd = [
        OSFMOUNT_COM,
        '-a',           # Add new virtual drive
        '-t', 'file',   # File image type
        '-f', str(image_path),
        '-s', size_str,  # Size
        '-m', mount_point,  # Mount point
        '-o', 'rw,rem'  # Options: read-write, removable
    ]
    
    print(f"Command: {OSFMOUNT_COM} -a -t file -f {image_path} -s {size_str} -m {mount_point} -o rw,rem")
    result = subprocess.run(mount_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"✗ Mount failed")
        print(f"STDERR:\n{result.stderr}")
        return False
    
    print(f"✓ Mounted image at {mount_point}")
    if result.stdout:
        print(f"Output: {result.stdout}")
    
    # Wait for drive to appear
    print(f"Waiting for drive to appear...")
    for i in range(20):
        if Path(mount_point).exists():
            print(f"✓ Drive appeared")
            break
        time.sleep(1)
    else:
        print(f"✗ Drive did not appear after 20 seconds")
        return False
    
    mounted = True
    try:
        # Format as exFAT
        print(f"\n=== Step 2: Format as exFAT ===")
        if not format_volume(drive_letter, '32K'):
            return False
        
        # Copy files
        print(f"\n=== Step 3: Copy files ===")
        dest_path = f"{mount_point}\\"
        if not copy_tree(source_dir, dest_path):
            return False
        
        print(f"\n✓ Image created successfully: {image_path}")
        return True
        
    finally:
        # Unmount
        if mounted:
            print(f"\n=== Step 4: Unmount ===")
            unmount_cmd = [
                OSFMOUNT_COM,
                '-d',
                '-m', mount_point
            ]
            result = subprocess.run(unmount_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ Unmounted {mount_point}")
            else:
                print(f"⚠ Unmount may have failed, try: {OSFMOUNT_COM} -d -m {mount_point}")

if __name__ == '__main__':
    # Check for admin privileges
    if not is_admin():
        print("ERROR: This script requires administrator privileges!")
        print("\nPlease run as administrator:")
        print("  Option 1: Right-click PowerShell and select 'Run as administrator'")
        print("  Option 2: In admin PowerShell, run: python make_exfat_official.py ...")
        sys.exit(1)
    
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <output.exfat> <input_dir> [size_gb]")
        print(f"Example: {sys.argv[0]} game.exfat ./PPSA17221-app 2")
        sys.exit(1)
    
    output = sys.argv[1]
    source = sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    
    success = create_exfat_with_osfmount(output, source, size)
    sys.exit(0 if success else 1)
