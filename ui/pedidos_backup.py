import os
import sqlite3
import datetime

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
        principal.setContentsMargins(24, 22, 24, 24)
        principal.setSpacing(18)

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

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(16)

        # ----------------------------------------------------
        # PRODUCTOS DISPONIBLES
        # ----------------------------------------------------

        productos_panel = QFrame()
        productos_panel.setObjectName("panel")

        productos_layout = QVBoxLayout(productos_panel)
        productos_layout.setContentsMargins(16, 16, 16, 16)
        productos_layout.setSpacing(12)

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

        self.tabla_productos.verticalHeader().setDefaultSectionSize(42)

        header = self.tabla_productos.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.Stretch
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents
        )

        productos_layout.addWidget(
            self.tabla_productos,
            1
        )

        btn_agregar = QPushButton(
            "＋ Agregar producto seleccionado"
        )
        btn_agregar.setObjectName("verde")
        btn_agregar.setMinimumHeight(44)
        btn_agregar.clicked.connect(
            self.agregar_producto_seleccionado
        )

        productos_layout.addWidget(btn_agregar)

        cuerpo.addWidget(productos_panel, 4)

        # ----------------------------------------------------
        # PEDIDO ACTUAL
        # ----------------------------------------------------

        pedido_panel = QFrame()
        pedido_panel.setObjectName("panel")

        pedido_layout = QVBoxLayout(pedido_panel)
        pedido_layout.setContentsMargins(16, 16, 16, 16)
        pedido_layout.setSpacing(12)

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

        self.tabla_pedido.verticalHeader().setDefaultSectionSize(54)

        header2 = self.tabla_pedido.horizontalHeader()

        header2.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )

        header2.setSectionResizeMode(
            1,
            QHeaderView.Stretch
        )

        header2.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents
        )

        header2.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents
        )

        header2.setSectionResizeMode(
            4,
            QHeaderView.ResizeToContents
        )

        header2.setSectionResizeMode(
            5,
            QHeaderView.Fixed
        )

        header2.resizeSection(5, 82)

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

        cuerpo.addWidget(pedido_panel, 6)

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
        header3.resizeSection(6, 190)

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

        cuerpo.addWidget(registrados_panel, 6)

        principal.addLayout(cuerpo, 1)

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

            codigo = str(producto[0] or "SIN COD")
            nombre = str(producto[1] or "")
            stock = int(producto[2] or 0)
            precio = float(producto[3] or 0)

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
                producto[0] or ""
            ).lower()

            nombre = str(
                producto[1] or ""
            ).lower()

            if texto in codigo or texto in nombre:
                encontrados.append(producto)

        self.mostrar_productos(encontrados)

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

        item_nombre = self.tabla_productos.item(
            fila,
            1
        )

        item_stock = self.tabla_productos.item(
            fila,
            2
        )

        item_precio = self.tabla_productos.item(
            fila,
            3
        )

        if not item_nombre or not item_precio:
            return

        codigo = item_codigo.text()
        nombre = item_nombre.text()

        try:
            stock = int(item_stock.text())
        except Exception:
            stock = 0

        texto_precio = (
            item_precio.text()
            .replace("$", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )

        try:
            precio = float(texto_precio)
        except Exception:
            precio = 0

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

        for producto in self.carrito:

            if (
                producto["codigo"] == codigo
                and producto["nombre"] == nombre
            ):

                producto["cantidad"] += 1

                self.actualizar_tabla_pedido()

                self.tabla_productos.setFocus()

                return

        self.carrito.append({
            "codigo": codigo,
            "nombre": nombre,
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

        total = sum(
            p["precio"] * p["cantidad"]
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

            cursor.execute("""
                INSERT INTO pedidos(
                    fecha,
                    entrega,
                    estado,
                    observaciones,
                    total,
                    forma_pago,
                    pago_efectivo,
                    pago_transferencia
                )
                VALUES(
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                fecha,
                entrega,
                "PENDIENTE",
                observaciones,
                total,
                "",
                0,
                0,
            ))

            pedido_id = cursor.lastrowid

            # Intentamos guardar el cliente si existe
            # una columna cliente_id.
            columnas = [
                fila[1]
                for fila in cursor.execute(
                    "PRAGMA table_info(pedidos)"
                ).fetchall()
            ]

            if "cliente_id" in columnas:
                pass

            for producto in self.carrito:

                subtotal = (
                    producto["precio"]
                    * producto["cantidad"]
                )

                cursor.execute("""
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
                """, (
                    pedido_id,
                    producto["nombre"],
                    producto["cantidad"],
                    producto["precio"],
                    subtotal,
                    producto["codigo"],
                ))

            conexion.commit()

        except Exception as error:

            conexion.rollback()

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar el pedido:\n\n{error}"
            )

            conexion.close()

            return

        conexion.close()

        QMessageBox.information(
            self,
            "Pedido guardado",
            f"Pedido #{pedido_id} guardado correctamente."
        )

        self.cliente.clear()
        self.obs.clear()
        self.carrito.clear()

        self.entrega.setDate(
            QDate.currentDate()
        )

        self.actualizar_tabla_pedido()
        self.cargar_pedidos()

    # ========================================================
    # PEDIDOS REGISTRADOS
    # ========================================================

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
                4, 4, 4, 4
            )

            acciones_layout.setSpacing(5)

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

        dialogo = DialogoPagoPedido(
            datos_pedido["total"],
            self
        )

        if dialogo.exec() != QDialog.Accepted:
            return

        pago = dialogo.datos()
        fecha_pago = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        conexion = sqlite3.connect(BASE_DATOS)
        cursor = conexion.cursor()

        try:
            cursor.execute("""
                UPDATE pedidos
                SET
                    estado=?,
                    forma_pago=?,
                    pago_efectivo=?,
                    pago_transferencia=?,
                    fecha_pago=?
                WHERE id=?
            """, (
                "ENTREGADO",
                pago["forma"],
                pago["efectivo"],
                pago["transferencia"],
                fecha_pago,
                pedido_id,
            ))

            conexion.commit()

        except Exception as error:
            conexion.rollback()
            conexion.close()

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo registrar el pago:\n\n{error}"
            )
            return

        conexion.close()

        # ====================================================
        # LA FACTURA SE GENERA Y GUARDA SOLAMENTE AL ENTREGAR
        # ====================================================
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
                "El pedido y el pago fueron registrados correctamente, "
                "pero no se pudo guardar la factura.\n\n"
                f"Error: {error}"
            )
            self.cargar_pedidos()
            return

        QMessageBox.information(
            self,
            "Pedido entregado",
            "El pedido fue marcado como ENTREGADO, el pago quedó "
            "registrado y la factura fue guardada correctamente.\n\n"
            f"Ubicación: {ruta}"
        )

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
            QPrintPreviewWidget.ZoomMode.FitToWidth
        )

        vista.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        vista.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
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

    def pintar_factura(
        self,
        printer,
        datos
    ):

        painter = QPainter(
            printer
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        painter.setRenderHint(
            QPainter.RenderHint.TextAntialiasing
        )

        rect = painter.viewport()

        ancho = rect.width()
        alto = rect.height()

        margen = int(ancho * 0.055)
        derecha = ancho - margen
        ancho_util = derecha - margen

        # ====================================================
        # COLORES
        # ====================================================

        azul = QColor("#1f2f63")
        rojo = QColor("#dc3b32")
        negro = QColor("#111827")
        gris = QColor("#64748b")
        gris_claro = QColor("#e2e8f0")
        fondo = QColor("#f8fafc")
        blanco = QColor("#ffffff")
        verde = QColor("#15803d")
        naranja = QColor("#c2410c")

        def fuente(
            tamano,
            negrita=False
        ):
            f = QFont("Arial")
            f.setPointSize(tamano)
            f.setBold(negrita)
            return f

        def escribir(
            x,
            y,
            w,
            h,
            texto,
            tamano=9,
            color=negro,
            negrita=False,
            alineacion=Qt.AlignLeft | Qt.AlignVCenter
        ):
            painter.setPen(color)
            painter.setFont(
                fuente(tamano, negrita)
            )
            painter.drawText(
                int(x),
                int(y),
                int(w),
                int(h),
                alineacion | Qt.TextSingleLine,
                str(texto)
            )

        def escribir_elidido(
            x,
            y,
            w,
            h,
            texto,
            tamano=9,
            color=negro,
            negrita=False
        ):
            f = fuente(tamano, negrita)
            fm = QFontMetrics(f)
            valor = fm.elidedText(
                str(texto),
                Qt.TextElideMode.ElideRight,
                int(w)
            )
            escribir(
                x, y, w, h, valor,
                tamano, color, negrita
            )

        def escribir_derecha(
            x,
            y,
            w,
            h,
            texto,
            tamano=9,
            color=negro,
            negrita=False
        ):
            escribir(
                x, y, w, h, texto,
                tamano, color, negrita,
                Qt.AlignRight | Qt.AlignVCenter
            )

        def linea(
            y,
            color=gris_claro,
            grosor=1
        ):
            painter.setPen(
                QPen(color, grosor)
            )
            painter.drawLine(
                margen,
                int(y),
                derecha,
                int(y)
            )

        # ====================================================
        # ENCABEZADO
        # ====================================================

        y = 38

        nombre_negocio = (
            get_setting(
                "nombre_negocio",
                "COTILLON"
            )
            or "COTILLON"
        ).upper()

        escribir(
            margen,
            y,
            int(ancho_util * 0.58),
            34,
            nombre_negocio,
            22,
            azul,
            True
        )

        y += 29

        direccion = get_setting(
            "direccion",
            ""
        ) or ""

        telefono = get_setting(
            "telefono",
            ""
        ) or ""

        email = get_setting(
            "email",
            ""
        ) or ""

        if direccion:
            escribir(
                margen, y,
                int(ancho_util * 0.58), 18,
                direccion, 8, gris
            )
            y += 14

        if telefono:
            escribir(
                margen, y,
                int(ancho_util * 0.58), 18,
                f"Tel: {telefono}", 8, gris
            )
            y += 14

        if email:
            escribir(
                margen, y,
                int(ancho_util * 0.58), 18,
                email, 8, gris
            )
            y += 14

        # ====================================================
        # BLOQUE FACTURA
        # ====================================================

        caja_w = int(ancho_util * 0.31)
        caja_h = 112
        caja_x = derecha - caja_w
        caja_y = 30

        painter.setBrush(
            QBrush(fondo)
        )
        painter.setPen(
            QPen(gris_claro, 1)
        )
        painter.drawRoundedRect(
            caja_x,
            caja_y,
            caja_w,
            caja_h,
            8,
            8
        )

        escribir(
            caja_x + 14,
            caja_y + 8,
            caja_w - 28,
            28,
            "FACTURA",
            17,
            rojo,
            True
        )

        escribir(
            caja_x + 14,
            caja_y + 38,
            92,
            18,
            "PEDIDO N°",
            8,
            azul,
            True
        )

        escribir_derecha(
            caja_x + 100,
            caja_y + 38,
            caja_w - 114,
            18,
            datos["id"],
            9,
            negro,
            True
        )

        escribir(
            caja_x + 14,
            caja_y + 60,
            92,
            18,
            "FECHA",
            8,
            azul,
            True
        )

        escribir_derecha(
            caja_x + 100,
            caja_y + 60,
            caja_w - 114,
            18,
            self.formatear_fecha(datos["fecha"]),
            8,
            negro
        )

        escribir(
            caja_x + 14,
            caja_y + 82,
            92,
            18,
            "ENTREGA",
            8,
            azul,
            True
        )

        escribir_derecha(
            caja_x + 100,
            caja_y + 82,
            caja_w - 114,
            18,
            self.formatear_fecha(datos["entrega"]),
            8,
            negro
        )

        y = max(
            y + 22,
            caja_y + caja_h + 18
        )

        linea(
            y,
            rojo,
            2
        )

        # ====================================================
        # CLIENTE / ENTREGA / ESTADO
        # ====================================================

        y += 16

        tercera = ancho_util / 3

        x1 = margen
        x2 = margen + tercera
        x3 = margen + tercera * 2

        escribir(
            x1, y, tercera - 12, 18,
            "FACTURAR A", 8, azul, True
        )
        escribir(
            x2, y, tercera - 12, 18,
            "FECHA DE ENTREGA", 8, azul, True
        )
        escribir(
            x3, y, tercera, 18,
            "ESTADO", 8, azul, True
        )

        y += 18

        escribir_elidido(
            x1, y, tercera - 12, 20,
            datos["cliente"] or "Sin cliente",
            9, negro, True
        )

        escribir(
            x2, y, tercera - 12, 20,
            self.formatear_fecha(datos["entrega"]) or "-",
            9, negro
        )

        estado = (
            datos.get("estado", "PENDIENTE")
            or "PENDIENTE"
        )

        color_estado = (
            verde
            if estado == "ENTREGADO"
            else naranja
        )

        escribir(
            x3, y, tercera, 20,
            estado, 9, color_estado, True
        )

        y += 27

        # ====================================================
        # OBSERVACIONES
        # ====================================================

        observaciones = (
            datos.get("observaciones", "")
            or ""
        )

        if observaciones:
            escribir(
                margen, y, 95, 18,
                "OBSERVACIONES", 8, azul, True
            )
            escribir_elidido(
                margen + 95, y,
                ancho_util - 95, 18,
                observaciones, 8, gris
            )
            y += 24

        # ====================================================
        # TABLA PRODUCTOS
        # ====================================================

        y += 6

        tabla_y = y
        tabla_h = 27

        painter.setBrush(
            QBrush(azul)
        )
        painter.setPen(
            Qt.NoPen
        )
        painter.drawRect(
            margen,
            tabla_y,
            ancho_util,
            tabla_h
        )

        # Columnas perfectamente separadas.
        w_cant = int(ancho_util * 0.10)
        w_producto = int(ancho_util * 0.48)
        w_precio = int(ancho_util * 0.20)
        w_importe = (
            ancho_util
            - w_cant
            - w_producto
            - w_precio
        )

        x_cant = margen
        x_producto = x_cant + w_cant
        x_precio = x_producto + w_producto
        x_importe = x_precio + w_precio

        escribir(
            x_cant + 6, tabla_y, w_cant - 12, tabla_h,
            "CANT.", 8, blanco, True,
            Qt.AlignCenter | Qt.AlignVCenter
        )

        escribir(
            x_producto + 8, tabla_y, w_producto - 16, tabla_h,
            "DESCRIPCIÓN", 8, blanco, True
        )

        escribir(
            x_precio + 5, tabla_y, w_precio - 10, tabla_h,
            "PRECIO UNIT.", 8, blanco, True,
            Qt.AlignRight | Qt.AlignVCenter
        )

        escribir(
            x_importe + 5, tabla_y, w_importe - 10, tabla_h,
            "IMPORTE", 8, blanco, True,
            Qt.AlignRight | Qt.AlignVCenter
        )

        y = tabla_y + tabla_h

        detalles = datos.get(
            "detalles", []
        )

        for indice, detalle in enumerate(detalles):

            producto = str(
                detalle[0] or ""
            )

            cantidad = int(
                detalle[1] or 0
            )

            precio = float(
                detalle[2] or 0
            )

            subtotal = float(
                detalle[3] or 0
            )

            fila_h = 29

            if indice % 2 == 1:
                painter.setBrush(
                    QBrush(QColor("#fafafa"))
                )
                painter.setPen(
                    Qt.NoPen
                )
                painter.drawRect(
                    margen,
                    y,
                    ancho_util,
                    fila_h
                )

            escribir(
                x_cant + 6, y, w_cant - 12, fila_h,
                cantidad, 8, negro, False,
                Qt.AlignCenter | Qt.AlignVCenter
            )

            escribir_elidido(
                x_producto + 8, y, w_producto - 16, fila_h,
                producto, 8, negro
            )

            escribir_derecha(
                x_precio + 5, y, w_precio - 10, fila_h,
                dinero(precio), 8, negro
            )

            escribir_derecha(
                x_importe + 5, y, w_importe - 10, fila_h,
                dinero(subtotal), 8, negro
            )

            painter.setPen(
                QPen(gris_claro, 1)
            )
            painter.drawLine(
                margen,
                y + fila_h,
                derecha,
                y + fila_h
            )

            y += fila_h

            # Evita que una lista enorme invada el pie.
            if y > alto - 290 and indice < len(detalles) - 1:
                painter.end()
                printer.newPage()
                painter = QPainter(printer)
                painter.setRenderHint(
                    QPainter.RenderHint.Antialiasing
                )
                painter.setRenderHint(
                    QPainter.RenderHint.TextAntialiasing
                )
                y = 50
                escribir(
                    margen, y, ancho_util, 25,
                    "FACTURA - CONTINUACIÓN",
                    14, azul, True
                )
                y += 30
                painter.setBrush(QBrush(azul))
                painter.setPen(Qt.NoPen)
                painter.drawRect(
                    margen, y, ancho_util, tabla_h
                )
                escribir(
                    x_cant + 6, y, w_cant - 12, tabla_h,
                    "CANT.", 8, blanco, True,
                    Qt.AlignCenter | Qt.AlignVCenter
                )
                escribir(
                    x_producto + 8, y, w_producto - 16, tabla_h,
                    "DESCRIPCIÓN", 8, blanco, True
                )
                escribir(
                    x_precio + 5, y, w_precio - 10, tabla_h,
                    "PRECIO UNIT.", 8, blanco, True,
                    Qt.AlignRight | Qt.AlignVCenter
                )
                escribir(
                    x_importe + 5, y, w_importe - 10, tabla_h,
                    "IMPORTE", 8, blanco, True,
                    Qt.AlignRight | Qt.AlignVCenter
                )
                y += tabla_h

        if not detalles:
            escribir(
                margen, y, ancho_util, 32,
                "No hay productos registrados.",
                9, gris, False,
                Qt.AlignCenter | Qt.AlignVCenter
            )
            y += 32

        # ====================================================
        # TOTALES
        # ====================================================

        y += 18

        total_x = int(
            margen + ancho_util * 0.60
        )
        total_w = derecha - total_x

        painter.setBrush(
            QBrush(fondo)
        )
        painter.setPen(
            QPen(gris_claro, 1)
        )
        painter.drawRoundedRect(
            total_x,
            y,
            total_w,
            86,
            8,
            8
        )

        subtotal = sum(
            float(d[3] or 0)
            for d in detalles
        )

        escribir(
            total_x + 14, y + 12,
            100, 20,
            "SUBTOTAL", 8, gris, True
        )

        escribir_derecha(
            total_x + 105, y + 12,
            total_w - 119, 20,
            dinero(subtotal), 9, negro
        )

        escribir(
            total_x + 14, y + 40,
            100, 25,
            "TOTAL", 11, azul, True
        )

        escribir_derecha(
            total_x + 105, y + 35,
            total_w - 119, 30,
            dinero(datos["total"]), 14, azul, True
        )

        y += 108

        # ====================================================
        # FORMA DE PAGO
        # ====================================================

        pago_w = int(
            ancho_util * 0.48
        )
        pago_h = 92

        painter.setBrush(
            QBrush(blanco)
        )
        painter.setPen(
            QPen(gris_claro, 1)
        )
        painter.drawRoundedRect(
            margen,
            y,
            pago_w,
            pago_h,
            8,
            8
        )

        escribir(
            margen + 14, y + 10,
            pago_w - 28, 20,
            "FORMA DE PAGO", 9, azul, True
        )

        forma = (
            datos.get("forma_pago", "")
            or "PENDIENTE"
        )

        escribir(
            margen + 14, y + 32,
            pago_w - 28, 20,
            forma, 9, negro, True
        )

        pago_linea = y + 54

        if float(datos.get("pago_efectivo", 0) or 0) > 0:
            escribir(
                margen + 14, pago_linea,
                pago_w - 28, 18,
                f"Efectivo: {dinero(datos['pago_efectivo'])}",
                8, gris
            )
            pago_linea += 17

        if float(datos.get("pago_transferencia", 0) or 0) > 0:
            escribir(
                margen + 14, pago_linea,
                pago_w - 28, 18,
                f"Transferencia: {dinero(datos['pago_transferencia'])}",
                8, gris
            )

        # ====================================================
        # PIE SIN FIRMA
        # ====================================================

        pie_y = alto - 62

        linea(
            pie_y,
            azul,
            1
        )

        escribir(
            margen, pie_y + 12,
            int(ancho_util * 0.65), 22,
            "Gracias por su compra",
            11, azul, True
        )

        escribir(
            margen, pie_y + 34,
            int(ancho_util * 0.65), 18,
            "Comprobante de pedido",
            8, gris
        )

        escribir_derecha(
            int(ancho * 0.65),
            pie_y + 14,
            derecha - int(ancho * 0.65),
            22,
            f"Pedido #{datos['id']}",
            8, gris, True
        )

        painter.end()

    # ========================================================
    # FECHAS
    # ========================================================

    def formatear_fecha(self, fecha):

        if not fecha:
            return ""

        try:

            if len(fecha) >= 10:

                partes = fecha[:10].split("-")

                if len(partes) == 3:
                    return (
                        f"{partes[2]}/"
                        f"{partes[1]}/"
                        f"{partes[0]}"
                    )

        except Exception:
            pass

        return str(fecha)