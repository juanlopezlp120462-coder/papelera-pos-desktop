import sqlite3
import datetime

from ui.db import BASE_DATOS

con = sqlite3.connect(BASE_DATOS)
cur = con.cursor()

print()
print("====================================")
print("ESTADO DE TODAS LAS VENTAS")
print("====================================")

resultado = cur.execute(
    "SELECT estado, COUNT(*) FROM ventas GROUP BY estado"
).fetchall()

print(resultado)

print()
print("====================================")
print("VENTAS DE HOY POR ESTADO")
print("====================================")

hoy = datetime.datetime.now().strftime("%Y-%m-%d")

resultado = cur.execute(
    """
    SELECT estado, COUNT(*)
    FROM ventas
    WHERE fecha LIKE ?
    GROUP BY estado
    """,
    (hoy + "%",)
).fetchall()

print(resultado)

print()
print("====================================")
print("VENTAS DE HOY")
print("====================================")

resultado = cur.execute(
    """
    SELECT id, fecha, total, estado
    FROM ventas
    WHERE fecha LIKE ?
    ORDER BY id DESC
    """,
    (hoy + "%",)
).fetchall()

for venta in resultado:
    print(venta)

print()
print("BASE DE DATOS:")
print(BASE_DATOS)

con.close()