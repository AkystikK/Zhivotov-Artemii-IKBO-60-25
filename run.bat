@echo off
python -B "%~dp0Emulator\src\main.py" %*
exit /b %errorlevel%
