@echo off
REM ══════════════════════════════════════════════════════════════════════════
REM  SOVEREIGN OS DIM — Build Script
REM ══════════════════════════════════════════════════════════════════════════
REM  Author  : Adam Beloucif
REM  Builds two versions: Folder (fast startup) and Standalone (portable)
REM ══════════════════════════════════════════════════════════════════════════

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║   SOVEREIGN OS DIM — Build Production                   ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

echo [1/3] Installation des dependances...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERREUR : Installation echouee.
    pause
    exit /b 1
)

echo.
echo [2/3] Compilation format Dossier (--onedir, demarrage rapide)...
pyinstaller --noconfirm --onedir --windowed ^
    --add-data "frontend;frontend" ^
    --name "Sovereign_OS_DIM" ^
    --icon "frontend/favicon.ico" ^
    main.py
if errorlevel 1 (
    echo ERREUR : Compilation Dossier echouee.
    pause
    exit /b 1
)

echo.
echo [3/3] Compilation format Standalone (--onefile, portable)...
pyinstaller --noconfirm --onefile --windowed ^
    --add-data "frontend;frontend" ^
    --name "Sovereign_OS_DIM_Portable" ^
    --icon "frontend/favicon.ico" ^
    main.py
if errorlevel 1 (
    echo ERREUR : Compilation Standalone echouee.
    pause
    exit /b 1
)

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║   BUILD TERMINE AVEC SUCCES !                           ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
echo    [1] Format Dossier    : dist\Sovereign_OS_DIM\Sovereign_OS_DIM.exe
echo    [2] Format Portable   : dist\Sovereign_OS_DIM_Portable.exe
echo.
pause
