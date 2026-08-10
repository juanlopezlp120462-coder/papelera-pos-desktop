# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_data_files

PROJECT_DIR = os.path.dirname(os.path.abspath(SPEC))

datas = []

datas += collect_data_files("certifi")

analysis = Analysis(
    [
        os.path.join(PROJECT_DIR, "updater.py")
    ],

    pathex=[
        PROJECT_DIR
    ],

    binaries=[],

    datas=datas,

    hiddenimports=[
        "certifi",
        "requests",
    ],

    hookspath=[],

    hooksconfig={},

    runtime_hooks=[],

    excludes=[],

    noarchive=False
)

pyz = PYZ(
    analysis.pure
)

exe = EXE(
    pyz,
    analysis.scripts,
    [],

    exclude_binaries=True,

    name="PAPELERA_UPDATER",

    debug=False,

    bootloader_ignore_signals=False,

    strip=False,

    upx=True,

    console=True
)

coll = COLLECT(
    exe,

    analysis.binaries,

    analysis.datas,

    analysis.zipfiles,

    strip=False,

    upx=True,

    name="PAPELERA_UPDATER"
)
