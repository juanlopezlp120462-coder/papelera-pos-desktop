import requests

SERVIDOR = "https://papelera-pos-backend-production.up.railway.app"

TIMEOUT = 15


def listar_productos():
    r = requests.get(f"{SERVIDOR}/productos/", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def listar_clientes():
    r = requests.get(f"{SERVIDOR}/clientes/", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def crear_venta(datos):
    r = requests.post(
        f"{SERVIDOR}/ventas/",
        json=datos,
        timeout=TIMEOUT
    )
    r.raise_for_status()
    return r.json()


def detalle_venta(id_venta):
    r = requests.get(
        f"{SERVIDOR}/ventas/{id_venta}/detalle",
        timeout=TIMEOUT
    )
    r.raise_for_status()
    return r.json()


def actualizar_producto(id_producto, datos):
    r = requests.put(
        f"{SERVIDOR}/productos/{id_producto}",
        json=datos,
        timeout=TIMEOUT
    )
    r.raise_for_status()
    return r.json()


def crear_cliente(datos):
    r = requests.post(
        f"{SERVIDOR}/clientes/",
        json=datos,
        timeout=TIMEOUT
    )
    r.raise_for_status()
    return r.json()