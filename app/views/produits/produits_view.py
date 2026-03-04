"""Vue pour l'onglet Produits avec toggle Liste/Creation et fiche detail."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QDoubleSpinBox,
    QTextEdit,
    QComboBox,
    QMessageBox,
    QScrollArea,
    QSpinBox,
    QAbstractSpinBox,
    QStackedWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from utils.styles import (
    style_section,
    style_input,
    style_bouton,
    style_spinbox,
    style_scroll_area,
    style_onglet,
    style_liste_selection,
    Couleurs,
)
from views.components.modern_segmented_control import ModernSegmentedControl
from views.components.produit_card import ProductCard
from viewmodels.produits_vm import ProduitsViewModel
from views.produits.fiche_produit_view import FicheProduitView


class ProduitsView(QWidget):
    """Vue pour la gestion des produits avec toggle Liste/Creation."""

    # Pages du stacked widget
    PAGE_LISTE = 0
    PAGE_CREATION = 1
    PAGE_FICHE = 2

    _PAGES = ["liste", "creation", "archives"]

    def _on_toggle_changed(self, index: int):
        """Appelé par le segmented control lors d'un changement d'onglet."""
        pages = self._pages_courantes()
        if index < len(pages):
            self._changer_page(pages[index])

    def _pages_courantes(self) -> list:
        """Retourne les pages disponibles selon le mode."""
        if self._mode_admin:
            return self._PAGES  # ["liste", "creation", "archives"]
        return ["liste", "archives"]

    def mettre_a_jour_mode(self, mode_admin: bool) -> None:
        """Met à jour la vue selon le mode administratif/fonctionnel."""
        # Récupérer la page AVANT de changer le mode
        pages_avant = self._pages_courantes()
        idx_avant = self._barre_toggle.current_index
        page_courante = (
            pages_avant[idx_avant] if idx_avant < len(pages_avant) else "liste"
        )

        self._mode_admin = mode_admin

        if mode_admin:
            labels = ["Liste", "Ajouter un produit", "Archives"]
        else:
            labels = ["Liste", "Archives"]

        pages_apres = self._pages_courantes()
        if page_courante not in pages_apres:
            page_courante = "liste"
        idx_cible = pages_apres.index(page_courante)

        ancien_toggle = self._barre_toggle
        self._layout_toggle.removeWidget(ancien_toggle)
        ancien_toggle.deleteLater()

        self._barre_toggle = ModernSegmentedControl(labels, initial_index=idx_cible)
        self._barre_toggle.selectionChanged.connect(self._on_toggle_changed)
        self._layout_toggle.insertWidget(1, self._barre_toggle)

        self._changer_page(page_courante)
        self._charger_produits()

        # Propager aux fiches
        self.fiche_produit.mettre_a_jour_mode(mode_admin)

    def __init__(self, parent=None):  # ← parent=None par défaut
        super().__init__(parent)
        self._mode_admin = True
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

        # === SEGMENTED CONTROL ===
        self._barre_toggle = ModernSegmentedControl(
            ["Liste", "Ajouter un produit", "Archives"]
        )
        self._barre_toggle.selectionChanged.connect(self._on_toggle_changed)

        self._layout_toggle = QHBoxLayout()
        self._layout_toggle.setContentsMargins(24, 16, 24, 8)
        self._layout_toggle.addStretch(1)
        self._layout_toggle.addWidget(self._barre_toggle)
        self._layout_toggle.addStretch(1)
        layout_principal.addLayout(self._layout_toggle)

        # === STACKED WIDGET ===
        self.pile = QStackedWidget()
        self.pile.addWidget(self._creer_page_liste())
        self.pile.addWidget(self._creer_page_creation())

        self.fiche_produit = FicheProduitView(viewmodel=self.viewmodel)
        self.fiche_produit.retour_demande.connect(lambda: self._changer_page("liste"))
        self.pile.addWidget(self.fiche_produit)

        layout_principal.addWidget(self.pile)
        self._changer_page("liste")

    def _changer_page(self, page: str):
        """Change de page dans le stack (liste/creation/archives/fiche)."""
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"=== Changement page : {page} ===")

        # Synchroniser le segmented control si appelé programmatiquement
        pages = self._pages_courantes()
        if page in pages:
            toggle_idx = pages.index(page)
            if self._barre_toggle.current_index != toggle_idx:
                self._barre_toggle.select(toggle_idx)

        if page == "liste":
            self.pile.setCurrentIndex(self.PAGE_LISTE)
            self._affiche_archives = False
            self._charger_produits()

        elif page == "creation":
            self._affiche_archives = False
            self.pile.setCurrentIndex(self.PAGE_CREATION)

        elif page == "archives":
            self.pile.setCurrentIndex(self.PAGE_LISTE)
            self._affiche_archives = True
            self._charger_produits()

        elif page == "fiche":
            self.pile.setCurrentIndex(self.PAGE_FICHE)

        logger.info(
            f"Page changée : index={self.pile.currentIndex()}, archives={self._affiche_archives}"
        )

        # Masquer le toggle sur la fiche
        self._barre_toggle.setVisible(page != "fiche")

    # ==================================================================
    # Page Liste
    # ==================================================================

    def _creer_page_liste(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # Barre de recherche unique
        self.input_recherche = QLineEdit()
        self.input_recherche.setPlaceholderText("🔍 Rechercher...")
        self.input_recherche.setStyleSheet(style_input())
        self.input_recherche.textChanged.connect(self._filtrer_produits)
        layout.addWidget(self.input_recherche)

        # Compteur
        self._label_nb_produits = QLabel()
        self._label_nb_produits.setStyleSheet(
            "color: #7f8c8d; font-size: 11pt; padding: 2px 0;"
        )
        layout.addWidget(self._label_nb_produits)

        # Zone scrollable de cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self._conteneur_cards = QWidget()
        self._layout_cards_produits = QVBoxLayout(self._conteneur_cards)
        self._layout_cards_produits.setContentsMargins(0, 0, 8, 0)
        self._layout_cards_produits.setSpacing(6)
        self._layout_cards_produits.addStretch()

        scroll.setWidget(self._conteneur_cards)
        layout.addWidget(scroll, stretch=1)

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

        # Photo du produit
        self.label_photo = QLabel("📦")
        self.label_photo.setFixedSize(150, 150)
        self.label_photo.setAlignment(Qt.AlignCenter)
        self.label_photo.setStyleSheet(
            "QLabel {"
            "    border: 2px dashed #9E9E9E;"
            "    border-radius: 8px;"
            "    background-color: #F5F5F5;"
            "    font-size: 48pt;"
            "}"
            "QLabel:hover {"
            "    background-color: #E3F2FD;"
            "    border-color: #2196F3;"
            "}"
        )
        self.label_photo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.label_photo.mousePressEvent = lambda e: self._choisir_photo_produit()
        self.photo_path = None
        form.addRow("Photo :", self.label_photo)

        groupe.setLayout(form)
        return groupe

    def _creer_section_attributs(self) -> QWidget:
        """Section pour les attributs personnalises du produit."""
        conteneur = QWidget()
        conteneur_layout = QVBoxLayout(conteneur)
        conteneur_layout.setSpacing(8)
        conteneur_layout.setContentsMargins(0, 0, 0, 0)

        # Header avec titre et bouton Actualiser
        header_layout = QHBoxLayout()

        titre = QLabel("Caracteristiques supplementaires")
        titre.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333;")
        header_layout.addWidget(titre)

        header_layout.addStretch()

        btn_actualiser = QPushButton("⟳ Actualiser")
        btn_actualiser.setStyleSheet(
            "QPushButton {"
            "    background-color: #2196F3;"
            "    color: white;"
            "    border: none;"
            "    border-radius: 6px;"
            "    padding: 6px 12px;"
            "    font-size: 11pt;"
            "}"
            "QPushButton:hover {"
            "    background-color: #1976D2;"
            "}"
        )
        btn_actualiser.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_actualiser.clicked.connect(self._recharger_attributs)
        header_layout.addWidget(btn_actualiser)

        conteneur_layout.addLayout(header_layout)

        # Groupe avec les attributs
        self.groupe_attributs = QGroupBox()
        self.groupe_attributs.setStyleSheet(style_section())

        self._remplir_attributs()

        conteneur_layout.addWidget(self.groupe_attributs)

        return conteneur

    def _remplir_attributs(self):
        """Remplit la section attributs avec les champs dynamiques."""
        layout = QVBoxLayout()

        attributs = self.viewmodel.lister_attributs_globaux()

        self.attributs_widgets = {}

        for attr in attributs:
            nom_attr = attr["nom_attribut"]

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

        self.groupe_attributs.setLayout(layout)

    def _recharger_attributs(self):
        """Recharge la section des attributs depuis la base de donnees."""
        # Supprimer l'ancien layout
        old_layout = self.groupe_attributs.layout()
        if old_layout:
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    while item.layout().count():
                        sub_item = item.layout().takeAt(0)
                        if sub_item.widget():
                            sub_item.widget().deleteLater()
            QWidget().setLayout(old_layout)

        # Recréer les attributs
        self._remplir_attributs()

    def _choisir_photo_produit(self):
        """Ouvre un QFileDialog pour sélectionner une image de produit."""
        from PySide6.QtWidgets import QFileDialog
        from PySide6.QtGui import QPixmap

        chemin, _ = QFileDialog.getOpenFileName(
            self, "Choisir une image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if chemin:
            # Stocker le chemin
            self.photo_path = chemin

            # Afficher l'image dans le label
            pixmap = QPixmap(chemin)
            if not pixmap.isNull():
                # Redimensionner l'image en gardant le ratio
                pixmap_scaled = pixmap.scaled(
                    150,
                    150,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.label_photo.setPixmap(pixmap_scaled)
                self.label_photo.setStyleSheet(
                    "QLabel {"
                    "    border: 2px solid #2196F3;"
                    "    border-radius: 8px;"
                    "    background-color: #F5F5F5;"
                    "}"
                    "QLabel:hover {"
                    "    background-color: #E3F2FD;"
                    "}"
                )

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
        """Charge les catégories dans le combo du formulaire ET dans le filtre liste."""
        # --- Combo formulaire (création) ---
        self.input_categorie.clear()
        self.input_categorie.addItem("— Sans catégorie —", None)
        categories = self.viewmodel.lister_categories()
        for cat in categories:
            self.input_categorie.addItem(cat["nom"], cat["id"])

        # --- Combo filtre liste ---
        if hasattr(self, "_combo_filtre_categorie"):
            self._combo_filtre_categorie.blockSignals(True)
            self._combo_filtre_categorie.clear()
            self._combo_filtre_categorie.addItem("Toutes les catégories", None)
            for cat in categories:
                self._combo_filtre_categorie.addItem(cat["nom"], cat["id"])
            self._combo_filtre_categorie.blockSignals(False)

    def _charger_produits(self):
        """Charge et filtre les produits via la barre de recherche multi-termes."""
        terme = (
            self.input_recherche.text().strip()
            if hasattr(self, "input_recherche")
            else ""
        )
        termes = [t for t in terme.split() if t]

        # Récupération complète depuis le viewmodel
        produits = self.viewmodel.lister_produits(archives=self._affiche_archives)

        # Filtrage multi-termes côté client
        if termes:
            produits = self._filtrer_par_termes(produits, termes)

        # Compteur
        if hasattr(self, "_label_nb_produits"):
            suffix = " archivé(s)" if self._affiche_archives else ""
            self._label_nb_produits.setText(f"{len(produits)} produit(s){suffix}")

        if not hasattr(self, "_layout_cards_produits"):
            return

        # Nettoyage
        while self._layout_cards_produits.count() > 1:
            item = self._layout_cards_produits.takeAt(0)
            if w := item.widget():
                w.deleteLater()

        # État vide
        if not produits:
            lbl = QLabel("Aucun produit trouvé.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #BBBBBB; font-size: 13pt; padding: 40px;")
            self._layout_cards_produits.insertWidget(0, lbl)
            return

        # Création des cards
        for produit in produits:
            # Attributs du produit (si le viewmodel les fournit)
            attributs = produit.get("attributs") or []

            card = ProductCard(
                produit,
                search_terms=termes,
                show_actions=self._mode_admin,
                is_archive=self._affiche_archives,
                attributs=attributs,
            )
            card.double_clicked.connect(self._voir_produit)
            card.action_archiver.connect(self._archiver_produit)
            card.action_restaurer.connect(self._desarchiver_produit)
            card.action_supprimer.connect(self._supprimer_produit)

            self._layout_cards_produits.insertWidget(
                self._layout_cards_produits.count() - 1, card
            )

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
            self._voir_produit(produits[0]["id"])

    # ==================================================================
    # Actions
    # ==================================================================

    def _voir_produit(self, produit_id: int):
        """Affiche la fiche detail d'un produit."""
        self.fiche_produit.charger_produit(produit_id)
        self._changer_page("fiche")

    def ouvrir_fiche(self, produit_id: int):
        """Point d'entrée public pour ouvrir une fiche produit depuis l'extérieur."""
        self._voir_produit(produit_id)

    def _editer_produit(self, produit_id: int):
        """Charge un produit pour edition."""
        produit = self.viewmodel.obtenir_produit(produit_id)
        if not produit:
            return

        self._mode_edition = True
        self._produit_id = produit_id

        self.input_nom.setText(produit["nom"])
        self.spin_prix.setValue(produit.get("prix", 0))
        self.spin_stock.setValue(produit.get("stock", 0) or 0)
        self.input_description.setPlainText(produit.get("description", "") or "")

        categorie_id = produit.get("categorie_id")
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
            self,
            "Confirmation",
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
            QMessageBox.warning(self, "Attention", "Veuillez saisir un nom de produit.")
            return

        prix = self.spin_prix.value()
        if prix <= 0:
            QMessageBox.warning(self, "Attention", "Le prix doit etre superieur a 0.")
            return

        categorie_id = self.input_categorie.currentData()
        stock = self.spin_stock.value()
        description = self.input_description.toPlainText().strip()

        if self._mode_edition and self._produit_id:
            succes = self.viewmodel.modifier_produit(
                self._produit_id,
                {
                    "nom": nom,
                    "categorie_id": categorie_id,
                    "prix": prix,
                    "stock": stock,
                    "description": description,
                    "photo": self.photo_path,
                },
            )
            if succes:
                QMessageBox.information(self, "Succes", "Produit modifie avec succes !")
                self._reinitialiser_formulaire()
                self._changer_page("liste")
        else:
            produit_id = self.viewmodel.creer_produit(
                categorie_id=categorie_id,
                nom=nom,
                prix=prix,
                stock=stock,
                description=description,
                photo=self.photo_path,
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

        # Réinitialiser la photo
        self.photo_path = None
        self.label_photo.clear()
        self.label_photo.setText("📦")
        self.label_photo.setStyleSheet(
            "QLabel {"
            "    border: 2px dashed #9E9E9E;"
            "    border-radius: 8px;"
            "    background-color: #F5F5F5;"
            "    font-size: 48pt;"
            "}"
            "QLabel:hover {"
            "    background-color: #E3F2FD;"
            "    border-color: #2196F3;"
            "}"
        )

    def _reset_filtres(self):
        """Réinitialise la recherche et tous les filtres de la liste."""
        if hasattr(self, "_combo_filtre_categorie"):
            self._combo_filtre_categorie.blockSignals(True)
            self._combo_filtre_categorie.setCurrentIndex(0)
            self._combo_filtre_categorie.blockSignals(False)
        if hasattr(self, "_spin_prix_min"):
            self._spin_prix_min.blockSignals(True)
            self._spin_prix_min.setValue(0)
            self._spin_prix_min.blockSignals(False)
        if hasattr(self, "_spin_prix_max"):
            self._spin_prix_max.blockSignals(True)
            self._spin_prix_max.setValue(999999)
            self._spin_prix_max.blockSignals(False)
        # Vider la recherche déclenche automatiquement _filtrer_produits
        if hasattr(self, "input_recherche"):
            self.input_recherche.clear()
        else:
            self._charger_produits()

    def _filtrer_par_termes(self, produits: list, termes: list[str]) -> list:
        """Chaque terme doit correspondre à au moins un champ du produit.

        Champs testés : nom, catégorie, prix (partie entière), valeurs d'attributs.
        """
        resultat = []
        for p in produits:
            nom = (p.get("nom") or "").lower()
            categorie = (p.get("categorie_nom") or "").lower()
            prix = p.get("prix") or 0.0
            attrs_vals = [
                (a.get("valeur") or "").lower() for a in (p.get("attributs") or [])
            ]

            tout_matche = True
            for t in termes:
                tl = t.lower()

                # Texte : nom ou catégorie
                if tl in nom or tl in categorie:
                    continue

                # Attributs
                if any(tl in v for v in attrs_vals):
                    continue

                # Prix : "10" → produits à 10.xx€, "10.5" → 10.50€ exact
                try:
                    t_float = float(t.replace(",", "."))
                    if int(prix) == int(t_float):  # même partie entière
                        continue
                    if abs(prix - t_float) < 0.005:  # prix exact
                        continue
                except ValueError:
                    pass

                tout_matche = False
                break

            if tout_matche:
                resultat.append(p)

        return resultat
