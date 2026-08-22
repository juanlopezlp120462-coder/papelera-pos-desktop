import sys
import os
import json
import threading
from datetime import datetime

from dotenv import load_dotenv
from supabase import create_client

from ui.db import (
    create_connection,
    init_db,
    archivar_ventas
)


# =========================================================
# SUPABASE
# =========================================================

if getattr(sys, "frozen", False):

    # =====================================================
    # INSTALACION COMPILADA
    # =====================================================

    BASE_DIR = os.path.dirname(
        os.path.abspath(
            sys.executable
        )
    )

    # Primero buscar junto al EXE
    ENV_FILE = os.path.join(
        BASE_DIR,
        ".env.pos"
    )

    # PyInstaller 6 puede colocar los datas dentro
    # de _internal.
    if not os.path.isfile(ENV_FILE):

        ENV_FILE = os.path.join(
            BASE_DIR,
            "_internal",
            ".env.pos"
        )

else:

    # =====================================================
    # EJECUCION DESDE PYTHON
    # =====================================================

    BASE_DIR = os.path.dirname(
        os.path.abspath(__file__)
    )

    ENV_FILE = os.path.join(
        BASE_DIR,
        ".env.pos"
    )


# =========================================================
# CARGAR CONFIGURACION
# =========================================================

load_dotenv(
    dotenv_path=ENV_FILE
)


SUPABASE_URL = os.getenv(
    "SUPABASE_URL"
)

SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY"
)


# =========================================================
# HEADERS SUPABASE
# =========================================================

def obtener_headers():

    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }



# =========================================================
# VERIFICAR CONFIGURACION
# =========================================================

if not os.path.isfile(ENV_FILE):

    raise RuntimeError(
        "No se encontro .env.pos en: "
        + ENV_FILE
    )


if not SUPABASE_URL or not SUPABASE_KEY:

    raise RuntimeError(
        "Faltan SUPABASE_URL o SUPABASE_KEY en: "
        + ENV_FILE
    )


# =========================================================
# CREAR CLIENTE SUPABASE
# =========================================================

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================================================
# INTERNET / SUPABASE
# =========================================================

def hay_internet():

    try:

        supabase.table(
            "productos"
        ).select(
            "id"
        ).limit(
            1
        ).execute()

        return True

    except Exception as e:

        print(
            "Sin conexión con Supabase:",
            e
        )

        return False


# =========================================================
# 1. SUBIDA DE PRODUCTOS
#    SQLITE -> SUPABASE
# =========================================================

def sincronizar_productos():

    init_db()

    if not hay_internet():
        return 0

    conexion = create_connection()
    cursor = conexion.cursor()

    pendientes = cursor.execute(
        """
        SELECT
            id,
            registro_uuid,
            accion,
            datos
        FROM sincronizacion
        WHERE sincronizado=0
          AND tabla='productos'
        ORDER BY id
        """
    ).fetchall()

    sincronizados = 0

    for fila in pendientes:

        sync_id = fila[0]
        producto_uuid = fila[1]
        accion = fila[2]
        datos_json = fila[3]

        if not producto_uuid:

            print(
                "Producto sin UUID:",
                sync_id
            )

            continue

        try:

            # =================================================
            # ELIMINAR
            # =================================================

            if accion == "eliminar":

                respuesta = (
                    supabase
                    .table("productos")
                    .delete()
                    .eq(
                        "uuid",
                        producto_uuid
                    )
                    .execute()
                )

                cursor.execute(
                    """
                    UPDATE sincronizacion
                    SET sincronizado=1
                    WHERE id=?
                    """,
                    (sync_id,)
                )

                sincronizados += 1

                print(
                    "Producto eliminado de Supabase:",
                    producto_uuid
                )

                continue

            # =================================================
            # CREAR / ACTUALIZAR
            # =================================================

            if not datos_json:

                print(
                    "Producto sin datos:",
                    producto_uuid
                )

                continue

            producto = json.loads(
                datos_json
            )

            datos = {

                "uuid": producto_uuid,

                "codigo_barras": producto.get(
                    "codigo_barras",
                    ""
                ),

                "nombre": producto.get(
                    "nombre",
                    ""
                ),

                "categoria": producto.get(
                    "categoria",
                    "General"
                ),

                "precio_compra": producto.get(
                    "precio_compra",
                    0
                ),

                "precio_venta": producto.get(
                    "precio_venta",
                    0
                ),

                "stock": producto.get(
                    "stock",
                    0
                ),

                "stock_minimo": producto.get(
                    "stock_minimo",
                    5
                )
            }

            (
                supabase
                .table("productos")
                .upsert(
                    datos,
                    on_conflict="uuid"
                )
                .execute()
            )

            cursor.execute(
                """
                UPDATE sincronizacion
                SET sincronizado=1
                WHERE id=?
                """,
                (sync_id,)
            )

            sincronizados += 1

            print(
                "Producto sincronizado:",
                producto_uuid
            )

        except Exception as e:

            print(
                "Error sincronizando producto:",
                e
            )

    conexion.commit()
    conexion.close()

    return sincronizados


# =========================================================
# 2. DESCARGA DE PRODUCTOS
#    SUPABASE -> SQLITE
# =========================================================

def descargar_productos():

    init_db()

    if not hay_internet():
        return 0

    conexion = None

    try:

        respuesta = (
            supabase
            .table("productos")
            .select("*")
            .execute()
        )

        productos_remotos = (
            respuesta.data or []
        )

        conexion = create_connection()
        cursor = conexion.cursor()

        actualizados = 0
        uuids_remotos = set()

        for prod in productos_remotos:

            uuid_prod = prod.get(
                "uuid"
            )

            if not uuid_prod:
                continue

            uuids_remotos.add(
                uuid_prod
            )

            existente = cursor.execute(
                """
                SELECT id
                FROM productos
                WHERE uuid=?
                """,
                (uuid_prod,)
            ).fetchone()

            datos = (
                prod.get("codigo_barras", ""),
                prod.get("nombre", ""),
                prod.get("categoria", "General"),
                prod.get("precio_compra", 0),
                prod.get("precio_venta", 0),
                prod.get("stock", 0),
                prod.get("stock_minimo", 5),
                uuid_prod
            )

            if existente:

                cursor.execute(
                    """
                    UPDATE productos
                    SET
                        codigo_barras=?,
                        nombre=?,
                        categoria=?,
                        precio_compra=?,
                        precio_venta=?,
                        stock=?,
                        stock_minimo=?
                    WHERE uuid=?
                    """,
                    datos
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO productos
                    (
                        uuid,
                        codigo_barras,
                        nombre,
                        categoria,
                        precio_compra,
                        precio_venta,
                        stock,
                        stock_minimo
                    )
                    VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        uuid_prod,
                        prod.get("codigo_barras", ""),
                        prod.get("nombre", ""),
                        prod.get("categoria", "General"),
                        prod.get("precio_compra", 0),
                        prod.get("precio_venta", 0),
                        prod.get("stock", 0),
                        prod.get("stock_minimo", 5)
                    )
                )

            actualizados += 1

        # =====================================================
        # ELIMINAR PRODUCTOS REMOTOS QUE YA NO EXISTEN
        # =====================================================

        productos_locales = cursor.execute(
            """
            SELECT
                id,
                uuid,
                nombre
            FROM productos
            """
        ).fetchall()

        eliminados = 0

        for producto_local in productos_locales:

            id_local = producto_local[0]
            uuid_local = producto_local[1]
            nombre_local = producto_local[2]

            if not uuid_local:
                continue

            if uuid_local in uuids_remotos:
                continue

            pendiente = cursor.execute(
                """
                SELECT 1
                FROM sincronizacion
                WHERE tabla='productos'
                  AND registro_uuid=?
                  AND sincronizado=0
                LIMIT 1
                """,
                (uuid_local,)
            ).fetchone()

            if pendiente:

                print(
                    "Producto pendiente:",
                    uuid_local,
                    nombre_local
                )

                continue

            cursor.execute(
                """
                DELETE FROM productos
                WHERE id=?
                """,
                (id_local,)
            )

            eliminados += 1

        conexion.commit()
        conexion.close()

        print(
            "PRODUCTOS:",
            actualizados,
            "| ELIMINADOS:",
            eliminados
        )

        return actualizados + eliminados

    except Exception as e:

        print(
            "Error descargando productos:",
            repr(e)
        )

        if conexion:

            try:
                conexion.rollback()
                conexion.close()
            except Exception:
                pass

        return 0


# =========================================================
# 3. SUBIDA DE VENTAS
#    SQLITE -> SUPABASE
# =========================================================

def sincronizar_ventas():

    init_db()

    if not hay_internet():
        return 0

    conexion = create_connection()
    cursor = conexion.cursor()

    # =====================================================
    # ASEGURAR COLUMNAS
    # =====================================================

    columnas = [
        fila[1]
        for fila in cursor.execute(
            "PRAGMA table_info(ventas)"
        ).fetchall()
    ]

    if "tipo" not in columnas:

        cursor.execute(
            """
            ALTER TABLE ventas
            ADD COLUMN tipo TEXT
            """
        )

    if "origen" not in columnas:

        cursor.execute(
            """
            ALTER TABLE ventas
            ADD COLUMN origen TEXT
            """
        )

    if "pedido_id" not in columnas:

        cursor.execute(
            """
            ALTER TABLE ventas
            ADD COLUMN pedido_id INTEGER
            """
        )

    conexion.commit()

    pendientes = cursor.execute(
        """
        SELECT
            id,
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
        registro_uuid = fila[1]
        accion = fila[2]
        datos_json = fila[3]

        if not registro_uuid:
            continue

        try:

            if accion == "eliminar":

                (
                    supabase
                    .table("ventas")
                    .delete()
                    .eq(
                        "uuid",
                        registro_uuid
                    )
                    .execute()
                )

                cursor.execute(
                    """
                    UPDATE sincronizacion
                    SET sincronizado=1
                    WHERE id=?
                    """,
                    (sync_id,)
                )

                sincronizadas += 1

                continue

            if not datos_json:

                print(
                    "Venta sin datos:",
                    registro_uuid
                )

                continue

            venta = json.loads(
                datos_json
            )

            # =================================================
            # RECUPERAR CLASIFICACIÓN
            # =================================================

            tipo = str(
                venta.get(
                    "tipo",
                    ""
                ) or ""
            ).strip().upper()

            origen = str(
                venta.get(
                    "origen",
                    ""
                ) or ""
            ).strip().upper()

            pedido_id = venta.get(
                "pedido_id"
            )

            if (
                not tipo
                or not origen
                or pedido_id is None
            ):

                venta_local = cursor.execute(
                    """
                    SELECT
                        tipo,
                        origen,
                        pedido_id
                    FROM ventas
                    WHERE uuid=?
                    LIMIT 1
                    """,
                    (registro_uuid,)
                ).fetchone()

                if venta_local:

                    if not tipo:
                        tipo = str(
                            venta_local[0] or ""
                        ).strip().upper()

                    if not origen:
                        origen = str(
                            venta_local[1] or ""
                        ).strip().upper()

                    if pedido_id is None:
                        pedido_id = venta_local[2]

            if (
                tipo == "PEDIDO"
                or origen == "PEDIDO"
                or pedido_id is not None
            ):

                tipo = "PEDIDO"
                origen = "PEDIDO"

            else:

                tipo = "VENTA"

                if not origen:
                    origen = "VENTA"

            # =================================================
            # DATOS DE VENTA
            # =================================================

            datos = {

                "uuid": registro_uuid,

                "fecha": venta.get(
                    "fecha"
                ),

                "total": venta.get(
                    "total",
                    0
                ),

                "forma_pago": venta.get(
                    "forma_pago",
                    "EFECTIVO"
                ),

                "cliente_id": venta.get(
                    "cliente_id"
                ),

                "estado": venta.get(
                    "estado",
                    "ACTIVA"
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

                "tipo": tipo,

                "origen": origen,

                "pedido_id": pedido_id
            }

            items = venta.get(
                "items",
                []
            )

            if not items:

                print(
                    "Venta sin items:",
                    registro_uuid
                )

                continue

            # =================================================
            # SUBIR VENTA
            # =================================================

            respuesta = (
                supabase
                .table("ventas")
                .upsert(
                    datos,
                    on_conflict="uuid"
                )
                .select("id,uuid")
                .execute()
            )

            if not respuesta.data:

                print(
                    "Supabase no devolvió la venta:",
                    registro_uuid
                )

                continue

            venta_remota_id = (
                respuesta.data[0]["id"]
            )

            # =================================================
            # DETALLES
            # =================================================

            (
                supabase
                .table("detalle_ventas")
                .delete()
                .eq(
                    "venta_id",
                    venta_remota_id
                )
                .execute()
            )

            detalles = []

            for item in items:

                detalles.append({

                    "venta_id":
                        venta_remota_id,

                    "producto":
                        item.get(
                            "producto",
                            ""
                        ),

                    "cantidad":
                        int(
                            item.get(
                                "cantidad",
                                0
                            ) or 0
                        ),

                    "precio":
                        float(
                            item.get(
                                "precio",
                                0
                            ) or 0
                        ),

                    "subtotal":
                        float(
                            item.get(
                                "subtotal",
                                0
                            ) or 0
                        ),

                    "codigo":
                        item.get(
                            "codigo",
                            ""
                        ) or ""
                })

            if detalles:

                (
                    supabase
                    .table("detalle_ventas")
                    .insert(detalles)
                    .execute()
                )

            # =================================================
            # MARCAR SINCRONIZADO
            # =================================================

            cursor.execute(
                """
                UPDATE sincronizacion
                SET sincronizado=1
                WHERE id=?
                """,
                (sync_id,)
            )

            sincronizadas += 1

            print(
                "Venta sincronizada:",
                registro_uuid,
                "TIPO:",
                tipo
            )

        except Exception as e:

            print(
                "Error sincronizando venta:",
                repr(e)
            )

    conexion.commit()
    conexion.close()

    return sincronizadas
# =========================================================
# ELIMINAR VENTAS LOCALES QUE YA NO EXISTEN EN SUPABASE
# =========================================================

def eliminar_ventas_locales_que_no_existen_en_supabase(
    ventas_remotas
):

    conexion = None

    try:

        conexion = create_connection()
        cursor = conexion.cursor()

        # UUID de todas las ventas que realmente existen
        # actualmente en Supabase
        uuids_remotos = {
            str(v.get("uuid"))
            for v in (ventas_remotas or [])
            if v.get("uuid")
        }

        ventas_locales = cursor.execute(
            """
            SELECT
                id,
                uuid
            FROM ventas
            WHERE uuid IS NOT NULL
            """
        ).fetchall()

        eliminadas = 0

        for venta_id, venta_uuid in ventas_locales:

            venta_uuid = str(venta_uuid)

            # Si existe remotamente, se conserva
            if venta_uuid in uuids_remotos:
                continue

            # =============================================
            # BORRAR DETALLES PRIMERO
            # =============================================

            cursor.execute(
                """
                DELETE FROM detalle_ventas
                WHERE venta_id=?
                """,
                (venta_id,)
            )

            # =============================================
            # BORRAR VENTA
            # =============================================

            cursor.execute(
                """
                DELETE FROM ventas
                WHERE id=?
                """,
                (venta_id,)
            )

            eliminadas += 1

            print(
                "VENTA LOCAL ELIMINADA - YA NO EXISTE EN SUPABASE:",
                venta_uuid
            )

        conexion.commit()

        print(
            "VENTAS LOCALES ELIMINADAS:",
            eliminadas
        )

        return eliminadas

    except Exception as e:

        print(
            "Error eliminando ventas locales obsoletas:",
            repr(e)
        )

        if conexion:

            try:
                conexion.rollback()
            except Exception:
                pass

        return 0

    finally:

        if conexion:

            try:
                conexion.close()
            except Exception:
                pass

# =========================================================
# 4. DESCARGA DE VENTAS
#    SUPABASE -> SQLITE
# =========================================================

def descargar_ventas():

    init_db()

    if not hay_internet():
        return 0

    conexion = None

    try:

        respuesta = (
            supabase
            .table("ventas")
            .select("*")
            .execute()
        )

        ventas_remotas = (
            respuesta.data or []
        )
        # =================================================
        # ELIMINAR LOCALES QUE YA NO EXISTEN EN SUPABASE
        # =================================================

        eliminar_ventas_locales_que_no_existen_en_supabase(
            ventas_remotas
        )
        conexion = create_connection()
        cursor = conexion.cursor()

        # =====================================================
        # COLUMNAS
        # =====================================================

        columnas = [
            fila[1]
            for fila in cursor.execute(
                "PRAGMA table_info(ventas)"
            ).fetchall()
        ]

        if "tipo" not in columnas:

            cursor.execute(
                """
                ALTER TABLE ventas
                ADD COLUMN tipo TEXT
                """
            )

        if "origen" not in columnas:

            cursor.execute(
                """
                ALTER TABLE ventas
                ADD COLUMN origen TEXT
                """
            )

        if "pedido_id" not in columnas:

            cursor.execute(
                """
                ALTER TABLE ventas
                ADD COLUMN pedido_id INTEGER
                """
            )

        conexion.commit()

        # =====================================================
        # ARQUEOS LOCALES
        # =====================================================

        ultimos_arqueos = {}

        filas_arqueos = cursor.execute(
            """
            SELECT fecha
            FROM arqueos
            WHERE fecha IS NOT NULL
            ORDER BY fecha ASC
            """
        ).fetchall()

        for fila in filas_arqueos:

            fecha = str(
                fila[0]
            )

            ultimos_arqueos[
                fecha[:10]
            ] = fecha

        actualizadas = 0

        for venta in ventas_remotas:

            uuid_venta = venta.get(
                "uuid"
            )

            if not uuid_venta:
                continue

            fecha_venta = venta.get(
                "fecha"
            )

            if not fecha_venta:
                continue

            fecha_venta = str(
                fecha_venta
            )

            # =================================================
            # ESTADO
            # =================================================

            estado_remoto = str(
                venta.get(
                    "estado",
                    "ACTIVA"
                ) or "ACTIVA"
            ).strip().upper()

            estado_final = (
                estado_remoto
            )

            arqueo_fecha = (
                ultimos_arqueos.get(
                    fecha_venta[:10]
                )
            )

            if (
                estado_remoto == "ACTIVA"
                and arqueo_fecha
            ):

                try:

                    fecha_v = datetime.fromisoformat(
                        fecha_venta.replace(
                            "Z",
                            ""
                        )
                    )

                    fecha_a = datetime.fromisoformat(
                        str(
                            arqueo_fecha
                        ).replace(
                            "T",
                            " "
                        )
                    )

                    if fecha_v <= fecha_a:

                        estado_final = (
                            "ARCHIVADA"
                        )

                except Exception as e:

                    print(
                        "Error comparando fechas:",
                        e
                    )

            # =================================================
            # TIPO
            # =================================================

            tipo_remoto = str(
                venta.get(
                    "tipo",
                    ""
                ) or ""
            ).strip().upper()

            origen_remoto = str(
                venta.get(
                    "origen",
                    ""
                ) or ""
            ).strip().upper()

            pedido_id_remoto = (
                venta.get(
                    "pedido_id"
                )
            )

            if (
                tipo_remoto == "PEDIDO"
                or origen_remoto == "PEDIDO"
                or pedido_id_remoto is not None
            ):

                tipo_final = "PEDIDO"
                origen_final = "PEDIDO"

            else:

                tipo_final = "VENTA"

                origen_final = (
                    origen_remoto
                    if origen_remoto
                    else "VENTA"
                )

            # =================================================
            # EXISTENCIA LOCAL
            # =================================================

            existente = cursor.execute(
                """
                SELECT
                    id,
                    tipo,
                    origen,
                    pedido_id
                FROM ventas
                WHERE uuid=?
                """,
                (uuid_venta,)
            ).fetchone()

            if existente:

                venta_id_local = existente[0]

                tipo_local = str(
                    existente[1] or ""
                ).strip().upper()

                origen_local = str(
                    existente[2] or ""
                ).strip().upper()

                pedido_id_local = (
                    existente[3]
                )

                if (
                    tipo_local == "PEDIDO"
                    or origen_local == "PEDIDO"
                    or pedido_id_local is not None
                ):

                    tipo_final = "PEDIDO"
                    origen_final = "PEDIDO"

                    if pedido_id_remoto is None:

                        pedido_id_remoto = (
                            pedido_id_local
                        )

                cursor.execute(
                    """
                    UPDATE ventas
                    SET
                        fecha=?,
                        total=?,
                        forma_pago=?,
                        cliente_id=?,
                        estado=?,
                        descuento=?,
                        usuario=?,
                        pago_efectivo=?,
                        pago_transferencia=?,
                        pago_tarjeta=?,
                        pago_cuenta=?,
                        tipo=?,
                        origen=?,
                        pedido_id=?
                    WHERE id=?
                    """,
                    (
                        fecha_venta,
                        venta.get("total", 0),
                        venta.get(
                            "forma_pago",
                            "EFECTIVO"
                        ),
                        venta.get(
                            "cliente_id"
                        ),
                        estado_final,
                        venta.get(
                            "descuento",
                            0
                        ),
                        venta.get(
                            "usuario",
                            "Administrador"
                        ),
                        venta.get(
                            "pago_efectivo",
                            0
                        ),
                        venta.get(
                            "pago_transferencia",
                            0
                        ),
                        venta.get(
                            "pago_tarjeta",
                            0
                        ),
                        venta.get(
                            "pago_cuenta",
                            0
                        ),
                        tipo_final,
                        origen_final,
                        pedido_id_remoto,
                        venta_id_local
                    )
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO ventas
                    (
                        uuid,
                        fecha,
                        total,
                        forma_pago,
                        cliente_id,
                        estado,
                        descuento,
                        usuario,
                        pago_efectivo,
                        pago_transferencia,
                        pago_tarjeta,
                        pago_cuenta,
                        tipo,
                        origen,
                        pedido_id
                    )
                    VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        uuid_venta,
                        fecha_venta,
                        venta.get(
                            "total",
                            0
                        ),
                        venta.get(
                            "forma_pago",
                            "EFECTIVO"
                        ),
                        venta.get(
                            "cliente_id"
                        ),
                        estado_final,
                        venta.get(
                            "descuento",
                            0
                        ),
                        venta.get(
                            "usuario",
                            "Administrador"
                        ),
                        venta.get(
                            "pago_efectivo",
                            0
                        ),
                        venta.get(
                            "pago_transferencia",
                            0
                        ),
                        venta.get(
                            "pago_tarjeta",
                            0
                        ),
                        venta.get(
                            "pago_cuenta",
                            0
                        ),
                        tipo_final,
                        origen_final,
                        pedido_id_remoto
                    )
                )

                venta_id_local = cursor.execute(
                    """
                    SELECT id
                    FROM ventas
                    WHERE uuid=?
                    """,
                    (uuid_venta,)
                ).fetchone()[0]

            # =================================================
            # DESCARGAR DETALLES
            # =================================================

            venta_remota_id = venta.get(
                "id"
            )

            if venta_remota_id:

                detalles_resp = (
                    supabase
                    .table("detalle_ventas")
                    .select("*")
                    .eq(
                        "venta_id",
                        venta_remota_id
                    )
                    .execute()
                )

                detalles = (
                    detalles_resp.data or []
                )

                if detalles:

                    existe_detalle = cursor.execute(
                        """
                        SELECT 1
                        FROM detalle_ventas
                        WHERE venta_id=?
                        LIMIT 1
                        """,
                        (venta_id_local,)
                    ).fetchone()

                    if not existe_detalle:

                        for detalle in detalles:

                            cursor.execute(
                                """
                                INSERT INTO detalle_ventas
                                (
                                    venta_id,
                                    producto,
                                    cantidad,
                                    precio,
                                    subtotal,
                                    codigo
                                )
                                VALUES
                                (?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    venta_id_local,
                                    detalle.get(
                                        "producto",
                                        ""
                                    ),
                                    int(
                                        detalle.get(
                                            "cantidad",
                                            0
                                        ) or 0
                                    ),
                                    float(
                                        detalle.get(
                                            "precio",
                                            0
                                        ) or 0
                                    ),
                                    float(
                                        detalle.get(
                                            "subtotal",
                                            0
                                        ) or 0
                                    ),
                                    detalle.get(
                                        "codigo",
                                        ""
                                    ) or ""
                                )
                            )

            actualizadas += 1

            print(
                "VENTA DESCARGADA:",
                uuid_venta,
                "TIPO:",
                tipo_final
            )

        conexion.commit()

        print(
            "Ventas descargadas:",
            actualizadas
        )

        conexion.close()

        return actualizadas

    except Exception as e:

        print(
            "Error descargando ventas:",
            repr(e)
        )

        if conexion:

            try:
                conexion.rollback()
                conexion.close()
            except Exception:
                pass

        return 0


# =========================================================
# 5. SUBIDA DE ARQUEOS
#    SQLITE -> SUPABASE
# =========================================================

def sincronizar_arqueos():

    init_db()

    if not hay_internet():
        return 0

    conexion = create_connection()
    cursor = conexion.cursor()

    pendientes = cursor.execute(
        """
        SELECT
            id,
            registro_uuid,
            datos
        FROM sincronizacion
        WHERE sincronizado=0
          AND tabla='arqueos'
        ORDER BY id
        """
    ).fetchall()

    sincronizados = 0

    for fila in pendientes:

        sync_id = fila[0]
        arqueo_uuid = fila[1]
        datos_json = fila[2]

        if not arqueo_uuid or not datos_json:
            continue

        try:

            arqueo = json.loads(
                datos_json
            )

            datos = {

                "uuid": arqueo_uuid,

                "fecha": arqueo.get(
                    "fecha"
                ),

                "apertura": arqueo.get(
                    "apertura",
                    0
                ),

                "esperado": arqueo.get(
                    "esperado",
                    0
                ),

                "real": arqueo.get(
                    "real",
                    0
                ),

                "diferencia": arqueo.get(
                    "diferencia",
                    0
                ),

                "usuario": arqueo.get(
                    "usuario",
                    "Administrador"
                ),

                "observaciones": arqueo.get(
                    "observaciones",
                    ""
                ),

                "ventas_total": arqueo.get(
                    "ventas_total",
                    0
                ),

                "ventas_efectivo": arqueo.get(
                    "ventas_efectivo",
                    0
                ),

                "ventas_transferencia": arqueo.get(
                    "ventas_transferencia",
                    0
                ),

                "ventas_tarjeta": arqueo.get(
                    "ventas_tarjeta",
                    0
                ),

                "ventas_cuenta": arqueo.get(
                    "ventas_cuenta",
                    0
                ),

                "cantidad_ventas": arqueo.get(
                    "cantidad_ventas",
                    0
                )
            }

            (
                supabase
                .table("arqueos")
                .upsert(
                    datos,
                    on_conflict="uuid"
                )
                .execute()
            )

            cursor.execute(
                """
                UPDATE sincronizacion
                SET sincronizado=1
                WHERE id=?
                """,
                (sync_id,)
            )

            sincronizados += 1

            print(
                "Arqueo sincronizado:",
                arqueo_uuid
            )

        except Exception as e:

            print(
                "Error sincronizando arqueo:",
                repr(e)
            )

    conexion.commit()
    conexion.close()

    return sincronizados


# =========================================================
# 6. DESCARGA DE ARQUEOS
#    SUPABASE -> SQLITE
# =========================================================

def descargar_arqueos():

    init_db()

    if not hay_internet():
        return 0

    try:

        respuesta = (
            supabase
            .table("arqueos")
            .select("*")
            .execute()
        )

        arqueos_remotos = (
            respuesta.data or []
        )

        conexion = create_connection()
        cursor = conexion.cursor()

        descargados = 0
        fechas_para_archivar = []

        for arqueo in arqueos_remotos:

            arqueo_uuid = arqueo.get(
                "uuid"
            )

            if not arqueo_uuid:
                continue

            existente = cursor.execute(
                """
                SELECT id
                FROM arqueos
                WHERE uuid=?
                """,
                (arqueo_uuid,)
            ).fetchone()

            if existente:
                continue

            cursor.execute(
                """
                INSERT INTO arqueos
                (
                    uuid,
                    fecha,
                    apertura,
                    esperado,
                    real,
                    diferencia,
                    usuario,
                    observaciones,
                    ventas_total,
                    ventas_efectivo,
                    ventas_transferencia,
                    ventas_tarjeta,
                    ventas_cuenta,
                    cantidad_ventas
                )
                VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    arqueo_uuid,
                    arqueo.get("fecha"),
                    arqueo.get("apertura", 0),
                    arqueo.get("esperado", 0),
                    arqueo.get("real", 0),
                    arqueo.get("diferencia", 0),
                    arqueo.get(
                        "usuario",
                        "Administrador"
                    ),
                    arqueo.get(
                        "observaciones",
                        ""
                    ),
                    arqueo.get(
                        "ventas_total",
                        0
                    ),
                    arqueo.get(
                        "ventas_efectivo",
                        0
                    ),
                    arqueo.get(
                        "ventas_transferencia",
                        0
                    ),
                    arqueo.get(
                        "ventas_tarjeta",
                        0
                    ),
                    arqueo.get(
                        "ventas_cuenta",
                        0
                    ),
                    arqueo.get(
                        "cantidad_ventas",
                        0
                    )
                )
            )

            descargados += 1

            fecha = arqueo.get(
                "fecha"
            )

            if fecha:

                fechas_para_archivar.append(
                    str(fecha)[:10]
                )

        conexion.commit()
        conexion.close()

        # =================================================
        # ARCHIVAR VENTAS
        # =================================================

        for fecha in fechas_para_archivar:

            try:

                archivar_ventas(
                    fecha=fecha
                )

                print(
                    "Ventas archivadas:",
                    fecha
                )

            except Exception as e:

                print(
                    "Error archivando ventas:",
                    e
                )

        print(
            "Arqueos descargados:",
            descargados
        )

        return descargados

    except Exception as e:

        print(
            "Error descargando arqueos:",
            repr(e)
        )

        return 0


# =========================================================
# 7. SUBIDA DE MOVIMIENTOS DE CAJA
#    SQLITE -> SUPABASE
# =========================================================

def sincronizar_movimientos_caja():

    init_db()

    if not hay_internet():
        return 0

    conexion = create_connection()
    cursor = conexion.cursor()

    pendientes = cursor.execute(
        """
        SELECT
            id,
            registro_uuid,
            accion,
            datos
        FROM sincronizacion
        WHERE sincronizado=0
          AND tabla='movimientos_caja'
        ORDER BY id
        """
    ).fetchall()

    sincronizados = 0

    for fila in pendientes:

        sync_id = fila[0]
        movimiento_uuid = fila[1]
        accion = fila[2]
        datos_json = fila[3]

        if not movimiento_uuid:
            continue

        try:

            if accion == "eliminar":

                (
                    supabase
                    .table("movimientos_caja")
                    .delete()
                    .eq(
                        "uuid",
                        movimiento_uuid
                    )
                    .execute()
                )

            else:

                if not datos_json:
                    continue

                movimiento = json.loads(
                    datos_json
                )

                datos = {

                    "uuid": movimiento_uuid,

                    "fecha": movimiento.get(
                        "fecha"
                    ),

                    "tipo": movimiento.get(
                        "tipo",
                        "INGRESO"
                    ),

                    "importe": movimiento.get(
                        "importe",
                        0
                    ),

                    "concepto": movimiento.get(
                        "concepto",
                        ""
                    ),

                    "usuario": movimiento.get(
                        "usuario",
                        "Administrador"
                    )
                }

                (
                    supabase
                    .table("movimientos_caja")
                    .upsert(
                        datos,
                        on_conflict="uuid"
                    )
                    .execute()
                )

            cursor.execute(
                """
                UPDATE sincronizacion
                SET sincronizado=1
                WHERE id=?
                """,
                (sync_id,)
            )

            sincronizados += 1

            print(
                "Movimiento sincronizado:",
                movimiento_uuid
            )

        except Exception as e:

            print(
                "Error sincronizando movimiento:",
                repr(e)
            )

    conexion.commit()
    conexion.close()

    return sincronizados


# =========================================================
# 8. DESCARGA DE MOVIMIENTOS DE CAJA
#    SUPABASE -> SQLITE
# =========================================================

def descargar_movimientos_caja():

    init_db()

    if not hay_internet():
        return 0

    try:

        respuesta = (
            supabase
            .table("movimientos_caja")
            .select("*")
            .execute()
        )

        movimientos_remotos = (
            respuesta.data or []
        )

        conexion = create_connection()
        cursor = conexion.cursor()

        descargados = 0

        for movimiento in movimientos_remotos:

            movimiento_uuid = (
                movimiento.get("uuid")
            )

            if not movimiento_uuid:
                continue

            existente = cursor.execute(
                """
                SELECT id
                FROM movimientos_caja
                WHERE uuid=?
                """,
                (movimiento_uuid,)
            ).fetchone()

            if existente:

                cursor.execute(
                    """
                    UPDATE movimientos_caja
                    SET
                        fecha=?,
                        tipo=?,
                        importe=?,
                        concepto=?,
                        usuario=?
                    WHERE uuid=?
                    """,
                    (
                        movimiento.get(
                            "fecha"
                        ),
                        movimiento.get(
                            "tipo",
                            "INGRESO"
                        ),
                        movimiento.get(
                            "importe",
                            0
                        ),
                        movimiento.get(
                            "concepto",
                            ""
                        ),
                        movimiento.get(
                            "usuario",
                            "Administrador"
                        ),
                        movimiento_uuid
                    )
                )

                continue

            cursor.execute(
                """
                INSERT INTO movimientos_caja
                (
                    fecha,
                    tipo,
                    importe,
                    concepto,
                    usuario,
                    uuid
                )
                VALUES
                (?, ?, ?, ?, ?, ?)
                """,
                (
                    movimiento.get(
                        "fecha"
                    ),
                    movimiento.get(
                        "tipo",
                        "INGRESO"
                    ),
                    movimiento.get(
                        "importe",
                        0
                    ),
                    movimiento.get(
                        "concepto",
                        ""
                    ),
                    movimiento.get(
                        "usuario",
                        "Administrador"
                    ),
                    movimiento_uuid
                )
            )

            descargados += 1

        conexion.commit()
        conexion.close()

        print(
            "Movimientos descargados:",
            descargados
        )

        return descargados

    except Exception as e:

        print(
            "Error descargando movimientos:",
            repr(e)
        )

        return 0


# =========================================================
# SINCRONIZACIÓN PRINCIPAL
# =========================================================

def sincronizar():

    print(
        "========================================"
    )

    print(
        "SINCRONIZACIÓN CON SUPABASE"
    )

    print(
        "========================================"
    )

    if not hay_internet():

        print(
            "Sin conexión con Supabase."
        )

        return {
            "ventas_subidas": 0,
            "productos_subidos": 0,
            "arqueos_subidos": 0,
            "movimientos_subidos": 0,
            "productos_bajados": 0,
            "ventas_bajadas": 0,
            "arqueos_bajados": 0,
            "movimientos_bajados": 0
        }

    # =====================================================
    # SUBIR
    # =====================================================

    productos_subidos = (
        sincronizar_productos()
    )

    ventas_subidas = (
        sincronizar_ventas()
    )

    arqueos_subidos = (
        sincronizar_arqueos()
    )

    movimientos_subidos = (
        sincronizar_movimientos_caja()
    )

    # =====================================================
    # BAJAR
    # =====================================================

    productos_bajados = (
        descargar_productos()
    )

    ventas_bajadas = (
        descargar_ventas()
    )

    arqueos_bajados = (
        descargar_arqueos()
    )

    movimientos_bajados = (
        descargar_movimientos_caja()
    )

    resultado = {

        "ventas_subidas":
            ventas_subidas,

        "productos_subidos":
            productos_subidos,

        "arqueos_subidos":
            arqueos_subidos,

        "movimientos_subidos":
            movimientos_subidos,

        "productos_bajados":
            productos_bajados,

        "ventas_bajadas":
            ventas_bajadas,

        "arqueos_bajados":
            arqueos_bajados,

        "movimientos_bajados":
            movimientos_bajados
    }

    print(
        "SINCRONIZACIÓN OK:",
        resultado
    )

    return resultado


# =========================================================
# SEGUNDO PLANO
# =========================================================

_sincronizacion_en_curso = False

_lock_sincronizacion = threading.Lock()


def sincronizar_en_segundo_plano():

    global _sincronizacion_en_curso

    with _lock_sincronizacion:

        if _sincronizacion_en_curso:

            print(
                "Sincronización ya en curso..."
            )

            return False

        _sincronizacion_en_curso = True

    def trabajo():

        global _sincronizacion_en_curso

        try:

            print(
                "========================================"
            )

            print(
                "SINCRONIZACIÓN EN SEGUNDO PLANO"
            )

            print(
                "========================================"
            )

            resultado = sincronizar()

            print(
                "Sincronización automática OK:",
                resultado
            )

        except Exception as e:

            print(
                "Error en sincronización:",
                repr(e)
            )

        finally:

            _sincronizacion_en_curso = False

            print(
                "Sincronización en segundo plano finalizada"
            )

    hilo = threading.Thread(
        target=trabajo,
        daemon=True
    )

    hilo.start()

    return True