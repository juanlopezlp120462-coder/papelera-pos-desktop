import sys
import sqlite3
from ui.keyboard import setup_numeric, parse_number
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QMessageBox,
    QGraphicsDropShadowEffect,
    QAbstractItemView,
    QStyledItemDelegate,
    QDialog,
    QFormLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from ui.db import BASE_DATOS, init_db


def mostrar_mensaje(parent, titulo, texto, icono=QMessageBox.Information, botones=QMessageBox.Ok):
    """Crea una ventana de mensaje personalizada con visibilidad garantizada."""
    msg = QMessageBox(parent)
    msg.setWindowTitle(titulo)
    msg.setText(texto)
    msg.setIcon(icono)
    msg.setStandardButtons(botones)
    
    # Estilo controlado que no interfiere con el texto nativo del QMessageBox
    msg.setStyleSheet("""
        QMessageBox {
            background-color: #ffffff;
        }
        QPushButton {
            background-color: #2563eb;
            color: #ffffff;
            font-weight: bold;
            border-radius: 6px;
            padding: 8px 16px;
            min-width: 80px;
            border: none;
        }
        QPushButton:hover {
            background-color: #1d4ed8;
        }
    """)
    return msg


def reparar_tabla_clientes(cursor):
    """
    Crea la tabla si no existe y verifica que contenga todas
    las columnas requeridas. Si falta alguna, la agrega dinámicamente.
    """
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    """)
    
    cursor.execute("PRAGMA table_info(clientes)")
    columnas_existentes = [col[1] for col in cursor.fetchall()]
    
    columnas_requeridas = {
        "documento": "TEXT",
        "telefono": "TEXT",
        "direccion": "TEXT",
        "saldo": "REAL DEFAULT 0.0"
    }
    
    for col, tipo in columnas_requeridas.items():
        if col not in columnas_existentes:
            cursor.execute(f"ALTER TABLE clientes ADD COLUMN {col} {tipo};")


# ==========================================
# VENTANA FLOTANTE PARA AGREGAR CLIENTE
# ==========================================
class AgregarClienteModal(QDialog):
    cliente_guardado = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("➕ Nuevo Cliente")
        self.setFixedSize(420, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                font-size: 13px;
                font-weight: 600;
                color: #334155;
            }
            QLineEdit {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                color: #0f172a;
            }
            QLineEdit:focus {
                border: 2px solid #2563eb;
                background-color: #ffffff;
            }
            QPushButton#btnGuardar {
                background-color: #2563eb;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
                padding: 12px;
                border: none;
            }
            QPushButton#btnGuardar:hover {
                background-color: #1d4ed8;
            }
            QPushButton#btnCancelar {
                background-color: #e2e8f0;
                color: #475569;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
                padding: 12px;
                border: none;
            }
            QPushButton#btnCancelar:hover {
                background-color: #cbd5e1;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        lbl_titulo = QLabel("Registrar Nuevo Cliente")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: 800; color: #0f172a; margin-bottom: 5px;")
        layout.addWidget(lbl_titulo)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.txt_doc = QLineEdit()
        self.txt_doc.setPlaceholderText("Opcional")

        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Juan Pérez (Obligatorio)")

        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("Opcional")

        self.txt_direccion = QLineEdit()
        self.txt_direccion.setPlaceholderText("Opcional")

        self.txt_saldo = QLineEdit()
        setup_numeric(self.txt_saldo, 2)
        self.txt_saldo.setPlaceholderText("Opcional (Por defecto $ 0.00)")

        form_layout.addRow("Nombre y Apellido *:", self.txt_nombre)
        form_layout.addRow("DNI / CUIT:", self.txt_doc)
        form_layout.addRow("Teléfono:", self.txt_telefono)
        form_layout.addRow("Dirección:", self.txt_direccion)
        form_layout.addRow("Saldo Inicial ($):", self.txt_saldo)

        layout.addLayout(form_layout)
        layout.addStretch()

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btnCancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton("💾 Guardar Cliente")
        btn_guardar.setObjectName("btnGuardar")
        btn_guardar.setCursor(Qt.PointingHandCursor)
        btn_guardar.clicked.connect(self.guardar_cliente)

        btn_box.addWidget(btn_cancelar)
        btn_box.addWidget(btn_guardar)

        layout.addLayout(btn_box)

    def guardar_cliente(self):
        nombre = self.txt_nombre.text().strip()
        doc = self.txt_doc.text().strip()
        tel = self.txt_telefono.text().strip()
        dire = self.txt_direccion.text().strip()
        saldo_txt = self.txt_saldo.text().replace('$','').strip()

        if not nombre:
            msg = mostrar_mensaje(self, "Aviso", "Por favor ingresá al menos el Nombre del cliente.", QMessageBox.Warning)
            msg.exec()
            return

        saldo = 0.0
        if saldo_txt:
            try:
                saldo = parse_number(saldo_txt) or 0.0
            except ValueError:
                saldo = 0.0

        try:
            conexion = sqlite3.connect(BASE_DATOS)
            cursor = conexion.cursor()
            reparar_tabla_clientes(cursor)
            
            cursor.execute("""
                INSERT INTO clientes (documento, nombre, telefono, direccion, saldo)
                VALUES (?, ?, ?, ?, ?)
            """, (doc, nombre, tel, dire, saldo))
            conexion.commit()
            conexion.close()

            self.cliente_guardado.emit()
            self.accept()
        except Exception as e:
            msg = mostrar_mensaje(self, "Error", f"No se pudo guardar el cliente:\n{e}", QMessageBox.Critical)
            msg.exec()


# ==========================================
# VENTANA FLOTANTE PARA EDITAR CLIENTE
# ==========================================
class EditarClienteModal(QDialog):
    cliente_actualizado = Signal()

    def __init__(self, cliente_id, parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.setWindowTitle("✏️ Editar Cliente")
        self.setFixedSize(420, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                font-size: 13px;
                font-weight: 600;
                color: #334155;
            }
            QLineEdit {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                color: #0f172a;
            }
            QLineEdit:focus {
                border: 2px solid #f59e0b;
                background-color: #ffffff;
            }
            QPushButton#btnGuardar {
                background-color: #f59e0b;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
                padding: 12px;
                border: none;
            }
            QPushButton#btnGuardar:hover {
                background-color: #d97706;
            }
            QPushButton#btnCancelar {
                background-color: #e2e8f0;
                color: #475569;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
                padding: 12px;
                border: none;
            }
            QPushButton#btnCancelar:hover {
                background-color: #cbd5e1;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        lbl_titulo = QLabel("Modificar Información")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: 800; color: #0f172a; margin-bottom: 5px;")
        layout.addWidget(lbl_titulo)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.txt_doc = QLineEdit()
        self.txt_nombre = QLineEdit()
        self.txt_telefono = QLineEdit()
        self.txt_direccion = QLineEdit()
        self.txt_saldo = QLineEdit()
        setup_numeric(self.txt_saldo, 2)

        form_layout.addRow("Nombre y Apellido *:", self.txt_nombre)
        form_layout.addRow("DNI / CUIT:", self.txt_doc)
        form_layout.addRow("Teléfono:", self.txt_telefono)
        form_layout.addRow("Dirección:", self.txt_direccion)
        form_layout.addRow("Saldo Pendiente ($):", self.txt_saldo)

        layout.addLayout(form_layout)
        layout.addStretch()

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btnCancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton("💾 Guardar Cambios")
        btn_guardar.setObjectName("btnGuardar")
        btn_guardar.setCursor(Qt.PointingHandCursor)
        btn_guardar.clicked.connect(self.actualizar_cliente)

        btn_box.addWidget(btn_cancelar)
        btn_box.addWidget(btn_guardar)

        layout.addLayout(btn_box)

        self.cargar_datos_cliente()

    def cargar_datos_cliente(self):
        try:
            conexion = sqlite3.connect(BASE_DATOS)
            cursor = conexion.cursor()
            reparar_tabla_clientes(cursor)
            cursor.execute("SELECT documento, nombre, telefono, direccion, saldo FROM clientes WHERE id = ?", (self.cliente_id,))
            cli = cursor.fetchone()
            conexion.close()

            if cli:
                self.txt_doc.setText(str(cli[0]) if cli[0] else "")
                self.txt_nombre.setText(str(cli[1]) if cli[1] else "")
                self.txt_telefono.setText(str(cli[2]) if cli[2] else "")
                self.txt_direccion.setText(str(cli[3]) if cli[3] else "")
                self.txt_saldo.setText(str(cli[4]) if cli[4] is not None else "0.00")
        except Exception as e:
            msg = mostrar_mensaje(self, "Error", f"No se pudieron cargar los datos del cliente:\n{e}", QMessageBox.Critical)
            msg.exec()

    def actualizar_cliente(self):
        nombre = self.txt_nombre.text().strip()
        doc = self.txt_doc.text().strip()
        tel = self.txt_telefono.text().strip()
        dire = self.txt_direccion.text().strip()
        saldo_txt = self.txt_saldo.text().replace('$','').strip()

        if not nombre:
            msg = mostrar_mensaje(self, "Aviso", "Por favor ingresá al menos el Nombre del cliente.", QMessageBox.Warning)
            msg.exec()
            return

        saldo = 0.0
        if saldo_txt:
            try:
                saldo = parse_number(saldo_txt) or 0.0
            except ValueError:
                saldo = 0.0

        try:
            conexion = sqlite3.connect(BASE_DATOS)
            cursor = conexion.cursor()
            reparar_tabla_clientes(cursor)
            cursor.execute("""
                UPDATE clientes 
                SET documento=?, nombre=?, telefono=?, direccion=?, saldo=?
                WHERE id=?
            """, (doc, nombre, tel, dire, saldo, self.cliente_id))
            conexion.commit()
            conexion.close()

            self.cliente_actualizado.emit()
            self.accept()
        except Exception as e:
            msg = mostrar_mensaje(self, "Error", f"No se pudo actualizar el cliente:\n{e}", QMessageBox.Critical)
            msg.exec()


# ==========================================
# DELEGADO DE EDICIÓN
# ==========================================
class EditorCeldaDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #0f172a;
                border: 2px solid #2563eb;
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


# ==========================================
# VISTA PRINCIPAL DE CLIENTES
# ==========================================
class Clientes(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gestión de Clientes - Abril POS")
        self.resize(980, 650)

        self.cargando_datos = False

        self.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
                font-family: 'Segoe UI', sans-serif;
            }
            QFrame#cardTabla, QFrame#cardKpi {
                background-color: #ffffff;
                border-radius: 16px;
                border: 1px solid #e2e8f0;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 14px;
                color: #0f172a;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
            QPushButton {
                font-weight: 600;
                font-size: 14px;
                border-radius: 10px;
                padding: 10px 18px;
                border: none;
            }
            QPushButton#btnAgregar {
                background-color: #2563eb;
                color: white;
            }
            QPushButton#btnAgregar:hover {
                background-color: #1d4ed8;
            }
            QPushButton#btnActualizar {
                background-color: #e2e8f0;
                color: #334155;
            }
            QPushButton#btnActualizar:hover {
                background-color: #cbd5e1;
            }
            QPushButton#btnEditar {
                background-color: #f59e0b;
                color: white;
            }
            QPushButton#btnEditar:hover {
                background-color: #d97706;
            }
            QPushButton#btnEliminar {
                background-color: #ef4444;
                color: white;
            }
            QPushButton#btnEliminar:hover {
                background-color: #dc2626;
            }
        """)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(20)

        # 1. ENCABEZADO Y BUSCADOR
        header_layout = QHBoxLayout()

        header_info = QVBoxLayout()
        lbl_titulo = QLabel("👥 Directorio de Clientes")
        lbl_titulo.setStyleSheet("font-size: 26px; font-weight: 800; color: #0f172a;")
        lbl_sub = QLabel("Administrá tus clientes, datos de contacto y saldos de cuenta corriente.")
        lbl_sub.setStyleSheet("font-size: 14px; color: #64748b;")
        header_info.addWidget(lbl_titulo)
        header_info.addWidget(lbl_sub)

        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("🔍 Buscar por nombre, DNI/CUIT o teléfono...")
        self.buscar.setFixedWidth(340)
        self.buscar.textChanged.connect(self.buscar_clientes)

        header_layout.addLayout(header_info)
        header_layout.addStretch()
        header_layout.addWidget(self.buscar)

        layout_principal.addLayout(header_layout)

        # 2. TARJETAS INFORMATIVAS (KPIs)
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(15)

        self.card_total_clientes = self.crear_tarjeta_kpi("👤 Total Clientes", "0", "#3b82f6")
        self.card_con_deuda = self.crear_tarjeta_kpi("⚠️ Con Saldo / Deuda", "0", "#ef4444")
        self.card_al_dia = self.crear_tarjeta_kpi("✅ Cuentas al Día", "0", "#10b981")

        kpi_layout.addWidget(self.card_total_clientes)
        kpi_layout.addWidget(self.card_con_deuda)
        kpi_layout.addWidget(self.card_al_dia)

        layout_principal.addLayout(kpi_layout)

        # 3. BARRA DE BOTONES DE ACCIÓN
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(12)

        btn_agregar = QPushButton("➕ Nuevo Cliente")
        btn_agregar.setObjectName("btnAgregar")
        btn_agregar.setCursor(Qt.PointingHandCursor)
        btn_agregar.clicked.connect(self.abrir_agregar)

        btn_actualizar = QPushButton("🔄 Actualizar")
        btn_actualizar.setObjectName("btnActualizar")
        btn_actualizar.setCursor(Qt.PointingHandCursor)
        btn_actualizar.clicked.connect(self.cargar_clientes)

        btn_editar = QPushButton("✏️ Editar Cliente")
        btn_editar.setObjectName("btnEditar")
        btn_editar.setCursor(Qt.PointingHandCursor)
        btn_editar.clicked.connect(self.editar_cliente)

        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setObjectName("btnEliminar")
        btn_eliminar.setCursor(Qt.PointingHandCursor)
        btn_eliminar.clicked.connect(self.eliminar_cliente)

        botones_layout.addWidget(btn_agregar)
        botones_layout.addWidget(btn_actualizar)
        botones_layout.addWidget(btn_editar)
        botones_layout.addWidget(btn_eliminar)
        botones_layout.addStretch()

        layout_principal.addLayout(botones_layout)

        # 4. TABLA DE CLIENTES
        card_tabla = QFrame()
        card_tabla.setObjectName("cardTabla")
        self.aplicar_sombra(card_tabla)

        tabla_layout = QVBoxLayout(card_tabla)
        tabla_layout.setContentsMargins(15, 15, 15, 15)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "ID / Doc.", "Nombre y Apellido", "Teléfono", "Dirección", "Saldo Pendiente", "Estado"
        ])
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setAlternatingRowColors(True)

        self.tabla.setItemDelegate(EditorCeldaDelegate(self.tabla))
        self.tabla.verticalHeader().setDefaultSectionSize(48)

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.tabla.setColumnWidth(2, 140)
        self.tabla.setColumnWidth(4, 140)

        self.tabla.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: none;
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
                color: #ffffff;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
        """)

        tabla_layout.addWidget(self.tabla)
        layout_principal.addWidget(card_tabla)

        self.cargar_clientes()

    def crear_tarjeta_kpi(self, titulo, valor_inicial, color_borde):
        card = QFrame()
        card.setObjectName("cardKpi")
        card.setStyleSheet(f"""
            QFrame#cardKpi {{
                border-left: 5px solid {color_borde};
                padding: 12px;
            }}
        """)
        self.aplicar_sombra(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(4)

        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748b;")

        lbl_val = QLabel(valor_inicial)
        lbl_val.setObjectName("valorKpi")
        lbl_val.setStyleSheet("font-size: 22px; font-weight: 800; color: #0f172a;")

        layout.addWidget(lbl_tit)
        layout.addWidget(lbl_val)

        return card

    def actualizar_tarjeta_kpi(self, card_widget, nuevo_valor):
        lbl = card_widget.findChild(QLabel, "valorKpi")
        if lbl:
            lbl.setText(str(nuevo_valor))

    def aplicar_sombra(self, widget):
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(20)
        sombra.setXOffset(0)
        sombra.setYOffset(4)
        sombra.setColor(QColor(0, 0, 0, 12))
        widget.setGraphicsEffect(sombra)

    def cargar_clientes(self):
        self.cargando_datos = True
        try:
            conexion = sqlite3.connect(BASE_DATOS)
            cursor = conexion.cursor()

            reparar_tabla_clientes(cursor)
            conexion.commit()

            cursor.execute("SELECT id, documento, nombre, telefono, direccion, saldo FROM clientes ORDER BY nombre ASC")
            clientes = cursor.fetchall()
            conexion.close()

            self.tabla.clearContents()
            self.tabla.setRowCount(len(clientes))

            total_clientes = len(clientes)
            con_deuda = 0
            al_dia = 0

            for fila, cli in enumerate(clientes):
                id_real = cli[0]
                doc_display = str(cli[1]) if cli[1] and str(cli[1]).strip() != "" else f"ID: {id_real}"
                nom = str(cli[2]) if cli[2] else "-"
                tel = str(cli[3]) if cli[3] else "-"
                dire = str(cli[4]) if cli[4] else "-"

                saldo = 0.0
                if cli[5] is not None:
                    try:
                        saldo_str = str(cli[5]).replace("$", "").strip()
                        saldo = parse_number(saldo_str) or 0.0
                    except (ValueError, TypeError):
                        saldo = 0.0

                saldo_txt = f"$ {saldo:,.2f}"

                if saldo > 0:
                    estado_txt = "⚠️ Con Deuda"
                    con_deuda += 1
                else:
                    estado_txt = "✅ Al Día"
                    al_dia += 1

                datos = [doc_display, nom, tel, dire, saldo_txt, estado_txt]

                for columna, dato in enumerate(datos):
                    item = QTableWidgetItem(dato)
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

                    if columna == 0:
                        item.setData(Qt.UserRole, id_real)
                        item.setTextAlignment(Qt.AlignCenter)
                    elif columna == 4:
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        if saldo > 0:
                            item.setForeground(QColor("#dc2626"))
                    elif columna == 5:
                        item.setTextAlignment(Qt.AlignCenter)

                    self.tabla.setItem(fila, columna, item)

            self.actualizar_tarjeta_kpi(self.card_total_clientes, total_clientes)
            self.actualizar_tarjeta_kpi(self.card_con_deuda, con_deuda)
            self.actualizar_tarjeta_kpi(self.card_al_dia, al_dia)

        except Exception as e:
            print(f"Error al cargar clientes: {e}")

        self.cargando_datos = False

    def buscar_clientes(self):
        texto = self.buscar.text().lower()

        for fila in range(self.tabla.rowCount()):
            doc = self.tabla.item(fila, 0)
            nombre = self.tabla.item(fila, 1)
            tel = self.tabla.item(fila, 2)

            coincide = False
            if nombre and texto in nombre.text().lower():
                coincide = True
            if doc and texto in doc.text().lower():
                coincide = True
            if tel and texto in tel.text().lower():
                coincide = True

            self.tabla.setRowHidden(fila, not coincide)

    def abrir_agregar(self):
        self.modal_agregar = AgregarClienteModal(self)
        self.modal_agregar.cliente_guardado.connect(self.cargar_clientes)
        self.modal_agregar.exec()

    def editar_cliente(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            msg = mostrar_mensaje(self, "Aviso", "Por favor, seleccione un cliente de la tabla para editar.", QMessageBox.Warning)
            msg.exec()
            return

        item_id = self.tabla.item(fila, 0)
        cliente_id = item_id.data(Qt.UserRole)

        self.modal_editar = EditarClienteModal(cliente_id, self)
        self.modal_editar.cliente_actualizado.connect(self.cargar_clientes)
        self.modal_editar.exec()

    def eliminar_cliente(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            msg = mostrar_mensaje(
                self, 
                "Aviso", 
                "Por favor, seleccione un cliente de la tabla para eliminar.", 
                QMessageBox.Warning
            )
            msg.exec()
            return

        item_id = self.tabla.item(fila, 0)
        if not item_id:
            return
            
        cliente_id = item_id.data(Qt.UserRole)
        nombre_item = self.tabla.item(fila, 1)
        nombre = nombre_item.text() if nombre_item else "este cliente"

        msg_confirmar = mostrar_mensaje(
            self,
            "Confirmar Eliminación",
            f"¿Estás segura de eliminar a '{nombre}'?\nEsta acción no se puede deshacer.",
            QMessageBox.Question,
            QMessageBox.Yes | QMessageBox.No
        )
        
        btn_si = msg_confirmar.button(QMessageBox.Yes)
        if btn_si:
            btn_si.setText("Sí, eliminar")
            btn_si.setStyleSheet("background-color: #ef4444; color: white;")

        btn_no = msg_confirmar.button(QMessageBox.No)
        if btn_no:
            btn_no.setText("Cancelar")
            btn_no.setStyleSheet("background-color: #cbd5e1; color: #334155;")

        if msg_confirmar.exec() == QMessageBox.Yes:
            try:
                conexion = sqlite3.connect(BASE_DATOS)
                cursor = conexion.cursor()
                cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
                conexion.commit()
                conexion.close()

                self.cargar_clientes()
                
                msg_exito = mostrar_mensaje(
                    self, 
                    "Éxito", 
                    f"El cliente '{nombre}' fue eliminado correctamente.", 
                    QMessageBox.Information
                )
                msg_exito.exec()

            except Exception as e:
                msg_err = mostrar_mensaje(
                    self, 
                    "Error", 
                    f"No se pudo eliminar el cliente:\n{e}", 
                    QMessageBox.Critical
                )
                msg_err.exec()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    v = Clientes()
    v.show()
    sys.exit(app.exec())