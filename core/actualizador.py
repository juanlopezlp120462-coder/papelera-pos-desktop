import os
import sys
import tempfile
import requests
import zipfile
import shutil
import subprocess
import datetime
import time


SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"

TIMEOUT = 10


# ============================================================
# LOG
# ============================================================

def escribir_log(texto):

    try:

        if getattr(sys, "frozen", False):

            carpeta = os.path.dirname(sys.executable)

        else:

            carpeta = os.getcwd()

        carpeta_logs = os.path.join(
            carpeta,
            "logs"
        )

        os.makedirs(
            carpeta_logs,
            exist_ok=True
        )

        archivo = os.path.join(
            carpeta_logs,
            "actualizador.txt"
        )

        with open(
            archivo,
            "a",
            encoding="utf-8"
        ) as f:

            f.write(
                str(texto) + "\n"
            )

    except Exception:
        pass


# ============================================================
# CARPETA DEL PROGRAMA
# ============================================================

def obtener_carpeta_programa():

    if getattr(sys, "frozen", False):

        return os.path.dirname(
            os.path.abspath(
                sys.executable
            )
        )

    return os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )


# ============================================================
# CERTIFICADO SSL
# ============================================================

def obtener_certificado_ssl():

    try:

        if getattr(sys, "frozen", False):

            carpeta_programa = obtener_carpeta_programa()

            certificado = os.path.join(
                carpeta_programa,
                "_internal",
                "certifi",
                "cacert.pem"
            )

            if os.path.exists(certificado):

                return certificado

        try:

            import certifi

            certificado = certifi.where()

            if os.path.exists(certificado):

                return certificado

        except Exception:
            pass

    except Exception as e:

        escribir_log(
            "ERROR obteniendo certificado SSL: "
            + repr(e)
        )

    return None


# ============================================================
# INFORMACION DE VERSION
# ============================================================

def obtener_info_version():

    try:

        url = f"{SERVIDOR}/version"

        escribir_log(
            "Consultando version en: "
            + url
        )

        certificado = obtener_certificado_ssl()

        existe_certificado = bool(
            certificado
            and os.path.exists(certificado)
        )

        if existe_certificado:

            respuesta = requests.get(
                url,
                timeout=TIMEOUT,
                verify=certificado
            )

        else:

            respuesta = requests.get(
                url,
                timeout=TIMEOUT
            )

        escribir_log(
            "HTTP version: "
            + str(respuesta.status_code)
        )

        escribir_log(
            "Respuesta version: "
            + respuesta.text
        )

        if respuesta.status_code == 200:

            datos = respuesta.json()

            escribir_log(
                "Version obtenida: "
                + str(datos)
            )

            return datos

    except Exception as e:

        escribir_log(
            "ERROR consultando version: "
            + repr(e)
        )

        print(
            "Error consultando version:",
            e
        )

    return None


# ============================================================
# ULTIMA VERSION
# ============================================================

def obtener_ultima_version():

    datos = obtener_info_version()

    if datos:

        return datos.get(
            "version"
        )

    return None


# ============================================================
# URL ACTUALIZACION
# ============================================================

def obtener_url_actualizacion():

    datos = obtener_info_version()

    if datos:

        return datos.get(
            "url"
        )

    return None


# ============================================================
# COMPROBAR ACTUALIZACION
# ============================================================

def hay_actualizacion(version_actual):

    escribir_log(
        "Version local recibida: "
        + str(version_actual)
    )

    datos = obtener_info_version()

    if datos is None:

        escribir_log(
            "RESULTADO: No se pudo obtener informacion del servidor"
        )

        return False, None

    ultima_version = datos.get(
        "version"
    )

    escribir_log(
        "Version servidor: "
        + str(ultima_version)
    )

    if not ultima_version:

        return False, None

    version_actual = str(
        version_actual
    ).replace(
        "\ufeff",
        ""
    ).strip()

    ultima_version = str(
        ultima_version
    ).replace(
        "\ufeff",
        ""
    ).strip()

    if ultima_version != version_actual:

        escribir_log(
            "RESULTADO: HAY ACTUALIZACION -> "
            + ultima_version
        )

        return True, ultima_version

    escribir_log(
        "RESULTADO: NO HAY ACTUALIZACION"
    )

    return False, ultima_version


# ============================================================
# DESCARGAR ACTUALIZACION
# ============================================================

def descargar_actualizacion(progreso=None):

    url = obtener_url_actualizacion()

    if not url:

        escribir_log(
            "No hay URL de actualizacion"
        )

        return False

    escribir_log(
        "Descargando actualizacion desde: "
        + url
    )

    try:

        certificado = obtener_certificado_ssl()

        existe_certificado = bool(
            certificado
            and os.path.exists(certificado)
        )

        if existe_certificado:

            respuesta = requests.get(
                url,
                timeout=60,
                stream=True,
                verify=certificado
            )

        else:

            respuesta = requests.get(
                url,
                timeout=60,
                stream=True
            )

        escribir_log(
            "HTTP descarga: "
            + str(respuesta.status_code)
        )

        if respuesta.status_code != 200:

            escribir_log(
                "ERROR descarga HTTP: "
                + str(respuesta.status_code)
            )

            return False

        total = int(
            respuesta.headers.get(
                "content-length",
                0
            )
        )

        archivo_temp = os.path.join(
            tempfile.gettempdir(),
            "PAPELERA_POS_update.zip"
        )

        if os.path.exists(archivo_temp):

            try:

                os.remove(
                    archivo_temp
                )

            except Exception:
                pass

        descargado = 0

        with open(
            archivo_temp,
            "wb"
        ) as f:

            for bloque in respuesta.iter_content(
                chunk_size=8192
            ):

                if bloque:

                    f.write(
                        bloque
                    )

                    descargado += len(
                        bloque
                    )

                    if total and progreso:

                        porcentaje = int(
                            descargado * 100 / total
                        )

                        progreso(
                            porcentaje
                        )

        escribir_log(
            "Actualizacion descargada: "
            + archivo_temp
        )

        return archivo_temp

    except Exception as e:

        escribir_log(
            "ERROR descarga actualizacion: "
            + repr(e)
        )

        return False


# ============================================================
# BACKUP
#
# IMPORTANTE:
#
# ESTE BACKUP NO TOCA DATABASE.
#
# DATABASE NO SE COPIA.
# DATABASE NO SE BORRA.
# DATABASE NO SE MUEVE.
# DATABASE NO SE REEMPLAZA.
# ============================================================

def crear_backup():

    try:

        carpeta_actual = obtener_carpeta_programa()

        carpeta_backups = os.path.join(
            carpeta_actual,
            "backups"
        )

        os.makedirs(
            carpeta_backups,
            exist_ok=True
        )

        fecha = datetime.datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        destino = os.path.join(
            carpeta_backups,
            f"backup_{fecha}"
        )

        os.makedirs(
            destino,
            exist_ok=True
        )

        # ----------------------------------------------------
        # SOLO BACKUP DE VERSION.TXT
        #
        # DATABASE NO SE COPIA.
        # ----------------------------------------------------

        version_origen = os.path.join(
            carpeta_actual,
            "version.txt"
        )

        version_destino = os.path.join(
            destino,
            "version.txt"
        )

        if os.path.exists(version_origen):

            shutil.copy2(
                version_origen,
                version_destino
            )

        escribir_log(
            "Backup creado correctamente: "
            + destino
        )

        limpiar_backups()

        return True

    except Exception as e:

        escribir_log(
            "ERROR creando backup: "
            + repr(e)
        )

        return False


# ============================================================
# LIMPIAR BACKUPS
# ============================================================

def limpiar_backups(max_backups=3):

    try:

        carpeta_actual = obtener_carpeta_programa()

        carpeta_backups = os.path.join(
            carpeta_actual,
            "backups"
        )

        if not os.path.exists(
            carpeta_backups
        ):

            return

        backups = []

        for nombre in os.listdir(
            carpeta_backups
        ):

            ruta = os.path.join(
                carpeta_backups,
                nombre
            )

            if os.path.isdir(ruta):

                backups.append(
                    ruta
                )

        backups.sort(
            key=os.path.getmtime,
            reverse=True
        )

        for backup in backups[max_backups:]:

            shutil.rmtree(
                backup,
                ignore_errors=True
            )

            escribir_log(
                "Backup eliminado: "
                + backup
            )

    except Exception as e:

        escribir_log(
            "ERROR limpiando backups: "
            + repr(e)
        )


# ============================================================
# INSTALAR ACTUALIZACION
#
# ============================================================
#
# MUY IMPORTANTE:
#
# ESTA FUNCION NUNCA MODIFICA DATABASE.
#
# SOLO REEMPLAZA:
#
#     PAPELERA_POS.exe
#     _internal
#     version.txt
#
# DATABASE:
#
#     NO SE BORRA
#     NO SE COPIA
#     NO SE MUEVE
#     NO SE REEMPLAZA
#
# ============================================================

def instalar_actualizacion(
    zip_path,
    nueva_version=None
):

    try:

        if not zip_path or not os.path.exists(zip_path):

            escribir_log(
                "ZIP de actualizacion no existe"
            )

            return False

        # ----------------------------------------------------
        # BACKUP
        # ----------------------------------------------------

        if not crear_backup():

            escribir_log(
                "No se pudo crear backup"
            )

            return False

        carpeta_actual = obtener_carpeta_programa()

        escribir_log(
            "CARPETA INSTALACION: "
            + carpeta_actual
        )

        # ----------------------------------------------------
        # PROTECCION DATABASE
        # ----------------------------------------------------

        database_actual = os.path.join(
            carpeta_actual,
            "database"
        )

        escribir_log(
            "DATABASE PROTEGIDA: "
            + database_actual
        )

        # ----------------------------------------------------
        # CARPETA TEMPORAL
        # ----------------------------------------------------

        carpeta_temp = os.path.join(
            tempfile.gettempdir(),
            "PAPELERA_POS_UPDATE"
        )

        if os.path.exists(
            carpeta_temp
        ):

            shutil.rmtree(
                carpeta_temp,
                ignore_errors=True
            )

            time.sleep(
                0.5
            )

        os.makedirs(
            carpeta_temp,
            exist_ok=True
        )

        # ----------------------------------------------------
        # EXTRAER ZIP
        # ----------------------------------------------------

        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as zip_ref:

            zip_ref.extractall(
                carpeta_temp
            )

        # ----------------------------------------------------
        # NORMALIZAR ZIP
        # ----------------------------------------------------

        carpeta_extra = os.path.join(
            carpeta_temp,
            "PAPELERA_POS"
        )

        if os.path.isdir(
            carpeta_extra
        ):

            for elemento in os.listdir(
                carpeta_extra
            ):

                # --------------------------------------------
                # NUNCA PERMITIR DATABASE
                # --------------------------------------------

                if elemento.lower() in (
                    "database",
                    "backups",
                    "logs"
                ):

                    escribir_log(
                        "IGNORANDO elemento protegido del ZIP: "
                        + elemento
                    )

                    continue

                origen = os.path.join(
                    carpeta_extra,
                    elemento
                )

                destino = os.path.join(
                    carpeta_temp,
                    elemento
                )

                if os.path.exists(
                    destino
                ):

                    if os.path.isdir(
                        destino
                    ):

                        shutil.rmtree(
                            destino,
                            ignore_errors=True
                        )

                    else:

                        os.remove(
                            destino
                        )

                shutil.move(
                    origen,
                    destino
                )

            shutil.rmtree(
                carpeta_extra,
                ignore_errors=True
            )

        # ----------------------------------------------------
        # VERSION
        # ----------------------------------------------------

        if nueva_version:

            nueva_version = str(
                nueva_version
            ).replace(
                "\ufeff",
                ""
            ).strip()

        else:

            escribir_log(
                "ERROR: No se recibio nueva version"
            )

            return False

        # ----------------------------------------------------
        # COMPROBAR EXE
        # ----------------------------------------------------

        nuevo_exe = os.path.join(
            carpeta_temp,
            "PAPELERA_POS.exe"
        )

        nuevo_internal = os.path.join(
            carpeta_temp,
            "_internal"
        )

        if not os.path.exists(
            nuevo_exe
        ):

            escribir_log(
                "ERROR: ZIP no contiene PAPELERA_POS.exe"
            )

            return False

        if not os.path.isdir(
            nuevo_internal
        ):

            escribir_log(
                "ERROR: ZIP no contiene _internal"
            )

            return False

        # ----------------------------------------------------
        # VERSION.TXT TEMPORAL
        # ----------------------------------------------------

        version_temp = os.path.join(
            carpeta_temp,
            "version.txt"
        )

        with open(
            version_temp,
            "w",
            encoding="utf-8",
            newline=""
        ) as f:

            f.write(
                nueva_version
            )

        # ----------------------------------------------------
        # RUTAS ACTUALES
        # ----------------------------------------------------

        exe_actual = os.path.join(
            carpeta_actual,
            "PAPELERA_POS.exe"
        )

        internal_actual = os.path.join(
            carpeta_actual,
            "_internal"
        )

        version_actual = os.path.join(
            carpeta_actual,
            "version.txt"
        )

        # ----------------------------------------------------
        # PID
        # ----------------------------------------------------

        pid_actual = os.getpid()

        escribir_log(
            "PID actual: "
            + str(pid_actual)
        )

        # ----------------------------------------------------
        # BAT EXTERNO
        # ----------------------------------------------------

        bat = os.path.join(
            tempfile.gettempdir(),
            "actualizar_papelera_pos.bat"
        )

        if os.path.exists(bat):

            try:

                os.remove(bat)

            except Exception:
                pass

        contenido_bat = f"""@echo off
setlocal

echo ==========================================
echo ACTUALIZANDO PAPELERA POS
echo ==========================================

echo PID del programa anterior: {pid_actual}

echo.
echo Esperando cierre del programa anterior...

:ESPERAR_PID

tasklist /FI "PID eq {pid_actual}" 2>NUL | find "{pid_actual}" >NUL

if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto ESPERAR_PID
)

echo.
echo Programa anterior cerrado.

timeout /t 1 /nobreak >nul

echo.
echo ==========================================
echo PROTECCION DATABASE
echo ==========================================

if exist "{database_actual}" (
    echo DATABASE ENCONTRADA.
    echo NO SE BORRARA.
    echo NO SE COPIARA.
    echo NO SE REEMPLAZARA.
) else (
    echo DATABASE NO EXISTE.
)

echo.
echo ==========================================
echo ELIMINANDO _internal ANTERIOR
echo ==========================================

if exist "{internal_actual}" (
    rmdir /s /q "{internal_actual}"
)

echo.
echo ==========================================
echo COPIANDO NUEVO _internal
echo ==========================================

xcopy "{nuevo_internal}" "{internal_actual}" /E /I /Y /H /C

echo.
echo ==========================================
echo COPIANDO NUEVO EXE
echo ==========================================

copy /Y "{nuevo_exe}" "{exe_actual}"

echo.
echo ==========================================
echo ACTUALIZANDO version.txt
echo ==========================================

powershell -NoProfile -ExecutionPolicy Bypass -Command "[System.IO.File]::WriteAllText('{version_actual}', '{nueva_version}', (New-Object System.Text.UTF8Encoding($false)))"

echo.
echo ==========================================
echo VERIFICACION FINAL
echo ==========================================

if not exist "{exe_actual}" (
    echo ERROR: No se encontro PAPELERA_POS.exe
    pause
    exit /b 1
)

if not exist "{internal_actual}" (
    echo ERROR: No se encontro _internal
    pause
    exit /b 1
)

if exist "{database_actual}" (
    echo.
    echo DATABASE OK.
    echo DATABASE NO FUE TOCADA.
) else (
    echo.
    echo AVISO: database no existe.
)

echo.
echo ==========================================
echo ACTUALIZACION COMPLETADA
echo ==========================================

echo.
echo Limpiando temporal...

rmdir /s /q "{carpeta_temp}" 2>NUL

echo.
echo Reiniciando PAPELERA POS...

start "" "{exe_actual}"

timeout /t 3 /nobreak >nul

exit
"""

        with open(
            bat,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                contenido_bat
            )

        escribir_log(
            "Actualizador externo creado: "
            + bat
        )

        # ----------------------------------------------------
        # EJECUTAR BAT
        # ----------------------------------------------------

        subprocess.Popen(
            [
                "cmd.exe",
                "/c",
                bat
            ],
            cwd=tempfile.gettempdir(),
            creationflags=(
                subprocess.CREATE_NEW_PROCESS_GROUP
                if hasattr(
                    subprocess,
                    "CREATE_NEW_PROCESS_GROUP"
                )
                else 0
            )
        )

        return True

    except Exception as e:

        escribir_log(
            "ERROR INSTALANDO ACTUALIZACION: "
            + repr(e)
        )

        print(
            "Error instalando actualización:",
            e
        )

        return False


# ============================================================
# REINICIAR
# ============================================================

def reiniciar_programa():

    try:

        if getattr(
            sys,
            "frozen",
            False
        ):

            ejecutable = sys.executable

            subprocess.Popen(
                [
                    ejecutable
                ],
                cwd=os.path.dirname(
                    ejecutable
                )
            )

        else:

            archivo_principal = os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(
                            __file__
                        )
                    )
                ),
                "main.py"
            )

            subprocess.Popen(
                [
                    sys.executable,
                    archivo_principal
                ],
                cwd=os.path.dirname(
                    archivo_principal
                )
            )

        sys.exit()

    except Exception as e:

        escribir_log(
            "ERROR reiniciando: "
            + repr(e)
        )

        print(
            "Error reiniciando:",
            e
        )
