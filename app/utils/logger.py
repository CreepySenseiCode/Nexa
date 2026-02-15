"""Configuration du logging centralise pour Nexa."""
import logging
import sys
from pathlib import Path
from datetime import datetime


def configurer_logger(
    nom: str = "nexa",
    niveau=logging.INFO,
    log_console: bool = True
) -> logging.Logger:
    """Configure et retourne le logger de l'application.

    Args:
        nom: Nom du logger (defaut: "nexa")
        niveau: Niveau de logging (defaut: INFO)
        log_console: Si True, affiche aussi dans la console

    Returns:
        Logger configure
    """
    # Créer dossier logs
    app_dir = Path(__file__).parent.parent
    log_dir = app_dir.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Fichier log avec date
    log_file = log_dir / f"nexa_{datetime.now():%Y%m%d}.log"

    # Logger
    logger = logging.getLogger(nom)
    logger.setLevel(niveau)

    # Éviter doublons si déjà configuré
    if logger.handlers:
        return logger

    # Format detaille
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler fichier (DEBUG et +)
    try:
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception as e:
        print(f"Impossible de creer le fichier log : {e}", file=sys.stderr)

    # Handler console (INFO et +)
    if log_console:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


# Logger global pour l'application
logger = configurer_logger()
