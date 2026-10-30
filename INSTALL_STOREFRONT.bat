@echo off
cd /d "%~dp0"
py -m pip install --prefer-binary -r requirements-storefront.txt
if errorlevel 1 (
  echo Installation failed. Please send the full error message.
  pause
  exit /b 1
)
echo Installation complete. Run: py main.py
pause
