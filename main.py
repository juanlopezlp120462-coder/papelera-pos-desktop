import sys
import os

from core.version import obtener_version_actual
from core.actualizador import hay_actualizacion

from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QProgressDialog
)

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication

from ui.keyboard import KeyboardAndNumberFilter
from ui.db import init_db
from ui.dashboard import Dashboard

from webhook_server import start_webhook_server
from sync import sincronizar


if __name__ == "__main__":

    app = QApplication(sys.argv)

    # ==================================
    # ESCALA DE PANTALLA
    # ==================================

    screen = QGuiApplication.primaryScreen().availableGeometry()

    factor = min(
        screen.width() / 1920,
        screen.height() / 1080
    )

    app.setStyleSheet(f"""
    QWidget {{
        font-size: {int(14 * factor)}px;
    }}

    QMessageBox {{
        background: #ffffff;
    }}

    QMessageBox QLabel {{
        color: #0f172a;
        font-size: 14px;
    }}

    QMessageBox QPushButton {{
        background: #0ea5e9;
        color: white;
        border: 0;
        border-radius: 8px;
        padding: 8px 18px;
        font-weight: 700;
    }}

    QDialog {{
        background: #ffffff;
    }}
    """)

    # ==================================
    # VERSION
    # ==================================

    version = obtener_version_actual()

    print(
        f"PAPELERA POS - VERSION {version}"
    )

    # ==================================
    # COMPROBAR ACTUALIZACION
    #
    # IMPORTANTE:
    # Esto se hace ANTES de iniciar:
    # - base de datos
    # - webhook
    # - sincronización
    # - Dashboard
    #
    # Así la versión vieja no queda
    # funcionando mientras se actualiza.
    # ==================================

    actualizar = False
    nueva_version = None

    if getattr(sys, "frozen", False):

        try:

            actualizar, nueva_version = hay_actualizacion(
                version
            )

        except Exception as e:

            print(
                "Error comprobando actualización:",
                e
            )

            actualizar = False
            nueva_version = None

    # ==================================
    # DIAGNOSTICO
    # ==================================

    try:

        ruta_diagnostico = os.path.join(
            os.path.dirname(sys.executable)
            if getattr(sys, "frozen", False)
            else os.getcwd(),
            "diagnostico_actualizacion.txt"
        )

        with open(
            ruta_diagnostico,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                f"VERSION LOCAL: {version}\n"
            )

            f.write(
                f"ACTUALIZAR: {actualizar}\n"
            )

            f.write(
                f"NUEVA VERSION: {nueva_version}\n"
            )

    except Exception as e:

        print(
            "Error escribiendo diagnóstico:",
            e
        )

    # ==================================
    # ACTUALIZACION
    # ==================================

    if actualizar:

        print(
            f"Hay una nueva versión disponible: {nueva_version}"
        )

        respuesta = QMessageBox.question(
            None,
            "Actualización disponible",
            (
                f"Hay una nueva versión disponible: "
                f"{nueva_version}\n\n"
                "¿Desea actualizar ahora?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if respuesta == QMessageBox.Yes:

            print(
                "Usuario aceptó actualización"
            )

            from core.actualizador import (
                descargar_actualizacion,
                instalar_actualizacion
            )

            # ==================================
            # PROGRESO
            # ==================================

            progreso = QProgressDialog(
                "Descargando actualización...",
                None,
                0,
                100
            )

            progreso.setWindowTitle(
                "Actualizando Papelera POS"
            )

            progreso.setMinimumDuration(0)

            progreso.setValue(0)

            progreso.setAutoClose(False)

            progreso.setAutoReset(False)

            progreso.setCancelButton(None)

            progreso.show()

            QApplication.processEvents()

            # ==================================
            # ACTUALIZAR PROGRESO
            # ==================================

            def actualizar_progreso(valor):

                progreso.setValue(valor)

                progreso.setLabelText(
                    f"Descargando actualización... {valor}%"
                )

                QApplication.processEvents()

            # ==================================
            # DESCARGAR
            # ==================================

            zip_actualizacion = descargar_actualizacion(
                actualizar_progreso
            )

            if zip_actualizacion:

                print(
                    "Actualización descargada."
                )

                # ==================================
                # INSTALAR
                # ==================================

                instalado = instalar_actualizacion(
                    zip_actualizacion,
                    nueva_version
                )

                if instalado:

                    print(
                        "Actualización instalada."
                    )

                    print(
                        "Cerrando versión anterior..."
                    )

                    progreso.setLabelText(
                        "Actualización instalada. Reiniciando..."
                    )

                    progreso.setValue(100)

                    QApplication.processEvents()

                    # ==================================
                    # MUY IMPORTANTE
                    #
                    # No crear Dashboard.
                    # No iniciar sincronización.
                    # No iniciar webhook.
                    #
                    # El BAT externo esperará que
                    # este proceso termine y luego
                    # abrirá el nuevo EXE.
                    # ==================================

                    app.quit()

                    sys.exit(0)

                else:

                    print(
                        "ERROR: No se pudo instalar la actualización."
                    )

                    progreso.close()

                    QMessageBox.warning(
                        None,
                        "Error",
                        (
                            "No se pudo instalar la actualización.\n\n"
                            "El programa continuará con la versión actual."
                        )
                    )

            else:

                print(
                    "ERROR: No se pudo descargar la actualización."
                )

                progreso.close()

                QMessageBox.warning(
                    None,
                    "Error",
                    (
                        "No se pudo descargar la actualización.\n\n"
                        "Verifique la conexión a Internet."
                    )
                )

        else:

            print(
                "Usuario rechazó actualización."
            )

    # ==================================
    # CREAR BASE LOCAL
    #
    # SOLAMENTE si no estamos actualizando.
    # ==================================

    init_db()

    # ==================================
    # SERVIDOR LOCAL
    # ==================================

    try:

        start_webhook_server()

    except Exception as e:

        print(
            "Error iniciando servidor webhook:",
            e
        )

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

    keyboard_filter = KeyboardAndNumberFilter(
        app
    )

    app.installEventFilter(
        keyboard_filter
    )

    # ==================================
    # PANTALLA PRINCIPAL
    # ==================================

    print(
        "Iniciando Dashboard..."
    )

    w = Dashboard()

    w.showMaximized()

    # ==================================
    # EJECUTAR APLICACION
    # ==================================

    sys.exit(
        app.exec()
    )