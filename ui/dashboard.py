# -*- coding: utf-8 -*-

import sqlite3
import datetime
import requests
import csv
import html

from PySide6.QtCore import Qt, QTimer, QSettings
from core.version import obtener_version_actual

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QDialog,
    QWidget,
    QLabel,
    QPushButton,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QStackedWidget,
    QScrollArea,
    QSizePolicy,
    QMessageBox,
    QFileDialog,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QGroupBox,
    QSizeGrip
)

from PySide6.QtCore import (
    Qt,
    QTimer,
    QSizeF,
)

from PySide6.QtGui import (
    QTextDocument,
    QPdfWriter,
    QPageSize,
)

from PySide6.QtPrintSupport import (
    QPrinter,
    QPrintDialog,
)

from ui.db import (
    BASE_DATOS,
    init_db,
    archivar_ventas,
    get_setting,
    registrar_sincronizacion,
    nuevo_uuid,
)

from ui.productos import Productos
from ui.ventas import Ventas
from ui.clientes import Clientes
from ui.historial import Historial
from ui.reportes import Reportes
from ui.pedidos import Pedidos
from ui.documentos import Documentos
from ui.carteles import Carteles
from ui.caja import Caja
from ui.configuracion import Configuracion


# ============================================================
# UTILIDADES
# ============================================================

def _tabla_columnas(cursor, tabla):

    try:

        return {
            row[1]
            for row in cursor.execute(
                f'PRAGMA table_info("{tabla}")'
            ).fetchall()
        }

    except Exception:

        return set()


def _numero(valor):

    try:

        if valor is None:
            return 0.0

        if isinstance(valor, str):

            valor = valor.strip()

            if not valor:
                return 0.0

            if "," in valor and "." in valor:

                valor = valor.replace(".", "")
                valor = valor.replace(",", ".")

            elif "," in valor:

                valor = valor.replace(",", ".")

        return float(valor)

    except Exception:

        return 0.0


def _moneda(valor):

    numero = _numero(valor)

    texto = f"{numero:,.2f}"

    texto = (
        texto
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    return f"$ {texto}"


def _fecha_bonita(fecha):

    if not fecha:
        return ""

    texto = str(fecha)

    if len(texto) >= 10:

        try:

            return datetime.datetime.strptime(
                texto[:10],
                "%Y-%m-%d"
            ).strftime("%d/%m/%Y")

        except Exception:
            pass

    return texto


def _item(texto):

    item = QTableWidgetItem(
        "" if texto is None else str(texto)
    )

    item.setFlags(
        item.flags()
        & ~Qt.ItemIsEditable
    )

    return item


# ============================================================
# TABLA CONFIGURADA
# ============================================================

def _configurar_tabla(tabla, nombre_config=None):

    tabla.setEditTriggers(
        QAbstractItemView.NoEditTriggers
    )

    tabla.setSelectionBehavior(
        QAbstractItemView.SelectRows
    )

    tabla.setSelectionMode(
        QAbstractItemView.SingleSelection
    )

    tabla.setWordWrap(False)

    tabla.setAlternatingRowColors(True)

    tabla.setHorizontalScrollBarPolicy(
        Qt.ScrollBarAsNeeded
    )

    tabla.setVerticalScrollBarPolicy(
        Qt.ScrollBarAsNeeded
    )

    tabla.setSizePolicy(
        QSizePolicy.Expanding,
        QSizePolicy.Expanding
    )

    tabla.setFrameShape(
        QFrame.NoFrame
    )

    tabla.setLineWidth(
        0
    )

    tabla.setMidLineWidth(
        0
    )



    # ========================================================
    # ENCABEZADO VERTICAL / ALTURA DE FILAS
    # ========================================================

    header_vertical = tabla.verticalHeader()

    # IMPORTANTE:
    # Tiene que estar visible para poder agarrar
    # el borde de las filas y cambiar su altura.
    header_vertical.setVisible(True)

    header_vertical.setDefaultSectionSize(34)

    header_vertical.setMinimumSectionSize(20)

    header_vertical.setSectionResizeMode(
        QHeaderView.Interactive
    )

    # ========================================================
    # ENCABEZADO HORIZONTAL / ANCHO DE COLUMNAS
    # ========================================================

    header = tabla.horizontalHeader()

    header.setStretchLastSection(False)

    header.setMinimumSectionSize(60)

    header.setDefaultSectionSize(120)

    header.setFixedHeight(42)

    # Todas las columnas se pueden modificar manualmente
    for i in range(tabla.columnCount()):

        header.setSectionResizeMode(
            i,
            QHeaderView.Interactive
        )

    # ========================================================
    # SIN CONFIGURACIÓN
    # ========================================================

    if not nombre_config:
        return

    settings = QSettings(
        "CotillonPOS",
        "CotillonPOS"
    )

    grupo = f"arqueo_mensual/{nombre_config}"

    # ========================================================
    # RECUPERAR ANCHOS
    # ========================================================

    for i in range(tabla.columnCount()):

        valor = settings.value(
            f"{grupo}/columna_{i}",
            None
        )

        if valor is not None:

            try:

                ancho = int(valor)

                if ancho >= 60:

                    header.resizeSection(
                        i,
                        ancho
                    )

            except (ValueError, TypeError):
                pass

    # ========================================================
    # RECUPERAR ALTURA
    # ========================================================

    altura_fila = settings.value(
        f"{grupo}/altura_fila",
        None
    )

    if altura_fila is not None:

        try:

            altura = int(
                altura_fila
            )

            if altura >= 20:

                header_vertical.setDefaultSectionSize(
                    altura
                )

        except (ValueError, TypeError):
            pass

    # ========================================================
    # GUARDAR ANCHOS
    # ========================================================

    def guardar_tamanos_columnas():

        try:

            for i in range(
                tabla.columnCount()
            ):

                settings.setValue(
                    f"{grupo}/columna_{i}",
                    header.sectionSize(i)
                )

            settings.sync()

        except Exception:
            pass

    # ========================================================
    # GUARDAR ALTURA
    # ========================================================

    def guardar_altura_fila():

        try:

            altura = (
                header_vertical.defaultSectionSize()
            )

            settings.setValue(
                f"{grupo}/altura_fila",
                altura
            )

            settings.sync()

        except Exception:
            pass

    # ========================================================
    # DETECTAR CAMBIOS DE COLUMNAS
    # ========================================================

    header.sectionResized.connect(
        lambda logicalIndex, oldSize, newSize:
            guardar_tamanos_columnas()
    )

    # ========================================================
    # DETECTAR CAMBIOS DE FILAS
    # ========================================================

    header_vertical.sectionResized.connect(
        lambda logicalIndex, oldSize, newSize:
            guardar_altura_fila()
    )
def _ajustar_columnas(tabla, anchos):

    header = tabla.horizontalHeader()

    for columna, ancho in enumerate(anchos):

        if columna >= tabla.columnCount():
            break

        header.resizeSection(
            columna,
            ancho
        )


def _agregar_fila(tabla, valores):

    fila = tabla.rowCount()

    tabla.insertRow(fila)

    for columna, valor in enumerate(valores):

        tabla.setItem(
            fila,
            columna,
            _item(valor)
        )

    return fila
def _agregar_total(tabla, valores):
    """
    Agrega una fila final de TOTAL a la tabla.
    La primera columna muestra TOTAL.
    """

    fila = tabla.rowCount()

    tabla.insertRow(fila)

    for columna, valor in enumerate(valores):

        item = QTableWidgetItem(
            "" if valor is None else str(valor)
        )

        item.setFlags(
            item.flags()
            & ~Qt.ItemIsEditable
        )

        font = item.font()
        font.setBold(True)
        item.setFont(font)

        tabla.setItem(
            fila,
            columna,
            item
        )

    return fila
def _habilitar_ajuste_manual(tabla):

    # ========================================================
    # COLUMNAS
    # ========================================================

    header = tabla.horizontalHeader()

    header.setStretchLastSection(False)

    header.setSectionsMovable(False)

    header.setMinimumSectionSize(60)

    for i in range(tabla.columnCount()):

        header.setSectionResizeMode(
            i,
            QHeaderView.Interactive
        )

    # ========================================================
    # FILAS
    # ========================================================

    vertical = tabla.verticalHeader()

    vertical.setVisible(True)

    vertical.setMinimumSectionSize(20)

    vertical.setDefaultSectionSize(34)

    vertical.setSectionsMovable(False)

    vertical.setSectionResizeMode(
        QHeaderView.Interactive
    )

    # ========================================================
    # TABLA
    # ========================================================

    tabla.setWordWrap(False)

    tabla.setHorizontalScrollBarPolicy(
        Qt.ScrollBarAsNeeded
    )

    tabla.setVerticalScrollBarPolicy(
        Qt.ScrollBarAsNeeded
    )

# ============================================================
# CONTENEDOR REDIMENSIONABLE PARA TABLAS
# ============================================================


class ContenedorTablaRedimensionable(QWidget):

    def __init__(
        self,
        tabla,
        nombre_config,
        parent=None
    ):

        super().__init__(parent)

        self.tabla = tabla
        self.nombre_config = nombre_config

        # ====================================================
        # CONFIGURACIÓN DEL CONTENEDOR
        # ====================================================

        self.setMinimumSize(
            300,
            150
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        # ====================================================
        # LAYOUT
        # ====================================================

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(0)

        layout.addWidget(
            self.tabla
        )
        layout.setStretch(
            0,
            1
        )

        self.tabla.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        # ====================================================
        # TAMAÑO INICIAL
        # ====================================================

        self.setMinimumSize(
            300,
            150
        )
        # ====================================================
        # CONFIGURACIÓN PERSISTENTE
        # ====================================================

        settings = QSettings(
            "CotillonPOS",
            "CotillonPOS"
        )

        grupo = (
            "arqueo_mensual/"
            + nombre_config
            + "/contenedor"
        )

        ancho = settings.value(
            f"{grupo}/ancho",
            None
        )

        alto = settings.value(
            f"{grupo}/alto",
            None
        )

        try:

            if ancho is not None:
                ancho = int(ancho)

            if alto is not None:
                alto = int(alto)

            if (
                ancho is not None
                and alto is not None
                and ancho >= 300
                and alto >= 150
            ):

                self.resize(
                    ancho,
                    alto
                )

        except (
            ValueError,
            TypeError
        ):

            pass

        # ====================================================
        # BORDE / ASA DE REDIMENSIONADO
        # ====================================================

        self.grip = QSizeGrip(
            self
        )

        self.grip.setFixedSize(
            20,
            20
        )

        self.grip.setStyleSheet(
            """
            QSizeGrip {
                background: transparent;
            }
            """
        )

        self.grip.raise_()

        # ====================================================
        # GUARDAR CONFIGURACIÓN
        # ====================================================

        self._settings = settings
        self._grupo = grupo

    def resizeEvent(self, event):

        super().resizeEvent(
            event
        )

        # ====================================================
        # POSICIONAR EL ASA
        # ====================================================

        self.grip.move(
            self.width()
            - self.grip.width(),
            self.height()
            - self.grip.height()
        )

        self.grip.raise_()

        # ====================================================
        # GUARDAR TAMAÑO
        # ====================================================

        try:

            self._settings.setValue(
                f"{self._grupo}/ancho",
                self.width()
            )

            self._settings.setValue(
                f"{self._grupo}/alto",
                self.height()
            )

            self._settings.sync()

        except Exception:

            pass


# ============================================================
# ARQUEO MENSUAL
# ============================================================

class ArqueoMensual(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        init_db()

        self.setWindowTitle(
            "📅 Arqueo mensual"
        )

        self.setMinimumSize(
            1100,
            720
        )

        self.resize(
            1400,
            900
        )

        # ====================================================
        # ESTILO COMPLETO DEL ARQUEO
        # ====================================================

        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
                color: #0f172a;
            }

            QDialog > QWidget {
                background-color: #f8fafc;
                color: #0f172a;
            }

            QWidget {
                color: #0f172a;
            }

            QLabel {
                color: #0f172a;
                background-color: transparent;
            }

            QScrollArea {
                background-color: #f8fafc;
                border: none;
            }

            QScrollArea > QWidget {
                background-color: #f8fafc;
            }

            QScrollArea > QWidget > QWidget {
                background-color: #f8fafc;
            }

            /* =================================================
               GROUPBOX
               ================================================= */

            QGroupBox {
                background-color: transparent;
                color: #0f172a;

                border: none;
                border-radius: 0;

                margin-top: 26px;
                padding: 28px 0px 0px 0px;

                font-size: 14px;
                font-weight: 800;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;

                background-color: #ffffff;
                color: #0f172a;

                left: 14px;
                top: -10px;

                padding: 4px 10px;

                border: 1px solid #cbd5e1;
                border-radius: 7px;

                font-size: 14px;
                font-weight: 900;
            }
            /* =================================================
               COMBOS
               ================================================= */

            QComboBox {
                background-color: #ffffff;
                color: #0f172a;

                border: 1px solid #cbd5e1;
                border-radius: 8px;

                padding: 8px 12px;

                min-width: 120px;
                min-height: 18px;
            }

            QComboBox:hover {
                border: 1px solid #94a3b8;
            }

            QComboBox:focus {
                border: 1px solid #0ea5e9;
            }

            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #0f172a;

                selection-background-color: #dbeafe;
                selection-color: #0f172a;

                border: 1px solid #cbd5e1;
            }

            /* =================================================
               TABLAS
               ================================================= */

            QTableWidget {
                background-color: #ffffff;
                color: #0f172a;

                alternate-background-color: #f8fafc;

                border: 1px solid #cbd5e1;
                border-radius: 8px;

                gridline-color: #e2e8f0;

                selection-background-color: #dbeafe;
                selection-color: #0f172a;
            }

            QTableWidget::item {
                background-color: #ffffff;
                color: #0f172a;

                padding: 7px;
            }

            QTableWidget::item:alternate {
                background-color: #f8fafc;
            }

            QTableWidget::item:selected {
                background-color: #dbeafe;
                color: #0f172a;
            }

            QHeaderView {
                background-color: #e2e8f0;
            }

            QHeaderView::section {
                background-color: #e2e8f0;
                color: #0f172a;

                padding: 8px 7px;

                border: 0;
                border-right: 1px solid #cbd5e1;
                border-bottom: 1px solid #cbd5e1;

                font-size: 12px;
                font-weight: 900;

                min-height: 28px;
            }

            /* =================================================
               BOTONES
               ================================================= */

            QPushButton {
                border: 0;
                border-radius: 8px;

                padding: 9px 16px;

                color: #ffffff;
                font-weight: 800;
            }

            QPushButton:hover {
                opacity: 0.90;
            }

            /* =================================================
               SCROLLBARS
               ================================================= */

            QScrollBar:vertical {
                background: #f1f5f9;
                width: 12px;
                margin: 0;
                border: none;
            }

            QScrollBar::handle:vertical {
                background: #94a3b8;
                border-radius: 6px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background: #64748b;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }

            QScrollBar:horizontal {
                background: #f1f5f9;
                height: 12px;
                margin: 0;
                border: none;
            }

            QScrollBar::handle:horizontal {
                background: #94a3b8;
                border-radius: 6px;
                min-width: 30px;
            }

            QScrollBar::handle:horizontal:hover {
                background: #64748b;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0;
            }
        """)

        # ====================================================
        # CONTENEDOR PRINCIPAL
        # ====================================================

        exterior = QVBoxLayout(self)

        exterior.setContentsMargins(
            15,
            15,
            15,
            15
        )

        exterior.setSpacing(10)

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        scroll.setFrameShape(
            QFrame.NoFrame
        )

        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #f8fafc;
                border: none;
            }

            QScrollArea QWidget {
                background-color: #f8fafc;
            }
        """)

        scroll.viewport().setStyleSheet(
            "background-color:#f8fafc;"
        )

        contenido = QWidget()

        contenido.setObjectName(
            "contenidoArqueo"
        )

        contenido.setStyleSheet("""
            QWidget#contenidoArqueo {
                background-color: #f8fafc;
            }
        """)

        contenido.setMinimumWidth(
            1000
        )

        root = QVBoxLayout(
            contenido
        )

        root.setContentsMargins(
            20,
            20,
            100,
            20
        )

        root.setSpacing(18)

        scroll.setWidget(
            contenido
        )

        exterior.addWidget(
            scroll,
            1
        )

        # ====================================================
        # TITULO
        # ====================================================

        titulo = QLabel(
            "📅 ARQUEO MENSUAL"
        )

        titulo.setStyleSheet("""
            QLabel {
                font-size: 30px;
                font-weight: 900;
                color: #0f172a;
                background: transparent;
            }
        """)

        root.addWidget(
            titulo
        )

        subtitulo = QLabel(
            "Resumen completo de ventas, medios de pago, "
            "movimientos de caja y arqueos realizados."
        )

        subtitulo.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #64748b;
                background: transparent;
            }
        """)

        root.addWidget(
            subtitulo
        )

        # ====================================================
        # FILTROS
        # ====================================================

        filtros_box = QFrame()

        filtros_box.setObjectName(
            "filtrosBox"
        )

        filtros_box.setStyleSheet("""
            QFrame#filtrosBox {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
            }

            QFrame#filtrosBox QLabel {
                background-color: transparent;
                color: #0f172a;
            }
        """)

        filtros = QHBoxLayout(
            filtros_box
        )

        filtros.setContentsMargins(
            15,
            12,
            15,
            12
        )

        filtros.setSpacing(10)

        lbl_mes = QLabel(
            "Mes:"
        )

        lbl_mes.setStyleSheet(
            """
            font-weight:800;
            color:#0f172a;
            background:transparent;
            """
        )

        filtros.addWidget(
            lbl_mes
        )

        self.mes = QComboBox()

        nombres = [
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        ]

        for numero, nombre in enumerate(
            nombres,
            1
        ):

            self.mes.addItem(
                nombre,
                numero
            )

        filtros.addWidget(
            self.mes
        )

        lbl_anio = QLabel(
            "Año:"
        )

        lbl_anio.setStyleSheet(
            """
            font-weight:800;
            color:#0f172a;
            background:transparent;
            """
        )

        filtros.addWidget(
            lbl_anio
        )

        self.anio = QComboBox()

        anio_actual = (
            datetime.datetime.now().year
        )

        for anio in range(
            anio_actual - 10,
            anio_actual + 2
        ):

            self.anio.addItem(
                str(anio),
                anio
            )

        filtros.addWidget(
            self.anio
        )

        self.mes.setCurrentIndex(
            datetime.datetime.now().month - 1
        )

        self.anio.setCurrentText(
            str(anio_actual)
        )

        actualizar = QPushButton(
            "🔄 Actualizar"
        )

        actualizar.setStyleSheet("""
            QPushButton {
                background-color: #0ea5e9;
                color: white;
            }

            QPushButton:hover {
                background-color: #0284c7;
            }
        """)

        actualizar.clicked.connect(
            self.generar
        )

        filtros.addWidget(
            actualizar
        )

        filtros.addStretch()

        root.addWidget(
            filtros_box
        )

        # ====================================================
        # RESUMEN
        # ====================================================

        grupo_resumen = QGroupBox(
            "📊 Resumen general del mes"
        )

        grupo_resumen.setMinimumHeight(
            350
        )

        self.resumen_layout = QGridLayout(
            grupo_resumen
        )

        self.resumen_layout.setContentsMargins(
            14,
            28,
            14,
            14
        )

        self.resumen_layout.setHorizontalSpacing(
            10
        )

        self.resumen_layout.setVerticalSpacing(
            10
        )

        self.resumen_widgets = {}

        campos = [

            (
                "ventas",
                "💰 Ventas totales",
                "$ 0,00"
            ),

            (
                "cantidad",
                "🧾 Cantidad de ventas",
                "0"
            ),

            (
                "efectivo",
                "💵 Efectivo",
                "$ 0,00"
            ),

            (
                "transferencia",
                "🏦 Transferencias",
                "$ 0,00"
            ),

            (
                "tarjeta",
                "💳 Tarjetas",
                "$ 0,00"
            ),

            (
                "cuenta",
                "👤 Ventas a cuenta",
                "$ 0,00"
            ),

            (
                "total_medios",
                "🧮 Total medios de pago",
                "$ 0,00"
            ),

            (
                "descuentos",
                "🏷️ Descuentos",
                "$ 0,00"
            ),

            (
                "ingresos_caja",
                "➕ Ingresos de caja",
                "$ 0,00"
            ),

            (
                "egresos_caja",
                "➖ Egresos de caja",
                "$ 0,00"
            ),

            (
                "ingresos_total",
                "📈 Ingresos totales",
                "$ 0,00"
            ),

            (
                "resultado",
                "📊 Resultado neto",
                "$ 0,00"
            ),

        ]

        for i, (
            clave,
            titulo_card,
            valor_inicial
        ) in enumerate(campos):

            frame = QFrame()

            frame.setObjectName(
                "resumenCard"
            )

            frame.setMinimumHeight(
                86
            )

            frame.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed
            )

            frame.setStyleSheet("""
                QFrame#resumenCard {
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 12px;
                }

                QFrame#resumenCard QLabel {
                    background-color: transparent;
                    color: #0f172a;
                }
            """)

            lay = QVBoxLayout(
                frame
            )

            lay.setContentsMargins(
                12,
                9,
                12,
                9
            )

            lay.setSpacing(
                3
            )

            lbl = QLabel(
                titulo_card
            )

            lbl.setStyleSheet("""
                QLabel {
                    color: #64748b;
                    background: transparent;
                    font-weight: 700;
                    font-size: 12px;
                }
            """)

            valor = QLabel(
                valor_inicial
            )

            valor.setStyleSheet("""
                QLabel {
                    font-size: 19px;
                    font-weight: 900;
                    color: #0f172a;
                    background: transparent;
                }
            """)

            valor.setMinimumWidth(
                180
            )

            valor.setMinimumHeight(
                26
            )

            lay.addWidget(
                lbl
            )

            lay.addWidget(
                valor
            )

            self.resumen_widgets[
                clave
            ] = valor

            fila = i // 4
            columna = i % 4

            self.resumen_layout.addWidget(
                frame,
                fila,
                columna
            )

        for columna in range(4):

            self.resumen_layout.setColumnStretch(
                columna,
                1
            )

        root.addWidget(
            grupo_resumen
        )

        # ====================================================
        # TABLA DIARIA
        # ====================================================

        grupo_dias = QGroupBox(
            "📆 Detalle diario"
        )

        grupo_dias.setMinimumHeight(
            320
        )

        lay_dias = QVBoxLayout(
            grupo_dias
        )

        lay_dias.setContentsMargins(
            0,
            28,
            0,
            0
        )

        lay_dias.setSpacing(
            0
        )

        self.tabla_dias = QTableWidget()

        self.tabla_dias.setColumnCount(
            9
        )

        self.tabla_dias.setHorizontalHeaderLabels(
            [
                "Fecha",
                "Ventas",
                "Cantidad",
                "Efectivo",
                "Transferencias",
                "Tarjetas",
                "Cuenta",
                "Total medios",
                "Diferencia",
            ]
        )

        _configurar_tabla(
            self.tabla_dias,
            "detalle_diario"
        )

        _ajustar_columnas(
            self.tabla_dias,
            [
                110,
                145,
                95,
                145,
                155,
                135,
                135,
                150,
                135,
            ]
        )

        _habilitar_ajuste_manual(
            self.tabla_dias
        )

        self.tabla_dias.setMinimumSize(
            0,
            0
        )

        self.tabla_dias.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.tabla_dias.setFrameShape(
            QFrame.NoFrame
        )

        self.tabla_dias.setLineWidth(
            0
        )

        lay_dias.addWidget(
            self.tabla_dias,
            1
        )

        root.addWidget(
            grupo_dias
        )


        # ====================================================
        # MOVIMIENTOS DE CAJA
        # ====================================================

        grupo_caja = QGroupBox(
            "💰 Movimientos de caja del mes"
        )

        grupo_caja.setMinimumHeight(
            320
        )

        lay_caja = QVBoxLayout(
            grupo_caja
        )

        lay_caja.setContentsMargins(
            0,
            28,
            0,
            0
        )

        lay_caja.setSpacing(
            0
        )

        self.tabla_caja = QTableWidget()

        self.tabla_caja.setColumnCount(
            4
        )

        self.tabla_caja.setHorizontalHeaderLabels(
            [
                "Fecha",
                "Tipo",
                "Importe",
                "Concepto",
            ]
        )

        _configurar_tabla(
            self.tabla_caja,
            "movimientos_caja"
        )

        _ajustar_columnas(
            self.tabla_caja,
            [
                160,
                150,
                160,
                600,
            ]
        )

        _habilitar_ajuste_manual(
            self.tabla_caja
        )

        self.tabla_caja.setMinimumSize(
            0,
            0
        )

        self.tabla_caja.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.tabla_caja.setFrameShape(
            QFrame.NoFrame
        )

        self.tabla_caja.setLineWidth(
            0
        )

        lay_caja.addWidget(
            self.tabla_caja,
            1
        )

        root.addWidget(
            grupo_caja
        )


        # ====================================================
        # ARQUEOS REALIZADOS
        # ====================================================

        grupo_arqueos = QGroupBox(
            "🧾 Arqueos realizados en el mes"
        )

        grupo_arqueos.setMinimumHeight(
            320
        )

        lay_arqueos = QVBoxLayout(
            grupo_arqueos
        )

        lay_arqueos.setContentsMargins(
            0,
            28,
            0,
            0
        )

        lay_arqueos.setSpacing(
            0
        )

        self.tabla_arqueos = QTableWidget()

        self.tabla_arqueos.setColumnCount(
            8
        )

        self.tabla_arqueos.setHorizontalHeaderLabels(
            [
                "Fecha",
                "Apertura",
                "Esperado",
                "Real",
                "Diferencia",
                "Ventas",
                "Efectivo",
                "Cantidad",
            ]
        )

        _configurar_tabla(
            self.tabla_arqueos,
            "arqueos_realizados"
        )

        _ajustar_columnas(
            self.tabla_arqueos,
            [
                160,
                130,
                150,
                150,
                150,
                150,
                150,
                100,
            ]
        )

        _habilitar_ajuste_manual(
            self.tabla_arqueos
        )

        self.tabla_arqueos.setMinimumSize(
            0,
            0
        )

        self.tabla_arqueos.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.tabla_arqueos.setFrameShape(
            QFrame.NoFrame
        )

        self.tabla_arqueos.setLineWidth(
            0
        )

        lay_arqueos.addWidget(
            self.tabla_arqueos,
            1
        )

        root.addWidget(
            grupo_arqueos
        )

        # ====================================================
        # BOTONES
        # ====================================================

        botones = QHBoxLayout()

        guardar_csv = QPushButton(
            "💾 Guardar CSV"
        )

        guardar_csv.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: white;
            }

            QPushButton:hover {
                background-color: #15803d;
            }
        """)

        guardar_csv.clicked.connect(
            self.guardar_csv
        )

        botones.addWidget(
            guardar_csv
        )

        guardar_pdf = QPushButton(
            "📄 Guardar PDF"
        )

        guardar_pdf.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
            }

            QPushButton:hover {
                background-color: #b91c1c;
            }
        """)

        guardar_pdf.clicked.connect(
            self.guardar_pdf
        )

        botones.addWidget(
            guardar_pdf
        )

        imprimir = QPushButton(
            "🖨️ Imprimir"
        )

        imprimir.setStyleSheet("""
            QPushButton {
                background-color: #475569;
                color: white;
            }

            QPushButton:hover {
                background-color: #334155;
            }
        """)

        imprimir.clicked.connect(
            self.imprimir
        )

        botones.addWidget(
            imprimir
        )

        botones.addStretch()

        cerrar = QPushButton(
            "Cerrar"
        )

        cerrar.setStyleSheet("""
            QPushButton {
                background-color: #e2e8f0;
                color: #334155;
            }

            QPushButton:hover {
                background-color: #cbd5e1;
            }
        """)

        cerrar.clicked.connect(
            self.close
        )

        botones.addWidget(
            cerrar
        )

        exterior.addLayout(
            botones
        )

        # ====================================================
        # PRIMERA CARGA
        # ====================================================

        self.generar()

    # ========================================================
    # RANGO
    # ========================================================

    def _rango_mes(self):

        anio = int(
            self.anio.currentData()
        )

        mes = int(
            self.mes.currentData()
        )

        inicio = datetime.date(
            anio,
            mes,
            1
        )

        if mes == 12:

            siguiente = datetime.date(
                anio + 1,
                1,
                1
            )

        else:

            siguiente = datetime.date(
                anio,
                mes + 1,
                1
            )

        return (
            inicio.isoformat(),
            siguiente.isoformat()
        )

    # ========================================================
    # MEDIOS DE PAGO
    # ========================================================

    def _medios_venta(
        self,
        data,
        columnas,
        total
    ):

        efectivo = _numero(
            data.get("pago_efectivo")
        )

        transferencia = _numero(
            data.get("pago_transferencia")
        )

        tarjeta = _numero(
            data.get("pago_tarjeta")
        )

        cuenta = _numero(
            data.get("pago_cuenta")
        )

        suma = (
            efectivo
            + transferencia
            + tarjeta
            + cuenta
        )

        forma = str(
            data.get("forma_pago")
            or ""
        ).strip().lower()

        if abs(suma) < 0.000001:

            if forma in (
                "efectivo",
            ):

                efectivo = total

            elif forma in (
                "transferencia",
                "transferencia bancaria",
            ):

                transferencia = total

            elif forma in (
                "tarjeta",
                "credito",
                "crédito",
                "debito",
                "débito",
            ):

                tarjeta = total

            elif forma in (
                "cuenta",
                "fiado",
                "credito cuenta",
                "crédito cuenta",
            ):

                cuenta = total

        return (
            efectivo,
            transferencia,
            tarjeta,
            cuenta
        )

    # ========================================================
    # GENERAR
    # ========================================================

    def generar(self):

        inicio, siguiente = (
            self._rango_mes()
        )

        conexion = sqlite3.connect(
            BASE_DATOS
        )

        conexion.row_factory = sqlite3.Row

        q = conexion.cursor()

        try:

            columnas_ventas = (
                _tabla_columnas(
                    q,
                    "ventas"
                )
            )

            columnas_caja = (
                _tabla_columnas(
                    q,
                    "movimientos_caja"
                )
            )

            columnas_arqueos = (
                _tabla_columnas(
                    q,
                    "arqueos"
                )
            )

            # =================================================
            # VENTAS
            # =================================================

            estado_sql = ""

            if "estado" in columnas_ventas:

                estado_sql = (
                    " AND COALESCE(estado, "
                    "'ACTIVA') = 'ACTIVA' "
                )

            venta_rows = q.execute(
                f"""
                SELECT *
                FROM ventas
                WHERE fecha >= ?
                  AND fecha < ?
                  {estado_sql}
                ORDER BY fecha ASC
                """,
                (
                    inicio,
                    siguiente
                )
            ).fetchall()

            total_ventas = 0.0
            cantidad = 0

            efectivo = 0.0
            transferencia = 0.0
            tarjeta = 0.0
            cuenta = 0.0

            descuentos = 0.0

            diarios = {}

            for row in venta_rows:

                data = dict(row)

                fecha = str(
                    data.get("fecha")
                    or ""
                )[:10]

                total = _numero(
                    data.get("total")
                )

                cantidad += 1

                total_ventas += total

                descuentos += _numero(
                    data.get("descuento")
                )

                (
                    ef,
                    tr,
                    ta,
                    cu
                ) = self._medios_venta(
                    data,
                    columnas_ventas,
                    total
                )

                efectivo += ef
                transferencia += tr
                tarjeta += ta
                cuenta += cu

                if fecha not in diarios:

                    diarios[fecha] = {
                        "ventas": 0.0,
                        "cantidad": 0,
                        "efectivo": 0.0,
                        "transferencia": 0.0,
                        "tarjeta": 0.0,
                        "cuenta": 0.0,
                    }

                diarios[fecha][
                    "ventas"
                ] += total

                diarios[fecha][
                    "cantidad"
                ] += 1

                diarios[fecha][
                    "efectivo"
                ] += ef

                diarios[fecha][
                    "transferencia"
                ] += tr

                diarios[fecha][
                    "tarjeta"
                ] += ta

                diarios[fecha][
                    "cuenta"
                ] += cu

            # =================================================
            # CAJA
            # =================================================

            ingresos_caja = 0.0
            egresos_caja = 0.0

            movimientos = []

            if columnas_caja:

                rows_caja = q.execute(
                    """
                    SELECT *
                    FROM movimientos_caja
                    WHERE fecha >= ?
                      AND fecha < ?
                    ORDER BY fecha ASC
                    """,
                    (
                        inicio,
                        siguiente
                    )
                ).fetchall()

                for row in rows_caja:

                    data = dict(row)

                    importe = _numero(
                        data.get("importe")
                    )

                    tipo_original = (
                        data.get("tipo")
                        or ""
                    )

                    tipo = str(
                        tipo_original
                    ).strip().lower()

                    concepto = (
                        data.get("concepto")
                        or data.get("descripcion")
                        or ""
                    )

                    if tipo in (
                        "ingreso",
                        "entrada",
                        "ingresos",
                        "entrada de dinero",
                    ):

                        ingresos_caja += importe

                    elif tipo in (
                        "egreso",
                        "salida",
                        "egresos",
                        "salida de dinero",
                    ):

                        egresos_caja += importe

                    movimientos.append({
                        "fecha": data.get(
                            "fecha"
                        ) or "",
                        "tipo": tipo_original,
                        "importe": importe,
                        "concepto": concepto,
                    })

                    fecha_mov = str(
                        data.get("fecha")
                        or ""
                    )[:10]

                    if fecha_mov:

                        if fecha_mov not in diarios:

                            diarios[fecha_mov] = {
                                "ventas": 0.0,
                                "cantidad": 0,
                                "efectivo": 0.0,
                                "transferencia": 0.0,
                                "tarjeta": 0.0,
                                "cuenta": 0.0,
                            }

            # =================================================
            # RESULTADOS
            # =================================================

            total_medios = (
                efectivo
                + transferencia
                + tarjeta
                + cuenta
            )

            ingresos_total = (
                total_ventas
                + ingresos_caja
            )

            resultado = (
                ingresos_total
                - egresos_caja
            )

            # =================================================
            # RESUMEN
            # =================================================

            self.resumen_widgets[
                "ventas"
            ].setText(
                _moneda(total_ventas)
            )

            self.resumen_widgets[
                "cantidad"
            ].setText(
                f"{cantidad:,}".replace(
                    ",",
                    "."
                )
            )

            self.resumen_widgets[
                "efectivo"
            ].setText(
                _moneda(efectivo)
            )

            self.resumen_widgets[
                "transferencia"
            ].setText(
                _moneda(transferencia)
            )

            self.resumen_widgets[
                "tarjeta"
            ].setText(
                _moneda(tarjeta)
            )

            self.resumen_widgets[
                "cuenta"
            ].setText(
                _moneda(cuenta)
            )

            self.resumen_widgets[
                "total_medios"
            ].setText(
                _moneda(total_medios)
            )

            self.resumen_widgets[
                "descuentos"
            ].setText(
                _moneda(descuentos)
            )

            self.resumen_widgets[
                "ingresos_caja"
            ].setText(
                _moneda(ingresos_caja)
            )

            self.resumen_widgets[
                "egresos_caja"
            ].setText(
                _moneda(egresos_caja)
            )

            self.resumen_widgets[
                "ingresos_total"
            ].setText(
                _moneda(ingresos_total)
            )

            self.resumen_widgets[
                "resultado"
            ].setText(
                _moneda(resultado)
            )

             # =================================================
            # TABLA DIARIA
            # =================================================

            self.tabla_dias.setRowCount(0)

            total_ventas_dias = 0.0
            total_cantidad_dias = 0
            total_efectivo_dias = 0.0
            total_transferencia_dias = 0.0
            total_tarjeta_dias = 0.0
            total_cuenta_dias = 0.0
            total_medios_dias = 0.0
            total_diferencia_dias = 0.0

            for fecha in sorted(
                diarios.keys()
            ):

                d = diarios[fecha]

                total_dia = (
                    d["efectivo"]
                    + d["transferencia"]
                    + d["tarjeta"]
                    + d["cuenta"]
                )

                diferencia = (
                    d["ventas"]
                    - total_dia
                )

                total_ventas_dias += d["ventas"]
                total_cantidad_dias += d["cantidad"]
                total_efectivo_dias += d["efectivo"]
                total_transferencia_dias += d["transferencia"]
                total_tarjeta_dias += d["tarjeta"]
                total_cuenta_dias += d["cuenta"]
                total_medios_dias += total_dia
                total_diferencia_dias += diferencia

                valores = [
                    _fecha_bonita(fecha),
                    _moneda(d["ventas"]),
                    f'{d["cantidad"]:,}'.replace(
                        ",",
                        "."
                    ),
                    _moneda(
                        d["efectivo"]
                    ),
                    _moneda(
                        d["transferencia"]
                    ),
                    _moneda(
                        d["tarjeta"]
                    ),
                    _moneda(
                        d["cuenta"]
                    ),
                    _moneda(
                        total_dia
                    ),
                    _moneda(
                        diferencia
                    ),
                ]

                _agregar_fila(
                    self.tabla_dias,
                    valores
                )

            # TOTAL DETALLE DIARIO
            _agregar_total(
                self.tabla_dias,
                [
                    "TOTAL",
                    _moneda(total_ventas_dias),
                    f'{total_cantidad_dias:,}'.replace(
                        ",",
                        "."
                    ),
                    _moneda(total_efectivo_dias),
                    _moneda(total_transferencia_dias),
                    _moneda(total_tarjeta_dias),
                    _moneda(total_cuenta_dias),
                    _moneda(total_medios_dias),
                    _moneda(total_diferencia_dias),
                ]
            )

            # =================================================
            # TABLA CAJA
            # =================================================

            self.tabla_caja.setRowCount(0)

            total_movimientos_caja = 0.0

            for mov in movimientos:

                importe = _numero(
                    mov["importe"]
                )

                total_movimientos_caja += importe

                valores = [
                    _fecha_bonita(
                        mov["fecha"]
                    ),
                    mov["tipo"],
                    _moneda(
                        importe
                    ),
                    mov["concepto"],
                ]

                _agregar_fila(
                    self.tabla_caja,
                    valores
                )

            # TOTAL MOVIMIENTOS DE CAJA
            _agregar_total(
                self.tabla_caja,
                [
                    "TOTAL",
                    "",
                    _moneda(
                        total_movimientos_caja
                    ),
                    "",
                ]
            )

            # =================================================
            # ARQUEOS REALIZADOS
            # =================================================

            self.tabla_arqueos.setRowCount(0)

            total_apertura_arqueos = 0.0
            total_esperado_arqueos = 0.0
            total_real_arqueos = 0.0
            total_diferencia_arqueos = 0.0
            total_ventas_arqueos = 0.0
            total_efectivo_arqueos = 0.0
            total_cantidad_arqueos = 0

            if columnas_arqueos:

                rows_arqueos = q.execute(
                    """
                    SELECT *
                    FROM arqueos
                    WHERE fecha >= ?
                      AND fecha < ?
                    ORDER BY fecha ASC
                    """,
                    (
                        inicio,
                        siguiente
                    )
                ).fetchall()

                for row in rows_arqueos:

                    data = dict(row)

                    fecha = (
                        data.get("fecha")
                        or data.get("fecha_arqueo")
                        or ""
                    )

                    apertura = _numero(
                        data.get(
                            "apertura"
                        )
                    )

                    esperado = _numero(
                        data.get(
                            "efectivo_esperado"
                        )
                    )

                    if esperado == 0:

                        esperado = _numero(
                            data.get(
                                "esperado"
                            )
                        )

                    real = _numero(
                        data.get(
                            "efectivo_real"
                        )
                    )

                    if real == 0:

                        real = _numero(
                            data.get(
                                "real"
                            )
                        )

                    diferencia = _numero(
                        data.get(
                            "diferencia"
                        )
                    )

                    if diferencia == 0:

                        diferencia = (
                            real
                            - esperado
                        )

                    ventas_arqueo = _numero(
                        data.get(
                            "ventas"
                        )
                    )

                    efectivo_arqueo = _numero(
                        data.get(
                            "efectivo"
                        )
                    )

                    cantidad_arqueo = int(
                        _numero(
                            data.get(
                                "cantidad_ventas"
                            )
                            or data.get(
                                "cantidad"
                            )
                        )
                    )

                    total_apertura_arqueos += apertura
                    total_esperado_arqueos += esperado
                    total_real_arqueos += real
                    total_diferencia_arqueos += diferencia
                    total_ventas_arqueos += ventas_arqueo
                    total_efectivo_arqueos += efectivo_arqueo
                    total_cantidad_arqueos += cantidad_arqueo

                    valores = [

                        _fecha_bonita(
                            fecha
                        ),

                        _moneda(
                            apertura
                        ),

                        _moneda(
                            esperado
                        ),

                        _moneda(
                            real
                        ),

                        _moneda(
                            diferencia
                        ),

                        _moneda(
                            ventas_arqueo
                        ),

                        _moneda(
                            efectivo_arqueo
                        ),

                        str(
                            cantidad_arqueo
                        ),

                    ]

                    _agregar_fila(
                        self.tabla_arqueos,
                        valores
                    )

            # TOTAL ARQUEOS
            _agregar_total(
                self.tabla_arqueos,
                [
                    "TOTAL",
                    _moneda(
                        total_apertura_arqueos
                    ),
                    _moneda(
                        total_esperado_arqueos
                    ),
                    _moneda(
                        total_real_arqueos
                    ),
                    _moneda(
                        total_diferencia_arqueos
                    ),
                    _moneda(
                        total_ventas_arqueos
                    ),
                    _moneda(
                        total_efectivo_arqueos
                    ),
                    str(
                        total_cantidad_arqueos
                    ),
                ]
            )


        except Exception as e:

            QMessageBox.critical(
                self,
                "Error en arqueo mensual",
                "No se pudo generar el arqueo mensual:\n\n"
                + str(e),
            )

        finally:

            conexion.close()

    # ========================================================
    # TITULO
    # ========================================================

    def _titulo_reporte(self):

        nombres = [
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        ]

        mes = int(
            self.mes.currentData()
        )

        anio = int(
            self.anio.currentData()
        )

        return (
            f"{nombres[mes - 1]} {anio}"
        )

    # ========================================================
    # HTML TABLA
    # ========================================================

    def _html_tabla(self, tabla):

        encabezados = []

        for columna in range(
            tabla.columnCount()
        ):

            encabezados.append(
                tabla.horizontalHeaderItem(
                    columna
                ).text()
            )

        html_tabla = (
            "<table>"
            "<tr>"
        )

        for encabezado in encabezados:

            html_tabla += (
                "<th>"
                + html.escape(
                    encabezado
                )
                + "</th>"
            )

        html_tabla += "</tr>"

        for fila in range(
            tabla.rowCount()
        ):

            html_tabla += "<tr>"

            for columna in range(
                tabla.columnCount()
            ):

                item = tabla.item(
                    fila,
                    columna
                )

                texto = (
                    item.text()
                    if item
                    else ""
                )

                html_tabla += (
                    "<td>"
                    + html.escape(
                        texto
                    )
                    + "</td>"
                )

            html_tabla += "</tr>"

        html_tabla += "</table>"

        return html_tabla

    # ========================================================
    # HTML REPORTE
    # ========================================================

    def _html_reporte(self):

        titulo = self._titulo_reporte()

        etiquetas = {

            "ventas":
                "Ventas totales",

            "cantidad":
                "Cantidad de ventas",

            "efectivo":
                "Efectivo",

            "transferencia":
                "Transferencias",

            "tarjeta":
                "Tarjetas",

            "cuenta":
                "Ventas a cuenta",

            "total_medios":
                "Total medios de pago",

            "descuentos":
                "Descuentos",

            "ingresos_caja":
                "Ingresos de caja",

            "egresos_caja":
                "Egresos de caja",

            "ingresos_total":
                "Ingresos totales",

            "resultado":
                "Resultado neto",
        }

        filas = ""

        for clave, widget in (
            self.resumen_widgets.items()
        ):

            filas += (
                "<tr>"
                "<td><b>"
                + html.escape(
                    etiquetas.get(
                        clave,
                        clave
                    )
                )
                + "</b></td>"
                "<td>"
                + html.escape(
                    widget.text()
                )
                + "</td>"
                "</tr>"
            )

        return f"""
        <html>
        <head>
        <meta charset="utf-8">

        <style>

        body {{
            font-family: Arial;
            color: #0f172a;
            font-size: 10px;
        }}

        h1 {{
            font-size: 22px;
        }}

        h2 {{
            font-size: 16px;
            margin-top: 20px;
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 18px;
        }}

        th {{
            background: #e2e8f0;
            border: 1px solid #94a3b8;
            padding: 6px;
            font-weight: bold;
        }}

        td {{
            border: none;
            padding: 5px;
        }}

        .cabecera {{
            font-size: 11px;
            color: #64748b;
        }}

        </style>

        </head>

        <body>

        <h1>
            📅 ARQUEO MENSUAL - {html.escape(titulo)}
        </h1>

        <p class="cabecera">
            Generado:
            {datetime.datetime.now().strftime(
                "%d/%m/%Y %H:%M"
            )}
        </p>

        <h2>
            📊 Resumen general
        </h2>

        <table>

            <tr>
                <th>Concepto</th>
                <th>Total</th>
            </tr>

            {filas}

        </table>

        <h2>
            📆 Detalle diario
        </h2>

        {self._html_tabla(
            self.tabla_dias
        )}

        <h2>
            💰 Movimientos de caja
        </h2>

        {self._html_tabla(
            self.tabla_caja
        )}

        <h2>
            🧾 Arqueos realizados
        </h2>

        {self._html_tabla(
            self.tabla_arqueos
        )}

        </body>
        </html>
        """

    # ========================================================
    # GUARDAR PDF
    # ========================================================

    # ========================================================
    # GUARDAR PDF
    # ========================================================

    def guardar_pdf(self):

        nombre = (
            f"arqueo_"
            f"{self.anio.currentData()}_"
            f"{int(self.mes.currentData()):02d}.pdf"
        )

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar arqueo mensual",
            nombre,
            "PDF (*.pdf)"
        )

        if not ruta:
            return

        if not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"

        try:

            # ------------------------------------------------
            # PDF NATIVO DE QT
            # ------------------------------------------------

            writer = QPdfWriter(ruta)

            writer.setResolution(96)

            try:
                writer.setPageSize(
                    QPageSize(
                        QPageSize.A4
                    )
                )
            except Exception:
                pass

            # ------------------------------------------------
            # DOCUMENTO
            # ------------------------------------------------

            doc = QTextDocument()

            doc.setDocumentMargin(20)

            doc.setDefaultStyleSheet("""
                body {
                    font-family: Arial;
                    color: #0f172a;
                    font-size: 9pt;
                }

                h1 {
                    font-size: 20pt;
                    margin-bottom: 10px;
                }

                h2 {
                    font-size: 13pt;
                    margin-top: 18px;
                    margin-bottom: 8px;
                }

                table {
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 14px;
                }

                th {
                    background-color: #e2e8f0;
                    color: #0f172a;
                    border: 1px solid #94a3b8;
                    padding: 5px;
                    font-weight: bold;
                }

                td {
                    border: 1px solid #cbd5e1;
                    padding: 4px;
                }

                .cabecera {
                    color: #64748b;
                    font-size: 9pt;
                }
            """)

            doc.setHtml(
                self._html_reporte()
            )

            # ------------------------------------------------
            # AJUSTAR DOCUMENTO AL ANCHO DE LA HOJA
            # ------------------------------------------------

            try:

                ancho = (
                    writer.width()
                    - 40
                )

                alto = (
                    writer.height()
                    - 40
                )

                if ancho > 0 and alto > 0:

                    doc.setPageSize(
                        QSizeF(
                            ancho,
                            alto
                        )
                    )

            except Exception:
                pass

            # ------------------------------------------------
            # GENERAR PDF
            # ------------------------------------------------

            doc.print_(
                writer
            )

            # ------------------------------------------------
            # VERIFICAR QUE REALMENTE SE CREÓ
            # ------------------------------------------------

            import os

            if not os.path.exists(ruta):

                raise Exception(
                    "Qt no pudo crear el archivo PDF."
                )

            if os.path.getsize(ruta) <= 0:

                raise Exception(
                    "El archivo PDF fue creado pero está vacío."
                )

            QMessageBox.information(
                self,
                "PDF guardado",
                "El arqueo mensual fue guardado correctamente en:\n\n"
                + ruta
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error al guardar PDF",
                "No se pudo guardar el PDF:\n\n"
                + str(e)
            )
    # ========================================================
    # IMPRIMIR
    # ========================================================

    # ========================================================
    # IMPRIMIR
    # ========================================================

    def imprimir(self):

        try:

            printer = QPrinter(
                QPrinter.HighResolution
            )

            dialogo = QPrintDialog(
                printer,
                self
            )

            if (
                dialogo.exec()
                != QDialog.Accepted
            ):
                return

            # ------------------------------------------------
            # DOCUMENTO
            # ------------------------------------------------

            doc = QTextDocument()

            doc.setDocumentMargin(20)

            doc.setDefaultStyleSheet("""
                body {
                    font-family: Arial;
                    color: #0f172a;
                    font-size: 9pt;
                }

                h1 {
                    font-size: 20pt;
                    margin-bottom: 10px;
                }

                h2 {
                    font-size: 13pt;
                    margin-top: 18px;
                    margin-bottom: 8px;
                }

                table {
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 14px;
                }

                th {
                    background-color: #e2e8f0;
                    color: #0f172a;
                    border: 1px solid #94a3b8;
                    padding: 5px;
                    font-weight: bold;
                }

                td {
                    border: 1px solid #cbd5e1;
                    padding: 4px;
                }

                .cabecera {
                    color: #64748b;
                    font-size: 9pt;
                }
            """)

            doc.setHtml(
                self._html_reporte()
            )

            # ------------------------------------------------
            # AJUSTAR AL ANCHO DE LA HOJA
            # ------------------------------------------------

            try:

                rect = printer.pageRect(
                    QPrinter.DevicePixel
                )

                ancho = rect.width()

                alto = rect.height()

                if ancho > 0 and alto > 0:

                    doc.setPageSize(
                        QSizeF(
                            ancho,
                            alto
                        )
                    )

            except Exception:
                pass

            # ------------------------------------------------
            # IMPRIMIR
            # ------------------------------------------------

            doc.print_(
                printer
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error de impresión",
                "No se pudo imprimir el arqueo mensual:\n\n"
                + str(e)
            )
    # ========================================================
    # CSV
    # ========================================================

    def guardar_csv(self):

        nombre = (
            f"arqueo_"
            f"{self.anio.currentData()}_"
            f"{int(self.mes.currentData()):02d}.csv"
        )

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar arqueo mensual",
            nombre,
            "CSV (*.csv)"
        )

        if not ruta:
            return

        try:

            with open(
                ruta,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as archivo:

                writer = csv.writer(
                    archivo,
                    delimiter=";"
                )

                writer.writerow(
                    [
                        "ARQUEO MENSUAL",
                        self._titulo_reporte()
                    ]
                )

                writer.writerow([])

                writer.writerow(
                    ["RESUMEN GENERAL"]
                )

                for clave, widget in (
                    self.resumen_widgets.items()
                ):

                    writer.writerow(
                        [
                            clave,
                            widget.text()
                        ]
                    )

                writer.writerow([])

                tablas = [

                    (
                        self.tabla_dias,
                        "DETALLE DIARIO"
                    ),

                    (
                        self.tabla_caja,
                        "MOVIMIENTOS DE CAJA"
                    ),

                    (
                        self.tabla_arqueos,
                        "ARQUEOS REALIZADOS"
                    ),

                ]

                for tabla, titulo in tablas:

                    writer.writerow(
                        [titulo]
                    )

                    writer.writerow(
                        [
                            tabla.horizontalHeaderItem(
                                i
                            ).text()
                            for i in range(
                                tabla.columnCount()
                            )
                        ]
                    )

                    for fila in range(
                        tabla.rowCount()
                    ):

                        writer.writerow(
                            [
                                (
                                    tabla.item(
                                        fila,
                                        columna
                                    ).text()
                                    if tabla.item(
                                        fila,
                                        columna
                                    )
                                    else ""
                                )
                                for columna in range(
                                    tabla.columnCount()
                                )
                            ]
                        )

                    writer.writerow([])

            QMessageBox.information(
                self,
                "Reporte guardado",
                "El arqueo mensual fue guardado en:\n\n"
                + ruta
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                "No se pudo guardar el CSV:\n\n"
                + str(e)
            )


# ============================================================
# DASHBOARD
# ============================================================

class Dashboard(QMainWindow):

    def __init__(self):

        super().__init__()

        init_db()

        self.nombre_negocio = (
            get_setting(
                "nombre_negocio",
                "COTILLON"
            )
            or "COTILLON"
        )

        self.setWindowTitle(
            f"{self.nombre_negocio} POS"
        )

        self.setMinimumSize(
            760,
            560
        )

        self.setStyleSheet(
            """
            QMainWindow {
                background:#f8fafc;
            }

            QFrame#side {
                background:#0f172a;
                border-radius:18px;
            }

            QPushButton {
                border:0;
                border-radius:10px;
                padding:12px;
                color:white;
                font-weight:600;
            }

            QPushButton.nav {
                background:transparent;
                text-align:left;
            }

            QPushButton.nav:hover {
                background:#1e293b;
            }

            QLabel {
                color:#0f172a;
            }
            """
        )

        # ====================================================
        # CENTRAL
        # ====================================================

        central = QWidget()

        central.setObjectName(
            "mainCentral"
        )

        central.setStyleSheet(
            """
            QWidget#mainCentral {
                background:#ffffff;
            }
            """
        )

        self.setCentralWidget(
            central
        )

        root = QHBoxLayout(
            central
        )

        root.setContentsMargins(
            18,
            18,
            18,
            18
        )

        # ====================================================
        # SIDEBAR
        # ====================================================

        side = QFrame()

        side.setObjectName(
            "side"
        )

        side.setMinimumWidth(
            175
        )

        side.setMaximumWidth(
            230
        )

        side.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Expanding
        )

        sl = QVBoxLayout(
            side
        )

        self.brand = QLabel(
            self.nombre_negocio
        )

        self.brand.setStyleSheet(
            """
            color:white;
            font-size:27px;
            font-weight:900;
            """
        )

        self.brand.setAlignment(
            Qt.AlignCenter
        )

        sl.addWidget(
            self.brand
        )

        version = QLabel(
            f"Versión {obtener_version_actual()}"
        )

        version.setStyleSheet(
            """
            color:#94a3b8;
            font-size:12px;
            font-weight:600;
            """
        )

        version.setAlignment(
            Qt.AlignCenter
        )

        sl.addWidget(
            version
        )

        self.nav_buttons = []

        botones_nav = [

            (
                "🏠 Inicio",
                self.ir_inicio
            ),

            (
                "🛒 Ventas",
                self.abrir_ventas
            ),

            (
                "📦 Productos",
                self.abrir_productos
            ),

            (
                "📋 Pedidos",
                self.abrir_pedidos
            ),

            (
                "🧾 Documentos",
                self.abrir_documentos
            ),

            (
                "🏷️ Carteles / Ofertas",
                self.abrir_carteles
            ),

            (
                "👥 Clientes",
                self.abrir_clientes
            ),

            (
                "🕘 Historial",
                self.abrir_historial
            ),

            (
                "💰 Caja / Arqueo",
                self.abrir_caja
            ),

            (
                "📅 Arqueo mensual",
                self.abrir_arqueo_mensual
            ),

            (
                "📊 Reportes",
                self.abrir_reportes
            ),

            (
                "⚙️ Configuración",
                self.abrir_config
            ),

        ]

        for texto, funcion in (
            botones_nav
        ):

            boton = QPushButton(
                texto
            )

            boton.setProperty(
                "class",
                "nav"
            )

            boton.setMinimumHeight(
                42
            )

            boton.setStyleSheet(
                """
                font-size:15px;
                text-align:left;
                padding:8px 10px;
                """
            )

            boton.clicked.connect(
                funcion
            )

            sl.addWidget(
                boton
            )

            self.nav_buttons.append(
                boton
            )

        sl.addStretch()

        cerrar = QPushButton(
            "🚪 Cerrar"
        )

        cerrar.clicked.connect(
            self.close
        )

        sl.addWidget(
            cerrar
        )

        root.addWidget(
            side
        )

        # ====================================================
        # STACK
        # ====================================================

        self.stack = QStackedWidget()

        self.stack.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.stack.setStyleSheet(
            """
            QStackedWidget {
                background:#ffffff;
            }
            """
        )

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(
            True
        )

        self.scroll.setFrameShape(
            QFrame.NoFrame
        )

        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.scroll.setStyleSheet(
            """
            QScrollArea {
                background:#ffffff;
                border:0;
            }

            QScrollArea > QWidget > QWidget {
                background:#ffffff;
            }
            """
        )

        self.scroll.viewport().setStyleSheet(
            "background:#ffffff;"
        )

        self.scroll.setWidget(
            self.stack
        )

        root.addWidget(
            self.scroll,
            1
        )

        # ====================================================
        # HOME
        # ====================================================

        self.home = QWidget()

        self.home.setObjectName(
            "home"
        )

        self.home.setStyleSheet(
            """
            QWidget#home {
                background:#ffffff;
            }
            """
        )

        self.stack.addWidget(
            self.home
        )

        self.build_home()

        self.stack.setCurrentWidget(
            self.home
        )

        # ====================================================
        # RESOLUCIÓN
        # ====================================================

        screen = (
            QApplication
            .primaryScreen()
            .availableGeometry()
        )

        ancho = screen.width()
        alto = screen.height()

        if (
            ancho < 1500
            or alto < 850
        ):

            self.resize(
                ancho,
                alto
            )

            self.move(
                (ancho - self.width()) // 2,
                (alto - self.height()) // 2
            )

        else:

            self.showMaximized()

        self.actualizar()

    # ========================================================
    # NOMBRE NEGOCIO
    # ========================================================

    def actualizar_nombre_negocio(
        self
    ):

        self.nombre_negocio = (
            get_setting(
                "nombre_negocio",
                "COTILLON"
            )
            or "COTILLON"
        )

        self.setWindowTitle(
            f"{self.nombre_negocio} POS"
        )

        self.brand.setText(
            self.nombre_negocio
        )

        self.titulo_home.setText(
            f"Bienvenido a {self.nombre_negocio} 👋"
        )

    # ========================================================
    # HOME
    # ========================================================

    def build_home(self):

        panel = QVBoxLayout(
            self.home
        )

        panel.setContentsMargins(
            25,
            25,
            25,
            25
        )

        self.titulo_home = QLabel(
            f"Bienvenido a {self.nombre_negocio} 👋"
        )

        self.titulo_home.setStyleSheet(
            """
            font-size:32px;
            font-weight:900;
            """
        )

        panel.addWidget(
            self.titulo_home
        )

        subtitulo = QLabel(
            "Punto de venta y gestión del negocio"
        )

        subtitulo.setStyleSheet(
            """
            font-size:16px;
            color:#64748b;
            """
        )

        panel.addWidget(
            subtitulo
        )

        # ====================================================
        # TARJETAS
        # ====================================================

        cards = QHBoxLayout()

        self.v = QLabel()
        self.p = QLabel()
        self.e = QLabel()

        tarjetas = [

            (
                "💰 Ventas de hoy",
                self.v
            ),

            (
                "📦 Productos",
                self.p
            ),

            (
                "💵 Efectivo esperado",
                self.e
            ),

        ]

        for titulo, widget in tarjetas:

            frame = QFrame()

            frame.setObjectName(
                "homeCard"
            )

            frame.setStyleSheet(
                """
                QFrame#homeCard {
                    background-color:#ffffff;
                    border:1px solid #e2e8f0;
                    border-radius:15px;
                }

                QFrame#homeCard QLabel {
                    background-color:transparent;
                    color:#0f172a;
                }
                """
            )

            layout = QVBoxLayout(
                frame
            )

            etiqueta = QLabel(
                titulo
            )

            etiqueta.setStyleSheet(
                """
                color:#64748b;
                background:transparent;
                font-weight:bold;
                """
            )

            widget.setStyleSheet(
                """
                color:#0f172a;
                background:transparent;
                font-size:25px;
                font-weight:900;
                """
            )

            layout.addWidget(
                etiqueta
            )

            layout.addWidget(
                widget
            )

            cards.addWidget(
                frame
            )

        panel.addLayout(
            cards
        )

        # ====================================================
        # BOTONES HOME
        # ====================================================

        botones = QHBoxLayout()

        nueva_venta = QPushButton(
            "🛒 Nueva venta"
        )

        nueva_venta.setStyleSheet(
            """
            background:#0ea5e9;
            color:white;
            padding:14px;
            font-weight:800;
            """
        )

        nueva_venta.clicked.connect(
            self.abrir_ventas
        )

        arqueo = QPushButton(
            "📅 Arqueo mensual"
        )

        arqueo.setStyleSheet(
            """
            background:#8b5cf6;
            color:white;
            padding:14px;
            font-weight:800;
            """
        )

        arqueo.clicked.connect(
            self.abrir_arqueo_mensual
        )

        reiniciar = QPushButton(
            "🧹 Reiniciar ventas de hoy"
        )

        reiniciar.setStyleSheet(
            """
            background:#e2e8f0;
            color:#334155;
            padding:14px;
            font-weight:800;
            """
        )

        reiniciar.clicked.connect(
            self.reiniciar_hoy
        )
        limpiar_pruebas = QPushButton(
            "🧹 Limpiar datos de prueba"
        )

        limpiar_pruebas.setStyleSheet(
            """
            background:#dc2626;
            color:white;
            padding:14px;
            font-weight:800;
            """
        )

        limpiar_pruebas.clicked.connect(
            self.limpiar_datos_prueba
        )

        botones.addWidget(
            nueva_venta
        )

        botones.addWidget(
            arqueo
        )

        botones.addWidget(
            reiniciar
        )
        botones.addWidget(
            limpiar_pruebas
        )

        botones.addStretch()

        panel.addLayout(
            botones
        )

        panel.addStretch()

    # ========================================================
    # ARQUEO MENSUAL
    # ========================================================

    def abrir_arqueo_mensual(
        self
    ):

        dlg = ArqueoMensual(
            self
        )

        dlg.exec()

    # ========================================================
    # SINCRONIZACIÓN REMOTA
    # ========================================================

    def verificar_sincronizacion_remota(
        self
    ):

        try:

            api_url = get_setting(
                "api_url",
                "https://papelera-pos-backend-production.up.railway.app"
            )

            response = requests.get(
                f"{api_url}/sincronizacion/pendientes",
                timeout=2
            )

            if response.status_code == 200:

                eventos = response.json()

                hoy = (
                    datetime.datetime
                    .now()
                    .strftime("%Y-%m-%d")
                )

                hubo_cambios = False

                for evento in eventos:

                    if (
                        evento.get(
                            "accion"
                        )
                        == "archivar_hoy"
                    ):

                        archivar_ventas(
                            fecha=hoy
                        )

                        hubo_cambios = True

                return hubo_cambios

        except Exception:
            pass

        return False

    # ========================================================
    # ACTUALIZAR
    # ========================================================

    def actualizar(self):

        hoy = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )

        c = sqlite3.connect(
            BASE_DATOS
        )

        q = c.cursor()

        try:

            # =================================================
            # VENTAS DE HOY
            # =================================================

            columnas_ventas = _tabla_columnas(
                q,
                "ventas"
            )

            # -------------------------------------------------
            # IMPORTANTE:
            #
            # El error:
            #
            # Incorrect number of bindings supplied.
            #
            # aparecía cuando la consulta tenía un solo ?
            # pero terminaba recibiendo varios parámetros.
            #
            # Ahora cada consulta recibe EXACTAMENTE los
            # parámetros que necesita.
            # -------------------------------------------------

            if "estado" in columnas_ventas:

                ventas = q.execute(
                    """
                    SELECT COALESCE(
                        SUM(total),
                        0
                    )
                    FROM ventas
                    WHERE fecha LIKE ?
                      AND COALESCE(
                          estado,
                          'ACTIVA'
                      ) = 'ACTIVA'
                    """,
                    (
                        hoy + "%",
                    )
                ).fetchone()[0]

            else:

                ventas = q.execute(
                    """
                    SELECT COALESCE(
                        SUM(total),
                        0
                    )
                    FROM ventas
                    WHERE fecha LIKE ?
                    """,
                    (
                        hoy + "%",
                    )
                ).fetchone()[0]

            # =================================================
            # PRODUCTOS
            # =================================================

            prod = q.execute(
                """
                SELECT COUNT(*)
                FROM productos
                """
            ).fetchone()[0]

            # =================================================
            # EFECTIVO ESPERADO
            # =================================================

            if "pago_efectivo" in columnas_ventas:

                if "estado" in columnas_ventas:

                    ef = q.execute(
                        """
                        SELECT COALESCE(
                            SUM(
                                COALESCE(
                                    pago_efectivo,
                                    0
                                )
                            ),
                            0
                        )
                        FROM ventas
                        WHERE fecha LIKE ?
                          AND COALESCE(
                              estado,
                              'ACTIVA'
                          ) = 'ACTIVA'
                        """,
                        (
                            hoy + "%",
                        )
                    ).fetchone()[0]

                else:

                    ef = q.execute(
                        """
                        SELECT COALESCE(
                            SUM(
                                COALESCE(
                                    pago_efectivo,
                                    0
                                )
                            ),
                            0
                        )
                        FROM ventas
                        WHERE fecha LIKE ?
                        """,
                        (
                            hoy + "%",
                        )
                    ).fetchone()[0]

            else:

                if "estado" in columnas_ventas:

                    ef = q.execute(
                        """
                        SELECT COALESCE(
                            SUM(
                                CASE
                                    WHEN LOWER(
                                        TRIM(
                                            COALESCE(
                                                forma_pago,
                                                ''
                                            )
                                        )
                                    ) = 'efectivo'
                                    THEN COALESCE(
                                        total,
                                        0
                                    )
                                    ELSE 0
                                END
                            ),
                            0
                        )
                        FROM ventas
                        WHERE fecha LIKE ?
                          AND COALESCE(
                              estado,
                              'ACTIVA'
                          ) = 'ACTIVA'
                        """,
                        (
                            hoy + "%",
                        )
                    ).fetchone()[0]

                else:

                    ef = q.execute(
                        """
                        SELECT COALESCE(
                            SUM(
                                CASE
                                    WHEN LOWER(
                                        TRIM(
                                            COALESCE(
                                                forma_pago,
                                                ''
                                            )
                                        )
                                    ) = 'efectivo'
                                    THEN COALESCE(
                                        total,
                                        0
                                    )
                                    ELSE 0
                                END
                            ),
                            0
                        )
                        FROM ventas
                        WHERE fecha LIKE ?
                        """,
                        (
                            hoy + "%",
                        )
                    ).fetchone()[0]

        except Exception as e:

            print(
                "ERROR Dashboard.actualizar():",
                e
            )

            raise

        finally:

            c.close()

        # =====================================================
        # MOSTRAR RESULTADOS
        # =====================================================

        self.v.setText(
            f"${float(ventas or 0):,.2f}"
        )

        self.p.setText(
            str(prod or 0)
        )

        self.e.setText(
            f"${float(ef or 0):,.2f}"
        )

        # =====================================================
        # COMPROBAR SINCRONIZACIÓN REMOTA
        # =====================================================

        QTimer.singleShot(
            100,
            self.verificar_sincronizacion_remota
        )
    # ========================================================
    # LIMPIAR DATOS DE PRUEBA
    #
    # BORRA TODO EXCEPTO PRODUCTOS
    # ========================================================

    # ========================================================
    # LIMPIAR DATOS DE PRUEBA
    #
    # BORRA TODO EXCEPTO PRODUCTOS
    # EN SQLITE Y SUPABASE
    # ========================================================

    def limpiar_datos_prueba(self):

        respuesta = QMessageBox.warning(
            self,
            "⚠️ Limpiar datos de prueba",
            (
                "Esto va a borrar TODOS los datos de prueba.\n\n"
                "Se conservarán únicamente los PRODUCTOS.\n\n"
                "Se eliminarán:\n"
                "• Clientes\n"
                "• Ventas\n"
                "• Detalle de ventas\n"
                "• Pedidos\n"
                "• Detalle de pedidos\n"
                "• Movimientos de caja\n"
                "• Arqueos\n"
                "• Registros de sincronización\n\n"
                "La limpieza también se realizará en SUPABASE.\n\n"
                "Los productos NO serán modificados.\n\n"
                "¿Querés continuar?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta != QMessageBox.Yes:
            return

        conexion = None

        try:

            # =================================================
            # SUPABASE
            # =================================================

            from core.sync import (
                SUPABASE_URL,
                obtener_headers
            )

            tablas_supabase = [
                # Primero los detalles
                "detalle_ventas",
                "detalle_pedidos",

                # Después las cabeceras
                "ventas",
                "pedidos",

                # Resto
                "clientes",
                "movimientos_caja",
                "arqueos"
            ]

            headers = obtener_headers()

            for tabla in tablas_supabase:

                respuesta_supabase = requests.delete(
                    f"{SUPABASE_URL}/rest/v1/{tabla}",
                    params={
                        "id": "gt.0"
                    },
                    headers=headers,
                    timeout=15
                )

                print(
                    "LIMPIAR SUPABASE:",
                    tabla,
                    respuesta_supabase.status_code,
                    respuesta_supabase.text
                )

                if respuesta_supabase.status_code not in (
                    200,
                    204
                ):

                    raise Exception(
                        "Error eliminando "
                        f"{tabla} en Supabase: "
                        f"{respuesta_supabase.status_code} "
                        f"{respuesta_supabase.text}"
                    )

            # =================================================
            # SQLITE LOCAL
            # =================================================

            conexion = sqlite3.connect(
                BASE_DATOS
            )

            cursor = conexion.cursor()

            tablas_locales = [
                # Detalles primero
                "detalle_ventas",
                "detalle_pedidos",

                # Cabeceras
                "ventas",
                "pedidos",

                # Resto
                "clientes",
                "movimientos_caja",
                "arqueos",

                # Cola de sincronización
                "sincronizacion"
            ]

            for tabla in tablas_locales:

                cursor.execute(
                    f"DELETE FROM {tabla}"
                )

            # =================================================
            # REINICIAR CONTADORES AUTOINCREMENT
            #
            # NO TOCAR productos
            # =================================================

            tablas_reset = [
                "clientes",
                "ventas",
                "detalle_ventas",
                "pedidos",
                "detalle_pedidos",
                "movimientos_caja",
                "arqueos",
                "sincronizacion"
            ]

            for tabla in tablas_reset:

                cursor.execute(
                    """
                    DELETE FROM sqlite_sequence
                    WHERE name = ?
                    """,
                    (tabla,)
                )

            conexion.commit()

            # =================================================
            # COMPROBAR SQLITE
            # =================================================

            resultados = {}

            for tabla in [
                "clientes",
                "ventas",
                "detalle_ventas",
                "pedidos",
                "detalle_pedidos",
                "movimientos_caja",
                "arqueos",
                "sincronizacion"
            ]:

                resultados[tabla] = cursor.execute(
                    f"SELECT COUNT(*) FROM {tabla}"
                ).fetchone()[0]

            productos = cursor.execute(
                "SELECT COUNT(*) FROM productos"
            ).fetchone()[0]

            conexion.close()
            conexion = None

            # =================================================
            # ACTUALIZAR DASHBOARD
            # =================================================

            self.actualizar()

            # =================================================
            # RESULTADO
            # =================================================

            QMessageBox.information(
                self,
                "Limpieza completada",
                (
                    "Los datos de prueba fueron eliminados "
                    "correctamente de SQLite y Supabase.\n\n"

                    f"Productos conservados: {productos}\n\n"

                    f"Clientes: "
                    f"{resultados['clientes']}\n"

                    f"Ventas: "
                    f"{resultados['ventas']}\n"

                    f"Detalle ventas: "
                    f"{resultados['detalle_ventas']}\n"

                    f"Pedidos: "
                    f"{resultados['pedidos']}\n"

                    f"Detalle pedidos: "
                    f"{resultados['detalle_pedidos']}\n"

                    f"Movimientos caja: "
                    f"{resultados['movimientos_caja']}\n"

                    f"Arqueos: "
                    f"{resultados['arqueos']}\n"

                    f"Sincronización: "
                    f"{resultados['sincronizacion']}"
                )
            )

        except Exception as e:

            if conexion is not None:

                try:
                    conexion.close()
                except Exception:
                    pass

            print(
                "ERROR limpiando datos de prueba:",
                e
            )

            QMessageBox.critical(
                self,
                "Error",
                (
                    "NO se completó la limpieza.\n\n"
                    "Los datos locales no se eliminaron "
                    "si Supabase falló antes de comenzar "
                    "la limpieza local.\n\n"
                    f"Error: {e}"
                )
            )
    # ========================================================
    # REINICIAR
    # ========================================================

    def reiniciar_hoy(self):

        hoy = (
            datetime.datetime
            .now()
            .strftime("%Y-%m-%d")
        )

        conexion = sqlite3.connect(
            BASE_DATOS
        )

        cantidad = conexion.execute(
            """
            SELECT COUNT(*)
            FROM ventas

            WHERE fecha LIKE ?

            AND COALESCE(
                estado,
                'ACTIVA'
            ) = 'ACTIVA'
            """,
            (
                hoy + "%",
            )
        ).fetchone()[0]

        conexion.close()

        if not cantidad:

            QMessageBox.information(
                self,
                "Ventas de hoy",
                "No hay ventas activas para reiniciar."
            )

            return

        box = QMessageBox(
            self
        )

        box.setIcon(
            QMessageBox.Warning
        )

        box.setWindowTitle(
            "Reiniciar ventas de hoy"
        )

        box.setText(
            f"Se archivarán {cantidad} ventas de hoy "
            "y la pantalla quedará en cero."
        )

        box.setInformativeText(
            "Las ventas seguirán disponibles "
            "en el historial. ¿Querés continuar?"
        )

        box.setStandardButtons(
            QMessageBox.Yes
            | QMessageBox.No
        )

        if (
            box.exec()
            != QMessageBox.Yes
        ):
            return

        archivar_ventas(
            fecha=hoy
        )

        try:

            datos_sync = {
                "fecha": hoy,
                "accion": "archivar_hoy",
            }

            registro_uuid = (
                nuevo_uuid()
            )

            registrar_sincronizacion(
                "ventas",
                registro_uuid,
                "archivar_hoy",
                datos_sync
            )

            api_url = get_setting(
                "api_url",
                "https://papelera-pos-backend-production.up.railway.app"
            )

            requests.post(
                f"{api_url}/sincronizar",
                json={
                    "tabla": "ventas",
                    "registro_uuid":
                        registro_uuid,
                    "accion":
                        "archivar_hoy",
                    "datos":
                        datos_sync,
                },
                timeout=2
            )

        except Exception as e:

            print(
                "Se archivó localmente, "
                "error al sincronizar reinicio:",
                e
            )

        self.actualizar()

        QMessageBox.information(
            self,
            "Listo",
            "Las ventas de hoy fueron archivadas. "
            "El inicio quedó en cero."
        )

    # ========================================================
    # NAVEGACIÓN
    # ========================================================

    def ir_inicio(self):

        self.stack.setCurrentWidget(
            self.home
        )

    def openw(self, cls):

        if not hasattr(
            self,
            "_module_cache"
        ):

            self._module_cache = {}

        widget = (
            self._module_cache.get(
                cls
            )
        )

        if widget is None:

            widget = cls()

            widget.setMinimumSize(
                0,
                0
            )

            widget.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Expanding
            )

            self.stack.addWidget(
                widget
            )

            self._module_cache[
                cls
            ] = widget

            # --------------------------------------------
            # VENTAS
            # --------------------------------------------

            if cls is Ventas:

                if hasattr(
                    widget,
                    "venta_realizada"
                ):

                    widget.venta_realizada.connect(
                        self.actualizar
                    )

            # --------------------------------------------
            # PEDIDOS
            # --------------------------------------------

            if cls is Pedidos:

                if hasattr(
                    widget,
                    "pedido_entregado"
                ):

                    widget.pedido_entregado.connect(
                        self.actualizar
                    )

            # --------------------------------------------
            # CAJA
            # --------------------------------------------

            if cls is Caja:

                if hasattr(
                    widget,
                    "arqueo_realizado"
                ):

                    widget.arqueo_realizado.connect(
                        self.actualizar
                    )

        self.stack.setCurrentWidget(
            widget
        )

        if cls is Ventas:

            self.scroll.verticalScrollBar().setValue(
                0
            )

            self.scroll.horizontalScrollBar().setValue(
                0
            )

            self.stack.setMinimumSize(
                self.scroll.viewport().size()
            )

            self.stack.resize(
                self.scroll.viewport().size()
            )

            if hasattr(
                widget,
                "refresh_layout_on_return"
            ):

                widget.refresh_layout_on_return()

            self.scroll.viewport().update()

            self.stack.updateGeometry()

        if (
            hasattr(
                widget,
                "actualizar_datos"
            )
            and cls is not Ventas
        ):

            widget.actualizar_datos()

        return widget

    # ========================================================
    # MÓDULOS
    # ========================================================

    def abrir_ventas(self):
        self.openw(
            Ventas
        )

    def abrir_productos(self):
        self.openw(
            Productos
        )

    def abrir_pedidos(self):
        self.openw(
            Pedidos
        )

    def abrir_documentos(self):
        self.openw(
            Documentos
        )

    def abrir_carteles(self):
        self.openw(
            Carteles
        )

    def abrir_clientes(self):
        self.openw(
            Clientes
        )

    def abrir_historial(self):
        self.openw(
            Historial
        )

    def abrir_caja(self):
        self.openw(
            Caja
        )

    def abrir_reportes(self):
        self.openw(
            Reportes
        )

    def abrir_config(self):
        self.openw(
            Configuracion
        )
