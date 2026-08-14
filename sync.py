import json
import requests

from ui.db import (
    create_connection,
    init_db,
    archivar_ventas
)


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


# ==========================================
# 1. SUBIDA DE VENTAS (LOCAL -> NUBE)
# ==========================================
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
            print("Venta sin UUID:", fila[2])
            continue

        if not datos_json:
            print("Venta sin datos:", fila[2])
            continue

        try:

            venta = json.loads(datos_json)

            datos = {
                "uuid": registro_uuid,
                "fecha": venta.get("fecha"),
                "total": venta.get("total", 0),
                "forma_pago": venta.get(
                    "forma_pago",
                    "EFECTIVO"
                ),
                "cliente_id": venta.get("cliente_id"),
                "descuento": venta.get("descuento", 0),
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

            respuesta = requests.post(
                f"{SERVIDOR}/ventas/sync",
                json=datos,
                timeout=15
            )

            if respuesta.status_code in (200, 201):

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


# ==========================================
# 2. SUBIDA DE PRODUCTOS (LOCAL -> NUBE)
# ==========================================
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
            tabla,
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
        producto_uuid = fila[2]
        accion = fila[3]
        datos_json = fila[4]

        if not producto_uuid:

            print(
                "Producto sin UUID:",
                sync_id
            )

            continue

        try:

            # ======================================================
            # ELIMINAR PRODUCTO EN RAILWAY
            # ======================================================

            if accion == "eliminar":

                print(
                    "ELIMINANDO PRODUCTO EN RAILWAY:",
                    producto_uuid
                )

                respuesta = requests.delete(
                    f"{SERVIDOR}/productos/sync/{producto_uuid}",
                    timeout=15
                )

                if respuesta.status_code in (200, 404):

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
                        "Producto eliminado de Railway:",
                        producto_uuid
                    )

                else:

                    print(
                        "Error eliminando producto:",
                        respuesta.status_code,
                        respuesta.text
                    )

                continue

            # ======================================================
            # CREAR / ACTUALIZAR PRODUCTO EN RAILWAY
            # ======================================================

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

            respuesta = requests.post(
                f"{SERVIDOR}/productos/sync",
                json=datos,
                timeout=15
            )

            if respuesta.status_code in (200, 201):

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

            else:

                print(
                    "Error producto:",
                    respuesta.status_code,
                    respuesta.text
                )

        except Exception as e:

            print(
                "Error sincronizando producto:",
                e
            )

    conexion.commit()
    conexion.close()

    return sincronizados

# ==========================================
# 3. SUBIDA DE ARQUEOS (LOCAL -> NUBE)
# ==========================================
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
            tabla,
            registro_uuid,
            accion,
            datos
        FROM sincronizacion
        WHERE sincronizado=0
        AND tabla='arqueos'
        ORDER BY id
        """
    ).fetchall()

    arqueos_sincronizados = 0

    for fila in pendientes:

        sync_id = fila[0]
        arqueo_uuid = fila[2]
        datos_json = fila[4]

        if not arqueo_uuid or not datos_json:
            continue

        try:

            arqueo = json.loads(
                datos_json
            )

            datos = {
                "uuid": arqueo_uuid,
                "fecha": arqueo.get("fecha"),
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

            respuesta = requests.post(
                f"{SERVIDOR}/caja/arqueos/sync",
                json=[datos],
                timeout=15
            )

            if respuesta.status_code in (200, 201):

                cursor.execute(
                    """
                    UPDATE sincronizacion
                    SET sincronizado=1
                    WHERE id=?
                    """,
                    (sync_id,)
                )

                arqueos_sincronizados += 1

                print(
                    "Arqueo sincronizado:",
                    arqueo_uuid
                )

            else:

                print(
                    "Error arqueo:",
                    respuesta.status_code,
                    respuesta.text
                )

        except Exception as e:

            print(
                "Error sincronizando arqueo:",
                e
            )

    conexion.commit()
    conexion.close()

    return arqueos_sincronizados



# ==========================================
# 4. SUBIDA DE MOVIMIENTOS DE CAJA
#    LOCAL -> NUBE
# ==========================================
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

    if not pendientes:

        conexion.close()

        return 0

    movimientos = []

    ids_sync = []

    for fila in pendientes:

        sync_id = fila[0]
        movimiento_uuid = fila[1]
        accion = fila[2]
        datos_json = fila[3]

        if accion != "crear":
            continue

        if not movimiento_uuid:
            print(
                "Movimiento de caja sin UUID:",
                sync_id
            )
            continue

        if not datos_json:
            print(
                "Movimiento de caja sin datos:",
                movimiento_uuid
            )
            continue

        try:

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

            movimientos.append(
                datos
            )

            ids_sync.append(
                sync_id
            )

        except Exception as e:

            print(
                "Error leyendo movimiento:",
                e
            )

    if not movimientos:

        conexion.close()

        return 0

    try:

        respuesta = requests.post(
            f"{SERVIDOR}/caja/movimientos/sync",
            json=movimientos,
            timeout=15
        )

        if respuesta.status_code in (200, 201):

            for sync_id in ids_sync:

                cursor.execute(
                    """
                    UPDATE sincronizacion
                    SET sincronizado=1
                    WHERE id=?
                    """,
                    (sync_id,)
                )

            conexion.commit()

            print(
                "Movimientos de caja sincronizados:",
                len(ids_sync)
            )

            resultado = len(ids_sync)

        else:

            print(
                "Error sincronizando movimientos:",
                respuesta.status_code,
                respuesta.text
            )

            resultado = 0

    except Exception as e:

        print(
            "Error sincronizando movimientos:",
            e
        )

        resultado = 0

    conexion.close()

    return resultado


# ==========================================
# 5. DESCARGA DE PRODUCTOS
#    NUBE -> LOCAL
# ==========================================
def descargar_productos():

    if not hay_internet():
        return 0

    try:

        respuesta = requests.get(
            f"{SERVIDOR}/productos",
            timeout=15
        )

        if respuesta.status_code != 200:
            return 0

        productos_remotos = respuesta.json()

        conexion = create_connection()
        cursor = conexion.cursor()

        actualizados = 0

        # ==========================================================
        # UUID DE TODOS LOS PRODUCTOS QUE EXISTEN EN RAILWAY
        # ==========================================================

        uuids_remotos = set()

        for prod in productos_remotos:

            uuid_prod = prod.get("uuid")

            if not uuid_prod:
                continue

            uuids_remotos.add(uuid_prod)

            codigo = prod.get(
                "codigo_barras",
                ""
            )

            nombre = prod.get(
                "nombre",
                ""
            )

            categoria = prod.get(
                "categoria",
                "General"
            )

            p_compra = prod.get(
                "precio_compra",
                0
            )

            p_venta = prod.get(
                "precio_venta",
                0
            )

            stock = prod.get(
                "stock",
                0
            )

            stock_minimo = prod.get(
                "stock_minimo",
                5
            )

            # ======================================================
            # BUSCAR PRODUCTO LOCAL
            # ======================================================

            existente = cursor.execute(
                """
                SELECT id
                FROM productos
                WHERE uuid=?
                """,
                (uuid_prod,)
            ).fetchone()

            # ======================================================
            # ACTUALIZAR PRODUCTO EXISTENTE
            # ======================================================

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
                    (
                        codigo,
                        nombre,
                        categoria,
                        p_compra,
                        p_venta,
                        stock,
                        stock_minimo,
                        uuid_prod
                    )
                )

                actualizados += 1

            # ======================================================
            # CREAR PRODUCTO NUEVO
            # ======================================================

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
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        uuid_prod,
                        codigo,
                        nombre,
                        categoria,
                        p_compra,
                        p_venta,
                        stock,
                        stock_minimo
                    )
                )

                actualizados += 1

        # ==========================================================
        # ELIMINAR PRODUCTOS LOCALES QUE YA NO EXISTEN EN RAILWAY
        # ==========================================================

        productos_locales = cursor.execute(
            """
            SELECT id, uuid, nombre
            FROM productos
            """
        ).fetchall()

        eliminados = 0

        for producto_local in productos_locales:

            id_local = producto_local["id"]
            uuid_local = producto_local["uuid"]
            nombre_local = producto_local["nombre"]

            if not uuid_local:
                continue

            # ------------------------------------------------------
            # Si existe en Railway, se mantiene
            # ------------------------------------------------------

            if uuid_local in uuids_remotos:
                continue

            # ------------------------------------------------------
            # No existe en Railway:
            # eliminarlo localmente.
            # ------------------------------------------------------

            print(
                "PRODUCTO ELIMINADO LOCALMENTE:",
                uuid_local,
                nombre_local
            )

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
            "PRODUCTOS SINCRONIZADOS:",
            actualizados,
            "| ELIMINADOS:",
            eliminados
        )

        return actualizados + eliminados

    except Exception as e:

        print(
            "ERROR DESCARGANDO PRODUCTOS:",
            e
        )

        try:
            conexion.close()
        except:
            pass

        return 0

# ==========================================
# 6. DESCARGA DE VENTAS
#    NUBE -> LOCAL
# ==========================================
def descargar_ventas():

    if not hay_internet():
        return 0

    conexion = None

    try:

        respuesta = requests.get(
            f"{SERVIDOR}/ventas/",
            timeout=15
        )

        if respuesta.status_code != 200:

            print(
                "Error descargando ventas:",
                respuesta.status_code,
                respuesta.text
            )

            return 0

        ventas_remotas = respuesta.json()

        if not isinstance(ventas_remotas, list):

            print(
                "Error: respuesta de ventas no es una lista"
            )

            return 0

        conexion = create_connection()
        cursor = conexion.cursor()

        # ==========================================
        # OBTENER EL ÚLTIMO ARQUEO DE CADA DÍA
        # ==========================================

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

            fecha_arqueo = fila[0]

            if not fecha_arqueo:
                continue

            fecha_arqueo = str(
                fecha_arqueo
            )

            fecha_dia = fecha_arqueo[:10]

            ultimos_arqueos[fecha_dia] = fecha_arqueo

        print(
            "ULTIMOS ARQUEOS:",
            ultimos_arqueos
        )

        # ==========================================
        # RECORRER VENTAS REMOTAS
        # ==========================================

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

            fecha_dia_venta = fecha_venta[:10]

            # ==========================================
            # CONVERTIR FECHA DE VENTA A DATETIME
            # ==========================================

            try:

                from datetime import datetime

                fecha_venta_dt = datetime.fromisoformat(
                    fecha_venta.replace(
                        "Z",
                        ""
                    )
                )

            except Exception:

                fecha_venta_dt = None

            # ==========================================
            # DETERMINAR SI LA VENTA ESTÁ CERRADA
            # ==========================================

            arqueo_fecha = ultimos_arqueos.get(
                fecha_dia_venta
            )

            estado_remoto = venta.get(
                "estado",
                "ACTIVA"
            )

            estado_final = estado_remoto

            if arqueo_fecha:

                try:

                    from datetime import datetime

                    fecha_arqueo_dt = datetime.fromisoformat(
                        str(arqueo_fecha).replace(
                            "T",
                            " "
                        )
                    )

                    if (
                        fecha_venta_dt
                        and fecha_venta_dt <= fecha_arqueo_dt
                    ):

                        estado_final = "ARCHIVADA"

                    else:

                        estado_final = "ACTIVA"

                except Exception as e:

                    print(
                        "Error comparando fechas:",
                        e
                    )

                    estado_final = estado_remoto

            # ==========================================
            # BUSCAR VENTA LOCAL POR UUID
            # ==========================================

            existente = cursor.execute(
                """
                SELECT id, estado
                FROM ventas
                WHERE uuid=?
                """,
                (uuid_venta,)
            ).fetchone()

            # ==========================================
            # SI YA EXISTE
            # ==========================================

            if existente:

                venta_id = existente[0]

                # Nunca reactivar una venta que ya fue
                # archivada por un arqueo anterior.
                #
                # EXCEPCIÓN:
                # si la venta es posterior al último
                # arqueo, debe quedar ACTIVA.

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
                        pago_cuenta=?
                    WHERE id=?
                    """,
                    (
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

                        venta_id
                    )
                )

                actualizadas += 1

            # ==========================================
            # VENTA NUEVA
            # ==========================================

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
                        pago_cuenta
                    )
                    VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        )
                    )
                )

                actualizadas += 1

        # ==========================================
        # GUARDAR
        # ==========================================

        conexion.commit()

        print(
            "Ventas descargadas:",
            actualizadas
        )

        # ==========================================
        # MOSTRAR CUÁNTAS QUEDAN ACTIVAS
        # ==========================================

        activas = cursor.execute(
            """
            SELECT COUNT(*)
            FROM ventas
            WHERE estado='ACTIVA'
            """
        ).fetchone()[0]

        archivadas = cursor.execute(
            """
            SELECT COUNT(*)
            FROM ventas
            WHERE estado='ARCHIVADA'
            """
        ).fetchone()[0]

        print(
            "VENTAS ACTIVAS:",
            activas
        )

        print(
            "VENTAS ARCHIVADAS:",
            archivadas
        )

        print(
            "DESCARGA DE VENTAS OK"
        )

        conexion.close()
        conexion = None

        return actualizadas

    except Exception as e:

        if conexion:

            try:
                conexion.rollback()
                conexion.close()
            except:
                pass

        print(
            "Error descargando ventas:",
            repr(e)
        )

        return 0

# ==========================================
# 7. DESCARGA DE ARQUEOS
#    NUBE -> LOCAL
# ==========================================
def descargar_arqueos():

    init_db()

    if not hay_internet():
        return 0

    try:

        respuesta = requests.get(
            f"{SERVIDOR}/caja/arqueos",
            timeout=15
        )

        if respuesta.status_code != 200:

            print(
                "Error descargando arqueos:",
                respuesta.status_code,
                respuesta.text
            )

            return 0

        arqueos_remotos = respuesta.json()

        conexion = create_connection()
        cursor = conexion.cursor()

        descargados = 0
        fechas_para_archivar = []

        for arqueo in arqueos_remotos:

            arqueo_uuid = arqueo.get("uuid")

            if not arqueo_uuid:
                continue

            # ==========================================
            # VERIFICAR SI EL ARQUEO YA EXISTE
            # ==========================================

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

            # ==========================================
            # GUARDAR ARQUEO LOCAL
            # ==========================================

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

            # ==========================================
            # GUARDAR FECHA PARA ARCHIVAR DESPUÉS
            # ==========================================

            fecha_arqueo = arqueo.get("fecha")

            if fecha_arqueo:

                fecha_dia = str(
                    fecha_arqueo
                )[:10]

                fechas_para_archivar.append(
                    fecha_dia
                )

        # ==========================================
        # GUARDAR ARQUEOS
        # ==========================================

        conexion.commit()

        # ==========================================
        # CERRAR SQLITE ANTES DE ARCHIVAR VENTAS
        # ==========================================

        conexion.close()

        # ==========================================
        # ARCHIVAR VENTAS DESPUÉS DE CERRAR
        # LA CONEXIÓN ANTERIOR
        # ==========================================

        for fecha_dia in fechas_para_archivar:

            try:

                archivar_ventas(
                    fecha=fecha_dia
                )

                print(
                    "Ventas archivadas por arqueo remoto:",
                    fecha_dia
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
            e
        )

        return 0


# ==========================================
# 8. DESCARGA DE MOVIMIENTOS DE CAJA
#    NUBE -> LOCAL
# ==========================================
def descargar_movimientos_caja():

    init_db()

    if not hay_internet():
        return 0

    try:

        respuesta = requests.get(
            f"{SERVIDOR}/caja/movimientos",
            timeout=15
        )

        if respuesta.status_code != 200:

            print(
                "Error descargando movimientos:",
                respuesta.status_code,
                respuesta.text
            )

            return 0

        movimientos_remotos = respuesta.json()

        conexion = create_connection()
        cursor = conexion.cursor()

        descargados = 0

        for movimiento in movimientos_remotos:

            movimiento_uuid = movimiento.get(
                "uuid"
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
            "Movimientos de caja descargados:",
            descargados
        )

        return descargados

    except Exception as e:

        print(
            "Error descargando movimientos:",
            e
        )

        return 0



# ==========================================
# FUNCIÓN PRINCIPAL DE SINCRONIZACIÓN
# ==========================================
def sincronizar():

    ventas_subidas = sincronizar_ventas()

    productos_subidos = sincronizar_productos()

    arqueos_subidos = sincronizar_arqueos()

    movimientos_subidos = sincronizar_movimientos_caja()

    productos_bajados = descargar_productos()

    arqueos_bajados = descargar_arqueos()

    ventas_bajadas = descargar_ventas()

    movimientos_bajados = descargar_movimientos_caja()

    return {
        "ventas_subidas": ventas_subidas,
        "productos_subidos": productos_subidos,
        "arqueos_subidos": arqueos_subidos,
        "movimientos_subidos": movimientos_subidos,
        "productos_bajados": productos_bajados,
        "ventas_bajadas": ventas_bajadas,
        "arqueos_bajados": arqueos_bajados,
        "movimientos_bajados": movimientos_bajados
    }
