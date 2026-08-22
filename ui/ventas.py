import sys
import os
import sqlite3
import datetime
import uuid
import json
import requests
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QComboBox,
    QCompleter,
    QHeaderView,
    QFrame,
    QStyledItemDelegate,
    QInputDialog,
    QDialog,
    QTextEdit,
    QFormLayout,
    QListWidget,
    QListWidgetItem,
    QDoubleSpinBox,
    QSizePolicy
)
from PySide6.QtCore import Qt, QLocale, QTimer, Signal

from ui.ticket import (
    generar_ticket,
    imprimir_ticket
)
from ui.api import (
    listar_productos,
    listar_clientes,
    crear_venta


)

from ui.db import BASE_DATOS, init_db, get_setting, create_connection
from ui.keyboard import setup_numeric, parse_number, format_number

from ui.api import (
    listar_productos,
    listar_clientes,
    crear_venta,
    actualizar_producto,
)

CARPETA_DB = os.path.dirname(BASE_DATOS)


def inicializar_base_datos_si_no_existe():
    """Crea la carpeta y las tablas necesarias si la base de datos está vacía o no existe."""
    if not os.path.exists(CARPETA_DB):
        os.makedirs(CARPETA_DB)

    conexion = sqlite3.connect(BASE_DATOS)
    cursor = conexion.cursor()

    # Crear tabla productos si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_barras TEXT,
            nombre TEXT NOT NULL,
            precio_costo REAL,
            porcentaje_ganancia REAL,
            precio_venta REAL NOT NULL,
            stock INTEGER DEFAULT 0
        )
    """)

    # Crear tabla clientes si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT
        )
    """)

    # Crear tabla ventas si no existe (¡Aquí se soluciona el error!)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE,
            fecha TEXT NOT NULL,
            total REAL NOT NULL,
            forma_pago TEXT,
            cliente_id INTEGER
        )
    """)

    # Crear tabla detalle_ventas si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER,
            producto TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio REAL NOT NULL,
            subtotal REAL NOT NULL,
            codigo TEXT
        )
    """)

    # Migraciones seguras para bases creadas con versiones anteriores.
    def agregar_columna_si_falta(tabla, columna, definicion):
        columnas = {fila[1] for fila in cursor.execute(f"PRAGMA table_info({tabla})").fetchall()}
        if columna not in columnas:
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")

    for columna, definicion in (
        ('pago_efectivo', 'REAL DEFAULT 0'),
        ('pago_transferencia', 'REAL DEFAULT 0'),
        ('pago_tarjeta', 'REAL DEFAULT 0'),
        ('pago_cuenta', 'REAL DEFAULT 0'),
    ):
        agregar_columna_si_falta('ventas', columna, definicion)

    agregar_columna_si_falta('detalle_ventas', 'codigo', 'TEXT')

    # Asegurar que las columnas nuevas también existan en las tablas de historial.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas_archivo (
            id INTEGER PRIMARY KEY, fecha TEXT, total REAL, forma_pago TEXT, cliente_id INTEGER,
            estado TEXT, descuento REAL DEFAULT 0, usuario TEXT,
            pago_efectivo REAL DEFAULT 0, pago_transferencia REAL DEFAULT 0,
            pago_tarjeta REAL DEFAULT 0, pago_cuenta REAL DEFAULT 0, archivada_en TEXT
        )
    """)
    for columna, definicion in (
        ('pago_efectivo', 'REAL DEFAULT 0'),
        ('pago_transferencia', 'REAL DEFAULT 0'),
        ('pago_tarjeta', 'REAL DEFAULT 0'),
        ('pago_cuenta', 'REAL DEFAULT 0'),
        ('estado', 'TEXT'), ('descuento', 'REAL DEFAULT 0'), ('usuario', 'TEXT'), ('archivada_en', 'TEXT')
    ):
        agregar_columna_si_falta('ventas_archivo', columna, definicion)

    conexion.commit()
    conexion.close()


class DialogoAviso(QDialog):
    """Ventana profesional de avisos del POS."""

    def __init__(self, titulo, mensaje, parent=None):

        super().__init__(parent)


        self.setWindowTitle(
            titulo
        )


        self.setFixedSize(
            460,
            300
        )


        self.setModal(
            True
        )


        self.setWindowFlags(
            Qt.Dialog |
            Qt.WindowTitleHint |
            Qt.CustomizeWindowHint
        )


        self.setStyleSheet(
            """
            QDialog {

                background:#f8fafc;
                border-radius:18px;

            }


            QLabel#titulo {

                font-size:22px;
                font-weight:900;
                color:#0f172a;

            }


            QLabel#mensaje {

                font-size:15px;
                color:#334155;

            }


            QLabel#icono {

                font-size:48px;

            }


            QFrame#card {

                background:white;
                border-radius:16px;
                border:1px solid #e2e8f0;

            }


            QPushButton {

                background:#2563eb;
                color:white;
                border-radius:10px;
                padding:12px 35px;
                font-size:15px;
                font-weight:700;

            }


            QPushButton:hover {

                background:#1d4ed8;

            }

            """
        )



        principal = QVBoxLayout(
            self
        )


        principal.setContentsMargins(
            25,
            25,
            25,
            25
        )


        principal.setSpacing(
            15
        )



        card = QFrame()


        card.setObjectName(
            "card"
        )


        card_layout = QVBoxLayout(
            card
        )


        card_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )


        card_layout.setSpacing(
            12
        )



        icono = QLabel(
            "✅"
        )


        icono.setObjectName(
            "icono"
        )


        icono.setAlignment(
            Qt.AlignCenter
        )



        lbl_titulo = QLabel(
            titulo
        )


        lbl_titulo.setObjectName(
            "titulo"
        )


        lbl_titulo.setAlignment(
            Qt.AlignCenter
        )



        lbl_mensaje = QLabel(
            mensaje
        )


        lbl_mensaje.setObjectName(
            "mensaje"
        )


        lbl_mensaje.setAlignment(
            Qt.AlignCenter
        )


        lbl_mensaje.setWordWrap(
            True
        )



        card_layout.addWidget(
            icono
        )


        card_layout.addWidget(
            lbl_titulo
        )


        card_layout.addWidget(
            lbl_mensaje
        )



        principal.addWidget(
            card
        )



        botones = QHBoxLayout()


        botones.addStretch()



        self.btn_ok = QPushButton(
            "Aceptar"
        )


        self.btn_ok.setCursor(
            Qt.PointingHandCursor
        )


        self.btn_ok.clicked.connect(
            self.accept
        )



        botones.addWidget(
            self.btn_ok
        )


        botones.addStretch()



        principal.addLayout(
            botones
        )

class EditorCeldaVentasDelegate(QStyledItemDelegate):
    """Delegado para asegurar que los editores de celdas de la tabla se vean grandes y proporcionados."""
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        setup_numeric(editor, 2)
        editor.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #0f172a;
                border: 2px solid #3b82f6;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
                padding: 4px 8px;
            }
        """)
        return editor

    def updateEditorGeometry(self, editor, option, index):
        rect = option.rect
        editor.setGeometry(rect.x() + 2, rect.y() + 2, rect.width() - 4, rect.height() - 4)


class DialogoPagoMixto(QDialog):

    pago_confirmado = Signal(dict)

    def __init__(self, total, parent=None):

        super().__init__(parent)

        self.total = total

        self.setWindowTitle("Forma de pago")
        self.setModal(True)
        self.setFixedSize(520, 460)


        self._esperando = False
        self._inicio_espera = None


        self._timer = QTimer(self)
        self._timer.setInterval(2500)
        self._timer.timeout.connect(
            self._buscar_pago_mp
        )


        self.setStyleSheet("""
            QDialog {
                background:#f8fafc;
            }

            QLabel {
                color:#0f172a;
            }

            QDoubleSpinBox {
                background:white;
                border:1px solid #cbd5e1;
                border-radius:9px;
                padding:8px;
                font-size:16px;
            }

            QPushButton {
                background:#10b981;
                color:white;
                border:0;
                border-radius:9px;
                padding:10px 16px;
                font-weight:800;
            }

            QPushButton#cancel {
                background:#e2e8f0;
                color:#334155;
            }

            QPushButton#mp {
                background:#2563eb;
            }
        """)


        lay = QVBoxLayout(self)


        title = QLabel(
            "💳 ¿Cómo pagó el cliente?"
        )

        title.setStyleSheet(
            "font-size:21px;font-weight:900;"
        )

        lay.addWidget(title)



        info = QLabel(
            f"Total de la venta: $ {total:,.2f}"
        )

        info.setStyleSheet("""
            font-size:18px;
            font-weight:900;
            color:#166534;
            background:#f0fdf4;
            border:1px solid #bbf7d0;
            border-radius:9px;
            padding:10px;
        """)

        lay.addWidget(info)



        form = QFormLayout()


        self.ef = QDoubleSpinBox()
        self.tr = QDoubleSpinBox()
        self.ta = QDoubleSpinBox()
        self.cc = QDoubleSpinBox()



        for w in (
            self.ef,
            self.tr,
            self.ta,
            self.cc
        ):

            w.setRange(
                0,
                total
            )

            w.setDecimals(2)

            w.setSingleStep(
                100
            )

            w.setPrefix(
                "$ "
            )

            w.setLocale(
                QLocale(
                    QLocale.Spanish,
                    QLocale.Argentina
                )
            )

            w.setMaximumWidth(
                250
            )



        # Orden de Enter

        self._keyboard_enter_sequence = (
            self.ef,
            self.tr,
            self.ta,
            self.cc
        )


        for w in self._keyboard_enter_sequence:
            w.setFocusPolicy(
                Qt.StrongFocus
            )


        self.setTabOrder(
            self.ef,
            self.tr
        )

        self.setTabOrder(
            self.tr,
            self.ta
        )

        self.setTabOrder(
            self.ta,
            self.cc
        )



        form.addRow(
            "💵 Efectivo:",
            self.ef
        )

        form.addRow(
            "🔄 Mercado Pago:",
            self.tr
        )

        form.addRow(
            "💳 Tarjeta:",
            self.ta
        )

        form.addRow(
            "📒 Cuenta corriente:",
            self.cc
        )


        lay.addLayout(form)



        self.estado = QLabel()

        self.estado.setWordWrap(
            True
        )

        self.estado.setStyleSheet(
            "font-weight:800;"
        )

        lay.addWidget(
            self.estado
        )



        self.mp_info = QLabel("")

        self.mp_info.setWordWrap(
            True
        )

        lay.addWidget(
            self.mp_info
        )



        for w in (
            self.ef,
            self.tr,
            self.ta,
            self.cc
        ):

            w.valueChanged.connect(
                self.validar
            )



        botones = QHBoxLayout()

        botones.addStretch()



        self.cancel = QPushButton(
            "Cancelar"
        )

        self.cancel.setObjectName(
            "cancel"
        )

        self.cancel.clicked.connect(
            self.reject
        )



        self.ok = QPushButton(
            "Confirmar pago"
        )

        self.ok.setProperty(
            "keyboard_primary",
            True
        )

        self.ok.clicked.connect(
            self.confirmar
        )



        self.mp = QPushButton(
            "🔎 Esperar Mercado Pago"
        )

        self.mp.setObjectName(
            "mp"
        )

        self.mp.clicked.connect(
            self.esperar_mercado_pago
        )



        botones.addWidget(
            self.cancel
        )

        botones.addWidget(
            self.mp
        )

        botones.addWidget(
            self.ok
        )


        lay.addLayout(
            botones
        )


        self.validar()


        self.ef.setFocus(
            Qt.OtherFocusReason
        )



    def suma(self):

        return (
            self.ef.value()
            + self.tr.value()
            + self.ta.value()
            + self.cc.value()
        )



    def validar(self):

        diferencia = round(
            self.total - self.suma(),
            2
        )


        if abs(diferencia) < 0.01:

            texto = "🟢 Importe completo"

            color = "#166534"

        elif diferencia > 0:

            texto = (
                f"⚠️ Falta pagar: $ {diferencia:,.2f}"
            )

            color = "#b45309"

        else:

            texto = (
                f"⚠️ Excede el total: $ {abs(diferencia):,.2f}"
            )

            color = "#b45309"



        self.estado.setText(
            texto
        )

        self.estado.setStyleSheet(
            f"font-weight:800;color:{color};"
        )


        self.mp.setEnabled(
            self.tr.value() > 0
            and abs(diferencia) < 0.01
            and not self._esperando
        )



    def keyboard_submit(self):

        self.confirmar()



    def confirmar(self):

        if abs(self.total - self.suma()) >= 0.01:

            QMessageBox.warning(
                self,
                "Pago incompleto",
                "Los medios de pago deben sumar exactamente el total de la venta."
            )

            return



        if self.tr.value() > 0 and not self._esperando:


            respuesta = QMessageBox.question(
                self,
                "Mercado Pago",
                "Se indicó un pago de Mercado Pago. ¿Querés confirmar manualmente o esperar la acreditación automática?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )


            if respuesta == QMessageBox.Yes:

                self.accept()

                return



            self.esperar_mercado_pago()

            return



        self.accept()



    def esperar_mercado_pago(self):

        if (
            self.tr.value() <= 0
            or abs(self.total - self.suma()) >= 0.01
        ):

            return



        from ui.mercadopago import (
            token_activo,
            nombre_cuenta_activa
        )


        token = token_activo()


        if not token:

            QMessageBox.warning(
                self,
                "Mercado Pago",
                "No hay una cuenta de Mercado Pago activa con Access Token."
            )

            return



        self._esperando = True

        self._inicio_espera = datetime.datetime.now(
            datetime.timezone.utc
        )


        self.mp.setEnabled(False)
        self.ok.setEnabled(False)
        self.cancel.setEnabled(False)



        self.mp_info.setText(
            f"🔵 Esperando acreditación de $ {self.tr.value():,.2f} "
            f"en {nombre_cuenta_activa()}...\n"
            "El POS consulta Mercado Pago automáticamente."
        )


        self._timer.start()



    def _buscar_pago_mp(self):

        try:

            from ui.mercadopago import (
                token_activo,
                buscar_pago_aprobado_por_importe,
                guardar_pagos
            )


            pago = buscar_pago_aprobado_por_importe(
                token_activo(),
                self.tr.value(),
                self._inicio_espera
            )


            if pago:

                guardar_pagos(
                    [pago]
                )


                self._timer.stop()

                self._esperando = False


                self.mp_info.setText(
                    f"✅ Pago encontrado y aprobado. ID: {pago.get('id')}"
                )


                self.ok.setEnabled(True)
                self.cancel.setEnabled(True)

                self.pago_confirmado.emit(self.datos())
                self.accept()


        except Exception:

            self.mp_info.setText(
                "⚠️ No se pudo consultar Mercado Pago. Se reintentará automáticamente."
            )



    def closeEvent(self, event):

        self._timer.stop()

        super().closeEvent(
            event
        )



    def datos(self):

        valores = {

            "efectivo": self.ef.value(),

            "transferencia": self.tr.value(),

            "tarjeta": self.ta.value(),

            "cuenta": self.cc.value()

        }


        usados = [
            k for k,v in valores.items()
            if v > 0
        ]


        nombres = {

            "efectivo":"Efectivo",

            "transferencia":"Mercado Pago",

            "tarjeta":"Tarjeta",

            "cuenta":"Cuenta corriente"

        }


        valores["forma"] = (
            " + ".join(
                nombres[k]
                for k in usados
            )
            if usados
            else "Efectivo"
        )


        return valores
class Ventas(QWidget):
    venta_realizada = Signal()
    def __init__(self):
        super().__init__()

        # ==========================================================
        # INICIALIZACIÓN
        # ==========================================================

        inicializar_base_datos_si_no_existe()

        self.setWindowTitle(
            f"{get_setting('nombre_negocio', 'COTILLON')} POS — Nueva venta"
        )

        self.resize(1200, 760)
        self.setMinimumSize(900, 600)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.carrito = []

        self.setFocusPolicy(
            Qt.StrongFocus
        )

        # ==========================================================
        # ESTILO GENERAL
        # ==========================================================

        self.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                color: #0f172a;
            }

            /* =====================================================
            INPUTS
            ===================================================== */

            QLineEdit,
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 9px 12px;
                font-size: 14px;
                color: #0f172a;
            }

            QLineEdit:focus,
            QComboBox:focus {
                border: 2px solid #3b82f6;
            }

            QComboBox::drop-down {
                border: 0px;
                width: 24px;
            }

            QComboBox QAbstractItemView {
                background-color: white;
                color: #1e293b;
                selection-background-color: #e0e7ff;
                selection-color: #3730a3;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
            }

            /* =====================================================
            TABLA PRINCIPAL
            ===================================================== */

            QTableWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                gridline-color: #e5e7eb;
                font-size: 15px;
                color: #334155;
                selection-background-color: #dbeafe;
                selection-color: #1e3a8a;
            }

            QTableWidget::item {
                padding: 7px 10px;
                color: #334155;
            }

            QTableWidget::item:selected {
                background-color: #dbeafe;
                color: #1e3a8a;
                font-weight: bold;
            }

            QHeaderView::section {
                background-color: #0f172a;
                color: white;
                padding: 11px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }

            /* =====================================================
            BOTONES GENERALES
            ===================================================== */

            QPushButton {
                background-color: #0ea5e9;
                color: white;
                border-radius: 8px;
                padding: 9px 14px;
                font-weight: 600;
                border: none;
            }

            QPushButton:hover {
                background-color: #0284c7;
            }

            QPushButton:pressed {
                background-color: #0369a1;
            }

            /* =====================================================
            BOTÓN ELIMINAR
            ===================================================== */

            QPushButton#btnEliminar {
                background-color: #fee2e2;
                color: #dc2626;
                border: 1px solid #fecaca;
            }

            QPushButton#btnEliminar:hover {
                background-color: #ef4444;
                color: white;
            }

            /* =====================================================
            BOTONES F2 - F11
            ===================================================== */

            QPushButton#atajo {
                background-color: #334155;
                color: white;
                border-radius: 6px;
                padding: 5px 9px;
                font-size: 12px;
                font-weight: 700;
                min-height: 28px;
            }

            QPushButton#atajo:hover {
                background-color: #475569;
            }

            QPushButton#atajo:pressed {
                background-color: #1e293b;
            }
        """)

        # ==========================================================
        # LAYOUT PRINCIPAL
        #
        # Ahora la pantalla se organiza verticalmente:
        #
        #   TÍTULO
        #   ATAJOS
        #   BUSCADOR
        #   TABLA GRANDE
        #   BOTONES
        #   CLIENTE / PAGO
        #   TOTAL GRANDE + COBRAR
        #
        # Esto elimina el panel vertical derecho que ocupaba
        # demasiado espacio.
        # ==========================================================

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            18,
            14,
            18,
            14
        )

        main_layout.setSpacing(
            10
        )

        # ==========================================================
        # CABECERA
        # ==========================================================

        encabezado = QHBoxLayout()

        encabezado.setContentsMargins(
            0,
            0,
            0,
            0
        )

        titulo = QLabel(
            "🛒 Nueva Venta"
        )

        titulo.setStyleSheet("""
            font-size: 25px;
            font-weight: 900;
            color: #0f172a;
            padding: 0px;
        """)

        encabezado.addWidget(
            titulo
        )

        encabezado.addStretch()

        main_layout.addLayout(
            encabezado
        )

        # ==========================================================
        # ATAJOS F2 - F11
        # ==========================================================

        accesos_frame = QFrame()

        accesos_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 9px;
            }
        """)

        accesos = QHBoxLayout(
            accesos_frame
        )

        accesos.setContentsMargins(
            6,
            5,
            6,
            5
        )

        accesos.setSpacing(
            5
        )

        accesos.setAlignment(
            Qt.AlignLeft
        )

        for texto, funcion in [
            ("F2 Arqueo", self.abrir_arqueo),
            ("F3 Dotación", self.dotacion),
            ("F4 Descuento", self.aplicar_descuento),
            ("F8 Cobrar", self.cobrar),
            ("F9 Cancelar", self.cancelar_venta),
            ("F10 Consulta", self.consulta_precio),
            ("F11 Buscar", lambda: self.buscar.setFocus())
        ]:

            b = QPushButton(
                texto
            )

            b.setObjectName(
                "atajo"
            )

            b.setCursor(
                Qt.PointingHandCursor
            )

            b.setMinimumHeight(
                29
            )

            b.clicked.connect(
                funcion
            )

            accesos.addWidget(
                b
            )

        accesos.addStretch()

        main_layout.addWidget(
            accesos_frame
        )

        # ==========================================================
        # BUSCADOR
        # ==========================================================

        layout_buscador = QHBoxLayout()

        layout_buscador.setSpacing(
            8
        )

        self.buscar = QLineEdit()

        self.buscar.focusInEvent = (
            self.limpiar_busqueda_al_entrar
        )

        self.buscar.setProperty(
            'keyboard_navigation_skip',
            True
        )

        self.buscar.setPlaceholderText(
            "🔍 Escanee código, busque producto o escriba uno libre y presione Enter..."
        )

        self.buscar.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 11px 15px;
                font-size: 15px;
                color: #0f172a;
            }

            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)

        # Mantener comportamiento actual
        self.buscar.returnPressed.connect(
            self.confirmar_sugerencia
        )

        self.buscar.editingFinished.connect(
            self.limpiar_buscador
        )

        btn_ver_todos = QPushButton(
            "📋 Ver BD"
        )

        btn_ver_todos.setToolTip(
            "Muestra todos los productos guardados en la base de datos"
        )

        btn_ver_todos.setCursor(
            Qt.PointingHandCursor
        )

        btn_ver_todos.clicked.connect(
            self.mostrar_todos_los_productos
        )

        btn_ver_todos.setStyleSheet("""
            QPushButton {
                background-color: #64748b;
                color: white;
                padding: 10px 16px;
                border-radius: 9px;
                font-weight: 700;
            }

            QPushButton:hover {
                background-color: #475569;
            }
        """)

        layout_buscador.addWidget(
            self.buscar,
            stretch=1
        )

        layout_buscador.addWidget(
            btn_ver_todos
        )

        main_layout.addLayout(
            layout_buscador
        )

        # ==========================================================
        # TABLA DE PRODUCTOS
        #
        # ESTA ES AHORA LA PARTE PRINCIPAL DE LA PANTALLA.
        # ==========================================================

        self.tabla = QTableWidget()

        self.tabla.setColumnCount(
            5
        )

        self.tabla.setHorizontalHeaderLabels([
            "Producto",
            "Cant.",
            "Precio Unit.",
            "Subtotal",
            "Código"
        ])

        self.tabla.verticalHeader().setDefaultSectionSize(
            48
        )

        self.tabla.setAlternatingRowColors(
            True
        )

        self.tabla.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.tabla.setSelectionMode(
            QTableWidget.SingleSelection
        )

        header = self.tabla.horizontalHeader()

        # Producto ocupa todo el espacio sobrante
        header.setSectionResizeMode(
            0,
            QHeaderView.Stretch
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeToContents
        )

        self.tabla.setColumnWidth(
            1,
            90
        )

        self.tabla.setColumnWidth(
            2,
            130
        )

        self.tabla.setColumnWidth(
            3,
            145
        )

        self.tabla.setColumnWidth(
            4,
            125
        )

        # La tabla es el elemento que más espacio recibe.
        main_layout.addWidget(
            self.tabla,
            stretch=1
        )

        # ==========================================================
        # BOTONES DE EDICIÓN DEL CARRITO
        # ==========================================================

        botones_tabla = QHBoxLayout()

        botones_tabla.setSpacing(
            8
        )

        btn_sumar = QPushButton(
            "➕ Sumar Cantidad"
        )

        btn_restar = QPushButton(
            "➖ Restar Cantidad"
        )

        btn_eliminar = QPushButton(
            "🗑️ Quitar Ítem"
        )

        btn_eliminar.setObjectName(
            "btnEliminar"
        )

        for btn in [
            btn_sumar,
            btn_restar,
            btn_eliminar
        ]:

            btn.setCursor(
                Qt.PointingHandCursor
            )

            btn.setMinimumHeight(
                36
            )

        btn_sumar.clicked.connect(
            self.sumar_cantidad
        )

        btn_restar.clicked.connect(
            self.restar_cantidad
        )

        btn_eliminar.clicked.connect(
            self.eliminar_producto
        )

        botones_tabla.addWidget(
            btn_sumar
        )

        botones_tabla.addWidget(
            btn_restar
        )

        botones_tabla.addWidget(
            btn_eliminar
        )

        botones_tabla.addStretch()

        main_layout.addLayout(
            botones_tabla
        )

        # ==========================================================
        # DATOS DE LA VENTA
        #
        # Cliente y forma de pago dejan de ocupar una columna
        # vertical gigante.
        # ==========================================================

        datos_venta = QFrame()

        datos_venta.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }

            QLabel {
                background: transparent;
                border: none;
            }
        """)

        datos_layout = QHBoxLayout(
            datos_venta
        )

        datos_layout.setContentsMargins(
            10,
            8,
            10,
            8
        )

        datos_layout.setSpacing(
            8
        )

        # ----------------------------------------------------------
        # CLIENTE
        # ----------------------------------------------------------

        lbl_cliente = QLabel(
            "👤 Cliente:"
        )

        lbl_cliente.setStyleSheet("""
            font-weight: 700;
            color: #475569;
            font-size: 13px;
        """)

        self.cliente = QComboBox()

        self.cliente.setCursor(
            Qt.PointingHandCursor
        )

        self.cliente.setMinimumHeight(
            38
        )

        self.cliente.setMinimumWidth(
            220
        )

        self.cliente.setStyleSheet("""
            QComboBox {
                padding: 8px 10px;
                font-size: 14px;
            }
        """)

        datos_layout.addWidget(
            lbl_cliente
        )

        datos_layout.addWidget(
            self.cliente,
            stretch=1
        )

        # Separador
        separador = QFrame()

        separador.setFixedWidth(
            1
        )

        separador.setStyleSheet(
            "background-color: #e2e8f0; border: none;"
        )

        datos_layout.addWidget(
            separador
        )

        # ----------------------------------------------------------
        # FORMA DE PAGO
        # ----------------------------------------------------------

        lbl_pago = QLabel(
            "💵 Forma de pago:"
        )

        lbl_pago.setStyleSheet("""
            font-weight: 700;
            color: #475569;
            font-size: 13px;
        """)

        self.forma_pago = QComboBox()

        self.forma_pago.setCursor(
            Qt.PointingHandCursor
        )

        self.forma_pago.addItems([
            "Efectivo",
            "Tarjeta",
            "Transferencia",
            "Cuenta corriente"
        ])

        self.forma_pago.setMinimumHeight(
            38
        )

        self.forma_pago.setMinimumWidth(
            190
        )

        self.forma_pago.setStyleSheet("""
            QComboBox {
                padding: 8px 10px;
                font-size: 14px;
            }
        """)

        datos_layout.addWidget(
            lbl_pago
        )

        datos_layout.addWidget(
            self.forma_pago
        )

        main_layout.addWidget(
            datos_venta
        )

        # ==========================================================
        # ZONA FINAL: TOTAL + COBRAR
        #
        # Ahora el total tiene mucho más protagonismo.
        # ==========================================================

        zona_final = QFrame()

        zona_final.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
            }
        """)

        zona_final_layout = QHBoxLayout(
            zona_final
        )

        zona_final_layout.setContentsMargins(
            14,
            10,
            14,
            10
        )

        zona_final_layout.setSpacing(
            14
        )

        # ----------------------------------------------------------
        # TOTAL
        # ----------------------------------------------------------

        cuadro_total = QFrame()

        cuadro_total.setStyleSheet("""
            QFrame {
                background-color: #f0fdf4;
                border: 2px solid #86efac;
                border-radius: 12px;
            }
        """)

        layout_total = QVBoxLayout(
            cuadro_total
        )

        layout_total.setContentsMargins(
            18,
            9,
            18,
            9
        )

        layout_total.setSpacing(
            2
        )

        lbl_total_titulo = QLabel(
            "TOTAL A PAGAR"
        )

        lbl_total_titulo.setStyleSheet("""
            font-size: 12px;
            font-weight: 900;
            color: #15803d;
            letter-spacing: 1px;
            border: none;
            background: transparent;
        """)

        self.total = QLabel(
            "$0,00"
        )

        self.total.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )

        self.total.setStyleSheet("""
            font-size: 32px;
            font-weight: 900;
            color: #166534;
            border: none;
            background: transparent;
        """)

        layout_total.addWidget(
            lbl_total_titulo
        )

        layout_total.addWidget(
            self.total
        )

        zona_final_layout.addWidget(
            cuadro_total,
            stretch=1
        )

        # ----------------------------------------------------------
        # BOTÓN COBRAR
        # ----------------------------------------------------------

        self.boton_cobrar = QPushButton(
            "💰  COBRAR (F8)"
        )

        self.boton_cobrar.setCursor(
            Qt.PointingHandCursor
        )

        self.boton_cobrar.setMinimumHeight(
            70
        )

        self.boton_cobrar.setMinimumWidth(
            230
        )

        self.boton_cobrar.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-size: 18px;
                font-weight: 900;
                padding: 12px 24px;
                border-radius: 12px;
                border: none;
            }

            QPushButton:hover {
                background-color: #059669;
            }

            QPushButton:pressed {
                background-color: #047857;
            }
        """)

        self.boton_cobrar.clicked.connect(
            self.cobrar
        )

        zona_final_layout.addWidget(
            self.boton_cobrar
        )

        main_layout.addWidget(
            zona_final
        )

        # ==========================================================
        # CONEXIONES Y CARGA INICIAL
        # ==========================================================

        self.tabla.itemChanged.connect(
            self.celda_modificada
        )

        # ==========================================================
        # INICIO RÁPIDO DE VENTAS
        # ==========================================================
        # Primero mostramos la pantalla.
        # Los datos se cargan inmediatamente después, sin bloquear
        # la apertura del módulo.

        self.buscar.setFocus()

        QTimer.singleShot(
            0,
            self.cargar_datos_iniciales_ventas
        )

    def cargar_datos_iniciales_ventas(self):
        """
        Carga los datos de Ventas después de que la interfaz
        ya fue creada y mostrada.

        Esto evita que la apertura del módulo quede bloqueada
        mientras se cargan clientes y productos.
        """

        # ------------------------------------------------------
        # CARGAR CLIENTES
        # ------------------------------------------------------
        try:

            self.cargar_clientes_local()

        except Exception as e:

            print(
                "Error cargando clientes locales de Ventas:",
                e
            )


        # ------------------------------------------------------
        # CARGAR SUGERENCIAS DE PRODUCTOS
        # ------------------------------------------------------
        try:

            self.cargar_sugerencias()

        except Exception as e:

            print(
                "Error cargando sugerencias de Ventas:",
                e
            )


        # ------------------------------------------------------
        # DEVOLVER EL FOCO AL BUSCADOR
        # ------------------------------------------------------
        try:

            self.buscar.setFocus(
                Qt.OtherFocusReason
            )

        except Exception:

            pass

    def refresh_layout_on_return(self):
        """Ajusta Ventas al viewport real del Dashboard al volver de otro módulo."""
        try:
            # Ventas vive dentro de QStackedWidget -> QScrollArea.
            # Tomamos el tamaño REAL disponible del viewport, evitando que
            # el QWidget conserve el tamaño de una vista anterior.
            parent = self.parentWidget()
            viewport = None
            while parent is not None:
                if hasattr(parent, "viewport") and callable(parent.viewport):
                    viewport = parent.viewport()
                    break
                parent = parent.parentWidget()

            if viewport is not None:
                size = viewport.size()
                if size.width() > 0 and size.height() > 0:
                    self.setMinimumSize(0, 0)
                    self.setMaximumSize(16777215, 16777215)
                    self.resize(size)
                    self.setMinimumSize(size)

            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.updateGeometry()
            lay = self.layout()
            if lay is not None:
                lay.invalidate()
                lay.activate()
                lay.setGeometry(self.rect())

            self.update()
            self.repaint()
        except Exception:
            # Nunca impedir que el módulo Ventas abra por un ajuste visual.
            pass

    def verificar_estado_caja_remota(self):
            try:
                api_url = get_setting('api_url', 'https://papelera-pos-backend-production.up.railway.app')
                response = requests.get(f"{api_url}/ventas/caja/estado", timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    if not data.get("caja_abierta", True):
                        # Si la caja está cerrada en la nube, limpiamos el carrito local
                        self.carrito.clear()
                        self.actualizar_tabla()
            except Exception as e:
                print("No se pudo verificar el estado de la caja:", e)

    def verificar_caja(self):
        try:
            api_url = get_setting('api_url', '...')
            resp = requests.get(f"{api_url}/caja/estado", timeout=3)
            if resp.status_code == 200:
                esta_abierta = resp.json().get("caja_abierta")
                if not esta_abierta:
                    # Deshabilitar botones de venta
                    self.boton_vender.setEnabled(False)
                    QMessageBox.warning(self, "Atención", "La caja está cerrada.")
        except:
            pass
    def showEvent(self, event):
        super().showEvent(event)

        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        # ==========================================================
        # APERTURA RÁPIDA
        # ==========================================================
        # No hacemos consultas a Railway desde showEvent().
        # showEvent() corre en el hilo de la interfaz y una petición
        # HTTP puede hacer que Ventas tarde en abrir.
        # Los datos locales se actualizan después de mostrar la ventana.

        self.buscar.setFocus()

        QTimer.singleShot(
            50,
            self.cargar_sugerencias_local
        )

        QTimer.singleShot(
            50,
            self.cargar_clientes_local
        )


        QTimer.singleShot(
            0,
            self.refresh_layout_on_return
        )

        QTimer.singleShot(
            50,
            self.refresh_layout_on_return
        )


    def keyPressEvent(self, event):
        k=event.key()
        if k==Qt.Key_F10: self.consulta_precio(); return
        if k==Qt.Key_F11: self.buscar.setFocus(); self.buscar.selectAll(); return
        if k==Qt.Key_F8: self.cobrar(); return
        if k==Qt.Key_F9: self.cancelar_venta(); return
        if k==Qt.Key_F4: self.aplicar_descuento(); return
        if k==Qt.Key_F3: self.dotacion(); return
        if k==Qt.Key_F2: self.abrir_arqueo(); return
        super().keyPressEvent(event)

    def cancelar_venta(self):
        if not self.carrito: return
        if QMessageBox.question(self,'Cancelar venta','¿Desea cancelar la venta actual?',QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            self.carrito.clear(); self.actualizar_tabla(); self.buscar.setFocus()

    def consulta_precio(self):
        d=QDialog(self); d.setWindowTitle('Consulta de precio (F10)'); d.resize(650,560); d.setStyleSheet('QDialog{background:#f8fafc;} QLabel{color:#0f172a;} QLineEdit{background:white;border:1px solid #cbd5e1;border-radius:10px;padding:12px;font-size:16px;} QListWidget{background:white;border:1px solid #e2e8f0;border-radius:10px;padding:5px;font-size:16px;} QListWidget::item{padding:10px;border-radius:7px;} QListWidget::item:selected{background:#dbeafe;color:#1e3a8a;} QPushButton{background:#2563eb;color:white;border:0;border-radius:10px;padding:12px 20px;font-weight:700;}')
        l=QVBoxLayout(d); l.setContentsMargins(28,28,28,28); l.setSpacing(14)
        head=QLabel('🔎 CONSULTA DE PRECIO'); head.setStyleSheet('font-size:26px;font-weight:900;'); l.addWidget(head)
        busc=QLineEdit(); busc.setPlaceholderText('Escribí el nombre o código de barras...'); busc.setProperty('keyboard_navigation_skip',True); l.addWidget(busc)
        lista=QListWidget(); l.addWidget(lista,1)
        detalle=QLabel('Seleccioná un producto para ver su precio.'); detalle.setWordWrap(True); detalle.setStyleSheet('background:#0f172a;color:white;border-radius:14px;padding:18px;font-size:18px;'); l.addWidget(detalle)
        cerrar=QPushButton('Cerrar'); cerrar.clicked.connect(d.accept); l.addWidget(cerrar)
        con=sqlite3.connect(BASE_DATOS); productos=con.execute('SELECT id,nombre,codigo_barras,precio_venta FROM productos ORDER BY nombre').fetchall(); con.close()
        def refrescar(texto=''):
            q=texto.strip().lower(); lista.clear()
            for pid,nombre,codigo,precio in productos:
                if not q or q in str(nombre).lower() or q in str(codigo or '').lower():
                    it=QListWidgetItem(f'{nombre}   —   $ {format_number(f"{precio:.2f}",2)}')
                    it.setData(Qt.UserRole,(nombre,codigo,precio)); lista.addItem(it)
            if lista.count(): lista.setCurrentRow(0)
        def mostrar(item):
            if not item:return
            nombre,codigo,precio=item.data(Qt.UserRole); codigo=codigo or 'Sin código'
            detalle.setText(
                f'''
                <div style="font-size:24px; font-weight:900;">
                    {nombre}
                </div>

                <div style="font-size:15px; margin-top:6px;">
                    Código: {codigo}
                </div>

                <div style="
                    font-size:44px;
                    font-weight:900;
                    margin-top:12px;
                ">
                    $ {format_number(f"{precio:.2f}", 2)}
                </div>
                '''
            )
        busc.textChanged.connect(refrescar); lista.currentItemChanged.connect(lambda cur,prev: mostrar(cur)); lista.itemClicked.connect(mostrar)
        refrescar(); d.exec()

    def aplicar_descuento(self):
        if not self.carrito:
            DialogoAviso(
                "Descuento",
                "No hay productos cargados en la venta.",
                self
            ).exec()
            return

        dialogo = QDialog(self)
        dialogo.setWindowTitle("Aplicar descuento")
        dialogo.setModal(True)
        dialogo.setFixedSize(380, 200)

        dialogo.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 12px;
            }

            QLabel {
                color: #0f172a;
                font-size: 15px;
            }

            QLineEdit {
                background-color: white;
                border: 2px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px;
                font-size: 18px;
                font-weight: bold;
            }

            QPushButton {
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton#aceptar {
                background-color: #10b981;
                color: white;
            }

            QPushButton#cancelar {
                background-color: #e2e8f0;
                color: #334155;
            }
        """)

        layout = QVBoxLayout(dialogo)

        titulo = QLabel("🏷️ Aplicar descuento")
        titulo.setStyleSheet(
            "font-size:22px;font-weight:800;color:#166534;"
        )

        texto = QLabel(
            "Ingrese el porcentaje de descuento:"
        )

        entrada = QLineEdit()
        entrada.setPlaceholderText("Ejemplo: 10")
        setup_numeric(entrada, 2)

        botones = QHBoxLayout()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("cancelar")

        btn_aceptar = QPushButton("Aplicar")
        btn_aceptar.setObjectName("aceptar")

        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_aceptar)

        layout.addWidget(titulo)
        layout.addWidget(texto)
        layout.addWidget(entrada)
        layout.addLayout(botones)

        resultado = {"valor": None}

        def confirmar():
            try:
                valor = parse_number(entrada.text())

                if valor is None:
                    valor = 0

                if valor < 0:
                    valor = 0

                if valor > 100:
                    valor = 100

                resultado["valor"] = valor
                dialogo.accept()

            except:
                dialogo.reject()


        btn_aceptar.clicked.connect(confirmar)
        btn_cancelar.clicked.connect(dialogo.reject)

        # ENTER aplica descuento
        entrada.returnPressed.connect(confirmar)

        entrada.setFocus()

        if dialogo.exec() != QDialog.Accepted:
            return

        pct = resultado["valor"]

        for p in self.carrito:
            p["precio"] *= 1 - pct / 100

        self.actualizar_tabla()

    def dotacion(self):
        monto,ok=QInputDialog.getDouble(self,'Dotación (F3)','Monto de dotación / efectivo inicial:',0,0,1000000000,2)
        if ok:
            QMessageBox.information(self,'Dotación registrada',f'Dotación informada: ${monto:,.2f}')

    def abrir_arqueo(self):
        from ui.caja import Caja
        self._caja=Caja(); self._caja.show()

    def cargar_clientes(self):

        try:
            clientes = listar_clientes()

            self.cliente.clear()
            self.cliente.addItem("👤 Consumidor final", 0)

            for c in clientes:
                self.cliente.addItem(
                    c["nombre"],
                    c["id"]
                )

        except Exception as e:
                print("Error cargando clientes desde Railway:", e)
    def cargar_clientes_local(self):
        """
        Carga los clientes directamente desde SQLite.
        No depende de Internet ni de Railway.
        """

        try:
            conexion = sqlite3.connect(BASE_DATOS)
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT id, nombre
                FROM clientes
                ORDER BY nombre COLLATE NOCASE
            """)

            clientes = cursor.fetchall()

            conexion.close()

            self.cliente.blockSignals(True)
            self.cliente.clear()

            self.cliente.addItem(
                "👤 Consumidor final",
                0
            )

            for cliente_id, nombre in clientes:

                self.cliente.addItem(
                    str(nombre),
                    cliente_id
                )

            self.cliente.blockSignals(False)

        except Exception as e:

            print(
                "ERROR CARGANDO CLIENTES LOCALES:",
                e
            )


    def cargar_sugerencias_local(self):
        """
        Carga el autocompletado directamente desde SQLite.
        """

        try:

            conexion = sqlite3.connect(BASE_DATOS)
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT nombre
                FROM productos
                WHERE nombre IS NOT NULL
                  AND TRIM(nombre) != ''
                ORDER BY nombre COLLATE NOCASE
            """)

            productos = [
                str(fila[0])
                for fila in cursor.fetchall()
            ]

            conexion.close()

            completador = QCompleter(
                productos
            )

            completador.setCaseSensitivity(
                Qt.CaseInsensitive
            )

            completador.setFilterMode(
                Qt.MatchContains
            )

            completador.activated[str].connect(
                self.seleccionar_producto_completer
            )

            # Vista previa más cómoda
            completador.popup().setStyleSheet("""
                QListView {
                    background: white;
                    color: #0f172a;
                    border: 1px solid #cbd5e1;
                    border-radius: 10px;
                    font-size: 18px;
                    padding: 6px;
                }

                QListView::item {
                    padding: 12px 14px;
                    min-height: 42px;
                }

                QListView::item:selected {
                    background: #dbeafe;
                    color: #1e3a8a;
                    font-weight: 700;
                }
            """)

            self.buscar.setCompleter(
                completador
            )

            # Guardamos la lista para poder refrescarla
            self._productos_sugerencias = productos

        except Exception as e:

            print(
                "ERROR CARGANDO SUGERENCIAS LOCALES:",
                e
            )


    def actualizar_datos_en_segundo_plano(self):
        """
        Actualiza información remota sin bloquear la interfaz.

        IMPORTANTE:
        Esta función no debe ejecutarse antes de mostrar Ventas.
        """

        try:

            # Primero comprobamos que Ventas siga visible.
            if not self.isVisible():
                return

            print(
                "SINCRONIZACIÓN EN SEGUNDO PLANO..."
            )

            # Acá dejamos solamente las tareas remotas
            # que ya tenga implementadas tu sistema.

            QTimer.singleShot(
                100,
                self.refrescar_datos_locales_despues_sync
            )

        except Exception as e:

            print(
                "ERROR EN SINCRONIZACIÓN EN SEGUNDO PLANO:",
                e
            )


    def refrescar_datos_locales_despues_sync(self):
        """
        Refresca los datos locales después de una eventual
        sincronización sin bloquear Ventas.
        """

        try:

            self.cargar_clientes_local()
            self.cargar_sugerencias_local()

        except Exception as e:

            print(
                "ERROR ACTUALIZANDO DATOS LOCALES:",
                e
            )
    def cargar_sugerencias(self):
        self.cargar_sugerencias_local()
        """
        Carga las sugerencias del buscador desde la base local.

        Se puede ejecutar nuevamente en cualquier momento para que
        los productos creados recientemente aparezcan sin reiniciar.
        """

        try:
            conexion = sqlite3.connect(BASE_DATOS)
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT nombre
                FROM productos
                WHERE nombre IS NOT NULL
                AND TRIM(nombre) <> ''
                ORDER BY nombre COLLATE NOCASE
            """)

            productos = [
                fila[0]
                for fila in cursor.fetchall()
            ]

            conexion.close()

            completador = QCompleter(productos)

            completador.setCaseSensitivity(
                Qt.CaseInsensitive
            )

            completador.setFilterMode(
                Qt.MatchContains
            )

            # ==================================================
            # SUGERENCIAS MÁS GRANDES Y LEGIBLES
            # ==================================================

            popup = completador.popup()

            popup.setStyleSheet("""
                QListView {
                    background-color: #ffffff;
                    color: #0f172a;
                    border: 1px solid #cbd5e1;
                    border-radius: 10px;
                    padding: 5px;
                    font-size: 17px;
                    font-weight: 600;
                }

                QListView::item {
                    padding: 12px 14px;
                    min-height: 34px;
                    border-radius: 7px;
                }

                QListView::item:hover {
                    background-color: #eff6ff;
                    color: #1d4ed8;
                }

                QListView::item:selected {
                    background-color: #dbeafe;
                    color: #1e3a8a;
                    font-weight: 800;
                }
            """)

            popup.setMinimumWidth(450)
            popup.setMinimumHeight(180)

            completador.activated[str].connect(
                self.seleccionar_producto_completer
            )

            self.buscar.setCompleter(
                completador
            )

            # Guardamos referencia para poder refrescarla
            self.completador_productos = completador

            print(
                f"DEBUG VENTAS: {len(productos)} productos cargados localmente."
            )

        except Exception as e:

            print(
                "Error al cargar sugerencias locales:",
                e
            )
    def confirmar_sugerencia(self):
        if getattr(self, "_agregando_producto", False):
            return

        texto = self.buscar.text().strip()

        if not texto:
            return

        conexion = sqlite3.connect(BASE_DATOS)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT *
            FROM productos
            WHERE nombre = ?
            OR codigo_barras = ?
            LIMIT 1
        """, (texto, texto))

        producto = cursor.fetchone()
        conexion.close()

        if producto:
            self.agregar_carrito({
                "producto_id": producto.get("id", 0),
                "producto_uuid": producto.get("uuid"),
                "codigo": producto.get("codigo_barras") or "SIN_COD",
                "nombre": producto["nombre"],
                "precio": float(producto["precio_venta"]),
                "cantidad": 1
            })

            self.buscar.clear()
            self.buscar.setFocus()
            return

            self.buscar.clear()
            self.buscar.setFocus()
            return

        self.buscar_producto()

    def seleccionar_producto_completer(self, texto):
        """
        Se ejecuta cuando se selecciona una sugerencia.
        Evita agregar dos veces el mismo producto.
        """

        if not texto:
            return

        try:
            conexion = sqlite3.connect(BASE_DATOS)
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT *
                FROM productos
                WHERE nombre = ?
                OR codigo_barras = ?
                LIMIT 1
            """, (texto, texto))

            producto = cursor.fetchone()

            conexion.close()

            if producto:

                producto_carrito = {
                    "producto_id": producto[0],
                    "producto_uuid": producto[1],
                    "codigo": producto[2] if producto[2] else "",
                    "nombre": producto[3],
                    "precio": float(producto[6]),
                    "cantidad": 1
                }

                self.agregar_carrito(producto_carrito)
                # LIMPIAR BUSCADOR DESPUES DE ELEGIR PRODUCTO
                self.buscar.blockSignals(True)

                self.buscar.clear()

                self.buscar.blockSignals(False)

                self.buscar.setText("")

                self.buscar.setFocus(
                    Qt.OtherFocusReason
                )
                # ==============================
                # LIMPIAR BUSCADOR DESPUES DE AGREGAR
                # ==============================

                QTimer.singleShot(
                    50,
                    self.limpiar_buscador
                )

                # ==============================
                # PREPARAR SIGUIENTE PRODUCTO
                # ==============================

                self.buscar.blockSignals(True)

                self.buscar.clear()

                self.buscar.blockSignals(False)


                self.buscar.setFocus(
                    Qt.OtherFocusReason
                )

        except Exception as e:
            print(f"Error al seleccionar producto del completer: {e}")

    def mostrar_todos_los_productos(self):
        try:
            conexion = sqlite3.connect(BASE_DATOS)
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT codigo_barras, nombre, precio_venta, stock
                FROM productos
                ORDER BY nombre
            """)

            productos = cursor.fetchall()
            conexion.close()

            if not productos:
                DialogoAviso(
                    "Inventario vacío",
                    "No hay productos cargados en la base de datos.",
                    self
                ).exec()
                return


            dialogo = QDialog(self)
            dialogo.setWindowTitle("📦 Inventario de Productos")
            dialogo.setModal(True)
            dialogo.resize(850, 550)


            dialogo.setStyleSheet("""
                QDialog {
                    background-color: #f8fafc;
                }

                QLabel {
                    color: #0f172a;
                }

                QLineEdit {
                    background-color: white;
                    border: 2px solid #cbd5e1;
                    border-radius: 10px;
                    padding: 10px;
                    font-size: 15px;
                }

                QTableWidget {
                    background-color: white;
                    border-radius: 12px;
                    border: 1px solid #e2e8f0;
                    gridline-color: #e2e8f0;
                    font-size: 14px;
                }

                QTableWidget::item {
                    padding: 8px;
                }

                QHeaderView::section {
                    background-color: #0f172a;
                    color: white;
                    padding: 12px;
                    font-weight: bold;
                    border: none;
                }

                QPushButton {
                    background-color: #2563eb;
                    color: white;
                    border-radius: 8px;
                    padding: 10px 25px;
                    font-weight: bold;
                    font-size: 14px;
                }

                QPushButton:hover {
                    background-color: #1d4ed8;
                }
            """)


            layout = QVBoxLayout(dialogo)

            titulo = QLabel("📦 Inventario Actual")
            titulo.setStyleSheet(
                "font-size:26px;font-weight:900;color:#0f172a;"
            )

            subtitulo = QLabel(
                f"Productos registrados: {len(productos)}"
            )
            subtitulo.setStyleSheet(
                "font-size:14px;color:#64748b;"
            )


            buscador = QLineEdit()
            buscador.setPlaceholderText(
                "🔍 Buscar producto por nombre o código..."
            )


            tabla = QTableWidget()
            tabla.setColumnCount(4)
            tabla.setHorizontalHeaderLabels(
                [
                    "Código",
                    "Producto",
                    "Precio",
                    "Stock"
                ]
            )

            tabla.horizontalHeader().setStretchLastSection(True)
            tabla.horizontalHeader().setSectionResizeMode(
                1,
                QHeaderView.Stretch
            )

            tabla.verticalHeader().setDefaultSectionSize(42)


            def cargar_tabla(filtro=""):

                tabla.setRowCount(0)

                filtro = filtro.lower()

                for producto in productos:

                    codigo = str(producto[0] or "")
                    nombre = str(producto[1] or "")
                    precio = producto[2] or 0
                    stock = producto[3] or 0


                    if (
                        filtro in nombre.lower()
                        or filtro in codigo.lower()
                    ):

                        fila = tabla.rowCount()
                        tabla.insertRow(fila)

                        tabla.setItem(
                            fila,
                            0,
                            QTableWidgetItem(
                                codigo if codigo else "SIN COD"
                            )
                        )

                        tabla.setItem(
                            fila,
                            1,
                            QTableWidgetItem(nombre)
                        )

                        tabla.setItem(
                            fila,
                            2,
                            QTableWidgetItem(
                                f"$ {precio:,.2f}"
                            )
                        )

                        tabla.setItem(
                            fila,
                            3,
                            QTableWidgetItem(
                                str(stock)
                            )
                        )


            buscador.textChanged.connect(cargar_tabla)


            boton = QPushButton("Cerrar")
            boton.clicked.connect(dialogo.accept)


            layout.addWidget(titulo)
            layout.addWidget(subtitulo)
            layout.addWidget(buscador)
            layout.addWidget(tabla)
            layout.addWidget(boton, alignment=Qt.AlignRight)


            cargar_tabla()

            dialogo.exec()


        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo cargar el inventario:\n{e}"
            )
    def buscar_producto(self):

        texto = self.buscar.text().strip()

        if not texto:
            return

        try:

            conexion = sqlite3.connect(
                BASE_DATOS
            )

            cursor = conexion.cursor()

            cursor.execute("""
                SELECT
                    id,
                    uuid,
                    codigo_barras,
                    nombre,
                    precio_venta,
                    stock
                FROM productos
                WHERE
                    LOWER(nombre) LIKE ?
                    OR LOWER(COALESCE(codigo_barras, '')) LIKE ?
                ORDER BY
                    CASE
                        WHEN LOWER(nombre) = ?
                        THEN 0
                        ELSE 1
                    END,
                    nombre COLLATE NOCASE
                LIMIT 20
            """, (
                f"%{texto.lower()}%",
                f"%{texto.lower()}%",
                texto.lower()
            ))

            encontrados = cursor.fetchall()

            conexion.close()

            if encontrados:

                # Tomamos el primer resultado,
                # igual que hacía tu código anterior.
                producto = encontrados[0]

                producto_id = producto[0]
                producto_uuid = producto[1]
                codigo = producto[2] or ""
                nombre = producto[3]
                precio = float(producto[4] or 0)

                self.agregar_carrito({

                    "producto_id": producto_id,

                    "producto_uuid": producto_uuid,

                    "codigo": codigo,

                    "nombre": nombre,

                    "precio": precio,

                    "cantidad": 1
                })

                print(
                    "PRODUCTO LOCAL AGREGADO:",
                    nombre
                )

                self.buscar.clear()

                self.buscar.setFocus()


                return

        except Exception as e:

            print(
                "ERROR BUSCANDO PRODUCTO LOCAL:",
                e
            )

        # ======================================================
        # SI NO ESTÁ LOCALMENTE
        # ======================================================

        # Dejamos tu diálogo actual de
        # "Producto no encontrado"
        # exactamente como ya lo tenés.



    def limpiar_busqueda_al_entrar(self, event):

            if event.reason() == Qt.MouseFocusReason:
                self.buscar.clear()

            QLineEdit.focusInEvent(
                self.buscar,
                event
            )

    def agregar_producto_libre(self, nombre_ingresado):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Precio del producto")
        dialogo.setModal(True)
        dialogo.resize(350, 150)

        layout = QVBoxLayout(dialogo)

        texto = QLabel(
            f"Ingrese el precio para:\n{nombre_ingresado}"
        )
        layout.addWidget(texto)

        precio_input = QLineEdit()
        precio_input.setPlaceholderText("Precio...")
        setup_numeric(precio_input, 2)
        layout.addWidget(precio_input)

        boton = QPushButton("Aceptar")
        layout.addWidget(boton)

        precio_resultado = {"valor": None}

        def confirmar():
            try:
                valor = parse_number(precio_input.text())

                if valor is None:
                    valor = 0

                precio_resultado["valor"] = valor
                dialogo.accept()

            except:
                dialogo.reject()


        boton.clicked.connect(confirmar)

        # ENTER confirma el precio
        precio_input.returnPressed.connect(confirmar)

        precio_input.setFocus()

        if dialogo.exec() != QDialog.Accepted:
            return

        precio = precio_resultado["valor"]

        item_temporal = {
            "codigo": "LIBRE",
            "nombre": nombre_ingresado,
            "precio": precio,
            "cantidad": 1
        }

        self.agregar_carrito(item_temporal)
        self.buscar.clear()
        self.buscar.setFocus()

    def agregar_carrito(self, prod_dict):

        # Si ya existe el producto, NO aumentar cantidad automáticamente
        for item in self.carrito:

            if (
                item.get("producto_uuid")
                and prod_dict.get("producto_uuid")
                and item["producto_uuid"] == prod_dict["producto_uuid"]
            ):

                self.actualizar_tabla()
                return


        # Producto nuevo siempre empieza en 1
        if "cantidad" not in prod_dict:
            prod_dict["cantidad"] = 1

        self.carrito.append(
            prod_dict
        )



        self.actualizar_tabla()

    def limpiar_buscador(self):

        self.buscar.blockSignals(True)

        self.buscar.clear()

        self.buscar.blockSignals(False)


        self.buscar.setFocus(
            Qt.OtherFocusReason
        )



    def actualizar_tabla(self):
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(self.carrito))
        total_acumulado = 0

        for fila, p in enumerate(self.carrito):
            subtotal = p["precio"] * p["cantidad"]
            total_acumulado += subtotal

            item_nombre = QTableWidgetItem(str(p["nombre"]))
            item_cant = QTableWidgetItem(str(p["cantidad"]))
            item_cant.setFlags(
                 item_cant.flags() | Qt.ItemIsEditable
            )

            item_precio = QTableWidgetItem(f"{p['precio']:.2f}")
            item_subtotal = QTableWidgetItem(f"${subtotal:,.2f}")
            item_codigo = QTableWidgetItem(str(p["codigo"]))

            item_nombre.setFlags(item_nombre.flags() ^ Qt.ItemIsEditable)
            item_subtotal.setFlags(item_subtotal.flags() ^ Qt.ItemIsEditable)
            item_codigo.setFlags(item_codigo.flags() ^ Qt.ItemIsEditable)

            item_cant.setTextAlignment(Qt.AlignCenter)
            item_precio.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_subtotal.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.tabla.setItem(fila, 0, item_nombre)
            self.tabla.setItem(fila, 1, item_cant)
            self.tabla.setItem(fila, 2, item_precio)
            self.tabla.setItem(fila, 3, item_subtotal)
            self.tabla.setItem(fila, 4, item_codigo)

        self.total.setText(f"${total_acumulado:,.2f}")
        self.tabla.blockSignals(False)

    def celda_modificada(self, item):


        fila = item.row()

        columna = item.column()



        if fila < 0 or fila >= len(self.carrito):

            return




        # ==========================
        # CAMBIO DE CANTIDAD
        # ==========================

        if columna == 1:


            texto = item.text().strip()



            try:


                cantidad = int(texto)



                if cantidad < 1:

                    cantidad = 1



                self.carrito[fila]["cantidad"] = cantidad




                subtotal = (

                    self.carrito[fila]["precio"]

                    *

                    cantidad

                )



                self.tabla.item(

                    fila,

                    3

                ).setText(

                    f"${subtotal:,.2f}"

                )




                total = sum(

                    p["precio"] * p["cantidad"]

                    for p in self.carrito

                )



                self.total.setText(

                    f"${total:,.2f}"

                )




            except:



                item.setText(

                    str(

                        self.carrito[fila]["cantidad"]

                    )

                )





        # ==========================
        # CAMBIO DE PRECIO
        # ==========================


        elif columna == 2:



            try:


                precio = parse_number(

                    item.text()

                )



                if precio is None:

                    raise ValueError



                if precio < 0:

                    precio = 0.0



                self.carrito[fila]["precio"] = precio




                subtotal = (

                    precio

                    *

                    self.carrito[fila]["cantidad"]

                )



                self.tabla.item(

                    fila,

                    3

                ).setText(

                    f"${subtotal:,.2f}"

                )



                total = sum(

                    p["precio"] * p["cantidad"]

                    for p in self.carrito

                )



                self.total.setText(

                    f"${total:,.2f}"

                )




            except:



                item.setText(

                    f"{self.carrito[fila]['precio']:.2f}"

                )

    def sumar_cantidad(self):
        fila = self.tabla.currentRow()
        if fila != -1:
            self.carrito[fila]["cantidad"] += 1
            self.actualizar_tabla()

    def restar_cantidad(self):
        fila = self.tabla.currentRow()
        if fila != -1:
            if self.carrito[fila]["cantidad"] > 1:
                self.carrito[fila]["cantidad"] -= 1
            else:
                del self.carrito[fila]
            self.actualizar_tabla()

    def eliminar_producto(self):
        fila = self.tabla.currentRow()
        if fila != -1:
            del self.carrito[fila]
            self.actualizar_tabla()


    def guardar_venta_local(self, venta):

        inicializar_base_datos_si_no_existe()

        conexion = create_connection()
        cursor = conexion.cursor()


        # Datos generales de la venta
        venta_uuid = str(uuid.uuid4())
        fecha = datetime.datetime.now().isoformat()
        total = sum(
            item["precio"] * item["cantidad"]
            for item in venta["items"]
        )


        # ======================================
        # TABLA DE SINCRONIZACION SEGURA
        # ======================================

        # Asegurar tabla sincronizacion
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sincronizacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tabla TEXT NOT NULL,
            registro INTEGER,
            registro_uuid TEXT,
            accion TEXT NOT NULL,
            datos TEXT,
            fecha TEXT,
            sincronizado INTEGER DEFAULT 0
        )
        """)


        columnas = {
            fila[1]
            for fila in cursor.execute(
                "PRAGMA table_info(sincronizacion)"
            ).fetchall()
        }


        columnas_necesarias = {
            "registro": "INTEGER",
            "registro_uuid": "TEXT",
            "accion": "TEXT",
            "datos": "TEXT",
            "fecha": "TEXT",
            "sincronizado": "INTEGER DEFAULT 0"
        }


        for nombre, tipo in columnas_necesarias.items():

            if nombre not in columnas:

                print(
                    "Agregando columna faltante:",
                    nombre
                )

                cursor.execute(
                    f"""
                    ALTER TABLE sincronizacion
                    ADD COLUMN {nombre} {tipo}
                    """
                )



        # ======================================
        # GUARDAR CABECERA DE VENTA
        # ======================================

        cursor.execute("""
            INSERT INTO ventas(
                uuid,
                fecha,
                total,
                forma_pago,
                cliente_id,
                estado,
                descuento,
                usuario,
                pago_efectivo,
                pago_transferencia,
                pago_tarjeta,
                pago_cuenta
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            venta_uuid,
            fecha,
            total,
            venta["forma_pago"],
            venta["cliente_id"],
            "ACTIVA",
            venta["descuento"],
            venta["usuario"],
            venta["pago_efectivo"],
            venta["pago_transferencia"],
            venta["pago_tarjeta"],
            venta["pago_cuenta"]
        ))


        venta_id = cursor.lastrowid

        print("DEBUG VENTA ID:", venta_id)
        print("DEBUG ITEMS:", venta["items"])
        print("DEBUG UUID:", venta_uuid)



        # ======================================
        # GUARDAR DETALLE DE VENTA
        # ======================================

        for item in venta["items"]:

            subtotal = (
                item["precio"] *
                item["cantidad"]
            )


            cursor.execute("""
                INSERT INTO detalle_ventas(
                    venta_id,
                    producto,
                    cantidad,
                    precio,
                    subtotal,
                    codigo
                )
                VALUES(?,?,?,?,?,?)
            """,
            (
                venta_id,
                item["producto"],
                item["cantidad"],
                item["precio"],
                subtotal,
                item["codigo"]
            ))



            # descontar stock local

            producto_uuid = item.get("producto_uuid")
            producto_id = item.get("producto_id")

            filas_actualizadas = 0

            if producto_uuid:

                cursor.execute(
                    """
                    UPDATE productos
                    SET stock = stock - ?
                    WHERE uuid = ?
                    """,
                    (
                        item["cantidad"],
                        producto_uuid
                    )
                )

                filas_actualizadas = cursor.rowcount

            else:

                cursor.execute(
                    """
                    UPDATE productos
                    SET stock = stock - ?
                    WHERE id = ?
                    """,
                    (
                        item["cantidad"],
                        producto_id
                    )
                )

                filas_actualizadas = cursor.rowcount


            print(
                "DEBUG STOCK:",
                "uuid =", producto_uuid,
                "id =", producto_id,
                "cantidad =", item["cantidad"],
                "filas_actualizadas =", filas_actualizadas
            )
        # ======================================
        # GUARDAR CAMBIO DE STOCK DEL PRODUCTO
        # ======================================

        if filas_actualizadas > 0 and producto_uuid:

            # IMPORTANTE:
            # Volvemos a consultar el producto y obtenemos
            # explícitamente todas las columnas necesarias.
            cursor.execute(
                """
                SELECT
                    id,
                    uuid,
                    codigo_barras,
                    nombre,
                    categoria,
                    precio_compra,
                    precio_venta,
                    stock,
                    stock_minimo
                FROM productos
                WHERE uuid = ?
                LIMIT 1
                """,
                (producto_uuid,)
            )

            producto_actualizado = cursor.fetchone()

            if producto_actualizado:

                producto_datos = {
                    "id": producto_actualizado[0],
                    "uuid": producto_actualizado[1],
                    "codigo_barras": producto_actualizado[2],
                    "nombre": producto_actualizado[3],
                    "categoria": producto_actualizado[4],
                    "precio_compra": producto_actualizado[5],
                    "precio_venta": producto_actualizado[6],
                    "stock": producto_actualizado[7],
                    "stock_minimo": producto_actualizado[8]
                }

                print(
                    "DEBUG SYNC PRODUCTO:",
                    producto_datos
                )

                cursor.execute(
                    """
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
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "productos",
                        producto_datos["id"],
                        producto_datos["uuid"],
                        "UPDATE",
                        json.dumps(
                            producto_datos,
                            ensure_ascii=False
                        ),
                        fecha,
                        0
                    )
                )

                print(
                    "DEBUG SYNC PRODUCTO INSERTADO:",
                    producto_datos["uuid"],
                    "stock =",
                    producto_datos["stock"],
                    "rowid =",
                    cursor.lastrowid
                )

        # ======================================
        # GUARDAR PENDIENTE DE SINCRONIZACION
        # ======================================


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
            VALUES(?,?,?,?,?,?,?)
        """,
        (
            "ventas",
            venta_id,
            venta_uuid,
            "INSERT",
            json.dumps(
                {
                    **venta,
                    "uuid": venta_uuid,
                    "fecha": fecha,
                    "total": total
                },
                ensure_ascii=False
            ),
            fecha,
            0
        ))
        print("DEBUG SYNC INSERTADA:", cursor.rowcount)

        conexion.commit()
        conexion.close()


        return venta_id


    def cobrar(self):
        if not self.carrito:
            DialogoAviso(
                "Aviso",
                "No hay productos en la venta actual.",
                self
            ).exec()
            return

        total_venta = sum(
            p["precio"] * p["cantidad"]
            for p in self.carrito
        )

        pago = DialogoPagoMixto(
            total_venta,
            self
        )

        if pago.exec() != QDialog.Accepted:
            return

        datos = pago.datos()

        try:

            items = []

            for p in self.carrito:
                items.append({
                    "producto_id": p.get("producto_id", 0),
                    "producto_uuid": p.get("producto_uuid"),
                    "producto": p["nombre"],
                    "cantidad": p["cantidad"],
                    "precio": p["precio"],
                    "subtotal": p["cantidad"] * p["precio"],
                    "codigo": p.get("codigo", "")
                })

            venta = {
                "items": items,
                "forma_pago": datos["forma"],
                "cliente_id": self.cliente.currentData() or 0,
                "descuento": 0,
                "usuario": "Administrador",
                "pago_efectivo": datos["efectivo"],
                "pago_transferencia": datos["transferencia"],
                "pago_tarjeta": datos["tarjeta"],
                "pago_cuenta": datos["cuenta"]
            }

            print("========== DEBUG CARRITO ANTES DE VENTA ==========")
            for p in self.carrito:
                print(
                    "PRODUCTO:",
                    p.get("nombre"),
                    "| ID:",
                    p.get("producto_id"),
                    "| UUID:",
                    p.get("producto_uuid"),
                    "| CANTIDAD:",
                    p.get("cantidad")
                )
            print("===================================================")
            venta_id = self.guardar_venta_local(venta)
            self.venta_realizada.emit()


            detalle_pago = f"""
    Venta guardada correctamente.

    Total: $ {total_venta:,.2f}

    Efectivo:
    $ {datos['efectivo']:,.2f}

    Mercado Pago:
    $ {datos['transferencia']:,.2f}

    Tarjeta:
    $ {datos['tarjeta']:,.2f}

    Cuenta corriente:
    $ {datos['cuenta']:,.2f}


    ¿Desea imprimir el ticket?
    """


            respuesta = QMessageBox.question(
                self,
                "Venta Exitosa",
                detalle_pago,
                QMessageBox.Yes | QMessageBox.No
            )


            if respuesta == QMessageBox.Yes:

                try:

                    ticket = generar_ticket(
                        venta_id
                    )

                    imprimir_ticket(
                        ticket
                    )


                except Exception as error:

                    DialogoAviso(
                        "Error de Impresión",
                        str(error),
                        self
                    ).exec()



            self.carrito.clear()

            self.actualizar_tabla()

            self.buscar.clear()

            self.buscar.setFocus()


        except Exception as error:

            DialogoAviso(
                "Error al guardar la venta",
                str(error),
                self
            ).exec()
