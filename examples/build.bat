@ECHO OFF
pyinstaller --clean --noconfirm build.spec
XCOPY dist\tools D:\Repos\thugpro-tools\ /S /E /I /Y
