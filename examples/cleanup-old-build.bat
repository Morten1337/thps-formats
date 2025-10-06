@ECHO OFF
ECHO Cleaning up old build system files...
ECHO.

REM Remove old centralized build files
IF EXIST build.spec (
    ECHO Removing build.spec
    DEL /F build.spec
)

IF EXIST build.json (
    ECHO Removing build.json
    DEL /F build.json
)

IF EXIST build.bat (
    ECHO Removing old build.bat
    DEL /F build.bat
)

IF EXIST requirements.txt (
    ECHO Removing requirements.txt
    DEL /F requirements.txt
)

REM Remove individual requirements.txt files
FOR %%A IN (qcompy prepack fontgen asscopy releasegen runmenow) DO (
    IF EXIST %%A\requirements.txt (
        ECHO Removing %%A\requirements.txt
        DEL /F %%A\requirements.txt
    )
    IF EXIST %%A\%%A.spec (
        ECHO Removing %%A\%%A.spec
        DEL /F %%A\%%A.spec
    )
)

ECHO.
ECHO Cleanup complete!
ECHO.
ECHO Old build system files have been removed.
ECHO You can now use the new uv-based build system.
