@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python 3 wurde nicht gefunden.
  pause
  exit /b 1
)

if not exist ".build-venv\Scripts\python.exe" py -3 -m venv .build-venv
if errorlevel 1 goto :error

".build-venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-build.txt
if errorlevel 1 goto :error

".build-venv\Scripts\pyinstaller.exe" --noconfirm --clean --windowed ^
  --name "PAPARAZZI-Python" ^
  --icon "paparazzi_icon_16.png" ^
  --add-data "gpl.txt;." ^
  --add-data "PAPARAZZI_3.0_UserManual.pdf;." ^
  "PAPARAZZI_Python.pyw"
if errorlevel 1 goto :error

copy /Y "README_PYTHON.md" "dist\PAPARAZZI-Python\README_PYTHON.md" >nul
copy /Y "gpl.txt" "dist\PAPARAZZI-Python\gpl.txt" >nul
echo.
echo Fertig: dist\PAPARAZZI-Python\PAPARAZZI-Python.exe
pause
exit /b 0

:error
echo.
echo Der Windows-Build ist fehlgeschlagen.
pause
exit /b 1

