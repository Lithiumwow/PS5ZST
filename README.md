# PSVZST

ZST workflow for PS5 game folder transfer and restore.

This project uses:
- PC-side compressor to create `.zst` files plus a `manifest.txt`
- PS5-side decompressor ELF to restore files to target path

## Included Files

- `compress_pkg.py` : compresses a game folder into `.zst` files and manifest
- `compress_image.py` : compresses a single `.exfat` image to `.exfat.zst`
- `make_image_and_compress.bat` : creates `.exfat` and automatically compresses to `.zst` (Windows, requires Admin)
- `New-OsfExfatImage.ps1` : PowerShell backend for `make_image_and_compress.bat`
- `ZSTDecompressionPS5.elf` : ready PS5 decompressor ELF

## Requirements (PC)

- Python 3
- Python package: `zstandard`

Install:

```bash
pip install zstandard
```

## Create ZST Package


```bash
python compress_pkg.py <game-folder> <output-folder> --level 3
```

Example:

```bash
python compress_pkg.py <src_folder> <output_folder> --level 3
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

## About ZST Format

`ZST` (Zstandard) is a modern lossless compression format designed for strong speed/ratio balance.


How this project uses ZST:

- `compress_pkg.py` compresses each file into a matching `.zst` file.
- `manifest.txt` stores source and destination mapping plus sizes.
- `ZSTDecompressionPS5.elf` reads the manifest and restores files in the original folder layout.


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
