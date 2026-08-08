# -*- mode: python ; coding: utf-8 -*-

analysis = Analysis(
    ['updater.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'core.actualizador'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(
    analysis.pure
)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name='PAPELERA_UPDATER',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    name='PAPELERA_UPDATER',
)