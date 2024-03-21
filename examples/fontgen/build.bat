@ECHO OFF
pyinstaller fontgen.py --paths ../../ --noconfirm --clean --icon=fontgen.ico
IF NOT EXIST D:\Repos\thugpro-open\ GOTO :EOF
COPY dist\fontgen\fontgen.exe D:\Repos\thugpro-open\tools
COPY dist\fontgen\_internal D:\Repos\thugpro-open\tools\_internal
