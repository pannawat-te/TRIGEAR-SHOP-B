@echo off
cd /d "%~dp0"
py -m pip install --upgrade pip
if errorlevel 1 goto failed
py -m pip install --only-binary=:all: -r requirements-camera.txt
if errorlevel 1 goto failed
py -c "import cv2; print('OpenCV:', cv2.__version__)"
if errorlevel 1 goto failed
echo Camera package installed. Camera access also requires device permissions.
pause
exit /b 0
:failed
echo Camera installation failed. No source build will be attempted.
echo The main application can still run; select a profile photo from a file.
echo Please send the full error and the output of: py -VV
pause
exit /b 1
