$ErrorActionPreference = "Stop"

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
# VERSION
# ============================================================

if ($args.Count -lt 1) {
    Write-Host "ERROR: No se indico la version." -ForegroundColor Red
    Write-Host "Uso: .\SUBIR_VERSION.ps1 1.0.52"
    exit 1
}

$VERSION = $args[0].ToString().Trim()

if ($VERSION -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host "ERROR: Version invalida: $VERSION" -ForegroundColor Red
    exit 1
}

$TAG = "v$VERSION"

# ============================================================
# RUTAS
# ============================================================

$VERSION_FILE = Join-Path $ROOT "version.txt"
$DATABASE_ORIGEN = Join-Path $ROOT "database\abril.db"

$DIST_ROOT = Join-Path $ROOT "dist"
$DIST_APP = Join-Path $DIST_ROOT "PAPELERA_POS"
$DIST_EXE = Join-Path $DIST_APP "PAPELERA_POS.exe"
$DIST_INTERNAL = Join-Path $DIST_APP "_internal"
$DIST_DATABASE_DIR = Join-Path $DIST_APP "database"
$DIST_DATABASE = Join-Path $DIST_DATABASE_DIR "abril.db"
$DIST_VERSION = Join-Path $DIST_APP "version.txt"

$DIST_BASE_LIBRARY = Join-Path $DIST_INTERNAL "base_library.zip"

$DIST_DOTENV = Join-Path $DIST_INTERNAL "dotenv"
$DIST_DOTENV_INIT = Join-Path $DIST_DOTENV "__init__.py"

$UPDATE_DIR = Join-Path $ROOT "UPDATE_TEMP"
$UPDATE_ZIP = Join-Path $ROOT "UPDATE.zip"

$UPDATER_DIST = Join-Path $DIST_ROOT "PAPELERA_UPDATER"
$UPDATER_EXE = Join-Path $UPDATER_DIST "PAPELERA_UPDATER.exe"

$BUILD_ROOT = Join-Path $ROOT "build"

# ============================================================
# VERSION ACTUAL
# ============================================================

if (Test-Path -LiteralPath $VERSION_FILE) {
    $VERSION_ACTUAL = (Get-Content -LiteralPath $VERSION_FILE -Raw).Trim()
}
else {
    $VERSION_ACTUAL = "1.0.0"
}

Write-Host "Version actual: $VERSION_ACTUAL"
Write-Host "Nueva version:  $VERSION" -ForegroundColor Yellow
Write-Host "Nuevo tag:      $TAG" -ForegroundColor Yellow
Write-Host ""

$CONFIRMAR = Read-Host "Continuar con la version $VERSION (S/N)"

if ($CONFIRMAR -notmatch '^[sS]$') {
    Write-Host ""
    Write-Host "Operacion cancelada." -ForegroundColor Yellow
    exit 0
}

# ============================================================
# ARCHIVOS REQUERIDOS
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
# DATABASE ORIGINAL
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       COMPROBANDO DATABASE ORIGINAL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$DATABASE_SIZE_ORIGINAL = (Get-Item -LiteralPath $DATABASE_ORIGEN).Length

Write-Host "Database encontrada."
Write-Host "Ruta: $DATABASE_ORIGEN"
Write-Host "Tamano: $DATABASE_SIZE_ORIGINAL bytes"
Write-Host ""

$DB_ORIGEN_TEST = python -c "import sqlite3; p=r'$DATABASE_ORIGEN'; c=sqlite3.connect(p); print('PRODUCTOS:',c.execute('SELECT COUNT(*) FROM productos').fetchone()[0]); print('VENTAS:',c.execute('SELECT COUNT(*) FROM ventas').fetchone()[0]); c.close()"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: No se pudo leer la database original." -ForegroundColor Red
    exit 1
}

Write-Host $DB_ORIGEN_TEST -ForegroundColor Green
Write-Host ""

# ============================================================
# VERSION.TXT
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       ACTUALIZANDO VERSION" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Set-Content -LiteralPath $VERSION_FILE -Value $VERSION -Encoding UTF8

$VERSION_COMPROBADA = (Get-Content -LiteralPath $VERSION_FILE -Raw).Trim()

if ($VERSION_COMPROBADA -ne $VERSION) {
    Write-Host "ERROR: version.txt no contiene $VERSION." -ForegroundColor Red
    exit 1
}

Write-Host "version.txt = $VERSION" -ForegroundColor Green
Write-Host ""

# ============================================================
# LIMPIAR
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       LIMPIANDO COMPILACIONES" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path -LiteralPath $BUILD_ROOT) {
    Write-Host "Eliminando build..." -ForegroundColor Yellow
    Remove-Item -LiteralPath $BUILD_ROOT -Recurse -Force
}

if (Test-Path -LiteralPath $DIST_ROOT) {
    Write-Host "Eliminando dist..." -ForegroundColor Yellow
    Remove-Item -LiteralPath $DIST_ROOT -Recurse -Force
}

if (Test-Path -LiteralPath $UPDATE_DIR) {
    Write-Host "Eliminando UPDATE_TEMP..." -ForegroundColor Yellow
    Remove-Item -LiteralPath $UPDATE_DIR -Recurse -Force
}

if (Test-Path -LiteralPath $UPDATE_ZIP) {
    Write-Host "Eliminando UPDATE.zip anterior..." -ForegroundColor Yellow
    Remove-Item -LiteralPath $UPDATE_ZIP -Force
}

Write-Host ""
Write-Host "Limpieza terminada." -ForegroundColor Green
Write-Host ""

# ============================================================
# COMPILAR PAPELERA POS
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       COMPILANDO PAPELERA POS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

python -m PyInstaller --clean PAPELERA_POS.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: PyInstaller fallo al compilar PAPELERA POS." -ForegroundColor Red
    exit 1
}

if (!(Test-Path -LiteralPath $DIST_EXE)) {
    Write-Host ""
    Write-Host "ERROR: No se genero PAPELERA_POS.exe." -ForegroundColor Red
    Write-Host $DIST_EXE -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "PAPELERA_POS.exe generado correctamente." -ForegroundColor Green
Write-Host ""

# ============================================================
# COMPROBAR _INTERNAL
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       COMPROBANDO _INTERNAL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (!(Test-Path -LiteralPath $DIST_INTERNAL)) {
    Write-Host "ERROR: PyInstaller no genero _internal." -ForegroundColor Red
    exit 1
}

Write-Host "_internal encontrado." -ForegroundColor Green
Write-Host ""

if (!(Test-Path -LiteralPath $DIST_BASE_LIBRARY)) {
    Write-Host "ERROR: No se encontro base_library.zip." -ForegroundColor Red
    exit 1
}

Write-Host "base_library.zip OK." -ForegroundColor Green
Write-Host ""

# ============================================================
# CRITICO:
# VERIFICAR DEPENDENCIAS DE SUPABASE EN DIST
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       VERIFICANDO SUPABASE EN DIST" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$SUPABASE_CARPETAS = @(
    "supabase",
    "postgrest",
    "realtime",
    "storage3",
    "supabase_auth",
    "supabase_functions",
    "pydantic"
)

foreach ($NOMBRE in $SUPABASE_CARPETAS) {

    $RUTA = Join-Path $DIST_INTERNAL $NOMBRE

    if (!(Test-Path -LiteralPath $RUTA -PathType Container)) {
        Write-Host ""
        Write-Host "ERROR CRITICO: Falta $NOMBRE en _internal." -ForegroundColor Red
        Write-Host "Ruta esperada: $RUTA" -ForegroundColor Red
        Write-Host ""
        Write-Host "NO se continuara con la publicacion." -ForegroundColor Red
        exit 1
    }

    $ARCHIVOS = @(
        Get-ChildItem `
            -LiteralPath $RUTA `
            -Recurse `
            -File `
            -ErrorAction SilentlyContinue
    )

    if ($ARCHIVOS.Count -eq 0) {
        Write-Host ""
        Write-Host "ERROR CRITICO: $NOMBRE existe pero esta vacio." -ForegroundColor Red
        Write-Host "Ruta: $RUTA" -ForegroundColor Red
        exit 1
    }

    Write-Host "_internal\$NOMBRE : OK ($($ARCHIVOS.Count) archivos)." -ForegroundColor Green
}

Write-Host ""
Write-Host "Todas las dependencias de Supabase estan presentes en dist." -ForegroundColor Green
Write-Host ""

# ============================================================
# CRITICO:
# VERIFICAR QUE PYINSTALLER NO HAYA METIDO abril.db
# DENTRO DE _internal
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       VERIFICANDO DATABASE EN _INTERNAL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$INTERNAL_DB_FILES = @(
    Get-ChildItem `
        -LiteralPath $DIST_INTERNAL `
        -Recurse `
        -File `
        -Filter "abril.db" `
        -ErrorAction SilentlyContinue
)

if ($INTERNAL_DB_FILES.Count -gt 0) {

    Write-Host ""
    Write-Host "ERROR CRITICO: PyInstaller incluyo abril.db dentro de _internal." -ForegroundColor Red
    Write-Host ""

    foreach ($DB_FILE in $INTERNAL_DB_FILES) {
        Write-Host $DB_FILE.FullName -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "NO se continuara con la publicacion." -ForegroundColor Red

    exit 1
}

Write-Host "Correcto: _internal NO contiene abril.db." -ForegroundColor Green
Write-Host ""

# ============================================================
# COMPROBAR DOTENV
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       COMPROBANDO PYTHON-DOTENV" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Carpeta dotenv:"
Write-Host $DIST_DOTENV -ForegroundColor DarkGray
Write-Host ""

Write-Host "Archivo __init__.py:"
Write-Host $DIST_DOTENV_INIT -ForegroundColor DarkGray
Write-Host ""

if (!(Test-Path -LiteralPath $DIST_DOTENV)) {
    Write-Host "ERROR CRITICO: No existe la carpeta dotenv." -ForegroundColor Red
    exit 1
}

if (!(Test-Path -LiteralPath $DIST_DOTENV_INIT)) {
    Write-Host "ERROR CRITICO: No existe dotenv\__init__.py." -ForegroundColor Red
    exit 1
}

Write-Host "dotenv encontrado correctamente." -ForegroundColor Green
Write-Host "__init__.py encontrado correctamente." -ForegroundColor Green
Write-Host ""

# ============================================================
# PREPARAR DATABASE INICIAL
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       PREPARANDO DATABASE INICIAL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (!(Test-Path -LiteralPath $DIST_DATABASE_DIR)) {
    New-Item -ItemType Directory -Path $DIST_DATABASE_DIR -Force | Out-Null
}

Write-Host "Copiando database inicial a dist..." -ForegroundColor Cyan

Copy-Item `
    -LiteralPath $DATABASE_ORIGEN `
    -Destination $DIST_DATABASE `
    -Force

if (!(Test-Path -LiteralPath $DIST_DATABASE)) {
    Write-Host ""
    Write-Host "ERROR: No se pudo copiar abril.db a dist." -ForegroundColor Red
    exit 1
}

$DATABASE_SIZE_DIST = (Get-Item -LiteralPath $DIST_DATABASE).Length

Write-Host ""
Write-Host "Database inicial OK." -ForegroundColor Green
Write-Host "Destino: $DIST_DATABASE" -ForegroundColor Green
Write-Host "Tamano: $DATABASE_SIZE_DIST bytes" -ForegroundColor Green
Write-Host ""

$DB_DIST_TEST = python -c "import sqlite3; p=r'$DIST_DATABASE'; c=sqlite3.connect(p); print('PRODUCTOS:',c.execute('SELECT COUNT(*) FROM productos').fetchone()[0]); print('VENTAS:',c.execute('SELECT COUNT(*) FROM ventas').fetchone()[0]); c.close()"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: No se pudo leer la database de dist." -ForegroundColor Red
    exit 1
}

Write-Host $DB_DIST_TEST -ForegroundColor Green
Write-Host ""

# ============================================================
# COPIAR VERSION A DIST
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
    Write-Host "ERROR: No se genero version.txt en dist." -ForegroundColor Red
    exit 1
}

$VERSION_DIST = (Get-Content -LiteralPath $DIST_VERSION -Raw).Trim()

if ($VERSION_DIST -ne $VERSION) {
    Write-Host "ERROR: La version de dist no coincide." -ForegroundColor Red
    Write-Host "Esperada: $VERSION"
    Write-Host "Encontrada: $VERSION_DIST"
    exit 1
}

Write-Host "version.txt en dist = $VERSION" -ForegroundColor Green
Write-Host ""

# ============================================================
# CREAR CARPETAS DE INSTALACION INICIAL
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       PREPARANDO CARPETAS INICIALES" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$DIST_BACKUPS = Join-Path $DIST_APP "backups"
$DIST_LOGS = Join-Path $DIST_APP "logs"
$DIST_TICKETS = Join-Path $DIST_APP "tickets"

New-Item -ItemType Directory -Path $DIST_BACKUPS -Force | Out-Null
New-Item -ItemType Directory -Path $DIST_LOGS -Force | Out-Null
New-Item -ItemType Directory -Path $DIST_TICKETS -Force | Out-Null

Write-Host "backups OK." -ForegroundColor Green
Write-Host "logs OK." -ForegroundColor Green
Write-Host "tickets OK." -ForegroundColor Green
Write-Host ""

# ============================================================
# COMPILAR UPDATER
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       COMPILANDO PAPELERA UPDATER" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

python -m PyInstaller --clean PAPELERA_UPDATER.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: PyInstaller fallo al compilar PAPELERA_UPDATER." -ForegroundColor Red
    exit 1
}

if (!(Test-Path -LiteralPath $UPDATER_EXE)) {
    Write-Host ""
    Write-Host "ERROR: No se genero PAPELERA_UPDATER.exe." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "PAPELERA_UPDATER compilado correctamente." -ForegroundColor Green
Write-Host ""

# ============================================================
# PREPARAR UPDATE_TEMP
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       PREPARANDO UPDATE.ZIP" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path -LiteralPath $UPDATE_DIR) {
    Remove-Item -LiteralPath $UPDATE_DIR -Recurse -Force
}

New-Item -ItemType Directory -Path $UPDATE_DIR -Force | Out-Null

# ============================================================
# COPIAR EXE
# ============================================================

Write-Host "Copiando PAPELERA_POS.exe..." -ForegroundColor Cyan

Copy-Item `
    -LiteralPath $DIST_EXE `
    -Destination (Join-Path $UPDATE_DIR "PAPELERA_POS.exe") `
    -Force

# ============================================================
# COPIAR _INTERNAL
# ============================================================

$UPDATE_INTERNAL = Join-Path $UPDATE_DIR "_internal"

Write-Host "Copiando _internal..." -ForegroundColor Cyan

Copy-Item `
    -LiteralPath $DIST_INTERNAL `
    -Destination $UPDATE_INTERNAL `
    -Recurse `
    -Force

# ============================================================
# COPIAR VERSION
# ============================================================

Write-Host "Copiando version.txt..." -ForegroundColor Cyan

Copy-Item `
    -LiteralPath $VERSION_FILE `
    -Destination (Join-Path $UPDATE_DIR "version.txt") `
    -Force

# ============================================================
# ELIMINAR ELEMENTOS DE INSTALACION INICIAL
# DEL UPDATE
# ============================================================

$UPDATE_DATABASE = Join-Path $UPDATE_DIR "database"
$UPDATE_BACKUPS = Join-Path $UPDATE_DIR "backups"
$UPDATE_LOGS = Join-Path $UPDATE_DIR "logs"
$UPDATE_TICKETS = Join-Path $UPDATE_DIR "tickets"
$UPDATE_ABRIL = Join-Path $UPDATE_DIR "abril.db"

foreach ($RUTA in @(
    $UPDATE_DATABASE,
    $UPDATE_BACKUPS,
    $UPDATE_LOGS,
    $UPDATE_TICKETS
)) {

    if (Test-Path -LiteralPath $RUTA) {
        Remove-Item `
            -LiteralPath $RUTA `
            -Recurse `
            -Force
    }
}

if (Test-Path -LiteralPath $UPDATE_ABRIL) {
    Remove-Item `
        -LiteralPath $UPDATE_ABRIL `
        -Force
}

# ============================================================
# CRITICO:
# EL UPDATE NO PUEDE CONTENER abril.db
# NI DENTRO NI FUERA DE _internal
# ============================================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       BUSCANDO abril.db EN UPDATE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$UPDATE_DB_FILES = @(
    Get-ChildItem `
        -LiteralPath $UPDATE_DIR `
        -Recurse `
        -File `
        -Filter "abril.db" `
        -ErrorAction SilentlyContinue
)

if ($UPDATE_DB_FILES.Count -gt 0) {

    Write-Host ""
    Write-Host "ERROR CRITICO: UPDATE_TEMP contiene abril.db." -ForegroundColor Red
    Write-Host ""

    foreach ($DB_FILE in $UPDATE_DB_FILES) {
        Write-Host $DB_FILE.FullName -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "NO se continuara con la publicacion." -ForegroundColor Red

    exit 1
}

Write-Host "Correcto: UPDATE_TEMP NO contiene abril.db." -ForegroundColor Green
Write-Host ""

# ============================================================
# VERIFICAR UPDATE_TEMP
# ============================================================

$UPDATE_TEMP_EXE = Join-Path $UPDATE_DIR "PAPELERA_POS.exe"
$UPDATE_TEMP_VERSION = Join-Path $UPDATE_DIR "version.txt"

if (!(Test-Path -LiteralPath $UPDATE_TEMP_EXE)) {
    Write-Host "ERROR: UPDATE_TEMP no contiene PAPELERA_POS.exe." -ForegroundColor Red
    exit 1
}

if (!(Test-Path -LiteralPath $UPDATE_INTERNAL)) {
    Write-Host "ERROR: UPDATE_TEMP no contiene _internal." -ForegroundColor Red
    exit 1
}

if (!(Test-Path -LiteralPath $UPDATE_TEMP_VERSION)) {
    Write-Host "ERROR: UPDATE_TEMP no contiene version.txt." -ForegroundColor Red
    exit 1
}

# ============================================================
# COMPROBAR DOTENV DENTRO DEL UPDATE
# ============================================================

$UPDATE_DOTENV = Join-Path $UPDATE_INTERNAL "dotenv"
$UPDATE_DOTENV_INIT = Join-Path $UPDATE_DOTENV "__init__.py"

if (!(Test-Path -LiteralPath $UPDATE_DOTENV)) {
    Write-Host ""
    Write-Host "ERROR CRITICO: UPDATE_TEMP no contiene dotenv." -ForegroundColor Red
    exit 1
}

if (!(Test-Path -LiteralPath $UPDATE_DOTENV_INIT)) {
    Write-Host ""
    Write-Host "ERROR CRITICO: UPDATE_TEMP no contiene dotenv\__init__.py." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "dotenv dentro del UPDATE: OK." -ForegroundColor Green
Write-Host ""

# ============================================================
# CRITICO:
# VERIFICAR DEPENDENCIAS DE SUPABASE EN UPDATE_TEMP
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       VERIFICANDO SUPABASE EN UPDATE_TEMP" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

foreach ($NOMBRE in $SUPABASE_CARPETAS) {

    $RUTA = Join-Path $UPDATE_INTERNAL $NOMBRE

    if (!(Test-Path -LiteralPath $RUTA -PathType Container)) {
        Write-Host ""
        Write-Host "ERROR CRITICO: UPDATE_TEMP no contiene _internal\$NOMBRE." -ForegroundColor Red
        Write-Host "Ruta: $RUTA" -ForegroundColor Red
        Write-Host ""
        Write-Host "NO se creara/publicara el update." -ForegroundColor Red
        exit 1
    }

    $ARCHIVOS = @(
        Get-ChildItem `
            -LiteralPath $RUTA `
            -Recurse `
            -File `
            -ErrorAction SilentlyContinue
    )

    if ($ARCHIVOS.Count -eq 0) {
        Write-Host ""
        Write-Host "ERROR CRITICO: UPDATE_TEMP contiene _internal\$NOMBRE pero esta vacio." -ForegroundColor Red
        exit 1
    }

    Write-Host "UPDATE_TEMP\_internal\$NOMBRE : OK ($($ARCHIVOS.Count) archivos)." -ForegroundColor Green
}

Write-Host ""
Write-Host "UPDATE_TEMP contiene todas las dependencias de Supabase." -ForegroundColor Green
Write-Host ""

# ============================================================
# CREAR UPDATE.ZIP
# ============================================================

Add-Type -AssemblyName System.IO.Compression.FileSystem

Write-Host "Creando UPDATE.zip..." -ForegroundColor Cyan

if (Test-Path -LiteralPath $UPDATE_ZIP) {
    Remove-Item -LiteralPath $UPDATE_ZIP -Force
}

[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $UPDATE_DIR,
    $UPDATE_ZIP,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)

# ============================================================
# COMPROBAR ZIP
# ============================================================

if (!(Test-Path -LiteralPath $UPDATE_ZIP)) {
    Write-Host "ERROR: No se pudo crear UPDATE.zip." -ForegroundColor Red
    exit 1
}

$UPDATE_SIZE = (Get-Item -LiteralPath $UPDATE_ZIP).Length

Write-Host ""
Write-Host "UPDATE.zip creado correctamente." -ForegroundColor Green
Write-Host "Tamano: $UPDATE_SIZE bytes" -ForegroundColor Green
Write-Host ""

# ============================================================
# LEER ZIP
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       VERIFICANDO UPDATE.ZIP" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$ZIP = [System.IO.Compression.ZipFile]::OpenRead(
    (Resolve-Path -LiteralPath $UPDATE_ZIP)
)

$ENTRADAS = @(
    $ZIP.Entries |
        ForEach-Object {
            $_.FullName
        }
)

Write-Host "Contenido de UPDATE.zip:" -ForegroundColor Cyan
Write-Host ""

foreach ($ENTRY in $ENTRADAS) {
    Write-Host "  $ENTRY"
}

Write-Host ""

$TIENE_EXE = $false
$TIENE_VERSION = $false
$TIENE_INTERNAL = $false
$TIENE_DOTENV = $false
$TIENE_DOTENV_INIT = $false
$TIENE_SUPABASE = $false
$TIENE_POSTGREST = $false
$TIENE_REALTIME = $false
$TIENE_STORAGE3 = $false
$TIENE_SUPABASE_AUTH = $false
$TIENE_SUPABASE_FUNCTIONS = $false
$TIENE_PYDANTIC = $false
$TIENE_DATABASE = $false
$TIENE_ABRIL = $false
$TIENE_BACKUPS = $false
$TIENE_LOGS = $false
$TIENE_TICKETS = $false

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

    if ($NORMAL -eq "_internal/dotenv/" -or $NORMAL.StartsWith("_internal/dotenv/")) {
        $TIENE_DOTENV = $true
    }

    if ($NORMAL -eq "_internal/dotenv/__init__.py") {
        $TIENE_DOTENV_INIT = $true
    }

    if ($NORMAL -eq "_internal/supabase/" -or $NORMAL.StartsWith("_internal/supabase/")) {
        $TIENE_SUPABASE = $true
    }

    if ($NORMAL -eq "_internal/postgrest/" -or $NORMAL.StartsWith("_internal/postgrest/")) {
        $TIENE_POSTGREST = $true
    }

    if ($NORMAL -eq "_internal/realtime/" -or $NORMAL.StartsWith("_internal/realtime/")) {
        $TIENE_REALTIME = $true
    }

    if ($NORMAL -eq "_internal/storage3/" -or $NORMAL.StartsWith("_internal/storage3/")) {
        $TIENE_STORAGE3 = $true
    }

    if ($NORMAL -eq "_internal/supabase_auth/" -or $NORMAL.StartsWith("_internal/supabase_auth/")) {
        $TIENE_SUPABASE_AUTH = $true
    }

    if ($NORMAL -eq "_internal/supabase_functions/" -or $NORMAL.StartsWith("_internal/supabase_functions/")) {
        $TIENE_SUPABASE_FUNCTIONS = $true
    }

    if ($NORMAL -eq "_internal/pydantic/" -or $NORMAL.StartsWith("_internal/pydantic/")) {
        $TIENE_PYDANTIC = $true
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

    if ($NORMAL -eq "tickets/" -or $NORMAL.StartsWith("tickets/")) {
        $TIENE_TICKETS = $true
    }
}

$ZIP.Dispose()

# ============================================================
# VALIDACIONES
# ============================================================

if (!$TIENE_EXE) {
    Write-Host "ERROR: UPDATE.zip no contiene PAPELERA_POS.exe." -ForegroundColor Red
    exit 1
}

Write-Host "PAPELERA_POS.exe: OK." -ForegroundColor Green

if (!$TIENE_INTERNAL) {
    Write-Host "ERROR: UPDATE.zip no contiene _internal." -ForegroundColor Red
    exit 1
}

Write-Host "_internal: OK." -ForegroundColor Green

if (!$TIENE_VERSION) {
    Write-Host "ERROR: UPDATE.zip no contiene version.txt." -ForegroundColor Red
    exit 1
}

Write-Host "version.txt: OK." -ForegroundColor Green

if (!$TIENE_DOTENV) {
    Write-Host "ERROR CRITICO: UPDATE.zip no contiene _internal/dotenv." -ForegroundColor Red
    exit 1
}

Write-Host "_internal/dotenv: OK." -ForegroundColor Green

if (!$TIENE_DOTENV_INIT) {
    Write-Host "ERROR CRITICO: UPDATE.zip no contiene _internal/dotenv/__init__.py." -ForegroundColor Red
    exit 1
}


$DEPENDENCIAS_ZIP = @(
    @{ Nombre = "supabase"; Variable = $TIENE_SUPABASE },
    @{ Nombre = "postgrest"; Variable = $TIENE_POSTGREST },
    @{ Nombre = "realtime"; Variable = $TIENE_REALTIME },
    @{ Nombre = "storage3"; Variable = $TIENE_STORAGE3 },
    @{ Nombre = "supabase_auth"; Variable = $TIENE_SUPABASE_AUTH },
    @{ Nombre = "supabase_functions"; Variable = $TIENE_SUPABASE_FUNCTIONS },
    @{ Nombre = "pydantic"; Variable = $TIENE_PYDANTIC }
)

Write-Host ""
Write-Host "Verificando dependencias Supabase dentro de UPDATE.zip..." -ForegroundColor Cyan

foreach ($DEPENDENCIA in $DEPENDENCIAS_ZIP) {

    if (!$DEPENDENCIA.Variable) {
        Write-Host ""
        Write-Host "ERROR CRITICO: UPDATE.zip NO contiene _internal\$($DEPENDENCIA.Nombre)." -ForegroundColor Red
        Write-Host ""
        Write-Host "El update NO sera publicado." -ForegroundColor Red
        exit 1
    }

    Write-Host "_internal\$($DEPENDENCIA.Nombre): OK." -ForegroundColor Green
}

Write-Host ""
Write-Host "Todas las dependencias Supabase estan dentro de UPDATE.zip." -ForegroundColor Green

if ($TIENE_DATABASE) {
    Write-Host "ERROR: UPDATE.zip contiene database." -ForegroundColor Red
    exit 1
}

if ($TIENE_ABRIL) {
    Write-Host "ERROR: UPDATE.zip contiene abril.db." -ForegroundColor Red
    exit 1
}

if ($TIENE_BACKUPS) {
    Write-Host "ERROR: UPDATE.zip contiene backups." -ForegroundColor Red
    exit 1
}

if ($TIENE_LOGS) {
    Write-Host "ERROR: UPDATE.zip contiene logs." -ForegroundColor Red
    exit 1
}

if ($TIENE_TICKETS) {
    Write-Host "ERROR: UPDATE.zip contiene tickets." -ForegroundColor Red
    exit 1
}

Write-Host "DATABASE: NO incluida." -ForegroundColor Green
Write-Host "abril.db: NO incluido." -ForegroundColor Green
Write-Host "BACKUPS: NO incluidos." -ForegroundColor Green
Write-Host "LOGS: NO incluidos." -ForegroundColor Green
Write-Host "TICKETS: NO incluidos." -ForegroundColor Green
Write-Host ""


# ============================================================
# COMPROBAR VERSION DENTRO DEL ZIP
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       VERIFICANDO CONTENIDO DEL ZIP" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$ZIP_VERSION_DIR = Join-Path $ROOT "ZIP_VERSION_CHECK"

# ------------------------------------------------------------
# LIMPIAR CARPETA ANTERIOR
# ------------------------------------------------------------

if (Test-Path -LiteralPath $ZIP_VERSION_DIR) {

    Write-Host "Eliminando ZIP_VERSION_CHECK anterior..." -ForegroundColor Yellow

    Remove-Item `
        -LiteralPath $ZIP_VERSION_DIR `
        -Recurse `
        -Force
}

# ------------------------------------------------------------
# CREAR CARPETA
# ------------------------------------------------------------

New-Item `
    -ItemType Directory `
    -Path $ZIP_VERSION_DIR `
    -Force |
    Out-Null

# ------------------------------------------------------------
# IMPORTANTE:
# DEFINIR SIEMPRE LA RUTA DEL version.txt
# ANTES DE USAR Test-Path
# ------------------------------------------------------------

$ZIP_VERSION_FILE = Join-Path `
    $ZIP_VERSION_DIR `
    "version.txt"

if ([string]::IsNullOrWhiteSpace($ZIP_VERSION_FILE)) {

    Write-Host ""
    Write-Host "ERROR CRITICO: No se pudo determinar la ruta de version.txt." -ForegroundColor Red
    Write-Host ""

    if (Test-Path -LiteralPath $ZIP_VERSION_DIR) {

        Remove-Item `
            -LiteralPath $ZIP_VERSION_DIR `
            -Recurse `
            -Force
    }

    exit 1
}

Write-Host "Carpeta de verificacion:" -ForegroundColor DarkGray
Write-Host $ZIP_VERSION_DIR -ForegroundColor DarkGray

Write-Host ""
Write-Host "version.txt esperado en:" -ForegroundColor DarkGray
Write-Host $ZIP_VERSION_FILE -ForegroundColor DarkGray
Write-Host ""

# ------------------------------------------------------------
# EXTRAER UPDATE.ZIP
# ------------------------------------------------------------

try {

    Write-Host "Extrayendo UPDATE.zip para verificacion..." -ForegroundColor Cyan

    Expand-Archive `
        -LiteralPath $UPDATE_ZIP `
        -DestinationPath $ZIP_VERSION_DIR `
        -Force

}
catch {

    Write-Host ""
    Write-Host "ERROR CRITICO: No se pudo extraer UPDATE.zip." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""

    if (Test-Path -LiteralPath $ZIP_VERSION_DIR) {

        Remove-Item `
            -LiteralPath $ZIP_VERSION_DIR `
            -Recurse `
            -Force
    }

    exit 1
}

# ------------------------------------------------------------
# VERIFICAR version.txt
# ------------------------------------------------------------

if (!(Test-Path -LiteralPath $ZIP_VERSION_FILE)) {

    Write-Host ""
    Write-Host "ERROR CRITICO: UPDATE.zip no contiene version.txt." -ForegroundColor Red
    Write-Host ""
    Write-Host "Ruta esperada:" -ForegroundColor Yellow
    Write-Host $ZIP_VERSION_FILE -ForegroundColor Yellow
    Write-Host ""

    exit 1
}

$ZIP_VERSION = (
    Get-Content `
        -LiteralPath $ZIP_VERSION_FILE `
        -Raw
).Trim()

if ([string]::IsNullOrWhiteSpace($ZIP_VERSION)) {

    Write-Host ""
    Write-Host "ERROR CRITICO: version.txt dentro del ZIP esta vacio." -ForegroundColor Red
    Write-Host ""

    exit 1
}

if ($ZIP_VERSION -ne $VERSION) {

    Write-Host ""
    Write-Host "ERROR CRITICO: La version dentro de UPDATE.zip no coincide." -ForegroundColor Red
    Write-Host ""
    Write-Host "Esperada : $VERSION" -ForegroundColor Yellow
    Write-Host "Encontrada: $ZIP_VERSION" -ForegroundColor Yellow
    Write-Host ""

    exit 1
}

Write-Host "version.txt dentro del ZIP: OK." -ForegroundColor Green
Write-Host "Version encontrada: $ZIP_VERSION" -ForegroundColor Green
Write-Host ""

# ============================================================
# VERIFICAR _internal
# ============================================================

$ZIP_INTERNAL = Join-Path `
    $ZIP_VERSION_DIR `
    "_internal"

if (!(Test-Path -LiteralPath $ZIP_INTERNAL -PathType Container)) {

    Write-Host ""
    Write-Host "ERROR CRITICO: UPDATE.zip no contiene _internal." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "_internal extraido: OK." -ForegroundColor Green
Write-Host ""

# ============================================================
# VERIFICAR SUPABASE
# ============================================================

$ZIP_SUPABASE = Join-Path `
    $ZIP_INTERNAL `
    "supabase"

if (!(Test-Path -LiteralPath $ZIP_SUPABASE -PathType Container)) {

    Write-Host ""
    Write-Host "ERROR CRITICO: UPDATE.zip no contiene _internal\supabase." -ForegroundColor Red
    Write-Host ""

    exit 1
}

$SUPABASE_COUNT = @(
    Get-ChildItem `
        -LiteralPath $ZIP_SUPABASE `
        -Recurse `
        -File `
        -ErrorAction SilentlyContinue
).Count

if ($SUPABASE_COUNT -le 0) {

    Write-Host ""
    Write-Host "ERROR CRITICO: _internal\supabase esta vacio." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "_internal\supabase : OK ($SUPABASE_COUNT archivos)." -ForegroundColor Green

# ============================================================
# VERIFICAR POSTGREST
# ============================================================

$ZIP_POSTGREST = Join-Path `
    $ZIP_INTERNAL `
    "postgrest"

if (!(Test-Path -LiteralPath $ZIP_POSTGREST -PathType Container)) {

    Write-Host ""
    Write-Host "ERROR CRITICO: UPDATE.zip no contiene _internal\postgrest." -ForegroundColor Red
    Write-Host ""

    exit 1
}

$POSTGREST_COUNT = @(
    Get-ChildItem `
        -LiteralPath $ZIP_POSTGREST `
        -Recurse `
        -File `
        -ErrorAction SilentlyContinue
).Count

if ($POSTGREST_COUNT -le 0) {

    Write-Host ""
    Write-Host "ERROR CRITICO: _internal\postgrest esta vacio." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "_internal\postgrest : OK ($POSTGREST_COUNT archivos)." -ForegroundColor Green

# ============================================================
# VERIFICAR REALTIME
# ============================================================

$ZIP_REALTIME = Join-Path `
    $ZIP_INTERNAL `
    "realtime"

if (!(Test-Path -LiteralPath $ZIP_REALTIME -PathType Container)) {

    Write-Host ""
    Write-Host "ERROR CRITICO: UPDATE.zip no contiene _internal\realtime." -ForegroundColor Red
    Write-Host ""

    exit 1
}

$REALTIME_COUNT = @(
    Get-ChildItem `
        -LiteralPath $ZIP_REALTIME `
        -Recurse `
        -File `
        -ErrorAction SilentlyContinue
).Count

if ($REALTIME_COUNT -le 0) {

    Write-Host ""
    Write-Host "ERROR CRITICO: _internal\realtime esta vacio." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "_internal\realtime : OK ($REALTIME_COUNT archivos)." -ForegroundColor Green

# ============================================================
# VERIFICAR STORAGE3
# ============================================================

$ZIP_STORAGE3 = Join-Path `
    $ZIP_INTERNAL `
    "storage3"

if (!(Test-Path -LiteralPath $ZIP_STORAGE3 -PathType Container)) {

    Write-Host ""
    Write-Host "ERROR CRITICO: UPDATE.zip no contiene _internal\storage3." -ForegroundColor Red
    Write-Host ""

    exit 1
}

$STORAGE3_COUNT = @(
    Get-ChildItem `
        -LiteralPath $ZIP_STORAGE3 `
        -Recurse `
        -File `
        -ErrorAction SilentlyContinue
).Count

if ($STORAGE3_COUNT -le 0) {

    Write-Host ""
    Write-Host "ERROR CRITICO: _internal\storage3 esta vacio." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "_internal\storage3 : OK ($STORAGE3_COUNT archivos)." -ForegroundColor Green

# ============================================================
# VERIFICAR SUPABASE AUTH
# ============================================================

$ZIP_AUTH = Join-Path `
    $ZIP_INTERNAL `
    "supabase_auth"

if (!(Test-Path -LiteralPath $ZIP_AUTH -PathType Container)) {

    Write-Host ""
    Write-Host "ERROR CRITICO: UPDATE.zip no contiene _internal\supabase_auth." -ForegroundColor Red
    Write-Host ""

    exit 1
}

$AUTH_COUNT = @(
    Get-ChildItem `
        -LiteralPath $ZIP_AUTH `
        -Recurse `
        -File `
        -ErrorAction SilentlyContinue
).Count

if ($AUTH_COUNT -le 0) {

    Write-Host ""
    Write-Host "ERROR CRITICO: _internal\supabase_auth esta vacio." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "_internal\supabase_auth : OK ($AUTH_COUNT archivos)." -ForegroundColor Green

# ============================================================
# VERIFICAR SUPABASE FUNCTIONS
# ============================================================

$ZIP_FUNCTIONS = Join-Path `
    $ZIP_INTERNAL `
    "supabase_functions"

if (!(Test-Path -LiteralPath $ZIP_FUNCTIONS -PathType Container)) {

    Write-Host ""
    Write-Host "ERROR CRITICO: UPDATE.zip no contiene _internal\supabase_functions." -ForegroundColor Red
    Write-Host ""

    exit 1
}

$FUNCTIONS_COUNT = @(
    Get-ChildItem `
        -LiteralPath $ZIP_FUNCTIONS `
        -Recurse `
        -File `
        -ErrorAction SilentlyContinue
).Count

if ($FUNCTIONS_COUNT -le 0) {

    Write-Host ""
    Write-Host "ERROR CRITICO: _internal\supabase_functions esta vacio." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "_internal\supabase_functions : OK ($FUNCTIONS_COUNT archivos)." -ForegroundColor Green

# ============================================================
# VERIFICAR PYDANTIC
# ============================================================

$ZIP_PYDANTIC = Join-Path `
    $ZIP_INTERNAL `
    "pydantic"

if (!(Test-Path -LiteralPath $ZIP_PYDANTIC -PathType Container)) {

    Write-Host ""
    Write-Host "ERROR CRITICO: UPDATE.zip no contiene _internal\pydantic." -ForegroundColor Red
    Write-Host ""

    exit 1
}

$PYDANTIC_COUNT = @(
    Get-ChildItem `
        -LiteralPath $ZIP_PYDANTIC `
        -Recurse `
        -File `
        -ErrorAction SilentlyContinue
).Count

if ($PYDANTIC_COUNT -le 0) {

    Write-Host ""
    Write-Host "ERROR CRITICO: _internal\pydantic esta vacio." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "_internal\pydantic : OK ($PYDANTIC_COUNT archivos)." -ForegroundColor Green

# ============================================================
# VERIFICAR QUE NO EXISTA abril.db
# ============================================================

$ZIP_EXTRACTED_DB = @(
    Get-ChildItem `
        -LiteralPath $ZIP_VERSION_DIR `
        -Recurse `
        -File `
        -Filter "abril.db" `
        -ErrorAction SilentlyContinue
)

if ($ZIP_EXTRACTED_DB.Count -gt 0) {

    Write-Host ""
    Write-Host "ERROR CRITICO: abril.db aparecio dentro del ZIP extraido." -ForegroundColor Red
    Write-Host ""

    foreach ($DB_FILE in $ZIP_EXTRACTED_DB) {

        Write-Host $DB_FILE.FullName -ForegroundColor Red
    }

    Write-Host ""

    exit 1
}

Write-Host "abril.db dentro del ZIP: NO encontrado. OK." -ForegroundColor Green
Write-Host ""

# ============================================================
# RESUMEN
# ============================================================

Write-Host "============================================" -ForegroundColor Green
Write-Host "       UPDATE.ZIP VERIFICADO CORRECTAMENTE" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

Write-Host "Version: $ZIP_VERSION" -ForegroundColor Green
Write-Host ""

Write-Host "Dependencias verificadas:" -ForegroundColor Cyan
Write-Host "  _internal\supabase" -ForegroundColor Green
Write-Host "  _internal\postgrest" -ForegroundColor Green
Write-Host "  _internal\realtime" -ForegroundColor Green
Write-Host "  _internal\storage3" -ForegroundColor Green
Write-Host "  _internal\supabase_auth" -ForegroundColor Green
Write-Host "  _internal\supabase_functions" -ForegroundColor Green
Write-Host "  _internal\pydantic" -ForegroundColor Green
Write-Host ""

Write-Host "Database: NO incluida." -ForegroundColor Green
Write-Host ""

# ============================================================
# ELIMINAR CARPETA TEMPORAL
# ============================================================

if (Test-Path -LiteralPath $ZIP_VERSION_DIR) {

    Remove-Item `
        -LiteralPath $ZIP_VERSION_DIR `
        -Recurse `
        -Force
}

Write-Host "Verificacion finalizada." -ForegroundColor Green
Write-Host ""



# ============================================================
# RESULTADO ZIP
# ============================================================

Write-Host "============================================" -ForegroundColor Green
Write-Host "   UPDATE.ZIP GENERADO Y VERIFICADO" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

Write-Host "UPDATE.zip contiene:" -ForegroundColor Cyan
Write-Host "  - PAPELERA_POS.exe"
Write-Host "  - _internal"
Write-Host "  - _internal\dotenv"
Write-Host "  - version.txt"
Write-Host ""

Write-Host "UPDATE.zip NO contiene:" -ForegroundColor Cyan
Write-Host "  - database"
Write-Host "  - abril.db"
Write-Host "  - backups"
Write-Host "  - logs"
Write-Host "  - tickets"
Write-Host ""

# ============================================================
# GIT
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "             GIT" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

git status

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: git status fallo." -ForegroundColor Red
    exit 1
}

$TAG_EXISTE_LOCAL = git tag -l $TAG

if ($TAG_EXISTE_LOCAL -eq $TAG) {
    Write-Host ""
    Write-Host "ERROR: El tag $TAG ya existe localmente." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Agregando cambios a Git..." -ForegroundColor Cyan

git add .

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: git add fallo." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Cambios preparados:" -ForegroundColor Cyan
git status --short

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: git status fallo." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Creando commit..." -ForegroundColor Cyan

git commit -m "Version $VERSION"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: git commit fallo." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Subiendo cambios a GitHub..." -ForegroundColor Cyan

git push

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: git push fallo." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Creando tag $TAG..." -ForegroundColor Cyan

git tag $TAG

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: No se pudo crear el tag $TAG." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Subiendo tag $TAG a GitHub..." -ForegroundColor Cyan

git push origin $TAG

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: No se pudo subir el tag $TAG." -ForegroundColor Red
    exit 1
}

# ============================================================
# LIMPIAR TEMPORAL SOLO DESPUES DE PUBLICAR
# ============================================================

if (Test-Path -LiteralPath $UPDATE_DIR) {
    Write-Host ""
    Write-Host "Eliminando UPDATE_TEMP despues de publicar..." -ForegroundColor Cyan

    Remove-Item `
        -LiteralPath $UPDATE_DIR `
        -Recurse `
        -Force
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

Write-Host "INSTALACION INICIAL:" -ForegroundColor Cyan
Write-Host "  - PAPELERA_POS.exe"
Write-Host "  - _internal"
Write-Host "  - database\abril.db"
Write-Host "  - backups"
Write-Host "  - logs"
Write-Host "  - tickets"
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
Write-Host "  - tickets"
Write-Host ""

Write-Host "UPDATE.zip generado y verificado correctamente." -ForegroundColor Green
Write-Host "python-dotenv incluido correctamente." -ForegroundColor Green
Write-Host "La database NO fue incluida en UPDATE.zip." -ForegroundColor Green
Write-Host "abril.db NO esta dentro de _internal." -ForegroundColor Green
Write-Host ""
Write-Host "GitHub Actions deberia generar/publicar ahora el Release." -ForegroundColor Yellow
Write-Host ""

