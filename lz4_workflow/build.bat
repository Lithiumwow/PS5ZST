@echo off
REM LZ4 Decompression ELF Build Script for PS5 (Windows)
REM Automatic compilation with PS5 SDK

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   LZ4 Decompression ELF Builder for PS5
echo ========================================
echo.

REM Check for PS5 SDK path
if not defined PS5_SDK_PATH (
    if exist "C:\Program Files\SCEI\PS5 SDK" (
        set "PS5_SDK_PATH=C:\Program Files\SCEI\PS5 SDK"
    ) else if exist "C:\PS5_SDK" (
        set "PS5_SDK_PATH=C:\PS5_SDK"
    ) else (
        echo ERROR: PS5 SDK not found!
        echo Set PS5_SDK_PATH environment variable or install SDK
        exit /b 1
    )
)

echo PS5 SDK Path: %PS5_SDK_PATH%

REM Check for compiler
if not exist "%PS5_SDK_PATH%\bin\x86_64-scei-ps5-gcc.exe" (
    echo ERROR: GCC compiler not found at: %PS5_SDK_PATH%\bin\x86_64-scei-ps5-gcc.exe
    exit /b 1
)

REM Check for LZ4 headers
if not exist "%PS5_SDK_PATH%\include\lz4.h" (
    echo ERROR: LZ4 headers not found in SDK
    echo Ensure liblz4-dev is installed in PS5 SDK
    exit /b 1
)

echo Compiler: %PS5_SDK_PATH%\bin\x86_64-scei-ps5-gcc.exe
echo.

REM Create output directory
if not exist build mkdir build
cd build

echo Compiling LZ4 Decompression ELF...
echo.

REM Compile with optimizations
"%PS5_SDK_PATH%\bin\x86_64-scei-ps5-gcc.exe" ^
    -O3 -march=native -flto ^
    -I"%PS5_SDK_PATH%\include" ^
    -L"%PS5_SDK_PATH%\lib" ^
    -o LZ4DecompressionPS5.elf ^
    ..\LZ4DecompressionPS5.c ^
    -llz4

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================
    echo Build Successful!
    echo ========================================
    echo.
    echo Output: build\LZ4DecompressionPS5.elf
    echo.
    echo Usage on PS5:
    echo   ./LZ4DecompressionPS5.elf ^<input.lz4^> ^<output^>
    echo.
) else (
    echo.
    echo ========================================
    echo Build Failed!
    echo ========================================
    echo.
    exit /b 1
)
