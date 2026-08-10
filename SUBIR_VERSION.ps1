# ==========================================
# SUBIR_VERSION.ps1
# PAPELERA POS
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
    Write-Host ".\SUBIR_VERSION.ps1 1.0.40"
    Write-Host ""

    exit 1
}


$VERSION = $args[0]


# ==========================================
# VALIDAR FORMATO VERSION
# ==========================================

if ($VERSION -notmatch '^\d+\.\d+\.\d+$') {

    Write-Host "ERROR: Version invalida: $VERSION" -ForegroundColor Red
    Write-Host ""
    Write-Host "Ejemplo correcto: 1.0.40"
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
# ACTUALIZAR VERSION.TXT
# ==========================================

Write-Host ""
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

    Write-Host "ERROR: version.txt no contiene $VERSION" -ForegroundColor Red

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

    exit 1
}


# ==========================================
# COMPROBAR EXE
# ==========================================

$EXE = ".\dist\PAPELERA_POS\PAPELERA_POS.exe"


if (!(Test-Path $EXE)) {

    Write-Host ""
    Write-Host "ERROR: No se genero PAPELERA_POS.exe." -ForegroundColor Red

    exit 1
}


Write-Host ""
Write-Host "PAPELERA_POS compilado correctamente." -ForegroundColor Green
Write-Host "PAPELERA_POS.exe OK." -ForegroundColor Green


# ==========================================
# COPIAR VERSION.TXT MANUALMENTE
# ==========================================

Write-Host ""
Write-Host "Copiando version.txt a dist..." -ForegroundColor Cyan


$DIST_VERSION = ".\dist\PAPELERA_POS\version.txt"


Copy-Item `
    ".\version.txt" `
    $DIST_VERSION `
    -Force


# ==========================================
# COMPROBAR VERSION.TXT EN DIST
# ==========================================

if (!(Test-Path $DIST_VERSION)) {

    Write-Host ""
    Write-Host "ERROR: No se genero version.txt en dist." -ForegroundColor Red

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

    exit 1
}


Write-Host "version.txt en dist = $VERSION" -ForegroundColor Green


# ==========================================
# COMPROBAR _INTERNAL
# ==========================================

$INTERNAL = ".\dist\PAPELERA_POS\_internal"


if (!(Test-Path $INTERNAL)) {

    Write-Host ""
    Write-Host "ERROR: No existe la carpeta _internal." -ForegroundColor Red

    exit 1
}


# ==========================================
# COMPROBAR base_library.zip
# ==========================================

$BASE_LIBRARY = ".\dist\PAPELERA_POS\_internal\base_library.zip"


if (!(Test-Path $BASE_LIBRARY)) {

    Write-Host ""
    Write-Host "ERROR: No se encontro _internal\base_library.zip." -ForegroundColor Red

    exit 1
}


Write-Host "base_library.zip OK." -ForegroundColor Green


# ==========================================
# COMPILAR UPDATER
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

    exit 1
}


$UPDATER_EXE = ".\dist\PAPELERA_UPDATER\PAPELERA_UPDATER.exe"


if (!(Test-Path $UPDATER_EXE)) {

    Write-Host ""
    Write-Host "ERROR: No se genero PAPELERA_UPDATER.exe." -ForegroundColor Red

    exit 1
}


Write-Host ""
Write-Host "PAPELERA_UPDATER compilado correctamente." -ForegroundColor Green


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

    Write-Host "ERROR: git add fallo." -ForegroundColor Red

    exit 1
}


# ==========================================
# GIT COMMIT
# ==========================================

Write-Host ""
Write-Host "Creando commit..." -ForegroundColor Cyan


git commit -m "Version $VERSION"


if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: git commit fallo." -ForegroundColor Red

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

    exit 1
}


# ==========================================
# COMPROBAR SI EL TAG YA EXISTE
# ==========================================

$TAG_EXISTE = git tag -l $TAG


if ($TAG_EXISTE -eq $TAG) {

    Write-Host ""
    Write-Host "ERROR: El tag $TAG ya existe." -ForegroundColor Red
    Write-Host ""
    Write-Host "No se creara nuevamente."

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
Write-Host ""

Write-Host "GitHub Actions deberia crear ahora el Release." -ForegroundColor Yellow
Write-Host ""

Write-Host "IMPORTANTE:" -ForegroundColor Yellow
Write-Host "El update.zip sera generado por GitHub Actions."
Write-Host "No cierres el proceso de GitHub Actions hasta que termine."
Write-Host ""