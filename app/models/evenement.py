"""Modèle pour les événements calendrier."""

import logging
from typing import Optional

from models.base_model import BaseModel

logger = logging.getLogger(__name__)


class EvenementModel(BaseModel):
    """CRUD pour la table evenements_calendrier."""

    _table = "evenements_calendrier"

    def creer_evenement(
        self,
        nom: str,
        description: str = "",
        couleur: str = "#FF9800",
        date_debut: str = "",
        date_fin: str = "",
    ) -> int:
        try:
            return self.db.execute(
                "INSERT INTO evenements_calendrier (nom, description, couleur, date_debut, date_fin) "
                "VALUES (?, ?, ?, ?, ?)",
                (nom, description, couleur, date_debut, date_fin),
            )
        except Exception as e:
            logger.error("Erreur création événement : %s", e)
            return 0

    def lister_evenements(
        self, date_debut: str = "", date_fin: str = ""
    ) -> list[dict]:
        """Liste les événements dont la plage chevauche [date_debut, date_fin]."""
        try:
            if date_debut and date_fin:
                return self.db.fetchall(
                    "SELECT * FROM evenements_calendrier "
                    "WHERE date_debut <= ? AND date_fin >= ? "
                    "ORDER BY date_debut",
                    (date_fin, date_debut),
                )
            return self.db.fetchall(
                "SELECT * FROM evenements_calendrier ORDER BY date_debut"
            )
        except Exception as e:
            logger.error("Erreur liste événements : %s", e)
            return []

    def modifier_evenement(self, evenement_id: int, data: dict) -> bool:
        colonnes_autorisees = {"nom", "description", "couleur", "date_debut", "date_fin"}
        sets = []
        vals = []
        for k, v in data.items():
            if k in colonnes_autorisees:
                sets.append(f"{k} = ?")
                vals.append(v)
        if not sets:
            return False
        vals.append(evenement_id)
        try:
            self.db.execute(
                f"UPDATE evenements_calendrier SET {', '.join(sets)} WHERE id = ?",
                tuple(vals),
            )
            return True
        except Exception as e:
            logger.error("Erreur modification événement : %s", e)
            return False

    def obtenir_evenement(self, evenement_id: int) -> Optional[dict]:
        return self.obtenir_par_id(evenement_id)

    def supprimer_evenement(self, evenement_id: int) -> bool:
        try:
            self.db.execute(
                "DELETE FROM evenements_calendrier WHERE id = ?",
                (evenement_id,),
            )
            return True
        except Exception as e:
            logger.error("Erreur suppression événement : %s", e)
            return False
