"""Modele pour la gestion des attributs de produits."""

import logging
import sqlite3

from models.database import get_db

logger = logging.getLogger(__name__)


class AttributProduitModel:
    """Modele pour les attributs personnalises des produits."""

    def __init__(self) -> None:
        self.db = get_db()

    def lister_attributs_globaux(self) -> list[dict]:
        """Retourne les attributs globaux (categorie_id IS NULL)."""
        try:
            return self.db.fetchall(
                "SELECT id, nom_attribut FROM attributs_produits "
                "WHERE categorie_id IS NULL ORDER BY nom_attribut"
            )
        except sqlite3.Error as e:
            logger.error("Erreur lors du listage des attributs : %s", e)
            return []

    def ajouter_attribut(self, nom: str) -> int:
        """Ajoute un attribut global. Retourne l'ID ou -1."""
        try:
            cursor = self.db.execute(
                "INSERT INTO attributs_produits (categorie_id, nom_attribut) "
                "VALUES (NULL, ?)",
                (nom,),
            )
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error("Erreur lors de l'ajout de l'attribut '%s' : %s", nom, e)
            raise

    def supprimer_attribut(self, nom: str) -> bool:
        """Supprime un attribut global par nom et ses valeurs associees."""
        try:
            attr = self.db.fetchone(
                "SELECT id FROM attributs_produits "
                "WHERE nom_attribut = ? AND categorie_id IS NULL",
                (nom,),
            )
            if not attr:
                return False
            with self.db.transaction():
                self.db.execute(
                    "DELETE FROM valeurs_attributs_produits WHERE attribut_id = ?",
                    (attr['id'],),
                )
                self.db.execute(
                    "DELETE FROM attributs_produits WHERE id = ?",
                    (attr['id'],),
                )
            return True
        except sqlite3.Error as e:
            logger.error("Erreur lors de la suppression de l'attribut '%s' : %s", nom, e)
            raise
