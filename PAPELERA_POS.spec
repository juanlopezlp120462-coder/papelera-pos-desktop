# -*- mode: python ; coding: utf-8 -*-

import os
import certifi

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
# CERTIFICADO SSL
# ==========================================

CERTIFI_FILE = certifi.where()

if not os.path.exists(CERTIFI_FILE):
    raise FileNotFoundError(
        "NO SE ENCONTRO cacert.pem: "
        + CERTIFI_FILE
    )


# ==========================================
# ARCHIVOS EXTRA
# ==========================================

datas = [
    (
        CERTIFI_FILE,
        "certifi"
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