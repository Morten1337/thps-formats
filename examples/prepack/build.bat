@ECHO OFF
SETLOCAL
cd /d %~dp0

ECHO Building prepack...

REM Build with PyInstaller using uv
cd ..\..
uv run --with pyinstaller ^
  pyinstaller --onefile --clean --noconfirm ^
  --paths . ^
  --icon=%~dp0prepack.ico ^
  --name=prepack ^
  --distpath=%~dp0dist ^
  --workpath=%~dp0build ^
  --specpath=%~dp0 ^
  %~dp0prepack.py

IF %ERRORLEVEL% NEQ 0 (
    ECHO Build failed!
    EXIT /B 1
)

ECHO Build complete: examples\prepack\dist\prepack.exe
ENDLOCAL
