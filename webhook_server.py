import json, threading, sqlite3, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from ui.db import BASE_DATOS, init_db

HOST = "127.0.0.1"
PORT = 8765

class MercadoPagoWebhookHandler(BaseHTTPRequestHandler):
    def _reply(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
    def do_POST(self):
        try:
            length=int(self.headers.get("Content-Length", "0"))
            raw=self.rfile.read(length) if length else b"{}"
            try: payload=json.loads(raw.decode("utf-8", "replace"))
            except Exception: payload={"raw":raw.decode("utf-8", "replace")}
            init_db()
            con=sqlite3.connect(BASE_DATOS)
            try:
                con.execute("CREATE TABLE IF NOT EXISTS mp_webhooks (id INTEGER PRIMARY KEY AUTOINCREMENT, recibido_en TEXT, payload TEXT, tipo TEXT, x_request_id TEXT)")
                # Compatibilidad con bases creadas por versiones anteriores.
                cols={r[1] for r in con.execute("PRAGMA table_info(mp_webhooks)").fetchall()}
                if "tipo" not in cols:
                    con.execute("ALTER TABLE mp_webhooks ADD COLUMN tipo TEXT")
                if "x_request_id" not in cols:
                    con.execute("ALTER TABLE mp_webhooks ADD COLUMN x_request_id TEXT")
                tipo=str(payload.get("type") or payload.get("action") or "desconocido")
                request_id=self.headers.get("x-request-id","")
                con.execute(
                    "INSERT INTO mp_webhooks(recibido_en,payload,tipo,x_request_id) VALUES(?,?,?,?)",
                    (datetime.datetime.now().isoformat(timespec="seconds"),json.dumps(payload,ensure_ascii=False),tipo,request_id)
                )
                con.commit()
            finally: con.close()
            self._reply(200)
        except Exception:
            self._reply(200)  # Mercado Pago should receive 200 to avoid unnecessary retries.
    def do_GET(self):
        if self.path.startswith("/webhook/mercadopago") or self.path == "/health" or self.path == "/":
            self._reply(200)
        else:
            self._reply(404)
    def log_message(self, format, *args):
        return

def start_webhook_server():
    def run():
        try:
            HTTPServer((HOST, PORT), MercadoPagoWebhookHandler).serve_forever()
        except Exception:
            pass
    t=threading.Thread(target=run,daemon=True)
    t.start()
    return t
