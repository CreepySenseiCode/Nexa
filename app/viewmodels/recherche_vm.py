"""ViewModel pour la recherche de clients."""
from PySide6.QtCore import QObject, Signal
from models.client import ClientModel
from models.vente import VenteModel
from models.parametres import ParametresModel
from typing import Optional


class RechercheViewModel(QObject):
    """ViewModel pour l'onglet Recherche."""

    # Signals
    client_selectionne = Signal(dict)  # Emet les données du client
    erreur = Signal(str)

    def __init__(self):
        super().__init__()
        self.client_model = ClientModel()
        self.vente_model = VenteModel()
        self.params_model = ParametresModel()

    def rechercher_clients(self, terme: str) -> list[dict]:
        """Recherche des clients. Retourne la liste des clients correspondants."""
        if not terme.strip():
            return []
        return self.client_model.rechercher_clients(terme)

    def charger_profil_client(self, client_id: int) -> Optional[dict]:
        """Charge le profil complet d'un client avec toutes ses relations.
        Retourne un dict avec :
        - Tous les champs du client
        - 'conjoint': dict ou None
        - 'enfants': liste de dicts
        - 'parents': liste de dicts
        - 'stats': dict avec les statistiques d'achat
        """
        client = self.client_model.obtenir_client(client_id)
        if not client:
            return None

        # Construire le dict du profil complet (copie pour ne pas modifier l'original)
        profil = dict(client)
        profil['conjoint'] = self.client_model.obtenir_conjoint(client_id)
        profil['enfants'] = self.client_model.obtenir_enfants(client_id)
        profil['parents'] = self.client_model.obtenir_parents(client_id)
        profil['stats'] = self.vente_model.obtenir_stats_client(client_id)

        self.client_selectionne.emit(profil)
        return profil

    def obtenir_symbole_monnaie(self) -> str:
        """Retourne le symbole de la monnaie."""
        return self.params_model.obtenir_symbole_monnaie()

    def obtenir_historique_complet(self, client_id: int) -> list[dict]:
        """Retourne l'historique d'achat complet d'un client (sans limite)."""
        return self.vente_model.obtenir_ventes_client(client_id, limite=0)

    def obtenir_depenses_client(self, client_id: int) -> list[dict]:
        """Retourne les ventes d'un client pour le graphique."""
        return self.vente_model.obtenir_depenses_client(client_id)

    def obtenir_repartition_categories(self, client_id: int) -> list[dict]:
        """Retourne la repartition par categorie pour un client."""
        return self.vente_model.obtenir_repartition_categories(client_id)
