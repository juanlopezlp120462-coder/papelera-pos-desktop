import sys
import datetime
import requests
import sqlite3
import json
import datetime
from ui.db import create_connection

from PySide6.QtWidgets import (
    QMessageBox,
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

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

from ui.keyboard import setup_numeric, parse_number


SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"



class DialogoAviso(QDialog):

    def __init__(self, titulo, mensaje, parent=None):

        super().__init__(parent)

        self.setWindowTitle(titulo)
        self.setFixedSize(390,170)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog {
                background:white;
                border-radius:15px;
            }

            QLabel {
                color:#0f172a;
                font-size:15px;
            }

            QPushButton {
                background:#2563eb;
                color:white;
                border-radius:10px;
                padding:10px 25px;
                font-weight:bold;
            }
        """)


        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            25,
            25,
            25,
            25
        )


        fila = QHBoxLayout()


        icono = QLabel("✅")
        icono.setStyleSheet(
            "font-size:30px;"
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





class EditarProducto(QWidget):

    producto_actualizado = Signal()


    def __init__(self, prod_id, prod_uuid):

        super().__init__()


        self.prod_id = prod_id
        self.prod_uuid = prod_uuid


        self.setWindowTitle(
            "✏️ Editar Producto - Abril POS"
        )


        self.resize(
            560,
            700
        )



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
                border-radius:14px;
                padding:12px 16px;
                font-size:15px;
                color:#0f172a;

            }


            QLineEdit:focus,
            QComboBox:focus {

                border:2px solid #2563eb;

            }


            QPushButton {

                border-radius:12px;
                padding:13px;
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



        principal = QVBoxLayout(self)


        principal.setContentsMargins(
            35,
            35,
            35,
            35
        )



        tarjeta = QFrame()


        tarjeta.setStyleSheet("""
            QFrame {
                background:white;
                border-radius:20px;
                border:1px solid #e2e8f0;
            }
        """)



        sombra = QGraphicsDropShadowEffect()

        sombra.setBlurRadius(30)

        sombra.setXOffset(0)

        sombra.setYOffset(6)

        sombra.setColor(
            QColor(0,0,0,35)
        )


        tarjeta.setGraphicsEffect(
            sombra
        )



        formulario = QVBoxLayout(
            tarjeta
        )


        formulario.setContentsMargins(
            35,
            35,
            35,
            35
        )


        formulario.setSpacing(
            15
        )



        titulo = QLabel(
            "✏️ Editar Producto"
        )


        titulo.setStyleSheet("""
            font-size:28px;
            font-weight:800;
        """)


        formulario.addWidget(
            titulo
        )



        subtitulo = QLabel(
            "Actualizá la información del producto"
        )


        subtitulo.setStyleSheet(
            "color:#64748b;"
        )


        formulario.addWidget(
            subtitulo
        )


        formulario.addSpacing(10)
        # ===============================
        # NOMBRE
        # ===============================

        formulario.addWidget(
            QLabel("📝 Nombre del producto")
        )


        self.nombre = QLineEdit()

        self.nombre.setPlaceholderText(
            "Ej: Vasos descartables"
        )


        formulario.addWidget(
            self.nombre
        )



        # ===============================
        # CATEGORIA
        # ===============================

        formulario.addWidget(
            QLabel("📂 Categoría")
        )


        self.categoria = QComboBox()


        self.categoria.addItems([
            "🎉  Cotillón",
            "📄  Papelera",
            "📦  Otro"
        ])


        formulario.addWidget(
            self.categoria
        )



        # ===============================
        # PRECIOS
        # ===============================

        fila_precios = QHBoxLayout()


        fila_precios.setSpacing(
            15
        )


        caja_compra = QVBoxLayout()


        caja_compra.addWidget(
            QLabel("💰 Precio compra")
        )


        self.compra = QLineEdit()


        setup_numeric(
            self.compra,
            2
        )


        self.compra.setPlaceholderText(
            "$ 0.00"
        )


        caja_compra.addWidget(
            self.compra
        )



        caja_venta = QVBoxLayout()


        caja_venta.addWidget(
            QLabel("💵 Precio venta")
        )


        self.venta = QLineEdit()


        setup_numeric(
            self.venta,
            2
        )


        self.venta.setPlaceholderText(
            "$ 0.00"
        )


        caja_venta.addWidget(
            self.venta
        )



        fila_precios.addLayout(
            caja_compra
        )


        fila_precios.addLayout(
            caja_venta
        )


        formulario.addLayout(
            fila_precios
        )



        # ===============================
        # STOCK
        # ===============================


        formulario.addWidget(
            QLabel("📦 Stock disponible")
        )


        self.stock = QLineEdit()


        setup_numeric(
            self.stock,
            0
        )


        self.stock.setPlaceholderText(
            "Cantidad"
        )


        # ESTE ES EL ULTIMO CAMPO
        # ENTER AQUI GUARDA

        self.stock.setProperty(
            "keyboard_last",
            True
        )


        formulario.addWidget(
            self.stock
        )



        # ===============================
        # ORDEN DEL ENTER
        # ===============================


        self._keyboard_enter_sequence = [

            self.nombre,

            self.categoria,

            self.compra,

            self.venta,

            self.stock

        ]



        # ===============================
        # BOTONES
        # ===============================


        botones = QHBoxLayout()


        botones.setSpacing(
            15
        )



        btn_cancelar = QPushButton(
            "❌ Cancelar"
        )


        btn_cancelar.setObjectName(
            "cancelar"
        )


        btn_cancelar.clicked.connect(
            self.close
        )



        btn_guardar = QPushButton(
            "💾 Guardar cambios"
        )


        btn_guardar.setObjectName(
            "guardar"
        )


        btn_guardar.setProperty(
            "keyboard_primary",
            True
        )


        btn_guardar.clicked.connect(
            self.guardar
        )



        botones.addWidget(
            btn_cancelar
        )


        botones.addWidget(
            btn_guardar
        )


        formulario.addLayout(
            botones
        )



        principal.addWidget(
            tarjeta
        )



        self.cargar_datos()
        # ===============================
        # ENTER DEL TECLADO GLOBAL
        # ===============================

    def keyboard_submit(self):

        self.guardar()



        # ===============================
        # CARGAR DATOS DEL PRODUCTO LOCAL
        # ===============================

    def cargar_datos(self):

        try:

            conexion = create_connection()

            conexion.row_factory = sqlite3.Row

            cursor = conexion.cursor()


            producto = cursor.execute("""
                SELECT *
                FROM productos
                WHERE id=?
            """,
            (
                self.prod_id,
            )).fetchone()


            conexion.close()


            if not producto:

                QMessageBox.warning(
                    self,
                    "Error",
                    "No se encontró el producto en la base local."
                )

                return



            self.nombre.setText(
                producto["nombre"] or ""
            )


            categoria = producto["categoria"] or "Otro"


            categorias = {
                "Cotillon":0,
                "Cotillón":0,
                "Papelera":1,
                "Otro":2
            }


            self.categoria.setCurrentIndex(
                categorias.get(
                    categoria,
                    2
                )
            )


            self.compra.setText(
                str(
                    producto["precio_compra"] or 0
                )
            )


            self.venta.setText(
                str(
                    producto["precio_venta"] or 0
                )
            )


            self.stock.setText(
                str(
                    producto["stock"] or 0
                )
            )


        except Exception as e:


            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo cargar el producto:\n{e}"
            )





    # ===============================
    # GUARDAR CAMBIOS
    # ===============================

    def guardar(self):

        print("ENTRO A GUARDAR")


        try:

            categoria_texto = self.categoria.currentText()


            if "Cotillón" in categoria_texto:
                categoria = "Cotillon"

            elif "Papelera" in categoria_texto:
                categoria = "Papelera"

            else:
                categoria = "Otro"



            datos = {

                "nombre":
                    self.nombre.text().strip(),

                "categoria":
                    categoria,

                "precio_compra":
                    parse_number(
                        self.compra.text()
                    ) or 0,

                "precio_venta":
                    parse_number(
                        self.venta.text()
                    ) or 0,

                "stock":
                    int(
                        parse_number(
                            self.stock.text()
                        ) or 0
                    )
            }



            conexion = create_connection()

            cursor = conexion.cursor()



            # ============================
            # ACTUALIZAR PRODUCTO LOCAL
            # ============================

            cursor.execute("""
                UPDATE productos
                SET
                    nombre=?,
                    categoria=?,
                    precio_compra=?,
                    precio_venta=?,
                    stock=?
                WHERE id=?
            """,
            (
                datos["nombre"],
                datos["categoria"],
                datos["precio_compra"],
                datos["precio_venta"],
                datos["stock"],
                self.prod_id
            ))



            # ============================
            # MARCAR PARA SINCRONIZAR
            # ============================

            import json

            cursor.execute("""
                INSERT INTO sincronizacion
                (
                    tabla,
                    registro_uuid,
                    accion,
                    datos,
                    fecha,
                    sincronizado
                )
                VALUES
                (
                    ?,?,?,?,?,?
                )
            """,
            (
                "productos",
                self.prod_uuid,
                "UPDATE",
                json.dumps({
                    "uuid": self.prod_uuid,
                    **datos
                }),
                datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                0
            ))



            conexion.commit()
            conexion.close()



            self.producto_actualizado.emit()



            aviso = DialogoAviso(
                "Producto actualizado",
                "✅ Producto actualizado en la PC.\nQuedó pendiente de sincronización.",
                self
            )

            aviso.exec()



            self.close()



        except Exception as e:


            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo actualizar:\n{e}"
            )
            
# ===============================
# EJECUTAR DIRECTO
# ===============================

if __name__ == "__main__":


    from PySide6.QtWidgets import QApplication


    app = QApplication(sys.argv)


    ventana = EditarProducto(
        1
    )


    ventana.show()


    sys.exit(
        app.exec()
    )
        
        