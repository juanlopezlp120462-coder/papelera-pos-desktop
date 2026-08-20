# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import (
    collect_all,
    collect_submodules,
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
# PAQUETES
# ============================================================

PAQUETES = [
    "supabase",
    "postgrest",
    "realtime",
    "storage3",
    "supabase_auth",
    "supabase_functions",
    "pydantic",
    "pydantic_core",
    "httpx",
    "httpcore",
    "anyio",
    "websockets",
    "jwt",
    "cryptography",
    "cffi",
    "dotenv",
    "certifi",
]

# ============================================================
# LISTAS
# ============================================================

hiddenimports = []
datas = []
binaries = []

# ============================================================
# UI PROPIA
# ============================================================

ui_imports = collect_submodules("ui")

print("")
print("=" * 70)
print(
    f"[PyInstaller] UI: {len(ui_imports)} submodulos encontrados"
)
print("=" * 70)

hiddenimports += ui_imports

# ============================================================
# RECOPILAR PAQUETES
# ============================================================

for paquete in PAQUETES:

    print("")
    print("=" * 70)
    print(f"[PyInstaller] RECOPILANDO: {paquete}")
    print("=" * 70)

    try:

        paquete_datas, paquete_binaries, paquete_hidden = (
            collect_all(paquete)
        )

        print(
            f"[PyInstaller] {paquete} hidden imports: "
            f"{len(paquete_hidden)}"
        )

        print(
            f"[PyInstaller] {paquete} datas: "
            f"{len(paquete_datas)}"
        )

        print(
            f"[PyInstaller] {paquete} binaries: "
            f"{len(paquete_binaries)}"
        )

        hiddenimports += paquete_hidden
        datas += paquete_datas
        binaries += paquete_binaries

    except Exception as e:

        print("")
        print(
            f"[PyInstaller] ERROR recopilando {paquete}"
        )
        print(e)
        print("")

        raise

# ============================================================
# RECOPILAR TODOS LOS SUBMODULOS
# ============================================================

for paquete in PAQUETES:

    try:

        submodulos = collect_submodules(paquete)

        print(
            f"[PyInstaller] {paquete}: "
            f"{len(submodulos)} submodulos adicionales"
        )

        hiddenimports += submodulos

    except Exception as e:

        print(
            f"[PyInstaller] ADVERTENCIA con submodulos "
            f"de {paquete}: {e}"
        )

# ============================================================
# HIDDEN IMPORTS EXPLICITOS
# ============================================================

hiddenimports += [

    # SUPABASE
    "supabase",
    "supabase.client",
    "supabase._sync",
    "supabase._sync.client",
    "supabase._sync.auth_client",
    "supabase._async",
    "supabase._async.client",
    "supabase._async.auth_client",

    # POSTGREST
    "postgrest",
    "postgrest._sync",
    "postgrest._sync.client",
    "postgrest._sync.request_builder",
    "postgrest._async",
    "postgrest._async.client",
    "postgrest._async.request_builder",

    # REALTIME
    "realtime",
    "realtime._sync",
    "realtime._sync.client",
    "realtime._sync.channel",
    "realtime._sync.presence",
    "realtime._async",
    "realtime._async.client",
    "realtime._async.channel",

    # STORAGE
    "storage3",
    "storage3._sync",
    "storage3._sync.client",
    "storage3._sync.bucket",
    "storage3._async",
    "storage3._async.client",
    "storage3._async.bucket",

    # AUTH
    "supabase_auth",
    "supabase_auth._sync",
    "supabase_auth._sync.gotrue_client",
    "supabase_auth._async",
    "supabase_auth._async.gotrue_client",

    # FUNCTIONS
    "supabase_functions",

    # PYDANTIC
    "pydantic",
    "pydantic_core",

    # HTTP
    "httpx",
    "httpcore",

    # ASYNC
    "anyio",

    # WEBSOCKETS
    "websockets",

    # JWT
    "jwt",

    # CRYPTO
    "cryptography",

    # CFFI
    "cffi",

    # DOTENV
    "dotenv",

    # CERTIFI
    "certifi",
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
# VERSION.TXT
# ============================================================

if os.path.exists(VERSION_FILE):

    datas.append(
        (
            VERSION_FILE,
            "."
        )
    )

else:

    print(
        "[PyInstaller] ADVERTENCIA: "
        "no existe version.txt"
    )

# ============================================================
# RESUMEN
# ============================================================

print("")
print("=" * 70)
print("RESUMEN FINAL PYINSTALLER")
print("=" * 70)

print(
    f"Hidden imports : {len(hiddenimports)}"
)

print(
    f"Data files     : {len(datas)}"
)

print(
    f"Binaries       : {len(binaries)}"
)

print("=" * 70)
print("")

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