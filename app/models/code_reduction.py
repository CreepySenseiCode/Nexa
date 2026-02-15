"""
Modèle pour la gestion des codes de réduction.

Ce module fournit la classe CodeReductionModel qui encapsule les opérations
CRUD sur les tables ``codes_reduction`` et ``utilisations_codes``.
"""

import logging
from datetime import date
from typing import Optional

from models.database import get_db

logger = logging.getLogger(__name__)


class CodeReductionModel:
    """Modèle pour la gestion des codes de réduction.

    Gère la création, la modification, la suppression, la validation et
    le suivi d'utilisation des codes promotionnels.
    """

    def __init__(self) -> None:
        self.db = get_db()

    # ------------------------------------------------------------------
    # Création
    # ------------------------------------------------------------------

    def creer_code(
        self,
        code: str,
        pourcentage: float,
        description: str,
        date_debut: str,
        date_fin: str,
        type_utilisation: str = 'illimite',
        limite_utilisations: Optional[int] = None,
    ) -> int:
        """Crée un nouveau code de réduction.

        Le code est automatiquement converti en majuscules avant
        l'insertion.

        Args:
            code:                 Code promotionnel (texte unique).
            pourcentage:          Pourcentage de réduction à appliquer.
            description:          Description du code promotionnel.
            date_debut:           Date de début de validité (``YYYY-MM-DD``).
            date_fin:             Date de fin de validité (``YYYY-MM-DD``).
            type_utilisation:     Type d'utilisation : 'illimite',
                                  'unique_par_client' ou 'limite_globale'.
            limite_utilisations:  Nombre maximal d'utilisations autorisées
                                  (utilisé uniquement si type == 'limite_globale').

        Returns:
            L'identifiant (ID) du code créé, ou ``-1`` en cas d'erreur.
        """
        try:
            cursor = self.db.execute(
                """
                INSERT INTO codes_reduction
                    (code, pourcentage, description, date_debut,
                     date_fin, type_utilisation, limite_utilisations)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    code.upper(),
                    pourcentage,
                    description,
                    date_debut,
                    date_fin,
                    type_utilisation,
                    limite_utilisations,
                ),
            )
            nouveau_id = cursor.lastrowid
            logger.info(
                "Code de réduction créé : '%s' (ID %s)", code.upper(), nouveau_id
            )
            return nouveau_id

        except Exception as e:
            logger.error(
                "Erreur lors de la création du code '%s' : %s", code, e
            )
            return -1

    # ------------------------------------------------------------------
    # Modification
    # ------------------------------------------------------------------

    def modifier_code(self, code_id: int, donnees: dict) -> bool:
        """Modifie un code de réduction existant.

        Args:
            code_id: Identifiant du code à modifier.
            donnees: Dictionnaire des colonnes à mettre à jour.

        Returns:
            ``True`` si la modification a réussi, ``False`` sinon.
        """
        try:
            if not donnees:
                return False

            clauses = ", ".join([f"{col} = ?" for col in donnees.keys()])
            valeurs = tuple(donnees.values()) + (code_id,)

            query = f"UPDATE codes_reduction SET {clauses} WHERE id = ?"
            self.db.execute(query, valeurs)

            logger.info("Code de réduction %s modifié avec succès", code_id)
            return True

        except Exception as e:
            logger.error(
                "Erreur lors de la modification du code %s : %s",
                code_id,
                e,
            )
            return False

    # ------------------------------------------------------------------
    # Suppression
    # ------------------------------------------------------------------

    def supprimer_code(self, code_id: int) -> bool:
        """Supprime un code de réduction de la base de données.

        Args:
            code_id: Identifiant du code à supprimer.

        Returns:
            ``True`` si la suppression a réussi, ``False`` sinon.
        """
        try:
            self.db.execute(
                "DELETE FROM codes_reduction WHERE id = ?", (code_id,)
            )
            logger.info("Code de réduction %s supprimé avec succès", code_id)
            return True

        except Exception as e:
            logger.error(
                "Erreur lors de la suppression du code %s : %s",
                code_id,
                e,
            )
            return False

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    def lister_codes(self) -> list[dict]:
        """Retourne tous les codes de réduction triés par date de création.

        Returns:
            Une liste de dictionnaires, un par code de réduction.
        """
        try:
            return self.db.fetchall(
                "SELECT * FROM codes_reduction ORDER BY date_creation DESC"
            )
        except Exception as e:
            logger.error(
                "Erreur lors du listage des codes de réduction : %s", e
            )
            return []

    def obtenir_code(self, code_id: int) -> Optional[dict]:
        """Retourne un code de réduction par son identifiant.

        Args:
            code_id: Identifiant du code recherché.

        Returns:
            Un dictionnaire représentant le code, ou ``None`` s'il
            n'existe pas ou en cas d'erreur.
        """
        try:
            return self.db.fetchone(
                "SELECT * FROM codes_reduction WHERE id = ?", (code_id,)
            )
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération du code %s : %s",
                code_id,
                e,
            )
            return None

    # ------------------------------------------------------------------
    # Vérification de validité
    # ------------------------------------------------------------------

    def verifier_code(self, code: str, client_id: Optional[int] = None) -> tuple:
        """Vérifie qu'un code promotionnel est valide et utilisable.

        Effectue des vérifications séquentielles et retourne un message
        d'erreur détaillé en cas d'échec.

        Args:
            code:      Code promotionnel à vérifier (insensible à la casse).
            client_id: Identifiant du client (nécessaire pour le type
                       ``unique_par_client``).

        Returns:
            Un tuple ``(code_data, message, type_erreur)``.

            Types d'erreur possibles :
                - ``None`` : Code valide
                - ``"INEXISTANT"`` : Le code n'existe pas
                - ``"DESACTIVE"`` : Le code a été désactivé
                - ``"PAS_ENCORE_VALIDE"`` : Le code n'est pas encore valide
                - ``"EXPIRE"`` : Le code a expiré
                - ``"DEJA_UTILISE"`` : Le client a déjà utilisé ce code
                - ``"CLIENT_REQUIS"`` : Client nécessaire pour ce type de code
                - ``"EPUISE"`` : Limite d'utilisations atteinte
        """
        try:
            code_upper = code.upper()

            # 1. Le code existe-t-il ?
            resultat = self.db.fetchone(
                "SELECT * FROM codes_reduction WHERE code = ?",
                (code_upper,),
            )
            if resultat is None:
                return (
                    None,
                    f"Le code '{code_upper}' n'existe pas dans la base de donn\u00e9es.",
                    "INEXISTANT",
                )

            # 2. Est-il actif ?
            if not resultat.get('actif'):
                return (
                    None,
                    f"Le code '{code_upper}' a \u00e9t\u00e9 d\u00e9sactiv\u00e9 par l'administrateur.",
                    "DESACTIVE",
                )

            # 3. Est-il dans la période de validité ?
            aujourd_hui = date.today().strftime("%Y-%m-%d")
            date_debut = resultat.get('date_debut', '')
            date_fin = resultat.get('date_fin', '')

            if date_debut and aujourd_hui < date_debut:
                return (
                    None,
                    f"Ce code ne sera valide qu'\u00e0 partir du {date_debut}.",
                    "PAS_ENCORE_VALIDE",
                )
            if date_fin and aujourd_hui > date_fin:
                return (
                    None,
                    f"Ce code a expir\u00e9 le {date_fin}.",
                    "EXPIRE",
                )

            # 4. Vérifications selon le type d'utilisation
            type_util = resultat.get('type_utilisation', 'illimite')

            if type_util == 'unique_par_client':
                if client_id is None:
                    # Pas de client fourni : le code est valide en soi
                    pass
                else:
                    deja_utilise = self.db.fetchone(
                        "SELECT id FROM utilisations_codes WHERE code_id = ? AND client_id = ?",
                        (resultat['id'], client_id),
                    )
                    if deja_utilise:
                        return (
                            None,
                            f"Vous avez d\u00e9j\u00e0 utilis\u00e9 le code '{code_upper}'.",
                            "DEJA_UTILISE",
                        )

            elif type_util == 'limite_globale':
                limite = resultat.get('limite_utilisations')
                nb_util = resultat.get('nombre_utilisations', 0)
                if limite is not None and nb_util >= limite:
                    return (
                        None,
                        f"Le code '{code_upper}' a atteint sa limite d'utilisations "
                        f"({limite} utilisations maximum).",
                        "EPUISE",
                    )

            # 5. Code valide !
            from datetime import datetime
            today = date.today()
            if date_fin:
                try:
                    fin = datetime.strptime(date_fin, "%Y-%m-%d").date()
                    jours_restants = (fin - today).days
                    message = (
                        f"Code valide ! R\u00e9duction de {resultat['pourcentage']}%.\n"
                        f"Expire dans {jours_restants} jour{'s' if jours_restants > 1 else ''}."
                    )
                except ValueError:
                    message = f"Code valide ! R\u00e9duction de {resultat['pourcentage']}%."
            else:
                message = f"Code valide ! R\u00e9duction de {resultat['pourcentage']}%."

            return (resultat, message, None)

        except Exception as e:
            logger.error(
                "Erreur lors de la vérification du code '%s' : %s", code, e
            )
            return (None, "Erreur lors de la v\u00e9rification du code.", "ERREUR")

    # ------------------------------------------------------------------
    # Activation / Désactivation
    # ------------------------------------------------------------------

    def activer_desactiver_code(self, code_id: int, actif: bool) -> bool:
        """Active ou désactive un code de réduction.

        Args:
            code_id: Identifiant du code à modifier.
            actif:   ``True`` pour activer, ``False`` pour désactiver.

        Returns:
            ``True`` si la modification a réussi, ``False`` sinon.
        """
        try:
            self.db.execute(
                "UPDATE codes_reduction SET actif = ? WHERE id = ?",
                (1 if actif else 0, code_id),
            )
            etat = "activé" if actif else "désactivé"
            logger.info("Code de réduction %s %s", code_id, etat)
            return True

        except Exception as e:
            logger.error(
                "Erreur lors de l'activation/désactivation du code %s : %s",
                code_id,
                e,
            )
            return False

    # ------------------------------------------------------------------
    # Utilisations
    # ------------------------------------------------------------------

    def enregistrer_utilisation(
        self, code_id: int, client_id: int, vente_id: int
    ) -> bool:
        """Enregistre l'utilisation d'un code de réduction.

        Une entrée est ajoutée dans ``utilisations_codes`` et le compteur
        ``nombre_utilisations`` du code est incrémenté de 1.

        Args:
            code_id:   Identifiant du code utilisé.
            client_id: Identifiant du client ayant utilisé le code.
            vente_id:  Identifiant de la vente associée.

        Returns:
            ``True`` si l'enregistrement a réussi, ``False`` sinon.
        """
        try:
            # Insérer l'utilisation
            self.db.execute(
                """
                INSERT INTO utilisations_codes (code_id, client_id, vente_id)
                VALUES (?, ?, ?)
                """,
                (code_id, client_id, vente_id),
            )

            # Incrémenter le compteur d'utilisations
            self.db.execute(
                """
                UPDATE codes_reduction
                SET nombre_utilisations = nombre_utilisations + 1
                WHERE id = ?
                """,
                (code_id,),
            )

            logger.info(
                "Utilisation du code %s enregistrée (client %s, vente %s)",
                code_id,
                client_id,
                vente_id,
            )
            return True

        except Exception as e:
            logger.error(
                "Erreur lors de l'enregistrement de l'utilisation du code %s : %s",
                code_id,
                e,
            )
            return False

    def obtenir_utilisations(self, code_id: int) -> list[dict]:
        """Retourne toutes les utilisations d'un code de réduction.

        Les résultats incluent les informations du client et de la vente
        via des jointures.

        Args:
            code_id: Identifiant du code de réduction.

        Returns:
            Une liste de dictionnaires, un par utilisation.
        """
        try:
            return self.db.fetchall(
                """
                SELECT uc.*,
                       c.nom    AS client_nom,
                       c.prenom AS client_prenom,
                       v.prix_total AS vente_montant
                FROM utilisations_codes uc
                JOIN clients c ON c.id = uc.client_id
                JOIN ventes v  ON v.id = uc.vente_id
                WHERE uc.code_id = ?
                ORDER BY uc.date_utilisation DESC
                """,
                (code_id,),
            )
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération des utilisations du code %s : %s",
                code_id,
                e,
            )
            return []
