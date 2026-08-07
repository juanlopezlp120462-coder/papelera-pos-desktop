import os
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QUrl
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrinterInfo
from ui.db import get_setting, set_setting, create_backup, find_removable_backups, restore_backup
from ui.printing import printer_names, show_no_printer, print_html

class VentanaActividadMercadoPago(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mercado Pago — Actividad")
        self.resize(850, 750)
        self.setMinimumSize(650, 550)
        self.setModal(False)

        try:
            from PySide6.QtWebEngineWidgets import QWebEngineView
            from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
        except ImportError:
            QMessageBox.warning(
                self, "Mercado Pago",
                "Falta PySide6-WebEngine. Ejecutá:\n\npip install PySide6-WebEngine"
            )
            return

        layout = QVBoxLayout(self)

        base = os.path.join(
            os.path.expanduser("~"), ".cotillon_pos", "mercadopago_web"
        )
        os.makedirs(base, exist_ok=True)

        # El perfil vive mientras vive esta ventana; la ventana se oculta al
        # cerrar, no se destruye. Así las cookies y WebEnginePage no se liberan
        # en un orden incorrecto.
        self.profile = QWebEngineProfile("MercadoPagoPOS", self)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.ForcePersistentCookies
        )
        self.profile.setPersistentStoragePath(base)
        self.profile.setCachePath(os.path.join(base, "cache"))

        self.web = QWebEngineView(self)
        self.page = QWebEnginePage(self.profile, self.web)
        self.web.setPage(self.page)
        self.web.loadFinished.connect(self._actividad_cargada)
        self.web.setUrl(QUrl("https://www.mercadopago.com.ar/activities"))
        layout.addWidget(self.web)

        barra = QHBoxLayout()
        barra.addStretch()

        cerrar_sesion = QPushButton("🔒 Cerrar sesión de Mercado Pago")
        cerrar_sesion.setProperty("class", "secondary")
        cerrar_sesion.clicked.connect(self.cerrar_sesion)
        barra.addWidget(cerrar_sesion)

        cerrar = QPushButton("Cerrar")
        cerrar.clicked.connect(self.close)
        barra.addWidget(cerrar)
        layout.addLayout(barra)

    def _actividad_cargada(self, ok):
        if not ok and self.isVisible():
            QTimer.singleShot(
                800,
                lambda: self.web.setUrl(
                    QUrl("https://www.mercadopago.com.ar/activities")
                )
            )

    def cerrar_sesion(self):
        self.profile.cookieStore().deleteAllCookies()
        self.profile.clearHttpCache()
        self.profile.clearAllVisitedLinks()
        self.web.setUrl(QUrl("https://www.mercadopago.com.ar/activities"))

    def closeEvent(self, event):
        # No destruimos QWebEnginePage/QWebEngineProfile al cerrar.
        # Solo ocultamos la ventana para poder abrirla nuevamente sin pantalla blanca.
        event.ignore()
        self.hide()


class Configuracion(QWidget):
    def __init__(self):
        super().__init__(); self.setObjectName('configuracion'); self.setWindowTitle('Configuración')
        self.setStyleSheet('''
            QWidget#configuracion{background:#f8fafc;color:#0f172a;font-family:"Segoe UI"}
            QTabWidget::pane{border:1px solid #e2e8f0;border-radius:16px;background:#f8fafc;top:-1px}
            QTabBar::tab{background:#e2e8f0;color:#334155;padding:11px 18px;margin-right:4px;border-radius:9px;font-weight:800}
            QTabBar::tab:selected{background:#0ea5e9;color:white}
            QGroupBox{background:white;border:1px solid #e2e8f0;border-radius:16px;margin-top:18px;padding:18px;font-weight:800}
            QGroupBox::title{subcontrol-origin:margin;left:16px;padding:0 8px;color:#0f172a;background:white}
            QLineEdit,QComboBox,QSpinBox{background:white;border:1px solid #cbd5e1;border-radius:9px;padding:9px;min-height:20px}
            QLineEdit:focus,QComboBox:focus,QSpinBox:focus{border:2px solid #38bdf8}
            QPushButton{background:#0ea5e9;color:white;border:0;border-radius:10px;padding:11px 15px;font-weight:800}
            QPushButton:hover{background:#0284c7} QPushButton.secondary{background:#e2e8f0;color:#334155}
            QPushButton.danger{background:#ef4444} QLabel.muted{color:#64748b;font-size:13px}
            QCheckBox{spacing:8px;padding:5px}
        ''')
        root=QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(16)
        head=QHBoxLayout(); title=QLabel('⚙️ Configuración'); title.setStyleSheet('font-size:30px;font-weight:900'); head.addWidget(title); head.addStretch(); save=QPushButton('💾 Guardar cambios'); save.clicked.connect(self.guardar); head.addWidget(save); root.addLayout(head)
        sub=QLabel('Configurá la identidad, impresión, seguridad, pagos y comportamiento del sistema desde un solo lugar.'); sub.setProperty('class','muted'); root.addWidget(sub)
        self.tabs=QTabWidget(); root.addWidget(self.tabs,1); self._build_business_tab(); self._build_print_tab(); self._build_payments_tab(); self._build_backup_tab(); self._build_system_tab()

    def _field(self,key,default=''): return QLineEdit(get_setting(key,default))

    def _build_business_tab(self):
        tab=QWidget(); lay=QVBoxLayout(tab); lay.setContentsMargins(8,18,8,8)
        box=QGroupBox('🏪 Identidad del negocio'); form=QFormLayout(box)
        self.nombre=self._field('nombre_negocio','COTILLON'); self.direccion=self._field('direccion'); self.telefono=self._field('telefono'); self.email=self._field('email'); self.cuit=self._field('cuit'); self.logo=self._field('logo_path')
        for label,w in [('Nombre:',self.nombre),('Dirección:',self.direccion),('Teléfono:',self.telefono),('Email:',self.email),('CUIT / dato fiscal:',self.cuit)]: form.addRow(label,w)
        row=QHBoxLayout(); row.addWidget(self.logo,1); b=QPushButton('📁 Buscar logo'); b.setProperty('class','secondary'); b.clicked.connect(self.seleccionar_logo); row.addWidget(b); form.addRow('Logo:',row); lay.addWidget(box)
        box2=QGroupBox('🧾 Personalización de comprobantes'); f=QFormLayout(box2); self.pie=self._field('pie_ticket','¡Gracias por su compra!'); self.observaciones=self._field('pie_documento',''); f.addRow('Pie del ticket:',self.pie); f.addRow('Pie de documentos:',self.observaciones); lay.addWidget(box2); lay.addStretch(); self.tabs.addTab(tab,'🏪 Negocio')

    def _printer_combo(self,key):
        c=QComboBox(); c.setObjectName(key); c.addItem('Seleccionar automáticamente', ''); names=printer_names();
        for n in names:c.addItem(n,n)
        current=get_setting(key,''); idx=c.findData(current); c.setCurrentIndex(idx if idx>=0 else 0); return c

    def _build_print_tab(self):
        tab=QWidget(); lay=QVBoxLayout(tab); lay.setContentsMargins(8,18,8,8)
        box=QGroupBox('🖨️ Configuración de impresión'); grid=QGridLayout(box)
        self.ancho_ticket=QComboBox(); self.ancho_ticket.addItems(['58 mm','80 mm']); self.ancho_ticket.setCurrentText(get_setting('ancho_ticket','80 mm'))
        self.formato_papel=QComboBox(); self.formato_papel.addItems(['Ticket 58 mm','Ticket 80 mm','A4','A5']); self.formato_papel.setCurrentText(get_setting('formato_papel','Ticket 80 mm'))
        self.copias_ticket=QSpinBox(); self.copias_ticket.setRange(1,10); self.copias_ticket.setValue(int(get_setting('copias_ticket','1') or 1))
        self.impresora_ticket=self._printer_combo('impresora_ticket'); self.impresora_a4=self._printer_combo('impresora_a4'); self.impresora_carteles=self._printer_combo('impresora_carteles')
        grid.addWidget(QLabel('Ancho de ticket:'),0,0); grid.addWidget(self.ancho_ticket,0,1)
        grid.addWidget(QLabel('Formato de papel:'),1,0); grid.addWidget(self.formato_papel,1,1)
        grid.addWidget(QLabel('Copias de ticket:'),2,0); grid.addWidget(self.copias_ticket,2,1)
        grid.addWidget(QLabel('Impresora de tickets:'),3,0); grid.addWidget(self.impresora_ticket,3,1)
        grid.addWidget(QLabel('Impresora A4:'),4,0); grid.addWidget(self.impresora_a4,4,1)
        grid.addWidget(QLabel('Impresora de carteles:'),5,0); grid.addWidget(self.impresora_carteles,5,1)
        lay.addWidget(box)
        row=QHBoxLayout(); refresh=QPushButton('🔄 Detectar impresoras'); refresh.setProperty('class','secondary'); refresh.clicked.connect(self._refresh_printers); test=QPushButton('🧪 Imprimir prueba'); test.clicked.connect(self._test_print); row.addWidget(refresh); row.addWidget(test); row.addStretch(); lay.addLayout(row)
        status=QGroupBox('📡 Estado de Windows'); sl=QVBoxLayout(status); self.printer_status=QLabel(); self.printer_status.setWordWrap(True); sl.addWidget(self.printer_status); lay.addWidget(status); self._update_printer_status(); lay.addStretch(); self.tabs.addTab(tab,'🖨️ Impresión')

    def _refresh_printers(self):
        for combo in (self.impresora_ticket,self.impresora_a4,self.impresora_carteles):
            current=combo.currentData(); combo.clear(); combo.addItem('Seleccionar automáticamente','')
            for n in printer_names():combo.addItem(n,n)
            idx=combo.findData(current); combo.setCurrentIndex(idx if idx>=0 else 0)
        self._update_printer_status()
        if printer_names(): QMessageBox.information(self,'Impresoras','Se detectaron: \n\n'+'\n'.join(printer_names()))
        else: show_no_printer(self)

    def _update_printer_status(self):
        names=printer_names(); self.printer_status.setText(('🟢 Impresoras detectadas: '+str(len(names))+'\n\n'+'\n'.join('• '+n for n in names)) if names else '🔴 No se detectó ninguna impresora en el sistema.\nConectá o instalá una impresora de Windows para poder imprimir.')
        self.printer_status.setStyleSheet('color:#166534;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:12px;' if names else 'color:#991b1b;background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:12px;')

    def _test_print(self):
        names=printer_names()
        if not names: show_no_printer(self); return
        html='<html><body style="font-family:Arial;text-align:center"><h1>COTILLON</h1><h2>PRUEBA DE IMPRESIÓN</h2><p>La impresora está correctamente detectada por Windows.</p></body></html>'
        print_html(html,self,'impresora_a4')


    def _build_payments_tab(self):
        tab=QWidget(); lay=QVBoxLayout(tab); lay.setContentsMargins(8,18,8,8)
        box=QGroupBox('💳 Mercado Pago — pagos y movimientos'); form=QFormLayout(box)
        self.mp_estado=QLabel(); self.mp_estado.setWordWrap(True)
        self._actualizar_estado_mp(); form.addRow('Estado:',self.mp_estado)
        info=QLabel('Los pagos se consultan automáticamente cada 15 segundos. Para ver también retiros, devoluciones, contracargos y otros movimientos que afectan el saldo, el POS puede generar e importar el reporte oficial “Todas las transacciones” de Mercado Pago.')
        info.setWordWrap(True); info.setProperty('class','muted'); form.addRow(info)
        row=QHBoxLayout()
        btn=QPushButton('🔗 Configurar / conectar'); btn.clicked.connect(self._configurar_mercado_pago)
        guide=QPushButton('📖 Guía oficial'); guide.setProperty('class','secondary'); guide.clicked.connect(self._abrir_guia_mp)
        actividad=QPushButton('🔵 Ver actividad de Mercado Pago'); actividad.setProperty('class','secondary'); actividad.clicked.connect(self._abrir_actividad_mercado_pago)
        row.addWidget(btn); row.addWidget(guide); row.addWidget(actividad); row.addStretch(); form.addRow(row)
        lay.addWidget(box)

        box2=QGroupBox('💚 Pagos recibidos — consulta automática'); l=QVBoxLayout(box2)
        self.mp_auto=QCheckBox('🔔 Actualizar pagos automáticamente cada 15 segundos')
        self.mp_auto.setChecked(get_setting('mp_auto_refresh','1')=='1')
        self.mp_auto.stateChanged.connect(self._toggle_mp_auto); l.addWidget(self.mp_auto)
        row2=QHBoxLayout()
        upd=QPushButton('🔄 Actualizar pagos ahora'); upd.clicked.connect(self._actualizar_comprobantes)
        row2.addWidget(upd); row2.addStretch(); l.addLayout(row2)
        self.mp_lista=QTableWidget(0,6)
        self.mp_lista.setHorizontalHeaderLabels(['Estado','Fecha','Importe','Operación','Medio','Detalle'])
        self.mp_lista.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mp_lista.setMinimumHeight(220); self.mp_lista.setAlternatingRowColors(True)
        self.mp_lista.setStyleSheet('''
            QTableWidget {
                background: #ffffff;
                color: #0f172a;
                gridline-color: #dbe3ea;
                selection-background-color: #dbeafe;
                selection-color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
            QTableWidget::item {
                background: #ffffff;
                color: #0f172a;
                padding: 6px;
            }
            QTableWidget::item:alternate {
                background: #f8fafc;
                color: #0f172a;
            }
            QTableWidget::item:selected {
                background: #dbeafe;
                color: #0f172a;
            }
            QHeaderView::section {
                background: #e2e8f0;
                color: #0f172a;
                font-weight: 800;
                padding: 7px;
                border: 0;
                border-right: 1px solid #cbd5e1;
            }
        ''')
        l.addWidget(self.mp_lista)
        self.mp_ultima=QLabel(''); self.mp_ultima.setProperty('class','muted'); l.addWidget(self.mp_ultima)
        lay.addWidget(box2)

        box3=QGroupBox('📊 Todos los movimientos de la cuenta'); l3=QVBoxLayout(box3)
        desc=QLabel('Incluye movimientos que afectan el saldo, como pagos, ingresos, devoluciones, contracargos y retiros. Mercado Pago genera este reporte de forma asíncrona.')
        desc.setWordWrap(True); desc.setProperty('class','muted'); l3.addWidget(desc)
        row3=QHBoxLayout()
        self.mp_mov_btn=QPushButton('📥 Obtener movimientos de los últimos 7 días')
        self.mp_mov_btn.clicked.connect(self._obtener_movimientos_completos)
        row3.addWidget(self.mp_mov_btn)
        self.mp_mov_estado=QLabel(''); self.mp_mov_estado.setProperty('class','muted'); row3.addWidget(self.mp_mov_estado); row3.addStretch()
        l3.addLayout(row3)
        self.mp_mov_lista=QTableWidget(0,8)
        self.mp_mov_lista.setHorizontalHeaderLabels(['Fecha','Tipo','Importe','Neto','Referencia','Descripción','Estado','Fuente'])
        self.mp_mov_lista.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mp_mov_lista.setMinimumHeight(260); self.mp_mov_lista.setAlternatingRowColors(True)
        self.mp_mov_lista.setStyleSheet('''
            QTableWidget {
                background: #ffffff;
                color: #0f172a;
                gridline-color: #dbe3ea;
                selection-background-color: #dbeafe;
                selection-color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
            QTableWidget::item {
                background: #ffffff;
                color: #0f172a;
                padding: 6px;
            }
            QTableWidget::item:alternate {
                background: #f8fafc;
                color: #0f172a;
            }
            QTableWidget::item:selected {
                background: #dbeafe;
                color: #0f172a;
            }
            QHeaderView::section {
                background: #e2e8f0;
                color: #0f172a;
                font-weight: 800;
                padding: 7px;
                border: 0;
                border-right: 1px solid #cbd5e1;
            }
        ''')
        l3.addWidget(self.mp_mov_lista)
        lay.addWidget(box3); lay.addStretch(); self.tabs.addTab(tab,'💳 Pagos')

        self._mp_timer=QTimer(self); self._mp_timer.setInterval(15000)
        self._mp_timer.timeout.connect(self._actualizar_comprobantes_silencioso)
        if self.mp_auto.isChecked(): self._mp_timer.start()
        self._cargar_comprobantes_guardados(); self._cargar_movimientos_guardados()

    def _actualizar_estado_mp(self):
        token=get_setting('mp_access_token','').strip()
        conectado=get_setting('mp_conectado','0')=='1' and bool(token)
        if conectado:
            self.mp_estado.setText('🟢 Mercado Pago conectado — pagos habilitados')
            self.mp_estado.setStyleSheet('font-weight:900;color:#166534;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:9px;padding:10px;')
        else:
            self.mp_estado.setText('🔴 Mercado Pago no conectado')
            self.mp_estado.setStyleSheet('font-weight:900;color:#b91c1c;background:#fef2f2;border:1px solid #fecaca;border-radius:9px;padding:10px;')

    def _toggle_mp_auto(self,state):
        on=bool(state); set_setting('mp_auto_refresh','1' if on else '0')
        if hasattr(self,'_mp_timer'):
            if on:self._mp_timer.start()
            else:self._mp_timer.stop()

    def _cargar_comprobantes_guardados(self):
        try:
            from ui.mercadopago import ultimos_guardados
            self._llenar_tabla_mp(ultimos_guardados(100))
        except Exception: pass

    def _llenar_tabla_mp(self,rows):
        self.mp_lista.setRowCount(0)
        for row in rows:
            r=self.mp_lista.rowCount(); self.mp_lista.insertRow(r)
            vals=[row[2],row[1],f"$ {row[3]:,.2f}".replace(',','X').replace('.',',').replace('X','.'),row[4],row[5],row[6]]
            for c,v in enumerate(vals):
                item=QTableWidgetItem(str(v)); item.setTextAlignment(Qt.AlignCenter if c<5 else Qt.AlignLeft|Qt.AlignVCenter); self.mp_lista.setItem(r,c,item)

    def _actualizar_comprobantes(self):
        token=get_setting('mp_access_token','').strip()
        if not token:
            QMessageBox.warning(self,'Mercado Pago','Primero configurá el Access Token de producción de Mercado Pago.'); return
        try:
            from ui.mercadopago import buscar_pagos,guardar_pagos,ultimos_guardados
            pagos=buscar_pagos(token,dias=30,limite=50); guardar_pagos(pagos)
            self._llenar_tabla_mp(ultimos_guardados(100))
            self.mp_ultima.setText('Última actualización: '+__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M:%S')+f' — {len(pagos)} pagos consultados.')
            set_setting('mp_conectado','1'); self._actualizar_estado_mp()
        except Exception as e: QMessageBox.critical(self,'Mercado Pago','No se pudieron consultar los pagos.\n\n'+str(e))

    def _actualizar_comprobantes_silencioso(self):
        token=get_setting('mp_access_token','').strip()
        if not token:return
        try:
            from ui.mercadopago import buscar_pagos,guardar_pagos,ultimos_guardados
            pagos=buscar_pagos(token,dias=30,limite=50); guardar_pagos(pagos); self._llenar_tabla_mp(ultimos_guardados(100))
            self.mp_ultima.setText('Última actualización: '+__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M:%S')+f' — {len(pagos)} pagos consultados.')
            set_setting('mp_conectado','1'); self._actualizar_estado_mp()
        except Exception: pass

    def _cargar_movimientos_guardados(self):
        try:
            from ui.mercadopago import ultimos_movimientos
            rows=ultimos_movimientos(200); self.mp_mov_lista.setRowCount(0)
            for row in rows:
                r=self.mp_mov_lista.rowCount(); self.mp_mov_lista.insertRow(r)
                vals=[row[1],row[2],self._mp_money(row[3]),self._mp_money(row[4]),row[5],row[6],row[7],row[8]]
                for c,v in enumerate(vals):
                    it=QTableWidgetItem(str(v)); it.setTextAlignment(Qt.AlignCenter if c!=5 else Qt.AlignLeft|Qt.AlignVCenter); self.mp_mov_lista.setItem(r,c,it)
        except Exception: pass

    def _mp_money(self,v):
        try:return f"$ {float(v):,.2f}".replace(',','X').replace('.',',').replace('X','.')
        except Exception:return str(v or '')

    def _obtener_movimientos_completos(self):
        token=get_setting('mp_access_token','').strip()
        if not token:
            QMessageBox.warning(self,'Mercado Pago','Primero configurá el Access Token de producción.'); return
        try:
            import datetime
            now=datetime.datetime.now(datetime.timezone.utc); begin=now-datetime.timedelta(days=7)
            from ui.mercadopago import crear_reporte_movimientos
            self.mp_mov_btn.setEnabled(False); self.mp_mov_estado.setText('Generando reporte de movimientos...')
            task=crear_reporte_movimientos(token,begin.strftime('%Y-%m-%dT%H:%M:%SZ'),now.strftime('%Y-%m-%dT%H:%M:%SZ'))
            self._mp_report_token=token; self._mp_report_task=task.get('id') or task.get('task_id')
            if not self._mp_report_task: raise RuntimeError('Mercado Pago no devolvió el ID de la tarea.')
            if not hasattr(self,'_mp_report_timer'):
                self._mp_report_timer=QTimer(self); self._mp_report_timer.timeout.connect(self._comprobar_reporte_movimientos)
            self._mp_report_timer.start(2000)
        except Exception as e:
            self.mp_mov_btn.setEnabled(True); self.mp_mov_estado.setText(''); QMessageBox.critical(self,'Mercado Pago','No se pudo generar el reporte.\n\n'+str(e))

    def _comprobar_reporte_movimientos(self):
        try:
            from ui.mercadopago import estado_reporte,descargar_reporte,importar_csv_movimientos
            st=estado_reporte(self._mp_report_token,self._mp_report_task); status=str(st.get('status') or '').lower()
            if status in ('processed','completed','success','finished'):
                self._mp_report_timer.stop(); name=st.get('file_name')
                if not name:
                    raise RuntimeError('El reporte terminó pero Mercado Pago no informó el archivo.')
                data=descargar_reporte(self._mp_report_token,name); n=importar_csv_movimientos(data)
                self._cargar_movimientos_guardados(); self.mp_mov_btn.setEnabled(True)
                self.mp_mov_estado.setText(f'✅ Movimientos actualizados: {n} registros importados.')
            elif status in ('failed','error','cancelled'):
                self._mp_report_timer.stop(); self.mp_mov_btn.setEnabled(True); self.mp_mov_estado.setText(''); QMessageBox.warning(self,'Mercado Pago','Mercado Pago no pudo generar el reporte.')
            else:
                self.mp_mov_estado.setText(f'Generando reporte... estado: {status or "pendiente"}')
        except Exception as e:
            self._mp_report_timer.stop(); self.mp_mov_btn.setEnabled(True); self.mp_mov_estado.setText(''); QMessageBox.critical(self,'Mercado Pago','No se pudo leer el reporte.\n\n'+str(e))

    def _abrir_guia_mp(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl('https://www.mercadopago.com.ar/developers/es/docs/security/oauth'))

    def _abrir_actividad_mercado_pago(self):
        # Reutilizar la misma ventana evita destruir el perfil WebEngine.
        if not hasattr(self, "_ventana_actividad_mp") or self._ventana_actividad_mp is None:
            self._ventana_actividad_mp = VentanaActividadMercadoPago(self)
        self._ventana_actividad_mp.show()
        self._ventana_actividad_mp.raise_()
        self._ventana_actividad_mp.activateWindow()

    def _configurar_mercado_pago(self):
        import json
        from ui.mercadopago import listar_cuentas, guardar_cuentas, probar_token
        d=QDialog(self); d.setWindowTitle('Cuentas de Mercado Pago'); d.resize(820,680)
        d.setStyleSheet('''
            QDialog { background:#f8fafc; color:#0f172a; }
            QLabel { color:#0f172a; font-size:14px; }
            QLabel#mpTitle { font-size:25px; font-weight:900; color:#0f172a; }
            QLabel#mpInfo { color:#334155; font-size:14px; line-height:1.3; }
            QComboBox, QLineEdit { background:#ffffff; color:#0f172a; border:2px solid #cbd5e1; border-radius:9px; padding:9px 11px; min-height:20px; font-size:14px; }
            QComboBox:focus, QLineEdit:focus { border:2px solid #2563eb; }
            QComboBox QAbstractItemView { background:#ffffff; color:#0f172a; selection-background-color:#dbeafe; selection-color:#1e3a8a; }
            QPushButton { background:#0ea5e9; color:#ffffff; border:0; border-radius:9px; padding:10px 15px; font-weight:800; min-height:18px; }
            QPushButton:hover { background:#0284c7; }
            QPushButton[class="danger"] { background:#ef4444; }
            QPushButton[class="secondary"] { background:#64748b; }
        ''')
        lay=QVBoxLayout(d); title=QLabel('💳 Cuentas de Mercado Pago'); title.setObjectName('mpTitle'); lay.addWidget(title)
        info=QLabel('Podés guardar varias cuentas. La cuenta seleccionada será la que el POS use para detectar automáticamente los cobros. Los Access Token se guardan localmente en la base de datos del POS.'); info.setObjectName('mpInfo'); info.setWordWrap(True); lay.addWidget(info)
        cuentas=listar_cuentas()
        if not cuentas and get_setting('mp_access_token','').strip(): cuentas=[{'nombre':'Cuenta principal','token':get_setting('mp_access_token','').strip(),'client_id':get_setting('mp_client_id',''),'client_secret':get_setting('mp_client_secret',''),'webhook_secret':get_setting('mp_webhook_secret','')}]
        selector=QComboBox(); selector.addItems([str(c.get('nombre') or f'Cuenta {i+1}') for i,c in enumerate(cuentas)]); lay.addWidget(QLabel('Cuenta activa:')); lay.addWidget(selector)
        form=QFormLayout(); nombre=QLineEdit(); token=QLineEdit(); token.setEchoMode(QLineEdit.Password); client=QLineEdit(); secret=QLineEdit(); secret.setEchoMode(QLineEdit.Password); wh=QLineEdit(); wh.setEchoMode(QLineEdit.Password)
        wh.setProperty('keyboard_last', True)
        form.addRow('Nombre:',nombre); form.addRow('Access Token:',token); form.addRow('Client ID:',client); form.addRow('Client Secret:',secret); form.addRow('Webhook Secret:',wh); lay.addLayout(form)
        def cargar(i):
            if i<0 or i>=len(cuentas):
                for w in (nombre,token,client,secret,wh):w.clear()
                return
            c=cuentas[i]; nombre.setText(str(c.get('nombre',''))); token.setText(str(c.get('token',''))); client.setText(str(c.get('client_id',''))); secret.setText(str(c.get('client_secret',''))); wh.setText(str(c.get('webhook_secret','')))
        selector.currentIndexChanged.connect(cargar); cargar(0 if cuentas else -1)
        b=QHBoxLayout(); nuevo=QPushButton('➕ Nueva cuenta'); guardar=QPushButton('💾 Guardar'); probar=QPushButton('🧪 Probar conexión'); eliminar=QPushButton('🗑️ Eliminar'); eliminar.setProperty('class','danger'); cerrar=QPushButton('Cerrar'); cerrar.setProperty('class','secondary')
        b.addWidget(nuevo); b.addWidget(guardar); b.addWidget(probar); b.addWidget(eliminar); b.addStretch(); b.addWidget(cerrar); lay.addLayout(b)
        def guardar_actual():
            i=selector.currentIndex(); c={'nombre':nombre.text().strip() or f'Cuenta {i+1}','token':token.text().strip(),'client_id':client.text().strip(),'client_secret':secret.text().strip(),'webhook_secret':wh.text().strip()}
            if i<0: cuentas.append(c); selector.addItem(c['nombre']); selector.setCurrentIndex(len(cuentas)-1); i=len(cuentas)-1
            else: cuentas[i]=c; selector.setItemText(i,c['nombre'])
            guardar_cuentas(cuentas,selector.currentIndex()); set_setting('mp_access_token',c['token']); set_setting('mp_client_id',c['client_id']); set_setting('mp_client_secret',c['client_secret']); set_setting('mp_webhook_secret',c['webhook_secret']); set_setting('mp_conectado','1' if c['token'] else '0'); self._actualizar_estado_mp(); QMessageBox.information(d,'Mercado Pago','Cuenta guardada y seleccionada como activa.')
        def nueva():
            cuentas.append({'nombre':f'Cuenta {len(cuentas)+1}','token':'','client_id':'','client_secret':'','webhook_secret':''}); selector.addItem(cuentas[-1]['nombre']); selector.setCurrentIndex(len(cuentas)-1); cargar(len(cuentas)-1)
        def eliminar_cuenta():
            i=selector.currentIndex()
            if i<0:return
            if QMessageBox.question(d,'Eliminar cuenta','¿Eliminar esta cuenta del POS?',QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
            cuentas.pop(i); selector.removeItem(i); guardar_cuentas(cuentas,max(0,selector.currentIndex())); cargar(selector.currentIndex())
        def cambiar_activa(i):
            if i>=0: guardar_cuentas(cuentas,i); c=cuentas[i] if i<len(cuentas) else {}; set_setting('mp_access_token',str(c.get('token',''))); set_setting('mp_client_id',str(c.get('client_id',''))); set_setting('mp_client_secret',str(c.get('client_secret',''))); set_setting('mp_webhook_secret',str(c.get('webhook_secret',''))); set_setting('mp_conectado','1' if c.get('token') else '0'); self._actualizar_estado_mp()
        selector.currentIndexChanged.connect(cambiar_activa); nuevo.clicked.connect(nueva); guardar.clicked.connect(guardar_actual); eliminar.clicked.connect(eliminar_cuenta); cerrar.clicked.connect(d.accept)
        def test_conn():
            t=token.text().strip()
            if not t: QMessageBox.warning(d,'Falta Access Token','Pegá el Access Token de producción para probar la conexión.'); return
            try: pagos=probar_token(t); QMessageBox.information(d,'Mercado Pago',f'Conexión correcta. Se pudo consultar Mercado Pago.\nPagos encontrados en la consulta de prueba: {len(pagos)}')
            except Exception as e: QMessageBox.critical(d,'Mercado Pago','La conexión no pudo validarse.\n\n'+str(e))
        probar.clicked.connect(test_conn)
        def keyboard_submit_mp():
            guardar_actual()
            return True
        d.keyboard_submit = keyboard_submit_mp
        d.exec(); self._actualizar_estado_mp()

    def _build_backup_tab(self):
        tab=QWidget(); lay=QVBoxLayout(tab); lay.setContentsMargins(8,18,8,8)
        box=QGroupBox('💾 Copias de seguridad'); bl=QVBoxLayout(box); text=QLabel('Protegé productos, ventas, clientes, pedidos, caja y configuración. El programa puede guardar una copia local y otra en un pendrive conectado.'); text.setWordWrap(True); text.setProperty('class','muted'); bl.addWidget(text); buttons=QHBoxLayout(); backup=QPushButton('💾 Hacer copia de seguridad'); backup.clicked.connect(self.backup); restore=QPushButton('📥 Recibir copia de seguridad'); restore.setProperty('class','secondary'); restore.clicked.connect(self.restore); buttons.addWidget(backup); buttons.addWidget(restore); buttons.addStretch(); bl.addLayout(buttons); lay.addWidget(box)
        box2=QGroupBox('🔁 Automatización'); f=QFormLayout(box2); self.auto_backup=QCheckBox('Recordar realizar copia de seguridad al cerrar'); self.auto_backup.setChecked(get_setting('recordar_backup_cierre','0')=='1'); f.addRow(self.auto_backup); self.backup_keep=QSpinBox(); self.backup_keep.setRange(1,100); self.backup_keep.setValue(int(get_setting('backups_a_conservar','30') or 30)); f.addRow('Copias locales a conservar:',self.backup_keep); lay.addWidget(box2); lay.addStretch(); self.tabs.addTab(tab,'💾 Seguridad')

    def _build_system_tab(self):
        tab=QWidget(); lay=QVBoxLayout(tab); lay.setContentsMargins(8,18,8,8)
        box=QGroupBox('🎛️ Preferencias del sistema'); form=QFormLayout(box); self.moneda=self._field('moneda','$'); self.formato_fecha=QComboBox(); self.formato_fecha.addItems(['DD/MM/AAAA','AAAA-MM-DD']); self.formato_fecha.setCurrentText(get_setting('formato_fecha','DD/MM/AAAA')); self.confirmar_venta=QCheckBox('Pedir confirmación antes de finalizar una venta'); self.confirmar_venta.setChecked(get_setting('confirmar_venta','0')=='1'); self.abrir_max=QCheckBox('Abrir el programa maximizado'); self.abrir_max.setChecked(get_setting('abrir_maximizado','1')=='1'); self.alertas_stock=QCheckBox('Mostrar alertas de stock en Productos'); self.alertas_stock.setChecked(get_setting('alertas_stock','1')=='1'); self.modo_venta=QComboBox(); self.modo_venta.addItems(['Venta rápida (recomendado)','Confirmación antes de cobrar']); self.modo_venta.setCurrentText(get_setting('modo_venta','Venta rápida (recomendado)')); form.addRow('Símbolo de moneda:',self.moneda); form.addRow('Formato de fecha:',self.formato_fecha); form.addRow('Modo de venta:',self.modo_venta); form.addRow(self.confirmar_venta); form.addRow(self.abrir_max); form.addRow(self.alertas_stock); lay.addWidget(box)
        info=QGroupBox('🛠️ Mantenimiento'); il=QVBoxLayout(info); label=QLabel('El programa mantiene una base de datos local portable. Antes de restaurar un backup se genera automáticamente un respaldo.'); label.setWordWrap(True); label.setProperty('class','muted'); il.addWidget(label); row=QHBoxLayout(); chk=QPushButton('🔍 Comprobar base de datos'); chk.setProperty('class','secondary'); chk.clicked.connect(self._check_db); row.addWidget(chk); row.addStretch(); il.addLayout(row); lay.addWidget(info); lay.addStretch(); self.tabs.addTab(tab,'⚙️ Sistema')

    def _check_db(self):
        from ui.db import BASE_DATOS, init_db
        import sqlite3
        try:
            init_db(); c=sqlite3.connect(BASE_DATOS); r=c.execute('PRAGMA integrity_check').fetchone()[0]; c.close(); QMessageBox.information(self,'Base de datos','✅ Base de datos correcta.' if r=='ok' else '⚠️ La base de datos requiere revisión.')
        except Exception as e: QMessageBox.critical(self,'Base de datos',str(e))

    def seleccionar_logo(self):
        p,_=QFileDialog.getOpenFileName(self,'Seleccionar logo','','Imágenes (*.png *.jpg *.jpeg *.webp)');
        if p:self.logo.setText(p)

    def guardar(self):
        values={'nombre_negocio':self.nombre.text().strip() or 'COTILLON','direccion':self.direccion.text().strip(),'telefono':self.telefono.text().strip(),'email':self.email.text().strip(),'cuit':self.cuit.text().strip(),'logo_path':self.logo.text().strip(),'pie_ticket':self.pie.text().strip(),'pie_documento':self.observaciones.text().strip(),'ancho_ticket':self.ancho_ticket.currentText(),'formato_papel':self.formato_papel.currentText(),'copias_ticket':str(self.copias_ticket.value()),'impresora_ticket':self.impresora_ticket.currentData() or '','impresora_a4':self.impresora_a4.currentData() or '','impresora_carteles':self.impresora_carteles.currentData() or '','recordar_impresoras':'1','recordar_backup_cierre':'1' if self.auto_backup.isChecked() else '0','backups_a_conservar':str(self.backup_keep.value()),'moneda':self.moneda.text().strip() or '$','formato_fecha':self.formato_fecha.currentText(),'confirmar_venta':'1' if self.confirmar_venta.isChecked() else '0','abrir_maximizado':'1' if self.abrir_max.isChecked() else '0','alertas_stock':'1' if self.alertas_stock.isChecked() else '0','modo_venta':self.modo_venta.currentText()}
        for k,v in values.items():set_setting(k,v)
        QMessageBox.information(self,'Configuración','✅ Los cambios fueron guardados correctamente.')

    def backup(self):
        try:
            import string,ctypes; dest=None
            if os.name=='nt':
                mask=ctypes.windll.kernel32.GetLogicalDrives()
                for i in range(26):
                    if mask&(1<<i):
                        d=f'{string.ascii_uppercase[i]}:\\'
                        if ctypes.windll.kernel32.GetDriveTypeW(d)==2:dest=d;break
            out=create_backup(dest); QMessageBox.information(self,'Copia realizada','✅ Copia creada correctamente.\n\n'+'\n'.join(out))
        except Exception as e:QMessageBox.critical(self,'Error',f'No se pudo crear la copia.\n\n{e}')

    def restore(self):
        files=find_removable_backups()
        if not files:
            p,_=QFileDialog.getOpenFileName(self,'Seleccionar copia','','Copia PAPELERA (*.pap)'); files=[p] if p else []
        if not files:return
        p,ok=QInputDialog.getItem(self,'Recibir copia','Seleccione la copia:',files,0,False)
        if ok:
            if QMessageBox.question(self,'Confirmar restauración','Se hará un backup de la información actual antes de restaurar. ¿Continuar?',QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
            try:restore_backup(p); QMessageBox.information(self,'Restauración','✅ Copia restaurada. Reinicie el programa para aplicar todos los datos.')
            except Exception as e:QMessageBox.critical(self,'Error',str(e))
