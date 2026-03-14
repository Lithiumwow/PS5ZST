#!/bin/bash
# LZ4 Decompression ELF Build Script for PS5
# Automatic compilation with PS5 SDK

set -e

echo "========================================"
echo "  LZ4 Decompression ELF Builder for PS5"
echo "========================================"
echo ""

# Check for PS5 SDK
if [ -z "$PS5_SDK_PATH" ]; then
    if [ -d "/opt/ps5-sdk" ]; then
        PS5_SDK_PATH="/opt/ps5-sdk"
    else
        echo "ERROR: PS5 SDK not found!"
        echo "Set PS5_SDK_PATH environment variable or install SDK to /opt/ps5-sdk"
        exit 1
    fi
fi

echo "PS5 SDK Path: $PS5_SDK_PATH"

# Check for compiler
if [ ! -f "$PS5_SDK_PATH/bin/x86_64-scei-ps5-gcc" ]; then
    echo "ERROR: GCC compiler not found at: $PS5_SDK_PATH/bin/x86_64-scei-ps5-gcc"
    exit 1
fi

# Check for LZ4 headers
if [ ! -f "$PS5_SDK_PATH/include/lz4.h" ]; then
    echo "ERROR: LZ4 headers not found in SDK"
    echo "Ensure liblz4-dev is installed in PS5 SDK"
    exit 1
fi

echo "Compiler: $PS5_SDK_PATH/bin/x86_64-scei-ps5-gcc"
echo ""

# Create output directory
mkdir -p build
cd build

echo "Compiling LZ4 Decompression ELF..."
echo ""

# Compile with optimizations
"$PS5_SDK_PATH/bin/x86_64-scei-ps5-gcc" \
    -O3 -march=native -flto \
    -I"$PS5_SDK_PATH/include" \
    -L"$PS5_SDK_PATH/lib" \
    -o LZ4DecompressionPS5.elf \
    ../LZ4DecompressionPS5.c \
    -llz4

echo ""
echo "========================================"
echo "Build Successful!"
echo "========================================"
echo ""
echo "Output: build/LZ4DecompressionPS5.elf"
echo ""
echo "Usage on PS5:"
echo "  ./LZ4DecompressionPS5.elf <input.lz4> <output>"
echo ""
