@REM make_image.bat - Wrapper for New-OsfExfatImage.ps1
@REM Usage: make_image.bat "output.exfat" "source_folder" [size]
@REM Example: make_image.bat "PPSA17221-final.exfat" "PPSA17221-app" "2G"

@echo off
setlocal enabledelayedexpansion

if "%~1"=="" (
    echo.
    echo Usage: make_image.bat "^<ImagePath^>" "^<SourceDir^>" ["^<Size^>"]
    echo.
    echo Examples:
    echo   make_image.bat "PPSA17221-final.exfat" "PPSA17221-app"
    echo   make_image.bat "PPSA17221-final.exfat" "PPSA17221-app" "2G"
    echo.
    echo Auto-sizes image if Size not provided.
    echo Requires PowerShell execution as Administrator.
    exit /b 1
)

set "ImagePath=%~1"
set "SourceDir=%~2"
set "Size=%~3"

if not exist "%SourceDir%" (
    echo Error: Source directory not found: %SourceDir%
    exit /b 1
)

echo.
echo ========================================
echo OSFMount exFAT Image Creator (Batch)
echo ========================================
echo ImagePath: %ImagePath%
echo SourceDir: %SourceDir%
if not "!Size!"=="" (
    echo Size: !Size!
) else (
    echo Size: auto-calculate
)
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

REM Run PowerShell script with proper parameters
if not "!Size!"=="" (
    powershell.exe -ExecutionPolicy Bypass -File .\New-OsfExfatImage.ps1 -ImagePath "%ImagePath%" -SourceDir "%SourceDir%" -Size "!Size!" -Label "OSFIMG" -ForceOverwrite
) else (
    powershell.exe -ExecutionPolicy Bypass -File .\New-OsfExfatImage.ps1 -ImagePath "%ImagePath%" -SourceDir "%SourceDir%" -Label "OSFIMG" -ForceOverwrite
)

if %errorlevel% equ 0 (
    echo.
    echo ✓ Image created successfully: %ImagePath%
) else (
    echo.
    echo ✗ Image creation failed with error code %errorlevel%
    exit /b %errorlevel%
)
