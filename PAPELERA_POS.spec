
# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import (
    collect_all,
    collect_submodules,
    collect_data_files,
)

# ============================================================
# CARPETA DEL PROYECTO
# ============================================================

PROJECT_DIR = os.path.dirname(
    os.path.abspath(SPEC)
)

# ============================================================
# VERSION
# ============================================================

VERSION_FILE = os.path.join(
    PROJECT_DIR,
    "version.txt"
)

# ============================================================
# HIDDEN IMPORTS
# ============================================================

hiddenimports = []

# ============================================================
# UI
# ============================================================

hiddenimports += collect_submodules("ui")

# ============================================================
# CERTIFI
# ============================================================

hiddenimports += collect_submodules("certifi")

# ============================================================
# DOTENV
# ============================================================

hiddenimports += collect_submodules("dotenv")

# ============================================================
# SUPABASE
#
# IMPORTANTE:
# Supabase 2.x esta compuesto por varios paquetes.
# Se fuerzan todos sus submodulos para evitar:
#
# ModuleNotFoundError: No module named 'supabase'
#
# en la PC donde NO existe el venv.
# ============================================================

SUPABASE_PACKAGES = [
    "supabase",
    "supabase_auth",
    "supabase_functions",
    "postgrest",
    "realtime",
    "storage3",
]

for package in SUPABASE_PACKAGES:

    try:

        hiddenimports += collect_submodules(package)

    except Exception:

        pass


# ============================================================
# IMPORTS EXPLICITOS SUPABASE
# ============================================================

hiddenimports += [

    # --------------------------------------------------------
    # SUPABASE
    # --------------------------------------------------------

    "supabase",
    "supabase.client",

    "supabase._sync",
    "supabase._sync.client",
    "supabase._sync.auth_client",

    "supabase._async",
    "supabase._async.client",
    "supabase._async.auth_client",

    # --------------------------------------------------------
    # POSTGREST
    # --------------------------------------------------------

    "postgrest",
    "postgrest._sync",
    "postgrest._sync.client",
    "postgrest._sync.request_builder",

    "postgrest._async",
    "postgrest._async.client",
    "postgrest._async.request_builder",

    # --------------------------------------------------------
    # REALTIME
    # --------------------------------------------------------

    "realtime",
    "realtime._sync",
    "realtime._sync.client",
    "realtime._sync.channel",
    "realtime._sync.presence",

    "realtime._async",
    "realtime._async.client",
    "realtime._async.channel",

    # --------------------------------------------------------
    # STORAGE3
    # --------------------------------------------------------

    "storage3",
    "storage3._sync",
    "storage3._sync.client",
    "storage3._sync.bucket",

    "storage3._async",
    "storage3._async.client",
    "storage3._async.bucket",

    # --------------------------------------------------------
    # AUTH
    # --------------------------------------------------------

    "supabase_auth",
    "supabase_auth._sync",
    "supabase_auth._sync.gotrue_client",

    "supabase_auth._async",
    "supabase_auth._async.gotrue_client",

    # --------------------------------------------------------
    # FUNCTIONS
    # --------------------------------------------------------

    "supabase_functions",

    # --------------------------------------------------------
    # HTTPX
    # --------------------------------------------------------

    "httpx",
    "httpx._api",
    "httpx._client",
    "httpx._config",
    "httpx._models",
    "httpx._transports",
    "httpx._transports.default",

    # --------------------------------------------------------
    # HTTPCORE
    # --------------------------------------------------------

    "httpcore",
    "httpcore._api",
    "httpcore._async",
    "httpcore._sync",
    "httpcore._models",
    "httpcore._ssl",
    "httpcore._backends",

    # --------------------------------------------------------
    # ANYIO
    # --------------------------------------------------------

    "anyio",

    # --------------------------------------------------------
    # WEBSOCKETS
    # --------------------------------------------------------

    "websockets",

    # --------------------------------------------------------
    # PYDANTIC
    # --------------------------------------------------------

    "pydantic",
    "pydantic_core",

    # --------------------------------------------------------
    # YARL
    # --------------------------------------------------------

    "yarl",

    # --------------------------------------------------------
    # JWT
    # --------------------------------------------------------

    "jwt",

    # --------------------------------------------------------
    # CRYPTOGRAPHY
    # --------------------------------------------------------

    "cryptography",
    "cffi",
]

# ============================================================
# DATOS
# ============================================================

datas = []
binaries = []

# ============================================================
# CERTIFI
# ============================================================

try:

    certifi_datas = collect_data_files(
        "certifi"
    )

    datas += certifi_datas

except Exception:

    pass


# ============================================================
# DOTENV
# ============================================================

try:

    dotenv_datas, dotenv_binaries, dotenv_hiddenimports = collect_all(
        "dotenv"
    )

    datas += dotenv_datas
    binaries += dotenv_binaries
    hiddenimports += dotenv_hiddenimports

except Exception:

    pass


# ============================================================
# SUPABASE Y PAQUETES RELACIONADOS
#
# collect_all incluye:
#
# - submodulos
# - archivos de datos
# - binarios
#
# ============================================================

for package in SUPABASE_PACKAGES:

    try:

        package_datas, package_binaries, package_hiddenimports = collect_all(
            package
        )

        datas += package_datas
        binaries += package_binaries
        hiddenimports += package_hiddenimports

    except Exception as e:

        print(
            f"AVISO: no se pudo recopilar completamente {package}: {e}"
        )


# ============================================================
# DEPENDENCIAS IMPORTANTES
# ============================================================

DEPENDENCY_PACKAGES = [

    "httpx",
    "httpcore",
    "anyio",
    "websockets",
    "pydantic",
    "pydantic_core",
    "yarl",
    "jwt",
    "cryptography",
    "cffi",
]

for package in DEPENDENCY_PACKAGES:

    try:

        package_datas, package_binaries, package_hiddenimports = collect_all(
            package
        )

        datas += package_datas
        binaries += package_binaries
        hiddenimports += package_hiddenimports

    except Exception:

        pass


# ============================================================
# VERSION.TXT
# ============================================================

if os.path.exists(VERSION_FILE):

    datas.append(
        (
            VERSION_FILE,
            "."
        )
    )


# ============================================================
# ELIMINAR DUPLICADOS
#
# Esto evita que datas/binaries/hiddenimports queden repetidos
# varias veces por collect_all + collect_submodules.
# ============================================================

def unique_list(items):

    resultado = []
    vistos = set()

    for item in items:

        try:

            clave = str(item)

        except Exception:

            clave = repr(item)

        if clave not in vistos:

            vistos.add(clave)
            resultado.append(item)

    return resultado


hiddenimports = unique_list(
    hiddenimports
)

datas = unique_list(
    datas
)

binaries = unique_list(
    binaries
)


# ============================================================
# IMPORTANTE:
# NO INCLUIR database/abril.db
# ============================================================

datas = [
    data
    for data in datas
    if not str(
        data[0]
    ).replace(
        "\\",
        "/"
    ).lower().endswith(
        "database/abril.db"
    )
]


# ============================================================
# ANALYSIS
# ============================================================

analysis = Analysis(

    [
        os.path.join(
            PROJECT_DIR,
            "main.py"
        )
    ],

    pathex=[
        PROJECT_DIR
    ],

    binaries=binaries,

    datas=datas,

    hiddenimports=hiddenimports,

    hookspath=[],

    hooksconfig={},

    runtime_hooks=[],

    excludes=[],

    noarchive=False,
)


# ============================================================
# PYZ
# ============================================================

pyz = PYZ(

    analysis.pure,

    analysis.zipped_data,
)


# ============================================================
# EXE
# ============================================================

exe = EXE(

    pyz,

    analysis.scripts,

    [],

    exclude_binaries=True,

    name="PAPELERA_POS",

    debug=False,

    bootloader_ignore_signals=False,

    strip=False,

    upx=True,

    console=False,
)


# ============================================================
# COLLECT
# ============================================================

coll = COLLECT(

    exe,

    analysis.binaries,

    analysis.datas,

    analysis.zipfiles,

    strip=False,

    upx=True,

    name="PAPELERA_POS",
)
