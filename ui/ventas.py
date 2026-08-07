import sys
import os
import sqlite3
import datetime
import uuid
import json

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
        super().__init__(parent); self.total=total; self.setWindowTitle('Forma de pago'); self.setModal(True); self.setFixedSize(520,460)
        self._esperando=False; self._inicio_espera=None; self._timer=QTimer(self); self._timer.setInterval(2500); self._timer.timeout.connect(self._buscar_pago_mp)
        self.setStyleSheet("QDialog{background:#f8fafc;} QLabel{color:#0f172a;} QDoubleSpinBox{background:white;border:1px solid #cbd5e1;border-radius:9px;padding:8px;font-size:16px;} QPushButton{background:#10b981;color:white;border:0;border-radius:9px;padding:10px 16px;font-weight:800;} QPushButton#cancel{background:#e2e8f0;color:#334155;} QPushButton#mp{background:#2563eb;}")
        lay=QVBoxLayout(self); title=QLabel('💳 ¿Cómo pagó el cliente?'); title.setStyleSheet('font-size:21px;font-weight:900'); lay.addWidget(title)
        info=QLabel(f'Total de la venta: $ {total:,.2f}'); info.setStyleSheet('font-size:18px;font-weight:900;color:#166534;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:9px;padding:10px;'); lay.addWidget(info)
        form=QFormLayout(); self.ef=QDoubleSpinBox(); self.tr=QDoubleSpinBox(); self.ta=QDoubleSpinBox(); self.cc=QDoubleSpinBox()
        for w in (self.ef,self.tr,self.ta,self.cc):
            w.setRange(0,total)
            w.setDecimals(2)
            w.setSingleStep(100)
            w.setPrefix('$ ')
            w.setLocale(QLocale(QLocale.Spanish, QLocale.Argentina))
            w.setMaximumWidth(250)

        # Orden explícito de Enter: sigue exactamente el orden visual de los
        # medios de pago y el último Enter confirma el pago.
        self._keyboard_enter_sequence = (self.ef, self.tr, self.ta, self.cc)
        for w in self._keyboard_enter_sequence:
            w.setFocusPolicy(Qt.StrongFocus)
        self.setTabOrder(self.ef, self.tr)
        self.setTabOrder(self.tr, self.ta)
        self.setTabOrder(self.ta, self.cc)

        form.addRow('💵 Efectivo:',self.ef); form.addRow('🔄 Mercado Pago:',self.tr); form.addRow('💳 Tarjeta:',self.ta); form.addRow('📒 Cuenta corriente:',self.cc); lay.addLayout(form)
        self.estado=QLabel(); self.estado.setWordWrap(True); self.estado.setStyleSheet('font-weight:800;'); lay.addWidget(self.estado)
        self.mp_info=QLabel(''); self.mp_info.setWordWrap(True); lay.addWidget(self.mp_info)
        for w in (self.ef,self.tr,self.ta,self.cc): w.valueChanged.connect(self.validar)
        b=QHBoxLayout(); b.addStretch(); cancel=QPushButton('Cancelar'); cancel.setObjectName('cancel'); cancel.clicked.connect(self.reject); self.ok=QPushButton('Confirmar pago'); self.ok.setProperty('keyboard_primary', True); self.ok.clicked.connect(self.confirmar); self.mp=QPushButton('🔎 Esperar Mercado Pago'); self.mp.setObjectName('mp'); self.mp.clicked.connect(self.esperar_mercado_pago); b.addWidget(cancel); b.addWidget(self.mp); b.addWidget(self.ok); lay.addLayout(b); self.validar()
        self.ef.setFocus(Qt.OtherFocusReason)
    def suma(self): return self.ef.value()+self.tr.value()+self.ta.value()+self.cc.value()
    def validar(self):
        dif=round(self.total-self.suma(),2); self.estado.setText('🟢 Importe completo' if abs(dif)<0.01 else (f'⚠️ Falta pagar: $ {dif:,.2f}' if dif>0 else f'⚠️ Excede el total: $ {abs(dif):,.2f}')); self.estado.setStyleSheet('font-weight:800;color:#166534;' if abs(dif)<0.01 else 'font-weight:800;color:#b45309;')
        self.mp.setEnabled(self.tr.value()>0 and abs(dif)<0.01 and not self._esperando)
    def keyboard_submit(self): self.confirmar()
    def confirmar(self):
        if abs(self.total-self.suma())>=0.01: QMessageBox.warning(self,'Pago incompleto','Los medios de pago deben sumar exactamente el total de la venta.'); return
        if self.tr.value()>0 and not self._esperando:
            r=QMessageBox.question(self,'Mercado Pago','Se indicó un pago de Mercado Pago. ¿Querés confirmar manualmente o esperar la acreditación automática?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
            if r==QMessageBox.Yes: self.accept(); return
            self.esperar_mercado_pago(); return
        self.accept()
    def esperar_mercado_pago(self):
        if self.tr.value()<=0 or abs(self.total-self.suma())>=0.01:return
        from ui.mercadopago import token_activo, nombre_cuenta_activa
        token=token_activo()
        if not token:
            QMessageBox.warning(self,'Mercado Pago','No hay una cuenta de Mercado Pago activa con Access Token. Configurala antes de usar la detección automática.'); return
        self._esperando=True; self._inicio_espera=datetime.datetime.now(datetime.timezone.utc); self.mp.setEnabled(False); self.ok.setEnabled(False); self.cancel.setEnabled(False)
        self.mp_info.setText(f'🔵 Esperando acreditación de $ {self.tr.value():,.2f} en {nombre_cuenta_activa()}...\nEl POS consulta Mercado Pago automáticamente.')
        self._timer.start()
    def _buscar_pago_mp(self):
        try:
            from ui.mercadopago import token_activo, buscar_pago_aprobado_por_importe, guardar_pagos
            p=buscar_pago_aprobado_por_importe(token_activo(),self.tr.value(),self._inicio_espera)
            if p:
                guardar_pagos([p]); self._timer.stop(); self._esperando=False; self.mp_info.setText(f'✅ Pago encontrado y aprobado. ID: {p.get("id")}'); self.ok.setEnabled(True); self.cancel.setEnabled(True); self.accept()
        except Exception as e:
            self.mp_info.setText('⚠️ No se pudo consultar Mercado Pago. Se reintentará automáticamente.')
    def closeEvent(self,e):
        self._timer.stop(); super().closeEvent(e)
    def datos(self):
        vals={'efectivo':self.ef.value(),'transferencia':self.tr.value(),'tarjeta':self.ta.value(),'cuenta':self.cc.value()}; usados=[k for k,v in vals.items() if v>0]; labels={'efectivo':'Efectivo','transferencia':'Mercado Pago','tarjeta':'Tarjeta','cuenta':'Cuenta corriente'}; vals['forma']=' + '.join(labels[k] for k in usados) if usados else 'Efectivo'; return vals

class Ventas(QWidget):

    def __init__(self):
        super().__init__()

        # Nos aseguramos de que la base de datos y sus tablas existan al abrir el módulo
        inicializar_base_datos_si_no_existe()

        self.setWindowTitle(f"{get_setting('nombre_negocio','COTILLON')} POS — Nueva venta")
        self.resize(1000, 680)
        self.setMinimumSize(900, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.carrito = []
        self.setFocusPolicy(Qt.StrongFocus)

        # Estilo Global Unificado (CSS) profesional
        self.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                color: #0f172a;
            }
            
            /* Inputs y Combos estilizados */
            QLineEdit, QComboBox {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                color: #0f172a;
            }
            QLineEdit:focus, QComboBox:focus {
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

            /* Tabla de Productos */
            QTableWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                gridline-color: #f1f5f9;
                font-size: 15px;
            }
            QTableWidget::item {
                padding: 6px 12px;
                color: #334155;
            }
            QTableWidget::item:selected {
                background-color: #e0e7ff;
                color: #3730a3;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #0f172a;
                color: white;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }

            /* Botones de acción corta */
            QPushButton {
                background-color: #0ea5e9;
                color: white;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: 600;
                border: none;
            }
            QPushButton:hover {
                background-color: #0284c7;
            }

            /* Botones secundarios */
            QPushButton#btnEliminar {
                background-color: #fee2e2;
                color: #dc2626;
                border: 1px solid #fecaca;
            }
            QPushButton#btnEliminar:hover {
                background-color: #ef4444;
                color: white;
            }
        """)

        # --- LAYOUT PRINCIPAL ---
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(25)

        # ==========================================
        # COLUMNA IZQUIERDA: BUSCADOR Y TABLA
        # ==========================================
        col_izquierda = QVBoxLayout()
        col_izquierda.setSpacing(15)

        titulo = QLabel("🛒 Nueva Venta")
        titulo.setStyleSheet("font-size: 26px; font-weight: 800; color: #0f172a;")
        col_izquierda.addWidget(titulo)

        # Buscador y botón de emergencia para listar productos
        layout_buscador = QHBoxLayout()
        
        self.buscar = QLineEdit()
        self.buscar.focusInEvent = self.limpiar_busqueda_al_entrar
        self.buscar.setProperty('keyboard_navigation_skip', True)
        self.buscar.setPlaceholderText("🔍 Escanee código, busque producto o escriba uno libre y presione Enter...")
        self.buscar.setStyleSheet("font-size: 15px; padding: 12px 16px; border-radius: 10px;")
        self.buscar.returnPressed.disconnect()
        self.buscar.returnPressed.connect(self.confirmar_sugerencia)
        self.buscar.returnPressed.connect(
        self.confirmar_sugerencia
        )

        self.buscar.editingFinished.connect(
        self.limpiar_buscador
        )
        btn_ver_todos = QPushButton("📋 Ver BD")
        btn_ver_todos.setToolTip("Muestra todos los productos guardados en la base de datos")
        btn_ver_todos.setCursor(Qt.PointingHandCursor)
        btn_ver_todos.clicked.connect(self.mostrar_todos_los_productos)
        btn_ver_todos.setStyleSheet("background-color: #64748b; padding: 10px 14px;")

        layout_buscador.addWidget(self.buscar, stretch=4)
        layout_buscador.addWidget(btn_ver_todos, stretch=1)
        col_izquierda.addLayout(layout_buscador)

        # Tabla de Productos
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Producto", "Cant.", "Precio Unit.", "Subtotal", "Código"])
        
        # self.tabla.setItemDelegate(EditorCeldaVentasDelegate(self.tabla))
        self.tabla.verticalHeader().setDefaultSectionSize(50)
        self.tabla.setAlternatingRowColors(True)
        
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.tabla.setColumnWidth(1, 90)
        self.tabla.setColumnWidth(2, 130)
        self.tabla.setColumnWidth(3, 130)

        col_izquierda.addWidget(self.tabla)

        # Botones para editar ítems del carrito
        botones_tabla = QHBoxLayout()
        botones_tabla.setSpacing(12)

        btn_sumar = QPushButton("➕ Sumar Cantidad")
        btn_restar = QPushButton("➖ Restar Cantidad")
        btn_eliminar = QPushButton("🗑️ Quitar Ítem")
        btn_eliminar.setObjectName("btnEliminar")

        for btn in [btn_sumar, btn_restar, btn_eliminar]:
            btn.setCursor(Qt.PointingHandCursor)

        btn_sumar.clicked.connect(self.sumar_cantidad)
        btn_restar.clicked.connect(self.restar_cantidad)
        btn_eliminar.clicked.connect(self.eliminar_producto)

        botones_tabla.addWidget(btn_sumar)
        botones_tabla.addWidget(btn_restar)
        botones_tabla.addWidget(btn_eliminar)
        col_izquierda.addLayout(botones_tabla)

        main_layout.addLayout(col_izquierda, stretch=3)

        # ==========================================
        # COLUMNA DERECHA: RESUMEN Y COBRO
        # ==========================================
        panel_derecho = QFrame()
        panel_derecho.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 16px;
                border: 1px solid #e2e8f0;
            }
        """)
        
        col_derecha = QVBoxLayout(panel_derecho)
        col_derecha.setContentsMargins(12, 12, 12, 12)
        col_derecha.setSpacing(10)

        header_panel = QHBoxLayout()
        lbl_resumen = QLabel("💳 Caja y Cobro")
        lbl_resumen.setStyleSheet("font-size: 20px; font-weight: 800; color: #0f172a; border: none;")
        header_panel.addWidget(lbl_resumen)
        col_derecha.addLayout(header_panel)

        linea_sep = QFrame()
        linea_sep.setFixedHeight(1)
        linea_sep.setStyleSheet("background-color: #e2e8f0; border: none;")
        col_derecha.addWidget(linea_sep)

        lbl_cli_title = QLabel("👤 Cliente")
        lbl_cli_title.setStyleSheet("font-weight: 700; color: #475569; font-size: 13px; border: none;")
        col_derecha.addWidget(lbl_cli_title)

        self.cliente = QComboBox()
        self.cliente.setCursor(Qt.PointingHandCursor)
        self.cliente.setStyleSheet("padding: 10px; font-size: 14px;")
        col_derecha.addWidget(self.cliente)

        lbl_pago_title = QLabel("💵 Forma de Pago")
        lbl_pago_title.setStyleSheet("font-weight: 700; color: #475569; font-size: 13px; border: none;")
        col_derecha.addWidget(lbl_pago_title)

        self.forma_pago = QComboBox()
        self.forma_pago.setCursor(Qt.PointingHandCursor)
        self.forma_pago.addItems(["Efectivo", "Tarjeta", "Transferencia", "Cuenta corriente"])
        self.forma_pago.setStyleSheet("padding: 10px; font-size: 14px;")
        col_derecha.addWidget(self.forma_pago)

        col_derecha.addStretch()

        cuadro_total = QFrame()
        cuadro_total.setStyleSheet("""
            QFrame {
                background-color: #f0fdf4;
                border: 2px solid #bbf7d0;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        layout_total = QVBoxLayout(cuadro_total)
        layout_total.setContentsMargins(10, 10, 10, 10)
        layout_total.setSpacing(4)
        
        lbl_total_titulo = QLabel("TOTAL A PAGAR")
        lbl_total_titulo.setStyleSheet("font-size: 11px; font-weight: 800; color: #15803d; letter-spacing: 1px; border: none;")
        
        self.total = QLabel("$0,00")
        self.total.setStyleSheet("font-size: 26px; font-weight: 900; color: #166534; border: none;")

        layout_total.addWidget(lbl_total_titulo)
        layout_total.addWidget(self.total)
        col_derecha.addWidget(cuadro_total)

        self.boton_cobrar = QPushButton("💰  COBRAR (F8)")
        self.boton_cobrar.setCursor(Qt.PointingHandCursor)
        self.boton_cobrar.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-size: 14px;
                font-weight: 800;
                padding: 10px;
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
        self.boton_cobrar.clicked.connect(self.cobrar)
        col_derecha.addWidget(self.boton_cobrar)

        main_layout.addWidget(panel_derecho, stretch=1)
        self.setLayout(main_layout)

        # Accesos rápidos visibles
        accesos = QHBoxLayout()
        for texto, funcion in [("F2 Arqueo", self.abrir_arqueo), ("F3 Dotación", self.dotacion), ("F4 Descuento", self.aplicar_descuento), ("F8 Cobrar", self.cobrar), ("F9 Cancelar", self.cancelar_venta), ("F10 Consulta", self.consulta_precio), ("F11 Buscar", lambda:self.buscar.setFocus())]:
            b=QPushButton(texto); b.setStyleSheet("background:#334155;padding:6px 8px;font-size:12px"); b.clicked.connect(funcion); b.setMinimumHeight(30)
            accesos.addWidget(b)
        # Insertarlos como primera fila del layout principal sin alterar el diseño original
        col_derecha.insertLayout(0, accesos)

        self.tabla.itemChanged.connect(self.celda_modificada)

        self.cargar_clientes()
        self.cargar_sugerencias()
        self.buscar.setFocus()

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

    def showEvent(self, event):
        super().showEvent(event)
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cargar_clientes()
        self.cargar_sugerencias()
        self.buscar.setFocus()
        QTimer.singleShot(0, self.refresh_layout_on_return)
        QTimer.singleShot(50, self.refresh_layout_on_return)


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
            detalle.setText(f'<b>{nombre}</b><br>Código: {codigo}<br><span style="font-size:40px;font-weight:900">$ {format_number(f"{precio:.2f}",2)}</span>')
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

    def cargar_sugerencias(self):
        try:
            conexion = sqlite3.connect(BASE_DATOS)
            cursor = conexion.cursor()
            cursor.execute("SELECT nombre FROM productos ORDER BY nombre")
            productos = [fila[0] for fila in cursor.fetchall()]
            conexion.close()

            completador = QCompleter(productos)
            completador.setCaseSensitivity(Qt.CaseInsensitive)
            completador.setFilterMode(Qt.MatchContains)
            completador.activated[str].connect(self.seleccionar_producto_completer)
            
            self.buscar.setCompleter(completador)
  
        except Exception as e:
            print(f"Error al cargar sugerencias: {e}")
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
                "codigo": producto[1] if producto[1] else "SIN_COD",
                "nombre": producto[2],
                "precio": producto[5],
                "cantidad": 1
            })

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
                    "codigo": producto[1] if producto[1] else "SIN_COD",
                    "nombre": producto[2],
                    "precio": float(producto[5]),
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
            productos = listar_productos()

            encontrados = []

            for p in productos:
                codigo = str(p.get("codigo_barras", "") or "")
                nombre = str(p.get("nombre", "") or "")

                if (
                    texto.lower() in nombre.lower()
                    or texto.lower() in codigo.lower()
                ):
                    encontrados.append(p)

            if encontrados:
                producto = encontrados[0]

                self.agregar_carrito({
                    "codigo": producto.get("codigo_barras") or "SIN_COD",
                    "nombre": producto["nombre"],
                    "precio": float(producto["precio_venta"]),
                    "cantidad": 1
                })

                self.buscar.clear()
                self.buscar.setFocus()
                return

        except Exception as e:
            print("Error consultando Railway:", e)

        dialogo = QDialog(self)
        dialogo.setWindowTitle("Producto no encontrado")
        dialogo.setModal(True)
        dialogo.setFixedSize(420, 220)

        dialogo.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 12px;
            }

            QLabel {
                color: #0f172a;
                font-size: 15px;
            }

            QPushButton {
                border-radius: 8px;
                padding: 10px 22px;
                font-weight: bold;
                font-size: 14px;
            }

            QPushButton#agregar {
                background-color: #10b981;
                color: white;
            }

            QPushButton#cancelar {
                background-color: #e2e8f0;
                color: #334155;
            }
        """)

        layout = QVBoxLayout(dialogo)

        titulo = QLabel("⚠️ Producto no encontrado")
        titulo.setStyleSheet(
            "font-size:22px;font-weight:800;color:#b45309;"
        )

        mensaje = QLabel(
            f"No existe el producto:\n\n"
            f"<b>{texto}</b>\n\n"
            "¿Desea cargarlo manualmente?"
        )
        mensaje.setWordWrap(True)

        layout.addWidget(titulo)
        layout.addWidget(mensaje)

        botones = QHBoxLayout()

        btn_no = QPushButton("Cancelar")
        btn_no.setObjectName("cancelar")

        btn_si = QPushButton("Agregar manual")
        btn_si.setObjectName("agregar")

        botones.addStretch()
        botones.addWidget(btn_no)
        botones.addWidget(btn_si)

        layout.addLayout(botones)

        resultado = {"ok": False}

        btn_si.clicked.connect(
            lambda: (resultado.update(ok=True), dialogo.accept())
        )

        btn_no.clicked.connect(dialogo.reject)

        dialogo.exec()

        if resultado["ok"]:
            self.agregar_producto_libre(texto)
        else:
            self.buscar.clear()
            self.buscar.setFocus()
            return

        if respuesta == QMessageBox.Yes:
            self.agregar_producto_libre(texto)
        else:
            self.buscar.clear()
            self.buscar.selectAll()
            
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
                item["codigo"] == prod_dict["codigo"]
                and item["nombre"] == prod_dict["nombre"]
            ):

                self.actualizar_tabla()
                return


        # Producto nuevo siempre empieza en 1
        prod_dict["cantidad"] = 1

        self.carrito.append(
            prod_dict
        )


        self.actualizar_tabla()
        self.actualizar_tabla()

    def limpiar_buscador(self):

        self.buscar.blockSignals(True)

        self.buscar.clear()

        self.buscar.blockSignals(False)


        self.buscar.setFocus(
            Qt.OtherFocusReason
        )
        
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
        """
        Guarda una venta en SQLite local.
        Funciona sin Internet.
        """
        init_db()
        conexion = create_connection()
        cursor = conexion.cursor()

        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        total = sum(
            item["precio"] * item["cantidad"]
            for item in venta["items"]
        )
        venta_uuid = str(uuid.uuid4())
        
        
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
        """,(
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
            """,(
                venta_id,
                item["producto"],
                item["cantidad"],
                item["precio"],
                subtotal,
                item["codigo"]
            ))


            # bajar stock local
            if item["codigo"] != "LIBRE":

                cursor.execute("""
                    UPDATE productos
                    SET stock = stock - ?
                    WHERE codigo_barras = ?
                """,(
                    item["cantidad"],
                    item["codigo"]
                ))

        
        import json

        # UUID único para la venta
        venta_uuid = str(uuid.uuid4())

        cursor.execute("""
        UPDATE ventas
        SET uuid=?
        WHERE id=?
        """, (
            venta_uuid,
            venta_id
        ))

        # Guardar pendiente de sincronización
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
        VALUES
        (
            ?, ?, ?, ?, ?, ?, ?
        )
        """,
        (
            "ventas",
            venta_id,
            venta_uuid,
            "INSERT",
            json.dumps(venta),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            0
        ))
        conexion.commit()
        conexion.close()

        return venta_id
    
    
    def cobrar(self):
        if not self.carrito:
            DialogoAviso("Aviso", "No hay productos en la venta actual.", self).exec(); return
        total_venta=sum(p["precio"]*p["cantidad"] for p in self.carrito)
        pago=DialogoPagoMixto(total_venta,self)
        if pago.exec()!=QDialog.Accepted: return
        datos=pago.datos()
        try:
            items = []

            for p in self.carrito:
                items.append({
                    "producto_id": 0,
                    "producto": p["nombre"],
                    "cantidad": p["cantidad"],
                    "precio": p["precio"],
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

            venta_id = self.guardar_venta_local(venta)
            respuesta=QMessageBox.question(self,"Venta Exitosa",f"Venta guardada correctamente.\n\nTotal: $ {total_venta:,.2f}\n\nEfectivo: $ {datos['efectivo']:,.2f}\nTransferencia: $ {datos['transferencia']:,.2f}\n\n¿Desea imprimir el ticket?",QMessageBox.Yes|QMessageBox.No)
            if respuesta==QMessageBox.Yes:
                try: imprimir_ticket(generar_ticket(venta_id))
                except Exception as error: DialogoAviso("Error de Impresión",str(error),self).exec()
            self.carrito.clear(); self.actualizar_tabla(); self.buscar.clear(); self.buscar.setFocus()
        except Exception as error:
            DialogoAviso(
                "Error al guardar la venta",
                str(error),
                self
            ).exec()

