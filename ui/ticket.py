import sqlite3, html
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtCore import QMarginsF
from ui.db import BASE_DATOS,init_db,get_setting
from ui.printing import print_html
def generar_ticket(venta_id):
 init_db();c=sqlite3.connect(BASE_DATOS);q=c.cursor();v=q.execute("SELECT v.fecha,v.total,v.forma_pago,COALESCE(cl.nombre,'Consumidor final'),COALESCE(v.pago_efectivo,0),COALESCE(v.pago_transferencia,0),COALESCE(v.pago_tarjeta,0),COALESCE(v.pago_cuenta,0) FROM ventas v LEFT JOIN clientes cl ON cl.id=v.cliente_id WHERE v.id=?",(venta_id,)).fetchone();d=q.execute('SELECT producto,cantidad,precio,subtotal FROM detalle_ventas WHERE venta_id=? ORDER BY id',(venta_id,)).fetchall();
 if not v: v=q.execute("SELECT v.fecha,v.total,v.forma_pago,COALESCE(cl.nombre,'Consumidor final'),COALESCE(v.pago_efectivo,0),COALESCE(v.pago_transferencia,0),COALESCE(v.pago_tarjeta,0),COALESCE(v.pago_cuenta,0) FROM ventas_archivo v LEFT JOIN clientes cl ON cl.id=v.cliente_id WHERE v.id=?",(venta_id,)).fetchone();d=q.execute('SELECT producto,cantidad,precio,subtotal FROM detalle_ventas_archivo WHERE venta_id=? ORDER BY id',(venta_id,)).fetchall() if v else [];c.close()
 if not v:raise ValueError('No se encontró la venta.')
 rows=''.join(f'<tr><td>{a}</td><td>{html.escape(str(p))}</td><td align="right">${s:,.2f}</td></tr>' for p,a,_,s in d)
 return f'<html><body style="font-family:Arial;font-size:10pt;color:#111"><h2 style="text-align:center">{html.escape(get_setting("nombre_negocio","PAPELERA"))}</h2><div style="text-align:center">Comprobante de venta</div><hr><b>Ticket:</b> {venta_id:06d}<br><b>Fecha:</b> {html.escape(str(v[0]))}<br><b>Cliente:</b> {html.escape(str(v[3]))}<br><b>Pago:</b> {html.escape(str(v[2] or 'Efectivo'))}<br><b>Efectivo:</b> ${v[4]:,.2f}<br><b>Transferencia:</b> ${v[5]:,.2f}<br><b>Tarjeta:</b> ${v[6]:,.2f}<br><b>Cuenta corriente:</b> ${v[7]:,.2f}<hr><table width="100%"><tr><th>Cant.</th><th align="left">Producto</th><th>Total</th></tr>{rows}</table><hr><h2 style="text-align:right">TOTAL: ${v[1]:,.2f}</h2><p style="text-align:center">{html.escape(get_setting("pie_ticket","¡Gracias por su compra!"))}</p></body></html>'
def guardar_pdf(contenido,ruta):
 d=QTextDocument();d.setHtml(contenido);p=QPrinter(QPrinter.HighResolution);p.setOutputFormat(QPrinter.PdfFormat);p.setOutputFileName(ruta);p.setPageMargins(QMarginsF(6,6,6,6));d.print_(p);return ruta
def imprimir_ticket(contenido,parent=None):
 return print_html(contenido,parent,'impresora_ticket')
