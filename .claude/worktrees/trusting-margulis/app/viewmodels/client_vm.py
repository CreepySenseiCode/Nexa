"""ViewModel pour la gestion des clients."""
from PySide6.QtCore import QObject, Signal
from models.client import ClientModel
from utils.formatters import formater_nom, formater_prenom, calculer_age
from utils.validators import valider_email, valider_telephone, valider_code_postal
from typing import Optional


class ClientViewModel(QObject):
    """ViewModel pour l'onglet Client."""

    # Signals
    client_sauvegarde = Signal(int)  # Emet l'id du client
    erreur = Signal(str)  # Emet le message d'erreur
    champs_charges = Signal(list)  # Emet la liste des dicts de champs actifs

    def __init__(self):
        super().__init__()
        self.model = ClientModel()
        self._client_actuel_id: Optional[int] = None

    def lister_clients(self) -> list[dict]:
        """Retourne tous les clients."""
        return self.model.lister_clients()

    def rechercher_clients(self, terme: str) -> list[dict]:
        """Recherche des clients par nom/prenom."""
        if not terme or len(terme) < 1:
            return self.lister_clients()
        tous = self.model.lister_clients()
        terme_lower = terme.lower()
        return [
            c for c in tous
            if terme_lower in (c.get('nom', '') or '').lower()
            or terme_lower in (c.get('prenom', '') or '').lower()
            or terme_lower in (c.get('email', '') or '').lower()
        ]

    def charger_champs_actifs(self) -> list[dict]:
        """Charge et retourne les champs clients actifs."""
        champs = self.model.obtenir_champs_actifs()
        self.champs_charges.emit(champs)
        return champs

    def sauvegarder_client(self, donnees: dict) -> Optional[int]:
        """Sauvegarde un client (création ou modification).

        - Format name to UPPERCASE
        - Format prenom to capitalize
        - Calculate age from date_naissance if provided
        - Validate email if provided
        - Validate telephone if provided
        - If self._client_actuel_id is set, update; otherwise create
        - Emit client_sauvegarde signal with client_id on success
        - Emit erreur signal on failure
        - Returns client_id or None
        """
        # Formater les données
        if 'nom' in donnees and donnees['nom']:
            donnees['nom'] = formater_nom(donnees['nom'])
        if 'prenom' in donnees and donnees['prenom']:
            donnees['prenom'] = formater_prenom(donnees['prenom'])

        # Valider les champs obligatoires
        if not donnees.get('nom') or not donnees.get('prenom'):
            self.erreur.emit("Le nom et le prénom sont obligatoires.")
            return None

        # Valider l'email
        if donnees.get('email') and not valider_email(donnees['email']):
            self.erreur.emit("L'adresse email n'est pas valide.")
            return None

        # Calculer l'âge
        if donnees.get('date_naissance'):
            try:
                donnees['age'] = calculer_age(donnees['date_naissance'])
            except Exception:
                donnees['age'] = None

        try:
            if self._client_actuel_id:
                self.model.modifier_client(self._client_actuel_id, donnees)
                client_id = self._client_actuel_id
            else:
                client_id = self.model.creer_client(donnees)

            self.client_sauvegarde.emit(client_id)
            return client_id
        except Exception as e:
            self.erreur.emit(f"Erreur lors de la sauvegarde : {str(e)}")
            return None

    def creer_client_lie(self, donnees: dict, type_relation: str, client_principal_id: int) -> Optional[int]:
        """Crée un client lié (conjoint, enfant, parent) et établit la relation.

        type_relation: 'conjoint', 'enfant', 'parent'
        """
        donnees['type_relation'] = type_relation

        # Formater les données
        if 'nom' in donnees and donnees['nom']:
            donnees['nom'] = formater_nom(donnees['nom'])
        if 'prenom' in donnees and donnees['prenom']:
            donnees['prenom'] = formater_prenom(donnees['prenom'])
        if donnees.get('date_naissance'):
            try:
                donnees['age'] = calculer_age(donnees['date_naissance'])
            except Exception:
                donnees['age'] = None

        try:
            nouveau_id = self.model.creer_client(donnees)
            if type_relation == 'conjoint':
                self.model.lier_conjoint(client_principal_id, nouveau_id)
            elif type_relation == 'enfant':
                self.model.lier_enfant(client_principal_id, nouveau_id)
            elif type_relation == 'parent':
                self.model.lier_parent(client_principal_id, nouveau_id)
            return nouveau_id
        except Exception as e:
            self.erreur.emit(f"Erreur lors de la création du client lié : {str(e)}")
            return None

    def charger_client(self, client_id: int) -> Optional[dict]:
        """Charge un client pour édition."""
        client = self.model.obtenir_client(client_id)
        if client:
            self._client_actuel_id = client_id
        return client

    def nouveau_client(self):
        """Réinitialise pour un nouveau client."""
        self._client_actuel_id = None

    def calculer_completude_profil(self, donnees: dict) -> int:
        """Calcule le pourcentage de complétude du profil (0-100).
        Compte le nombre de champs remplis par rapport au total des champs actifs."""
        champs = self.model.obtenir_champs_actifs()
        if not champs:
            return 0
        total = len(champs)
        remplis = 0
        for champ in champs:
            nom = champ['nom_champ']
            val = donnees.get(nom)
            if val is not None and val != '' and val != 0 and val != False:
                remplis += 1
        return int((remplis / total) * 100) if total > 0 else 0
