@echo off
setlocal ENABLEEXTENSIONS

REM ==== Build config ====
set "APP_NAME=dbfcleaner"
set "GUI_ENTRY=gui\app.py"
set "CLI_ENTRY=cli\main.py"

REM ==== Info ====
echo [INFO] Current directory: "%cd%"

REM ==== Wymagany Python 3.7 32-bit ====
py -3.7-32 -c "print('OK')" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3.7 32-bit not found.
  exit /b 1
)

REM ==== Zależności ====
py -3.7-32 -m pip install --upgrade pip
if errorlevel 1 (
  echo [ERROR] Failed to upgrade pip.
  exit /b 1
)

py -3.7-32 -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Failed to install requirements.
  exit /b 1
)

REM ==== PyInstaller ====
py -3.7-32 -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
  echo [INFO] PyInstaller not found. Installing...
  py -3.7-32 -m pip install pyinstaller
  if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller.
    exit /b 1
  )
)

REM ==== Build GUI ====
echo [INFO] Building GUI EXE...
py -3.7-32 -m PyInstaller --noconsole --onefile --name "%APP_NAME%_gui" "%GUI_ENTRY%"
if errorlevel 1 (
  echo [ERROR] GUI build failed.
  exit /b 1
)

REM ==== Build CLI ====
echo [INFO] Building CLI EXE...
py -3.7-32 -m PyInstaller --console --onefile --name "%APP_NAME%_cli" "%CLI_ENTRY%"
if errorlevel 1 (
  echo [ERROR] CLI build failed.
  exit /b 1
)

echo.
echo [DONE] Artifacts created in the "dist\" directory.
exit /b 0