@REM make_image_and_compress.bat
@REM Creates exFAT image AND automatically compresses to .zst
@REM Usage: make_image_and_compress.bat "output.exfat" "source_folder" [size]
@REM Example: make_image_and_compress.bat "PPSA17221-osfmount.exfat" "PPSA17221-app"

@echo off
setlocal enabledelayedexpansion

if "%~1"=="" (
    echo.
    echo Usage: make_image_and_compress.bat "^<ImagePath^>" "^<SourceDir^>" ["^<Size^>"]
    echo.
    echo This script will:
    echo   1. Create exFAT image using make_image.bat
    echo   2. Automatically compress to .zst
    echo.
    echo Examples:
    echo   make_image_and_compress.bat "PPSA17221-osfmount.exfat" "PPSA17221-app"
    echo   make_image_and_compress.bat "PPSA17221-osfmount.exfat" "PPSA17221-app" "2G"
    echo.
    exit /b 1
)

set "ImagePath=%~1"
set "SourceDir=%~2"
set "Size=%~3"
set "ZstOutput=!ImagePath!.zst"

echo.
echo ========================================
echo OSFMount exFAT + ZST Compression Builder
echo ========================================
echo ImagePath: !ImagePath!
echo SourceDir: !SourceDir!
if not "!Size!"=="" (
    echo Size: !Size!
) else (
    echo Size: auto-calculate
)
echo ZST Output: !ZstOutput!
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: This script requires Administrator privileges.
    echo Please run Command Prompt as Administrator.
    echo.
    exit /b 1
)

REM Step 1: Create exFAT image
echo [Step 1/2] Creating exFAT image...
echo.

if not "!Size!"=="" (
    call "%~dp0make_image.bat" "!ImagePath!" "!SourceDir!" "!Size!"
) else (
    call "%~dp0make_image.bat" "!ImagePath!" "!SourceDir!"
)

if %errorlevel% neq 0 (
    echo.
    echo ✗ Image creation failed!
    exit /b %errorlevel%
)

REM Step 1.5: Wait for OSFMount to fully complete
echo.
echo [Step 1.5/2] Waiting for OSFMount process to complete...
echo.

REM Force-kill OSFMount to ensure clean state and full resource release
taskkill /IM osfmount.exe /F /T 2>nul
if %errorlevel% equ 0 (
    echo   - OSFMount process terminated
) else (
    echo   - OSFMount not running (already cleaned up)
)

REM Wait for file handles to fully release
timeout /t 3 /nobreak
echo   - Waiting 3 seconds for file handles to release...
echo.

REM Step 2: Compress to ZST
echo [Step 2/2] Compressing to .zst...
echo.

python "%~dp0compress_image.py" "!ImagePath!" "!ZstOutput!"

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✓ SUCCESS!
    echo ========================================
    echo.
    echo Created Files:
    echo   - !ImagePath!
    echo   - !ZstOutput!
    echo.
) else (
    echo.
    echo ✗ Compression failed with error code %errorlevel%
    exit /b %errorlevel%
)
