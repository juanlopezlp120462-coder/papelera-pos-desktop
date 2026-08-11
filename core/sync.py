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
            print("SYNC IGNORADO: registro sin datos", item)
            marcar_sincronizado(id_sync)
            continue

        datos = json.loads(item[4])


        try:

            if tabla == "productos":

                payload = datos.copy()
                payload["uuid"] = registro_uuid
                payload["accion"] = accion

                respuesta = requests.post(
                    f"{SERVIDOR}/productos/sync",
                    json=payload,
                    timeout=10
                )

                print("SYNC PRODUCTO")
                print("STATUS:", respuesta.status_code)
                print("RESPUESTA:", respuesta.text)


                if respuesta.status_code in (200,201):

                    marcar_sincronizado(id_sync)


            elif tabla == "ventas":

                respuesta = requests.post(
                    f"{SERVIDOR}/ventas/sync",
                    json={
                        "uuid": registro_uuid,
                        "accion": accion,
                        "datos": datos
                    },
                    timeout=10
                )


                if respuesta.status_code in (200,201):

                    marcar_sincronizado(id_sync)


        except Exception as e:

            print("Error sincronizando:", e)


    return True