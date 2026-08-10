# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_submodules


# ==========================================
# CARPETA DEL PROYECTO
# ==========================================

PROJECT_DIR = os.getcwd()


# ==========================================
# IMPORTS OCULTOS DE UI
# ==========================================

hiddenimports = collect_submodules("ui")


# ==========================================
# VERSION.TXT
# ==========================================

VERSION_FILE = os.path.join(
    PROJECT_DIR,
    "version.txt"
)


if not os.path.exists(VERSION_FILE):
    raise FileNotFoundError(
        "NO SE ENCONTRO version.txt: "
        + VERSION_FILE
    )


datas = [
    (
        VERSION_FILE,
        "."
    )
]


# ==========================================
# ANALYSIS
# ==========================================

analysis = Analysis(
    ["main.py"],

    pathex=[
        PROJECT_DIR
    ],

    binaries=[],

    datas=datas,

    hiddenimports=hiddenimports,

    hookspath=[],

    hooksconfig={},

    runtime_hooks=[],

    excludes=[],

    noarchive=False,
)


# ==========================================
# PYZ
# ==========================================

pyz = PYZ(
    analysis.pure
)


# ==========================================
# EXE
# ==========================================

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


# ==========================================
# COLLECT
# ==========================================

coll = COLLECT(
    exe,

    analysis.binaries,

    analysis.datas,

    analysis.zipfiles,

    strip=False,

    upx=True,

    name="PAPELERA_POS",
)