@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
 echo Python no esta instalado. Ejecuta CREAR_EXE.bat para preparar el programa.
 pause
 exit /b 1
)
py main.py
