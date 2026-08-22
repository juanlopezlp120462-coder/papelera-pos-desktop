
import os
import json
import requests

from dotenv import load_dotenv

from ui.db import (
    obtener_pendientes,
    marcar_sincronizado
)


# ============================================================
# CARGAR VARIABLES DE ENTORNO
# ============================================================

import sys

if getattr(sys, "frozen", False):
    # Programa compilado con PyInstaller.
    # .env.pos queda junto al .exe
    BASE_CONFIG = os.path.dirname(
        sys.executable
    )
else:
    # Programa ejecutado desde el proyecto
    BASE_CONFIG = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )

ENV_POS = os.path.join(
    BASE_CONFIG,
    ".env.pos"
)

ENV_NORMAL = os.path.join(
    BASE_CONFIG,
    ".env"
)

# Primero intentar .env.pos
if os.path.exists(ENV_POS):
    load_dotenv(
        ENV_POS,
        override=True
    )

# Si no existe .env.pos, usar .env
elif os.path.exists(ENV_NORMAL):
    load_dotenv(
        ENV_NORMAL,
        override=True
    )


SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    "https://vspfeihawhfdlpeqwxgp.supabase.co"
).rstrip("/")


SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY",
    ""
)


# ============================================================
# HEADERS SUPABASE
# ============================================================

def obtener_headers():

    return {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }


# ============================================================
# URL TABLA SUPABASE
# ============================================================

def url_tabla(tabla):

    return (
        f"{SUPABASE_URL}/rest/v1/{tabla}"
    )


# ============================================================
# VALIDAR CONFIGURACION
# ============================================================

def supabase_configurado():

    if not SUPABASE_URL:

        print(
            "SYNC ERROR: SUPABASE_URL no configurada"
        )

        return False


    if not SUPABASE_KEY:

        print(
            "SYNC ERROR: SUPABASE_KEY no configurada"
        )

        return False


    return True


# ============================================================
# SINCRONIZAR
# ============================================================

def sincronizar():

    # ========================================================
    # VERIFICAR CONFIGURACION
    # ========================================================

    if not supabase_configurado():

        return False


    # ========================================================
    # OBTENER PENDIENTES
    # ========================================================

    pendientes = obtener_pendientes()


    if not pendientes:

        return True


    # ========================================================
    # PROCESAR COLA
    # ========================================================

    for item in pendientes:

        id_sync = item[0]
        tabla = item[1]
        registro_uuid = item[2]
        accion = item[3]
        datos_json = item[4]


        # ====================================================
        # VALIDAR DATOS
        # ====================================================

        if not datos_json:

            print(
                "SYNC IGNORADO: registro sin datos",
                item
            )

            marcar_sincronizado(
                id_sync
            )

            continue


        # ====================================================
        # LEER JSON
        # ====================================================

        try:

            datos = json.loads(
                datos_json
            )

        except Exception as e:

            print(
                "ERROR leyendo datos de sincronizacion:",
                e
            )

            continue


        # ====================================================
        # ARCHIVAR VENTAS DEL DIA
        # ====================================================

        if (
            tabla == "ventas"
            and accion == "archivar_hoy"
        ):

            print(
                "SYNC IGNORADO: "
                "archivar_hoy ya fue enviado "
                "por Dashboard",
                registro_uuid
            )

            marcar_sincronizado(
                id_sync
            )

            continue


        # ====================================================
        # PRODUCTOS
        # ====================================================

        if tabla == "productos":

            try:

                payload = datos.copy()


                payload["uuid"] = (
                    registro_uuid
                )


                # No necesitamos enviar
                # "accion" a Supabase.
                #
                # La accion se utiliza
                # solamente para decidir
                # INSERT / UPDATE.

                payload.pop(
                    "accion",
                    None
                )


                print(
                    "SYNC PRODUCTO ENVIANDO:",
                    json.dumps(
                        payload,
                        ensure_ascii=False
                    )
                )


                # =================================================
                # BUSCAR SI YA EXISTE
                # =================================================

                respuesta_busqueda = requests.get(

                    url_tabla(
                        "productos"
                    ),

                    params={
                        "uuid": f"eq.{registro_uuid}"
                    },

                    headers=obtener_headers(),

                    timeout=10
                )


                print(
                    "SYNC PRODUCTO BUSQUEDA:",
                    respuesta_busqueda.status_code,
                    respuesta_busqueda.text
                )


                # =================================================
                # ERROR DE CONEXION / SERVIDOR
                # =================================================

                if respuesta_busqueda.status_code != 200:

                    print(
                        "SYNC PRODUCTO ERROR BUSQUEDA:",
                        respuesta_busqueda.status_code
                    )

                    continue


                existentes = (
                    respuesta_busqueda.json()
                )


                # =================================================
                # DELETE
                # =================================================

                if accion == "DELETE":

                    if existentes:

                        respuesta = requests.delete(

                            url_tabla(
                                "productos"
                            ),

                            params={
                                "uuid": f"eq.{registro_uuid}"
                            },

                            headers=obtener_headers(),

                            timeout=10
                        )


                        print(
                            "SYNC PRODUCTO DELETE:",
                            respuesta.status_code,
                            respuesta.text
                        )


                        if respuesta.status_code in (
                            200,
                            204
                        ):

                            marcar_sincronizado(
                                id_sync
                            )

                    else:

                        # Ya no existe.
                        marcar_sincronizado(
                            id_sync
                        )


                    continue


                # =================================================
                # UPDATE
                # =================================================

                if existentes:

                    respuesta = requests.patch(

                        url_tabla(
                            "productos"
                        ),

                        params={
                            "uuid": f"eq.{registro_uuid}"
                        },

                        headers=obtener_headers(),

                        json=payload,

                        timeout=10
                    )


                    print(
                        "SYNC PRODUCTO UPDATE:",
                        respuesta.status_code,
                        respuesta.text
                    )


                # =================================================
                # INSERT
                # =================================================

                else:

                    respuesta = requests.post(

                        url_tabla(
                            "productos"
                        ),

                        headers=obtener_headers(),

                        json=payload,

                        timeout=10
                    )


                    print(
                        "SYNC PRODUCTO INSERT:",
                        respuesta.status_code,
                        respuesta.text
                    )


                # =================================================
                # CONFIRMAR
                # =================================================

                if respuesta.status_code in (
                    200,
                    201,
                    204
                ):

                    marcar_sincronizado(
                        id_sync
                    )

                else:

                    print(
                        "SYNC PRODUCTO ERROR:",
                        respuesta.status_code
                    )


            except requests.exceptions.RequestException as e:

                print(
                    "SYNC PRODUCTO SIN INTERNET:",
                    e
                )

                continue


            except Exception as e:

                print(
                    "SYNC PRODUCTO ERROR:",
                    e
                )

                continue


        # ========================================================
        # VENTAS
        # ========================================================

        elif tabla == "ventas":

            try:

                payload = datos.copy()


                payload["uuid"] = (
                    registro_uuid
                )


                # =================================================
                # VALIDAR ITEMS
                # =================================================

                items = payload.get(
                    "items"
                )


                if not items:

                    print(
                        "SYNC VENTA ERROR: "
                        "la venta no tiene items:",
                        registro_uuid
                    )

                    # No marcar.
                    #
                    # Queda pendiente para
                    # poder revisarla.

                    continue


                payload["items"] = items


                # =================================================
                # DEBUG
                # =================================================

                print(
                    "SYNC VENTA ENVIANDO:",
                    json.dumps(
                        payload,
                        ensure_ascii=False
                    )
                )


                # =================================================
                # SUPABASE
                #
                # Las ventas tienen dos tablas:
                #
                # ventas
                # detalle_ventas
                #
                # Primero verificamos si la cabecera
                # ya existe.
                # =================================================

                respuesta_busqueda = requests.get(

                    url_tabla(
                        "ventas"
                    ),

                    params={
                        "uuid": f"eq.{registro_uuid}"
                    },

                    headers=obtener_headers(),

                    timeout=10
                )


                print(
                    "SYNC VENTA BUSQUEDA:",
                    respuesta_busqueda.status_code,
                    respuesta_busqueda.text
                )


                if respuesta_busqueda.status_code != 200:

                    print(
                        "SYNC VENTA ERROR BUSQUEDA:",
                        respuesta_busqueda.status_code
                    )

                    continue


                existentes = (
                    respuesta_busqueda.json()
                )


                # =================================================
                # CREAR / ACTUALIZAR CABECERA
                # =================================================

                datos_venta = payload.copy()


                # Sacar items porque la tabla
                # ventas no tiene esa columna.

                datos_venta.pop(
                    "items",
                    None
                )


                # Sacar accion porque tampoco
                # es una columna de ventas.

                datos_venta.pop(
                    "accion",
                    None
                )


                if existentes:

                    respuesta_venta = requests.patch(

                        url_tabla(
                            "ventas"
                        ),

                        params={
                            "uuid": f"eq.{registro_uuid}"
                        },

                        headers=obtener_headers(),

                        json=datos_venta,

                        timeout=10
                    )


                    print(
                        "SYNC VENTA UPDATE:",
                        respuesta_venta.status_code,
                        respuesta_venta.text
                    )


                else:

                    respuesta_venta = requests.post(

                        url_tabla(
                            "ventas"
                        ),

                        headers=obtener_headers(),

                        json=datos_venta,

                        timeout=10
                    )


                    print(
                        "SYNC VENTA INSERT:",
                        respuesta_venta.status_code,
                        respuesta_venta.text
                    )


                if respuesta_venta.status_code not in (
                    200,
                    201
                ):

                    print(
                        "SYNC VENTA ERROR CABECERA:",
                        respuesta_venta.status_code
                    )

                    continue


                # =================================================
                # OBTENER ID DE LA VENTA
                # =================================================

                respuesta_id = requests.get(

                    url_tabla(
                        "ventas"
                    ),

                    params={
                        "uuid": f"eq.{registro_uuid}",
                        "select": "id"
                    },

                    headers=obtener_headers(),

                    timeout=10
                )


                if respuesta_id.status_code != 200:

                    print(
                        "SYNC VENTA ERROR OBTENIENDO ID:",
                        respuesta_id.status_code
                    )

                    continue


                ventas_encontradas = (
                    respuesta_id.json()
                )


                if not ventas_encontradas:

                    print(
                        "SYNC VENTA ERROR: "
                        "no se encontró ID remoto"
                    )

                    continue


                venta_id = (
                    ventas_encontradas[0]["id"]
                )


                # =================================================
                # BORRAR DETALLES ANTERIORES
                #
                # Esto evita duplicar items si
                # una venta se reintenta.
                # =================================================

                respuesta_delete_detalles = requests.delete(

                    url_tabla(
                        "detalle_ventas"
                    ),

                    params={
                        "venta_id": f"eq.{venta_id}"
                    },

                    headers=obtener_headers(),

                    timeout=10
                )


                if respuesta_delete_detalles.status_code not in (
                    200,
                    204
                ):

                    print(
                        "SYNC VENTA ERROR BORRANDO DETALLES:",
                        respuesta_delete_detalles.status_code,
                        respuesta_delete_detalles.text
                    )

                    continue


                # =================================================
                # INSERTAR ITEMS
                # =================================================

                for item_venta in items:

                    detalle = {

                        "venta_id": venta_id,

                        "producto": item_venta.get(
                            "producto",
                            ""
                        ),

                        "cantidad": int(
                            item_venta.get(
                                "cantidad",
                                0
                            )
                        ),

                        "precio": float(
                            item_venta.get(
                                "precio",
                                0
                            )
                        ),

                        "subtotal": float(
                            item_venta.get(
                                "subtotal",
                                0
                            )
                        ),

                        "codigo": item_venta.get(
                            "codigo",
                            ""
                        )
                    }


                    respuesta_detalle = requests.post(

                        url_tabla(
                            "detalle_ventas"
                        ),

                        headers=obtener_headers(),

                        json=detalle,

                        timeout=10
                    )


                    if respuesta_detalle.status_code not in (
                        200,
                        201
                    ):

                        print(
                            "SYNC VENTA ERROR DETALLE:",
                            respuesta_detalle.status_code,
                            respuesta_detalle.text
                        )

                        break


                else:

                    # =================================================
                    # TODO CORRECTO
                    # =================================================

                    marcar_sincronizado(
                        id_sync
                    )

                    print(
                        "SYNC VENTA OK:",
                        registro_uuid
                    )

                    continue


                # Si salió del for por error,
                # NO marcar sincronizado.

                continue


            except requests.exceptions.RequestException as e:

                print(
                    "SYNC VENTA SIN INTERNET:",
                    e
                )

                continue


            except Exception as e:

                print(
                    "SYNC VENTA ERROR:",
                    e
                )

                continue


        # ========================================================
        # OTRAS TABLAS
        # ========================================================

        else:

            print(
                "SYNC IGNORADO: tabla no soportada:",
                tabla
            )

            # No marcar.
            #
            # Así no perdemos información.

            continue


    return True
