import sys
import os
import requests
import zipfile
import tempfile
import shutil
import subprocess


# ============================================================
# CONFIGURACIÓN SUPABASE
# ============================================================

SUPABASE_URL = "https://vspfeihawhfdlpeqwxgp.supabase.co"

# Clave pública.
# NO usar service_role dentro del EXE.
SUPABASE_KEY_PUBLICA = (
    "sb_publishable_EReRHa9kq-8RLNusRzIC6Q_H2Q8TEk9"
)


# ============================================================
# CARGAR .ENV SI EXISTE
# ============================================================

try:
    from dotenv import load_dotenv

    load_dotenv()

except Exception:
    pass


# ============================================================
# CONFIGURACIÓN FINAL
# ============================================================

# Si existe .env y tiene valores válidos, los utiliza.
# Si no existe .env, utiliza los valores incorporados.

SUPABASE_URL_FINAL = (
    os.getenv("SUPABASE_URL")
    or SUPABASE_URL
)

SUPABASE_KEY_FINAL = (
    os.getenv("SUPABASE_KEY")
    or SUPABASE_KEY_PUBLICA
)


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

TIMEOUT_VERSION = 10
TIMEOUT_DESCARGA = 60


# ============================================================
# LIMPIAR VERSIÓN
# ============================================================

def limpiar_version(version):

    if version is None:
        return ""

    version = str(version)

    version = version.replace("\ufeff", "")
    version = version.replace("ï»¿", "")

    version = version.strip()

    return version


# ============================================================
# CONVERTIR VERSIÓN A NÚMEROS
# ============================================================

def version_numerica(version):

    version = limpiar_version(version)

    try:

        partes = version.split(".")

        if len(partes) != 3:
            return None

        return (
            int(partes[0]),
            int(partes[1]),
            int(partes[2])
        )

    except Exception:

        return None


# ============================================================
# OBTENER RUTA DE VERSION.TXT
# ============================================================

def obtener_ruta_version():

    # --------------------------------------------------------
    # PROGRAMA COMPILADO
    # --------------------------------------------------------

    if getattr(sys, "frozen", False):

        exe_dir = os.path.dirname(
            os.path.abspath(sys.executable)
        )

        base_dir = exe_dir

    # --------------------------------------------------------
    # PYTHON
    # --------------------------------------------------------

    else:

        # core/actualizador.py
        #
        # dirname(__file__)          -> core
        # dirname(dirname(__file__)) -> proyecto

        exe_dir = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )

        base_dir = exe_dir

    # --------------------------------------------------------
    # POSIBLES UBICACIONES
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # RUTA PRINCIPAL POR DEFECTO
    # --------------------------------------------------------

    return os.path.join(
        exe_dir,
        "version.txt"
    )


# ============================================================
# OBTENER VERSIÓN LOCAL
# ============================================================

def obtener_version_actual():

    version_por_defecto = "1.0.1"

    print()
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

    ruta_version = obtener_ruta_version()

    print(
        "DEBUG VERSION_FILE:",
        ruta_version
    )

    print(
        "DEBUG EXISTE VERSION_FILE:",
        os.path.exists(ruta_version)
    )

    try:

        if os.path.exists(ruta_version):

            with open(
                ruta_version,
                "r",
                encoding="utf-8-sig"
            ) as archivo:

                version = archivo.read()

            version = limpiar_version(version)

            print(
                "VERSION FILE:",
                ruta_version
            )

            print(
                "VERSION LOCAL LIMPIA:",
                repr(version)
            )

            if version:

                version_num = version_numerica(version)

                if version_num is not None:

                    print(
                        "VERSION LOCAL NUMERICA:",
                        version_num
                    )

                    print(
                        "VERSION LOCAL FINAL:",
                        version
                    )

                    print(
                        "=========================================="
                    )

                    return version

                print(
                    "ADVERTENCIA: Formato de version invalido:",
                    repr(version)
                )

    except Exception as e:

        print(
            "ERROR leyendo version local:",
            repr(e)
        )

    print(
        "Usando version por defecto:",
        version_por_defecto
    )

    print(
        "=========================================="
    )

    return version_por_defecto


# ============================================================
# OBTENER ÚLTIMA VERSIÓN DESDE SUPABASE
# ============================================================

def obtener_ultima_version():

    try:

        endpoint = (
            SUPABASE_URL_FINAL.rstrip("/")
            + "/rest/v1/versiones"
        )

        # ----------------------------------------------------
        # PARÁMETROS
        # ----------------------------------------------------

        parametros = {

            "select": (
                "version,url,activo,created_at"
            ),

            "activo": "eq.true",

            "order": "created_at.desc",

            "limit": "1"
        }

        # ----------------------------------------------------
        # HEADERS
        # ----------------------------------------------------

        headers = {

            "apikey": SUPABASE_KEY_FINAL,

            "Authorization":
                "Bearer "
                + SUPABASE_KEY_FINAL,

            "Accept": "application/json"
        }

        print()
        print(
            "Consultando versión en Supabase..."
        )

        print(
            "URL SUPABASE:",
            endpoint
        )

        # ----------------------------------------------------
        # CONSULTA
        # ----------------------------------------------------

        respuesta = requests.get(

            endpoint,

            params=parametros,

            headers=headers,

            timeout=TIMEOUT_VERSION
        )

        print(
            "HTTP SUPABASE:",
            respuesta.status_code
        )

        print(
            "RESPUESTA SUPABASE:",
            respuesta.text
        )

        # ----------------------------------------------------
        # ERROR HTTP
        # ----------------------------------------------------

        if respuesta.status_code != 200:

            print(
                "ERROR: Supabase devolvió HTTP",
                respuesta.status_code
            )

            return None

        # ----------------------------------------------------
        # CONVERTIR A JSON
        # ----------------------------------------------------

        try:

            datos = respuesta.json()

        except Exception as e:

            print(
                "ERROR convirtiendo respuesta Supabase a JSON:",
                repr(e)
            )

            return None

        print(
            "DATOS SUPABASE:",
            repr(datos)
        )

        # ----------------------------------------------------
        # SIN REGISTROS
        # ----------------------------------------------------

        if not datos:

            print(
                "ERROR: No existe ninguna versión activa en Supabase."
            )

            return None

        registro = datos[0]

        # ----------------------------------------------------
        # OBTENER VERSIÓN
        # ----------------------------------------------------

        version = registro.get("version")

        if version is None:

            print(
                "ERROR: Supabase no devolvió version."
            )

            return None

        version = limpiar_version(version)

        # ----------------------------------------------------
        # OBTENER URL
        # ----------------------------------------------------

        url = registro.get("url")

        if not url:

            print(
                "ERROR: Supabase no devolvió URL de actualización."
            )

            return None

        url = str(url).strip()

        # ----------------------------------------------------
        # VALIDAR VERSIÓN
        # ----------------------------------------------------

        if not version:

            print(
                "ERROR: La versión de Supabase está vacía."
            )

            return None

        version_num = version_numerica(version)

        if version_num is None:

            print(
                "ERROR: Versión inválida en Supabase:",
                repr(version)
            )

            return None

        # ----------------------------------------------------
        # VALIDAR URL
        # ----------------------------------------------------

        if not (
            url.startswith("https://")
            or url.startswith("http://")
        ):

            print(
                "ERROR: URL de actualización inválida:",
                repr(url)
            )

            return None

        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        resultado = {

            "version": version,

            "url": url
        }

        print(
            "VERSION SUPABASE:",
            repr(version)
        )

        print(
            "URL ACTUALIZACION:",
            url
        )

        return resultado

    except requests.RequestException as e:

        print(
            "ERROR de conexión con Supabase:",
            repr(e)
        )

        return None

    except Exception as e:

        print(
            "ERROR consultando Supabase:",
            repr(e)
        )

        return None


# ============================================================
# COMPROBAR SI HAY ACTUALIZACIÓN
# ============================================================

def hay_actualizacion(version_actual):

    # --------------------------------------------------------
    # LIMPIAR VERSIÓN LOCAL
    # --------------------------------------------------------

    version_actual = limpiar_version(
        version_actual
    )

    print()
    print(
        "VERSION LOCAL PARA COMPARAR:",
        repr(version_actual)
    )

    # --------------------------------------------------------
    # CONVERTIR VERSIÓN LOCAL
    # --------------------------------------------------------

    version_local_num = version_numerica(
        version_actual
    )

    if version_local_num is None:

        print(
            "ERROR: La versión local no tiene formato X.X.X:",
            repr(version_actual)
        )

        return False, None

    print(
        "VERSION LOCAL NUMERICA:",
        version_local_num
    )

    # --------------------------------------------------------
    # CONSULTAR SERVIDOR
    # --------------------------------------------------------

    datos = obtener_ultima_version()

    if datos is None:

        print(
            "No se pudo obtener versión del servidor."
        )

        return False, None

    # --------------------------------------------------------
    # VERSIÓN SERVIDOR
    # --------------------------------------------------------

    ultima_version = datos.get("version")

    if ultima_version is None:

        print(
            "ERROR: El servidor no devolvió versión."
        )

        return False, None

    ultima_version = limpiar_version(
        ultima_version
    )

    print(
        "VERSION SERVIDOR PARA COMPARAR:",
        repr(ultima_version)
    )

    # --------------------------------------------------------
    # CONVERTIR VERSIÓN SERVIDOR
    # --------------------------------------------------------

    version_servidor_num = version_numerica(
        ultima_version
    )

    if version_servidor_num is None:

        print(
            "ERROR: Versión del servidor inválida:",
            repr(ultima_version)
        )

        return False, None

    print(
        "VERSION SERVIDOR NUMERICA:",
        version_servidor_num
    )

    # --------------------------------------------------------
    # COMPARACIÓN
    # --------------------------------------------------------

    if version_servidor_num <= version_local_num:

        print(
            "RESULTADO: NO HAY ACTUALIZACION"
        )

        return False, ultima_version

    # --------------------------------------------------------
    # HAY ACTUALIZACIÓN
    # --------------------------------------------------------

    print(
        "RESULTADO: HAY ACTUALIZACION ->",
        ultima_version
    )

    return True, ultima_version


# ============================================================
# DESCARGAR ACTUALIZACIÓN
# ============================================================

def descargar_actualizacion(callback_progreso=None):

    carpeta_temp = None

    try:

        # ----------------------------------------------------
        # OBTENER DATOS
        # ----------------------------------------------------

        datos = obtener_ultima_version()

        if not datos:

            print(
                "ERROR: No se pudo obtener información de actualización."
            )

            return None

        url = datos.get("url")

        if not url:

            print(
                "ERROR: No existe URL de actualización."
            )

            return None

        version = datos.get("version")

        print(
            "VERSION A DESCARGAR:",
            version
        )

        print(
            "URL ACTUALIZACION:",
            url
        )

        # ----------------------------------------------------
        # CARPETA TEMPORAL
        # ----------------------------------------------------

        carpeta_temp = tempfile.mkdtemp(
            prefix="papelera_update_"
        )

        archivo_zip = os.path.join(
            carpeta_temp,
            "update.zip"
        )

        print(
            "CARPETA TEMPORAL:",
            carpeta_temp
        )

        print(
            "ARCHIVO ZIP:",
            archivo_zip
        )

        # ----------------------------------------------------
        # DESCARGA
        # ----------------------------------------------------

        print(
            "Descargando actualización..."
        )

        respuesta = requests.get(

            url,

            stream=True,

            timeout=TIMEOUT_DESCARGA,

            allow_redirects=True
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

        # ----------------------------------------------------
        # TAMAÑO
        # ----------------------------------------------------

        try:

            total = int(
                respuesta.headers.get(
                    "content-length",
                    0
                )
            )

        except Exception:

            total = 0

        descargado = 0

        # ----------------------------------------------------
        # GUARDAR ZIP
        # ----------------------------------------------------

        with open(
            archivo_zip,
            "wb"
        ) as archivo:

            for bloque in respuesta.iter_content(
                chunk_size=1024 * 64
            ):

                if not bloque:
                    continue

                archivo.write(bloque)

                descargado += len(bloque)

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
            "Actualización descargada:"
        )

        print(
            archivo_zip
        )

        # ----------------------------------------------------
        # VERIFICAR ARCHIVO
        # ----------------------------------------------------

        if not os.path.exists(
            archivo_zip
        ):

            print(
                "ERROR: El ZIP no fue creado."
            )

            shutil.rmtree(
                carpeta_temp,
                ignore_errors=True
            )

            return None

        if os.path.getsize(
            archivo_zip
        ) <= 0:

            print(
                "ERROR: El ZIP está vacío."
            )

            shutil.rmtree(
                carpeta_temp,
                ignore_errors=True
            )

            return None

        # ----------------------------------------------------
        # VERIFICAR ZIP
        # ----------------------------------------------------

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

    except requests.RequestException as e:

        print(
            "ERROR de conexión descargando actualización:",
            repr(e)
        )

        if carpeta_temp:

            shutil.rmtree(
                carpeta_temp,
                ignore_errors=True
            )

        return None

    except Exception as e:

        print(
            "ERROR descargando actualización:",
            repr(e)
        )

        if carpeta_temp:

            shutil.rmtree(
                carpeta_temp,
                ignore_errors=True
            )

        return None


# ============================================================
# INSTALAR ACTUALIZACIÓN
# ============================================================

def instalar_actualizacion(
    archivo_zip,
    nueva_version
):

    carpeta_temp = None

    try:

        # ----------------------------------------------------
        # VALIDAR ZIP
        # ----------------------------------------------------

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

        if not zipfile.is_zipfile(
            archivo_zip
        ):

            print(
                "ERROR: El archivo no es un ZIP válido."
            )

            return False

        # ----------------------------------------------------
        # CARPETA DEL PROGRAMA
        # ----------------------------------------------------

        if getattr(
            sys,
            "frozen",
            False
        ):

            carpeta_programa = os.path.dirname(
                os.path.abspath(
                    sys.executable
                )
            )

            exe_actual = os.path.abspath(
                sys.executable
            )

        else:

            carpeta_programa = os.path.dirname(
                os.path.dirname(
                    os.path.abspath(
                        __file__
                    )
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

        # ----------------------------------------------------
        # CARPETA TEMPORAL
        # ----------------------------------------------------

        carpeta_temp = tempfile.mkdtemp(
            prefix="papelera_extract_"
        )

        print(
            "CARPETA EXTRACCION:",
            carpeta_temp
        )

        # ----------------------------------------------------
        # EXTRAER ZIP
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # DETECTAR CONTENIDO
        # ----------------------------------------------------

        contenido = os.listdir(
            carpeta_temp
        )

        print(
            "CONTENIDO UPDATE:",
            contenido
        )

        carpeta_update = carpeta_temp

        # ----------------------------------------------------
        # DETECTAR CARPETA RAÍZ
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # RUTAS DE ACTUALIZACIÓN
        # ----------------------------------------------------

        exe_update = os.path.join(
            carpeta_update,
            "PAPELERA_POS.exe"
        )

        internal_update = os.path.join(
            carpeta_update,
            "_internal"
        )

        version_update = os.path.join(
            carpeta_update,
            "version.txt"
        )

        # ----------------------------------------------------
        # VERIFICAR EXE
        # ----------------------------------------------------

        if not os.path.isfile(
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

        # ----------------------------------------------------
        # VERIFICAR INTERNAL
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # VERIFICAR VERSION.TXT
        # ----------------------------------------------------

        if os.path.isfile(
            version_update
        ):

            try:

                with open(
                    version_update,
                    "r",
                    encoding="utf-8-sig"
                ) as archivo:

                    version_zip = limpiar_version(
                        archivo.read()
                    )

                print(
                    "VERSION DENTRO DEL ZIP:",
                    repr(version_zip)
                )

                if nueva_version:

                    nueva_version_limpia = limpiar_version(
                        nueva_version
                    )

                    if version_zip != nueva_version_limpia:

                        print(
                            "ADVERTENCIA: version.txt del ZIP "
                            "no coincide con nueva_version."
                        )

            except Exception as e:

                print(
                    "ADVERTENCIA leyendo version.txt del ZIP:",
                    repr(e)
                )

        # ----------------------------------------------------
        # RUTAS DESTINO
        # ----------------------------------------------------

        script = os.path.join(
            carpeta_programa,
            "_actualizar_papelera.bat"
        )

        internal_destino = os.path.join(
            carpeta_programa,
            "_internal"
        )

        exe_destino = os.path.join(
            carpeta_programa,
            "PAPELERA_POS.exe"
        )

        version_destino = os.path.join(
            carpeta_programa,
            "version.txt"
        )

        # ----------------------------------------------------
        # SCRIPT BAT
        # ----------------------------------------------------

        contenido_bat = f'''@echo off
setlocal EnableExtensions

echo ==========================================
echo ACTUALIZANDO PAPELERA POS
echo ==========================================
echo.

echo Esperando que cierre PAPELERA_POS...
echo.

:ESPERAR
tasklist /FI "IMAGENAME eq PAPELERA_POS.exe" 2>NUL | find /I "PAPELERA_POS.exe" >NUL

if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto ESPERAR
)

echo Programa cerrado.
echo.

echo ==========================================
echo REEMPLAZANDO ARCHIVOS
echo ==========================================
echo.

echo Eliminando _internal anterior...

if exist "{internal_destino}" (
    rmdir /S /Q "{internal_destino}"
)

if exist "{internal_destino}" (
    echo ERROR: No se pudo eliminar _internal anterior.
    pause
    exit /b 1
)

echo _internal anterior eliminado.
echo.

echo Copiando nuevo _internal...

xcopy "{internal_update}" "{internal_destino}" /E /I /Y /Q >nul

if errorlevel 1 (
    echo ERROR copiando _internal.
    pause
    exit /b 1
)

echo Nuevo _internal copiado.
echo.

echo Copiando PAPELERA_POS.exe...

copy /Y "{exe_update}" "{exe_destino}" >nul

if errorlevel 1 (
    echo ERROR copiando PAPELERA_POS.exe.
    pause
    exit /b 1
)

echo Nuevo PAPELERA_POS.exe copiado.
echo.

echo Actualizando version.txt...

if exist "{version_update}" (

    copy /Y "{version_update}" "{version_destino}" >nul

    if errorlevel 1 (
        echo ERROR copiando version.txt.
        pause
        exit /b 1
    )

    echo version.txt actualizado.

) else (

    echo No se encontro version.txt dentro del ZIP.
)

echo.

echo ==========================================
echo ACTUALIZACION TERMINADA
echo ==========================================
echo.

echo Version instalada:
echo {nueva_version}
echo.

echo Iniciando PAPELERA POS...
echo.

timeout /t 2 /nobreak >nul

start "" "{exe_actual}"

echo Programa iniciado.
echo.

echo Limpiando archivos temporales...

timeout /t 3 /nobreak >nul

rmdir /S /Q "{carpeta_temp}" >nul 2>&1

echo.

echo Eliminando actualizador...

del "%~f0"

endlocal
'''

        # ----------------------------------------------------
        # ESCRIBIR BAT
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # EJECUTAR BAT
        # ----------------------------------------------------

        print(
            "Iniciando actualizador externo..."
        )

        subprocess.Popen(

            [
                "cmd.exe",
                "/c",
                "start",
                "",
                script
            ],

            cwd=carpeta_programa,

            creationflags=(
                subprocess.CREATE_NEW_CONSOLE
            )
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

        if carpeta_temp:

            shutil.rmtree(
                carpeta_temp,
                ignore_errors=True
            )

        return False
