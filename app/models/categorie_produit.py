"""Modèle pour la gestion des catégories de produits.

Ce module fournit la classe CategorieProduitModel qui encapsule les opérations
CRUD sur la table ``categories_produits``.
"""

import logging
from typing import Optional

from models.base_model import BaseModel

logger = logging.getLogger(__name__)


class CategorieProduitModel(BaseModel):
    """Modèle pour la gestion des catégories de produits.

    Gère la création, la modification, la suppression et la consultation
    des catégories de produits.
    """

    _table = "categories_produits"

    def ajouter_categorie(self, nom: str, description: str = "") -> int:
        """Ajoute une nouvelle catégorie de produit.

        Args:
            nom: Nom de la catégorie
            description: Description optionnelle de la catégorie

        Returns:
            ID de la catégorie créée, ou -1 en cas d'erreur
        """
        if not nom or not nom.strip():
            logger.warning("Tentative d'ajout d'une catégorie sans nom")
            return -1

        try:
            cursor = self.db.execute(
                "INSERT INTO categories_produits (nom, description) VALUES (?, ?)",
                (nom.strip(), description.strip())
            )
            categorie_id = cursor.lastrowid
            logger.info(f"Catégorie créée : {nom} (ID: {categorie_id})")
            return categorie_id

        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la catégorie '{nom}' : {e}", exc_info=True)
            return -1

    def supprimer_categorie(self, categorie_id: int) -> bool:
        """Supprime une catégorie de produit.

        Args:
            categorie_id: ID de la catégorie à supprimer

        Returns:
            True si la suppression a réussi, False sinon
        """
        try:
            self.db.execute(
                "DELETE FROM categories_produits WHERE id = ?",
                (categorie_id,)
            )
            logger.info(f"Catégorie {categorie_id} supprimée")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la catégorie {categorie_id} : {e}", exc_info=True)
            return False

    def lister_categories(self, actives_uniquement: bool = True) -> list[dict]:
        """Liste toutes les catégories de produits.

        Args:
            actives_uniquement: Si True, ne retourne que les catégories actives

        Returns:
            Liste de dictionnaires représentant les catégories
            Format: [{'id': int, 'nom': str, 'description': str, ...}, ...]
        """
        try:
            if actives_uniquement:
                query = """
                    SELECT id, nom, description, actif, ordre, date_creation
                    FROM categories_produits
                    WHERE actif = 1
                    ORDER BY ordre, nom
                """
            else:
                query = """
                    SELECT id, nom, description, actif, ordre, date_creation
                    FROM categories_produits
                    ORDER BY ordre, nom
                """

            categories = self.db.fetchall(query)
            logger.info(f"{len(categories)} catégories chargées")
            return categories

        except Exception as e:
            logger.error(f"Erreur lors du chargement des catégories : {e}", exc_info=True)
            return []

    def obtenir_categorie(self, categorie_id: int) -> Optional[dict]:
        """Récupère une catégorie par son ID.

        Args:
            categorie_id: ID de la catégorie

        Returns:
            Dictionnaire représentant la catégorie, ou None si non trouvée
        """
        try:
            categorie = self.db.fetchone(
                "SELECT id, nom, description, actif, ordre, date_creation FROM categories_produits WHERE id = ?",
                (categorie_id,)
            )
            return categorie

        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la catégorie {categorie_id} : {e}", exc_info=True)
            return None

    def modifier_categorie(self, categorie_id: int, nom: str = None, description: str = None, actif: bool = None, ordre: int = None) -> bool:
        """Modifie une catégorie existante.

        Args:
            categorie_id: ID de la catégorie à modifier
            nom: Nouveau nom (optionnel)
            description: Nouvelle description (optionnel)
            actif: Statut actif/inactif (optionnel)
            ordre: Ordre d'affichage (optionnel)

        Returns:
            True si la modification a réussi, False sinon
        """
        try:
            updates = []
            params = []

            if nom is not None:
                updates.append("nom = ?")
                params.append(nom.strip())
            if description is not None:
                updates.append("description = ?")
                params.append(description.strip())
            if actif is not None:
                updates.append("actif = ?")
                params.append(1 if actif else 0)
            if ordre is not None:
                updates.append("ordre = ?")
                params.append(ordre)

            if not updates:
                logger.warning(f"Aucune modification à apporter à la catégorie {categorie_id}")
                return False

            params.append(categorie_id)
            query = f"UPDATE categories_produits SET {', '.join(updates)} WHERE id = ?"

            self.db.execute(query, tuple(params))
            logger.info(f"Catégorie {categorie_id} modifiée")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de la modification de la catégorie {categorie_id} : {e}", exc_info=True)
            return False
