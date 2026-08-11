import requests
import json

from ui.db import obtener_pendientes, marcar_sincronizado


SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"


def sincronizar():

    pendientes = obtener_pendientes()

    if not pendientes:
        return True


    for item in pendientes:

        id_sync = item[0]
        tabla = item[1]
        registro_uuid = item[2]
        accion = item[3]

        if not item[4]:

            print(
                "SYNC IGNORADO: registro sin datos",
                item
            )

            marcar_sincronizado(id_sync)

            continue


        try:

            datos = json.loads(item[4])


        except Exception as e:

            print(
                "ERROR leyendo datos de sincronizacion:",
                e
            )

            continue


        try:

            # ==========================================
            # PRODUCTOS
            # ==========================================

            if tabla == "productos":

                payload = datos.copy()

                payload["uuid"] = registro_uuid
                payload["accion"] = accion


                respuesta = requests.post(
                    f"{SERVIDOR}/productos/sync",
                    json=payload,
                    timeout=10
                )


                print(
                    "SYNC PRODUCTO",
                    respuesta.status_code,
                    respuesta.text
                )


                if respuesta.status_code in (200, 201):

                    marcar_sincronizado(
                        id_sync
                    )


            # ==========================================
            # VENTAS
            # ==========================================

            elif tabla == "ventas":

                payload = datos.copy()

                payload["uuid"] = registro_uuid
                payload["accion"] = accion


                respuesta = requests.post(
                    f"{SERVIDOR}/ventas/sync",
                    json=payload,
                    timeout=10
                )


                print(
                    "SYNC VENTA",
                    respuesta.status_code,
                    respuesta.text
                )


                if respuesta.status_code in (200, 201):

                    marcar_sincronizado(
                        id_sync
                    )


        except Exception as e:

            print(
                "Error sincronizando:",
                e
            )


    return True