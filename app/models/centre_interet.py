"""
Modèle pour la gestion des centres d'intérêt.

Ce module fournit la classe CentreInteretModel qui encapsule les opérations
CRUD sur les tables ``centres_interet`` et ``clients_centres_interet``.
"""

import logging
from typing import Optional

from models.database import get_db

logger = logging.getLogger(__name__)


class CentreInteretModel:
    """Modèle pour la gestion des centres d'intérêt.

    Gère la création, la suppression et la consultation des centres
    d'intérêt, ainsi que les liaisons entre clients et centres d'intérêt.
    """

    def __init__(self) -> None:
        self.db = get_db()

    # ------------------------------------------------------------------
    # Centres d'intérêt
    # ------------------------------------------------------------------

    def lister_tous(self) -> list[dict]:
        """Retourne tous les centres d'intérêt triés par nom.

        Returns:
            Une liste de dictionnaires, un par centre d'intérêt.
        """
        try:
            return self.db.fetchall(
                "SELECT * FROM centres_interet ORDER BY nom"
            )
        except Exception as e:
            logger.error(
                "Erreur lors du listage des centres d'intérêt : %s", e
            )
            return []

    def creer(self, nom: str) -> int:
        """Crée un nouveau centre d'intérêt.

        Si un centre portant le même nom existe déjà, son identifiant
        est retourné sans créer de doublon.

        Args:
            nom: Nom du centre d'intérêt.

        Returns:
            L'identifiant (ID) du centre créé ou existant, ou ``-1`` en
            cas d'erreur.
        """
        try:
            # Vérifier si le centre existe déjà
            existant = self.db.fetchone(
                "SELECT id FROM centres_interet WHERE nom = ?", (nom,)
            )
            if existant:
                return existant["id"]

            cursor = self.db.execute(
                "INSERT INTO centres_interet (nom) VALUES (?)", (nom,)
            )
            nouveau_id = cursor.lastrowid
            logger.info(
                "Centre d'intérêt créé : '%s' (ID %s)", nom, nouveau_id
            )
            return nouveau_id

        except Exception as e:
            logger.error(
                "Erreur lors de la création du centre d'intérêt '%s' : %s",
                nom,
                e,
            )
            return -1

    def supprimer(self, centre_id: int) -> bool:
        """Supprime un centre d'intérêt et toutes ses liaisons clients.

        Les liaisons dans ``clients_centres_interet`` sont supprimées en
        premier, puis le centre d'intérêt lui-même.

        Args:
            centre_id: Identifiant du centre d'intérêt à supprimer.

        Returns:
            ``True`` si la suppression a réussi, ``False`` sinon.
        """
        try:
            with self.db.transaction():
                # Supprimer les liaisons clients
                self.db.execute(
                    "DELETE FROM clients_centres_interet WHERE centre_interet_id = ?",
                    (centre_id,),
                )
                # Supprimer le centre d'intérêt
                self.db.execute(
                    "DELETE FROM centres_interet WHERE id = ?", (centre_id,)
                )

            logger.info(
                "Centre d'intérêt %s supprimé avec succès", centre_id
            )
            return True

        except Exception as e:
            logger.error(
                "Erreur lors de la suppression du centre d'intérêt %s : %s",
                centre_id,
                e,
            )
            return False

    # ------------------------------------------------------------------
    # Liaisons clients - centres d'intérêt
    # ------------------------------------------------------------------

    def obtenir_centres_client(self, client_id: int) -> list[dict]:
        """Retourne tous les centres d'intérêt associés à un client.

        Les centres sont récupérés via une jointure entre
        ``clients_centres_interet`` et ``centres_interet``.

        Args:
            client_id: Identifiant du client.

        Returns:
            Une liste de dictionnaires, un par centre d'intérêt.
        """
        try:
            return self.db.fetchall(
                """
                SELECT ci.*
                FROM clients_centres_interet cci
                JOIN centres_interet ci ON ci.id = cci.centre_interet_id
                WHERE cci.client_id = ?
                ORDER BY ci.nom
                """,
                (client_id,),
            )
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération des centres du client %s : %s",
                client_id,
                e,
            )
            return []

    def ajouter_centre_client(
        self, client_id: int, centre_interet_id: int
    ) -> bool:
        """Associe un centre d'intérêt à un client.

        Si la liaison existe déjà, l'opération est ignorée grâce à la
        contrainte ``UNIQUE(client_id, centre_interet_id)``.

        Args:
            client_id:         Identifiant du client.
            centre_interet_id: Identifiant du centre d'intérêt.

        Returns:
            ``True`` si la liaison a été créée, ``False`` sinon.
        """
        try:
            self.db.execute(
                """
                INSERT OR IGNORE INTO clients_centres_interet
                    (client_id, centre_interet_id)
                VALUES (?, ?)
                """,
                (client_id, centre_interet_id),
            )
            logger.info(
                "Centre d'intérêt %s associé au client %s",
                centre_interet_id,
                client_id,
            )
            return True

        except Exception as e:
            logger.error(
                "Erreur lors de l'association du centre %s au client %s : %s",
                centre_interet_id,
                client_id,
                e,
            )
            return False

    def retirer_centre_client(
        self, client_id: int, centre_interet_id: int
    ) -> bool:
        """Retire l'association entre un centre d'intérêt et un client.

        Args:
            client_id:         Identifiant du client.
            centre_interet_id: Identifiant du centre d'intérêt.

        Returns:
            ``True`` si la liaison a été supprimée, ``False`` sinon.
        """
        try:
            self.db.execute(
                """
                DELETE FROM clients_centres_interet
                WHERE client_id = ? AND centre_interet_id = ?
                """,
                (client_id, centre_interet_id),
            )
            logger.info(
                "Centre d'intérêt %s retiré du client %s",
                centre_interet_id,
                client_id,
            )
            return True

        except Exception as e:
            logger.error(
                "Erreur lors du retrait du centre %s du client %s : %s",
                centre_interet_id,
                client_id,
                e,
            )
            return False

    def definir_centres_client(
        self, client_id: int, noms_centres: list[str]
    ) -> bool:
        """Remplace tous les centres d'intérêt d'un client.

        Les anciennes liaisons sont supprimées, puis chaque centre de la
        liste est créé s'il n'existe pas encore et associé au client.

        Args:
            client_id:    Identifiant du client.
            noms_centres: Liste des noms de centres d'intérêt à associer.

        Returns:
            ``True`` si l'opération a réussi, ``False`` sinon.
        """
        try:
            with self.db.transaction():
                # Supprimer toutes les liaisons existantes
                self.db.execute(
                    "DELETE FROM clients_centres_interet WHERE client_id = ?",
                    (client_id,),
                )

                # Créer et associer chaque centre
                for nom in noms_centres:
                    centre_id = self.creer(nom)
                    if centre_id == -1:
                        logger.error(
                            "Impossible de créer le centre '%s' pour le client %s",
                            nom,
                            client_id,
                        )
                        continue
                    self.ajouter_centre_client(client_id, centre_id)

            logger.info(
                "Centres d'intérêt redéfinis pour le client %s (%d centres)",
                client_id,
                len(noms_centres),
            )
            return True

        except Exception as e:
            logger.error(
                "Erreur lors de la redéfinition des centres du client %s : %s",
                client_id,
                e,
            )
            return False
