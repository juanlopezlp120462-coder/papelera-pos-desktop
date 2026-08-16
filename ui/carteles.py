
import sqlite3
import html
import math

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QDialog,
    QMessageBox,
    QFileDialog,
    QAbstractItemView,
    QScrollArea,
    QFrame,
    QCheckBox,
)

from PySide6.QtGui import (
    QTextDocument,
    QPixmap,
    QImage,
    QPainter,
    QFont,
    QFontMetrics,
    QColor,
    QPen,
    QBrush,
    QPolygonF,
)

from PySide6.QtPrintSupport import QPrinter
from PySide6.QtCore import Qt, QMarginsF, QPointF

from ui.db import BASE_DATOS, init_db, get_setting
from ui.printing import print_html, printer_names, show_no_printer


class Carteles(QWidget):

    A4_ANCHO_CM = 21.0
    A4_ALTO_CM = 29.7
    DPI_PREVIEW = 96

    def __init__(self):
        super().__init__()

        init_db()

        self.setWindowTitle(
            f"Carteles y Ofertas - "
            f"{get_setting('nombre_negocio', 'COTILLON')}"
        )

        self.resize(1150, 850)

        self.setStyleSheet("""
            QWidget {
                background: #f8fafc;
                color: #0f172a;
                font-family: "Segoe UI";
            }

            QGroupBox {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
                margin-top: 14px;
                padding: 16px;
                font-weight: 800;
            }

            QGroupBox::title {
                background: white;
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 8px;
                color: #0f172a;
            }

            QLineEdit,
            QComboBox,
            QSpinBox,
            QDoubleSpinBox {
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 9px;
                padding: 9px;
                min-height: 22px;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QSpinBox:focus,
            QDoubleSpinBox:focus {
                border: 2px solid #0ea5e9;
            }

            QPushButton {
                background: #0ea5e9;
                color: white;
                border: 0;
                border-radius: 9px;
                padding: 10px 16px;
                font-weight: 800;
            }

            QPushButton:hover {
                background: #0284c7;
            }

            QPushButton.secondary {
                background: #e2e8f0;
                color: #334155;
            }

            QPushButton.secondary:hover {
                background: #cbd5e1;
            }

            QListWidget {
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 5px;
            }

            QListWidget::item {
                padding: 10px;
                border-radius: 7px;
            }

            QListWidget::item:selected {
                background: #e0f2fe;
                color: #0369a1;
            }

            QLabel.muted {
                color: #64748b;
            }

            QLabel.counter {
                color: #0369a1;
                background: #e0f2fe;
                border-radius: 8px;
                padding: 6px 10px;
                font-weight: 800;
            }

            QCheckBox {
                background: white;
                padding: 5px;
                font-weight: 700;
            }
        """)

        self.rows = []

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(14)

        # ======================================================
        # CABECERA
        # ======================================================

        head = QHBoxLayout()

        title = QLabel("🏷️ Carteles y Ofertas")
        title.setStyleSheet(
            "font-size:28px;font-weight:900;"
        )

        head.addWidget(title)
        head.addStretch()

        root.addLayout(head)

        sub = QLabel(
            "Seleccioná productos y armá carteles con formas, "
            "tamaños y diseños diferentes para imprimir en A4."
        )

        sub.setProperty("class", "muted")
        root.addWidget(sub)

        # ======================================================
        # PRODUCTOS
        # ======================================================

        productos_box = QGroupBox("🛒 Productos")
        productos_layout = QVBoxLayout(productos_box)

        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText(
            "🔎 Buscar por nombre o código de barras..."
        )
        self.busqueda.setClearButtonEnabled(True)
        self.busqueda.textChanged.connect(
            self.filtrar_productos
        )

        productos_layout.addWidget(self.busqueda)

        info = QLabel(
            "Podés seleccionar varios productos. Usá Ctrl para "
            "seleccionar productos separados o Shift para seleccionar "
            "un rango."
        )

        info.setProperty("class", "muted")
        info.setWordWrap(True)

        productos_layout.addWidget(info)

        self.lista_productos = QListWidget()

        self.lista_productos.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )

        self.lista_productos.setMinimumHeight(190)

        self.lista_productos.itemSelectionChanged.connect(
            self.actualizar_seleccion
        )

        productos_layout.addWidget(
            self.lista_productos
        )

        acciones = QHBoxLayout()

        self.btn_todos = QPushButton(
            "☑ Seleccionar todos"
        )

        self.btn_todos.setProperty(
            "class",
            "secondary"
        )

        self.btn_todos.clicked.connect(
            self.seleccionar_todos
        )

        self.btn_limpiar = QPushButton(
            "✕ Limpiar selección"
        )

        self.btn_limpiar.setProperty(
            "class",
            "secondary"
        )

        self.btn_limpiar.clicked.connect(
            self.lista_productos.clearSelection
        )

        acciones.addWidget(self.btn_todos)
        acciones.addWidget(self.btn_limpiar)
        acciones.addStretch()

        self.lbl_seleccionados = QLabel(
            "0 productos seleccionados"
        )

        self.lbl_seleccionados.setProperty(
            "class",
            "counter"
        )

        acciones.addWidget(
            self.lbl_seleccionados
        )

        productos_layout.addLayout(
            acciones
        )

        root.addWidget(
            productos_box,
            1
        )

        # ======================================================
        # CONFIGURACIÓN
        # ======================================================

        config_box = QGroupBox(
            "🎨 Diseño e impresión"
        )

        config = QGridLayout(
            config_box
        )

        self.tamanos = {
            "Chico — 8 × 5 cm": (8.0, 5.0),
            "Mediano — 10 × 7 cm": (10.0, 7.0),
            "Grande — 14 × 10 cm": (14.0, 10.0),
            "1/4 de A4 — 14,85 × 10,5 cm": (
                14.85,
                10.5
            ),
            "1/2 A4 — 21 × 14,85 cm": (
                21.0,
                14.85
            ),
            "A4 completo — 29,7 × 21 cm": (
                29.7,
                21.0
            ),
        }

        self.tam = QComboBox()

        self.tam.addItems(
            list(self.tamanos.keys())
        )

        self.tam.setCurrentText(
            "Chico — 8 × 5 cm"
        )

        self.tam.currentIndexChanged.connect(
            self.actualizar_preview_automaticamente
        )

        # ======================================================
        # MUCHOS DISEÑOS REALMENTE DIFERENTES
        # ======================================================

        self.disenos = [
            "Nube",
            "Burbuja",
            "Óvalo",
            "Círculo",
            "Píldora",
            "Etiqueta",
            "Etiqueta clásica",
            "Ticket",
            "Ticket redondeado",
            "Estrella",
            "Explosión",
            "Sello",
            "Rombo",
            "Diamante",
            "Hexágono",
            "Escudo",
            "Cinta",
            "Cinta diagonal",
            "Banner",
            "Premium",
            "Boutique",
            "Fiesta",
            "Cotillón",
            "Impacto",
            "Cartel comercial",
            "Precio gigante",
            "Oferta circular",
            "Marco doble",
            "Globo",
            "Súper oferta",
        ]

        self.estilo = QComboBox()

        self.estilo.addItems(
            self.disenos
        )

        self.estilo.currentIndexChanged.connect(
            self.actualizar_preview_automaticamente
        )

        self.leyenda = QLineEdit(
            "OFERTA"
        )

        self.leyenda.setPlaceholderText(
            "Ej.: OFERTA, PROMO, LIQUIDACIÓN"
        )

        self.leyenda.textChanged.connect(
            self.actualizar_preview_automaticamente
        )

        self.extra = QLineEdit()

        self.extra.setPlaceholderText(
            'Ej.: "Hasta agotar stock"'
        )

        self.extra.textChanged.connect(
            self.actualizar_preview_automaticamente
        )

        self.texto_precio = QComboBox()

        self.texto_precio.addItems([
            "Automático",
            "Pequeño",
            "Mediano",
            "Grande",
            "Muy grande",
        ])

        self.texto_precio.currentIndexChanged.connect(
            self.actualizar_preview_automaticamente
        )

        self.cantidad = QSpinBox()

        self.cantidad.setRange(
            1,
            100
        )

        self.cantidad.setValue(1)

        self.cantidad.valueChanged.connect(
            self.actualizar_preview_automaticamente
        )

        self.distribucion = QComboBox()

        self.distribucion.addItems([
            "Máximo aprovechamiento",
            "Una por fila",
        ])

        self.distribucion.currentIndexChanged.connect(
            self.actualizar_preview_automaticamente
        )

        self.separacion = QDoubleSpinBox()

        self.separacion.setRange(
            0.0,
            2.0
        )

        self.separacion.setSingleStep(
            0.05
        )

        self.separacion.setDecimals(
            2
        )

        self.separacion.setValue(
            0.0
        )

        self.separacion.setSuffix(
            " cm"
        )

        self.separacion.setToolTip(
            "Espacio REAL entre carteles."
        )

        self.separacion.valueChanged.connect(
            self.actualizar_preview_automaticamente
        )

        self.continuar_mitad = QCheckBox(
            "Continuar desde mitad de hoja"
        )

        self.continuar_mitad.setToolTip(
            "Reserva la mitad superior de la primera hoja."
        )

        self.continuar_mitad.stateChanged.connect(
            self.actualizar_preview_automaticamente
        )

        self.mitad_posicion = QComboBox()

        self.mitad_posicion.addItems([
            "Comenzar en la mitad inferior",
            "Comenzar en la mitad superior",
        ])

        self.mitad_posicion.setEnabled(
            False
        )

        self.continuar_mitad.stateChanged.connect(
            lambda estado:
            self.mitad_posicion.setEnabled(
                bool(estado)
            )
        )

        self.mitad_posicion.currentIndexChanged.connect(
            self.actualizar_preview_automaticamente
        )

        campos = [
            (
                QLabel("Tamaño físico:"),
                self.tam,
                0, 0, 0, 1
            ),
            (
                QLabel("Diseño:"),
                self.estilo,
                0, 2, 0, 3
            ),
            (
                QLabel("Leyenda:"),
                self.leyenda,
                1, 0, 1, 1
            ),
            (
                QLabel("Texto adicional:"),
                self.extra,
                1, 2, 1, 3
            ),
            (
                QLabel("Texto del precio:"),
                self.texto_precio,
                2, 0, 2, 1
            ),
            (
                QLabel("Cantidad por producto:"),
                self.cantidad,
                2, 2, 2, 3
            ),
            (
                QLabel("Distribución:"),
                self.distribucion,
                3, 0, 3, 1
            ),
            (
                QLabel("Separación:"),
                self.separacion,
                3, 2, 3, 3
            ),
        ]

        for (
            label,
            widget,
            r1,
            c1,
            r2,
            c2
        ) in campos:

            config.addWidget(
                label,
                r1,
                c1
            )

            config.addWidget(
                widget,
                r2,
                c2
            )

        config.addWidget(
            self.continuar_mitad,
            4,
            0,
            1,
            2
        )

        config.addWidget(
            self.mitad_posicion,
            4,
            2,
            1,
            2
        )

        root.addWidget(
            config_box
        )

        # ======================================================
        # BOTONES
        # ======================================================

        botones = QHBoxLayout()

        self.btn_preview = QPushButton(
            "👁 Vista previa A4"
        )

        self.btn_preview.clicked.connect(
            self.preview
        )

        self.btn_pdf = QPushButton(
            "📄 Guardar PDF"
        )

        self.btn_pdf.setProperty(
            "class",
            "secondary"
        )

        self.btn_pdf.clicked.connect(
            self.save_pdf
        )

        self.btn_print = QPushButton(
            "🖨 Imprimir A4"
        )

        self.btn_print.clicked.connect(
            self.imprimir
        )

        botones.addWidget(
            self.btn_preview
        )

        botones.addWidget(
            self.btn_pdf
        )

        botones.addWidget(
            self.btn_print
        )

        botones.addStretch()

        root.addLayout(
            botones
        )

        self.cargar_productos()

    # ==========================================================
    # PRODUCTOS
    # ==========================================================

    def cargar_productos(self):

        try:

            conexion = sqlite3.connect(
                BASE_DATOS
            )

            self.rows = conexion.execute(
                """
                SELECT
                    id,
                    nombre,
                    precio_venta,
                    codigo_barras
                FROM productos
                ORDER BY nombre
                """
            ).fetchall()

            conexion.close()

            self.recargar_lista()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudieron cargar los productos.\n\n{e}"
            )

    def recargar_lista(self):

        texto = (
            self.busqueda.text()
            .strip()
            .lower()
        )

        seleccionados = set(
            self.obtener_ids_seleccionados()
        )

        self.lista_productos.blockSignals(
            True
        )

        self.lista_productos.clear()

        for row in self.rows:

            producto_id = row[0]

            nombre = str(
                row[1] or ""
            )

            precio = float(
                row[2] or 0
            )

            codigo = str(
                row[3] or ""
            )

            if texto and not (
                texto in nombre.lower()
                or texto in codigo.lower()
            ):
                continue

            item = QListWidgetItem()

            item.setData(
                Qt.UserRole,
                producto_id
            )

            texto_item = (
                f"{nombre}    —    "
                f"$ {precio:,.2f}"
            )

            if codigo:
                texto_item += (
                    f"    |    Código: {codigo}"
                )

            item.setText(
                texto_item
            )

            self.lista_productos.addItem(
                item
            )

            if producto_id in seleccionados:
                item.setSelected(
                    True
                )

        self.lista_productos.blockSignals(
            False
        )

        self.actualizar_seleccion()

    def filtrar_productos(
        self,
        texto
    ):
        self.recargar_lista()

    def obtener_ids_seleccionados(self):

        return [
            item.data(Qt.UserRole)
            for item in
            self.lista_productos.selectedItems()
        ]

    def obtener_productos_seleccionados(self):

        ids = set(
            self.obtener_ids_seleccionados()
        )

        return [
            row
            for row in self.rows
            if row[0] in ids
        ]

    def actualizar_seleccion(self):

        cantidad = len(
            self.lista_productos.selectedItems()
        )

        self.lbl_seleccionados.setText(
            "1 producto seleccionado"
            if cantidad == 1
            else f"{cantidad} productos seleccionados"
        )

    def seleccionar_todos(self):

        self.lista_productos.selectAll()

    # ==========================================================
    # TAMAÑO
    # ==========================================================

    def obtener_tamano(self):

        return self.tamanos.get(
            self.tam.currentText(),
            (8.0, 5.0)
        )

    def precio_font_size(self):

        modo = (
            self.texto_precio.currentText()
        )

        ancho, alto = (
            self.obtener_tamano()
        )

        if modo == "Pequeño":
            return 22

        if modo == "Mediano":
            return 30

        if modo == "Grande":
            return 40

        if modo == "Muy grande":
            return 52

        if ancho <= 8:
            return 21

        if ancho <= 10:
            return 27

        if ancho <= 14:
            return 36

        return 46

    # ==========================================================
    # PALETAS
    # ==========================================================

    def colores_estilo(self):

        nombre = (
            self.estilo.currentText()
        )

        paletas = {

            "Nube": (
                "#e0f2fe",
                "#0284c7",
                "#0369a1",
                "#0f172a"
            ),

            "Burbuja": (
                "#ecfeff",
                "#06b6d4",
                "#0e7490",
                "#164e63"
            ),

            "Óvalo": (
                "#eff6ff",
                "#2563eb",
                "#1d4ed8",
                "#111827"
            ),

            "Círculo": (
                "#f5f3ff",
                "#7c3aed",
                "#5b21b6",
                "#1e1b4b"
            ),

            "Píldora": (
                "#f0fdf4",
                "#16a34a",
                "#15803d",
                "#14532d"
            ),

            "Etiqueta": (
                "#fdf4ff",
                "#a855f7",
                "#7e22ce",
                "#1f2937"
            ),

            "Etiqueta clásica": (
                "#fffbeb",
                "#92400e",
                "#78350f",
                "#1c1917"
            ),

            "Ticket": (
                "#fff7ed",
                "#ea580c",
                "#c2410c",
                "#111827"
            ),

            "Ticket redondeado": (
                "#fff1f2",
                "#e11d48",
                "#be123c",
                "#3f172a"
            ),

            "Estrella": (
                "#fff7ed",
                "#f59e0b",
                "#c2410c",
                "#111827"
            ),

            "Explosión": (
                "#fef2f2",
                "#ef4444",
                "#b91c1c",
                "#111827"
            ),

            "Sello": (
                "#fefce8",
                "#ca8a04",
                "#a16207",
                "#422006"
            ),

            "Rombo": (
                "#f0f9ff",
                "#0891b2",
                "#0e7490",
                "#164e63"
            ),

            "Diamante": (
                "#faf5ff",
                "#8b5cf6",
                "#6d28d9",
                "#2e1065"
            ),

            "Hexágono": (
                "#f0fdf4",
                "#22c55e",
                "#15803d",
                "#14532d"
            ),

            "Escudo": (
                "#eff6ff",
                "#3b82f6",
                "#1d4ed8",
                "#172554"
            ),

            "Cinta": (
                "#fef2f2",
                "#dc2626",
                "#991b1b",
                "#450a0a"
            ),

            "Cinta diagonal": (
                "#eff6ff",
                "#2563eb",
                "#1d4ed8",
                "#111827"
            ),

            "Banner": (
                "#fff7ed",
                "#f97316",
                "#ea580c",
                "#431407"
            ),

            "Premium": (
                "#faf5ff",
                "#7c3aed",
                "#5b21b6",
                "#1e1b4b"
            ),

            "Boutique": (
                "#fff1f2",
                "#e11d48",
                "#be123c",
                "#3f172a"
            ),

            "Fiesta": (
                "#f0fdf4",
                "#16a34a",
                "#15803d",
                "#14532d"
            ),

            "Cotillón": (
                "#fdf2f8",
                "#db2777",
                "#be185d",
                "#500724"
            ),

            "Impacto": (
                "#fff7ed",
                "#ea580c",
                "#c2410c",
                "#111827"
            ),

            "Cartel comercial": (
                "#f8fafc",
                "#334155",
                "#0f172a",
                "#0f172a"
            ),

            "Precio gigante": (
                "#fef2f2",
                "#dc2626",
                "#991b1b",
                "#111827"
            ),

            "Oferta circular": (
                "#ecfdf5",
                "#10b981",
                "#047857",
                "#064e3b"
            ),

            "Marco doble": (
                "#fffbeb",
                "#d97706",
                "#92400e",
                "#451a03"
            ),

            "Globo": (
                "#fdf4ff",
                "#c026d3",
                "#a21caf",
                "#4a044e"
            ),

            "Súper oferta": (
                "#fef2f2",
                "#dc2626",
                "#991b1b",
                "#450a0a"
            ),
        }

        fondo, borde, acento, texto = paletas.get(
            nombre,
            paletas["Nube"]
        )

        return {
            "fondo": fondo,
            "borde": borde,
            "acento": acento,
            "texto": texto,
        }

    # ==========================================================
    # FORMA HTML
    # ==========================================================

    def html_forma(self):

        estilo = self.estilo.currentText()

        colores = self.colores_estilo()

        borde = colores["borde"]
        fondo = colores["fondo"]

        # ======================================================
        # FORMAS REALMENTE DIFERENTES
        # ======================================================

        if estilo == "Nube":

            return f"""
            border:0.07cm solid {borde};
            border-radius:
                45% 55% 38% 62%
                / 55% 40% 60% 45%;
            background:{fondo};
            """

        if estilo == "Burbuja":

            return f"""
            border:0.07cm solid {borde};
            border-radius:45%;
            background:{fondo};
            """

        if estilo == "Óvalo":

            return f"""
            border:0.08cm solid {borde};
            border-radius:50%;
            background:{fondo};
            """

        if estilo == "Círculo":

            return f"""
            border:0.10cm solid {borde};
            border-radius:50%;
            background:{fondo};
            """

        if estilo == "Píldora":

            return f"""
            border:0.07cm solid {borde};
            border-radius:999px;
            background:{fondo};
            """

        if estilo == "Etiqueta":

            return f"""
            border:0.07cm solid {borde};
            border-radius:0.15cm;
            background:{fondo};
            """

        if estilo == "Etiqueta clásica":

            return f"""
            border:0.10cm double {borde};
            border-radius:0.20cm;
            background:{fondo};
            """

        if estilo == "Ticket":

            return f"""
            border:0.07cm dashed {borde};
            border-radius:0.12cm;
            background:{fondo};
            """

        if estilo == "Ticket redondeado":

            return f"""
            border:0.07cm dashed {borde};
            border-radius:0.45cm;
            background:{fondo};
            """

        if estilo == "Estrella":

            return f"""
            border:0.08cm solid {borde};
            border-radius:0.10cm;
            background:{fondo};
            """

        if estilo == "Explosión":

            return f"""
            border:0.10cm solid {borde};
            border-radius:0.04cm;
            background:{fondo};
            """

        if estilo == "Sello":

            return f"""
            border:0.10cm dashed {borde};
            border-radius:0.22cm;
            background:{fondo};
            """

        if estilo == "Rombo":

            return f"""
            border:0.08cm solid {borde};
            transform:rotate(0deg);
            border-radius:0.20cm;
            background:{fondo};
            """

        if estilo == "Diamante":

            return f"""
            border:0.10cm solid {borde};
            border-radius:0.10cm;
            background:{fondo};
            """

        if estilo == "Hexágono":

            return f"""
            border:0.08cm solid {borde};
            border-radius:0.18cm;
            background:{fondo};
            """

        if estilo == "Escudo":

            return f"""
            border:0.10cm solid {borde};
            border-radius:
                0.25cm 0.25cm 0.80cm 0.80cm;
            background:{fondo};
            """

        if estilo == "Cinta":

            return f"""
            border:0.08cm solid {borde};
            border-radius:0.05cm;
            background:{fondo};
            """

        if estilo == "Cinta diagonal":

            return f"""
            border:0.06cm solid {borde};
            border-radius:0.10cm;
            background:{fondo};
            """

        if estilo == "Banner":

            return f"""
            border:0.08cm solid {borde};
            border-radius:0.10cm;
            background:{fondo};
            """

        if estilo == "Premium":

            return f"""
            border:0.11cm double {borde};
            border-radius:0.25cm;
            background:{fondo};
            """

        if estilo == "Boutique":

            return f"""
            border:0.06cm solid {borde};
            border-radius:
                0.55cm 0.10cm
                0.55cm 0.10cm;
            background:{fondo};
            """

        if estilo == "Fiesta":

            return f"""
            border:0.06cm solid {borde};
            border-radius:0.30cm;
            background:{fondo};
            """

        if estilo == "Cotillón":

            return f"""
            border:0.08cm solid {borde};
            border-radius:0.38cm;
            background:{fondo};
            """

        if estilo == "Impacto":

            return f"""
            border:0.12cm solid {borde};
            border-radius:0.02cm;
            background:{fondo};
            """

        if estilo == "Cartel comercial":

            return f"""
            border:0.11cm solid {borde};
            border-radius:0;
            background:{fondo};
            """

        if estilo == "Precio gigante":

            return f"""
            border:0.12cm solid {borde};
            border-radius:0.18cm;
            background:{fondo};
            """

        if estilo == "Oferta circular":

            return f"""
            border:0.09cm solid {borde};
            border-radius:50%;
            background:{fondo};
            """

        if estilo == "Marco doble":

            return f"""
            border:0.12cm double {borde};
            border-radius:0.15cm;
            background:{fondo};
            """

        if estilo == "Globo":

            return f"""
            border:0.08cm solid {borde};
            border-radius:
                50% 50% 45% 45%;
            background:{fondo};
            """

        if estilo == "Súper oferta":

            return f"""
            border:0.14cm solid {borde};
            border-radius:0.10cm;
            background:{fondo};
            """

        return f"""
        border:0.07cm solid {borde};
        border-radius:0.15cm;
        background:{fondo};
        """

    # ==========================================================
    # HTML CARTEL
    # ==========================================================

    def html_cartel(self, producto):

        nombre = html.escape(
            str(producto[1] or "")
        )

        precio = float(
            producto[2] or 0
        )

        codigo = html.escape(
            str(producto[3] or "")
        )

        leyenda = html.escape(
            self.leyenda.text().strip()
            or "OFERTA"
        )

        extra = html.escape(
            self.extra.text().strip()
        )

        ancho_cm, alto_cm = (
            self.obtener_tamano()
        )

        colores = self.colores_estilo()

        precio_size = (
            self.precio_font_size()
        )

        if ancho_cm <= 8:

            nombre_size = 11
            leyenda_size = 9
            extra_size = 6
            negocio_size = 5

        elif ancho_cm <= 10:

            nombre_size = 14
            leyenda_size = 12
            extra_size = 7
            negocio_size = 6

        elif ancho_cm <= 14:

            nombre_size = 19
            leyenda_size = 16
            extra_size = 9
            negocio_size = 8

        else:

            nombre_size = 26
            leyenda_size = 21
            extra_size = 11
            negocio_size = 9

        negocio = html.escape(
            str(
                get_setting(
                    "nombre_negocio",
                    "COTILLON"
                )
            )
        )

        extra_html = ""

        if extra:

            extra_html = f"""
            <div style="
                font-size:{extra_size}pt;
                color:#475569;
                margin-top:0.04cm;
                font-weight:600;
                line-height:1;
            ">
                {extra}
            </div>
            """

        codigo_html = ""

        if codigo:

            codigo_html = f"""
            <div style="
                font-size:{max(5, extra_size - 1)}pt;
                color:#64748b;
                margin-top:0.03cm;
                line-height:1;
            ">
                Código: {codigo}
            </div>
            """

        base = f"""
        width:{ancho_cm}cm;
        height:{alto_cm}cm;
        box-sizing:border-box;
        text-align:center;
        font-family:Arial;
        color:{colores['texto']};
        overflow:hidden;
        padding:0.25cm;
        position:relative;
        """

        forma = self.html_forma()

        estilo = self.estilo.currentText()

        # ======================================================
        # DECORACIONES
        # ======================================================

        decoracion = ""

        if estilo == "Nube":

            decoracion = f"""
            <div style="
                position:absolute;
                width:0.45cm;
                height:0.45cm;
                border-radius:50%;
                background:{colores['borde']};
                top:0.12cm;
                left:0.25cm;
            "></div>
            """

        elif estilo == "Burbuja":

            decoracion = f"""
            <div style="
                position:absolute;
                width:0.35cm;
                height:0.35cm;
                border-radius:50%;
                background:{colores['acento']};
                right:0.30cm;
                bottom:0.25cm;
            "></div>
            """

        elif estilo in (
            "Estrella",
            "Explosión",
            "Fiesta",
            "Cotillón",
        ):

            decoracion = f"""
            <div style="
                position:absolute;
                left:0.18cm;
                top:0.12cm;
                color:{colores['borde']};
                font-size:16pt;
                font-weight:900;
            ">
                ✦
            </div>

            <div style="
                position:absolute;
                right:0.18cm;
                bottom:0.12cm;
                color:{colores['acento']};
                font-size:16pt;
                font-weight:900;
            ">
                ✦
            </div>
            """

        elif estilo == "Cinta":

            decoracion = f"""
            <div style="
                position:absolute;
                left:-0.15cm;
                right:-0.15cm;
                top:0.15cm;
                height:0.48cm;
                background:{colores['borde']};
                color:white;
                font-weight:900;
                font-size:8pt;
                line-height:0.48cm;
            ">
                PROMO
            </div>
            """

        elif estilo == "Cinta diagonal":

            decoracion = f"""
            <div style="
                position:absolute;
                right:-0.65cm;
                top:0.35cm;
                width:2.5cm;
                background:{colores['borde']};
                color:white;
                font-weight:900;
                font-size:7pt;
                padding:0.07cm;
                transform:rotate(35deg);
            ">
                OFERTA
            </div>
            """

        elif estilo == "Banner":

            decoracion = f"""
            <div style="
                position:absolute;
                left:0.20cm;
                right:0.20cm;
                top:0.12cm;
                height:0.35cm;
                background:{colores['borde']};
                color:white;
                font-size:7pt;
                font-weight:900;
                line-height:0.35cm;
            ">
                ★ PROMOCIÓN ★
            </div>
            """

        elif estilo == "Sello":

            decoracion = f"""
            <div style="
                position:absolute;
                right:0.20cm;
                top:0.18cm;
                width:0.90cm;
                height:0.90cm;
                border:0.05cm solid {colores['borde']};
                border-radius:50%;
                color:{colores['borde']};
                font-size:5pt;
                font-weight:900;
                line-height:0.90cm;
            ">
                OFERTA
            </div>
            """

        elif estilo == "Oferta circular":

            decoracion = f"""
            <div style="
                position:absolute;
                right:0.25cm;
                top:0.20cm;
                width:1.05cm;
                height:1.05cm;
                border-radius:50%;
                background:{colores['borde']};
                color:white;
                font-size:6pt;
                font-weight:900;
                display:block;
                padding-top:0.28cm;
                box-sizing:border-box;
            ">
                OFERTA
            </div>
            """

        elif estilo == "Precio gigante":

            decoracion = f"""
            <div style="
                position:absolute;
                left:0;
                right:0;
                top:0;
                height:0.18cm;
                background:{colores['borde']};
            "></div>
            """

        elif estilo == "Cartel comercial":

            decoracion = f"""
            <div style="
                position:absolute;
                left:0;
                top:0;
                width:100%;
                height:0.15cm;
                background:{colores['borde']};
            "></div>

            <div style="
                position:absolute;
                left:0;
                bottom:0;
                width:100%;
                height:0.15cm;
                background:{colores['acento']};
            "></div>
            """

        elif estilo == "Súper oferta":

            decoracion = f"""
            <div style="
                position:absolute;
                left:0;
                right:0;
                top:0;
                background:{colores['borde']};
                color:white;
                font-size:9pt;
                font-weight:900;
                padding:0.08cm;
            ">
                🔥 SÚPER OFERTA 🔥
            </div>
            """

        elif estilo == "Globo":

            decoracion = f"""
            <div style="
                position:absolute;
                left:50%;
                bottom:-0.30cm;
                width:0;
                height:0;
                border-left:0.25cm solid transparent;
                border-right:0.25cm solid transparent;
                border-top:0.45cm solid {colores['borde']};
                transform:translateX(-50%);
            "></div>
            """

        elif estilo == "Premium":

            decoracion = f"""
            <div style="
                position:absolute;
                left:0.25cm;
                right:0.25cm;
                top:0.25cm;
                bottom:0.25cm;
                border:0.025cm solid {colores['borde']};
                border-radius:0.15cm;
            "></div>
            """

        # ======================================================
        # CARTEL
        # ======================================================

        return f"""
        <div style="
            {base}
            {forma}
        ">

            {decoracion}

            <div style="
                background:{colores['borde']};
                color:white;
                border-radius:0.10cm;
                padding:0.07cm 0.14cm;
                font-size:{leyenda_size}pt;
                font-weight:900;
                margin-bottom:0.08cm;
                line-height:1;
            ">
                {leyenda}
            </div>

            <div style="
                font-size:{nombre_size}pt;
                font-weight:900;
                color:{colores['acento']};
                line-height:1;
                margin:0.04cm 0;
            ">
                {nombre}
            </div>

            <div style="
                font-size:{precio_size}pt;
                font-weight:900;
                color:#111827;
                line-height:0.95;
                margin:0.07cm 0;
                white-space:nowrap;
            ">
                $ {precio:,.2f}
            </div>

            {extra_html}

            <div style="
                font-size:{negocio_size}pt;
                font-weight:800;
                margin-top:0.05cm;
                color:#334155;
                line-height:1;
            ">
                {negocio}
            </div>

            {codigo_html}

        </div>
        """

    # ==========================================================
    # CARTELES
    # ==========================================================

    def obtener_carteles(self):

        productos = (
            self.obtener_productos_seleccionados()
        )

        if not productos:
            return []

        cantidad = (
            self.cantidad.value()
        )

        carteles = []

        for producto in productos:

            for _ in range(cantidad):

                carteles.append({
                    "producto": producto,
                    "html": self.html_cartel(
                        producto
                    ),
                })

        return carteles

    # ==========================================================
    # DISTRIBUCIÓN A4
    # ==========================================================

    def calcular_distribucion(self):

        ancho, alto = (
            self.obtener_tamano()
        )

        margen = 0.20

        separacion = (
            self.separacion.value()
        )

        usable_ancho = (
            self.A4_ANCHO_CM
            - margen * 2
        )

        usable_alto = (
            self.A4_ALTO_CM
            - margen * 2
        )

        if (
            self.distribucion.currentText()
            == "Una por fila"
        ):

            columnas = 1

        else:

            columnas = int(
                (
                    usable_ancho
                    + separacion
                )
                //
                (
                    ancho
                    + separacion
                )
            )

        filas = int(
            (
                usable_alto
                + separacion
            )
            //
            (
                alto
                + separacion
            )
        )

        columnas = max(
            1,
            columnas
        )

        filas = max(
            1,
            filas
        )

        if self.continuar_mitad.isChecked():

            mitad = (
                self.A4_ALTO_CM
                / 2.0
            )

            alto_disponible = (
                mitad - margen
            )

            filas_mitad = int(
                (
                    alto_disponible
                    + separacion
                )
                //
                (
                    alto
                    + separacion
                )
            )

            filas_mitad = max(
                1,
                filas_mitad
            )

            por_hoja_mitad = (
                columnas
                * filas_mitad
            )

            return {
                "cartel_ancho": ancho,
                "cartel_alto": alto,
                "margen": margen,
                "separacion": separacion,
                "columnas": columnas,
                "filas": filas,
                "por_hoja":
                    columnas * filas,
                "filas_mitad":
                    filas_mitad,
                "por_hoja_mitad":
                    por_hoja_mitad,
            }

        return {
            "cartel_ancho": ancho,
            "cartel_alto": alto,
            "margen": margen,
            "separacion": separacion,
            "columnas": columnas,
            "filas": filas,
            "por_hoja":
                columnas * filas,
            "filas_mitad": filas,
            "por_hoja_mitad":
                columnas * filas,
        }

    # ==========================================================
    # HTML A4
    # ==========================================================

    def html_a4(self):

        carteles = (
            self.obtener_carteles()
        )

        if not carteles:

            return """
            <html>
            <body>
                <h2>No hay productos seleccionados.</h2>
            </body>
            </html>
            """

        d = (
            self.calcular_distribucion()
        )

        ancho = d["cartel_ancho"]
        alto = d["cartel_alto"]
        margen = d["margen"]
        separacion = d["separacion"]
        columnas = d["columnas"]

        primera_capacidad = (
            d["por_hoja_mitad"]
            if self.continuar_mitad.isChecked()
            else d["por_hoja"]
        )

        if self.continuar_mitad.isChecked():

            resto = max(
                0,
                len(carteles)
                - primera_capacidad
            )

            paginas = (
                1
                + (
                    math.ceil(
                        resto
                        / d["por_hoja"]
                    )
                    if resto
                    else 0
                )
            )

        else:

            paginas = math.ceil(
                len(carteles)
                / d["por_hoja"]
            )

        paginas_html = []

        indice = 0

        for numero_pagina in range(
            paginas
        ):

            es_primera = (
                numero_pagina == 0
            )

            if (
                es_primera
                and self.continuar_mitad.isChecked()
            ):

                capacidad = (
                    d["por_hoja_mitad"]
                )

                if (
                    self.mitad_posicion.currentIndex()
                    == 0
                ):

                    top_reservado = (
                        self.A4_ALTO_CM
                        / 2.0
                    )

                else:

                    top_reservado = 0.0

            else:

                capacidad = (
                    d["por_hoja"]
                )

                top_reservado = 0.0

            filas_pagina = max(
                1,
                math.ceil(
                    capacidad
                    / columnas
                )
            )

            filas_html = []

            if top_reservado > 0:

                filas_html.append(
                    f"""
                    <tr>
                        <td
                            colspan="{columnas}"
                            style="
                                height:
                                    {top_reservado}cm;
                                padding:0;
                            "
                        ></td>
                    </tr>
                    """
                )

            for fila in range(
                filas_pagina
            ):

                celdas = []

                for columna in range(
                    columnas
                ):

                    if (
                        indice
                        < len(carteles)
                    ):

                        cartel = (
                            carteles[indice]
                            ["html"]
                        )

                        indice += 1

                        contenido = f"""
                        <div style="
                            width:{ancho}cm;
                            height:{alto}cm;
                            overflow:hidden;
                            margin:0;
                            padding:0;
                        ">
                            {cartel}
                        </div>
                        """

                    else:

                        contenido = ""

                    celdas.append(
                        f"""
                        <td style="
                            width:{ancho}cm;
                            height:{alto}cm;
                            padding:
                                0
                                {separacion / 2}cm;
                            vertical-align:top;
                        ">
                            {contenido}
                        </td>
                        """
                    )

                filas_html.append(
                    "<tr>"
                    + "".join(celdas)
                    + "</tr>"
                )

            pagina = f"""
            <div style="
                width:21cm;
                height:29.7cm;
                box-sizing:border-box;
                background:white;
                padding:{margen}cm;
                margin:0;
                page-break-after:always;
                overflow:hidden;
            ">

                <table
                    cellspacing="0"
                    cellpadding="0"
                    style="
                        border-collapse:
                            separate;
                        border-spacing:
                            0 {separacion}cm;
                        margin:0;
                        padding:0;
                    "
                >

                    {''.join(filas_html)}

                </table>

            </div>
            """

            paginas_html.append(
                pagina
            )

        return f"""
        <html>

        <head>

            <meta charset="utf-8">

            <style>

                @page {{
                    size:A4 portrait;
                    margin:0;
                }}

                html,
                body {{
                    margin:0;
                    padding:0;
                    background:white;
                }}

                table {{
                    border-collapse:separate;
                }}

                td {{
                    padding:0;
                    margin:0;
                }}

            </style>

        </head>

        <body>

            {''.join(paginas_html)}

        </body>

        </html>
        """

    # ==========================================================
    # UTILIDADES DE PREVIEW
    # ==========================================================

    def px_cm(
        self,
        cm,
        escala
    ):

        return max(
            1,
            int(
                cm
                * self.DPI_PREVIEW
                / 2.54
                * escala
            )
        )

    def font_px(
        self,
        pt,
        escala
    ):

        return max(
            5,
            int(
                pt
                * self.DPI_PREVIEW
                / 72
                * escala
            )
        )

    # ==========================================================
    # DIBUJAR FORMAS
    # ==========================================================

    def dibujar_forma_exterior(
        self,
        painter,
        rect,
        estilo,
        borde,
        fondo,
        px
    ):

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QBrush(fondo)
        )

        # ------------------------------------------------------
        # NUBE
        # ------------------------------------------------------

        if estilo == "Nube":

            painter.drawRoundedRect(
                rect,
                px(0.45),
                px(0.45)
            )

        # ------------------------------------------------------
        # BURBUJA
        # ------------------------------------------------------

        elif estilo == "Burbuja":

            painter.drawEllipse(
                rect
            )

        # ------------------------------------------------------
        # ÓVALO
        # ------------------------------------------------------

        elif estilo == "Óvalo":

            painter.drawEllipse(
                rect
            )

        # ------------------------------------------------------
        # CÍRCULO
        # ------------------------------------------------------

        elif estilo == "Círculo":

            lado = min(
                rect.width(),
                rect.height()
            )

            r = QRect = rect

            x = (
                rect.center().x()
                - lado // 2
            )

            y = (
                rect.center().y()
                - lado // 2
            )

            painter.drawEllipse(
                x,
                y,
                lado,
                lado
            )

        # ------------------------------------------------------
        # PÍLDORA
        # ------------------------------------------------------

        elif estilo == "Píldora":

            painter.drawRoundedRect(
                rect,
                rect.height() / 2,
                rect.height() / 2
            )

        # ------------------------------------------------------
        # ESCUDO
        # ------------------------------------------------------

        elif estilo == "Escudo":

            puntos = [
                QPointF(
                    rect.left(),
                    rect.top()
                    + rect.height() * 0.12
                ),

                QPointF(
                    rect.center().x(),
                    rect.top()
                ),

                QPointF(
                    rect.right(),
                    rect.top()
                    + rect.height() * 0.12
                ),

                QPointF(
                    rect.right()
                    - rect.width() * 0.03,
                    rect.bottom()
                    - rect.height() * 0.25
                ),

                QPointF(
                    rect.center().x(),
                    rect.bottom()
                ),

                QPointF(
                    rect.left()
                    + rect.width() * 0.03,
                    rect.bottom()
                    - rect.height() * 0.25
                ),
            ]

            painter.drawPolygon(
                QPolygonF(puntos)
            )

        # ------------------------------------------------------
        # ROMBO / DIAMANTE
        # ------------------------------------------------------

        elif estilo in (
            "Rombo",
            "Diamante",
        ):

            puntos = [
                QPointF(
                    rect.center().x(),
                    rect.top()
                ),

                QPointF(
                    rect.right(),
                    rect.center().y()
                ),

                QPointF(
                    rect.center().x(),
                    rect.bottom()
                ),

                QPointF(
                    rect.left(),
                    rect.center().y()
                ),
            ]

            painter.drawPolygon(
                QPolygonF(puntos)
            )

        # ------------------------------------------------------
        # HEXÁGONO
        # ------------------------------------------------------

        elif estilo == "Hexágono":

            puntos = [
                QPointF(
                    rect.left()
                    + rect.width() * 0.18,
                    rect.top()
                ),

                QPointF(
                    rect.right()
                    - rect.width() * 0.18,
                    rect.top()
                ),

                QPointF(
                    rect.right(),
                    rect.center().y()
                ),

                QPointF(
                    rect.right()
                    - rect.width() * 0.18,
                    rect.bottom()
                ),

                QPointF(
                    rect.left()
                    + rect.width() * 0.18,
                    rect.bottom()
                ),

                QPointF(
                    rect.left(),
                    rect.center().y()
                ),
            ]

            painter.drawPolygon(
                QPolygonF(puntos)
            )

        # ------------------------------------------------------
        # ESTRELLA
        # ------------------------------------------------------

        elif estilo == "Estrella":

            puntos = []

            cx = rect.center().x()
            cy = rect.center().y()

            radio_exterior = (
                min(
                    rect.width(),
                    rect.height()
                ) * 0.50
            )

            radio_interior = (
                radio_exterior * 0.48
            )

            for i in range(20):

                angulo = (
                    -math.pi / 2
                    + i * math.pi / 10
                )

                radio = (
                    radio_exterior
                    if i % 2 == 0
                    else radio_interior
                )

                puntos.append(
                    QPointF(
                        cx
                        + math.cos(angulo)
                        * radio,

                        cy
                        + math.sin(angulo)
                        * radio
                    )
                )

            painter.drawPolygon(
                QPolygonF(puntos)
            )

        # ------------------------------------------------------
        # EXPLOSIÓN
        # ------------------------------------------------------

        elif estilo == "Explosión":

            puntos = []

            cx = rect.center().x()
            cy = rect.center().y()

            exterior = (
                min(
                    rect.width(),
                    rect.height()
                ) * 0.52
            )

            interior = (
                exterior * 0.72
            )

            for i in range(32):

                angulo = (
                    -math.pi / 2
                    + i * math.pi / 16
                )

                radio = (
                    exterior
                    if i % 2 == 0
                    else interior
                )

                puntos.append(
                    QPointF(
                        cx
                        + math.cos(angulo)
                        * radio,

                        cy
                        + math.sin(angulo)
                        * radio
                    )
                )

            painter.drawPolygon(
                QPolygonF(puntos)
            )

        # ------------------------------------------------------
        # TICKET
        # ------------------------------------------------------

        elif estilo in (
            "Ticket",
            "Ticket redondeado",
        ):

            radius = (
                rect.height() * 0.10
                if estilo == "Ticket"
                else rect.height() * 0.25
            )

            painter.drawRoundedRect(
                rect,
                radius,
                radius
            )

        # ------------------------------------------------------
        # GLOBO
        # ------------------------------------------------------

        elif estilo == "Globo":

            cuerpo = rect.adjusted(
                px(0.05),
                px(0.05),
                -px(0.05),
                -px(0.35)
            )

            painter.drawEllipse(
                cuerpo
            )

            puntos = [
                QPointF(
                    rect.center().x()
                    - px(0.20),
                    cuerpo.bottom()
                ),

                QPointF(
                    rect.center().x()
                    + px(0.20),
                    cuerpo.bottom()
                ),

                QPointF(
                    rect.center().x(),
                    rect.bottom()
                ),
            ]

            painter.drawPolygon(
                QPolygonF(puntos)
            )

        # ------------------------------------------------------
        # RESTO
        # ------------------------------------------------------

        else:

            radius = (
                px(0.20)
            )

            painter.drawRoundedRect(
                rect,
                radius,
                radius
            )

        # ======================================================
        # BORDE
        # ======================================================

        pen = QPen(
            borde,
            max(
                2,
                px(0.07)
            )
        )

        if estilo in (
            "Sello",
            "Ticket",
            "Ticket redondeado",
        ):

            pen.setStyle(
                Qt.DashLine
            )

        elif estilo in (
            "Premium",
            "Marco doble",
        ):

            pen.setStyle(
                Qt.DoubleLine
            )

            pen.setWidth(
                max(
                    2,
                    px(0.08)
                )
            )

        elif estilo == "Impacto":

            pen.setWidth(
                max(
                    3,
                    px(0.12)
                )
            )

        painter.setPen(
            pen
        )

        painter.setBrush(
            Qt.NoBrush
        )

        # Reutilizamos geometrías principales
        # para el borde.

        if estilo in (
            "Burbuja",
            "Óvalo",
        ):

            painter.drawEllipse(
                rect
            )

        elif estilo == "Círculo":

            lado = min(
                rect.width(),
                rect.height()
            )

            painter.drawEllipse(
                rect.center().x()
                - lado // 2,

                rect.center().y()
                - lado // 2,

                lado,
                lado
            )

        elif estilo == "Píldora":

            painter.drawRoundedRect(
                rect,
                rect.height() / 2,
                rect.height() / 2
            )

        elif estilo in (
            "Escudo",
            "Rombo",
            "Diamante",
            "Hexágono",
            "Estrella",
            "Explosión",
        ):

            # Para estas formas se vuelve a crear
            # la misma geometría usando el fondo
            # transparente.

            painter.setBrush(
                Qt.NoBrush
            )

            if estilo == "Escudo":

                puntos = [
                    QPointF(
                        rect.left(),
                        rect.top()
                        + rect.height() * 0.12
                    ),
                    QPointF(
                        rect.center().x(),
                        rect.top()
                    ),
                    QPointF(
                        rect.right(),
                        rect.top()
                        + rect.height() * 0.12
                    ),
                    QPointF(
                        rect.right()
                        - rect.width() * 0.03,
                        rect.bottom()
                        - rect.height() * 0.25
                    ),
                    QPointF(
                        rect.center().x(),
                        rect.bottom()
                    ),
                    QPointF(
                        rect.left()
                        + rect.width() * 0.03,
                        rect.bottom()
                        - rect.height() * 0.25
                    ),
                ]

            elif estilo in (
                "Rombo",
                "Diamante",
            ):

                puntos = [
                    QPointF(
                        rect.center().x(),
                        rect.top()
                    ),
                    QPointF(
                        rect.right(),
                        rect.center().y()
                    ),
                    QPointF(
                        rect.center().x(),
                        rect.bottom()
                    ),
                    QPointF(
                        rect.left(),
                        rect.center().y()
                    ),
                ]

            elif estilo == "Hexágono":

                puntos = [
                    QPointF(
                        rect.left()
                        + rect.width() * 0.18,
                        rect.top()
                    ),
                    QPointF(
                        rect.right()
                        - rect.width() * 0.18,
                        rect.top()
                    ),
                    QPointF(
                        rect.right(),
                        rect.center().y()
                    ),
                    QPointF(
                        rect.right()
                        - rect.width() * 0.18,
                        rect.bottom()
                    ),
                    QPointF(
                        rect.left()
                        + rect.width() * 0.18,
                        rect.bottom()
                    ),
                    QPointF(
                        rect.left(),
                        rect.center().y()
                    ),
                ]

            else:

                puntos = []

                cx = rect.center().x()
                cy = rect.center().y()

                exterior = (
                    min(
                        rect.width(),
                        rect.height()
                    ) * 0.50
                )

                interior = (
                    exterior * 0.48
                )

                if estilo == "Explosión":
                    exterior *= 1.0
                    interior = exterior * 0.72

                cantidad = (
                    20
                    if estilo == "Estrella"
                    else 32
                )

                for i in range(cantidad):

                    angulo = (
                        -math.pi / 2
                        + i * math.pi
                        / (
                            cantidad / 2
                        )
                    )

                    radio = (
                        exterior
                        if i % 2 == 0
                        else interior
                    )

                    puntos.append(
                        QPointF(
                            cx
                            + math.cos(angulo)
                            * radio,

                            cy
                            + math.sin(angulo)
                            * radio
                        )
                    )

            painter.drawPolygon(
                QPolygonF(puntos)
            )

        elif estilo == "Globo":

            cuerpo = rect.adjusted(
                px(0.05),
                px(0.05),
                -px(0.05),
                -px(0.35)
            )

            painter.drawEllipse(
                cuerpo
            )

        else:

            radius = (
                rect.height() * 0.10
            )

            if estilo in (
                "Nube",
                "Burbuja",
                "Boutique",
                "Cotillón",
            ):

                radius = (
                    rect.height()
                    * 0.30
                )

            elif estilo == "Premium":
                radius = px(0.20)

            elif estilo == "Marco doble":
                radius = px(0.15)

            painter.drawRoundedRect(
                rect,
                radius,
                radius
            )

    # ==========================================================
    # PREVIEW DEL CARTEL
    # ==========================================================

    def crear_cartel_preview(
        self,
        producto,
        escala
    ):

        ancho_cm, alto_cm = (
            self.obtener_tamano()
        )

        ancho_px = max(
            1,
            int(
                ancho_cm
                * self.DPI_PREVIEW
                / 2.54
                * escala
            )
        )

        alto_px = max(
            1,
            int(
                alto_cm
                * self.DPI_PREVIEW
                / 2.54
                * escala
            )
        )

        imagen = QImage(
            ancho_px,
            alto_px,
            QImage.Format_ARGB32
        )

        imagen.fill(
            Qt.white
        )

        painter = QPainter(
            imagen
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        colores = (
            self.colores_estilo()
        )

        nombre = str(
            producto[1] or ""
        )

        precio = float(
            producto[2] or 0
        )

        leyenda = (
            self.leyenda.text().strip()
            or "OFERTA"
        )

        extra = (
            self.extra.text().strip()
        )

        negocio = str(
            get_setting(
                "nombre_negocio",
                "COTILLON"
            )
        )

        factor = (
            self.DPI_PREVIEW
            / 2.54
            * escala
        )

        def px(cm):
            return max(
                1,
                int(cm * factor)
            )

        def font_pt(v):
            return max(
                5,
                int(
                    v
                    * self.DPI_PREVIEW
                    / 72
                    * escala
                )
            )

        # ======================================================
        # TAMAÑOS
        # ======================================================

        if ancho_cm <= 8:

            nombre_size = 10
            leyenda_size = 8
            extra_size = 6
            negocio_size = 5

        elif ancho_cm <= 10:

            nombre_size = 13
            leyenda_size = 11
            extra_size = 7
            negocio_size = 6

        elif ancho_cm <= 14:

            nombre_size = 18
            leyenda_size = 15
            extra_size = 9
            negocio_size = 7

        else:

            nombre_size = 25
            leyenda_size = 20
            extra_size = 11
            negocio_size = 9

        precio_size = (
            self.precio_font_size()
        )

        margen = px(
            0.30
        )

        rect = imagen.rect().adjusted(
            px(0.04),
            px(0.04),
            -px(0.04),
            -px(0.04)
        )

        estilo = (
            self.estilo.currentText()
        )

        borde = QColor(
            colores["borde"]
        )

        fondo = QColor(
            colores["fondo"]
        )

        acento = QColor(
            colores["acento"]
        )

        # ======================================================
        # FORMA
        # ======================================================

        self.dibujar_forma_exterior(
            painter,
            rect,
            estilo,
            borde,
            fondo,
            px
        )

        # ======================================================
        # DECORACIONES
        # ======================================================

        painter.setPen(
            Qt.NoPen
        )

        if estilo == "Estrella":

            self.dibujar_estrellas(
                painter,
                ancho_px,
                alto_px,
                borde
            )

        elif estilo == "Fiesta":

            self.dibujar_fiesta(
                painter,
                ancho_px,
                alto_px
            )

        elif estilo == "Cotillón":

            self.dibujar_fiesta(
                painter,
                ancho_px,
                alto_px
            )

        elif estilo == "Cinta":

            painter.setBrush(
                QBrush(borde)
            )

            painter.drawRect(
                px(0.10),
                px(0.15),
                ancho_px - px(0.20),
                px(0.48)
            )

        elif estilo == "Cinta diagonal":

            painter.save()

            painter.translate(
                ancho_px - px(0.70),
                px(0.80)
            )

            painter.rotate(
                35
            )

            painter.setBrush(
                QBrush(borde)
            )

            painter.drawRect(
                -px(1.30),
                -px(0.12),
                px(2.60),
                px(0.24)
            )

            painter.restore()

        elif estilo == "Banner":

            painter.setBrush(
                QBrush(borde)
            )

            painter.drawRect(
                px(0.20),
                px(0.15),
                ancho_px - px(0.40),
                px(0.45)
            )

        elif estilo == "Oferta circular":

            radio = min(
                px(0.55),
                min(
                    ancho_px,
                    alto_px
                ) // 8
            )

            painter.setBrush(
                QBrush(borde)
            )

            painter.drawEllipse(
                ancho_px
                - margen
                - radio * 2,
                margen,
                radio * 2,
                radio * 2
            )

        elif estilo == "Sello":

            radio = min(
                px(0.45),
                min(
                    ancho_px,
                    alto_px
                ) // 9
            )

            painter.setPen(
                QPen(
                    borde,
                    max(
                        1,
                        px(0.04)
                    )
                )
            )

            painter.setBrush(
                Qt.NoBrush
            )

            painter.drawEllipse(
                ancho_px
                - margen
                - radio * 2,
                margen,
                radio * 2,
                radio * 2
            )

        elif estilo == "Premium":

            painter.setPen(
                QPen(
                    borde,
                    max(
                        1,
                        px(0.025)
                    )
                )
            )

            painter.setBrush(
                Qt.NoBrush
            )

            painter.drawRoundedRect(
                px(0.22),
                px(0.22),
                ancho_px - px(0.44),
                alto_px - px(0.44),
                px(0.15),
                px(0.15)
            )

        elif estilo == "Marco doble":

            painter.setPen(
                QPen(
                    borde,
                    max(
                        1,
                        px(0.025)
                    )
                )
            )

            painter.drawRect(
                px(0.25),
                px(0.25),
                ancho_px - px(0.50),
                alto_px - px(0.50)
            )

        # ======================================================
        # LEYENDA
        # ======================================================

        fuente = QFont(
            "Arial",
            font_pt(
                leyenda_size
            )
        )

        fuente.setBold(
            True
        )

        painter.setFont(
            fuente
        )

        painter.setPen(
            Qt.white
        )

        painter.setBrush(
            QBrush(borde)
        )

        badge_h = max(
            px(0.50),
            16
        )

        badge_w = int(
            (ancho_px - margen * 2)
            * 0.76
        )

        badge_x = (
            ancho_px
            - badge_w
        ) // 2

        badge_y = (
            margen
            + px(0.12)
        )

        # En precio gigante y súper oferta
        # la parte superior es más grande.

        if estilo == "Súper oferta":

            badge_w = (
                ancho_px
                - margen * 2
            )

            badge_x = margen

        painter.drawRoundedRect(
            badge_x,
            badge_y,
            badge_w,
            badge_h,
            px(0.07),
            px(0.07)
        )

        painter.drawText(
            badge_x,
            badge_y,
            badge_w,
            badge_h,
            Qt.AlignCenter,
            leyenda
        )

        # ======================================================
        # NOMBRE
        # ======================================================

        nombre_y = (
            badge_y
            + badge_h
            + px(0.12)
        )

        nombre_alto = int(
            alto_px * 0.27
        )

        fuente_nombre = QFont(
            "Arial",
            font_pt(
                nombre_size
            )
        )

        fuente_nombre.setBold(
            True
        )

        rect_nombre = (
            margen,
            nombre_y,
            ancho_px - margen * 2,
            nombre_alto
        )

        fuente_nombre = (
            self.ajustar_fuente_texto(
                nombre,
                fuente_nombre,
                rect_nombre,
                painter
            )
        )

        painter.setFont(
            fuente_nombre
        )

        painter.setPen(
            acento
        )

        painter.drawText(
            *rect_nombre,
            Qt.AlignCenter
            | Qt.TextWordWrap,
            nombre
        )

        # ======================================================
        # PRECIO
        # ======================================================

        precio_texto = (
            f"$ {precio:,.2f}"
        )

        fuente_precio = QFont(
            "Arial",
            font_pt(
                precio_size
            )
        )

        fuente_precio.setBold(
            True
        )

        # Precio gigante más protagonista.

        if estilo == "Precio gigante":

            precio_y = int(
                alto_px * 0.43
            )

            precio_alto = int(
                alto_px * 0.28
            )

        else:

            precio_y = int(
                alto_px * 0.47
            )

            precio_alto = int(
                alto_px * 0.20
            )

        rect_precio = (
            margen,
            precio_y,
            ancho_px - margen * 2,
            precio_alto
        )

        fuente_precio = (
            self.ajustar_fuente_texto(
                precio_texto,
                fuente_precio,
                rect_precio,
                painter,
                una_linea=True
            )
        )

        painter.setFont(
            fuente_precio
        )

        painter.setPen(
            QColor("#111827")
        )

        painter.drawText(
            *rect_precio,
            Qt.AlignCenter,
            precio_texto
        )

        # ======================================================
        # EXTRA
        # ======================================================

        if extra:

            fuente_extra = QFont(
                "Arial",
                font_pt(
                    extra_size
                )
            )

            painter.setFont(
                fuente_extra
            )

            painter.setPen(
                QColor("#475569")
            )

            rect_extra = (
                margen,
                int(
                    alto_px * 0.70
                ),
                ancho_px - margen * 2,
                int(
                    alto_px * 0.10
                )
            )

            painter.drawText(
                *rect_extra,
                Qt.AlignCenter
                | Qt.TextWordWrap,
                extra
            )

        # ======================================================
        # NEGOCIO
        # ======================================================

        fuente_negocio = QFont(
            "Arial",
            font_pt(
                negocio_size
            )
        )

        fuente_negocio.setBold(
            True
        )

        painter.setFont(
            fuente_negocio
        )

        painter.setPen(
            QColor("#334155")
        )

        rect_negocio = (
            margen,
            int(
                alto_px * 0.84
            ),
            ancho_px - margen * 2,
            int(
                alto_px * 0.07
            )
        )

        painter.drawText(
            *rect_negocio,
            Qt.AlignCenter,
            negocio
        )

        painter.end()

        return QPixmap.fromImage(
            imagen
        )

    # ==========================================================
    # DECORACIONES
    # ==========================================================

    def dibujar_estrellas(
        self,
        painter,
        ancho,
        alto,
        color
    ):

        painter.setBrush(
            QBrush(color)
        )

        painter.setPen(
            Qt.NoPen
        )

        puntos = [
            (0.14, 0.15, 0.09),
            (0.85, 0.16, 0.07),
            (0.12, 0.84, 0.07),
            (0.88, 0.83, 0.10),
        ]

        for x, y, r in puntos:

            cx = x * ancho
            cy = y * alto

            rr = (
                r
                * min(
                    ancho,
                    alto
                )
            )

            estrella = []

            for i in range(10):

                angulo = (
                    -math.pi / 2
                    + i * math.pi / 5
                )

                radio = (
                    rr
                    if i % 2 == 0
                    else rr * 0.42
                )

                estrella.append(
                    QPointF(
                        cx
                        + math.cos(angulo)
                        * radio,

                        cy
                        + math.sin(angulo)
                        * radio
                    )
                )

            painter.drawPolygon(
                QPolygonF(estrella)
            )

    def dibujar_fiesta(
        self,
        painter,
        ancho,
        alto
    ):

        colores = [
            "#e11d48",
            "#2563eb",
            "#f59e0b",
            "#16a34a",
            "#7c3aed",
            "#db2777",
        ]

        puntos = [
            (0.10, 0.15, 0),
            (0.28, 0.09, 1),
            (0.48, 0.15, 2),
            (0.70, 0.08, 3),
            (0.88, 0.16, 4),

            (0.10, 0.82, 5),
            (0.30, 0.90, 2),
            (0.52, 0.84, 0),
            (0.72, 0.91, 1),
            (0.90, 0.82, 3),
        ]

        painter.setPen(
            Qt.NoPen
        )

        for x, y, color_index in puntos:

            radio = max(
                3,
                int(
                    0.08
                    * min(
                        ancho,
                        alto
                    )
                )
            )

            painter.setBrush(
                QBrush(
                    QColor(
                        colores[
                            color_index
                        ]
                    )
                )
            )

            painter.drawEllipse(
                int(
                    x * ancho
                    - radio
                ),
                int(
                    y * alto
                    - radio
                ),
                radio * 2,
                radio * 2
            )

    # ==========================================================
    # AJUSTAR FUENTE
    # ==========================================================

    def ajustar_fuente_texto(
        self,
        texto,
        fuente,
        rect,
        painter,
        una_linea=False
    ):

        fuente = QFont(
            fuente
        )

        ancho = rect[2]
        alto = rect[3]

        while (
            fuente.pointSize() > 5
        ):

            metricas = QFontMetrics(
                fuente
            )

            if una_linea:

                if (
                    metricas.horizontalAdvance(
                        texto
                    )
                    <= ancho
                ):

                    break

            else:

                rect_texto = (
                    metricas.boundingRect(
                        0,
                        0,
                        ancho,
                        alto,
                        Qt.TextWordWrap,
                        texto
                    )
                )

                if (
                    rect_texto.height()
                    <= alto
                ):

                    break

            fuente.setPointSize(
                fuente.pointSize() - 1
            )

        return fuente

    # ==========================================================
    # PREVIEW DE PÁGINA
    # ==========================================================

    def crear_pagina_preview(
        self,
        carteles,
        pagina_numero,
        total_paginas,
        ancho_pagina=794,
        reservar_mitad=False,
        posicion_mitad=0
    ):

        escala = (
            ancho_pagina
            / self.DPI_PREVIEW
            * 2.54
            / self.A4_ANCHO_CM
        )

        alto_pagina = int(
            self.A4_ALTO_CM
            / self.A4_ANCHO_CM
            * ancho_pagina
        )

        pagina = QFrame()

        pagina.setFixedSize(
            ancho_pagina,
            alto_pagina
        )

        pagina.setStyleSheet("""
            QFrame {
                background:white;
                border:1px solid #cbd5e1;
            }
        """)

        layout = QGridLayout(
            pagina
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setHorizontalSpacing(
            0
        )

        layout.setVerticalSpacing(
            0
        )

        d = (
            self.calcular_distribucion()
        )

        margen = d["margen"]
        separacion = d["separacion"]
        columnas = d["columnas"]

        margen_horizontal = int(
            margen
            / self.A4_ANCHO_CM
            * ancho_pagina
        )

        margen_vertical = int(
            margen
            / self.A4_ALTO_CM
            * alto_pagina
        )

        layout.setContentsMargins(
            margen_horizontal,
            margen_vertical,
            margen_horizontal,
            margen_vertical
        )

        horizontal_spacing = int(
            separacion
            / self.A4_ANCHO_CM
            * ancho_pagina
        )

        vertical_spacing = int(
            separacion
            / self.A4_ALTO_CM
            * alto_pagina
        )

        layout.setHorizontalSpacing(
            max(
                0,
                horizontal_spacing
            )
        )

        layout.setVerticalSpacing(
            max(
                0,
                vertical_spacing
            )
        )

        # ======================================================
        # CARTeles
        # ======================================================

        for indice, cartel in enumerate(
            carteles
        ):

            producto = (
                cartel["producto"]
            )

            pixmap = (
                self.crear_cartel_preview(
                    producto,
                    escala
                )
            )

            label = QLabel()

            label.setPixmap(
                pixmap
            )

            label.setFixedSize(
                pixmap.size()
            )

            label.setAlignment(
                Qt.AlignCenter
            )

            label.setStyleSheet("""
                QLabel {
                    background:transparent;
                    border:0;
                    padding:0;
                    margin:0;
                }
            """)

            fila = (
                indice
                // columnas
            )

            columna = (
                indice
                % columnas
            )

            layout.addWidget(
                label,
                fila,
                columna,
                Qt.AlignTop
                | Qt.AlignLeft
            )

        contenedor = QWidget()

        contenedor_layout = (
            QVBoxLayout(
                contenedor
            )
        )

        contenedor_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        etiqueta = QLabel(
            f"Hoja {pagina_numero} "
            f"de {total_paginas}"
        )

        etiqueta.setAlignment(
            Qt.AlignCenter
        )

        etiqueta.setStyleSheet("""
            QLabel {
                color:#475569;
                font-weight:800;
                padding:6px;
            }
        """)

        contenedor_layout.addWidget(
            etiqueta
        )

        contenedor_layout.addWidget(
            pagina
        )

        return contenedor

    # ==========================================================
    # VISTA PREVIA
    # ==========================================================

    def preview(self):

        carteles = (
            self.obtener_carteles()
        )

        if not carteles:

            QMessageBox.warning(
                self,
                "Sin productos",
                "Seleccioná al menos un producto."
            )

            return

        d = (
            self.calcular_distribucion()
        )

        if (
            self.continuar_mitad.isChecked()
        ):

            primera = (
                d["por_hoja_mitad"]
            )

            resto = max(
                0,
                len(carteles)
                - primera
            )

            total_paginas = (
                1
                + math.ceil(
                    resto
                    / d["por_hoja"]
                )
                if resto
                else 1
            )

        else:

            total_paginas = math.ceil(
                len(carteles)
                / d["por_hoja"]
            )

        dialogo = QDialog(
            self
        )

        dialogo.setWindowTitle(
            "Vista previa — A4"
        )

        dialogo.resize(
            950,
            900
        )

        dialogo.setStyleSheet("""
            QDialog {
                background:#e5e7eb;
            }

            QScrollArea {
                background:#e5e7eb;
                border:0;
            }

            QPushButton {
                background:#0ea5e9;
                color:white;
                border:0;
                border-radius:8px;
                padding:9px 16px;
                font-weight:800;
            }

            QPushButton:hover {
                background:#0284c7;
            }

            QPushButton.secondary {
                background:#e2e8f0;
                color:#334155;
            }
        """)

        principal = QVBoxLayout(
            dialogo
        )

        modo = ""

        if (
            self.continuar_mitad.isChecked()
        ):

            modo = (
                "   •   Continuar desde "
                "mitad de hoja"
            )

        info = QLabel(
            f"📄 {total_paginas} "
            f"{'hoja' if total_paginas == 1 else 'hojas'} A4"
            f"   •   {len(carteles)} carteles"
            f"   •   {self.tam.currentText()}"
            f"   •   Diseño: "
            f"{self.estilo.currentText()}"
            f"   •   Separación: "
            f"{self.separacion.value():.2f} cm"
            f"{modo}"
        )

        info.setAlignment(
            Qt.AlignCenter
        )

        info.setWordWrap(
            True
        )

        info.setStyleSheet("""
            QLabel {
                background:white;
                border-radius:8px;
                padding:10px;
                color:#334155;
                font-weight:800;
            }
        """)

        principal.addWidget(
            info
        )

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setAlignment(
            Qt.AlignHCenter
        )

        scroll.setStyleSheet("""
            QScrollArea {
                background:#d1d5db;
                border:0;
            }
        """)

        contenido = QWidget()

        contenido.setStyleSheet("""
            QWidget {
                background:#d1d5db;
            }
        """)

        contenido_layout = (
            QVBoxLayout(
                contenido
            )
        )

        contenido_layout.setContentsMargins(
            30,
            30,
            30,
            30
        )

        contenido_layout.setSpacing(
            25
        )

        indice = 0

        for pagina in range(
            total_paginas
        ):

            if (
                pagina == 0
                and self.continuar_mitad.isChecked()
            ):

                capacidad = (
                    d["por_hoja_mitad"]
                )

                reservar = True

                posicion = (
                    self.mitad_posicion
                    .currentIndex()
                )

            else:

                capacidad = (
                    d["por_hoja"]
                )

                reservar = False
                posicion = 0

            fin = min(
                indice
                + capacidad,
                len(carteles)
            )

            carteles_pagina = (
                carteles[
                    indice:fin
                ]
            )

            indice = fin

            pagina_widget = (
                self.crear_pagina_preview(
                    carteles_pagina,
                    pagina + 1,
                    total_paginas,
                    reservar_mitad=reservar,
                    posicion_mitad=posicion
                )
            )

            contenido_layout.addWidget(
                pagina_widget,
                0,
                Qt.AlignHCenter
            )

        contenido_layout.addStretch()

        scroll.setWidget(
            contenido
        )

        principal.addWidget(
            scroll,
            1
        )

        botones = QHBoxLayout()

        cerrar = QPushButton(
            "Cerrar"
        )

        cerrar.setProperty(
            "class",
            "secondary"
        )

        cerrar.clicked.connect(
            dialogo.accept
        )

        imprimir = QPushButton(
            "🖨 Imprimir"
        )

        imprimir.clicked.connect(
            lambda: (
                dialogo.accept(),
                self.imprimir()
            )
        )

        botones.addStretch()

        botones.addWidget(
            cerrar
        )

        botones.addWidget(
            imprimir
        )

        principal.addLayout(
            botones
        )

        dialogo.exec()

    # ==========================================================
    # ACTUALIZACIÓN
    # ==========================================================

    def actualizar_preview_automaticamente(
        self
    ):
        # No abrimos una ventana nueva automáticamente.
        # La configuración queda lista y el usuario puede
        # pulsar "Vista previa A4".
        pass

    # ==========================================================
    # PDF
    # ==========================================================

    def save_pdf(self):

        carteles = (
            self.obtener_carteles()
        )

        if not carteles:

            QMessageBox.warning(
                self,
                "Sin productos",
                "Seleccioná al menos un producto."
            )

            return

        ruta, _ = (
            QFileDialog.getSaveFileName(
                self,
                "Guardar carteles en PDF",
                "carteles_ofertas.pdf",
                "PDF (*.pdf)"
            )
        )

        if not ruta:
            return

        try:

            documento = (
                QTextDocument()
            )

            documento.setHtml(
                self.html_a4()
            )

            printer = QPrinter(
                QPrinter.HighResolution
            )

            printer.setOutputFormat(
                QPrinter.PdfFormat
            )

            printer.setOutputFileName(
                ruta
            )

            printer.setPageMargins(
                QMarginsF(
                    0,
                    0,
                    0,
                    0
                )
            )

            documento.print_(
                printer
            )

            QMessageBox.information(
                self,
                "PDF",
                "El PDF se guardó correctamente."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo crear el PDF.\n\n{e}"
            )

    # ==========================================================
    # IMPRIMIR
    # ==========================================================

    def imprimir(self):

        carteles = (
            self.obtener_carteles()
        )

        if not carteles:

            QMessageBox.warning(
                self,
                "Sin productos",
                "Seleccioná al menos un producto."
            )

            return

        if not printer_names():

            show_no_printer(
                self
            )

            return

        try:

            html_doc = (
                self.html_a4()
            )

            print_html(
                html_doc,
                self,
                "impresora_carteles"
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error de impresión",
                f"No se pudo imprimir.\n\n{e}"
            )

    def print(self):

        self.imprimir()




import sqlite3
import math
import html

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QComboBox, QSpinBox, QDoubleSpinBox, QDialog, QMessageBox,
    QFileDialog, QAbstractItemView, QScrollArea, QFrame, QCheckBox
)
from PySide6.QtGui import (
    QImage, QPixmap, QPainter, QFont, QFontMetrics, QColor,
    QPen, QBrush, QPolygonF, QPainterPath
)
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtCore import Qt, QMarginsF, QPointF
from PySide6.QtGui import QPageSize, QPageLayout

from ui.db import BASE_DATOS, init_db, get_setting
from ui.printing import printer_names, show_no_printer


class Carteles(QWidget):
    """Generador profesional de carteles.

    Principios de esta versión:
    - Una única geometría de render para vista previa, PDF e impresión.
    - A4 real: 210 x 297 mm, siempre en vertical.
    - El primer cartel siempre empieza arriba a la izquierda.
    - La separación es física y se aplica exactamente en X/Y.
    - Se eliminó el modo de comenzar desde la mitad de una hoja.
    - Las formas son geométricamente distintas y se conservan en preview/impresión.
    """

    A4_ANCHO_CM = 21.0
    A4_ALTO_CM = 29.7
    PREVIEW_DPI = 96

    def __init__(self):
        super().__init__()
        init_db()

        self.setWindowTitle(
            f"Carteles y Ofertas - {get_setting('nombre_negocio', 'COTILLON')}"
        )
        self.resize(1180, 860)

        self.setStyleSheet("""
            QWidget { background:#f6f8fb; color:#172033; font-family:"Segoe UI"; }
            QGroupBox {
                background:#ffffff; border:1px solid #dfe5ee; border-radius:16px;
                margin-top:14px; padding:16px; font-weight:800;
            }
            QGroupBox::title { background:#ffffff; subcontrol-origin:margin; left:14px; padding:0 8px; }
            QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox {
                background:#fff; border:1px solid #cfd7e3; border-radius:10px;
                padding:9px; min-height:22px;
            }
            QLineEdit:focus,QComboBox:focus,QSpinBox:focus,QDoubleSpinBox:focus { border:2px solid #2563eb; }
            QPushButton {
                background:#2563eb; color:white; border:0; border-radius:10px;
                padding:10px 16px; font-weight:800;
            }
            QPushButton:hover { background:#1d4ed8; }
            QPushButton.secondary { background:#e8edf5; color:#25324a; }
            QPushButton.secondary:hover { background:#dbe3ef; }
            QListWidget { background:#fff; border:1px solid #cfd7e3; border-radius:10px; padding:5px; }
            QListWidget::item { padding:10px; border-radius:7px; }
            QListWidget::item:selected { background:#dbeafe; color:#1d4ed8; }
            QLabel.muted { color:#64748b; }
            QLabel.counter { color:#1d4ed8; background:#dbeafe; border-radius:8px; padding:6px 10px; font-weight:800; }
            QCheckBox { background:#fff; padding:5px; font-weight:700; }
        """)

        self.rows = []
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(14)

        head = QHBoxLayout()
        title = QLabel("🏷️ Carteles y Ofertas")
        title.setStyleSheet("font-size:28px;font-weight:900;")
        head.addWidget(title)
        head.addStretch()
        root.addLayout(head)

        sub = QLabel(
            "Diseñá carteles profesionales con medidas físicas reales. "
            "La vista previa, el PDF y la impresión utilizan exactamente el mismo render."
        )
        sub.setProperty("class", "muted")
        root.addWidget(sub)

        productos_box = QGroupBox("🛒 Productos")
        productos_layout = QVBoxLayout(productos_box)
        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText("🔎 Buscar por nombre o código de barras...")
        self.busqueda.setClearButtonEnabled(True)
        self.busqueda.textChanged.connect(self.filtrar_productos)
        productos_layout.addWidget(self.busqueda)

        info = QLabel("Podés seleccionar varios productos. Usá Ctrl para seleccionar separados o Shift para un rango.")
        info.setProperty("class", "muted")
        info.setWordWrap(True)
        productos_layout.addWidget(info)

        self.lista_productos = QListWidget()
        self.lista_productos.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lista_productos.setMinimumHeight(180)
        self.lista_productos.itemSelectionChanged.connect(self.actualizar_seleccion)
        productos_layout.addWidget(self.lista_productos)

        acciones = QHBoxLayout()
        self.btn_todos = QPushButton("☑ Seleccionar todos")
        self.btn_todos.setProperty("class", "secondary")
        self.btn_todos.clicked.connect(self.seleccionar_todos)
        self.btn_limpiar = QPushButton("✕ Limpiar selección")
        self.btn_limpiar.setProperty("class", "secondary")
        self.btn_limpiar.clicked.connect(self.lista_productos.clearSelection)
        acciones.addWidget(self.btn_todos)
        acciones.addWidget(self.btn_limpiar)
        acciones.addStretch()
        self.lbl_seleccionados = QLabel("0 productos seleccionados")
        self.lbl_seleccionados.setProperty("class", "counter")
        acciones.addWidget(self.lbl_seleccionados)
        productos_layout.addLayout(acciones)
        root.addWidget(productos_box, 1)

        config_box = QGroupBox("🎨 Diseño e impresión")
        config = QGridLayout(config_box)

        self.tamanos = {
            "Chico — 8 × 5 cm": (8.0, 5.0),
            "Mediano — 10 × 7 cm": (10.0, 7.0),
            "Grande — 14 × 10 cm": (14.0, 10.0),
            "1/4 de A4 — 14,85 × 10,5 cm": (14.85, 10.5),
            "1/2 A4 — 21 × 14,85 cm": (21.0, 14.85),
            "A4 completo — 21 × 29,7 cm": (21.0, 29.7),
        }
        self.tam = QComboBox()
        self.tam.addItems(self.tamanos.keys())
        self.tam.currentIndexChanged.connect(self.actualizar_preview_automaticamente)

        # Solo formas realmente distintas.
        self.disenos = [
            "Nube",
            "Globo de mensaje",
            "Explosión",
            "Estrella",
            "Etiqueta con troquel",
            "Sello circular",
            "Ticket",
            "Cinta diagonal",
            "Hexágono",
            "Premium",
        ]
        self.estilo = QComboBox()
        self.estilo.addItems(self.disenos)
        self.estilo.currentIndexChanged.connect(self.actualizar_preview_automaticamente)

        self.leyenda = QLineEdit("OFERTA")
        self.leyenda.setPlaceholderText("Ej.: OFERTA, PROMO, LIQUIDACIÓN")
        self.leyenda.textChanged.connect(self.actualizar_preview_automaticamente)

        self.extra = QLineEdit()
        self.extra.setPlaceholderText('Ej.: "Hasta agotar stock"')
        self.extra.textChanged.connect(self.actualizar_preview_automaticamente)

        self.texto_precio = QComboBox()
        self.texto_precio.addItems(["Automático", "Pequeño", "Mediano", "Grande", "Muy grande"])
        self.texto_precio.currentIndexChanged.connect(self.actualizar_preview_automaticamente)

        self.cantidad = QSpinBox()
        self.cantidad.setRange(1, 100)
        self.cantidad.setValue(1)
        self.cantidad.valueChanged.connect(self.actualizar_preview_automaticamente)

        self.distribucion = QComboBox()
        self.distribucion.addItems(["Máximo aprovechamiento", "Una por fila"])
        self.distribucion.currentIndexChanged.connect(self.actualizar_preview_automaticamente)

        self.separacion = QDoubleSpinBox()
        self.separacion.setRange(0.0, 2.0)
        self.separacion.setSingleStep(0.05)
        self.separacion.setDecimals(2)
        self.separacion.setValue(0.0)
        self.separacion.setSuffix(" cm")
        self.separacion.setToolTip("Separación física real entre carteles. 0 cm = carteles juntos.")
        self.separacion.valueChanged.connect(self.actualizar_preview_automaticamente)

        campos = [
            (QLabel("Tamaño físico:"), self.tam, 0, 0, 0, 1),
            (QLabel("Forma:"), self.estilo, 0, 2, 0, 3),
            (QLabel("Leyenda:"), self.leyenda, 1, 0, 1, 1),
            (QLabel("Texto adicional:"), self.extra, 1, 2, 1, 3),
            (QLabel("Tamaño del precio:"), self.texto_precio, 2, 0, 2, 1),
            (QLabel("Cantidad por producto:"), self.cantidad, 2, 2, 2, 3),
            (QLabel("Distribución:"), self.distribucion, 3, 0, 3, 1),
            (QLabel("Separación:"), self.separacion, 3, 2, 3, 3),
        ]
        for label, widget, r1, c1, r2, c2 in campos:
            config.addWidget(label, r1, c1)
            config.addWidget(widget, r2, c2)
        root.addWidget(config_box)

        botones = QHBoxLayout()
        self.btn_preview = QPushButton("👁 Vista previa A4")
        self.btn_preview.clicked.connect(self.preview)
        self.btn_pdf = QPushButton("📄 Guardar PDF")
        self.btn_pdf.setProperty("class", "secondary")
        self.btn_pdf.clicked.connect(self.save_pdf)
        self.btn_print = QPushButton("🖨 Imprimir A4")
        self.btn_print.clicked.connect(self.imprimir)
        botones.addWidget(self.btn_preview)
        botones.addWidget(self.btn_pdf)
        botones.addWidget(self.btn_print)
        botones.addStretch()
        root.addLayout(botones)

        self.cargar_productos()

    # ----------------------------------------------------------
    # PRODUCTOS
    # ----------------------------------------------------------
    def cargar_productos(self):
        try:
            conexion = sqlite3.connect(BASE_DATOS)
            self.rows = conexion.execute(
                "SELECT id, nombre, precio_venta, codigo_barras FROM productos ORDER BY nombre"
            ).fetchall()
            conexion.close()
            self.recargar_lista()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los productos.\n\n{e}")

    def recargar_lista(self):
        texto = self.busqueda.text().strip().lower()
        seleccionados = set(self.obtener_ids_seleccionados())
        self.lista_productos.blockSignals(True)
        self.lista_productos.clear()
        for row in self.rows:
            producto_id, nombre, precio, codigo = row
            nombre = str(nombre or "")
            codigo = str(codigo or "")
            if texto and texto not in nombre.lower() and texto not in codigo.lower():
                continue
            item = QListWidgetItem(f"{nombre}    —    $ {float(precio or 0):,.2f}" + (f"    |    Código: {codigo}" if codigo else ""))
            item.setData(Qt.UserRole, producto_id)
            self.lista_productos.addItem(item)
            if producto_id in seleccionados:
                item.setSelected(True)
        self.lista_productos.blockSignals(False)
        self.actualizar_seleccion()

    def filtrar_productos(self, texto):
        self.recargar_lista()

    def obtener_ids_seleccionados(self):
        return [item.data(Qt.UserRole) for item in self.lista_productos.selectedItems()]

    def obtener_productos_seleccionados(self):
        ids = set(self.obtener_ids_seleccionados())
        return [row for row in self.rows if row[0] in ids]

    def actualizar_seleccion(self):
        cantidad = len(self.lista_productos.selectedItems())
        self.lbl_seleccionados.setText("1 producto seleccionado" if cantidad == 1 else f"{cantidad} productos seleccionados")

    def seleccionar_todos(self):
        self.lista_productos.selectAll()

    # ----------------------------------------------------------
    # CONFIGURACIÓN
    # ----------------------------------------------------------
    def obtener_tamano(self):
        return self.tamanos.get(self.tam.currentText(), (8.0, 5.0))

    def precio_font_size(self):
        modo = self.texto_precio.currentText()
        ancho, _ = self.obtener_tamano()
        if modo == "Pequeño": return 22
        if modo == "Mediano": return 30
        if modo == "Grande": return 40
        if modo == "Muy grande": return 52
        if ancho <= 8: return 21
        if ancho <= 10: return 27
        if ancho <= 14: return 36
        return 46

    def paleta(self):
        return {
            "Nube": ("#EAF7FF", "#1D8ED1", "#075985", "#0F172A"),
            "Globo de mensaje": ("#F0FDF4", "#16A34A", "#166534", "#0F172A"),
            "Explosión": ("#FFF1F2", "#E11D48", "#9F1239", "#111827"),
            "Estrella": ("#FFF7ED", "#F59E0B", "#B45309", "#111827"),
            "Etiqueta con troquel": ("#F5F3FF", "#7C3AED", "#5B21B6", "#1F1B3A"),
            "Sello circular": ("#FEFCE8", "#CA8A04", "#854D0E", "#422006"),
            "Ticket": ("#EFF6FF", "#2563EB", "#1D4ED8", "#172554"),
            "Cinta diagonal": ("#FFF7ED", "#EA580C", "#C2410C", "#431407"),
            "Hexágono": ("#ECFEFF", "#0891B2", "#0E7490", "#164E63"),
            "Premium": ("#FAF5FF", "#7C3AED", "#5B21B6", "#2E1065"),
        }

    def colores_estilo(self):
        fondo, borde, acento, texto = self.paleta()[self.estilo.currentText()]
        return {"fondo": QColor(fondo), "borde": QColor(borde), "acento": QColor(acento), "texto": QColor(texto)}

    # ----------------------------------------------------------
    # DISTRIBUCIÓN A4
    # ----------------------------------------------------------
    def calcular_distribucion(self):
        ancho, alto = self.obtener_tamano()
        margen = 0.20
        separacion = max(0.0, float(self.separacion.value()))
        usable_ancho = self.A4_ANCHO_CM - 2 * margen
        usable_alto = self.A4_ALTO_CM - 2 * margen

        columnas = 1 if self.distribucion.currentText() == "Una por fila" else max(1, int((usable_ancho + separacion) // (ancho + separacion)))
        filas = max(1, int((usable_alto + separacion) // (alto + separacion)))

        return {
            "cartel_ancho": ancho,
            "cartel_alto": alto,
            "margen": margen,
            "separacion": separacion,
            "columnas": columnas,
            "filas": filas,
            "por_hoja": columnas * filas,
        }

    # ----------------------------------------------------------
    # DATOS DE CARTELES
    # ----------------------------------------------------------
    def obtener_carteles(self):
        productos = self.obtener_productos_seleccionados()
        cantidad = self.cantidad.value()
        resultado = []
        for producto in productos:
            for _ in range(cantidad):
                resultado.append(producto)
        return resultado

    # ----------------------------------------------------------
    # GEOMETRÍA DE FORMAS
    # ----------------------------------------------------------
    def forma_path(self, estilo, rect):
        x, y, w, h = rect
        path = QPainterPath()

        if estilo == "Nube":
            # Nube real: base redondeada + tres lóbulos superiores.
            path.moveTo(x + 0.14*w, y + 0.78*h)
            path.cubicTo(x + 0.04*w, y + 0.78*h, x + 0.02*w, y + 0.68*h, x + 0.05*w, y + 0.60*h)
            path.cubicTo(x + 0.00*w, y + 0.45*h, x + 0.10*w, y + 0.31*h, x + 0.23*w, y + 0.34*h)
            path.cubicTo(x + 0.25*w, y + 0.15*h, x + 0.42*w, y + 0.06*h, x + 0.53*w, y + 0.20*h)
            path.cubicTo(x + 0.65*w, y + 0.02*h, x + 0.84*w, y + 0.13*h, x + 0.82*w, y + 0.31*h)
            path.cubicTo(x + 0.96*w, y + 0.28*h, x + 1.02*w, y + 0.44*h, x + 0.94*w, y + 0.56*h)
            path.cubicTo(x + 0.99*w, y + 0.70*h, x + 0.91*w, y + 0.78*h, x + 0.79*w, y + 0.78*h)
            path.closeSubpath()
        elif estilo == "Globo de mensaje":
            path.moveTo(x+0.10*w,y+0.08*h)
            path.addRoundedRect(x+0.05*w,y+0.05*h,0.90*w,0.72*h,min(w,h)*0.08,min(w,h)*0.08)
            path.moveTo(x+0.25*w,y+0.76*h)
            path.lineTo(x+0.18*w,y+0.94*h)
            path.lineTo(x+0.39*w,y+0.77*h)
        elif estilo == "Explosión":
            pts=[]
            cx=x+w/2; cy=y+h/2
            for i in range(24):
                ang=-math.pi/2+i*2*math.pi/24
                r=min(w,h)*(0.50 if i%2==0 else 0.39)
                pts.append(QPointF(cx+math.cos(ang)*r,cy+math.sin(ang)*r))
            path.addPolygon(QPolygonF(pts))
        elif estilo == "Estrella":
            pts=[]; cx=x+w/2; cy=y+h/2
            for i in range(10):
                ang=-math.pi/2+i*math.pi/5
                r=min(w,h)*(0.50 if i%2==0 else 0.23)
                pts.append(QPointF(cx+math.cos(ang)*r,cy+math.sin(ang)*r))
            path.addPolygon(QPolygonF(pts))
        elif estilo == "Etiqueta con troquel":
            path.addRoundedRect(x,y,w,h,min(w,h)*0.08,min(w,h)*0.08)
            path.addEllipse(x+w*0.84,y+h*0.38,w*0.12,h*0.24)
        elif estilo == "Sello circular":
            r=min(w,h)*0.48
            path.addEllipse(x+w/2-r,y+h/2-r,2*r,2*r)
        elif estilo == "Ticket":
            path.moveTo(x,y+h*0.08)
            path.lineTo(x+w,y+h*0.08)
            path.lineTo(x+w,y+h*0.92)
            tooth=w*0.035
            n=max(8,int(h/(tooth*2.2)))
            step=h*0.84/n
            yy=y+h*0.92
            for i in range(n):
                path.lineTo(x+w-(tooth if i%2==0 else 0),yy)
                yy-=step
            path.lineTo(x,y+h*0.92)
            path.closeSubpath()
        elif estilo == "Cinta diagonal":
            path.addRoundedRect(x,y,w,h,min(w,h)*0.04,min(w,h)*0.04)
        elif estilo == "Hexágono":
            pts=[QPointF(x+w*0.18,y),QPointF(x+w*0.82,y),QPointF(x+w,y+h*0.5),QPointF(x+w*0.82,y+h),QPointF(x+w*0.18,y+h),QPointF(x,y+h*0.5)]
            path.addPolygon(QPolygonF(pts))
        else:  # Premium
            path.addRoundedRect(x,y,w,h,min(w,h)*0.06,min(w,h)*0.06)
        return path

    # ----------------------------------------------------------
    # RENDER DE UN CARTEL — USADO POR PREVIEW/PDF/IMPRESIÓN
    # ----------------------------------------------------------
    def render_cartel(self, painter, producto, rect):
        x,y,w,h=rect
        estilo=self.estilo.currentText()
        c=self.colores_estilo()
        nombre=str(producto[1] or "")
        precio=float(producto[2] or 0)
        codigo=str(producto[3] or "")
        leyenda=self.leyenda.text().strip() or "OFERTA"
        extra=self.extra.text().strip()
        negocio=str(get_setting("nombre_negocio","COTILLON"))

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        path=self.forma_path(estilo,rect)
        painter.setPen(QPen(c["borde"], max(1,w*0.007)))
        painter.setBrush(QBrush(c["fondo"]))
        painter.drawPath(path)

        # Interior seguro para texto.
        pad=min(w,h)*0.055
        ix,iy,iw,ih=x+pad,y+pad,w-2*pad,h-2*pad

        # Cinta diagonal: forma propia y no cambia el tamaño físico del cartel.
        if estilo=="Cinta diagonal":
            painter.save()
            painter.setPen(Qt.NoPen); painter.setBrush(QBrush(c["borde"]))
            painter.translate(x+w*0.78,y+h*0.15); painter.rotate(32)
            painter.drawRect(-w*0.24,-h*0.035,w*0.48,h*0.07)
            painter.restore()

        # Sello: anillo interior.
        if estilo=="Sello circular":
            r=min(w,h)*0.39
            painter.setBrush(Qt.NoBrush); painter.setPen(QPen(c["acento"],max(1,w*0.006)))
            painter.drawEllipse(x+w/2-r,y+h/2-r,2*r,2*r)

        # Premium: doble marco.
        if estilo=="Premium":
            painter.setBrush(Qt.NoBrush); painter.setPen(QPen(c["acento"],max(1,w*0.003)))
            painter.drawRoundedRect(x+w*.045,y+h*.045,w*.91,h*.91,min(w,h)*.035,min(w,h)*.035)

        # Globo: cola visible fuera del cuerpo.
        if estilo=="Globo de mensaje":
            tail=QPainterPath()
            tail.moveTo(x+w*.23,y+h*.75); tail.lineTo(x+w*.16,y+h*.95); tail.lineTo(x+w*.39,y+h*.77); tail.closeSubpath()
            painter.setPen(QPen(c["borde"],max(1,w*.007))); painter.setBrush(QBrush(c["fondo"]))
            painter.drawPath(tail)

        # Nube: pequeños círculos de volumen para reforzar la silueta.
        if estilo=="Nube":
            painter.setPen(Qt.NoPen); painter.setBrush(QBrush(c["acento"]))
            r=min(w,h)*.025
            painter.drawEllipse(x+w*.12,y+h*.67,r*2,r*2)
            painter.drawEllipse(x+w*.83,y+h*.63,r*2.5,r*2.5)

        # Encabezado.
        if estilo=="Sello circular":
            badge_rect=(ix,iy,iw,ih*.15)
        else:
            badge_rect=(ix,iy,iw*.78,ih*.15)
            badge_rect=(x+(w-badge_rect[2])/2,y+pad,badge_rect[2],badge_rect[3])

        painter.setPen(Qt.NoPen); painter.setBrush(QBrush(c["borde"]))
        if estilo=="Sello circular":
            painter.drawRoundedRect(*badge_rect,min(w,h)*.025,min(w,h)*.025)
        else:
            painter.drawRoundedRect(*badge_rect,min(w,h)*.025,min(w,h)*.025)
        self.draw_center_text(painter,leyenda,badge_rect,max(7,w*0.035),QColor("white"),True)

        # Nombre.
        nombre_rect=(ix, y+h*.25, iw, h*.25)
        self.draw_fit_text(painter,nombre,nombre_rect,max(8,w*.075),c["acento"],True,True)

        # Precio.
        precio_rect=(ix,y+h*.48,iw,h*.19)
        self.draw_fit_text(painter,f"$ {precio:,.2f}",precio_rect,max(10,w*.11),QColor("#111827"),True,False)

        if extra:
            self.draw_fit_text(painter,extra,(ix,y+h*.69,iw,h*.10),max(6,w*.035),QColor("#475569"),False,True)

        self.draw_center_text(painter,negocio,(ix,y+h*.82,iw,h*.075),max(5,w*.028),QColor("#334155"),True)

        if codigo and estilo not in ("Sello circular",):
            self.draw_center_text(painter,f"Código: {codigo}",(ix,y+h*.90,iw,h*.055),max(4,w*.020),QColor("#64748b"),False)

        # Decoración específica adicional.
        if estilo=="Estrella":
            painter.setPen(Qt.NoPen); painter.setBrush(QBrush(c["acento"]))
            for px,py,rr in ((.12,.15,.045),(.84,.18,.035),(.15,.82,.035),(.85,.80,.045)):
                painter.drawEllipse(x+w*px-w*rr,y+h*py-h*rr,w*rr*2,h*rr*2)
        elif estilo=="Explosión":
            painter.setPen(QPen(c["acento"],max(1,w*.006))); painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(x+w*.34,y+h*.34,w*.32,h*.32)
        elif estilo=="Ticket":
            painter.setPen(QPen(c["acento"],max(1,w*.004)))
            painter.drawLine(x+w*.08,y+h*.20,x+w*.92,y+h*.20)
        elif estilo=="Hexágono":
            painter.setPen(QPen(c["acento"],max(1,w*.004))); painter.setBrush(Qt.NoBrush)
            painter.drawLine(x+w*.22,y+h*.08,x+w*.78,y+h*.08)

        painter.restore()

    def draw_center_text(self,painter,text,rect,size,color,bold=False):
        font=QFont("Arial")
        font.setPointSize(max(5,int(size*72/self.PREVIEW_DPI)))
        font.setBold(bold)
        painter.setFont(font); painter.setPen(color)
        painter.drawText(*map(int,rect),Qt.AlignCenter|Qt.TextWordWrap,str(text))

    def draw_fit_text(self,painter,text,rect,size,color,bold=False,wrap=True):
        x,y,w,h=map(int,rect)
        font=QFont("Arial")
        font.setPointSize(max(5,int(size*72/self.PREVIEW_DPI)))
        font.setBold(bold)
        while font.pointSize()>5:
            fm=QFontMetrics(font)
            if wrap:
                r=fm.boundingRect(0,0,w,h,Qt.AlignCenter|Qt.TextWordWrap,str(text))
                if r.height()<=h and r.width()<=w: break
            else:
                if fm.horizontalAdvance(str(text))<=w and fm.height()<=h: break
            font.setPointSize(font.pointSize()-1)
        painter.setFont(font); painter.setPen(color)
        flags=Qt.AlignCenter|(Qt.TextWordWrap if wrap else 0)
        painter.drawText(x,y,w,h,flags,str(text))

    # ----------------------------------------------------------
    # PÁGINA A4 — MISMO RENDER EN PREVIEW/PDF/IMPRESORA
    # ----------------------------------------------------------
    def render_page(self,painter,carteles,offset=0):
        page_w=painter.viewport().width()
        page_h=painter.viewport().height()
        # El tamaño físico se toma siempre del ancho/alto A4 del dispositivo.
        cmx=page_w/self.A4_ANCHO_CM
        cmy=page_h/self.A4_ALTO_CM
        margen=self.calcular_distribucion()["margen"]
        sep=self.calcular_distribucion()["separacion"]
        ancho,alto=self.obtener_tamano()
        d=self.calcular_distribucion()
        columnas=d["columnas"]

        x0=margen*cmx
        y0=margen*cmy
        w=ancho*cmx
        h=alto*cmy
        sx=sep*cmx
        sy=sep*cmy

        for i,producto in enumerate(carteles):
            fila=i//columnas
            col=i%columnas
            x=x0+col*(w+sx)
            y=y0+fila*(h+sy)
            if x+w > page_w+1 or y+h > page_h+1:
                continue
            self.render_cartel(painter,producto,(x,y,w,h))

    def render_page_image(self,carteles,scale=1.0):
        w=max(1,int(self.A4_ANCHO_CM/2.54*self.PREVIEW_DPI*scale))
        h=max(1,int(self.A4_ALTO_CM/2.54*self.PREVIEW_DPI*scale))
        image=QImage(w,h,QImage.Format_ARGB32)
        image.fill(Qt.white)
        painter=QPainter(image)
        self.render_page(painter,carteles)
        painter.end()
        return image

    # ----------------------------------------------------------
    # PREVIEW
    # ----------------------------------------------------------
    def preview(self):
        carteles=self.obtener_carteles()
        if not carteles:
            QMessageBox.warning(self,"Sin productos","Seleccioná al menos un producto.")
            return

        d=self.calcular_distribucion()
        total_paginas=math.ceil(len(carteles)/d["por_hoja"])

        dialogo=QDialog(self)
        dialogo.setWindowTitle("Vista previa — A4 real")
        dialogo.resize(1000,900)
        dialogo.setStyleSheet("QDialog{background:#d9dee7;} QScrollArea{background:#d9dee7;border:0;} QPushButton{background:#2563eb;color:white;border:0;border-radius:8px;padding:9px 16px;font-weight:800;} QPushButton.secondary{background:#e8edf5;color:#25324a;}")
        principal=QVBoxLayout(dialogo)

        info=QLabel(
            f"📄 A4 vertical 210 × 297 mm  •  {total_paginas} {'hoja' if total_paginas==1 else 'hojas'}  •  "
            f"{len(carteles)} carteles  •  {self.tam.currentText()}  •  Separación: {d['separacion']:.2f} cm  •  Inicio: esquina superior izquierda"
        )
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("background:white;border-radius:9px;padding:10px;color:#334155;font-weight:800;")
        principal.addWidget(info)

        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setAlignment(Qt.AlignHCenter)
        contenido=QWidget(); layout=QVBoxLayout(contenido); layout.setContentsMargins(30,30,30,30); layout.setSpacing(24)

        for pagina in range(total_paginas):
            inicio=pagina*d["por_hoja"]
            fin=min(len(carteles),(pagina+1)*d["por_hoja"])
            page_carteles=carteles[inicio:fin]
            # 96 DPI = referencia A4 en pantalla: 794 x 1122 px.
            image=self.render_page_image(page_carteles,1.0)
            label=QLabel(); label.setPixmap(QPixmap.fromImage(image)); label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("background:white;border:1px solid #c4cad4;")
            holder=QVBoxLayout();
            page_label=QLabel(f"Hoja {pagina+1} de {total_paginas}"); page_label.setAlignment(Qt.AlignCenter); page_label.setStyleSheet("color:#475569;font-weight:800;padding:5px;")
            wrapper=QWidget(); wl=QVBoxLayout(wrapper); wl.setContentsMargins(0,0,0,0); wl.addWidget(page_label); wl.addWidget(label)
            layout.addWidget(wrapper,0,Qt.AlignHCenter)
        layout.addStretch()
        scroll.setWidget(contenido); principal.addWidget(scroll,1)

        botones=QHBoxLayout(); botones.addStretch()
        cerrar=QPushButton("Cerrar"); cerrar.setProperty("class","secondary"); cerrar.clicked.connect(dialogo.accept)
        imprimir=QPushButton("🖨 Imprimir exactamente esta vista")
        imprimir.clicked.connect(lambda:(dialogo.accept(),self.imprimir()))
        botones.addWidget(cerrar); botones.addWidget(imprimir); principal.addLayout(botones)
        dialogo.exec()

    def actualizar_preview_automaticamente(self):
        # La vista previa se genera al abrirla. Se mantiene esta señal para no romper la interfaz existente.
        pass

    # ----------------------------------------------------------
    # SALIDA FÍSICA
    # ----------------------------------------------------------
    def _configurar_printer(self,printer,output_file=None):
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageOrientation(QPageLayout.Portrait)
        printer.setPageMargins(QMarginsF(0,0,0,0),QPrinter.Unit.Millimeter)
        if output_file:
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(output_file)

    def _imprimir_con_printer(self,printer,carteles):
        d=self.calcular_distribucion()
        por_hoja=d["por_hoja"]
        paginas=math.ceil(len(carteles)/por_hoja)
        painter=QPainter(printer)
        try:
            for pagina in range(paginas):
                if pagina>0:
                    printer.newPage()
                inicio=pagina*por_hoja
                fin=min(len(carteles),(pagina+1)*por_hoja)
                self.render_page(painter,carteles[inicio:fin])
        finally:
            painter.end()

    def save_pdf(self):
        carteles=self.obtener_carteles()
        if not carteles:
            QMessageBox.warning(self,"Sin productos","Seleccioná al menos un producto.")
            return
        ruta,_=QFileDialog.getSaveFileName(self,"Guardar carteles en PDF","carteles_ofertas.pdf","PDF (*.pdf)")
        if not ruta: return
        try:
            printer=QPrinter(QPrinter.HighResolution)
            self._configurar_printer(printer,ruta)
            self._imprimir_con_printer(printer,carteles)
            QMessageBox.information(self,"PDF","El PDF se guardó correctamente en A4, usando el mismo render de la vista previa.")
        except Exception as e:
            QMessageBox.critical(self,"Error",f"No se pudo crear el PDF.\n\n{e}")

    def imprimir(self):
        carteles=self.obtener_carteles()
        if not carteles:
            QMessageBox.warning(self,"Sin productos","Seleccioná al menos un producto.")
            return
        if not printer_names():
            show_no_printer(self)
            return
        try:
            printer=QPrinter(QPrinter.HighResolution)
            self._configurar_printer(printer)
            self._imprimir_con_printer(printer,carteles)
        except Exception as e:
            QMessageBox.critical(self,"Error de impresión",f"No se pudo imprimir.\n\n{e}")

    def print(self):
        self.imprimir()
