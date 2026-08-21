import os
import sys
import time
import shutil
import zipfile
import subprocess
import tempfile


# ============================================================
# CONFIGURACION
# ============================================================

NOMBRE_EXE = "PAPELERA_POS.exe"

CARPETA_TEMP = "PAPELERA_UPDATE_TEMP"

MAX_INTENTOS = 30

ESPERA = 1


# ============================================================
# ESPERAR CIERRE DEL PROGRAMA
# ============================================================

def esperar_programa():

    for intento in range(MAX_INTENTOS):

        try:

            r = subprocess.run(
                [
                    "tasklist",
                    "/FI",
                    f"IMAGENAME eq {NOMBRE_EXE}"
                ],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if NOMBRE_EXE.lower() not in r.stdout.lower():

                return True

        except Exception:

            pass

        time.sleep(ESPERA)

    return False


# ============================================================
# BORRAR CARPETA
# ============================================================

def borrar_carpeta(ruta):

    if not os.path.exists(ruta):

        return True

    for _ in range(MAX_INTENTOS):

        try:

            shutil.rmtree(ruta)

            return True

        except Exception:

            time.sleep(ESPERA)

    return False


# ============================================================
# BORRAR ARCHIVO
# ============================================================

def borrar_archivo(ruta):

    if not os.path.exists(ruta):

        return True

    for _ in range(MAX_INTENTOS):

        try:

            os.remove(ruta)

            return True

        except Exception:

            time.sleep(ESPERA)

    return False


# ============================================================
# LEER VERSION
# ============================================================

def leer_version(ruta):

    try:

        with open(
            ruta,
            "r",
            encoding="utf-8"
        ) as f:

            return f.read().strip()

    except Exception:

        return ""


# ============================================================
# COPIAR ARCHIVO
# ============================================================

def copiar_archivo(origen, destino):

    for _ in range(MAX_INTENTOS):

        try:

            shutil.copy2(
                origen,
                destino
            )

            return True

        except Exception:

            time.sleep(ESPERA)

    return False


# ============================================================
# RESTAURAR BACKUP
# ============================================================

def restaurar_backup(
    exe_actual,
    internal_actual,
    exe_backup,
    internal_backup
):

    print("")
    print("Restaurando version anterior...")

    # --------------------------------------------------------
    # ELIMINAR INSTALACION NUEVA
    # --------------------------------------------------------

    borrar_archivo(
        exe_actual
    )

    borrar_carpeta(
        internal_actual
    )

    # --------------------------------------------------------
    # RESTAURAR EXE
    # --------------------------------------------------------

    if os.path.exists(exe_backup):

        try:

            shutil.move(
                exe_backup,
                exe_actual
            )

        except Exception as e:

            print(
                "ERROR restaurando EXE:",
                e
            )

    # --------------------------------------------------------
    # RESTAURAR INTERNAL
    # --------------------------------------------------------

    if os.path.exists(internal_backup):

        try:

            shutil.move(
                internal_backup,
                internal_actual
            )

        except Exception as e:

            print(
                "ERROR restaurando _internal:",
                e
            )

    # ========================================================
    # IMPORTANTE
    #
    # .env.pos NO SE TOCA.
    #
    # database NO SE TOCA.
    # ========================================================

    print("")
    print("Backup restaurado.")


# ============================================================
# ACTUALIZAR
# ============================================================

def actualizar():

    # ========================================================
    # VERIFICAR ARGUMENTOS
    # ========================================================

    if len(sys.argv) < 2:

        print(
            "No se recibio update.zip"
        )

        return False


    zip_path = os.path.abspath(
        sys.argv[1]
    )


    if not os.path.exists(zip_path):

        print(
            "No existe:",
            zip_path
        )

        return False


    # ========================================================
    # CARPETA DE INSTALACION
    # ========================================================

    carpeta_actual = os.path.dirname(
        os.path.abspath(
            sys.executable
        )
    )


    print("")
    print("===================================")
    print(" ACTUALIZADOR PAPELERA POS")
    print("===================================")
    print("")
    print(
        "Instalacion:",
        carpeta_actual
    )


    # ========================================================
    # .ENV.POS FIJO
    #
    # IMPORTANTE:
    #
    # .env.pos esta FUERA de _internal.
    #
    # El updater NO lo mueve.
    # El updater NO lo copia.
    # El updater NO lo elimina.
    #
    # sync.py lo busca directamente aqui:
    #
    # PAPELERA_POS\.env.pos
    # ========================================================

    env_pos = os.path.join(
        carpeta_actual,
        ".env.pos"
    )


    if os.path.isfile(env_pos):

        print("")
        print(
            ".env.pos encontrado."
        )
        print(
            ".env.pos queda fijo y NO sera tocado."
        )

    else:

        print("")
        print(
            "AVISO: no se encontro .env.pos."
        )
        print(
            "La actualizacion continuara."
        )


    # ========================================================
    # ESPERAR CIERRE
    # ========================================================

    print("")
    print(
        "Esperando cierre del programa..."
    )


    if not esperar_programa():

        print("")
        print(
            "ERROR: el programa sigue abierto."
        )

        return False


    # ========================================================
    # TEMP
    # ========================================================

    carpeta_temp = os.path.join(
        tempfile.gettempdir(),
        CARPETA_TEMP
    )


    borrar_carpeta(
        carpeta_temp
    )


    os.makedirs(
        carpeta_temp,
        exist_ok=True
    )


    # ========================================================
    # EXTRAER ZIP
    # ========================================================

    print("")
    print(
        "Extrayendo update..."
    )


    try:

        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as z:

            z.extractall(
                carpeta_temp
            )

    except Exception as e:

        print("")
        print(
            "ERROR extrayendo update:",
            e
        )

        borrar_carpeta(
            carpeta_temp
        )

        return False


    # ========================================================
    # RUTAS NUEVAS
    # ========================================================

    nuevo_exe = os.path.join(
        carpeta_temp,
        NOMBRE_EXE
    )


    nuevo_internal = os.path.join(
        carpeta_temp,
        "_internal"
    )


    nueva_version = os.path.join(
        carpeta_temp,
        "version.txt"
    )


    # ========================================================
    # VERIFICAR UPDATE EXTRAIDO
    # ========================================================

    if not os.path.exists(nuevo_exe):

        print("")
        print(
            "ERROR: falta PAPELERA_POS.exe en el update."
        )

        borrar_carpeta(
            carpeta_temp
        )

        return False


    if not os.path.isdir(nuevo_internal):

        print("")
        print(
            "ERROR: falta _internal en el update."
        )

        borrar_carpeta(
            carpeta_temp
        )

        return False


    if not os.path.exists(nueva_version):

        print("")
        print(
            "ERROR: falta version.txt en el update."
        )

        borrar_carpeta(
            carpeta_temp
        )

        return False


    # ========================================================
    # VERIFICAR PYTHON312.DLL EN EL UPDATE
    # ========================================================

    nuevo_python_dll = os.path.join(
        nuevo_internal,
        "python312.dll"
    )


    if not os.path.exists(
        nuevo_python_dll
    ):

        print("")
        print(
            "ERROR: el update no contiene python312.dll."
        )

        borrar_carpeta(
            carpeta_temp
        )

        return False


    # ========================================================
    # RUTAS INSTALACION ACTUAL
    # ========================================================

    exe_actual = os.path.join(
        carpeta_actual,
        NOMBRE_EXE
    )


    internal_actual = os.path.join(
        carpeta_actual,
        "_internal"
    )


    version_actual = os.path.join(
        carpeta_actual,
        "version.txt"
    )


    # ========================================================
    # BACKUPS
    # ========================================================

    exe_backup = os.path.join(
        carpeta_actual,
        "PAPELERA_POS_BACKUP.exe"
    )


    internal_backup = os.path.join(
        carpeta_actual,
        "_internal_BACKUP"
    )


    # ========================================================
    # VERSION DEL UPDATE
    # ========================================================

    version_nueva = leer_version(
        nueva_version
    )


    if not version_nueva:

        print("")
        print(
            "ERROR: version.txt del update esta vacio."
        )

        borrar_carpeta(
            carpeta_temp
        )

        return False


    version_instalada_anterior = leer_version(
        version_actual
    )


    print("")
    print(
        "Version instalada:",
        version_instalada_anterior
    )

    print(
        "Version del update:",
        version_nueva
    )


    # ========================================================
    # EVITAR ACTUALIZACION INVALIDA
    # ========================================================

    if (
        version_instalada_anterior
        and
        version_nueva
        == version_instalada_anterior
    ):

        print("")
        print(
            "La version del update ya esta instalada."
        )

        borrar_carpeta(
            carpeta_temp
        )

        return False


    # ========================================================
    # LIMPIAR BACKUPS ANTERIORES
    # ========================================================

    borrar_archivo(
        exe_backup
    )


    borrar_carpeta(
        internal_backup
    )


    print("")
    print(
        "Creando backups..."
    )


    # ========================================================
    # BACKUP EXE
    # ========================================================

    if os.path.exists(exe_actual):

        try:

            shutil.move(
                exe_actual,
                exe_backup
            )

        except Exception as e:

            print("")
            print(
                "ERROR: no se pudo respaldar EXE:"
            )
            print(e)

            borrar_carpeta(
                carpeta_temp
            )

            return False


    # ========================================================
    # BACKUP INTERNAL
    # ========================================================

    if os.path.exists(internal_actual):

        try:

            shutil.move(
                internal_actual,
                internal_backup
            )

        except Exception as e:

            print("")
            print(
                "ERROR: no se pudo respaldar _internal:"
            )
            print(e)

            # Restaurar EXE

            if os.path.exists(
                exe_backup
            ):

                try:

                    shutil.move(
                        exe_backup,
                        exe_actual
                    )

                except Exception as restore_error:

                    print(
                        "ERROR restaurando EXE:",
                        restore_error
                    )

            borrar_carpeta(
                carpeta_temp
            )

            return False


    # ========================================================
    # INSTALAR NUEVA VERSION
    # ========================================================

    print("")
    print(
        "Instalando nueva version..."
    )


    try:

        # ----------------------------------------------------
        # MOVER NUEVO INTERNAL
        # ----------------------------------------------------

        shutil.move(
            nuevo_internal,
            internal_actual
        )


        # ----------------------------------------------------
        # COPIAR EXE
        # ----------------------------------------------------

        shutil.copy2(
            nuevo_exe,
            exe_actual
        )


        # ----------------------------------------------------
        # VERSION
        # ----------------------------------------------------

        shutil.copy2(
            nueva_version,
            version_actual
        )


    except Exception as e:

        print("")
        print(
            "ERROR instalando nueva version:"
        )
        print(e)


        restaurar_backup(
            exe_actual,
            internal_actual,
            exe_backup,
            internal_backup
        )


        borrar_carpeta(
            carpeta_temp
        )

        return False


    # ========================================================
    # VERIFICAR EXE
    # ========================================================

    if not os.path.exists(
        exe_actual
    ):

        print("")
        print(
            "ERROR: no existe PAPELERA_POS.exe despues de instalar."
        )


        restaurar_backup(
            exe_actual,
            internal_actual,
            exe_backup,
            internal_backup
        )


        borrar_carpeta(
            carpeta_temp
        )

        return False


    # ========================================================
    # VERIFICAR INTERNAL
    # ========================================================

    if not os.path.isdir(
        internal_actual
    ):

        print("")
        print(
            "ERROR: no existe _internal despues de instalar."
        )


        restaurar_backup(
            exe_actual,
            internal_actual,
            exe_backup,
            internal_backup
        )


        borrar_carpeta(
            carpeta_temp
        )

        return False


    # ========================================================
    # VERIFICAR PYTHON312.DLL
    # ========================================================

    python_dll = os.path.join(
        internal_actual,
        "python312.dll"
    )


    if not os.path.exists(
        python_dll
    ):

        print("")
        print(
            "ERROR: falta python312.dll en la nueva version."
        )


        restaurar_backup(
            exe_actual,
            internal_actual,
            exe_backup,
            internal_backup
        )


        borrar_carpeta(
            carpeta_temp
        )

        return False


    print("")
    print(
        "python312.dll : OK"
    )


    # ========================================================
    # VERIFICAR VERSION INSTALADA
    # ========================================================

    version_instalada = leer_version(
        version_actual
    )


    print("")
    print(
        "Version instalada despues de actualizar:",
        version_instalada
    )


    if version_nueva != version_instalada:

        print("")
        print(
            "ERROR: la version instalada no coincide con el update."
        )

        print(
            "Esperada:",
            version_nueva
        )

        print(
            "Encontrada:",
            version_instalada
        )


        restaurar_backup(
            exe_actual,
            internal_actual,
            exe_backup,
            internal_backup
        )


        borrar_carpeta(
            carpeta_temp
        )

        return False


    # ========================================================
    # VERIFICAR .ENV.POS
    #
    # SOLAMENTE LO COMPROBAMOS.
    #
    # NO LO TOCAMOS.
    # ========================================================

    if os.path.isfile(env_pos):

        print("")
        print(
            ".env.pos : CONSERVADO"
        )

    else:

        print("")
        print(
            "AVISO: .env.pos no existe."
        )

        print(
            "El updater no lo crea ni lo modifica."
        )


    # ========================================================
    # VERIFICACION FINAL
    # ========================================================

    print("")
    print(
        "==================================="
    )
    print(
        " VERIFICACION FINAL"
    )
    print(
        "==================================="
    )


    print("")
    print(
        "PAPELERA_POS.exe : OK"
    )

    print(
        "_internal : OK"
    )

    print(
        "python312.dll : OK"
    )

    print(
        "version.txt : OK"
    )

    print(
        ".env.pos : NO TOCADO"
    )

    print(
        "database : NO TOCADA"
    )


    # ========================================================
    # ELIMINAR BACKUPS
    # ========================================================

    print("")
    print(
        "Eliminando backups..."
    )


    borrar_archivo(
        exe_backup
    )


    borrar_carpeta(
        internal_backup
    )


    # ========================================================
    # LIMPIAR TEMP
    # ========================================================

    borrar_carpeta(
        carpeta_temp
    )


    # ========================================================
    # ACTUALIZACION CORRECTA
    # ========================================================

    print("")
    print(
        "==================================="
    )
    print(
        " ACTUALIZACION CORRECTA"
    )
    print(
        "==================================="
    )
    print("")

    print(
        "Version instalada:",
        version_instalada
    )

    print(
        ".env.pos conservado."
    )

    print(
        "Base de datos conservada."
    )

    print("")
    print(
        "Abriendo programa..."
    )


    # ========================================================
    # ABRIR NUEVA VERSION
    # ========================================================

    try:

        subprocess.Popen(
            [exe_actual],
            cwd=carpeta_actual
        )

    except Exception as e:

        print("")
        print(
            "ERROR abriendo PAPELERA_POS.exe:"
        )
        print(e)

        return False


    return True


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    try:

        resultado = actualizar()

        if not resultado:

            print("")
            print(
                "La actualizacion no pudo completarse."
            )

            time.sleep(5)

    except Exception as e:

        print("")
        print(
            "==================================="
        )
        print(
            " ERROR GENERAL DEL ACTUALIZADOR"
        )
        print(
            "==================================="
        )
        print("")

        print(e)

        time.sleep(5)