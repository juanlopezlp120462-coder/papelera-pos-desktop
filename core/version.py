import sys
import os
import requests


SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"

TIMEOUT = 5


# ============================================================
# ARCHIVO DE VERSION
# ============================================================

if getattr(sys, "frozen", False):

    VERSION_FILE = os.path.join(
        os.path.dirname(sys.executable),
        "version.txt"
    )

else:

    VERSION_FILE = os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        ),
        "version.txt"
    )


# ============================================================
# VERSION LOCAL
# ============================================================

def obtener_version_actual():

    version_por_defecto = "1.0.1"

    print(
        "DEBUG FROZEN:",
        getattr(sys, "frozen", False)
    )

    print(
        "DEBUG SYS.EXECUTABLE:",
        sys.executable
    )

    print(
        "DEBUG VERSION_FILE:",
        VERSION_FILE
    )

    print(
        "DEBUG EXISTE VERSION_FILE:",
        os.path.exists(VERSION_FILE)
    )

    try:

        if os.path.exists(VERSION_FILE):

            with open(
                VERSION_FILE,
                "r",
                encoding="utf-8-sig"
            ) as archivo:

                version = archivo.read()

                # Elimina BOM normal
                version = version.replace(
                    "\ufeff",
                    ""
                )

                # Elimina BOM mal interpretado
                version = version.replace(
                    "ï»¿",
                    ""
                )

                version = version.strip()

                print(
                    "VERSION FILE:",
                    VERSION_FILE
                )

                print(
                    "VERSION LOCAL LIMPIA:",
                    repr(version)
                )

                if version:

                    return version

    except Exception as e:

        print(
            "Error leyendo versión local:",
            repr(e)
        )

    print("Usando versión por defecto:", version_por_defecto)
    return version_por_defecto


# ============================================================
# VERSION DEL SERVIDOR
# ============================================================

def obtener_ultima_version():

    try:

        url = f"{SERVIDOR}/version"

        # Intentamos obtener el token si está definido en el entorno
        headers = {}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"

        print(
            "Consultando versión:",
            url
        )

        respuesta = requests.get(
            url,
            headers=headers,
            timeout=TIMEOUT
        )

        print(
            "HTTP versión:",
            respuesta.status_code
        )

        print(
            "Respuesta servidor:",
            respuesta.text
        )

        if respuesta.status_code != 200:

            return None

        datos = respuesta.json()

        print(
            "Datos versión:",
            repr(datos)
        )

        version = datos.get(
            "version"
        )

        if version is None:

            print(
                "ERROR: El servidor no devolvió version"
            )

            return None

        version = str(
            version
        ).replace(
            "\ufeff",
            ""
        ).replace(
            "ï»¿",
            ""
        ).strip()

        if not version:

            print(
                "ERROR: La versión del servidor está vacía"
            )

            return None

        return datos

    except Exception as e:

        print(
            "Error consultando versión:",
            repr(e)
        )

    return None


# ============================================================
# COMPROBAR ACTUALIZACION
# ============================================================

def hay_actualizacion(version_actual):

    version_actual = str(
        version_actual
    ).replace(
        "\ufeff",
        ""
    ).replace(
        "ï»¿",
        ""
    ).strip()

    print(
        "VERSION LOCAL PARA COMPARAR:",
        repr(version_actual)
    )

    datos = obtener_ultima_version()

    if datos is None:

        print(
            "No se pudo obtener versión del servidor"
        )

        return False, None

    ultima_version = datos.get(
        "version"
    )

    if ultima_version is None:

        print(
            "ERROR: El servidor no devolvió version"
        )

        return False, None

    ultima_version = str(
        ultima_version
    ).replace(
        "\ufeff",
        ""
    ).replace(
        "ï»¿",
        ""
    ).strip()

    print(
        "VERSION SERVIDOR PARA COMPARAR:",
        repr(ultima_version)
    )

    if not ultima_version:

        print(
            "ERROR: Version servidor vacía"
        )

        return False, None

    if ultima_version == version_actual:

        print(
            "RESULTADO: NO HAY ACTUALIZACION"
        )

        return False, ultima_version

    print(
        "RESULTADO: HAY ACTUALIZACION ->",
        ultima_version
    )

    return True, ultima_version