"""ViewModel pour les statistiques."""
from PySide6.QtCore import QObject, Signal
from models.statistiques import StatistiquesModel


class StatsViewModel(QObject):
    """ViewModel pour l'onglet Statistiques."""

    donnees_chargees = Signal(dict)
    erreur = Signal(str)

    def __init__(self):
        super().__init__()
        self.model = StatistiquesModel()

    def charger_statistiques(self, date_debut: str, date_fin: str) -> dict:
        """Charge toutes les stats pour une periode et retourne un dict complet."""
        try:
            donnees = {
                'kpis': self.model.obtenir_kpis(date_debut, date_fin),
                'top_clients': self.model.top_clients(date_debut, date_fin),
                'top_produits': self.model.top_produits(date_debut, date_fin),
                'ventes': self.model.ventes_periode(date_debut, date_fin),
            }
            self.donnees_chargees.emit(donnees)
            return donnees
        except Exception as e:
            self.erreur.emit(f"Erreur lors du chargement des statistiques : {e}")
            return {}
