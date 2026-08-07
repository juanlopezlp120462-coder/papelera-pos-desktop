import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DATOS = os.path.join(BASE_DIR, "database", "abril.db")

print("Ruta de la DB:", BASE_DATOS)
print("¿Existe el archivo?", os.path.exists(BASE_DATOS))

if os.path.exists(BASE_DATOS):
    conexion = sqlite3.connect(BASE_DATOS)
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM ventas")
        cantidad = cursor.fetchone()[0]
        print(f"Cantidad de ventas registradas: {cantidad}")
        
        cursor.execute("SELECT * FROM ventas")
        print("Registros:", cursor.fetchall())
    except Exception as e:
        print("La tabla 'ventas' no existe o dio error:", e)
    conexion.close()