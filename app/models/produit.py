"""
Modèle pour la gestion des produits et catégories.

Ce module fournit la classe ProduitModel qui encapsule les opérations
CRUD sur les tables ``produits`` et ``categories_produits``.
"""

import logging
from typing import Optional

from models.database import get_db

logger = logging.getLogger(__name__)


class ProduitModel:
    """Modèle pour la gestion des produits et catégories.

    Gère la création, la modification, la suppression et la consultation
    des produits et de leurs catégories.
    """

    def __init__(self) -> None:
        self.db = get_db()

    # ==================================================================
    # Catégories
    # ==================================================================

    def creer_categorie(self, nom: str) -> int:
        """Crée une nouvelle catégorie de produits.

        Args:
            nom: Nom de la catégorie.

        Returns:
            L'identifiant (ID) de la catégorie créée, ou ``-1`` en cas
            d'erreur.
        """
        try:
            cursor = self.db.execute(
                "INSERT INTO categories_produits (nom) VALUES (?)",
                (nom,),
            )
            nouveau_id = cursor.lastrowid
            logger.info("Catégorie créée : '%s' (ID %s)", nom, nouveau_id)
            return nouveau_id

        except Exception as e:
            logger.error(
                "Erreur lors de la création de la catégorie '%s' : %s", nom, e
            )
            return -1

    def lister_categories(self) -> list[dict]:
        """Retourne toutes les catégories de produits.

        Returns:
            Une liste de dictionnaires, un par catégorie.
        """
        try:
            return self.db.fetchall(
                "SELECT * FROM categories_produits ORDER BY nom"
            )
        except Exception as e:
            logger.error(
                "Erreur lors du listage des catégories : %s", e
            )
            return []

    def supprimer_categorie(self, categorie_id: int) -> bool:
        """Supprime une catégorie et tous ses produits associés.

        Les produits rattachés à cette catégorie sont supprimés en
        premier, puis la catégorie elle-même.

        Args:
            categorie_id: Identifiant de la catégorie à supprimer.

        Returns:
            ``True`` si la suppression a réussi, ``False`` sinon.
        """
        try:
            with self.db.transaction():
                # Supprimer d'abord les produits de la catégorie
                self.db.execute(
                    "DELETE FROM produits WHERE categorie_id = ?",
                    (categorie_id,),
                )
                # Supprimer les attributs de la catégorie
                self.db.execute(
                    "DELETE FROM attributs_produits WHERE categorie_id = ?",
                    (categorie_id,),
                )
                # Supprimer la catégorie
                self.db.execute(
                    "DELETE FROM categories_produits WHERE id = ?",
                    (categorie_id,),
                )

            logger.info("Catégorie %s supprimée avec succès", categorie_id)
            return True

        except Exception as e:
            logger.error(
                "Erreur lors de la suppression de la catégorie %s : %s",
                categorie_id,
                e,
            )
            return False

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
    ) -> int:
        """Crée un nouveau produit.

        Args:
            categorie_id: Identifiant de la catégorie parente (peut être None).
            nom:          Nom du produit.
            prix:         Prix unitaire du produit (défaut 0.0).
            description:  Description textuelle du produit.
            stock:        Stock initial du produit (défaut 0).

        Returns:
            L'identifiant (ID) du produit créé, ou ``-1`` en cas
            d'erreur.
        """
        try:
            cursor = self.db.execute(
                """
                INSERT INTO produits (categorie_id, nom, prix, stock, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (categorie_id, nom, prix, stock, description),
            )
            nouveau_id = cursor.lastrowid
            logger.info("Produit créé : '%s' (ID %s)", nom, nouveau_id)
            return nouveau_id

        except Exception as e:
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

        except Exception as e:
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
        except Exception as e:
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

        except Exception as e:
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

        except Exception as e:
            logger.error(
                "Erreur lors de la suppression du produit %s : %s",
                produit_id,
                e,
            )
            return False
