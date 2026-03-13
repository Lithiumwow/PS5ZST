#!/usr/bin/env python3
"""
compress_pkg.py  -  Compress a PS5 game folder for FTP-then-decompress workflow

PC side of the workflow:
  1. Run this script to compress the game folder
  2. FTP the output folder to your PS5 (USB drive or internal staging area)
  3. Run decompress_ps5.elf on the PS5 to restore files to destination

Usage:
  python compress_pkg.py <game_folder> <output_folder> [--level N]

  game_folder   : source game directory (e.g. PPSA11193-app)
  output_folder : where compressed files and manifest are written
  --level N     : zstd compression level 1-22 (default: 3, fast + decent ratio)
                  Use 1 for fastest (large files like .cas), 9+ for better ratio

Requires:
  pip install zstandard

Example:
  python compress_pkg.py "D:\\PPSA11193-app" "D:\\PPSA11193-compressed" --level 3
"""

import os
import sys
import time
import argparse

# ---------------------------------------------------------------------------
# Extensions that are already compressed – store at level 1 to avoid wasting
# CPU time trying to re-compress incompressible data.
# ---------------------------------------------------------------------------
ALREADY_COMPRESSED_EXTS = {
    '.cas',   # Frostbite engine bundles (NHL, FIFA, etc.)
    '.bik', '.bk2',   # Bink video
    '.ogg', '.opus', '.mp3', '.aac', '.at9',  # audio
    '.png', '.jpg', '.jpeg', '.dds',          # images (DDS often compressed)
    '.zip', '.gz', '.lz4', '.lzma', '.zst',   # already compressed
}

MANIFEST_NAME = "manifest.txt"

def human(n):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def compress_folder(src_root, out_root, level=3):
    try:
        import zstandard as zstd
    except ImportError:
        print("ERROR: 'zstandard' module not found.")
        print("  Install it with:  pip install zstandard")
        sys.exit(1)

    src_root = os.path.abspath(src_root)
    out_root = os.path.abspath(out_root)
    os.makedirs(out_root, exist_ok=True)

    # Collect all files
    all_files = []
    for dirpath, dirnames, filenames in os.walk(src_root):
        dirnames.sort()   # deterministic order
        for fname in sorted(filenames):
            src_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(src_path, src_root).replace(os.sep, '/')
            all_files.append((src_path, rel_path))

    total = len(all_files)
    print(f"Found {total} files in {src_root}")
    print(f"Output: {out_root}")
    print(f"Default compression level: {level}")
    print("-" * 60)

    manifest_lines = [
        "# PS5 Decompressor Manifest v1",
        "# Fields: src_rel|dst_rel|original_size|compressed_size",
        "#",
    ]

    total_orig = 0
    total_comp = 0
    t_start = time.time()

    for i, (src_path, rel_path) in enumerate(all_files):
        out_rel  = rel_path + '.zst'
        out_path = os.path.join(out_root, out_rel.replace('/', os.sep))
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        orig_size = os.path.getsize(src_path)

        # Choose level: already-compressed files → level 1 (just store)
        ext = os.path.splitext(src_path)[1].lower()
        use_level = 1 if ext in ALREADY_COMPRESSED_EXTS else level

        t0 = time.time()
        cctx = zstd.ZstdCompressor(level=use_level, threads=-1)
        with open(src_path, 'rb') as fin, open(out_path, 'wb') as fout:
            cctx.copy_stream(fin, fout)

        comp_size = os.path.getsize(out_path)
        elapsed   = time.time() - t0
        ratio     = comp_size / orig_size if orig_size > 0 else 1.0

        total_orig += orig_size
        total_comp += comp_size

        # Progress line
        bar_done = int(40 * (i + 1) / total)
        bar = '#' * bar_done + '-' * (40 - bar_done)
        print(f"[{bar}] {i+1}/{total}  {rel_path}")
        print(f"   {human(orig_size)} -> {human(comp_size)}  ({ratio:.1%})  lvl={use_level}  {elapsed:.1f}s")

        # Manifest entry: src_rel|dst_rel|orig_size|comp_size
        manifest_lines.append(f"{out_rel}|{rel_path}|{orig_size}|{comp_size}")

    # Write manifest
    manifest_path = os.path.join(out_root, MANIFEST_NAME)
    with open(manifest_path, 'w', newline='\n') as f:
        f.write('\n'.join(manifest_lines) + '\n')

    elapsed_total = time.time() - t_start
    ratio_total   = total_comp / total_orig if total_orig > 0 else 1.0

    print()
    print("=" * 60)
    print(f"  Files    : {total}")
    print(f"  Original : {human(total_orig)}  ({total_orig} bytes)")
    print(f"  Compressed: {human(total_comp)}  ({total_comp} bytes)")
    print(f"  Ratio    : {ratio_total:.1%}")
    print(f"  Saved    : {human(total_orig - total_comp)}")
    print(f"  Time     : {elapsed_total:.0f}s")
    print(f"  Manifest : {manifest_path}")
    print("=" * 60)
    print()
    print("Next step: FTP the output folder to your PS5, then run:")
    print("  decompress_ps5.elf <manifest.txt> <src_base_on_ps5> <dst_base_on_ps5>")


def main():
    parser = argparse.ArgumentParser(
        description="Compress PS5 game folder for FTP transfer + PS5-side decompression"
    )
    parser.add_argument("game_folder",   help="Source game folder to compress")
    parser.add_argument("output_folder", help="Destination folder for compressed output")
    parser.add_argument(
        "--level", type=int, default=3,
        help="zstd compression level 1-22 (default: 3). "
             "Already-compressed files (.cas, .png, etc.) are always level 1."
    )
    args = parser.parse_args()

    if not os.path.isdir(args.game_folder):
        print(f"ERROR: game_folder not found: {args.game_folder}")
        sys.exit(1)

    compress_folder(args.game_folder, args.output_folder, args.level)


if __name__ == "__main__":
    main()
