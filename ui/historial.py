import sqlite3
import os

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

from ui.db import BASE_DATOS, init_db
from ui.ticket import generar_ticket, imprimir_ticket, guardar_pdf


# ==================================================
# PRUEBA DE RUTA DE BASE DE DATOS
# ==================================================

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

        init_db()

        self.setWindowTitle(
            "Historial"
        )


        self.setStyleSheet("""
        QWidget{
            background:#f8fafc;
            font-family:"Segoe UI";
            color:#0f172a
        }

        QLineEdit,QComboBox{
            background:white;
            border:1px solid #cbd5e1;
            border-radius:10px;
            padding:10px
        }

        QPushButton{
            background:#0ea5e9;
            color:white;
            border:0;
            border-radius:9px;
            padding:10px 14px;
            font-weight:700
        }

        QPushButton.secondary{
            background:#e2e8f0;
            color:#334155
        }

        QPushButton.danger{
            background:#dc2626;
            color:white
        }

        QTableWidget{
            background:white;
            border:1px solid #e2e8f0;
            border-radius:12px;
            gridline-color:#e2e8f0
        }

        QHeaderView::section{
            background:#0f172a;
            color:white;
            padding:10px;
            border:0;
            font-weight:bold
        }

        QToolButton{
            font-size:20px;
            padding:2px
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


        titulo = QLabel(
            "🕘 Historial"
        )

        titulo.setStyleSheet(
            "font-size:28px;font-weight:900"
        )

        layout.addWidget(
            titulo
        )


        barra = QHBoxLayout()


        self.buscar = QLineEdit()

        self.buscar.setPlaceholderText(
            "Buscar ticket, fecha, cliente o forma de pago..."
        )

        self.buscar.textChanged.connect(
            self.cargar_historial
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
                "Arqueo"
            ]
        )

        self.tipo.currentTextChanged.connect(
            self.cargar_historial
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
            self.cargar_historial
        )

        barra.addWidget(
            self.pago
        )


        boton_actualizar = QPushButton(
            "🔄 Actualizar"
        )

        boton_actualizar.clicked.connect(
            self.cargar_historial
        )

        barra.addWidget(
            boton_actualizar
        )


        layout.addLayout(
            barra
        )


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
        resumen = QHBoxLayout()

        self.cant = QLabel()
        self.total = QLabel()
        self.prom = QLabel()


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
                font-weight:bold
                """
            )

            resumen.addWidget(x)


        layout.addLayout(
            resumen
        )


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


        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )


        self.tabla.setSelectionMode(
            QAbstractItemView.NoSelection
        )


        self.tabla.cellDoubleClicked.connect(
            lambda r,c:self.ver_ticket(r)
        )


        layout.addWidget(
            self.tabla
        )


        self.cargar_historial()



    # ==========================================
    # ACTUALIZAR AL VOLVER A ABRIR
    # ==========================================

    def showEvent(self,event):

        super().showEvent(event)

        self.cargar_historial()



    # ==========================================
    # TEXTO DE FORMA DE PAGO
    # ==========================================

    def pago_texto(self,pay):

        e,t,ta,c = pay

        partes=[]


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


        return " | ".join(partes) if partes else "—"



    # ==========================================
    # CARGAR HISTORIAL
    # ==========================================

    def cargar_historial(self):

        try:

            c = sqlite3.connect(
                BASE_DATOS
            )

            q = c.cursor()


            termino = self.buscar.text().strip()

            tipo = self.tipo.currentText()

            pago = self.pago.currentText()


            filas=[]



            # ===============================
            # VENTAS
            # ===============================

            if tipo in (
                "Todos",
                "Venta diaria"
            ):


                tablas = [
                    ("ventas","ACTIVA"),
                    ("ventas_archivo","ARCHIVADA")
                ]


                for tabla,estado in tablas:


                    # Verifica si existe la tabla
                    existe = q.execute(
                        """
                        SELECT name 
                        FROM sqlite_master
                        WHERE type='table'
                        AND name=?
                        """,
                        (tabla,)
                    ).fetchone()


                    if not existe:
                        continue



                    sql=f"""
                    SELECT
                    'Venta diaria',
                    v.id,
                    v.fecha,
                    COALESCE(cl.nombre,'Consumidor final'),
                    COALESCE(v.forma_pago,''),
                    v.total,
                    COALESCE(v.estado,'{estado}')
                    FROM {tabla} v
                    LEFT JOIN clientes cl
                    ON cl.id=v.cliente_id
                    WHERE 1=1
                    """



                    datos=[]



                    if termino:


                        sql += """
                        AND (
                        CAST(v.id AS TEXT) LIKE ?
                        OR v.fecha LIKE ?
                        OR cl.nombre LIKE ?
                        OR v.forma_pago LIKE ?
                        )
                        """


                        buscar = "%" + termino + "%"


                        datos += [
                            buscar,
                            buscar,
                            buscar,
                            buscar
                        ]



                    resultado = q.execute(
                        sql,
                        datos
                    ).fetchall()



                    for fila in resultado:


                        pago_row = q.execute(
                            f"""
                            SELECT
                            COALESCE(pago_efectivo,0),
                            COALESCE(pago_transferencia,0),
                            COALESCE(pago_tarjeta,0),
                            COALESCE(pago_cuenta,0)

                            FROM {tabla}

                            WHERE id=?
                            """,
                            (fila[1],)
                        ).fetchone()



                        if pago_row and sum(
                            float(x or 0)
                            for x in pago_row
                        ) > 0:


                            fila = (
                                fila[0],
                                fila[1],
                                fila[2],
                                fila[3],
                                self.pago_texto(pago_row),
                                fila[5],
                                fila[6]
                            )


                        filas.append(
                            fila
                        )



            # ===============================
            # ARQUEOS
            # ===============================

            if tipo in (
                "Todos",
                "Arqueo"
            ):


                sql="""

                SELECT

                'Arqueo',
                id,
                fecha,

                (
                'Efectivo: $ ' ||
                printf('%.2f',COALESCE(ventas_efectivo,0))

                ),

                'Todos los medios',

                COALESCE(ventas_total,0),

                'GUARDADO'


                FROM arqueos

                WHERE 1=1

                """


                datos=[]



                if termino:

                    sql += """
                    AND (
                    CAST(id AS TEXT) LIKE ?
                    OR fecha LIKE ?
                    )
                    """

                    buscar="%"+termino+"%"

                    datos += [
                        buscar,
                        buscar
                    ]



                filas += q.execute(
                    sql,
                    datos
                ).fetchall()



            c.close()


            filas.sort(
                key=lambda x:x[2],
                reverse=True
            )


            self.tabla.setRowCount(
                0
            )

            print(
                "CREANDO TABLA CON:",
                len(filas),
                "REGISTROS"
            )


            total=0
            ventas=0



            for i,fila in enumerate(filas):

                print(
                    "FILA TABLA:",
                    fila
                )

                self.tabla.insertRow(i)


                for j,valor in enumerate(
                    fila[:7]
                ):


                    texto = (
                        f"$ {valor:,.2f}"
                        if j==5
                        else str(valor)
                    )


                    item = QTableWidgetItem(
                        texto
                    )


                    if (
                        j==0
                        and fila[0]=="Venta diaria"
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


                total += float(
                    fila[5] or 0
                )


                if fila[0]=="Venta diaria":
                    ventas += 1



            self.cant.setText(
                f"Ventas: {ventas}"
            )

            self.total.setText(
                f"Total ventas: $ {total:,.2f}"
            )

            self.prom.setText(
                f"Promedio: $ {(total/ventas if ventas else 0):,.2f}"
            )



        except Exception as e:


            try:

                with open(
                    "error_historial.txt",
                    "w",
                    encoding="utf-8"
                ) as archivo:

                    archivo.write(
                        str(e)
                    )


            except:

                pass



            QMessageBox.critical(
                self,
                "Error",
                "No se pudo cargar historial:\n"
                + str(e)
            )
    # ==========================================
    # SELECCIONAR TODAS LAS VENTAS
    # ==========================================

    def seleccionar_todas(self):

        for r in range(
            self.tabla.rowCount()
        ):

            item = self.tabla.item(
                r,
                0
            )

            if (
                item
                and item.text()=="Venta diaria"
            ):

                item.setCheckState(
                    Qt.Checked
                )



    # ==========================================
    # ELIMINAR VENTAS
    # ==========================================

    def eliminar_seleccionadas(self):

        ids=[]


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


            if (
                tipo
                and numero
                and tipo.text()=="Venta diaria"
                and tipo.checkState()==Qt.Checked
            ):

                ids.append(
                    int(numero.text())
                )



        if not ids:

            QMessageBox.information(
                self,
                "Historial",
                "Seleccioná al menos una venta."
            )

            return



        confirmar = QMessageBox.question(
            self,
            "Eliminar ventas",
            f"Se eliminarán {len(ids)} ventas.\n¿Continuar?",
            QMessageBox.Yes |
            QMessageBox.No
        )


        if confirmar != QMessageBox.Yes:

            return



        try:

            c = sqlite3.connect(
                BASE_DATOS
            )


            marcas = ",".join(
                "?" for _ in ids
            )


            tablas = [
                "detalle_ventas",
                "detalle_ventas_archivo",
                "ventas",
                "ventas_archivo"
            ]


            for tabla in tablas:

                existe = c.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table'
                    AND name=?
                    """,
                    (tabla,)
                ).fetchone()


                if existe:

                    if "detalle" in tabla:

                        c.execute(
                            f"""
                            DELETE FROM {tabla}
                            WHERE venta_id IN ({marcas})
                            """,
                            ids
                        )

                    else:

                        c.execute(
                            f"""
                            DELETE FROM {tabla}
                            WHERE id IN ({marcas})
                            """,
                            ids
                        )


            c.commit()

            c.close()


            self.cargar_historial()



        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )



    # ==========================================
    # VER TICKET
    # ==========================================

    def ver_ticket(self,r):

        if self.tabla.item(r,0).text()!="Venta diaria":

            return


        numero=int(
            self.tabla.item(r,1).text()
        )


        d=QDialog(self)

        d.setWindowTitle(
            "Ticket"
        )

        d.resize(
            520,
            650
        )


        layout=QVBoxLayout(d)


        visor=QTextBrowser()


        visor.setHtml(
            generar_ticket(numero)
        )


        layout.addWidget(
            visor
        )


        boton=QPushButton(
            "Cerrar"
        )

        boton.clicked.connect(
            d.accept
        )

        layout.addWidget(
            boton
        )


        d.exec()



    # ==========================================
    # GUARDAR PDF TICKET
    # ==========================================

    def pdf_ticket(self,r):

        numero=int(
            self.tabla.item(r,1).text()
        )


        ruta,_=QFileDialog.getSaveFileName(
            self,
            "Guardar ticket PDF",
            f"ticket_{numero:06d}.pdf",
            "PDF (*.pdf)"
        )


        if ruta:

            guardar_pdf(
                generar_ticket(numero),
                ruta
            )



    # ==========================================
    # IMPRIMIR TICKET
    # ==========================================

    def imprimir(self,r):

        numero=int(
            self.tabla.item(r,1).text()
        )


        try:

            imprimir_ticket(
                generar_ticket(numero),
                self
            )


        except Exception as e:

            QMessageBox.warning(
                self,
                "No se pudo imprimir",
                str(e)
            )



    # ==========================================
    # ARQUEO HTML
    # ==========================================

    def arqueo_html(self,r):

        numero=int(
            self.tabla.item(r,1).text()
        )


        con=sqlite3.connect(
            BASE_DATOS
        )


        try:

            row=con.execute(
                """
                SELECT
                fecha,
                apertura,
                esperado,
                real,
                diferencia,
                usuario,
                observaciones,
                ventas_total

                FROM arqueos

                WHERE id=?
                """,
                (numero,)
            ).fetchone()


        finally:

            con.close()



        if not row:

            return "<h2>Arqueo no encontrado</h2>"



        return f"""

        <html>

        <body style="font-family:Arial">

        <h1 align="center">
        ARQUEO DE CAJA
        </h1>

        <hr>

        <b>N°:</b> {numero}<br>

        <b>Fecha:</b> {row[0]}<br>

        <b>Usuario:</b> {row[5] or ""}

        <hr>

        <b>Total ventas:</b>
        $ {float(row[7] or 0):,.2f}

        <hr>

        <b>Efectivo inicial:</b>
        $ {float(row[1] or 0):,.2f}

        <br>

        <b>Esperado:</b>
        $ {float(row[2] or 0):,.2f}

        <br>

        <b>Real:</b>
        $ {float(row[3] or 0):,.2f}

        <br>

        <b>Diferencia:</b>
        $ {float(row[4] or 0):,.2f}

        <hr>

        <b>Observaciones:</b>
        {row[6] or "—"}

        </body>

        </html>

        """



    def ver_arqueo(self,r):

        d=QDialog(self)

        d.setWindowTitle(
            "Arqueo"
        )

        d.resize(
            560,
            520
        )


        l=QVBoxLayout(d)


        texto=QTextBrowser()

        texto.setHtml(
            self.arqueo_html(r)
        )


        l.addWidget(
            texto
        )


        boton=QPushButton(
            "Cerrar"
        )


        boton.clicked.connect(
            d.accept
        )


        l.addWidget(
            boton
        )


        d.exec()



    def pdf_arqueo(self,r):

        ruta,_=QFileDialog.getSaveFileName(
            self,
            "Guardar arqueo PDF",
            "arqueo.pdf",
            "PDF (*.pdf)"
        )


        if ruta:

            guardar_pdf(
                self.arqueo_html(r),
                ruta
            )



    def imprimir_arqueo(self,r):

        try:

            imprimir_ticket(
                self.arqueo_html(r),
                self
            )


        except Exception as e:

            QMessageBox.warning(
                self,
                "No se pudo imprimir",
                str(e)
            )