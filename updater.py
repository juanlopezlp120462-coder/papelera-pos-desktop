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

MAX_INTENTOS = 20

ESPERA_ENTRE_INTENTOS = 1


# ============================================================
# ESPERAR A QUE PAPELERA POS TERMINE COMPLETAMENTE
# ============================================================

def esperar_programa_cerrado():

    print("")
    print("Esperando que PAPELERA POS termine...")

    for intento in range(MAX_INTENTOS):

        try:

            resultado = subprocess.run(
                [
                    "tasklist",
                    "/FI",
                    f"IMAGENAME eq {NOMBRE_EXE}"
                ],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            salida = resultado.stdout.lower()

            if NOMBRE_EXE.lower() not in salida:

                print("PAPELERA POS ya esta cerrado.")

                return True

            print(
                f"PAPELERA POS sigue abierto. "
                f"Intento {intento + 1}/{MAX_INTENTOS}"
            )

        except Exception as e:

            print(
                "No se pudo comprobar el proceso:",
                e
            )

        time.sleep(
            ESPERA_ENTRE_INTENTOS
        )


    print("")
    print(
        "ERROR: PAPELERA POS sigue ejecutandose."
    )

    return False


# ============================================================
# BORRAR ARCHIVO CON REINTENTOS
# ============================================================

def borrar_archivo_seguro(ruta):

    if not os.path.exists(ruta):

        return True


    for intento in range(MAX_INTENTOS):

        try:

            os.remove(ruta)

            return True

        except Exception as e:

            print(
                f"No se pudo borrar archivo "
                f"(intento {intento + 1}/{MAX_INTENTOS}):",
                ruta
            )

            time.sleep(
                ESPERA_ENTRE_INTENTOS
            )


    return False


# ============================================================
# BORRAR CARPETA CON REINTENTOS
# ============================================================

def borrar_carpeta_segura(ruta):

    if not os.path.exists(ruta):

        return True


    ultimo_error = None


    for intento in range(MAX_INTENTOS):

        try:

            shutil.rmtree(
                ruta
            )

            return True

        except Exception as e:

            ultimo_error = e

            print(
                f"No se pudo borrar carpeta "
                f"(intento {intento + 1}/{MAX_INTENTOS}):",
                ruta
            )

            time.sleep(
                ESPERA_ENTRE_INTENTOS
            )


    print(
        "ERROR borrando carpeta:",
        ruta,
        ultimo_error
    )

    return False


# ============================================================
# COPIAR ARCHIVO CON REINTENTOS
# ============================================================

def copiar_archivo_seguro(origen, destino):

    carpeta_destino = os.path.dirname(
        destino
    )

    if carpeta_destino:

        os.makedirs(
            carpeta_destino,
            exist_ok=True
        )


    ultimo_error = None


    for intento in range(MAX_INTENTOS):

        try:

            shutil.copy2(
                origen,
                destino
            )

            return True

        except Exception as e:

            ultimo_error = e

            print(
                f"No se pudo copiar archivo "
                f"(intento {intento + 1}/{MAX_INTENTOS}):",
                destino
            )

            time.sleep(
                ESPERA_ENTRE_INTENTOS
            )


    print(
        "ERROR copiando archivo:",
        origen,
        "->",
        destino,
        ultimo_error
    )

    return False


# ============================================================
# COPIAR CARPETA COMPLETA
# ============================================================

def copiar_carpeta_segura(origen, destino):

    print("")
    print(
        "Copiando carpeta:",
        origen
    )

    for root, dirs, files in os.walk(origen):

        relativo = os.path.relpath(
            root,
            origen
        )

        if relativo == ".":

            destino_root = destino

        else:

            destino_root = os.path.join(
                destino,
                relativo
            )


        os.makedirs(
            destino_root,
            exist_ok=True
        )


        for archivo in files:

            archivo_origen = os.path.join(
                root,
                archivo
            )

            archivo_destino = os.path.join(
                destino_root,
                archivo
            )


            if not copiar_archivo_seguro(
                archivo_origen,
                archivo_destino
            ):

                return False


    return True


# ============================================================
# LEER VERSION
# ============================================================

def leer_version(ruta):

    if not os.path.exists(ruta):

        return None


    try:

        with open(
            ruta,
            "r",
            encoding="utf-8"
        ) as archivo:

            return archivo.read().strip()

    except Exception as e:

        print(
            "ERROR leyendo version:",
            e
        )

        return None


# ============================================================
# ACTUALIZAR
# ============================================================

def actualizar():

    if len(sys.argv) < 2:

        print(
            "ERROR: No se recibio UPDATE.zip."
        )

        return False


    zip_path = os.path.abspath(
        sys.argv[1]
    )


    if not os.path.exists(zip_path):

        print(
            "ERROR: No existe UPDATE.zip:",
            zip_path
        )

        return False


    # ========================================================
    # CARPETA DONDE ESTA INSTALADO PAPELERA POS
    # ========================================================

    carpeta_actual = os.path.dirname(
        os.path.abspath(
            sys.executable
        )
    )


    print("")
    print("============================================")
    print("       ACTUALIZADOR PAPELERA POS")
    print("============================================")
    print("")

    print(
        "Carpeta de instalacion:",
        carpeta_actual
    )

    print(
        "ZIP:",
        zip_path
    )

    print("")


    # ========================================================
    # ESPERAR A QUE EL PROGRAMA PRINCIPAL ESTE CERRADO
    # ========================================================

    if not esperar_programa_cerrado():

        print("")
        print(
            "La actualizacion fue cancelada."
        )

        return False


    # ========================================================
    # CARPETA TEMPORAL
    # ========================================================

    carpeta_temp = os.path.join(
        tempfile.gettempdir(),
        CARPETA_TEMP
    )


    if os.path.exists(carpeta_temp):

        print(
            "Eliminando temporal anterior..."
        )

        if not borrar_carpeta_segura(
            carpeta_temp
        ):

            return False


    os.makedirs(
        carpeta_temp,
        exist_ok=True
    )


    # ========================================================
    # EXTRAER ZIP
    # ========================================================

    print("")
    print(
        "Extrayendo UPDATE.zip..."
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
            "ERROR extrayendo UPDATE.zip:",
            e
        )

        return False


    # ========================================================
    # NORMALIZAR CARPETA PAPELERA_POS
    # ========================================================

    carpeta_extra = os.path.join(
        carpeta_temp,
        "PAPELERA_POS"
    )


    if os.path.exists(carpeta_extra):

        print(
            "Normalizando estructura del ZIP..."
        )


        for item in os.listdir(
            carpeta_extra
        ):

            origen = os.path.join(
                carpeta_extra,
                item
            )

            destino = os.path.join(
                carpeta_temp,
                item
            )


            if os.path.exists(destino):

                if os.path.isdir(destino):

                    if not borrar_carpeta_segura(
                        destino
                    ):

                        return False

                else:

                    if not borrar_archivo_seguro(
                        destino
                    ):

                        return False


            shutil.move(
                origen,
                destino
            )


        if not borrar_carpeta_segura(
            carpeta_extra
        ):

            return False


    # ========================================================
    # COMPROBAR ARCHIVOS DEL UPDATE
    # ========================================================

    nuevo_exe = os.path.join(
        carpeta_temp,
        NOMBRE_EXE
    )

    nuevo_internal = os.path.join(
        carpeta_temp,
        "_internal"
    )

    nueva_version_file = os.path.join(
        carpeta_temp,
        "version.txt"
    )


    if not os.path.exists(nuevo_exe):

        print("")
        print(
            "ERROR: UPDATE.zip no contiene",
            NOMBRE_EXE
        )

        return False


    if not os.path.isdir(nuevo_internal):

        print("")
        print(
            "ERROR: UPDATE.zip no contiene _internal."
        )

        return False


    if not os.path.exists(nueva_version_file):

        print("")
        print(
            "ERROR: UPDATE.zip no contiene version.txt."
        )

        return False


    nueva_version = leer_version(
        nueva_version_file
    )


    if not nueva_version:

        print("")
        print(
            "ERROR: version.txt esta vacio."
        )

        return False


    print("")
    print(
        "Nueva version:",
        nueva_version
    )


    # ========================================================
    # RUTAS DE INSTALACION
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
    # BACKUP TEMPORAL DE _INTERNAL
    #
    # NO BORRAMOS DIRECTAMENTE EL _internal VIEJO.
    #
    # Primero lo movemos.
    # Si algo falla podemos restaurarlo.
    # ========================================================

    internal_backup = os.path.join(
        carpeta_actual,
        "_internal_UPDATE_BACKUP"
    )


    if os.path.exists(internal_backup):

        print(
            "Eliminando backup temporal anterior..."
        )

        if not borrar_carpeta_segura(
            internal_backup
        ):

            return False


    if os.path.exists(internal_actual):

        print("")
        print(
            "Preparando reemplazo de _internal..."
        )


        movido = False


        for intento in range(
            MAX_INTENTOS
        ):

            try:

                os.rename(
                    internal_actual,
                    internal_backup
                )

                movido = True

                print(
                    "_internal anterior guardado temporalmente."
                )

                break

            except Exception as e:

                print(
                    f"_internal ocupado "
                    f"(intento {intento + 1}/{MAX_INTENTOS})"
                )

                time.sleep(
                    ESPERA_ENTRE_INTENTOS
                )


        if not movido:

            print("")
            print(
                "ERROR: No se pudo reemplazar _internal."
            )

            print(
                "La actualizacion NO se realizo."
            )

            return False


    # ========================================================
    # COPIAR NUEVO _INTERNAL
    # ========================================================

    print("")
    print(
        "Instalando nuevo _internal..."
    )


    try:

        if not copiar_carpeta_segura(
            nuevo_internal,
            internal_actual
        ):

            raise Exception(
                "No se pudo copiar completamente _internal."
            )


    except Exception as e:

        print("")
        print(
            "ERROR instalando _internal:",
            e
        )


        # ====================================================
        # RESTAURAR VERSION ANTERIOR
        # ====================================================

        if os.path.exists(
            internal_actual
        ):

            borrar_carpeta_segura(
                internal_actual
            )


        if os.path.exists(
            internal_backup
        ):

            try:

                os.rename(
                    internal_backup,
                    internal_actual
                )

                print(
                    "Se restauro _internal anterior."
                )

            except Exception as restore_error:

                print(
                    "ERROR restaurando _internal:",
                    restore_error
                )


        return False


    # ========================================================
    # COPIAR EXE
    # ========================================================

    print("")
    print(
        "Instalando PAPELERA_POS.exe..."
    )


    if not copiar_archivo_seguro(
        nuevo_exe,
        exe_actual
    ):

        print("")
        print(
            "ERROR: No se pudo instalar PAPELERA_POS.exe."
        )

        # Restaurar internal anterior si todavía existe

        if os.path.exists(
            internal_actual
        ):

            borrar_carpeta_segura(
                internal_actual
            )


        if os.path.exists(
            internal_backup
        ):

            try:

                os.rename(
                    internal_backup,
                    internal_actual
                )

                print(
                    "Se restauro _internal anterior."
                )

            except Exception as e:

                print(
                    "ERROR restaurando _internal:",
                    e
                )


        return False


    # ========================================================
    # COPIAR VERSION
    # ========================================================

    print("")
    print(
        "Actualizando version.txt..."
    )


    if not copiar_archivo_seguro(
        nueva_version_file,
        version_actual
    ):

        print("")
        print(
            "ADVERTENCIA: No se pudo actualizar version.txt."
        )


    # ========================================================
    # VERIFICAR INSTALACION
    # ========================================================

    print("")
    print(
        "Verificando archivos instalados..."
    )


    if not os.path.exists(
        exe_actual
    ):

        print(
            "ERROR: PAPELERA_POS.exe no existe."
        )

        return False


    if not os.path.isdir(
        internal_actual
    ):

        print(
            "ERROR: _internal no existe."
        )

        return False


    version_instalada = leer_version(
        version_actual
    )


    if version_instalada != nueva_version:

        print(
            "ERROR: La version instalada no coincide."
        )

        print(
            "Esperada:",
            nueva_version
        )

        print(
            "Encontrada:",
            version_instalada
        )

        return False


    print("")
    print(
        "============================================"
    )
    print(
        "       ACTUALIZACION COMPLETADA"
    )
    print(
        "============================================"
    )
    print("")

    print(
        "Version instalada:",
        nueva_version
    )

    print("")


    # ========================================================
    # ELIMINAR BACKUP TEMPORAL
    # ========================================================

    if os.path.exists(
        internal_backup
    ):

        if not borrar_carpeta_segura(
            internal_backup
        ):

            print(
                "Aviso: no se pudo eliminar "
                "_internal_UPDATE_BACKUP."
            )


    # ========================================================
    # ELIMINAR TEMPORAL
    # ========================================================

    if os.path.exists(
        carpeta_temp
    ):

        borrar_carpeta_segura(
            carpeta_temp
        )


    # ========================================================
    # ABRIR NUEVA VERSION
    # ========================================================

    print(
        "Abriendo PAPELERA POS..."
    )


    try:

        subprocess.Popen(
            [
                exe_actual
            ],
            cwd=carpeta_actual,
            close_fds=True
        )

    except Exception as e:

        print("")
        print(
            "ERROR ABRIENDO PAPELERA POS:"
        )

        print(
            e
        )

        return False


    return True


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":

    try:

        resultado = actualizar()

        if not resultado:

            print("")
            print(
                "LA ACTUALIZACION NO SE COMPLETO."
            )

            time.sleep(5)

    except Exception as e:

        print("")
        print(
            "ERROR GENERAL DEL UPDATER:"
        )

        print(
            e
        )

        time.sleep(5)