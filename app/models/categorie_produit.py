"""
Modèle Catégorie Produit.
"""
import logging
import sqlite3

from models.database import get_db

logger = logging.getLogger(__name__)


class CategorieProduitModel:
    """Gestion des catégories de produits."""

    def __init__(self):
        self.db = get_db()

    def lister_categories(self, actives_uniquement=True):
        """Liste toutes les catégories."""
        query = """
            SELECT id, nom, description, actif, ordre
            FROM categories_produits
        """

        if actives_uniquement:
            query += " WHERE actif = 1"

        query += " ORDER BY ordre ASC, nom ASC"

        return self.db.fetchall(query)

    def obtenir_categorie(self, categorie_id: int):
        """Récupère une catégorie par son ID."""
        return self.db.fetchone(
            "SELECT * FROM categories_produits WHERE id = ?",
            (categorie_id,)
        )

    def creer_categorie(self, nom: str, description: str = None) -> int:
        """Crée une nouvelle catégorie."""
        try:
            existe = self.db.fetchone(
                "SELECT id FROM categories_produits WHERE nom = ?",
                (nom,)
            )

            if existe:
                return existe['id']

            max_ordre = self.db.fetchone(
                "SELECT MAX(ordre) as max_ordre FROM categories_produits"
            )
            ordre = (max_ordre['max_ordre'] or 0) + 1 if max_ordre else 1

            self.db.execute(
                """
                INSERT INTO categories_produits (nom, description, ordre)
                VALUES (?, ?, ?)
                """,
                (nom, description, ordre)
            )

            result = self.db.fetchone(
                "SELECT last_insert_rowid() as id"
            )
            return result['id'] if result else None

        except sqlite3.Error as e:
            logger.error("Erreur création catégorie : %s", e)
            return None

    def modifier_categorie(self, categorie_id: int, nom: str = None,
                           description: str = None, actif: int = None):
        """Modifie une catégorie."""
        updates = []
        params = []

        if nom is not None:
            updates.append("nom = ?")
            params.append(nom)

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if actif is not None:
            updates.append("actif = ?")
            params.append(actif)

        if not updates:
            return False

        params.append(categorie_id)

        query = f"UPDATE categories_produits SET {', '.join(updates)} WHERE id = ?"

        try:
            self.db.execute(query, tuple(params))
            return True
        except sqlite3.Error as e:
            logger.error("Erreur modification catégorie : %s", e)
            return False

    def supprimer_categorie(self, categorie_id: int, soft_delete=True):
        """Supprime ou désactive une catégorie."""
        try:
            if soft_delete:
                self.db.execute(
                    "UPDATE categories_produits SET actif = 0 WHERE id = ?",
                    (categorie_id,)
                )
            else:
                self.db.execute(
                    "UPDATE produits SET categorie_id = NULL WHERE categorie_id = ?",
                    (categorie_id,)
                )
                self.db.execute(
                    "DELETE FROM categories_produits WHERE id = ?",
                    (categorie_id,)
                )

            return True

        except sqlite3.Error as e:
            logger.error("Erreur suppression catégorie : %s", e)
            return False

    def compter_produits(self, categorie_id: int) -> int:
        """Compte le nombre de produits dans une catégorie."""
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM produits WHERE categorie_id = ?",
            (categorie_id,)
        )
        return result['count'] if result else 0
