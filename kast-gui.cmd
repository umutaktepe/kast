@echo off
setlocal
chcp 65001 >nul 2>&1
set "SCRIPT_DIR=%~dp0"

if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    "%SCRIPT_DIR%.venv\Scripts\python.exe" "%SCRIPT_DIR%kast.py" --gui %*
) else (
    python "%SCRIPT_DIR%kast.py" --gui %*
)
endlocal
