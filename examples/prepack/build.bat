@ECHO OFF
pyinstaller prepack.py --paths ../../ --noconfirm --clean --icon=prepack.ico
IF NOT EXIST D:\Repos\thugpro-open\ GOTO :EOF
COPY dist\prepack\prepack.exe D:\Repos\thugpro-open\tools
COPY dist\prepack\_internal D:\Repos\thugpro-open\tools\_internal
