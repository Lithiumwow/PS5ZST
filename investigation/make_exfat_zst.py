#!/usr/bin/env python3
"""
make_exfat_zst.py  -  Build an exFAT image from a game folder and compress it
                      to a single .exfat.zst file ready for FTP to PS5.

Requires NO external tools.  Pure-Python exFAT writer (mkexfat.py) does
everything in userspace — no admin rights, no OSFMount, no format.com.

Internally does:
  1. Build a .exfat image with mkexfat.py  (pure Python, any OS)
  2. Compress to .exfat.zst  (zstd, one file)
  3. Write manifest.txt       (for ZSTDecompressionPS5.elf)
  4. Clean up temp .exfat     (unless --keep-image)

Requirements:
  pip install zstandard

Usage:
  python make_exfat_zst.py <game_folder> <output>.exfat.zst [--level N]

Example:
  python make_exfat_zst.py PPSA12345-app PPSA12345.exfat.zst --level 3
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

MANIFEST_NAME = "manifest.txt"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def human(n: int) -> str:
    value = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"


def ensure_zstd():
    try:
        import zstandard as zstd
        return zstd
    except ImportError:
        print("ERROR: 'zstandard' module not found.")
        print("Install it with:  pip install zstandard")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Compress
# ---------------------------------------------------------------------------

def compress_image(image: Path, out_zst: Path, level: int) -> tuple[int, int, float]:
    zstd = ensure_zstd()
    orig = image.stat().st_size
    t0 = time.time()
    cctx = zstd.ZstdCompressor(level=level, threads=-1)
    with image.open("rb") as fin, out_zst.open("wb") as fout:
        cctx.copy_stream(fin, fout)
    comp = out_zst.stat().st_size
    elapsed = time.time() - t0
    return orig, comp, elapsed


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def write_manifest(path: Path, zst_name: str, image_name: str,
                   orig: int, comp: int) -> None:
    lines = [
        "# PS5 Decompressor Manifest v1",
        "# Fields: src_rel|dst_rel|original_size|compressed_size",
        "#",
        f"{zst_name}|{image_name}|{orig}|{comp}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build an exFAT image from a game folder and compress it "
            "to a single .exfat.zst file for PS5 FTP transfer. "
            "No external tools needed."
        )
    )
    parser.add_argument(
        "game_folder",
        help="Game source directory (eboot.bin must be at its root)."
    )
    parser.add_argument(
        "output_file",
        help="Output path for the .exfat.zst file (e.g. PPSA12345.exfat.zst)"
    )
    parser.add_argument(
        "--level", type=int, default=3,
        help="zstd compression level 1-22 (default: 3)"
    )
    parser.add_argument(
        "--keep-image", action="store_true",
        help="Keep the intermediate .exfat image after compression"
    )
    parser.add_argument(
        "--no-manifest", action="store_true",
        help="Skip writing manifest.txt"
    )
    parser.add_argument(
        "--cluster", type=int, default=None,
        help="Override cluster size in bytes (default: auto, 32768 or 65536)"
    )
    parser.add_argument(
        "--label", default="EXFAT",
        help="exFAT volume label (default: EXFAT)"
    )
    args = parser.parse_args()

    # --- Validate inputs -------------------------------------------------------
    if args.level < 1 or args.level > 22:
        print("ERROR: --level must be between 1 and 22")
        sys.exit(1)

    src = Path(args.game_folder).resolve()
    out_zst = Path(args.output_file).resolve()

    if not src.is_dir():
        print(f"ERROR: game_folder not found: {src}")
        sys.exit(1)

    if not (src / "eboot.bin").is_file():
        print(f"ERROR: eboot.bin not found in: {src}")
        print("The game_folder must be the game root (eboot.bin at top level).")
        sys.exit(1)

    if not str(out_zst).lower().endswith(".exfat.zst"):
        print(f"WARNING: output_file does not end with .exfat.zst: {out_zst.name}")

    out_zst.parent.mkdir(parents=True, exist_ok=True)

    if out_zst.exists():
        print(f"ERROR: output file already exists: {out_zst}")
        sys.exit(1)

    # Derive the intermediate image name from the output filename
    image_name = out_zst.name
    if image_name.lower().endswith(".zst"):
        image_name = image_name[:-4]
    temp_image = out_zst.parent / image_name

    if temp_image.exists():
        print(f"ERROR: temp image path already exists: {temp_image}")
        print("Remove it manually or choose a different output filename.")
        sys.exit(1)

    # --- Import pure-Python exFAT writer ---------------------------------------
    try:
        from mkexfat import ExFATWriter
    except ImportError:
        print("ERROR: mkexfat.py not found.  Place it in the same directory as this script.")
        sys.exit(1)

    # --- Build exFAT image (pure Python, no external tools) --------------------
    print(f"[1/3] Building exFAT image (pure Python)...")
    try:
        writer = ExFATWriter(temp_image, src,
                             label=args.label,
                             cluster_size=args.cluster)
        writer.build()
    except Exception as exc:
        print(f"\nERROR: Image build failed: {exc}")
        if temp_image.exists():
            temp_image.unlink()
        sys.exit(1)

    print(f"      Size   : {human(temp_image.stat().st_size)}")

    # --- Compress --------------------------------------------------------------
    print(f"[2/3] Compressing {image_name} at zstd level {args.level}...")
    try:
        orig, comp, elapsed = compress_image(temp_image, out_zst, args.level)
    except Exception as exc:
        print(f"\nERROR: Compression failed: {exc}")
        sys.exit(1)

    ratio = comp / orig if orig > 0 else 1.0

    # --- Manifest --------------------------------------------------------------
    if not args.no_manifest:
        manifest_path = out_zst.parent / MANIFEST_NAME
        write_manifest(manifest_path, out_zst.name, image_name, orig, comp)

    # --- Cleanup ---------------------------------------------------------------
    if not args.keep_image:
        try:
            temp_image.unlink()
        except OSError as exc:
            print(f"WARNING: could not delete temp image: {exc}")

    # --- Report ----------------------------------------------------------------
    print()
    print("[3/3] Done.")
    print("=" * 60)
    print(f"  Image (raw)  : {human(orig)}")
    print(f"  Compressed   : {human(comp)}  ({ratio:.1%})")
    print(f"  Saved        : {human(orig - comp)}")
    print(f"  Time         : {elapsed:.1f}s")
    print(f"  Output       : {out_zst}")
    if not args.no_manifest:
        print(f"  Manifest     : {out_zst.parent / MANIFEST_NAME}")
    print("=" * 60)
    print()
    print("FTP the output folder to your PS5, then run:")
    print(f"  ZSTDecompressionPS5.elf manifest.txt <src_dir> <dst_dir>")
    print(f"  # Restores {image_name} to <dst_dir>/")
    print(f"  # ShadowMountPlus will auto-mount it from there.")


if __name__ == "__main__":
    main()
