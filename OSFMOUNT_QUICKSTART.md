# OSFMount exFAT Image Creation - Quick Start

## Method 1: Using make_image.bat (EASIEST)

1. **Open Command Prompt as Administrator**
   - Right-click on Command Prompt → "Run as Administrator"

2. **Navigate to workspace folder**
   ```
   cd C:\Users\Lithiumwow\ps4-5\SDKPS5FTPandNewprojecthere
   ```

3. **Run the script**
   ```
   make_image.bat "PPSA17221-osfmount.exfat" "PPSA17221-app" "2G"
   ```

   Arguments:
   - `"PPSA17221-osfmount.exfat"` = output image path
   - `"PPSA17221-app"` = source folder
   - `"2G"` = image size (optional - auto-calculates if omitted)

## Method 2: Using PowerShell Directly

1. **Open PowerShell as Administrator**
   - Right-click PowerShell → "Run as Administrator"

2. **Navigate to workspace**
   ```
   cd C:\Users\Lithiumwow\ps4-5\SDKPS5FTPandNewprojecthere
   ```

3. **Run the script**
   ```
   powershell.exe -ExecutionPolicy Bypass -File .\New-OsfExfatImage.ps1 -ImagePath "PPSA17221-osfmount.exfat" -SourceDir "PPSA17221-app" -Size "2G" -Label "OSFIMG" -ForceOverwrite
   ```

## What This Does

- Creates a 2GB raw image file
- Mounts it via OSFMount
- Formats as exFAT
- Copies all files from PPSA17221-app into the image
- Unmounts and finalizes

## Requirements

✓ OSFMount installed (found at: C:\Program Files\OSFMount\osfmount.com)
✓ Administrator privileges
✓ Source folder exists (PPSA17221-app)
✓ Both make_image.bat and New-OsfExfatImage.ps1 in same folder

## After Image Creation

1. **Compress the image** (optional for transfer):
   ```
   python compress_image.py PPSA17221-osfmount.exfat PPSA17221-osfmount.exfat.zst
   ```

2. **Transfer to PS5**:
   - Use uncompressed: `PPSA17221-osfmount.exfat`
   - Or compressed: `PPSA17221-osfmount.exfat.zst` (with ZSTDecompressionPS5.elf)

## Common Issues

**Error: "run PowerShell as Administrator"**
- Solution: Right-click PowerShell/Command Prompt → "Run as Administrator"

**Error: "osfmount.com not found"**
- Solution: OSFMount needs PATH update. Add C:\Program Files\OSFMount to your system PATH
- Or manually install from: https://www.osforensics.com/tools/mount-disk-images.html

**Error: "Image file already exists"**
- Solution: Add `-ForceOverwrite` parameter (already in the bat file)
- Or manually delete the old image first

