"""Vue pour l'onglet Vente (enregistrement de ventes multi-articles)."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton,
    QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit,
    QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QSizePolicy,
    QAbstractItemView, QScrollArea, QAbstractSpinBox,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from views.client_card import SearchResultsWidget
from views.produit_card import SearchProductsWidget
from utils.styles import style_scroll_area, Couleurs


class VenteView(QWidget):
    """Vue pour l'onglet d'enregistrement des ventes."""

    def __init__(self, viewmodel=None):
        super().__init__()

        # Creer le ViewModel si non fourni
        if viewmodel is None:
            from viewmodels.vente_vm import VenteViewModel
            self.viewmodel = VenteViewModel()
        else:
            self.viewmodel = viewmodel

        # Variable pour stocker l'ID du client selectionne
        self._client_id = None
        # Variable pour stocker le produit sélectionné (dict)
        self._produit_selectionne = None
        # Code promo valide (dict ou None)
        self._code_promo_valide = None
        # Liste des articles ajoutes
        self._articles = []

        self._construire_ui()
        self._connecter_signaux()

    # ------------------------------------------------------------------ #
    #                        Construction de l'UI                         #
    # ------------------------------------------------------------------ #

    def _construire_ui(self):
        """Construit l'interface."""

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

        # Finaliser le scroll
        scroll.setWidget(conteneur)
        layout_self = QVBoxLayout(self)
        layout_self.setContentsMargins(0, 0, 0, 0)
        layout_self.addWidget(scroll)

    # ------------------------------------------------------------------ #
    #                   Helpers de construction UI                        #
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
        self.table_articles.setHorizontalHeaderLabels([
            "Produit", "Quantite", "Prix unitaire", "Total", "Actions"
        ])
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
            "\"Ajouter cet article\"."
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
        self.input_code_promo.setPlaceholderText(
            "Entrez un code promo (optionnel)"
        )
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

        self.btn_annuler = QPushButton("\U0001F5D1\uFE0F Annuler")
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

        # Recherche client (cards)
        self.input_recherche_client.textChanged.connect(
            self._on_recherche_client
        )
        self._search_results.client_selected.connect(
            self._on_client_selectionne
        )
        self._btn_changer_client.clicked.connect(self._deselectionner_client)

        # Recherche produit (cards)
        self.input_recherche_produit.textChanged.connect(
            self._on_recherche_produit
        )
        self.widget_resultats_produits.produit_selected.connect(
            self._on_produit_selectionne
        )

        # Calcul du sous-total article
        self.spin_quantite.valueChanged.connect(self._calculer_sous_total)
        self.spin_prix.valueChanged.connect(self._calculer_sous_total)

        # Ajouter article
        self.btn_ajouter_article.clicked.connect(self._ajouter_article)

        # Code promo
        self.btn_verifier_code.clicked.connect(self._verifier_code_promo)
        self.input_code_promo.returnPressed.connect(self._verifier_code_promo)

        # Boutons d'action
        self.btn_enregistrer.clicked.connect(self._enregistrer_vente)
        self.btn_annuler.clicked.connect(self._annuler)

    # ------------------------------------------------------------------ #
    #                           Categories                                #
    # ------------------------------------------------------------------ #

    # NOTE: Les anciennes méthodes _charger_categories(), _on_categorie_change()
    # et _on_produit_change() ont été supprimées car remplacées par le système
    # de recherche avec cards visuelles (P4.2)

    def _on_produit_change_legacy(self, index: int):
        """[OBSOLÈTE] Ancienne méthode - conservée pour référence historique."""
        # Cette méthode n'est plus utilisée depuis P4.2
        # La sélection se fait maintenant via SearchProductsWidget
        produit_id = 0  # Dummy pour éviter les erreurs
        if not produit_id:
            self.label_stock.setText("\U0001F4E6 Stock : \u2014")
            self.label_stock.setStyleSheet(
                "QLabel {"
                "    font-size: 12pt; color: #666; font-weight: 600;"
                "    padding: 10px; background-color: #F5F5F5; border-radius: 6px;"
                "}"
            )
            self.spin_quantite.setEnabled(True)
            self.spin_quantite.setMaximum(9999)
            self._calculer_sous_total()
            return

        prix = self.viewmodel.obtenir_prix_produit(produit_id)
        self.spin_prix.setValue(prix)

        # Recuperer et afficher le stock
        produit = self.viewmodel.obtenir_produit(produit_id)

        if produit:
            stock = produit.get('stock', 0) or 0

            if stock <= 0:
                self.label_stock.setText("\U0001F4E6 Stock disponible : 0")
                self.label_stock.setStyleSheet(
                    "QLabel {"
                    "    font-size: 12pt; color: #D32F2F; font-weight: bold;"
                    "    padding: 10px; background-color: #FFEBEE;"
                    "    border: 2px solid #F44336; border-radius: 6px;"
                    "}"
                )
                self.spin_quantite.setEnabled(False)
                self.spin_quantite.setValue(0)
                QMessageBox.warning(
                    self, "Stock \u00e9puis\u00e9",
                    f"Le produit '{produit['nom']}' n'est plus en stock."
                )
            else:
                self.label_stock.setText(f"\U0001F4E6 Stock disponible : {stock}")
                self.label_stock.setStyleSheet(
                    "QLabel {"
                    "    font-size: 12pt; color: #1976D2; font-weight: 600;"
                    "    padding: 10px; background-color: #E3F2FD;"
                    "    border: 2px solid #2196F3; border-radius: 6px;"
                    "}"
                )
                self.spin_quantite.setEnabled(True)
                self.spin_quantite.setMaximum(stock)
                self.spin_quantite.setValue(1)

        self._calculer_sous_total()

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
            QMessageBox.warning(
                self, "Attention", "Veuillez selectionner un produit."
            )
            return

        produit_id = self._produit_selectionne.get('id')
        produit_nom = self._produit_selectionne.get('nom', '')

        quantite = self.spin_quantite.value()
        prix_unitaire = self.spin_prix.value()
        total = quantite * prix_unitaire

        # Stocker les donnees
        article = {
            'produit_id': produit_id,
            'produit_nom': produit_nom,
            'quantite': quantite,
            'prix_unitaire': prix_unitaire,
            'total': total,
        }
        self._articles.append(article)

        # Ajouter a la table
        row = self.table_articles.rowCount()
        self.table_articles.insertRow(row)

        self.table_articles.setItem(
            row, 0, QTableWidgetItem(produit_nom)
        )
        self.table_articles.setItem(
            row, 1, QTableWidgetItem(str(quantite))
        )
        self.table_articles.setItem(
            row, 2, QTableWidgetItem(f"{prix_unitaire:.2f} \u20ac")
        )
        self.table_articles.setItem(
            row, 3, QTableWidgetItem(f"{total:.2f} \u20ac")
        )

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
            self.table_articles.setItem(
                i, 0, QTableWidgetItem(article['produit_nom'])
            )
            self.table_articles.setItem(
                i, 1, QTableWidgetItem(str(article['quantite']))
            )
            self.table_articles.setItem(
                i, 2,
                QTableWidgetItem(f"{article['prix_unitaire']:.2f} \u20ac"),
            )
            self.table_articles.setItem(
                i, 3,
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
        total = sum(a['total'] for a in self._articles)

        if self._code_promo_valide and total > 0:
            pourcentage = self._code_promo_valide.get('pourcentage', 0)
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
            self.label_code_promo.setStyleSheet(
                "font-weight: bold; color: #4CAF50;"
            )
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
            nom = (client.get('nom') or '').upper()
            prenom = client.get('prenom') or ''
            email = client.get('email') or ''
            self.label_client_selectionne.setText(
                f"Client : {nom} {prenom} ({email})"
            )

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
            if p.get('id') == produit_id:
                self._produit_selectionne = p
                break

        if not self._produit_selectionne:
            return

        # Afficher le produit sélectionné
        nom = self._produit_selectionne.get('nom', '')
        prix = self._produit_selectionne.get('prix', 0.0)
        stock = self._produit_selectionne.get('stock', 0)

        self.label_produit_selectionne.setText(
            f"Produit : {nom} - {prix:.2f} EUR"
        )

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
            combo_cat.addItem(cat['nom'], cat['id'])

        layout.addRow("Catégorie :", combo_cat)
        layout.addRow("Nom :", input_nom)
        layout.addRow("Prix :", input_prix)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
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
                    self, "Succès",
                    f"Produit '{input_nom.text()}' créé avec succès.\n"
                    "Recherchez-le pour l'ajouter à la vente."
                )

    # ------------------------------------------------------------------ #
    #                    Enregistrement de la vente                       #
    # ------------------------------------------------------------------ #

    def _enregistrer_vente(self):
        """Enregistre la vente (tous les articles) via le ViewModel avec verification du stock."""
        if not self._client_id:
            QMessageBox.warning(
                self, "Attention", "Veuillez selectionner un client."
            )
            return

        if not self._articles:
            QMessageBox.warning(
                self, "Attention",
                "Veuillez ajouter au moins un article a la vente.",
            )
            return

        # Verifier le stock de tous les articles avant d'enregistrer
        for article in self._articles:
            produit = self.viewmodel.obtenir_produit(article['produit_id'])
            if produit:
                stock_disponible = produit.get('stock', 0) or 0
                if article['quantite'] > stock_disponible:
                    QMessageBox.critical(
                        self,
                        "Stock insuffisant",
                        f"\U0001F4E6 Produit : {article['produit_nom']}\n"
                        f"\U0001F4E6 Stock disponible : {stock_disponible}\n"
                        f"\U0001F4E6 Quantite demandee : {article['quantite']}\n\n"
                        "\u274C Impossible d'enregistrer la vente.",
                    )
                    return

        # Calculer le pourcentage de promo
        pourcentage_promo = 0
        if self._code_promo_valide:
            pourcentage_promo = self._code_promo_valide.get('pourcentage', 0)

        date_str = self.date_vente.date().toString("yyyy-MM-dd")
        notes = self.texte_notes.toPlainText()
        premier_vente_id = None

        # Creer une vente par article
        for article in self._articles:
            prix_total = article['total']
            if pourcentage_promo > 0:
                prix_total = prix_total * (1 - pourcentage_promo / 100)

            vente_id = self.viewmodel.enregistrer_vente(
                client_id=self._client_id,
                produit_id=article['produit_id'],
                quantite=article['quantite'],
                prix_unitaire=article['prix_unitaire'],
                date_vente=date_str,
                notes=notes,
            )

            if premier_vente_id is None:
                premier_vente_id = vente_id

            # Decrementer le stock
            self.viewmodel.decrementer_stock(
                article['produit_id'], article['quantite']
            )

        # Enregistrer l'utilisation du code promo
        if self._code_promo_valide and premier_vente_id:
            self.viewmodel.enregistrer_utilisation_code(
                code_id=self._code_promo_valide['id'],
                client_id=self._client_id,
                vente_id=premier_vente_id,
            )

        nb = len(self._articles)
        QMessageBox.information(
            self, "\u2705 Succ\u00e8s",
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
