@echo off
python -B "%~dp0src\main.py" %*
exit /b %errorlevel%
