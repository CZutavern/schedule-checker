@echo off
setlocal
cd /d "%~dp0"
title Schedule Checker - test the phone call

if not exist "venv\Scripts\python.exe" (
  echo  Please run Setup.bat first.
  pause
  exit /b 1
)

"venv\Scripts\python.exe" test_twilio.py
echo.
pause
