@ECHO OFF
pyinstaller asscopy.py --paths ../../ --noconfirm --clean --icon=asscopy.ico
COPY dist\asscopy\asscopy.exe D:\Repos\thugpro-tools
