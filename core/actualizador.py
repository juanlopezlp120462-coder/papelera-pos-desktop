import os
import tempfile
import requests
import zipfile
import shutil
import sys
import subprocess
import datetime


SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"

TIMEOUT = 10
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

            print(
                "No se pudo crear backup. Cancelando actualización."
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
            ruta_debug = os.path.join(
                tempfile.gettempdir(),
                "PAPELERA_debug.txt"
            )

            with open(
                ruta_debug,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(
                    "CARPETA INSTALACION:\n"
                )
                f.write(
                    carpeta_actual
                )
                f.write(
                    "\n\nEXE:\n"
                )
                f.write(
                    sys.executable
                )
                f.write(
                    "\n"
                )
               
        try:
            with open(
                "actualizador_debug.txt",
                "a",
                encoding="utf-8"
            ) as f:
                f.write("\n====================\n")
                f.write(
                    f"CARPETA INSTALACION: {carpeta_actual}\n"
                )
                f.write(
                    f"EXE ACTUAL: {sys.executable}\n"
                )
                f.write(
                    f"CONTENIDO: {os.listdir(carpeta_actual)}\n"
                )

        except Exception as e:
            pass                    
                
        print("CARPETA INSTALACION:", carpeta_actual)
        print("CONTENIDO INSTALACION:", os.listdir(carpeta_actual))
        carpeta_temp = os.path.join(
            tempfile.gettempdir(),
            "PAPELERA_POS_UPDATE"
        )


        if os.path.exists(carpeta_temp):

            shutil.rmtree(
                carpeta_temp
            )


        os.makedirs(
            carpeta_temp
        )


        print(
            "Extrayendo actualización..."
        )


        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as zip_ref:

            zip_ref.extractall(
                carpeta_temp
            )
            
        # Corregir estructura si viene carpeta PAPELERA_POS dentro del ZIP

        carpeta_extra = os.path.join(
            carpeta_temp,
            "PAPELERA_POS"
        )

        if os.path.exists(carpeta_extra):

            escribir_log(
                "Detectada carpeta extra PAPELERA_POS"
            )

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
                        shutil.rmtree(destino)
                    else:
                        os.remove(destino)

                shutil.move(
                    origen,
                    destino
                )

            shutil.rmtree(
                carpeta_extra
            )            


        print(
            "Copiando archivos nuevos..."
        )

        # BORRAR _internal UNA SOLA VEZ

        internal_viejo = os.path.join(
            carpeta_actual,
            "_internal"
        )


        if os.path.exists(internal_viejo):

            try:

                shutil.rmtree(
                    internal_viejo
                )

                escribir_log(
                    "ELIMINADO _internal VIEJO"
                )


            except Exception as e:

                escribir_log(
                    f"ERROR BORRANDO _internal: {e}"
                )



        # COPIAR TODO EL UPDATE

        for root, dirs, files in os.walk(
            carpeta_temp
        ):


            destino = root.replace(
                carpeta_temp,
                carpeta_actual
            )


            os.makedirs(
                destino,
                exist_ok=True
            )


            for archivo in files:


                origen_archivo = os.path.join(
                    root,
                    archivo
                )


                destino_archivo = os.path.join(
                    destino,
                    archivo
                )


                shutil.copy2(
                    origen_archivo,
                    destino_archivo
                )


                escribir_log(
                    f"COPIADO: {destino_archivo}"
                )
        print(
            "Actualización instalada correctamente"
        )
        escribir_log(
            "Actualización instalada correctamente"
        )
        # Actualizar versión local instalada

        archivo_version = os.path.join(
            carpeta_actual,
            "version.txt"
        )

        datos_version = obtener_info_version()

        nueva_version = datos_version.get(
            "version",
            "1.0.0"
        ) if datos_version else "1.0.0"


        print(
            "ESCRIBIENDO VERSION EN:",
            archivo_version
        )

        print(
            "NUEVA VERSION:",
            nueva_version
        )
        escribir_log(
            "ESCRIBIENDO VERSION EN: " + archivo_version
        )

        escribir_log(
            "NUEVA VERSION: " + nueva_version
        )
        with open(
            archivo_version,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                nueva_version
            )


        print(
            f"Versión local actualizada a {nueva_version}"
        )
        return True


    except Exception as e:

        print(
            "Error instalando actualización:",
            e
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