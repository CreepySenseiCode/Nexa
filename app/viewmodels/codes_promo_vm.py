"""ViewModel pour la gestion des codes de reduction."""
from PySide6.QtCore import QObject, Signal
from models.code_reduction import CodeReductionModel
from typing import Optional


class CodesPromoViewModel(QObject):
    """ViewModel pour la gestion des codes promotionnels.

    Fournit les methodes necessaires aux vues de creation (patron)
    et de recherche (vendeur) de codes de reduction.
    """

    # Signals
    code_cree = Signal(int)        # Emet l'id du code cree
    erreur = Signal(str)           # Emet un message d'erreur
    codes_modifies = Signal()      # Emis apres modification/suppression/activation

    def __init__(self):
        super().__init__()
        self.code_reduction_model = CodeReductionModel()

    # ------------------------------------------------------------------ #
    #                          Creation (Patron)                          #
    # ------------------------------------------------------------------ #

    def creer_code(
        self,
        code: str,
        pourcentage: float,
        description: str,
        date_debut: str,
        date_fin: str,
        type_utilisation: str = 'illimite',
        limite: int = 0,
    ) -> int:
        """Cree un nouveau code de reduction.

        Args:
            code:              Le code promotionnel (ex. NOEL2026).
            pourcentage:       Le pourcentage de reduction (0 a 100).
            description:       Description optionnelle du code.
            date_debut:        Date de debut de validite (format YYYY-MM-DD).
            date_fin:          Date de fin de validite (format YYYY-MM-DD).
            type_utilisation:  'illimite', 'unique_par_client', ou 'limite_globale'.
            limite:            Nombre maximal d'utilisations (pour limite_globale).

        Returns:
            L'identifiant du code cree, ou -1 en cas d'erreur.
        """
        if not code.strip():
            self.erreur.emit("Le code ne peut pas etre vide.")
            return -1
        if pourcentage <= 0 or pourcentage > 100:
            self.erreur.emit("Le pourcentage doit etre compris entre 0 et 100.")
            return -1
        if date_fin < date_debut:
            self.erreur.emit("La date de fin doit etre posterieure a la date de debut.")
            return -1

        # Determiner la limite selon le type
        limite_val = None
        if type_utilisation == 'limite_globale' and limite > 0:
            limite_val = limite

        try:
            code_id = self.code_reduction_model.creer_code(
                code=code.strip().upper(),
                pourcentage=pourcentage,
                description=description.strip(),
                date_debut=date_debut,
                date_fin=date_fin,
                type_utilisation=type_utilisation,
                limite_utilisations=limite_val,
            )
            self.code_cree.emit(code_id)
            self.codes_modifies.emit()
            return code_id
        except Exception as e:
            self.erreur.emit(f"Erreur lors de la creation du code : {str(e)}")
            return -1

    # ------------------------------------------------------------------ #
    #                         Modification                                #
    # ------------------------------------------------------------------ #

    def modifier_code(self, code_id: int, donnees: dict) -> bool:
        """Modifie un code de reduction existant.

        Args:
            code_id: Identifiant du code a modifier.
            donnees: Dictionnaire des champs a mettre a jour.

        Returns:
            True si la modification a reussi, False sinon.
        """
        try:
            resultat = self.code_reduction_model.modifier_code(code_id, donnees)
            if resultat:
                self.codes_modifies.emit()
            return resultat
        except Exception as e:
            self.erreur.emit(f"Erreur lors de la modification : {str(e)}")
            return False

    # ------------------------------------------------------------------ #
    #                          Suppression                                #
    # ------------------------------------------------------------------ #

    def supprimer_code(self, code_id: int) -> bool:
        """Supprime un code de reduction.

        Args:
            code_id: Identifiant du code a supprimer.

        Returns:
            True si la suppression a reussi, False sinon.
        """
        try:
            resultat = self.code_reduction_model.supprimer_code(code_id)
            if resultat:
                self.codes_modifies.emit()
            return resultat
        except Exception as e:
            self.erreur.emit(f"Erreur lors de la suppression : {str(e)}")
            return False

    # ------------------------------------------------------------------ #
    #                           Listing                                   #
    # ------------------------------------------------------------------ #

    def lister_codes(self) -> list[dict]:
        """Retourne la liste de tous les codes de reduction.

        Returns:
            Liste de dictionnaires representant les codes.
        """
        try:
            return self.code_reduction_model.lister_codes()
        except Exception as e:
            self.erreur.emit(f"Erreur lors du chargement des codes : {str(e)}")
            return []

    # ------------------------------------------------------------------ #
    #                       Verification (Vendeur)                        #
    # ------------------------------------------------------------------ #

    def verifier_code(self, code: str, client_id: int = None) -> tuple:
        """Verifie si un code promo est valide et retourne ses details.

        Args:
            code:      Le code promotionnel a verifier.
            client_id: L'ID du client (pour la verification unique_par_client).

        Returns:
            Tuple (code_data, message, type_erreur).
            Si valide: (dict, message, None). Si invalide: (None, raison, type_erreur).
        """
        if not code.strip():
            return None, "Veuillez saisir un code.", "VIDE"
        try:
            return self.code_reduction_model.verifier_code(
                code.strip().upper(), client_id
            )
        except Exception as e:
            self.erreur.emit(f"Erreur lors de la verification : {str(e)}")
            return None, "Erreur lors de la verification.", "ERREUR"

    # ------------------------------------------------------------------ #
    #                     Activation / Desactivation                      #
    # ------------------------------------------------------------------ #

    def activer_desactiver(self, code_id: int, actif: bool) -> bool:
        """Active ou desactive un code de reduction.

        Args:
            code_id: Identifiant du code.
            actif:   True pour activer, False pour desactiver.

        Returns:
            True si l'operation a reussi, False sinon.
        """
        try:
            resultat = self.code_reduction_model.activer_desactiver_code(code_id, actif)
            if resultat:
                self.codes_modifies.emit()
            return resultat
        except Exception as e:
            self.erreur.emit(f"Erreur lors du changement de statut : {str(e)}")
            return False

    # ------------------------------------------------------------------ #
    #                    Enregistrement d'utilisation                     #
    # ------------------------------------------------------------------ #

    def enregistrer_utilisation(
        self, code_id: int, client_id: int, vente_id: int
    ) -> bool:
        """Enregistre l'utilisation d'un code promo lors d'une vente.

        Args:
            code_id:   Identifiant du code utilise.
            client_id: Identifiant du client ayant utilise le code.
            vente_id:  Identifiant de la vente associee.

        Returns:
            True si l'enregistrement a reussi, False sinon.
        """
        try:
            resultat = self.code_reduction_model.enregistrer_utilisation(
                code_id, client_id, vente_id
            )
            if resultat:
                self.codes_modifies.emit()
            return resultat
        except Exception as e:
            self.erreur.emit(f"Erreur lors de l'enregistrement de l'utilisation : {str(e)}")
            return False
