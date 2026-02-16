"""Vue pour l'onglet Produits avec toggle Liste/Creation et fiche detail."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QDoubleSpinBox, QTextEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QAbstractItemView, QScrollArea,
    QSpinBox, QAbstractSpinBox, QStackedWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from utils.styles import (
    style_section, style_input, style_bouton, style_spinbox,
    style_scroll_area, style_onglet, style_toggle, style_liste_selection, Couleurs,
)
from viewmodels.produits_vm import ProduitsViewModel
from views.fiche_produit_view import FicheProduitView


class ProduitsView(QWidget):
    """Vue pour la gestion des produits avec toggle Liste/Creation."""

    # Pages du stacked widget
    PAGE_LISTE = 0
    PAGE_CREATION = 1
    PAGE_FICHE = 2

    def __init__(self):
        super().__init__()
        self._mode_edition = False
        self._produit_id = None
        self._affiche_archives = False
        self.viewmodel = ProduitsViewModel()
        self._construire_ui()
        self._charger_categories()
        self._charger_produits()

    def _construire_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # === BARRE DE TOGGLE ===
        barre_toggle = QWidget()
        barre_toggle.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        toggle_layout = QHBoxLayout(barre_toggle)
        toggle_layout.setContentsMargins(30, 15, 30, 0)
        toggle_layout.setSpacing(10)

        titre = QLabel("Produits")
        titre.setStyleSheet(
            f"font-size: 20pt; font-weight: bold; color: {Couleurs.PRIMAIRE};"
        )
        toggle_layout.addWidget(titre)
        toggle_layout.addStretch()

        self.btn_toggle_liste = QPushButton("Liste")
        self.btn_toggle_liste.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_liste.clicked.connect(lambda: self._changer_page("liste"))

        self.btn_toggle_creation = QPushButton("Ajouter un produit")
        self.btn_toggle_creation.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_creation.clicked.connect(lambda: self._changer_page("creation"))

        self.btn_toggle_archives = QPushButton("Archives")
        self.btn_toggle_archives.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_archives.clicked.connect(lambda: self._changer_page("archives"))

        toggle_layout.addWidget(self.btn_toggle_liste)
        toggle_layout.addWidget(self.btn_toggle_creation)
        toggle_layout.addWidget(self.btn_toggle_archives)

        layout_principal.addWidget(barre_toggle)

        # === STACKED WIDGET ===
        self.pile = QStackedWidget()

        # Page 0 : Liste
        self.pile.addWidget(self._creer_page_liste())

        # Page 1 : Creation/Edition
        self.pile.addWidget(self._creer_page_creation())

        # Page 2 : Fiche produit
        self.fiche_produit = FicheProduitView(viewmodel=self.viewmodel)
        self.fiche_produit.retour_demande.connect(lambda: self._changer_page("liste"))
        self.pile.addWidget(self.fiche_produit)

        layout_principal.addWidget(self.pile)

        # Etat initial
        self._changer_page("liste")

    def _changer_page(self, page: str):
        """Change la page affichee (liste/creation/archives/fiche)."""
        # Désactiver TOUS les boutons puis activer le bon
        for btn in [self.btn_toggle_liste, self.btn_toggle_creation, self.btn_toggle_archives]:
            btn.setStyleSheet(style_toggle(False))

        # Activer le bon bouton et gérer l'état
        if page == "liste":
            self._affiche_archives = False
            self.btn_toggle_liste.setStyleSheet(style_toggle(True))
            self.pile.setCurrentIndex(self.PAGE_LISTE)
            self._charger_produits()

        elif page == "creation":
            self._affiche_archives = False
            self.btn_toggle_creation.setStyleSheet(style_toggle(True))
            self.pile.setCurrentIndex(self.PAGE_CREATION)

        elif page == "archives":
            self._affiche_archives = True
            self.btn_toggle_archives.setStyleSheet(style_toggle(True))
            self.pile.setCurrentIndex(self.PAGE_LISTE)  # Même table que liste
            self._charger_produits()  # Mais filtrée sur archives

        elif page == "fiche":
            # Pas de changement de toggle pour la fiche
            self.pile.setCurrentIndex(self.PAGE_FICHE)

        # Masquer les boutons toggle sur la fiche
        visible = page != "fiche"
        self.btn_toggle_liste.setVisible(visible)
        self.btn_toggle_creation.setVisible(visible)
        self.btn_toggle_archives.setVisible(visible)

    # ==================================================================
    # Page Liste
    # ==================================================================

    def _creer_page_liste(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 15, 30, 30)
        layout.setSpacing(15)

        # Barre de recherche
        search_layout = QHBoxLayout()
        self.input_recherche = QLineEdit()
        self.input_recherche.setPlaceholderText("Rechercher un produit...")
        self.input_recherche.setStyleSheet(style_input())
        self.input_recherche.textChanged.connect(self._filtrer_produits)
        search_layout.addWidget(self.input_recherche)
        layout.addLayout(search_layout)

        # Tableau
        self.table_produits = QTableWidget()
        self.table_produits.setColumnCount(6)
        self.table_produits.setHorizontalHeaderLabels([
            "Nom", "Categorie", "Prix", "Stock", "Date ajout", "Actions",
        ])

        self.table_produits.horizontalHeader().setStretchLastSection(True)
        self.table_produits.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.table_produits.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table_produits.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table_produits.setAlternatingRowColors(True)
        self.table_produits.verticalHeader().setVisible(False)
        self.table_produits.verticalHeader().setDefaultSectionSize(60)
        self.table_produits.horizontalHeader().setMinimumSectionSize(100)
        self.table_produits.setStyleSheet(
            "QTableWidget {"
            f"    alternate-background-color: {Couleurs.FOND_CLAIR};"
            f"    background-color: {Couleurs.BLANC};"
            f"    border: 2px solid {Couleurs.GRIS};"
            "    border-radius: 8px;"
            "}"
            "QHeaderView::section {"
            f"    background-color: {Couleurs.PRIMAIRE_TRES_CLAIR};"
            "    padding: 8px;"
            "    font-weight: bold;"
            "    border: none;"
            "}"
            "QTableWidget::item { min-height: 55px; padding: 10px; font-size: 12pt; }"
        )
        self.table_produits.doubleClicked.connect(self._on_double_click_produit)

        layout.addWidget(self.table_produits)

        return page

    # ==================================================================
    # Page Creation/Edition
    # ==================================================================

    def _creer_page_creation(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(style_scroll_area())

        conteneur = QWidget()
        conteneur.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        layout = QVBoxLayout(conteneur)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 15, 30, 30)

        # Formulaire
        layout.addWidget(self._creer_formulaire())

        # Attributs
        layout.addWidget(self._creer_section_attributs())

        # Boutons
        layout.addLayout(self._creer_boutons())

        layout.addStretch()
        scroll.setWidget(conteneur)
        return scroll

    def _creer_formulaire(self) -> QGroupBox:
        groupe = QGroupBox("Informations du produit")
        groupe.setStyleSheet(style_section())

        form = QFormLayout()
        form.setSpacing(12)

        font_corps = QFont()
        font_corps.setPointSize(12)

        self.input_nom = QLineEdit()
        self.input_nom.setFont(font_corps)
        self.input_nom.setPlaceholderText("Nom du produit")
        self.input_nom.setStyleSheet(style_input())
        form.addRow("Nom :", self.input_nom)

        self.input_categorie = QComboBox()
        self.input_categorie.setFont(font_corps)
        self.input_categorie.setStyleSheet(style_input())
        form.addRow("Categorie :", self.input_categorie)

        self.spin_prix = QDoubleSpinBox()
        self.spin_prix.setFont(font_corps)
        self.spin_prix.setMinimum(0.00)
        self.spin_prix.setMaximum(999999.99)
        self.spin_prix.setDecimals(2)
        self.spin_prix.setSuffix(" EUR")
        self.spin_prix.setStyleSheet(style_input())
        form.addRow("Prix :", self.spin_prix)

        self.spin_stock = QSpinBox()
        self.spin_stock.setFont(font_corps)
        self.spin_stock.setMinimum(0)
        self.spin_stock.setMaximum(999999)
        self.spin_stock.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.spin_stock.setAccelerated(True)
        self.spin_stock.setStyleSheet(style_spinbox())
        form.addRow("Stock :", self.spin_stock)

        self.input_description = QTextEdit()
        self.input_description.setFont(font_corps)
        self.input_description.setPlaceholderText("Description (optionnel)")
        self.input_description.setFixedHeight(80)
        self.input_description.setStyleSheet(style_input())
        form.addRow("Description :", self.input_description)

        groupe.setLayout(form)
        return groupe

    def _creer_section_attributs(self) -> QGroupBox:
        """Section pour les attributs personnalises du produit."""
        groupe = QGroupBox("Caracteristiques supplementaires")
        groupe.setStyleSheet(style_section())

        layout = QVBoxLayout()

        attributs = self.viewmodel.lister_attributs_globaux()

        self.attributs_widgets = {}

        for attr in attributs:
            nom_attr = attr['nom_attribut']

            row_layout = QHBoxLayout()

            label = QLabel(f"{nom_attr} :")
            label.setStyleSheet("font-weight: 600; min-width: 120px;")
            row_layout.addWidget(label)

            input_field = QLineEdit()
            input_field.setPlaceholderText(f"Valeur pour {nom_attr}")
            input_field.setStyleSheet(style_input())
            row_layout.addWidget(input_field)

            self.attributs_widgets[nom_attr] = input_field

            layout.addLayout(row_layout)

        if not attributs:
            info_label = QLabel(
                "Aucun attribut personnalise defini.\n"
                "Allez dans Parametres > Attributs produits pour en ajouter."
            )
            info_label.setStyleSheet(
                f"color: {Couleurs.TEXTE_DESACTIVE}; font-style: italic; padding: 20px;"
            )
            info_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(info_label)

        groupe.setLayout(layout)
        return groupe

    def _creer_boutons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(10)

        font_corps = QFont()
        font_corps.setPointSize(12)

        self.btn_ajouter = QPushButton("Ajouter le produit")
        self.btn_ajouter.setFont(font_corps)
        self.btn_ajouter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ajouter.setStyleSheet(style_bouton(Couleurs.SUCCES))
        self.btn_ajouter.clicked.connect(self._ajouter_produit)

        self.btn_annuler = QPushButton("Annuler")
        self.btn_annuler.setFont(font_corps)
        self.btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_annuler.setStyleSheet(style_bouton(Couleurs.GRIS))
        self.btn_annuler.clicked.connect(self._reinitialiser_formulaire)

        layout.addWidget(self.btn_annuler)
        layout.addStretch()
        layout.addWidget(self.btn_ajouter)

        return layout

    # ==================================================================
    # Chargement des donnees
    # ==================================================================

    def _charger_categories(self):
        """Charge les categories dans le combo."""
        self.input_categorie.clear()
        self.input_categorie.addItem("\u2014 Sans categorie \u2014", None)
        categories = self.viewmodel.lister_categories()
        for cat in categories:
            self.input_categorie.addItem(cat['nom'], cat['id'])

    def _charger_produits(self):
        """Charge les produits dans le tableau."""
        terme = self.input_recherche.text().strip() if hasattr(self, 'input_recherche') else ''
        if terme:
            produits = self.viewmodel.rechercher_produits(terme, archives=self._affiche_archives)
        else:
            produits = self.viewmodel.lister_produits(archives=self._affiche_archives)

        self.table_produits.setRowCount(len(produits))

        for row, produit in enumerate(produits):
            self.table_produits.setItem(row, 0, QTableWidgetItem(produit['nom']))

            categorie_nom = produit.get('categorie_nom', 'Sans categorie')
            self.table_produits.setItem(row, 1, QTableWidgetItem(categorie_nom or 'Sans categorie'))

            self.table_produits.setItem(row, 2, QTableWidgetItem(f"{produit.get('prix', 0):.2f} EUR"))

            stock = produit.get('stock', 0) or 0
            stock_item = QTableWidgetItem(str(stock))
            if stock <= 0:
                stock_item.setForeground(QColor(Couleurs.DANGER))
            elif stock <= 5:
                stock_item.setForeground(QColor(Couleurs.AVERTISSEMENT))
            self.table_produits.setItem(row, 3, stock_item)

            date_creation = produit.get('date_creation', '')
            self.table_produits.setItem(
                row, 4, QTableWidgetItem(str(date_creation)[:10] if date_creation else '')
            )

            # Boutons actions
            btn_layout_widget = QWidget()
            btn_layout = QHBoxLayout(btn_layout_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)

            btn_voir = QPushButton("Voir")
            btn_voir.setStyleSheet(style_bouton(Couleurs.PRIMAIRE, taille="petit"))
            btn_voir.setCursor(Qt.CursorShape.PointingHandCursor)
            produit_id = produit['id']
            btn_voir.clicked.connect(
                lambda checked=False, pid=produit_id: self._voir_produit(pid)
            )
            btn_layout.addWidget(btn_voir)

            btn_edit = QPushButton("Modifier")
            btn_edit.setStyleSheet(style_bouton(Couleurs.AVERTISSEMENT, taille="petit"))
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.clicked.connect(
                lambda checked=False, pid=produit_id: self._editer_produit(pid)
            )
            btn_layout.addWidget(btn_edit)

            if self._affiche_archives:
                btn_restore = QPushButton("Restaurer")
                btn_restore.setStyleSheet(style_bouton(Couleurs.SUCCES, taille="petit"))
                btn_restore.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_restore.clicked.connect(
                    lambda checked=False, pid=produit_id: self._desarchiver_produit(pid)
                )
                btn_layout.addWidget(btn_restore)
            else:
                btn_archive = QPushButton("Archiver")
                btn_archive.setStyleSheet(style_bouton(Couleurs.ARDOISE, taille="petit"))
                btn_archive.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_archive.clicked.connect(
                    lambda checked=False, pid=produit_id: self._archiver_produit(pid)
                )
                btn_layout.addWidget(btn_archive)

            btn_del = QPushButton("Supprimer")
            btn_del.setStyleSheet(style_bouton(Couleurs.DANGER, taille="petit"))
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.clicked.connect(
                lambda checked=False, pid=produit_id: self._supprimer_produit(pid)
            )
            btn_layout.addWidget(btn_del)

            self.table_produits.setCellWidget(row, 5, btn_layout_widget)

    def _filtrer_produits(self):
        """Filtre le tableau selon le texte de recherche."""
        self._charger_produits()

    def _on_double_click_produit(self, index):
        """Ouvre la fiche produit au double-clic."""
        row = index.row()
        nom = self.table_produits.item(row, 0).text()
        # Retrouver l'ID du produit
        produits = self.viewmodel.rechercher_produits(nom)
        if produits:
            self._voir_produit(produits[0]['id'])

    # ==================================================================
    # Actions
    # ==================================================================

    def _voir_produit(self, produit_id: int):
        """Affiche la fiche detail d'un produit."""
        self.fiche_produit.charger_produit(produit_id)
        self._changer_page("fiche")

    def _editer_produit(self, produit_id: int):
        """Charge un produit pour edition."""
        produit = self.viewmodel.obtenir_produit(produit_id)
        if not produit:
            return

        self._mode_edition = True
        self._produit_id = produit_id

        self.input_nom.setText(produit['nom'])
        self.spin_prix.setValue(produit.get('prix', 0))
        self.spin_stock.setValue(produit.get('stock', 0) or 0)
        self.input_description.setPlainText(produit.get('description', '') or '')

        categorie_id = produit.get('categorie_id')
        if categorie_id:
            index = self.input_categorie.findData(categorie_id)
            if index >= 0:
                self.input_categorie.setCurrentIndex(index)
        else:
            self.input_categorie.setCurrentIndex(0)

        self.btn_ajouter.setText("Modifier le produit")
        self._changer_page("creation")

    def _supprimer_produit(self, produit_id: int):
        """Supprime un produit apres confirmation."""
        rep = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment supprimer ce produit ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if rep == QMessageBox.Yes:
            if self.viewmodel.supprimer_produit(produit_id):
                self._charger_produits()

    def _ajouter_produit(self):
        """Ajoute ou modifie un produit."""
        nom = self.input_nom.text().strip()
        if not nom:
            QMessageBox.warning(
                self, "Attention", "Veuillez saisir un nom de produit."
            )
            return

        prix = self.spin_prix.value()
        if prix <= 0:
            QMessageBox.warning(
                self, "Attention", "Le prix doit etre superieur a 0."
            )
            return

        categorie_id = self.input_categorie.currentData()
        stock = self.spin_stock.value()
        description = self.input_description.toPlainText().strip()

        if self._mode_edition and self._produit_id:
            succes = self.viewmodel.modifier_produit(
                self._produit_id,
                {'nom': nom, 'categorie_id': categorie_id, 'prix': prix,
                 'stock': stock, 'description': description}
            )
            if succes:
                QMessageBox.information(self, "Succes", "Produit modifie avec succes !")
                self._reinitialiser_formulaire()
                self._changer_page("liste")
        else:
            produit_id = self.viewmodel.creer_produit(
                categorie_id=categorie_id, nom=nom, prix=prix,
                stock=stock, description=description,
            )
            if produit_id and produit_id > 0:
                QMessageBox.information(
                    self, "Succes", f"Le produit '{nom}' a ete ajoute avec succes !"
                )
                self._reinitialiser_formulaire()
                self._changer_page("liste")

    def _basculer_archives(self):
        """Bascule entre la vue liste et la vue archives."""
        self._affiche_archives = not self._affiche_archives
        self._changer_page("liste")

    def _archiver_produit(self, produit_id: int):
        """Archive un produit."""
        if self.viewmodel.archiver_produit(produit_id):
            self._charger_produits()

    def _desarchiver_produit(self, produit_id: int):
        """Restaure un produit archive."""
        if self.viewmodel.desarchiver_produit(produit_id):
            self._charger_produits()

    def _reinitialiser_formulaire(self):
        self._mode_edition = False
        self._produit_id = None
        self.input_nom.clear()
        self.input_categorie.setCurrentIndex(0)
        self.spin_prix.setValue(0.00)
        self.spin_stock.setValue(0)
        self.input_description.clear()
        self.btn_ajouter.setText("Ajouter le produit")
