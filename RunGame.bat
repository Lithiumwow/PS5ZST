@echo off
REM Batch script to generate exFAT image with admin privileges
REM Automatically runs the PowerShell script and enables compression

cd /d "C:\Users\Lithiumwow\ps4-5\SDKPS5FTPandNewprojecthere"

REM Clean up previous attempt
del /f /q "E:\compressed\PPSA04264.exfat" 2>nul

REM Run the PowerShell script with parameters and auto-answer Y for compression
powershell -NoExit -ExecutionPolicy Bypass -Command ^
  "$SourceFolder = 'C:\Users\Lithiumwow\ps4-5\SDKPS5FTPandNewprojecthere\PPSA04264'; " ^
  "$OutputFolder = 'E:\compressed'; " ^
  "$CompressChoice = 'Y'; " ^
  ". '.\Create-ExfatImage.ps1' -SourceFolder $SourceFolder -OutputFolder $OutputFolder; " ^
  "if ($CompressChoice -eq 'Y' -or $CompressChoice -eq 'y') { Write-Host 'Y' }"

pause
