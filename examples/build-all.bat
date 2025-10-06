@ECHO OFF
SETLOCAL ENABLEDELAYEDEXPANSION

ECHO --------------------------------------------------------------------
ECHO building all example tools
ECHO --------------------------------------------------------------------
ECHO.

SET APPS=qcompy prepack fontgen asscopy runmenow
SET FAILED=

FOR %%A IN (%APPS%) DO (
    ECHO.
    ECHO --------------------------------------------------------------------
    ECHO building %%A...
    ECHO --------------------------------------------------------------------
    CALL %%A\build.bat
    IF ERRORLEVEL 1 (
        ECHO [error] failed to build %%A
        SET FAILED=!FAILED! %%A
    ) ELSE (
        ECHO [success] %%A built successfully
    )
)

ECHO.
ECHO --------------------------------------------------------------------
ECHO build summary
ECHO --------------------------------------------------------------------

IF DEFINED FAILED (
    ECHO failed builds:%FAILED%
    EXIT /B 1
) ELSE (
    ECHO all builds completed successfully!
)

ENDLOCAL
