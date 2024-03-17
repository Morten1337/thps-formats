@ECHO OFF
SETLOCAL ENABLEDELAYEDEXPANSION
SET SOURCE_DIR="%CD%\source"
SET OUTPUT_DIR="%CD%\source"
QConsole.exe -def %CD%\defines.txt -r -c %SOURCE_DIR%\code\qb -o %OUTPUT_DIR%\code\qb || PAUSE
PAUSE
