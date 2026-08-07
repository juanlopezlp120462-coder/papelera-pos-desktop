import sqlite3,datetime
from PySide6.QtWidgets import *
from ui.db import BASE_DATOS,init_db,get_setting
class Pedidos(QWidget):
 def __init__(self):
  super().__init__();init_db();self.setWindowTitle(f"Pedidos - {get_setting('nombre_negocio','COTILLON')}");self.resize(900,650);self.setStyleSheet('QWidget{background:#f8fafc;font-family:"Segoe UI";color:#0f172a} QLineEdit,QPlainTextEdit,QDateEdit{background:white;border:1px solid #cbd5e1;border-radius:10px;padding:10px} QPushButton{background:#0ea5e9;color:white;border:0;border-radius:10px;padding:11px;font-weight:800} QTableWidget{background:white;border:1px solid #e2e8f0;border-radius:12px} QHeaderView::section{background:#0f172a;color:white;padding:10px;font-weight:bold}');l=QVBoxLayout(self);t=QLabel('📋 Pedidos');t.setStyleSheet('font-size:28px;font-weight:800');l.addWidget(t);f=QFormLayout();self.cliente=QLineEdit();self.entrega=QDateEdit();self.entrega.setCalendarPopup(True);self.entrega.setDate(__import__('PySide6').QtCore.QDate.currentDate());self.obs=QLineEdit();self.obs.setPlaceholderText('Observaciones');self.items=QPlainTextEdit();self.items.setPlaceholderText('Producto; cantidad; precio — una línea por producto');f.addRow('Cliente',self.cliente);f.addRow('Entrega',self.entrega);f.addRow('Observaciones',self.obs);l.addLayout(f);l.addWidget(self.items);b=QPushButton('💾 Guardar pedido');b.clicked.connect(self.guardar);l.addWidget(b);self.lista=QTableWidget(0,5);self.lista.setHorizontalHeaderLabels(['Pedido','Fecha','Entrega','Estado','Total']);self.lista.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);l.addWidget(self.lista);self.cargar()
 def guardar(self):
  c=sqlite3.connect(BASE_DATOS);cur=c.cursor();cur.execute('INSERT INTO pedidos(fecha,entrega,estado,observaciones,total) VALUES(?,?,?,?,0)',(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),self.entrega.date().toString('yyyy-MM-dd'),'PENDIENTE',self.obs.text()));pid=cur.lastrowid;tot=0
  for line in self.items.toPlainText().splitlines():
   try:
    p,q,pr=[x.strip() for x in line.split(';')[:3]];q=int(q);pr=float(pr.replace(',','.'));sub=q*pr;tot+=sub;cur.execute('INSERT INTO detalle_pedidos(pedido_id,producto,cantidad,precio,subtotal) VALUES(?,?,?,?,?)',(pid,p,q,pr,sub))
   except:continue
  cur.execute('UPDATE pedidos SET total=? WHERE id=?',(tot,pid));c.commit();c.close();self.items.clear();self.cargar();QMessageBox.information(self,'Pedido','Pedido guardado correctamente.')
 def cargar(self):
  c=sqlite3.connect(BASE_DATOS);rows=c.execute('SELECT id,fecha,entrega,estado,total FROM pedidos ORDER BY id DESC').fetchall();c.close();self.lista.setRowCount(0)
  for i,r in enumerate(rows):self.lista.insertRow(i);[self.lista.setItem(i,j,QTableWidgetItem(str(v))) for j,v in enumerate(r)]
