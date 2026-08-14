import sqlite3
from ui.db import BASE_DATOS

c = sqlite3.connect(BASE_DATOS)
c.row_factory = sqlite3.Row

productos = c.execute("""
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
    ORDER BY id
""").fetchall()

print("\nPRODUCTOS LOCALES")
print("=================")

for p in productos:
    print(dict(p))

c.close()