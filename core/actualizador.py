import os
import tempfile
import requests
import zipfile
import shutil
import sys
import subprocess
import datetime
import time


SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"

TIMEOUT = 10


# ==========================================================
# LOG
# ==========================================================

def escribir_log(texto):

    try:

        if getattr(sys, "frozen", False):

            carpeta = os.path.dirname(
                sys.executable
            )

            print(
                "EXE ACTUAL:",
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


# ==========================================================
# CERTIFICADO SSL
# ==========================================================

def obtener_certificado_ssl():

    if getattr(sys, "frozen", False):

        carpeta_exe = os.path.dirname(
            sys.executable
        )

        certificado = os.path.join(
            carpeta_exe,
            "_internal",
            "certifi",
            "cacert.pem"
        )

    else:

        import certifi

        certificado = certifi.where()

    return certificado


# ==========================================================
# INFORMACION DE VERSION
# ==========================================================

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
            + certificado
        )

        escribir_log(
            "Certificado existe: "
            + str(os.path.exists(certificado))
        )

        respuesta = requests.get(
            url,
            timeout=TIMEOUT,
            verify=certificado
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


# ==========================================================
# ULTIMA VERSION
# ==========================================================

def obtener_ultima_version():

    datos = obtener_info_version()

    if datos:

        return datos.get(
            "version"
        )

    return None


# ==========================================================
# URL DE ACTUALIZACION
# ==========================================================

def obtener_url_actualizacion():

    datos = obtener_info_version()

    if datos:

        return datos.get(
            "url"
        )

    return None


# ==========================================================
# COMPROBAR ACTUALIZACION
# ==========================================================

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

    if ultima_version != version_actual:

        escribir_log(
            "RESULTADO: HAY ACTUALIZACION -> "
            + str(ultima_version)
        )

        return True, ultima_version

    escribir_log(
        "RESULTADO: NO HAY ACTUALIZACION"
    )

    return False, ultima_version


# ==========================================================
# DESCARGAR ACTUALIZACION
# ==========================================================

def descargar_actualizacion(progreso=None):

    url = obtener_url_actualizacion()

    if not url:

        print(
            "No hay URL de actualización"
        )

        escribir_log(
            "No hay URL de actualización"
        )

        return False

    try:

        escribir_log(
            "Descargando actualización desde: "
            + url
        )

        certificado = obtener_certificado_ssl()

        escribir_log(
            "Certificado SSL descarga: "
            + certificado
        )

        respuesta = requests.get(
            url,
            timeout=60,
            stream=True,
            verify=certificado
        )

        escribir_log(
            "HTTP descarga: "
            + str(respuesta.status_code)
        )

        if respuesta.status_code != 200:

            print(
                "Error descargando actualización:",
                respuesta.status_code
            )

            escribir_log(
                "Error descargando actualización: "
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
            "Actualización descargada: "
            + archivo_temp
        )

        print(
            "Actualización descargada:",
            archivo_temp
        )

        return archivo_temp

    except Exception as e:

        print(
            "Error descarga actualización:",
            e
        )

        escribir_log(
            "ERROR descarga actualización: "
            + repr(e)
        )

        return False


# ==========================================================
# CREAR BACKUP
# ==========================================================

def crear_backup():

    try:

        if getattr(sys, "frozen", False):

            carpeta_actual = os.path.dirname(
                sys.executable
            )

        else:

            carpeta_actual = os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )

        print(
            "CARPETA BACKUP:",
            carpeta_actual
        )

        escribir_log(
            "CARPETA BACKUP: "
            + carpeta_actual
        )

        print(
            "CONTENIDO:",
            os.listdir(carpeta_actual)
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

        print(
            "Error creando backup:",
            e
        )

        escribir_log(
            "ERROR creando backup: "
            + repr(e)
        )

        return False


# ==========================================================
# LIMPIAR BACKUPS
# ==========================================================

def limpiar_backups(max_backups=3):

    try:

        if getattr(sys, "frozen", False):

            carpeta_actual = os.path.dirname(
                sys.executable
            )

        else:

            carpeta_actual = os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )

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
                backup
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

        print(
            "Error limpiando backups:",
            e
        )

        escribir_log(
            "ERROR limpiando backups: "
            + repr(e)
        )


# ==========================================================
# INSTALAR ACTUALIZACION
# ==========================================================

def instalar_actualizacion(zip_path):

    try:

        if not crear_backup():

            escribir_log(
                "No se pudo crear backup"
            )

            return False

        if getattr(sys, "frozen", False):

            carpeta_actual = os.path.dirname(
                sys.executable
            )

        else:

            carpeta_actual = os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )

        escribir_log(
            "CARPETA INSTALACION: "
            + carpeta_actual
        )

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

        # ==================================================
        # NORMALIZAR CARPETA DEL ZIP
        # ==================================================

        carpeta_extra = os.path.join(
            carpeta_temp,
            "PAPELERA_POS"
        )

        if os.path.exists(
            carpeta_extra
        ):

            escribir_log(
                "El ZIP contiene carpeta PAPELERA_POS"
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
                            destino
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
                carpeta_extra
            )

        # ==================================================
        # OBTENER NUEVA VERSION
        # ==================================================

        datos_version = obtener_info_version()

        nueva_version = "1.0.0"

        if datos_version:

            nueva_version = datos_version.get(
                "version",
                "1.0.0"
            )

        escribir_log(
            "Nueva versión detectada: "
            + nueva_version
        )

        archivo_version = os.path.join(
            carpeta_actual,
            "version.txt"
        )

        # ==================================================
        # ACTUALIZADOR EXTERNO
        # ==================================================

        bat = os.path.join(
            tempfile.gettempdir(),
            "actualizar_papelera_pos.bat"
        )

        internal_viejo = os.path.join(
            carpeta_actual,
            "_internal"
        )

        with open(
            bat,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                f"""@echo off
echo Esperando cierre del programa...
timeout /t 3 >nul

echo Eliminando _internal viejo...
rmdir /s /q "{internal_viejo}"

echo Copiando nueva version...
xcopy "{carpeta_temp}\\*" "{carpeta_actual}\\" /E /Y /I /H

echo Actualizando version...
echo {nueva_version}> "{archivo_version}"

echo Reiniciando programa...
start "" "{sys.executable}"

del "%~f0"
"""
            )

        escribir_log(
            "Actualizador externo creado: "
            + bat
        )

        escribir_log(
            "Ejecutando actualizador externo"
        )

        subprocess.Popen(
            bat,
            shell=True
        )

        return True

    except Exception as e:

        escribir_log(
            "ERROR INSTALANDO ACTUALIZACION: "
            + repr(e)
        )

        return False


# ==========================================================
# REINICIAR PROGRAMA
# ==========================================================

def reiniciar_programa():

    try:

        if getattr(sys, "frozen", False):

            ejecutable = sys.executable

            subprocess.Popen(
                [ejecutable],
                cwd=os.path.dirname(
                    ejecutable
                )
            )

        else:

            archivo_principal = os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(__file__)
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

        print(
            "Error reiniciando:",
            e
        )

        escribir_log(
            "ERROR REINICIANDO: "
            + repr(e)
        )