# Create exFAT Image from Any Folder Location
# Usage: .\Create-ExfatImage.ps1
# Requires: Administrator privileges, OSFMount installed, Python with zstandard

param(
    [string]$SourceFolder = "",
    [string]$OutputFolder = ""
)

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "Please right-click and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# If parameters not provided, prompt for them
if (-not $SourceFolder) {
    Write-Host "`n=== exFAT Image Creator ===" -ForegroundColor Cyan
    Write-Host "Step 1: Select Game Folder" -ForegroundColor Yellow
    $SourceFolder = Read-Host "Enter full path to game folder (e.g., D:\Games\PPSA04264)"
}

# Remove quotes if user included them
$SourceFolder = $SourceFolder -replace '^["'']|["'']$'

if (-not $OutputFolder) {
    Write-Host "`nStep 2: Select Output Folder" -ForegroundColor Yellow
    $OutputFolder = Read-Host "Enter full path for output folder (e.g., E:\Compressed)"
}

# Remove quotes if user included them
$OutputFolder = $OutputFolder -replace '^["'']|["'']$'

# Validate source folder exists
if (-not (Test-Path $SourceFolder -PathType Container)) {
    Write-Host "ERROR: Source folder '$SourceFolder' not found!" -ForegroundColor Red
    exit 1
}

# Create output folder if it doesn't exist
if (-not (Test-Path $OutputFolder -PathType Container)) {
    Write-Host "Creating output folder..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $OutputFolder -Force | Out-Null
}

# Calculate source folder size
Write-Host "`nCalculating folder size..." -ForegroundColor Cyan
$folderSize = (Get-ChildItem $SourceFolder -Recurse | Measure-Object -Sum Length).Sum
$folderSizeGB = [math]::Round($folderSize / 1GB, 2)
Write-Host "Source folder size: $folderSizeGB GB" -ForegroundColor Green

# Add 20% overhead for exFAT filesystem
$imageSizeMB = [math]::Ceiling(($folderSizeGB * 1.2) * 1024)
$imageSizeGB = [math]::Round($imageSizeMB / 1024, 2)

Write-Host "Creating exFAT image of $imageSizeGB GB..." -ForegroundColor Cyan

# Get base name for image file
$folderName = Split-Path -Leaf $SourceFolder
$imagePath = Join-Path $OutputFolder "$folderName.exfat"

# Check if image already exists
if (Test-Path $imagePath) {
    Write-Host "WARNING: Image file already exists: $imagePath" -ForegroundColor Yellow
    $overwrite = Read-Host "Overwrite? (Y/N)"
    if ($overwrite -ne "Y" -and $overwrite -ne "y") {
        Write-Host "Cancelled." -ForegroundColor Red
        exit 1
    }
    Remove-Item $imagePath -Force
}

# Create exFAT image using OSFMount
Write-Host "Creating raw image file..." -ForegroundColor Cyan
$osfmountPath = "C:\Program Files\OSFMount\osfmount.com"

if (-not (Test-Path $osfmountPath)) {
    Write-Host "ERROR: OSFMount not found at $osfmountPath" -ForegroundColor Red
    Write-Host "Please install OSFMount from: https://www.osforensics.com/tools/mount-disk-images.html" -ForegroundColor Yellow
    exit 1
}

# Create and mount the image
Write-Host "Mounting image..." -ForegroundColor Cyan
& $osfmountPath -a -t vm -of vmdk -size "$($imageSizeMB)M" -fstype EXFAT "$imagePath"

# Wait a moment for mount to complete
Start-Sleep -Seconds 2

# Find the mounted drive letter
$mountedDrive = $null
$drives = Get-Volume | Where-Object {$_.FileSystem -eq "exFAT"} | Select-Object -First 1
if ($drives) {
    $mountedDrive = $drives.DriveLetter + ":"
    Write-Host "Image mounted as: $mountedDrive" -ForegroundColor Green
} else {
    Write-Host "ERROR: Could not find mounted exFAT drive!" -ForegroundColor Red
    exit 1
}

# Copy files to mounted image
Write-Host "`nCopying files to image (this may take a while for large folders)..." -ForegroundColor Cyan
Write-Host "Source: $SourceFolder" -ForegroundColor Gray
Write-Host "Target: $mountedDrive\" -ForegroundColor Gray

try {
    Copy-Item "$SourceFolder\*" "$mountedDrive\" -Recurse -Force
    Write-Host "Files copied successfully!" -ForegroundColor Green
} catch {
    Write-Host "ERROR during copy: $_" -ForegroundColor Red
    Write-Host "Attempting to unmount..." -ForegroundColor Yellow
    & $osfmountPath -d -m $mountedDrive
    exit 1
}

# Unmount the image
Write-Host "`nUnmounting image..." -ForegroundColor Cyan
& $osfmountPath -d -m $mountedDrive
Start-Sleep -Seconds 1
Write-Host "Image unmounted successfully!" -ForegroundColor Green

# Check image file size
$imageFileSize = (Get-Item $imagePath).Length
$imageFileSizeGB = [math]::Round($imageFileSize / 1GB, 2)
Write-Host "Image file created: $imagePath ($imageFileSizeGB GB)" -ForegroundColor Green

# Ask about compression
Write-Host "`n=== Compression Step ===" -ForegroundColor Cyan
$compressChoice = Read-Host "Compress to .zst format? (Y/N)"

if ($compressChoice -eq "Y" -or $compressChoice -eq "y") {
    Write-Host "Starting compression..." -ForegroundColor Cyan
    
    # Check if Python and zstandard are available
    try {
        $pythonCheck = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Python not found"
        }
    } catch {
        Write-Host "ERROR: Python not found or not in PATH!" -ForegroundColor Red
        Write-Host "Please install Python and add it to PATH, or run compress_image.py manually:" -ForegroundColor Yellow
        Write-Host "python compress_image.py `"$imagePath`" `"$imagePath.zst`"" -ForegroundColor Gray
        exit 1
    }
    
    # Run compression script
    $zstPath = Join-Path $OutputFolder "$folderName.exfat.zst"
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    $compressScript = Join-Path $scriptPath "compress_image.py"
    
    if (-not (Test-Path $compressScript)) {
        Write-Host "ERROR: compress_image.py not found at $compressScript" -ForegroundColor Red
        Write-Host "Compression script not available." -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "Compressing $imagePath to .zst..." -ForegroundColor Cyan
    python "$compressScript" "$imagePath" "$zstPath"
    
    if ($LASTEXITCODE -eq 0) {
        $compressedSize = (Get-Item $zstPath).Length
        $compressedSizeGB = [math]::Round($compressedSize / 1GB, 2)
        $ratio = [math]::Round(($compressedSize / $imageFileSize) * 100, 1)
        
        Write-Host "`n=== Compression Complete ===" -ForegroundColor Green
        Write-Host "Original:   $imageFileSizeGB GB" -ForegroundColor Cyan
        Write-Host "Compressed: $compressedSizeGB GB" -ForegroundColor Cyan
        Write-Host "Ratio:      $ratio%" -ForegroundColor Cyan
        Write-Host "Location:   $zstPath" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Compression failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Skipping compression." -ForegroundColor Yellow
}

Write-Host "`n=== Complete ===" -ForegroundColor Green
Write-Host "Files saved to: $OutputFolder" -ForegroundColor Cyan
Write-Host "Close this window or press any key..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
