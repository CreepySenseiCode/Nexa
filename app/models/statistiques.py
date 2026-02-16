"""Modele pour les statistiques de ventes."""

import logging
import sqlite3

from models.base_model import BaseModel

logger = logging.getLogger(__name__)


class StatistiquesModel(BaseModel):
    """Modele pour les statistiques de ventes."""

    _table = "ventes"

    def obtenir_kpis(self, date_debut: str, date_fin: str) -> dict:
        """Retourne les KPIs pour une periode donnee.

        Returns:
            dict avec nb_ventes, ca_total, clients_actifs, panier_moyen
        """
        try:
            row = self.db.fetchone(
                """
                SELECT
                    COUNT(*) AS nb_ventes,
                    COALESCE(SUM(prix_total), 0) AS ca_total,
                    COUNT(DISTINCT client_id) AS clients_actifs
                FROM ventes
                WHERE date_vente >= ? AND date_vente <= ?
                """,
                (date_debut, date_fin),
            )
            nb_ventes = row['nb_ventes'] if row else 0
            ca_total = row['ca_total'] if row else 0
            clients_actifs = row['clients_actifs'] if row else 0
            panier_moyen = ca_total / nb_ventes if nb_ventes > 0 else 0

            logger.info(
                "KPIs pour %s -> %s : %d ventes, %.2f EUR CA, "
                "%d clients actifs, %.2f EUR panier moyen",
                date_debut, date_fin, nb_ventes, ca_total,
                clients_actifs, panier_moyen,
            )

            return {
                'nb_ventes': nb_ventes,
                'ca_total': ca_total,
                'clients_actifs': clients_actifs,
                'panier_moyen': panier_moyen,
            }
        except sqlite3.Error as e:
            logger.error("Erreur lors du calcul des KPIs : %s", e, exc_info=True)
            return {'nb_ventes': 0, 'ca_total': 0, 'clients_actifs': 0, 'panier_moyen': 0}

    def top_clients(self, date_debut: str, date_fin: str, limite: int = 5) -> list[dict]:
        """Retourne les top N clients par CA pour une periode."""
        try:
            return self.db.fetchall(
                """
                SELECT c.nom, c.prenom,
                       SUM(v.prix_total) AS total_ca,
                       COUNT(*) AS nb_achats
                FROM ventes v
                JOIN clients c ON c.id = v.client_id
                WHERE v.date_vente >= ? AND v.date_vente <= ?
                GROUP BY v.client_id
                ORDER BY total_ca DESC
                LIMIT ?
                """,
                (date_debut, date_fin, limite),
            )
        except sqlite3.Error as e:
            logger.error("Erreur lors du calcul du top clients : %s", e)
            return []

    def top_produits(self, date_debut: str, date_fin: str, limite: int = 5) -> list[dict]:
        """Retourne les top N produits par CA pour une periode."""
        try:
            return self.db.fetchall(
                """
                SELECT p.nom,
                       SUM(v.quantite) AS total_qte,
                       SUM(v.prix_total) AS total_ca
                FROM ventes v
                JOIN produits p ON p.id = v.produit_id
                WHERE v.date_vente >= ? AND v.date_vente <= ?
                GROUP BY v.produit_id
                ORDER BY total_ca DESC
                LIMIT ?
                """,
                (date_debut, date_fin, limite),
            )
        except sqlite3.Error as e:
            logger.error("Erreur lors du calcul du top produits : %s", e)
            return []

    def ventes_periode(self, date_debut: str, date_fin: str) -> list[dict]:
        """Retourne les ventes brutes pour une periode (pour graphiques)."""
        try:
            return self.db.fetchall(
                """
                SELECT date_vente, prix_total, quantite
                FROM ventes
                WHERE date_vente >= ? AND date_vente <= ?
                ORDER BY date_vente
                """,
                (date_debut, date_fin),
            )
        except sqlite3.Error as e:
            logger.error("Erreur lors de la recuperation des ventes : %s", e)
            return []
