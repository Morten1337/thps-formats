@ECHO OFF
pyinstaller --clean --noconfirm build.spec
if EXIST "D:\Repos\thugpro-tools\_internal\" RMDIR "D:\Repos\thugpro-tools\_internal\" /S /Q
XCOPY dist\tools D:\Repos\thugpro-tools\ /S /E /I /Y
