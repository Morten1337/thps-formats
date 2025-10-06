@ECHO OFF
SETLOCAL
cd /d %~dp0

ECHO Building asscopy...

REM Build with PyInstaller using uv
cd ..\..
uv run --with pyinstaller ^
  pyinstaller --onefile --clean --noconfirm ^
  --paths . ^
  --icon=%~dp0asscopy.ico ^
  --name=asscopy ^
  --distpath=%~dp0dist ^
  --workpath=%~dp0build ^
  --specpath=%~dp0 ^
  %~dp0asscopy.py

IF %ERRORLEVEL% NEQ 0 (
    ECHO Build failed!
    EXIT /B 1
)

ECHO Build complete: examples\asscopy\dist\asscopy.exe
ENDLOCAL
