import sqlite3
import datetime
import requests
from core.version import obtener_version_actual
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

from ui.db import BASE_DATOS, init_db, archivar_ventas, get_setting, registrar_sincronizacion, nuevo_uuid
from ui.productos import Productos
from ui.ventas import Ventas
from ui.clientes import Clientes
from ui.historial import Historial
from ui.reportes import Reportes
from ui.pedidos import Pedidos
from ui.documentos import Documentos
from ui.carteles import Carteles
from ui.caja import Caja
from ui.configuracion import Configuracion


class Dashboard(QMainWindow):

    def __init__(self):
        super().__init__()
        init_db()

        self.nombre_negocio = get_setting('nombre_negocio', 'COTILLON') or 'COTILLON'
        self.setWindowTitle(f'{self.nombre_negocio} POS')
        self.setMinimumSize(760, 560)

        self.setStyleSheet(
            'QMainWindow{background:#f8fafc} '
            'QFrame#side{background:#0f172a;border-radius:18px} '
            'QPushButton{border:0;border-radius:10px;padding:12px;color:white;font-weight:600} '
            'QPushButton.nav{background:transparent;text-align:left} '
            'QPushButton.nav:hover{background:#1e293b} '
            'QLabel{color:#0f172a}'
        )

        # --- Widget central y layout raíz ---
        c = QWidget()
        c.setObjectName('mainCentral')
        c.setStyleSheet('QWidget#mainCentral{background:#ffffff;}')
        self.setCentralWidget(c)

        root = QHBoxLayout(c)
        root.setContentsMargins(18, 18, 18, 18)

        # --- Barra lateral (side) ---
        side = QFrame()
        side.setObjectName('side')
        side.setMinimumWidth(165)
        side.setMaximumWidth(210)
        side.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        sl = QVBoxLayout(side)

        self.brand = QLabel(self.nombre_negocio)
        self.brand.setStyleSheet('color:white;font-size:27px;font-weight:900')
        self.brand.setAlignment(Qt.AlignCenter)
        sl.addWidget(self.brand)
        version = QLabel(
            f"Versión {obtener_version_actual()}"
        )

        version.setStyleSheet(
            '''
            color:#94a3b8;
            font-size:12px;
            font-weight:600;
            '''
        )

        version.setAlignment(
            Qt.AlignCenter
        )

        sl.addWidget(version)        

        self.nav_buttons = []

        botones_nav = [
            ('🏠 Inicio', self.ir_inicio),
            ('🛒 Ventas', self.abrir_ventas),
            ('📦 Productos', self.abrir_productos),
            ('📋 Pedidos', self.abrir_pedidos),
            ('🧾 Documentos', self.abrir_documentos),
            ('🏷️ Carteles / Ofertas', self.abrir_carteles),
            ('👥 Clientes', self.abrir_clientes),
            ('🕘 Historial', self.abrir_historial),
            ('💰 Caja / Arqueo', self.abrir_caja),
            ('📊 Reportes', self.abrir_reportes),
            ('⚙️ Configuración', self.abrir_config),
        ]

        for txt, fn in botones_nav:
            b = QPushButton(txt)
            b.setProperty('class', 'nav')
            b.setMinimumHeight(42)
            b.setStyleSheet('font-size:15px;text-align:left;padding:8px 10px;')
            b.clicked.connect(fn)
            sl.addWidget(b)
            self.nav_buttons.append(b)

        sl.addStretch()

        q = QPushButton('🚪 Cerrar')
        q.clicked.connect(self.close)
        sl.addWidget(q)

        root.addWidget(side)

        # --- Área central con scroll y stack de módulos ---
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stack.setStyleSheet('QStackedWidget{background:#ffffff;}')

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(
            'QScrollArea{background:#ffffff;border:0;} '
            'QScrollArea>QWidget>QWidget{background:#ffffff;}'
        )
        self.scroll.viewport().setStyleSheet('background:#ffffff;')
        self.scroll.setWidget(self.stack)

        root.addWidget(self.scroll, 1)

        # --- Pantalla de inicio (home) ---
        self.home = QWidget()
        self.home.setObjectName('home')
        self.home.setStyleSheet('QWidget#home{background:#ffffff;}')
        self.stack.addWidget(self.home)
        self.build_home()
        self.stack.setCurrentWidget(self.home)

        # AJUSTE AUTOMATICO DE RESOLUCION
        screen = QApplication.primaryScreen().availableGeometry()

        ancho = screen.width()
        alto = screen.height()

        if ancho < 1500 or alto < 850:
            self.resize(
                ancho,
                alto
            )

            self.move(
                (ancho - self.width()) // 2,
                (alto - self.height()) // 2
            )

        else:
            self.showMaximized()

        self.actualizar()

    def actualizar_nombre_negocio(self):
        self.nombre_negocio = get_setting(
            'nombre_negocio',
            'COTILLON'
        ) or 'COTILLON'

        self.setWindowTitle(
            f'{self.nombre_negocio} POS'
        )

        self.brand.setText(
            self.nombre_negocio
        )

        self.titulo_home.setText(
            f'Bienvenido a {self.nombre_negocio} 👋'
        )

    def build_home(self):
        panel = QVBoxLayout(self.home)
        panel.setContentsMargins(25, 25, 25, 25)

        self.titulo_home = QLabel(
            f'Bienvenido a {self.nombre_negocio} 👋'
        )

        self.titulo_home.setStyleSheet(
            'font-size:32px;font-weight:900'
        )

        panel.addWidget(self.titulo_home)

        sub = QLabel('Punto de venta y gestión del negocio')
        sub.setStyleSheet('font-size:16px;color:#64748b')
        panel.addWidget(sub)

        cards = QHBoxLayout()
        self.v = QLabel()
        self.p = QLabel()
        self.e = QLabel()

        tarjetas = [
            ('💰 Ventas de hoy', self.v),
            ('📦 Productos', self.p),
            ('💵 Efectivo esperado', self.e),
        ]

        for title, w in tarjetas:
            f = QFrame()
            f.setStyleSheet('background:white;border:1px solid #e2e8f0;border-radius:15px;padding:10px')

            x = QVBoxLayout(f)

            a = QLabel(title)
            a.setStyleSheet('color:#64748b;font-weight:bold')

            w.setStyleSheet('font-size:25px;font-weight:900')

            x.addWidget(a)
            x.addWidget(w)

            cards.addWidget(f)

        panel.addLayout(cards)

        b = QHBoxLayout()

        new = QPushButton('🛒 Nueva venta')
        new.setStyleSheet('background:#0ea5e9;color:white;padding:14px;font-weight:800')
        new.clicked.connect(self.abrir_ventas)

        clear = QPushButton('🧹 Reiniciar ventas de hoy')
        clear.setStyleSheet('background:#e2e8f0;color:#334155;padding:14px;font-weight:800')
        clear.clicked.connect(self.reiniciar_hoy)

        b.addWidget(new)
        b.addWidget(clear)
        b.addStretch()

        panel.addLayout(b)
        panel.addStretch()

    def verificar_sincronizacion_remota(self):
        """Consulta al backend si alguna otra terminal realizó un cierre/arqueo de ventas."""
        try:
            api_url = get_setting('api_url', 'https://papelera-pos-backend-production.up.railway.app')
            response = requests.get(f"{api_url}/sincronizacion/pendientes", timeout=2)
            
            if response.status_code == 200:
                eventos = response.json()
                hoy = datetime.datetime.now().strftime('%Y-%m-%d')
                hubo_cambios = False

                for ev in eventos:
                    # Si el evento indica archivar el día, lo aplicamos localmente
                    if ev.get("accion") == "archivar_hoy":
                        archivar_ventas(fecha=hoy)
                        hubo_cambios = True

                return hubo_cambios
        except Exception:
            # Si no hay red o el servidor no responde, no rompe la app local
            pass
        return False

    def actualizar(self):
        # Verificar si hay eventos pendientes en la red antes de calcular
        self.verificar_sincronizacion_remota()

        hoy = datetime.datetime.now().strftime('%Y-%m-%d')

        c = sqlite3.connect(BASE_DATOS)
        q = c.cursor()

        ventas = q.execute(
            "SELECT COALESCE(SUM(total),0) FROM ventas "
            "WHERE fecha LIKE ? AND COALESCE(estado,'ACTIVA')='ACTIVA'",
            (hoy + '%',)
        ).fetchone()[0]

        prod = q.execute('SELECT COUNT(*) FROM productos').fetchone()[0]

        ef = q.execute(
            "SELECT COALESCE(SUM(CASE WHEN COALESCE(pago_efectivo,0)>0 THEN pago_efectivo "
            "ELSE CASE WHEN LOWER(TRIM(COALESCE(forma_pago,'')))='efectivo' THEN total ELSE 0 END END),0) "
            "FROM ventas WHERE fecha LIKE ? AND COALESCE(estado,'ACTIVA')='ACTIVA'",
            (hoy + '%',)
        ).fetchone()[0]

        c.close()

        self.v.setText(f'${ventas:,.2f}')
        self.p.setText(str(prod))
        self.e.setText(f'${ef:,.2f}')

    def reiniciar_hoy(self):
        hoy = datetime.datetime.now().strftime('%Y-%m-%d')

        c = sqlite3.connect(BASE_DATOS)
        n = c.execute(
            "SELECT COUNT(*) FROM ventas "
            "WHERE fecha LIKE ? AND COALESCE(estado,'ACTIVA')='ACTIVA'",
            (hoy + '%',)
        ).fetchone()[0]
        c.close()

        if not n:
            QMessageBox.information(self, 'Ventas de hoy', 'No hay ventas activas para reiniciar.')
            return

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle('Reiniciar ventas de hoy')
        box.setText(f'Se archivarán {n} ventas de hoy y la pantalla quedará en cero.')
        box.setInformativeText('Las ventas seguirán disponibles en el historial. ¿Querés continuar?')
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setStyleSheet(
            'QMessageBox{background:white;} '
            'QLabel{color:#0f172a;font-size:14px;} '
            'QPushButton{background:#0ea5e9;color:white;border:0;border-radius:8px;padding:8px 18px;font-weight:700;}'
        )

        if box.exec() != QMessageBox.Yes:
            return

        archivar_ventas(fecha=hoy)
        
        # Registrar y notificar al backend la acción manual de reinicio
        try:
            datos_sync = {"fecha": hoy, "accion": "archivar_hoy"}
            registrar_sincronizacion("ventas", nuevo_uuid(), "archivar_hoy", datos_sync)
            api_url = get_setting('api_url', 'https://papelera-pos-backend-production.up.railway.app')
            requests.post(f"{api_url}/sincronizar", json={
                "tabla": "ventas",
                "registro_uuid": nuevo_uuid(),
                "accion": "archivar_hoy",
                "datos": datos_sync
            }, timeout=2)
        except Exception as e:
            print("Se archivó localmente, error al sincronizar reinicio:", e)

        self.actualizar()
        QMessageBox.information(self, 'Listo', 'Las ventas de hoy fueron archivadas. El inicio quedó en cero.')

    def ir_inicio(self):
        self.stack.setCurrentWidget(self.home)

    def openw(self, cls):
        if not hasattr(self, '_module_cache'):
            self._module_cache = {}

        w = self._module_cache.get(cls)

        if w is None:
            w = cls()
            w.setMinimumSize(0, 0)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.stack.addWidget(w)
            self._module_cache[cls] = w

            if cls is Ventas:
                w.venta_realizada.connect(self.actualizar)
            if cls is Caja:
                w.arqueo_realizado.connect(self.actualizar)

        self.stack.setCurrentWidget(w)

        if cls is Ventas:
            self.scroll.verticalScrollBar().setValue(0)
            self.scroll.horizontalScrollBar().setValue(0)
            self.stack.setMinimumSize(self.scroll.viewport().size())
            self.stack.resize(self.scroll.viewport().size())

            if hasattr(w, 'refresh_layout_on_return'):
                w.refresh_layout_on_return()

            self.scroll.viewport().update()
            self.stack.updateGeometry()

        if hasattr(w, 'actualizar_datos') and cls is not Ventas:
            w.actualizar_datos()

        return w

    def abrir_ventas(self):
        self.openw(Ventas)

    def abrir_productos(self):
        self.openw(Productos)

    def abrir_pedidos(self):
        self.openw(Pedidos)

    def abrir_documentos(self):
        self.openw(Documentos)

    def abrir_carteles(self):
        self.openw(Carteles)

    def abrir_clientes(self):
        self.openw(Clientes)

    def abrir_historial(self):
        self.openw(Historial)

    def abrir_caja(self):
        self.openw(Caja)

    def abrir_reportes(self):
        self.openw(Reportes)

    def abrir_config(self):
        self.openw(Configuracion)