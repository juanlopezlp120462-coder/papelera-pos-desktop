# ============================================================
# SUBIR_VERSION.ps1 (OPTIMIZADO Y RÁPIDO)
# PAPELERA POS
# ============================================================

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

if ($args.Count -lt 1) {
    Write-Host "ERROR: No se indico la version." -ForegroundColor Red
    Write-Host ""
    Write-Host "Uso:"
    Write-Host ".\SUBIR_VERSION.ps1 1.0.63"
    Write-Host ""
    exit 1
}

$VERSION = $args[0].ToString().Trim()

if ($VERSION -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host "ERROR: Version invalida: $VERSION" -ForegroundColor Red
    Write-Host ""
    Write-Host "Ejemplo correcto: 1.0.63"
    Write-Host ""
    exit 1
}

$TAG = "v$VERSION"
$VERSION_FILE = Join-Path $ROOT "version.txt"

# ============================================================
# VERSION ACTUAL
# ============================================================

if (Test-Path -LiteralPath $VERSION_FILE) {
    $VERSION_ACTUAL = (Get-Content -LiteralPath $VERSION_FILE -Raw).Trim()
} else {
    $VERSION_ACTUAL = "1.0.0"
}

Write-Host "Version actual: $VERSION_ACTUAL"
Write-Host ""
Write-Host "Nueva version: $VERSION" -ForegroundColor Yellow
Write-Host "Nuevo tag: $TAG" -ForegroundColor Yellow
Write-Host ""

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

Set-Content -LiteralPath $VERSION_FILE -Value $VERSION -Encoding UTF8

$VERSION_COMPROBADA = (Get-Content -LiteralPath $VERSION_FILE -Raw).Trim()

if ($VERSION_COMPROBADA -ne $VERSION) {
    Write-Host "ERROR: version.txt no contiene $VERSION." -ForegroundColor Red
    exit 1
}

Write-Host "version.txt actualizado a $VERSION" -ForegroundColor Green
Write-Host ""

# ============================================================
# GIT: ADD, COMMIT, PUSH Y TAG
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       SUBIENDO CAMBIOS A GITHUB" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

git status

$TAG_EXISTE_LOCAL = git tag -l $TAG

if ($TAG_EXISTE_LOCAL -eq $TAG) {
    Write-Host "ERROR: El tag $TAG ya existe localmente." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Agregando cambios a Git..." -ForegroundColor Cyan
git add .

Write-Host "Creando commit..." -ForegroundColor Cyan
git commit -m "Version $VERSION"

Write-Host "Subiendo cambios a GitHub..." -ForegroundColor Cyan
git push

Write-Host "Creando tag $TAG..." -ForegroundColor Cyan
git tag $TAG

Write-Host "Subiendo tag $TAG a GitHub..." -ForegroundColor Cyan
git push origin $TAG

# ============================================================
# FINAL
# ============================================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "       VERSION PUBLICADA CON ÉXITO" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Version: $VERSION" -ForegroundColor Green
Write-Host "Tag: $TAG" -ForegroundColor Green
Write-Host ""
Write-Host "GitHub Actions está compilando y generando el release en la nube automáticamente." -ForegroundColor Yellow
Write-Host ""