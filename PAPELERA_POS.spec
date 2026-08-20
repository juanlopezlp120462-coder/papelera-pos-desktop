# -*- mode: python ; coding: utf-8 -*-

import os

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

# UI
hiddenimports += collect_submodules("ui")

# Certifi
hiddenimports += collect_submodules("certifi")

# Dotenv
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
# SUPABASE FORZADO
# ============================================================

hiddenimports += [
    "supabase",
    "supabase.client",
    "supabase._sync",
    "supabase._sync.client",
    "supabase._sync.auth_client",
    "supabase._async",
    "supabase._async.client",
    "supabase._async.auth_client",

    "postgrest",
    "postgrest._sync",
    "postgrest._sync.client",
    "postgrest._sync.request_builder",
    "postgrest._async",
    "postgrest._async.client",
    "postgrest._async.request_builder",

    "realtime",
    "realtime._sync",
    "realtime._sync.client",
    "realtime._sync.channel",
    "realtime._sync.presence",
    "realtime._async",
    "realtime._async.client",
    "realtime._async.channel",

    "storage3",
    "storage3._sync",
    "storage3._sync.client",
    "storage3._sync.bucket",
    "storage3._async",
    "storage3._async.client",
    "storage3._async.bucket",

    "supabase_auth",
    "supabase_auth._sync",
    "supabase_auth._sync.gotrue_client",
    "supabase_auth._async",
    "supabase_auth._async.gotrue_client",
]
# ============================================================
# DATOS
# ============================================================

datas = []
binaries = []

# ------------------------------------------------------------
# Certifi
# ------------------------------------------------------------

datas += collect_data_files("certifi")

# ------------------------------------------------------------
# Dotenv
# ------------------------------------------------------------

dotenv_datas, dotenv_binaries, dotenv_hiddenimports = collect_all(
    "dotenv"
)

datas += dotenv_datas
binaries += dotenv_binaries
hiddenimports += dotenv_hiddenimports

# ------------------------------------------------------------
# Supabase
# ------------------------------------------------------------

supabase_datas, supabase_binaries, supabase_hiddenimports = collect_all(
    "supabase"
)

datas += supabase_datas
binaries += supabase_binaries
hiddenimports += supabase_hiddenimports

# ------------------------------------------------------------
# PostgREST
# ------------------------------------------------------------

postgrest_datas, postgrest_binaries, postgrest_hiddenimports = collect_all(
    "postgrest"
)

datas += postgrest_datas
binaries += postgrest_binaries
hiddenimports += postgrest_hiddenimports

# ------------------------------------------------------------
# Realtime
# ------------------------------------------------------------

realtime_datas, realtime_binaries, realtime_hiddenimports = collect_all(
    "realtime"
)

datas += realtime_datas
binaries += realtime_binaries
hiddenimports += realtime_hiddenimports

# ------------------------------------------------------------
# Storage3
# ------------------------------------------------------------

storage3_datas, storage3_binaries, storage3_hiddenimports = collect_all(
    "storage3"
)

datas += storage3_datas
binaries += storage3_binaries
hiddenimports += storage3_hiddenimports

# ------------------------------------------------------------
# Supabase Auth
# ------------------------------------------------------------

auth_datas, auth_binaries, auth_hiddenimports = collect_all(
    "supabase_auth"
)

datas += auth_datas
binaries += auth_binaries
hiddenimports += auth_hiddenimports

# ------------------------------------------------------------
# Supabase Functions
# ------------------------------------------------------------

functions_datas, functions_binaries, functions_hiddenimports = collect_all(
    "supabase_functions"
)

datas += functions_datas
binaries += functions_binaries
hiddenimports += functions_hiddenimports

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
# IMPORTANTE:
# NO INCLUIR database/abril.db EN PYINSTALLER
# ============================================================

datas = [
    data
    for data in datas
    if not str(data[0]).replace("\\", "/").lower().endswith(
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

    name="PAPELERA_POS"
)