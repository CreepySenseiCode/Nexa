"""Modèle pour la gestion des catégories de produits.

Ce module permet de créer, lister et supprimer des catégories de produits.
"""

import logging
from models.database import Database

logger = logging.getLogger(__name__)


def ajouter_categorie(nom: str, description: str = "") -> int:
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
        db = Database()
        # Vérifier que la table existe
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS categories_produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL UNIQUE,
                description TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        db.execute(
            "INSERT INTO categories_produits (nom, description) VALUES (?, ?)",
            (nom.strip(), description.strip())
        )
        categorie_id = db.lastrowid()
        logger.info(f"Catégorie créée : {nom} (ID: {categorie_id})")
        return categorie_id

    except Exception as e:
        logger.error(f"Erreur lors de l'ajout de la catégorie '{nom}' : {e}", exc_info=True)
        return -1


def supprimer_categorie(categorie_id: int) -> bool:
    """Supprime une catégorie de produit.

    Args:
        categorie_id: ID de la catégorie à supprimer

    Returns:
        True si la suppression a réussi, False sinon
    """
    try:
        db = Database()
        db.execute(
            "DELETE FROM categories_produits WHERE id = ?",
            (categorie_id,)
        )
        logger.info(f"Catégorie {categorie_id} supprimée")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de la suppression de la catégorie {categorie_id} : {e}", exc_info=True)
        return False


def lister_categories() -> list[dict]:
    """Liste toutes les catégories de produits.

    Returns:
        Liste de dictionnaires représentant les catégories
        Format: [{'id': int, 'nom': str, 'description': str, 'date_creation': str}, ...]
    """
    try:
        db = Database()
        # Vérifier que la table existe
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS categories_produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL UNIQUE,
                description TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        categories = db.fetchall(
            "SELECT id, nom, description, date_creation FROM categories_produits ORDER BY nom"
        )
        logger.info(f"{len(categories)} catégories chargées")
        return categories

    except Exception as e:
        logger.error(f"Erreur lors du chargement des catégories : {e}", exc_info=True)
        return []


def obtenir_categorie(categorie_id: int) -> dict | None:
    """Récupère une catégorie par son ID.

    Args:
        categorie_id: ID de la catégorie

    Returns:
        Dictionnaire représentant la catégorie, ou None si non trouvée
    """
    try:
        db = Database()
        categorie = db.fetchone(
            "SELECT id, nom, description, date_creation FROM categories_produits WHERE id = ?",
            (categorie_id,)
        )
        return categorie

    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la catégorie {categorie_id} : {e}", exc_info=True)
        return None
