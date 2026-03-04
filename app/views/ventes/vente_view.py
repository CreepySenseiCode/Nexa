"""Vue pour l'onglet Vente (enregistrement de ventes multi-articles + historique + commandes)."""

import uuid

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QDateEdit,
    QTimeEdit,
    QTextEdit,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QSizePolicy,
    QAbstractItemView,
    QScrollArea,
    QAbstractSpinBox,
    QStackedWidget,
    QCheckBox,
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QFont

from views.components.client_card import SearchResultsWidget
from views.components.produit_card import SearchProductsWidget
from views.components.modern_segmented_control import ModernSegmentedControl
from views.components.vente_card import VenteCard
from views.components.commande_card import CommandeCard
from views.ventes.fiche_vente_view import FicheVenteView
from views.ventes.fiche_commande_view import FicheCommandeView
from viewmodels.commande_vm import CommandeViewModel
from utils.styles import style_scroll_area, Couleurs


class VenteView(QWidget):
    """Vue pour l'onglet d'enregistrement des ventes."""

    def __init__(self, viewmodel=None, parent=None):  # ← parent=None par défaut
        super().__init__(parent)
        self._mode_admin = True

        # Creer le ViewModel si non fourni
        if viewmodel is None:
            from viewmodels.vente_vm import VenteViewModel

            self.viewmodel = VenteViewModel()
        else:
            self.viewmodel = viewmodel

        # ViewModel commandes
        self.commande_vm = CommandeViewModel()

        # Variable pour stocker l'ID du client selectionne
        self._client_id = None
        # Variable pour stocker le produit sélectionné (dict)
        self._produit_selectionne = None
        # Code promo valide (dict ou None)
        self._code_promo_valide = None
        # Liste des articles ajoutes
        self._articles = []

        # --- Commande form state ---
        self._cmd_client_id = None
        self._cmd_produit_selectionne = None
        self._cmd_articles = []

        self._construire_ui()
        self._connecter_signaux()

    # ------------------------------------------------------------------ #
    #                        Construction de l'UI                         #
    # ------------------------------------------------------------------ #

    PAGE_HISTORIQUE = 0
    PAGE_NOUVEAU = 1
    PAGE_FICHE = 2
    PAGE_FICHE_COMMANDE = 3
    _PAGES = ["historique", "nouveau"]

    def _construire_ui(self):
        """Construit l'interface avec toggle Historique / Nouveau."""
        layout_self = QVBoxLayout(self)
        layout_self.setContentsMargins(0, 0, 0, 0)
        layout_self.setSpacing(0)

        # Toggle segmenté principal
        self._barre_toggle = ModernSegmentedControl(["Historique", "Nouveau"])
        self._barre_toggle.selectionChanged.connect(self._on_toggle_changed)

        layout_haut = QHBoxLayout()
        layout_haut.setContentsMargins(24, 16, 24, 8)
        layout_haut.addStretch(1)
        layout_haut.addWidget(self._barre_toggle)
        layout_haut.addStretch(1)
        layout_self.addLayout(layout_haut)

        # Stacked widget
        self.pile = QStackedWidget()
        self.pile.addWidget(self._creer_page_historique())  # 0
        self.pile.addWidget(self._creer_page_nouveau())  # 1

        # Fiche détail vente (page 2, cachée du toggle)
        self.fiche_vente = FicheVenteView(viewmodel=self.viewmodel)
        self.fiche_vente.retour_demande.connect(
            lambda: self._changer_page("historique")
        )
        self.pile.addWidget(self.fiche_vente)  # 2

        # Fiche détail commande (page 3, cachée du toggle)
        self.fiche_commande = FicheCommandeView(viewmodel=self.commande_vm)
        self.fiche_commande.retour_demande.connect(
            lambda: self._changer_page("historique")
        )
        self.pile.addWidget(self.fiche_commande)  # 3

        layout_self.addWidget(self.pile)
        self._barre_toggle.select(self.PAGE_HISTORIQUE)
        self._charger_historique()

    def _on_toggle_changed(self, index: int):
        self._changer_page(self._PAGES[index])

    def mettre_a_jour_mode(self, mode_admin: bool) -> None:
        """Met à jour la vue selon le mode administratif/fonctionnel."""
        self._mode_admin = mode_admin
        if self.pile.currentIndex() == self.PAGE_HISTORIQUE:
            self._charger_historique()
        self.fiche_vente.mettre_a_jour_mode(mode_admin)
        self.fiche_commande.mettre_a_jour_mode(mode_admin)

    def _changer_page(self, page: str):
        if page in self._PAGES:
            idx = self._PAGES.index(page)
            if self._barre_toggle.current_index != idx:
                self._barre_toggle.select(idx)

        if page == "historique":
            self.pile.setCurrentIndex(self.PAGE_HISTORIQUE)
            self._charger_historique()
        elif page == "nouveau":
            self.pile.setCurrentIndex(self.PAGE_NOUVEAU)
        elif page == "fiche":
            self.pile.setCurrentIndex(self.PAGE_FICHE)
        elif page == "fiche_commande":
            self.pile.setCurrentIndex(self.PAGE_FICHE_COMMANDE)

        hidden_pages = ("fiche", "fiche_commande")
        self._barre_toggle.setVisible(page not in hidden_pages)

    def _creer_page_historique(self) -> QWidget:
        """Crée la page historique des ventes."""
        page = QWidget()
        page.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # Barre de recherche
        self.input_recherche_ventes = QLineEdit()
        self.input_recherche_ventes.setPlaceholderText(
            "Rechercher une vente (client, produit, date, montant...)"
        )
        self.input_recherche_ventes.setStyleSheet(
            f"QLineEdit {{ border: 2px solid {Couleurs.BORDURE}; border-radius: 8px; "
            f"padding: 10px 14px; font-size: 12pt; background: white; }}"
            f"QLineEdit:focus {{ border-color: {Couleurs.PRIMAIRE}; }}"
        )
        self.input_recherche_ventes.textChanged.connect(self._charger_historique)
        layout.addWidget(self.input_recherche_ventes)

        # Filtre type
        filtre_row = QHBoxLayout()
        self._combo_filtre_type = QComboBox()
        self._combo_filtre_type.addItems(["Tout", "Ventes", "Commandes"])
        self._combo_filtre_type.setStyleSheet("font-size: 11pt; padding: 4px;")
        self._combo_filtre_type.currentIndexChanged.connect(
            lambda: self._charger_historique()
        )
        filtre_row.addWidget(QLabel("Afficher :"))
        filtre_row.addWidget(self._combo_filtre_type)
        filtre_row.addStretch()
        layout.addLayout(filtre_row)

        # Compteur
        self._label_nb_ventes = QLabel()
        self._label_nb_ventes.setStyleSheet(
            "color: #7f8c8d; font-size: 11pt; border: none;"
        )
        layout.addWidget(self._label_nb_ventes)

        # Scroll area avec cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(style_scroll_area())

        self._conteneur_ventes = QWidget()
        self._conteneur_ventes.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        self._layout_ventes = QVBoxLayout(self._conteneur_ventes)
        self._layout_ventes.setContentsMargins(0, 0, 8, 0)
        self._layout_ventes.setSpacing(6)
        self._layout_ventes.addStretch()

        scroll.setWidget(self._conteneur_ventes)
        layout.addWidget(scroll, stretch=1)

        return page

    def _charger_historique(self):
        """Charge et affiche l'historique des ventes et commandes."""
        terme = self.input_recherche_ventes.text().strip()
        termes = [t for t in terme.split() if t]
        filtre_type = (
            self._combo_filtre_type.currentIndex()
        )  # 0=tout, 1=ventes, 2=commandes

        # Vider les cards existantes
        while self._layout_ventes.count() > 1:
            item = self._layout_ventes.takeAt(0)
            if w := item.widget():
                w.deleteLater()

        total_items = 0

        # Ventes
        if filtre_type in (0, 1):
            transactions = self.viewmodel.lister_transactions()
            if termes:
                transactions = self._filtrer_ventes(transactions, termes)
            transactions.sort(key=lambda t: t.get("date_vente") or "", reverse=True)
            for txn in transactions:
                card = VenteCard(
                    txn, search_terms=termes, show_actions=self._mode_admin
                )
                card.double_clicked.connect(self._voir_vente)
                card.action_supprimer.connect(self._supprimer_vente)
                self._layout_ventes.insertWidget(self._layout_ventes.count() - 1, card)
            total_items += len(transactions)

        # Commandes
        if filtre_type in (0, 2):
            commandes = self.commande_vm.lister_commandes()
            if termes:
                commandes = self._filtrer_commandes(commandes, termes)
            commandes.sort(key=lambda c: c.get("date_prevue") or "", reverse=True)
            for cmd in commandes:
                card = CommandeCard(cmd, show_actions=self._mode_admin)
                card.double_clicked.connect(self._voir_commande)
                card.action_supprimer.connect(self._supprimer_commande_action)
                self._layout_ventes.insertWidget(self._layout_ventes.count() - 1, card)
            total_items += len(commandes)

        labels = {0: "élément(s)", 1: "vente(s)", 2: "commande(s)"}
        self._label_nb_ventes.setText(
            f"{total_items} {labels.get(filtre_type, 'élément(s)')}"
        )

        if total_items == 0:
            lbl = QLabel("Aucun élément trouvé.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                "color: #BBBBBB; font-size: 13pt; padding: 40px; border: none;"
            )
            self._layout_ventes.insertWidget(0, lbl)

    def _filtrer_ventes(self, transactions: list, termes: list[str]) -> list:
        """Filtre multi-termes sur tous les champs de la transaction."""
        resultat = []
        for txn in transactions:
            client_nom = (
                f"{txn.get('client_nom', '')} {txn.get('client_prenom', '')}"
            ).lower()
            articles = (txn.get("articles_resume") or "").lower()
            date_str = (txn.get("date_vente") or "").lower()
            total_str = str(txn.get("total_transaction", ""))
            notes = (txn.get("notes") or "").lower()

            tout_matche = True
            for t in termes:
                tl = t.lower()
                if (
                    tl in client_nom
                    or tl in articles
                    or tl in date_str
                    or tl in total_str
                    or tl in notes
                ):
                    continue
                tout_matche = False
                break

            if tout_matche:
                resultat.append(txn)
        return resultat

    def _voir_vente(self, transaction_id: str):
        """Ouvre la fiche détaillée d'une vente."""
        self.fiche_vente.charger_vente(transaction_id)
        self._changer_page("fiche")

    def ouvrir_fiche_vente_par_id(self, vente_id: int):
        """Ouvre la fiche d'une vente par son ID (depuis l'extérieur)."""
        ventes = self.viewmodel.lister_ventes()
        for v in ventes:
            if v.get("id") == vente_id:
                self._voir_vente(v.get("transaction_id", ""))
                return

    def ouvrir_fiche_commande(self, commande_id: int):
        """Ouvre la fiche d'une commande (depuis l'extérieur)."""
        self._voir_commande(commande_id)

    def _supprimer_vente(self, transaction_id: str):
        """Supprime une transaction après confirmation."""
        rep = QMessageBox.question(
            self,
            "Confirmation",
            "Supprimer cette vente et tous ses articles ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            self.viewmodel.supprimer_transaction(transaction_id)
            self._charger_historique()

    def _creer_page_nouveau(self) -> QWidget:
        """Crée la page Nouveau avec sous-toggle Vente / Commande."""
        page = QWidget()
        page.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sous-toggle compact
        self._sub_toggle = ModernSegmentedControl(
            ["Vente", "Commande"], style="compact"
        )
        sub_row = QHBoxLayout()
        sub_row.setContentsMargins(24, 8, 24, 4)
        sub_row.addWidget(self._sub_toggle)
        sub_row.addStretch()
        layout.addLayout(sub_row)

        # Stacked widget interne
        self._nouveau_pile = QStackedWidget()
        self._nouveau_pile.addWidget(self._creer_page_vente())  # 0
        self._nouveau_pile.addWidget(self._creer_page_creation_commande())  # 1

        self._sub_toggle.selectionChanged.connect(self._nouveau_pile.setCurrentIndex)
        layout.addWidget(self._nouveau_pile)

        return page

    def _creer_page_vente(self) -> QWidget:
        """Crée la page du formulaire de vente (ancien contenu de _construire_ui)."""
        # Conteneur scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(style_scroll_area())

        conteneur = QWidget()
        conteneur.setStyleSheet("background-color: #FFFFFF;")
        layout_principal = QVBoxLayout(conteneur)
        layout_principal.setSpacing(16)

        # --- Titre ---
        label_titre = QLabel("Enregistrer une vente")
        font_titre = QFont()
        font_titre.setPointSize(16)
        font_titre.setBold(True)
        label_titre.setFont(font_titre)
        layout_principal.addWidget(label_titre)

        # --- Sections ---
        layout_principal.addWidget(self._creer_section_client())
        layout_principal.addWidget(self._creer_section_article())
        layout_principal.addWidget(self._creer_section_panier())
        layout_principal.addWidget(self._creer_section_paiement())

        layout_principal.addStretch()

        scroll.setWidget(conteneur)
        return scroll

    def _filtrer_commandes(self, commandes: list, termes: list[str]) -> list:
        """Filtre multi-termes sur les champs de la commande."""
        resultat = []
        for cmd in commandes:
            client_nom = (
                f"{cmd.get('client_nom', '')} {cmd.get('client_prenom', '')}"
            ).lower()
            articles = (cmd.get("articles_resume") or "").lower()
            date_str = (cmd.get("date_prevue") or "").lower()
            statut = (cmd.get("statut") or "").lower()
            total_str = str(cmd.get("total", ""))

            tout_matche = True
            for t in termes:
                tl = t.lower()
                if (
                    tl in client_nom
                    or tl in articles
                    or tl in date_str
                    or tl in statut
                    or tl in total_str
                ):
                    continue
                tout_matche = False
                break

            if tout_matche:
                resultat.append(cmd)
        return resultat

    def _voir_commande(self, commande_id: int):
        """Ouvre la fiche détaillée d'une commande."""
        self.fiche_commande.charger_commande(commande_id)
        self._changer_page("fiche_commande")

    def _supprimer_commande_action(self, commande_id: int):
        """Supprime une commande après confirmation."""
        rep = QMessageBox.question(
            self,
            "Confirmation",
            "Supprimer cette commande et tous ses articles ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            self.commande_vm.supprimer_commande(commande_id)
            self._charger_historique()

    # ------------------------------------------------------------------ #
    #              Page Création Commande (formulaire)                     #
    # ------------------------------------------------------------------ #

    def _creer_page_creation_commande(self) -> QWidget:
        """Crée la page formulaire de création de commande."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(style_scroll_area())

        conteneur = QWidget()
        conteneur.setStyleSheet("background-color: #FFFFFF;")
        layout_principal = QVBoxLayout(conteneur)
        layout_principal.setSpacing(16)

        # Titre
        label_titre = QLabel("Nouvelle commande")
        font_titre = QFont()
        font_titre.setPointSize(16)
        font_titre.setBold(True)
        label_titre.setFont(font_titre)
        label_titre.setStyleSheet("color: #E65100;")
        layout_principal.addWidget(label_titre)

        # --- Section Client ---
        layout_principal.addWidget(self._creer_section_client_commande())

        # --- Section Articles ---
        layout_principal.addWidget(self._creer_section_article_commande())

        # --- Section Panier ---
        layout_principal.addWidget(self._creer_section_panier_commande())

        # --- Section Planification ---
        layout_principal.addWidget(self._creer_section_planification())

        # (Section tâches supprimée — gestion via onglet Tâches avec association)

        # --- Section Notes + Total + Boutons ---
        layout_principal.addWidget(self._creer_section_final_commande())

        layout_principal.addStretch()
        scroll.setWidget(conteneur)
        return scroll

    def _creer_section_client_commande(self) -> QGroupBox:
        """Section client pour le formulaire commande."""
        groupe = QGroupBox("Client")
        layout = QVBoxLayout(groupe)

        self.cmd_input_recherche_client = QLineEdit()
        self.cmd_input_recherche_client.setPlaceholderText(
            "Rechercher un client (nom, prenom, email, telephone)..."
        )
        self.cmd_input_recherche_client.setFixedHeight(40)
        self.cmd_input_recherche_client.setStyleSheet("font-size: 13pt;")
        layout.addWidget(self.cmd_input_recherche_client)

        self._cmd_search_results = SearchResultsWidget()
        self._cmd_search_results.setMinimumHeight(400)
        self._cmd_search_results.setVisible(False)
        layout.addWidget(self._cmd_search_results)

        self._cmd_widget_client_sel = QWidget()
        layout_sel = QHBoxLayout(self._cmd_widget_client_sel)
        layout_sel.setContentsMargins(0, 5, 0, 5)

        self.cmd_label_client_sel = QLabel("")
        self.cmd_label_client_sel.setStyleSheet(
            "font-size: 13pt; font-weight: bold; color: #333;"
        )
        layout_sel.addWidget(self.cmd_label_client_sel)
        layout_sel.addStretch()

        btn_changer = QPushButton("Changer de client")
        btn_changer.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; "
            "padding: 6px 14px; border-radius: 4px; border: none; font-size: 11pt; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        btn_changer.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_changer.clicked.connect(self._cmd_deselectionner_client)
        layout_sel.addWidget(btn_changer)

        self._cmd_widget_client_sel.setVisible(False)
        layout.addWidget(self._cmd_widget_client_sel)

        return groupe

    def _creer_section_article_commande(self) -> QWidget:
        """Section sélection article pour le formulaire commande."""
        section = QWidget()
        layout_section = QVBoxLayout(section)
        layout_section.setContentsMargins(0, 0, 0, 0)
        layout_section.setSpacing(16)

        groupe_produit = QGroupBox("Produit")
        layout_produit = QVBoxLayout(groupe_produit)

        self.cmd_input_recherche_produit = QLineEdit()
        self.cmd_input_recherche_produit.setPlaceholderText(
            "Rechercher un produit (nom ou catégorie)..."
        )
        self.cmd_input_recherche_produit.setFixedHeight(40)
        self.cmd_input_recherche_produit.setStyleSheet("font-size: 13pt;")
        layout_produit.addWidget(self.cmd_input_recherche_produit)

        self.cmd_widget_resultats_produits = SearchProductsWidget()
        self.cmd_widget_resultats_produits.setVisible(False)
        layout_produit.addWidget(self.cmd_widget_resultats_produits)

        self.cmd_label_produit_sel = QLabel("Aucun produit sélectionné")
        self.cmd_label_produit_sel.setStyleSheet(
            "QLabel { font-size: 12pt; color: #666; padding: 10px; "
            "background-color: #FFF3E0; border-radius: 6px; border: 2px solid #FF9800; }"
        )
        layout_produit.addWidget(self.cmd_label_produit_sel)

        self.cmd_label_stock = QLabel("Stock : \u2014")
        self.cmd_label_stock.setStyleSheet(
            "QLabel { font-size: 12pt; color: #666; font-weight: 600; "
            "padding: 10px; background-color: #F5F5F5; border-radius: 6px; }"
        )
        layout_produit.addWidget(self.cmd_label_stock)

        layout_section.addWidget(groupe_produit)

        # Détails article
        groupe_details = QGroupBox("Détails de l'article")
        layout_details = QFormLayout(groupe_details)
        layout_details.setSpacing(12)
        layout_details.setContentsMargins(15, 25, 15, 15)

        spinbox_style = (
            "QSpinBox, QDoubleSpinBox { min-height: 44px; font-size: 13pt; "
            "padding: 6px 12px; border: 2px solid #E0E0E0; border-radius: 10px; background: white; }"
            "QSpinBox:focus, QDoubleSpinBox:focus { border: 2px solid #FF9800; }"
        )

        self.cmd_spin_quantite = QSpinBox()
        self.cmd_spin_quantite.setMinimum(1)
        self.cmd_spin_quantite.setMaximum(9999)
        self.cmd_spin_quantite.setValue(1)
        self.cmd_spin_quantite.setMinimumHeight(40)
        self.cmd_spin_quantite.setStyleSheet(spinbox_style)
        layout_details.addRow("Quantité :", self.cmd_spin_quantite)

        self.cmd_spin_prix = QDoubleSpinBox()
        self.cmd_spin_prix.setMinimum(0)
        self.cmd_spin_prix.setMaximum(999999.99)
        self.cmd_spin_prix.setDecimals(2)
        self.cmd_spin_prix.setSuffix(" \u20ac")
        self.cmd_spin_prix.setMinimumHeight(40)
        self.cmd_spin_prix.setStyleSheet(spinbox_style)
        layout_details.addRow("Prix unitaire :", self.cmd_spin_prix)

        self.cmd_label_sous_total = QLabel("0,00 \u20ac")
        self.cmd_label_sous_total.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #666; padding: 10px;"
        )
        layout_details.addRow("Sous-total :", self.cmd_label_sous_total)

        layout_section.addWidget(groupe_details)

        # Bouton ajouter article
        self.cmd_btn_ajouter_article = QPushButton("Ajouter cet article")
        self.cmd_btn_ajouter_article.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; "
            "border: none; border-radius: 8px; padding: 12px 24px; "
            "font-size: 13pt; font-weight: bold; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        self.cmd_btn_ajouter_article.setCursor(Qt.CursorShape.PointingHandCursor)
        layout_section.addWidget(self.cmd_btn_ajouter_article)

        return section

    def _creer_section_panier_commande(self) -> QGroupBox:
        """Panier articles commande."""
        groupe = QGroupBox("Articles de la commande")
        layout = QVBoxLayout(groupe)

        self.cmd_table_articles = QTableWidget()
        self.cmd_table_articles.setColumnCount(5)
        self.cmd_table_articles.setHorizontalHeaderLabels(
            ["Produit", "Quantité", "Prix unitaire", "Total", "Actions"]
        )
        self.cmd_table_articles.horizontalHeader().setStretchLastSection(True)
        self.cmd_table_articles.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.cmd_table_articles.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cmd_table_articles.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cmd_table_articles.verticalHeader().setVisible(False)
        self.cmd_table_articles.setMinimumHeight(150)
        self.cmd_table_articles.setRowCount(0)
        layout.addWidget(self.cmd_table_articles)

        self.cmd_label_aucun_article = QLabel(
            "Aucun article ajouté. Sélectionnez un produit et cliquez "
            '"Ajouter cet article".'
        )
        self.cmd_label_aucun_article.setAlignment(Qt.AlignCenter)
        self.cmd_label_aucun_article.setStyleSheet(
            "color: #999; font-style: italic; padding: 20px;"
        )
        layout.addWidget(self.cmd_label_aucun_article)

        return groupe

    def _creer_section_planification(self) -> QGroupBox:
        """Section date/heure prévue pour la commande."""
        groupe = QGroupBox("Planification")
        layout = QFormLayout(groupe)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 25, 15, 15)

        self.cmd_date_prevue = QDateEdit()
        self.cmd_date_prevue.setCalendarPopup(True)
        self.cmd_date_prevue.setDate(QDate.currentDate().addDays(1))
        self.cmd_date_prevue.setDisplayFormat("dd/MM/yyyy")
        self.cmd_date_prevue.setMinimumHeight(40)
        self.cmd_date_prevue.setStyleSheet("font-size: 14pt; padding: 5px;")
        layout.addRow("Date prévue :", self.cmd_date_prevue)

        # Heure optionnelle
        heure_row = QHBoxLayout()
        self.cmd_check_heure = QCheckBox("Définir une heure")
        self.cmd_check_heure.setStyleSheet("font-size: 11pt;")
        heure_row.addWidget(self.cmd_check_heure)

        self.cmd_heure_prevue = QTimeEdit()
        self.cmd_heure_prevue.setDisplayFormat("HH:mm")
        self.cmd_heure_prevue.setTime(QTime(9, 0))
        self.cmd_heure_prevue.setMinimumHeight(40)
        self.cmd_heure_prevue.setStyleSheet("font-size: 14pt; padding: 5px;")
        self.cmd_heure_prevue.setVisible(False)
        self.cmd_check_heure.toggled.connect(self.cmd_heure_prevue.setVisible)
        heure_row.addWidget(self.cmd_heure_prevue)
        heure_row.addStretch()

        layout.addRow("", heure_row)

        return groupe

    def _creer_section_final_commande(self) -> QWidget:
        """Section notes + total + boutons pour la commande."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Total
        groupe_total = QGroupBox("Total")
        layout_total = QVBoxLayout(groupe_total)
        self.cmd_label_total = QLabel("0,00 \u20ac")
        self.cmd_label_total.setStyleSheet(
            "font-size: 22pt; font-weight: bold; color: #FF9800; padding: 15px;"
        )
        self.cmd_label_total.setAlignment(Qt.AlignCenter)
        layout_total.addWidget(self.cmd_label_total)
        layout.addWidget(groupe_total)

        # Notes
        groupe_notes = QGroupBox("Notes")
        layout_notes = QVBoxLayout(groupe_notes)
        self.cmd_texte_notes = QTextEdit()
        self.cmd_texte_notes.setFixedHeight(70)
        self.cmd_texte_notes.setPlaceholderText("Notes (optionnel)")
        layout_notes.addWidget(self.cmd_texte_notes)
        layout.addWidget(groupe_notes)

        # Boutons
        layout_boutons = QHBoxLayout()
        layout_boutons.addStretch()

        btn_annuler = QPushButton("Annuler")
        btn_annuler.setMinimumHeight(50)
        btn_annuler.setMinimumWidth(150)
        btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_annuler.setStyleSheet(
            "QPushButton { background-color: #9E9E9E; color: white; "
            "border: none; border-radius: 8px; padding: 12px 24px; "
            "font-size: 13pt; font-weight: 600; }"
            "QPushButton:hover { background-color: #757575; }"
        )
        btn_annuler.clicked.connect(self._cmd_annuler)
        layout_boutons.addWidget(btn_annuler)

        self.cmd_btn_creer = QPushButton("Créer la commande")
        self.cmd_btn_creer.setMinimumHeight(50)
        self.cmd_btn_creer.setMinimumWidth(200)
        self.cmd_btn_creer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cmd_btn_creer.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; "
            "border: none; border-radius: 8px; padding: 12px 24px; "
            "font-size: 13pt; font-weight: 600; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        self.cmd_btn_creer.clicked.connect(self._cmd_enregistrer)
        layout_boutons.addWidget(self.cmd_btn_creer)

        layout.addLayout(layout_boutons)

        return section

    # ------------------------------------------------------------------ #
    #                   Logique formulaire commande                       #
    # ------------------------------------------------------------------ #

    def _cmd_on_recherche_client(self, texte: str):
        if len(texte) < 2:
            self._cmd_search_results.vider()
            self._cmd_search_results.setVisible(False)
            return
        resultats = self.commande_vm.rechercher_clients(texte)
        self._cmd_search_results.afficher_resultats(resultats, texte.split())
        self._cmd_search_results.setVisible(True)

    def _cmd_on_client_selectionne(self, client_id: int):
        self._cmd_client_id = client_id
        client = self.commande_vm.obtenir_client(client_id)
        if client:
            nom = (client.get("nom") or "").upper()
            prenom = client.get("prenom") or ""
            email = client.get("email") or ""
            self.cmd_label_client_sel.setText(f"Client : {nom} {prenom} ({email})")

        self._cmd_search_results.setVisible(False)
        self.cmd_input_recherche_client.blockSignals(True)
        self.cmd_input_recherche_client.clear()
        self.cmd_input_recherche_client.setVisible(False)
        self.cmd_input_recherche_client.blockSignals(False)
        self._cmd_widget_client_sel.setVisible(True)

    def _cmd_deselectionner_client(self):
        self._cmd_client_id = None
        self._cmd_widget_client_sel.setVisible(False)
        self.cmd_input_recherche_client.setVisible(True)
        self.cmd_input_recherche_client.setFocus()
        self.cmd_label_client_sel.setText("")

    def _cmd_on_recherche_produit(self, texte: str):
        if len(texte) < 2:
            self.cmd_widget_resultats_produits.vider()
            self.cmd_widget_resultats_produits.setVisible(False)
            return
        produits = self.commande_vm.rechercher_produits(texte)
        if produits:
            self.cmd_widget_resultats_produits.afficher_produits(
                produits, search_terms=[texte]
            )
            self.cmd_widget_resultats_produits.setVisible(True)
        else:
            self.cmd_widget_resultats_produits.vider()
            self.cmd_widget_resultats_produits.setVisible(False)

    def _cmd_on_produit_selectionne(self, produit_id: int):
        produits = self.commande_vm.rechercher_produits(
            self.cmd_input_recherche_produit.text()
        )
        for p in produits:
            if p.get("id") == produit_id:
                self._cmd_produit_selectionne = p
                break
        if not self._cmd_produit_selectionne:
            return

        nom = self._cmd_produit_selectionne.get("nom", "")
        prix = self._cmd_produit_selectionne.get("prix", 0.0)
        stock = self._cmd_produit_selectionne.get("stock", 0)

        self.cmd_label_produit_sel.setText(f"Produit : {nom} - {prix:.2f} EUR")

        color = "#4CAF50" if stock > 10 else ("#FF9800" if stock > 0 else "#F44336")
        self.cmd_label_stock.setStyleSheet(
            f"QLabel {{ font-size: 12pt; color: {color}; font-weight: 600; "
            f"padding: 10px; background-color: #F5F5F5; border-radius: 6px; }}"
        )
        self.cmd_label_stock.setText(f"Stock : {stock}")
        self.cmd_spin_prix.setValue(prix)

        self.cmd_widget_resultats_produits.setVisible(False)
        self.cmd_input_recherche_produit.blockSignals(True)
        self.cmd_input_recherche_produit.clear()
        self.cmd_input_recherche_produit.blockSignals(False)

    def _cmd_calculer_sous_total(self):
        quantite = self.cmd_spin_quantite.value()
        prix = self.cmd_spin_prix.value()
        self.cmd_label_sous_total.setText(f"{quantite * prix:.2f} \u20ac")

    def _cmd_ajouter_article(self):
        if not self._cmd_produit_selectionne:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un produit.")
            return

        produit_id = self._cmd_produit_selectionne.get("id")
        produit_nom = self._cmd_produit_selectionne.get("nom", "")
        quantite = self.cmd_spin_quantite.value()
        prix_unitaire = self.cmd_spin_prix.value()
        total = quantite * prix_unitaire

        article = {
            "produit_id": produit_id,
            "produit_nom": produit_nom,
            "quantite": quantite,
            "prix_unitaire": prix_unitaire,
            "total": total,
        }
        self._cmd_articles.append(article)
        self._cmd_rafraichir_panier()

        # Reset
        self.cmd_spin_quantite.setValue(1)
        self.cmd_spin_prix.setValue(0)
        self._cmd_produit_selectionne = None
        self.cmd_label_produit_sel.setText("Aucun produit sélectionné")
        self.cmd_label_stock.setText("Stock : \u2014")

    def _cmd_supprimer_article(self, index: int):
        if index < len(self._cmd_articles):
            self._cmd_articles.pop(index)
        self._cmd_rafraichir_panier()

    def _cmd_rafraichir_panier(self):
        """Reconstruit le tableau des articles commande."""
        self.cmd_table_articles.setRowCount(0)
        for i, article in enumerate(self._cmd_articles):
            self.cmd_table_articles.insertRow(i)
            self.cmd_table_articles.setItem(
                i, 0, QTableWidgetItem(article["produit_nom"])
            )
            self.cmd_table_articles.setItem(
                i, 1, QTableWidgetItem(str(article["quantite"]))
            )
            self.cmd_table_articles.setItem(
                i, 2, QTableWidgetItem(f"{article['prix_unitaire']:.2f} \u20ac")
            )
            self.cmd_table_articles.setItem(
                i, 3, QTableWidgetItem(f"{article['total']:.2f} \u20ac")
            )

            btn_suppr = QPushButton("Supprimer")
            btn_suppr.setStyleSheet(
                "QPushButton { background-color: #F44336; color: white; "
                "border: none; border-radius: 5px; padding: 5px 10px; }"
                "QPushButton:hover { background-color: #D32F2F; }"
            )
            btn_suppr.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_suppr.clicked.connect(
                lambda checked=False, r=i: self._cmd_supprimer_article(r)
            )
            self.cmd_table_articles.setCellWidget(i, 4, btn_suppr)

        self.cmd_label_aucun_article.setVisible(not self._cmd_articles)
        self._cmd_calculer_total()

    def _cmd_calculer_total(self):
        total = sum(a["total"] for a in self._cmd_articles)
        self.cmd_label_total.setText(f"{total:.2f} \u20ac")

    def _cmd_enregistrer(self):
        """Crée la commande via le ViewModel."""
        if not self._cmd_client_id:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un client.")
            return
        if not self._cmd_articles:
            QMessageBox.warning(
                self, "Attention", "Veuillez ajouter au moins un article."
            )
            return

        date_str = self.cmd_date_prevue.date().toString("yyyy-MM-dd")
        heure_str = None
        if self.cmd_check_heure.isChecked():
            heure_str = self.cmd_heure_prevue.time().toString("HH:mm")
        notes = self.cmd_texte_notes.toPlainText()

        commande_id = self.commande_vm.creer_commande_complete(
            client_id=self._cmd_client_id,
            articles=self._cmd_articles,
            date_prevue=date_str,
            heure_prevue=heure_str,
            notes=notes,
        )

        if commande_id:
            QMessageBox.information(
                self,
                "Commande créée",
                f"Commande #{commande_id} créée avec succès !",
            )
            self._cmd_reinitialiser()
            self._changer_page("historique")
        else:
            QMessageBox.critical(self, "Erreur", "Impossible de créer la commande.")

    def _cmd_reinitialiser(self):
        """Réinitialise le formulaire de création de commande."""
        self._cmd_client_id = None
        self._cmd_produit_selectionne = None
        self._cmd_articles.clear()
        self.cmd_input_recherche_client.clear()
        self.cmd_input_recherche_client.setVisible(True)
        self._cmd_widget_client_sel.setVisible(False)
        self.cmd_label_client_sel.setText("")

        self.cmd_input_recherche_produit.clear()
        self.cmd_label_produit_sel.setText("Aucun produit sélectionné")
        self.cmd_label_stock.setText("Stock : \u2014")
        self.cmd_widget_resultats_produits.setVisible(False)

        self.cmd_spin_quantite.setValue(1)
        self.cmd_spin_prix.setValue(0)
        self.cmd_label_sous_total.setText("0,00 \u20ac")
        self.cmd_label_total.setText("0,00 \u20ac")
        self.cmd_table_articles.setRowCount(0)
        self.cmd_label_aucun_article.setVisible(True)

        self.cmd_date_prevue.setDate(QDate.currentDate().addDays(1))
        self.cmd_check_heure.setChecked(False)
        self.cmd_heure_prevue.setTime(QTime(9, 0))
        self.cmd_texte_notes.clear()

    def _cmd_annuler(self):
        """Annule la création de commande."""
        self._cmd_reinitialiser()
        self._changer_page("nouveau")

    # ------------------------------------------------------------------ #
    #                   Helpers de construction UI  (vente)               #
    # ------------------------------------------------------------------ #

    def _creer_section_client(self):
        """Cree et retourne le QGroupBox de selection du client."""

        groupe_client = QGroupBox("Client")
        layout_client = QVBoxLayout(groupe_client)

        # Champ de recherche
        self.input_recherche_client = QLineEdit()
        self.input_recherche_client.setPlaceholderText(
            "Rechercher un client (nom, prenom, email, telephone)..."
        )
        self.input_recherche_client.setFixedHeight(40)
        self.input_recherche_client.setStyleSheet("font-size: 13pt;")
        layout_client.addWidget(self.input_recherche_client)

        # Resultats de recherche (cards)
        self._search_results = SearchResultsWidget()
        self._search_results.setMinimumHeight(400)
        self._search_results.setVisible(False)
        layout_client.addWidget(self._search_results)

        # Widget client selectionne (masque par defaut)
        self._widget_client_selectionne = QWidget()
        layout_sel = QHBoxLayout(self._widget_client_selectionne)
        layout_sel.setContentsMargins(0, 5, 0, 5)

        self.label_client_selectionne = QLabel("")
        self.label_client_selectionne.setStyleSheet(
            "font-size: 13pt; font-weight: bold; color: #333;"
        )
        layout_sel.addWidget(self.label_client_selectionne)

        layout_sel.addStretch()

        self._btn_changer_client = QPushButton("Changer de client")
        self._btn_changer_client.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; "
            "padding: 6px 14px; border-radius: 4px; border: none; font-size: 11pt; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        self._btn_changer_client.setCursor(Qt.CursorShape.PointingHandCursor)
        layout_sel.addWidget(self._btn_changer_client)

        self._widget_client_selectionne.setVisible(False)
        layout_client.addWidget(self._widget_client_selectionne)

        return groupe_client

    def _creer_section_article(self):
        """Cree et retourne un QWidget contenant la selection de produit,
        les details de l'article et le bouton 'Ajouter cet article'."""

        section = QWidget()
        layout_section = QVBoxLayout(section)
        layout_section.setContentsMargins(0, 0, 0, 0)
        layout_section.setSpacing(16)

        # --- Selection du produit ---
        groupe_produit = QGroupBox("Produit")
        layout_produit = QVBoxLayout(groupe_produit)

        # Champ de recherche produit
        self.input_recherche_produit = QLineEdit()
        self.input_recherche_produit.setPlaceholderText(
            "Rechercher un produit (nom ou catégorie)..."
        )
        self.input_recherche_produit.setFixedHeight(40)
        self.input_recherche_produit.setStyleSheet("font-size: 13pt;")
        layout_produit.addWidget(self.input_recherche_produit)

        # Widget de résultats (cards produits)
        self.widget_resultats_produits = SearchProductsWidget()
        self.widget_resultats_produits.setVisible(False)
        layout_produit.addWidget(self.widget_resultats_produits)

        # Label produit sélectionné
        self.label_produit_selectionne = QLabel("Aucun produit sélectionné")
        self.label_produit_selectionne.setStyleSheet(
            "QLabel {"
            "    font-size: 12pt;"
            "    color: #666;"
            "    padding: 10px;"
            "    background-color: #E3F2FD;"
            "    border-radius: 6px;"
            "    border: 2px solid #2196F3;"
            "}"
        )
        layout_produit.addWidget(self.label_produit_selectionne)

        # Label de stock
        self.label_stock = QLabel("📦 Stock : —")
        self.label_stock.setStyleSheet(
            "QLabel {"
            "    font-size: 12pt;"
            "    color: #666;"
            "    font-weight: 600;"
            "    padding: 10px;"
            "    background-color: #F5F5F5;"
            "    border-radius: 6px;"
            "}"
        )
        layout_produit.addWidget(self.label_stock)

        layout_section.addWidget(groupe_produit)

        # --- Details de l'article ---
        groupe_details = QGroupBox("Details de l'article")
        groupe_details.setStyleSheet(
            "QGroupBox { padding: 20px; margin-top: 10px; }"
            "QGroupBox::title { padding: 0 8px; }"
        )
        layout_details = QFormLayout(groupe_details)
        layout_details.setSpacing(12)
        layout_details.setContentsMargins(15, 25, 15, 15)

        spinbox_style = (
            "QSpinBox, QDoubleSpinBox {"
            "    min-height: 44px;"
            "    font-size: 13pt;"
            "    padding: 6px 12px;"
            "    border: 2px solid #E0E0E0;"
            "    border-radius: 10px;"
            "    background: white;"
            "}"
            "QSpinBox:focus, QDoubleSpinBox:focus {"
            "    border: 2px solid #2196F3;"
            "}"
            "QSpinBox::up-button, QSpinBox::down-button,"
            "QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {"
            "    width: 36px;"
            "    border: none;"
            "    background: #2196F3;"
            "}"
            "QSpinBox::up-button:hover, QSpinBox::down-button:hover,"
            "QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {"
            "    background: #1976D2;"
            "}"
            "QSpinBox::up-button, QDoubleSpinBox::up-button {"
            "    border-top-right-radius: 8px;"
            "}"
            "QSpinBox::down-button, QDoubleSpinBox::down-button {"
            "    border-bottom-right-radius: 8px;"
            "}"
        )

        # Quantite
        self.spin_quantite = QSpinBox()
        self.spin_quantite.setMinimum(1)
        self.spin_quantite.setMaximum(9999)
        self.spin_quantite.setValue(1)
        self.spin_quantite.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.spin_quantite.setAccelerated(True)
        self.spin_quantite.setMinimumHeight(40)
        self.spin_quantite.setMinimumWidth(100)
        self.spin_quantite.setStyleSheet(spinbox_style)
        layout_details.addRow("Quantite :", self.spin_quantite)

        # Prix unitaire
        self.spin_prix = QDoubleSpinBox()
        self.spin_prix.setMinimum(0)
        self.spin_prix.setMaximum(999999.99)
        self.spin_prix.setDecimals(2)
        self.spin_prix.setSuffix(" \u20ac")
        self.spin_prix.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.spin_prix.setAccelerated(True)
        self.spin_prix.setMinimumHeight(40)
        self.spin_prix.setMinimumWidth(150)
        self.spin_prix.setStyleSheet(spinbox_style)
        layout_details.addRow("Prix unitaire :", self.spin_prix)

        # Sous-total article (preview)
        self.label_sous_total = QLabel("0,00 \u20ac")
        self.label_sous_total.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #666; padding: 10px;"
        )
        layout_details.addRow("Sous-total :", self.label_sous_total)

        layout_section.addWidget(groupe_details)

        # --- Bouton Ajouter l'article ---
        self.btn_ajouter_article = QPushButton("Ajouter cet article")
        self.btn_ajouter_article.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "border: none; border-radius: 8px; padding: 12px 24px; "
            "font-size: 13pt; font-weight: bold; }"
            "QPushButton:hover { background-color: #388E3C; }"
        )
        self.btn_ajouter_article.setCursor(Qt.CursorShape.PointingHandCursor)
        layout_section.addWidget(self.btn_ajouter_article)

        return section

    def _creer_section_panier(self):
        """Cree et retourne le QGroupBox du tableau des articles (panier)."""

        groupe_articles = QGroupBox("Articles de la vente")
        layout_articles = QVBoxLayout(groupe_articles)

        self.table_articles = QTableWidget()
        self.table_articles.setColumnCount(5)
        self.table_articles.setHorizontalHeaderLabels(
            ["Produit", "Quantite", "Prix unitaire", "Total", "Actions"]
        )
        self.table_articles.horizontalHeader().setStretchLastSection(True)
        self.table_articles.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.table_articles.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_articles.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_articles.verticalHeader().setVisible(False)
        self.table_articles.setMinimumHeight(150)
        self.table_articles.setRowCount(0)
        layout_articles.addWidget(self.table_articles)

        # Label quand aucun article
        self.label_aucun_article = QLabel(
            "Aucun article ajoute. Selectionnez un produit et cliquez "
            '"Ajouter cet article".'
        )
        self.label_aucun_article.setAlignment(Qt.AlignCenter)
        self.label_aucun_article.setStyleSheet(
            "color: #999; font-style: italic; padding: 20px;"
        )
        layout_articles.addWidget(self.label_aucun_article)

        return groupe_articles

    def _creer_section_paiement(self):
        """Cree et retourne un QWidget contenant le code promo, le total,
        les informations complementaires et les boutons d'action."""

        section = QWidget()
        layout_section = QVBoxLayout(section)
        layout_section.setContentsMargins(0, 0, 0, 0)
        layout_section.setSpacing(16)

        # --- Code promotionnel ---
        groupe_promo = QGroupBox("Code promotionnel")
        layout_promo = QVBoxLayout(groupe_promo)

        layout_promo_row = QHBoxLayout()

        self.input_code_promo = QLineEdit()
        self.input_code_promo.setPlaceholderText("Entrez un code promo (optionnel)")
        layout_promo_row.addWidget(self.input_code_promo)

        self.btn_verifier_code = QPushButton("Verifier")
        self.btn_verifier_code.setProperty("class", "btn-primary")
        self.btn_verifier_code.setMaximumWidth(120)
        layout_promo_row.addWidget(self.btn_verifier_code)

        layout_promo.addLayout(layout_promo_row)

        self.label_code_promo = QLabel("")
        self.label_code_promo.setStyleSheet("font-weight: bold;")
        layout_promo.addWidget(self.label_code_promo)

        layout_section.addWidget(groupe_promo)

        # --- Total general ---
        groupe_total = QGroupBox("Total")
        layout_total_box = QVBoxLayout(groupe_total)

        self.label_total = QLabel("0,00 \u20ac")
        self.label_total.setStyleSheet(
            "font-size: 22pt; font-weight: bold; color: #2196F3; padding: 15px;"
        )
        self.label_total.setAlignment(Qt.AlignCenter)
        layout_total_box.addWidget(self.label_total)

        layout_section.addWidget(groupe_total)

        # --- Date et notes ---
        groupe_infos = QGroupBox("Informations complementaires")
        layout_infos = QFormLayout(groupe_infos)
        layout_infos.setSpacing(12)

        # Date de vente
        self.date_vente = QDateEdit()
        self.date_vente.setCalendarPopup(True)
        self.date_vente.setDate(QDate.currentDate())
        self.date_vente.setDisplayFormat("dd/MM/yyyy")
        self.date_vente.setMinimumHeight(40)
        self.date_vente.setStyleSheet("font-size: 14pt; padding: 5px;")
        layout_infos.addRow("Date de vente :", self.date_vente)

        # Notes (optionnel)
        self.texte_notes = QTextEdit()
        self.texte_notes.setFixedHeight(70)
        self.texte_notes.setPlaceholderText("Notes (optionnel)")
        layout_infos.addRow("Notes :", self.texte_notes)

        layout_section.addWidget(groupe_infos)

        # --- Barre de boutons d'action ---
        layout_boutons = QHBoxLayout()
        layout_boutons.addStretch()

        self.btn_annuler = QPushButton("\U0001f5d1\ufe0f Annuler")
        self.btn_annuler.setMinimumHeight(50)
        self.btn_annuler.setMinimumWidth(150)
        self.btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_annuler.setStyleSheet(
            "QPushButton {"
            "    background-color: #9E9E9E;"
            "    color: white;"
            "    border: none;"
            "    border-radius: 8px;"
            "    padding: 12px 24px;"
            "    font-size: 13pt;"
            "    font-weight: 600;"
            "}"
            "QPushButton:hover {"
            "    background-color: #757575;"
            "}"
        )
        layout_boutons.addWidget(self.btn_annuler)

        self.btn_enregistrer = QPushButton("\u2705 Enregistrer la vente")
        self.btn_enregistrer.setMinimumHeight(50)
        self.btn_enregistrer.setMinimumWidth(200)
        self.btn_enregistrer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_enregistrer.setStyleSheet(
            "QPushButton {"
            "    background-color: #4CAF50;"
            "    color: white;"
            "    border: none;"
            "    border-radius: 8px;"
            "    padding: 12px 24px;"
            "    font-size: 13pt;"
            "    font-weight: 600;"
            "}"
            "QPushButton:hover {"
            "    background-color: #45A049;"
            "}"
        )
        layout_boutons.addWidget(self.btn_enregistrer)

        layout_section.addLayout(layout_boutons)

        return section

    # ------------------------------------------------------------------ #
    #                        Connexion des signaux                        #
    # ------------------------------------------------------------------ #

    def _connecter_signaux(self):
        """Connecte les signaux aux slots."""

        # Recherche client (cards) — vente
        self.input_recherche_client.textChanged.connect(self._on_recherche_client)
        self._search_results.client_selected.connect(self._on_client_selectionne)
        self._btn_changer_client.clicked.connect(self._deselectionner_client)

        # Recherche produit (cards) — vente
        self.input_recherche_produit.textChanged.connect(self._on_recherche_produit)
        self.widget_resultats_produits.produit_selected.connect(
            self._on_produit_selectionne
        )

        # Calcul du sous-total article — vente
        self.spin_quantite.valueChanged.connect(self._calculer_sous_total)
        self.spin_prix.valueChanged.connect(self._calculer_sous_total)

        # Ajouter article — vente
        self.btn_ajouter_article.clicked.connect(self._ajouter_article)

        # Code promo
        self.btn_verifier_code.clicked.connect(self._verifier_code_promo)
        self.input_code_promo.returnPressed.connect(self._verifier_code_promo)

        # Boutons d'action — vente
        self.btn_enregistrer.clicked.connect(self._enregistrer_vente)
        self.btn_annuler.clicked.connect(self._annuler)

        # --- Signaux commande ---
        self.cmd_input_recherche_client.textChanged.connect(
            self._cmd_on_recherche_client
        )
        self._cmd_search_results.client_selected.connect(
            self._cmd_on_client_selectionne
        )
        self.cmd_input_recherche_produit.textChanged.connect(
            self._cmd_on_recherche_produit
        )
        self.cmd_widget_resultats_produits.produit_selected.connect(
            self._cmd_on_produit_selectionne
        )
        self.cmd_spin_quantite.valueChanged.connect(self._cmd_calculer_sous_total)
        self.cmd_spin_prix.valueChanged.connect(self._cmd_calculer_sous_total)
        self.cmd_btn_ajouter_article.clicked.connect(self._cmd_ajouter_article)

    # ------------------------------------------------------------------ #
    #                           Categories                                #
    # ------------------------------------------------------------------ #

    # NOTE: Les anciennes méthodes _charger_categories(), _on_categorie_change()
    # et _on_produit_change() ont été supprimées car remplacées par le système
    # de recherche avec cards visuelles (P4.2)

    def _calculer_sous_total(self):
        """Calcule et affiche le sous-total de l'article en cours."""
        quantite = self.spin_quantite.value()
        prix = self.spin_prix.value()
        sous_total = quantite * prix
        self.label_sous_total.setText(f"{sous_total:.2f} \u20ac")

    # ------------------------------------------------------------------ #
    #                      Multi-articles                                 #
    # ------------------------------------------------------------------ #

    def _ajouter_article(self):
        """Ajoute l'article actuel a la liste des articles."""
        if not self._produit_selectionne:
            QMessageBox.warning(self, "Attention", "Veuillez selectionner un produit.")
            return

        produit_id = self._produit_selectionne.get("id")
        produit_nom = self._produit_selectionne.get("nom", "")

        quantite = self.spin_quantite.value()
        prix_unitaire = self.spin_prix.value()
        total = quantite * prix_unitaire

        # Stocker les donnees
        article = {
            "produit_id": produit_id,
            "produit_nom": produit_nom,
            "quantite": quantite,
            "prix_unitaire": prix_unitaire,
            "total": total,
        }
        self._articles.append(article)

        # Ajouter a la table
        row = self.table_articles.rowCount()
        self.table_articles.insertRow(row)

        self.table_articles.setItem(row, 0, QTableWidgetItem(produit_nom))
        self.table_articles.setItem(row, 1, QTableWidgetItem(str(quantite)))
        self.table_articles.setItem(
            row, 2, QTableWidgetItem(f"{prix_unitaire:.2f} \u20ac")
        )
        self.table_articles.setItem(row, 3, QTableWidgetItem(f"{total:.2f} \u20ac"))

        # Bouton supprimer
        btn_supprimer = QPushButton("Supprimer")
        btn_supprimer.setStyleSheet(
            "QPushButton {"
            "    background-color: #F44336;"
            "    color: white;"
            "    border: none;"
            "    border-radius: 5px;"
            "    padding: 5px 10px;"
            "}"
            "QPushButton:hover { background-color: #D32F2F; }"
        )
        btn_supprimer.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_supprimer.clicked.connect(
            lambda checked=False, r=row: self._supprimer_article(r)
        )
        self.table_articles.setCellWidget(row, 4, btn_supprimer)

        # Masquer le label "aucun article"
        self.label_aucun_article.setVisible(False)

        # Reinitialiser le formulaire produit
        self.spin_quantite.setValue(1)
        self.spin_prix.setValue(0)
        self._produit_selectionne = None
        self.label_produit_selectionne.setText("Aucun produit sélectionné")
        self.label_stock.setText("📦 Stock : —")

        # Recalculer le total general
        self._calculer_total_general()

    def _supprimer_article(self, row: int):
        """Supprime un article de la liste."""
        if row < len(self._articles):
            self._articles.pop(row)

        # Reconstruire la table
        self.table_articles.setRowCount(0)
        for i, article in enumerate(self._articles):
            self.table_articles.insertRow(i)
            self.table_articles.setItem(i, 0, QTableWidgetItem(article["produit_nom"]))
            self.table_articles.setItem(
                i, 1, QTableWidgetItem(str(article["quantite"]))
            )
            self.table_articles.setItem(
                i,
                2,
                QTableWidgetItem(f"{article['prix_unitaire']:.2f} \u20ac"),
            )
            self.table_articles.setItem(
                i,
                3,
                QTableWidgetItem(f"{article['total']:.2f} \u20ac"),
            )

            btn_supprimer = QPushButton("Supprimer")
            btn_supprimer.setStyleSheet(
                "QPushButton {"
                "    background-color: #F44336;"
                "    color: white;"
                "    border: none;"
                "    border-radius: 5px;"
                "    padding: 5px 10px;"
                "}"
                "QPushButton:hover { background-color: #D32F2F; }"
            )
            btn_supprimer.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_supprimer.clicked.connect(
                lambda checked=False, r=i: self._supprimer_article(r)
            )
            self.table_articles.setCellWidget(i, 4, btn_supprimer)

        if not self._articles:
            self.label_aucun_article.setVisible(True)

        self._calculer_total_general()

    def _calculer_total_general(self):
        """Calcule le total general de tous les articles avec code promo."""
        total = sum(a["total"] for a in self._articles)

        if self._code_promo_valide and total > 0:
            pourcentage = self._code_promo_valide.get("pourcentage", 0)
            reduction = total * pourcentage / 100
            total_final = total - reduction
            self.label_total.setText(
                f"<s>{total:.2f} \u20ac</s>  \u2192  {total_final:.2f} \u20ac "
                f"<span style='color: #4CAF50;'>(-{pourcentage:.0f}%)</span>"
            )
        else:
            self.label_total.setText(f"{total:.2f} \u20ac")

    # ------------------------------------------------------------------ #
    #                      Code promotionnel                              #
    # ------------------------------------------------------------------ #

    def _verifier_code_promo(self):
        """Verifie la validite d'un code promotionnel."""
        code = self.input_code_promo.text().strip()
        if not code:
            self._code_promo_valide = None
            self.label_code_promo.setText("")
            self._calculer_total_general()
            return

        resultat, message, type_erreur = self.viewmodel.verifier_code_promo(
            code, self._client_id
        )

        if type_erreur is None:
            self._code_promo_valide = resultat
            self.label_code_promo.setText(
                f"\u2705 Code valide : -{resultat['pourcentage']:.0f}%"
            )
            self.label_code_promo.setStyleSheet("font-weight: bold; color: #4CAF50;")
        else:
            self._code_promo_valide = None
            self.label_code_promo.setText(message or "Code invalide")
            if type_erreur == "EXPIRE":
                self.label_code_promo.setStyleSheet(
                    "font-weight: bold; color: #F57C00;"
                )
            elif type_erreur == "EPUISE":
                self.label_code_promo.setStyleSheet(
                    "font-weight: bold; color: #D32F2F;"
                )
            else:
                self.label_code_promo.setStyleSheet(
                    "font-weight: bold; color: #F44336;"
                )
        self._calculer_total_general()

    # ------------------------------------------------------------------ #
    #                     Recherche & selection client                    #
    # ------------------------------------------------------------------ #

    def _on_recherche_client(self, texte: str):
        """Recherche des clients et affiche les resultats."""
        if len(texte) < 2:
            self._search_results.vider()
            self._search_results.setVisible(False)
            return

        resultats = self.viewmodel.rechercher_clients(texte)
        search_terms = texte.split()
        self._search_results.afficher_resultats(resultats, search_terms)
        self._search_results.setVisible(True)

    def _on_client_selectionne(self, client_id: int):
        """Callback quand un client est selectionne via une card."""
        self._client_id = client_id

        # Recuperer les infos du client
        client = self.viewmodel.obtenir_client(client_id)
        if client:
            nom = (client.get("nom") or "").upper()
            prenom = client.get("prenom") or ""
            email = client.get("email") or ""
            self.label_client_selectionne.setText(f"Client : {nom} {prenom} ({email})")

        # Masquer la recherche, afficher le client selectionne
        self._search_results.setVisible(False)
        self.input_recherche_client.blockSignals(True)
        self.input_recherche_client.clear()
        self.input_recherche_client.setVisible(False)
        self.input_recherche_client.blockSignals(False)
        self._widget_client_selectionne.setVisible(True)

    def _deselectionner_client(self):
        """Deselectionne le client et re-affiche la barre de recherche."""
        self._client_id = None
        self._widget_client_selectionne.setVisible(False)
        self.input_recherche_client.setVisible(True)
        self.input_recherche_client.setFocus()
        self.label_client_selectionne.setText("")

    # ------------------------------------------------------------------ #
    #                   Gestion de la recherche produit                   #
    # ------------------------------------------------------------------ #

    def _on_recherche_produit(self, texte: str):
        """Callback quand le texte de recherche produit change."""
        if len(texte) < 2:
            self.widget_resultats_produits.vider()
            self.widget_resultats_produits.setVisible(False)
            return

        # Rechercher les produits
        produits = self.viewmodel.rechercher_produits_avance(texte)

        # Afficher les résultats
        if produits:
            self.widget_resultats_produits.afficher_produits(
                produits, search_terms=[texte]
            )
            self.widget_resultats_produits.setVisible(True)
        else:
            self.widget_resultats_produits.vider()
            self.widget_resultats_produits.setVisible(False)

    def _on_produit_selectionne(self, produit_id: int):
        """Callback quand un produit est sélectionné via une card."""
        # Récupérer les détails du produit depuis la recherche
        produits = self.viewmodel.rechercher_produits_avance(
            self.input_recherche_produit.text()
        )

        for p in produits:
            if p.get("id") == produit_id:
                self._produit_selectionne = p
                break

        if not self._produit_selectionne:
            return

        # Afficher le produit sélectionné
        nom = self._produit_selectionne.get("nom", "")
        prix = self._produit_selectionne.get("prix", 0.0)
        stock = self._produit_selectionne.get("stock", 0)

        self.label_produit_selectionne.setText(f"Produit : {nom} - {prix:.2f} EUR")

        # Afficher le stock
        color = "#4CAF50" if stock > 10 else ("#FF9800" if stock > 0 else "#F44336")
        self.label_stock.setStyleSheet(
            f"QLabel {{"
            f"    font-size: 12pt;"
            f"    color: {color};"
            f"    font-weight: 600;"
            f"    padding: 10px;"
            f"    background-color: #F5F5F5;"
            f"    border-radius: 6px;"
            f"}}"
        )
        self.label_stock.setText(f"📦 Stock : {stock}")

        # Pré-remplir le prix
        self.spin_prix.setValue(prix)

        # Masquer les résultats
        self.widget_resultats_produits.setVisible(False)
        self.input_recherche_produit.blockSignals(True)
        self.input_recherche_produit.clear()
        self.input_recherche_produit.blockSignals(False)

    # ------------------------------------------------------------------ #
    #                   Creation categorie / produit                      #
    # ------------------------------------------------------------------ #

    def _creer_categorie(self):
        """Popup pour creer une nouvelle categorie."""
        from PySide6.QtWidgets import QInputDialog

        nom, ok = QInputDialog.getText(
            self, "Nouvelle categorie", "Nom de la categorie :"
        )
        if ok and nom.strip():
            cat_id = self.viewmodel.creer_categorie(nom.strip())
            if cat_id:
                QMessageBox.information(
                    self, "Succès", f"Catégorie '{nom}' créée avec succès."
                )

    def _creer_produit(self):
        """Popup pour creer un nouveau produit."""
        from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Nouveau produit")
        dialog.setMinimumWidth(350)
        layout = QFormLayout(dialog)

        input_nom = QLineEdit()
        input_nom.setPlaceholderText("Nom du produit")

        input_prix = QDoubleSpinBox()
        input_prix.setMaximum(999999.99)
        input_prix.setDecimals(2)
        input_prix.setSuffix(" \u20ac")

        # ComboBox pour sélectionner la catégorie
        combo_cat = QComboBox()
        combo_cat.addItem("-- Sélectionner une catégorie --", None)
        categories = self.viewmodel.lister_categories()
        for cat in categories:
            combo_cat.addItem(cat["nom"], cat["id"])

        layout.addRow("Catégorie :", combo_cat)
        layout.addRow("Nom :", input_nom)
        layout.addRow("Prix :", input_prix)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() == QDialog.Accepted and input_nom.text().strip():
            categorie_id = combo_cat.currentData()
            if not categorie_id:
                QMessageBox.warning(
                    self, "Attention", "Veuillez sélectionner une catégorie."
                )
                return

            prod_id = self.viewmodel.creer_produit(
                categorie_id, input_nom.text().strip(), input_prix.value()
            )
            if prod_id:
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Produit '{input_nom.text()}' créé avec succès.\n"
                    "Recherchez-le pour l'ajouter à la vente.",
                )

    # ------------------------------------------------------------------ #
    #                    Enregistrement de la vente                       #
    # ------------------------------------------------------------------ #

    def _enregistrer_vente(self):
        """Enregistre la vente (tous les articles) via le ViewModel avec verification du stock."""
        if not self._client_id:
            QMessageBox.warning(self, "Attention", "Veuillez selectionner un client.")
            return

        if not self._articles:
            QMessageBox.warning(
                self,
                "Attention",
                "Veuillez ajouter au moins un article a la vente.",
            )
            return

        # Verifier le stock de tous les articles avant d'enregistrer
        for article in self._articles:
            produit = self.viewmodel.obtenir_produit(article["produit_id"])
            if produit:
                stock_disponible = produit.get("stock", 0) or 0
                if article["quantite"] > stock_disponible:
                    QMessageBox.critical(
                        self,
                        "Stock insuffisant",
                        f"\U0001f4e6 Produit : {article['produit_nom']}\n"
                        f"\U0001f4e6 Stock disponible : {stock_disponible}\n"
                        f"\U0001f4e6 Quantite demandee : {article['quantite']}\n\n"
                        "\u274c Impossible d'enregistrer la vente.",
                    )
                    return

        # Calculer le pourcentage de promo
        pourcentage_promo = 0
        if self._code_promo_valide:
            pourcentage_promo = self._code_promo_valide.get("pourcentage", 0)

        from datetime import datetime as _dt

        date_str = self.date_vente.date().toString("yyyy-MM-dd")
        # Ajouter l'heure actuelle automatiquement
        heure_str = _dt.now().strftime("%H:%M:%S")
        date_str = f"{date_str} {heure_str}"
        notes = self.texte_notes.toPlainText()
        premier_vente_id = None
        txn_id = str(uuid.uuid4())

        # Creer une vente par article (même transaction_id pour tous)
        for article in self._articles:
            prix_total = article["total"]
            if pourcentage_promo > 0:
                prix_total = prix_total * (1 - pourcentage_promo / 100)

            vente_id = self.viewmodel.enregistrer_vente(
                client_id=self._client_id,
                produit_id=article["produit_id"],
                quantite=article["quantite"],
                prix_unitaire=article["prix_unitaire"],
                date_vente=date_str,
                notes=notes,
                transaction_id=txn_id,
            )

            if premier_vente_id is None:
                premier_vente_id = vente_id

            # Decrementer le stock
            self.viewmodel.decrementer_stock(article["produit_id"], article["quantite"])

        # Enregistrer l'utilisation du code promo
        if self._code_promo_valide and premier_vente_id:
            self.viewmodel.enregistrer_utilisation_code(
                code_id=self._code_promo_valide["id"],
                client_id=self._client_id,
                vente_id=premier_vente_id,
            )

        nb = len(self._articles)
        QMessageBox.information(
            self,
            "\u2705 Succ\u00e8s",
            f"Vente enregistree avec succes ({nb} article(s)) !",
        )
        self._reinitialiser_formulaire_vente()

    # ------------------------------------------------------------------ #
    #                       Reinitialisation                              #
    # ------------------------------------------------------------------ #

    def _reinitialiser_formulaire_vente(self):
        """Reinitialise le formulaire de vente (mais garde le client)."""
        # Réinitialiser la sélection de produit
        self._produit_selectionne = None
        self.label_produit_selectionne.setText("Aucun produit sélectionné")
        self.label_stock.setText("📦 Stock : —")
        self.input_recherche_produit.clear()
        self.widget_resultats_produits.setVisible(False)

        self.spin_quantite.setValue(1)
        self.spin_prix.setValue(0)
        self.label_sous_total.setText("0,00 \u20ac")
        self.label_total.setText("0,00 \u20ac")
        self.date_vente.setDate(QDate.currentDate())
        self.texte_notes.clear()
        self.input_code_promo.clear()
        self.label_code_promo.setText("")
        self._code_promo_valide = None
        self._articles.clear()
        self.table_articles.setRowCount(0)
        self.label_aucun_article.setVisible(True)

    def _annuler(self):
        """Annule et reinitialise tout le formulaire."""
        self._client_id = None
        self.input_recherche_client.clear()
        self.label_client_selectionne.setText("")
        self._widget_client_selectionne.setVisible(False)
        self.input_recherche_client.setVisible(True)
        self._reinitialiser_formulaire_vente()
