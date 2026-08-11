# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_data_files


# ============================================================
# CARPETA DEL PROYECTO
# ============================================================

PROJECT_DIR = os.path.dirname(
    os.path.abspath(SPEC)
)


# ============================================================
# IMPORTS OCULTOS
# ============================================================

hiddenimports = []

hiddenimports += collect_submodules("ui")
hiddenimports += collect_submodules("certifi")


# ============================================================
# DATOS
# ============================================================

datas = []

datas += collect_data_files(
    "certifi"
)


# ============================================================
# VERSION.TXT
# ============================================================

VERSION_FILE = os.path.join(
    PROJECT_DIR,
    "version.txt"
)

if os.path.exists(VERSION_FILE):
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

    binaries=[],

    datas=datas,

    hiddenimports=hiddenimports,

    hookspath=[],

    hooksconfig={},

    runtime_hooks=[],

    excludes=[],

    noarchive=False
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

    console=True
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

