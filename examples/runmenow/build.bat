@ECHO OFF
SETLOCAL
cd /d %~dp0

ECHO Building runmenow...

REM Build with PyInstaller using uv (noconsole for background process)
cd ..\..
uv run --with pyinstaller --with pywin32 ^
  pyinstaller --onefile --clean --noconfirm ^
  --paths . ^
  --noconsole ^
  --icon=%~dp0runmenow.ico ^
  --name=runmenow ^
  --distpath=%~dp0dist ^
  --workpath=%~dp0build ^
  --specpath=%~dp0 ^
  %~dp0runmenow.py

IF %ERRORLEVEL% NEQ 0 (
    ECHO Build failed!
    EXIT /B 1
)

ECHO Build complete: examples\runmenow\dist\runmenow.exe
ENDLOCAL
