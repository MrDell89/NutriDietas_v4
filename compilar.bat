@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   Compilando NutriDietas (.exe)
echo ============================================
echo.

echo [1/3] Cerrando la app si esta abierta...
taskkill /F /IM NutriDietas.exe >nul 2>&1
rem pequena espera para que Windows libere los archivos
ping -n 2 127.0.0.1 >nul

echo [2/3] Eliminando compilaciones anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist build (
    echo.
    echo *** No se pudo borrar build\ (archivo en uso). Cierra NutriDietas y reintenta. ***
    pause
    exit /b 1
)
if exist dist (
    echo.
    echo *** No se pudo borrar dist\ (archivo en uso). Cierra NutriDietas y reintenta. ***
    pause
    exit /b 1
)

echo [3/3] Compilando con PyInstaller...
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
