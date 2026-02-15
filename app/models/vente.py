"""
Modèle pour la gestion des ventes.

Ce module fournit la classe VenteModel qui encapsule les opérations de
création, de lecture et de statistiques sur la table ``ventes``.
"""

import logging
from datetime import datetime
from typing import Optional

import sqlite3

from models.database import get_db

logger = logging.getLogger(__name__)


class VenteModel:
    """Modèle pour la gestion des ventes.

    Gère l'enregistrement des ventes, la consultation de l'historique
    par client et le calcul de statistiques d'achat.
    """

    def __init__(self) -> None:
        self.db = get_db()

    # ------------------------------------------------------------------
    # Création
    # ------------------------------------------------------------------

    def creer_vente(
        self,
        client_id: int,
        produit_id: int,
        quantite: int,
        prix_unitaire: float,
        prix_total: float,
        date_vente: Optional[str] = None,
        notes: str = "",
    ) -> int:
        """Enregistre une nouvelle vente dans la base de données.

        Args:
            client_id:     Identifiant du client acheteur.
            produit_id:    Identifiant du produit vendu.
            quantite:      Nombre d'unités vendues.
            prix_unitaire: Prix d'une unité du produit.
            prix_total:    Montant total de la vente.
            date_vente:    Date de la vente au format ``YYYY-MM-DD HH:MM:SS``.
                           Si ``None``, la date courante est utilisée.
            notes:         Notes optionnelles associées à la vente.

        Returns:
            L'identifiant (ID) de la vente créée, ou ``-1`` en cas
            d'erreur.
        """
        try:
            if date_vente is None:
                date_vente = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor = self.db.execute(
                """
                INSERT INTO ventes
                    (client_id, produit_id, quantite, prix_unitaire,
                     prix_total, date_vente, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    client_id,
                    produit_id,
                    quantite,
                    prix_unitaire,
                    prix_total,
                    date_vente,
                    notes,
                ),
            )

            nouveau_id = cursor.lastrowid
            logger.info(
                "Vente créée (ID %s) : client %s, produit %s, total %.2f",
                nouveau_id,
                client_id,
                produit_id,
                prix_total,
            )
            return nouveau_id

        except sqlite3.Error as e:
            logger.error("Erreur lors de la création de la vente : %s", e)
            return -1

    # ------------------------------------------------------------------
    # Lecture par client
    # ------------------------------------------------------------------

    def obtenir_ventes_client(
        self, client_id: int, limite: int = 5
    ) -> list[dict]:
        """Retourne les dernières ventes d'un client.

        Les ventes sont triées par date décroissante et limitées au
        nombre spécifié. Le nom du produit est inclus via une jointure
        avec la table ``produits``.

        Args:
            client_id: Identifiant du client.
            limite:    Nombre maximal de ventes retournées (défaut 5).

        Returns:
            Une liste de dictionnaires, un par vente.
        """
        try:
            # LIMIT -1 = pas de limite en SQLite
            sql_limite = limite if limite > 0 else -1
            return self.db.fetchall(
                """
                SELECT v.*, p.nom AS produit_nom
                FROM ventes v
                JOIN produits p ON p.id = v.produit_id
                WHERE v.client_id = ?
                ORDER BY v.date_vente DESC
                LIMIT ?
                """,
                (client_id, sql_limite),
            )
        except sqlite3.Error as e:
            logger.error(
                "Erreur lors de la récupération des ventes du client %s : %s",
                client_id,
                e,
            )
            return []

    # ------------------------------------------------------------------
    # Statistiques
    # ------------------------------------------------------------------

    def obtenir_stats_client(self, client_id: int) -> dict:
        """Retourne les statistiques d'achat d'un client.

        Les statistiques calculées sont :
        - ``nombre_achats`` : nombre total de ventes.
        - ``montant_total`` : somme des montants.
        - ``produit_prefere`` : nom du produit le plus acheté.
        - ``categorie_preferee`` : nom de la catégorie la plus achetée.
        - ``dernier_achat`` : date de la dernière vente.

        Args:
            client_id: Identifiant du client.

        Returns:
            Un dictionnaire contenant les statistiques. Les valeurs sont
            à ``None`` (ou 0) si le client n'a aucun achat.
        """
        stats: dict = {
            "nombre_achats": 0,
            "montant_total": 0.0,
            "produit_prefere": None,
            "categorie_preferee": None,
            "dernier_achat": None,
        }

        try:
            # --- Agrégats globaux ---
            row = self.db.fetchone(
                """
                SELECT
                    COUNT(*)        AS nombre_achats,
                    COALESCE(SUM(prix_total), 0) AS montant_total,
                    MAX(date_vente) AS dernier_achat
                FROM ventes
                WHERE client_id = ?
                """,
                (client_id,),
            )

            if row is None or row["nombre_achats"] == 0:
                return stats

            stats["nombre_achats"] = row["nombre_achats"]
            stats["montant_total"] = row["montant_total"]
            stats["dernier_achat"] = row["dernier_achat"]

            # --- Produit préféré (le plus acheté en quantité) ---
            produit_row = self.db.fetchone(
                """
                SELECT p.nom
                FROM ventes v
                JOIN produits p ON p.id = v.produit_id
                WHERE v.client_id = ?
                GROUP BY v.produit_id
                ORDER BY SUM(v.quantite) DESC
                LIMIT 1
                """,
                (client_id,),
            )
            if produit_row:
                stats["produit_prefere"] = produit_row["nom"]

            # --- Catégorie préférée (la plus achetée en quantité) ---
            categorie_row = self.db.fetchone(
                """
                SELECT cp.nom
                FROM ventes v
                JOIN produits p ON p.id = v.produit_id
                JOIN categories_produits cp ON cp.id = p.categorie_id
                WHERE v.client_id = ?
                GROUP BY p.categorie_id
                ORDER BY SUM(v.quantite) DESC
                LIMIT 1
                """,
                (client_id,),
            )
            if categorie_row:
                stats["categorie_preferee"] = categorie_row["nom"]

            return stats

        except sqlite3.Error as e:
            logger.error(
                "Erreur lors du calcul des stats du client %s : %s",
                client_id,
                e,
            )
            return stats

    # ------------------------------------------------------------------
    # Données pour graphiques
    # ------------------------------------------------------------------

    def obtenir_depenses_client(self, client_id: int) -> list[dict]:
        """Retourne les ventes d'un client avec date et prix_total."""
        try:
            return self.db.fetchall(
                """
                SELECT date(date_vente) as date_vente, prix_total
                FROM ventes
                WHERE client_id = ?
                ORDER BY date_vente
                """,
                (client_id,),
            )
        except sqlite3.Error as e:
            logger.error("Erreur depenses client %s : %s", client_id, e)
            return []

    def obtenir_repartition_categories(self, client_id: int) -> list[dict]:
        """Retourne la repartition des achats par categorie pour un client."""
        try:
            return self.db.fetchall(
                """
                SELECT
                    COALESCE(cp.nom, 'Sans categorie') as categorie,
                    SUM(v.prix_total) as total,
                    COUNT(*) as nombre
                FROM ventes v
                JOIN produits p ON v.produit_id = p.id
                LEFT JOIN categories_produits cp ON p.categorie_id = cp.id
                WHERE v.client_id = ?
                GROUP BY cp.id, cp.nom
                ORDER BY total DESC
                """,
                (client_id,),
            )
        except sqlite3.Error as e:
            logger.error("Erreur repartition categories client %s : %s", client_id, e)
            return []

    # ------------------------------------------------------------------
    # Listing général
    # ------------------------------------------------------------------

    def lister_ventes(
        self,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
    ) -> list[dict]:
        """Retourne toutes les ventes, optionnellement filtrées par date.

        Les résultats incluent le nom du client et le nom du produit
        via des jointures.

        Args:
            date_debut: Date de début du filtre (format ``YYYY-MM-DD``).
                        Si ``None``, aucune borne inférieure.
            date_fin:   Date de fin du filtre (format ``YYYY-MM-DD``).
                        Si ``None``, aucune borne supérieure.

        Returns:
            Une liste de dictionnaires, un par vente.
        """
        try:
            query = """
                SELECT v.*,
                       c.nom   AS client_nom,
                       c.prenom AS client_prenom,
                       p.nom   AS produit_nom
                FROM ventes v
                JOIN clients  c ON c.id = v.client_id
                JOIN produits p ON p.id = v.produit_id
            """

            conditions: list[str] = []
            params: list[str] = []

            if date_debut is not None:
                conditions.append("v.date_vente >= ?")
                params.append(date_debut)

            if date_fin is not None:
                conditions.append("v.date_vente <= ?")
                params.append(date_fin)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY v.date_vente DESC"

            return self.db.fetchall(query, tuple(params))

        except sqlite3.Error as e:
            logger.error(
                "Erreur lors du listage des ventes : %s", e
            )
            return []
