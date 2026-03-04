"""Modèle pour la gestion des commandes."""

import logging
import sqlite3
from datetime import datetime
from typing import Optional

from models.base_model import BaseModel

logger = logging.getLogger(__name__)


class CommandeModel(BaseModel):
    """Modèle pour la gestion des commandes clients."""

    _table = "commandes"

    def creer_commande(
        self,
        client_id: int,
        date_prevue: str,
        heure_prevue: Optional[str] = None,
        notes: str = "",
        total: float = 0.0,
    ) -> int:
        try:
            cursor = self.db.execute(
                """
                INSERT INTO commandes
                    (client_id, date_prevue, heure_prevue, notes, total)
                VALUES (?, ?, ?, ?, ?)
                """,
                (client_id, date_prevue, heure_prevue, notes, total),
            )
            nouveau_id = cursor.lastrowid
            logger.info("Commande créée (ID %s) pour client %s", nouveau_id, client_id)
            return nouveau_id
        except sqlite3.Error as e:
            logger.error("Erreur création commande : %s", e)
            return -1

    def ajouter_article(
        self,
        commande_id: int,
        produit_id: int,
        quantite: int,
        prix_unitaire: float,
    ) -> int:
        prix_total = round(quantite * prix_unitaire, 2)
        try:
            cursor = self.db.execute(
                """
                INSERT INTO articles_commande
                    (commande_id, produit_id, quantite, prix_unitaire, prix_total)
                VALUES (?, ?, ?, ?, ?)
                """,
                (commande_id, produit_id, quantite, prix_unitaire, prix_total),
            )
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error("Erreur ajout article commande : %s", e)
            return -1

    def obtenir_commande(self, commande_id: int) -> Optional[dict]:
        try:
            commande = self.db.fetchone(
                """
                SELECT c.*, cl.nom AS client_nom, cl.prenom AS client_prenom,
                       cl.email AS client_email
                FROM commandes c
                JOIN clients cl ON cl.id = c.client_id
                WHERE c.id = ?
                """,
                (commande_id,),
            )
            if not commande:
                return None

            articles = self.db.fetchall(
                """
                SELECT ac.*, p.nom AS produit_nom, p.photo AS produit_photo
                FROM articles_commande ac
                JOIN produits p ON p.id = ac.produit_id
                WHERE ac.commande_id = ?
                ORDER BY ac.id
                """,
                (commande_id,),
            )

            taches = self.db.fetchall(
                """
                SELECT t.*, ct.nom AS categorie_nom, ct.couleur AS categorie_couleur
                FROM taches t
                LEFT JOIN categories_taches ct ON ct.id = t.categorie_id
                WHERE t.commande_id = ?
                ORDER BY t.priorite, t.titre
                """,
                (commande_id,),
            )

            commande["articles"] = articles
            commande["taches"] = taches
            commande["total"] = sum(a["prix_total"] for a in articles)
            return commande
        except sqlite3.Error as e:
            logger.error("Erreur obtenir commande %s : %s", commande_id, e)
            return None

    def lister_commandes(self, statut: Optional[str] = None) -> list[dict]:
        try:
            query = """
                SELECT
                    c.id,
                    c.client_id,
                    cl.nom AS client_nom,
                    cl.prenom AS client_prenom,
                    c.date_prevue,
                    c.heure_prevue,
                    c.statut,
                    c.total,
                    c.notes,
                    c.date_commande,
                    COUNT(ac.id) AS nb_articles,
                    GROUP_CONCAT(p.nom || ' x' || ac.quantite, ', ')
                        AS articles_resume
                FROM commandes c
                JOIN clients cl ON cl.id = c.client_id
                LEFT JOIN articles_commande ac ON ac.commande_id = c.id
                LEFT JOIN produits p ON p.id = ac.produit_id
            """
            params = ()
            if statut:
                query += " WHERE c.statut = ?"
                params = (statut,)

            query += " GROUP BY c.id ORDER BY c.date_prevue DESC"
            return self.db.fetchall(query, params)
        except sqlite3.Error as e:
            logger.error("Erreur lister commandes : %s", e)
            return []

    def modifier_statut(self, commande_id: int, statut: str) -> bool:
        try:
            self.db.execute(
                "UPDATE commandes SET statut = ? WHERE id = ?",
                (statut, commande_id),
            )
            logger.info("Commande %s → statut '%s'", commande_id, statut)
            return True
        except sqlite3.Error as e:
            logger.error("Erreur modifier statut commande %s : %s", commande_id, e)
            return False

    def supprimer_commande(self, commande_id: int) -> bool:
        try:
            with self.db.transaction():
                self.db.execute(
                    "DELETE FROM taches WHERE commande_id = ?", (commande_id,)
                )
                self.db.execute(
                    "DELETE FROM articles_commande WHERE commande_id = ?",
                    (commande_id,),
                )
                self.db.execute(
                    "DELETE FROM commandes WHERE id = ?", (commande_id,)
                )
            logger.info("Commande %s supprimée", commande_id)
            return True
        except sqlite3.Error as e:
            logger.error("Erreur suppression commande %s : %s", commande_id, e)
            return False

    def obtenir_commandes_par_date(
        self, date_debut: str, date_fin: str
    ) -> list[dict]:
        try:
            return self.db.fetchall(
                """
                SELECT c.id, c.client_id, cl.nom AS client_nom,
                       cl.prenom AS client_prenom,
                       c.date_prevue, c.heure_prevue, c.statut, c.total
                FROM commandes c
                JOIN clients cl ON cl.id = c.client_id
                WHERE c.date_prevue >= ? AND c.date_prevue <= ?
                ORDER BY c.date_prevue, c.heure_prevue
                """,
                (date_debut, date_fin),
            )
        except sqlite3.Error as e:
            logger.error("Erreur commandes par date : %s", e)
            return []

    def obtenir_articles_commande(self, commande_id: int) -> list[dict]:
        try:
            return self.db.fetchall(
                """
                SELECT ac.*, p.nom AS produit_nom
                FROM articles_commande ac
                JOIN produits p ON p.id = ac.produit_id
                WHERE ac.commande_id = ?
                ORDER BY ac.id
                """,
                (commande_id,),
            )
        except sqlite3.Error as e:
            logger.error("Erreur articles commande %s : %s", commande_id, e)
            return []

    def mettre_a_jour_total(self, commande_id: int) -> bool:
        try:
            row = self.db.fetchone(
                "SELECT COALESCE(SUM(prix_total), 0) AS total "
                "FROM articles_commande WHERE commande_id = ?",
                (commande_id,),
            )
            total = row["total"] if row else 0.0
            self.db.execute(
                "UPDATE commandes SET total = ? WHERE id = ?",
                (total, commande_id),
            )
            return True
        except sqlite3.Error as e:
            logger.error("Erreur MAJ total commande %s : %s", commande_id, e)
            return False
