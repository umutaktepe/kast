@echo off
setlocal
echo Kast 2.0 Windows Kurulumu Baslatiliyor...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [HATA] Kurulum sirasinda bir sorun olustu.
    pause
    exit /b %ERRORLEVEL%
)
echo.
pause
endlocal
