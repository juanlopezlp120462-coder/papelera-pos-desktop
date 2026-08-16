import sys
import datetime
import sqlite3
import json

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


# ============================================================
# AVISO
# ============================================================

class DialogoAviso(QDialog):

    def __init__(self, titulo, mensaje, parent=None):

        super().__init__(parent)

        self.setWindowTitle(titulo)
        self.setFixedSize(390, 170)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog {
                background: white;
                border-radius: 15px;
            }

            QLabel {
                color: #0f172a;
                font-size: 15px;
            }

            QPushButton {
                background: #2563eb;
                color: white;
                border-radius: 10px;
                padding: 10px 25px;
                font-weight: bold;
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


# ============================================================
# EDITAR PRODUCTO
# ============================================================

class EditarProducto(QWidget):

    producto_actualizado = Signal()

    def __init__(self, prod_id, prod_uuid):

        super().__init__()

        self.prod_id = prod_id
        self.prod_uuid = prod_uuid

        self._actualizando_campos = False

        self.setWindowTitle(
            "✏️ Editar Producto - Abril POS"
        )

        self.resize(
            600,
            760
        )

        self.setStyleSheet("""
            QWidget {
                background: #f8fafc;
                font-family: 'Segoe UI';
                color: #0f172a;
            }

            QLabel {
                font-size: 14px;
                font-weight: 600;
            }

            QLineEdit,
            QComboBox {
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 14px;
                padding: 12px 16px;
                font-size: 15px;
                color: #0f172a;
            }

            QLineEdit:focus,
            QComboBox:focus {
                border: 2px solid #2563eb;
            }

            QPushButton {
                border-radius: 12px;
                padding: 13px;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton#guardar {
                background: #2563eb;
                color: white;
            }

            QPushButton#guardar:hover {
                background: #1d4ed8;
            }

            QPushButton#cancelar {
                background: #e2e8f0;
                color: #334155;
            }

            QPushButton#cancelar:hover {
                background: #cbd5e1;
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
                background: white;
                border-radius: 20px;
                border: 1px solid #e2e8f0;
            }
        """)

        sombra = QGraphicsDropShadowEffect()

        sombra.setBlurRadius(30)
        sombra.setXOffset(0)
        sombra.setYOffset(6)

        sombra.setColor(
            QColor(0, 0, 0, 35)
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

        # ====================================================
        # TITULO
        # ====================================================

        titulo = QLabel(
            "✏️ Editar Producto"
        )

        titulo.setStyleSheet("""
            font-size: 28px;
            font-weight: 800;
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

        # ====================================================
        # CODIGO DE BARRAS
        # ====================================================

        formulario.addWidget(
            QLabel("🏷️ Código de barras")
        )

        self.codigo_barras = QLineEdit()

        self.codigo_barras.setPlaceholderText(
            "Código de barras"
        )

        formulario.addWidget(
            self.codigo_barras
        )

        # ====================================================
        # NOMBRE
        # ====================================================

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

        # ====================================================
        # CATEGORIA
        # ====================================================

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

        # ====================================================
        # PRECIOS
        # ====================================================

        fila_precios = QHBoxLayout()

        fila_precios.setSpacing(
            12
        )

        # ----------------------------------------------------
        # PRECIO COMPRA
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # GANANCIA
        # ----------------------------------------------------

        caja_ganancia = QVBoxLayout()

        caja_ganancia.addWidget(
            QLabel("📈 Ganancia (%)")
        )

        self.ganancia = QLineEdit()

        setup_numeric(
            self.ganancia,
            2
        )

        self.ganancia.setPlaceholderText(
            "Ej: 50"
        )

        caja_ganancia.addWidget(
            self.ganancia
        )

        # ----------------------------------------------------
        # PRECIO VENTA
        # ----------------------------------------------------

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
            caja_ganancia
        )

        fila_precios.addLayout(
            caja_venta
        )

        formulario.addLayout(
            fila_precios
        )

        # ====================================================
        # CONEXIONES DE PRECIOS
        # ====================================================

        self.ganancia.editingFinished.connect(
            self.calcular_venta_desde_ganancia
        )

        self.venta.editingFinished.connect(
            self.calcular_ganancia_desde_venta
        )

        self.compra.editingFinished.connect(
            self.recalcular_desde_compra
        )

        # ====================================================
        # STOCK
        # ====================================================

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

        self.stock.setProperty(
            "keyboard_last",
            True
        )

        formulario.addWidget(
            self.stock
        )

        # ====================================================
        # ORDEN DEL ENTER
        # ====================================================

        self._keyboard_enter_sequence = [

            self.codigo_barras,

            self.nombre,

            self.categoria,

            self.compra,

            self.ganancia,

            self.venta,

            self.stock

        ]

        # ====================================================
        # BOTONES
        # ====================================================

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

        # ====================================================
        # CARGAR DATOS
        # ====================================================

        self.cargar_datos()

    # ========================================================
    # ENTER DEL TECLADO
    # ========================================================

    def keyboard_submit(self):

        self.guardar()

    # ========================================================
    # CALCULAR VENTA DESDE GANANCIA
    # ========================================================

    def calcular_venta_desde_ganancia(self):

        if self._actualizando_campos:
            return

        try:

            compra = parse_number(
                self.compra.text()
            ) or 0

            ganancia = parse_number(
                self.ganancia.text()
            ) or 0

            if compra <= 0:
                return

            if ganancia < 0:
                ganancia = 0

            venta = compra * (
                1 + (ganancia / 100)
            )

            self._actualizando_campos = True

            self.venta.setText(
                f"{venta:.2f}"
            )

            self._actualizando_campos = False

        except Exception:

            self._actualizando_campos = False

    # ========================================================
    # CALCULAR GANANCIA DESDE VENTA
    # ========================================================

    def calcular_ganancia_desde_venta(self):

        if self._actualizando_campos:
            return

        try:

            compra = parse_number(
                self.compra.text()
            ) or 0

            venta = parse_number(
                self.venta.text()
            ) or 0

            if compra <= 0:
                self.ganancia.setText("0")
                return

            ganancia = (
                (venta - compra)
                / compra
            ) * 100

            self._actualizando_campos = True

            self.ganancia.setText(
                f"{ganancia:.2f}"
            )

            self._actualizando_campos = False

        except Exception:

            self._actualizando_campos = False

    # ========================================================
    # RECALCULAR AL CAMBIAR COMPRA
    # ========================================================

    def recalcular_desde_compra(self):

        if self._actualizando_campos:
            return

        try:

            compra = parse_number(
                self.compra.text()
            ) or 0

            ganancia = parse_number(
                self.ganancia.text()
            ) or 0

            if compra <= 0:
                return

            if ganancia < 0:
                ganancia = 0

            venta = compra * (
                1 + (ganancia / 100)
            )

            self._actualizando_campos = True

            self.venta.setText(
                f"{venta:.2f}"
            )

            self._actualizando_campos = False

        except Exception:

            self._actualizando_campos = False

    # ========================================================
    # CARGAR DATOS DEL PRODUCTO
    # ========================================================

    def cargar_datos(self):

        try:

            conexion = create_connection()

            conexion.row_factory = sqlite3.Row

            cursor = conexion.cursor()

            producto = cursor.execute("""
                SELECT *
                FROM productos
                WHERE id=?
            """, (
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

            # =================================================
            # CODIGO DE BARRAS
            # =================================================

            self.codigo_barras.setText(
                str(
                    producto["codigo_barras"] or ""
                )
            )

            # =================================================
            # NOMBRE
            # =================================================

            self.nombre.setText(
                producto["nombre"] or ""
            )

            # =================================================
            # CATEGORIA
            # =================================================

            categoria = (
                producto["categoria"]
                or "Otro"
            )

            categorias = {
                "Cotillon": 0,
                "Cotillón": 0,
                "Papelera": 1,
                "Otro": 2
            }

            self.categoria.setCurrentIndex(
                categorias.get(
                    categoria,
                    2
                )
            )

            # =================================================
            # PRECIOS
            # =================================================

            precio_compra = float(
                producto["precio_compra"] or 0
            )

            precio_venta = float(
                producto["precio_venta"] or 0
            )

            self._actualizando_campos = True

            self.compra.setText(
                f"{precio_compra:.2f}"
            )

            self.venta.setText(
                f"{precio_venta:.2f}"
            )

            # =================================================
            # CALCULAR GANANCIA
            # =================================================

            if precio_compra > 0:

                ganancia = (
                    (
                        precio_venta
                        - precio_compra
                    )
                    / precio_compra
                ) * 100

                self.ganancia.setText(
                    f"{ganancia:.2f}"
                )

            else:

                self.ganancia.setText(
                    "0"
                )

            self._actualizando_campos = False

            # =================================================
            # STOCK
            # =================================================

            self.stock.setText(
                str(
                    producto["stock"] or 0
                )
            )

        except Exception as e:

            self._actualizando_campos = False

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo cargar el producto:\n{e}"
            )

    # ========================================================
    # GUARDAR CAMBIOS
    # ========================================================

    def guardar(self):

        print("ENTRO A GUARDAR")

        try:

            # =================================================
            # CATEGORIA
            # =================================================

            categoria_texto = (
                self.categoria.currentText()
            )

            if "Cotillón" in categoria_texto:
                categoria = "Cotillon"

            elif "Papelera" in categoria_texto:
                categoria = "Papelera"

            else:
                categoria = "Otro"

            # =================================================
            # DATOS
            # =================================================

            codigo_barras = (
                self.codigo_barras.text().strip()
            )

            nombre = (
                self.nombre.text().strip()
            )

            precio_compra = (
                parse_number(
                    self.compra.text()
                ) or 0
            )

            precio_venta = (
                parse_number(
                    self.venta.text()
                ) or 0
            )

            ganancia = (
                parse_number(
                    self.ganancia.text()
                ) or 0
            )

            stock = int(
                parse_number(
                    self.stock.text()
                ) or 0
            )

            # =================================================
            # VALIDACIONES
            # =================================================

            if not nombre:

                QMessageBox.warning(
                    self,
                    "Producto",
                    "Ingresá el nombre del producto."
                )

                self.nombre.setFocus()

                return

            if precio_compra < 0:

                QMessageBox.warning(
                    self,
                    "Precio de compra",
                    "El precio de compra no puede ser negativo."
                )

                self.compra.setFocus()

                return

            if precio_venta < 0:

                QMessageBox.warning(
                    self,
                    "Precio de venta",
                    "El precio de venta no puede ser negativo."
                )

                self.venta.setFocus()

                return

            if ganancia < 0:

                QMessageBox.warning(
                    self,
                    "Ganancia",
                    "El porcentaje de ganancia no puede ser negativo."
                )

                self.ganancia.setFocus()

                return

            if stock < 0:

                QMessageBox.warning(
                    self,
                    "Stock",
                    "El stock no puede ser negativo."
                )

                self.stock.setFocus()

                return

            # =================================================
            # DATOS PARA GUARDAR
            # =================================================

            datos = {

                "codigo_barras":
                    codigo_barras,

                "nombre":
                    nombre,

                "categoria":
                    categoria,

                "precio_compra":
                    precio_compra,

                "precio_venta":
                    precio_venta,

                "stock":
                    stock
            }

            # =================================================
            # CONEXION
            # =================================================

            conexion = create_connection()

            cursor = conexion.cursor()

            # =================================================
            # ACTUALIZAR PRODUCTO LOCAL
            # =================================================

            cursor.execute("""
                UPDATE productos
                SET
                    codigo_barras=?,
                    nombre=?,
                    categoria=?,
                    precio_compra=?,
                    precio_venta=?,
                    stock=?
                WHERE id=?
            """,
            (
                datos["codigo_barras"],
                datos["nombre"],
                datos["categoria"],
                datos["precio_compra"],
                datos["precio_venta"],
                datos["stock"],
                self.prod_id
            ))

            # =================================================
            # VERIFICAR ACTUALIZACION
            # =================================================

            if cursor.rowcount != 1:

                raise Exception(
                    "No se pudo actualizar el producto "
                    "en la base local."
                )

            # =================================================
            # MARCAR PARA SINCRONIZAR
            # =================================================

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
                    ?, ?, ?, ?, ?, ?
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

            # =================================================
            # CONFIRMAR
            # =================================================

            conexion.commit()

            conexion.close()

            # =================================================
            # AVISAR AL PADRE
            # =================================================

            self.producto_actualizado.emit()

            # =================================================
            # MENSAJE
            # =================================================

            aviso = DialogoAviso(
                "Producto actualizado",
                "✅ Producto actualizado en la PC.\n\n"
                "Quedó pendiente de sincronización.",
                self
            )

            aviso.exec()

            # =================================================
            # CERRAR
            # =================================================

            self.close()

        except Exception as e:

            try:
                conexion.rollback()
                conexion.close()
            except Exception:
                pass

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo actualizar:\n{e}"
            )


# ============================================================
# EJECUTAR DIRECTO
# ============================================================

if __name__ == "__main__":

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # IMPORTANTE:
    # Para probar directamente necesitás pasar también
    # el UUID real del producto.
    ventana = EditarProducto(
        1,
        ""
    )

    ventana.show()

    sys.exit(
        app.exec()
    )