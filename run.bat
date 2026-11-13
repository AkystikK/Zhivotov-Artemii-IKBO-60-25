@echo off

if "%~1"=="" (
    echo Start this launcher from PowerShell with a VFS archive path.
    echo Usage: .\run.bat --vfs "path\to\archive.zip"
    echo Optional: --script "path\to\startup.txt"
    echo.
    pause
    exit /b 2
)

python -B "%~dp0Emulator\src\main.py" %*
exit /b %errorlevel%
