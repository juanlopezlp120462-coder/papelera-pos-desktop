
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
    Write-Host ""
    Write-Host "Uso:" -ForegroundColor Yellow
    Write-Host ".\SUBIR_VERSION.ps1 2.0.59" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

$VERSION = $args[0].ToString().Trim()

if ($VERSION -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host ""
    Write-Host "ERROR: Version invalida: $VERSION" -ForegroundColor Red
    Write-Host "La version debe tener formato X.X.X" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

$TAG = "v$VERSION"

# ============================================================
# RUTAS
# ============================================================

$VERSION_FILE = Join-Path $ROOT "version.txt"
$SPEC_FILE = Join-Path $ROOT "PAPELERA_POS.spec"
$UPDATER_SPEC_FILE = Join-Path $ROOT "PAPELERA_UPDATER.spec"
$MAIN_FILE = Join-Path $ROOT "main.py"
$UPDATER_FILE = Join-Path $ROOT "updater.py"
$WORKFLOW_FILE = Join-Path $ROOT ".github\workflows\build-release.yml"

# ============================================================
# COMPROBAR VERSION ACTUAL
# ============================================================

if (Test-Path -LiteralPath $VERSION_FILE) {

    $VERSION_ACTUAL = (
        Get-Content `
            -LiteralPath $VERSION_FILE `
            -Raw
    ).Trim()

}
else {

    Write-Host ""
    Write-Host "ERROR: No existe version.txt." -ForegroundColor Red
    Write-Host $VERSION_FILE -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host "Version actual : $VERSION_ACTUAL" -ForegroundColor Cyan
Write-Host "Nueva version  : $VERSION" -ForegroundColor Yellow
Write-Host "Nuevo tag      : $TAG" -ForegroundColor Yellow
Write-Host ""

# ============================================================
# NO PERMITIR MISMA VERSION
# ============================================================

if ($VERSION_ACTUAL -eq $VERSION) {

    Write-Host ""
    Write-Host "ERROR: La nueva version es igual a la version actual." -ForegroundColor Red
    Write-Host "Version actual: $VERSION_ACTUAL" -ForegroundColor Red
    Write-Host ""
    exit 1
}

# ============================================================
# COMPROBAR TAG LOCAL
# ============================================================

$TAG_EXISTE_LOCAL = git tag -l $TAG

if ($TAG_EXISTE_LOCAL -eq $TAG) {

    Write-Host ""
    Write-Host "ERROR: El tag $TAG ya existe localmente." -ForegroundColor Red
    Write-Host ""
    exit 1
}

# ============================================================
# COMPROBAR TAG REMOTO
# ============================================================

$TAG_EXISTE_REMOTO = git ls-remote --tags origin "refs/tags/$TAG"

if ($TAG_EXISTE_REMOTO) {

    Write-Host ""
    Write-Host "ERROR: El tag $TAG ya existe en GitHub." -ForegroundColor Red
    Write-Host ""
    exit 1
}

# ============================================================
# COMPROBAR ARCHIVOS PRINCIPALES
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       COMPROBANDO ARCHIVOS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$ARCHIVOS_REQUERIDOS = @(
    $VERSION_FILE,
    $MAIN_FILE,
    $SPEC_FILE,
    $UPDATER_FILE,
    $UPDATER_SPEC_FILE,
    $WORKFLOW_FILE
)

foreach ($ARCHIVO in $ARCHIVOS_REQUERIDOS) {

    if (!(Test-Path -LiteralPath $ARCHIVO)) {

        Write-Host ""
        Write-Host "ERROR: Falta el archivo:" -ForegroundColor Red
        Write-Host $ARCHIVO -ForegroundColor Red
        Write-Host ""

        exit 1
    }

    Write-Host "OK: $ARCHIVO" -ForegroundColor Green
}

Write-Host ""

# ============================================================
# COMPROBAR YAML
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       COMPROBANDO WORKFLOW YAML" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$YAML_TEST = @"
import yaml
with open(r'$WORKFLOW_FILE', encoding='utf-8') as f:
    yaml.safe_load(f)
print('YAML CORRECTO')
"@

$YAML_RESULT = python -c $YAML_TEST

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: build-release.yml no es valido." -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host $YAML_RESULT -ForegroundColor Green
Write-Host ""

# ============================================================
# GIT STATUS
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "             ESTADO DE GIT" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

git status --short

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: git status fallo." -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================
# MOSTRAR CAMBIOS
# ============================================================

Write-Host "Se publicara:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Version: $VERSION" -ForegroundColor Green
Write-Host "  Tag:     $TAG" -ForegroundColor Green
Write-Host ""

Write-Host "El proceso sera:" -ForegroundColor Cyan
Write-Host "  1. Actualizar version.txt"
Write-Host "  2. Crear commit"
Write-Host "  3. Subir main a GitHub"
Write-Host "  4. Crear tag $TAG"
Write-Host "  5. Subir tag a GitHub"
Write-Host "  6. GitHub Actions compilara PAPELERA POS"
Write-Host "  7. GitHub Actions generara UPDATE.zip"
Write-Host "  8. GitHub Actions publicara el Release"
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
# ACTUALIZAR VERSION.TXT
# ============================================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       ACTUALIZANDO VERSION" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Set-Content `
    -LiteralPath $VERSION_FILE `
    -Value $VERSION `
    -Encoding UTF8

$VERSION_COMPROBADA = (
    Get-Content `
        -LiteralPath $VERSION_FILE `
        -Raw
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
# GIT DIFF CHECK
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       VERIFICANDO CAMBIOS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

git diff --check

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: git diff --check encontro problemas." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "git diff --check: OK." -ForegroundColor Green
Write-Host ""

# ============================================================
# GIT ADD
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "             GIT ADD" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

git add .

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: git add fallo." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "git add: OK." -ForegroundColor Green
Write-Host ""

# ============================================================
# MOSTRAR STAGED
# ============================================================

Write-Host "Cambios preparados para commit:" -ForegroundColor Cyan
Write-Host ""

git status --short

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: git status fallo." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host ""

# ============================================================
# COMMIT
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "             CREANDO COMMIT" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

git commit -m "Version $VERSION"

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: git commit fallo." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host ""
Write-Host "Commit creado correctamente." -ForegroundColor Green
Write-Host ""

# ============================================================
# PUSH MAIN
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "          SUBIENDO MAIN A GITHUB" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

git push origin main

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: No se pudo subir main a GitHub." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host ""
Write-Host "main subido correctamente." -ForegroundColor Green
Write-Host ""

# ============================================================
# CREAR TAG
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "             CREANDO TAG" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

git tag $TAG

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: No se pudo crear el tag $TAG." -ForegroundColor Red
    Write-Host ""

    exit 1
}

Write-Host "Tag $TAG creado correctamente." -ForegroundColor Green
Write-Host ""

# ============================================================
# PUSH TAG
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "          SUBIENDO TAG A GITHUB" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

git push origin $TAG

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: No se pudo subir el tag $TAG." -ForegroundColor Red
    Write-Host ""
    Write-Host "IMPORTANTE: El tag existe localmente." -ForegroundColor Yellow
    Write-Host "Si es necesario, puede subirse manualmente con:" -ForegroundColor Yellow
    Write-Host "git push origin $TAG" -ForegroundColor Yellow
    Write-Host ""

    exit 1
}

Write-Host ""
Write-Host "Tag $TAG subido correctamente." -ForegroundColor Green
Write-Host ""

# ============================================================
# FINAL
# ============================================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "       VERSION PUBLICADA CORRECTAMENTE" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

Write-Host "Version : $VERSION" -ForegroundColor Green
Write-Host "Tag     : $TAG" -ForegroundColor Green
Write-Host ""

Write-Host "GitHub Actions deberia comenzar automaticamente." -ForegroundColor Yellow
Write-Host ""
Write-Host "GitHub Actions se encargara de:" -ForegroundColor Cyan
Write-Host "  - Compilar PAPELERA_POS.exe"
Write-Host "  - Compilar PAPELERA_UPDATER.exe"
Write-Host "  - Preparar UPDATE.zip"
Write-Host "  - Verificar el contenido"
Write-Host "  - Publicar el Release"
Write-Host "  - Adjuntar UPDATE.zip"
Write-Host ""

Write-Host "============================================" -ForegroundColor Green
Write-Host "              FIN DEL PROCESO" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
