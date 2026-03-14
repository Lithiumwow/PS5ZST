@echo off
REM Launch Create-ExfatImage.ps1 as Administrator
REM This wrapper allows double-click execution with admin privileges

setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%Create-ExfatImage.ps1"

REM Check if PowerShell script exists
if not exist "!PS_SCRIPT!" (
    echo ERROR: Create-ExfatImage.ps1 not found in %SCRIPT_DIR%
    pause
    exit /b 1
)

REM Run PowerShell script as Administrator
powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoExit -ExecutionPolicy Bypass -File \"!PS_SCRIPT!\"'"

exit /b 0
