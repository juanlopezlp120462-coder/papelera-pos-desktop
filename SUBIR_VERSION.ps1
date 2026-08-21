
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
    Write-Host ".\SUBIR_VERSION.ps1 2.0.82" -ForegroundColor Yellow
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
# DATOS GITHUB / SUPABASE
# ============================================================

$GITHUB_REPO = "juanlopezlp120462-coder/papelera-pos-desktop"

$UPDATE_URL = "https://github.com/$GITHUB_REPO/releases/download/$TAG/update.zip"

$SUPABASE_ENV_FILE = Join-Path $ROOT ".env"

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
Write-Host "Update URL     : $UPDATE_URL" -ForegroundColor DarkGray
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
# COMPROBAR .ENV
# ============================================================

if (!(Test-Path -LiteralPath $SUPABASE_ENV_FILE)) {

    Write-Host ""
    Write-Host "ERROR: No existe .env." -ForegroundColor Red
    Write-Host $SUPABASE_ENV_FILE -ForegroundColor Red
    Write-Host ""
    Write-Host "Debe contener SUPABASE_URL y SUPABASE_KEY." -ForegroundColor Yellow
    Write-Host ""

    exit 1
}

Write-Host "OK: .env encontrado." -ForegroundColor Green
Write-Host ""

# ============================================================
# COMPROBAR PYTHON / SUPABASE
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       COMPROBANDO SUPABASE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------
# CREAR SCRIPT PYTHON TEMPORAL
# ------------------------------------------------------------

$SUPABASE_TEST_FILE = Join-Path $ROOT "_supabase_test_temp.py"

$SUPABASE_TEST = @'
from dotenv import load_dotenv
from supabase import create_client
import os

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url:
    raise Exception("Falta SUPABASE_URL")

if not key:
    raise Exception("Falta SUPABASE_KEY")

supabase = create_client(url, key)

respuesta = (
    supabase
    .table("versiones")
    .select("version,url,activo")
    .eq("activo", True)
    .order("created_at", desc=True)
    .limit(1)
    .execute()
)

print("SUPABASE OK")
print("VERSION ACTIVA:", respuesta.data)
'@

try {

    Set-Content `
        -LiteralPath $SUPABASE_TEST_FILE `
        -Value $SUPABASE_TEST `
        -Encoding UTF8

    Write-Host "Ejecutando prueba de Supabase..." -ForegroundColor DarkGray
    Write-Host ""

    $SUPABASE_RESULT = python $SUPABASE_TEST_FILE

    if ($LASTEXITCODE -ne 0) {
        throw "Python devolvio error."
    }

}
catch {

    Write-Host ""
    Write-Host "ERROR: No se pudo conectar con Supabase." -ForegroundColor Red
    Write-Host ""
    Write-Host $_ -ForegroundColor Red
    Write-Host ""

    exit 1

}
finally {

    if (Test-Path -LiteralPath $SUPABASE_TEST_FILE) {

        Remove-Item `
            -LiteralPath $SUPABASE_TEST_FILE `
            -Force `
            -ErrorAction SilentlyContinue
    }
}

Write-Host $SUPABASE_RESULT -ForegroundColor Green
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
# CONFIRMACION
# ============================================================

Write-Host "============================================" -ForegroundColor Yellow
Write-Host "             PUBLICAR VERSION" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "Version: $VERSION" -ForegroundColor Green
Write-Host "Tag:     $TAG" -ForegroundColor Green
Write-Host ""

Write-Host "El proceso automatico sera:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Actualizar version.txt"
Write-Host "  2. Crear commit"
Write-Host "  3. Subir main a GitHub"
Write-Host "  4. Crear tag $TAG"
Write-Host "  5. Subir tag a GitHub"
Write-Host "  6. Esperar a GitHub Actions"
Write-Host "  7. Esperar a que exista update.zip"
Write-Host "  8. Actualizar automaticamente Supabase"
Write-Host "  9. Activar version $VERSION"
Write-Host " 10. Desactivar la version anterior"
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
    Write-Host "El tag existe localmente." -ForegroundColor Yellow
    Write-Host ""

    exit 1
}

Write-Host ""
Write-Host "Tag $TAG subido correctamente." -ForegroundColor Green
Write-Host ""

# ============================================================
# ESPERAR RELEASE / UPDATE.ZIP
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       ESPERANDO UPDATE.ZIP" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "GitHub Actions esta compilando..." -ForegroundColor Yellow
Write-Host ""
Write-Host "URL esperada:" -ForegroundColor DarkGray
Write-Host $UPDATE_URL -ForegroundColor DarkGray
Write-Host ""

$MAX_ESPERA = 600
$INTERVALO = 10
$TIEMPO = 0
$RELEASE_LISTO = $false

while ($TIEMPO -lt $MAX_ESPERA) {

    try {

        $respuesta = Invoke-WebRequest `
            -Uri $UPDATE_URL `
            -Method Head `
            -MaximumRedirection 10 `
            -TimeoutSec 15 `
            -ErrorAction Stop

        if ($respuesta.StatusCode -ge 200 -and $respuesta.StatusCode -lt 400) {

            $RELEASE_LISTO = $true

            Write-Host ""
            Write-Host "UPDATE.zip encontrado correctamente." -ForegroundColor Green
            Write-Host ""

            break
        }

    }
    catch {

        # Todavia no existe.
    }

    $minutos = [math]::Floor($TIEMPO / 60)
    $segundos = $TIEMPO % 60

    Write-Host `
        ("Esperando Release... {0}:{1:D2}" -f $minutos, $segundos) `
        -ForegroundColor DarkYellow

    Start-Sleep -Seconds $INTERVALO

    $TIEMPO += $INTERVALO
}

if (-not $RELEASE_LISTO) {

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "     RELEASE TODAVIA NO DISPONIBLE" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    Write-Host ""

    Write-Host "GitHub Actions puede seguir compilando." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Por seguridad NO se modificara Supabase." -ForegroundColor Yellow
    Write-Host "La version anterior continuara activa." -ForegroundColor Yellow
    Write-Host ""

    exit 1
}

# ============================================================
# ACTUALIZAR SUPABASE
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       ACTUALIZANDO SUPABASE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Nueva version : $VERSION" -ForegroundColor Green
Write-Host "URL           : $UPDATE_URL" -ForegroundColor Green
Write-Host ""

$SUPABASE_UPDATE = @"
from dotenv import load_dotenv
from supabase import create_client
import os
import sys

VERSION = "$VERSION"
URL = "$UPDATE_URL"

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL:
    raise Exception("Falta SUPABASE_URL en .env")

if not SUPABASE_KEY:
    raise Exception("Falta SUPABASE_KEY en .env")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

print("")
print("Conectando con Supabase...")
print("Version nueva:", VERSION)
print("URL nueva:", URL)
print("")

# ============================================================
# DESACTIVAR TODAS LAS VERSIONES ANTERIORES
# ============================================================

print("Desactivando versiones anteriores...")

resultado_update = (
    supabase
    .table("versiones")
    .update({"activo": False})
    .eq("activo", True)
    .execute()
)

print(
    "Versiones anteriores desactivadas."
)

# ============================================================
# INSERTAR NUEVA VERSION
# ============================================================

print("Registrando nueva version...")

registro = {
    "version": VERSION,
    "url": URL,
    "activo": True
}

resultado_insert = (
    supabase
    .table("versiones")
    .insert(registro)
    .execute()
)

if not resultado_insert.data:

    raise Exception(
        "Supabase no devolvio el registro insertado."
    )

print("")
print("======================================")
print(" SUPABASE ACTUALIZADO CORRECTAMENTE")
print("======================================")
print("")
print(
    "Registro:",
    resultado_insert.data
)
print("")
"@

try {

    $SUPABASE_RESULT = python -c $SUPABASE_UPDATE

    if ($LASTEXITCODE -ne 0) {

        throw "Python devolvio error actualizando Supabase."
    }

}
catch {

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "       ERROR ACTUALIZANDO SUPABASE" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    Write-Host ""

    Write-Host $_ -ForegroundColor Red
    Write-Host ""

    Write-Host "IMPORTANTE:" -ForegroundColor Yellow
    Write-Host "El Release ya existe en GitHub." -ForegroundColor Yellow
    Write-Host "Pero Supabase NO fue actualizado." -ForegroundColor Yellow
    Write-Host ""

    exit 1
}

Write-Host $SUPABASE_RESULT -ForegroundColor Green
Write-Host ""

# ============================================================
# VERIFICACION FINAL SUPABASE
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       VERIFICACION FINAL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$SUPABASE_VERIFY = @"
from dotenv import load_dotenv
from supabase import create_client
import os

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

respuesta = (
    supabase
    .table("versiones")
    .select("version,url,activo,created_at")
    .eq("activo", True)
    .order("created_at", desc=True)
    .limit(1)
    .execute()
)

print("VERSION ACTIVA EN SUPABASE:")
print(respuesta.data)
"@

$VERIFY_RESULT = python -c $SUPABASE_VERIFY

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ADVERTENCIA: No se pudo verificar Supabase." -ForegroundColor Yellow
    Write-Host ""

}
else {

    Write-Host $VERIFY_RESULT -ForegroundColor Green
    Write-Host ""
}

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
Write-Host "Release : GitHub" -ForegroundColor Green
Write-Host "Update  : $UPDATE_URL" -ForegroundColor Green
Write-Host "Servidor: Supabase" -ForegroundColor Green
Write-Host ""

Write-Host "La proxima PC que abra PAPELERA POS" -ForegroundColor Cyan
Write-Host "consultara automaticamente la version $VERSION." -ForegroundColor Cyan
Write-Host ""

Write-Host "============================================" -ForegroundColor Green
Write-Host "              FIN DEL PROCESO" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""