"""
Modèle pour la gestion des clients.

Ce module fournit la classe ClientModel qui encapsule toutes les opérations
CRUD sur la table ``clients`` ainsi que les relations (conjoint, enfants,
parents) et la configuration dynamique des champs.
"""

import logging
from datetime import datetime
from typing import Optional

from models.database import get_db

logger = logging.getLogger(__name__)


class ClientModel:
    """Modèle pour la gestion des clients.

    Toutes les opérations de lecture et d'écriture sur la table ``clients``
    et ses tables de liaison (``conjoints``, ``enfants``, ``parents_clients``)
    passent par cette classe.
    """

    def __init__(self) -> None:
        self.db = get_db()

    # ------------------------------------------------------------------
    # Création
    # ------------------------------------------------------------------

    def creer_client(self, donnees: dict) -> int:
        """Crée un nouveau client dans la base de données.

        Args:
            donnees: Dictionnaire dont les clés correspondent aux colonnes
                     de la table ``clients`` (nom, prenom, email, etc.).

        Returns:
            L'identifiant (ID) du client nouvellement créé, ou ``-1`` en
            cas d'erreur.
        """
        try:
            # Construire dynamiquement la liste des colonnes et des placeholders
            colonnes = list(donnees.keys())
            placeholders = ", ".join(["?"] * len(colonnes))
            noms_colonnes = ", ".join(colonnes)
            valeurs = tuple(donnees[col] for col in colonnes)

            query = f"INSERT INTO clients ({noms_colonnes}) VALUES ({placeholders})"
            cursor = self.db.execute(query, valeurs)

            nouveau_id = cursor.lastrowid
            logger.info("Client créé avec l'ID %s", nouveau_id)
            return nouveau_id

        except Exception as e:
            logger.error("Erreur lors de la création du client : %s", e)
            return -1

    # ------------------------------------------------------------------
    # Modification
    # ------------------------------------------------------------------

    def modifier_client(self, client_id: int, donnees: dict) -> bool:
        """Modifie un client existant.

        La colonne ``date_modification`` est automatiquement mise à jour
        avec l'horodatage courant.

        Args:
            client_id: Identifiant du client à modifier.
            donnees:   Dictionnaire des colonnes à mettre à jour.

        Returns:
            ``True`` si la modification a réussi, ``False`` sinon.
        """
        try:
            # Ajouter automatiquement la date de modification
            donnees["date_modification"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            clauses = ", ".join([f"{col} = ?" for col in donnees.keys()])
            valeurs = tuple(donnees.values()) + (client_id,)

            query = f"UPDATE clients SET {clauses} WHERE id = ?"
            self.db.execute(query, valeurs)

            logger.info("Client %s modifié avec succès", client_id)
            return True

        except Exception as e:
            logger.error(
                "Erreur lors de la modification du client %s : %s",
                client_id,
                e,
            )
            return False

    # ------------------------------------------------------------------
    # Suppression
    # ------------------------------------------------------------------

    def supprimer_client(self, client_id: int) -> bool:
        """Supprime un client de la base de données.

        Les liaisons associées (conjoints, enfants, parents) sont
        également supprimées.

        Args:
            client_id: Identifiant du client à supprimer.

        Returns:
            ``True`` si la suppression a réussi, ``False`` sinon.
        """
        try:
            # Supprimer les liaisons relationnelles
            self.db.execute(
                "DELETE FROM conjoints WHERE client_id = ? OR conjoint_client_id = ?",
                (client_id, client_id),
            )
            self.db.execute(
                "DELETE FROM enfants WHERE client_id = ? OR enfant_client_id = ?",
                (client_id, client_id),
            )
            self.db.execute(
                "DELETE FROM parents_clients WHERE client_id = ? OR parent_client_id = ?",
                (client_id, client_id),
            )

            # Supprimer le client lui-même
            self.db.execute("DELETE FROM clients WHERE id = ?", (client_id,))

            logger.info("Client %s supprimé avec succès", client_id)
            return True

        except Exception as e:
            logger.error(
                "Erreur lors de la suppression du client %s : %s",
                client_id,
                e,
            )
            return False

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    def obtenir_client(self, client_id: int) -> Optional[dict]:
        """Retourne un client par son identifiant.

        Args:
            client_id: Identifiant du client recherché.

        Returns:
            Un dictionnaire représentant le client, ou ``None`` s'il
            n'existe pas ou en cas d'erreur.
        """
        try:
            return self.db.fetchone(
                "SELECT * FROM clients WHERE id = ?", (client_id,)
            )
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération du client %s : %s",
                client_id,
                e,
            )
            return None

    def lister_clients(self) -> list[dict]:
        """Retourne la liste de tous les clients.

        Returns:
            Une liste de dictionnaires, un par client.
        """
        try:
            return self.db.fetchall(
                "SELECT * FROM clients ORDER BY nom, prenom"
            )
        except Exception as e:
            logger.error("Erreur lors du listage des clients : %s", e)
            return []

    # ------------------------------------------------------------------
    # Recherche
    # ------------------------------------------------------------------

    def rechercher_clients(self, terme: str) -> list[dict]:
        """Recherche des clients par nom, prénom, email ou téléphone.

        La recherche est insensible à la casse. Chaque mot du terme est
        recherché indépendamment et un client doit correspondre à **tous**
        les mots (logique AND).

        Args:
            terme: Chaîne de recherche (peut contenir plusieurs mots
                   séparés par des espaces).

        Returns:
            Une liste de dictionnaires correspondant aux clients trouvés.
        """
        try:
            mots = terme.strip().split()
            if not mots:
                return self.lister_clients()

            # Construire une clause WHERE avec un AND par mot
            clauses: list[str] = []
            params: list[str] = []

            for mot in mots:
                motif = f"%{mot}%"
                clauses.append(
                    "(nom LIKE ? OR prenom LIKE ? OR email LIKE ? OR telephone LIKE ?)"
                )
                params.extend([motif, motif, motif, motif])

            where = " AND ".join(clauses)
            query = f"SELECT * FROM clients WHERE {where} ORDER BY nom, prenom"

            return self.db.fetchall(query, tuple(params))

        except Exception as e:
            logger.error(
                "Erreur lors de la recherche de clients ('%s') : %s",
                terme,
                e,
            )
            return []

    # ------------------------------------------------------------------
    # Relations : Conjoint
    # ------------------------------------------------------------------

    def obtenir_conjoint(self, client_id: int) -> Optional[dict]:
        """Retourne le conjoint d'un client via la table ``conjoints``.

        Args:
            client_id: Identifiant du client dont on cherche le conjoint.

        Returns:
            Un dictionnaire représentant le conjoint, ou ``None`` si le
            client n'a pas de conjoint enregistré.
        """
        try:
            # Chercher dans les deux sens de la liaison
            liaison = self.db.fetchone(
                "SELECT conjoint_client_id FROM conjoints WHERE client_id = ?",
                (client_id,),
            )
            if liaison is None:
                liaison = self.db.fetchone(
                    "SELECT client_id AS conjoint_client_id "
                    "FROM conjoints WHERE conjoint_client_id = ?",
                    (client_id,),
                )

            if liaison is None:
                return None

            return self.db.fetchone(
                "SELECT * FROM clients WHERE id = ?",
                (liaison["conjoint_client_id"],),
            )

        except Exception as e:
            logger.error(
                "Erreur lors de la récupération du conjoint du client %s : %s",
                client_id,
                e,
            )
            return None

    def lier_conjoint(self, client_id: int, conjoint_id: int) -> bool:
        """Crée une liaison conjoint bidirectionnelle.

        Une seule ligne est insérée dans la table ``conjoints`` ; la
        méthode ``obtenir_conjoint`` gère la bidirectionnalité.

        Args:
            client_id:  Identifiant du premier client.
            conjoint_id: Identifiant du second client (conjoint).

        Returns:
            ``True`` si la liaison a été créée, ``False`` sinon.
        """
        try:
            self.db.execute(
                "INSERT INTO conjoints (client_id, conjoint_client_id) VALUES (?, ?)",
                (client_id, conjoint_id),
            )
            logger.info(
                "Liaison conjoint créée entre %s et %s",
                client_id,
                conjoint_id,
            )
            return True

        except Exception as e:
            logger.error(
                "Erreur lors de la liaison conjoint (%s <-> %s) : %s",
                client_id,
                conjoint_id,
                e,
            )
            return False

    # ------------------------------------------------------------------
    # Relations : Enfants
    # ------------------------------------------------------------------

    def obtenir_enfants(self, client_id: int) -> list[dict]:
        """Retourne les enfants d'un client via la table ``enfants``.

        Args:
            client_id: Identifiant du client parent.

        Returns:
            Une liste de dictionnaires, un par enfant.
        """
        try:
            return self.db.fetchall(
                """
                SELECT c.*, e.ordre
                FROM enfants e
                JOIN clients c ON c.id = e.enfant_client_id
                WHERE e.client_id = ?
                ORDER BY e.ordre
                """,
                (client_id,),
            )
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération des enfants du client %s : %s",
                client_id,
                e,
            )
            return []

    def lier_enfant(
        self, client_id: int, enfant_id: int, ordre: int = 1
    ) -> bool:
        """Crée une liaison parent-enfant dans la table ``enfants``.

        Args:
            client_id: Identifiant du client parent.
            enfant_id: Identifiant du client enfant.
            ordre:     Ordre de l'enfant (défaut 1).

        Returns:
            ``True`` si la liaison a été créée, ``False`` sinon.
        """
        try:
            self.db.execute(
                "INSERT INTO enfants (client_id, enfant_client_id, ordre) VALUES (?, ?, ?)",
                (client_id, enfant_id, ordre),
            )
            logger.info(
                "Liaison enfant créée : parent %s -> enfant %s (ordre %s)",
                client_id,
                enfant_id,
                ordre,
            )
            return True

        except Exception as e:
            logger.error(
                "Erreur lors de la liaison enfant (%s -> %s) : %s",
                client_id,
                enfant_id,
                e,
            )
            return False

    # ------------------------------------------------------------------
    # Relations : Parents
    # ------------------------------------------------------------------

    def obtenir_parents(self, client_id: int) -> list[dict]:
        """Retourne les parents d'un client via la table ``parents_clients``.

        Args:
            client_id: Identifiant du client dont on cherche les parents.

        Returns:
            Une liste de dictionnaires, un par parent.
        """
        try:
            return self.db.fetchall(
                """
                SELECT c.*, pc.type_parent
                FROM parents_clients pc
                JOIN clients c ON c.id = pc.parent_client_id
                WHERE pc.client_id = ?
                """,
                (client_id,),
            )
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération des parents du client %s : %s",
                client_id,
                e,
            )
            return []

    def lier_parent(
        self, client_id: int, parent_id: int, type_parent: str = ""
    ) -> bool:
        """Crée une liaison client-parent dans la table ``parents_clients``.

        Args:
            client_id:   Identifiant du client.
            parent_id:   Identifiant du client parent.
            type_parent: Type de parent (ex. « père », « mère »).

        Returns:
            ``True`` si la liaison a été créée, ``False`` sinon.
        """
        try:
            self.db.execute(
                "INSERT INTO parents_clients (client_id, parent_client_id, type_parent) "
                "VALUES (?, ?, ?)",
                (client_id, parent_id, type_parent),
            )
            logger.info(
                "Liaison parent créée : client %s -> parent %s (%s)",
                client_id,
                parent_id,
                type_parent,
            )
            return True

        except Exception as e:
            logger.error(
                "Erreur lors de la liaison parent (%s -> %s) : %s",
                client_id,
                parent_id,
                e,
            )
            return False

    # ------------------------------------------------------------------
    # Champs clients configurables
    # ------------------------------------------------------------------

    def obtenir_champs_actifs(self) -> list[dict]:
        """Retourne les champs clients actifs depuis ``champs_clients_actifs``.

        Seuls les champs dont la colonne ``actif`` vaut 1 sont retournés,
        triés par ``ordre_affichage``.

        Returns:
            Une liste de dictionnaires décrivant chaque champ actif.
        """
        try:
            return self.db.fetchall(
                "SELECT * FROM champs_clients_actifs WHERE actif = 1 "
                "ORDER BY ordre_affichage"
            )
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération des champs actifs : %s", e
            )
            return []
