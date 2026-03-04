"""ViewModel pour les mails enregistres."""
from PySide6.QtCore import QObject, Signal
from models.email_model import EmailModel
from typing import Optional


class MailsViewModel(QObject):
    """ViewModel pour l'onglet Mails enregistres."""

    mails_modifies = Signal()
    erreur = Signal(str)

    def __init__(self):
        super().__init__()
        self.model = EmailModel()

    def lister_mails(self) -> list[dict]:
        """Retourne tous les mails enregistres."""
        return self.model.lister_mails()

    def obtenir_mail(self, mail_id: int) -> Optional[dict]:
        """Retourne un mail par ID."""
        return self.model.obtenir_mail(mail_id)

    def creer_mail(self, nom: str, objet: str = "", contenu_html: str = "",
                   contenu_texte: str = "", type_mail: str = "template",
                   pieces_jointes: str = "") -> int:
        """Cree un nouveau mail. Retourne l'ID ou leve une exception."""
        result = self.model.creer_mail(
            nom, objet, contenu_html, contenu_texte, type_mail, pieces_jointes
        )
        self.mails_modifies.emit()
        return result

    def modifier_mail(self, mail_id: int, **kwargs) -> bool:
        """Met a jour un mail."""
        result = self.model.modifier_mail(mail_id, **kwargs)
        if result:
            self.mails_modifies.emit()
        return result

    def supprimer_mail(self, mail_id: int) -> bool:
        """Supprime un mail."""
        result = self.model.supprimer_mail(mail_id)
        if result:
            self.mails_modifies.emit()
        return result
