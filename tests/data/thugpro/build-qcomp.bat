@ECHO OFF
SETLOCAL ENABLEDELAYEDEXPANSION
SET TOOLS_DIR="D:\dev\thps-formats\examples\qcompy\dist\qcompy\"
SET SOURCE_DIR="%CD%\source"
SET OUTPUT_DIR="%CD%\output"
%TOOLS_DIR%\qcompy.exe %SOURCE_DIR%\code\qb --output %OUTPUT_DIR%\data\qb --defines %CD%\defines.txt --recursive
