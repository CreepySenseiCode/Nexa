"""Modele pour la gestion des emails enregistres (templates et brouillons)."""

import logging
from typing import Optional
import sqlite3

from models.database import get_db

logger = logging.getLogger(__name__)


class EmailModel:
    """Modele pour les emails enregistres."""

    def __init__(self) -> None:
        self.db = get_db()

    def lister_mails(self) -> list[dict]:
        """Retourne tous les mails enregistres."""
        try:
            return self.db.fetchall(
                "SELECT id, nom_mail, objet FROM mails_enregistres "
                "ORDER BY date_modification DESC"
            )
        except sqlite3.Error as e:
            logger.error("Erreur lors du listage des mails : %s", e)
            return []

    def obtenir_mail(self, mail_id: int) -> Optional[dict]:
        """Retourne un mail par ID."""
        try:
            return self.db.fetchone(
                "SELECT * FROM mails_enregistres WHERE id = ?", (mail_id,)
            )
        except sqlite3.Error as e:
            logger.error("Erreur lors de la lecture du mail %s : %s", mail_id, e)
            return None

    def creer_mail(self, nom: str, objet: str = "", contenu_html: str = "") -> int:
        """Cree un nouveau mail enregistre. Retourne l'ID."""
        try:
            cursor = self.db.execute(
                "INSERT INTO mails_enregistres (nom_mail, objet, contenu_html) "
                "VALUES (?, ?, ?)",
                (nom, objet, contenu_html),
            )
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error("Erreur lors de la creation du mail : %s", e)
            raise

    def supprimer_mail(self, mail_id: int) -> bool:
        """Supprime un mail enregistre."""
        try:
            self.db.execute(
                "DELETE FROM mails_enregistres WHERE id = ?", (mail_id,)
            )
            return True
        except sqlite3.Error as e:
            logger.error("Erreur lors de la suppression du mail %s : %s", mail_id, e)
            raise
