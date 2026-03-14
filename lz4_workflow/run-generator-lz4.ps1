# LZ4 Image Generator and Compressor for PS5
# Ultra-fast compression with minimal decompression time

param()

# Check if running as admin
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    # Re-run as admin
    $scriptPath = $PSCommandPath
    $args = "-NoExit -ExecutionPolicy Bypass -File `"$scriptPath`""
    Start-Process powershell.exe -Verb RunAs -ArgumentList $args -Wait
    exit
}

# Now running as admin
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  exFAT Image Generator + LZ4 Compression" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for OSFMount
Write-Host "Checking for OSFMount.com..." -ForegroundColor Cyan

$osfmountPaths = @(
    "${env:ProgramFiles}\OSFMount\osfmount.com",
    "${env:ProgramFiles(x86)}\OSFMount\osfmount.com",
    "${env:ProgramFiles}\PassMark\OSFMount\osfmount.com",
    "${env:ProgramFiles(x86)}\PassMark\OSFMount\osfmount.com"
)

$osfmountFound = $false
foreach ($path in $osfmountPaths) {
    if (Test-Path $path) {
        Write-Host "  [+] OSFMount found at: $path" -ForegroundColor Green
        $osfmountFound = $true
        break
    }
}

if (-not $osfmountFound) {
    try {
        $cmd = Get-Command "osfmount.com" -ErrorAction SilentlyContinue
        if ($cmd) {
            Write-Host "  [+] OSFMount found in PATH" -ForegroundColor Green
            $osfmountFound = $true
        }
    } catch {
        $null = $null
    }
}

if (-not $osfmountFound) {
    Write-Host ""
    Write-Host "OSFMount not found. Installing via winget..." -ForegroundColor Yellow
    Write-Host ""
    
    try {
        Write-Host "Running: winget install --exact --quiet PassMark.OSFMount" -ForegroundColor Cyan
        & winget install --exact --quiet PassMark.OSFMount
        Start-Sleep -Seconds 3
        
        if (Test-Path "${env:ProgramFiles}\PassMark\OSFMount\osfmount.com") {
            Write-Host "  [+] OSFMount installed successfully" -ForegroundColor Green
            $osfmountFound = $true
        } elseif (Test-Path "${env:ProgramFiles(x86)}\PassMark\OSFMount\osfmount.com") {
            Write-Host "  [+] OSFMount installed successfully (x86)" -ForegroundColor Green
            $osfmountFound = $true
        }
    } catch {
        Write-Host "  [!] winget install failed" -ForegroundColor Yellow
    }
}

if (-not $osfmountFound) {
    Write-Host ""
    Write-Host "ERROR: OSFMount could not be installed via winget." -ForegroundColor Red
    Write-Host "Please install OSFMount manually from: https://www.passmark.com/osfmount/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check for LZ4 Python support
Write-Host ""
Write-Host "Checking for lz4 Python module..." -ForegroundColor Cyan

try {
    python -c "import lz4.frame; print('OK')" | Out-Null
    Write-Host "  [+] lz4 module found" -ForegroundColor Green
} catch {
    Write-Host "  [!] Installing lz4 module..." -ForegroundColor Yellow
    pip install lz4 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [+] lz4 module installed" -ForegroundColor Green
    } else {
        Write-Host "  [!] Failed to install lz4" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Get input from user
$sourcePath = Read-Host "Enter game package folder (e.g., C:\path\to\PPSA04264)"
$outputPath = Read-Host "Enter output folder for exFAT and .lz4 (e.g., E:\Compressed)"

# Validate paths
if (-not (Test-Path $sourcePath -PathType Container)) {
    Write-Host ""
    Write-Host "ERROR: Source folder not found: $sourcePath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path $outputPath -PathType Container)) {
    Write-Host ""
    Write-Host "ERROR: Output folder not found: $outputPath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Extract package name from path
$packageName = Split-Path -Leaf $sourcePath
$imagePath = Join-Path $outputPath "$packageName.exfat"

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Source:   $sourcePath"
Write-Host "  Output:   $outputPath"
Write-Host "  Image:    $imagePath"
Write-Host ""

# Confirm before proceeding
$confirm = Read-Host "Proceed with generation? (y/n)"
if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

# Clean up old files
Write-Host ""
Write-Host "Cleaning up old files..." -ForegroundColor Cyan
Remove-Item "$imagePath*" -Force -ErrorAction SilentlyContinue | Out-Null
taskkill /IM osfmount.exe /F /T 2>$null | Out-Null
Start-Sleep -Seconds 3

# Get the script directory
$scriptDir = Split-Path -Parent $PSCommandPath

# Run the batch file for image creation
Write-Host ""
Write-Host "Starting exFAT generation..." -ForegroundColor Cyan
Write-Host ""

$batchPath = Join-Path $scriptDir "..\make_image.bat"

if (-not (Test-Path $batchPath)) {
    Write-Host "ERROR: Batch file not found: $batchPath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

& cmd /c "`"$batchPath`" `"$imagePath`" `"$sourcePath`""

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Image creation failed" -ForegroundColor Red
    exit 1
}

# Cleanup OSFMount
Write-Host ""
Write-Host "Cleaning up OSFMount processes..." -ForegroundColor Cyan
timeout /t 2 /nobreak
taskkill /IM osfmount.exe /F /T 2>$null | Out-Null
timeout /t 2 /nobreak

# Compress with LZ4
Write-Host ""
Write-Host "Starting LZ4 compression..." -ForegroundColor Cyan
Write-Host ""

$lz4Script = Join-Path $scriptDir "compress_lz4.py"
python "$lz4Script" "$imagePath" -o "$imagePath.lz4" -l 1

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: LZ4 compression failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Done! Check $outputPath for files:" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  [exFAT]  $packageName.exfat"
Write-Host "  [LZ4]    $packageName.exfat.lz4"
Write-Host ""
Write-Host "PS5 Decompression: ~30 seconds with LZ4DecompressionPS5.elf" -ForegroundColor Yellow
Write-Host ""
