@echo off
setlocal

cd /d "%~dp0"

echo ==========================================
echo   PAPELERA POS - CREAR EJECUTABLE
echo ==========================================

where py >nul 2>nul
if errorlevel 1 (
    echo No se encontro Python. Instala Python 3.11+ y volve a ejecutar este archivo.
    pause
    exit /b 1
)

py -m pip install --upgrade pip

py -m pip install -r requirements.txt

if errorlevel 1 (
    echo No se pudieron instalar las dependencias.
    pause
    exit /b 1
)

py -m PyInstaller --noconfirm --clean PAPELERA_POS.spec

if errorlevel 1 (
    echo No se pudo generar el EXE.
    pause
    exit /b 1
)

if not exist "dist\PAPELERA_POS\database" mkdir "dist\PAPELERA_POS\database"

if exist "database\abril.db" (
    copy /Y "database\abril.db" "dist\PAPELERA_POS\database\abril.db" >nul
)

if not exist "dist\PAPELERA_POS\tickets" mkdir "dist\PAPELERA_POS\tickets"

if not exist "dist\PAPELERA_POS\backups" mkdir "dist\PAPELERA_POS\backups"

REM Copiar version del programa
if exist "version.txt" (
    copy /Y "version.txt" "dist\PAPELERA_POS\version.txt" >nul
)

echo.
echo ==========================================
echo   EXE LISTO
echo ==========================================
echo.
echo Ubicacion:
echo dist\PAPELERA_POS\PAPELERA_POS.exe
echo.
echo Version:
type "dist\PAPELERA_POS\version.txt"

echo.
echo Copia toda la carpeta dist\PAPELERA_POS a la otra computadora.
pause