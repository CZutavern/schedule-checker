@echo off
setlocal
cd /d "%~dp0"
title Schedule Checker - Setup
echo.
echo  ===========================================
echo    Schedule Checker - one-time setup
echo  ===========================================
echo.

rem ---- 1. Find Python 3.10 or newer ------------------------------------------
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set "PY=py -3"
if not defined PY (
  python -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set "PY=python"
)

if not defined PY (
  echo  Python 3.10 or newer was not found on this computer.
  echo.
  where winget >nul 2>nul
  if errorlevel 1 goto :manualpython
  choice /c YN /m " Install Python 3.12 now with Windows Package Manager (winget)"
  if errorlevel 2 goto :manualpython
  winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
  echo.
  echo  Python is installed. Please CLOSE this window and double-click Setup.bat again.
  pause
  exit /b 0
)

:havepython
echo  Using: %PY%
echo.

rem ---- 2. Private Python environment inside this folder ----------------------
if not exist "venv\Scripts\python.exe" (
  echo  Creating the private Python environment...
  %PY% -m venv venv
  if errorlevel 1 goto :fail
)

rem ---- 3. Install the packages and the browser -------------------------------
echo  Installing packages (this can take a minute)...
"venv\Scripts\python.exe" -m pip install --upgrade pip -q
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :fail
echo.
echo  Installing the browser the program uses (about 150 MB, one time)...
"venv\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 goto :fail

rem ---- 4. Settings file -------------------------------------------------------
if not exist "settings.txt" copy /y "settings.example.txt" "settings.txt" >nul

echo.
echo  ===========================================
echo    Setup finished.
echo  ===========================================
echo.
echo  Next:
echo    1. Notepad is opening settings.txt. Fill in the values after each "="
echo       (the scheduler web address; Twilio is optional), then Save and close it.
echo    2. Double-click Run.bat to start.
echo.
start "" notepad "settings.txt"
pause
exit /b 0

:manualpython
echo.
echo  Please install Python from https://www.python.org/downloads/
echo  IMPORTANT: on the first installer screen, tick "Add python.exe to PATH".
echo  Then double-click Setup.bat again.
echo.
start "" "https://www.python.org/downloads/"
pause
exit /b 1

:fail
echo.
echo  Something went wrong during setup (see the messages above).
echo  Check your internet connection and double-click Setup.bat again.
echo  If it keeps failing, take a screenshot of this window and ask for help.
pause
exit /b 1
