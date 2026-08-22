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

    # ============================================================
    # PRODUCTOS
    # ============================================================

    rows = "".join(
        f"<tr>"
        f"<td>{cantidad}</td>"
        f"<td>{html.escape(str(producto))}</td>"
        f"<td>${subtotal:,.2f}</td>"
        f"</tr>"
        for producto, cantidad, precio, subtotal in d
    )

    # ============================================================
    # DATOS GENERALES
    # ============================================================

    nombre_negocio = html.escape(
        get_setting("nombre_negocio", "PAPELERA")
    )

    forma_pago = html.escape(
        str(v[2] or "Efectivo")
    )

    cliente = html.escape(
        str(v[3] or "Consumidor final")
    )

    pie_ticket = html.escape(
        get_setting(
            "pie_ticket",
            "¡Gracias por su compra!"
        )
    )

    # ============================================================
    # MEDIOS DE PAGO
    # SOLO MOSTRAR LOS QUE TENGAN IMPORTE
    # ============================================================

    pagos = []

    efectivo = float(v[4] or 0)
    transferencia = float(v[5] or 0)
    tarjeta = float(v[6] or 0)
    cuenta = float(v[7] or 0)

    if efectivo > 0:
        pagos.append(
            f"<p><b>Efectivo:</b> ${efectivo:,.2f}</p>"
        )

    if transferencia > 0:
        pagos.append(
            f"<p><b>Transferencia:</b> ${transferencia:,.2f}</p>"
        )

    if tarjeta > 0:
        pagos.append(
            f"<p><b>Tarjeta:</b> ${tarjeta:,.2f}</p>"
        )

    if cuenta > 0:
        pagos.append(
            f"<p><b>Cuenta corriente:</b> ${cuenta:,.2f}</p>"
        )

    pagos_html = "".join(pagos)

    # ============================================================
    # TICKET
    # ============================================================

    return (
        f"<html>"
        f"<body>"
        f"<h2>{nombre_negocio}</h2>"
        f"<h3>Comprobante de venta</h3>"

        f"<p><b>Ticket:</b> {venta_id:06d}</p>"

        f"<p><b>Fecha:</b> "
        f"{html.escape(str(v[0]))}"
        f"</p>"

        f"<p><b>Cliente:</b> "
        f"{cliente}"
        f"</p>"

        f"<p><b>Pago:</b> "
        f"{forma_pago}"
        f"</p>"

        f"{pagos_html}"

        f"<table width='100%'>"

        f"<tr>"
        f"<th>Cant.</th>"
        f"<th>Producto</th>"
        f"<th>Total</th>"
        f"</tr>"

        f"{rows}"

        f"</table>"

        f"<h3>TOTAL: ${float(v[1] or 0):,.2f}</h3>"

        f"<p>{pie_ticket}</p>"

        f"</body>"
        f"</html>"
    )


def guardar_pdf(contenido, ruta):

    d = QTextDocument()
    d.setHtml(contenido)

    p = QPrinter(QPrinter.HighResolution)

    p.setOutputFormat(
        QPrinter.PdfFormat
    )

    p.setOutputFileName(
        ruta
    )

    p.setPageMargins(
        QMarginsF(6, 6, 6, 6)
    )

    d.print(p)

    return ruta


def imprimir_ticket(contenido, parent=None):

    return print_html(
        contenido,
        parent,
        "impresora_ticket"
    )
