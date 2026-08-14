import sys
import sqlite3
import datetime
from ui.db import registrar_producto_sync

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QStyledItemDelegate,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect
)


from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor


from ui.db import (
    create_connection,
    get_setting,
    registrar_producto_sync
)



SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"







class DialogoAviso(QDialog):


    def __init__(
        self,
        titulo,
        mensaje,
        parent=None
    ):

        super().__init__(parent)



        self.setWindowTitle(
            titulo
        )



        self.setFixedSize(
            430,
            200
        )



        self.setStyleSheet("""

        QDialog{

            background:#ffffff;

        }



        QLabel{

            color:#0f172a;
            font-size:15px;

        }



        QPushButton{

            background:#2563eb;
            color:white;
            border-radius:10px;
            padding:10px 30px;
            font-weight:bold;

        }



        QPushButton:hover{

            background:#1d4ed8;

        }


        """)



        layout = QVBoxLayout(
            self
        )



        layout.setContentsMargins(
            30,
            30,
            30,
            30
        )



        texto = QLabel(
            mensaje
        )



        texto.setWordWrap(
            True
        )



        layout.addWidget(
            texto
        )



        boton = QPushButton(
            "Aceptar"
        )



        boton.clicked.connect(
            self.accept
        )



        layout.addWidget(
            boton
        )










class DialogoConfirmacion(QDialog):


    def __init__(
        self,
        mensaje,
        parent=None
    ):

        super().__init__(parent)



        self.setWindowTitle(
            "Confirmar eliminación"
        )



        self.setFixedSize(
            450,
            230
        )



        self.setStyleSheet("""

        QDialog{

            background:white;
            border-radius:18px;

        }



        QLabel#titulo{

            color:#0f172a;
            font-size:22px;
            font-weight:800;

        }



        QLabel#mensaje{

            color:#475569;
            font-size:15px;

        }



        QPushButton{

            border-radius:10px;
            padding:12px 25px;
            font-size:14px;
            font-weight:bold;

        }



        QPushButton#cancelar{

            background:#e2e8f0;
            color:#334155;

        }



        QPushButton#cancelar:hover{

            background:#cbd5e1;

        }



        QPushButton#eliminar{

            background:#ef4444;
            color:white;

        }



        QPushButton#eliminar:hover{

            background:#dc2626;

        }


        """)






        layout = QVBoxLayout(
            self
        )



        layout.setContentsMargins(
            35,
            30,
            35,
            30
        )



        layout.setSpacing(
            15
        )






        titulo = QLabel(
            "⚠️ Eliminar producto"
        )


        titulo.setObjectName(
            "titulo"
        )



        layout.addWidget(
            titulo
        )






        texto = QLabel(
            mensaje
        )


        texto.setObjectName(
            "mensaje"
        )


        texto.setWordWrap(
            True
        )



        layout.addWidget(
            texto
        )





        botones = QHBoxLayout()



        botones.addStretch()





        cancelar = QPushButton(
            "Cancelar"
        )


        cancelar.setObjectName(
            "cancelar"
        )





        eliminar = QPushButton(
            "🗑 Eliminar"
        )


        eliminar.setObjectName(
            "eliminar"
        )





        cancelar.clicked.connect(
            self.reject
        )



        eliminar.clicked.connect(
            self.accept
        )





        botones.addWidget(
            cancelar
        )



        botones.addWidget(
            eliminar
        )



        layout.addLayout(
            botones
        )










class EditorCeldaDelegate(QStyledItemDelegate):


    def createEditor(
        self,
        parent,
        option,
        index
    ):


        editor = QLineEdit(
            parent
        )



        editor.setStyleSheet("""

        QLineEdit{

            background:white;
            color:#0f172a;
            border:2px solid #2563eb;
            border-radius:8px;
            padding:8px;

        }


        """)



        return editor





    def updateEditorGeometry(
        self,
        editor,
        option,
        index
    ):


        editor.setGeometry(
            option.rect
        )








class Productos(QWidget):


    def __init__(self):


        super().__init__()



        self.setWindowTitle(
            f"{get_setting('nombre_negocio','COTILLON')} - Productos"
        )



        self.resize(
            1200,
            780
        )



        self.cargando_datos = False
        self.setStyleSheet("""

        QWidget{

            background:#f1f5f9;
            font-family:'Segoe UI';

        }



        QLabel{

            color:#0f172a;

        }



        QLineEdit{

            background:white;
            color:#0f172a;
            border:1px solid #cbd5e1;
            border-radius:14px;
            padding:12px 16px;
            font-size:15px;

        }



        QLineEdit:focus{

            border:2px solid #2563eb;

        }



        QPushButton{

            border-radius:12px;
            padding:12px 22px;
            font-size:14px;
            font-weight:bold;
            background:#e2e8f0;
            color:#0f172a;

        }



        QPushButton:hover{

            opacity:0.85;

        }



        QPushButton#nuevo{

            background:#2563eb;
            color:white;

        }



        QPushButton#actualizar{

            background:#059669;
            color:white;

        }



        QPushButton#editar{

            background:#7c3aed;
            color:white;

        }



        QPushButton#sync{

            background:#7c3aed;
            color:white;

        }


        """)





        principal = QVBoxLayout(
            self
        )



        principal.setContentsMargins(
            30,
            30,
            30,
            30
        )



        principal.setSpacing(
            20
        )






        # =================================
        # ENCABEZADO
        # =================================


        encabezado = QHBoxLayout()



        informacion = QVBoxLayout()



        titulo = QLabel(
            "📦 Gestión de Productos"
        )



        titulo.setStyleSheet("""

        font-size:32px;
        font-weight:900;

        """)



        subtitulo = QLabel(
            "Administración de stock, precios e inventario"
        )



        subtitulo.setStyleSheet("""

        color:#64748b;
        font-size:15px;

        """)



        informacion.addWidget(
            titulo
        )



        informacion.addWidget(
            subtitulo
        )



        encabezado.addLayout(
            informacion
        )



        encabezado.addStretch()





        self.buscar = QLineEdit()



        self.buscar.setPlaceholderText(
            "🔍 Buscar por nombre o código..."
        )



        self.buscar.setFixedWidth(
            380
        )



        self.buscar.textChanged.connect(
            self.buscar_productos
        )



        encabezado.addWidget(
            self.buscar
        )



        principal.addLayout(
            encabezado
        )







        # =================================
        # TARJETAS DE INFORMACION
        # =================================


        tarjetas = QHBoxLayout()



        tarjetas.setSpacing(
            18
        )



        self.card_productos = QLabel(
            "📦 Productos\n0"
        )


        self.card_stock = QLabel(
            "⚠️ Bajo Stock\n0"
        )


        self.card_valor = QLabel(
            "💰 Inventario\n$0"
        )





        for tarjeta in [

            self.card_productos,
            self.card_stock,
            self.card_valor

        ]:


            tarjeta.setMinimumHeight(
                95
            )



            tarjeta.setStyleSheet("""

            QLabel{

                background:white;
                border-radius:18px;
                padding:20px;
                font-size:18px;
                font-weight:bold;
                border:1px solid #e2e8f0;

            }


            """)



            sombra = QGraphicsDropShadowEffect()



            sombra.setBlurRadius(
                20
            )



            sombra.setYOffset(
                5
            )



            sombra.setColor(
                QColor(
                    0,
                    0,
                    0,
                    30
                )
            )



            tarjeta.setGraphicsEffect(
                sombra
            )



            tarjetas.addWidget(
                tarjeta
            )



        principal.addLayout(
            tarjetas
        )
        # =================================
        # BARRA DE BOTONES
        # =================================


        barra_botones = QHBoxLayout()


        barra_botones.setSpacing(
            15
        )



        btn_agregar = QPushButton(
            "➕ Nuevo producto"
        )


        btn_agregar.setObjectName(
            "nuevo"
        )


        btn_agregar.clicked.connect(
            self.abrir_agregar
        )



        btn_actualizar = QPushButton(
            "🔄 Actualizar"
        )


        btn_actualizar.setObjectName(
            "actualizar"
        )


        btn_actualizar.clicked.connect(
            self.cargar_productos
        )



        btn_editar = QPushButton(
            "✏️ Editar completo"
        )


        btn_editar.setObjectName(
            "✏ Editar"
        )


        btn_editar.clicked.connect(
            self.editar_producto
        )



        btn_sync = QPushButton(
            "☁ Sincronizar"
        )


        btn_sync.setObjectName(
            "sync"
        )


        btn_sync.clicked.connect(
            self.sincronizar_datos
        )



        barra_botones.addWidget(
            btn_agregar
        )


        barra_botones.addWidget(
            btn_actualizar
        )


        barra_botones.addWidget(
            btn_editar
        )


        barra_botones.addWidget(
            btn_sync
        )



        barra_botones.addStretch()



        principal.addLayout(
            barra_botones
        )







        # =================================
        # CONTENEDOR TABLA
        # =================================


        contenedor_tabla = QFrame()



        contenedor_tabla.setStyleSheet("""

        QFrame{

            background:white;
            border-radius:22px;
            border:1px solid #e2e8f0;

        }

        """)



        sombra_tabla = QGraphicsDropShadowEffect()



        sombra_tabla.setBlurRadius(
            35
        )



        sombra_tabla.setYOffset(
            8
        )



        sombra_tabla.setColor(
            QColor(
                0,
                0,
                0,
                35
            )
        )



        contenedor_tabla.setGraphicsEffect(
            sombra_tabla
        )



        layout_tabla = QVBoxLayout(
            contenedor_tabla
        )



        layout_tabla.setContentsMargins(
            20,
            20,
            20,
            20
        )







        # =================================
        # TABLA
        # =================================


        self.tabla = QTableWidget()



        self.tabla.setColumnCount(
            7
        )



        self.tabla.setHorizontalHeaderLabels(
            [
                "Código",
                "Producto",
                "Categoría",
                "Compra",
                "Venta",
                "Stock",
                "Acciones"
            ]
        )



        self.tabla.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )



        self.tabla.setSelectionMode(
            QAbstractItemView.SingleSelection
        )



        self.tabla.setAlternatingRowColors(
            False
        )



        self.tabla.verticalHeader().setDefaultSectionSize(
            65
        )



        self.tabla.setItemDelegate(
            EditorCeldaDelegate(
                self.tabla
            )
        )



        self.tabla.itemChanged.connect(
            self.guardar_precio_editado
        )



        self.tabla.setShowGrid(
            False
        )
        self.tabla.setStyleSheet("""

        QTableWidget{

            background:white;
            border:none;
            outline:none;

        }



        QTableWidget::item{

             outline:none;

        }



        QTableWidget::item:hover{

            background:#eff6ff;

        }



        QTableWidget::item:selected{

            background:#dbeafe;
            color:#1e3a8a;
            font-weight:bold;

        }



        QHeaderView::section{

            background:#0f172a;
            color:white;
            padding:15px;
            border:none;
            font-size:14px;
            font-weight:bold;

        }



        QScrollBar:vertical{

            background:#f1f5f9;
            width:14px;
            margin:0px;

        }



        QScrollBar::handle:vertical{

            background:#94a3b8;
            border-radius:7px;
            min-height:50px;

        }



        QScrollBar::handle:vertical:hover{

            background:#2563eb;

        }



        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical{

            height:0px;

        }



        QScrollBar:horizontal{

            background:#f1f5f9;
            height:14px;

        }



        QScrollBar::handle:horizontal{

            background:#94a3b8;
            border-radius:7px;

        }



        QScrollBar::handle:horizontal:hover{

            background:#2563eb;

        }



        """)





        header = self.tabla.horizontalHeader()



        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )


        header.setSectionResizeMode(
            1,
            QHeaderView.Stretch
        )


        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents
        )


        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents
        )


        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeToContents
        )


        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeToContents
        )


        header.setSectionResizeMode(
            6,
            QHeaderView.Fixed
        )



        self.tabla.setColumnWidth(
            6,
            180
        )



        layout_tabla.addWidget(
            self.tabla
        )



        principal.addWidget(
            contenedor_tabla
        )





        # =================================
        # CARGA INICIAL
        # =================================


        self.cargar_productos()
    def showEvent(self, event):
        super().showEvent(event)

        # Cada vez que volvemos al módulo Productos,
        # recargamos el stock directamente desde SQLite.
        QTimer.singleShot(
            0,
            self.cargar_productos
        )
        
    # =================================
    # CARGAR PRODUCTOS
    # =================================


    def cargar_productos(self):


        self.cargando_datos = True


        try:


            conexion = create_connection()


            conexion.row_factory = sqlite3.Row


            cursor = conexion.cursor()



            productos = cursor.execute("""

                SELECT *
                FROM productos
                ORDER BY id DESC

            """).fetchall()



            conexion.close()





            # ACTUALIZAR TARJETAS


            total = len(productos)


            stock_bajo = 0


            valor_total = 0



            for producto in productos:


                stock = producto["stock"] or 0



                if stock <= 5:

                    stock_bajo += 1



                valor_total += (

                    float(producto["precio_compra"] or 0)
                    *
                    stock

                )




            self.card_productos.setText(

                f"📦 Productos\n{total}"

            )


            self.card_stock.setText(

                f"⚠️ Bajo Stock\n{stock_bajo}"

            )


            self.card_valor.setText(

                f"💰 Inventario\n${valor_total:,.0f}"

            )






            self.tabla.blockSignals(
                True
            )



            self.tabla.clearContents()



            self.tabla.setRowCount(
                len(productos)
            )







            for fila, producto in enumerate(productos):


                prod_id = producto["id"]


                prod_uuid = producto["uuid"]




                datos = [

                    producto["codigo_barras"] or "-",

                    producto["nombre"] or "",

                    producto["categoria"] or "General",

                    f"${float(producto['precio_compra'] or 0):,.2f}",

                    f"${float(producto['precio_venta'] or 0):,.2f}",

                    str(producto["stock"] or 0)

                ]







                for columna, valor in enumerate(datos):


                    item = QTableWidgetItem(
                        str(valor)
                    )



                    item.setData(
                        Qt.UserRole,
                        prod_id
                    )



                    item.setData(
                        Qt.UserRole + 1,
                        prod_uuid
                    )




                    if columna in [3,4,5]:


                        item.setFlags(

                            Qt.ItemIsEnabled |
                            Qt.ItemIsSelectable |
                            Qt.ItemIsEditable

                        )


                    else:


                        item.setFlags(

                            Qt.ItemIsEnabled |
                            Qt.ItemIsSelectable

                        )






                    # COLOR STOCK


                    if columna == 5:


                        stock = producto["stock"] or 0



                        if stock <= 0:


                            item.setForeground(
                                QColor("#dc2626")
                            )



                        elif stock <= 5:


                            item.setForeground(
                                QColor("#ea580c")
                            )



                        elif stock <= 10:


                            item.setForeground(
                                QColor("#ca8a04")
                            )



                        else:


                            item.setForeground(
                                QColor("#16a34a")
                            )



                    else:


                        item.setForeground(
                            QColor("#0f172a")
                        )





                    self.tabla.setItem(

                        fila,
                        columna,
                        item

                    )   
                # =================================
                # BOTONES ACCION
                # =================================


                contenedor_acciones = QWidget()


                acciones = QHBoxLayout(
                    contenedor_acciones
                )


                acciones.setContentsMargins(
                    5,
                    5,
                    5,
                    5
                )


                acciones.setSpacing(
                    8
                )



                btn_editar = QPushButton(
                    "✏️"
                )


                btn_editar.setFixedSize(
                    85,
                    38
                )


                btn_editar.setToolTip(
                    "Editar producto"
                )



                btn_editar.setStyleSheet("""

                QPushButton{

                    background:#f59e0b;
                    color:white;
                    border-radius:8px;
                    font-size:16px;

                }


                QPushButton:hover{

                    background:#d97706;

                }

                """)



                btn_editar.clicked.connect(
                    lambda checked=False,
                    f=fila:
                    self.editar_desde_fila(f)
                )





                btn_eliminar = QPushButton(
                    "🗑 Eliminar"
                )


                btn_eliminar.setFixedSize(
                    85,
                    38
                )


                btn_eliminar.setToolTip(
                    "Eliminar producto"
                )



                btn_eliminar.setStyleSheet("""

                QPushButton{

                    background:#ef4444;
                    color:white;
                    border-radius:8px;
                    font-size:16px;

                }


                QPushButton:hover{

                    background:#b91c1c;

                }

                """)



                btn_eliminar.clicked.connect(

                    lambda checked=False,
                    pid=prod_id,
                    nom=producto["nombre"]:
                    self.eliminar_por_id(
                        pid,
                        nom
                    )

                )



                acciones.addWidget(
                    btn_editar
                )


                acciones.addWidget(
                    btn_eliminar
                )



                self.tabla.setCellWidget(
                    fila,
                    6,
                    contenedor_acciones
                )



            self.tabla.blockSignals(
                False
            )



        except Exception as e:


            DialogoAviso(
                "Error cargando productos",
                str(e),
                self
            ).exec()



        self.cargando_datos = False








    # =================================
    # EDITAR DESDE BOTON
    # =================================


    def editar_desde_fila(
        self,
        fila
    ):


        self.tabla.selectRow(
            fila
        )


        self.editar_producto()







    # =================================
    # BUSCAR
    # =================================


    def buscar_productos(self):


        texto = self.buscar.text().lower().strip()



        for fila in range(
            self.tabla.rowCount()
        ):


            nombre = self.tabla.item(
                fila,
                1
            )


            codigo = self.tabla.item(
                fila,
                0
            )



            mostrar = False



            if texto == "":

                mostrar = True



            elif nombre and texto in nombre.text().lower():

                mostrar = True



            elif codigo and texto in codigo.text().lower():

                mostrar = True



            self.tabla.setRowHidden(
                fila,
                not mostrar
            )







    # =================================
    # ABRIR AGREGAR
    # =================================


    def abrir_agregar(self):    


        try:


            from ui.agregar_producto import AgregarProducto



            self.ventana_agregar = AgregarProducto()



            self.ventana_agregar.producto_guardado.connect(
                self.cargar_productos
            )



            self.ventana_agregar.show()



        except Exception as e:


            DialogoAviso(
                "Error",
                str(e),
                self
            ).exec()







    # =================================
    # EDITAR COMPLETO
    # =================================


    def editar_producto(self):


        fila = self.tabla.currentRow()



        if fila < 0:


            DialogoAviso(
                "Aviso",
                "Seleccione un producto primero.",
                self
            ).exec()


            return




        item = self.tabla.item(
            fila,
            0
        )



        if not item:

            return



        prod_id = item.data(
            Qt.UserRole
        )


        prod_uuid = item.data(
            Qt.UserRole + 1
        )



        from ui.editar_producto import EditarProducto



        self.ventana_editar = EditarProducto(
            prod_id,
            prod_uuid
        )



        self.ventana_editar.producto_actualizado.connect(
            self.cargar_productos
        )



        self.ventana_editar.show()





    # =================================
    # SINCRONIZAR
    # =================================


    def sincronizar_datos(self):


        try:


            from core.sync import sincronizar



            sincronizar()



            self.cargar_productos()



        except Exception as e:


            DialogoAviso(
                "Error sincronizando",
                str(e),
                self
            ).exec()






    # =================================
    # GUARDAR EDICION RAPIDA
    # =================================


    def guardar_precio_editado(
        self,
        item
    ):


        if self.cargando_datos:

            return



        if item.column() not in [3,4,5]:

            return



        prod_id = item.data(
            Qt.UserRole
        )



        if not prod_id:

            return



        try:


            valor = item.text().replace(
                "$",
                ""
            ).replace(
                ",",
                ""
            )



            conexion = create_connection()


            cursor = conexion.cursor()



            campos = {

                3:"precio_compra",

                4:"precio_venta",

                5:"stock"

            }



            campo = campos[item.column()]



            cursor.execute(
                f"""
                UPDATE productos
                SET {campo}=?
                WHERE id=?
                """,
                (
                    float(valor),
                    prod_id
                )
            )



            conexion.commit()


            conexion.close()
            conexion = create_connection()

            producto = conexion.execute(
                """
                SELECT *
                FROM productos
                WHERE id=?
                """,
                (prod_id,)
            ).fetchone()

            conexion.close()


            if producto:

                registrar_producto_sync(
                    dict(producto),
                    "editar"
                )



        except Exception as e:


            DialogoAviso(
                "Error guardando",
                str(e),
                self
            ).exec()







    # =================================
    # ELIMINAR
    # =================================


    def eliminar_por_id(
        self,
        prod_id,
        nombre
    ):


        confirmar = DialogoConfirmacion(
            f"¿Eliminar producto?\n\n{nombre}",
            self
        )


        if confirmar.exec() != QDialog.Accepted:

            return



        conexion = create_connection()
        cursor = conexion.cursor()


        try:


            # =========================
            # OBTENER PRODUCTO
            # ANTES DE BORRAR
            # =========================

            producto = cursor.execute(
                """
                SELECT
                    uuid,
                    nombre,
                    codigo_barras,
                    categoria,
                    precio_compra,
                    precio_venta,
                    stock
                FROM productos
                WHERE id=?
                """,
                (
                    prod_id,
                )
            ).fetchone()



            if producto:


                from ui.db import registrar_sincronizacion


                # =========================
                # REGISTRAR ELIMINACION
                # PARA SINCRONIZAR
                # =========================

                registrar_sincronizacion(
                    "productos",
                    producto[0],
                    "eliminar",
                    {
                        "uuid": producto[0],
                        "nombre": producto[1],
                        "codigo_barras": producto[2],
                        "categoria": producto[3],
                        "precio_compra": producto[4],
                        "precio_venta": producto[5],
                        "stock": producto[6]
                    }
                )



            # =========================
            # BORRAR PRODUCTO LOCAL
            # =========================

            cursor.execute(
                """
                DELETE FROM productos
                WHERE id=?
                """,
                (
                    prod_id,
                )
            )


            conexion.commit()



        except Exception as e:


            DialogoAviso(
                "Error eliminando producto",
                str(e),
                self
            ).exec()



        finally:


            conexion.close()



        self.cargar_productos()




    # =================================
    # DOBLE CLICK
    # =================================


    def mouseDoubleClickEvent(
        self,
        event
    ):


        posicion = self.tabla.indexAt(
            event.position().toPoint()
        )



        if posicion.isValid():

            self.editar_producto()



        super().mouseDoubleClickEvent(
            event
        )







if __name__ == "__main__":


    from PySide6.QtWidgets import QApplication



    app = QApplication(
        sys.argv
    )


    ventana = Productos()


    ventana.show()


    sys.exit(
        app.exec()
    )