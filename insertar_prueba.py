import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DATOS = os.path.join(BASE_DIR, "database", "abril.db")

conexion = sqlite3.connect(BASE_DATOS)
cursor = conexion.cursor()

# Asegurar tabla
cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        total REAL NOT NULL,
        forma_pago TEXT,
        cliente_id INTEGER
    )
""")

# Insertar venta de prueba
fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
cursor.execute("""
    INSERT INTO ventas (fecha, total, forma_pago, cliente_id)
    VALUES (?, ?, ?, ?)
""", (fecha_actual, 2500.50, "Efectivo", 1))

conexion.commit()
conexion.close()

print("¡Venta de prueba insertada con éxito! Ahora abrilo desde el sistema.")