#!/usr/bin/env python3
"""
Create exFAT image using OSFMount via Python subprocess.
This is a reference implementation to compare with our Python version.
"""

import subprocess
import sys
import time
from pathlib import Path

def run_osfmount_image(image_path, source_dir, drive_letter='Z'):
    """
    Create exFAT image using OSFMount.
    
    Steps:
    1. Mount blank image as virtual drive
    2. Format as exFAT
    3. Copy files
    4. Unmount
    """
    
    image_path = Path(image_path).resolve()
    source_dir = Path(source_dir).resolve()
    
    print(f"OSFMount Reference Image Creator")
    print(f"Image: {image_path}")
    print(f"Source: {source_dir}")
    print(f"Drive: {drive_letter}:\\")
    
    # Check image exists
    if not image_path.exists():
        print(f"✗ Image file not found: {image_path}")
        return False
    
    if not source_dir.exists():
        print(f"✗ Source directory not found: {source_dir}")
        return False
    
    print(f"\n=== Step 1: Mount image with OSFMount ===")
    # Mount command: osfmount.exe -a -t file -f image_path -m Z
    mount_cmd = [
        'osfmount.exe',
        '-a',           # Add new virtual drive
        '-t', 'file',   # File image type
        '-f', str(image_path),
        '-m', f'{drive_letter}'
    ]
    
    print(f"Command: {' '.join(mount_cmd)}")
    try:
        result = subprocess.run(mount_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"✗ Mount failed: {result.stderr}")
            return False
        print(f"✓ Mount succeeded")
        print(f"Output: {result.stdout}")
    except Exception as e:
        print(f"✗ Error running OSFMount: {e}")
        return False
    
    time.sleep(2)  # Wait for mount to complete
    
    print(f"\n=== Step 2: Format as exFAT ===")
    format_cmd = [
        'format.exe',
        f'{drive_letter}:',
        '/FS:exFAT',
        '/Q'  # Quick format
    ]
    
    print(f"Command: {' '.join(format_cmd)}")
    try:
        result = subprocess.run(format_cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"✗ Format failed: {result.stderr}")
        else:
            print(f"✓ Format succeeded")
    except Exception as e:
        print(f"✗ Error formatting: {e}")
    
    time.sleep(2)
    
    print(f"\n=== Step 3: Copy files ===")
    # Use robocopy or xcopy to copy files
    copy_cmd = [
        'robocopy.exe',
        str(source_dir),
        f'{drive_letter}:\\',
        '/E',   # Copy directories and subdirectories
        '/R:1', # 1 retry
        '/W:1'  # 1 second wait between retries
    ]
    
    print(f"Command: {' '.join(copy_cmd)}")
    try:
        result = subprocess.run(copy_cmd, capture_output=True, text=True, timeout=600)
        print(f"Copy completed")
        if result.stdout:
            lines = result.stdout.split('\n')
            for line in lines[-10:]:  # Last 10 lines
                if line.strip():
                    print(f"  {line}")
    except Exception as e:
        print(f"✗ Error copying files: {e}")
    
    time.sleep(2)
    
    print(f"\n=== Step 4: Unmount image ===")
    unmount_cmd = [
        'osfmount.exe',
        '-d',           # Dismount
        '-m', f'{drive_letter}'
    ]
    
    print(f"Command: {' '.join(unmount_cmd)}")
    try:
        result = subprocess.run(unmount_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"✗ Unmount failed: {result.stderr}")
        else:
            print(f"✓ Unmount succeeded")
    except Exception as e:
        print(f"✗ Error unmounting: {e}")
    
    print(f"\n✓ Image creation complete: {image_path}")
    return True

if __name__ == '__main__':
    image_path = 'PPSA17221-osfmount.exfat'
    source_dir = 'PPSA17221-app'
    drive_letter = 'Z'
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    if len(sys.argv) > 2:
        source_dir = sys.argv[2]
    if len(sys.argv) > 3:
        drive_letter = sys.argv[3]
    
    success = run_osfmount_image(image_path, source_dir, drive_letter)
    sys.exit(0 if success else 1)
