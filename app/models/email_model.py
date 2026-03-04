"""Modele pour la gestion des emails enregistres (templates et brouillons)."""

import logging
from typing import Optional
import sqlite3

from models.base_model import BaseModel

logger = logging.getLogger(__name__)


class EmailModel(BaseModel):
    """Modele pour les emails enregistres."""

    _table = "mails_enregistres"

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

    def lister_brouillons(self) -> list[dict]:
        """Retourne les mails de type brouillon."""
        try:
            return self.db.fetchall(
                "SELECT id, nom_mail, objet FROM mails_enregistres "
                "WHERE type = 'brouillon' ORDER BY date_creation DESC"
            )
        except sqlite3.Error as e:
            logger.error("Erreur lors du listage des brouillons : %s", e)
            return []

    def lister_templates_only(self) -> list[dict]:
        """Retourne les mails de type template."""
        try:
            return self.db.fetchall(
                "SELECT id, nom_mail, objet FROM mails_enregistres "
                "WHERE type = 'template' ORDER BY date_creation DESC"
            )
        except sqlite3.Error as e:
            logger.error("Erreur lors du listage des templates : %s", e)
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

    def creer_mail(self, nom: str, objet: str = "", contenu_html: str = "",
                   contenu_texte: str = "", type_mail: str = "template",
                   pieces_jointes: str = "") -> int:
        """Cree un nouveau mail enregistre. Retourne l'ID."""
        try:
            cursor = self.db.execute(
                "INSERT INTO mails_enregistres "
                "(nom_mail, objet, contenu_html, contenu_texte, type, pieces_jointes) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (nom, objet, contenu_html, contenu_texte, type_mail, pieces_jointes),
            )
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error("Erreur lors de la creation du mail : %s", e)
            raise

    def modifier_mail(self, mail_id: int, nom: str = None, objet: str = None,
                      contenu_html: str = None, contenu_texte: str = None) -> bool:
        """Met a jour un mail enregistre."""
        try:
            fields = []
            params = []
            if nom is not None:
                fields.append("nom_mail = ?")
                params.append(nom)
            if objet is not None:
                fields.append("objet = ?")
                params.append(objet)
            if contenu_html is not None:
                fields.append("contenu_html = ?")
                params.append(contenu_html)
            if contenu_texte is not None:
                fields.append("contenu_texte = ?")
                params.append(contenu_texte)
            if not fields:
                return False
            fields.append("date_modification = CURRENT_TIMESTAMP")
            params.append(mail_id)
            self.db.execute(
                f"UPDATE mails_enregistres SET {', '.join(fields)} WHERE id = ?",
                tuple(params),
            )
            return True
        except sqlite3.Error as e:
            logger.error("Erreur modification mail %s : %s", mail_id, e)
            return False

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
