#!/usr/bin/env python3
"""
LZ4 Compression Tool for PS5 exFAT Images
Optimized for fast compression and ultra-fast PS5 decompression
"""

import os
import sys
import argparse
import time
from pathlib import Path

try:
    import lz4.frame
except ImportError:
    print("ERROR: lz4 not installed. Install with: pip install lz4")
    sys.exit(1)


def format_bytes(bytes_val):
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"


def compress_lz4(input_path, output_path, compression_level=1, block_size=65536):
    """
    Compress file using LZ4
    
    Args:
        input_path: Path to input file (exFAT image)
        output_path: Path to output .lz4 file
        compression_level: 1-12 (1=fastest, 12=best compression)
        block_size: Internal block size (default 65536 for large files)
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        return False
    
    file_size = input_path.stat().st_size
    print(f"\n{'='*60}")
    print(f"LZ4 Compression")
    print(f"{'='*60}")
    print(f"Input:  {input_path.name}")
    print(f"Size:   {format_bytes(file_size)}")
    print(f"Output: {output_path.name}")
    print(f"Level:  {compression_level}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    bytes_processed = 0
    
    try:
        # Open with LZ4 frame compression
        with open(input_path, 'rb') as f_in:
            with lz4.frame.open(output_path, 'wb', compression_level=compression_level) as f_out:
                # Process in chunks for progress reporting
                chunk_size = 10 * 1024 * 1024  # 10MB chunks
                chunk_num = 0
                
                while True:
                    chunk = f_in.read(chunk_size)
                    if not chunk:
                        break
                    
                    f_out.write(chunk)
                    bytes_processed += len(chunk)
                    chunk_num += 1
                    
                    # Progress update every 50MB
                    if chunk_num % 5 == 0:
                        percent = (bytes_processed / file_size) * 100
                        elapsed = time.time() - start_time
                        rate = bytes_processed / (1024 * 1024 * elapsed) if elapsed > 0 else 0
                        print(f"  {percent:5.1f}% | {format_bytes(bytes_processed):>10} | {rate:6.1f} MB/s", end='\r')
        
        elapsed = time.time() - start_time
        output_size = output_path.stat().st_size
        compression_ratio = (output_size / file_size) * 100
        rate = file_size / (1024 * 1024 * elapsed) if elapsed > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"Compression Complete!")
        print(f"{'='*60}")
        print(f"Input Size:  {format_bytes(file_size)}")
        print(f"Output Size: {format_bytes(output_size)}")
        print(f"Ratio:       {compression_ratio:.1f}%")
        print(f"Time:        {elapsed:.1f}s")
        print(f"Speed:       {rate:.1f} MB/s")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\nERROR during compression: {e}")
        if output_path.exists():
            output_path.unlink()
        return False


def decompress_lz4(input_path, output_path):
    """Decompress LZ4 file (testing/verification only)"""
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        return False
    
    file_size = input_path.stat().st_size
    print(f"\nDecompressing: {input_path.name}")
    print(f"Size: {format_bytes(file_size)}\n")
    
    start_time = time.time()
    
    try:
        with lz4.frame.open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                chunk_size = 10 * 1024 * 1024
                while True:
                    chunk = f_in.read(chunk_size)
                    if not chunk:
                        break
                    f_out.write(chunk)
        
        elapsed = time.time() - start_time
        output_size = output_path.stat().st_size
        rate = output_size / (1024 * 1024 * elapsed) if elapsed > 0 else 0
        
        print(f"Decompression Complete!")
        print(f"Output Size: {format_bytes(output_size)}")
        print(f"Time:        {elapsed:.1f}s")
        print(f"Speed:       {rate:.1f} MB/s\n")
        
        return True
        
    except Exception as e:
        print(f"ERROR during decompression: {e}")
        if output_path.exists():
            output_path.unlink()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='LZ4 Compression Tool for PS5 exFAT Images'
    )
    parser.add_argument('input', help='Input file path')
    parser.add_argument('-o', '--output', help='Output file path (default: input.lz4)')
    parser.add_argument('-d', '--decompress', action='store_true', help='Decompress instead of compress')
    parser.add_argument('-l', '--level', type=int, default=1, help='Compression level 1-12 (default: 1, fastest)')
    parser.add_argument('--block-size', type=int, default=65536, help='LZ4 block size')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if not args.output:
        if args.decompress:
            args.output = str(input_path).replace('.lz4', '')
        else:
            args.output = str(input_path) + '.lz4'
    
    if args.decompress:
        success = decompress_lz4(args.input, args.output)
    else:
        success = compress_lz4(args.input, args.output, args.level, args.block_size)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
