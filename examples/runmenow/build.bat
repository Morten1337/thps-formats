@ECHO OFF

SETLOCAL ENABLEDELAYEDEXPANSION
IF NOT DEFINED THUGPRO_TOOLS_PATH (
	SET THUGPRO_TOOLS_PATH=D:\Repos\thugpro-tools
)
pyinstaller runmenow.py --paths ../../ --noconfirm --onefile --noconsole --clean --icon=runmenow.ico --upx-dir="D:/Tools/upx-4.2.4-win64"
COPY dist\runmenow.exe %THUGPRO_TOOLS_PATH%
