import requests

from ui.db import create_connection, init_db


SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"


def hay_internet():

    try:

        requests.get(
            SERVIDOR,
            timeout=5
        )

        return True

    except Exception:

        return False


def sincronizar_ventas():

    init_db()

    if not hay_internet():

        return 0


    conexion = create_connection()
    cursor = conexion.cursor()


    pendientes = cursor.execute(
        """
        SELECT
            id,
            tabla,
            registro,
            registro_uuid,
            accion,
            datos
        FROM sincronizacion
        WHERE sincronizado=0
        AND tabla='ventas'
        ORDER BY id
        """
    ).fetchall()


    sincronizadas = 0


    for fila in pendientes:

        sync_id = fila[0]
        registro_uuid = fila[3]
        datos_json = fila[5]


        if not registro_uuid:

            print(
                "Venta sin UUID:",
                fila[2]
            )

            continue


        if not datos_json:

            print(
                "Venta sin datos:",
                fila[2]
            )

            continue


        try:

            import json

            venta = json.loads(datos_json)


            # ==================================
            # AGREGAR UUID AL ENVÍO
            # ==================================

            datos = {

                "uuid": registro_uuid,

                "fecha": venta.get("fecha"),

                "total": venta.get("total", 0),

                "forma_pago": venta.get(
                    "forma_pago",
                    "EFECTIVO"
                ),

                "cliente_id": venta.get(
                    "cliente_id"
                ),

                "descuento": venta.get(
                    "descuento",
                    0
                ),

                "usuario": venta.get(
                    "usuario",
                    "Administrador"
                ),

                "pago_efectivo": venta.get(
                    "pago_efectivo",
                    0
                ),

                "pago_transferencia": venta.get(
                    "pago_transferencia",
                    0
                ),

                "pago_tarjeta": venta.get(
                    "pago_tarjeta",
                    0
                ),

                "pago_cuenta": venta.get(
                    "pago_cuenta",
                    0
                ),

                "items": venta.get(
                    "items",
                    []
                )

            }


            if not datos["items"]:

                print(
                    "Venta sin items:",
                    fila[2]
                )

                continue


            # ==================================
            # ENVIAR AL SERVIDOR
            # ==================================

            respuesta = requests.post(

                f"{SERVIDOR}/ventas/sync",

                json=datos,

                timeout=15

            )


            # ==================================
            # VENTA SINCRONIZADA
            # ==================================

            if respuesta.status_code in (200, 201):

                resultado = respuesta.json()


                cursor.execute(
                    """
                    UPDATE sincronizacion
                    SET sincronizado=1
                    WHERE id=?
                    """,
                    (
                        sync_id,
                    )
                )


                sincronizadas += 1


                if resultado.get("actualizada"):

                    print(
                        "Venta actualizada en servidor:",
                        registro_uuid
                    )

                elif resultado.get("creada"):

                    print(
                        "Venta creada en servidor:",
                        registro_uuid
                    )

                elif resultado.get("duplicada"):

                    print(
                        "Venta duplicada en servidor:",
                        registro_uuid
                    )

                else:

                    print(
                        "Venta sincronizada:",
                        registro_uuid
                    )


            else:

                print(
                    "Error sincronizando venta:",
                    respuesta.status_code,
                    respuesta.text
                )


        except Exception as e:

            print(
                "Error sincronizando venta:",
                e
            )


    conexion.commit()

    conexion.close()


    return sincronizadas
def sincronizar():
    sincronizar_ventas()