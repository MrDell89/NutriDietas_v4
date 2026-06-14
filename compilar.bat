@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   Compilando NutriDietas (.exe)
echo ============================================
echo.

echo [1/2] Limpiando compilaciones anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/2] Compilando con PyInstaller...
python -m PyInstaller NutriDietas.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo *** ERROR en la compilacion. Revisa el mensaje de arriba. ***
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Listo. Ejecutable generado en:
echo   dist\NutriDietas\NutriDietas.exe
echo.
echo   Para abrirlo usa: ejecutar.bat
echo ============================================
pause
