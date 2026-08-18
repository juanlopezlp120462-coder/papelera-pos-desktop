import sqlite3
import requests

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QToolButton,
    QDialog,
    QTextBrowser,
    QFileDialog,
    QMessageBox
)
from PySide6.QtCore import Qt
import math

from ui.db import BASE_DATOS, init_db, get_setting
from ui.ticket import (
    generar_ticket,
    imprimir_ticket,
    guardar_pdf
)


# ============================================================
# PRUEBA DE RUTA DE BASE DE DATOS
# ============================================================

try:

    with open(
        "ruta_db_prueba.txt",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(BASE_DATOS)

    print(
        "BASE DATOS HISTORIAL:",
        BASE_DATOS
    )

except Exception as e:

    print(
        "ERROR ESCRIBIENDO RUTA:",
        e
    )


class Historial(QWidget):

    def __init__(self):

        super().__init__()
        # ====================================================
        # PAGINACIÓN DEL HISTORIAL
        # ====================================================

        self.registros_por_pagina = 50
        self.pagina_actual = 1
        self.total_paginas = 1

        init_db()

        self.setWindowTitle(
            "Historial"
        )

        # ====================================================
        # MAPEO INTERNO DE FILAS
        #
        # Guarda de qué tabla proviene cada fila.
        #
        # Ejemplo:
        # self._origenes_fila[0] =
        # ("ventas", 25)
        #
        # self._origenes_fila[1] =
        # ("ventas_archivo", 10)
        #
        # Esto evita borrar una venta incorrecta
        # cuando dos tablas tienen el mismo ID.
        # ====================================================

        self._origenes_fila = []
        self.pagina_actual = 1
        self.registros_por_pagina = 50      

        self.setStyleSheet("""
        QWidget {
            background: #f8fafc;
            font-family: "Segoe UI";
            color: #0f172a;
        }

        QLineEdit, QComboBox {
            background: white;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 10px;
        }

        QPushButton {
            background: #0ea5e9;
            color: white;
            border: 0;
            border-radius: 9px;
            padding: 10px 14px;
            font-weight: 700;
        }

        QPushButton.secondary {
            background: #e2e8f0;
            color: #334155;
        }

        QPushButton.danger {
            background: #dc2626;
            color: white;
        }

        QTableWidget {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            gridline-color: #e2e8f0;
        }

        QHeaderView::section {
            background: #0f172a;
            color: white;
            padding: 10px;
            border: 0;
            font-weight: bold;
        }

        QToolButton {
            font-size: 20px;
            padding: 2px;
            background: transparent;
            border: none;
        }

        QToolButton:hover {
            background: #e2e8f0;
            border-radius: 6px;
        }
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        layout.setSpacing(
            14
        )

        # ====================================================
        # TITULO
        # ====================================================

        titulo = QLabel(
            "🕘 Historial"
        )

        titulo.setStyleSheet(
            "font-size:28px;font-weight:900;"
        )

        layout.addWidget(
            titulo
        )
                # ====================================================
        # PAGINACIÓN
        # ====================================================

        paginacion = QHBoxLayout()

        paginacion.addStretch()

        self.boton_anterior = QPushButton(
            "◀ Anterior"
        )

        self.boton_anterior.clicked.connect(
            self.pagina_anterior
        )

        paginacion.addWidget(
            self.boton_anterior
        )

        self.info_pagina = QLabel(
            "Página 1 de 1"
        )

        self.info_pagina.setStyleSheet(
            """
            font-weight:bold;
            padding:8px 14px;
            """
        )

        paginacion.addWidget(
            self.info_pagina
        )

        self.boton_siguiente = QPushButton(
            "Siguiente ▶"
        )

        self.boton_siguiente.clicked.connect(
            self.pagina_siguiente
        )

        paginacion.addWidget(
            self.boton_siguiente
        )

        paginacion.addStretch()

        layout.addLayout(
            paginacion
        )

        # ====================================================
        # BARRA DE FILTROS
        # ====================================================

        barra = QHBoxLayout()

        self.buscar = QLineEdit()

        self.buscar.setPlaceholderText(
            "Buscar ticket, fecha, cliente o forma de pago..."
        )

        self.buscar.textChanged.connect(
            self.filtro_cambiado
        )
        barra.addWidget(
            self.buscar,
            4
        )

        self.tipo = QComboBox()

        self.tipo.addItems(
            [
                "Todos",
                "Venta diaria",
                "Pedido",
                "Arqueo"
            ]
        )

        self.tipo.currentTextChanged.connect(
            self.filtro_cambiado
        )

        barra.addWidget(
            self.tipo
        )

        self.pago = QComboBox()

        self.pago.addItems(
            [
                "Todas",
                "Efectivo",
                "Tarjeta",
                "Transferencia",
                "Cuenta corriente"
            ]
        )

        self.pago.currentTextChanged.connect(
            self.filtro_cambiado
        )
        barra.addWidget(
            self.pago
        )

        # ====================================================
        # ORDENAR HISTORIAL
        # ====================================================

        self.ordenar = QComboBox()

        self.ordenar.addItems(
            [
                "Más recientes",
                "Más antiguos",
                "Número menor → mayor",
                "Número mayor → menor",
                "Total menor → mayor",
                "Total mayor → menor"
            ]
        )

        self.ordenar.setCurrentText(
            "Número mayor → menor"
        )

        self.ordenar.currentTextChanged.connect(
            self.filtro_cambiado
        )
        barra.addWidget(
            self.ordenar
        )
        

        # ====================================================
        # ACTUALIZAR / SINCRONIZAR
        # ====================================================

        boton_actualizar = QPushButton(
            "🔄 Actualizar"
        )

        boton_actualizar.setToolTip(
            "Sincronizar ventas y arqueos y actualizar el historial"
        )

        boton_actualizar.clicked.connect(
            self.actualizar_completo
        )

        barra.addWidget(
            boton_actualizar
        )

        layout.addLayout(
            barra
        )

        # ====================================================
        # ACCIONES
        # ====================================================

        acciones = QHBoxLayout()

        self.seleccionar = QPushButton(
            "☑ Seleccionar todas"
        )

        self.seleccionar.setProperty(
            "class",
            "secondary"
        )

        self.seleccionar.clicked.connect(
            self.seleccionar_todas
        )

        acciones.addWidget(
            self.seleccionar
        )

        self.eliminar = QPushButton(
            "🗑 Eliminar ventas seleccionadas"
        )

        self.eliminar.setProperty(
            "class",
            "danger"
        )

        self.eliminar.clicked.connect(
            self.eliminar_seleccionadas
        )

        acciones.addWidget(
            self.eliminar
        )

        acciones.addStretch()

        layout.addLayout(
            acciones
        )

        # ====================================================
        # RESUMEN
        # ====================================================

        resumen = QHBoxLayout()

        self.cant = QLabel(
            "Ventas: 0"
        )

        self.total = QLabel(
            "Total ventas: $ 0.00"
        )

        self.prom = QLabel(
            "Promedio: $ 0.00"
        )

        for x in (
            self.cant,
            self.total,
            self.prom
        ):

            x.setStyleSheet(
                """
                background:white;
                border:1px solid #e2e8f0;
                border-radius:12px;
                padding:12px;
                font-weight:bold;
                """
            )

            resumen.addWidget(
                x
            )

        layout.addLayout(
            resumen
        )

        # ====================================================
        # TABLA
        # ====================================================

        self.tabla = QTableWidget(
            0,
            8
        )

        self.tabla.setHorizontalHeaderLabels(
            [
                "Tipo",
                "N.º",
                "Fecha",
                "Cliente / detalle",
                "Pago",
                "Total",
                "Estado",
                "Acciones"
            ]
        )

        # ====================================================
        # ANCHOS DE COLUMNAS
        # ====================================================

        header = self.tabla.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
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
            QHeaderView.Stretch
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.Stretch
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            7,
            QHeaderView.ResizeToContents
        )

        self.tabla.setSelectionMode(
            QAbstractItemView.NoSelection
        )

        self.tabla.setAlternatingRowColors(
            True
        )

        self.tabla.cellDoubleClicked.connect(
            self._doble_click_fila
        )

        layout.addWidget(
            self.tabla
        )
        # ========================================================
        # PAGINACION
        # ========================================================

        self.pagina_actual = 1
        self.por_pagina = 15
        self.total_paginas = 1

        paginacion = QHBoxLayout()

        self.btn_anterior = QPushButton(
            "◀ Anterior"
        )

        self.btn_anterior.setProperty(
            "class",
            "secondary"
        )

        self.btn_anterior.clicked.connect(
            self.pagina_anterior
        )

        paginacion.addWidget(
            self.btn_anterior
        )

        self.lbl_pagina = QLabel(
            "Página 1 de 1"
        )

        self.lbl_pagina.setAlignment(
            Qt.AlignCenter
        )

        paginacion.addWidget(
            self.lbl_pagina
        )

        self.btn_siguiente = QPushButton(
            "Siguiente ▶"
        )

        self.btn_siguiente.setProperty(
            "class",
            "secondary"
        )

        self.btn_siguiente.clicked.connect(
            self.pagina_siguiente
        )

        paginacion.addWidget(
            self.btn_siguiente
        )

        layout.addLayout(
            paginacion
        )

    # ====================================================
    # CARGA INICIAL
    # ====================================================

    # La primera carga se realiza al mostrarse la ventana.
    # No cargar aquí para evitar una doble carga.

    # ========================================================
    # ACTUALIZAR TODO
    # ========================================================

    def actualizar_completo(self):

        try:

            QApplication.setOverrideCursor(
                Qt.WaitCursor
            )

            print(
                "========================================"
            )

            print(
                "ACTUALIZACION MANUAL DEL HISTORIAL"
            )

            self.sincronizar_ventas_nube()

            self.sincronizar_arqueos_nube()

            print(
                "RECARGANDO HISTORIAL LOCAL"
            )

            self.cargar_historial()

            print(
                "ACTUALIZACION COMPLETA OK"
            )

            print(
                "========================================"
            )

        except Exception as e:

            print(
                "ERROR ACTUALIZANDO HISTORIAL:",
                repr(e)
            )

            QMessageBox.warning(
                self,
                "Actualización",
                "No se pudo completar la actualización:\n"
                + str(e)
            )

        finally:

            QApplication.restoreOverrideCursor()

    # ========================================================
    # DOBLE CLICK
    # ========================================================

    def _doble_click_fila(
        self,
        fila,
        columna
    ):

        item = self.tabla.item(
            fila,
            0
        )

        if not item:

            return

        tipo = item.text()

        if tipo in (
            "Venta diaria",
            "Pedido"
        ):

            self.ver_ticket(
                fila
            )

        elif tipo == "Arqueo":
            self.ver_arqueo(fila)

    # ========================================================
    # UTILIDADES
    # ========================================================

    def _tabla_existe(
        self,
        cursor,
        nombre
    ):

        return cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name=?
            """,
            (nombre,)
        ).fetchone() is not None

    # ========================================================

    def _columnas_tabla(
        self,
        cursor,
        nombre
    ):

        if not self._tabla_existe(
            cursor,
            nombre
        ):

            return []

        return [
            fila[1]
            for fila in cursor.execute(
                f"PRAGMA table_info({nombre})"
            ).fetchall()
        ]

    # ========================================================

    def _tipo_venta_texto(
        self,
        valor
    ):

        texto = str(
            valor or ""
        ).strip().upper()

        if texto == "PEDIDO":

            return "Pedido"

        return "Venta diaria"

    # ========================================================

    def _es_venta(
        self,
        tipo
    ):

        return tipo in (
            "Venta diaria",
            "Pedido"
        )

    # ========================================================

    def _dinero(
        self,
        valor
    ):

        try:

            return f"$ {float(valor or 0):,.2f}"

        except Exception:

            return "$ 0.00"

    # ========================================================
    # FORMA DE PAGO SIMPLE
    # ========================================================

    def _forma_pago_coincide(
        self,
        forma_pago,
        filtro
    ):

        if filtro == "Todas":

            return True

        texto = str(
            forma_pago or ""
        ).strip().lower()

        if filtro == "Efectivo":

            return (
                "efectivo" in texto
            )

        if filtro == "Transferencia":

            return (
                "transfer" in texto
                or
                "transf" in texto
            )

        if filtro == "Tarjeta":

            return (
                "tarjeta" in texto
            )

        if filtro == "Cuenta corriente":

            return (
                "cuenta" in texto
            )

        return False

    # ========================================================
    # PAGO DETALLADO COINCIDE
    # ========================================================

    def _pago_detallado_coincide(
        self,
        pago_row,
        filtro
    ):

        if filtro == "Todas":

            return True

        e = float(
            pago_row[0] or 0
        )

        t = float(
            pago_row[1] or 0
        )

        ta = float(
            pago_row[2] or 0
        )

        c = float(
            pago_row[3] or 0
        )

        if filtro == "Efectivo":

            return e > 0

        if filtro == "Transferencia":

            return t > 0

        if filtro == "Tarjeta":

            return ta > 0

        if filtro == "Cuenta corriente":

            return c > 0

        return False

    # ========================================================
    # TEXTO DE FORMA DE PAGO
    # ========================================================

    def pago_texto(
        self,
        pay
    ):

        e, t, ta, c = pay

        partes = []

        if float(e or 0):

            partes.append(
                f"Efectivo $ {float(e):,.2f}"
            )

        if float(t or 0):

            partes.append(
                f"Transf. $ {float(t):,.2f}"
            )

        if float(ta or 0):

            partes.append(
                f"Tarjeta $ {float(ta):,.2f}"
            )

        if float(c or 0):

            partes.append(
                f"Cuenta $ {float(c):,.2f}"
            )

        return (
            " | ".join(partes)
            if partes
            else "—"
        )
    # ========================================================
    # CAMBIO DE FILTRO / BÚSQUEDA
    # ========================================================

    def filtro_cambiado(
        self
    ):

        self.pagina_actual = 1

        self.cargar_historial(
            mantener_pagina=True
        )
        
    # ========================================================
    # ACTUALIZAR AL VOLVER A ABRIR
    # ========================================================

    def showEvent(self, event):

        super().showEvent(event)

        # Solo recarga local.
        #
        # NO hacemos sincronización aquí porque showEvent
        # puede ejecutarse muchas veces.

        self.pagina_actual = 1

        self.cargar_historial()
        
    # ========================================================
    # SINCRONIZAR VENTAS DESDE LA NUBE
    # ========================================================

    def sincronizar_ventas_nube(
        self
    ):

        con = None

        try:

            api_url = get_setting(
                "api_url",
                "https://papelera-pos-backend-production.up.railway.app"
            ).rstrip("/")

            print(
                "========================================"
            )

            print(
                "SINCRONIZANDO VENTAS DESDE LA NUBE"
            )

            print(
                "SERVIDOR:",
                api_url
            )

            # ==================================================
            # OBTENER VENTAS
            # ==================================================

            response = requests.get(
                f"{api_url}/ventas",
                timeout=10
            )

            if response.status_code != 200:

                print(
                    "ERROR OBTENIENDO VENTAS:",
                    response.status_code,
                    response.text[:500]
                )

                return

            ventas_remotas = response.json()

            if not isinstance(
                ventas_remotas,
                list
            ):

                print(
                    "ERROR: respuesta de ventas no es una lista"
                )

                return

            print(
                "VENTAS REMOTAS:",
                len(ventas_remotas)
            )

            # ==================================================
            # SQLITE
            # ==================================================

            con = sqlite3.connect(
                BASE_DATOS
            )

            cur = con.cursor()

            # ==================================================
            # ASEGURAR TABLA VENTAS
            # ==================================================

            if not self._tabla_existe(
                cur,
                "ventas"
            ):

                print(
                    "ERROR: no existe tabla ventas"
                )

                return

            # ==================================================
            # ASEGURAR UUID
            # ==================================================

            columnas = self._columnas_tabla(
                cur,
                "ventas"
            )

            if "uuid" not in columnas:

                cur.execute(
                    """
                    ALTER TABLE ventas
                    ADD COLUMN uuid TEXT
                    """
                )

                columnas = self._columnas_tabla(
                    cur,
                    "ventas"
                )

            # ==================================================
            # ASEGURAR TIPO
            # ==================================================

            if "tipo" not in columnas:

                cur.execute(
                    """
                    ALTER TABLE ventas
                    ADD COLUMN tipo TEXT
                    """
                )

                columnas = self._columnas_tabla(
                    cur,
                    "ventas"
                )

            # ==================================================
            # DETALLE
            # ==================================================

            columnas_detalle = self._columnas_tabla(
                cur,
                "detalle_ventas"
            )

            if (
                columnas_detalle
                and
                "codigo" not in columnas_detalle
            ):

                cur.execute(
                    """
                    ALTER TABLE detalle_ventas
                    ADD COLUMN codigo TEXT
                    """
                )

            con.commit()

            # ==================================================
            # FECHAS CERRADAS
            # ==================================================

            fechas_cerradas = set()

            if self._tabla_existe(
                cur,
                "arqueos"
            ):

                filas_arqueos = cur.execute(
                    """
                    SELECT fecha
                    FROM arqueos
                    WHERE fecha IS NOT NULL
                    """
                ).fetchall()

                for fila in filas_arqueos:

                    fecha_arqueo = fila[0]

                    if fecha_arqueo:

                        fecha_dia = str(
                            fecha_arqueo
                        )[:10]

                        fechas_cerradas.add(
                            fecha_dia
                        )

            print(
                "FECHAS CERRADAS:",
                sorted(fechas_cerradas)
            )

            ventas_nuevas = 0
            ventas_actualizadas = 0
            detalles_nuevos = 0
            errores_detalle = 0

            # ==================================================
            # CADA VENTA REMOTA
            # ==================================================

            for v in ventas_remotas:

                if not isinstance(
                    v,
                    dict
                ):

                    continue

                uuid_venta = v.get(
                    "uuid"
                )

                if not uuid_venta:

                    print(
                        "VENTA REMOTA SIN UUID:",
                        v
                    )

                    continue

                fecha_venta = v.get(
                    "fecha"
                )

                fecha_dia_venta = ""

                if fecha_venta:

                    fecha_dia_venta = str(
                        fecha_venta
                    )[:10]

                # ==================================================
                # BUSCAR LOCAL
                #
                # IMPORTANTE:
                # También recuperamos pedido_id para no perder
                # la identificación de los pedidos durante
                # la sincronización.
                # ==================================================

                columnas_ventas_actuales = self._columnas_tabla(
                    cur,
                    "ventas"
                )

                tiene_pedido_id = (
                    "pedido_id" in columnas_ventas_actuales
                )

                if tiene_pedido_id:

                    venta_local = cur.execute(
                        """
                        SELECT
                            id,
                            estado,
                            COALESCE(tipo, ''),
                            pedido_id
                        FROM ventas
                        WHERE uuid=?
                        LIMIT 1
                        """,
                        (uuid_venta,)
                    ).fetchone()

                else:

                    venta_local = cur.execute(
                        """
                        SELECT
                            id,
                            estado,
                            COALESCE(tipo, ''),
                            NULL
                        FROM ventas
                        WHERE uuid=?
                        LIMIT 1
                        """,
                        (uuid_venta,)
                    ).fetchone()

                estado_remoto = v.get(
                    "estado",
                    "ACTIVA"
                )

                # ==================================================
                # ESTADO FINAL
                # ==================================================

                if fecha_dia_venta in fechas_cerradas:

                    estado_final = "ARCHIVADA"

                elif (
                    venta_local
                    and
                    str(
                        venta_local[1] or ""
                    ).upper() == "ARCHIVADA"
                ):

                    estado_final = "ARCHIVADA"

                else:

                    estado_final = estado_remoto

                # ==================================================
                # TIPO FINAL
                #
                # Un registro es PEDIDO si cualquiera de estas
                # condiciones lo identifica como tal:
                #
                # 1. La nube informa tipo = PEDIDO
                # 2. La nube informa origen = PEDIDO
                # 3. La nube informa pedido_id
                # 4. La copia local ya tiene tipo = PEDIDO
                # 5. La copia local ya tiene pedido_id
                #
                # Esto evita que una sincronización convierta
                # accidentalmente un PEDIDO en VENTA DIARIA.
                # ==================================================

                tipo_remoto = str(
                    v.get(
                        "tipo",
                        ""
                    ) or ""
                ).strip().upper()

                origen_remoto = str(
                    v.get(
                        "origen",
                        ""
                    ) or ""
                ).strip().upper()

                pedido_id_remoto = v.get(
                    "pedido_id"
                )

                tipo_local = ""

                pedido_id_local = None

                if venta_local:

                    tipo_local = str(
                        venta_local[2] or ""
                    ).strip().upper()

                    pedido_id_local = venta_local[3]


                # ==================================================
                # DETERMINAR SI ES PEDIDO
                # ==================================================

                es_pedido = (

                    tipo_remoto == "PEDIDO"

                    or

                    origen_remoto == "PEDIDO"

                    or

                    pedido_id_remoto is not None

                    or

                    tipo_local == "PEDIDO"

                    or

                    pedido_id_local is not None
                )


                if es_pedido:

                    tipo_final = "PEDIDO"

                else:

                    tipo_final = "VENTA"


                print(
                    "TIPO SINCRONIZADO:",
                    uuid_venta,
                    "| remoto:",
                    tipo_remoto,
                    "| origen:",
                    origen_remoto,
                    "| pedido_id remoto:",
                    pedido_id_remoto,
                    "| tipo local:",
                    tipo_local,
                    "| pedido_id local:",
                    pedido_id_local,
                    "| FINAL:",
                    tipo_final
                )
                # ==================================================
                # ACTUALIZAR EXISTENTE
                # ==================================================

                if venta_local:

                    venta_id_local = venta_local[0]

                    cur.execute(
                        """
                        UPDATE ventas
                        SET
                            fecha=?,
                            total=?,
                            forma_pago=?,
                            cliente_id=?,
                            estado=?,
                            pago_efectivo=?,
                            pago_transferencia=?,
                            pago_tarjeta=?,
                            pago_cuenta=?,
                            tipo=?,
                            pedido_id=?
                        WHERE id=?
                        """,
                        (
                            fecha_venta,
                            v.get("total", 0),
                            v.get("forma_pago", ""),
                            v.get("cliente_id", 0),
                            estado_final,
                            v.get("pago_efectivo", 0),
                            v.get("pago_transferencia", 0),
                            v.get("pago_tarjeta", 0),
                            v.get("pago_cuenta", 0),
                            tipo_final,
                            pedido_id_remoto,
                            venta_id_local
                        )
                    )

                    ventas_actualizadas += 1

                # ==================================================
                # VENTA NUEVA
                # ==================================================

                else:

                    cur.execute(
                        """
                        INSERT INTO ventas(
                            uuid,
                            fecha,
                            total,
                            forma_pago,
                            cliente_id,
                            estado,
                            pago_efectivo,
                            pago_transferencia,
                            pago_tarjeta,
                            pago_cuenta,
                            tipo
                        )
                        VALUES(
                            ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?
                        )
                        """,
                        (
                            uuid_venta,

                            fecha_venta,

                            v.get(
                                "total",
                                0
                            ),

                            v.get(
                                "forma_pago",
                                ""
                            ),

                            v.get(
                                "cliente_id",
                                0
                            ),

                            estado_final,

                            v.get(
                                "pago_efectivo",
                                0
                            ),

                            v.get(
                                "pago_transferencia",
                                0
                            ),

                            v.get(
                                "pago_tarjeta",
                                0
                            ),

                            v.get(
                                "pago_cuenta",
                                0
                            ),

                            tipo_final
                        )
                    )

                    venta_id_local = cur.lastrowid

                    ventas_nuevas += 1

                # ==================================================
                # DETALLE
                # ==================================================

                id_venta_remota = v.get(
                    "id"
                )

                if not id_venta_remota:

                    print(
                        "VENTA SIN ID REMOTO:",
                        uuid_venta
                    )

                    continue

                if not self._tabla_existe(
                    cur,
                    "detalle_ventas"
                ):

                    continue

                try:

                    detalle_response = requests.get(
                        f"{api_url}/ventas/{id_venta_remota}/detalle",
                        timeout=10
                    )

                    if detalle_response.status_code != 200:

                        print(
                            "ERROR DETALLE VENTA",
                            id_venta_remota,
                            ":",
                            detalle_response.status_code
                        )

                        errores_detalle += 1

                        continue

                    detalles_remotos = detalle_response.json()

                    if not isinstance(
                        detalles_remotos,
                        list
                    ):

                        continue

                    # ==================================================
                    # BORRAR DETALLE ANTERIOR
                    # ==================================================

                    cur.execute(
                        """
                        DELETE FROM detalle_ventas
                        WHERE venta_id=?
                        """,
                        (venta_id_local,)
                    )

                    columnas_detalle = self._columnas_tabla(
                        cur,
                        "detalle_ventas"
                    )

                    tiene_codigo = (
                        "codigo"
                        in
                        columnas_detalle
                    )

                    # ==================================================
                    # INSERTAR DETALLE
                    # ==================================================

                    for d in detalles_remotos:

                        if not isinstance(
                            d,
                            dict
                        ):

                            continue

                        producto = d.get(
                            "producto",
                            ""
                        )

                        cantidad = d.get(
                            "cantidad",
                            0
                        )

                        precio = d.get(
                            "precio",
                            0
                        )

                        subtotal = d.get(
                            "subtotal",
                            0
                        )

                        codigo = d.get(
                            "codigo"
                        )

                        if tiene_codigo:

                            cur.execute(
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
                                    venta_id_local,
                                    str(producto),
                                    cantidad,
                                    precio,
                                    subtotal,
                                    codigo
                                )
                            )

                        else:

                            cur.execute(
                                """
                                INSERT INTO detalle_ventas(
                                    venta_id,
                                    producto,
                                    cantidad,
                                    precio,
                                    subtotal
                                )
                                VALUES(
                                    ?, ?, ?, ?, ?
                                )
                                """,
                                (
                                    venta_id_local,
                                    str(producto),
                                    cantidad,
                                    precio,
                                    subtotal
                                )
                            )

                        detalles_nuevos += 1

                except Exception as e:

                    errores_detalle += 1

                    print(
                        "ERROR SINCRONIZANDO DETALLE:",
                        id_venta_remota,
                        e
                    )

            con.commit()

            print(
                "----------------------------------------"
            )

            print(
                "VENTAS NUEVAS:",
                ventas_nuevas
            )

            print(
                "VENTAS ACTUALIZADAS:",
                ventas_actualizadas
            )

            print(
                "DETALLES SINCRONIZADOS:",
                detalles_nuevos
            )

            print(
                "ERRORES DETALLE:",
                errores_detalle
            )

            print(
                "VENTAS ACTIVAS LOCALES:",
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM ventas
                    WHERE COALESCE(
                        estado,
                        'ACTIVA'
                    )='ACTIVA'
                    """
                ).fetchone()[0]
            )

            print(
                "VENTAS ARCHIVADAS LOCALES:",
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM ventas
                    WHERE estado='ARCHIVADA'
                    """
                ).fetchone()[0]
            )

            print(
                "SINCRONIZACION DE VENTAS OK"
            )

            print(
                "========================================"
            )

        except Exception as e:

            if con:

                try:

                    con.rollback()

                except Exception:

                    pass

            print(
                "ERROR AL SINCRONIZAR VENTAS:",
                repr(e)
            )

        finally:

            if con:

                try:

                    con.close()

                except Exception:

                    pass

    # ========================================================
    # SINCRONIZAR ARQUEOS
    # ========================================================

    def asegurar_columnas_arqueo(self, cur):
        columnas = {fila[1] for fila in cur.execute("PRAGMA table_info(arqueos)").fetchall()}
        campos = {
            "ventas_total": "REAL DEFAULT 0",
            "ventas_efectivo": "REAL DEFAULT 0",
            "ventas_transferencia": "REAL DEFAULT 0",
            "ventas_tarjeta": "REAL DEFAULT 0",
            "ventas_cuenta": "REAL DEFAULT 0",
            "cantidad_ventas": "INTEGER DEFAULT 0",
        }
        for nombre, tipo in campos.items():
            if nombre not in columnas:
                cur.execute(f"ALTER TABLE arqueos ADD COLUMN {nombre} {tipo}")

    def asegurar_columna_movimientos_arqueo(self, cur):
        existe = cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='movimientos_caja'"
        ).fetchone()
        if not existe:
            return

        columnas = {fila[1] for fila in cur.execute(
            "PRAGMA table_info(movimientos_caja)"
        ).fetchall()}

        if "arqueo_id" not in columnas:
            cur.execute(
                "ALTER TABLE movimientos_caja ADD COLUMN arqueo_id INTEGER"
            )

        cur.execute(
            """
            UPDATE movimientos_caja
            SET arqueo_id = (
                SELECT MIN(a.id)
                FROM arqueos a
                WHERE substr(a.fecha,1,10) = substr(movimientos_caja.fecha,1,10)
                  AND a.fecha >= movimientos_caja.fecha
            )
            WHERE arqueo_id IS NULL
            """
        )


    def sincronizar_arqueos_nube(
        self
    ):

        con = None

        try:

            api_url = get_setting(
                "api_url",
                "https://papelera-pos-backend-production.up.railway.app"
            ).rstrip("/")

            response = requests.get(
                f"{api_url}/caja/arqueos",
                timeout=5
            )

            if response.status_code != 200:

                print(
                    "ERROR OBTENIENDO ARQUEOS:",
                    response.status_code
                )

                return

            arqueos_remotos = response.json()

            if not isinstance(
                arqueos_remotos,
                list
            ):

                print(
                    "ERROR: respuesta de arqueos no es una lista"
                )

                return

            con = sqlite3.connect(
                BASE_DATOS
            )

            cur = con.cursor()

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS arqueos(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT UNIQUE,
                    fecha TEXT,
                    apertura REAL,
                    esperado REAL,
                    real REAL,
                    diferencia REAL,
                    usuario TEXT,
                    observaciones TEXT,
                    ventas_total REAL,
                    ventas_efectivo REAL,
                    cantidad_ventas INTEGER
                )
                """
            )
            self.asegurar_columnas_arqueo(cur)
            self.asegurar_columna_movimientos_arqueo(cur)

            for arq in arqueos_remotos:

                if not isinstance(
                    arq,
                    dict
                ):

                    continue

                uuid = arq.get(
                    "uuid"
                )

                if not uuid:

                    continue

                cur.execute(
                    """
                    INSERT OR IGNORE INTO arqueos(
                        uuid,
                        fecha,
                        apertura,
                        esperado,
                        real,
                        diferencia,
                        usuario,
                        observaciones,
                        ventas_total,
                        ventas_efectivo,
                        ventas_transferencia,
                        ventas_tarjeta,
                        ventas_cuenta,
                        cantidad_ventas
                    )
                    VALUES(
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        uuid,
                        arq.get("fecha"),
                        arq.get("apertura"),
                        arq.get("esperado"),
                        arq.get("real"),
                        arq.get("diferencia"),
                        arq.get("usuario"),
                        arq.get("observaciones"),
                        arq.get("ventas_total"),
                        arq.get("ventas_efectivo"),
                        arq.get("ventas_transferencia", 0),
                        arq.get("ventas_tarjeta", 0),
                        arq.get("ventas_cuenta", 0),
                        arq.get("cantidad_ventas")
                    )
                )

            con.commit()

            print(
                "SINCRONIZACION DE ARQUEOS OK"
            )

        except Exception as e:

            if con:

                try:

                    con.rollback()

                except Exception:

                    pass

            print(
                "No se pudieron sincronizar los arqueos desde la nube:",
                e
            )

        finally:

            if con:

                try:

                    con.close()

                except Exception:

                    pass
    # ========================================================
    # PAGINACIÓN
    # ========================================================

    def actualizar_controles_paginacion(
        self
    ):

        self.info_pagina.setText(
            f"Página {self.pagina_actual} de {self.total_paginas}"
        )

        self.boton_anterior.setEnabled(
            self.pagina_actual > 1
        )

        self.boton_siguiente.setEnabled(
            self.pagina_actual < self.total_paginas
        )


    def pagina_anterior(
        self
    ):

        if self.pagina_actual <= 1:

            return

        self.pagina_actual -= 1

        self.cargar_historial(
            mantener_pagina=True
        )



    def pagina_siguiente(
        self
    ):

        if self.pagina_actual >= self.total_paginas:

            return

        self.pagina_actual += 1

        self.cargar_historial(
            mantener_pagina=True
        )


    def reiniciar_paginacion(
        self
    ):

        self.pagina_actual = 1
    # ========================================================
    # CARGAR HISTORIAL
    # ========================================================

    def cargar_historial(self, mantener_pagina=False):
        c = None

        try:

            c = sqlite3.connect(
                BASE_DATOS
            )

            q = c.cursor()

            termino = self.buscar.text().strip()
            tipo_filtro = self.tipo.currentText()
            pago_filtro = self.pago.currentText()

            filas = []

            # ==================================================
            # VENTAS
            #
            # OPTIMIZADO:
            # - Una sola consulta por tabla.
            # - Los pagos se obtienen junto con la venta.
            # - Se eliminan las consultas repetidas dentro
            #   del for de cada venta.
            # ==================================================

            if tipo_filtro in (
                "Todos",
                "Venta diaria",
                "Pedido"
            ):

                tablas = [
                    ("ventas", "ACTIVA"),
                    ("ventas_archivo", "ARCHIVADA")
                ]

                for tabla, estado_defecto in tablas:

                    if not self._tabla_existe(
                        q,
                        tabla
                    ):

                        continue

                    columnas = self._columnas_tabla(
                        q,
                        tabla
                    )

                    tiene_tipo = (
                        "tipo" in columnas
                    )

                    tiene_pagos = all(
                        columna in columnas
                        for columna in (
                            "pago_efectivo",
                            "pago_transferencia",
                            "pago_tarjeta",
                            "pago_cuenta"
                        )
                    )

                    # ==================================================
                    # TIPO
                    # ==================================================

                    if tiene_tipo:

                        expresion_tipo = """
                            CASE
                                WHEN UPPER(
                                    TRIM(
                                        COALESCE(
                                            v.tipo,
                                            ''
                                        )
                                    )
                                ) = 'PEDIDO'
                                THEN 'Pedido'
                                ELSE 'Venta diaria'
                            END
                        """

                    else:

                        expresion_tipo = "'Venta diaria'"

                    # ==================================================
                    # PAGOS
                    #
                    # Si existen las columnas, las traemos directamente
                    # en la misma consulta.
                    # ==================================================

                    if tiene_pagos:

                        expresion_pago_efectivo = """
                            COALESCE(
                                v.pago_efectivo,
                                0
                            )
                        """

                        expresion_pago_transferencia = """
                            COALESCE(
                                v.pago_transferencia,
                                0
                            )
                        """

                        expresion_pago_tarjeta = """
                            COALESCE(
                                v.pago_tarjeta,
                                0
                            )
                        """

                        expresion_pago_cuenta = """
                            COALESCE(
                                v.pago_cuenta,
                                0
                            )
                        """

                    else:

                        expresion_pago_efectivo = "0"
                        expresion_pago_transferencia = "0"
                        expresion_pago_tarjeta = "0"
                        expresion_pago_cuenta = "0"

                    # ==================================================
                    # SQL
                    # ==================================================

                    sql = f"""
                        SELECT
                            {expresion_tipo},
                            v.id,
                            v.fecha,
                            COALESCE(
                                cl.nombre,
                                'Consumidor final'
                            ),
                            COALESCE(
                                v.forma_pago,
                                ''
                            ),
                            COALESCE(
                                v.total,
                                0
                            ),
                            COALESCE(
                                v.estado,
                                '{estado_defecto}'
                            ),
                            {expresion_pago_efectivo},
                            {expresion_pago_transferencia},
                            {expresion_pago_tarjeta},
                            {expresion_pago_cuenta}
                        FROM {tabla} v
                        LEFT JOIN clientes cl
                            ON cl.id = v.cliente_id
                        WHERE 1=1
                    """

                    datos = []

                    # ==================================================
                    # BUSQUEDA
                    # ==================================================

                    if termino:

                        sql += """
                            AND (
                                CAST(v.id AS TEXT) LIKE ?
                                OR v.fecha LIKE ?
                                OR cl.nombre LIKE ?
                                OR v.forma_pago LIKE ?
                            )
                        """

                        buscar = (
                            "%"
                            + termino
                            + "%"
                        )

                        datos.extend(
                            [
                                buscar,
                                buscar,
                                buscar,
                                buscar
                            ]
                        )

                    # ==================================================
                    # FILTRO TIPO
                    # ==================================================

                    if tipo_filtro == "Pedido":

                        if tiene_tipo:

                            sql += """
                                AND UPPER(
                                    TRIM(
                                        COALESCE(
                                            v.tipo,
                                            ''
                                        )
                                    )
                                ) = 'PEDIDO'
                            """

                        else:

                            continue

                    elif tipo_filtro == "Venta diaria":

                        if tiene_tipo:

                            sql += """
                                AND (
                                    UPPER(
                                        TRIM(
                                            COALESCE(
                                                v.tipo,
                                                ''
                                            )
                                        )
                                    ) <> 'PEDIDO'
                                    OR v.tipo IS NULL
                                    OR TRIM(v.tipo) = ''
                                )
                            """

                    # ==================================================
                    # ORDENAR DESDE SQLITE
                    #
                    # Así evitamos ordenar posteriormente una cantidad
                    # grande de registros innecesariamente.
                    # ==================================================

                    sql += """
                        ORDER BY v.fecha DESC
                    """

                    resultado = q.execute(
                        sql,
                        datos
                    ).fetchall()

                    # ==================================================
                    # PROCESAR FILAS
                    # ==================================================

                    for fila in resultado:

                        tipo_mostrar = str(
                            fila[0]
                            or "Venta diaria"
                        )

                        # ----------------------------------------------
                        # PAGOS
                        # ----------------------------------------------

                        pago_row = (
                            float(fila[7] or 0),
                            float(fila[8] or 0),
                            float(fila[9] or 0),
                            float(fila[10] or 0)
                        )

                        # ----------------------------------------------
                        # FILTRO DE PAGO
                        # ----------------------------------------------

                        if pago_filtro != "Todas":

                            if tiene_pagos:

                                if not self._pago_detallado_coincide(
                                    pago_row,
                                    pago_filtro
                                ):

                                    continue

                            else:

                                if not self._forma_pago_coincide(
                                    fila[4],
                                    pago_filtro
                                ):

                                    continue

                        # ----------------------------------------------
                        # TEXTO DE PAGO
                        # ----------------------------------------------

                        pago_mostrar = fila[4]

                        if tiene_pagos:

                            suma_pagos = sum(
                                pago_row
                            )

                            if suma_pagos > 0:

                                pago_mostrar = self.pago_texto(
                                    pago_row
                                )

                        # ----------------------------------------------
                        # FILA FINAL
                        # ----------------------------------------------

                        fila_base = (
                            tipo_mostrar,
                            fila[1],
                            fila[2],
                            fila[3],
                            pago_mostrar,
                            fila[5],
                            fila[6]
                        )

                        filas.append(
                            (
                                fila_base,
                                tabla
                            )
                        )

            # ==================================================
            # ARQUEOS
            # ==================================================

            if tipo_filtro in (
                "Todos",
                "Arqueo"
            ):

                if self._tabla_existe(
                    q,
                    "arqueos"
                ):

                    sql = """
                        SELECT
                            'Arqueo',
                            id,
                            fecha,
                            (
                                'Efectivo: $ ' ||
                                printf(
                                    '%.2f',
                                    COALESCE(
                                        ventas_efectivo,
                                        0
                                    )
                                ) ||
                                ' | Transf.: $ ' ||
                                printf(
                                    '%.2f',
                                    COALESCE(
                                        ventas_transferencia,
                                        0
                                    )
                                ) ||
                                ' | Tarjeta: $ ' ||
                                printf(
                                    '%.2f',
                                    COALESCE(
                                        ventas_tarjeta,
                                        0
                                    )
                                ) ||
                                ' | Cuenta: $ ' ||
                                printf(
                                    '%.2f',
                                    COALESCE(
                                        ventas_cuenta,
                                        0
                                    )
                                )
                            ),
                            'Todos los medios',
                            COALESCE(
                                ventas_total,
                                0
                            ),
                            'GUARDADO'
                        FROM arqueos
                        WHERE 1=1
                    """

                    datos = []

                    if termino:

                        sql += """
                            AND (
                                CAST(id AS TEXT) LIKE ?
                                OR fecha LIKE ?
                            )
                        """

                        buscar = (
                            "%"
                            + termino
                            + "%"
                        )

                        datos.extend(
                            [
                                buscar,
                                buscar
                            ]
                        )

                    sql += """
                        ORDER BY fecha DESC
                    """

                    resultados_arqueos = q.execute(
                        sql,
                        datos
                    ).fetchall()

                    for fila in resultados_arqueos:

                        filas.append(
                            (
                                fila,
                                "arqueos"
                            )
                        )

            # ==================================================
            # MOVIMIENTOS DE CAJA
            # ==================================================

            if tipo_filtro == "Todos":

                if self._tabla_existe(
                    q,
                    "movimientos_caja"
                ):

                    resultados_mov = q.execute(
                        """
                        SELECT
                            'Movimiento caja',
                            id,
                            fecha,
                            COALESCE(
                                concepto,
                                ''
                            ),
                            tipo,
                            importe,
                            COALESCE(
                                usuario,
                                'Administrador'
                            )
                        FROM movimientos_caja
                        ORDER BY fecha DESC
                        """
                    ).fetchall()

                    for fila in resultados_mov:

                        filas.append(
                            (
                                fila,
                                "movimientos_caja"
                            )
                        )

            # ==================================================
            # ORDEN FINAL
            # ==================================================
            #
            # Se combinan ventas, pedidos, arqueos y movimientos
            # en una sola lista.
            #
            # El usuario puede elegir cómo ordenarlos.
            # ==================================================

            orden = self.ordenar.currentText()

            if orden == "Más recientes":

                filas.sort(
                    key=lambda x: str(
                        x[0][2] or ""
                    ),
                    reverse=True
                )

            elif orden == "Más antiguos":

                filas.sort(
                    key=lambda x: str(
                        x[0][2] or ""
                    )
                )

            elif orden == "Número menor → mayor":

                filas.sort(
                    key=lambda x: (
                        int(x[0][1])
                        if str(x[0][1]).isdigit()
                        else 0
                    )
                )

            elif orden == "Número mayor → menor":

                filas.sort(
                    key=lambda x: (
                        int(x[0][1])
                        if str(x[0][1]).isdigit()
                        else 0
                    ),
                    reverse=True
                )

            elif orden == "Total menor → mayor":

                filas.sort(
                    key=lambda x: (
                        float(x[0][5] or 0)
                    )
                )

            elif orden == "Total mayor → menor":

                filas.sort(
                    key=lambda x: (
                        float(x[0][5] or 0)
                    ),
                    reverse=True
                )

            # ========================================================
            # PAGINACION
            # ========================================================

            total_registros = len(filas)

            self.total_paginas = max(
                1,
                (total_registros + self.por_pagina - 1)
                // self.por_pagina
            )
            self.lbl_pagina.setText(
                f"Página {self.pagina_actual} de {self.total_paginas}"
            )

            self.btn_anterior.setEnabled(
                self.pagina_actual > 1
            )

            self.btn_siguiente.setEnabled(
                self.pagina_actual < self.total_paginas
            )

            self.pagina_actual = min(
                self.pagina_actual,
                self.total_paginas
            )

            inicio = (
                self.pagina_actual - 1
            ) * self.por_pagina

            fin = inicio + self.por_pagina

            filas_pagina = filas[
                inicio:fin
            ]

            # ========================================================
            # LIMPIAR TABLA
            # ========================================================

            self.tabla.setUpdatesEnabled(False)
            self.tabla.setSortingEnabled(False)

            self.tabla.setRowCount(
                len(filas_pagina)
            )

            self._origenes_fila = []

            print(
                "CREANDO TABLA CON:",
                len(filas),
                "REGISTROS"
            )

            total_ventas = 0
            cantidad_ventas = 0

            # ==================================================
            # PINTAR TABLA
            # ==================================================

            for i, registro in enumerate(
                filas_pagina
            ):

                fila = registro[0]
                origen = registro[1]


                tipo_fila = str(
                    fila[0]
                )

                # ==================================================
                # ORIGEN
                # ==================================================

                self._origenes_fila.append(
                    (
                        origen,
                        fila[1]
                    )
                )

                # ==================================================
                # CELDAS
                # ==================================================

                for j, valor in enumerate(
                    fila[:7]
                ):

                    if j == 5:

                        texto = self._dinero(
                            valor
                        )

                    else:

                        texto = str(
                            valor
                            if valor is not None
                            else ""
                        )

                    item = QTableWidgetItem(
                        texto
                    )

                    if (
                        j == 0
                        and
                        self._es_venta(
                            tipo_fila
                        )
                    ):

                        item.setFlags(
                            item.flags()
                            |
                            Qt.ItemIsUserCheckable
                        )

                        item.setCheckState(
                            Qt.Unchecked
                        )

                    self.tabla.setItem(
                        i,
                        j,
                        item
                    )

                # ==================================================
                # ACCIONES
                # ==================================================

                widget_acciones = QWidget()

                layout_acciones = QHBoxLayout(
                    widget_acciones
                )

                layout_acciones.setContentsMargins(
                    4,
                    2,
                    4,
                    2
                )

                layout_acciones.setSpacing(
                    4
                )

                layout_acciones.setAlignment(
                    Qt.AlignCenter
                )

                # ==================================================
                # VENTA / PEDIDO
                # ==================================================

                if self._es_venta(
                    tipo_fila
                ):

                    btn_ver = QToolButton()

                    btn_ver.setText(
                        "👁"
                    )

                    btn_ver.setToolTip(
                        "Ver ticket"
                    )

                    btn_ver.clicked.connect(
                        lambda checked=False,
                        r=i:
                        self.ver_ticket(r)
                    )

                    btn_pdf = QToolButton()

                    btn_pdf.setText(
                        "💾"
                    )

                    btn_pdf.setToolTip(
                        "Guardar PDF"
                    )

                    btn_pdf.clicked.connect(
                        lambda checked=False,
                        r=i:
                        self.pdf_ticket(r)
                    )

                    btn_print = QToolButton()

                    btn_print.setText(
                        "🖨️"
                    )

                    btn_print.setToolTip(
                        "Imprimir ticket"
                    )

                    btn_print.clicked.connect(
                        lambda checked=False,
                        r=i:
                        self.imprimir(r)
                    )

                # ==================================================
                # ARQUEO
                # ==================================================

                elif tipo_fila == "Arqueo":

                    btn_ver = QToolButton()

                    btn_ver.setText(
                        "👁"
                    )

                    btn_ver.setToolTip(
                        "Ver arqueo"
                    )

                    btn_ver.clicked.connect(
                        lambda checked=False,
                        r=i:
                        self.ver_arqueo(r)
                    )

                    btn_pdf = QToolButton()

                    btn_pdf.setText(
                        "💾"
                    )

                    btn_pdf.setToolTip(
                        "Guardar arqueo PDF"
                    )

                    btn_pdf.clicked.connect(
                        lambda checked=False,
                        r=i:
                        self.pdf_arqueo(r)
                    )

                    btn_print = QToolButton()

                    btn_print.setText(
                        "🖨️"
                    )

                    btn_print.setToolTip(
                        "Imprimir arqueo"
                    )

                    btn_print.clicked.connect(
                        lambda checked=False,
                        r=i:
                        self.imprimir_arqueo(r)
                    )

                # ==================================================
                # MOVIMIENTO DE CAJA
                # ==================================================

                if tipo_fila == "Movimiento caja":

                    btn_ver = QToolButton()

                    btn_ver.setText(
                        "💰"
                    )

                    btn_ver.setToolTip(
                        "Movimiento de caja"
                    )

                    btn_ver.setEnabled(
                        False
                    )

                    btn_pdf = QToolButton()

                    btn_pdf.setText(
                        ""
                    )

                    btn_pdf.setEnabled(
                        False
                    )

                    btn_print = QToolButton()

                    btn_print.setText(
                        ""
                    )

                    btn_print.setEnabled(
                        False
                    )

                layout_acciones.addWidget(
                    btn_ver
                )

                layout_acciones.addWidget(
                    btn_pdf
                )

                layout_acciones.addWidget(
                    btn_print
                )

                self.tabla.setCellWidget(
                    i,
                    7,
                    widget_acciones
                )

                # ==================================================
                # RESUMEN
                # ==================================================

                if self._es_venta(
                    tipo_fila
                ):

                    try:

                        total_ventas += float(
                            fila[5] or 0
                        )

                    except Exception:

                        pass

                    cantidad_ventas += 1

            # ==================================================
            # RESUMEN FINAL
            # ==================================================

            self.cant.setText(
                f"Ventas: {cantidad_ventas}"
            )

            self.total.setText(
                "Total ventas: "
                + self._dinero(
                    total_ventas
                )
            )

            promedio = (
                total_ventas / cantidad_ventas
                if cantidad_ventas
                else 0
            )

            self.prom.setText(
                "Promedio: "
                + self._dinero(
                    promedio
                )
            )
            self.tabla.setUpdatesEnabled(True)
            self.tabla.viewport().update()

        except Exception as e:

            try:

                with open(
                    "error_historial.txt",
                    "w",
                    encoding="utf-8"
                ) as archivo:

                    archivo.write(
                        repr(e)
                    )

            except Exception:

                pass

            print(
                "ERROR CARGANDO HISTORIAL:",
                repr(e)
            )

            QMessageBox.critical(
                self,
                "Error",
                "No se pudo cargar historial:\n"
                + str(e)
            )

        finally:

            if c:

                try:

                    c.close()

                except Exception:

                    pass
    # ========================================================
    # PAGINA ANTERIOR
    # ========================================================

    def pagina_anterior(
        self
    ):

        if self.pagina_actual > 1:

            self.pagina_actual -= 1

            self.cargar_historial()


    # ========================================================
    # PAGINA SIGUIENTE
    # ========================================================

    def pagina_siguiente(
        self
    ):

        if self.pagina_actual < self.total_paginas:

            self.pagina_actual += 1

            self.cargar_historial()
    # ========================================================
    # SELECCIONAR TODAS
    # ========================================================

    def seleccionar_todas(
        self
    ):

        for r in range(
            self.tabla.rowCount()
        ):

            item = self.tabla.item(
                r,
                0
            )

            if (
                item
                and
                self._es_venta(
                    item.text()
                )
            ):

                item.setCheckState(
                    Qt.Checked
                )

    # ========================================================
    # ELIMINAR VENTAS SELECCIONADAS
    # ========================================================

    def eliminar_seleccionadas(
        self
    ):

        registros = []

        for r in range(
            self.tabla.rowCount()
        ):

            tipo = self.tabla.item(
                r,
                0
            )

            numero = self.tabla.item(
                r,
                1
            )

            if not (
                tipo
                and
                numero
            ):

                continue

            if not self._es_venta(
                tipo.text()
            ):

                continue

            if (
                tipo.checkState()
                != Qt.Checked
            ):

                continue

            try:

                numero_id = int(
                    numero.text()
                )

            except Exception:

                continue

            # ==================================================
            # OBTENER TABLA REAL DE ORIGEN
            # ==================================================

            if (
                r >= len(
                    self._origenes_fila
                )
            ):

                continue

            origen, id_origen = (
                self._origenes_fila[r]
            )

            if origen not in (
                "ventas",
                "ventas_archivo"
            ):

                continue

            registros.append(
                (
                    origen,
                    numero_id
                )
            )

        if not registros:

            QMessageBox.information(
                self,
                "Historial",
                "Seleccioná al menos una venta."
            )

            return

        confirmar = QMessageBox.question(
            self,
            "Eliminar ventas",
            (
                f"Se eliminarán {len(registros)} ventas.\n\n"
                "Esta acción eliminará también sus detalles.\n\n"
                "¿Continuar?"
            ),
            QMessageBox.Yes |
            QMessageBox.No
        )

        if confirmar != QMessageBox.Yes:

            return

        con = None

        try:

            con = sqlite3.connect(
                BASE_DATOS
            )

            # ==================================================
            # AGRUPAR POR TABLA
            # ==================================================

            por_tabla = {}

            for tabla, numero_id in registros:

                por_tabla.setdefault(
                    tabla,
                    []
                ).append(
                    numero_id
                )

            # ==================================================
            # ELIMINAR CADA VENTA
            # DE SU TABLA CORRESPONDIENTE
            # ==================================================

            for tabla_ventas, ids in por_tabla.items():

                if not self._tabla_existe(
                    con,
                    tabla_ventas
                ):

                    continue

                # ==================================================
                # TABLA DE DETALLES CORRESPONDIENTE
                # ==================================================

                if tabla_ventas == "ventas":

                    tabla_detalle = "detalle_ventas"

                else:

                    tabla_detalle = "detalle_ventas_archivo"

                marcas = ",".join(
                    "?"
                    for _ in ids
                )

                # ==================================================
                # BORRAR DETALLES
                # ==================================================

                if self._tabla_existe(
                    con,
                    tabla_detalle
                ):

                    con.execute(
                        f"""
                        DELETE FROM {tabla_detalle}
                        WHERE venta_id IN ({marcas})
                        """,
                        ids
                    )

                # ==================================================
                # BORRAR VENTAS
                # ==================================================

                con.execute(
                    f"""
                    DELETE FROM {tabla_ventas}
                    WHERE id IN ({marcas})
                    """,
                    ids
                )

            con.commit()

            QMessageBox.information(
                self,
                "Historial",
                (
                    f"Se eliminaron correctamente "
                    f"{len(registros)} ventas."
                )
            )

            self.cargar_historial()

        except Exception as e:

            if con:

                try:

                    con.rollback()

                except Exception:

                    pass

            QMessageBox.critical(
                self,
                "Error",
                "No se pudieron eliminar las ventas:\n"
                + str(e)
            )

        finally:

            if con:

                try:

                    con.close()

                except Exception:

                    pass

    # ========================================================
    # VER TICKET
    # ========================================================

    def ver_ticket(
        self,
        r
    ):

        item_tipo = self.tabla.item(
            r,
            0
        )

        item_numero = self.tabla.item(
            r,
            1
        )

        if not item_tipo or not item_numero:

            return

        if not self._es_venta(
            item_tipo.text()
        ):

            return

        try:

            numero = int(
                item_numero.text()
            )

        except Exception:

            return

        d = QDialog(
            self
        )

        d.setWindowTitle(
            "Ticket"
        )

        d.resize(
            520,
            650
        )

        layout = QVBoxLayout(
            d
        )

        visor = QTextBrowser()

        try:

            html = generar_ticket(
                numero
            )

        except Exception as e:

            html = (
                "<h2>Error generando ticket</h2>"
                f"<p>{e}</p>"
            )

        visor.setHtml(
            html
        )

        layout.addWidget(
            visor
        )

        boton = QPushButton(
            "Cerrar"
        )

        boton.clicked.connect(
            d.accept
        )

        layout.addWidget(
            boton
        )

        d.exec()

    # ========================================================
    # GUARDAR PDF TICKET
    # ========================================================

    def pdf_ticket(
        self,
        r
    ):

        item_tipo = self.tabla.item(
            r,
            0
        )

        item_numero = self.tabla.item(
            r,
            1
        )

        if not item_tipo or not item_numero:

            return

        if not self._es_venta(
            item_tipo.text()
        ):

            return

        try:

            numero = int(
                item_numero.text()
            )

        except Exception:

            return

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar ticket PDF",
            f"ticket_{numero:06d}.pdf",
            "PDF (*.pdf)"
        )

        if not ruta:

            return

        try:

            guardar_pdf(
                generar_ticket(
                    numero
                ),
                ruta
            )

            QMessageBox.information(
                self,
                "PDF",
                "El ticket fue guardado correctamente."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "PDF",
                "No se pudo guardar el PDF:\n"
                + str(e)
            )

    # ========================================================
    # IMPRIMIR TICKET
    # ========================================================

    def imprimir(
        self,
        r
    ):

        item_tipo = self.tabla.item(
            r,
            0
        )

        item_numero = self.tabla.item(
            r,
            1
        )

        if not item_tipo or not item_numero:

            return

        if not self._es_venta(
            item_tipo.text()
        ):

            return

        try:

            numero = int(
                item_numero.text()
            )

        except Exception:

            return

        try:

            imprimir_ticket(
                generar_ticket(
                    numero
                ),
                self
            )

        except Exception as e:

            QMessageBox.warning(
                self,
                "No se pudo imprimir",
                str(e)
            )

    # ========================================================
    # ARQUEO HTML
    # ========================================================

    def arqueo_html(self, r):
        item_numero = self.tabla.item(r, 1)
        try:
            numero = int(item_numero.text())
        except Exception:
            return "<h2>Arqueo no encontrado</h2>"

        con = sqlite3.connect(BASE_DATOS)
        try:
            cur = con.cursor()
            self.asegurar_columnas_arqueo(cur)
            self.asegurar_columna_movimientos_arqueo(cur)
            con.commit()
            row = cur.execute("""
                SELECT fecha, apertura, esperado, real, diferencia, usuario, observaciones,
                       ventas_total, ventas_efectivo, ventas_transferencia, ventas_tarjeta, ventas_cuenta, cantidad_ventas
                FROM arqueos WHERE id=?
            """, (numero,)).fetchone()
        finally:
            con.close()

        if not row:
            return "<h2>Arqueo no encontrado</h2>"

        # Los movimientos de caja se consultan por la fecha del arqueo.
        # No se mezclan con el total de ventas: solamente afectan el efectivo esperado.
        fecha_dia = (row[0] or "")[:10]
        ingresos = 0.0
        egresos = 0.0
        movimientos_html = "<i>Sin movimientos manuales de caja.</i>"

        con = sqlite3.connect(BASE_DATOS)
        try:
            movimientos = con.execute("""
                SELECT fecha, tipo, importe, concepto, usuario
                FROM movimientos_caja
                WHERE arqueo_id = ?
                ORDER BY id ASC
            """, (numero,)).fetchall()

            if movimientos:
                filas_mov = []
                for fecha_mov, tipo, importe, concepto, usuario in movimientos:
                    importe = float(importe or 0)
                    if str(tipo).upper() == "INGRESO":
                        ingresos += importe
                    elif str(tipo).upper() == "EGRESO":
                        egresos += importe
                    filas_mov.append(
                        f"<tr><td>{fecha_mov}</td><td>{tipo}</td><td>$ {importe:,.2f}</td><td>{concepto or '—'}</td></tr>"
                    )
                movimientos_html = (
                    "<table border='1' cellspacing='0' cellpadding='5' width='100%'>"
                    "<tr><th>Fecha</th><th>Tipo</th><th>Importe</th><th>Concepto</th></tr>"
                    + "".join(filas_mov) + "</table>"
                )
        except sqlite3.OperationalError:
            pass
        finally:
            con.close()

        return f"""
        <html><body style="font-family:Arial">
        <h1 align="center">ARQUEO DE CAJA</h1><hr>
        <b>N°:</b> {numero}<br>
        <b>Fecha:</b> {row[0]}<br>
        <b>Usuario:</b> {row[5] or ''}<hr>
        <h3>DETALLE DE VENTAS</h3>
        <b>Total ventas:</b> $ {float(row[7] or 0):,.2f}<br>
        <b>💵 Efectivo:</b> $ {float(row[8] or 0):,.2f}<br>
        <b>🏦 Transferencias:</b> $ {float(row[9] or 0):,.2f}<br>
        <b>💳 Tarjetas:</b> $ {float(row[10] or 0):,.2f}<br>
        <b>👤 Cuenta corriente:</b> $ {float(row[11] or 0):,.2f}<br>
        <b>🧾 Cantidad de ventas:</b> {int(row[12] or 0)}<hr>
        <h3>CIERRE DE EFECTIVO</h3>
        <b>Efectivo inicial:</b> $ {float(row[1] or 0):,.2f}<br>
        <b>Ventas en efectivo:</b> $ {float(row[8] or 0):,.2f}<br>
        <b>Ingresos de caja:</b> $ {ingresos:,.2f}<br>
        <b>Egresos de caja:</b> $ {egresos:,.2f}<br>
        <b>Efectivo esperado:</b> $ {float(row[2] or 0):,.2f}<br>
        <b>Efectivo contado:</b> $ {float(row[3] or 0):,.2f}<br>
        <b>Diferencia:</b> $ {float(row[4] or 0):,.2f}<hr>
        <h3>MOVIMIENTOS DE CAJA</h3>
        {movimientos_html}<hr>
        <b>Observaciones:</b> {row[6] or '—'}
        </body></html>
        """

    # ========================================================
    # VER ARQUEO
    # ========================================================

    def ver_arqueo(
        self,
        r
    ):

        d = QDialog(
            self
        )

        d.setWindowTitle(
            "Arqueo"
        )

        d.resize(
            560,
            520
        )

        l = QVBoxLayout(
            d
        )

        texto = QTextBrowser()

        texto.setHtml(
            self.arqueo_html(
                r
            )
        )

        l.addWidget(
            texto
        )

        boton = QPushButton(
            "Cerrar"
        )

        boton.clicked.connect(
            d.accept
        )

        l.addWidget(
            boton
        )

        d.exec()

    # ========================================================
    # PDF ARQUEO
    # ========================================================

    def pdf_arqueo(
        self,
        r
    ):

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar arqueo PDF",
            "arqueo.pdf",
            "PDF (*.pdf)"
        )

        if not ruta:

            return

        try:

            guardar_pdf(
                self.arqueo_html(
                    r
                ),
                ruta
            )

            QMessageBox.information(
                self,
                "PDF",
                "El arqueo fue guardado correctamente."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "PDF",
                "No se pudo guardar el arqueo:\n"
                + str(e)
            )

    # ========================================================
    # IMPRIMIR ARQUEO
    # ========================================================

    def imprimir_arqueo(
        self,
        r
    ):

        try:

            imprimir_ticket(
                self.arqueo_html(
                    r
                ),
                self
            )

        except Exception as e:

            QMessageBox.warning(
                self,
                "No se pudo imprimir",
                str(e)
            )