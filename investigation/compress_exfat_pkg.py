#!/usr/bin/env python3
"""
compress_exfat_pkg.py - Build or compress one exFAT image to a single .exfat.zst.

Goal:
- Keep existing per-file compressor unchanged.
- Produce one compressed file (GAME.exfat.zst) instead of thousands of .zst files.
- Optionally emit a one-line manifest compatible with ZSTDecompressionPS5.elf.

Usage examples:

1) Compress an already-created image:
   python compress_exfat_pkg.py "D:\\PPSA12345.exfat" "D:\\out"

2) Build image from folder using ShadowMountPlus Windows helper, then compress:
   python compress_exfat_pkg.py "D:\\PPSA12345-app" "D:\\out" ^
     --build-command "make_image.bat \"{image}\" \"{src}\""

3) Linux exfat builder flow example:
   python compress_exfat_pkg.py "/games/PPSA12345-app" "/games/out" \
     --build-command "./mkexfat.sh \"{src}\" \"{image}\""

Notes:
- If <source> is a directory, --build-command is required.
- --build-command supports placeholders: {src} and {image}.
- The source directory must be the game root (eboot.bin/sce_sys at root).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

MANIFEST_NAME = "manifest.txt"


def human(n: int) -> str:
    value = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"


def ensure_zstd() -> "object":
    try:
        import zstandard as zstd
    except ImportError:
        print("ERROR: 'zstandard' module not found.")
        print("Install it with: pip install zstandard")
        sys.exit(1)
    return zstd


def build_exfat_image(src_dir: Path, image_path: Path, build_command: str) -> None:
    if not build_command.strip():
        raise ValueError("--build-command cannot be empty when source is a directory")

    cmd = build_command.format(src=str(src_dir), image=str(image_path))
    print("Running image builder command:")
    print(f"  {cmd}")

    started = time.time()
    completed = subprocess.run(cmd, shell=True)
    elapsed = time.time() - started

    if completed.returncode != 0:
        raise RuntimeError(f"Image builder failed with exit code {completed.returncode}")

    if not image_path.is_file():
        raise FileNotFoundError(
            f"Builder command succeeded but image was not found: {image_path}"
        )

    print(f"Image build completed in {elapsed:.1f}s")


def compress_image(image_path: Path, out_zst: Path, level: int) -> tuple[int, int, float]:
    zstd = ensure_zstd()
    out_zst.parent.mkdir(parents=True, exist_ok=True)

    orig_size = image_path.stat().st_size
    t0 = time.time()

    cctx = zstd.ZstdCompressor(level=level, threads=-1)
    with image_path.open("rb") as fin, out_zst.open("wb") as fout:
        cctx.copy_stream(fin, fout)

    comp_size = out_zst.stat().st_size
    elapsed = time.time() - t0
    return orig_size, comp_size, elapsed


def write_single_manifest(manifest_path: Path, out_zst_name: str, image_name: str, orig: int, comp: int) -> None:
    lines = [
        "# PS5 Decompressor Manifest v1",
        "# Fields: src_rel|dst_rel|original_size|compressed_size",
        "#",
        f"{out_zst_name}|{image_name}|{orig}|{comp}",
    ]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build/compress one exFAT image to a single .exfat.zst package"
    )
    parser.add_argument(
        "source",
        help="Source directory (game root) OR existing .exfat image path",
    )
    parser.add_argument(
        "output_dir",
        help="Output directory for .exfat.zst and optional manifest",
    )
    parser.add_argument(
        "--image-name",
        default=None,
        help="Image filename (default: <source_basename>.exfat)",
    )
    parser.add_argument(
        "--build-command",
        default=None,
        help=(
            "Required when source is a directory. Command template to build the exfat image. "
            "Use {src} and {image} placeholders."
        ),
    )
    parser.add_argument(
        "--level",
        type=int,
        default=3,
        help="zstd compression level 1-22 (default: 3)",
    )
    parser.add_argument(
        "--no-manifest",
        action="store_true",
        help="Do not emit manifest.txt",
    )
    parser.add_argument(
        "--manifest-name",
        default=MANIFEST_NAME,
        help=f"Manifest filename (default: {MANIFEST_NAME})",
    )
    parser.add_argument(
        "--keep-image",
        action="store_true",
        help="Keep the built .exfat image if source is a directory",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.level < 1 or args.level > 22:
        print("ERROR: --level must be between 1 and 22")
        sys.exit(1)

    source = Path(args.source).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.image_name:
        image_name = args.image_name
    else:
        image_name = f"{source.stem}.exfat" if source.is_file() else f"{source.name}.exfat"

    if not image_name.lower().endswith(".exfat"):
        image_name = f"{image_name}.exfat"

    built_image = False
    if source.is_dir():
        build_command = args.build_command
        if not build_command:
            print("ERROR: source is a directory, so --build-command is required.")
            print("Example:")
            print('  --build-command "make_image.bat \\\"{image}\\\" \\\"{src}\\\""')
            sys.exit(1)

        image_path = out_dir / image_name
        if image_path.exists():
            print(f"ERROR: target image already exists: {image_path}")
            print("Use --image-name to change name, or remove existing file.")
            sys.exit(1)

        build_exfat_image(source, image_path, build_command)
        built_image = True

    elif source.is_file():
        image_path = source
        image_name = image_path.name
        if not image_name.lower().endswith(".exfat"):
            print("WARNING: source file does not end with .exfat")
            print(f"Continuing anyway: {image_path}")

    else:
        print(f"ERROR: source does not exist: {source}")
        sys.exit(1)

    out_zst = out_dir / f"{image_name}.zst"
    if out_zst.exists():
        print(f"ERROR: output already exists: {out_zst}")
        sys.exit(1)

    print("-" * 60)
    print(f"Image: {image_path}")
    print(f"Output: {out_zst}")
    print(f"zstd level: {args.level}")
    print("-" * 60)

    original_size, compressed_size, elapsed = compress_image(image_path, out_zst, args.level)
    ratio = compressed_size / original_size if original_size > 0 else 1.0

    print()
    print("=" * 60)
    print(f"Original   : {human(original_size)}  ({original_size} bytes)")
    print(f"Compressed : {human(compressed_size)}  ({compressed_size} bytes)")
    print(f"Ratio      : {ratio:.1%}")
    print(f"Saved      : {human(original_size - compressed_size)}")
    print(f"Time       : {elapsed:.1f}s")
    print(f"File       : {out_zst}")

    if not args.no_manifest:
        manifest_path = out_dir / args.manifest_name
        write_single_manifest(
            manifest_path=manifest_path,
            out_zst_name=out_zst.name,
            image_name=image_name,
            orig=original_size,
            comp=compressed_size,
        )
        print(f"Manifest   : {manifest_path}")
        print()
        print("PS5 restore example (existing decompressor ELF):")
        print(f"  ZSTDecompressionPS5.elf {manifest_path} {out_dir} <dst_base_on_ps5>")
        print("  # this restores one file: <dst_base_on_ps5>/<image_name>")

    print("=" * 60)

    if built_image and not args.keep_image:
        try:
            image_path.unlink()
            print(f"Deleted temporary built image: {image_path}")
        except OSError as exc:
            print(f"WARNING: failed to delete temporary image: {exc}")


if __name__ == "__main__":
    main()
