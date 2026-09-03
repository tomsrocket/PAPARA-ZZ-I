@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python wurde nicht gefunden.
  echo Bitte entweder Python 3.10 oder neuer installieren oder den fertigen
  echo PAPARAZZI-Python-Programmordner verwenden.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\pythonw.exe" (
  echo PAPARAZZI-Python wird einmalig eingerichtet...
  py -3 -m venv .venv
  if errorlevel 1 goto :error
  ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
  if errorlevel 1 goto :error
)

start "" ".venv\Scripts\pythonw.exe" PAPARAZZI_Python.pyw
exit /b 0

:error
echo.
echo Die Einrichtung ist fehlgeschlagen. Bitte die angezeigte Fehlermeldung weitergeben.
pause
exit /b 1

