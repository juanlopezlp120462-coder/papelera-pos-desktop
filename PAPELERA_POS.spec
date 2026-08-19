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


# Todos los módulos de ui
hiddenimports += collect_submodules(
    "ui"
)


# Certifi
hiddenimports += collect_submodules(
    "certifi"
)


# ============================================================
# DOTENV
# ============================================================

dotenv_datas, dotenv_binaries, dotenv_hiddenimports = collect_all(
    "dotenv"
)

datas = []

datas += dotenv_datas

hiddenimports += dotenv_hiddenimports

binaries = []

binaries += dotenv_binaries


# ============================================================
# CERTIFI
# ============================================================

datas += collect_data_files(
    "certifi"
)


# ============================================================
# VERSION.TXT
# ============================================================

if os.path.exists(
    VERSION_FILE
):

    datas.append(
        (
            VERSION_FILE,
            "."
        )
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