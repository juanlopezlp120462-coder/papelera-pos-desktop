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
    """,
    (
        id_producto,
    ))

    p = cursor.fetchone()

    conn.close()


    if not p:
        return {
            "error": "Producto no encontrado"
        }


    return {
        "id": p[0],
        "uuid": p[1],
        "codigo_barras": p[1],
        "nombre": p[2],
        "categoria": p[3],
        "precio_compra": p[4],
        "precio_venta": p[5],
        "stock": p[6]
    }
    
@app.get("/productos/uuid/{uuid}")
def buscar_producto_uuid(uuid: str):

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM productos
        WHERE uuid=?
    """,
    (
        uuid,
    ))

    producto = cursor.fetchone()

    conn.close()


    if producto:

        return {
            "id": producto[0]
        }


    return {
        "id": None
    }

@app.post("/productos")
def crear_producto(producto: Producto):

    conn = create_connection()
    cursor = conn.cursor()
    producto_uuid = producto.uuid or str(uuid.uuid4())

    cursor.execute("""
        INSERT INTO productos
        (
            codigo_barras,
            nombre,
            categoria,
            precio_compra,
            precio_venta,
            stock
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """,
    (
        producto_uuid,
        producto.codigo_barras,
        producto.nombre,
        producto.categoria,
        producto.precio_compra,
        producto.precio_venta,
        producto.stock
    ))

    nuevo_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "mensaje": "Producto creado correctamente",
        "id": nuevo_id
    }


@app.put("/productos/{id_producto}")
def editar_producto(id_producto: int, producto: Producto):

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE productos
        SET
            codigo_barras=?,
            nombre=?,
            categoria=?,
            precio_compra=?,
            precio_venta=?,
            stock=?
        WHERE id=?
    """,
    (
        producto.codigo_barras,
        producto.nombre,
        producto.categoria,
        producto.precio_compra,
        producto.precio_venta,
        producto.stock,
        id_producto
    ))

    conn.commit()
    conn.close()

    return {
        "mensaje": "Producto actualizado correctamente"
    }


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
# RECIBIR VENTAS
# =========================

@app.post("/ventas/")
def crear_venta(venta: Venta):

    conn = create_connection()
    cursor = conn.cursor()


    total = 0


    for item in venta.items:

        subtotal = (
            item["cantidad"]
            *
            item["precio"]
        )

        total += subtotal



    cursor.execute("""
        INSERT INTO ventas
        (
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
            datetime('now'),
            ?,?,?,?,?,?,?,?,?
        )
    """,
    (
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
            item.get("codigo","")
        ))



    conn.commit()
    conn.close()


    return {
        "mensaje": "Venta sincronizada correctamente",
        "id": venta_id
    }    