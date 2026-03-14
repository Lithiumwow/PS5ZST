#!/usr/bin/env pwsh
<#
.SYNOPSIS
Complete PS5 exFAT image generation and compression workflow.

.DESCRIPTION
1. Generates exFAT image (using OSFMount if available, otherwise uses mkexfat.py)
2. Compresses to .zst
3. Archives investigation/debug files
#>

param(
    [string]$SourceDir = "PPSA17221-app",
    [string]$OutputImage = "PPSA17221-final.exfat",
    [switch]$UseOSFMount = $false
)

$ErrorActionPreference = "Stop"

Write-Host "======== PS5 exFAT Workflow ========`n" -ForegroundColor Cyan

# ========== STEP 1: Generate exFAT Image ==========
Write-Host "[1] Generating exFAT image..." -ForegroundColor Yellow

if ($UseOSFMount) {
    Write-Host "  Using OSFMount..." -ForegroundColor Cyan
    
    # Find OSFMount executable
    $osfmountPaths = @(
        "C:\Program Files\Passmark\OSFMount\OSFMount.exe",
        "C:\Program Files (x86)\Passmark\OSFMount\OSFMount.exe"
    )
    
    $osfmountExe = $null
    foreach ($path in $osfmountPaths) {
        if (Test-Path $path) {
            $osfmountExe = $path
            Write-Host "  Found OSFMount at: $path" -ForegroundColor Green
            break
        }
    }
    
    if (!$osfmountExe) {
        Write-Host "  ERROR: OSFMount not found. Install it first." -ForegroundColor Red
        Write-Host "  Command: winget install -e --id PassmarkSoftware.OSFMount" -ForegroundColor Yellow
        exit 1
    }
    
    # Use OSFMount to create image
    # OSFMount -target <dir> -f <output.img> [-size <sizeGB>]
    $sizeGB = 2
    Write-Host "  Creating 2GB exFAT image..." -ForegroundColor Cyan
    & $osfmountExe -target "$SourceDir" -f "$OutputImage" -size $sizeGB -label OSFIMG
    
    if (!$?) {
        Write-Host "  ERROR: OSFMount failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✓ Image created: $OutputImage" -ForegroundColor Green
} else {
    Write-Host "  Using mkexfat.py..." -ForegroundColor Cyan
    python mkexfat.py "$SourceDir" "$OutputImage" --size 2 --label OSFIMG 2>&1 | Select-Object -Last 3
    
    if (!$?) {
        Write-Host "  ERROR: mkexfat.py failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✓ Image created: $OutputImage" -ForegroundColor Green
}

# ========== STEP 2: Compress to .zst ==========
Write-Host "`n[2] Compressing to .zst..." -ForegroundColor Yellow

$compressedImage = "$OutputImage.zst"

if (Test-Path $compressedImage) {
    Remove-Item $compressedImage -Force
}

python -c "
import zstandard as z
from pathlib import Path

img_path = Path('$OutputImage')
zst_path = Path('$compressedImage')

print(f'  Reading {img_path.stat().st_size / (1<<30):.2f} GB...')
data = img_path.read_bytes()

print(f'  Compressing with level 3...')
compressed = z.ZstdCompressor(level=3).compress(data)

zst_path.write_bytes(compressed)
ratio = 100 * len(compressed) / len(data)
print(f'  ✓ Compressed: {len(compressed) / (1<<30):.2f} GB ({ratio:.1f}%)')
"

if (!$?) {
    Write-Host "  ERROR: Compression failed" -ForegroundColor Red
    exit 1
}

# ========== STEP 3: Archive Investigation Files ==========
Write-Host "`n[3] Archiving investigation files..." -ForegroundColor Yellow

$invDir = "investigation"
if (!(Test-Path $invDir)) {
    New-Item -ItemType Directory -Path $invDir | Out-Null
}

# Patterns to move
$patterns = @(
    "test-*.exfat",
    "test-*.exfat.zst",
    "*debug*.py",
    "*debug*.exfat",
    "check_*.py",
    "compare_*.py",
    "dump_*.py",
    "extract_*.py",
    "trace_*.py",
    "verify_*.py",
    "analyze_*.py",
    "map_clusters.py",
    "final_verification.py"
)

$movedCount = 0
foreach ($pattern in $patterns) {
    Get-ChildItem -Path "." -Filter $pattern -ErrorAction SilentlyContinue | ForEach-Object {
        Move-Item -Path $_.FullName -Destination "$invDir\" -Force
        $movedCount++
        Write-Host "  → $($_.Name)" -ForegroundColor DarkGray
    }
}

Write-Host "  ✓ Moved $movedCount files to $invDir\" -ForegroundColor Green

# ========== SUMMARY ==========
Write-Host "`n======== Summary ========" -ForegroundColor Cyan
Write-Host "✓ exFAT image:    $OutputImage"
Write-Host "✓ Compressed:     $compressedImage"
Write-Host "✓ Investigation:  $invDir\"
Write-Host "`nReady for PS5 transfer!" -ForegroundColor Green
