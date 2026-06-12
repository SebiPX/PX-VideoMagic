@echo off
echo Building PX-VideoMagic Backend with PyInstaller...

:: Clean previous builds
rmdir /s /q build
rmdir /s /q dist

:: Run PyInstaller
pyinstaller --name backend ^
  --onefile ^
  --add-data "../../video-use/helpers;video-use/helpers" ^
  --add-data "../frontend/dist;frontend_dist" ^
  main.py

echo Build complete! The executable is located at dist/backend.exe
pause
