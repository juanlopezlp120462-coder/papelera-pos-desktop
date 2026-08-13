import os
import sqlite3
import shutil
import datetime
import string
import sys
import json
import uuid

from core.database import create_connection


ROOT = (
    os.path.dirname(os.path.abspath(sys.executable))
    if getattr(sys, "frozen", False)
    else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

DB_DIR = os.path.join(ROOT, "database")
BASE_DATOS = os.path.join(DB_DIR, "abril.db")
BACKUP_DIR = os.path.join(ROOT, "backups")


def init_db():

    os.makedirs(DB_DIR, exist_ok=True)

    c = create_connection()
    x = c.cursor()

    # =========================
    # PRODUCTOS
    # =========================

    x.execute("""
    CREATE TABLE IF NOT EXISTS productos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid TEXT UNIQUE,
        codigo_barras TEXT,
        nombre TEXT NOT NULL,
        categoria TEXT,
        precio_compra REAL DEFAULT 0,
        precio_venta REAL DEFAULT 0,
        stock INTEGER DEFAULT 0,
        stock_minimo INTEGER DEFAULT 5
    )
    """)

    columnas = [
        fila[1]
        for fila in x.execute(
            "PRAGMA table_info(productos)"
        ).fetchall()
    ]

    if "uuid" not in columnas:

        x.execute(
            "ALTER TABLE productos ADD COLUMN uuid TEXT"
        )

        productos = x.execute(
            "SELECT id FROM productos"
        ).fetchall()

        for p in productos:

            x.execute(
                "UPDATE productos SET uuid=? WHERE id=?",
                (
                    str(uuid.uuid4()),
                    p[0]
                )
            )

    # =========================
    # CLIENTES
    # =========================

    x.execute("""
    CREATE TABLE IF NOT EXISTS clientes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        documento TEXT,
        telefono TEXT,
        direccion TEXT,
        email TEXT,
        saldo REAL DEFAULT 0
    )
    """)

    # =========================
    # VENTAS
    # =========================

    x.execute("""
    CREATE TABLE IF NOT EXISTS ventas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid TEXT UNIQUE,
        fecha TEXT NOT NULL,
        total REAL NOT NULL,
        forma_pago TEXT,
        cliente_id INTEGER,
        estado TEXT DEFAULT 'ACTIVA',
        descuento REAL DEFAULT 0,
        usuario TEXT DEFAULT 'Administrador',
        pago_efectivo REAL DEFAULT 0,
        pago_transferencia REAL DEFAULT 0,
        pago_tarjeta REAL DEFAULT 0,
        pago_cuenta REAL DEFAULT 0
    )
    """)

    columnas = [
        fila[1]
        for fila in x.execute(
            "PRAGMA table_info(ventas)"
        ).fetchall()
    ]

    if "uuid" not in columnas:

        x.execute(
            "ALTER TABLE ventas ADD COLUMN uuid TEXT"
        )

        ventas = x.execute(
            "SELECT id FROM ventas"
        ).fetchall()

        for v in ventas:

            x.execute(
                "UPDATE ventas SET uuid=? WHERE id=?",
                (
                    str(uuid.uuid4()),
                    v[0]
                )
            )

    campos = {
        "pago_efectivo":"REAL DEFAULT 0",
        "pago_transferencia":"REAL DEFAULT 0",
        "pago_tarjeta":"REAL DEFAULT 0",
        "pago_cuenta":"REAL DEFAULT 0"
    }

    columnas = [
        fila[1]
        for fila in x.execute(
            "PRAGMA table_info(ventas)"
        ).fetchall()
    ]

    for nombre,tipo in campos.items():

        if nombre not in columnas:

            x.execute(
                f"ALTER TABLE ventas ADD COLUMN {nombre} {tipo}"
            )

    # =========================
    # DETALLE VENTAS
    # =========================

    x.execute("""
    CREATE TABLE IF NOT EXISTS detalle_ventas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER,
        producto TEXT,
        cantidad INTEGER,
        precio REAL,
        subtotal REAL,
        codigo TEXT
    )
    """)

    # =========================
    # SINCRONIZACION
    # =========================

    x.execute("""
    CREATE TABLE IF NOT EXISTS sincronizacion(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tabla TEXT,
        registro INTEGER,
        registro_uuid TEXT,
        accion TEXT,
        datos TEXT,
        fecha TEXT,
        sincronizado INTEGER DEFAULT 0
    )
    """)
    
    columnas = [
        fila[1]
        for fila in x.execute(
            "PRAGMA table_info(sincronizacion)"
        ).fetchall()
    ]

    if "registro_uuid" not in columnas:

        x.execute(
            "ALTER TABLE sincronizacion ADD COLUMN registro_uuid TEXT"
        )

    if "datos" not in columnas:

        x.execute(
            "ALTER TABLE sincronizacion ADD COLUMN datos TEXT"
        )
        
    # =========================
    # PEDIDOS
    # =========================

    x.execute("""
    CREATE TABLE IF NOT EXISTS pedidos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        entrega TEXT,
        cliente_id INTEGER,
        estado TEXT DEFAULT 'PENDIENTE',
        observaciones TEXT,
        total REAL DEFAULT 0
    )
    """)

    x.execute("""
    CREATE TABLE IF NOT EXISTS detalle_pedidos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        producto TEXT,
        cantidad INTEGER,
        precio REAL,
        subtotal REAL,
        codigo TEXT
    )
    """)

    # =========================
    # CAJA
    # =========================

    x.execute("""
    CREATE TABLE IF NOT EXISTS movimientos_caja(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid TEXT UNIQUE,
        fecha TEXT,
        tipo TEXT,
        importe REAL,
        concepto TEXT,
        usuario TEXT DEFAULT 'Administrador'
    )
    """)

    # ==========================================
    # MIGRACIÓN: UUID EN MOVIMIENTOS DE CAJA
    # ==========================================

    columnas_movimientos = [
        fila[1]
        for fila in x.execute(
            "PRAGMA table_info(movimientos_caja)"
        ).fetchall()
    ]

    if "uuid" not in columnas_movimientos:
        x.execute("""
            ALTER TABLE movimientos_caja
            ADD COLUMN uuid TEXT
        """)


    x.execute("""
    CREATE TABLE IF NOT EXISTS arqueos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid TEXT UNIQUE,
        fecha TEXT,
        apertura REAL,
        esperado REAL,
        real REAL,
        diferencia REAL,
        usuario TEXT,
        observaciones TEXT,
        ventas_total REAL DEFAULT 0,
        ventas_efectivo REAL DEFAULT 0,
        ventas_transferencia REAL DEFAULT 0,
        ventas_tarjeta REAL DEFAULT 0,
        ventas_cuenta REAL DEFAULT 0,
        cantidad_ventas INTEGER DEFAULT 0
    )
    """)

    # =========================
    # MIGRACION ARQUEOS
    # =========================

    columnas_arqueos = [
        fila[1]
        for fila in x.execute(
            "PRAGMA table_info(arqueos)"
        ).fetchall()
    ]

    if "uuid" not in columnas_arqueos:

        x.execute(
            "ALTER TABLE arqueos ADD COLUMN uuid TEXT"
        )

        arqueos_registros = x.execute(
            "SELECT id FROM arqueos"
        ).fetchall()

        for a in arqueos_registros:

            x.execute(
                "UPDATE arqueos SET uuid=? WHERE id=?",
                (
                    str(uuid.uuid4()),
                    a[0]
                )
            )

    campos_arqueos = {
        "ventas_total": "REAL DEFAULT 0",
        "ventas_efectivo": "REAL DEFAULT 0",
        "ventas_transferencia": "REAL DEFAULT 0",
        "ventas_tarjeta": "REAL DEFAULT 0",
        "ventas_cuenta": "REAL DEFAULT 0",
        "cantidad_ventas": "INTEGER DEFAULT 0"
    }

    columnas_arqueos = [
        fila[1]
        for fila in x.execute(
            "PRAGMA table_info(arqueos)"
        ).fetchall()
    ]

    for nombre, tipo in campos_arqueos.items():

        if nombre not in columnas_arqueos:

            x.execute(
                f"ALTER TABLE arqueos ADD COLUMN {nombre} {tipo}"
            )

    # =========================
    # CONFIGURACION
    # =========================

    x.execute("""
    CREATE TABLE IF NOT EXISTS configuracion(
        clave TEXT PRIMARY KEY,
        valor TEXT
    )
    """)

    for k, v in {
        "nombre_negocio": "COTILLON",
        "direccion": "",
        "telefono": "",
        "email": "",
        "cuit": ""
    }.items():

        x.execute(
            "INSERT OR IGNORE INTO configuracion VALUES(?,?)",
            (k, v)
        )

    x.execute(
        "CREATE INDEX IF NOT EXISTS idx_v_fecha ON ventas(fecha)"
    )

    x.execute(
        "CREATE INDEX IF NOT EXISTS idx_p_codigo ON productos(codigo_barras)"
    )

    c.commit()
    c.close()
    
    
def registrar_sincronizacion(tabla, registro_uuid, accion, datos):

    c = create_connection()
    cur = c.cursor()

    cur.execute("""
        INSERT INTO sincronizacion(
            tabla,
            registro_uuid,
            accion,
            datos,
            fecha,
            sincronizado
        )
        VALUES(?,?,?,?,datetime('now'),0)
    """, (
        tabla,
        registro_uuid,
        accion,
        json.dumps(datos)
    ))

    c.commit()
    c.close()    

def registrar_producto_sync(producto, accion="crear"):

    registrar_sincronizacion(
        "productos",
        producto["uuid"],
        accion,
        producto
    ) 

def obtener_pendientes():

    c = create_connection()

    datos = c.execute("""
        SELECT
            id,
            tabla,
            registro_uuid,
            accion,
            datos
        FROM sincronizacion
        WHERE sincronizado=0
        ORDER BY id
    """).fetchall()

    c.close()

    return datos

def marcar_sincronizado(id_sync):

    c = create_connection()

    c.execute("""
        UPDATE sincronizacion
        SET sincronizado=1
        WHERE id=?
    """, (id_sync,))

    c.commit()
    c.close()      

def get_setting(k, d=""):

    init_db()

    c = create_connection()

    r = c.execute(
        "SELECT valor FROM configuracion WHERE clave=?",
        (k,)
    ).fetchone()

    c.close()

    return r[0] if r else d


def set_setting(k, v):

    init_db()

    c = create_connection()

    c.execute("""
        INSERT INTO configuracion(clave,valor)
        VALUES(?,?)
        ON CONFLICT(clave)
        DO UPDATE SET valor=excluded.valor
    """, (k, str(v)))

    c.commit()
    c.close()


# =========================
# BACKUP BASE DE DATOS
# =========================

def crear_backup():

    os.makedirs(BACKUP_DIR, exist_ok=True)

    fecha = datetime.datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    destino = os.path.join(
        BACKUP_DIR,
        f"abril_backup_{fecha}.db"
    )

    try:

        shutil.copy2(
            BASE_DATOS,
            destino
        )

        return destino

    except Exception as e:

        print(
            "Error creando backup:",
            e
        )

        return None


# =========================
# LIMPIAR BACKUPS VIEJOS
# =========================

def limpiar_backups(maximo=10):

    if not os.path.exists(BACKUP_DIR):
        return

    archivos = sorted(
        os.listdir(BACKUP_DIR)
    )

    while len(archivos) > maximo:

        borrar = archivos.pop(0)

        ruta = os.path.join(
            BACKUP_DIR,
            borrar
        )

        try:

            os.remove(ruta)

        except:

            pass


# =========================
# GENERAR UUID
# =========================

def nuevo_uuid():

    return str(
        uuid.uuid4()
    )


# =========================
# EJECUTAR CONSULTA
# =========================

def ejecutar_sql(sql, parametros=()):

    c = create_connection()

    try:

        cur = c.cursor()

        cur.execute(
            sql,
            parametros
        )

        c.commit()

        return cur.lastrowid

    except Exception as e:

        print(
            "Error SQL:",
            e
        )

        return None

    finally:

        c.close()


# =========================
# OBTENER FECHA ACTUAL
# =========================

def fecha_actual():

    return datetime.datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

# =========================
# ARCHIVAR VENTAS DEL DIA
# =========================

def archivar_ventas(fecha=None):

    c = create_connection()

    try:

        if fecha:

            c.execute("""
                UPDATE ventas
                SET estado='ARCHIVADA'
                WHERE fecha LIKE ?
                AND estado='ACTIVA'
            """,
            (
                fecha + '%',
            ))

        else:

            c.execute("""
                UPDATE ventas
                SET estado='ARCHIVADA'
                WHERE estado='ACTIVA'
            """)

        c.commit()

    except Exception as e:

        print(
            "Error archivando ventas:",
            e
        )

    finally:

        c.close()

# =========================
# CREAR BACKUP
# =========================

def create_backup():

    os.makedirs(BACKUP_DIR, exist_ok=True)

    fecha = datetime.datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    destino = os.path.join(
        BACKUP_DIR,
        f"backup_{fecha}.db"
    )

    try:

        shutil.copy2(
            BASE_DATOS,
            destino
        )

        return destino

    except Exception as e:

        print(
            "Error creando backup:",
            e
        )

        return None


# =========================
# BUSCAR BACKUPS VIEJOS
# =========================

def find_removable_backups():

    if not os.path.exists(BACKUP_DIR):
        return []

    archivos = sorted(
        os.listdir(BACKUP_DIR)
    )

    if len(archivos) <= 10:

        return []

    return [
        os.path.join(
            BACKUP_DIR,
            x
        )
        for x in archivos[:-10]
    ]


# =========================
# RESTAURAR BACKUP
# =========================

def restore_backup(ruta_backup):

    try:

        shutil.copy2(
            ruta_backup,
            BASE_DATOS
        )

        return True

    except Exception as e:

        print(
            "Error restaurando backup:",
            e
        )

        return False