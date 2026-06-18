@echo off
chcp 65001 >nul
cd /d "%~dp0dist\NutriDietas"

if not exist "NutriDietas.exe" (
    echo No se encontro dist\NutriDietas\NutriDietas.exe
    echo Primero compila la aplicacion ejecutando: compilar.bat
    pause
    exit /b 1
)

echo Abriendo NutriDietas...
start "" "NutriDietas.exe"
