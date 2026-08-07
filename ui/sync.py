import requests
import datetime

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
        SELECT id,tabla,registro,accion
        FROM sincronizacion
        WHERE sincronizado=0
        """
    ).fetchall()


    sincronizadas = 0


    for fila in pendientes:

        sync_id = fila[0]
        tabla = fila[1]
        registro = fila[2]


        if tabla != "ventas":
            continue



        venta = cursor.execute(
            """
            SELECT 
            id,
            fecha,
            total,
            forma_pago,
            cliente_id,
            descuento,
            usuario,
            pago_efectivo,
            pago_transferencia,
            pago_tarjeta,
            pago_cuenta

            FROM ventas
            WHERE id=?
            """,
            (registro,)
        ).fetchone()


        if not venta:
            continue



        detalles = cursor.execute(
            """
            SELECT
            producto,
            cantidad,
            precio,
            subtotal,
            codigo

            FROM detalle_ventas
            WHERE venta_id=?
            """,
            (registro,)
        ).fetchall()



        datos = {

            "venta_id_local": venta[0],

            "fecha": venta[1],

            "total": venta[2],

            "forma_pago": venta[3],

            "cliente_id": venta[4] or 0,

            "descuento": venta[5] or 0,

            "usuario": venta[6],

            "pago_efectivo": venta[7] or 0,

            "pago_transferencia": venta[8] or 0,

            "pago_tarjeta": venta[9] or 0,

            "pago_cuenta": venta[10] or 0,


            "items":[

                {
                    "producto":d[0],
                    "cantidad":d[1],
                    "precio":d[2],
                    "subtotal":d[3],
                    "codigo":d[4]

                }

                for d in detalles

            ]

        }



        try:

            respuesta = requests.post(
                f"{SERVIDOR}/ventas/sync",
                json=datos,
                timeout=10
            )


            if respuesta.status_code in (200,201):

                cursor.execute(
                    """
                    UPDATE sincronizacion
                    SET sincronizado=1
                    WHERE id=?
                    """,
                    (sync_id,)
                )


                sincronizadas += 1



        except Exception:

            pass



    conexion.commit()
    conexion.close()


    return sincronizadas