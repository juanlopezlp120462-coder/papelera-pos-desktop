import sys
import uuid
import requests
import sqlite3
import datetime
import json


from ui.db import BASE_DATOS, create_connection, init_db

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QComboBox,
    QDialog,
    QGraphicsDropShadowEffect
)

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor


from ui.keyboard import setup_numeric, parse_number



SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"



def crear_producto_servidor(producto):

    try:

        respuesta = requests.post(
            SERVIDOR + "/productos/",
            json=producto,
            timeout=10
        )

        print(
            "SERVIDOR:",
            respuesta.status_code
        )

        print(
            respuesta.text
        )

        respuesta.raise_for_status()

        return respuesta.json()


    except Exception as e:

        print(
            "ERROR API:",
            e
        )

        return None





class DialogoAviso(QDialog):

    def __init__(self, titulo, mensaje, parent=None):

        super().__init__(parent)


        self.setWindowTitle(titulo)

        self.setFixedSize(
            380,
            160
        )

        self.setModal(True)


        self.setStyleSheet("""
            QDialog {
                background:white;
            }

            QLabel {
                color:#0f172a;
                font-size:15px;
            }

            QPushButton {
                background:#2563eb;
                color:white;
                border-radius:8px;
                padding:10px 24px;
                font-weight:bold;
            }
        """)


        layout = QVBoxLayout(self)


        fila = QHBoxLayout()


        icono = QLabel("✅")

        icono.setStyleSheet(
            "font-size:28px;"
        )


        texto = QLabel(mensaje)

        texto.setWordWrap(True)


        fila.addWidget(icono)

        fila.addWidget(
            texto,
            1
        )


        layout.addLayout(fila)


        boton = QPushButton(
            "Aceptar"
        )


        boton.clicked.connect(
            self.accept
        )


        layout.addWidget(
            boton
        )
class AgregarProducto(QWidget):
    

    producto_guardado = Signal()


    def __init__(self):

        super().__init__()


        self.setWindowTitle(
            "➕ Nuevo Producto - Abril POS"
        )


        self.resize(
            520,
            720
        )


        self.calculando = False



        self.setStyleSheet("""
            QWidget {
                background:#f8fafc;
                font-family:'Segoe UI';
                color:#0f172a;
            }

            QLabel {
                font-size:14px;
                font-weight:600;
            }

            QLineEdit,
            QComboBox {
                background:white;
                border:1px solid #cbd5e1;
                border-radius:10px;
                padding:11px;
                font-size:14px;
            }


            QPushButton {
                border-radius:10px;
                padding:12px;
                font-size:15px;
                font-weight:bold;
            }


            QPushButton#guardar {
                background:#2563eb;
                color:white;
            }


            QPushButton#cancelar {
                background:#e2e8f0;
                color:#334155;
            }

        """)



        layout = QVBoxLayout(self)


        layout.setContentsMargins(
            35,
            35,
            35,
            35
        )



        card = QFrame()


        card.setStyleSheet("""
            QFrame {
                background:white;
                border-radius:18px;
                border:1px solid #e2e8f0;
            }
        """)



        sombra = QGraphicsDropShadowEffect()

        sombra.setBlurRadius(25)

        sombra.setXOffset(0)

        sombra.setYOffset(5)

        sombra.setColor(
            QColor(0,0,0,25)
        )


        card.setGraphicsEffect(
            sombra
        )



        formulario = QVBoxLayout(card)


        formulario.setContentsMargins(
            30,
            30,
            30,
            30
        )


        formulario.setSpacing(
            14
        )



        titulo = QLabel(
            "📦 Nuevo Producto"
        )


        titulo.setStyleSheet("""
            font-size:26px;
            font-weight:800;
        """)


        formulario.addWidget(
            titulo
        )



        subtitulo = QLabel(
            "Completá los datos del producto"
        )


        subtitulo.setStyleSheet(
            "color:#64748b;"
        )


        formulario.addWidget(
            subtitulo
        )



        formulario.addSpacing(10)



        formulario.addWidget(
            QLabel("🏷️ Código de barras")
        )


        self.input_codigo = QLineEdit()


        self.input_codigo.setPlaceholderText(
            "Ej: 779123456789"
        )


        formulario.addWidget(
            self.input_codigo
        )



        formulario.addWidget(
            QLabel("📝 Nombre del producto *")
        )


        self.input_nombre = QLineEdit()


        self.input_nombre.setPlaceholderText(
            "Ej: Vasos descartables"
        )


        formulario.addWidget(
            self.input_nombre
        )



        formulario.addWidget(
            QLabel("📂 Categoría")
        )


        self.input_categoria = QComboBox()


        self.input_categoria.addItems([
            "Cotillon",
            "Papelera",
            "Otro"
        ])


        formulario.addWidget(
            self.input_categoria
        )



        fila = QHBoxLayout()



        compra_box = QVBoxLayout()


        compra_box.addWidget(
            QLabel("💰 Precio compra")
        )


        self.input_compra = QLineEdit()


        setup_numeric(
            self.input_compra,
            2
        )


        self.input_compra.setPlaceholderText(
            "$ 0,00"
        )


        compra_box.addWidget(
            self.input_compra
        )



        ganancia_box = QVBoxLayout()


        ganancia_box.addWidget(
            QLabel("📈 Ganancia %")
        )


        self.input_ganancia = QLineEdit()


        setup_numeric(
            self.input_ganancia,
            0
        )


        self.input_ganancia.setPlaceholderText(
            "Ej: 50"
        )


        ganancia_box.addWidget(
            self.input_ganancia
        )



        fila.addLayout(
            compra_box
        )


        fila.addLayout(
            ganancia_box
        )


        formulario.addLayout(
            fila
        )
        formulario.addWidget(
            QLabel("💵 Precio venta")
        )


        self.input_venta = QLineEdit()


        setup_numeric(
            self.input_venta,
            2
        )


        self.input_venta.setPlaceholderText(
            "$ 0,00"
        )


        formulario.addWidget(
            self.input_venta
        )



        formulario.addWidget(
            QLabel("📦 Stock inicial")
        )


        self.input_stock = QLineEdit()


        setup_numeric(
            self.input_stock,
            0
        )


        self.input_stock.setText(
            "0"
        )


        # ESTE ES EL ULTIMO CAMPO
        # ENTER AQUI EJECUTA GUARDAR
        self.input_stock.setProperty(
            "keyboard_last",
            True
        )


        formulario.addWidget(
            self.input_stock
        )



        self.input_compra.textChanged.connect(
            self.calcular_precio
        )


        self.input_ganancia.textChanged.connect(
            self.calcular_precio
        )



        botones = QHBoxLayout()



        self.btn_cancelar = QPushButton(
            "❌ Cancelar"
        )


        self.btn_cancelar.setObjectName(
            "cancelar"
        )


        self.btn_cancelar.clicked.connect(
            self.close
        )



        self.btn_guardar = QPushButton(
            "💾 Guardar Producto"
        )


        self.btn_guardar.setObjectName(
            "guardar"
        )


        self.btn_guardar.setProperty(
            "keyboard_primary",
            True
        )


        self.btn_guardar.clicked.connect(
            self.guardar_producto
        )



        botones.addWidget(
            self.btn_cancelar
        )


        botones.addWidget(
            self.btn_guardar
        )



        formulario.addLayout(
            botones
        )



        layout.addWidget(
            card
        )



        self.input_codigo.setFocus()



    # ==========================
    # ENTER ULTIMO CAMPO
    # ==========================

    def keyboard_submit(self):

        self.guardar_producto()
        # ==========================
    # CONVERTIR NUMERO
    # ==========================

    def convertir_numero(self, texto):

        numero = parse_number(texto)

        if numero is None:
            return 0

        return numero



    # ==========================
    # CALCULAR PRECIO
    # ==========================

    def calcular_precio(self):

        if self.calculando:
            return


        self.calculando = True


        try:

            compra = self.convertir_numero(
                self.input_compra.text()
            )


            ganancia = self.convertir_numero(
                self.input_ganancia.text()
            )


            precio = compra + (
                compra * ganancia / 100
            )


            if compra:

                self.input_venta.setText(
                    f"{precio:.2f}"
                )


        except Exception as e:

            print(
                "ERROR CALCULO:",
                e
            )


        self.calculando = False




# ==========================
# GUARDAR PRODUCTO
# ==========================

    def guardar_producto(self):

        nombre = self.input_nombre.text().strip()

        if not nombre:
            DialogoAviso(
                "Falta nombre",
                "Ingresá el nombre del producto.",
                self
            ).exec()

            self.input_nombre.setFocus()
            return


        producto = {

            "codigo_barras":
                self.input_codigo.text().strip() or None,

            "nombre":
                nombre,

            "categoria":
                self.input_categoria.currentText(),

            "precio_compra":
                self.convertir_numero(
                    self.input_compra.text()
                ),

            "precio_venta":
                self.convertir_numero(
                    self.input_venta.text()
                ),

            "stock":
                int(
                    self.convertir_numero(
                        self.input_stock.text()
                    )
                ),

            "stock_minimo": 5
        }


        try:

            init_db()

            conexion = create_connection()
            cursor = conexion.cursor()


            producto_uuid = str(uuid.uuid4())


            cursor.execute("""
            INSERT INTO productos
            (
                uuid,
                codigo_barras,
                nombre,
                categoria,
                precio_compra,
                precio_venta,
                stock,
                stock_minimo
            )
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                producto_uuid,
                producto["codigo_barras"],
                producto["nombre"],
                producto["categoria"],
                producto["precio_compra"],
                producto["precio_venta"],
                producto["stock"],
                producto["stock_minimo"]
            ))


            producto_id = cursor.lastrowid


            producto["uuid"] = producto_uuid


            cursor.execute("""
            INSERT INTO sincronizacion
            (
                tabla,
                registro,
                registro_uuid,
                accion,
                datos,
                fecha,
                sincronizado
            )
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                "productos",
                producto_id,
                producto_uuid,
                "crear",
                json.dumps(producto),
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                0
            ))


            conexion.commit()

            print("PRODUCTO GUARDADO UUID:", producto_uuid)

            print(
                "SYNC INSERTADO:",
                cursor.execute(
                    "SELECT * FROM sincronizacion ORDER BY id DESC LIMIT 1"
                ).fetchone()
            )

            conexion.close()


            DialogoAviso(
                "Producto guardado",
                "✅ Producto guardado en la PC.\nQuedó pendiente de sincronización.",
                self
            ).exec()


            self.producto_guardado.emit()
            self.close()


        except Exception as e:

            DialogoAviso(
                "Error al guardar",
                str(e),
                self
            ).exec()

# ==========================
# EJECUTAR DIRECTO
# ==========================

if __name__ == "__main__":


    from PySide6.QtWidgets import QApplication


    app = QApplication(sys.argv)


    ventana = AgregarProducto()


    ventana.show()


    sys.exit(
        app.exec()
    )   
        
        
        
        