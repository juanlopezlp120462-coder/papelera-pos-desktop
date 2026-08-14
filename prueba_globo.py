import sqlite3

from ui.db import BASE_DATOS

conexion = sqlite3.connect(BASE_DATOS)
conexion.row_factory = sqlite3.Row

filas = conexion.execute("""
    SELECT
        id,
        uuid,
        codigo_barras,
        nombre,
        categoria,
        precio_compra,
        precio_venta,
        stock,
        stock_minimo
    FROM productos
""").fetchall()

for fila in filas:
    if "globo" in (fila["nombre"] or "").lower():
        print(dict(fila))

conexion.close()