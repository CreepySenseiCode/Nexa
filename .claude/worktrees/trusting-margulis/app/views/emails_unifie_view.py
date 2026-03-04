"""Vue unifiee des emails : Reception, Envoyes, Brouillons avec toggle."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QTabWidget,
)
from PySide6.QtCore import Qt, Signal

from utils.styles import style_toggle, style_bouton, Couleurs
from views.boite_reception_view import BoiteReceptionView
from views.historique_mails_view import HistoriqueMailsView
from views.mails_enregistres_view import MailsEnregistresView
from views.emailing_view import EmailingView


class EmailsUnifieView(QWidget):
    """Vue unifiee combinant reception, envoyes et brouillons."""

    # Signal emis quand l'utilisateur clique sur "+" pour un nouvel email
    nouveau_mail_demande = Signal()

    PAGE_RECEPTION = 0
    PAGE_ENVOYES = 1
    PAGE_BROUILLONS = 2
    PAGE_TEMPLATES = 3
    PAGE_COMPOSITION = 4

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

        self.btn_composition = QPushButton("✉️ Rédiger")
        self.btn_composition.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_composition.clicked.connect(lambda: self._changer(self.PAGE_COMPOSITION))

        barre_layout.addWidget(self.btn_reception)
        barre_layout.addWidget(self.btn_envoyes)
        barre_layout.addWidget(self.btn_brouillons)
        barre_layout.addWidget(self.btn_templates)
        barre_layout.addWidget(self.btn_composition)

        # Bouton "+" nouveau mail (ajoute un nouveau tab)
        self.btn_nouveau = QPushButton("➕")
        self.btn_nouveau.setFixedSize(40, 40)
        self.btn_nouveau.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nouveau.setStyleSheet(style_bouton(Couleurs.SUCCES))
        self.btn_nouveau.clicked.connect(self._ajouter_tab_composition)
        barre_layout.addWidget(self.btn_nouveau)

        layout.addWidget(barre)

        # === STACKED WIDGET ===
        self.pile = QStackedWidget()

        self.vue_reception = BoiteReceptionView()
        self.vue_envoyes = HistoriqueMailsView()
        # Vue Brouillons (filtrée sur brouillons uniquement)
        self.vue_brouillons = MailsEnregistresView(mode="brouillons")
        # Vue Templates (filtrée sur templates uniquement)
        self.vue_templates = MailsEnregistresView(mode="templates")

        # Vue Composition (QTabWidget pour emails multiples)
        self.tabs_composition = QTabWidget()
        self.tabs_composition.setTabsClosable(True)
        self.tabs_composition.setMovable(True)
        self.tabs_composition.tabCloseRequested.connect(self._fermer_tab_composition)
        self.tabs_composition.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #9E9E9E; }"
            "QTabBar::tab { min-width: 150px; padding: 8px; }"
        )

        self.pile.addWidget(self.vue_reception)
        self.pile.addWidget(self.vue_envoyes)
        self.pile.addWidget(self.vue_brouillons)
        self.pile.addWidget(self.vue_templates)
        self.pile.addWidget(self.tabs_composition)

        layout.addWidget(self.pile)

        self._changer(self.PAGE_RECEPTION)

    def _changer(self, index: int):
        """Change la sous-vue affichee."""
        self.pile.setCurrentIndex(index)
        self.btn_reception.setStyleSheet(style_toggle(index == self.PAGE_RECEPTION))
        self.btn_envoyes.setStyleSheet(style_toggle(index == self.PAGE_ENVOYES))
        self.btn_brouillons.setStyleSheet(style_toggle(index == self.PAGE_BROUILLONS))
        self.btn_templates.setStyleSheet(style_toggle(index == self.PAGE_TEMPLATES))
        self.btn_composition.setStyleSheet(style_toggle(index == self.PAGE_COMPOSITION))

    def _ajouter_tab_composition(self):
        """Ajoute un nouveau tab de composition d'email."""
        # Basculer vers la page composition
        self._changer(self.PAGE_COMPOSITION)

        # Créer une nouvelle instance d'EmailingView
        emailing_view = EmailingView()

        # Ajouter le tab
        index = self.tabs_composition.addTab(emailing_view, f"Nouvel email {self.tabs_composition.count() + 1}")

        # Sélectionner le nouveau tab
        self.tabs_composition.setCurrentIndex(index)

        # Connecter les signaux (si EmailingView a des signaux pour enregistrer/envoyer)
        # emailing_view.email_envoye.connect(lambda: self._on_email_envoye(index))
        # emailing_view.brouillon_sauve.connect(lambda: self._on_brouillon_sauve(index))

    def _fermer_tab_composition(self, index: int):
        """Ferme un tab de composition."""
        widget = self.tabs_composition.widget(index)
        if widget:
            self.tabs_composition.removeTab(index)
            widget.deleteLater()

        # Si plus de tabs, retourner à la réception
        if self.tabs_composition.count() == 0:
            self._changer(self.PAGE_RECEPTION)
