# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_data_files,
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
# PAQUETES IMPORTANTES
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
# HIDDEN IMPORTS
# ============================================================

hiddenimports = []

# ============================================================
# UI PROPIA
# ============================================================

ui_imports = collect_submodules("ui")

print(
    f"[PyInstaller] UI: "
    f"{len(ui_imports)} submodulos encontrados"
)

hiddenimports += ui_imports

# ============================================================
# RECOPILAR SUBMODULOS
# ============================================================

for paquete in PAQUETES:

    print("")
    print("=" * 60)
    print(f"[PyInstaller] ANALIZANDO: {paquete}")
    print("=" * 60)

    try:

        encontrados = collect_submodules(paquete)

        print(
            f"[PyInstaller] {paquete}: "
            f"{len(encontrados)} submodulos encontrados"
        )

        if not encontrados:

            print(
                f"[PyInstaller] ADVERTENCIA: "
                f"{paquete} no devolvio submodulos"
            )

        hiddenimports += encontrados

    except Exception as e:

        print(
            f"[PyInstaller] ERROR recopilando "
            f"submodulos de {paquete}: {e}"
        )

        raise

# ============================================================
# IMPORTS PRINCIPALES FORZADOS
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

    # --------------------------------------------------------
    # DOTENV
    # --------------------------------------------------------

    "dotenv",

    # --------------------------------------------------------
    # CERTIFI
    # --------------------------------------------------------

    "certifi",
]

# ============================================================
# ELIMINAR DUPLICADOS
# ============================================================

hiddenimports = list(
    dict.fromkeys(hiddenimports)
)

# ============================================================
# DATOS
# ============================================================

datas = []
binaries = []

# ============================================================
# RECOPILAR DATOS
# ============================================================

for paquete in PAQUETES:

    print("")
    print(
        f"[PyInstaller] RECOPILANDO DATOS: {paquete}"
    )

    try:

        encontrados = collect_data_files(
            paquete,
            include_py_files=True
        )

        print(
            f"[PyInstaller] {paquete}: "
            f"{len(encontrados)} archivos de datos"
        )

        datas += encontrados

    except Exception as e:

        print(
            f"[PyInstaller] ERROR recopilando datos "
            f"de {paquete}: {e}"
        )

        raise

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
        "no existe version.txt en el proyecto"
    )

# ============================================================
# ELIMINAR DUPLICADOS
# ============================================================

datas = list(
    dict.fromkeys(datas)
)

binaries = list(
    dict.fromkeys(binaries)
)

# ============================================================
# RESUMEN
# ============================================================

print("")
print("=" * 60)
print("RESUMEN PYINSTALLER")
print("=" * 60)

print(
    f"Hidden imports: {len(hiddenimports)}"
)

print(
    f"Data files: {len(datas)}"
)

print(
    f"Binaries: {len(binaries)}"
)

print("=" * 60)
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