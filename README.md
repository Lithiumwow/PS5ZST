# PSVZST

ZST workflow for PS5 game folder transfer and restore.

This project uses:
- PC-side compressor to create `.zst` files plus a `manifest.txt`
- PS5-side decompressor ELF to restore files to target path

## Quick Start

**Create exFAT + ZST with one command (Windows, PowerShell):**

```powershell
powershell -ExecutionPolicy Bypass -File run-generator.ps1
```

That's it! The script will:
1. ✅ Auto-elevate to Administrator (one UAC prompt)
2. ✅ Check for OSFMount (downloads via winget if missing)
3. ✅ Ask for source folder (your game package)
4. ✅ Ask for output folder (where to save files)
5. ✅ Create 88+ GB exFAT image
6. ✅ Compress to .zst with real-time progress
7. ✅ Show both files ready in output folder

## Setup Instructions (First Time)

### Step 1: Clone/Download Repository

```powershell
# Option A: Clone with Git
git clone <your-repo-url>
cd SDKPS5FTPandNewprojecthere

# Option B: Download ZIP and extract
# Then open PowerShell in the extracted folder
```

### Step 2: Install Python Requirements

Open PowerShell in the repository folder and run:

```powershell
pip install zstandard
```

### Step 3: Run the Generator

```powershell
.\run-generator.ps1
```

PowerShell will prompt for:
1. **Source folder path**: Your game package folder (e.g., `C:\path\to\PPSA04264`)
2. **Output folder path**: Where to save the exFAT and .zst files (e.g., `E:\Compressed`)
3. **Confirmation**: Review settings and confirm to proceed

The script handles everything automatically and will display progress as it works.

## Included Files

- `run-generator.ps1` : **Main script** — One-button workflow with auto-elevation and OSFMount checking
- `make_image_and_compress.bat` : Creates `.exfat` and automatically compresses to `.zst` (orchestrator)
- `compress_image.py` : Compresses a single `.exfat` image to `.exfat.zst` with progress tracking
- `make_image.bat` : Wrapper for PowerShell backend
- `New-OsfExfatImage.ps1` : Core engine for exFAT creation via OSFMount
- `compress_pkg.py` : Compresses a game folder into `.zst` files and manifest (alternative method)
- `ZSTDecompressionPS5.elf` : Ready PS5 decompressor ELF

## Requirements (PC)

- Windows 10/11
- PowerShell 5.1+
- Administrator access (script auto-elevates)
- Python 3
- Python package: `zstandard`
- **OSFMount by PassMark** (script auto-installs via winget if missing)

Install Python package:

```bash
pip install zstandard
```

## Usage: Create exFAT + ZST (Recommended)

**One command to rule them all:**

```powershell
powershell -ExecutionPolicy Bypass -File run-generator.ps1
```

The script will:

1. **Auto-elevate to Administrator** — You'll see one UAC prompt
2. **Check for OSFMount** — If missing, automatically installs via winget
3. **Ask for paths:**
   - Source: Your game package folder (e.g., `C:\path\to\PPSA04264`)
   - Output: Where to save exFAT and .zst files (e.g., `E:\Compressed`)
4. **Validate paths** — Confirms both folders exist
5. **Show configuration** — Displays what will happen, asks for confirmation
6. **Create exFAT image** — Mounts via OSFMount, formats to exFAT, copies all game data
7. **Compress automatically** — Real-time progress shows % complete, speed (MB/s), and ETA
8. **Output ready** — Both `.exfat` (88+ GB) and `.exfat.zst` (compressed) files ready

**Example interaction:**

```
Enter game package folder (e.g., C:\path\to\PPSA04264): C:\Games\PPSA17221
Enter output folder for exFAT and .zst (e.g., E:\Compressed): D:\PS5_Output

Configuration:
  Source:  C:\Games\PPSA17221
  Output:  D:\PS5_Output
  Image:   D:\PS5_Output\PPSA17221.exfat

Proceed with generation? (y/n): y
```

Then monitor the progress:

```
[12.5%] 11.00 GB read | 150.0 MB/s | ETA:  65.3 min
[25.0%] 22.00 GB read | 145.0 MB/s | ETA:  62.1 min
```

## Alternative: Create ZST Package (Per-File Method)

If you prefer compressing files individually:

```bash
python compress_pkg.py <game-folder> <output-folder> --level 3
```

Example:

```bash
python compress_pkg.py C:\Games\PPSA17221 D:\PS5_Output --level 3
```

### What `--level` means

- `--level` controls zstd compression strength.
- Lower values are faster compression but produce larger output files.
- Higher values are slower compression but produce smaller output files.
- Typical range in this tool: `1` to `22`.
- Recommended starting value: `3`.

Practical choices:

- `--level 1` for fastest pack time.
- `--level 3` for balanced speed/size.
- `--level 9+` when transfer size matters more than pack speed.

Reference implementation: `compress_pkg.py`.

Output folder contains:
- many `.zst` files
- `manifest.txt`

## Troubleshooting

### OSFMount fails to install

**If winget install fails:**

1. Download from official site: https://www.passmark.com/osfmount/
2. Run the installer and follow prompts
3. Add OSFMount folder to Windows PATH (System Settings → Environment Variables)
4. Restart PowerShell and try again

### Script asks for admin but closes

Make sure you're NOT right-clicking and selecting "Run as administrator" first. Instead:

```powershell
# Just run it normally - the script auto-elevates
powershell -ExecutionPolicy Bypass -File run-generator.ps1
```

### Paths not found errors

- Use full paths: `C:\Users\YourName\Desktop\PPSA17221` not `~/PPSA17221`
- Don't use quotes unless the path has spaces
- Check path exists in File Explorer first

### Compression seems slow or stuck

- The progress updates every 500MB (expected for large files)
- ~150 MB/s is normal speed (depends on disk I/O)
- Game data doesn't compress well (97%+ ratio typical)
- Don't close the window — let it complete

### "Drive letter in use" error

The script handles this automatically by:
- Detecting phantom OSFMount drives and skipping them
- Using M: drive which is typically available
- Cleaning up OSFMount processes between runs

If you still see this error:
- Close any open file explorer windows pointing to mounted drives
- Run: `taskkill /IM osfmount.exe /F /T` in admin PowerShell
- Try again

## About ZST Format

`ZST` (Zstandard) is a modern lossless compression format designed for strong speed/ratio balance.

How this project uses ZST:

- **Single image method** (recommended): `run-generator.ps1` creates one exFAT image and compresses it
- **Per-file method**: `compress_pkg.py` compresses each file individually with manifest
- `manifest.txt` stores source and destination mapping plus sizes
- `ZSTDecompressionPS5.elf` reads the manifest and restores files in the original folder layout


## Transfer To PS5

Transfer the whole compressed output folder (not only manifest) to PS5 storage or USB.

## Decompress On PS5

Run:

```bash
ZSTDecompressionPS5.elf \
  /mnt/usb0/gamepackage/manifest.txt \
  /mnt/usb0/gamepackage-compressed \
  /data/game/gamepackage-app
```

## Single-File exFAT Package (`.exfat.zst`)

One compressed file instead of thousands of `.zst` files, mountable by ShadowMountPlus.

### Windows — Create exFAT + Compress (Recommended)

**Prerequisites:**
- OSFMount installed: https://www.osforensics.com/tools/mount-disk-images.html
- Python 3 + `zstandard` package
- Administrator Command Prompt

**One Command — Creates Both `.exfat` and `.exfat.zst` Automatically:**

```cmd
make_image_and_compress.bat "<output_name>.exfat" "<source_folder>"
```

**What happens:**
1. Creates exFAT image from source folder
2. Automatically compresses to `.exfat.zst`
3. Done — both files ready

**Manual compression (if you already have `.exfat` file):**

```bash
python compress_image.py <input_name>.exfat <output_name>.exfat.zst
```

### Restore on PS5

FTP the output folder to PS5 storage, then send the payload using any commercially available tool

---

## ShadowMountPlus — Auto-Mount Images on PS5

**ShadowMountPlus** is a background payload for jailbroken PS5 that automatically detects, mounts, and installs game dumps from internal/external storage.

### Download

**Repository:** https://github.com/drakmor/ShadowMountPlus

**Latest Release:** https://github.com/drakmor/ShadowMountPlus/releases

**Download:** Get the latest `shadowmountplus.elf` from [ShadowMountPlus Releases](https://github.com/drakmor/ShadowMountPlus/releases)

### Installation

#### Method 1 — Manual Payload Injection (Port 9021)

Use a payload sender (NetCat GUI, web loader, etc.) to send `shadowmountplus.elf` to port 9021.

1. Send `shadowmountplus.elf`
2. Wait for notification: "ShadowMount+"



### Usage

After installation, ShadowMountPlus automatically scans default paths and mounts images:

**Supported formats:**
- `.exfat` (recommended, exFAT filesystem)
- `.ffpkg` (legacy, UFS filesystem)
- `.ffpfs` (experimental, PFS filesystem)

**Default scan paths:**
- `/data/imgmnt/{exfatmnt,ufsmnt,pfsmnt}` (mounted images)
- `/data/homebrew/`
- `/mnt/usb0-7/`
- `/mnt/ext0-1/`

**Recommended file structure:**

```
/data/imgmnt/exfatmnt/
  <image1>.exfat        ← auto-mounted
  <image2>.exfat
```

### Configuration

Optional: create `/data/shadowmount/config.ini` for runtime settings:

```ini
debug=1
mount_read_only=1
exfat_backend=lvd
image_rw=<image_filename>
```

**Key options:**
- `debug=1|0` — enable debug logging
- `mount_read_only=1|0` — default mount mode
- `exfat_backend=lvd|md` — filesystem backend
- `image_rw=<filename>` — force read-write for specific image
- `scanpath=<path>` — custom scan directory

See [ShadowMountPlus README](https://github.com/drakmor/ShadowMountPlus/blob/main/README.md) for full documentation.

### Troubleshooting

**Image not mounting:**
- Check `/data/shadowmount/debug.log` for errors
- Verify image location is in scan path
- Ensure image filename matches supported format (`.exfat`, `.ffpkg`, `.ffpfs`)
- Verify `sce_sys/param.json` exists at image root (no extra folder nesting)

**Game not starting after mount:**
- Remove game from system settings and re-add
- Check game registration in notification log
- Try moving image to different USB port or storage location

---

## Acknowledgements

**exFAT Image Generation:**
- **OSFMount**  Passmark Software (https://www.osforensics.com/tools/mount-disk-images.html)  commercial tool for creating and mounting disk images

**PS5 Payloads & Tools:**
- **ShadowMountPlus**  [drakmor](https://github.com/drakmor)  automated image auto-mounter for PS5 (https://github.com/drakmor/ShadowMountPlus)
  - Originally based on [ShadowMount](https://github.com/VoidWhisper) by [VoidWhisper](https://github.com/VoidWhisper)
 

**Compression & File Handling:**
- **Zstandard (zstd)**  Meta/Facebook (https://facebook.github.io/zstd/)  modern lossless compression
- **zstandard-python**  community Python bindings

**Related Projects:**
- [mkufs2](https://github.com/earthonion/mkufs2) by earthonion  create UFS images mountable by PS5/PS4
- [UFS2Tool](https://github.com/SvenGDK/UFS2Tool)  Windows UFS image builder

**Community & Testing:**
- Thanks to **earthonion** for input and information

**License:**

This project is provided as-is. Use at your own risk. Verify all images work correctly before relying on them.

Warning: Mounting images can cause shutdown issues or data corruption depending on firmware version and setup. Take appropriate precautions.
