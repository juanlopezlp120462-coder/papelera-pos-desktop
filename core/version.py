import sys
import os
import requests


# ============================================================
# CONFIGURACION
# ============================================================

SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"

TIMEOUT = 10

VERSION_POR_DEFECTO = "1.0.1"


# ============================================================
# ARCHIVO DE VERSION
# ============================================================

def obtener_ruta_version():

    if getattr(sys, "frozen", False):

        exe_dir = os.path.dirname(
            os.path.abspath(sys.executable)
        )

        posibles_rutas = [

            os.path.join(
                exe_dir,
                "version.txt"
            ),

            os.path.join(
                exe_dir,
                "_internal",
                "version.txt"
            )
        ]

    else:

        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )

        posibles_rutas = [

            os.path.join(
                base_dir,
                "version.txt"
            ),

            os.path.join(
                base_dir,
                "_internal",
                "version.txt"
            )
        ]


    for ruta in posibles_rutas:

        if os.path.isfile(ruta):

            return ruta


    # Devolvemos la ubicación esperada aunque todavía
    # no exista, para que el diagnóstico sea claro.

    if getattr(sys, "frozen", False):

        return os.path.join(
            os.path.dirname(
                os.path.abspath(sys.executable)
            ),
            "version.txt"
        )

    return os.path.join(
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

    ruta_version = obtener_ruta_version()

    print("")
    print("==========================================")
    print("DIAGNOSTICO VERSION LOCAL")
    print("==========================================")
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
        ruta_version
    )
    print(
        "DEBUG EXISTE VERSION_FILE:",
        os.path.isfile(ruta_version)
    )


    try:

        if os.path.isfile(ruta_version):

            with open(
                ruta_version,
                "r",
                encoding="utf-8-sig"
            ) as archivo:

                version = archivo.read()


            version = (
                version
                .replace("\ufeff", "")
                .replace("ï»¿", "")
                .replace("Ã¯Â»Â¿", "")
                .strip()
            )


            print(
                "VERSION FILE:",
                ruta_version
            )

            print(
                "VERSION LOCAL LIMPIA:",
                repr(version)
            )


            if version:

                print(
                    "VERSION LOCAL FINAL:",
                    version
                )

                print("==========================================")
                print("")

                return version


    except Exception as e:

        print(
            "ERROR leyendo version.txt:",
            repr(e)
        )


    print(
        "ADVERTENCIA: No se pudo leer version.txt."
    )

    print(
        "Usando versión por defecto:",
        VERSION_POR_DEFECTO
    )

    print("==========================================")
    print("")

    return VERSION_POR_DEFECTO


# ============================================================
# VERSION DEL SERVIDOR
# ============================================================

def obtener_ultima_version():

    try:

        url = f"{SERVIDOR}/version"

        print("")
        print("==========================================")
        print("CONSULTANDO VERSION DEL SERVIDOR")
        print("==========================================")
        print(
            "URL:",
            url
        )


        respuesta = requests.get(
            url,
            timeout=TIMEOUT
        )


        print(
            "HTTP versión:",
            respuesta.status_code
        )


        if respuesta.status_code != 200:

            print(
                "ERROR: El servidor devolvió HTTP",
                respuesta.status_code
            )

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
                "ERROR: El servidor no devolvió version."
            )

            return None


        version = (
            str(version)
            .replace("\ufeff", "")
            .replace("ï»¿", "")
            .replace("Ã¯Â»Â¿", "")
            .strip()
        )


        if not version:

            print(
                "ERROR: La versión del servidor está vacía."
            )

            return None


        url_update = datos.get(
            "url"
        )


        if url_update:

            url_update = str(
                url_update
            ).strip()


        resultado = {

            "version": version,

            "url": url_update
        }


        print(
            "VERSION SERVIDOR:",
            repr(version)
        )

        print(
            "URL UPDATE:",
            url_update
        )

        print("==========================================")
        print("")


        return resultado


    except Exception as e:

        print(
            "ERROR consultando versión:",
            repr(e)
        )

        return None


# ============================================================
# CONVERTIR VERSION
# ============================================================

def convertir_version(version):

    try:

        partes = str(
            version
        ).strip().split(".")


        if len(partes) != 3:

            return None


        return tuple(
            int(parte)
            for parte in partes
        )


    except Exception:

        return None


# ============================================================
# COMPROBAR ACTUALIZACION
# ============================================================

def hay_actualizacion(version_actual):

    version_actual = (
        str(version_actual)
        .replace("\ufeff", "")
        .replace("ï»¿", "")
        .replace("Ã¯Â»Â¿", "")
        .strip()
    )


    print("")
    print("==========================================")
    print("COMPROBANDO ACTUALIZACION")
    print("==========================================")

    print(
        "VERSION LOCAL PARA COMPARAR:",
        repr(version_actual)
    )


    datos = obtener_ultima_version()


    if datos is None:

        print(
            "No se pudo obtener versión del servidor."
        )

        return False, None


    ultima_version = datos.get(
        "version"
    )


    if not ultima_version:

        print(
            "ERROR: El servidor no devolvió versión."
        )

        return False, None


    ultima_version = (
        str(ultima_version)
        .replace("\ufeff", "")
        .replace("ï»¿", "")
        .replace("Ã¯Â»Â¿", "")
        .strip()
    )


    print(
        "VERSION SERVIDOR PARA COMPARAR:",
        repr(ultima_version)
    )


    local_tuple = convertir_version(
        version_actual
    )

    servidor_tuple = convertir_version(
        ultima_version
    )


    if local_tuple is None:

        print(
            "ERROR: La versión local no tiene formato X.X.X:",
            repr(version_actual)
        )

        return False, None


    if servidor_tuple is None:

        print(
            "ERROR: La versión del servidor no tiene formato X.X.X:",
            repr(ultima_version)
        )

        return False, None


    # ========================================================
    # VERSION IGUAL
    # ========================================================

    if servidor_tuple == local_tuple:

        print(
            "RESULTADO: NO HAY ACTUALIZACION"
        )

        print("==========================================")
        print("")

        return False, ultima_version


    # ========================================================
    # VERSION NUEVA
    # ========================================================

    if servidor_tuple > local_tuple:

        print(
            "RESULTADO: HAY ACTUALIZACION"
        )

        print(
            "Nueva versión:",
            ultima_version
        )

        print("==========================================")
        print("")

        return True, ultima_version


    # ========================================================
    # SERVIDOR MAS VIEJO
    # ========================================================

    print(
        "RESULTADO: EL SERVIDOR TIENE UNA VERSION MAS VIEJA."
    )

    print("==========================================")
    print("")

    return False, ultima_version