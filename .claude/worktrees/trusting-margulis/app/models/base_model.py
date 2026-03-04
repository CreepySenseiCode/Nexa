"""Classe de base pour les modeles de donnees."""

import logging
import sqlite3
from typing import Optional

from models.database import get_db

logger = logging.getLogger(__name__)


class BaseModel:
    """Classe de base fournissant les operations CRUD generiques.

    Les sous-classes doivent definir ``_table`` pour beneficier des
    methodes generiques ``obtenir_par_id``, ``supprimer_par_id`` et
    ``compter``.
    """

    _table: str = ""

    def __init__(self) -> None:
        self.db = get_db()

    def obtenir_par_id(self, record_id: int) -> Optional[dict]:
        """Retourne un enregistrement par son ID, ou None."""
        if not self._table:
            raise NotImplementedError("_table non defini")
        try:
            return self.db.fetchone(
                f"SELECT * FROM {self._table} WHERE id = ?",
                (record_id,),
            )
        except sqlite3.Error as e:
            logger.error("Erreur obtenir_par_id(%s, %s) : %s", self._table, record_id, e)
            return None

    def supprimer_par_id(self, record_id: int) -> bool:
        """Supprime un enregistrement par son ID."""
        if not self._table:
            raise NotImplementedError("_table non defini")
        try:
            self.db.execute(
                f"DELETE FROM {self._table} WHERE id = ?",
                (record_id,),
            )
            return True
        except sqlite3.Error as e:
            logger.error("Erreur supprimer_par_id(%s, %s) : %s", self._table, record_id, e)
            return False

    def compter(self) -> int:
        """Retourne le nombre d'enregistrements dans la table."""
        if not self._table:
            raise NotImplementedError("_table non defini")
        try:
            row = self.db.fetchone(f"SELECT COUNT(*) AS total FROM {self._table}")
            return row["total"] if row else 0
        except sqlite3.Error as e:
            logger.error("Erreur compter(%s) : %s", self._table, e)
            return 0
