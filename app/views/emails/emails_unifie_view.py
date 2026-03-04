"""Vue unifiee des emails : Reception, Envoyes, Brouillons avec toggle."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QTabWidget,
)
from PySide6.QtCore import Qt, Signal

from utils.styles import style_bouton, Couleurs
from views.components.modern_segmented_control import ModernSegmentedControl
from views.emails.boite_reception_view import BoiteReceptionView
from views.emails.historique_mails_view import HistoriqueMailsView
from views.emails.mails_enregistres_view import MailsEnregistresView
from views.emails.emailing_view import EmailingView


class EmailsUnifieView(QWidget):
    """Vue unifiee combinant reception, envoyes et brouillons."""

    # Signal emis quand l'utilisateur clique sur "+" pour un nouvel email
    nouveau_mail_demande = Signal()

    PAGE_RECEPTION = 0
    PAGE_ENVOYES = 1
    PAGE_BROUILLONS = 2
    PAGE_TEMPLATES = 3
    PAGE_COMPOSITION = 4

    def __init__(self, parent=None):  # ← parent=None par défaut
        super().__init__(parent)
        self._construire_ui()

    def _construire_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === SEGMENTED CONTROL ===
        self._barre_toggle = ModernSegmentedControl(
            ["Réception", "Envoyés", "Brouillons", "Templates", "Rédiger"]
        )
        self._barre_toggle.selectionChanged.connect(self._changer)

        # Bouton "+" nouveau mail (action rapide, hors du toggle)
        self.btn_nouveau = QPushButton("➕")
        self.btn_nouveau.setFixedSize(40, 40)
        self.btn_nouveau.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nouveau.setStyleSheet(style_bouton(Couleurs.SUCCES))
        self.btn_nouveau.clicked.connect(self._ajouter_tab_composition)

        layout_haut = QHBoxLayout()
        layout_haut.setContentsMargins(16, 16, 16, 8)
        layout_haut.addStretch(1)
        layout_haut.addWidget(self._barre_toggle)
        layout_haut.addStretch(1)
        layout_haut.addWidget(self.btn_nouveau)

        layout.addLayout(layout_haut)

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

        # Connecter "Utiliser template" des deux vues
        self.vue_templates.utiliser_template_demande.connect(self._utiliser_template)
        self.vue_brouillons.utiliser_template_demande.connect(self._utiliser_template)

        self.pile.addWidget(self.vue_reception)
        self.pile.addWidget(self.vue_envoyes)
        self.pile.addWidget(self.vue_brouillons)
        self.pile.addWidget(self.vue_templates)
        self.pile.addWidget(self.tabs_composition)

        layout.addWidget(self.pile)

        self.btn_nouveau.setVisible(False)
        self._changer(self.PAGE_RECEPTION)

    def _changer(self, index: int):
        """Change la sous-vue affichee."""
        self.pile.setCurrentIndex(index)
        if self._barre_toggle.current_index != index:
            self._barre_toggle.select(index)
        # Bouton "+" visible uniquement sur la page Rédiger
        self.btn_nouveau.setVisible(index == self.PAGE_COMPOSITION)

    def _ajouter_tab_composition(self):
        """Ajoute un nouveau tab de composition d'email."""
        # Basculer vers la page composition
        self._changer(self.PAGE_COMPOSITION)

        # Créer une nouvelle instance d'EmailingView
        emailing_view = EmailingView()

        # Ajouter le tab
        index = self.tabs_composition.addTab(
            emailing_view, f"Nouvel email {self.tabs_composition.count() + 1}"
        )

        # Sélectionner le nouveau tab
        self.tabs_composition.setCurrentIndex(index)

        # Connecter les signaux
        emailing_view.email_envoye.connect(lambda idx=index: self._on_email_envoye(idx))
        emailing_view.brouillon_sauve.connect(
            lambda idx=index: self._on_brouillon_sauve(idx)
        )

    def _on_email_envoye(self, tab_index: int):
        """Apres envoi reussi : fermer le tab et rafraichir l'historique."""
        self._fermer_tab_composition(tab_index)
        self.vue_envoyes._charger_historique()
        self._changer(self.PAGE_ENVOYES)

    def _on_brouillon_sauve(self, tab_index: int):
        """Apres sauvegarde brouillon : rafraichir la liste brouillons."""
        self.vue_brouillons._charger_templates()

    def _fermer_tab_composition(self, index: int):
        """Ferme un tab de composition."""
        widget = self.tabs_composition.widget(index)
        if widget:
            self.tabs_composition.removeTab(index)
            widget.deleteLater()

        # Si plus de tabs, retourner a la reception
        if self.tabs_composition.count() == 0:
            self._changer(self.PAGE_RECEPTION)

    def _utiliser_template(self, mail_data: dict):
        """Cree un nouveau tab de composition pre-rempli avec le template."""
        self._changer(self.PAGE_COMPOSITION)

        emailing_view = EmailingView()
        tab_name = mail_data.get("nom_mail", "Email")[:25]
        index = self.tabs_composition.addTab(emailing_view, tab_name)
        self.tabs_composition.setCurrentIndex(index)

        # Pre-remplir
        emailing_view.input_objet.setText(mail_data.get("objet", ""))
        contenu_html = mail_data.get("contenu_html", "")
        if contenu_html:
            emailing_view.text_message.setHtml(contenu_html)
        else:
            emailing_view.text_message.setPlainText(mail_data.get("contenu_texte", ""))

        # Connecter signaux
        emailing_view.email_envoye.connect(lambda idx=index: self._on_email_envoye(idx))
        emailing_view.brouillon_sauve.connect(
            lambda idx=index: self._on_brouillon_sauve(idx)
        )
