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

            carpeta = os.path.dirname(
                sys.executable
            )

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
            os.path.abspath(sys.executable)
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

        # ----------------------------------------------------
        # PyInstaller
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Python normal
        # ----------------------------------------------------

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

        escribir_log(
            "Certificado SSL: "
            + str(certificado)
        )

        existe_certificado = bool(
            certificado
            and os.path.exists(certificado)
        )

        escribir_log(
            "Certificado existe: "
            + str(existe_certificado)
        )

        if existe_certificado:

            respuesta = requests.get(
                url,
                timeout=TIMEOUT,
                verify=certificado
            )

        else:

            # Requests utiliza su certificado normal
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

        escribir_log(
            "ERROR HTTP version: "
            + str(respuesta.status_code)
        )

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

        escribir_log(
            "RESULTADO: El servidor no devolvio version"
        )

        return False, None

    # --------------------------------------------------------
    # LIMPIAR VERSIONES
    # --------------------------------------------------------

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

    escribir_log(
        "Version local limpia: "
        + version_actual
    )

    escribir_log(
        "Version servidor limpia: "
        + ultima_version
    )

    # --------------------------------------------------------
    # COMPARAR
    # --------------------------------------------------------

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

        print(
            "No hay URL de actualización"
        )

        return False

    escribir_log(
        "Descargando actualizacion desde: "
        + url
    )

    try:

        certificado = obtener_certificado_ssl()

        escribir_log(
            "Certificado SSL descarga: "
            + str(certificado)
        )

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

            print(
                "Error descargando actualización:",
                respuesta.status_code
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

        print(
            "Actualización descargada:",
            archivo_temp
        )

        return archivo_temp

    except Exception as e:

        escribir_log(
            "ERROR descarga actualizacion: "
            + repr(e)
        )

        print(
            "Error descarga actualización:",
            e
        )

        return False


# ============================================================
# BACKUP
# ============================================================

def crear_backup():

    try:

        carpeta_actual = obtener_carpeta_programa()

        print(
            "CARPETA BACKUP:",
            carpeta_actual
        )

        escribir_log(
            "CARPETA BACKUP: "
            + carpeta_actual
        )

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
            destino
        )

        archivos_backup = [
            "database",
            "version.txt"
        ]

        for archivo in archivos_backup:

            origen = os.path.join(
                carpeta_actual,
                archivo
            )

            copia = os.path.join(
                destino,
                archivo
            )

            if os.path.exists(origen):

                print(
                    "Copiando backup:",
                    origen
                )

                escribir_log(
                    "Copiando backup: "
                    + origen
                )

                if os.path.isdir(origen):

                    shutil.copytree(
                        origen,
                        copia
                    )

                else:

                    shutil.copy2(
                        origen,
                        copia
                    )

            else:

                print(
                    "No existe para backup:",
                    origen
                )

                escribir_log(
                    "No existe para backup: "
                    + origen
                )

        print(
            "Backup creado correctamente:",
            destino
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

        print(
            "Error creando backup:",
            e
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

            print(
                "Backup eliminado:",
                backup
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

        escribir_log(
            "Extrayendo ZIP"
        )

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

            escribir_log(
                "ZIP contiene carpeta PAPELERA_POS"
            )

            for elemento in os.listdir(
                carpeta_extra
            ):

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
                "ERROR: No se recibió nueva versión para instalar"
            )
            return False

        escribir_log(
            "Nueva version para instalar: "
            + nueva_version
        )

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
                "ERROR: El ZIP no contiene PAPELERA_POS.exe"
            )

            return False

        if not os.path.isdir(
            nuevo_internal
        ):

            escribir_log(
                "ERROR: El ZIP no contiene _internal"
            )

            return False

        # ----------------------------------------------------
        # VERSION.TXT
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

        escribir_log(
            "version.txt preparado: "
            + nueva_version
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

                os.remove(
                    bat
                )

            except Exception:
                pass

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
        # PID DEL PROCESO ACTUAL
        #
        # El BAT esperará específicamente a este PID.
        # Esto evita problemas si existiera otra instancia.
        # ----------------------------------------------------

        pid_actual = os.getpid()

        escribir_log(
            "PID actual: "
            + str(pid_actual)
        )

        # ----------------------------------------------------
        # BAT EXTERNO
        # ----------------------------------------------------

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
echo El programa anterior ya esta cerrado.

echo.
echo Esperando un momento...
timeout /t 1 /nobreak >nul

echo.
echo Eliminando _internal anterior...

if exist "{internal_actual}" (
    rmdir /s /q "{internal_actual}"
)

echo.
echo Copiando nueva version...

xcopy "{carpeta_temp}\\*" "{carpeta_actual}\\" /E /I /Y /H /C

echo.
echo Verificando PAPELERA_POS.exe...

if not exist "{exe_actual}" (
    echo ERROR: No se encontro el nuevo EXE.
    pause
    exit /b 1
)

echo.
echo Verificando _internal...

if not exist "{internal_actual}" (
    echo ERROR: No se encontro _internal.
    pause
    exit /b 1
)

echo.
echo Actualizando version.txt...

powershell -NoProfile -ExecutionPolicy Bypass -Command "[System.IO.File]::WriteAllText('{version_actual}', '{nueva_version}', (New-Object System.Text.UTF8Encoding($false)))"

echo.
echo ==========================================
echo ACTUALIZACION INSTALADA CORRECTAMENTE
echo ==========================================

echo.
echo Limpiando archivos temporales...

rmdir /s /q "{carpeta_temp}" 2>NUL

echo.
echo Reiniciando PAPELERA POS...

start "" "{exe_actual}"

echo.
echo Actualizador finalizado.

timeout /t 2 /nobreak >nul

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

        escribir_log(
            "Ejecutando actualizador externo"
        )

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

        # ----------------------------------------------------
        # IMPORTANTE
        #
        # NO reiniciar desde Python.
        #
        # El BAT:
        #
        # 1. Espera que muera este PID.
        # 2. Elimina _internal.
        # 3. Copia la nueva versión.
        # 4. Actualiza version.txt.
        # 5. Abre el nuevo EXE.
        #
        # ----------------------------------------------------

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