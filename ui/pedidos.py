# -*- coding: utf-8 -*-
import os
import sqlite3
import datetime
import json
import uuid
from PySide6.QtCore import Qt, QDate, QSize, QMarginsF
from PySide6.QtGui import (
    QFont,
    QColor,
    QPainter,
    QPen,
    QBrush,
    QPageSize,
    QPageLayout,
    QFontMetrics,
)
from PySide6.QtPrintSupport import (
    QPrinter,
    QPrintPreviewDialog,
    QPrintPreviewWidget,
    QPrintDialog,
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QDateEdit,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QSpinBox,
    QComboBox,
    QDoubleSpinBox,
    QAbstractItemView,
    QGroupBox,
    QSizePolicy,
)

from ui.db import BASE_DATOS, init_db, get_setting


# ============================================================
# UTILIDADES
# ============================================================

def dinero(valor):
    try:
        return f"$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "$ 0,00"


def asegurar_columna(cursor, tabla, columna, tipo):
    columnas = [
        fila[1]
        for fila in cursor.execute(
            f"PRAGMA table_info({tabla})"
        ).fetchall()
    ]

    if columna not in columnas:
        cursor.execute(
            f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}"
        )


# ============================================================
# DIALOGO DE PAGO
# ============================================================

class DialogoPagoPedido(QDialog):

    def __init__(self, total, parent=None):
        super().__init__(parent)

        self.total = float(total)

        self.setWindowTitle("Registrar pago")
        self.setModal(True)
        self.resize(520, 420)

        self.setStyleSheet("""
            QDialog {
                background: #f8fafc;
            }

            QLabel {
                color: #0f172a;
            }

            QLabel#titulo {
                font-size: 24px;
                font-weight: 900;
            }

            QLabel#total {
                font-size: 30px;
                font-weight: 900;
                color: #2563eb;
            }

            QGroupBox {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
                margin-top: 12px;
                padding: 18px;
                font-weight: 800;
                color: #334155;
            }

            QRadioButton {
                font-size: 15px;
                font-weight: 700;
                padding: 8px;
            }

            QDoubleSpinBox {
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 9px;
                padding: 9px;
                font-size: 15px;
            }

            QPushButton {
                border: none;
                border-radius: 9px;
                padding: 11px 22px;
                font-size: 14px;
                font-weight: 800;
            }

            QPushButton#aceptar {
                background: #2563eb;
                color: white;
            }

            QPushButton#aceptar:hover {
                background: #1d4ed8;
            }

            QPushButton#cancelar {
                background: #e2e8f0;
                color: #334155;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        titulo = QLabel("Registrar pago")
        titulo.setObjectName("titulo")

        lbl_total_texto = QLabel("Total del pedido")
        lbl_total_texto.setStyleSheet(
            "font-size:13px;color:#64748b;font-weight:700;"
        )

        self.lbl_total = QLabel(dinero(self.total))
        self.lbl_total.setObjectName("total")

        layout.addWidget(titulo)
        layout.addWidget(lbl_total_texto)
        layout.addWidget(self.lbl_total)

        grupo = QGroupBox("Forma de pago")

        grupo_layout = QVBoxLayout(grupo)
        grupo_layout.setSpacing(8)

        self.forma = QComboBox()
        self.forma.addItems([
            "EFECTIVO",
            "TRANSFERENCIA",
            "COMBINADO",
        ])

        self.forma.setStyleSheet("""
            QComboBox {
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 9px;
                padding: 10px;
                font-size: 15px;
                font-weight: 700;
            }

            QComboBox::drop-down {
                width: 32px;
                border: none;
                border-left: 1px solid #e2e8f0;
            }

            QComboBox QAbstractItemView {
                background: white;
                selection-background-color: #dbeafe;
                selection-color: #1e3a8a;
                padding: 6px;
            }
        """)

        grupo_layout.addWidget(self.forma)

        layout.addWidget(grupo)

        self.panel_combinado = QFrame()
        self.panel_combinado.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }

            QLabel {
                color: #475569;
                font-weight: 700;
            }
        """)

        grid = QGridLayout(self.panel_combinado)
        grid.setContentsMargins(15, 15, 15, 15)
        grid.setSpacing(10)

        lbl_efectivo = QLabel("Efectivo")
        lbl_transferencia = QLabel("Transferencia")

        self.efectivo = QDoubleSpinBox()
        self.efectivo.setRange(0, 999999999)
        self.efectivo.setDecimals(2)
        self.efectivo.setPrefix("$ ")
        self.efectivo.setSingleStep(100)

        self.transferencia = QDoubleSpinBox()
        self.transferencia.setRange(0, 999999999)
        self.transferencia.setDecimals(2)
        self.transferencia.setPrefix("$ ")
        self.transferencia.setSingleStep(100)

        grid.addWidget(lbl_efectivo, 0, 0)
        grid.addWidget(self.efectivo, 0, 1)

        grid.addWidget(lbl_transferencia, 1, 0)
        grid.addWidget(self.transferencia, 1, 1)

        self.lbl_restante = QLabel("Restante: $ 0,00")
        self.lbl_restante.setStyleSheet(
            "font-size:14px;font-weight:900;color:#2563eb;"
        )

        grid.addWidget(self.lbl_restante, 2, 0, 1, 2)

        layout.addWidget(self.panel_combinado)

        botones = QHBoxLayout()
        botones.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_aceptar = QPushButton("✓ Confirmar pago")
        btn_aceptar.setObjectName("aceptar")
        btn_aceptar.clicked.connect(self.aceptar_pago)

        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_aceptar)

        layout.addLayout(botones)

        self.forma.currentTextChanged.connect(self.actualizar_forma)
        self.efectivo.valueChanged.connect(self.actualizar_restante)
        self.transferencia.valueChanged.connect(self.actualizar_restante)

        self.actualizar_forma(self.forma.currentText())

    def actualizar_forma(self, forma):
        combinado = forma == "COMBINADO"

        self.panel_combinado.setVisible(combinado)

        if forma == "EFECTIVO":
            self.efectivo.setValue(self.total)
            self.transferencia.setValue(0)

        elif forma == "TRANSFERENCIA":
            self.efectivo.setValue(0)
            self.transferencia.setValue(self.total)

        else:
            self.efectivo.setValue(0)
            self.transferencia.setValue(0)

        self.actualizar_restante()

    def actualizar_restante(self):
        if self.forma.currentText() != "COMBINADO":
            self.lbl_restante.setText("")
            return

        suma = self.efectivo.value() + self.transferencia.value()
        restante = self.total - suma

        if abs(restante) < 0.01:
            self.lbl_restante.setText("✓ Pago completo")
            self.lbl_restante.setStyleSheet(
                "font-size:14px;font-weight:900;color:#16a34a;"
            )
        elif restante > 0:
            self.lbl_restante.setText(
                f"Restante: {dinero(restante)}"
            )
            self.lbl_restante.setStyleSheet(
                "font-size:14px;font-weight:900;color:#d97706;"
            )
        else:
            self.lbl_restante.setText(
                f"Excede: {dinero(abs(restante))}"
            )
            self.lbl_restante.setStyleSheet(
                "font-size:14px;font-weight:900;color:#dc2626;"
            )

    def aceptar_pago(self):

        forma = self.forma.currentText()

        if forma == "EFECTIVO":
            efectivo = self.total
            transferencia = 0

        elif forma == "TRANSFERENCIA":
            efectivo = 0
            transferencia = self.total

        else:
            efectivo = self.efectivo.value()
            transferencia = self.transferencia.value()

            if abs((efectivo + transferencia) - self.total) > 0.01:
                QMessageBox.warning(
                    self,
                    "Pago incompleto",
                    "En el pago combinado, la suma de efectivo "
                    "y transferencia debe coincidir exactamente "
                    "con el total del pedido."
                )
                return

        self._datos = {
            "forma": forma,
            "efectivo": efectivo,
            "transferencia": transferencia,
        }

        self.accept()

    def datos(self):
        return getattr(
            self,
            "_datos",
            {
                "forma": "",
                "efectivo": 0,
                "transferencia": 0,
            }
        )


# ============================================================
# PEDIDOS
# ============================================================

class Pedidos(QWidget):

    def __init__(self):
        super().__init__()

        init_db()

        self.carrito = []
        self.pedido_seleccionado = None

        self.setWindowTitle(
            f"Pedidos - {get_setting('nombre_negocio', 'COTILLON')}"
        )

        self.setMinimumSize(1200, 760)
        self.resize(1400, 900)

        self.preparar_base_datos()
        self.construir_interfaz()
        self.cargar_productos()
        self.cargar_pedidos()

    # ========================================================
    # BASE DE DATOS
    # ========================================================

    def preparar_base_datos(self):

        conexion = sqlite3.connect(BASE_DATOS)
        
        cursor = conexion.cursor()

        # Nuevos campos para pedidos.
        asegurar_columna(
            cursor,
            "pedidos",
            "forma_pago",
            "TEXT"
        )

        asegurar_columna(
            cursor,
            "pedidos",
            "pago_efectivo",
            "REAL DEFAULT 0"
        )

        asegurar_columna(
            cursor,
            "pedidos",
            "pago_transferencia",
            "REAL DEFAULT 0"
        )

        asegurar_columna(
            cursor,
            "pedidos",
            "fecha_pago",
            "TEXT"
        )

        asegurar_columna(
            cursor,
            "pedidos",
            "venta_id",
            "INTEGER"
        )

        # El cliente debe quedar guardado en el pedido para que
        # aparezca tanto en Pedidos registrados como en la factura.
        asegurar_columna(
            cursor,
            "pedidos",
            "cliente",
            "TEXT"
        )

        conexion.commit()
        conexion.close()

    # ========================================================
    # ESTILOS
    # ========================================================

    def construir_interfaz(self):

        self.setStyleSheet("""
            QWidget {
                background: #f1f5f9;
                color: #0f172a;
                font-family: "Segoe UI";
            }

            QFrame#panel {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
            }

            QLabel#titulo {
                font-size: 30px;
                font-weight: 900;
                color: #0f172a;
            }

            QLabel#subtitulo {
                font-size: 14px;
                color: #64748b;
            }

            QLabel#titulo_panel {
                font-size: 18px;
                font-weight: 900;
                color: #0f172a;
            }

            QLabel#total {
                font-size: 27px;
                font-weight: 900;
                color: #2563eb;
            }

            QLineEdit,
            QPlainTextEdit,
            QDateEdit,
            QComboBox {
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 10px 12px;
                font-size: 14px;
                selection-background-color: #2563eb;
                selection-color: white;
            }

            QLineEdit:focus,
            QPlainTextEdit:focus,
            QDateEdit:focus,
            QComboBox:focus {
                border: 2px solid #60a5fa;
            }

            QDateEdit {
                padding-right: 36px;
                min-height: 38px;
            }

            QDateEdit::drop-down {
                width: 34px;
                border: none;
                border-left: 1px solid #e2e8f0;
                background: #f8fafc;
                border-top-right-radius: 9px;
                border-bottom-right-radius: 9px;
            }

            QDateEdit::down-button {
                width: 30px;
                border: none;
                background: transparent;
            }

            QDateEdit::down-arrow {
                width: 10px;
                height: 10px;
            }

            QTableWidget {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                gridline-color: #f1f5f9;
                font-size: 14px;
                outline: none;
                selection-mode: SingleSelection;
                selection-behavior: SelectRows;
            }

            QTableWidget::item {
                padding: 8px 10px;
                color: #334155;
                border-bottom: 1px solid #f1f5f9;
            }

            QTableWidget::item:selected {
                background: #dbeafe;
                color: #1e3a8a;
                font-weight: 800;
                border-top: 1px solid #93c5fd;
                border-bottom: 1px solid #93c5fd;
            }

            QHeaderView::section {
                background: #0f172a;
                color: white;
                padding: 11px;
                font-weight: 800;
                font-size: 13px;
                border: none;
            }

            QSpinBox {
                background: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 4px 34px 4px 8px;
                min-height: 34px;
                font-size: 14px;
                font-weight: 800;
            }

            QSpinBox:hover {
                border: 1px solid #93c5fd;
                background: white;
            }

            QSpinBox::up-button {
                width: 28px;
                border: none;
                border-left: 1px solid #e2e8f0;
                border-top-right-radius: 7px;
                background: #eff6ff;
            }

            QSpinBox::down-button {
                width: 28px;
                border: none;
                border-left: 1px solid #e2e8f0;
                border-bottom-right-radius: 7px;
                background: #eff6ff;
            }

            QSpinBox::up-button:hover,
            QSpinBox::down-button:hover {
                background: #dbeafe;
            }

            QPushButton {
                border: none;
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 800;
            }

            QPushButton#primario {
                background: #2563eb;
                color: white;
            }

            QPushButton#primario:hover {
                background: #1d4ed8;
            }

            QPushButton#verde {
                background: #16a34a;
                color: white;
            }

            QPushButton#verde:hover {
                background: #15803d;
            }

            QPushButton#rojo {
                background: #fee2e2;
                color: #dc2626;
                border: 1px solid #fecaca;
            }

            QPushButton#rojo:hover {
                background: #dc2626;
                color: white;
            }

            QPushButton#secundario {
                background: #e2e8f0;
                color: #334155;
            }

            QPushButton#secundario:hover {
                background: #cbd5e1;
            }

            QPushButton#factura {
                background: #dbeafe;
                color: #1d4ed8;
                border: 1px solid #bfdbfe;
            }

            QPushButton#factura:hover {
                background: #2563eb;
                color: white;
            }

            QScrollBar:vertical {
                background: #f1f5f9;
                width: 10px;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 5px;
                min-height: 30px;
            }
        """)

        principal = QVBoxLayout(self)
        principal.setContentsMargins(16, 14, 16, 14)
        principal.setSpacing(10)

        # ====================================================
        # ENCABEZADO
        # ====================================================

        encabezado = QHBoxLayout()

        titulo_box = QVBoxLayout()
        titulo_box.setSpacing(2)

        titulo = QLabel("📋 Pedidos")
        titulo.setObjectName("titulo")

        subtitulo = QLabel(
            "Administrá pedidos, productos, entregas y pagos"
        )
        subtitulo.setObjectName("subtitulo")

        titulo_box.addWidget(titulo)
        titulo_box.addWidget(subtitulo)

        encabezado.addLayout(titulo_box)
        encabezado.addStretch()

        principal.addLayout(encabezado)

        # ====================================================
        # PARTE SUPERIOR
        # ====================================================

        datos_panel = QFrame()
        datos_panel.setObjectName("panel")

        datos_layout = QVBoxLayout(datos_panel)
        datos_layout.setContentsMargins(18, 18, 18, 18)
        datos_layout.setSpacing(12)

        lbl_datos = QLabel("Datos del pedido")
        lbl_datos.setObjectName("titulo_panel")

        datos_layout.addWidget(lbl_datos)

        form = QGridLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)

        lbl_cliente = QLabel("Cliente")
        lbl_entrega = QLabel("Fecha de entrega")
        lbl_obs = QLabel("Observaciones")

        for lbl in [lbl_cliente, lbl_entrega, lbl_obs]:
            lbl.setStyleSheet(
                "font-size:13px;color:#64748b;font-weight:800;"
            )

        self.cliente = QLineEdit()
        self.cliente.setPlaceholderText(
            "Nombre del cliente..."
        )

        self.entrega = QDateEdit()
        self.entrega.setCalendarPopup(True)
        self.entrega.setDate(QDate.currentDate())
        self.entrega.setDisplayFormat("dd/MM/yyyy")
        self.entrega.setMinimumHeight(40)

        self.obs = QLineEdit()
        self.obs.setPlaceholderText(
            "Observaciones o indicaciones de entrega..."
        )

        form.addWidget(lbl_cliente, 0, 0)
        form.addWidget(self.cliente, 1, 0)

        form.addWidget(lbl_entrega, 0, 1)
        form.addWidget(self.entrega, 1, 1)

        form.addWidget(lbl_obs, 0, 2)
        form.addWidget(self.obs, 1, 2)

        form.setColumnStretch(0, 1)
        form.setColumnStretch(1, 1)
        form.setColumnStretch(2, 2)

        datos_layout.addLayout(form)

        principal.addWidget(datos_panel)

        # ====================================================
        # CUERPO PRINCIPAL
        # ====================================================
        # Productos y pedido actual arriba; pedidos registrados abajo.
        cuerpo_superior = QHBoxLayout()
        cuerpo_superior.setSpacing(12)

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(16)

        # ----------------------------------------------------
        # PRODUCTOS DISPONIBLES
        # ----------------------------------------------------

        productos_panel = QFrame()
        productos_panel.setObjectName("panel")

        productos_layout = QVBoxLayout(productos_panel)
        productos_layout.setContentsMargins(16, 16, 16, 16)
        productos_layout.setSpacing(8)

        titulo_productos = QLabel("Buscar productos")
        titulo_productos.setObjectName("titulo_panel")

        productos_layout.addWidget(titulo_productos)

        self.buscar_producto = QLineEdit()
        self.buscar_producto.setPlaceholderText(
            "🔎 Buscar por nombre o código..."
        )

        self.buscar_producto.textChanged.connect(
            self.filtrar_productos
        )

        productos_layout.addWidget(self.buscar_producto)

        self.tabla_productos = QTableWidget()
        self.tabla_productos.setColumnCount(4)

        self.tabla_productos.setHorizontalHeaderLabels([
            "Código",
            "Producto",
            "Stock",
            "Precio",
        ])

        self.tabla_productos.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.tabla_productos.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.tabla_productos.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.tabla_productos.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.tabla_productos.setWordWrap(False)

        self.tabla_productos.verticalHeader().setDefaultSectionSize(42)

        header = self.tabla_productos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.resizeSection(0, 90)
        header.resizeSection(2, 70)
        header.resizeSection(3, 105)

        productos_layout.addWidget(
            self.tabla_productos,
            1
        )

        btn_agregar = QPushButton(
            "➕ Agregar producto seleccionado"
        )
        btn_agregar.setObjectName("verde")
        btn_agregar.setMinimumHeight(44)
        btn_agregar.clicked.connect(
            self.agregar_producto_seleccionado
        )

        productos_layout.addWidget(btn_agregar)

        cuerpo_superior.addWidget(productos_panel, 5)

        # ----------------------------------------------------
        # PEDIDO ACTUAL
        # ----------------------------------------------------

        pedido_panel = QFrame()
        pedido_panel.setObjectName("panel")

        pedido_layout = QVBoxLayout(pedido_panel)
        pedido_layout.setContentsMargins(16, 16, 16, 16)
        pedido_layout.setSpacing(8)

        titulo_pedido = QLabel("Productos del pedido")
        titulo_pedido.setObjectName("titulo_panel")

        pedido_layout.addWidget(titulo_pedido)

        self.tabla_pedido = QTableWidget()
        self.tabla_pedido.setColumnCount(6)

        self.tabla_pedido.setHorizontalHeaderLabels([
            "Código",
            "Producto",
            "Cantidad",
            "Precio",
            "Subtotal",
            "Acción",
        ])

        self.tabla_pedido.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.tabla_pedido.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.tabla_pedido.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.tabla_pedido.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.tabla_pedido.setWordWrap(False)

        self.tabla_pedido.verticalHeader().setDefaultSectionSize(54)

        header2 = self.tabla_pedido.horizontalHeader()

        for columna in range(5):
            header2.setSectionResizeMode(
                columna,
                QHeaderView.Stretch
            )

        header2.setSectionResizeMode(
            5,
            QHeaderView.Fixed
        )

        header2.resizeSection(5, 76)

        pedido_layout.addWidget(
            self.tabla_pedido,
            1
        )

        resumen = QFrame()
        resumen.setStyleSheet("""
            QFrame {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
        """)

        resumen_layout = QHBoxLayout(resumen)
        resumen_layout.setContentsMargins(15, 12, 15, 12)

        lbl_total_texto = QLabel("TOTAL DEL PEDIDO")
        lbl_total_texto.setStyleSheet(
            "font-size:13px;font-weight:900;color:#64748b;"
        )

        self.total = QLabel("$ 0,00")
        self.total.setObjectName("total")

        resumen_layout.addWidget(lbl_total_texto)
        resumen_layout.addStretch()
        resumen_layout.addWidget(self.total)

        pedido_layout.addWidget(resumen)

        botones_pedido = QHBoxLayout()

        btn_vaciar = QPushButton("🗑 Vaciar pedido")
        btn_vaciar.setObjectName("rojo")
        btn_vaciar.setMinimumHeight(44)
        btn_vaciar.clicked.connect(
            self.vaciar_pedido
        )

        btn_guardar = QPushButton("💾 Guardar pedido")
        btn_guardar.setObjectName("primario")
        btn_guardar.setMinimumHeight(44)
        btn_guardar.clicked.connect(
            self.guardar_pedido
        )

        botones_pedido.addWidget(btn_vaciar)
        botones_pedido.addWidget(btn_guardar)

        pedido_layout.addLayout(botones_pedido)

        cuerpo_superior.addWidget(pedido_panel, 7)

        # ----------------------------------------------------
        # PEDIDOS REGISTRADOS
        # ----------------------------------------------------

        registrados_panel = QFrame()
        registrados_panel.setObjectName("panel")

        registrados_layout = QVBoxLayout(registrados_panel)
        registrados_layout.setContentsMargins(16, 16, 16, 16)
        registrados_layout.setSpacing(12)

        titulo_registrados = QLabel("Pedidos registrados")
        titulo_registrados.setObjectName("titulo_panel")

        registrados_layout.addWidget(titulo_registrados)

        self.buscar_pedido = QLineEdit()
        self.buscar_pedido.setPlaceholderText(
            "🔎 Buscar pedido o cliente..."
        )

        self.buscar_pedido.textChanged.connect(
            self.filtrar_pedidos
        )

        registrados_layout.addWidget(
            self.buscar_pedido
        )

        self.tabla_registrados = QTableWidget()
        self.tabla_registrados.setColumnCount(7)

        self.tabla_registrados.setHorizontalHeaderLabels([
            "N°",
            "Fecha",
            "Cliente",
            "Entrega",
            "Estado",
            "Total",
            "Acciones",
        ])

        self.tabla_registrados.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.tabla_registrados.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.tabla_registrados.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        # La tabla ocupa todo el ancho disponible y no permite
        # desplazamiento horizontal.
        self.tabla_registrados.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.tabla_registrados.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.tabla_registrados.verticalHeader().setDefaultSectionSize(50)

        header3 = self.tabla_registrados.horizontalHeader()

        # Todas las columnas de datos se adaptan al ancho de la ventana.
        # La columna de acciones mantiene un ancho razonable.
        for columna in range(6):
            header3.setSectionResizeMode(
                columna,
                QHeaderView.Stretch
            )

        header3.setSectionResizeMode(
            6,
            QHeaderView.Fixed
        )
        header3.resizeSection(6, 155)

        self.tabla_registrados.itemSelectionChanged.connect(
            self.seleccionar_pedido_registrado
        )

        registrados_layout.addWidget(
            self.tabla_registrados,
            1
        )

        leyenda = QLabel(
            "🟠 PENDIENTE   •   🟢 ENTREGADO   •   "
            "✓ Marcar entregado   •   🧾 Ver factura"
        )

        leyenda.setStyleSheet(
            "font-size:12px;color:#64748b;font-weight:700;"
        )

        registrados_layout.addWidget(leyenda)

        # Primero la fila superior.
        principal.addLayout(cuerpo_superior, 1)

        # Después Pedidos registrados a todo el ancho.
        principal.addWidget(registrados_panel, 0)

        # ====================================================
        # CONEXIONES
        # ====================================================

        self.tabla_productos.doubleClicked.connect(
            self.agregar_producto_seleccionado
        )

    # ========================================================
    # PRODUCTOS
    # ========================================================

    def cargar_productos(self):

        conexion = sqlite3.connect(BASE_DATOS)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id,
                codigo_barras,
                nombre,
                stock,
                precio_venta
            FROM productos
            ORDER BY nombre COLLATE NOCASE
        """)

        self.productos = cursor.fetchall()

        conexion.close()

        self.mostrar_productos(self.productos)

    def mostrar_productos(self, productos):

        self.tabla_productos.setRowCount(0)

        for producto in productos:

            producto_id = producto[0]

            codigo = str(
                producto[1] or "SIN COD"
            )

            nombre = str(
                producto[2] or ""
            )

            stock = int(
                producto[3] or 0
            )

            precio = float(
                producto[4] or 0
            )

            fila = self.tabla_productos.rowCount()

            self.tabla_productos.insertRow(fila)

            valores = [
                codigo,
                nombre,
                str(stock),
                dinero(precio),
            ]

            for columna, valor in enumerate(valores):

                item = QTableWidgetItem(valor)

                item.setFlags(
                    item.flags()
                    & ~Qt.ItemIsEditable
                )

                if columna in (0, 2, 3):

                    item.setTextAlignment(
                        Qt.AlignCenter
                    )

                self.tabla_productos.setItem(
                    fila,
                    columna,
                    item
                )

            # Guardamos el ID REAL del producto
            # dentro de la fila, sin mostrarlo.
            self.tabla_productos.item(
                fila,
                0
            ).setData(
                Qt.UserRole,
                producto_id
            )

            # Guardamos también el PRECIO REAL de venta.
            # No debemos volver a obtenerlo desde el texto formateado.
            self.tabla_productos.item(
                fila,
                3
            ).setData(
                Qt.UserRole,
                precio
            )
    def filtrar_productos(self, texto):

        texto = texto.strip().lower()

        if not texto:

            self.mostrar_productos(
                self.productos
            )

            return

        encontrados = []

        for producto in self.productos:

            codigo = str(
                producto[1] or ""
            ).lower()

            nombre = str(
                producto[2] or ""
            ).lower()

            if texto in codigo or texto in nombre:

                encontrados.append(
                    producto
                )

        self.mostrar_productos(
            encontrados
        )
    def agregar_producto_seleccionado(self):

        fila = self.tabla_productos.currentRow()

        if fila < 0:
            QMessageBox.information(
                self,
                "Seleccionar producto",
                "Seleccioná primero un producto."
            )
            return

        item_codigo = self.tabla_productos.item(
            fila,
            0
        )

        # ID REAL del producto en la base de datos
        producto_id = item_codigo.data(
            Qt.UserRole
        )

        item_nombre = self.tabla_productos.item(
            fila,
            1
        )

        item_stock = self.tabla_productos.item(
            fila,
            2
        )

        if not item_codigo or not item_nombre:
            return

        codigo = item_codigo.text()
        nombre = item_nombre.text()

        try:

            stock = int(
                item_stock.text()
            )

        except Exception:

            stock = 0

        # ========================================================
        # OBTENER PRECIO REAL DESDE LA BASE DE DATOS
        # ========================================================

        precio = 0.0

        conexion = sqlite3.connect(
            BASE_DATOS
        )

        cursor = conexion.cursor()

        try:

            resultado_precio = cursor.execute(
                """
                SELECT precio_venta
                FROM productos
                WHERE id = ?
                LIMIT 1
                """,
                (producto_id,)
            ).fetchone()

            if resultado_precio:

                precio = float(
                    resultado_precio[0] or 0
                )

        except sqlite3.Error as error:

            conexion.close()

            QMessageBox.critical(
                self,
                "Error",
                "No se pudo obtener el precio del producto.\n\n"
                f"{error}"
            )

            return

        finally:

            try:
                conexion.close()
            except Exception:
                pass

        # ========================================================
        # VERIFICAR STOCK
        # ========================================================

        if stock <= 0:

            respuesta = QMessageBox.question(
                self,
                "Stock agotado",
                f"El producto '{nombre}' "
                "no tiene stock disponible.\n\n"
                "¿Deseás agregarlo igualmente al pedido?",
                QMessageBox.Yes | QMessageBox.No
            )

            if respuesta != QMessageBox.Yes:
                return

        # ========================================================
        # SI EL PRODUCTO YA ESTÁ EN EL CARRITO
        # ========================================================

        for producto in self.carrito:

            if (
                producto["codigo"] == codigo
                and producto["nombre"] == nombre
            ):

                producto["cantidad"] += 1

                # Actualizamos también el precio real
                producto["precio"] = precio

                self.actualizar_tabla_pedido()

                self.tabla_productos.setFocus()

                return

        # ========================================================
        # AGREGAR PRODUCTO NUEVO
        # ========================================================

        self.carrito.append({

            "id": producto_id,

            "codigo": codigo,

            "nombre": nombre,

            # PRECIO REAL DE precio_venta
            "precio": precio,

            "cantidad": 1,

            "stock": stock,
        })

        self.actualizar_tabla_pedido()

        self.tabla_productos.setFocus()

    # ========================================================
    # TABLA DEL PEDIDO
    # ========================================================

    def actualizar_tabla_pedido(self):

        self.tabla_pedido.blockSignals(True)

        self.tabla_pedido.setRowCount(0)

        total = 0

        for indice, producto in enumerate(
            self.carrito
        ):

            fila = self.tabla_pedido.rowCount()

            self.tabla_pedido.insertRow(fila)

            codigo = producto["codigo"]
            nombre = producto["nombre"]
            cantidad = int(producto["cantidad"])
            precio = float(producto["precio"])

            subtotal = cantidad * precio

            total += subtotal

            item_codigo = QTableWidgetItem(
                str(codigo)
            )

            item_nombre = QTableWidgetItem(
                str(nombre)
            )

            item_precio = QTableWidgetItem(
                dinero(precio)
            )

            item_subtotal = QTableWidgetItem(
                dinero(subtotal)
            )

            item_codigo.setTextAlignment(
                Qt.AlignCenter
            )

            item_precio.setTextAlignment(
                Qt.AlignRight | Qt.AlignVCenter
            )

            item_subtotal.setTextAlignment(
                Qt.AlignRight | Qt.AlignVCenter
            )

            self.tabla_pedido.setItem(
                fila,
                0,
                item_codigo
            )

            self.tabla_pedido.setItem(
                fila,
                1,
                item_nombre
            )

            # ----------------------------------------------
            # SPINBOX DE CANTIDAD
            # ----------------------------------------------

            spinner = QSpinBox()

            spinner.setMinimum(1)
            spinner.setMaximum(9999)
            spinner.setValue(cantidad)

            spinner.setToolTip(
                "Modificar cantidad"
            )

            spinner.setFixedWidth(105)
            spinner.setMinimumHeight(38)

            spinner.valueChanged.connect(
                lambda valor, i=indice:
                self.cambiar_cantidad(i, valor)
            )

            contenedor = QWidget()

            cont_layout = QHBoxLayout(
                contenedor
            )

            cont_layout.setContentsMargins(
                5, 5, 5, 5
            )

            cont_layout.setAlignment(
                Qt.AlignCenter
            )

            cont_layout.addWidget(
                spinner
            )

            self.tabla_pedido.setCellWidget(
                fila,
                2,
                contenedor
            )

            self.tabla_pedido.setItem(
                fila,
                3,
                item_precio
            )

            self.tabla_pedido.setItem(
                fila,
                4,
                item_subtotal
            )

            # ----------------------------------------------
            # BOTON ELIMINAR
            # ----------------------------------------------

            btn_eliminar = QPushButton("🗑")

            btn_eliminar.setObjectName(
                "rojo"
            )

            btn_eliminar.setToolTip(
                "Eliminar producto"
            )

            btn_eliminar.setFixedSize(
                46,
                38
            )

            btn_eliminar.setIconSize(
                QSize(20, 20)
            )

            btn_eliminar.clicked.connect(
                lambda checked=False, i=indice:
                self.eliminar_producto(i)
            )

            contenedor_btn = QWidget()

            btn_layout = QHBoxLayout(
                contenedor_btn
            )

            btn_layout.setContentsMargins(
                4, 4, 4, 4
            )

            btn_layout.setAlignment(
                Qt.AlignCenter
            )

            btn_layout.addWidget(
                btn_eliminar
            )

            self.tabla_pedido.setCellWidget(
                fila,
                5,
                contenedor_btn
            )

        self.total.setText(
            dinero(total)
        )

        self.tabla_pedido.blockSignals(False)

    def cambiar_cantidad(self, indice, cantidad):

        if indice < 0:
            return

        if indice >= len(self.carrito):
            return

        self.carrito[indice]["cantidad"] = int(
            cantidad
        )

        self.actualizar_tabla_pedido()

    def eliminar_producto(self, indice):

        if indice < 0:
            return

        if indice >= len(self.carrito):
            return

        del self.carrito[indice]

        self.actualizar_tabla_pedido()

    def vaciar_pedido(self):

        if not self.carrito:
            return

        respuesta = QMessageBox.question(
            self,
            "Vaciar pedido",
            "¿Seguro que querés quitar todos "
            "los productos del pedido?",
            QMessageBox.Yes | QMessageBox.No
        )

        if respuesta != QMessageBox.Yes:
            return

        self.carrito.clear()

        self.actualizar_tabla_pedido()

    # ========================================================
    # GUARDAR PEDIDO
    # ========================================================

    def guardar_pedido(self):

        if not self.cliente.text().strip():

            QMessageBox.warning(
                self,
                "Cliente requerido",
                "Ingresá el nombre del cliente."
            )

            self.cliente.setFocus()

            return

        if not self.carrito:

            QMessageBox.warning(
                self,
                "Pedido vacío",
                "Agregá al menos un producto."
            )

            return

        # ========================================================
        # CALCULAR TOTAL
        # ========================================================

        total = sum(
            float(p["precio"]) * int(p["cantidad"])
            for p in self.carrito
        )

        fecha = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        entrega = self.entrega.date().toString(
            "yyyy-MM-dd"
        )

        cliente = self.cliente.text().strip()
        observaciones = self.obs.text().strip()

        conexion = sqlite3.connect(
            BASE_DATOS
        )

        cursor = conexion.cursor()

        try:

            # ====================================================
            # BUSCAR CLIENTE
            # ====================================================

            cliente_id = None

            try:

                resultado_cliente = cursor.execute(
                    """
                    SELECT id
                    FROM clientes
                    WHERE LOWER(TRIM(nombre)) =
                        LOWER(TRIM(?))
                    LIMIT 1
                    """,
                    (cliente,)
                ).fetchone()

                if resultado_cliente:

                    cliente_id = resultado_cliente[0]

            except sqlite3.Error:

                cliente_id = None

            # ====================================================
            # VALIDAR PRODUCTOS DEL CARRITO
            #
            # IMPORTANTE:
            # ACÁ NO SE DESCUENTA STOCK.
            #
            # Tampoco se exige que haya stock suficiente.
            # El stock se verificará recién al entregar.
            # ====================================================

            for producto in self.carrito:

                producto_id = producto.get("id")

                cantidad = int(
                    producto.get("cantidad", 0)
                )

                if not producto_id:

                    raise Exception(
                        f"El producto "
                        f"'{producto.get('nombre', '')}' "
                        "no tiene un ID válido."
                    )

                if cantidad <= 0:

                    raise Exception(
                        f"La cantidad del producto "
                        f"'{producto.get('nombre', '')}' "
                        "no es válida."
                    )

                # ------------------------------------------------
                # Verificar que el producto todavía exista.
                #
                # NO modificamos stock.
                # ------------------------------------------------

                resultado_producto = cursor.execute(
                    """
                    SELECT
                        id,
                        codigo_barras,
                        nombre,
                        precio_venta
                    FROM productos
                    WHERE id = ?
                    LIMIT 1
                    """,
                    (producto_id,)
                ).fetchone()

                if not resultado_producto:

                    raise Exception(
                        f"No se encontró el producto:\n\n"
                        f"{producto.get('nombre', '')}\n"
                        f"Código: "
                        f"{producto.get('codigo', '')}"
                    )

            # ====================================================
            # GUARDAR PEDIDO
            # ====================================================

            cursor.execute(
                """
                INSERT INTO pedidos(
                    fecha,
                    entrega,
                    estado,
                    observaciones,
                    total,
                    forma_pago,
                    pago_efectivo,
                    pago_transferencia,
                    cliente,
                    cliente_id
                )
                VALUES(
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    fecha,
                    entrega,
                    "PENDIENTE",
                    observaciones,
                    total,
                    "",
                    0,
                    0,
                    cliente,
                    cliente_id,
                )
            )

            pedido_id = cursor.lastrowid

            # ====================================================
            # GUARDAR DETALLE DEL PEDIDO
            # ====================================================

            for producto in self.carrito:

                cantidad = int(
                    producto["cantidad"]
                )

                precio = float(
                    producto["precio"]
                )

                subtotal = (
                    precio * cantidad
                )

                cursor.execute(
                    """
                    INSERT INTO detalle_pedidos(
                        pedido_id,
                        producto,
                        cantidad,
                        precio,
                        subtotal,
                        codigo
                    )
                    VALUES(
                        ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        pedido_id,
                        producto["nombre"],
                        cantidad,
                        precio,
                        subtotal,
                        producto["codigo"],
                    )
                )

            # ====================================================
            # IMPORTANTE
            #
            # NO HAY UPDATE DE STOCK ACÁ.
            #
            # El stock se descontará únicamente en:
            #
            #     marcar_entregado()
            #
            # cuando el pedido pase a ENTREGADO.
            # ====================================================

            # ====================================================
            # CONFIRMAR TODO
            # ====================================================

            conexion.commit()

        except Exception as error:

            # ====================================================
            # SI ALGO FALLA, DESHACER TODO
            # ====================================================

            conexion.rollback()

            QMessageBox.critical(
                self,
                "No se pudo guardar el pedido",
                f"{error}\n\n"
                "El pedido NO fue guardado "
                "y el stock NO fue modificado."
            )

            conexion.close()

            return

        # ========================================================
        # CERRAR CONEXIÓN
        # ========================================================

        conexion.close()

        # ========================================================
        # CONFIRMACIÓN
        # ========================================================

        QMessageBox.information(
            self,
            "Pedido guardado",
            f"Pedido #{pedido_id} guardado correctamente.\n\n"
            "El stock se descontará cuando el pedido "
            "sea marcado como ENTREGADO."
        )

        # ========================================================
        # LIMPIAR FORMULARIO
        # ========================================================

        self.cliente.clear()

        self.obs.clear()

        self.carrito.clear()

        self.entrega.setDate(
            QDate.currentDate()
        )

        # ========================================================
        # ACTUALIZAR INTERFAZ
        # ========================================================

        self.actualizar_tabla_pedido()

        self.cargar_pedidos()
    def cargar_pedidos(self):

        conexion = sqlite3.connect(
            BASE_DATOS
        )

        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id,
                fecha,
                entrega,
                estado,
                total,
                observaciones,
                COALESCE(forma_pago, ''),
                COALESCE(pago_efectivo, 0),
                COALESCE(pago_transferencia, 0)
            FROM pedidos
            ORDER BY id DESC
        """)

        self.pedidos = cursor.fetchall()

        conexion.close()

        self.mostrar_pedidos(
            self.pedidos
        )

    def mostrar_pedidos(self, pedidos):

        self.tabla_registrados.setRowCount(0)

        filtro = self.buscar_pedido.text().strip().lower()

        for pedido in pedidos:

            (
                pedido_id,
                fecha,
                entrega,
                estado,
                total,
                observaciones,
                forma_pago,
                pago_efectivo,
                pago_transferencia,
            ) = pedido

            cliente = self.obtener_cliente_pedido(
                pedido_id
            )

            fecha_mostrar = self.formatear_fecha(
                fecha
            )

            entrega_mostrar = self.formatear_fecha(
                entrega
            )

            if filtro:

                texto_busqueda = (
                    f"{pedido_id} "
                    f"{cliente} "
                    f"{fecha_mostrar} "
                    f"{entrega_mostrar} "
                    f"{estado}"
                ).lower()

                if filtro not in texto_busqueda:
                    continue

            fila = self.tabla_registrados.rowCount()

            self.tabla_registrados.insertRow(
                fila
            )

            valores = [
                str(pedido_id),
                fecha_mostrar,
                cliente,
                entrega_mostrar,
                estado,
                dinero(total),
            ]

            for columna, valor in enumerate(
                valores
            ):

                item = QTableWidgetItem(
                    str(valor)
                )

                item.setFlags(
                    item.flags()
                    & ~Qt.ItemIsEditable
                )

                if columna in (
                    0,
                    1,
                    3,
                    4,
                    5,
                ):
                    item.setTextAlignment(
                        Qt.AlignCenter
                    )

                self.tabla_registrados.setItem(
                    fila,
                    columna,
                    item
                )

            # Estado
            estado_item = self.tabla_registrados.item(
                fila,
                4
            )

            if estado == "ENTREGADO":

                estado_item.setForeground(
                    QColor("#15803d")
                )

                estado_item.setBackground(
                    QColor("#dcfce7")
                )

                font = estado_item.font()
                font.setBold(True)
                estado_item.setFont(font)

            else:

                estado_item.setForeground(
                    QColor("#b45309")
                )

                estado_item.setBackground(
                    QColor("#fef3c7")
                )

                font = estado_item.font()
                font.setBold(True)
                estado_item.setFont(font)

            # ------------------------------------------------
            # BOTONES DE ACCIÓN
            # ------------------------------------------------

            acciones = QWidget()

            acciones_layout = QHBoxLayout(
                acciones
            )

            acciones_layout.setContentsMargins(
                2, 2, 2, 2
            )

            acciones_layout.setSpacing(3)

            if estado != "ENTREGADO":

                btn_entregado = QPushButton("✓")
                btn_entregado.setObjectName(
                    "verde"
                )

                btn_entregado.setToolTip(
                    "Marcar pedido como entregado y registrar pago"
                )

                btn_entregado.setFixedSize(
                    42,
                    36
                )

                btn_entregado.clicked.connect(
                    lambda checked=False,
                    pid=pedido_id:
                    self.marcar_entregado(pid)
                )

                acciones_layout.addWidget(
                    btn_entregado
                )

            btn_factura = QPushButton("🧾")

            btn_factura.setObjectName(
                "factura"
            )

            btn_factura.setToolTip(
                "Ver y guardar factura"
            )

            btn_factura.setFixedSize(
                42,
                36
            )

            btn_factura.clicked.connect(
                lambda checked=False,
                pid=pedido_id:
                self.mostrar_factura(pid)
            )

            acciones_layout.addWidget(
                btn_factura
            )
            
            # ------------------------------------------------
            # BOTÓN ELIMINAR
            # ------------------------------------------------

            btn_eliminar = QPushButton("🗑")

            btn_eliminar.setObjectName(
                "eliminar"
            )

            btn_eliminar.setToolTip(
                "Eliminar pedido"
            )

            btn_eliminar.setFixedSize(
                42,
                36
            )

            btn_eliminar.clicked.connect(
                lambda checked=False,
                pid=pedido_id:
                self.eliminar_pedido(pid)
            )

            acciones_layout.addWidget(
                btn_eliminar
            )

            self.tabla_registrados.setCellWidget(
                fila,
                6,
                acciones
            )

    def filtrar_pedidos(self):

        self.mostrar_pedidos(
            self.pedidos
        )

    def obtener_cliente_pedido(
        self,
        pedido_id
    ):

        # El pedido actual usa el nombre del cliente
        # mediante observaciones / datos del pedido.
        #
        # Si posteriormente la tabla pedidos tiene
        # cliente_id, esta función puede ampliarse.

        conexion = sqlite3.connect(
            BASE_DATOS
        )

        cursor = conexion.cursor()

        columnas = [
            fila[1]
            for fila in cursor.execute(
                "PRAGMA table_info(pedidos)"
            ).fetchall()
        ]

        cliente = ""

        if "cliente" in columnas:

            resultado = cursor.execute(
                """
                SELECT COALESCE(cliente, '')
                FROM pedidos
                WHERE id=?
                """,
                (pedido_id,)
            ).fetchone()

            if resultado:
                cliente = resultado[0]

        elif "cliente_id" in columnas:

            resultado = cursor.execute(
                """
                SELECT
                    COALESCE(c.nombre, '')
                FROM pedidos p
                LEFT JOIN clientes c
                    ON c.id=p.cliente_id
                WHERE p.id=?
                """,
                (pedido_id,)
            ).fetchone()

            if resultado:
                cliente = resultado[0]

        conexion.close()

        return cliente or "Sin cliente"

    # ========================================================
    # SELECCIÓN DE PEDIDO
    # ========================================================

    def seleccionar_pedido_registrado(self):

        fila = self.tabla_registrados.currentRow()

        if fila < 0:
            return

        item = self.tabla_registrados.item(
            fila,
            0
        )

        if not item:
            return

        try:
            self.pedido_seleccionado = int(
                item.text()
            )
        except Exception:
            self.pedido_seleccionado = None
    # ========================================================
    # ELIMINAR PEDIDO
    # ========================================================

    def eliminar_pedido(self, pedido_id):

        respuesta = QMessageBox.question(
            self,
            "Eliminar pedido",
            f"¿Seguro que querés eliminar el pedido N° {pedido_id}?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta != QMessageBox.Yes:
            return

        conexion = sqlite3.connect(
            BASE_DATOS
        )

        cursor = conexion.cursor()

        try:

            # Eliminar primero los detalles del pedido
            cursor.execute(
                """
                DELETE FROM detalle_pedidos
                WHERE pedido_id = ?
                """,
                (pedido_id,)
            )

            # Eliminar el pedido
            cursor.execute(
                """
                DELETE FROM pedidos
                WHERE id = ?
                """,
                (pedido_id,)
            )

            conexion.commit()

        except Exception as error:

            conexion.rollback()

            QMessageBox.critical(
                self,
                "Error",
                "No se pudo eliminar el pedido.\n\n"
                f"{error}"
            )

            conexion.close()
            return

        conexion.close()

        # Si estaba seleccionado, quitar selección
        if self.pedido_seleccionado == pedido_id:
            self.pedido_seleccionado = None

        # Recargar pedidos
        self.cargar_pedidos()

        QMessageBox.information(
            self,
            "Pedido eliminado",
            f"El pedido N° {pedido_id} fue eliminado correctamente."
        )
    # ========================================================
    # MARCAR ENTREGADO
    # ========================================================

    def marcar_entregado(self, pedido_id):

        datos_pedido = self.obtener_datos_pedido(
            pedido_id
        )

        if not datos_pedido:
            return

        if datos_pedido["estado"] == "ENTREGADO":

            QMessageBox.information(
                self,
                "Pedido entregado",
                "Este pedido ya está marcado como entregado."
            )

            return

        # ========================================================
        # ABRIR VENTANA DE PAGO
        # ========================================================

        dialogo = DialogoPagoPedido(
            datos_pedido["total"],
            self
        )

        if dialogo.exec() != QDialog.Accepted:

            # Canceló el pago.
            # NO se modifica el stock.
            return

        pago = dialogo.datos()

        fecha_pago = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        conexion = sqlite3.connect(
            BASE_DATOS
        )

        cursor = conexion.cursor()

        try:

            # ====================================================
            # OBTENER PRODUCTOS DEL PEDIDO
            # ====================================================

            detalles = cursor.execute(
                """
                SELECT
                    codigo,
                    producto,
                    cantidad
                FROM detalle_pedidos
                WHERE pedido_id = ?
                ORDER BY id
                """,
                (
                    pedido_id,
                )
            ).fetchall()

            if not detalles:

                raise Exception(
                    "El pedido no tiene productos asociados."
                )

            # ====================================================
            # BUSCAR TODOS LOS PRODUCTOS Y VERIFICAR STOCK
            # ====================================================

            productos_stock = []

            for detalle in detalles:

                codigo = str(detalle[0] or "").strip()
                nombre_pedido = str(detalle[1] or "").strip()

                cantidad = int(
                    detalle[2] or 0
                )

                if cantidad <= 0:

                    raise Exception(
                        f"La cantidad del producto "
                        f"'{nombre_pedido}' no es válida."
                    )

                # ------------------------------------------------
                # BUSCAR PRODUCTO
                #
                # PRIMERO POR CÓDIGO DE BARRAS.
                # Si no existe código, se busca por nombre.
                # ------------------------------------------------

                producto_db = None

                # =================================================
                # 1. BUSCAR POR CÓDIGO
                # =================================================

                if codigo:

                    producto_db = cursor.execute(
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
                        WHERE TRIM(COALESCE(codigo_barras, ''))
                            = TRIM(?)
                        LIMIT 1
                        """,
                        (
                            codigo,
                        )
                    ).fetchone()

                # =================================================
                # 2. SI NO SE ENCONTRÓ, BUSCAR POR NOMBRE
                # =================================================

                if not producto_db:

                    producto_db = cursor.execute(
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
                        WHERE LOWER(TRIM(nombre))
                            = LOWER(TRIM(?))
                        LIMIT 1
                        """,
                        (
                            nombre_pedido,
                        )
                    ).fetchone()

                # =================================================
                # PRODUCTO NO ENCONTRADO
                # =================================================

                if not producto_db:

                    raise Exception(
                        f"No se encontró el producto:\n\n"
                        f"{nombre_pedido}\n\n"
                        f"Código: {codigo or 'Sin código'}"
                    )

                # =================================================
                # DATOS DEL PRODUCTO
                # =================================================

                producto_id = producto_db[0]
                producto_uuid = producto_db[1]
                codigo_db = producto_db[2]
                nombre_db = producto_db[3]
                categoria_db = producto_db[4]

                precio_compra_db = float(
                    producto_db[5] or 0
                )

                precio_venta_db = float(
                    producto_db[6] or 0
                )

                stock_actual = int(
                    producto_db[7] or 0
                )

                stock_minimo_db = int(
                    producto_db[8] or 0
                )

                # =================================================
                # VERIFICAR STOCK
                # =================================================

                if stock_actual < cantidad:

                    raise Exception(
                        f"No hay stock suficiente para:\n\n"
                        f"{nombre_db}\n\n"
                        f"Stock disponible: {stock_actual}\n"
                        f"Cantidad necesaria: {cantidad}"
                    )

                # =================================================
                # GUARDAR CAMBIO A REALIZAR
                #
                # TODAVÍA NO MODIFICAMOS LA BASE.
                # Primero verificamos TODOS los productos.
                # =================================================

                productos_stock.append({
                    "id": producto_id,
                    "uuid": producto_uuid,
                    "codigo": codigo_db,
                    "nombre": nombre_db,
                    "categoria": categoria_db,
                    "precio_compra": precio_compra_db,
                    "precio_venta": precio_venta_db,
                    "stock_minimo": stock_minimo_db,
                    "stock_anterior": stock_actual,
                    "cantidad": cantidad,
                    "stock_nuevo": (
                        stock_actual - cantidad
                    )
                })

            # ====================================================
            # DESCONTAR STOCK Y REGISTRAR SINCRONIZACIÓN
            # ====================================================

            for producto in productos_stock:

                # -----------------------------------------------
                # Actualizar stock local
                # -----------------------------------------------

                cursor.execute("""
                    UPDATE productos
                    SET stock = ?
                    WHERE id = ?
                """, (
                    producto["stock_nuevo"],
                    producto["id"]
                ))

                if cursor.rowcount != 1:

                    raise Exception(
                        f"No se pudo actualizar el stock de:\n\n"
                        f"{producto['nombre']}"
                    )

                # -----------------------------------------------
                # Registrar el PRODUCTO COMPLETO para sincronizar
                # -----------------------------------------------
                #
                # IMPORTANTE:
                # No mandamos solamente el stock.
                # Mandamos también precio de compra, precio de
                # venta, categoría, código, etc.
                #
                # Así el servidor no pone los precios en 0.
                # -----------------------------------------------

                datos_sync = {
                    "uuid": producto["uuid"],
                    "codigo_barras": producto["codigo"],
                    "nombre": producto["nombre"],
                    "categoria": producto["categoria"],
                    "precio_compra": producto["precio_compra"],
                    "precio_venta": producto["precio_venta"],
                    "stock": producto["stock_nuevo"],
                    "stock_minimo": producto["stock_minimo"]
                }

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
                """, (
                    "productos",
                    producto["uuid"],
                    "UPDATE",
                    json.dumps(datos_sync),
                    datetime.datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    0
                ))
                # ------------------------------------------------
                # ASEGURAR QUE REALMENTE SE ACTUALIZÓ
                # ------------------------------------------------

                if cursor.rowcount != 1:

                    raise Exception(
                        "No se pudo descontar correctamente "
                        "el stock de:\n\n"
                        f"{producto['nombre']}\n\n"
                        "El pedido NO fue entregado."
                    )

            # ====================================================
            # MARCAR PEDIDO COMO ENTREGADO
            # ====================================================

            cursor.execute(
                """
                UPDATE pedidos
                SET
                    estado = ?,
                    forma_pago = ?,
                    pago_efectivo = ?,
                    pago_transferencia = ?,
                    fecha_pago = ?
                WHERE id = ?
                """,
                (
                    "ENTREGADO",
                    pago["forma"],
                    pago["efectivo"],
                    pago["transferencia"],
                    fecha_pago,
                    pedido_id,
                )
            )

            if cursor.rowcount != 1:

                raise Exception(
                    "No se pudo marcar el pedido "
                    "como ENTREGADO."
                )

            # ====================================================
            # CREAR VENTA AL ENTREGAR EL PEDIDO
            #
            # IMPORTANTE:
            # La venta solamente se crea cuando el pedido
            # fue efectivamente entregado.
            #
            # Esta venta queda identificada como PEDIDO
            # para que Historial pueda mostrarla como:
            #
            #     Pedido
            #
            # en lugar de:
            #
            #     Venta diaria
            # ====================================================

            venta_uuid = str(uuid.uuid4())


            # ====================================================
            # OBTENER DATOS DEL PEDIDO
            # ====================================================

            pedido_db = cursor.execute(
                """
                SELECT
                    cliente_id,
                    total
                FROM pedidos
                WHERE id = ?
                """,
                (pedido_id,)
            ).fetchone()


            if not pedido_db:

                raise Exception(
                    "No se pudieron obtener los datos "
                    "del pedido para crear la venta."
                )


            cliente_id_pedido = pedido_db[0]

            total_pedido = float(
                pedido_db[1] or 0
            )


            # ====================================================
            # CREAR CABECERA DE VENTA
            # ====================================================

            # Asegurar que exista la columna tipo.
            # El historial utiliza esta columna para distinguir
            # una Venta diaria de un Pedido.

            columnas_ventas = [
                fila[1]
                for fila in cursor.execute(
                    "PRAGMA table_info(ventas)"
                ).fetchall()
            ]

            if "tipo" not in columnas_ventas:

                cursor.execute(
                    """
                    ALTER TABLE ventas
                    ADD COLUMN tipo TEXT
                    """
                )


            cursor.execute(
                """
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
                    pago_cuenta,
                    origen,
                    pedido_id,
                    tipo
                )
                VALUES(
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?
                )
                """,
                (
                    venta_uuid,

                    fecha_pago,

                    total_pedido,

                    pago["forma"],

                    cliente_id_pedido,

                    "ACTIVA",

                    0,

                    "Administrador",

                    pago["efectivo"],

                    pago["transferencia"],

                    0,

                    0,

                    "PEDIDO",

                    pedido_id,

                    # ================================================
                    # ESTA ES LA CLAVE
                    # ================================================
                    "PEDIDO"
                )
            )

            venta_id = cursor.lastrowid


            if not venta_id:

                raise Exception(
                    "No se pudo crear la venta "
                    "correspondiente al pedido."
                )


            # ====================================================
            # COPIAR PRODUCTOS DEL PEDIDO A LA VENTA
            # ====================================================

            detalles_pedido = cursor.execute(
                """
                SELECT
                    producto,
                    cantidad,
                    precio,
                    subtotal,
                    codigo
                FROM detalle_pedidos
                WHERE pedido_id = ?
                ORDER BY id
                """,
                (pedido_id,)
            ).fetchall()


            if not detalles_pedido:

                raise Exception(
                    "El pedido no tiene productos para "
                    "crear el detalle de la venta."
                )


            for detalle in detalles_pedido:

                cursor.execute(
                    """
                    INSERT INTO detalle_ventas(
                        venta_id,
                        producto,
                        cantidad,
                        precio,
                        subtotal,
                        codigo
                    )
                    VALUES(
                        ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        venta_id,

                        detalle[0],

                        detalle[1],

                        detalle[2],

                        detalle[3],

                        detalle[4]
                    )
                )

            # ====================================================
            # PREPARAR PRODUCTOS PARA SINCRONIZACIÓN
            # ====================================================

            items_sync = []

            for detalle in detalles_pedido:

                items_sync.append({
                    "producto": detalle[0],
                    "cantidad": int(detalle[1] or 0),
                    "precio": float(detalle[2] or 0),
                    "subtotal": float(detalle[3] or 0),
                    "codigo": detalle[4] or ""
                })

            # ====================================================
            # REGISTRAR VENTA PARA SINCRONIZACIÓN
            # ====================================================

            datos_venta_sync = {

                "uuid": venta_uuid,

                "fecha": fecha_pago,

                "total": total_pedido,

                "forma_pago": pago["forma"],

                "cliente_id": cliente_id_pedido,

                "estado": "ACTIVA",

                "descuento": 0,

                "usuario": "Administrador",

                "pago_efectivo": pago["efectivo"],

                "pago_transferencia": pago["transferencia"],

                "pago_tarjeta": 0,

                "pago_cuenta": 0,

                # =================================================
                # IDENTIFICACIÓN DEL ORIGEN
                # =================================================

                "origen": "PEDIDO",

                "pedido_id": pedido_id,

                # =================================================
                # TIPO PARA EL HISTORIAL
                # =================================================

                "tipo": "PEDIDO",

                # =================================================
                # DETALLE DE LOS PRODUCTOS
                # =================================================

                "items": items_sync
            }


            cursor.execute(
                """
                INSERT INTO sincronizacion(
                    tabla,
                    registro_uuid,
                    accion,
                    datos,
                    fecha,
                    sincronizado
                )
                VALUES(
                    ?, ?, ?, ?, datetime('now'), 0
                )
                """,
                (
                    "ventas",
                    venta_uuid,
                    "CREATE",
                    json.dumps(
                        datos_venta_sync,
                        ensure_ascii=False
                    )
                )
            )

            # ====================================================
            # CONFIRMAR TODO JUNTO
            # ========================================================================================================

            conexion.commit()

        except Exception as error:

            conexion.rollback()

            conexion.close()

            QMessageBox.critical(
                self,
                "No se pudo entregar el pedido",
                f"{error}\n\n"
                "El pedido NO fue entregado.\n"
                "El stock NO fue modificado.\n"
                "El pago NO fue registrado."
            )

            return

        # ========================================================
        # CERRAR CONEXIÓN
        # ========================================================

        conexion.close()

        # ========================================================
        # RECARGAR PRODUCTOS
        #
        # IMPORTANTE:
        # Esto hace que la tabla de productos muestre
        # inmediatamente el nuevo stock.
        # ========================================================

        self.cargar_productos()

        # ========================================================
        # LA FACTURA SE GENERA SOLAMENTE AL ENTREGAR
        # ========================================================

        datos_factura = self.obtener_datos_pedido(
            pedido_id
        )

        ruta = self.ruta_factura(
            pedido_id
        )

        try:

            self.generar_factura_pdf(
                datos_factura,
                ruta
            )

        except Exception as error:

            QMessageBox.warning(
                self,
                "Pedido entregado",
                "El pedido y el pago fueron registrados "
                "correctamente y el stock fue descontado, "
                "pero no se pudo guardar la factura.\n\n"
                f"Error: {error}"
            )

            self.cargar_pedidos()

            return

        # ========================================================
        # CONFIRMACIÓN
        # ========================================================

        QMessageBox.information(
            self,
            "Pedido entregado",
            "El pedido fue marcado como ENTREGADO.\n\n"
            "El pago quedó registrado.\n"
            "El stock fue descontado correctamente.\n"
            "La factura fue guardada correctamente.\n\n"
            f"Ubicación: {ruta}"
        )

        # ========================================================
        # ACTUALIZAR PEDIDOS
        # ========================================================

        self.cargar_pedidos()
    # ========================================================
    # DATOS DEL PEDIDO
    # ========================================================

    def obtener_datos_pedido(
        self,
        pedido_id
    ):

        conexion = sqlite3.connect(
            BASE_DATOS
        )

        cursor = conexion.cursor()

        resultado = cursor.execute("""
            SELECT
                id,
                fecha,
                entrega,
                estado,
                observaciones,
                total,
                COALESCE(forma_pago, ''),
                COALESCE(pago_efectivo, 0),
                COALESCE(pago_transferencia, 0),
                COALESCE(fecha_pago, '')
            FROM pedidos
            WHERE id=?
        """, (
            pedido_id,
        )).fetchone()

        if not resultado:

            conexion.close()

            return None

        (
            pid,
            fecha,
            entrega,
            estado,
            observaciones,
            total,
            forma_pago,
            pago_efectivo,
            pago_transferencia,
            fecha_pago,
        ) = resultado

        detalles = cursor.execute("""
            SELECT
                producto,
                cantidad,
                precio,
                subtotal,
                COALESCE(codigo, '')
            FROM detalle_pedidos
            WHERE pedido_id=?
            ORDER BY id
        """, (
            pedido_id,
        )).fetchall()

        conexion.close()

        cliente = self.obtener_cliente_pedido(
            pedido_id
        )

        return {
            "id": pid,
            "fecha": fecha,
            "entrega": entrega,
            "estado": estado,
            "observaciones": observaciones or "",
            "total": float(total or 0),
            "forma_pago": forma_pago or "",
            "pago_efectivo": float(
                pago_efectivo or 0
            ),
            "pago_transferencia": float(
                pago_transferencia or 0
            ),
            "fecha_pago": fecha_pago or "",
            "cliente": cliente,
            "detalles": detalles,
        }

    # ========================================================
    # FACTURA
    # ========================================================

    def ruta_factura(self, pedido_id):

        carpeta = os.path.join(
            os.path.dirname(
                os.path.abspath(BASE_DATOS)
            ),
            "facturas"
        )

        os.makedirs(
            carpeta,
            exist_ok=True
        )

        return os.path.join(
            carpeta,
            f"Factura_Pedido_{pedido_id}.pdf"
        )

    def mostrar_factura(self, pedido_id):

        datos = self.obtener_datos_pedido(
            pedido_id
        )

        if not datos:
            QMessageBox.warning(
                self,
                "Factura",
                "No se encontró el pedido."
            )
            return

        # IMPORTANTE:
        # Esta función SOLO muestra la factura.
        # NO genera ni guarda ningún PDF.
        # El PDF se genera únicamente desde marcar_entregado().

        printer = QPrinter(
            QPrinter.HighResolution
        )

        printer.setPageSize(
            QPageSize(
                QPageSize.PageSizeId.A4
            )
        )

        printer.setPageMargins(
            QMarginsF(10, 10, 10, 10),
            QPageLayout.Millimeter
        )

        dialogo = QDialog(self)
        dialogo.setWindowTitle(
            f"Factura - Pedido #{pedido_id}"
        )
        dialogo.resize(1200, 850)
        dialogo.setModal(True)

        dialogo.setStyleSheet("""
            QDialog {
                background: #f1f5f9;
            }

            QPushButton {
                border: none;
                border-radius: 9px;
                padding: 10px 18px;
                font-size: 14px;
                font-weight: 800;
            }

            QPushButton#imprimir {
                background: #2563eb;
                color: white;
            }

            QPushButton#imprimir:hover {
                background: #1d4ed8;
            }

            QPushButton#cerrar {
                background: #e2e8f0;
                color: #334155;
            }

            QPushButton#cerrar:hover {
                background: #cbd5e1;
            }
        """)

        layout = QVBoxLayout(dialogo)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        vista = QPrintPreviewWidget(
            printer,
            dialogo
        )

        vista.setZoomMode(
            QPrintPreviewWidget.ZoomMode.FitInView
        )

        vista.paintRequested.connect(
            lambda p: self.pintar_factura(
                p,
                datos
            )
        )

        layout.addWidget(
            vista,
            1
        )

        botones = QHBoxLayout()
        botones.setContentsMargins(8, 4, 8, 4)
        botones.addStretch()

        btn_cerrar = QPushButton(
            "Cerrar"
        )
        btn_cerrar.setObjectName(
            "cerrar"
        )
        btn_cerrar.setMinimumHeight(42)
        btn_cerrar.clicked.connect(
            dialogo.reject
        )

        btn_imprimir = QPushButton(
            "🖨 Imprimir factura"
        )
        btn_imprimir.setObjectName(
            "imprimir"
        )
        btn_imprimir.setMinimumHeight(42)
        btn_imprimir.clicked.connect(
            lambda: self.imprimir_factura(
                datos
            )
        )

        botones.addWidget(
            btn_cerrar
        )
        botones.addWidget(
            btn_imprimir
        )

        layout.addLayout(
            botones
        )

        vista.updatePreview()
        dialogo.exec()

    def imprimir_factura(self, datos):

        printer = QPrinter(
            QPrinter.HighResolution
        )

        printer.setPageSize(
            QPageSize(
                QPageSize.PageSizeId.A4
            )
        )

        printer.setPageMargins(
            QMarginsF(10, 10, 10, 10),
            QPageLayout.Millimeter
        )

        dialogo_impresion = QPrintDialog(
            printer,
            self
        )

        dialogo_impresion.setWindowTitle(
            "Imprimir factura"
        )

        if dialogo_impresion.exec() != QDialog.Accepted:
            return

        try:
            self.pintar_factura(
                printer,
                datos
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Imprimir factura",
                "No se pudo imprimir la factura:\n\n"
                f"{error}"
            )

    def generar_factura_pdf(
        self,
        datos,
        ruta
    ):

        printer = QPrinter(
            QPrinter.HighResolution
        )

        printer.setOutputFormat(
            QPrinter.PdfFormat
        )

        printer.setOutputFileName(
            ruta
        )

        printer.setPageSize(
            QPageSize(
                QPageSize.PageSizeId.A4
            )
        )

        printer.setPageMargins(
            QMarginsF(10, 10, 10, 10),
            QPageLayout.Millimeter
        )

        self.pintar_factura(
            printer,
            datos
        )

    # ========================================================
    # FACTURA - VISTA PREVIA / IMPRESION / PDF
    # ========================================================

    def pintar_factura(self, printer, datos):
        """Dibuja la factura usando coordenadas físicas de A4.

        La versión anterior utilizaba coordenadas fijas en píxeles.
        En una QPrinter de alta resolución eso hacía que todo el contenido
        quedara comprimido en la parte superior de la hoja. Esta versión
        trabaja en milímetros y convierte cada coordenada al tamaño real
        de la página imprimible.
        """

        painter = QPainter(printer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        # La página configurada por mostrar_factura(), imprimir_factura()
        # y generar_factura_pdf() es A4 vertical con 10 mm de margen.
        # Usamos el viewport real para que también funcione correctamente
        # en PDF y en impresoras con distintas resoluciones.
        viewport = painter.viewport()
        px_w = max(1, viewport.width())
        px_h = max(1, viewport.height())

        # Área imprimible de A4 con márgenes de 10 mm.
        page_w_mm = 190.0
        page_h_mm = 277.0
        sx = px_w / page_w_mm
        sy = px_h / page_h_mm

        def X(mm):
            return int(round(mm * sx))

        def Y(mm):
            return int(round(mm * sy))

        # Paleta
        azul = QColor("#1e3a8a")
        azul_claro = QColor("#eff6ff")
        rojo = QColor("#dc2626")
        negro = QColor("#1f2937")
        gris = QColor("#64748b")
        gris_claro = QColor("#e2e8f0")
        gris_fondo = QColor("#f8fafc")
        gris_fila = QColor("#f8fafc")
        blanco = QColor("#ffffff")
        verde = QColor("#059669")
        naranja = QColor("#d97706")
        amarillo_fondo = QColor("#fffbeb")

        # --------------------------------------------------------
        # UTILIDADES DE DIBUJO
        # --------------------------------------------------------

        def fuente(tamano, negrita=False):
            f = QFont("Arial")
            f.setPointSizeF(float(tamano))
            f.setBold(bool(negrita))
            return f

        def escribir(x, y, w, h, texto, tamano=9, color=negro,
                     negrita=False,
                     alineacion=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter):
            painter.setPen(color)
            painter.setFont(fuente(tamano, negrita))
            painter.drawText(
                X(x), Y(y), X(w), Y(h),
                alineacion | Qt.TextFlag.TextSingleLine,
                str(texto),
            )

        def escribir_elidido(x, y, w, h, texto, tamano=9, color=negro,
                             negrita=False,
                             alineacion=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter):
            f = fuente(tamano, negrita)
            fm = QFontMetrics(f)
            # El ancho de QFontMetrics está en coordenadas del dispositivo.
            ancho_px = max(1, X(w))
            valor = fm.elidedText(
                str(texto),
                Qt.TextElideMode.ElideRight,
                ancho_px,
            )
            escribir(x, y, w, h, valor, tamano, color, negrita, alineacion)

        def escribir_derecha(x, y, w, h, texto, tamano=9, color=negro,
                             negrita=False):
            escribir(
                x, y, w, h, texto, tamano, color, negrita,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            )

        def escribir_centro(x, y, w, h, texto, tamano=9, color=negro,
                            negrita=False):
            escribir(
                x, y, w, h, texto, tamano, color, negrita,
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
            )

        def linea(y, color=gris_claro, grosor=1):
            painter.setPen(QPen(color, max(1, X(grosor * 0.30))))
            painter.drawLine(X(6), Y(y), X(184), Y(y))

        def caja(x, y, w, h, fondo=blanco, borde=gris_claro, radio=2.5):
            painter.setBrush(QBrush(fondo))
            painter.setPen(QPen(borde, max(1, X(0.30))))
            painter.drawRoundedRect(
                X(x), Y(y), X(w), Y(h),
                float(radio), float(radio),
            )

        def rect_sin_borde(x, y, w, h, color):
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(X(x), Y(y), X(w), Y(h))

        # --------------------------------------------------------
        # DIMENSIONES GENERALES
        # --------------------------------------------------------

        izquierda = 6.0
        derecha = 184.0
        ancho = derecha - izquierda
        pie = 270.0

        # --------------------------------------------------------
        # ENCABEZADO
        # --------------------------------------------------------

        y = 7.0

        nombre_negocio = (
            get_setting("nombre_negocio", "COTILLON") or "COTILLON"
        ).upper()
        direccion = get_setting("direccion", "") or ""
        telefono = get_setting("telefono", "") or ""
        email = get_setting("email", "") or ""

        # Caja de factura a la derecha.
        caja_factura_x = 133.0
        caja_factura_w = 51.0
        caja_factura_h = 36.0

        caja(
            caja_factura_x,
            7.0,
            caja_factura_w,
            caja_factura_h,
            gris_fondo,
            gris_claro,
            3,
        )

        escribir_centro(
            caja_factura_x,
            10.0,
            caja_factura_w,
            8.0,
            "FACTURA",
            16,
            rojo,
            True,
        )

        painter.setPen(QPen(gris_claro, max(1, X(0.30))))
        painter.drawLine(
            X(caja_factura_x + 5),
            Y(20),
            X(caja_factura_x + caja_factura_w - 5),
            Y(20),
        )

        escribir(caja_factura_x + 5, 22.0, 20, 5, "PEDIDO N°", 7.5, gris, True)
        escribir_derecha(
            caja_factura_x + 25,
            22.0,
            21,
            5,
            datos.get("id", ""),
            9,
            negro,
            True,
        )

        escribir(caja_factura_x + 5, 27.0, 20, 5, "FECHA", 7.5, gris, True)
        escribir_derecha(
            caja_factura_x + 25,
            27.0,
            21,
            5,
            self.formatear_fecha(datos.get("fecha", "")),
            8,
            negro,
        )

        escribir(caja_factura_x + 5, 32.0, 20, 5, "ENTREGA", 7.5, gris, True)
        escribir_derecha(
            caja_factura_x + 25,
            32.0,
            21,
            5,
            self.formatear_fecha(datos.get("entrega", "")),
            8,
            negro,
        )

        # Nombre del negocio.
        escribir_elidido(
            izquierda,
            y,
            118,
            12,
            nombre_negocio,
            20,
            azul,
            True,
        )
        y += 14

        if direccion:
            escribir_elidido(izquierda, y, 118, 5.5, direccion, 8, gris)
            y += 6

        if telefono:
            escribir_elidido(izquierda, y, 118, 5.5, f"Tel: {telefono}", 8, gris)
            y += 6

        if email:
            escribir_elidido(izquierda, y, 118, 5.5, email, 8, gris)
            y += 6

        y = max(y + 4, 48.0)
        linea(y, azul, 2.0)
        y += 6

        # --------------------------------------------------------
        # DATOS DEL CLIENTE / ESTADO
        # --------------------------------------------------------

        col1 = izquierda
        col2 = 68.0
        col3 = 126.0

        escribir(col1, y, 55, 5, "CLIENTE", 7.5, gris, True)
        escribir(col2, y, 52, 5, "FECHA DE ENTREGA", 7.5, gris, True)
        escribir(col3, y, 58, 5, "ESTADO", 7.5, gris, True)
        y += 6

        cliente_texto = datos.get("cliente", "") or "Sin cliente"
        fecha_entrega = self.formatear_fecha(datos.get("entrega", "")) or "-"
        estado = str(datos.get("estado", "PENDIENTE") or "PENDIENTE").upper()
        color_estado = verde if estado == "ENTREGADO" else naranja

        escribir_elidido(col1, y, 55, 8, cliente_texto, 9.5, negro, True)
        escribir(col2, y, 52, 8, fecha_entrega, 9.5, negro)
        escribir(col3, y, 58, 8, estado, 9.5, color_estado, True)
        y += 12

        # --------------------------------------------------------
        # OBSERVACIONES
        # --------------------------------------------------------

        observaciones = datos.get("observaciones", "") or ""
        if observaciones.strip():
            caja(
                izquierda,
                y,
                ancho,
                13,
                amarillo_fondo,
                QColor("#f59e0b"),
                2,
            )
            escribir(izquierda + 3, y + 2, 28, 7, "OBSERVACIONES", 7.5, naranja, True)
            escribir_elidido(
                izquierda + 31,
                y + 2,
                ancho - 34,
                7,
                observaciones,
                8,
                negro,
            )
            y += 19
        else:
            y += 3

        # --------------------------------------------------------
        # TABLA DE PRODUCTOS
        # --------------------------------------------------------

        detalles = datos.get("detalles", []) or []

        tabla_x = izquierda
        tabla_w = ancho
        header_h = 9.0
        fila_h = 9.0

        w_cant = 18.0
        w_producto = 83.0
        w_precio = 38.0
        w_importe = tabla_w - w_cant - w_producto - w_precio

        x_cant = tabla_x
        x_producto = x_cant + w_cant
        x_precio = x_producto + w_producto
        x_importe = x_precio + w_precio

        def dibujar_cabecera_tabla(y_tabla):
            rect_sin_borde(tabla_x, y_tabla, tabla_w, header_h, azul)
            escribir_centro(x_cant, y_tabla, w_cant, header_h, "CANT.", 7.5, blanco, True)
            escribir(x_producto + 2, y_tabla, w_producto - 4, header_h, "DESCRIPCIÓN", 7.5, blanco, True)
            escribir_derecha(x_precio, y_tabla, w_precio - 2, header_h, "PRECIO UNIT.", 7.5, blanco, True)
            escribir_derecha(x_importe, y_tabla, w_importe - 2, header_h, "IMPORTE", 7.5, blanco, True)

        dibujar_cabecera_tabla(y)
        y += header_h

        # Reservamos espacio para el pie de la página.
        limite_productos = pie - 14

        def nueva_pagina_productos():
            nonlocal y
            if not printer.newPage():
                return False

            # El painter sigue activo después de newPage().
            y = 12.0
            escribir(izquierda, y, ancho, 9, "FACTURA - CONTINUACIÓN", 13, azul, True)
            y += 13
            dibujar_cabecera_tabla(y)
            y += header_h
            return True

        if detalles:
            for indice, detalle in enumerate(detalles):
                producto = str(detalle[0] or "")
                cantidad = int(detalle[1] or 0)
                precio = float(detalle[2] or 0)
                subtotal = float(detalle[3] or 0)

                if y + fila_h > limite_productos:
                    nueva_pagina_productos()

                if indice % 2 == 1:
                    rect_sin_borde(tabla_x, y, tabla_w, fila_h, gris_fila)

                painter.setPen(QPen(gris_claro, max(1, X(0.25))))
                painter.drawLine(X(tabla_x), Y(y + fila_h), X(derecha), Y(y + fila_h))

                escribir_centro(x_cant, y, w_cant, fila_h, cantidad, 8.5, negro)
                escribir_elidido(x_producto + 2, y, w_producto - 4, fila_h, producto, 8.5, negro)
                escribir_derecha(x_precio, y, w_precio - 2, fila_h, dinero(precio), 8.5, negro)
                escribir_derecha(x_importe, y, w_importe - 2, fila_h, dinero(subtotal), 8.5, negro)

                y += fila_h
        else:
            escribir_centro(
                tabla_x,
                y,
                tabla_w,
                fila_h,
                "No hay productos registrados",
                8.5,
                gris,
            )
            y += fila_h

        # --------------------------------------------------------
        # TOTALES Y PAGO
        # --------------------------------------------------------

        # Si los totales no entran, pasamos a una página nueva.
        if y + 48 > pie - 2:
            printer.newPage()
            y = 12.0
            escribir(izquierda, y, ancho, 9, "FACTURA - CONTINUACIÓN", 13, azul, True)
            y += 14

        y += 5

        subtotal_general = sum(float(d[3] or 0) for d in detalles)
        total_general = float(datos.get("total", 0) or 0)

        # Bloque de pago a la izquierda.
        pago_x = izquierda
        pago_w = 83.0
        total_x = 116.0
        total_w = derecha - total_x
        bloque_y = y

        forma = datos.get("forma_pago", "") or "PENDIENTE"
        pago_efectivo = float(datos.get("pago_efectivo", 0) or 0)
        pago_transferencia = float(datos.get("pago_transferencia", 0) or 0)

        escribir(pago_x, bloque_y, pago_w, 6, "FORMA DE PAGO", 8.5, azul, True)
        caja(pago_x, bloque_y + 7, pago_w, 30, blanco, gris_claro, 2)
        escribir_elidido(pago_x + 4, bloque_y + 10, pago_w - 8, 7, forma, 9, negro, True)

        pago_linea_y = bloque_y + 19
        if pago_efectivo > 0:
            escribir(pago_x + 4, pago_linea_y, 28, 6, "Efectivo:", 7.5, gris)
            escribir_derecha(pago_x + 33, pago_linea_y, pago_w - 37, 6, dinero(pago_efectivo), 7.5, negro)
            pago_linea_y += 7

        if pago_transferencia > 0:
            escribir(pago_x + 4, pago_linea_y, 32, 6, "Transferencia:", 7.5, gris)
            escribir_derecha(pago_x + 37, pago_linea_y, pago_w - 41, 6, dinero(pago_transferencia), 7.5, negro)

        # Bloque de totales a la derecha.
        caja(total_x, bloque_y, total_w, 42, gris_fondo, gris_claro, 2.5)
        escribir(total_x + 5, bloque_y + 7, 38, 6, "Subtotal", 8, gris, True)
        escribir_derecha(total_x + 43, bloque_y + 7, total_w - 48, 6, dinero(subtotal_general), 8.5, negro)

        painter.setPen(QPen(gris_claro, max(1, X(0.30))))
        painter.drawLine(
            X(total_x + 5),
            Y(bloque_y + 19),
            X(derecha - 5),
            Y(bloque_y + 19),
        )

        escribir(total_x + 5, bloque_y + 23, 38, 9, "TOTAL", 10.5, azul, True)
        escribir_derecha(total_x + 43, bloque_y + 22, total_w - 48, 10, dinero(total_general), 13, azul, True)

        # --------------------------------------------------------
        # PIE DE PÁGINA
        # --------------------------------------------------------

        linea(pie - 7, azul, 1.5)
        escribir(izquierda, pie - 4, 110, 6, "Gracias por su compra", 8.5, azul, True)
        escribir_derecha(116, pie - 4, 68, 6, f"Pedido #{datos.get('id', '')}", 8, gris, True)
        escribir(
            izquierda,
            pie + 3,
            ancho,
            5,
            "Comprobante de pedido - No válido como factura fiscal",
            6.5,
            gris,
        )

        painter.end()

    def formatear_fecha(self, fecha):
        if not fecha:
            return ""

        try:
            texto = str(fecha)
            if len(texto) >= 10:
                partes = texto[:10].split("-")
                if len(partes) == 3:
                    return f"{partes[2]}/{partes[1]}/{partes[0]}"
        except Exception:
            pass

        return str(fecha)
