import sys
import os
import requests

SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"

TIMEOUT = 5


if getattr(sys, "frozen", False):

    VERSION_FILE = os.path.join(
        os.path.dirname(sys.executable),
        "version.txt"
    )

else:

    VERSION_FILE = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "version.txt"
    )

def obtener_version_actual():

    try:
        if os.path.exists(VERSION_FILE):

            with open(
                VERSION_FILE,
                "r",
                encoding="utf-8"
            ) as archivo:

                return archivo.read().strip()

    except Exception as e:
        print(
            "Error leyendo versión local:",
            e
        )

    return "1.0.0"



def obtener_ultima_version():

    try:

        respuesta = requests.get(
            f"{SERVIDOR}/version",
            timeout=TIMEOUT
        )

        if respuesta.status_code == 200:

            datos = respuesta.json()

            return datos


    except Exception as e:

        print(
            "Error consultando versión:",
            e
        )


    return None



def hay_actualizacion(version_actual):

    datos = obtener_ultima_version()


    if datos is None:

        return False, None, 


    ultima_version = datos.get(
        "version",
        version_actual
    )


    url = datos.get(
        "url"
    )

    if ultima_version != version_actual:

        return True, ultima_version


    return False, ultima_version