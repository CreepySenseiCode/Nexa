"""ViewModel pour l'historique."""
from PySide6.QtCore import QObject, Signal
from models.email_recu import HistoriqueEmailModel


class HistoriqueViewModel(QObject):
    """ViewModel pour l'onglet Historique."""

    historique_charge = Signal(list)
    erreur = Signal(str)

    def __init__(self):
        super().__init__()
        self.model = HistoriqueEmailModel()

    def charger_historique(self) -> list[dict]:
        """Charge l'historique des emails envoyes."""
        historique = self.model.lister_historique()
        self.historique_charge.emit(historique)
        return historique
