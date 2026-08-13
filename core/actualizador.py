import sys
import os
import requests
import zipfile
import tempfile
import shutil
import subprocess
import time


SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"

TIMEOUT = 10


# ============================================================
# ARCHIVO DE VERSION
# ============================================================

def obtener_ruta_version():

    if getattr(sys, "frozen", False):

        exe_dir = os.path.dirname(
            sys.executable
        )

        base_dir = getattr(
            sys,
            "_MEIPASS",
            exe_dir
        )

    else:

        exe_dir = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )

        base_dir = exe_dir


    posibles_rutas = [

        os.path.join(
            exe_dir,
            "version.txt"
        ),

        os.path.join(
            exe_dir,
            "_internal",
            "version.txt"
        ),

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

        if os.path.exists(ruta):

            return ruta


    return os.path.join(
        exe_dir,
        "version.txt"
    )


VERSION_FILE = obtener_ruta_version()


# ============================================================
# VERSION LOCAL
# ============================================================

def obtener_version_actual():

    version_por_defecto = "1.0.1"


    try:

        ruta_actual = obtener_ruta_version()

        print(
            "RUTA DETECTADA VERSION_FILE:",
            ruta_actual
        )


        if os.path.exists(ruta_actual):

            with open(
                ruta_actual,
                "r",
                encoding="utf-8-sig"
            ) as archivo:

                version = archivo.read()


            version = version.replace(
                "\ufeff",
                ""
            )

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


    print(
        "Usando versión por defecto:",
        version_por_defecto
    )

    return version_por_defecto


# ============================================================
# VERSION DEL SERVIDOR
# ============================================================

def obtener_ultima_version():

    try:

        url = f"{SERVIDOR}/version"


        headers = {}

        token = os.getenv(
            "GITHUB_TOKEN"
        )

        if token:

            headers["Authorization"] = (
                f"token {token}"
            )


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


# ============================================================
# DESCARGAR ACTUALIZACION
# ============================================================

def descargar_actualizacion(
    callback_progreso=None
):

    try:

        datos = obtener_ultima_version()


        if not datos:

            print(
                "ERROR: No se pudo obtener información de actualización."
            )

            return None


        url = datos.get(
            "url"
        )


        if not url:

            print(
                "ERROR: El servidor no devolvió URL de actualización."
            )

            return None


        print(
            "URL ACTUALIZACION:",
            url
        )


        carpeta_temp = tempfile.mkdtemp(
            prefix="papelera_update_"
        )


        archivo_zip = os.path.join(
            carpeta_temp,
            "update.zip"
        )


        print(
            "Descargando actualización..."
        )


        respuesta = requests.get(
            url,
            stream=True,
            timeout=60
        )


        print(
            "HTTP descarga:",
            respuesta.status_code
        )


        if respuesta.status_code != 200:

            print(
                "ERROR descargando actualización:",
                respuesta.status_code
            )

            shutil.rmtree(
                carpeta_temp,
                ignore_errors=True
            )

            return None


        total = int(
            respuesta.headers.get(
                "content-length",
                0
            )
        )


        descargado = 0


        with open(
            archivo_zip,
            "wb"
        ) as archivo:

            for bloque in respuesta.iter_content(
                chunk_size=1024 * 64
            ):

                if not bloque:

                    continue


                archivo.write(
                    bloque
                )


                descargado += len(
                    bloque
                )


                if total > 0:

                    porcentaje = int(
                        descargado * 100 / total
                    )

                else:

                    porcentaje = 0


                if callback_progreso:

                    try:

                        callback_progreso(
                            porcentaje
                        )

                    except Exception:

                        pass


        print(
            "Actualización descargada:",
            archivo_zip
        )


        # ====================================================
        # VERIFICAR ZIP
        # ====================================================

        if not zipfile.is_zipfile(
            archivo_zip
        ):

            print(
                "ERROR: El archivo descargado no es un ZIP válido."
            )

            shutil.rmtree(
                carpeta_temp,
                ignore_errors=True
            )

            return None


        print(
            "UPDATE.zip válido."
        )


        return archivo_zip


    except Exception as e:

        print(
            "ERROR descargando actualización:",
            repr(e)
        )

        return None


# ============================================================
# INSTALAR ACTUALIZACION
# ============================================================

def instalar_actualizacion(
    archivo_zip,
    nueva_version
):

    try:

        if not archivo_zip:

            print(
                "ERROR: No se recibió archivo ZIP."
            )

            return False


        if not os.path.exists(
            archivo_zip
        ):

            print(
                "ERROR: No existe el ZIP:",
                archivo_zip
            )

            return False


        # ====================================================
        # CARPETA DE LA INSTALACION
        # ====================================================

        if getattr(
            sys,
            "frozen",
            False
        ):

            carpeta_programa = os.path.dirname(
                sys.executable
            )

            exe_actual = sys.executable

        else:

            carpeta_programa = os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )

            exe_actual = os.path.join(
                carpeta_programa,
                "PAPELERA_POS.exe"
            )


        print(
            "CARPETA PROGRAMA:",
            carpeta_programa
        )

        print(
            "EXE ACTUAL:",
            exe_actual
        )


        # ====================================================
        # CARPETA TEMPORAL DE EXTRACCION
        # ====================================================

        carpeta_temp = tempfile.mkdtemp(
            prefix="papelera_extract_"
        )


        print(
            "Extrayendo actualización..."
        )


        with zipfile.ZipFile(
            archivo_zip,
            "r"
        ) as zip_ref:

            zip_ref.extractall(
                carpeta_temp
            )


        # ====================================================
        # DETECTAR CONTENIDO DEL ZIP
        # ====================================================

        contenido = os.listdir(
            carpeta_temp
        )


        print(
            "CONTENIDO UPDATE:",
            contenido
        )


        # Si GitHub tiene una carpeta raíz dentro del ZIP,
        # la detectamos automáticamente.

        carpeta_update = carpeta_temp


        if len(contenido) == 1:

            posible_carpeta = os.path.join(
                carpeta_temp,
                contenido[0]
            )


            if os.path.isdir(
                posible_carpeta
            ):

                carpeta_update = posible_carpeta


        print(
            "CARPETA UPDATE:",
            carpeta_update
        )


        # ====================================================
        # VERIFICAR EXE
        # ====================================================

        exe_update = os.path.join(
            carpeta_update,
            "PAPELERA_POS.exe"
        )


        if not os.path.exists(
            exe_update
        ):

            print(
                "ERROR: UPDATE.zip no contiene PAPELERA_POS.exe."
            )

            shutil.rmtree(
                carpeta_temp,
                ignore_errors=True
            )

            return False


        # ====================================================
        # VERIFICAR _internal
        # ====================================================

        internal_update = os.path.join(
            carpeta_update,
            "_internal"
        )


        if not os.path.isdir(
            internal_update
        ):

            print(
                "ERROR: UPDATE.zip no contiene _internal."
            )

            shutil.rmtree(
                carpeta_temp,
                ignore_errors=True
            )

            return False


        print(
            "UPDATE.zip contiene PAPELERA_POS.exe y _internal."
        )


        # ====================================================
        # CREAR SCRIPT DE ACTUALIZACION
        # ====================================================

        script = os.path.join(
            carpeta_programa,
            "_actualizar_papelera.bat"
        )


        # IMPORTANTE:
        #
        # NO copiamos database.
        #
        # Solamente reemplazamos:
        #
        # PAPELERA_POS.exe
        # _internal
        # version.txt
        #
        # La database existente queda intacta.
        #

        contenido_bat = f'''@echo off
setlocal

echo ==========================================
echo ACTUALIZANDO PAPELERA POS
echo ==========================================

timeout /t 2 /nobreak >nul

echo.
echo Esperando que cierre PAPELERA_POS...

:ESPERAR
tasklist /FI "IMAGENAME eq PAPELERA_POS.exe" 2>NUL | find /I "PAPELERA_POS.exe" >NUL

if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto ESPERAR
)

echo.
echo Reemplazando archivos...

echo Eliminando _internal anterior...
if exist "{os.path.join(carpeta_programa, "_internal")}" (
    rmdir /S /Q "{os.path.join(carpeta_programa, "_internal")}"
)

echo Copiando nuevo _internal...
xcopy /E /I /Y "{internal_update}" "{os.path.join(carpeta_programa, "_internal")}" >nul

echo.
echo Copiando PAPELERA_POS.exe...
copy /Y "{exe_update}" "{os.path.join(carpeta_programa, "PAPELERA_POS.exe")}" >nul

echo.
echo Actualizando version.txt...

if exist "{os.path.join(carpeta_update, "version.txt")}" (
    copy /Y "{os.path.join(carpeta_update, "version.txt")}" "{os.path.join(carpeta_programa, "version.txt")}" >nul
)

echo.
echo ==========================================
echo ACTUALIZACION TERMINADA
echo ==========================================

echo.
echo Iniciando nueva version...

start "" "{exe_actual}"

echo.
echo Limpiando archivos temporales...

timeout /t 2 /nobreak >nul

rmdir /S /Q "{carpeta_temp}"

del "%~f0"

endlocal
'''


        with open(
            script,
            "w",
            encoding="utf-8"
        ) as archivo:

            archivo.write(
                contenido_bat
            )


        print(
            "SCRIPT ACTUALIZACION:",
            script
        )


        # ====================================================
        # EJECUTAR BAT
        # ====================================================

        subprocess.Popen(
            [
                "cmd.exe",
                "/c",
                "start",
                "",
                script
            ],
            cwd=carpeta_programa,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )


        print(
            "Actualizador externo iniciado."
        )


        return True


    except Exception as e:

        print(
            "ERROR instalando actualización:",
            repr(e)
        )

        return False