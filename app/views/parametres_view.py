"""Vue pour l'onglet Parametres."""

import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox, QDateEdit,
    QTableWidget, QTableWidgetItem, QScrollArea, QMessageBox,
    QCheckBox, QComboBox, QSpinBox, QListWidget, QDialog, QTextEdit,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from utils.styles import style_section, style_input, style_bouton, style_scroll_area, Couleurs
from viewmodels.parametres_vm import ParametresViewModel
from models.categorie_produit import CategorieProduitModel


class ParametresView(QWidget):
    """Onglet Parametres."""

    def __init__(self):
        super().__init__()
        self.viewmodel = ParametresViewModel()
        self.categorie_model = CategorieProduitModel()
        self._construire_ui()
        self._charger_donnees()

    def _construire_ui(self):
        # ScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(style_scroll_area())

        content = QWidget()
        content.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 20, 30, 30)

        # Section 1 : Informations de l'entreprise
        layout.addWidget(self._creer_section_entreprise())

        # Section 2 : Securite
        layout.addWidget(self._creer_section_securite())

        # Section 3 : Comptes email
        layout.addWidget(self._creer_section_email())

        # Section 4 : Attributs produits personnalisables
        layout.addWidget(self._creer_section_attributs_produits())

        # Section 5 : Categories de produits
        layout.addWidget(self._creer_section_categories_produits())

        # Section 6 : Configuration des champs clients
        layout.addWidget(self._creer_section_champs_clients())

        # Section 7 : Apparence
        layout.addWidget(self._creer_section_apparence())

        # Section 8 : Base de donnees
        layout.addWidget(self._creer_section_database())

        # Section 9 : Composition de la base de donnees
        layout.addWidget(self._creer_section_composition_db())

        layout.addStretch()
        content.setLayout(layout)

        scroll.setWidget(content)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def _creer_section_entreprise(self) -> QGroupBox:
        box = QGroupBox("Informations de l'entreprise")
        box.setStyleSheet(style_section())

        layout = QFormLayout()
        layout.setSpacing(15)

        self.input_nom_entreprise = QLineEdit()
        self.input_nom_entreprise.setStyleSheet(style_input())
        layout.addRow("Nom de l'entreprise :", self.input_nom_entreprise)

        self.input_date_creation = QDateEdit()
        self.input_date_creation.setCalendarPopup(True)
        self.input_date_creation.setDisplayFormat("dd/MM/yyyy")
        self.input_date_creation.setStyleSheet(style_input())
        layout.addRow("Date de creation :", self.input_date_creation)

        self.input_adresse_entreprise = QLineEdit()
        self.input_adresse_entreprise.setStyleSheet(style_input())
        layout.addRow("Adresse :", self.input_adresse_entreprise)

        self.input_telephone_entreprise = QLineEdit()
        self.input_telephone_entreprise.setStyleSheet(style_input())
        layout.addRow("Telephone :", self.input_telephone_entreprise)

        btn_save = QPushButton("Enregistrer")
        btn_save.setStyleSheet(style_bouton())
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self._sauvegarder_entreprise)
        layout.addRow("", btn_save)

        box.setLayout(layout)
        return box

    def _creer_section_securite(self) -> QGroupBox:
        box = QGroupBox("Securite")
        box.setStyleSheet(style_section())

        layout = QVBoxLayout()

        self.label_status_mdp = QLabel(
            "Gestion par mot de passe : Activee"
        )
        self.label_status_mdp.setStyleSheet(
            "font-size: 12pt; color: #333; font-weight: 600; margin-bottom: 10px;"
        )
        layout.addWidget(self.label_status_mdp)

        btn_layout = QHBoxLayout()

        self.btn_modifier_mdp = QPushButton("Modifier le mot de passe")
        self.btn_modifier_mdp.setStyleSheet(style_bouton())
        self.btn_modifier_mdp.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_modifier_mdp.clicked.connect(self._modifier_mot_de_passe)
        btn_layout.addWidget(self.btn_modifier_mdp)

        self.btn_desactiver_mdp = QPushButton("Desactiver le mot de passe")
        self.btn_desactiver_mdp.setStyleSheet(style_bouton(Couleurs.DANGER))
        self.btn_desactiver_mdp.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_desactiver_mdp.clicked.connect(self._desactiver_mot_de_passe)
        btn_layout.addWidget(self.btn_desactiver_mdp)

        layout.addLayout(btn_layout)

        email_layout = QFormLayout()
        self.input_email_recuperation = QLineEdit()
        self.input_email_recuperation.setStyleSheet(style_input())
        self.input_email_recuperation.setPlaceholderText("email@exemple.com")
        email_layout.addRow("Email de recuperation :", self.input_email_recuperation)
        layout.addLayout(email_layout)

        box.setLayout(layout)
        return box

    def _creer_section_email(self) -> QGroupBox:
        box = QGroupBox("Comptes email")
        box.setStyleSheet(style_section())

        layout = QVBoxLayout()

        self.table_comptes = QTableWidget()
        self.table_comptes.setColumnCount(4)
        self.table_comptes.setHorizontalHeaderLabels([
            "Adresse email", "Quota journalier", "Statut", "Actions",
        ])
        self.table_comptes.horizontalHeader().setStretchLastSection(True)
        self.table_comptes.setStyleSheet(
            "QTableWidget {"
            "    border: 2px solid #9E9E9E;"
            "    border-radius: 8px;"
            "    background-color: white;"
            "}"
            "QHeaderView::section {"
            "    background-color: #E3F2FD;"
            "    padding: 10px;"
            "    font-weight: bold;"
            "    border: none;"
            "}"
        )
        layout.addWidget(self.table_comptes)

        btn_add_email = QPushButton("Ajouter un compte email")
        btn_add_email.setStyleSheet(style_bouton())
        btn_add_email.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_email.clicked.connect(self._ajouter_compte_email)
        layout.addWidget(btn_add_email)

        box.setLayout(layout)
        return box

    def _creer_section_champs_clients(self) -> QGroupBox:
        box = QGroupBox("Configuration des champs clients")
        box.setStyleSheet(style_section())

        layout = QVBoxLayout()

        info_label = QLabel(
            "Choisissez quelles informations vous souhaitez collecter "
            "sur vos clients. Les champs coches apparaitront dans le "
            "formulaire de creation de client."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "color: #666; font-size: 11pt; margin-bottom: 15px;"
        )
        layout.addWidget(info_label)

        # Preset buttons
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Prereglages rapides :")
        preset_label.setStyleSheet("font-weight: 600;")
        preset_layout.addWidget(preset_label)

        btn_minimal = QPushButton("Minimal")
        btn_minimal.setStyleSheet(style_bouton(Couleurs.AVERTISSEMENT))
        btn_minimal.setCursor(Qt.CursorShape.PointingHandCursor)
        preset_layout.addWidget(btn_minimal)

        btn_standard = QPushButton("Standard")
        btn_standard.setStyleSheet(style_bouton(Couleurs.SUCCES))
        btn_standard.setCursor(Qt.CursorShape.PointingHandCursor)
        preset_layout.addWidget(btn_standard)

        btn_complet = QPushButton("Complet")
        btn_complet.setStyleSheet(style_bouton(Couleurs.PRIMAIRE))
        btn_complet.setCursor(Qt.CursorShape.PointingHandCursor)
        preset_layout.addWidget(btn_complet)

        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        # Checkboxes for fields
        champs = [
            ("Nom", True), ("Prenom", True), ("Date de naissance", True),
            ("Email", True), ("Telephone", True), ("Adresse", False),
            ("Ville", False), ("Code postal", False),
            ("Situation maritale", False), ("Profession", False),
            ("Centre d'interet", False), ("Photo", False),
            ("Notes personnalisees", False),
        ]

        self._checkboxes_champs = {}
        for nom, defaut in champs:
            cb = QCheckBox(nom)
            cb.setChecked(defaut)
            cb.setStyleSheet("font-size: 11pt; padding: 4px;")
            self._checkboxes_champs[nom] = cb
            layout.addWidget(cb)

        btn_save_champs = QPushButton("Enregistrer la configuration")
        btn_save_champs.setStyleSheet(style_bouton())
        btn_save_champs.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(btn_save_champs)

        box.setLayout(layout)
        return box

    def _creer_section_apparence(self) -> QGroupBox:
        box = QGroupBox("Apparence")
        box.setStyleSheet(style_section())

        layout = QFormLayout()
        layout.setSpacing(15)

        self.combo_monnaie = QComboBox()
        self.combo_monnaie.addItems(["EUR", "USD", "GBP", "CHF", "CAD", "XOF", "XAF"])
        self.combo_monnaie.setStyleSheet(style_input())
        layout.addRow("Monnaie :", self.combo_monnaie)

        self.combo_langue = QComboBox()
        self.combo_langue.addItems(["Francais", "English"])
        self.combo_langue.setStyleSheet(style_input())
        layout.addRow("Langue :", self.combo_langue)

        box.setLayout(layout)
        return box

    def _creer_section_database(self) -> QGroupBox:
        box = QGroupBox("Base de donnees")
        box.setStyleSheet(style_section())

        layout = QVBoxLayout()

        info_label = QLabel("Gestion de la base de donnees de l'application.")
        info_label.setStyleSheet("color: #666; font-size: 11pt; margin-bottom: 10px;")
        layout.addWidget(info_label)

        btn_layout = QHBoxLayout()

        btn_export = QPushButton("Exporter la base")
        btn_export.setStyleSheet(style_bouton(Couleurs.SUCCES))
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export.clicked.connect(self._exporter_base)
        btn_layout.addWidget(btn_export)

        btn_import = QPushButton("Importer une base")
        btn_import.setStyleSheet(style_bouton(Couleurs.AVERTISSEMENT))
        btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_import.clicked.connect(self._importer_base)
        btn_layout.addWidget(btn_import)

        btn_reset = QPushButton("Reinitialiser")
        btn_reset.setStyleSheet(style_bouton(Couleurs.DANGER))
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.clicked.connect(self._reinitialiser_base)
        btn_layout.addWidget(btn_reset)

        layout.addLayout(btn_layout)

        box.setLayout(layout)
        return box

    # ------------------------------------------------------------------ #
    #               Composition de la base de donnees                    #
    # ------------------------------------------------------------------ #

    def _creer_section_composition_db(self) -> QGroupBox:
        """Section pour configurer quelles informations supplementaires stocker."""
        box = QGroupBox("Composition de la base de donnees")
        box.setStyleSheet(style_section())

        layout = QVBoxLayout()

        info_label = QLabel(
            "Choisissez quelles informations complementaires vous souhaitez "
            "stocker pour vos clients. Ces champs seront visibles dans les "
            "fiches clients et le formulaire de creation."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "color: #666; font-size: 11pt; margin-bottom: 15px;"
        )
        layout.addWidget(info_label)

        champs_composition = [
            ("enfants", "Enfants (nombre, prenoms)"),
            ("parents", "Parents (nom, prenom, contact)"),
            ("conjoint", "Conjoint (nom, prenom, date naissance)"),
            ("situation_familiale", "Situation familiale detaillee"),
        ]

        self._checkboxes_composition = {}
        for cle, label in champs_composition:
            cb = QCheckBox(label)
            cb.setStyleSheet("font-size: 11pt; padding: 6px;")
            self._checkboxes_composition[cle] = cb
            layout.addWidget(cb)

        btn_save = QPushButton("Enregistrer la composition")
        btn_save.setStyleSheet(style_bouton())
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self._sauvegarder_composition_db)
        layout.addWidget(btn_save)

        box.setLayout(layout)

        # Charger l'etat sauvegarde
        self._charger_composition_db()

        return box

    def _charger_composition_db(self):
        """Charge la configuration de composition depuis les parametres."""
        raw = self.viewmodel.params_model.obtenir_parametre('composition_db')
        if raw:
            try:
                config = json.loads(raw)
                for cle, cb in self._checkboxes_composition.items():
                    cb.setChecked(config.get(cle, False))
            except (json.JSONDecodeError, TypeError):
                pass

    def _sauvegarder_composition_db(self):
        """Sauvegarde la configuration de composition dans les parametres."""
        config = {
            cle: cb.isChecked()
            for cle, cb in self._checkboxes_composition.items()
        }
        self.viewmodel.params_model.definir_parametre(
            'composition_db', json.dumps(config)
        )
        QMessageBox.information(
            self, "Succes", "Configuration de la base enregistree."
        )

    # ------------------------------------------------------------------ #
    #                  Attributs produits personnalisables                #
    # ------------------------------------------------------------------ #

    def _creer_section_attributs_produits(self) -> QGroupBox:
        """Section pour gerer les attributs personnalises des produits."""
        box = QGroupBox("Attributs produits personnalisables")
        box.setStyleSheet(style_section())

        layout = QVBoxLayout()

        info_label = QLabel(
            "Definissez les caracteristiques que vous souhaitez suivre pour vos produits "
            "(ex: Marque, Couleur, Taille, Matiere, etc.)"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 11pt; margin-bottom: 15px;")
        layout.addWidget(info_label)

        # Liste des attributs actuels
        self.list_attributs = QListWidget()
        self.list_attributs.setStyleSheet(
            "QListWidget {"
            "    border: 2px solid #9E9E9E;"
            "    border-radius: 8px;"
            "    padding: 5px;"
            "    font-size: 12pt;"
            "}"
        )
        layout.addWidget(self.list_attributs)

        # Formulaire d'ajout
        form_layout = QHBoxLayout()

        self.input_nouvel_attribut = QLineEdit()
        self.input_nouvel_attribut.setPlaceholderText(
            "Nom du nouvel attribut (ex: Marque)"
        )
        self.input_nouvel_attribut.setStyleSheet(style_input())
        form_layout.addWidget(self.input_nouvel_attribut)

        btn_ajouter = QPushButton("Ajouter")
        btn_ajouter.setStyleSheet(style_bouton())
        btn_ajouter.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ajouter.clicked.connect(self._ajouter_attribut)
        form_layout.addWidget(btn_ajouter)

        btn_supprimer = QPushButton("Supprimer")
        btn_supprimer.setStyleSheet(style_bouton(Couleurs.DANGER))
        btn_supprimer.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_supprimer.clicked.connect(self._supprimer_attribut)
        form_layout.addWidget(btn_supprimer)

        layout.addLayout(form_layout)

        box.setLayout(layout)

        # Charger les attributs existants
        self._charger_attributs()

        return box

    def _charger_attributs(self):
        """Charge les attributs globaux depuis la base de donnees."""
        attributs = self.viewmodel.lister_attributs()
        self.list_attributs.clear()
        for attr in attributs:
            self.list_attributs.addItem(attr['nom_attribut'])

    def _ajouter_attribut(self):
        """Ajoute un nouvel attribut global."""
        nom = self.input_nouvel_attribut.text().strip()

        if not nom:
            QMessageBox.warning(
                self, "Erreur", "Veuillez entrer un nom d'attribut."
            )
            return

        try:
            self.viewmodel.ajouter_attribut(nom)
            self._charger_attributs()
            self.input_nouvel_attribut.clear()
            QMessageBox.information(
                self, "Succes", f"Attribut '{nom}' ajoute avec succes."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur SQL",
                f"Impossible d'ajouter l'attribut.\n\nErreur : {str(e)}",
            )

    def _supprimer_attribut(self):
        """Supprime l'attribut selectionne."""
        item = self.list_attributs.currentItem()

        if not item:
            QMessageBox.warning(
                self, "Erreur",
                "Veuillez selectionner un attribut a supprimer.",
            )
            return

        nom = item.text()

        reponse = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous vraiment supprimer l'attribut '{nom}' ?\n"
            "Les valeurs associees seront egalement supprimees.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reponse == QMessageBox.Yes:
            try:
                self.viewmodel.supprimer_attribut(nom)
                self._charger_attributs()
                QMessageBox.information(
                    self, "Succes", f"Attribut '{nom}' supprime."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Erreur",
                    f"Erreur lors de la suppression : {e}",
                )

    # ------------------------------------------------------------------ #
    #               Section Categories Produits                            #
    # ------------------------------------------------------------------ #

    def _creer_section_categories_produits(self) -> QGroupBox:
        """Section pour gérer les catégories de produits."""
        box = QGroupBox("Catégories de produits")
        box.setStyleSheet(style_section())

        layout = QVBoxLayout()

        info_label = QLabel(
            "Organisez vos produits par catégories pour une meilleure gestion "
            "(ex: Électronique, Vêtements, Alimentation, etc.)"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 11pt; margin-bottom: 15px;")
        layout.addWidget(info_label)

        # Liste des catégories actuelles
        self.list_categories = QListWidget()
        self.list_categories.setStyleSheet(
            "QListWidget {"
            "    border: 2px solid #9E9E9E;"
            "    border-radius: 8px;"
            "    padding: 5px;"
            "    font-size: 12pt;"
            "}"
        )
        layout.addWidget(self.list_categories)

        # Boutons d'action
        btn_layout = QHBoxLayout()

        btn_ajouter = QPushButton("Ajouter une catégorie")
        btn_ajouter.setStyleSheet(style_bouton())
        btn_ajouter.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ajouter.clicked.connect(self._ajouter_categorie)
        btn_layout.addWidget(btn_ajouter)

        btn_supprimer = QPushButton("Supprimer")
        btn_supprimer.setStyleSheet(style_bouton(Couleurs.DANGER))
        btn_supprimer.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_supprimer.clicked.connect(self._supprimer_categorie)
        btn_layout.addWidget(btn_supprimer)

        layout.addLayout(btn_layout)

        box.setLayout(layout)

        # Charger les catégories existantes
        self._charger_categories()

        return box

    def _charger_categories(self):
        """Charge les catégories depuis la base de données."""
        categories = self.categorie_model.lister_categories(actives_uniquement=False)
        self.list_categories.clear()
        for cat in categories:
            nom = cat['nom']
            desc = cat.get('description', '')
            if desc:
                self.list_categories.addItem(f"{nom} - {desc}")
            else:
                self.list_categories.addItem(nom)

    def _ajouter_categorie(self):
        """Affiche un dialog pour ajouter une nouvelle catégorie."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Nouvelle catégorie")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        input_nom = QLineEdit()
        input_nom.setPlaceholderText("Ex: Électronique")
        input_nom.setStyleSheet(style_input())
        layout.addRow("Nom :", input_nom)

        input_desc = QTextEdit()
        input_desc.setPlaceholderText("Description optionnelle...")
        input_desc.setMaximumHeight(100)
        input_desc.setStyleSheet(style_input())
        layout.addRow("Description :", input_desc)

        btn_layout = QHBoxLayout()
        btn_valider = QPushButton("Créer")
        btn_valider.setStyleSheet(style_bouton())
        btn_valider.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_valider.clicked.connect(dialog.accept)

        btn_annuler = QPushButton("Annuler")
        btn_annuler.setStyleSheet(style_bouton(Couleurs.DANGER))
        btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_annuler.clicked.connect(dialog.reject)

        btn_layout.addWidget(btn_valider)
        btn_layout.addWidget(btn_annuler)
        layout.addRow(btn_layout)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.Accepted:
            nom = input_nom.text().strip()
            desc = input_desc.toPlainText().strip()

            if not nom:
                QMessageBox.warning(
                    self, "Erreur", "Veuillez entrer un nom de catégorie."
                )
                return

            try:
                categorie_id = self.categorie_model.ajouter_categorie(nom, desc)
                if categorie_id > 0:
                    self._charger_categories()
                    QMessageBox.information(
                        self, "Succès", f"Catégorie '{nom}' créée avec succès."
                    )
                else:
                    QMessageBox.warning(
                        self, "Erreur", "Impossible de créer la catégorie."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self, "Erreur SQL",
                    f"Impossible de créer la catégorie.\n\nErreur : {str(e)}"
                )

    def _supprimer_categorie(self):
        """Supprime la catégorie sélectionnée."""
        item = self.list_categories.currentItem()

        if not item:
            QMessageBox.warning(
                self, "Erreur",
                "Veuillez sélectionner une catégorie à supprimer."
            )
            return

        # Extraire le nom (avant " - " s'il y a une description)
        texte = item.text()
        nom = texte.split(" - ")[0] if " - " in texte else texte

        reponse = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous vraiment supprimer la catégorie '{nom}' ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reponse == QMessageBox.Yes:
            try:
                # Trouver l'ID de la catégorie par son nom
                categories = self.categorie_model.lister_categories(actives_uniquement=False)
                cat_id = None
                for cat in categories:
                    if cat['nom'] == nom:
                        cat_id = cat['id']
                        break

                if cat_id:
                    self.categorie_model.supprimer_categorie(cat_id)
                    self._charger_categories()
                    QMessageBox.information(
                        self, "Succès", f"Catégorie '{nom}' supprimée."
                    )
                else:
                    QMessageBox.warning(
                        self, "Erreur", "Catégorie introuvable."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self, "Erreur",
                    f"Erreur lors de la suppression : {e}"
                )

    # ------------------------------------------------------------------ #
    #                     Chargement des donnees                          #
    # ------------------------------------------------------------------ #

    def _charger_donnees(self):
        """Charge les valeurs existantes depuis la base de donnees."""
        donnees = self.viewmodel.charger_donnees()
        champs = {
            'nom_entreprise': self.input_nom_entreprise,
            'adresse_entreprise': self.input_adresse_entreprise,
            'telephone_entreprise': self.input_telephone_entreprise,
            'email_recuperation': self.input_email_recuperation,
        }
        for cle, widget in champs.items():
            if cle in donnees:
                widget.setText(donnees[cle])

    # ------------------------------------------------------------------ #
    #                         Actions                                     #
    # ------------------------------------------------------------------ #

    def _sauvegarder_entreprise(self):
        """Enregistre les informations de l'entreprise dans la base."""
        nom = self.input_nom_entreprise.text().strip()

        if not nom:
            QMessageBox.warning(
                self, "Erreur", "Le nom de l'entreprise est requis."
            )
            return

        donnees = {
            'nom_entreprise': nom,
            'adresse_entreprise': self.input_adresse_entreprise.text().strip(),
            'telephone_entreprise': self.input_telephone_entreprise.text().strip(),
        }

        if self.viewmodel.sauvegarder_entreprise(donnees):
            # Actualiser le header de la fenetre principale
            main_window = self.window()
            if hasattr(main_window, 'actualiser_nom_entreprise'):
                main_window.actualiser_nom_entreprise()

            QMessageBox.information(
                self, "Succes", "Informations de l'entreprise enregistrees."
            )

    def _modifier_mot_de_passe(self):
        QMessageBox.information(
            self, "Info", "Fonctionnalite de modification du mot de passe."
        )

    def _desactiver_mot_de_passe(self):
        reponse = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment desactiver le mot de passe patron ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reponse == QMessageBox.Yes:
            QMessageBox.information(self, "Info", "Mot de passe desactive.")

    def _ajouter_compte_email(self):
        QMessageBox.information(
            self, "Info", "Fonctionnalite d'ajout de compte email."
        )

    def _exporter_base(self):
        QMessageBox.information(self, "Info", "Export de la base de donnees.")

    def _importer_base(self):
        QMessageBox.information(self, "Info", "Import de la base de donnees.")

    def _reinitialiser_base(self):
        reponse = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment reinitialiser la base de donnees ?\n"
            "Toutes les donnees seront perdues.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reponse == QMessageBox.Yes:
            QMessageBox.information(
                self, "Info", "Base de donnees reinitialisee."
            )
