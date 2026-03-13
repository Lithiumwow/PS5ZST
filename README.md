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

## Optional WSL Helper

```bash
wsl bash scripts/pack_zst_manifest_wsl.sh PPSA17221-app PPSA17221-compressed 3
```
