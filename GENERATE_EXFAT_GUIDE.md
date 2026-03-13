# How to Generate exFAT Image Using make_image.bat

## Quick Summary
- `make_image.bat` is a **Windows batch script** that automates exFAT image creation
- It uses **OSFMount** (commercial tool) to create and format the image
- It requires **Administrator privileges**
- It copies your game files into the image automatically

---

## Prerequisites ✓

All already available:
- ✓ `make_image.bat` — in your workspace root
- ✓ `New-OsfExfatImage.ps1` — in your workspace root (PowerShell backend)
- ✓ **OSFMount installed** at `C:\Program Files\OSFMount\osfmount.com`
- ✓ **PPSA17221-app** folder — your game source folder

---

## How to Generate (3 Steps)

### Step 1: Open Command Prompt as Administrator

**Important: You MUST run as Administrator**

Option A (Recommended):
- Press `Windows Key + R`
- Type: `cmd`
- Press `Ctrl + Shift + Enter` (runs as Admin)

Option B:
- Right-click on Command Prompt
- Select "Run as Administrator"

You'll see "Administrator Command Prompt" in the title bar.

---

### Step 2: Navigate to Your Workspace

```cmd
cd C:\Users\Lithiumwow\ps4-5\SDKPS5FTPandNewprojecthere
```

---

### Step 3: Run make_image.bat

**Option A: Auto-size (Recommended)**

```cmd
make_image.bat "PPSA17221-osfmount.exfat" "PPSA17221-app"
```

This will:
- Automatically calculate the image size based on your game files
- Create `PPSA17221-osfmount.exfat` (will be ~2GB for your game)
- Take 2-5 minutes to complete

**Option B: Fixed size (2GB)**

```cmd
make_image.bat "PPSA17221-osfmount.exfat" "PPSA17221-app" "2G"
```

**Option C: Different sizes**

```cmd
make_image.bat "PPSA17221-osfmount.exfat" "PPSA17221-app" "4G"
```

---

## What Happens During Generation

1. ✓ Creates raw image file
2. ✓ Mounts it via OSFMount
3. ✓ Formats partition as exFAT
4. ✓ Copies all files from `PPSA17221-app` into image root
5. ✓ Validates that `sce_sys/param.json` is present
6. ✓ Unmounts and finalizes

**Progress Output:**
```
========================================
OSFMount exFAT Image Creator (Batch)
========================================
ImagePath: PPSA17221-osfmount.exfat
SourceDir: PPSA17221-app
Size: auto-calculate

[... mounting and formatting ...]
[... copying files ...]

✓ Image created successfully: PPSA17221-osfmount.exfat
```

---

## After Generation ✓

### Compress for Transfer (Optional)

Your generated image will be ~2GB. To compress it to ~650MB for transfer:

```cmd
python compress_image.py PPSA17221-osfmount.exfat PPSA17221-osfmount.exfat.zst
```

### Transfer to PS5

You now have two options:

**Option 1: Direct (Uncompressed)**
- Transfer `PPSA17221-osfmount.exfat` directly to PS5
- Place in `/data/imgmnt/exfatmnt/`
- ShadowMountPlus will auto-mount it

**Option 2: Compressed**
- Transfer `PPSA17221-osfmount.exfat.zst` to PS5
- Transfer `ZSTDecompressionPS5.elf` to PS5
- Decompress on PS5 using the .elf
- Then move to `/data/imgmnt/exfatmnt/`

---

## Troubleshooting

### ❌ "Access Denied" or "not recognized"

**Solution:** You didn't run Command Prompt as Administrator
- Close the window
- Right-click Command Prompt
- Select "Run as Administrator"
- Try again

### ❌ "OSFMount not found" or "osfmount.com not found"

**Solution:** OSFMount is not in system PATH
- Manual fix: Add Python path to PATH environment variable
- Or: Run PowerShell script directly:

```cmd
powershell.exe -ExecutionPolicy Bypass -File .\New-OsfExfatImage.ps1 -ImagePath "PPSA17221-osfmount.exfat" -SourceDir "PPSA17221-app" -Size 2G -Label "OSFIMG" -ForceOverwrite
```

### ❌ "File already exists"

**Solution:** The .exfat file was already created
- Command will overwrite it automatically (because of `-ForceOverwrite` in the script)
- If you want to keep old version, rename it first:
  ```cmd
  ren PPSA17221-osfmount.exfat PPSA17221-osfmount-v1.exfat
  ```

### ❌ "Source folder not found"

**Solution:** Path to PPSA17221-app is wrong
- Make sure folder exists: `PPSA17221-app\sce_sys\param.json` should be present
- Use full path if in different folder:
  ```cmd
  make_image.bat "output.exfat" "C:\full\path\to\PPSA17221-app"
  ```

### ❌ "eboot.bin not found in source"

**Solution:** Source folder is missing game executable
- Your PPSA17221-app folder must contain `eboot.bin` at root level
- Valid structure:
  ```
  PPSA17221-app\
    eboot.bin          ← Must exist
    sce_sys\
      param.json
      icon0.dds
    data\
  ```

---

## Complete Example Command

```cmd
cd C:\Users\Lithiumwow\ps4-5\SDKPS5FTPandNewprojecthere
make_image.bat "PPSA17221-osfmount.exfat" "PPSA17221-app"
```

After completion:
```cmd
python compress_image.py PPSA17221-osfmount.exfat PPSA17221-osfmount.exfat.zst
```

Then transfer both `.exfat` and `.zst` files to PS5.

---

## Notes

- **Time:** 2-5 minutes for 2GB image (depends on disk speed)
- **Disk Space:** Need ~2GB free space on C: drive (or where OSFMount mounts)
- **Admin Required:** Cannot work without Administrator privileges
- **One at a Time:** Don't run multiple make_image.bat instances simultaneously
- **Final Check:** After generation, image should be ~2.00 GB in size

