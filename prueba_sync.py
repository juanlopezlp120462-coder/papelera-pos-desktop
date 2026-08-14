import sqlite3

from ui.db import BASE_DATOS

conexion = sqlite3.connect(BASE_DATOS)
conexion.row_factory = sqlite3.Row

filas = conexion.execute("""
    SELECT
        id,
        tabla,
        registro_uuid,
        accion,
        datos,
        sincronizado
    FROM sincronizacion
    WHERE tabla = 'productos'
    ORDER BY id DESC
""").fetchall()

print("REGISTROS DE SINCRONIZACION DE PRODUCTOS:")
print("=========================================")

for fila in filas:
    print(dict(fila))

conexion.close()