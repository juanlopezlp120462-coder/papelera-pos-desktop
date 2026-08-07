import sqlite3
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from ui.db import BASE_DATOS, init_db
from ui.ticket import generar_ticket, imprimir_ticket, guardar_pdf

class Historial(QWidget):
    def __init__(self):
        super().__init__(); init_db(); self.setWindowTitle('Historial'); self.setStyleSheet('''
        QWidget{background:#f8fafc;font-family:"Segoe UI";color:#0f172a}
        QLineEdit,QComboBox{background:white;border:1px solid #cbd5e1;border-radius:10px;padding:10px}
        QPushButton{background:#0ea5e9;color:white;border:0;border-radius:9px;padding:10px 14px;font-weight:700}
        QPushButton.secondary{background:#e2e8f0;color:#334155} QPushButton.danger{background:#dc2626;color:white}
        QTableWidget{background:white;border:1px solid #e2e8f0;border-radius:12px;gridline-color:#e2e8f0}
        QHeaderView::section{background:#0f172a;color:white;padding:10px;border:0;font-weight:bold}
        QToolButton{font-size:20px;padding:2px}
        ''')
        l=QVBoxLayout(self); l.setContentsMargins(24,24,24,24); l.setSpacing(14)
        t=QLabel('🕘 Historial'); t.setStyleSheet('font-size:28px;font-weight:900'); l.addWidget(t)
        b=QHBoxLayout(); self.buscar=QLineEdit(); self.buscar.setPlaceholderText('Buscar ticket, fecha, cliente o forma de pago...'); self.buscar.textChanged.connect(self.cargar_historial); b.addWidget(self.buscar,4)
        self.tipo=QComboBox(); self.tipo.addItems(['Todos','Venta diaria','Arqueo']); self.tipo.currentTextChanged.connect(self.cargar_historial); b.addWidget(self.tipo)
        self.pago=QComboBox(); self.pago.addItems(['Todas','Efectivo','Tarjeta','Transferencia','Cuenta corriente']); self.pago.currentTextChanged.connect(self.cargar_historial); b.addWidget(self.pago)
        r=QPushButton('🔄 Actualizar'); r.clicked.connect(self.cargar_historial); b.addWidget(r); l.addLayout(b)
        actions=QHBoxLayout(); self.seleccionar=QPushButton('☑ Seleccionar todas'); self.seleccionar.setProperty('class','secondary'); self.seleccionar.clicked.connect(self.seleccionar_todas); actions.addWidget(self.seleccionar)
        self.eliminar=QPushButton('🗑 Eliminar ventas seleccionadas'); self.eliminar.setProperty('class','danger'); self.eliminar.clicked.connect(self.eliminar_seleccionadas); actions.addWidget(self.eliminar); actions.addStretch(); l.addLayout(actions)
        s=QHBoxLayout(); self.cant=QLabel(); self.total=QLabel(); self.prom=QLabel();
        for x in (self.cant,self.total,self.prom): x.setStyleSheet('background:white;border:1px solid #e2e8f0;border-radius:12px;padding:12px;font-weight:bold'); s.addWidget(x)
        l.addLayout(s)
        self.tabla=QTableWidget(0,8); self.tabla.setHorizontalHeaderLabels(['Tipo','N.º','Fecha','Cliente / detalle','Pago','Total','Estado','Acciones']); self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.tabla.setSelectionMode(QAbstractItemView.NoSelection); self.tabla.cellDoubleClicked.connect(lambda r,c:self.ver_ticket(r)); l.addWidget(self.tabla)
        self.cargar_historial()

    def showEvent(self, event):
        # El historial se refresca automáticamente cada vez que se vuelve a abrir,
        # así un arqueo recién guardado aparece sin pulsar Actualizar.
        super().showEvent(event)
        self.cargar_historial()

    def pago_texto(self, pay):
        e,t,ta,c=pay; parts=[]
        if float(e or 0): parts.append(f'Efectivo $ {float(e or 0):,.2f}')
        if float(t or 0): parts.append(f'Transf. $ {float(t or 0):,.2f}')
        if float(ta or 0): parts.append(f'Tarjeta $ {float(ta or 0):,.2f}')
        if float(c or 0): parts.append(f'Cuenta $ {float(c or 0):,.2f}')
        return ' | '.join(parts) if parts else '—'

    def cargar_historial(self):
        try:
            c=sqlite3.connect(BASE_DATOS); q=c.cursor(); term=self.buscar.text().strip(); tipo=self.tipo.currentText(); pago=self.pago.currentText(); rows=[]
            if tipo in ('Todos','Venta diaria'):
                for table,status in [('ventas','ACTIVA'),('ventas_archivo','ARCHIVADA')]:
                    sql=f"SELECT 'Venta diaria',v.id,v.fecha,COALESCE(cl.nombre,'Consumidor final'),COALESCE(v.forma_pago,''),v.total,COALESCE(v.estado,'{status}'),'{status}' FROM {table} v LEFT JOIN clientes cl ON cl.id=v.cliente_id WHERE 1=1"; a=[]
                    if term: sql+=' AND (CAST(v.id AS TEXT) LIKE ? OR v.fecha LIKE ? OR cl.nombre LIKE ? OR v.forma_pago LIKE ?)'; z='%'+term+'%'; a += [z,z,z,z]
                    if pago!='Todas': sql+=' AND (v.forma_pago LIKE ? OR (?="Efectivo" AND COALESCE(v.pago_efectivo,0)>0) OR (?="Transferencia" AND COALESCE(v.pago_transferencia,0)>0) OR (?="Tarjeta" AND COALESCE(v.pago_tarjeta,0)>0) OR (?="Cuenta corriente" AND COALESCE(v.pago_cuenta,0)>0))'; a += [f'%{pago}%',pago,pago,pago,pago]
                    for rr in q.execute(sql,a).fetchall():
                        pay=q.execute(f'SELECT COALESCE(pago_efectivo,0),COALESCE(pago_transferencia,0),COALESCE(pago_tarjeta,0),COALESCE(pago_cuenta,0) FROM {table} WHERE id=?',(rr[1],)).fetchone()
                        if pay and sum(float(v or 0) for v in pay)>0: rr=rr[:4]+(self.pago_texto(pay),)+rr[5:]
                        rows.append(rr)
            if tipo in ('Todos','Arqueo'):
                sql="SELECT 'Arqueo',id,fecha,('Efectivo: $ ' || printf('%.2f',COALESCE(ventas_efectivo,0)) || ' | Transferencia: $ ' || printf('%.2f',COALESCE(ventas_transferencia,0)) || ' | Tarjeta: $ ' || printf('%.2f',COALESCE(ventas_tarjeta,0)) || ' | Cuenta: $ ' || printf('%.2f',COALESCE(ventas_cuenta,0))), 'Todos los medios', COALESCE(ventas_total,0),'GUARDADO','ARQUEO' FROM arqueos WHERE 1=1"; a=[]
                if term: sql+=' AND (CAST(id AS TEXT) LIKE ? OR fecha LIKE ?)'; z='%'+term+'%'; a += [z,z]
                rows += q.execute(sql,a).fetchall()
            c.close(); rows.sort(key=lambda r:r[2], reverse=True); self.tabla.setRowCount(0); total=0; ventas=0
            for i,row in enumerate(rows):
                self.tabla.insertRow(i)
                for j,val in enumerate(row[:7]):
                    text=f'$ {val:,.2f}' if j==5 else str(val); it=QTableWidgetItem(text)
                    if j==0 and row[0]=='Venta diaria': it.setFlags(it.flags() | Qt.ItemIsUserCheckable); it.setCheckState(Qt.Unchecked)
                    it.setTextAlignment(Qt.AlignCenter if j in (0,1,4,6) else Qt.AlignVCenter); self.tabla.setItem(i,j,it)
                w=QWidget(); h=QHBoxLayout(w); h.setContentsMargins(0,0,0,0); h.setSpacing(4); h.setAlignment(Qt.AlignCenter)
                if row[0]=='Venta diaria':
                    ventas+=1; total+=float(row[5] or 0); acts=[('👁','Ver ticket',self.ver_ticket),('📄','Guardar PDF',self.pdf_ticket),('🖨','Imprimir',self.imprimir)]
                else:
                    acts=[('👁','Ver arqueo',self.ver_arqueo),('📄','Guardar PDF',self.pdf_arqueo),('🖨','Imprimir',self.imprimir_arqueo)]
                for icon,tip,fn in acts:
                    x=QToolButton(); x.setText(icon); x.setToolTip(tip); x.setFixedSize(44,38); x.setAutoRaise(True); x.setStyleSheet('QToolButton{font-size:20px;padding:0;margin:0;}'); x.clicked.connect(lambda _,rr=i,f=fn:f(rr)); h.addWidget(x)
                self.tabla.setCellWidget(i,7,w)
            self.cant.setText(f'Ventas: {ventas}'); self.total.setText(f'Total ventas: $ {total:,.2f}'); self.prom.setText(f'Promedio: $ {(total/ventas if ventas else 0):,.2f}')
        except Exception as e: QMessageBox.critical(self,'Error','No se pudo cargar historial:\n'+str(e))

    def arqueo_html(self,r):
        item = self.tabla.item(r,1)
        if not item:
            return '<h2>Arqueo no encontrado</h2>'
        n=int(item.text())
        # Mantener la conexión abierta hasta terminar todas las consultas.
        # Esto evita el error "cannot operate on a closed database" al ver/imprimir.
        con=sqlite3.connect(BASE_DATOS)
        try:
            row=con.execute('SELECT fecha,apertura,esperado,real,diferencia,usuario,observaciones,COALESCE(ventas_total,0),COALESCE(ventas_efectivo,0),COALESCE(ventas_transferencia,0),COALESCE(ventas_tarjeta,0),COALESCE(ventas_cuenta,0),COALESCE(cantidad_ventas,0) FROM arqueos WHERE id=?',(n,)).fetchone()
        finally:
            con.close()
        if not row:
            return '<h2>Arqueo no encontrado</h2>'
        return f'<html><body style="font-family:Arial;color:#111"><h1 style="text-align:center">ARQUEO DE CAJA</h1><hr><b>N.º:</b> {n:06d}<br><b>Fecha:</b> {row[0]}<br><b>Usuario:</b> {row[5] or ""}<hr><b>Total de ventas:</b> $ {float(row[7] or 0):,.2f}<br><b>Efectivo:</b> $ {float(row[8] or 0):,.2f}<br><b>Transferencias:</b> $ {float(row[9] or 0):,.2f}<br><b>Tarjetas:</b> $ {float(row[10] or 0):,.2f}<br><b>Cuenta corriente:</b> $ {float(row[11] or 0):,.2f}<br><b>Cantidad de ventas:</b> {int(row[12] or 0)}<hr><b>Efectivo inicial:</b> $ {float(row[1] or 0):,.2f}<br><b>Efectivo esperado:</b> $ {float(row[2] or 0):,.2f}<br><b>Efectivo contado:</b> $ {float(row[3] or 0):,.2f}<br><b>Diferencia:</b> $ {float(row[4] or 0):,.2f}<hr><b>Observaciones:</b> {row[6] or "—"}</body></html>'

    def seleccionar_todas(self):
        for r in range(self.tabla.rowCount()):
            if self.tabla.item(r,0) and self.tabla.item(r,0).text()=='Venta diaria': self.tabla.item(r,0).setCheckState(Qt.Checked)

    def eliminar_seleccionadas(self):
        ids=[int(self.tabla.item(r,1).text()) for r in range(self.tabla.rowCount()) if self.tabla.item(r,0) and self.tabla.item(r,0).text()=='Venta diaria' and self.tabla.item(r,0).checkState()==Qt.Checked]
        if not ids: QMessageBox.information(self,'Historial','Seleccioná al menos una venta.'); return
        if QMessageBox.question(self,'Eliminar ventas',f'Se eliminarán definitivamente {len(ids)} ventas seleccionadas. ¿Continuar?',QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        try:
            c=sqlite3.connect(BASE_DATOS); marks=','.join('?' for _ in ids); c.execute(f'DELETE FROM detalle_ventas WHERE venta_id IN ({marks})',ids); c.execute(f'DELETE FROM detalle_ventas_archivo WHERE venta_id IN ({marks})',ids); c.execute(f'DELETE FROM ventas WHERE id IN ({marks})',ids); c.execute(f'DELETE FROM ventas_archivo WHERE id IN ({marks})',ids); c.commit(); c.close(); self.cargar_historial()
        except Exception as e: QMessageBox.critical(self,'Error',str(e))

    def ver_ticket(self,r):
        if self.tabla.item(r,0).text()!='Venta diaria': return
        d=QDialog(self); d.setWindowTitle('Ticket'); d.resize(520,650); l=QVBoxLayout(d); v=QTextBrowser(); v.setHtml(generar_ticket(int(self.tabla.item(r,1).text()))); l.addWidget(v); b=QPushButton('Cerrar'); b.clicked.connect(d.accept); l.addWidget(b); d.exec()
    def pdf_ticket(self,r):
        if self.tabla.item(r,0).text()!='Venta diaria': return
        p,_=QFileDialog.getSaveFileName(self,'Guardar ticket PDF',f'ticket_{int(self.tabla.item(r,1).text()):06d}.pdf','PDF (*.pdf)');
        if p: guardar_pdf(generar_ticket(int(self.tabla.item(r,1).text())),p)
    def imprimir(self,r):
        if self.tabla.item(r,0).text()!='Venta diaria': return
        try: imprimir_ticket(generar_ticket(int(self.tabla.item(r,1).text())),self)
        except Exception as e: QMessageBox.warning(self,'No se pudo imprimir',str(e))
    def ver_arqueo(self,r):
        if self.tabla.item(r,0).text()!='Arqueo': return
        d=QDialog(self); d.setWindowTitle('Arqueo de caja'); d.resize(560,520); l=QVBoxLayout(d); v=QTextBrowser(); v.setHtml(self.arqueo_html(r)); l.addWidget(v); b=QPushButton('Cerrar'); b.clicked.connect(d.accept); l.addWidget(b); d.exec()
    def pdf_arqueo(self,r):
        if self.tabla.item(r,0).text()!='Arqueo': return
        p,_=QFileDialog.getSaveFileName(self,'Guardar arqueo PDF',f'arqueo_{int(self.tabla.item(r,1).text()):06d}.pdf','PDF (*.pdf)');
        if p: guardar_pdf(self.arqueo_html(r),p)
    def imprimir_arqueo(self,r):
        if self.tabla.item(r,0).text()!='Arqueo': return
        try: imprimir_ticket(self.arqueo_html(r),self)
        except Exception as e: QMessageBox.warning(self,'No se pudo imprimir',str(e))
