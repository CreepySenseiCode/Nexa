"""Vue unifiee des emails : Reception, Envoyes, Brouillons avec toggle."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget,
)
from PySide6.QtCore import Qt, Signal

from utils.styles import style_toggle, style_bouton, Couleurs
from views.boite_reception_view import BoiteReceptionView
from views.historique_mails_view import HistoriqueMailsView
from views.mails_enregistres_view import MailsEnregistresView


class EmailsUnifieView(QWidget):
    """Vue unifiee combinant reception, envoyes et brouillons."""

    # Signal emis quand l'utilisateur clique sur "+" pour un nouvel email
    nouveau_mail_demande = Signal()

    PAGE_RECEPTION = 0
    PAGE_ENVOYES = 1
    PAGE_BROUILLONS = 2
    PAGE_TEMPLATES = 3

    def __init__(self):
        super().__init__()
        self._construire_ui()

    def _construire_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === BARRE DE TOGGLE ===
        barre = QWidget()
        barre.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        barre_layout = QHBoxLayout(barre)
        barre_layout.setContentsMargins(30, 15, 30, 0)
        barre_layout.setSpacing(10)

        titre = QLabel("Emails")
        titre.setStyleSheet(
            f"font-size: 20pt; font-weight: bold; color: {Couleurs.PRIMAIRE};"
        )
        barre_layout.addWidget(titre)
        barre_layout.addStretch()

        self.btn_reception = QPushButton("Reception")
        self.btn_reception.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reception.clicked.connect(lambda: self._changer(self.PAGE_RECEPTION))

        self.btn_envoyes = QPushButton("Envoyes")
        self.btn_envoyes.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_envoyes.clicked.connect(lambda: self._changer(self.PAGE_ENVOYES))

        self.btn_brouillons = QPushButton("Brouillons")
        self.btn_brouillons.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_brouillons.clicked.connect(lambda: self._changer(self.PAGE_BROUILLONS))

        self.btn_templates = QPushButton("📋 Templates")
        self.btn_templates.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_templates.clicked.connect(lambda: self._changer(self.PAGE_TEMPLATES))

        barre_layout.addWidget(self.btn_reception)
        barre_layout.addWidget(self.btn_envoyes)
        barre_layout.addWidget(self.btn_brouillons)
        barre_layout.addWidget(self.btn_templates)

        # Bouton "+" nouveau mail
        btn_nouveau = QPushButton("+")
        btn_nouveau.setFixedSize(40, 40)
        btn_nouveau.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nouveau.setStyleSheet(style_bouton(Couleurs.SUCCES))
        btn_nouveau.clicked.connect(self.nouveau_mail_demande.emit)
        barre_layout.addWidget(btn_nouveau)

        layout.addWidget(barre)

        # === STACKED WIDGET ===
        self.pile = QStackedWidget()

        self.vue_reception = BoiteReceptionView()
        self.vue_envoyes = HistoriqueMailsView()
        self.vue_brouillons = MailsEnregistresView()
        self.vue_templates = MailsEnregistresView()  # Vue séparée pour templates

        self.pile.addWidget(self.vue_reception)
        self.pile.addWidget(self.vue_envoyes)
        self.pile.addWidget(self.vue_brouillons)
        self.pile.addWidget(self.vue_templates)

        layout.addWidget(self.pile)

        self._changer(self.PAGE_RECEPTION)

    def _changer(self, index: int):
        """Change la sous-vue affichee."""
        self.pile.setCurrentIndex(index)
        self.btn_reception.setStyleSheet(style_toggle(index == self.PAGE_RECEPTION))
        self.btn_envoyes.setStyleSheet(style_toggle(index == self.PAGE_ENVOYES))
        self.btn_brouillons.setStyleSheet(style_toggle(index == self.PAGE_BROUILLONS))
        self.btn_templates.setStyleSheet(style_toggle(index == self.PAGE_TEMPLATES))
