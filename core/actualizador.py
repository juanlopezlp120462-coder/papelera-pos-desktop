import sys
import os
import requests


SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"

TIMEOUT = 5


# ============================================================
# ARCHIVO DE VERSION (RUTAS ROBUSTAS PARA PYINSTALLER)
# ============================================================

def obtener_ruta_version():
    """Busca el archivo version.txt en todas las ubicaciones posibles tanto en desarrollo como empaquetado."""
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        base_dir = getattr(sys, "_MEIPASS", exe_dir)
    else:
        exe_dir = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
        base_dir = exe_dir

    posibles_rutas = [
        os.path.join(exe_dir, "version.txt"),
        os.path.join(exe_dir, "_internal", "version.txt"),
        os.path.join(base_dir, "version.txt"),
        os.path.join(base_dir, "_internal", "version.txt")
    ]

    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            return ruta
            
    return os.path.join(exe_dir, "version.txt")

VERSION_FILE = obtener_ruta_version()


# ============================================================
# VERSION LOCAL
# ============================================================

def obtener_version_actual():
    # Versión fija de respaldo por si el archivo de texto no existe o falla
    version_por_defecto = "1.0.1"

    try:
        ruta_actual = obtener_ruta_version()
        print("RUTA DETECTADA VERSION_FILE:", ruta_actual)

        if os.path.exists(ruta_actual):

            with open(
                ruta_actual,
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
                    ruta_actual
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