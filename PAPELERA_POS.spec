# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_data_files,
    collect_all,
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
# ============================================================

hiddenimports += collect_submodules("supabase")
hiddenimports += collect_submodules("postgrest")
hiddenimports += collect_submodules("realtime")
hiddenimports += collect_submodules("storage3")
hiddenimports += collect_submodules("supabase_auth")
hiddenimports += collect_submodules("supabase_functions")

# ============================================================
# PYDANTIC
# ============================================================

hiddenimports += collect_submodules("pydantic")

# ============================================================
# HTTPX
# ============================================================

hiddenimports += collect_submodules("httpx")

# ============================================================
# HTTP CORE
# ============================================================

hiddenimports += collect_submodules("httpcore")

# ============================================================
# ANYIO
# ============================================================

hiddenimports += collect_submodules("anyio")

# ============================================================
# WEBSOCKETS
# ============================================================

hiddenimports += collect_submodules("websockets")

# ============================================================
# JWT
# ============================================================

hiddenimports += collect_submodules("jwt")

# ============================================================
# CRYPTOGRAPHY
# ============================================================

hiddenimports += collect_submodules("cryptography")

# ============================================================
# CFFI
# ============================================================

hiddenimports += collect_submodules("cffi")

# ============================================================
# SUPABASE - IMPORTS PRINCIPALES FORZADOS
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
    # STORAGE
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
    # PYDANTIC
    # --------------------------------------------------------

    "pydantic",
    "pydantic_core",

    # --------------------------------------------------------
    # HTTP
    # --------------------------------------------------------

    "httpx",
    "httpcore",

    # --------------------------------------------------------
    # ASYNC
    # --------------------------------------------------------

    "anyio",

    # --------------------------------------------------------
    # WEBSOCKETS
    # --------------------------------------------------------

    "websockets",

    # --------------------------------------------------------
    # JWT
    # --------------------------------------------------------

    "jwt",

    # --------------------------------------------------------
    # CRYPTO
    # --------------------------------------------------------

    "cryptography",

    # --------------------------------------------------------
    # CFFI
    # --------------------------------------------------------

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

datas += collect_data_files("certifi")

# ============================================================
# DOTENV
# ============================================================

dotenv_datas, dotenv_binaries, dotenv_hiddenimports = collect_all(
    "dotenv"
)

datas += dotenv_datas
binaries += dotenv_binaries
hiddenimports += dotenv_hiddenimports

# ============================================================
# SUPABASE
# ============================================================

supabase_datas, supabase_binaries, supabase_hiddenimports = collect_all(
    "supabase"
)

datas += supabase_datas
binaries += supabase_binaries
hiddenimports += supabase_hiddenimports

# ============================================================
# POSTGREST
# ============================================================

postgrest_datas, postgrest_binaries, postgrest_hiddenimports = collect_all(
    "postgrest"
)

datas += postgrest_datas
binaries += postgrest_binaries
hiddenimports += postgrest_hiddenimports

# ============================================================
# REALTIME
# ============================================================

realtime_datas, realtime_binaries, realtime_hiddenimports = collect_all(
    "realtime"
)

datas += realtime_datas
binaries += realtime_binaries
hiddenimports += realtime_hiddenimports

# ============================================================
# STORAGE3
# ============================================================

storage3_datas, storage3_binaries, storage3_hiddenimports = collect_all(
    "storage3"
)

datas += storage3_datas
binaries += storage3_binaries
hiddenimports += storage3_hiddenimports

# ============================================================
# SUPABASE AUTH
# ============================================================

auth_datas, auth_binaries, auth_hiddenimports = collect_all(
    "supabase_auth"
)

datas += auth_datas
binaries += auth_binaries
hiddenimports += auth_hiddenimports

# ============================================================
# SUPABASE FUNCTIONS
# ============================================================

functions_datas, functions_binaries, functions_hiddenimports = collect_all(
    "supabase_functions"
)

datas += functions_datas
binaries += functions_binaries
hiddenimports += functions_hiddenimports

# ============================================================
# PYDANTIC
# ============================================================

pydantic_datas, pydantic_binaries, pydantic_hiddenimports = collect_all(
    "pydantic"
)

datas += pydantic_datas
binaries += pydantic_binaries
hiddenimports += pydantic_hiddenimports

# ============================================================
# PYDANTIC CORE
# ============================================================

pydantic_core_datas, pydantic_core_binaries, pydantic_core_hiddenimports = collect_all(
    "pydantic_core"
)

datas += pydantic_core_datas
binaries += pydantic_core_binaries
hiddenimports += pydantic_core_hiddenimports

# ============================================================
# HTTPX
# ============================================================

httpx_datas, httpx_binaries, httpx_hiddenimports = collect_all(
    "httpx"
)

datas += httpx_datas
binaries += httpx_binaries
hiddenimports += httpx_hiddenimports

# ============================================================
# HTTPCORE
# ============================================================

httpcore_datas, httpcore_binaries, httpcore_hiddenimports = collect_all(
    "httpcore"
)

datas += httpcore_datas
binaries += httpcore_binaries
hiddenimports += httpcore_hiddenimports

# ============================================================
# ANYIO
# ============================================================

anyio_datas, anyio_binaries, anyio_hiddenimports = collect_all(
    "anyio"
)

datas += anyio_datas
binaries += anyio_binaries
hiddenimports += anyio_hiddenimports

# ============================================================
# WEBSOCKETS
# ============================================================

websockets_datas, websockets_binaries, websockets_hiddenimports = collect_all(
    "websockets"
)

datas += websockets_datas
binaries += websockets_binaries
hiddenimports += websockets_hiddenimports

# ============================================================
# PYJWT
# ============================================================

jwt_datas, jwt_binaries, jwt_hiddenimports = collect_all(
    "jwt"
)

datas += jwt_datas
binaries += jwt_binaries
hiddenimports += jwt_hiddenimports

# ============================================================
# CRYPTOGRAPHY
# ============================================================

crypto_datas, crypto_binaries, crypto_hiddenimports = collect_all(
    "cryptography"
)

datas += crypto_datas
binaries += crypto_binaries
hiddenimports += crypto_hiddenimports

# ============================================================
# CFFI
# ============================================================

cffi_datas, cffi_binaries, cffi_hiddenimports = collect_all(
    "cffi"
)

datas += cffi_datas
binaries += cffi_binaries
hiddenimports += cffi_hiddenimports

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
# ELIMINAR DATABASE
# ============================================================

datas = [
    data
    for data in datas
    if not str(data[0]).replace(
        "\\",
        "/"
    ).lower().endswith(
        "database/abril.db"
    )
]

# ============================================================
# ELIMINAR DUPLICADOS
# ============================================================

hiddenimports = list(
    dict.fromkeys(hiddenimports)
)

datas = list(
    dict.fromkeys(datas)
)

binaries = list(
    dict.fromkeys(binaries)
)

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

    name="PAPELERA_POS"
)