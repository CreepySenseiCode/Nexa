"""Modèle pour la gestion des catégories de tâches."""

import logging
import sqlite3
from typing import Optional

from models.base_model import BaseModel

logger = logging.getLogger(__name__)


class CategorieTacheModel(BaseModel):
    """Modèle pour les catégories de tâches."""

    _table = "categories_taches"

    def creer_categorie(self, nom: str, couleur: str = "#2196F3") -> int:
        try:
            cursor = self.db.execute(
                "INSERT INTO categories_taches (nom, couleur) VALUES (?, ?)",
                (nom, couleur),
            )
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning("Catégorie tâche '%s' existe déjà", nom)
            row = self.db.fetchone(
                "SELECT id FROM categories_taches WHERE nom = ?", (nom,)
            )
            return row["id"] if row else -1
        except sqlite3.Error as e:
            logger.error("Erreur création catégorie tâche : %s", e)
            return -1

    def lister_categories(self) -> list[dict]:
        try:
            return self.db.fetchall(
                "SELECT * FROM categories_taches ORDER BY nom"
            )
        except sqlite3.Error as e:
            logger.error("Erreur listing catégories tâches : %s", e)
            return []

    def supprimer_categorie(self, categorie_id: int) -> bool:
        try:
            self.db.execute(
                "UPDATE taches SET categorie_id = NULL WHERE categorie_id = ?",
                (categorie_id,),
            )
            self.db.execute(
                "DELETE FROM categories_taches WHERE id = ?", (categorie_id,)
            )
            return True
        except sqlite3.Error as e:
            logger.error("Erreur suppression catégorie tâche %s : %s", categorie_id, e)
            return False

    def modifier_couleur(self, categorie_id: int, couleur: str) -> bool:
        try:
            self.db.execute(
                "UPDATE categories_taches SET couleur = ? WHERE id = ?",
                (couleur, categorie_id),
            )
            return True
        except sqlite3.Error as e:
            logger.error("Erreur modif couleur catégorie %s : %s", categorie_id, e)
            return False

    def modifier_categorie(
        self, categorie_id: int, nom: str, couleur: str
    ) -> bool:
        try:
            self.db.execute(
                "UPDATE categories_taches SET nom = ?, couleur = ? WHERE id = ?",
                (nom, couleur, categorie_id),
            )
            return True
        except sqlite3.Error as e:
            logger.error("Erreur modification catégorie tâche %s : %s", categorie_id, e)
            return False
