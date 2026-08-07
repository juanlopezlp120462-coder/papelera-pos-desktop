from PySide6.QtPrintSupport import QPrinter, QPrinterInfo, QPrintDialog
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QMessageBox
from ui.db import get_setting


def printer_names():
    try:
        return [p.printerName() for p in QPrinterInfo.availablePrinters() if p.printerName()]
    except Exception:
        return []


def show_no_printer(parent=None):
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Warning)
    box.setWindowTitle('Impresora')
    box.setText('No se detectó ninguna impresora en el sistema.')
    box.setInformativeText('Conectá o instalá una impresora de Windows y luego volvé a intentarlo.')
    box.setStyleSheet('QMessageBox{background:white;} QLabel{color:#0f172a;font-size:14px;} QPushButton{background:#0ea5e9;color:white;border:0;border-radius:8px;padding:8px 18px;font-weight:700;}')
    box.exec()


def printer_for_setting(key, parent=None):
    names = printer_names()
    if not names:
        show_no_printer(parent)
        return None
    wanted = get_setting(key, '').strip()
    p = QPrinter(QPrinter.HighResolution)
    if wanted and wanted in names:
        p.setPrinterName(wanted)
    return p


def print_html(html, parent=None, printer_key='', page_size=None, margins=8.0):
    p = printer_for_setting(printer_key, parent)
    if p is None:
        return False
    if page_size:
        p.setPageSize(page_size)
    dlg = QPrintDialog(p, parent)
    dlg.setWindowTitle('Seleccionar impresora')
    if not dlg.exec():
        return False
    doc = QTextDocument()
    doc.setHtml(html)
    doc.print_(p)
    return True
