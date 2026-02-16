"""
Modèle pour la gestion des produits.

Ce module fournit la classe ProduitModel qui encapsule les opérations
CRUD sur la table ``produits``. Pour la gestion des catégories, voir
:class:`~models.categorie_produit.CategorieProduitModel`.
"""

import logging
import sqlite3
from typing import Optional

from models.base_model import BaseModel

logger = logging.getLogger(__name__)


class ProduitModel(BaseModel):
    """Modèle pour la gestion des produits.

    Gère la création, la modification, la suppression et la consultation
    des produits.
    """

    _table = "produits"

    # ==================================================================
    # Produits
    # ==================================================================

    def creer_produit(
        self,
        categorie_id: int = None,
        nom: str = "",
        prix: float = 0.0,
        description: str = "",
        stock: int = 0,
        photo: str = None,
    ) -> int:
        """Crée un nouveau produit.

        Args:
            categorie_id: Identifiant de la catégorie parente (peut être None).
            nom:          Nom du produit.
            prix:         Prix unitaire du produit (défaut 0.0).
            description:  Description textuelle du produit.
            stock:        Stock initial du produit (défaut 0).
            photo:        Chemin vers l'image du produit (optionnel).

        Returns:
            L'identifiant (ID) du produit créé, ou ``-1`` en cas
            d'erreur.
        """
        try:
            cursor = self.db.execute(
                """
                INSERT INTO produits (categorie_id, nom, prix, stock, description, photo)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (categorie_id, nom, prix, stock, description, photo),
            )
            nouveau_id = cursor.lastrowid
            logger.info("Produit créé : '%s' (ID %s)", nom, nouveau_id)
            return nouveau_id

        except sqlite3.Error as e:
            logger.error(
                "Erreur lors de la création du produit '%s' : %s", nom, e
            )
            return -1

    def modifier_produit(self, produit_id: int, donnees: dict) -> bool:
        """Modifie un produit existant.

        Args:
            produit_id: Identifiant du produit à modifier.
            donnees:    Dictionnaire des colonnes à mettre à jour.

        Returns:
            ``True`` si la modification a réussi, ``False`` sinon.
        """
        try:
            if not donnees:
                return False

            clauses = ", ".join([f"{col} = ?" for col in donnees.keys()])
            valeurs = tuple(donnees.values()) + (produit_id,)

            query = f"UPDATE produits SET {clauses} WHERE id = ?"
            self.db.execute(query, valeurs)

            logger.info("Produit %s modifié avec succès", produit_id)
            return True

        except sqlite3.Error as e:
            logger.error(
                "Erreur lors de la modification du produit %s : %s",
                produit_id,
                e,
            )
            return False

    def obtenir_produit(self, produit_id: int) -> Optional[dict]:
        """Retourne un produit par son identifiant.

        Args:
            produit_id: Identifiant du produit recherché.

        Returns:
            Un dictionnaire représentant le produit, ou ``None`` s'il
            n'existe pas ou en cas d'erreur.
        """
        try:
            return self.db.fetchone(
                "SELECT * FROM produits WHERE id = ?", (produit_id,)
            )
        except sqlite3.Error as e:
            logger.error(
                "Erreur lors de la récupération du produit %s : %s",
                produit_id,
                e,
            )
            return None

    def lister_produits(self, categorie_id: Optional[int] = None,
                        uniquement_en_stock: bool = False) -> list[dict]:
        """Retourne les produits, filtrés par catégorie si spécifié.

        Le nom de la catégorie est inclus via une jointure avec la
        table ``categories_produits``.

        Args:
            categorie_id:       Identifiant de la catégorie pour filtrer.
                                Si ``None``, tous les produits sont retournés.
            uniquement_en_stock: Si True, exclut les produits à stock <= 0.

        Returns:
            Une liste de dictionnaires, un par produit.
        """
        try:
            query = """
                SELECT p.*, COALESCE(cp.nom, 'Sans catégorie') AS categorie_nom
                FROM produits p
                LEFT JOIN categories_produits cp ON cp.id = p.categorie_id
                WHERE 1=1
            """
            params = []

            if categorie_id is not None:
                query += " AND p.categorie_id = ?"
                params.append(categorie_id)

            if uniquement_en_stock:
                query += " AND p.stock > 0"

            query += " ORDER BY cp.nom, p.nom"

            return self.db.fetchall(query, tuple(params) if params else ())

        except sqlite3.Error as e:
            logger.error(
                "Erreur lors du listage des produits : %s", e
            )
            return []

    def supprimer_produit(self, produit_id: int) -> bool:
        """Supprime un produit de la base de données.

        Les valeurs d'attributs associées au produit sont également
        supprimées.

        Args:
            produit_id: Identifiant du produit à supprimer.

        Returns:
            ``True`` si la suppression a réussi, ``False`` sinon.
        """
        try:
            with self.db.transaction():
                # Supprimer les valeurs d'attributs associées
                self.db.execute(
                    "DELETE FROM valeurs_attributs_produits WHERE produit_id = ?",
                    (produit_id,),
                )
                # Supprimer le produit
                self.db.execute(
                    "DELETE FROM produits WHERE id = ?", (produit_id,)
                )

            logger.info("Produit %s supprimé avec succès", produit_id)
            return True

        except sqlite3.Error as e:
            logger.error(
                "Erreur lors de la suppression du produit %s : %s",
                produit_id,
                e,
            )
            return False
