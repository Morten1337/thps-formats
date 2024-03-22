@ECHO OFF
pyinstaller fontgen.py --paths ../../ --noconfirm --clean --icon=fontgen.ico --hidden-import=PIL --hidden-import=PIL._imaging --hidden-import=PIL.Image
IF NOT EXIST D:\Repos\thugpro-open\ GOTO :EOF
COPY dist\fontgen\fontgen.exe D:\Repos\thugpro-open\tools
XCOPY /S /I /Y dist\fontgen\_internal D:\Repos\thugpro-open\tools\_internal
