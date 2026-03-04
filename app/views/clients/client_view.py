"""Vue pour l'onglet Client - Formulaire de creation/edition d'un client.

Ce module fournit la classe ClientView qui constitue l'interface graphique
pour la saisie et la modification des informations d'un client. La vue
communique avec le ClientViewModel selon le pattern MVVM.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QPushButton,
    QStackedWidget,
    QFrame,
)
from PySide6.QtCore import Qt, Signal

from viewmodels.client_vm import ClientViewModel
from utils.styles import style_input, Couleurs
from views.components.modern_segmented_control import ModernSegmentedControl
from views.clients.formulaire_client_base import FormulaireClientBase
from views.clients.fiche_client_view import FicheClientView
from viewmodels.recherche_vm import RechercheViewModel


class ClientView(QWidget):
    """Vue principale pour la gestion d'un client (creation/edition).

    Contient un toggle Liste/Creation et un QStackedWidget pour
    alterner entre la liste des clients et le formulaire.
    """

    # --- Signaux ---
    client_sauvegarde = Signal(int)  # Re-emet l'id du client sauvegarde
    demande_edition_client = Signal(int)  # Demande d'edition d'un client

    def __init__(self, viewmodel=None, parent=None):  # ← parent=None par défaut
        super().__init__(parent)
        # Si le viewmodel n'est pas fourni, on en cree un
        self.viewmodel = viewmodel if viewmodel is not None else ClientViewModel()

        # Construire l'interface
        self._construire_ui()

    # ==================================================================
    # Construction de l'interface
    # ==================================================================

    # Pages du stacked widget
    PAGE_LISTE = 0
    PAGE_CREATION = 1

    def _construire_ui(self):
        """Construit l'interface complete avec toggle Liste/Creation."""

        # --- Layout principal ---
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # === SEGMENTED CONTROL ===
        self._barre_toggle = ModernSegmentedControl(["Liste", "Nouveau client"])
        self._barre_toggle.selectionChanged.connect(self._changer_page_client)

        layout_haut = QHBoxLayout()
        layout_haut.setContentsMargins(24, 16, 24, 8)
        layout_haut.addStretch(1)
        layout_haut.addWidget(self._barre_toggle)
        layout_haut.addStretch(1)

        layout_principal.addLayout(layout_haut)

        # === STACKED WIDGET ===
        self.pile_client = QStackedWidget()

        # Page 0 : Liste des clients
        self.pile_client.addWidget(self._creer_page_liste_clients())

        # Page 1 : Formulaire creation/edition
        self.pile_client.addWidget(self._creer_page_formulaire())

        layout_principal.addWidget(self.pile_client)

        # Charger la liste des clients au démarrage
        self._charger_liste_clients()

    def _changer_page_client(self, index: int):
        """Change la page affichee."""
        self.pile_client.setCurrentIndex(index)
        if self._barre_toggle.current_index != index:
            self._barre_toggle.select(index)
        if index == self.PAGE_LISTE:
            self._charger_liste_clients()

    # ------------------------------------------------------------------
    # Page Liste
    # ------------------------------------------------------------------

    def _creer_page_liste_clients(self) -> QWidget:
        """Crée la page Liste avec recherche + résultats + fiche inline."""
        page = QWidget()
        page.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(8)

        # --- Zone LISTE ---
        self.widget_liste_clients = QWidget()
        layout_liste = QVBoxLayout(self.widget_liste_clients)
        layout_liste.setContentsMargins(0, 0, 0, 0)
        layout_liste.setSpacing(8)

        # Barre de recherche
        self.input_recherche_client = QLineEdit()
        self.input_recherche_client.setPlaceholderText("🔍 Rechercher un client...")
        self.input_recherche_client.setStyleSheet(style_input())
        self.input_recherche_client.textChanged.connect(self._charger_liste_clients)
        layout_liste.addWidget(self.input_recherche_client)

        # Label nombre resultats
        self.label_nb_clients = QLabel()
        self.label_nb_clients.setStyleSheet(
            "color: #7f8c8d; font-size: 11pt; padding: 5px 0;"
        )
        layout_liste.addWidget(self.label_nb_clients)

        # Widget de resultats avec cartes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        from views.components.client_card import SearchResultsWidget

        self.widget_resultats = SearchResultsWidget()

        # Connexions : simple clic = sélection, double-clic = ouvrir fiche
        self.widget_resultats.client_selected.connect(self._on_client_selected)
        self.widget_resultats.client_double_clicked.connect(
            self._on_client_double_clicked
        )

        scroll.setWidget(self.widget_resultats)
        layout_liste.addWidget(scroll, stretch=1)

        layout.addWidget(self.widget_liste_clients, stretch=1)

        # --- Zone PROFIL (cachée par défaut) ---
        # FicheClientView gère son propre scroll en interne → pas de QScrollArea externe
        self.widget_profil_client = QWidget()
        layout_profil_wrapper = QVBoxLayout(self.widget_profil_client)
        layout_profil_wrapper.setContentsMargins(0, 0, 0, 0)
        layout_profil_wrapper.setSpacing(0)

        # Bouton retour
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(16, 10, 16, 4)
        self.btn_retour_liste_clients = QPushButton("← Retour à la liste")
        self.btn_retour_liste_clients.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_retour_liste_clients.clicked.connect(self._retour_liste_clients)
        top_bar.addWidget(self.btn_retour_liste_clients)
        top_bar.addStretch()
        layout_profil_wrapper.addLayout(top_bar)

        self.profil_client_widget = FicheClientView()
        layout_profil_wrapper.addWidget(self.profil_client_widget, stretch=1)

        self.widget_profil_client.hide()
        layout.addWidget(self.widget_profil_client, stretch=1)

        return page

    def _charger_liste_clients(self):
        """Charge les clients dans les cartes."""
        terme = ""
        search_terms = []
        if hasattr(self, "input_recherche_client"):
            terme = self.input_recherche_client.text().strip()

        if terme:
            clients = self.viewmodel.rechercher_clients(terme)
            search_terms = terme.split()
            if hasattr(self, "label_nb_clients"):
                self.label_nb_clients.setText(f"{len(clients)} résultat(s)")
        else:
            clients = self.viewmodel.lister_clients()
            if hasattr(self, "label_nb_clients"):
                self.label_nb_clients.setText(f"{len(clients)} client(s)")

        # Afficher dans le widget de cartes
        if hasattr(self, "widget_resultats"):
            self.widget_resultats.afficher_resultats(clients, search_terms)

    def _retour_liste_clients(self):
        """Retour de la fiche vers la liste."""
        if hasattr(self, "widget_profil_client") and hasattr(
            self, "widget_liste_clients"
        ):
            self.widget_profil_client.hide()
            self.widget_liste_clients.show()

    def _afficher_fiche_client(self, profil: dict):
        """Affiche la fiche client dans l'onglet Client (comme Recherche)."""
        if not hasattr(self, "profil_client_widget"):
            return
        from viewmodels.recherche_vm import RechercheViewModel

        vm_recherche = RechercheViewModel()
        self.profil_client_widget.set_symbole_monnaie(
            vm_recherche.obtenir_symbole_monnaie()
        )
        self.profil_client_widget.afficher_profil(profil)

        self.widget_liste_clients.hide()
        self.widget_profil_client.show()

    def _on_client_selected(self, client_id: int):
        """Gere la selection d'un client (simple clic) - feedback visuel uniquement."""
        pass

    def _on_client_double_clicked(self, client_id: int):
        """
        Double-clic dans la liste de l’onglet Client :
        ouvre la même fiche client que l’onglet Recherche, en lecture seule,
        dans le toggle Liste (pas dans une nouvelle fenêtre).
        """
        from viewmodels.recherche_vm import RechercheViewModel

        recherche_vm = RechercheViewModel()
        profil = recherche_vm.charger_profil_client(client_id)
        if not profil:
            return

        self._afficher_fiche_client(profil)

    # ------------------------------------------------------------------
    # Page Formulaire
    # ------------------------------------------------------------------

    def _creer_page_formulaire(self) -> QWidget:
        """Cree la page formulaire de creation/edition client."""
        page_form = QWidget()
        layout = QVBoxLayout(page_form)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Utiliser FormulaireCreationClient
        self.formulaire_creation = FormulaireCreationClient(self.viewmodel, parent=self)

        # Connecter les signaux
        self.formulaire_creation.client_sauvegarde.connect(self._on_client_sauvegarde)

        layout.addWidget(self.formulaire_creation)

        return page_form

    def _on_client_sauvegarde(self, client_id: int):
        """Gere la sauvegarde d'un client depuis le formulaire."""
        self.client_sauvegarde.emit(client_id)
        self._changer_page_client(self.PAGE_LISTE)

    # ==================================================================
    # Methodes publiques
    # ==================================================================

    def nouveau_client(self):
        """Reinitialise le formulaire pour un nouveau client."""
        if hasattr(self, "formulaire_creation"):
            self.formulaire_creation.vider_formulaire()

    def charger_client(self, client_id: int):
        """Charge un client pour edition."""
        if hasattr(self, "formulaire_creation"):
            self.formulaire_creation.charger_client(client_id)

    def ouvrir_fiche_client(self, client_id: int):
        """Ouvre la fiche d'un client (depuis l'extérieur)."""
        self._on_client_double_clicked(client_id)


# À ajouter APRÈS la définition de ClientView (tout à la fin du fichier)

# ============================================================================
# Formulaires de création et d'édition (héritent de FormulaireClientBase)
# ============================================================================


class FormulaireCreationClient(FormulaireClientBase):
    """Formulaire pour créer un nouveau client."""

    def _obtenir_titre(self) -> str:
        """Retourne le titre pour un nouveau client."""
        return "Nouveau Client"

    def _construire_barre_boutons(self, layout_parent):
        """Construit la barre de boutons pour la création."""
        barre = QWidget()
        barre.setStyleSheet(
            f"background-color: {Couleurs.BLANC}; border-top: 1px solid #E0E0E0;"
        )
        barre_layout = QHBoxLayout(barre)
        barre_layout.setContentsMargins(20, 15, 20, 15)
        barre_layout.setSpacing(10)

        barre_layout.addStretch()

        # Bouton Annuler
        self.btn_annuler = QPushButton("Annuler")
        self.btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_annuler.clicked.connect(self.annuler)
        self.btn_annuler.setStyleSheet(style_input())
        barre_layout.addWidget(self.btn_annuler)

        # Bouton Sauvegarder
        self.btn_sauvegarder = QPushButton("💾 Sauvegarder")
        self.btn_sauvegarder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sauvegarder.clicked.connect(self.sauvegarder)
        self.btn_sauvegarder.setStyleSheet(style_input())
        barre_layout.addWidget(self.btn_sauvegarder)

        layout_parent.addWidget(barre)


class FormulaireEditionClient(FormulaireClientBase):
    """Formulaire pour modifier un client existant (utilisé dans QDialog)."""

    # Signal supplémentaire pour demander retour à la fiche
    retour_demande = Signal()

    def _obtenir_titre(self) -> str:
        """Retourne le titre dynamique avec nom du client."""
        if self._client_id:
            # Récupérer le nom depuis les champs du formulaire
            nom = self.input_nom.text().upper()
            prenom = self.input_prenom.text()
            if nom or prenom:
                return f"Modifier Client : {nom} {prenom}".strip()
        return "Modifier Client"

    def _construire_barre_boutons(self, layout_parent):
        """Construit la barre de boutons pour l'édition."""
        barre = QWidget()
        barre.setStyleSheet(
            f"background-color: {Couleurs.BLANC}; border-top: 1px solid #E0E0E0;"
        )
        barre_layout = QHBoxLayout(barre)
        barre_layout.setContentsMargins(20, 15, 20, 15)
        barre_layout.setSpacing(10)

        # Bouton Retour (spécifique à l'édition)
        self.btn_retour = QPushButton("← Retour à la fiche")
        self.btn_retour.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_retour.clicked.connect(self.retour_demande.emit)
        self.btn_retour.setStyleSheet(style_input())
        barre_layout.addWidget(self.btn_retour)

        barre_layout.addStretch()

        # Bouton Sauvegarder
        self.btn_sauvegarder = QPushButton("💾 Sauvegarder")
        self.btn_sauvegarder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sauvegarder.clicked.connect(self.sauvegarder)
        self.btn_sauvegarder.setStyleSheet(style_input())
        barre_layout.addWidget(self.btn_sauvegarder)

        layout_parent.addWidget(barre)

    def annuler(self):
        """Override : ne rien faire (le bouton Retour gère la fermeture)."""
        pass
