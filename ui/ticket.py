import sqlite3
import html

from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtCore import QMarginsF

from ui.db import BASE_DATOS, init_db, get_setting
from ui.printing import print_html


def generar_ticket(venta_id):

    init_db()

    c = sqlite3.connect(BASE_DATOS)
    q = c.cursor()

    v = q.execute(
        """
        SELECT
            v.fecha,
            v.total,
            v.forma_pago,
            COALESCE(cl.nombre, 'Consumidor final'),
            COALESCE(v.pago_efectivo, 0),
            COALESCE(v.pago_transferencia, 0),
            COALESCE(v.pago_tarjeta, 0),
            COALESCE(v.pago_cuenta, 0)
        FROM ventas v
        LEFT JOIN clientes cl ON cl.id = v.cliente_id
        WHERE v.id = ?
        """,
        (venta_id,)
    ).fetchone()

    d = q.execute(
        """
        SELECT producto, cantidad, precio, subtotal
        FROM detalle_ventas
        WHERE venta_id = ?
        ORDER BY id
        """,
        (venta_id,)
    ).fetchall()

    if not v:
        v = q.execute(
            """
            SELECT
                v.fecha,
                v.total,
                v.forma_pago,
                COALESCE(cl.nombre, 'Consumidor final'),
                COALESCE(v.pago_efectivo, 0),
                COALESCE(v.pago_transferencia, 0),
                COALESCE(v.pago_tarjeta, 0),
                COALESCE(v.pago_cuenta, 0)
            FROM ventas_archivo v
            LEFT JOIN clientes cl ON cl.id = v.cliente_id
            WHERE v.id = ?
            """,
            (venta_id,)
        ).fetchone()

        d = q.execute(
            """
            SELECT producto, cantidad, precio, subtotal
            FROM detalle_ventas_archivo
            WHERE venta_id = ?
            ORDER BY id
            """,
            (venta_id,)
        ).fetchall() if v else []

    c.close()

    if not v:
        raise ValueError("No se encontró la venta.")

    rows = "".join(
        f"{cantidad}{html.escape(str(producto))}${subtotal:,.2f}"
        for producto, cantidad, precio, subtotal in d
    )

    nombre_negocio = html.escape(
        get_setting("nombre_negocio", "PAPELERA")
    )

    forma_pago = html.escape(
        str(v[2] or "Efectivo")
    )

    pie_ticket = html.escape(
        get_setting("pie_ticket", "¡Gracias por su compra!")
    )

    return (
        f"<html>"
        f"<body>"
        f"<h2>{nombre_negocio}</h2>"
        f"<h3>Comprobante de venta</h3>"
        f"<p><b>Ticket:</b> {venta_id:06d}</p>"
        f"<p><b>Fecha:</b> {html.escape(str(v[0]))}</p>"
        f"<p><b>Cliente:</b> {html.escape(str(v[3]))}</p>"
        f"<p><b>Pago:</b> {forma_pago}</p>"
        f"<p><b>Efectivo:</b> ${v[4]:,.2f}</p>"
        f"<p><b>Transferencia:</b> ${v[5]:,.2f}</p>"
        f"<p><b>Tarjeta:</b> ${v[6]:,.2f}</p>"
        f"<p><b>Cuenta corriente:</b> ${v[7]:,.2f}</p>"
        f"<table width='100%'>"
        f"<tr><th>Cant.</th><th>Producto</th><th>Total</th></tr>"
        f"{rows}"
        f"</table>"
        f"<h3>TOTAL: ${v[1]:,.2f}</h3>"
        f"<p>{pie_ticket}</p>"
        f"</body>"
        f"</html>"
    )


def guardar_pdf(contenido, ruta):

    d = QTextDocument()
    d.setHtml(contenido)

    p = QPrinter(QPrinter.HighResolution)
    p.setOutputFormat(QPrinter.PdfFormat)
    p.setOutputFileName(ruta)
    p.setPageMargins(QMarginsF(6, 6, 6, 6))

    d.print(p)

    return ruta


def imprimir_ticket(contenido, parent=None):

    return print_html(
        contenido,
        parent,
        "impresora_ticket"
    )