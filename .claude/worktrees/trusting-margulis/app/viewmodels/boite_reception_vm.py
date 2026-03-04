"""ViewModel pour la boite de reception."""
from PySide6.QtCore import QObject, Signal
from models.email_recu import EmailRecuModel


class BoiteReceptionViewModel(QObject):
    """ViewModel pour l'onglet Boite de reception."""

    emails_charges = Signal(list)
    erreur = Signal(str)

    def __init__(self):
        super().__init__()
        self.model = EmailRecuModel()

    def charger_emails(self, adresse: str = None) -> list[dict]:
        """Charge les emails. Si adresse est None ou 'Toutes les boites', charge tout."""
        filtre = None
        if adresse and adresse != "Toutes les bo\u00eetes":
            filtre = adresse
        emails = self.model.lister_emails(filtre)
        self.emails_charges.emit(emails)
        return emails
