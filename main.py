import sys

from core.version import obtener_version_actual
from core.actualizador import hay_actualizacion

from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog
from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication


from ui.keyboard import KeyboardAndNumberFilter
from ui.db import init_db
from ui.dashboard import Dashboard


from webhook_server import start_webhook_server
from sync import sincronizar



if __name__ == "__main__":


    app = QApplication(sys.argv)



    screen = QGuiApplication.primaryScreen().availableGeometry()


    factor = min(
        screen.width() / 1920,
        screen.height() / 1080
    )


    app.setStyleSheet(f"""
    QWidget {{
        font-size: {int(14 * factor)}px;
    }}
    """)



    app.setStyleSheet('''

    QMessageBox{
        background:#ffffff;
    }


    QMessageBox QLabel{
        color:#0f172a;
        font-size:14px;
    }


    QMessageBox QPushButton{
        background:#0ea5e9;
        color:white;
        border:0;
        border-radius:8px;
        padding:8px 18px;
        font-weight:700;
    }


    QDialog{
        background:#ffffff;
    }

    ''')



    # ==================================
    # CREAR BASE LOCAL SI NO EXISTE
    # ==================================

    init_db()



    # ==================================
    # SERVIDOR LOCAL DEL POS
    # ==================================

    start_webhook_server()



    # ==================================
    # SINCRONIZACION INICIAL
    # ==================================

    try:

        sincronizar()


        print(
            "Sincronización inicial OK"
        )


    except Exception as e:


        print(
            "Error sincronización inicial:",
            e
        )



    # ==================================
    # SINCRONIZACION AUTOMATICA
    # ==================================

    timer_sync = QTimer()


    timer_sync.timeout.connect(
        sincronizar
    )


    timer_sync.start(
        60000
    )



    # ==================================
    # TECLADO ESPECIAL POS
    # ==================================

    keyboard_filter = KeyboardAndNumberFilter(app)


    app.installEventFilter(
        keyboard_filter
    )



    # ==================================
    # VERSION Y ACTUALIZACION
    # ==================================

    version = obtener_version_actual()


    print(
        f"PAPELERA POS actualizado - VERSION {obtener_version_actual()}"
    )


    actualizar, nueva_version = hay_actualizacion(version)



    if actualizar:


        print(
            f"Hay una nueva versión disponible: {nueva_version}"
        )



        respuesta = QMessageBox.question(
            None,
            "Actualización disponible",
            f"Hay una nueva versión disponible: {nueva_version}\n\n¿Desea actualizar ahora?",
            QMessageBox.Yes | QMessageBox.No
        )



        if respuesta == QMessageBox.Yes:


            print(
                "Usuario aceptó actualización"
            )


            from core.actualizador import (
                descargar_actualizacion,
                instalar_actualizacion,
                reiniciar_programa
            )



            progreso = QProgressDialog(
                "Descargando actualización...",
                None,
                0,
                100
            )

            progreso.setWindowTitle(
                "Actualizando Papelera POS"
            )

            progreso.setAutoClose(
                False
            )

            progreso.setAutoReset(
                False
            )

            progreso.show()


            def actualizar_progreso(valor):

                progreso.setValue(
                    valor
                )


            archivo = descargar_actualizacion(
                actualizar_progreso
            )


            progreso.close()
            if archivo:

                if instalar_actualizacion(archivo):

                    reiniciar_programa()



            print(
                "Archivo descargado:",
                archivo
            )



        else:


            print(
                "Actualización pospuesta"
            )



   


    # ==================================
    # PANTALLA PRINCIPAL
    # ==================================

    w = Dashboard()


    w.showMaximized()



    sys.exit(
        app.exec()
    )