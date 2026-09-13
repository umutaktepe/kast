@echo off
setlocal
echo Kast 2.0 Windows Kaldirma Islemi Baslatiliyor...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1"
echo.
pause
endlocal
