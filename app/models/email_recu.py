"""Modele pour la gestion des emails recus et de l'historique d'envoi."""

import logging
from typing import Optional
import sqlite3

from models.database import get_db

logger = logging.getLogger(__name__)


class EmailRecuModel:
    """Modele pour les emails recus."""

    def __init__(self) -> None:
        self.db = get_db()

    def lister_emails(self, adresse: str = None) -> list[dict]:
        """Retourne les emails recus, optionnellement filtres par adresse."""
        try:
            if adresse:
                return self.db.fetchall(
                    """
                    SELECT id, expediteur_email, expediteur_nom, objet,
                           date_reception, lu, pieces_jointes, compte_email_recepteur
                    FROM emails_recus
                    WHERE compte_email_recepteur = ?
                    ORDER BY date_reception DESC
                    """,
                    (adresse,),
                )
            else:
                return self.db.fetchall(
                    """
                    SELECT id, expediteur_email, expediteur_nom, objet,
                           date_reception, lu, pieces_jointes, compte_email_recepteur
                    FROM emails_recus
                    ORDER BY date_reception DESC
                    """
                )
        except sqlite3.Error as e:
            logger.error("Erreur lors du listage des emails : %s", e)
            return []


class HistoriqueEmailModel:
    """Modele pour l'historique des emails envoyes."""

    def __init__(self) -> None:
        self.db = get_db()

    def lister_historique(self) -> list[dict]:
        """Retourne l'historique des emails envoyes."""
        try:
            return self.db.fetchall(
                """
                SELECT id, objet, type_envoi, nombre_destinataires,
                       destinataires, date_envoi, statut
                FROM historique_emails
                ORDER BY date_envoi DESC
                """
            )
        except sqlite3.Error as e:
            logger.error("Erreur lors du listage de l'historique : %s", e)
            return []
