@ECHO OFF
SETLOCAL ENABLEDELAYEDEXPANSION

ECHO ============================================
ECHO Building all example tools
ECHO ============================================
ECHO.

SET APPS=qcompy prepack fontgen asscopy runmenow
SET FAILED=

FOR %%A IN (%APPS%) DO (
    ECHO.
    ECHO ----------------------------------------
    ECHO Building %%A...
    ECHO ----------------------------------------
    CALL %%A\build.bat
    IF ERRORLEVEL 1 (
        ECHO [ERROR] Failed to build %%A
        SET FAILED=!FAILED! %%A
    ) ELSE (
        ECHO [SUCCESS] %%A built successfully
    )
)

ECHO.
ECHO ============================================
ECHO Build Summary
ECHO ============================================

IF DEFINED FAILED (
    ECHO Failed builds:%FAILED%
    EXIT /B 1
) ELSE (
    ECHO All builds completed successfully!
    ECHO.
    ECHO Executables are located in each app's dist\ folder:
    FOR %%A IN (%APPS%) DO (
        IF EXIST %%A\dist\%%A.exe (
            ECHO   - %%A\dist\%%A.exe
        )
    )
)

ENDLOCAL
