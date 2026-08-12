import uuid
from fastapi import FastAPI
from pydantic import BaseModel

from ui.db import init_db
from core.database import create_connection

app = FastAPI(
    title="Cotillon POS Sync Server"
)

# Crear base si no existe
init_db()


class Producto(BaseModel):
    uuid: str | None = None
    codigo_barras: str | None = None
    nombre: str
    categoria: str | None = None
    precio_compra: float = 0
    precio_venta: float = 0
    stock: int = 0


class Venta(BaseModel):
    uuid: str | None = None
    items: list
    forma_pago: str = "efectivo"
    cliente_id: int = 0
    descuento: float = 0
    usuario: str = "Administrador"
    pago_efectivo: float = 0
    pago_transferencia: float = 0
    pago_tarjeta: float = 0
    pago_cuenta: float = 0


@app.get("/")
def inicio():
    return {
        "mensaje": "Servidor Cotillon POS funcionando"
    }


@app.get("/productos")
def obtener_productos():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            uuid,
            codigo_barras,
            nombre,
            categoria,
            precio_compra,
            precio_venta,
            stock
        FROM productos
        ORDER BY nombre
    """)

    productos = cursor.fetchall()
    conn.close()

    return [
        {
            "id": p[0],
            "uuid": p[1],
            "codigo_barras": p[2],
            "nombre": p[3],
            "categoria": p[4],
            "precio_compra": p[5],
            "precio_venta": p[6],
            "stock": p[7]
        }
        for p in productos
    ]


@app.get("/productos/{id_producto}")
def obtener_producto(id_producto: int):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            uuid,
            codigo_barras,
            nombre,
            categoria,
            precio_compra,
            precio_venta,
            stock
        FROM productos
        WHERE id=?
    """, (id_producto,))

    p = cursor.fetchone()
    conn.close()

    if not p:
        return {
            "error": "Producto no encontrado"
        }

    return {
        "id": p[0],
        "uuid": p[1],
        "codigo_barras": p[2],
        "nombre": p[3],
        "categoria": p[4],
        "precio_compra": p[5],
        "precio_venta": p[6],
        "stock": p[7]
    }


# =========================
# ENDPOINT DE SYNC DE PRODUCTOS
# =========================
@app.post("/productos/sync")
def sincronizar_producto_servidor(producto: Producto):
    conn = create_connection()
    cursor = conn.cursor()
    
    prod_uuid = producto.uuid or str(uuid.uuid4())

    cursor.execute("SELECT id FROM productos WHERE uuid=?", (prod_uuid,))
    existente = cursor.fetchone()

    if existente:
        cursor.execute("""
            UPDATE productos
            SET codigo_barras=?, nombre=?, categoria=?, precio_compra=?, precio_venta=?, stock=?
            WHERE uuid=?
        """, (
            producto.codigo_barras,
            producto.nombre,
            producto.categoria,
            producto.precio_compra,
            producto.precio_venta,
            producto.stock,
            prod_uuid
        ))
        conn.commit()
        conn.close()
        return {"mensaje": "Producto actualizado en servidor", "actualizada": True}
    else:
        cursor.execute("""
            INSERT INTO productos (uuid, codigo_barras, nombre, categoria, precio_compra, precio_venta, stock)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            prod_uuid,
            producto.codigo_barras,
            producto.nombre,
            producto.categoria,
            producto.precio_compra,
            producto.precio_venta,
            producto.stock
        ))
        conn.commit()
        conn.close()
        return {"mensaje": "Producto creado en servidor", "creada": True}


@app.delete("/productos/{id_producto}")
def borrar_producto(id_producto: int):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM productos WHERE id=?",
        (id_producto,)
    )

    conn.commit()
    conn.close()

    return {
        "mensaje": "Producto eliminado correctamente"
    }


# =========================
# OBTENER VENTAS (PARA DESCARGA)
# =========================
@app.get("/ventas")
def obtener_ventas():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            uuid,
            fecha,
            total,
            forma_pago,
            cliente_id,
            descuento,
            usuario
        FROM ventas
        ORDER BY id
    """)

    ventas = cursor.fetchall()
    conn.close()

    return [
        {
            "id": v[0],
            "uuid": v[1],
            "fecha": v[2],
            "total": v[3],
            "forma_pago": v[4],
            "cliente_id": v[5],
            "descuento": v[6],
            "usuario": v[7]
        }
        for v in ventas
    ]


# =========================
# ENDPOINT DE SYNC DE VENTAS
# =========================
@app.post("/ventas/sync")
def sincronizar_venta_servidor(venta: Venta):
    conn = create_connection()
    cursor = conn.cursor()

    if venta.uuid:
        cursor.execute("SELECT id FROM ventas WHERE uuid=?", (venta.uuid,))
        existente = cursor.fetchone()
        if existente:
            conn.close()
            return {"mensaje": "La venta ya existe en el servidor", "duplicada": True}

    total = sum(item["cantidad"] * item["precio"] for item in venta.items)

    cursor.execute("""
        INSERT INTO ventas
        (
            uuid,
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
        )
        VALUES
        (
            ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """,
    (
        venta.uuid,
        total,
        venta.forma_pago,
        venta.cliente_id,
        venta.descuento,
        venta.usuario,
        venta.pago_efectivo,
        venta.pago_transferencia,
        venta.pago_tarjeta,
        venta.pago_cuenta
    ))

    venta_id = cursor.lastrowid

    for item in venta.items:
        cursor.execute("""
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
            (?,?,?,?,?,?)
        """,
        (
            venta_id,
            item["producto"],
            item["cantidad"],
            item["precio"],
            item["cantidad"] * item["precio"],
            item.get("codigo", "")
        ))

    conn.commit()
    conn.close()

    return {
        "mensaje": "Venta sincronizada correctamente en servidor",
        "creada": True,
        "id": venta_id
    }