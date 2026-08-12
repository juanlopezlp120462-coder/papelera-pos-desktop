```powershell
# ============================================================
# SUBIR_VERSION.ps1
# PAPELERA POS
#
# USO:
#     .\SUBIR_VERSION.ps1 1.0.57
#
# EL SCRIPT DEBE ESTAR EN LA CARPETA PRINCIPAL DEL PROYECTO.
#
# FLUJO:
#
# 1. Validar versión
# 2. Validar database original
# 3. Actualizar version.txt
# 4. Limpiar build/dist
# 5. Compilar PAPELERA_POS
# 6. Copiar database inicial
# 7. Copiar version.txt a dist
# 8. Verificar _internal
# 9. Compilar PAPELERA_UPDATER
# 10. Crear UPDATE.zip
# 11. Verificar UPDATE.zip
# 12. Verificar que NO tenga database
# 13. Git add
# 14. Git commit
# 15. Git push
# 16. Crear tag
# 17. Subir tag
#
# IMPORTANTE:
#
# INSTALACION INICIAL:
#   PAPELERA_POS.exe
#   _internal
#   database\abril.db
#   version.txt
#
# UPDATE.zip:
#   PAPELERA_POS.exe
#   _internal
#   version.txt
#
# UPDATE.zip NO contiene:
#   database
#   abril.db
#   backups
#   logs
#
# ============================================================

$ErrorActionPreference = "Stop"

# ============================================================
# RUTA PRINCIPAL DEL PROYECTO
# ============================================================

$ROOT = $PSScriptRoot

if ([string]::IsNullOrWhiteSpace($ROOT)) {
    $ROOT = (Get-Location).Path
}

Set-Location $ROOT

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       SUBIR VERSION - PAPELERA POS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Carpeta del proyecto:" -ForegroundColor DarkGray
Write-Host $ROOT -ForegroundColor DarkGray
Write-Host ""

# ============================================================
# RECIBIR VERSION
# ============================================================

if ($args.Count -lt 1) {

    Write-Host "ERROR: No se indico la version." -ForegroundColor Red
    Write-Host ""
    Write-Host "Uso:"
    Write-Host ".\SUBIR_VERSION.ps1 1.0.57"
    Write-Host ""

    exit 1
}

$VERSION = $args[0].ToString().Trim()

# ============================================================
# VALIDAR VERSION
# ============================================================

if ($VERSION -notmatch '^\d+\.\d+\.\d+$') {

    Write-Host "ERROR: Version invalida: $VERSION" -ForegroundColor Red
    Write-Host ""
    Write-Host "Ejemplo correcto: 1.0.57"
    Write-Host ""

    exit 1
}

$TAG = "v$VERSION"

# ============================================================
# DEFINIR RUTAS
# ============================================================

$VERSION_FILE = Join-Path $ROOT "version.txt"

$DATABASE_ORIGEN = Join-Path $ROOT "database\abril.db"

$DIST_ROOT = Join-Path $ROOT "dist"

$DIST_APP = Join-Path $DIST_ROOT "PAPELERA_POS"

$DIST_EXE = Join-Path $DIST_APP "PAPELERA_POS.exe"

$DIST_DATABASE_DIR = Join-Path $DIST_APP "database"

$DIST_DATABASE = Join-Path $DIST_DATABASE_DIR "abril.db"

$DIST_VERSION = Join-Path $DIST_APP "version.txt"

$DIST_INTERNAL = Join-Path $DIST_APP "_internal"

$DIST_BASE_LIBRARY = Join-Path $DIST_INTERNAL "base_library.zip"

$UPDATE_DIR = Join-Path $ROOT "UPDATE_TEMP"

$UPDATE_ZIP = Join-Path $ROOT "UPDATE.zip"

$UPDATER_DIST = Join-Path $DIST_ROOT "PAPELERA_UPDATER"

$UPDATER_EXE = Join-Path $UPDATER_DIST "PAPELERA_UPDATER.exe"

$BUILD_ROOT = Join-Path $ROOT "build"

# ============================================================
# VERSION ACTUAL
# ============================================================

if (Test-Path -LiteralPath $VERSION_FILE) {

    $VERSION_ACTUAL = (
        Get-Content -LiteralPath $VERSION_FILE -Raw
    ).Trim()

}
else {

    $VERSION_ACTUAL = "1.0.0"
}

Write-Host "Version actual: $VERSION_ACTUAL"
Write-Host ""
Write-Host "Nueva version: $VERSION" -ForegroundColor Yellow
Write-Host "Nuevo tag: $TAG" -ForegroundColor Yellow
Write-Host ""

# ============================================================
# CONFIRMACION
# ============================================================

$CONFIRMAR = Read-Host "Continuar con la version $VERSION (S/N)"

if ($CONFIRMAR -notmatch '^[sS]$') {

    Write-Host ""
    Write-Host "Operacion cancelada." -ForegroundColor Yellow
    Write-Host ""

    exit 0
}

# ============================================================
# COMPROBAR ARCHIVOS IMPORTANTES DEL PROYECTO
# ============================================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       COMPROBANDO ARCHIVOS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$ARCHIVOS_REQUERIDOS = @(
    (Join-Path $ROOT "main.py"),
    (Join-Path $ROOT "PAPELERA_POS.spec"),
    (Join-Path $ROOT "updater.py"),
    (Join-Path $ROOT "PAPELERA_UPDATER.spec"),
    $DATABASE_ORIGEN
)

foreach ($ARCHIVO in $ARCHIVOS_REQUERIDOS) {

    if (!(Test-Path -LiteralPath $ARCHIVO)) {

        Write-Host ""
        Write-Host "ERROR: Falta el archivo:" -ForegroundColor Red
        Write-Host $ARCHIVO -ForegroundColor Red
        Write-Host ""

        exit 1
    }
}

Write-Host "Archivos principales OK." -ForegroundColor Green
Write-Host ""

# ============================================================
# COMPROBAR DATABASE ORIGINAL
# ============================================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       COMPROBANDO DATABASE ORIGINAL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$DATABASE_SIZE_ORIGINAL = (
    Get-Item -LiteralPath $DATABASE_ORIGEN
).Length

Write-Host "Database original encontrada." -ForegroundColor Green
Write-Host "Ruta: $DATABASE_ORIGEN"
Write-Host "Tamaño: $DATABASE_SIZE_ORIGINAL bytes"
Write-Host ""

Write-Host "Comprobando contenido de database original..." -ForegroundColor Cyan

$DB_ORIGEN_TEST = python -c "import sqlite3,sys; p=r'$DATABASE_ORIGEN'; c=sqlite3.connect(p); print('PRODUCTOS:',c.execute('SELECT COUNT(*) FROM productos').fetchone()[0]); print('VENTAS:',c.execute('SELECT COUNT(*) FROM ventas').fetchone()[0]); c.close()"

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: No se pudo leer la database original." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host $DB_ORIGEN_TEST -ForegroundColor Green
Write-Host ""

# ============================================================
# ACTUALIZAR VERSION.TXT
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       ACTUALIZANDO VERSION" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Set-Content `
    -LiteralPath $VERSION_FILE `
    -Value $VERSION `
    -Encoding UTF8

$VERSION_COMPROBADA = (
    Get-Content -LiteralPath $VERSION_FILE -Raw
).Trim()

if ($VERSION_COMPROBADA -ne $VERSION) {

    Write-Host ""
    Write-Host "ERROR: version.txt no contiene $VERSION." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "version.txt = $VERSION" -ForegroundColor Green
Write-Host ""

# ============================================================
# LIMPIAR BUILD Y DIST
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       LIMPIANDO COMPILACIONES" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path -LiteralPath $BUILD_ROOT) {

    Write-Host "Eliminando build..." -ForegroundColor Yellow

    Remove-Item `
        -LiteralPath $BUILD_ROOT `
        -Recurse `
        -Force
}

if (Test-Path -LiteralPath $DIST_ROOT) {

    Write-Host "Eliminando dist..." -ForegroundColor Yellow

    Remove-Item `
        -LiteralPath $DIST_ROOT `
        -Recurse `
        -Force
}

if (Test-Path -LiteralPath $UPDATE_DIR) {

    Write-Host "Eliminando UPDATE_TEMP..." -ForegroundColor Yellow

    Remove-Item `
        -LiteralPath $UPDATE_DIR `
        -Recurse `
        -Force
}

if (Test-Path -LiteralPath $UPDATE_ZIP) {

    Write-Host "Eliminando UPDATE.zip anterior..." -ForegroundColor Yellow

    Remove-Item `
        -LiteralPath $UPDATE_ZIP `
        -Force
}

Write-Host ""
Write-Host "build y dist eliminados." -ForegroundColor Green
Write-Host ""

# ============================================================
# COMPILAR PAPELERA POS
# ============================================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       COMPILANDO PAPELERA POS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

python -m PyInstaller --clean PAPELERA_POS.spec

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: PyInstaller fallo al compilar PAPELERA_POS." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ============================================================
# COMPROBAR EXE
# ============================================================

if (!(Test-Path -LiteralPath $DIST_EXE)) {

    Write-Host ""
    Write-Host "ERROR: No se genero PAPELERA_POS.exe." -ForegroundColor Red
    Write-Host "Esperado:" -ForegroundColor Yellow
    Write-Host $DIST_EXE -ForegroundColor Yellow
    Write-Host ""

    exit 1
}

Write-Host ""
Write-Host "PAPELERA_POS compilado correctamente." -ForegroundColor Green
Write-Host "PAPELERA_POS.exe OK." -ForegroundColor Green
Write-Host ""

# ============================================================
# COMPROBAR _INTERNAL GENERADO POR PYINSTALLER
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       COMPROBANDO _INTERNAL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (!(Test-Path -LiteralPath $DIST_INTERNAL)) {

    Write-Host ""
    Write-Host "ERROR: PyInstaller no genero _internal." -ForegroundColor Red
    Write-Host ""
    Write-Host "Ruta esperada:" -ForegroundColor Yellow
    Write-Host $DIST_INTERNAL -ForegroundColor Yellow
    Write-Host ""

    exit 1
}

Write-Host "_internal encontrado." -ForegroundColor Green
Write-Host ""

# ============================================================
# COMPROBAR BASE_LIBRARY
# ============================================================

if (!(Test-Path -LiteralPath $DIST_BASE_LIBRARY)) {

    Write-Host ""
    Write-Host "ERROR: No se encontro:" -ForegroundColor Red
    Write-Host $DIST_BASE_LIBRARY -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "base_library.zip OK." -ForegroundColor Green
Write-Host ""

# ============================================================
# PREPARAR DATABASE INICIAL
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       PREPARANDO DATABASE INICIAL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (!(Test-Path -LiteralPath $DIST_DATABASE_DIR)) {

    New-Item `
        -ItemType Directory `
        -Path $DIST_DATABASE_DIR `
        -Force `
        | Out-Null
}

Write-Host "Copiando database inicial a dist..." -ForegroundColor Cyan

Copy-Item `
    -LiteralPath $DATABASE_ORIGEN `
    -Destination $DIST_DATABASE `
    -Force

if (!(Test-Path -LiteralPath $DIST_DATABASE)) {

    Write-Host ""
    Write-Host "ERROR: No se pudo copiar abril.db a dist." -ForegroundColor Red
    Write-Host ""

    exit 1
}

$DATABASE_SIZE_DIST = (
    Get-Item -LiteralPath $DIST_DATABASE
).Length

Write-Host ""
Write-Host "Database inicial OK." -ForegroundColor Green
Write-Host "Destino: $DIST_DATABASE" -ForegroundColor Green
Write-Host "Tamaño: $DATABASE_SIZE_DIST bytes" -ForegroundColor Green
Write-Host ""

# ============================================================
# COMPROBAR DATABASE DIST
# ============================================================

Write-Host "Comprobando contenido de database de dist..." -ForegroundColor Cyan

$DB_DIST_TEST = python -c "import sqlite3,sys; p=r'$DIST_DATABASE'; c=sqlite3.connect(p); print('PRODUCTOS:',c.execute('SELECT COUNT(*) FROM productos').fetchone()[0]); print('VENTAS:',c.execute('SELECT COUNT(*) FROM ventas').fetchone()[0]); c.close()"

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: No se pudo leer la database de dist." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host $DB_DIST_TEST -ForegroundColor Green
Write-Host ""

Write-Host "DATABASE INICIAL PREPARADA CORRECTAMENTE." -ForegroundColor Green
Write-Host ""

# ============================================================
# COPIAR VERSION.TXT A DIST
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       PREPARANDO VERSION EN DIST" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Copy-Item `
    -LiteralPath $VERSION_FILE `
    -Destination $DIST_VERSION `
    -Force

if (!(Test-Path -LiteralPath $DIST_VERSION)) {

    Write-Host ""
    Write-Host "ERROR: No se genero version.txt en dist." -ForegroundColor Red
    Write-Host ""

    exit 1
}

$VERSION_DIST = (
    Get-Content -LiteralPath $DIST_VERSION -Raw
).Trim()

if ($VERSION_DIST -ne $VERSION) {

    Write-Host ""
    Write-Host "ERROR: La version de dist no coincide." -ForegroundColor Red
    Write-Host "Esperada: $VERSION"
    Write-Host "Encontrada: $VERSION_DIST"
    Write-Host ""

    exit 1
}

Write-Host "version.txt en dist = $VERSION" -ForegroundColor Green
Write-Host ""

# ============================================================
# COMPILAR PAPELERA UPDATER
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       COMPILANDO PAPELERA UPDATER" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

python -m PyInstaller --clean PAPELERA_UPDATER.spec

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: PyInstaller fallo al compilar PAPELERA_UPDATER." -ForegroundColor Red
    Write-Host ""

    exit 1
}

if (!(Test-Path -LiteralPath $UPDATER_EXE)) {

    Write-Host ""
    Write-Host "ERROR: No se genero PAPELERA_UPDATER.exe." -ForegroundColor Red
    Write-Host "Esperado:" -ForegroundColor Yellow
    Write-Host $UPDATER_EXE -ForegroundColor Yellow
    Write-Host ""

    exit 1
}

Write-Host ""
Write-Host "PAPELERA_UPDATER compilado correctamente." -ForegroundColor Green
Write-Host ""

# ============================================================
# CREAR UPDATE_TEMP
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       PREPARANDO UPDATE.ZIP" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path -LiteralPath $UPDATE_DIR) {

    Remove-Item `
        -LiteralPath $UPDATE_DIR `
        -Recurse `
        -Force
}

New-Item `
    -ItemType Directory `
    -Path $UPDATE_DIR `
    -Force `
    | Out-Null

# ============================================================
# COPIAR EXE AL UPDATE
# ============================================================

Write-Host "Copiando PAPELERA_POS.exe..." -ForegroundColor Cyan

Copy-Item `
    -LiteralPath $DIST_EXE `
    -Destination (Join-Path $UPDATE_DIR "PAPELERA_POS.exe") `
    -Force

# ============================================================
# COPIAR _INTERNAL AL UPDATE
# ============================================================

$UPDATE_INTERNAL = Join-Path $UPDATE_DIR "_internal"

Write-Host "Copiando _internal..." -ForegroundColor Cyan

Copy-Item `
    -LiteralPath $DIST_INTERNAL `
    -Destination $UPDATE_INTERNAL `
    -Recurse `
    -Force

# ============================================================
# COPIAR VERSION.TXT AL UPDATE
# ============================================================

Write-Host "Copiando version.txt..." -ForegroundColor Cyan

Copy-Item `
    -LiteralPath $VERSION_FILE `
    -Destination (Join-Path $UPDATE_DIR "version.txt") `
    -Force

# ============================================================
# ASEGURAR QUE UPDATE_TEMP NO TENGA DATABASE
# ============================================================

$UPDATE_DATABASE = Join-Path $UPDATE_DIR "database"
$UPDATE_BACKUPS = Join-Path $UPDATE_DIR "backups"
$UPDATE_LOGS = Join-Path $UPDATE_DIR "logs"
$UPDATE_ABRIL = Join-Path $UPDATE_DIR "abril.db"

if (Test-Path -LiteralPath $UPDATE_DATABASE) {

    Remove-Item `
        -LiteralPath $UPDATE_DATABASE `
        -Recurse `
        -Force
}

if (Test-Path -LiteralPath $UPDATE_BACKUPS) {

    Remove-Item `
        -LiteralPath $UPDATE_BACKUPS `
        -Recurse `
        -Force
}

if (Test-Path -LiteralPath $UPDATE_LOGS) {

    Remove-Item `
        -LiteralPath $UPDATE_LOGS `
        -Recurse `
        -Force
}

if (Test-Path -LiteralPath $UPDATE_ABRIL) {

    Remove-Item `
        -LiteralPath $UPDATE_ABRIL `
        -Force
}

# ============================================================
# VERIFICAR UPDATE_TEMP
# ============================================================

$UPDATE_TEMP_EXE = Join-Path $UPDATE_DIR "PAPELERA_POS.exe"
$UPDATE_TEMP_VERSION = Join-Path $UPDATE_DIR "version.txt"

if (!(Test-Path -LiteralPath $UPDATE_TEMP_EXE)) {

    Write-Host ""
    Write-Host "ERROR: UPDATE_TEMP no contiene PAPELERA_POS.exe." -ForegroundColor Red
    Write-Host ""

    exit 1
}

if (!(Test-Path -LiteralPath $UPDATE_INTERNAL)) {

    Write-Host ""
    Write-Host "ERROR: UPDATE_TEMP no contiene _internal." -ForegroundColor Red
    Write-Host ""

    exit 1
}

if (!(Test-Path -LiteralPath $UPDATE_TEMP_VERSION)) {

    Write-Host ""
    Write-Host "ERROR: UPDATE_TEMP no contiene version.txt." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host ""
Write-Host "UPDATE_TEMP preparado correctamente." -ForegroundColor Green
Write-Host ""

# ============================================================
# CARGAR SYSTEM.IO.COMPRESSION
# ============================================================

Add-Type -AssemblyName System.IO.Compression.FileSystem

# ============================================================
# CREAR UPDATE.ZIP CON .NET
#
# NO usamos Compress-Archive porque anteriormente
# produjo un error de archivo bloqueado con
# _internal\base_library.zip.
# ============================================================

Write-Host "Creando UPDATE.zip..." -ForegroundColor Cyan

if (Test-Path -LiteralPath $UPDATE_ZIP) {

    Remove-Item `
        -LiteralPath $UPDATE_ZIP `
        -Force
}

[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $UPDATE_DIR,
    $UPDATE_ZIP,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)

# ============================================================
# ELIMINAR UPDATE_TEMP
# ============================================================

if (Test-Path -LiteralPath $UPDATE_DIR) {

    Remove-Item `
        -LiteralPath $UPDATE_DIR `
        -Recurse `
        -Force
}

# ============================================================
# COMPROBAR UPDATE.ZIP
# ============================================================

if (!(Test-Path -LiteralPath $UPDATE_ZIP)) {

    Write-Host ""
    Write-Host "ERROR: No se pudo crear UPDATE.zip." -ForegroundColor Red
    Write-Host ""

    exit 1
}

$UPDATE_SIZE = (
    Get-Item -LiteralPath $UPDATE_ZIP
).Length

Write-Host ""
Write-Host "UPDATE.zip creado correctamente." -ForegroundColor Green
Write-Host "Tamaño: $UPDATE_SIZE bytes" -ForegroundColor Green
Write-Host ""

# ============================================================
# LEER CONTENIDO DEL ZIP
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       VERIFICANDO UPDATE.ZIP" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$ZIP = [System.IO.Compression.ZipFile]::OpenRead(
    (Resolve-Path -LiteralPath $UPDATE_ZIP)
)

$ENTRADAS = @(
    $ZIP.Entries | ForEach-Object {
        $_.FullName
    }
)

Write-Host "Contenido de UPDATE.zip:" -ForegroundColor Cyan
Write-Host ""

foreach ($ENTRY in $ENTRADAS) {

    Write-Host "  $ENTRY"
}

Write-Host ""

# ============================================================
# BUSCAR ARCHIVOS PRINCIPALES
# ============================================================

$TIENE_EXE = $false
$TIENE_VERSION = $false
$TIENE_INTERNAL = $false
$TIENE_DATABASE = $false
$TIENE_ABRIL = $false
$TIENE_BACKUPS = $false
$TIENE_LOGS = $false

foreach ($ENTRY in $ENTRADAS) {

    $NORMAL = $ENTRY.Replace("\", "/").TrimStart("/")

    if ($NORMAL -eq "PAPELERA_POS.exe") {
        $TIENE_EXE = $true
    }

    if ($NORMAL -eq "version.txt") {
        $TIENE_VERSION = $true
    }

    if ($NORMAL -eq "_internal/" -or $NORMAL.StartsWith("_internal/")) {
        $TIENE_INTERNAL = $true
    }

    if ($NORMAL -eq "database/" -or $NORMAL.StartsWith("database/")) {
        $TIENE_DATABASE = $true
    }

    if ($NORMAL -eq "abril.db" -or $NORMAL.EndsWith("/abril.db")) {
        $TIENE_ABRIL = $true
    }

    if ($NORMAL -eq "backups/" -or $NORMAL.StartsWith("backups/")) {
        $TIENE_BACKUPS = $true
    }

    if ($NORMAL -eq "logs/" -or $NORMAL.StartsWith("logs/")) {
        $TIENE_LOGS = $true
    }
}

# ============================================================
# CERRAR ZIP
# ============================================================

$ZIP.Dispose()

# ============================================================
# VERIFICAR EXE
# ============================================================

if (!$TIENE_EXE) {

    Write-Host ""
    Write-Host "ERROR: UPDATE.zip no contiene PAPELERA_POS.exe." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "PAPELERA_POS.exe: OK." -ForegroundColor Green

# ============================================================
# VERIFICAR _INTERNAL
# ============================================================

if (!$TIENE_INTERNAL) {

    Write-Host ""
    Write-Host "ERROR: UPDATE.zip no contiene _internal." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "_internal: OK." -ForegroundColor Green

# ============================================================
# VERIFICAR VERSION
# ============================================================

if (!$TIENE_VERSION) {

    Write-Host ""
    Write-Host "ERROR: UPDATE.zip no contiene version.txt." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "version.txt: OK." -ForegroundColor Green

# ============================================================
# VERIFICAR DATABASE
# ============================================================

if ($TIENE_DATABASE) {

    Write-Host ""
    Write-Host "ERROR: UPDATE.zip contiene DATABASE." -ForegroundColor Red
    Write-Host ""

    exit 1
}

if ($TIENE_ABRIL) {

    Write-Host ""
    Write-Host "ERROR: UPDATE.zip contiene abril.db." -ForegroundColor Red
    Write-Host ""

    exit 1
}

if ($TIENE_BACKUPS) {

    Write-Host ""
    Write-Host "ERROR: UPDATE.zip contiene backups." -ForegroundColor Red
    Write-Host ""

    exit 1
}

if ($TIENE_LOGS) {

    Write-Host ""
    Write-Host "ERROR: UPDATE.zip contiene logs." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "DATABASE: NO incluida." -ForegroundColor Green
Write-Host "abril.db: NO incluido." -ForegroundColor Green
Write-Host "BACKUPS: NO incluidos." -ForegroundColor Green
Write-Host "LOGS: NO incluidos." -ForegroundColor Green
Write-Host ""

# ============================================================
# VERIFICAR VERSION DENTRO DEL ZIP
# ============================================================

$ZIP_VERSION_DIR = Join-Path $ROOT "ZIP_VERSION_CHECK"

if (Test-Path -LiteralPath $ZIP_VERSION_DIR) {

    Remove-Item `
        -LiteralPath $ZIP_VERSION_DIR `
        -Recurse `
        -Force
}

New-Item `
    -ItemType Directory `
    -Path $ZIP_VERSION_DIR `
    -Force `
    | Out-Null

try {

    Expand-Archive `
        -LiteralPath $UPDATE_ZIP `
        -DestinationPath $ZIP_VERSION_DIR `
        -Force

    $ZIP_VERSION_FILE = Join-Path $ZIP_VERSION_DIR "version.txt"

    if (!(Test-Path -LiteralPath $ZIP_VERSION_FILE)) {

        throw "version.txt no fue encontrado despues de extraer UPDATE.zip."
    }

    $ZIP_VERSION = (
        Get-Content -LiteralPath $ZIP_VERSION_FILE -Raw
    ).Trim()

    if ($ZIP_VERSION -ne $VERSION) {

        throw "La version dentro de UPDATE.zip es $ZIP_VERSION y se esperaba $VERSION."
    }

    Write-Host "Version dentro de UPDATE.zip = $ZIP_VERSION" -ForegroundColor Green
}
finally {

    if (Test-Path -LiteralPath $ZIP_VERSION_DIR) {

        Remove-Item `
            -LiteralPath $ZIP_VERSION_DIR `
            -Recurse `
            -Force
    }
}

Write-Host ""

# ============================================================
# RESULTADO FINAL DEL ZIP
# ============================================================

Write-Host "============================================" -ForegroundColor Green
Write-Host "   UPDATE.ZIP GENERADO Y VERIFICADO" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

Write-Host "UPDATE.zip contiene:" -ForegroundColor Cyan
Write-Host "  - PAPELERA_POS.exe"
Write-Host "  - _internal"
Write-Host "  - version.txt"
Write-Host ""

Write-Host "UPDATE.zip NO contiene:" -ForegroundColor Cyan
Write-Host "  - database"
Write-Host "  - abril.db"
Write-Host "  - backups"
Write-Host "  - logs"
Write-Host ""

# ============================================================
# GIT STATUS
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "             GIT" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

git status

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: git status fallo." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ============================================================
# COMPROBAR TAG
# ============================================================

$TAG_EXISTE_LOCAL = git tag -l $TAG

if ($TAG_EXISTE_LOCAL -eq $TAG) {

    Write-Host ""
    Write-Host "ERROR: El tag $TAG ya existe localmente." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ============================================================
# GIT ADD
# ============================================================

Write-Host ""
Write-Host "Agregando cambios a Git..." -ForegroundColor Cyan

git add .

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: git add fallo." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ============================================================
# GIT STATUS
# ============================================================

Write-Host ""
Write-Host "Cambios preparados:" -ForegroundColor Cyan
Write-Host ""

git status --short

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: git status fallo." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ============================================================
# GIT COMMIT
# ============================================================

Write-Host ""
Write-Host "Creando commit..." -ForegroundColor Cyan

git commit -m "Version $VERSION"

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: git commit fallo." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ============================================================
# GIT PUSH
# ============================================================

Write-Host ""
Write-Host "Subiendo cambios a GitHub..." -ForegroundColor Cyan

git push

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: git push fallo." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ============================================================
# CREAR TAG
# ============================================================

Write-Host ""
Write-Host "Creando tag $TAG..." -ForegroundColor Cyan

git tag $TAG

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: No se pudo crear el tag $TAG." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ============================================================
# SUBIR TAG
# ============================================================

Write-Host ""
Write-Host "Subiendo tag $TAG a GitHub..." -ForegroundColor Cyan

git push origin $TAG

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: No se pudo subir el tag $TAG." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ============================================================
# FINAL
# ============================================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "       VERSION PUBLICADA CORRECTAMENTE" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

Write-Host "Version: $VERSION" -ForegroundColor Green
Write-Host "Tag: $TAG" -ForegroundColor Green
Write-Host "UPDATE.zip: $UPDATE_ZIP" -ForegroundColor Green
Write-Host ""

Write-Host "============================================" -ForegroundColor Yellow
Write-Host "       RESUMEN DE LA VERSION" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "INSTALACION INICIAL:" -ForegroundColor Cyan
Write-Host "  - PAPELERA_POS.exe"
Write-Host "  - _internal"
Write-Host "  - database\abril.db"
Write-Host "  - version.txt"
Write-Host ""

Write-Host "ACTUALIZACION:" -ForegroundColor Cyan
Write-Host "  - PAPELERA_POS.exe"
Write-Host "  - _internal"
Write-Host "  - version.txt"
Write-Host ""

Write-Host "NO SE ACTUALIZA:" -ForegroundColor Cyan
Write-Host "  - database\abril.db"
Write-Host "  - backups"
Write-Host "  - logs"
Write-Host ""

Write-Host "UPDATE.zip generado y verificado correctamente." -ForegroundColor Green
Write-Host "La database NO fue incluida en UPDATE.zip." -ForegroundColor Green
Write-Host "La database de una instalacion existente NO sera reemplazada por el updater." -ForegroundColor Green
Write-Host ""

Write-Host "GitHub Actions deberia generar/publicar ahora el Release." -ForegroundColor Yellow
Write-Host ""

# ============================================================
# FIN
# ============================================================
