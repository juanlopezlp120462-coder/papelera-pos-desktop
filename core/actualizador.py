import os
import tempfile
import requests
import zipfile
import shutil
import sys
import subprocess


SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"

TIMEOUT = 10


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



def descargar_actualizacion():

    url = obtener_url_actualizacion()


    if not url:

        print(
            "No hay URL de actualización"
        )

        return False



    try:

        respuesta = requests.get(
            url,
            timeout=60
        )


        if respuesta.status_code != 200:

            print(
                "Error descargando actualización:",
                respuesta.status_code
            )

            return False



        archivo_temp = os.path.join(
            tempfile.gettempdir(),
            "PAPELERA_POS_update.zip"
        )


        with open(
            archivo_temp,
            "wb"
        ) as f:

            f.write(
                respuesta.content
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



def instalar_actualizacion(zip_path):

    try:

        carpeta_actual = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )


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


        print(
            "Copiando archivos nuevos..."
        )


        for root, dirs, files in os.walk(carpeta_temp):

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


        print(
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