import requests
import sqlite3


from ui.db import BASE_DATOS



SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"





def hay_internet():


    try:

        requests.get(
            SERVIDOR,
            timeout=3
        )

        return True


    except:

        return False

def existe_producto_servidor(uuid):

    try:

        r = requests.get(
            f"{SERVIDOR}/productos/uuid/{uuid}",
            timeout=10
        )

        if r.status_code == 200:
            return r.json()["id"]

        return None


    except Exception as e:

        print("Error buscando producto:", e)
        return None






def sincronizar_ventas():


    conexion = sqlite3.connect(BASE_DATOS)

    conexion.row_factory = sqlite3.Row

    cursor = conexion.cursor()



    pendientes = cursor.execute("""
        SELECT *
        FROM sincronizacion
        WHERE sincronizado=0
        AND tabla='ventas'
    """).fetchall()



    for fila in pendientes:


        venta_id = fila["registro"]



        venta = cursor.execute("""
            SELECT *
            FROM ventas
            WHERE id=?
        """,
        (
            venta_id,
        )).fetchone()



        if not venta:

            continue





        detalles = cursor.execute("""
            SELECT *
            FROM detalle_ventas
            WHERE venta_id=?
        """,
        (
            venta_id,
        )).fetchall()



        items = []



        for d in detalles:


            items.append({

                "producto_id":0,

                "producto":d["producto"],

                "cantidad":d["cantidad"],

                "precio":d["precio"],

                "codigo":d["codigo"] or ""

            })





        datos = {


            "items":items,

            "forma_pago":venta["forma_pago"] or "efectivo",

            "cliente_id":venta["cliente_id"] or 0,

            "descuento":venta["descuento"] or 0,

            "usuario":venta["usuario"] or "Administrador",


            "pago_efectivo":venta["pago_efectivo"] or 0,

            "pago_transferencia":venta["pago_transferencia"] or 0,

            "pago_tarjeta":venta["pago_tarjeta"] or 0,

            "pago_cuenta":venta["pago_cuenta"] or 0

        }





        try:


            r = requests.post(

                f"{SERVIDOR}/ventas/",

                json=datos,

                timeout=10

            )



            if r.status_code in (200, 201):



                cursor.execute("""
                    UPDATE sincronizacion
                    SET sincronizado=1
                    WHERE id=?
                """,
                (
                    fila["id"],
                ))



                print(
                    "Venta sincronizada:",
                    venta_id
                )



            else:


                print(
                    "Error venta:",
                    r.text
                )



        except Exception as e:


            print(
                "Error venta:",
                e
            )




    conexion.commit()

    conexion.close()





def existe_producto_servidor(uuid_producto):

    try:

        r = requests.get(
            f"{SERVIDOR}/productos",
            timeout=10
        )

        r.raise_for_status()

        productos = r.json()

        for p in productos:

            if p.get("uuid") == uuid_producto:

                return p["id"]

        return None


    except Exception as e:

        print(
            "Error buscando producto servidor:",
            e
        )

        return None

def sincronizar_productos():



    conexion = sqlite3.connect(BASE_DATOS)

    conexion.row_factory = sqlite3.Row

    cursor = conexion.cursor()




    pendientes = cursor.execute("""
        SELECT *
        FROM sincronizacion
        WHERE sincronizado=0
        AND tabla='productos'
    """).fetchall()





    for fila in pendientes:



        producto_id = fila["registro"]




        producto = cursor.execute("""
            SELECT *
            FROM productos
            WHERE id=?
        """,
        (
            producto_id,
        )).fetchone()



        if not producto:

            continue





        datos = {

            "uuid": producto["uuid"],
            
            "codigo_barras":producto["codigo_barras"],

            "nombre":producto["nombre"],

            "categoria":producto["categoria"],

            "precio_compra":producto["precio_compra"],

            "precio_venta":producto["precio_venta"],

            "stock":producto["stock"]

        }





        try:

            id_servidor = existe_producto_servidor(
                producto["uuid"]
            )


            if id_servidor:


                r = requests.put(

                    f"{SERVIDOR}/productos/{id_servidor}",

                    json=datos,

                    timeout=10

                )


            else:


                r = requests.post(

                    f"{SERVIDOR}/productos",

                    json=datos,

                    timeout=10

                )


            if r.status_code == 200:



                cursor.execute("""
                    UPDATE sincronizacion
                    SET sincronizado=1
                    WHERE id=?
                """,
                (
                    fila["id"],
                ))



                print(
                    "Producto sincronizado:",
                    producto_id
                )



            else:


                print(
                    "Error producto:",
                    r.text
                )



        except Exception as e:


            print(
                "Error producto:",
                e
            )




    conexion.commit()

    conexion.close()







def descargar_productos():



    conexion = sqlite3.connect(BASE_DATOS)

    conexion.row_factory = sqlite3.Row

    cursor = conexion.cursor()



    try:



        respuesta = requests.get(

            f"{SERVIDOR}/productos",

            timeout=10

        )



        respuesta.raise_for_status()



        productos = respuesta.json()





        for p in productos:



            existe = cursor.execute("""
                SELECT id
                FROM productos
                WHERE codigo_barras=?
            """,
            (
                p["codigo_barras"],
            )).fetchone()





            if existe:



                cursor.execute("""
                    UPDATE productos
                    SET

                        nombre=?,

                        categoria=?,

                        precio_compra=?,

                        precio_venta=?,

                        stock=?

                    WHERE codigo_barras=?

                """,
                (

                    p["nombre"],

                    p["categoria"],

                    p["precio_compra"],

                    p["precio_venta"],

                    p["stock"],

                    p["codigo_barras"]

                ))





            else:



                cursor.execute("""
                    INSERT INTO productos
                    (
                        codigo_barras,
                        nombre,
                        categoria,
                        precio_compra,
                        precio_venta,
                        stock,
                        stock_minimo
                    )

                    VALUES
                    (?,?,?,?,?,?,?)

                """,
                (

                    p["codigo_barras"],

                    p["nombre"],

                    p["categoria"],

                    p["precio_compra"],

                    p["precio_venta"],

                    p["stock"],

                    5

                ))






        conexion.commit()



        print(
            "Productos descargados OK"
        )



    except Exception as e:



        print(
            "Error descargando productos:",
            e
        )



    finally:


        conexion.close()







def sincronizar():



    if not hay_internet():

        


        print(
            "Sin conexión"
        )

        return




    sincronizar_ventas()



    sincronizar_productos()



    descargar_productos()







if __name__ == "__main__":


    sincronizar()