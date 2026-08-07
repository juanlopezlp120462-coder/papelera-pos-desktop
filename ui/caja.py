import sqlite3
import datetime

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer

from ui.db import (
    BASE_DATOS,
    init_db,
    archivar_ventas,
    get_setting
)

from ui.keyboard import setup_numeric

from ui.ventas import DialogoAviso




class Caja(QWidget):


    def __init__(self):

        super().__init__()


        init_db()


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



        self.lbl_total_ventas = QLabel(
            "$ 0.00"
        )

        self.lbl_efectivo_ventas = QLabel(
            "$ 0.00"
        )

        self.lbl_otros = QLabel(
            "$ 0.00"
        )

        self.lbl_cantidad = QLabel(
            "0"
        )



        self.add_kpi(
            grid,
            0,
            0,
            "🧾 Ventas del día",
            self.lbl_total_ventas
        )


        self.add_kpi(
            grid,
            0,
            1,
            "💵 Ventas efectivo",
            self.lbl_efectivo_ventas
        )


        self.add_kpi(
            grid,
            1,
            0,
            "💳 Otros pagos",
            self.lbl_otros
        )


        self.add_kpi(
            grid,
            1,
            1,
            "📦 Cantidad",
            self.lbl_cantidad
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


        # self.obs.returnPressed.connect(
        #     self.enter_observacion
        # )



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


        # IMPORTANTE:
        # NO usar setValue(0)
        # porque pisa lo escrito


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



        con = sqlite3.connect(
            BASE_DATOS
        )


        cur = con.cursor()



        total = cur.execute(
            """
            SELECT COALESCE(SUM(total),0)
            FROM ventas
            WHERE fecha LIKE ?
            AND estado='ACTIVA'
            """,
            (hoy,)
        ).fetchone()[0]



        efectivo = cur.execute(
            """
            SELECT COALESCE(
                SUM(
                    CASE

                    WHEN COALESCE(pago_efectivo,0)>0
                    THEN pago_efectivo


                    WHEN LOWER(
                        COALESCE(forma_pago,'')
                    )='efectivo'

                    THEN total


                    ELSE 0

                    END
                ),
            0)

            FROM ventas

            WHERE fecha LIKE ?
            AND estado='ACTIVA'
            """,
            (hoy,)
        ).fetchone()[0]



        cantidad = cur.execute(
            """
            SELECT COUNT(*)
            FROM ventas
            WHERE fecha LIKE ?
            AND estado='ACTIVA'
            """,
            (hoy,)
        ).fetchone()[0]



        con.close()



        return (

            float(total or 0),

            float(efectivo or 0),

            int(cantidad or 0)

        )



    # ==========================
    # ACTUALIZAR DATOS
    # ==========================


    def actualizar_datos(self):


        (
            self.total_ventas,
            self.efectivo_ventas,
            self.cantidad_ventas

        ) = self.obtener_ventas_dia()



        self.lbl_total_ventas.setText(
            f"$ {self.total_ventas:,.2f}"
        )



        self.lbl_efectivo_ventas.setText(
            f"$ {self.efectivo_ventas:,.2f}"
        )



        self.lbl_otros.setText(
            "$ 0.00"
        )



        self.lbl_cantidad.setText(
            str(self.cantidad_ventas)
        )



        self.calcular()



    # ==========================
    # CALCULAR ARQUEO
    # ==========================


    def calcular(self):


        if not hasattr(
            self,
            "efectivo_ventas"
        ):

            return



        esperado = (

            self.apertura.value()

            +

            self.efectivo_ventas

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
💵 Efectivo inicial:
$ {self.apertura.value():,.2f}


🧾 Ventas efectivo:
$ {self.efectivo_ventas:,.2f}


💰 EFECTIVO ESPERADO:
$ {self.esperado:,.2f}


💵 EFECTIVO CONTADO:
$ {self.real.value():,.2f}


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


            con = sqlite3.connect(
                BASE_DATOS
            )


            con.execute(

                """
                INSERT INTO arqueos
                (
                    fecha,
                    apertura,
                    esperado,
                    real,
                    diferencia,
                    usuario,
                    observaciones,
                    ventas_total,
                    ventas_efectivo,
                    cantidad_ventas
                )

                VALUES
                (?,?,?,?,?,?,?,?,?,?)
                """,

                (

                    datetime.datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

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

                    self.cantidad_ventas

                )

            )


            con.commit()

            con.close()



            if self.archivar.isChecked():


                archivar_ventas(
                    fecha=self.fecha_hoy()
                )



            DialogoAviso(

                "✅ Cierre de caja completado",

                f"""
El arqueo fue guardado correctamente.


📅 Fecha:
{self.fecha_hoy_display()}


🧾 Ventas realizadas:
{self.cantidad_ventas}


💵 Total vendido:
$ {self.total_ventas:,.2f}


💰 Efectivo esperado:
$ {self.esperado:,.2f}


💵 Efectivo contado:
$ {self.real.value():,.2f}

""",

                self

            ).exec()



            self.obs.clear()

            self.apertura.clear()

            self.real.clear()



            self.total_ventas = 0

            self.efectivo_ventas = 0

            self.cantidad_ventas = 0

            self.esperado = 0



            self.lbl_total_ventas.setText(
                "$ 0.00"
            )


            self.lbl_efectivo_ventas.setText(
                "$ 0.00"
            )


            self.lbl_otros.setText(
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

            self.cantidad_ventas = 0

            self.esperado = 0



            self.lbl_total_ventas.setText(
                "$ 0.00"
            )


            self.lbl_efectivo_ventas.setText(
                "$ 0.00"
            )


            self.lbl_otros.setText(
                "$ 0.00"
            )


            self.lbl_cantidad.setText(
                "0"
            )


            self.resultado.clear()



            self.foco_inicio()



        except Exception as e:


            DialogoAviso(

                "Error al cerrar caja",

                str(e),

                self

            ).exec()


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