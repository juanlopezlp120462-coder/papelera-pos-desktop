import sqlite3
from ui.db import BASE_DATOS

conexion = sqlite3.connect(BASE_DATOS)
cursor = conexion.cursor()

print("BASE DE DATOS:")
print(BASE_DATOS)
print()

print("PRODUCTOS ANTES DE LIMPIAR:")
productos = cursor.execute("""
    SELECT id, uuid, codigo_barras, nombre, precio_compra, precio_venta, stock
    FROM productos
    ORDER BY id
""").fetchall()

for p in productos:
    print(p)

print()
print("ELIMINANDO PRODUCTOS...")

cursor.execute("DELETE FROM productos")

print("ELIMINANDO REGISTROS DE SINCRONIZACION DE PRODUCTOS...")

cursor.execute("""
    DELETE FROM sincronizacion
    WHERE tabla = 'productos'
""")

conexion.commit()

print()
print("PRODUCTOS DESPUES DE LIMPIAR:")

productos = cursor.execute("""
    SELECT id, uuid, codigo_barras, nombre, precio_compra, precio_venta, stock
    FROM productos
    ORDER BY id
""").fetchall()

for p in productos:
    print(p)

print()
print("REGISTROS DE SINCRONIZACION DE PRODUCTOS RESTANTES:")

sync = cursor.execute("""
    SELECT id, registro_uuid, accion, sincronizado
    FROM sincronizacion
    WHERE tabla = 'productos'
""").fetchall()

for s in sync:
    print(s)

conexion.close()

print()
print("LIMPIEZA TERMINADA.")