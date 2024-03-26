@ECHO OFF
pyinstaller qcompy.py --paths ../../ --noconfirm --clean --icon=qcompy.ico
COPY dist\qcompy\qcompy.exe D:\Repos\thugpro-tools
