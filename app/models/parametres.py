"""
Modèle pour la gestion des paramètres de l'application.

Ce module fournit la classe ParametresModel qui encapsule les opérations
de lecture et d'écriture sur la table ``parametres``.
"""

import logging
from typing import Optional

from models.database import get_db

logger = logging.getLogger(__name__)


class ParametresModel:
    """Modèle pour la gestion des paramètres de l'application.

    Les paramètres sont stockés sous forme de paires clé/valeur dans la
    table ``parametres``. Cette classe offre des accesseurs simples pour
    lire et modifier ces valeurs.
    """

    def __init__(self) -> None:
        self.db = get_db()

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    def obtenir_parametre(self, cle: str) -> Optional[str]:
        """Retourne la valeur d'un paramètre par sa clé.

        Args:
            cle: Clé du paramètre recherché.

        Returns:
            La valeur du paramètre sous forme de chaîne, ou ``None``
            si la clé n'existe pas ou en cas d'erreur.
        """
        try:
            row = self.db.fetchone(
                "SELECT valeur FROM parametres WHERE cle = ?", (cle,)
            )
            if row is not None:
                return row["valeur"]
            return None

        except Exception as e:
            logger.error(
                "Erreur lors de la lecture du paramètre '%s' : %s", cle, e
            )
            return None

    def obtenir_tous_parametres(self) -> dict:
        """Retourne tous les paramètres sous forme de dictionnaire.

        Returns:
            Un dictionnaire ``{cle: valeur}`` contenant l'ensemble des
            paramètres enregistrés.
        """
        try:
            rows = self.db.fetchall("SELECT cle, valeur FROM parametres")
            return {row["cle"]: row["valeur"] for row in rows}

        except Exception as e:
            logger.error(
                "Erreur lors de la récupération de tous les paramètres : %s", e
            )
            return {}

    # ------------------------------------------------------------------
    # Écriture
    # ------------------------------------------------------------------

    def definir_parametre(self, cle: str, valeur: str) -> bool:
        """Définit ou met à jour la valeur d'un paramètre.

        Utilise ``INSERT OR REPLACE`` pour créer le paramètre s'il
        n'existe pas encore ou mettre à jour sa valeur sinon.

        Args:
            cle:    Clé du paramètre.
            valeur: Nouvelle valeur à enregistrer.

        Returns:
            ``True`` si l'opération a réussi, ``False`` sinon.
        """
        try:
            self.db.execute(
                "INSERT OR REPLACE INTO parametres (cle, valeur) VALUES (?, ?)",
                (cle, valeur),
            )
            logger.info("Paramètre '%s' défini à '%s'", cle, valeur)
            return True

        except Exception as e:
            logger.error(
                "Erreur lors de la définition du paramètre '%s' : %s", cle, e
            )
            return False

    # ------------------------------------------------------------------
    # Raccourcis utilitaires
    # ------------------------------------------------------------------

    def obtenir_symbole_monnaie(self) -> str:
        """Retourne le symbole de la monnaie configurée.

        Consulte le paramètre ``symbole_monnaie``. Si celui-ci n'est
        pas défini, retourne le symbole par défaut ``'€'``.

        Returns:
            Le symbole de la monnaie sous forme de chaîne.
        """
        symbole = self.obtenir_parametre("symbole_monnaie")
        return symbole if symbole is not None else "€"
