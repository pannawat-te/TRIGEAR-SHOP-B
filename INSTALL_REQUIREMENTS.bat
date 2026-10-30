@echo off
cd /d "%~dp0"
py -m pip install --upgrade pip
if errorlevel 1 goto failed
py -m pip install --prefer-binary -r requirements.txt
if errorlevel 1 goto failed
echo Core installation complete. Open START_TRIGEAR.bat.
echo Camera support is optional: run INSTALL_CAMERA.bat separately.
pause
exit /b 0
:failed
echo Installation failed. Please keep the full error message.
pause
exit /b 1
