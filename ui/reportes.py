import sys
import sqlite3
import datetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QFrame,
    QHeaderView,
    QDialog,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ui.db import BASE_DATOS, init_db


class DialogoAviso(QDialog):
    """Ventana de aviso/éxito personalizada para evitar pantallas en blanco."""
    def __init__(self, titulo, mensaje, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setFixedSize(380, 160)
        self.setModal(True)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                border-radius: 12px;
            }
            QLabel {
                color: #0f172a;
                font-size: 15px;
            }
            QPushButton {
                font-weight: 600;
                font-size: 14px;
                border-radius: 8px;
                padding: 10px 24px;
                border: none;
                background-color: #2563eb;
                color: white;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        lbl_icono = QLabel("✅")
        lbl_icono.setStyleSheet("font-size: 26px;")
        
        lbl_texto = QLabel(mensaje)
        lbl_texto.setWordWrap(True)
        lbl_texto.setStyleSheet("font-size: 15px; font-weight: 500; color: #1e293b;")

        top_layout = QHBoxLayout()
        top_layout.addWidget(lbl_icono)
        top_layout.addWidget(lbl_texto, 1)
        layout.addLayout(top_layout)

        botones_layout = QHBoxLayout()
        botones_layout.addStretch()

        self.btn_ok = QPushButton("Aceptar")
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.clicked.connect(self.accept)

        botones_layout.addWidget(self.btn_ok)
        layout.addLayout(botones_layout)


class TarjetaKPI(QFrame):
    """Tarjeta moderna para mostrar métricas clave (KPIs) en el dashboard."""
    def __init__(self, titulo, valor_inicial, icono, color_borde="#2563eb"):
        super().__init__()
        self.setObjectName("tarjetaKPI")
        self.setStyleSheet(f"""
            QFrame#tarjetaKPI {{
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                border-left: 5px solid {color_borde};
            }}
            QLabel {{
                font-family: 'Segoe UI', sans-serif;
                border: none;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        lbl_icono = QLabel(icono)
        lbl_icono.setStyleSheet("font-size: 18px;")
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase;")
        
        header_layout.addWidget(lbl_icono)
        header_layout.addWidget(lbl_titulo, 1)
        layout.addLayout(header_layout)

        self.lbl_valor = QLabel(valor_inicial)
        self.lbl_valor.setStyleSheet("font-size: 22px; font-weight: 800; color: #0f172a;")
        layout.addWidget(self.lbl_valor)

    def actualizar_valor(self, nuevo_valor):
        self.lbl_valor.setText(str(nuevo_valor))


class Reportes(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Reportes y Ventas Realizadas - Abril POS")
        self.resize(980, 680)

        self.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #0f172a;
            }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                gridline-color: #f1f5f9;
                selection-background-color: #e0e7ff;
                selection-color: #1e293b;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                color: #334155;
                font-weight: 700;
                font-size: 13px;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #cbd5e1;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #f1f5f9;
            }
        """)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(20)

        # Encabezado
        top_layout = QHBoxLayout()

        titulo_layout = QVBoxLayout()
        titulo = QLabel("📊 Historial de Ventas y Reportes")
        titulo.setStyleSheet("font-size: 24px; font-weight: 800; color: #0f172a;")
        sub_titulo = QLabel("Control de transacciones realizadas, ingresos totales y gestión de registros.")
        sub_titulo.setStyleSheet("font-size: 13px; color: #64748b;")
        
        titulo_layout.addWidget(titulo)
        titulo_layout.addWidget(sub_titulo)
        top_layout.addLayout(titulo_layout)

        top_layout.addStretch()

        self.btn_actualizar = QPushButton("🔄 Actualizar Reportes")
        self.btn_actualizar.setCursor(Qt.PointingHandCursor)
        self.btn_actualizar.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-weight: 600;
                font-size: 13px;
                border-radius: 8px;
                padding: 10px 18px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        self.btn_actualizar.clicked.connect(self.cargar_reporte)
        top_layout.addWidget(self.btn_actualizar)

        layout_principal.addLayout(top_layout)

        # Dashboard de KPIs
        grid_kpi = QHBoxLayout()
        grid_kpi.setSpacing(15)

        self.card_hoy = TarjetaKPI("Ventas Hoy", "$0.00", "📅", "#2563eb")
        self.card_mes = TarjetaKPI("Ventas del Mes", "$0.00", "🗓️", "#0284c7")
        self.card_total = TarjetaKPI("Total Acumulado", "$0.00", "💰", "#0d9488")
        self.card_ganancia = TarjetaKPI("Ganancia Neta", "$0.00", "📈", "#16a34a")
        self.card_top = TarjetaKPI("Producto Estrella", "Sin ventas", "⭐", "#d97706")

        grid_kpi.addWidget(self.card_hoy)
        grid_kpi.addWidget(self.card_mes)
        grid_kpi.addWidget(self.card_total)
        grid_kpi.addWidget(self.card_ganancia)
        grid_kpi.addWidget(self.card_top)

        layout_principal.addLayout(grid_kpi)

        # Tabla Detallada de Ventas
        lbl_seccion = QLabel("🧾 Listado de Ventas Registradas")
        lbl_seccion.setStyleSheet("font-size: 16px; font-weight: 700; color: #1e293b; margin-top: 10px;")
        layout_principal.addWidget(lbl_seccion)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels([
            "ID Venta",
            "Fecha y Hora",
            "Total Cobrado ($)",
            "Acciones"
        ])
        
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.tabla.verticalHeader().setVisible(False)

        layout_principal.addWidget(self.tabla)

        self.setLayout(layout_principal)
        self.cargar_reporte()

    def cargar_reporte(self):
        try:
            conexion = sqlite3.connect(BASE_DATOS)
            cursor = conexion.cursor()

            # Métricas KPIs
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM ventas")
            ventas = cursor.fetchone()
            cantidad_ventas = ventas[0]
            total_general = ventas[1]

            hoy = datetime.datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT COALESCE(SUM(total), 0) FROM ventas WHERE fecha LIKE ?", (hoy + "%",))
            venta_hoy = cursor.fetchone()[0]

            mes = datetime.datetime.now().strftime("%Y-%m")
            cursor.execute("SELECT COALESCE(SUM(total), 0) FROM ventas WHERE fecha LIKE ?", (mes + "%",))
            venta_mes = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COALESCE(SUM((p.precio_venta - p.precio_compra) * d.cantidad), 0)
                FROM detalle_ventas d
                JOIN productos p ON p.nombre = d.producto
            """)
            ganancia = cursor.fetchone()[0]

            cursor.execute("""
                SELECT producto, SUM(cantidad)
                FROM detalle_ventas
                GROUP BY producto
                ORDER BY SUM(cantidad) DESC
                LIMIT 1
            """)
            producto_top = cursor.fetchone()

            if producto_top:
                mas_vendido = f"{producto_top[0]} ({producto_top[1]} u.)"
            else:
                mas_vendido = "Sin ventas"

            self.card_hoy.actualizar_valor(f"${venta_hoy:,.2f}")
            self.card_mes.actualizar_valor(f"${venta_mes:,.2f}")
            self.card_total.actualizar_valor(f"${total_general:,.2f}")
            self.card_ganancia.actualizar_valor(f"${ganancia:,.2f}")
            self.card_top.actualizar_valor(mas_vendido)

            # Cargar tabla de ventas individuales
            cursor.execute("""
                SELECT id, fecha, total
                FROM ventas
                ORDER BY id DESC
            """)

            lista_ventas = cursor.fetchall()
            conexion.close()

            self.tabla.setRowCount(len(lista_ventas))

            for fila, venta in enumerate(lista_ventas):
                id_venta = venta[0]
                fecha_venta = str(venta[1])
                val_total = float(venta[2]) if venta[2] else 0.0

                # Establecer una altura fija generosa para la fila (ej. 50 píxeles) para que el botón respire
                self.tabla.setRowHeight(fila, 50)

                # ID Venta
                item_id = QTableWidgetItem(f"#{id_venta}")
                item_id.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                self.tabla.setItem(fila, 0, item_id)

                # Fecha y Hora
                item_fecha = QTableWidgetItem(fecha_venta)
                item_fecha.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.tabla.setItem(fila, 1, item_fecha)

                # Total Cobrado
                item_total = QTableWidgetItem(f"${val_total:,.2f}")
                item_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_total.setForeground(QColor("#15803d"))
                self.tabla.setItem(fila, 2, item_total)

                # Botón de Papelera con tamaño adecuado y diseño limpio
                btn_eliminar = QPushButton("🗑️ Eliminar Venta")
                btn_eliminar.setCursor(Qt.PointingHandCursor)
                btn_eliminar.setFixedHeight(32)
                btn_eliminar.setStyleSheet("""
                    QPushButton {
                        background-color: #fee2e2;
                        color: #991b1b;
                        border: 1px solid #fca5a5;
                        border-radius: 6px;
                        font-weight: 600;
                        font-size: 12px;
                        padding: 0px 12px;
                    }
                    QPushButton:hover {
                        background-color: #fecaca;
                        color: #7f1d1d;
                    }
                """)
                btn_eliminar.clicked.connect(lambda checked=False, id_v=id_venta: self.eliminar_venta(id_v))
                
                # Contenedor para centrar el botón perfectamente en la celda
                celda_widget = QWidget()
                celda_layout = QHBoxLayout(celda_widget)
                celda_layout.addWidget(btn_eliminar)
                celda_layout.setAlignment(Qt.AlignCenter)
                celda_layout.setContentsMargins(6, 4, 6, 4)

                self.tabla.setCellWidget(fila, 3, celda_widget)

        except Exception as e:
            print(f"Error al cargar reportes: {e}")

    def eliminar_venta(self, id_venta):
        """Elimina una venta específica de la base de datos."""
        try:
            conexion = sqlite3.connect(BASE_DATOS)
            cursor = conexion.cursor()

            cursor.execute("DELETE FROM ventas WHERE id = ?", (id_venta,))
            conexion.commit()
            conexion.close()

            self.cargar_reporte()

            aviso = DialogoAviso("Venta eliminada", f"Se eliminó correctamente la venta #{id_venta}.", self)
            aviso.exec()

        except Exception as e:
            aviso_err = DialogoAviso("Error", f"No se pudo eliminar la venta: {e}", self)
            aviso_err.exec()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    v = Reportes()
    v.show()
    sys.exit(app.exec())