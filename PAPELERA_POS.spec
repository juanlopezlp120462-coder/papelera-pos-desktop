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
# ARCHIVO DE VERSION
# ============================================================

VERSION_FILE = os.path.join(
    PROJECT_DIR,
    "version.txt"
)


# ============================================================
# HIDDEN IMPORTS
# ============================================================

hiddenimports = []


# ------------------------------------------------------------
# Todos los módulos de UI
# ------------------------------------------------------------

hiddenimports += collect_submodules(
    "ui"
)


# ------------------------------------------------------------
# Certifi
# ------------------------------------------------------------

hiddenimports += collect_submodules(
    "certifi"
)


# ------------------------------------------------------------
# python-dotenv
# ------------------------------------------------------------

hiddenimports += collect_submodules(
    "dotenv"
)


# ------------------------------------------------------------
# SUPABASE
# ------------------------------------------------------------

hiddenimports += collect_submodules(
    "supabase"
)

hiddenimports += collect_submodules(
    "postgrest"
)

hiddenimports += collect_submodules(
    "realtime"
)

hiddenimports += collect_submodules(
    "storage3"
)

hiddenimports += collect_submodules(
    "supabase_auth"
)

hiddenimports += collect_submodules(
    "supabase_functions"
)


# ============================================================
# DATOS
# ============================================================

datas = []


# ------------------------------------------------------------
# BASE DE DATOS INICIAL
# ------------------------------------------------------------

DATABASE_FILE = os.path.join(
    PROJECT_DIR,
    "database",
    "abril.db"
)

if os.path.exists(DATABASE_FILE):

    datas.append(
        (
            DATABASE_FILE,
            "database"
        )
    )


# ------------------------------------------------------------
# Certifi
# ------------------------------------------------------------

datas += collect_data_files(
    "certifi"
)

# ------------------------------------------------------------
# python-dotenv
# ------------------------------------------------------------

dotenv_datas, dotenv_binaries, dotenv_hiddenimports = collect_all(
    "dotenv"
)

datas += dotenv_datas

hiddenimports += dotenv_hiddenimports


# ------------------------------------------------------------
# SUPABASE
# ------------------------------------------------------------

supabase_datas, supabase_binaries, supabase_hiddenimports = collect_all(
    "supabase"
)

datas += supabase_datas

hiddenimports += supabase_hiddenimports


# ------------------------------------------------------------
# PostgREST
# ------------------------------------------------------------

postgrest_datas, postgrest_binaries, postgrest_hiddenimports = collect_all(
    "postgrest"
)

datas += postgrest_datas

hiddenimports += postgrest_hiddenimports


# ------------------------------------------------------------
# Realtime
# ------------------------------------------------------------

realtime_datas, realtime_binaries, realtime_hiddenimports = collect_all(
    "realtime"
)

datas += realtime_datas

hiddenimports += realtime_hiddenimports


# ------------------------------------------------------------
# Storage3
# ------------------------------------------------------------

storage3_datas, storage3_binaries, storage3_hiddenimports = collect_all(
    "storage3"
)

datas += storage3_datas

hiddenimports += storage3_hiddenimports


# ------------------------------------------------------------
# Supabase Auth
# ------------------------------------------------------------

auth_datas, auth_binaries, auth_hiddenimports = collect_all(
    "supabase_auth"
)

datas += auth_datas

hiddenimports += auth_hiddenimports


# ------------------------------------------------------------
# Supabase Functions
# ------------------------------------------------------------

functions_datas, functions_binaries, functions_hiddenimports = collect_all(
    "supabase_functions"
)

datas += functions_datas

hiddenimports += functions_hiddenimports


# ------------------------------------------------------------
# Version.txt
# ------------------------------------------------------------

if os.path.exists(VERSION_FILE):

    datas.append(
        (
            VERSION_FILE,
            "."
        )
    )

# ============================================================
# NO INCLUIR LA BASE DE DATOS EN PYINSTALLER
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

    binaries=(
        dotenv_binaries
        + supabase_binaries
        + postgrest_binaries
        + realtime_binaries
        + storage3_binaries
        + auth_binaries
        + functions_binaries
    ),

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
    analysis.pure
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