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
# ACTUALIZAR
# ============================================================

def actualizar():

    if len(sys.argv) < 2:

        print("No se recibio UPDATE.zip")

        return False


    zip_path = os.path.abspath(
        sys.argv[1]
    )

    if not os.path.exists(zip_path):

        print("No existe:", zip_path)

        return False


    carpeta_actual = os.path.dirname(
        os.path.abspath(sys.executable)
    )


    print("")
    print("===================================")
    print(" ACTUALIZADOR PAPELERA POS")
    print("===================================")
    print("")
    print("Instalacion:", carpeta_actual)


    # ========================================================
    # ESPERAR CIERRE
    # ========================================================

    print("Esperando cierre del programa...")

    if not esperar_programa():

        print("El programa sigue abierto")

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

    print("Extrayendo update...")

    try:

        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as z:

            z.extractall(
                carpeta_temp
            )

    except Exception as e:

        print("Error extrayendo:", e)

        return False


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


    if not os.path.exists(nuevo_exe):

        print("Falta PAPELERA_POS.exe")

        return False


    if not os.path.isdir(nuevo_internal):

        print("Falta _internal")

        return False


    if not os.path.exists(nueva_version):

        print("Falta version.txt")

        return False


    # ========================================================
    # RUTAS INSTALACION
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
    # .ENV.POS
    #
    # ESTE ARCHIVO NO DEBE SER REEMPLAZADO POR EL UPDATE.
    # ========================================================

    env_pos_actual = os.path.join(
        internal_actual,
        ".env.pos"
    )

    env_pos_backup = os.path.join(
        internal_backup,
        ".env.pos"
    )

    env_pos_nuevo = os.path.join(
        internal_actual,
        ".env.pos"
    )


    conservar_env_pos = os.path.isfile(
        env_pos_actual
    )


    if conservar_env_pos:

        print("")
        print("Configuracion .env.pos encontrada.")
        print("Se conservara durante la actualizacion.")

    else:

        print("")
        print("No se encontro .env.pos en la instalacion actual.")


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
    print("Creando backups...")


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

            print(
                "No se pudo respaldar EXE:",
                e
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

            print(
                "No se pudo respaldar _internal:",
                e
            )


            # Restaurar EXE

            if os.path.exists(exe_backup):

                shutil.move(
                    exe_backup,
                    exe_actual
                )

            return False


    # ========================================================
    # INSTALAR NUEVA VERSION
    # ========================================================

    print("")
    print("Instalando nueva version...")


    try:

        # ----------------------------------------------------
        # MOVER NUEVO INTERNAL
        # ----------------------------------------------------

        shutil.move(
            nuevo_internal,
            internal_actual
        )


        # ----------------------------------------------------
        # RESTAURAR .ENV.POS
        # ----------------------------------------------------
        #
        # El .env.pos anterior queda dentro de:
        #
        # _internal_BACKUP\.env.pos
        #
        # Lo copiamos al nuevo _internal.
        #

        if conservar_env_pos:

            if os.path.isfile(
                env_pos_backup
            ):

                print(
                    "Restaurando .env.pos..."
                )

                if not copiar_archivo(
                    env_pos_backup,
                    env_pos_nuevo
                ):

                    raise Exception(
                        "No se pudo restaurar .env.pos"
                    )

            else:

                raise Exception(
                    "Se esperaba .env.pos en el backup pero no existe"
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

        print(
            "Error instalando:",
            e
        )


        # ====================================================
        # RESTAURAR VERSION ANTERIOR
        # ====================================================

        print(
            "Restaurando version anterior..."
        )


        borrar_archivo(
            exe_actual
        )

        borrar_carpeta(
            internal_actual
        )


        if os.path.exists(
            exe_backup
        ):

            shutil.move(
                exe_backup,
                exe_actual
            )


        if os.path.exists(
            internal_backup
        ):

            shutil.move(
                internal_backup,
                internal_actual
            )


        return False


    # ========================================================
    # VERIFICAR DLL
    # ========================================================

    python_dll = os.path.join(
        internal_actual,
        "python312.dll"
    )


    if not os.path.exists(
        python_dll
    ):

        print(
            "ERROR: falta python312.dll"
        )


        borrar_archivo(
            exe_actual
        )

        borrar_carpeta(
            internal_actual
        )


        if os.path.exists(
            exe_backup
        ):

            shutil.move(
                exe_backup,
                exe_actual
            )


        if os.path.exists(
            internal_backup
        ):

            shutil.move(
                internal_backup,
                internal_actual
            )


        return False


    # ========================================================
    # VERIFICAR .ENV.POS
    # ========================================================

    if conservar_env_pos:

        if not os.path.isfile(
            env_pos_nuevo
        ):

            print(
                "ERROR: .env.pos no fue restaurado"
            )


            # Restaurar version anterior

            borrar_archivo(
                exe_actual
            )

            borrar_carpeta(
                internal_actual
            )


            if os.path.exists(
                exe_backup
            ):

                shutil.move(
                    exe_backup,
                    exe_actual
                )


            if os.path.exists(
                internal_backup
            ):

                shutil.move(
                    internal_backup,
                    internal_actual
                )


            return False


        print(
            ".env.pos conservado correctamente."
        )


    # ========================================================
    # VERIFICAR VERSION
    # ========================================================

    version_nueva = leer_version(
        nueva_version
    )

    version_instalada = leer_version(
        version_actual
    )


    if version_nueva != version_instalada:

        print(
            "Version incorrecta"
        )

        return False


    # ========================================================
    # ELIMINAR BACKUPS
    # ========================================================

    borrar_archivo(
        exe_backup
    )

    borrar_carpeta(
        internal_backup
    )


    # ========================================================
    # ABRIR NUEVA VERSION
    # ========================================================

    print("")
    print("Actualizacion correcta")
    print("Abriendo programa...")


    subprocess.Popen(
        [exe_actual],
        cwd=carpeta_actual
    )


    return True


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    try:

        actualizar()

    except Exception as e:

        print("")
        print("ERROR GENERAL")
        print(e)

        time.sleep(5)