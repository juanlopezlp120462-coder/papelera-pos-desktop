import sqlite3, html
from PySide6.QtWidgets import *
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtCore import QMarginsF
from ui.db import BASE_DATOS, init_db, get_setting
from ui.printing import print_html, printer_names, show_no_printer

class Carteles(QWidget):
    def __init__(self):
        super().__init__(); init_db(); self.setWindowTitle(f"Carteles y Ofertas - {get_setting('nombre_negocio','COTILLON')}")
        self.setStyleSheet('''
        QWidget{background:#f8fafc;font-family:"Segoe UI";color:#0f172a}
        QGroupBox{background:white;border:1px solid #e2e8f0;border-radius:16px;margin-top:16px;padding:18px;font-weight:800}
        QGroupBox::title{background:white;subcontrol-origin:margin;left:14px;padding:0 8px;color:#0f172a}
        QComboBox,QSpinBox,QLineEdit{background:white;border:1px solid #cbd5e1;border-radius:10px;padding:10px;min-height:20px}
        QPushButton{background:#0ea5e9;color:white;border:0;border-radius:10px;padding:11px 15px;font-weight:800}
        QPushButton:hover{background:#0284c7} QPushButton.secondary{background:#e2e8f0;color:#334155}
        QLabel.muted{color:#64748b}
        ''')
        root=QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(16)
        head=QHBoxLayout(); title=QLabel('🏷️ Carteles de ofertas'); title.setStyleSheet('font-size:30px;font-weight:900'); head.addWidget(title); head.addStretch(); root.addLayout(head)
        sub=QLabel('Diseñá carteles atractivos, elegí el tamaño y decidí exactamente cómo distribuirlos en A4.'); sub.setProperty('class','muted'); root.addWidget(sub)

        box=QGroupBox('🎨 Diseño del cartel'); g=QGridLayout(box)
        c=sqlite3.connect(BASE_DATOS); self.rows=c.execute('SELECT id,nombre,precio_venta FROM productos ORDER BY nombre').fetchall(); c.close()
        self.busqueda=QLineEdit(); self.busqueda.setPlaceholderText('🔎 Buscar por nombre o código de barras...'); self.busqueda.textChanged.connect(self.filtrar_productos)
        self.prod=QComboBox();
        for r in self.rows:self.prod.addItem(f'{r[1]} — ${r[2]:,.2f}',r[0])
        self.tam=QComboBox(); self.tam.addItems(['Chico','Mediano','Grande','1/4 de página','1/2 página','Página completa'])
        self.estilo=QComboBox(); self.estilo.addItems(['Moderno','Clásico','Impacto'])
        self.leyenda=QLineEdit('OFERTA'); self.leyenda.setPlaceholderText('Ej.: OFERTA, PROMO, LIQUIDACIÓN')
        self.extra=QLineEdit(); self.extra.setPlaceholderText('Texto opcional: "Hasta agotar stock"')
        g.addWidget(QLabel('Buscar:'),0,0); g.addWidget(self.busqueda,0,1,1,3)
        g.addWidget(QLabel('Producto:'),1,0); g.addWidget(self.prod,1,1,1,3)
        g.addWidget(QLabel('Tamaño:'),2,0); g.addWidget(self.tam,2,1)
        g.addWidget(QLabel('Diseño:'),2,2); g.addWidget(self.estilo,2,3)
        g.addWidget(QLabel('Leyenda:'),3,0); g.addWidget(self.leyenda,3,1,1,3)
        g.addWidget(QLabel('Texto adicional:'),4,0); g.addWidget(self.extra,4,1,1,3)
        root.addWidget(box)

        box2=QGroupBox('📄 Impresión A4'); g2=QGridLayout(box2)
        self.cant=QSpinBox(); self.cant.setRange(1,100); self.cant.setValue(1)
        self.dist=QComboBox(); self.dist.addItems(['1 por hoja','2 por hoja','4 por hoja'])
        g2.addWidget(QLabel('Cantidad total:'),0,0); g2.addWidget(self.cant,0,1)
        g2.addWidget(QLabel('Distribución:'),0,2); g2.addWidget(self.dist,0,3)
        info=QLabel('Podés imprimir un solo cartel o varios. La distribución se aplica solo cuando vos la elegís.'); info.setProperty('class','muted'); info.setWordWrap(True); g2.addWidget(info,1,0,1,4)
        root.addWidget(box2)

        b=QHBoxLayout(); pv=QPushButton('👁 Vista previa'); pv.clicked.connect(self.preview); pr=QPushButton('🖨 Imprimir A4'); pr.clicked.connect(self.print); pdf=QPushButton('📄 Guardar PDF'); pdf.setProperty('class','secondary'); pdf.clicked.connect(self.save_pdf); b.addWidget(pv); b.addWidget(pdf); b.addWidget(pr); b.addStretch(); root.addLayout(b); root.addStretch()

    def filtrar_productos(self, texto):
        texto=texto.strip().lower()
        actual=self.prod.currentData()
        self.prod.blockSignals(True); self.prod.clear()
        for r in self.rows:
            if not texto or texto in str(r[1]).lower() or texto in str(r[0]).lower():
                self.prod.addItem(f'{r[1]} — $ {r[2]:,.2f}',r[0])
        idx=self.prod.findData(actual)
        if idx>=0:self.prod.setCurrentIndex(idx)
        self.prod.blockSignals(False)

    def selected(self):
        return next((x for x in self.rows if x[0]==self.prod.currentData()),None)

    def html(self):
        r=self.selected()
        if not r:return '<html><body><h2>No hay productos cargados.</h2></body></html>'
        name=html.escape(str(r[1])); price=f'$ {r[2]:,.2f}'; ley=html.escape(self.leyenda.text().strip() or 'OFERTA'); extra=html.escape(self.extra.text().strip())
        size={'Chico':'25pt','Mediano':'36pt','Grande':'52pt','1/4 de página':'54pt','1/2 página':'72pt','Página completa':'105pt'}[self.tam.currentText()]
        style=self.estilo.currentText()
        if style=='Clásico':
            bg='#ffffff'; border='#0f172a'; accent='#0f172a'; badge='#0f172a'
        elif style=='Impacto':
            bg='#fff7ed'; border='#ea580c'; accent='#c2410c'; badge='#ea580c'
        else:
            bg='#eff6ff'; border='#0284c7'; accent='#0369a1'; badge='#0284c7'
        return f'''<html><body style="font-family:Arial;background:{bg};color:#111;text-align:center;margin:0;padding:0;">
        <div style="border:5px solid {border};border-radius:18px;padding:28px;margin:10px;background:{bg};">
        <div style="font-size:30pt;font-weight:900;color:white;background:{badge};padding:10px 18px;border-radius:12px;">{ley}</div>
        <div style="font-size:28pt;font-weight:900;color:{accent};margin-top:28px;">{name}</div>
        <div style="font-size:{size};font-weight:900;margin:22px 0;color:#111;letter-spacing:1px;">{price}</div>
        {f'<div style="font-size:16pt;color:#475569;margin-top:10px;">{extra}</div>' if extra else ''}
        <div style="font-size:14pt;font-weight:700;margin-top:26px;">{html.escape(get_setting('nombre_negocio','COTILLON'))}</div>
        </div></body></html>'''

    def preview(self):
        d=QDialog(self); d.setWindowTitle('Vista previa — Cartel'); d.resize(760,820); d.setStyleSheet('QDialog{background:#ffffff;} QTextBrowser{background:white;color:#111;border:1px solid #e2e8f0;}')
        l=QVBoxLayout(d); v=QTextBrowser(); v.setHtml(self.html()); l.addWidget(v); close=QPushButton('Cerrar'); close.clicked.connect(d.accept); l.addWidget(close); d.exec()

    def save_pdf(self):
        p,_=QFileDialog.getSaveFileName(self,'Guardar cartel PDF','cartel_oferta.pdf','PDF (*.pdf)')
        if not p:return
        doc=QTextDocument(); doc.setHtml(self.html()); pr=QPrinter(QPrinter.HighResolution); pr.setOutputFormat(QPrinter.PdfFormat); pr.setOutputFileName(p); pr.setPageMargins(QMarginsF(8,8,8,8)); doc.print_(pr)
        QMessageBox.information(self,'PDF','Cartel guardado correctamente.')

    def print(self):
        if not printer_names(): show_no_printer(self); return
        n={'1 por hoja':1,'2 por hoja':2,'4 por hoja':4}[self.dist.currentText()]
        total=self.cant.value(); one=self.html().replace('<html><body','<div').replace('</body></html>','</div>')
        # Un documento A4 con una grilla de carteles. Se fuerza salto de página cada N carteles.
        chunks=[]
        for start in range(0,total,n):
            cells=[]
            for _ in range(min(n,total-start)):
                cells.append(f'<td style="width:{100/n}%;height:{96/n}vh;vertical-align:middle;padding:8px;">{one}</td>')
            while len(cells)<n: cells.append('<td style="width:'+str(100/n)+'%;"></td>')
            chunks.append('<table width="100%" cellspacing="0" cellpadding="0" style="page-break-after:always;"><tr>'+''.join(cells)+'</tr></table>')
        html_doc='<html><body style="margin:0;padding:0;">'+''.join(chunks)+'</body></html>'
        print_html(html_doc,self,'impresora_carteles')
