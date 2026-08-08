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


def obtener_info_version():

    try:

        respuesta = requests.get(
            f"{SERVIDOR}/version",
            timeout=TIMEOUT
        )

        if respuesta.status_code == 200:

            return respuesta.json()


    except Exception as e:

        print(
            "Error consultando versión:",
            e
        )


    return None



def obtener_ultima_version():

    datos = obtener_info_version()


    if datos:

        return datos.get(
            "version",
            "1.0.0"
        )


    return None



def obtener_url_actualizacion():

    datos = obtener_info_version()


    if datos:

        return datos.get(
            "url"
        )


    return None



def hay_actualizacion(version_actual):

    ultima_version = obtener_ultima_version()


    if ultima_version is None:

        return False, None


    if ultima_version != version_actual:

        return True, ultima_version


    return False, ultima_version



def descargar_actualizacion(progreso=None):

    url = obtener_url_actualizacion()

    if not url:

        print(
            "No hay URL de actualización"
        )

        return False


    try:

        respuesta = requests.get(
            url,
            timeout=60,
            stream=True
        )


        if respuesta.status_code != 200:

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

        return False



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
            "CARPETA BACKUP: " + carpeta_actual
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

        os.makedirs(destino)

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
                    "Copiando backup: " + origen
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
                    "No existe para backup: " + origen
                )                

        print(
            "Backup creado correctamente:",
            destino
        )
        
        limpiar_backups()
        
        return True


    except Exception as e:

        print(
            "Error creando backup:",
            e
        )

        return False
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

        if not os.path.exists(carpeta_backups):
            return


        backups = []

        for nombre in os.listdir(carpeta_backups):

            ruta = os.path.join(
                carpeta_backups,
                nombre
            )

            if os.path.isdir(ruta):

                backups.append(ruta)


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


    except Exception as e:

        print(
            "Error limpiando backups:",
            e
        )
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
            "CARPETA INSTALACION: " + carpeta_actual
        )


        carpeta_temp = os.path.join(
            tempfile.gettempdir(),
            "PAPELERA_POS_UPDATE"
        )


        if os.path.exists(carpeta_temp):

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


        # Si viene una carpeta PAPELERA_POS dentro del ZIP

        carpeta_extra = os.path.join(
            carpeta_temp,
            "PAPELERA_POS"
        )


        if os.path.exists(carpeta_extra):

            for elemento in os.listdir(carpeta_extra):

                origen = os.path.join(
                    carpeta_extra,
                    elemento
                )

                destino = os.path.join(
                    carpeta_temp,
                    elemento
                )

                if os.path.exists(destino):

                    if os.path.isdir(destino):

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


        datos_version = obtener_info_version()


        nueva_version = "1.0.0"


        if datos_version:

            nueva_version = datos_version.get(
                "version",
                "1.0.0"
            )


        archivo_version = os.path.join(
            carpeta_actual,
            "version.txt"
        )


        # Creamos actualizador externo BAT

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
xcopy "{carpeta_temp}\*" "{carpeta_actual}\" /E /Y /I /H

echo Actualizando version...
echo {nueva_version}> "{archivo_version}"

echo Reiniciando programa...
start "" "{sys.executable}"

del "%~f0"
"""
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
            "ERROR INSTALANDO ACTUALIZACION: " + str(e)
        )

        return False



def reiniciar_programa():
    try:

        if getattr(sys, "frozen", False):
            # Si es el .exe generado por PyInstaller
            ejecutable = sys.executable

            subprocess.Popen(
                [ejecutable],
                cwd=os.path.dirname(ejecutable)
            )

        else:
            # Si estamos ejecutando con Python
            archivo_principal = os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(__file__)
                    )
                ),
                "main.py"
            )

            subprocess.Popen(
                [sys.executable, archivo_principal],
                cwd=os.path.dirname(archivo_principal)
            )


        sys.exit()


    except Exception as e:

        print(
            "Error reiniciando:",
            e
        )