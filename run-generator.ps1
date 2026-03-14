# Auto-elevate and run the batch file with user input
param()

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    # Re-run as admin
    $scriptPath = $PSCommandPath
    $args = "-NoExit -ExecutionPolicy Bypass -File `"$scriptPath`""
    Start-Process powershell.exe -Verb RunAs -ArgumentList $args -Wait
    exit
}

# Now running as admin
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  exFAT Image Generator + Compressor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get input from user
$sourcePath = Read-Host "Enter game package folder (e.g., C:\path\to\PPSA04264)"
$outputPath = Read-Host "Enter output folder for exFAT and .zst (e.g., E:\Compressed)"

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
Write-Host "  Source:  $sourcePath"
Write-Host "  Output:  $outputPath"
Write-Host "  Image:   $imagePath"
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

# Run the batch file
Write-Host ""
Write-Host "Starting exFAT generation and compression..." -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $PSCommandPath
$batchPath = Join-Path $scriptDir "make_image_and_compress.bat"

if (-not (Test-Path $batchPath)) {
    Write-Host "ERROR: Batch file not found: $batchPath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

& cmd /c "`"$batchPath`" `"$imagePath`" `"$sourcePath`""

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Done! Check $outputPath for the exFAT and .zst files" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
