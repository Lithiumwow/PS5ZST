# Auto-elevate and run the batch file with user input
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
Write-Host "  exFAT Image Generator + Compressor" -ForegroundColor Cyan
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
    # Check if it's in PATH
    try {
        $cmd = Get-Command "osfmount.com" -ErrorAction SilentlyContinue
        if ($cmd) {
            Write-Host "  [+] OSFMount found in PATH" -ForegroundColor Green
            $osfmountFound = $true
        }
    } catch {
        # Not found
    }
}

if (-not $osfmountFound) {
    Write-Host ""
    Write-Host "OSFMount not found. Installing via winget..." -ForegroundColor Yellow
    Write-Host ""
    
    # Try to install via winget
    try {
        Write-Host "Running: winget install --exact --quiet PassMark.OSFMount" -ForegroundColor Cyan
        $installResult = & winget install --exact --quiet PassMark.OSFMount
        Start-Sleep -Seconds 3
        
        # Verify installation
        if (Test-Path "${env:ProgramFiles}\PassMark\OSFMount\osfmount.com") {
            Write-Host "  [+] OSFMount installed successfully" -ForegroundColor Green
            $osfmountFound = $true
        } elseif (Test-Path "${env:ProgramFiles(x86)}\PassMark\OSFMount\osfmount.com") {
            Write-Host "  [+] OSFMount installed successfully (x86)" -ForegroundColor Green
            $osfmountFound = $true
        }
    } catch {
        Write-Host "  ! winget install failed" -ForegroundColor Yellow
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

Write-Host ""

# Get input from user
$sourcePath = (Read-Host "Enter game package folder (e.g., C:\path\to\PPSA04264)").Trim('" ')
$outputPath = (Read-Host "Enter output folder for exFAT and .zst (e.g., E:\Compressed)").Trim('" ')

# Validate paths
if (-not (Test-Path $sourcePath -PathType Container)) {
    Write-Host ""
    Write-Host "ERROR: Source folder not found: $sourcePath" -ForegroundColor Red
    Write-Host "Tip: Paste path WITHOUT quotes" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path $outputPath -PathType Container)) {
    Write-Host ""
    Write-Host "ERROR: Output folder not found: $outputPath" -ForegroundColor Red
    Write-Host "Tip: Paste path WITHOUT quotes" -ForegroundColor Yellow
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
Write-Host "Cleaning up OSFMount processes..." -ForegroundColor Cyan

# Final cleanup: attempt graceful dismount of any lingering mounts
$attempts = 0
$maxAttempts = 5
while ($attempts -lt $maxAttempts) {
    $osfProcess = Get-Process osfmount -ErrorAction SilentlyContinue
    if (-not $osfProcess) {
        Write-Host "  [+] OSFMount fully cleaned up" -ForegroundColor Green
        break
    }
    
    $attempts++
    Write-Host "  Attempt $attempts/$maxAttempts to clean up OSFMount..." -ForegroundColor Yellow
    Start-Sleep -Seconds 1
}

if ($osfProcess) {
    Write-Host "  [!] Force-terminating remaining OSFMount processes..." -ForegroundColor Yellow
    Stop-Process -Name osfmount -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Done! Check $outputPath for the exFAT and .zst files" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
