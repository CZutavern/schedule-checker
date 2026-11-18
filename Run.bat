@echo off
setlocal
cd /d "%~dp0"
title Schedule Checker

if not exist "venv\Scripts\python.exe" (
  echo  First time here: running setup first.
  echo.
  call Setup.bat
  if not exist "venv\Scripts\python.exe" exit /b 1
)

if not exist "settings.txt" (
  copy /y "settings.example.txt" "settings.txt" >nul
  echo  Created settings.txt. Fill it in, save it, then double-click Run.bat again.
  start "" notepad "settings.txt"
  pause
  exit /b 0
)

"venv\Scripts\python.exe" main.py
echo.
echo  The program has stopped.
pause
