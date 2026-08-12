import requests
import json

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
                "forma_pago": venta.get("forma_pago", "EFECTIVO"),
                "cliente_id": venta.get("cliente_id"),
                "descuento": venta.get("descuento", 0),
                "usuario": venta.get("usuario", "Administrador"),
                "pago_efectivo": venta.get("pago_efectivo", 0),
                "pago_transferencia": venta.get("pago_transferencia", 0),
                "pago_tarjeta": venta.get("pago_tarjeta", 0),
                "pago_cuenta": venta.get("pago_cuenta", 0),
                "items": venta.get("items", [])
            }

            if not datos["items"]:
                print("Venta sin items:", fila[2])
                continue

            respuesta = requests.post(
                f"{SERVIDOR}/ventas/sync",
                json=datos,
                timeout=15
            )

            if respuesta.status_code in (200, 201):
                resultado = respuesta.json()

                cursor.execute(
                    """
                    UPDATE sincronizacion
                    SET sincronizado=1
                    WHERE id=?
                    """,
                    (sync_id,)
                )

                sincronizadas += 1
                print("Venta sincronizada:", registro_uuid)
            else:
                print("Error sincronizando venta:", respuesta.status_code, respuesta.text)

        except Exception as e:
            print("Error sincronizando venta:", e)

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
        datos_json = fila[4]

        if not producto_uuid:
            print("Producto sin UUID")
            continue

        if not datos_json:
            print("Producto sin datos")
            continue

        try:
            producto = json.loads(datos_json)

            datos = {
                "uuid": producto_uuid,
                "codigo_barras": producto.get("codigo_barras", ""),
                "nombre": producto.get("nombre", ""),
                "categoria": producto.get("categoria", "General"),
                "precio_compra": producto.get("precio_compra", 0),
                "precio_venta": producto.get("precio_venta", 0),
                "stock": producto.get("stock", 0)
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
                print("Producto sincronizado:", producto_uuid)
            else:
                print("Error producto:", respuesta.status_code, respuesta.text)

        except Exception as e:
            print("Error sincronizando producto:", e)

    conexion.commit()
    conexion.close()
    return sincronizados


# ==========================================
# 3. DESCARGA DE PRODUCTOS (NUBE -> LOCAL)
# ==========================================
def descargar_productos():
    if not hay_internet():
        return 0

    try:
        respuesta = requests.get(f"{SERVIDOR}/productos", timeout=15)
        if respuesta.status_code == 200:
            productos_remotos = respuesta.json()
            conexion = create_connection()
            cursor = conexion.cursor()

            actualizados = 0
            for prod in productos_remotos:
                uuid_prod = prod.get("uuid")
                codigo = prod.get("codigo_barras", "")
                nombre = prod.get("nombre", "")
                categoria = prod.get("categoria", "General")
                p_compra = prod.get("precio_compra", 0)
                p_venta = prod.get("precio_venta", 0)
                stock = prod.get("stock", 0)
                stock_minimo = prod.get("stock_minimo", 5)

                if uuid_prod:
                    cursor.execute("""
                        INSERT INTO productos (uuid, codigo_barras, nombre, categoria, precio_compra, precio_venta, stock, stock_minimo)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(uuid) DO UPDATE SET
                            codigo_barras=excluded.codigo_barras,
                            nombre=excluded.nombre,
                            categoria=excluded.categoria,
                            precio_compra=excluded.precio_compra,
                            precio_venta=excluded.precio_venta,
                            stock=excluded.stock,
                            stock_minimo=excluded.stock_minimo
                    """, (uuid_prod, codigo, nombre, categoria, p_compra, p_venta, stock, stock_minimo))
                    actualizados += 1

            conexion.commit()
            conexion.close()
            return actualizados
        return 0
    except Exception as e:
        print("Error descargando productos:", e)
        return 0


# ==========================================
# 4. DESCARGA DE VENTAS / HISTORIAL (NUBE -> LOCAL)
# ==========================================
def descargar_ventas():
    if not hay_internet():
        return 0

    try:
        respuesta = requests.get(f"{SERVIDOR}/ventas", timeout=15)
        if respuesta.status_code == 200:
            ventas_remotas = respuesta.json()
            conexion = create_connection()
            cursor = conexion.cursor()

            actualizadas = 0
            for venta in ventas_remotas:
                uuid_venta = venta.get("uuid")
                fecha = venta.get("fecha")
                total = venta.get("total", 0)
                forma_pago = venta.get("forma_pago", "EFECTIVO")
                cliente_id = venta.get("cliente_id")
                descuento = venta.get("descuento", 0)
                usuario = venta.get("usuario", "Administrador")

                if uuid_venta:
                    cursor.execute("""
                        INSERT OR IGNORE INTO ventas (uuid, fecha, total, forma_pago, cliente_id, descuento, usuario)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (uuid_venta, fecha, total, forma_pago, cliente_id, descuento, usuario))
                    actualizadas += 1

            conexion.commit()
            conexion.close()
            return actualizadas
        return 0
    except Exception as e:
        print("Error descargando ventas:", e)
        return 0


# ==========================================
# FUNCIÓN PRINCIPAL DE SINCRONIZACIÓN
# ==========================================
def sincronizar():
    # 1. Subir cambios locales pendientes
    ventas_subidas = sincronizar_ventas()
    productos_subidos = sincronizar_productos()

    # 2. Descargar cambios nuevos de la nube (otras PCs)
    productos_bajados = descargar_productos()
    ventas_bajadas = descargar_ventas()

    return {
        "ventas_subidas": ventas_subidas,
        "productos_subidos": productos_subidos,
        "productos_bajados": productos_bajados,
        "ventas_bajadas": ventas_bajadas
    }