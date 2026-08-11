import json
import sqlite3
from datetime import datetime
from pathlib import Path

from core.config import DATABASE_FILE


SYNC_FILE = Path(DATABASE_FILE).parent / "sync_queue.json"


def add_change(tabla, accion, datos):
    cola = []
    if SYNC_FILE.exists():
        try:
            cola = json.loads(SYNC_FILE.read_text(encoding="utf-8"))
        except Exception:
            cola = []

    cola.append({
        "fecha": datetime.now().isoformat(),
        "tabla": tabla,
        "accion": accion,
        "datos": datos
    })

    SYNC_FILE.write_text(
        json.dumps(cola, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def get_pending_changes():
    if not SYNC_FILE.exists():
        return []

    try:
        return json.loads(SYNC_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def clear_pending_changes():
    if SYNC_FILE.exists():
        SYNC_FILE.unlink()
