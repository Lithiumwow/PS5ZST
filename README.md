# PSVZST

ZST workflow for PS5 game folder transfer and restore.

This project uses:
- PC-side compressor to create `.zst` files plus a `manifest.txt`
- PS5-side decompressor ELF to restore files to target path

## Included Files

- `compress_pkg.py` : compresses a game folder into `.zst` files and manifest
- `compress_image.py` : compresses a single `.exfat` image to `.exfat.zst`
- `make_image.bat` : creates `.exfat` image using OSFMount (Windows, requires Admin)
- `make_image_and_compress.bat` : creates `.exfat` and automatically compresses to `.zst` (Windows, requires Admin)
- `New-OsfExfatImage.ps1` : PowerShell backend for `make_image.bat`
- `ZSTDecompressionPS5.elf` : ready PS5 decompressor ELF
- `shadowmountplus.elf` : PS5 auto-mounter payload (optional, for mounting images directly)

## Requirements (PC)

- Python 3
- Python package: `zstandard`

Install:

```bash
pip install zstandard
```

## Create ZST Package

From workspace root:

```bash
python compress_pkg.py <GAME_FOLDER> <OUTPUT_FOLDER> --level 3
```

Example:

```bash
python compress_pkg.py PPSA17221-app PPSA17221-compressed --level 3
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

## Average Compression And Transfer Savings

Real run example from this project (`PPSA17221-app`, level `3`):

- Original size: `1,104,719,782` bytes
- Compressed size: `688,237,588` bytes
- Compression ratio: `62.3%` (compressed size as a percent of original)
- Transfer savings: `37.7%`

What this means in practice:

- You transfer about `0.62x` of the original data size.
- If your network transfer is the main bottleneck, expected transfer time is around `1.6x` faster than uncompressed copy.

Notes:

- Results vary by game content and file types.
- Already-compressed assets may not shrink much.
- Some tiny files can grow slightly due to compression framing overhead.

## About ZST Format

`ZST` (Zstandard) is a modern lossless compression format designed for strong speed/ratio balance.

Key points:

- Lossless: original bytes are restored exactly.
- Very fast decompression: good for restore workflows.
- Tunable levels: lower levels are faster to compress, higher levels usually produce smaller output.
- Stream/frame format: ZST compresses byte streams, not folder trees by itself.

How this project uses ZST:

- `compress_pkg.py` compresses each file into a matching `.zst` file.
- `manifest.txt` stores source and destination mapping plus sizes.
- `ZSTDecompressionPS5.elf` reads the manifest and restores files in the original folder layout.

Why this design is used:

- Reliable path reconstruction on PS5.
- Easy progress tracking and failure visibility per file.
- No dependency on archive extraction tools.

## Transfer To PS5

Transfer the whole compressed output folder (not only manifest) to PS5 storage or USB.

Example source on PS5:
- `/mnt/usb0/PPSA17221-compressed`

## Decompress On PS5

Run:

```bash
ZSTDecompressionPS5.elf <manifest.txt> <src_base> <dst_base>
```

Example:

```bash
ZSTDecompressionPS5.elf \
  /mnt/usb0/PPSA17221-compressed/manifest.txt \
  /mnt/usb0/PPSA17221-compressed \
  /data/game/PPSA17221-app
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
make_image_and_compress.bat "PPSA12345-osfmount.exfat" "PPSA12345-app"
```

**What happens:**
1. Creates 2GB `.exfat` image from source folder
2. Automatically compresses to `.exfat.zst` (~37% of original)
3. Done — both files ready

**Output files:**
- `PPSA12345-osfmount.exfat` (1.7 GB)
- `PPSA12345-osfmount.exfat.zst` (0.6 GB) — ready to transfer

**Manual compression (if you already have `.exfat` file):**

```bash
python compress_image.py PPSA12345-osfmount.exfat PPSA12345-osfmount.exfat.zst
```

### Pure Python — One Command (Option A)

No OSFMount, no admin rights required. Uses built-in exFAT writer.

`make_exfat_zst.py` uses the built-in pure-Python writer (`mkexfat.py`), then compresses and writes manifest.

### Restore on PS5

FTP the output folder to PS5 storage, then run:

```bash
ZSTDecompressionPS5.elf manifest.txt <src_dir_on_ps5> <dst_dir_on_ps5>
# Restores PPSA12345.exfat to <dst_dir_on_ps5>/
# ShadowMountPlus will auto-mount it from there.
```

---

## ShadowMountPlus — Auto-Mount Images on PS5

**ShadowMountPlus** is a background payload for jailbroken PS5 that automatically detects, mounts, and installs game dumps from internal/external storage.

### Download

**Repository:** https://github.com/drakmor/ShadowMountPlus

**Latest Release:** https://github.com/drakmor/ShadowMountPlus/releases

**Download:** `shadowmountplus.elf`

### Installation

#### Method 1 — Manual Payload Injection (Port 9021)

Use a payload sender (NetCat GUI, web loader, etc.) to send `shadowmountplus.elf` to port 9021.

1. Send `shadowmountplus.elf`
2. Wait for notification: "ShadowMount+"

#### Method 2 — AutoLoader (Recommended)

Add to `autoload.txt` for plk-autoloader to start on every boot:

```
shadowmountplus.elf
!3000
kstuff.elf
```

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
  PPSA12345-game.exfat      ← auto-mounted
  PPSA54321-game.exfat
```

### Configuration

Optional: create `/data/shadowmount/config.ini` for runtime settings:

```ini
debug=1
mount_read_only=1
exfat_backend=lvd
image_rw=PPSA12345-my-game.exfat
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
  - Originally based on ShadowMount by VoidWhisper
  - Contributors: EchoStretch (kstuff-toggle), BestPig (BackPort), and the PS5 R&D community

**Compression & File Handling:**
- **Zstandard (zstd)**  Meta/Facebook (https://facebook.github.io/zstd/)  modern lossless compression
- **zstandard-python**  community Python bindings

**Related Projects:**
- [mkufs2](https://github.com/earthonion/mkufs2) by earthonion  create UFS images mountable by PS5/PS4
- [UFS2Tool](https://github.com/SvenGDK/UFS2Tool)  Windows UFS image builder

**Community & Testing:**
- Thanks to **earthonion** for input and information
- Thanks to **LightningMods** and the active PS5 modding community

**License:**

This project is provided as-is. Use at your own risk. Verify all images work correctly before relying on them.

Warning: Mounting images can cause shutdown issues or data corruption depending on firmware version and setup. Take appropriate precautions.
