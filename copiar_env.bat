@echo off

copy /Y ".env.pos" "dist\PAPELERA_POS\.env.pos"

if errorlevel 1 (
    echo ERROR: no se pudo copiar .env.pos
    exit /b 1
)

echo .env.pos copiado correctamente.