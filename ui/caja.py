import sqlite3
import datetime
import uuid
import requests

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer, Signal

from ui.db import (
    BASE_DATOS,
    init_db,
    archivar_ventas,
    get_setting,
    registrar_sincronizacion,
    nuevo_uuid
)

from ui.keyboard import setup_numeric

from ui.ventas import DialogoAviso




class Caja(QWidget):

    arqueo_realizado = Signal()

    def __init__(self):

        super().__init__()


        init_db()
        self.asegurar_columnas_movimientos_caja()

        self.ingresos_caja = 0.0
        self.egresos_caja = 0.0


        self.setWindowTitle(
            f"{get_setting('nombre_negocio','COTILLON')} — Arqueo de Caja"
        )


        self.resize(
            760,
            600
        )


        self.setMinimumSize(
            760,
            560
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )



        self.setStyleSheet("""
        
        QWidget {
            background:#f8fafc;
            color:#0f172a;
            font-family:'Segoe UI';
        }


        QFrame#card {
            background:white;
            border:1px solid #e2e8f0;
            border-radius:16px;
        }


        QLabel.title {
            font-size:24px;
            font-weight:900;
        }


        QLabel.value {
            font-size:22px;
            font-weight:900;
        }


        QDoubleSpinBox,
        QLineEdit {

            background:white;
            border:1px solid #cbd5e1;
            border-radius:10px;
            padding:10px;
            font-size:16px;

        }



        QDoubleSpinBox:focus,
        QLineEdit:focus {

            border:2px solid #2563eb;

        }



        QPushButton {

            border-radius:10px;
            padding:12px;
            font-weight:bold;

        }



        QPushButton#close {

            background:#2563eb;
            color:white;

        }



        QPushButton#calc {

            background:#0ea5e9;
            color:white;

        }



        QLabel#result {

            background:#0f172a;
            color:white;
            border-radius:12px;
            padding:12px;
            font-size:14px;
            font-weight:bold;

        }

        """)



        root = QVBoxLayout(self)


        root.setContentsMargins(
            28,
            28,
            28,
            28
        )


        root.setSpacing(
            18
        )



        titulo = QLabel(
            "💰 Arqueo de caja diario"
        )


        titulo.setProperty(
            "class",
            "title"
        )


        root.addWidget(
            titulo
        )



        subtitulo = QLabel(
            f"Cálculo correspondiente al día {self.fecha_hoy_display()}"
        )


        root.addWidget(
            subtitulo
        )



        # ==========================
        # RESUMEN
        # ==========================


        card = QFrame()


        card.setObjectName(
            "card"
        )


        grid = QGridLayout(
            card
        )



        # En el ARQUEO se muestra solamente el efectivo físico.
        # Transferencias, tarjetas y cuenta corriente se conservan en BD para HISTORIAL.
        self.lbl_efectivo_ventas = QLabel("$ 0.00")
        self.lbl_cantidad = QLabel("0")

        self.add_kpi(
            grid, 0, 0, "💵 Ventas en efectivo", self.lbl_efectivo_ventas
        )
        self.add_kpi(
            grid, 0, 1, "📦 Cantidad de ventas", self.lbl_cantidad
        )


        root.addWidget(
            card
        )



        # ==========================
        # CAMPOS CAJA
        # ==========================


        form = QFrame()


        form.setObjectName(
            "card"
        )


        fl = QFormLayout(
            form
        )


        fl.setContentsMargins(
            12,
            12,
            12,
            12
        )


        fl.setSpacing(
            8
        )



        self.apertura = QDoubleSpinBox()


        setup_numeric(
            self.apertura,
            2
        )


        self.configurar_numero(
            self.apertura
        )



        self.real = QDoubleSpinBox()


        setup_numeric(
            self.real,
            2
        )


        self.configurar_numero(
            self.real
        )



        self.obs = QLineEdit()


        self.obs.setPlaceholderText(
            "Observaciones opcionales"
        )    
        self._keyboard_enter_sequence = [
            self.apertura,
            self.real,
            self.obs
        ]
        print("CAJA SECUENCIA CREADA")
        self.obs.setProperty(
              "keyboard_last",
                True
        )
        # ==========================
        # ORDEN ENTER CAJA
        # ==========================


        
        self.obs.setProperty(
            "keyboard_last",
            True
        )   
        


        fl.addRow(
            "💵 Efectivo con el que arrancó el día",
            self.apertura
        )


        fl.addRow(
            "💰 Efectivo que terminó en caja",
            self.real
        )


        fl.addRow(
            "📝 Observaciones",
            self.obs
        )



        self.archivar = QCheckBox(
            "📦 Archivar ventas del día al cerrar"
        )


        self.archivar.setChecked(
            True
        )


        fl.addRow(
            "",
            self.archivar
        )


        root.addWidget(
            form
        )
        
        # ==========================
        # MOVIMIENTOS DE CAJA
        # ==========================

        movimientos_card = QFrame()

        movimientos_card.setObjectName(
            "card"
        )

        movimientos_layout = QVBoxLayout(
            movimientos_card
        )

        titulo_movimientos = QLabel(
            "💰 Movimientos de caja"
        )

        titulo_movimientos.setStyleSheet(
            "font-size:18px;font-weight:900;"
        )

        movimientos_layout.addWidget(
            titulo_movimientos
        )

        fila_movimiento = QHBoxLayout()

        self.mov_tipo = QComboBox()

        self.mov_tipo.addItems([
            "INGRESO",
            "EGRESO"
        ])

        self.mov_importe = QDoubleSpinBox()

        setup_numeric(
            self.mov_importe,
            2
        )

        self.configurar_numero(
            self.mov_importe
        )

        self.mov_importe.setMinimum(
            0
        )

        self.mov_concepto = QLineEdit()

        self.mov_concepto.setPlaceholderText(
            "Concepto del movimiento"
        )

        self.btn_movimiento = QPushButton(
            "Registrar movimiento"
        )

        self.btn_movimiento.clicked.connect(
            self.registrar_movimiento_caja
        )

        fila_movimiento.addWidget(
            QLabel("Tipo:")
        )

        fila_movimiento.addWidget(
            self.mov_tipo
        )

        fila_movimiento.addWidget(
            QLabel("Importe:")
        )

        fila_movimiento.addWidget(
            self.mov_importe
        )

        fila_movimiento.addWidget(
            self.mov_concepto
        )

        fila_movimiento.addWidget(
            self.btn_movimiento
        )

        movimientos_layout.addLayout(
            fila_movimiento
        )

        root.addWidget(
            movimientos_card
        )
        
        # ==========================
        # RESULTADO
        # ==========================


        self.resultado = QLabel()


        self.resultado.setObjectName(
            "result"
        )


        self.resultado.setAlignment(
            Qt.AlignCenter
        )


        self.resultado.setWordWrap(
            True
        )


        root.addWidget(
            self.resultado
        )



        # ==========================
        # BOTONES
        # ==========================


        botones = QHBoxLayout()



        actualizar = QPushButton(
            "🔄 Actualizar ventas"
        )


        actualizar.clicked.connect(
            self.actualizar_datos
        )



        calcular = QPushButton(
            "🧮 Calcular"
        )


        calcular.setObjectName(
            "calc"
        )


        calcular.clicked.connect(
            self.calcular
        )



        cerrar = QPushButton(
            "🔒 Cerrar caja"
        )


        cerrar.setObjectName(
            "close"
        )


        cerrar.clicked.connect(
            self.cerrar
        )



        botones.addWidget(
            actualizar
        )


        botones.addStretch()



        botones.addWidget(
            calcular
        )


        botones.addWidget(
            cerrar
        )



        root.addLayout(
            botones
        )



        # ==========================
        # ENTER IGUAL A AGREGAR PROD
        # ==========================


        self.apertura.lineEdit().returnPressed.connect(
            self.enter_apertura
        )


        self.real.lineEdit().returnPressed.connect(
            self.enter_real
        )



        # ==========================
        # ACTUALIZAR MIENTRAS ESCRIBE
        # ==========================


        self.apertura.valueChanged.connect(
            self.calcular
        )


        self.real.valueChanged.connect(
            self.calcular
        )



        # ==========================
        # CARGA INICIAL
        # ==========================


        self.actualizar_datos()



        # ENTRAR SIEMPRE LIMPIO
        QTimer.singleShot(
            300,
            self.foco_inicio
        )



    # ==========================
    # ASEGURAR COLUMNA DE ARQUEO EN MOVIMIENTOS
    # ==========================
    def asegurar_columnas_movimientos_caja(self):
        con = sqlite3.connect(BASE_DATOS)
        try:
            cur = con.cursor()
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

            # Movimientos anteriores: quedan vinculados al primer arqueo
            # posterior del mismo día. Así no vuelven a aparecer.
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
            con.commit()
        finally:
            con.close()


    # ==========================
    # ASEGURAR COLUMNAS DEL ARQUEO
    # ==========================
    def asegurar_columnas_arqueo(self):
        con = sqlite3.connect(BASE_DATOS)
        try:
            cur = con.cursor()
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
            con.commit()
        finally:
            con.close()

    # ==========================
    # CONFIGURAR NUMERO
    # ==========================


    def configurar_numero(
        self,
        campo
    ):


        campo.setMaximum(
            999999999999.99
        )


        campo.setDecimals(
            2
        )


        campo.setPrefix(
            "$ "
        )


        campo.setKeyboardTracking(
            True
        )



    # ==========================
    # ENTER APERTURA
    # ==========================


    def enter_apertura(self):


        self.apertura.interpretText()


        self.calcular()



        self.real.setFocus(
            Qt.OtherFocusReason
        )


        self.real.lineEdit().selectAll()



    # ==========================
    # ENTER REAL
    # ==========================


    def enter_real(self):


        self.real.interpretText()


        self.calcular()



        self.obs.setFocus(
            Qt.OtherFocusReason
        )



    # ==========================
    # ENTER FINAL
    # ==========================


    def enter_observacion(self):
        print("ENTRO A OBSERVACIONES ENTER")


        self.cerrar()



    # ==========================
    # FOCO INICIO
    # ==========================


    def foco_inicio(self):


        self.apertura.setFocus(
            Qt.OtherFocusReason
        )


        self.apertura.lineEdit().selectAll()



    # ==========================
    # FECHAS
    # ==========================


    def fecha_hoy(self):

        return datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )



    def fecha_hoy_display(self):

        return datetime.datetime.now().strftime(
            "%d/%m/%Y"
        )



    # ==========================
    # TARJETAS RESUMEN
    # ==========================


    def add_kpi(
        self,
        grid,
        fila,
        columna,
        titulo,
        valor
    ):


        caja = QVBoxLayout()


        texto = QLabel(
            titulo
        )


        texto.setStyleSheet(
            "font-weight:bold;color:#64748b;"
        )


        valor.setProperty(
            "class",
            "value"
        )


        caja.addWidget(
            texto
        )


        caja.addWidget(
            valor
        )


        grid.addLayout(
            caja,
            fila,
            columna
        )



    # ==========================
    # OBTENER VENTAS DEL DIA
    # ==========================


    def obtener_ventas_dia(self):
        hoy = self.fecha_hoy() + "%"
        con = sqlite3.connect(BASE_DATOS)
        cur = con.cursor()
        try:
            row = cur.execute("""
                SELECT
                    COALESCE(SUM(total), 0),
                    COALESCE(SUM(
                        CASE
                            WHEN COALESCE(pago_efectivo,0) > 0 THEN pago_efectivo
                            WHEN LOWER(TRIM(COALESCE(forma_pago,''))) IN ('efectivo','cash') THEN total
                            ELSE 0
                        END
                    ),0),
                    COALESCE(SUM(
                        CASE
                            WHEN COALESCE(pago_transferencia,0) > 0 THEN pago_transferencia
                            WHEN LOWER(TRIM(COALESCE(forma_pago,''))) IN ('transferencia','transfer','mercadopago','mercado pago') THEN total
                            ELSE 0
                        END
                    ),0),
                    COALESCE(SUM(
                        CASE
                            WHEN COALESCE(pago_tarjeta,0) > 0 THEN pago_tarjeta
                            WHEN LOWER(TRIM(COALESCE(forma_pago,''))) IN ('tarjeta','credito','crédito','debito','débito') THEN total
                            ELSE 0
                        END
                    ),0),
                    COALESCE(SUM(
                        CASE
                            WHEN COALESCE(pago_cuenta,0) > 0 THEN pago_cuenta
                            WHEN LOWER(TRIM(COALESCE(forma_pago,''))) IN ('cuenta','cuenta corriente','fiado') THEN total
                            ELSE 0
                        END
                    ),0),
                    COUNT(*)
                FROM ventas
                WHERE fecha LIKE ?
                  AND COALESCE(estado,'ACTIVA')='ACTIVA'
            """, (hoy,)).fetchone()

            return tuple(float(x or 0) for x in row[:5]) + (int(row[5] or 0),)
        finally:
            con.close()

    def obtener_movimientos_dia(self):
        hoy = self.fecha_hoy()

        con = sqlite3.connect(BASE_DATOS)
        cur = con.cursor()

        try:
            # =====================================================
            # BUSCAR EL ÚLTIMO ARQUEO REALIZADO HOY
            # =====================================================
            ultimo_arqueo = cur.execute(
                """
                SELECT MAX(fecha)
                FROM arqueos
                WHERE fecha LIKE ?
                """,
                (hoy + "%",)
            ).fetchone()[0]

            # =====================================================
            # PRIMER ARQUEO DEL DÍA
            #
            # Si todavía no hubo ningún arqueo hoy,
            # toma todos los movimientos realizados hoy.
            # =====================================================
            if not ultimo_arqueo:

                row = cur.execute(
                    """
                    SELECT
                        COALESCE(
                            SUM(
                                CASE
                                    WHEN UPPER(TRIM(tipo)) = 'INGRESO'
                                    THEN importe
                                    ELSE 0
                                END
                            ),
                            0
                        ),

                        COALESCE(
                            SUM(
                                CASE
                                    WHEN UPPER(TRIM(tipo)) = 'EGRESO'
                                    THEN importe
                                    ELSE 0
                                END
                            ),
                            0
                        )

                    FROM movimientos_caja

                    WHERE fecha LIKE ?
                      AND arqueo_id IS NULL
                    """,
                    (hoy + "%",)
                ).fetchone()

            # =====================================================
            # ARQUEOS POSTERIORES
            #
            # Solamente toma movimientos realizados DESPUÉS
            # del último arqueo.
            # =====================================================
            else:

                row = cur.execute(
                    """
                    SELECT
                        COALESCE(
                            SUM(
                                CASE
                                    WHEN UPPER(TRIM(tipo)) = 'INGRESO'
                                    THEN importe
                                    ELSE 0
                                END
                            ),
                            0
                        ),

                        COALESCE(
                            SUM(
                                CASE
                                    WHEN UPPER(TRIM(tipo)) = 'EGRESO'
                                    THEN importe
                                    ELSE 0
                                END
                            ),
                            0
                        )

                    FROM movimientos_caja

                    WHERE fecha LIKE ?
                      AND fecha > ?
                      AND arqueo_id IS NULL
                    """,
                    (
                        hoy + "%",
                        ultimo_arqueo
                    )
                ).fetchone()

            return (
                float(row[0] or 0),
                float(row[1] or 0)
            )

        finally:
            con.close()
    # ==========================
    # ACTUALIZAR DATOS
    # ==========================
    def actualizar_datos(self):
        (
            self.total_ventas,
            self.efectivo_ventas,
            self.transferencia_ventas,
            self.tarjeta_ventas,
            self.cuenta_ventas,
            self.cantidad_ventas
        ) = self.obtener_ventas_dia()

        (self.ingresos_caja, self.egresos_caja) = self.obtener_movimientos_dia()

        self.lbl_efectivo_ventas.setText(f"$ {self.efectivo_ventas:,.2f}")
        self.lbl_cantidad.setText(str(self.cantidad_ventas))
        self.calcular()

    # ==========================
    # REGISTRAR MOVIMIENTO
    # ==========================

    def registrar_movimiento_caja(self):

        self.mov_importe.interpretText()

        importe = float(
            self.mov_importe.value()
        )

        tipo = self.mov_tipo.currentText()

        concepto = self.mov_concepto.text().strip()

        if importe <= 0:

            QMessageBox.warning(
                self,
                "Movimiento de caja",
                "Ingresá un importe mayor a cero."
            )

            self.mov_importe.setFocus()

            return

        if not concepto:

            QMessageBox.warning(
                self,
                "Movimiento de caja",
                "Ingresá un concepto."
            )

            self.mov_concepto.setFocus()

            return

        try:

            movimiento_uuid = str(
                uuid.uuid4()
            )

            fecha_str = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            con = sqlite3.connect(
                BASE_DATOS
            )

            con.execute(
                """
                INSERT INTO movimientos_caja
                (
                    fecha,
                    tipo,
                    importe,
                    concepto,
                    usuario,
                    uuid
                )
                VALUES
                (?, ?, ?, ?, ?, ?)
                """,
                (
                    fecha_str,
                    tipo,
                    importe,
                    concepto,
                    "Administrador",
                    movimiento_uuid
                )
            )

            con.commit()
            con.close()

            datos_movimiento = {
                "uuid": movimiento_uuid,
                "fecha": fecha_str,
                "tipo": tipo,
                "importe": importe,
                "concepto": concepto,
                "usuario": "Administrador"
            }

            registrar_sincronizacion(
                "movimientos_caja",
                movimiento_uuid,
                "crear",
                datos_movimiento
            )

            self.mov_importe.setValue(
                0
            )

            self.mov_concepto.clear()

            self.mov_concepto.setFocus()

            QMessageBox.information(
                self,
                "Movimiento registrado",
                f"{tipo} registrado correctamente."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo registrar el movimiento:\n\n{e}"
            )

    # ==========================
    # CALCULAR ARQUEO
    # ==========================


    def calcular(self):


        if not hasattr(
            self,
            "efectivo_ventas"
        ):

            return



        # ARQUEO EXCLUSIVAMENTE EN EFECTIVO.
        # Transferencias, tarjetas y cuenta corriente no forman parte de la caja física.
        # INGRESOS/EGRESOS se guardan para REPORTES, pero no se muestran ni se suman aquí.
        esperado = (
            self.apertura.value()
            + self.efectivo_ventas
        )


        self.esperado = esperado



        diferencia = (

            self.real.value()

            -

            esperado

        )



        if diferencia > 0.01:


            estado = (
                f"🟢 SOBRANTE: $ {diferencia:,.2f}"
            )


        elif diferencia < -0.01:


            estado = (
                f"🔴 FALTANTE: $ {abs(diferencia):,.2f}"
            )


        else:


            estado = (
                "🟢 CAJA CUADRADA"
            )



        self.resultado.setText(
            f"""
💵 EFECTIVO INICIAL:
$ {self.apertura.value():,.2f}

💵 VENTAS EN EFECTIVO:
$ {self.efectivo_ventas:,.2f}

💰 EFECTIVO ESPERADO:
$ {self.esperado:,.2f}

💵 EFECTIVO CONTADO:
$ {self.real.value():,.2f}

📊 DIFERENCIA:
$ {diferencia:,.2f}

{estado}
"""
        )


    # ==========================
    # CERRAR CAJA
    # ==========================


    def cerrar(self):


        self.apertura.interpretText()

        self.real.interpretText()



        self.calcular()



        confirmar = QDialog(self)


        confirmar.setWindowTitle(
            "🔒 Confirmar cierre"
        )


        confirmar.setFixedSize(
            450,
            320
        )


        confirmar.setStyleSheet(
            """
            QDialog {

                background:#f8fafc;

            }


            QLabel#titulo {

                font-size:22px;
                font-weight:900;
                color:#0f172a;

            }


            QLabel#texto {

                font-size:14px;
                color:#334155;

            }


            QPushButton {

                border-radius:10px;
                padding:12px 28px;
                font-weight:bold;
                font-size:14px;

            }


            QPushButton#si {

                background:#16a34a;
                color:white;

            }


            QPushButton#si:hover {

                background:#15803d;

            }


            QPushButton#no {

                background:#dc2626;
                color:white;

            }


            QPushButton#no:hover {

                background:#b91c1c;

            }

            """
        )



        layout_confirmar = QVBoxLayout(
            confirmar
        )


        layout_confirmar.setContentsMargins(
            25,
            25,
            25,
            25
        )


        layout_confirmar.setSpacing(
            15
        )



        icono = QLabel(
            "🔒"
        )


        icono.setAlignment(
            Qt.AlignCenter
        )


        icono.setStyleSheet(
            "font-size:34px;"
        )



        titulo = QLabel(
            "Confirmar cierre de caja"
        )


        titulo.setObjectName(
            "titulo"
        )


        titulo.setAlignment(
            Qt.AlignCenter
        )



        detalle = QLabel(
            self.resultado.text()
            +
            "\n\n¿Confirmás cerrar la caja?"
        )


        detalle.setObjectName(
            "texto"
        )


        detalle.setAlignment(
            Qt.AlignCenter
        )


        detalle.setWordWrap(
            True
        )



        layout_confirmar.addWidget(
            icono
        )


        layout_confirmar.addWidget(
            titulo
        )


        layout_confirmar.addWidget(
            detalle
        )



        botones = QHBoxLayout()



        btn_cancelar = QPushButton(
            "Cancelar"
        )


        btn_cancelar.setObjectName(
            "no"
        )


        btn_cancelar.clicked.connect(
            confirmar.reject
        )



        btn_cerrar = QPushButton(
            "Cerrar caja"
        )


        btn_cerrar.setObjectName(
            "si"
        )


        btn_cerrar.clicked.connect(
            confirmar.accept
        )



        botones.addWidget(
            btn_cancelar
        )


        botones.addWidget(
            btn_cerrar
        )



        layout_confirmar.addLayout(
            botones
        )



        respuesta = confirmar.exec()



        if respuesta != QDialog.Accepted:

            return



        try:
            uuid_arqueo = str(uuid.uuid4())
            fecha_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            con = sqlite3.connect(
                BASE_DATOS
            )


            con.execute(

                """
                INSERT INTO arqueos
                (
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

                VALUES
                (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,

                (
                    uuid_arqueo,
                    fecha_str,
                    self.apertura.value(),
                    self.esperado,
                    self.real.value(),
                    self.real.value()
                    -
                    self.esperado,
                    "Administrador",
                    self.obs.text(),
                    self.total_ventas,
                    self.efectivo_ventas,
                    self.transferencia_ventas,
                    self.tarjeta_ventas,
                    self.cuenta_ventas,
                    self.cantidad_ventas

                )

            )

            # Asociar al arqueo los movimientos que acaba de tomar.
            # No se eliminan: REPORTES los seguirá mostrando.
            arqueo_id = con.execute(
                "SELECT id FROM arqueos WHERE uuid = ?",
                (uuid_arqueo,)
            ).fetchone()[0]

            con.execute(
                """
                UPDATE movimientos_caja
                SET arqueo_id = ?
                WHERE fecha LIKE ?
                  AND fecha <= ?
                  AND arqueo_id IS NULL
                """,
                (arqueo_id, fecha_str[:10] + "%", fecha_str)
            )

            con.commit()

            con.close()

            # ==========================================
            # REGISTRAR ARQUEO PARA SINCRONIZACIÓN
            # ==========================================

            datos_arqueo_sync = {
                "uuid": uuid_arqueo,
                "fecha": fecha_str,
                "apertura": self.apertura.value(),
                "esperado": self.esperado,
                "real": self.real.value(),
                "diferencia": self.real.value() - self.esperado,
                "usuario": "Administrador",
                "observaciones": self.obs.text(),
                "ventas_total": self.total_ventas,
                "ventas_efectivo": self.efectivo_ventas,
                "ventas_transferencia": self.transferencia_ventas,
                "ventas_tarjeta": self.tarjeta_ventas,
                "ventas_cuenta": self.cuenta_ventas,
                "cantidad_ventas": self.cantidad_ventas
            }

            registrar_sincronizacion(
                "arqueos",
                uuid_arqueo,
                "crear",
                datos_arqueo_sync
            )

            # ==========================================
            # REGISTRAR CIERRE/ARCHIVADO DE VENTAS
            # ==========================================

            hoy_str = self.fecha_hoy()

            datos_sync = {
                "fecha": hoy_str,
                "accion": "archivar_hoy"
            }

            registrar_sincronizacion(
                "ventas",
                nuevo_uuid(),
                "archivar_hoy",
                datos_sync
            )
            try:
                datos_arqueo = {
                    "uuid": uuid_arqueo,
                    "fecha": fecha_str,
                    "apertura": self.apertura.value(),
                    "esperado": self.esperado,
                    "real": self.real.value(),
                    "diferencia": self.real.value() - self.esperado,
                    "usuario": "Administrador",
                    "observaciones": self.obs.text(),
                    "ventas_total": self.total_ventas,
                    "ventas_efectivo": self.efectivo_ventas,
                    "ventas_transferencia": self.transferencia_ventas,
                    "ventas_tarjeta": self.tarjeta_ventas,
                    "ventas_cuenta": self.cuenta_ventas,
                    "cantidad_ventas": self.cantidad_ventas
                }
                api_url = get_setting('api_url', 'https://papelera-pos-backend-production.up.railway.app')
                # CORREGIDO: Añadido '/caja' para que coincida con el backend
                requests.post(f"{api_url}/caja/arqueos", json=datos_arqueo, timeout=5)
                
                # Notificar también la acción de sincronización de cierre al backend
                requests.post(f"{api_url}/sincronizar", json={
                    "tabla": "ventas",
                    "registro_uuid": nuevo_uuid(),
                    "accion": "archivar_hoy",
                    "datos": datos_sync
                }, timeout=2)
            except Exception as sync_err:
                print("El arqueo se guardó localmente, error al sincronizar con la nube:", sync_err)



            if self.archivar.isChecked():


                archivar_ventas(
                    fecha=hoy_str
                )
            
            # Avisar al Dashboard que el arqueo terminó
            # para actualizar Inicio inmediatamente.
            self.arqueo_realizado.emit()

            DialogoAviso(

                "✅ Cierre de caja completado",

                f"""
El arqueo fue guardado correctamente.

📅 Fecha:
{self.fecha_hoy_display()}

🧾 Ventas realizadas:
{self.cantidad_ventas}

💵 Ventas en efectivo:
$ {self.efectivo_ventas:,.2f}

💰 Efectivo esperado:
$ {self.esperado:,.2f}

💵 Efectivo contado:
$ {self.real.value():,.2f}

📊 Diferencia:
$ {self.real.value() - self.esperado:,.2f}
""",

                self

            ).exec()



            self.obs.clear()

            self.apertura.clear()

            self.real.clear()



            self.total_ventas = 0

            self.efectivo_ventas = 0
            self.transferencia_ventas = 0
            self.tarjeta_ventas = 0
            self.cuenta_ventas = 0
            self.cantidad_ventas = 0

            self.ingresos_caja = 0
            self.egresos_caja = 0
            self.esperado = 0




            self.lbl_efectivo_ventas.setText(
                "$ 0.00"
            )




            self.lbl_cantidad.setText(
                "0"
            )


            self.resultado.clear()



            self.foco_inicio()



        except Exception as e:


            DialogoAviso(

                "❌ Error al cerrar caja",

                str(e),

                self

            ).exec()


            # ==========================
            # LIMPIEZA COMPLETA
            # ==========================


            self.obs.clear()



            self.apertura.clear()


            self.real.clear()



            self.total_ventas = 0

            self.efectivo_ventas = 0
            self.transferencia_ventas = 0
            self.tarjeta_ventas = 0
            self.cuenta_ventas = 0
            self.cantidad_ventas = 0

            self.ingresos_caja = 0
            self.egresos_caja = 0
            self.esperado = 0




            self.lbl_efectivo_ventas.setText(
                "$ 0.00"
            )




            self.lbl_cantidad.setText(
                "0"
            )


            self.resultado.clear()



            self.foco_inicio()



    # ==========================
    # ENTER DESDE OBSERVACIONES
    # ==========================

    def keyboard_submit(self):

        print(">>> ENTRE A KEYBOARD_SUBMIT CAJA")
        
        self.cerrar()
        
        return True     
      
        
        


    # ==========================
    # AL VOLVER AL MODULO CAJA
    # ==========================


    def showEvent(
        self,
        event
    ):


        super().showEvent(
            event
        )



        # RECARGA DATOS ACTUALES

        self.actualizar_datos()



        # LIMPIA CAMPOS ANTERIORES

        self.apertura.clear()

        self.real.clear()

        self.resultado.clear()



        self.esperado = 0



        QTimer.singleShot(

            300,

            self.foco_inicio

        )
        self.installEventFilter(
            self.parent()
        )