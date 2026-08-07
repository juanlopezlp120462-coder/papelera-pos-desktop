import time
import threading
from sync import sincronizar


def iniciar_sync_automatico():

    def trabajo():

        while True:
            try:
                sincronizar()
            except Exception as e:
                print("Sync esperando conexión:", e)

            time.sleep(60)  # revisa cada 60 segundos


    hilo = threading.Thread(
        target=trabajo,
        daemon=True
    )

    hilo.start()