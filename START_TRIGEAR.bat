@echo off
cd /d "%~dp0"
py -c "import customtkinter, PIL, reportlab" >nul 2>&1
if errorlevel 1 (
  echo Required packages are missing for this Python.
  echo Run INSTALL_REQUIREMENTS.bat first, then try again.
  pause
  exit /b 1
)
py main.py
if errorlevel 1 pause
 