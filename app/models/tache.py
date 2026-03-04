"""Modèle pour la gestion des tâches."""

import logging
import sqlite3
from datetime import datetime
from typing import Optional

from models.base_model import BaseModel

logger = logging.getLogger(__name__)


class TacheModel(BaseModel):
    """Modèle pour la gestion des tâches (rappels)."""

    _table = "taches"

    def creer_tache(
        self,
        titre: str,
        description: str = "",
        priorite: int = 5,
        categorie_id: Optional[int] = None,
        date_echeance: Optional[str] = None,
        heure_echeance: Optional[str] = None,
        visibilite: str = "tous",
        commande_id: Optional[int] = None,
        couleur: Optional[str] = None,
        parent_id: Optional[int] = None,
        niveau: int = 0,
        type_recurrence: Optional[str] = None,
        intervalle_recurrence: int = 1,
        date_fin_recurrence: Optional[str] = None,
        client_id: Optional[int] = None,
        vente_id: Optional[int] = None,
        produit_id: Optional[int] = None,
        code_promo_id: Optional[int] = None,
        evenement_id: Optional[int] = None,
    ) -> int:
        try:
            cursor = self.db.execute(
                """
                INSERT INTO taches
                    (titre, description, priorite, categorie_id,
                     date_echeance, heure_echeance, visibilite, commande_id,
                     couleur, parent_id, niveau, type_recurrence,
                     intervalle_recurrence, date_fin_recurrence,
                     client_id, vente_id, produit_id, code_promo_id, evenement_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    titre,
                    description,
                    priorite,
                    categorie_id,
                    date_echeance,
                    heure_echeance,
                    visibilite,
                    commande_id,
                    couleur,
                    parent_id,
                    niveau,
                    type_recurrence,
                    intervalle_recurrence,
                    date_fin_recurrence,
                    client_id,
                    vente_id,
                    produit_id,
                    code_promo_id,
                    evenement_id,
                ),
            )
            nouveau_id = cursor.lastrowid
            logger.info("Tâche créée (ID %s) : %s", nouveau_id, titre)
            return nouveau_id
        except sqlite3.Error as e:
            logger.error("Erreur création tâche : %s", e)
            return -1

    def modifier_tache(self, tache_id: int, data: dict) -> bool:
        colonnes_autorisees = {
            "titre", "description", "priorite", "categorie_id",
            "date_echeance", "heure_echeance", "visibilite", "terminee",
            "couleur", "parent_id", "niveau", "type_recurrence",
            "intervalle_recurrence", "date_fin_recurrence",
            "supprimee", "date_suppression", "validee_admin",
            "client_id", "vente_id", "cochee",
            "produit_id", "code_promo_id", "evenement_id",
        }
        champs = {k: v for k, v in data.items() if k in colonnes_autorisees}
        if not champs:
            return False

        champs["date_modification"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sets = ", ".join(f"{k} = ?" for k in champs)
        vals = list(champs.values()) + [tache_id]

        try:
            self.db.execute(
                f"UPDATE taches SET {sets} WHERE id = ?", tuple(vals)
            )
            logger.info("Tâche %s modifiée", tache_id)
            return True
        except sqlite3.Error as e:
            logger.error("Erreur modification tâche %s : %s", tache_id, e)
            return False

    def basculer_cochee(self, tache_id: int) -> bool:
        """Toggle cochee 0↔1 pour une sous-tâche (checklist)."""
        try:
            row = self.db.fetchone(
                "SELECT cochee FROM taches WHERE id = ?", (tache_id,)
            )
            if row is None:
                return False
            nouveau = 0 if row.get("cochee") else 1
            self.db.execute(
                "UPDATE taches SET cochee = ?, date_modification = ? WHERE id = ?",
                (nouveau, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tache_id),
            )
            return True
        except sqlite3.Error as e:
            logger.error("Erreur basculer cochee tâche %s : %s", tache_id, e)
            return False

    def basculer_terminee(self, tache_id: int) -> bool:
        """Toggle terminee pour une tâche.

        - Sous-tâche : redirige vers basculer_cochee (checklist)
        - Parent terminé → cascade terminee=1 sur sous-tâches
        - Parent dé-terminé → cascade terminee=0 sur sous-tâches
        """
        try:
            row = self.db.fetchone(
                "SELECT terminee, parent_id FROM taches WHERE id = ?", (tache_id,)
            )
            if row is None:
                return False

            # Sous-tâche → checklist (cochee) au lieu de terminee
            if row.get("parent_id"):
                return self.basculer_cochee(tache_id)

            nouveau = 0 if row["terminee"] else 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.execute(
                "UPDATE taches SET terminee = ?, date_modification = ? WHERE id = ?",
                (nouveau, now, tache_id),
            )

            # Cascade sur sous-tâches
            self.db.execute(
                "UPDATE taches SET terminee = ?, date_modification = ? WHERE parent_id = ?",
                (nouveau, now, tache_id),
            )

            return True
        except sqlite3.Error as e:
            logger.error("Erreur basculer tâche %s : %s", tache_id, e)
            return False

    def lister_taches(
        self,
        visibilite_filtre: Optional[list[str]] = None,
        categorie_id: Optional[int] = None,
        inclure_terminees: bool = True,
        inclure_supprimees: bool = False,
    ) -> list[dict]:
        try:
            query = """
                SELECT t.*, ct.nom AS categorie_nom, ct.couleur AS categorie_couleur
                FROM taches t
                LEFT JOIN categories_taches ct ON ct.id = t.categorie_id
                WHERE 1=1
            """
            params: list = []

            if not inclure_supprimees:
                query += " AND (t.supprimee = 0 OR t.supprimee IS NULL)"

            if visibilite_filtre:
                placeholders = ", ".join("?" for _ in visibilite_filtre)
                query += f" AND t.visibilite IN ({placeholders})"
                params.extend(visibilite_filtre)

            if categorie_id is not None:
                query += " AND t.categorie_id = ?"
                params.append(categorie_id)

            if not inclure_terminees:
                query += " AND t.terminee = 0"

            query += " ORDER BY t.terminee, t.priorite DESC, t.date_echeance"
            return self.db.fetchall(query, tuple(params))
        except sqlite3.Error as e:
            logger.error("Erreur listing tâches : %s", e)
            return []

    def lister_taches_supprimees(
        self,
        visibilite_filtre: Optional[list[str]] = None,
    ) -> list[dict]:
        """Retourne les tâches soft-deleted."""
        try:
            query = """
                SELECT t.*, ct.nom AS categorie_nom, ct.couleur AS categorie_couleur
                FROM taches t
                LEFT JOIN categories_taches ct ON ct.id = t.categorie_id
                WHERE t.supprimee = 1
            """
            params: list = []

            if visibilite_filtre:
                placeholders = ", ".join("?" for _ in visibilite_filtre)
                query += f" AND t.visibilite IN ({placeholders})"
                params.extend(visibilite_filtre)

            query += " ORDER BY t.date_suppression DESC"
            return self.db.fetchall(query, tuple(params))
        except sqlite3.Error as e:
            logger.error("Erreur listing tâches supprimées : %s", e)
            return []

    def obtenir_taches_par_date(
        self,
        date_debut: str,
        date_fin: str,
        visibilite_filtre: Optional[list[str]] = None,
    ) -> list[dict]:
        try:
            query = """
                SELECT t.*, ct.nom AS categorie_nom, ct.couleur AS categorie_couleur
                FROM taches t
                LEFT JOIN categories_taches ct ON ct.id = t.categorie_id
                WHERE t.date_echeance >= ? AND t.date_echeance <= ?
                  AND (t.supprimee = 0 OR t.supprimee IS NULL)
            """
            params: list = [date_debut, date_fin]

            if visibilite_filtre:
                placeholders = ", ".join("?" for _ in visibilite_filtre)
                query += f" AND t.visibilite IN ({placeholders})"
                params.extend(visibilite_filtre)

            query += " ORDER BY t.date_echeance, t.heure_echeance, t.priorite DESC"
            return self.db.fetchall(query, tuple(params))
        except sqlite3.Error as e:
            logger.error("Erreur tâches par date : %s", e)
            return []

    def supprimer_tache(self, tache_id: int) -> bool:
        """Soft-delete : marque la tâche comme supprimée."""
        try:
            # Supprimer aussi les sous-tâches
            self.db.execute(
                "UPDATE taches SET supprimee = 1, date_suppression = ? WHERE parent_id = ?",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tache_id),
            )
            self.db.execute(
                "UPDATE taches SET supprimee = 1, date_suppression = ? WHERE id = ?",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tache_id),
            )
            logger.info("Tâche %s soft-deleted", tache_id)
            return True
        except sqlite3.Error as e:
            logger.error("Erreur soft-delete tâche %s : %s", tache_id, e)
            return False

    def supprimer_definitivement(self, tache_id: int) -> bool:
        """Hard-delete définitif."""
        return self.supprimer_par_id(tache_id)

    def restaurer_tache(self, tache_id: int) -> bool:
        """Restaure une tâche soft-deleted."""
        try:
            self.db.execute(
                "UPDATE taches SET supprimee = 0, date_suppression = NULL WHERE id = ?",
                (tache_id,),
            )
            # Restaurer aussi les sous-tâches
            self.db.execute(
                "UPDATE taches SET supprimee = 0, date_suppression = NULL WHERE parent_id = ?",
                (tache_id,),
            )
            logger.info("Tâche %s restaurée", tache_id)
            return True
        except sqlite3.Error as e:
            logger.error("Erreur restauration tâche %s : %s", tache_id, e)
            return False

    def lister_sous_taches(self, parent_id: int) -> list[dict]:
        """Retourne les sous-tâches d'une tâche parente."""
        try:
            return self.db.fetchall(
                """
                SELECT t.*, ct.nom AS categorie_nom, ct.couleur AS categorie_couleur
                FROM taches t
                LEFT JOIN categories_taches ct ON ct.id = t.categorie_id
                WHERE t.parent_id = ? AND (t.supprimee = 0 OR t.supprimee IS NULL)
                ORDER BY t.priorite DESC, t.titre
                """,
                (parent_id,),
            )
        except sqlite3.Error as e:
            logger.error("Erreur listing sous-tâches parent %s : %s", parent_id, e)
            return []

    def valider_mission(self, tache_id: int) -> bool:
        """Admin valide qu'une mission terminée est bien complétée."""
        try:
            self.db.execute(
                "UPDATE taches SET validee_admin = 1, date_modification = ? WHERE id = ?",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tache_id),
            )
            return True
        except sqlite3.Error as e:
            logger.error("Erreur validation mission %s : %s", tache_id, e)
            return False

    def obtenir_tache(self, tache_id: int) -> Optional[dict]:
        try:
            return self.db.fetchone(
                """
                SELECT t.*, ct.nom AS categorie_nom, ct.couleur AS categorie_couleur
                FROM taches t
                LEFT JOIN categories_taches ct ON ct.id = t.categorie_id
                WHERE t.id = ?
                """,
                (tache_id,),
            )
        except sqlite3.Error as e:
            logger.error("Erreur obtenir tâche %s : %s", tache_id, e)
            return None

    def lister_taches_parents(
        self,
        visibilite_filtre: Optional[list[str]] = None,
        max_niveau: int = 1,
    ) -> list[dict]:
        """Liste les tâches pouvant être parentes (niveau < max_niveau)."""
        try:
            query = """
                SELECT t.id, t.titre, t.niveau, t.visibilite
                FROM taches t
                WHERE t.niveau < ?
                  AND (t.supprimee = 0 OR t.supprimee IS NULL)
                  AND t.terminee = 0
            """
            params: list = [max_niveau]

            if visibilite_filtre:
                placeholders = ", ".join("?" for _ in visibilite_filtre)
                query += f" AND t.visibilite IN ({placeholders})"
                params.extend(visibilite_filtre)

            query += " ORDER BY t.titre"
            return self.db.fetchall(query, tuple(params))
        except sqlite3.Error as e:
            logger.error("Erreur listing tâches parents : %s", e)
            return []
