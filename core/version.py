import sys
import os
import requests

SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"
TIMEOUT = 5

# ... (todo tu código anterior se mantiene igual hasta la función obtener_ultima_version)

# ============================================================
# VERSION DEL SERVIDOR (CORREGIDA)
# ============================================================

def obtener_ultima_version():

    try:
        url = f"{SERVIDOR}/version"
        
        # AGREGAMOS ESTO:
        # Intentamos obtener el token si está definido en el entorno
        headers = {}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"

        print("Consultando versión:", url)

        # Pasamos los headers a la petición
        respuesta = requests.get(
            url,
            headers=headers,
            timeout=TIMEOUT
        )

        print("HTTP versión:", respuesta.status_code)
        
        # ... (el resto de tu código se mantiene exactamente igual)
        
        if respuesta.status_code != 200:
            return None

        datos = respuesta.json()
        # ... (continúa igual tu lógica)
        
        # (Asegúrate de no borrar nada más abajo)
        version = datos.get("version")
        # ...
        
        return datos

    except Exception as e:
        print("Error consultando versión:", repr(e))
    return None