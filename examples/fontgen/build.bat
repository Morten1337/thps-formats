@ECHO OFF
SETLOCAL
cd /d %~dp0

ECHO Building fontgen...

REM Build with PyInstaller using uv
cd ..\..
uv run --with pyinstaller ^
  pyinstaller --onefile --clean --noconfirm ^
  --paths . ^
  --hidden-import=PIL ^
  --hidden-import=PIL._imaging ^
  --hidden-import=PIL.Image ^
  --icon=%~dp0fontgen.ico ^
  --name=fontgen ^
  --distpath=%~dp0dist ^
  --workpath=%~dp0build ^
  --specpath=%~dp0 ^
  %~dp0fontgen.py

IF %ERRORLEVEL% NEQ 0 (
    ECHO Build failed!
    EXIT /B 1
)

ECHO Build complete: examples\fontgen\dist\fontgen.exe
ENDLOCAL
