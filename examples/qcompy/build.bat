@ECHO OFF
SETLOCAL
cd /d %~dp0

ECHO Building qcompy...

REM Build with PyInstaller using uv
REM Run from root directory for proper dependency resolution
cd ..\..
uv run --with pyinstaller ^
  pyinstaller --onefile --clean --noconfirm ^
  --paths . ^
  --icon=%~dp0qcompy.ico ^
  --name=qcompy ^
  --distpath=%~dp0dist ^
  --workpath=%~dp0build ^
  --specpath=%~dp0 ^
  %~dp0qcompy.py

IF %ERRORLEVEL% NEQ 0 (
    ECHO Build failed!
    EXIT /B 1
)

ECHO Build complete: %~dp0dist\qcompy.exe
ENDLOCAL
