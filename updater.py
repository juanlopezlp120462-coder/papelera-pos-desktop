import os
import sys
import time
import shutil
import zipfile
import subprocess
import tempfile


def actualizar():

    if len(sys.argv) < 2:
        return

    zip_path = sys.argv[1]

    carpeta_actual = os.path.dirname(
        sys.executable
    )

    print("Actualizando:", carpeta_actual)

    time.sleep(3)

    carpeta_temp = os.path.join(
        tempfile.gettempdir(),
        "PAPELERA_UPDATE_TEMP"
    )

    if os.path.exists(carpeta_temp):
        shutil.rmtree(carpeta_temp)

    os.makedirs(carpeta_temp)


    print("Extrayendo ZIP")

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(carpeta_temp)


    # Si viene dentro de PAPELERA_POS
    carpeta_extra = os.path.join(
        carpeta_temp,
        "PAPELERA_POS"
    )

    if os.path.exists(carpeta_extra):

        for item in os.listdir(carpeta_extra):

            origen = os.path.join(
                carpeta_extra,
                item
            )

            destino = os.path.join(
                carpeta_temp,
                item
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


        shutil.rmtree(carpeta_extra)


    print("Copiando archivos")

    internal_viejo = os.path.join(
        carpeta_actual,
        "_internal"
    )

    if os.path.exists(internal_viejo):

        print("Borrando _internal viejo")

        shutil.rmtree(
            internal_viejo,
            ignore_errors=True
        )


    for root, dirs, files in os.walk(carpeta_temp):

        destino_root = root.replace(
            carpeta_temp,
            carpeta_actual
        )

        os.makedirs(
            destino_root,
            exist_ok=True
        )


        for archivo in files:

            origen = os.path.join(
                root,
                archivo
            )

            destino = os.path.join(
                destino_root,
                archivo
            )


            shutil.copy2(
                origen,
                destino
            )


    print("Actualización terminada")


    version_nueva = os.path.join(
        carpeta_actual,
        "version.txt"
    )

    version_zip = os.path.join(
        carpeta_temp,
        "version.txt"
    )

    if os.path.exists(version_zip):

        with open(
            version_zip,
            "r",
            encoding="utf-8"
        ) as v:

            nueva_version = v.read().strip()

    else:
        print(
            "ERROR: No se recibió nueva versión para instalar"
        )
        return False


    with open(
        version_nueva,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(nueva_version)


    exe = os.path.join(
        carpeta_actual,
        "PAPELERA_POS.exe"
    )

    subprocess.Popen(
        exe,
        cwd=carpeta_actual
    )


if __name__ == "__main__":
    actualizar()