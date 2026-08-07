import os
import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QFormLayout,
    QDialog,
    QTextBrowser,
    QFileDialog
)

from PySide6.QtGui import QTextDocument
from PySide6.QtCore import QMarginsF
from PySide6.QtPrintSupport import QPrinter

from ui.db import get_setting
from ui.printing import print_html


class Documentos(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            f"Documentos - {get_setting('nombre_negocio','COTILLON')}"
        )

        self.resize(
            850,
            700
        )


        self.setStyleSheet("""
            QWidget {
                background:#f8fafc;
                font-family:"Segoe UI";
                color:#0f172a;
            }

            QLineEdit,
            QPlainTextEdit {
                background:white;
                border:1px solid #cbd5e1;
                border-radius:10px;
                padding:10px;
            }

            QPushButton {
                background:#0ea5e9;
                color:white;
                border:0;
                border-radius:10px;
                padding:11px;
                font-weight:800;
            }
        """)


        layout = QVBoxLayout(self)


        titulo = QLabel(
            "🧾 Documentos profesionales"
        )

        titulo.setStyleSheet(
            "font-size:28px;font-weight:800;"
        )


        layout.addWidget(titulo)



        formulario = QFormLayout()


        self.cliente = QLineEdit()

        self.documento = QLineEdit()

        self.observaciones = QLineEdit()

        self.items = QPlainTextEdit()


        self.items.setPlaceholderText(
            "Producto; cantidad; precio"
        )


        formulario.addRow(
            "Cliente",
            self.cliente
        )

        formulario.addRow(
            "Documento / CUIT",
            self.documento
        )

        formulario.addRow(
            "Observaciones",
            self.observaciones
        )


        layout.addLayout(
            formulario
        )


        layout.addWidget(
            self.items
        )



        botones = QHBoxLayout()


        vista = QPushButton(
            "👁 Vista previa"
        )

        vista.clicked.connect(
            self.preview
        )



        pdf = QPushButton(
            "📄 Guardar PDF"
        )

        pdf.clicked.connect(
            self.save
        )



        imprimir = QPushButton(
            "🖨 Imprimir A4"
        )

        imprimir.clicked.connect(
            self.imprimir
        )



        botones.addWidget(vista)

        botones.addWidget(pdf)

        botones.addWidget(imprimir)


        layout.addLayout(
            botones
        )



    def html(self):

        filas = []

        total = 0


        for linea in self.items.toPlainText().splitlines():

            try:

                producto, cantidad, precio = [
                    x.strip()
                    for x in linea.split(";")[:3]
                ]


                cantidad = int(cantidad)


                precio = float(
                    precio.replace(",", ".")
                )


                subtotal = cantidad * precio


                total += subtotal


                filas.append(
                    f"""
                    <tr>
                    <td>{producto}</td>
                    <td>{cantidad}</td>
                    <td>${precio:,.2f}</td>
                    <td>${subtotal:,.2f}</td>
                    </tr>
                    """
                )


            except:

                pass



        return f"""

        <html>

        <body style="font-family:Arial;color:#111">

        <h1>
        {get_setting("nombre_negocio","PAPELERA")}
        </h1>


        <h2>
        DOCUMENTO COMERCIAL
        </h2>


        <p>
        Fecha:
        {datetime.datetime.now():%d/%m/%Y %H:%M}
        </p>


        <p>
        <b>Cliente:</b>
        {self.cliente.text()}

        &nbsp;

        <b>Documento:</b>
        {self.documento.text()}
        </p>



        <table width="100%"
        border="1"
        cellspacing="0"
        cellpadding="8">


        <tr>

        <th>Producto</th>
        <th>Cant.</th>
        <th>Precio</th>
        <th>Subtotal</th>

        </tr>


        {"".join(filas)}


        </table>



        <h2 style="text-align:right">

        TOTAL:
        ${total:,.2f}

        </h2>



        <p>

        <b>Observaciones:</b>

        {self.observaciones.text()}

        </p>


        </body>

        </html>

        """



    def preview(self):

        dialogo = QDialog(self)

        dialogo.resize(
            750,
            800
        )


        layout = QVBoxLayout(dialogo)


        navegador = QTextBrowser()

        navegador.setHtml(
            self.html()
        )


        layout.addWidget(
            navegador
        )


        dialogo.exec()



    def save(self):

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar documento",
            "documento_papelera.pdf",
            "PDF (*.pdf)"
        )


        if ruta:

            self.to_pdf(
                ruta
            )



    def to_pdf(self, ruta):

        documento = QTextDocument()

        documento.setHtml(
            self.html()
        )


        impresora = QPrinter(
            QPrinter.HighResolution
        )


        impresora.setOutputFormat(
            QPrinter.PdfFormat
        )


        impresora.setOutputFileName(
            ruta
        )


        impresora.setPageMargins(
            QMarginsF(
                10,
                10,
                10,
                10
            )
        )


        documento.print_(
            impresora
        )



    def imprimir(self):

        print_html(
            self.html(),
            self,
            "impresora_a4"
        )