"""Utilitaire de sauvegarde de la base de donnees."""

import os
import shutil
from datetime import datetime

_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_PATH = os.path.join(_APP_DIR, "data", "app.db")
_BACKUP_DIR = os.path.join(_APP_DIR, "data", "backups")


def sauvegarder_base() -> str:
    """Cree une copie horodatee de la base de donnees.

    Returns:
        Le chemin du fichier de sauvegarde cree.
    """
    os.makedirs(_BACKUP_DIR, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(_BACKUP_DIR, f"app_{horodatage}.db")
    shutil.copy2(_DB_PATH, dest)
    return dest
