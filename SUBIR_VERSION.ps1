```powershell
# ==========================================
# SUBIR_VERSION.ps1
# PAPELERA POS
#
# FLUJO COMPLETO
#
# 1. Cambiar version.txt
# 2. Limpiar build/dist
# 3. Compilar PAPELERA_POS
# 4. Preparar database inicial
# 5. Verificar database
# 6. Verificar version.txt
# 7. Verificar _internal
# 8. Compilar PAPELERA_UPDATER
# 9. Crear UPDATE.zip
# 10. Verificar contenido de UPDATE.zip
# 11. Verificar que UPDATE.zip NO tenga database
# 12. Git add
# 13. Git commit
# 14. Git push
# 15. Crear tag
# 16. Subir tag
#
# IMPORTANTE:
#
# La database SOLO pertenece a la instalacion inicial.
#
# UPDATE.zip contiene:
#
#   PAPELERA_POS.exe
#   _internal\*
#   version.txt
#
# UPDATE.zip NO contiene:
#
#   database
#   abril.db
#   backups
#   logs
#
# ==========================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "       SUBIR VERSION - PAPELERA POS" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ==========================================
# RECIBIR VERSION
# ==========================================

if ($args.Count -lt 1) {

    Write-Host "ERROR: No se indico la version." -ForegroundColor Red
    Write-Host ""
    Write-Host "Uso:"
    Write-Host ".\SUBIR_VERSION.ps1 1.0.53"
    Write-Host ""

    exit 1
}

$VERSION = $args[0]

# ==========================================
# VALIDAR VERSION
# ==========================================

if ($VERSION -notmatch '^\d+\.\d+\.\d+$') {

    Write-Host "ERROR: Version invalida: $VERSION" -ForegroundColor Red
    Write-Host ""
    Write-Host "Ejemplo correcto: 1.0.53"
    Write-Host ""

    exit 1
}

$TAG = "v$VERSION"

# ==========================================
# VERSION ACTUAL
# ==========================================

if (Test-Path ".\version.txt") {

    $VERSION_ACTUAL = (
        Get-Content ".\version.txt" -Raw
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

# ==========================================
# CONFIRMACION
# ==========================================

$CONFIRMAR = Read-Host "Continuar con la version $VERSION (S/N)"

if ($CONFIRMAR -notmatch '^[sS]$') {

    Write-Host ""
    Write-Host "Operacion cancelada." -ForegroundColor Yellow

    exit 0
}

# ==========================================
# COMPROBAR DATABASE ORIGINAL
# ==========================================

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "       COMPROBANDO DATABASE ORIGINAL" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$DATABASE_ORIGEN = ".\database\abril.db"

if (!(Test-Path $DATABASE_ORIGEN)) {

    Write-Host ""
    Write-Host "ERROR: No existe la database original:" -ForegroundColor Red
    Write-Host $DATABASE_ORIGEN -ForegroundColor Red
    Write-Host ""

    exit 1
}

$DATABASE_ORIGEN_SIZE = (
    Get-Item $DATABASE_ORIGEN
).Length

Write-Host "Database original encontrada." -ForegroundColor Green
Write-Host "Ruta: $DATABASE_ORIGEN"
Write-Host "Tamaño: $DATABASE_ORIGEN_SIZE bytes"
Write-Host ""

# ==========================================
# COMPROBAR DATABASE ORIGINAL
# ==========================================

Write-Host "Comprobando contenido de database original..." -ForegroundColor Cyan

$DB_ORIGEN_TEST = python -c "import sqlite3; c=sqlite3.connect(r'$DATABASE_ORIGEN'); print('PRODUCTOS:', c.execute('SELECT COUNT(*) FROM productos').fetchone()[0]); print('VENTAS:', c.execute('SELECT COUNT(*) FROM ventas').fetchone()[0]); c.close()"

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: No se pudo leer la database original." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host $DB_ORIGEN_TEST -ForegroundColor Green
Write-Host ""

# ==========================================
# ACTUALIZAR VERSION.TXT
# ==========================================

Write-Host "Actualizando version.txt..." -ForegroundColor Cyan

Set-Content `
    -Path ".\version.txt" `
    -Value $VERSION `
    -Encoding UTF8

# ==========================================
# COMPROBAR VERSION.TXT
# ==========================================

$VERSION_COMPROBADA = (
    Get-Content ".\version.txt" -Raw
).Trim()

if ($VERSION_COMPROBADA -ne $VERSION) {

    Write-Host ""
    Write-Host "ERROR: version.txt no contiene $VERSION" -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "version.txt = $VERSION" -ForegroundColor Green

# ==========================================
# LIMPIAR BUILD Y DIST
# ==========================================

Write-Host ""
Write-Host "Limpiando compilaciones anteriores..." -ForegroundColor Cyan

if (Test-Path ".\build") {

    Remove-Item `
        ".\build" `
        -Recurse `
        -Force
}

if (Test-Path ".\dist") {

    Remove-Item `
        ".\dist" `
        -Recurse `
        -Force
}

Write-Host "build y dist eliminados." -ForegroundColor Green

# ==========================================
# LIMPIAR UPDATE TEMPORAL
# ==========================================

$UPDATE_DIR = ".\UPDATE_TEMP"
$UPDATE_ZIP = ".\UPDATE.zip"

if (Test-Path $UPDATE_DIR) {

    Remove-Item `
        $UPDATE_DIR `
        -Recurse `
        -Force
}

if (Test-Path $UPDATE_ZIP) {

    Remove-Item `
        $UPDATE_ZIP `
        -Force
}

# ==========================================
# COMPILAR PAPELERA POS
# ==========================================

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "       COMPILANDO PAPELERA POS" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

python -m PyInstaller --clean PAPELERA_POS.spec

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: PyInstaller fallo al compilar PAPELERA_POS." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ==========================================
# RUTAS PRINCIPALES
# ==========================================

$POS_DIR = ".\dist\PAPELERA_POS"
$EXE = "$POS_DIR\PAPELERA_POS.exe"
$INTERNAL = "$POS_DIR\_internal"

# ==========================================
# COMPROBAR EXE
# ==========================================

if (!(Test-Path $EXE)) {

    Write-Host ""
    Write-Host "ERROR: No se genero PAPELERA_POS.exe." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host ""
Write-Host "PAPELERA_POS compilado correctamente." -ForegroundColor Green
Write-Host "PAPELERA_POS.exe OK." -ForegroundColor Green

# ==========================================
# COMPROBAR _INTERNAL
# ==========================================

if (!(Test-Path $INTERNAL)) {

    Write-Host ""
    Write-Host "ERROR: PyInstaller no genero _internal." -ForegroundColor Red
    Write-Host ""
    Write-Host "Ruta esperada:"
    Write-Host $INTERNAL
    Write-Host ""

    exit 1
}

$INTERNAL_FILES = @(
    Get-ChildItem `
        $INTERNAL `
        -Recurse `
        -File
)

if ($INTERNAL_FILES.Count -eq 0) {

    Write-Host ""
    Write-Host "ERROR: _internal esta vacio." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "_internal OK." -ForegroundColor Green
Write-Host "Archivos dentro de _internal: $($INTERNAL_FILES.Count)" -ForegroundColor Green

# ==========================================
# PREPARAR DATABASE INICIAL
# ==========================================

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "       PREPARANDO DATABASE INICIAL" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$DATABASE_DIST_DIR = "$POS_DIR\database"
$DATABASE_DIST = "$DATABASE_DIST_DIR\abril.db"

if (!(Test-Path $DATABASE_DIST_DIR)) {

    New-Item `
        -ItemType Directory `
        -Path $DATABASE_DIST_DIR `
        -Force `
        | Out-Null

    Write-Host "Carpeta database creada en dist." -ForegroundColor Green
}

Write-Host "Copiando database inicial a dist..." -ForegroundColor Cyan

Copy-Item `
    $DATABASE_ORIGEN `
    $DATABASE_DIST `
    -Force

# ==========================================
# COMPROBAR DATABASE
# ==========================================

if (!(Test-Path $DATABASE_DIST)) {

    Write-Host ""
    Write-Host "ERROR: No se pudo copiar abril.db a dist." -ForegroundColor Red
    Write-Host ""

    exit 1
}

$DATABASE_SIZE = (
    Get-Item $DATABASE_DIST
).Length

Write-Host ""
Write-Host "Database inicial OK." -ForegroundColor Green
Write-Host "Destino: $DATABASE_DIST" -ForegroundColor Green
Write-Host "Tamaño: $DATABASE_SIZE bytes" -ForegroundColor Green
Write-Host ""

# ==========================================
# COMPROBAR CONTENIDO DATABASE DIST
# ==========================================

Write-Host "Comprobando contenido de database de dist..." -ForegroundColor Cyan

$DB_DIST_TEST = python -c "import sqlite3; c=sqlite3.connect(r'$DATABASE_DIST'); print('PRODUCTOS:', c.execute('SELECT COUNT(*) FROM productos').fetchone()[0]); print('VENTAS:', c.execute('SELECT COUNT(*) FROM ventas').fetchone()[0]); c.close()"

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: No se pudo leer la database de dist." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host $DB_DIST_TEST -ForegroundColor Green
Write-Host ""

Write-Host "DATABASE INICIAL PREPARADA CORRECTAMENTE." -ForegroundColor Green

# ==========================================
# COPIAR VERSION.TXT A DIST
# ==========================================

Write-Host ""
Write-Host "Preparando version.txt en dist..." -ForegroundColor Cyan

$DIST_VERSION = "$POS_DIR\version.txt"

Copy-Item `
    ".\version.txt" `
    $DIST_VERSION `
    -Force

if (!(Test-Path $DIST_VERSION)) {

    Write-Host ""
    Write-Host "ERROR: No se pudo copiar version.txt a dist." -ForegroundColor Red
    Write-Host ""

    exit 1
}

$VERSION_DIST = (
    Get-Content $DIST_VERSION -Raw
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

# ==========================================
# COMPROBAR base_library.zip
# ==========================================

$BASE_LIBRARY = "$INTERNAL\base_library.zip"

if (!(Test-Path $BASE_LIBRARY)) {

    Write-Host ""
    Write-Host "ERROR: No se encontro _internal\base_library.zip." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "base_library.zip OK." -ForegroundColor Green

# ==========================================
# COMPILAR PAPELERA UPDATER
# ==========================================

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "       COMPILANDO PAPELERA UPDATER" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

python -m PyInstaller --clean PAPELERA_UPDATER.spec

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: PyInstaller fallo al compilar PAPELERA_UPDATER." -ForegroundColor Red
    Write-Host ""

    exit 1
}

$UPDATER_EXE = ".\dist\PAPELERA_UPDATER\PAPELERA_UPDATER.exe"

if (!(Test-Path $UPDATER_EXE)) {

    Write-Host ""
    Write-Host "ERROR: No se genero PAPELERA_UPDATER.exe." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host ""
Write-Host "PAPELERA_UPDATER compilado correctamente." -ForegroundColor Green

# ==========================================
# CREAR UPDATE_TEMP
# ==========================================

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "       PREPARANDO UPDATE.ZIP" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

New-Item `
    -ItemType Directory `
    -Path $UPDATE_DIR `
    -Force `
    | Out-Null

# ==========================================
# COPIAR EXE
# ==========================================

Write-Host "Copiando PAPELERA_POS.exe..." -ForegroundColor Cyan

Copy-Item `
    $EXE `
    "$UPDATE_DIR\PAPELERA_POS.exe" `
    -Force

# ==========================================
# COPIAR _INTERNAL
# ==========================================

Write-Host "Copiando _internal completo..." -ForegroundColor Cyan

New-Item `
    -ItemType Directory `
    -Path "$UPDATE_DIR\_internal" `
    -Force `
    | Out-Null

Copy-Item `
    "$INTERNAL\*" `
    "$UPDATE_DIR\_internal\" `
    -Recurse `
    -Force

# ==========================================
# COPIAR VERSION
# ==========================================

Write-Host "Copiando version.txt..." -ForegroundColor Cyan

Copy-Item `
    ".\version.txt" `
    "$UPDATE_DIR\version.txt" `
    -Force

# ==========================================
# COMPROBAR UPDATE_TEMP
# ==========================================

Write-Host ""
Write-Host "Verificando UPDATE_TEMP..." -ForegroundColor Cyan

if (!(Test-Path "$UPDATE_DIR\PAPELERA_POS.exe")) {

    Write-Host ""
    Write-Host "ERROR: No se copio PAPELERA_POS.exe." -ForegroundColor Red
    exit 1
}

if (!(Test-Path "$UPDATE_DIR\_internal")) {

    Write-Host ""
    Write-Host "ERROR: No se copio _internal." -ForegroundColor Red
    exit 1
}

if (!(Test-Path "$UPDATE_DIR\version.txt")) {

    Write-Host ""
    Write-Host "ERROR: No se copio version.txt." -ForegroundColor Red
    exit 1
}

$TEMP_INTERNAL_FILES = @(
    Get-ChildItem `
        "$UPDATE_DIR\_internal" `
        -Recurse `
        -File
)

if ($TEMP_INTERNAL_FILES.Count -eq 0) {

    Write-Host ""
    Write-Host "ERROR: UPDATE_TEMP\_internal esta vacio." -ForegroundColor Red
    exit 1
}

Write-Host "PAPELERA_POS.exe: OK." -ForegroundColor Green
Write-Host "_internal: OK." -ForegroundColor Green
Write-Host "Archivos _internal: $($TEMP_INTERNAL_FILES.Count)" -ForegroundColor Green
Write-Host "version.txt: OK." -ForegroundColor Green
Write-Host ""

# ==========================================
# ASEGURAR QUE NO EXISTAN ELEMENTOS
# PROTEGIDOS
# ==========================================

if (Test-Path "$UPDATE_DIR\database") {

    Write-Host "Eliminando database del temporal..." -ForegroundColor Yellow

    Remove-Item `
        "$UPDATE_DIR\database" `
        -Recurse `
        -Force
}

if (Test-Path "$UPDATE_DIR\backups") {

    Remove-Item `
        "$UPDATE_DIR\backups" `
        -Recurse `
        -Force
}

if (Test-Path "$UPDATE_DIR\logs") {

    Remove-Item `
        "$UPDATE_DIR\logs" `
        -Recurse `
        -Force
}

# ==========================================
# CREAR ZIP CON .NET
#
# NO USAMOS Compress-Archive
#
# Esto evita el problema:
#
# base_library.zip
# "esta siendo utilizado por otro proceso"
# ==========================================

Write-Host ""
Write-Host "Comprimiendo UPDATE.zip..." -ForegroundColor Cyan

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

if (Test-Path $UPDATE_ZIP) {

    Remove-Item `
        $UPDATE_ZIP `
        -Force
}

$ZIP_FULL_PATH = (
    Resolve-Path "." 
).Path + "\UPDATE.zip"

$ZIP = [System.IO.Compression.ZipFile]::Open(
    $ZIP_FULL_PATH,
    [System.IO.Compression.ZipArchiveMode]::Create
)

try {

    $FILES_TO_ZIP = Get-ChildItem `
        $UPDATE_DIR `
        -Recurse `
        -File

    foreach ($FILE in $FILES_TO_ZIP) {

        $RELATIVE_PATH = $FILE.FullName.Substring(
            (Resolve-Path $UPDATE_DIR).Path.Length + 1
        )

        $RELATIVE_PATH = $RELATIVE_PATH.Replace("\", "/")

        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $ZIP,
            $FILE.FullName,
            $RELATIVE_PATH,
            [System.IO.Compression.CompressionLevel]::Optimal
        ) | Out-Null
    }

}
finally {

    $ZIP.Dispose()
}

# ==========================================
# ELIMINAR UPDATE_TEMP
# ==========================================

Remove-Item `
    $UPDATE_DIR `
    -Recurse `
    -Force

# ==========================================
# COMPROBAR UPDATE.ZIP
# ==========================================

if (!(Test-Path $UPDATE_ZIP)) {

    Write-Host ""
    Write-Host "ERROR: No se pudo crear UPDATE.zip." -ForegroundColor Red
    Write-Host ""

    exit 1
}

$UPDATE_SIZE = (
    Get-Item $UPDATE_ZIP
).Length

if ($UPDATE_SIZE -le 0) {

    Write-Host ""
    Write-Host "ERROR: UPDATE.zip esta vacio." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host ""
Write-Host "UPDATE.zip creado correctamente." -ForegroundColor Green
Write-Host "Tamaño: $UPDATE_SIZE bytes" -ForegroundColor Green
Write-Host ""

# ==========================================
# LEER ZIP
# ==========================================

Write-Host "Contenido de UPDATE.zip:" -ForegroundColor Cyan
Write-Host ""

$ZIP_CHECK = [System.IO.Compression.ZipFile]::OpenRead(
    (Resolve-Path $UPDATE_ZIP)
)

try {

    foreach ($ENTRY in $ZIP_CHECK.Entries) {

        Write-Host "  $($ENTRY.FullName)"
    }

}
finally {

    $ZIP_CHECK.Dispose()
}

Write-Host ""

# ==========================================
# VERIFICAR ZIP
# ==========================================

$ZIP_CHECK = [System.IO.Compression.ZipFile]::OpenRead(
    (Resolve-Path $UPDATE_ZIP)
)

try {

    $ZIP_ENTRIES = @(
        $ZIP_CHECK.Entries
    )

}
finally {

    $ZIP_CHECK.Dispose()
}

# ==========================================
# BUSCAR EXE
# ==========================================

$TIENE_EXE = $ZIP_ENTRIES |
    Where-Object {
        $_.FullName -eq "PAPELERA_POS.exe"
    }

if (!$TIENE_EXE) {

    Write-Host ""
    Write-Host "ERROR: UPDATE.zip no contiene PAPELERA_POS.exe." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ==========================================
# BUSCAR VERSION
# ==========================================

$TIENE_VERSION = $ZIP_ENTRIES |
    Where-Object {
        $_.FullName -eq "version.txt"
    }

if (!$TIENE_VERSION) {

    Write-Host ""
    Write-Host "ERROR: UPDATE.zip no contiene version.txt." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ==========================================
# BUSCAR _INTERNAL
# ==========================================

$TIENE_INTERNAL = $ZIP_ENTRIES |
    Where-Object {
        $_.FullName -like "_internal/*"
    }

if (!$TIENE_INTERNAL) {

    Write-Host ""
    Write-Host "ERROR: UPDATE.zip no contiene _internal." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ==========================================
# CONTAR ARCHIVOS INTERNAL
# ==========================================

$INTERNAL_ZIP_FILES = @(
    $ZIP_ENTRIES |
        Where-Object {
            $_.FullName -like "_internal/*"
        }
)

if ($INTERNAL_ZIP_FILES.Count -lt 1) {

    Write-Host ""
    Write-Host "ERROR: _internal dentro del ZIP esta vacio." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ==========================================
# VERIFICAR DATABASE
# ==========================================

$DATABASE_EN_ZIP = $ZIP_ENTRIES |
    Where-Object {

        $_.FullName -match '(^|/)database(/|$)' -or
        $_.FullName -match '(^|/)abril\.db$' -or
        $_.FullName -match '(^|/)backups(/|$)' -or
        $_.FullName -match '(^|/)logs(/|$)'
    }

if ($DATABASE_EN_ZIP) {

    Write-Host ""
    Write-Host "ERROR: UPDATE.zip contiene elementos protegidos." -ForegroundColor Red
    Write-Host ""

    foreach ($ITEM in $DATABASE_EN_ZIP) {

        Write-Host "  $($ITEM.FullName)" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "La actualizacion NO puede continuar." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ==========================================
# MOSTRAR RESULTADO ZIP
# ==========================================

Write-Host "==========================================" -ForegroundColor Green
Write-Host "       UPDATE.ZIP VERIFICADO" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

Write-Host "PAPELERA_POS.exe: OK." -ForegroundColor Green
Write-Host "_internal: OK." -ForegroundColor Green
Write-Host "Archivos _internal: $($INTERNAL_ZIP_FILES.Count)" -ForegroundColor Green
Write-Host "version.txt: OK." -ForegroundColor Green
Write-Host "database: NO incluida." -ForegroundColor Green
Write-Host "abril.db: NO incluida." -ForegroundColor Green
Write-Host "backups: NO incluidos." -ForegroundColor Green
Write-Host "logs: NO incluidos." -ForegroundColor Green
Write-Host ""

# ==========================================
# GIT STATUS
# ==========================================

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "             GIT" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

git status

# ==========================================
# GIT ADD
# ==========================================

Write-Host ""
Write-Host "Agregando cambios a Git..." -ForegroundColor Cyan

git add .

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: git add fallo." -ForegroundColor Red

    exit 1
}

# ==========================================
# STATUS
# ==========================================

Write-Host ""
Write-Host "Cambios preparados:" -ForegroundColor Cyan

git status --short

# ==========================================
# GIT COMMIT
# ==========================================

Write-Host ""
Write-Host "Creando commit..." -ForegroundColor Cyan

git commit -m "Version $VERSION"

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: git commit fallo." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ==========================================
# GIT PUSH
# ==========================================

Write-Host ""
Write-Host "Subiendo cambios a GitHub..." -ForegroundColor Cyan

git push

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: git push fallo." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ==========================================
# COMPROBAR TAG
# ==========================================

$TAG_EXISTE = git tag -l $TAG

if ($TAG_EXISTE -eq $TAG) {

    Write-Host ""
    Write-Host "ERROR: El tag $TAG ya existe." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ==========================================
# CREAR TAG
# ==========================================

Write-Host ""
Write-Host "Creando tag $TAG..." -ForegroundColor Cyan

git tag $TAG

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: No se pudo crear el tag." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ==========================================
# SUBIR TAG
# ==========================================

Write-Host ""
Write-Host "Subiendo tag $TAG a GitHub..." -ForegroundColor Cyan

git push origin $TAG

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: No se pudo subir el tag." -ForegroundColor Red
    Write-Host ""

    exit 1
}

# ==========================================
# FINAL
# ==========================================

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "       VERSION PUBLICADA CORRECTAMENTE" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Version: $VERSION" -ForegroundColor Green
Write-Host "Tag: $TAG" -ForegroundColor Green
Write-Host "UPDATE.zip: $UPDATE_ZIP" -ForegroundColor Green
Write-Host ""

Write-Host "==========================================" -ForegroundColor Yellow
Write-Host "       RESUMEN DE ACTUALIZACION" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "INSTALACION INICIAL:" -ForegroundColor Cyan
Write-Host "  - PAPELERA_POS.exe"
Write-Host "  - _internal"
Write-Host "  - database\abril.db"
Write-Host "  - version.txt"
Write-Host ""

Write-Host "UPDATE.zip:" -ForegroundColor Cyan
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

Write-Host "GitHub Actions deberia crear ahora el Release." -ForegroundColor Yellow
Write-Host ""

Write-Host "UPDATE.zip generado y verificado correctamente." -ForegroundColor Green
Write-Host "La database NO fue incluida en UPDATE.zip." -ForegroundColor Green
Write-Host "La database de una instalacion existente NO sera reemplazada por el updater." -ForegroundColor Green
Write-Host ""
```
