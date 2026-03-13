# PSVZST

ZST workflow for PS5 game folder transfer and restore.

This project uses:
- PC-side compressor to create `.zst` files plus a `manifest.txt`
- PS5-side decompressor ELF to restore files to target path

## Included Files

- `compress_pkg.py` : compresses a game folder into `.zst` files and manifest
- `decompress_ps5.c` : source for PS5 decompressor
- `ZSTDecompressionPS5.elf` : ready PS5 decompressor ELF
- `scripts/pack_zst_manifest_wsl.sh` : helper script to run compressor from WSL

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

## Optional WSL Helper

```bash
wsl bash scripts/pack_zst_manifest_wsl.sh PPSA17221-app PPSA17221-compressed 3
```
