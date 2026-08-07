from pathlib import Path
import sys

if getattr(sys, "frozen", False):
    ROOT_DIR = Path(sys.executable).resolve().parent
else:
    ROOT_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = ROOT_DIR / "database"
BACKUP_DIR = ROOT_DIR / "backups"
LOG_DIR = ROOT_DIR / "logs"
DATABASE_FILE = DATABASE_DIR / "abril.db"

DATABASE_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
