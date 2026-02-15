"""Vue pour l'onglet Produits (gestion des produits)."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QDoubleSpinBox, QTextEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QAbstractItemView, QScrollArea, QDialog,
    QDialogButtonBox, QSpinBox, QAbstractSpinBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from utils.styles import style_section, style_input, style_bouton, style_spinbox, style_scroll_area, Couleurs
from viewmodels.produits_vm import ProduitsViewModel


class ProduitsView(QWidget):
    """Vue pour la gestion des produits (Patron)."""

    def __init__(self):
        super().__init__()
        self._mode_edition = False
        self._produit_id = None
        self.viewmodel = ProduitsViewModel()
        self._construire_ui()
        self._charger_categories()
        self._charger_produits()

    def _construire_ui(self):
        # Conteneur scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(style_scroll_area())

        conteneur = QWidget()
        conteneur.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        layout_principal = QVBoxLayout(conteneur)
        layout_principal.setSpacing(20)
        layout_principal.setContentsMargins(30, 20, 30, 30)

        # Titre
        titre = QLabel("Gestion des produits")
        titre.setStyleSheet(
            f"font-size: 20pt; font-weight: bold; color: {Couleurs.PRIMAIRE}; padding: 10px 0;"
        )
        layout_principal.addWidget(titre)

        # Formulaire de creation
        layout_principal.addWidget(self._creer_formulaire())

        # Attributs personnalises
        layout_principal.addWidget(self._creer_section_attributs())

        # Barre de boutons
        layout_principal.addLayout(self._creer_boutons())

        # Tableau des produits
        layout_principal.addWidget(self._creer_tableau())

        layout_principal.addStretch()

        scroll.setWidget(conteneur)

        layout_self = QVBoxLayout(self)
        layout_self.setContentsMargins(0, 0, 0, 0)
        layout_self.addWidget(scroll)

    def _creer_formulaire(self) -> QGroupBox:
        groupe = QGroupBox("Ajouter un nouveau produit")
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

    def _creer_tableau(self) -> QGroupBox:
        groupe = QGroupBox("Produits existants")
        groupe.setStyleSheet(style_section())

        layout = QVBoxLayout()

        # Barre de recherche
        search_layout = QHBoxLayout()
        self.input_recherche = QLineEdit()
        self.input_recherche.setPlaceholderText("Rechercher un produit...")
        self.input_recherche.setStyleSheet(style_input())
        search_layout.addWidget(self.input_recherche)
        layout.addLayout(search_layout)

        self.table_produits = QTableWidget()
        self.table_produits.setColumnCount(7)
        self.table_produits.setHorizontalHeaderLabels([
            "Nom", "Categorie", "Prix", "Stock",
            "Description", "Date ajout", "Actions",
        ])

        self.table_produits.horizontalHeader().setStretchLastSection(True)
        self.table_produits.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.table_produits.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        self.table_produits.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table_produits.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table_produits.setAlternatingRowColors(True)
        self.table_produits.verticalHeader().setVisible(False)
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
        )

        layout.addWidget(self.table_produits)
        groupe.setLayout(layout)
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

    def _charger_categories(self):
        """Charge les categories dans le combo (par ID)."""
        self.input_categorie.clear()
        self.input_categorie.addItem("\u2014 Sans cat\u00e9gorie \u2014", None)

        categories = self.viewmodel.lister_categories()

        for cat in categories:
            self.input_categorie.addItem(cat['nom'], cat['id'])

    def _charger_produits(self):
        """Charge les produits dans le tableau."""
        produits = self.viewmodel.lister_produits()

        self.table_produits.setRowCount(len(produits))

        for row, produit in enumerate(produits):
            self.table_produits.setItem(row, 0, QTableWidgetItem(produit['nom']))

            categorie_nom = produit.get('categorie_nom', 'Sans cat\u00e9gorie')
            self.table_produits.setItem(row, 1, QTableWidgetItem(categorie_nom or 'Sans cat\u00e9gorie'))

            self.table_produits.setItem(row, 2, QTableWidgetItem(f"{produit.get('prix', 0):.2f} \u20ac"))

            stock = produit.get('stock', 0) or 0
            stock_item = QTableWidgetItem(str(stock))
            if stock <= 0:
                stock_item.setForeground(QColor(Couleurs.DANGER))
            self.table_produits.setItem(row, 3, stock_item)

            self.table_produits.setItem(row, 4, QTableWidgetItem(produit.get('description', '') or ''))

            date_creation = produit.get('date_creation', '')
            self.table_produits.setItem(row, 5, QTableWidgetItem(str(date_creation)[:10] if date_creation else ''))

            # Boutons actions
            btn_layout_widget = QWidget()
            btn_layout = QHBoxLayout(btn_layout_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)

            btn_edit = QPushButton("Modifier")
            btn_edit.setStyleSheet(style_bouton(Couleurs.PRIMAIRE, taille="petit"))
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            produit_id = produit['id']
            btn_edit.clicked.connect(
                lambda checked=False, pid=produit_id: self._editer_produit(pid)
            )
            btn_layout.addWidget(btn_edit)

            btn_del = QPushButton("Supprimer")
            btn_del.setStyleSheet(style_bouton(Couleurs.DANGER, taille="petit"))
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.clicked.connect(
                lambda checked=False, pid=produit_id: self._supprimer_produit(pid)
            )
            btn_layout.addWidget(btn_del)

            self.table_produits.setCellWidget(row, 6, btn_layout_widget)

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
        """Ajoute ou modifie un produit avec categorie_id."""
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

        if hasattr(self, '_mode_edition') and self._mode_edition and hasattr(self, '_produit_id'):
            succes = self.viewmodel.modifier_produit(
                self._produit_id,
                {'nom': nom, 'categorie_id': categorie_id, 'prix': prix, 'stock': stock, 'description': description}
            )
            if succes:
                QMessageBox.information(self, "Succes", "Produit modifie avec succes !")
                self._charger_produits()
                self._reinitialiser_formulaire()
        else:
            produit_id = self.viewmodel.creer_produit(
                categorie_id=categorie_id, nom=nom, prix=prix, stock=stock, description=description,
            )
            if produit_id and produit_id > 0:
                QMessageBox.information(
                    self, "Succes", f"Le produit '{nom}' a ete ajoute avec succes !"
                )
                self._charger_produits()
                self._reinitialiser_formulaire()

    def _reinitialiser_formulaire(self):
        self._mode_edition = False
        self._produit_id = None
        self.input_nom.clear()
        self.input_categorie.setCurrentIndex(0)
        self.spin_prix.setValue(0.00)
        self.spin_stock.setValue(0)
        self.input_description.clear()
        self.btn_ajouter.setText("Ajouter le produit")
