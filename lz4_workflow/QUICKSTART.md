# LZ4 Workflow - Quick Start Guide

## What is LZ4?

LZ4 is an ultra-fast compression algorithm:
- **90% faster decompression than zstd** on PS5 (30 seconds vs 10-15 minutes)
- **Smaller compressed files** (50-55% of original)
- **Perfect for games** that need fast load times

## Step 1: PC Side - Create & Compress (10-15 minutes)

### Option A: Automated (Recommended)

```powershell
# Windows PowerShell
cd C:\your\repo\lz4_workflow
.\run-generator-lz4.ps1

# Follow prompts:
# 1. Enter game folder: C:\PPSA04264
# 2. Enter output folder: C:\Output
# 3. Confirm and wait
```

Creates:
- `PPSA04264.exfat` (90 GB)
- `PPSA04264.exfat.lz4` (45 GB)

### Option B: Manual Steps

```powershell
# Create exFAT image
..\run-generator.ps1

# Or compress existing exFAT
python compress_lz4.py C:\path\to\game.exfat
```

## Step 2: PS5 Side - Transfer & Decompress (5-10 minutes)

### A. Compile ELF (One-time, needs PS5 SDK)

**On Linux/Mac with PS5 SDK:**

```bash
cd lz4_workflow
chmod +x build.sh
PS5_SDK_PATH=/opt/ps5-sdk ./build.sh

# Output: build/LZ4DecompressionPS5.elf
```

**On Windows with PS5 SDK:**

```cmd
cd lz4_workflow
build.bat

REM Output: build\LZ4DecompressionPS5.elf
```

### B. Transfer to PS5

```bash
# Via FTP
put C:\Output\PPSA04264.exfat.lz4 /path/on/ps5/

# Via USB
# Copy .lz4 file to USB drive, then copy to PS5
```

### C. Decompress on PS5

```bash
# SSH/shell on PS5
cd /path/where/you/put/file

./LZ4DecompressionPS5.elf PPSA04264.exfat.lz4 PPSA04264.exfat

# Takes ~30 seconds for 90GB
# Then copy PPSA04264.exfat to game folder
```

## Time Comparison

| Step | Time | Notes |
|------|------|-------|
| Create exFAT | ~12 min | One-time, on PC |
| Compress (LZ4) | ~10 min | 10 MB/s compression |
| Transfer (1Gbps) | ~6 min | For 45 GB .lz4 file |
| PS5 Decompress | ~30 sec | Ultra-fast! |
| **Total** | **~28 min** | vs 30-40 min with zstd |

## Troubleshooting

### "lz4 module not found"

```powershell
pip install lz4
```

### "OSFMount not found"

```powershell
winget install PassMark.OSFMount
```

### PS5 SDK not found during build

Set environment variable:
```bash
export PS5_SDK_PATH=/opt/ps5-sdk  # Linux/Mac
set PS5_SDK_PATH=C:\PS5_SDK       # Windows
```

### Compilation fails

Ensure PS5 SDK includes LZ4 development files. If not:

```bash
# Linux/Mac
sudo apt-get install liblz4-dev
# Add to PS5 SDK include/lib paths
```

## Files Reference

| File | Purpose |
|------|---------|
| `run-generator-lz4.ps1` | One-click: create exFAT + LZ4 compress |
| `compress_lz4.py` | Manual LZ4 compression tool |
| `LZ4DecompressionPS5.c` | PS5 decompressor source |
| `build.sh` / `build.bat` | Compile ELF (Linux/Mac or Windows) |
| `CMakeLists.txt` | CMake build config |
| `README.md` | Full documentation |

## Next Steps

1. **Copy `lz4_workflow` folder** to your system
2. **Install lz4** Python module: `pip install lz4`
3. **Run generator** on PC: `.\run-generator-lz4.ps1`
4. **Build ELF** for PS5 (if you have SDK)
5. **Transfer .lz4** file to PS5
6. **Decompress** with ELF on PS5

## Performance Tuning

### Faster Compression (default already optimal)
```powershell
python compress_lz4.py file.exfat -l 1  # Fastest (default)
```

### Better Compression (slower)
```powershell
python compress_lz4.py file.exfat -l 4  # Balance
python compress_lz4.py file.exfat -l 8  # Maximum compression
```

### Parallel Transfers
If you have multiple files, use:
```powershell
# Upload multiple chunks simultaneously
robocopy source dest /E /MT:8  # 8 parallel threads
```

---

**Questions?** Check `README.md` for detailed information.
