"""ViewModel pour le calendrier."""
from PySide6.QtCore import QObject, Signal


class CalendrierViewModel(QObject):
    """ViewModel pour l'onglet Calendrier.

    Actuellement le calendrier ne contient pas de logique metier.
    Ce ViewModel est prepare pour de futures fonctionnalites
    (evenements, rendez-vous, etc.).
    """

    erreur = Signal(str)

    def __init__(self):
        super().__init__()
