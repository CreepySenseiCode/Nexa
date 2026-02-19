"""Formulaire client reutilisable avec architecture heritee.

Ce module fournit FormulaireClientBase, une classe de base abstraite
contenant toute la logique de construction et de gestion du formulaire client.

Les sous-classes (FormulaireCreationClient, FormulaireEditionClient)
n'implementent que les differences (barre de boutons, titre).
"""

import os
import re
import shutil
import time
from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QDateEdit,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QGroupBox,
    QPushButton,
    QTextEdit,
    QScrollArea,
    QProgressBar,
    QMessageBox,
    QFrame,
    QFileDialog,
    QAbstractSpinBox,
)
from PySide6.QtCore import Qt, QDate, QRect, Signal
from PySide6.QtGui import (
    QFont,
    QPixmap,
    QPainter,
    QPainterPath,
    QPen,
    QLinearGradient,
    QColor,
)

from models.centre_interet import CentreInteretModel
from viewmodels.client_vm import ClientViewModel
from utils.formatters import calculer_age
from utils.validators import valider_email
from utils.styles import style_input, style_bouton, Couleurs


# ============================================================================
# Widget de tags pour les centres d'interet
# ============================================================================


class CentresInteretWidget(QWidget):
    """Widget de type tags pour la saisie de centres d'interet.

    Permet d'ajouter des tags via un champ texte + bouton, et de les
    supprimer en cliquant sur le bouton X de chaque tag.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tags: list[str] = []
        self._construire_ui()

    def _construire_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(6)

        # Zone de saisie
        layout_saisie = QHBoxLayout()
        layout_saisie.setSpacing(6)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Ajouter un centre d'interet...")
        self._input.returnPressed.connect(self._ajouter_tag)
        layout_saisie.addWidget(self._input)

        self._btn_ajouter = QPushButton("+")
        self._btn_ajouter.setFixedSize(35, 35)
        self._btn_ajouter.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_ajouter.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "border-radius: 4px; border: none; font-size: 16pt; font-weight: bold; }"
            "QPushButton:hover { background-color: #1976D2; }"
        )
        self._btn_ajouter.clicked.connect(self._ajouter_tag)
        layout_saisie.addWidget(self._btn_ajouter)

        layout_principal.addLayout(layout_saisie)

        # Zone d'affichage des tags (flow layout simule)
        self._conteneur_tags = QWidget()
        self._layout_tags = QHBoxLayout(self._conteneur_tags)
        self._layout_tags.setContentsMargins(0, 0, 0, 0)
        self._layout_tags.setSpacing(4)
        self._layout_tags.addStretch()
        layout_principal.addWidget(self._conteneur_tags)

    def _ajouter_tag(self):
        texte = self._input.text().strip()
        if not texte:
            return
        # Eviter les doublons (insensible a la casse)
        if texte.lower() in [t.lower() for t in self._tags]:
            self._input.clear()
            return
        self._tags.append(texte)
        self._input.clear()
        self._rafraichir_tags()

    def _supprimer_tag(self, nom: str):
        self._tags = [t for t in self._tags if t != nom]
        self._rafraichir_tags()

    def _rafraichir_tags(self):
        # Vider le layout actuel (sauf le stretch)
        while self._layout_tags.count() > 0:
            item = self._layout_tags.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # Recreer les tags
        for nom in self._tags:
            tag = QPushButton(f"  {nom}  x")
            tag.setCursor(Qt.CursorShape.PointingHandCursor)
            tag.setStyleSheet(
                "QPushButton { background-color: #E3F2FD; color: #1565C0; "
                "border: 1px solid #90CAF9; border-radius: 12px; "
                "padding: 4px 10px; font-size: 11pt; }"
                "QPushButton:hover { background-color: #BBDEFB; }"
            )
            tag.clicked.connect(lambda checked, n=nom: self._supprimer_tag(n))
            self._layout_tags.addWidget(tag)

        self._layout_tags.addStretch()

    # --- API publique ---

    def obtenir_centres(self) -> list[str]:
        """Retourne la liste des centres d'interet saisis."""
        return list(self._tags)

    def definir_centres(self, noms: list[str]):
        """Definit la liste des centres d'interet (remplace les existants)."""
        self._tags = list(noms)
        self._rafraichir_tags()

    def vider(self):
        """Vide tous les tags."""
        self._tags.clear()
        self._rafraichir_tags()


# ============================================================================
# Classe de base pour les formulaires client
# ============================================================================


class FormulaireClientBase(QWidget):
    """Classe de base abstraite pour les formulaires client (creation/edition).

    Contient toute la logique de construction du formulaire :
    - Section photo de profil
    - Informations generales (nom, prenom, date naissance, adresse)
    - Coordonnees (email, telephone)
    - Situation familiale (conjoint, enfants, parents)
    - Informations supplementaires (centres d'interet, notes)
    - Indicateur de completion

    Signaux:
        client_sauvegarde (int): Emis lors de la sauvegarde (id du client)

    Methodes abstraites (a implementer par les sous-classes):
        _construire_barre_boutons(): Cree les boutons d'action specifiques
        _obtenir_titre(): Retourne le titre du formulaire
    """

    # Signaux
    client_sauvegarde = Signal(int)

    def __init__(self, viewmodel: ClientViewModel, parent=None):
        """Initialise le formulaire client.

        Args:
            viewmodel: Instance de ClientViewModel pour la logique metier
            parent: Widget parent (optionnel)
        """
        super().__init__(parent)
        self.viewmodel = viewmodel

        # ID du client en cours d'edition (None pour creation)
        self._client_id: Optional[int] = None

        # Liste pour stocker les formulaires enfants dynamiques
        self._formulaires_enfants: list[dict] = []

        # Construire l'interface
        self._construire_ui()

        # Connecter les signaux
        self._connecter_signaux()

    # ==================================================================
    # Construction de l'interface
    # ==================================================================

    def _construire_ui(self):
        """Construit l'interface complete du formulaire."""
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # --- Zone scrollable ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Widget conteneur pour le scroll
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(20, 20, 20, 20)
        self.scroll_layout.setSpacing(10)

        # --- Section : Photo de profil ---
        self._construire_section_photo()

        # --- Section : Informations generales ---
        self._construire_section_infos_generales()

        # --- Section : Coordonnees ---
        self._construire_section_coordonnees()

        # --- Section : Situation familiale ---
        self._construire_section_situation_familiale()

        # --- Section : Informations supplementaires ---
        self._construire_section_infos_supplementaires()

        # --- Indicateur de completude ---
        self._construire_indicateur_completude()

        # Espacement flexible en bas
        self.scroll_layout.addStretch()

        # Finaliser le scroll
        self.scroll_area.setWidget(self.scroll_widget)
        layout_principal.addWidget(self.scroll_area)

        # --- Barre de boutons (definie par la sous-classe) ---
        self._construire_barre_boutons(layout_principal)

    # ------------------------------------------------------------------
    # Methodes abstraites
    # ------------------------------------------------------------------

    def annuler(self):
        """Annule la saisie et réinitialise le formulaire."""
        reponse = QMessageBox.question(
            self,
            "Annuler",
            "Êtes-vous sûr de vouloir annuler ? Toutes les modifications seront perdues.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reponse == QMessageBox.StandardButton.Yes:
            self.vider_formulaire()

    def sauvegarder(self):
        """Sauvegarde le client (création ou modification)."""
        # Collecter les données du formulaire
        donnees = self._collecter_donnees()

        if not donnees:
            return  # Erreurs déjà affichées par _collecter_donnees

        try:
            if self._client_id:
                # Modification
                succes = self.viewmodel.modifier_client(self._client_id, donnees)
                message = "Client modifié avec succès !"
            else:
                # Création
                client_id = self.viewmodel.creer_client(donnees)
                succes = client_id is not None
                self._client_id = client_id
                message = "Client créé avec succès !"

            if succes:
                QMessageBox.information(self, "Succès", message)
                self.client_sauvegarde.emit(self._client_id)
                self.vider_formulaire()
            else:
                QMessageBox.warning(
                    self, "Erreur", "Impossible de sauvegarder le client."
                )

        except Exception as e:
            QMessageBox.critical(
                self, "Erreur", f"Erreur lors de la sauvegarde : {str(e)}"
            )

    def _collecter_donnees(self) -> dict:
        """Collecte toutes les données du formulaire."""
        # Validation du nom
        nom = self.input_nom.text().strip()
        if not nom:
            QMessageBox.warning(self, "Validation", "Le nom est obligatoire.")
            self.input_nom.setFocus()
            return None

        # Validation de l'email
        email = self.input_email.text().strip()
        if email and not valider_email(email):
            QMessageBox.warning(self, "Validation", "L'adresse email est invalide.")
            self.input_email.setFocus()
            return None

        # Collecter les données de base
        donnees = {
            "nom": nom.upper(),
            "prenom": self.input_prenom.text().strip(),
            "email": email,
            "telephone": self.input_telephone.text().strip(),
            "adresse_rue": self.input_adresse.text().strip(),
            "adresse_ville": self.input_ville.text().strip(),
            "adresse_cp": self.input_code_postal.text().strip(),
            "situation_familiale": self.combo_situation.currentText(),
            "notes": (
                self.input_notes.toPlainText().strip()
                if hasattr(self, "input_notes")
                else ""
            ),
            "photo_path": self._photo_path if hasattr(self, "_photo_path") else "",
        }

        # Date de naissance
        if self.input_date_naissance.date() != QDate(1900, 1, 1):
            donnees["date_naissance"] = self.input_date_naissance.date().toString(
                "yyyy-MM-dd"
            )

        # Centres d'intérêt
        if hasattr(self, "widget_centres_interet"):
            centres = self.widget_centres_interet.obtenir_centres()
            donnees["centres_interet"] = ",".join(centres) if centres else ""

        return donnees

    def charger_client(self, client_id: int):
        """Charge un client pour édition."""
        self._client_id = client_id

        # Utiliser le model directement
        from models.client import ClientModel

        model = ClientModel()
        client = model.obtenir_client(client_id)

        if not client:
            QMessageBox.warning(self, "Erreur", f"Client {client_id} introuvable.")
            return

        # Remplir les champs
        self.input_nom.setText(client.get("nom", ""))
        self.input_prenom.setText(client.get("prenom", ""))
        self.input_email.setText(client.get("email", ""))
        self.input_telephone.setText(client.get("telephone", ""))
        self.input_adresse.setText(client.get("adresse_rue", ""))
        self.input_ville.setText(client.get("adresse_ville", ""))
        self.input_code_postal.setText(client.get("adresse_cp", ""))

        # Date de naissance
        if client.get("date_naissance"):
            date = QDate.fromString(client["date_naissance"], "yyyy-MM-dd")
            if date.isValid():
                self.input_date_naissance.setDate(date)

        # Situation familiale
        if client.get("situation_familiale"):
            index = self.combo_situation.findText(client["situation_familiale"])
            if index >= 0:
                self.combo_situation.setCurrentIndex(index)

        # Profession
        if hasattr(self, "input_profession") and client.get("profession"):
            self.input_profession.setText(client["profession"])

        # Notes
        if hasattr(self, "input_notes") and client.get("notes"):
            self.input_notes.setPlainText(client["notes"])

        # Photo
        if client.get("photo_path"):
            import os

            photo_path = client["photo_path"]
            # Vérifier si c'est un chemin absolu ou relatif
            if not os.path.isabs(photo_path):
                # Chemin relatif depuis le dossier app
                photo_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    photo_path,
                )

            if os.path.exists(photo_path):
                self._photo_path = photo_path
                pixmap = QPixmap(photo_path)
                if not pixmap.isNull():
                    self.afficher_photo_pixmap(pixmap)

    def supprimer_photo(self):
        """Supprime la photo de profil."""
        self._photo_path = ""
        self.label_photo.setPixmap(QPixmap())
        self.label_photo.setText("\U0001f464")
        self.label_photo.setFont(QFont("Arial", 80))
        self.label_photo.setStyleSheet(
            "QLabel { border: 3px solid #2196F3; border-radius: 90px; "
            "background-color: white; color: #BDBDBD; }"
        )

    def vider_formulaire(self):
        """Vide tous les champs du formulaire."""
        self._client_id = None
        self.input_nom.clear()
        self.input_prenom.clear()
        self.input_email.clear()
        self.input_telephone.clear()
        self.input_adresse.clear()
        self.input_ville.clear()
        self.input_code_postal.clear()
        self.input_date_naissance.setDate(QDate(1900, 1, 1))
        self.combo_situation.setCurrentIndex(0)

        if hasattr(self, "input_notes"):
            self.input_notes.clear()

        if hasattr(self, "widget_centres_interet"):
            self.widget_centres_interet.vider()

        # Réinitialiser la photo
        self.supprimer_photo()

    def _construire_barre_boutons(self, layout_parent):
        """Construit la barre de boutons d'action du formulaire.

        A implementer par les sous-classes selon leurs besoins.

        Args:
            layout_parent: Layout principal ou ajouter la barre
        """
        raise NotImplementedError(
            "Les sous-classes doivent implementer _construire_barre_boutons()"
        )

    def _obtenir_titre(self) -> str:
        """Retourne le titre du formulaire.

        A implementer par les sous-classes.

        Returns:
            Titre a afficher en haut du formulaire
        """
        raise NotImplementedError(
            "Les sous-classes doivent implementer _obtenir_titre()"
        )

    # ------------------------------------------------------------------
    # Section : Photo de profil (centree)
    # ------------------------------------------------------------------

    def _construire_section_photo(self):
        """Construit la section photo de profil avec photo cliquable et hover effect."""
        container = QWidget()
        container.setFixedSize(200, 200)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self._photo_path = ""

        # Label photo (cliquable)
        self.label_photo = QLabel()
        self.label_photo.setFixedSize(180, 180)
        self.label_photo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Photo par defaut (silhouette)
        self.label_photo.setText("\U0001f464")
        self.label_photo.setFont(QFont("Arial", 80))
        self.label_photo.setStyleSheet(
            "QLabel { border: 3px solid #2196F3; border-radius: 90px; "
            "background-color: white; color: #BDBDBD; }"
        )

        # Rendre cliquable avec mousePressEvent
        self.label_photo.mousePressEvent = lambda event: self._choisir_photo()
        self.label_photo.setCursor(Qt.CursorShape.PointingHandCursor)

        # Hover effect
        self.label_photo.enterEvent = lambda event: self._photo_hover_enter()
        self.label_photo.leaveEvent = lambda event: self._photo_hover_leave()

        layout.addWidget(self.label_photo, alignment=Qt.AlignmentFlag.AlignCenter)

        self.scroll_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)

    # ------------------------------------------------------------------
    # Section : Informations generales (grille cote a cote)
    # ------------------------------------------------------------------

    def _construire_section_infos_generales(self):
        """Construit la section Informations generales avec champs cote a cote."""
        groupe = QGroupBox("Informations generales")
        font_section = QFont()
        font_section.setPointSize(14)
        font_section.setWeight(QFont.Weight.DemiBold)
        groupe.setFont(font_section)
        groupe.setStyleSheet(
            "QGroupBox {"
            "    font-size: 13pt; font-weight: 600; color: #1976D2;"
            "    border: 2px solid #2196F3; border-radius: 12px;"
            "    background-color: #FAFAFA; padding: 25px; margin-top: 20px;"
            "}"
            "QGroupBox::title {"
            "    subcontrol-origin: margin; left: 20px; padding: 0 10px;"
            "    background-color: white; border-radius: 4px;"
            "}"
        )

        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setContentsMargins(15, 20, 15, 15)

        font_corps = QFont()
        font_corps.setPointSize(12)

        font_label = QFont()
        font_label.setPointSize(11)
        font_label.setWeight(QFont.Weight.DemiBold)

        style_label = "color: #555555;"
        si = (
            "QLineEdit { border: 1px solid #E0E0E0; border-radius: 6px; "
            "padding: 8px 12px; background-color: #FAFAFA; }"
            "QLineEdit:focus { border: 2px solid #2196F3; background-color: #FFFFFF; }"
        )
        style_date = (
            "QDateEdit { border: 1px solid #E0E0E0; border-radius: 6px; "
            "padding: 8px 12px; background-color: #FAFAFA; }"
            "QDateEdit:focus { border: 2px solid #2196F3; background-color: #FFFFFF; }"
        )

        row = 0
        # --- Ligne 1 : Nom | Prenom ---
        lbl_nom = QLabel("Nom :")
        lbl_nom.setFont(font_label)
        lbl_nom.setStyleSheet(style_label)
        grid.addWidget(lbl_nom, row, 0)

        self.input_nom = QLineEdit()
        self.input_nom.setFont(font_corps)
        self.input_nom.setPlaceholderText("NOM")
        self.input_nom.setStyleSheet(si)
        self.input_nom.setMinimumHeight(38)
        grid.addWidget(self.input_nom, row, 1)

        lbl_prenom = QLabel("Prenom :")
        lbl_prenom.setFont(font_label)
        lbl_prenom.setStyleSheet(style_label)
        grid.addWidget(lbl_prenom, row, 2)

        self.input_prenom = QLineEdit()
        self.input_prenom.setFont(font_corps)
        self.input_prenom.setPlaceholderText("Prenom")
        self.input_prenom.setStyleSheet(si)
        self.input_prenom.setMinimumHeight(38)
        grid.addWidget(self.input_prenom, row, 3)

        row += 1
        # --- Ligne 2 : Date naissance | Age ---
        lbl_naissance = QLabel("Date de naissance :")
        lbl_naissance.setFont(font_label)
        lbl_naissance.setStyleSheet(style_label)
        grid.addWidget(lbl_naissance, row, 0)

        self.input_date_naissance = QDateEdit()
        self.input_date_naissance.setFont(font_corps)
        self.input_date_naissance.setCalendarPopup(True)
        self.input_date_naissance.setDisplayFormat("dd/MM/yyyy")
        self.input_date_naissance.setMinimumDate(QDate(1900, 1, 1))
        self.input_date_naissance.setSpecialValueText("Non renseignee")
        self.input_date_naissance.setDate(QDate(1900, 1, 1))
        self.input_date_naissance.setStyleSheet(style_date)
        self.input_date_naissance.setMinimumHeight(38)
        grid.addWidget(self.input_date_naissance, row, 1)

        lbl_age = QLabel("Age :")
        lbl_age.setFont(font_label)
        lbl_age.setStyleSheet(style_label)
        grid.addWidget(lbl_age, row, 2)

        self.label_age = QLabel("\u2014 ans")
        self.label_age.setFont(QFont("", 13, QFont.Weight.Bold))
        self.label_age.setStyleSheet("color: #1976D2;")
        grid.addWidget(self.label_age, row, 3)

        row += 1
        # --- Ligne 3 : Adresse (toute la largeur) ---
        lbl_adresse = QLabel("Adresse :")
        lbl_adresse.setFont(font_label)
        lbl_adresse.setStyleSheet(style_label)
        grid.addWidget(lbl_adresse, row, 0)

        self.input_adresse = QLineEdit()
        self.input_adresse.setFont(font_corps)
        self.input_adresse.setPlaceholderText("Adresse")
        self.input_adresse.setStyleSheet(si)
        self.input_adresse.setMinimumHeight(38)
        grid.addWidget(self.input_adresse, row, 1, 1, 3)

        row += 1
        # --- Ligne 4 : Ville | Code postal ---
        lbl_ville = QLabel("Ville :")
        lbl_ville.setFont(font_label)
        lbl_ville.setStyleSheet(style_label)
        grid.addWidget(lbl_ville, row, 0)

        self.input_ville = QLineEdit()
        self.input_ville.setFont(font_corps)
        self.input_ville.setPlaceholderText("Ville")
        self.input_ville.setStyleSheet(si)
        self.input_ville.setMinimumHeight(38)
        grid.addWidget(self.input_ville, row, 1)

        lbl_cp = QLabel("Code postal :")
        lbl_cp.setFont(font_label)
        lbl_cp.setStyleSheet(style_label)
        grid.addWidget(lbl_cp, row, 2)

        self.input_code_postal = QLineEdit()
        self.input_code_postal.setFont(font_corps)
        self.input_code_postal.setMaxLength(5)
        self.input_code_postal.setPlaceholderText("75000")
        self.input_code_postal.setStyleSheet(si)
        self.input_code_postal.setMinimumHeight(38)
        grid.addWidget(self.input_code_postal, row, 3)

        # Colonnes 1 et 3 extensibles pour remplir l'espace
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        groupe.setLayout(grid)
        self.scroll_layout.addWidget(groupe)

    # ------------------------------------------------------------------
    # Section : Coordonnees
    # ------------------------------------------------------------------

    def _construire_section_coordonnees(self):
        """Construit la section Coordonnees (email + telephone)."""
        groupe = QGroupBox("Coordonnees")
        font_section = QFont()
        font_section.setPointSize(14)
        font_section.setWeight(QFont.Weight.DemiBold)
        groupe.setFont(font_section)
        groupe.setStyleSheet(
            "QGroupBox {"
            "    font-size: 13pt; font-weight: 600; color: #1976D2;"
            "    border: 2px solid #2196F3; border-radius: 12px;"
            "    background-color: #FAFAFA; padding: 25px; margin-top: 20px;"
            "}"
            "QGroupBox::title {"
            "    subcontrol-origin: margin; left: 20px; padding: 0 10px;"
            "    background-color: white; border-radius: 4px;"
            "}"
        )

        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setContentsMargins(15, 20, 15, 15)

        font_corps = QFont()
        font_corps.setPointSize(12)

        font_label = QFont()
        font_label.setPointSize(11)
        font_label.setWeight(QFont.Weight.DemiBold)

        style_label = "color: #555555;"
        si = (
            "QLineEdit { border: 1px solid #E0E0E0; border-radius: 6px; "
            "padding: 8px 12px; background-color: #FAFAFA; }"
            "QLineEdit:focus { border: 2px solid #2196F3; background-color: #FFFFFF; }"
        )

        # --- Ligne 1 : Email (toute la largeur) ---
        lbl_email = QLabel("Email :")
        lbl_email.setFont(font_label)
        lbl_email.setStyleSheet(style_label)
        grid.addWidget(lbl_email, 0, 0)

        self.input_email = QLineEdit()
        self.input_email.setFont(font_corps)
        self.input_email.setPlaceholderText("email@exemple.fr")
        self.input_email.setStyleSheet(si)
        self.input_email.setMinimumHeight(38)
        grid.addWidget(self.input_email, 0, 1, 1, 3)

        # --- Ligne 2 : Telephone (indicatif + numero) ---
        lbl_tel = QLabel("Telephone :")
        lbl_tel.setFont(font_label)
        lbl_tel.setStyleSheet(style_label)
        grid.addWidget(lbl_tel, 1, 0)

        layout_telephone = QHBoxLayout()
        layout_telephone.setSpacing(6)

        self.combo_indicatif = QComboBox()
        self.combo_indicatif.setFont(font_corps)
        self.combo_indicatif.setMinimumWidth(130)
        self.combo_indicatif.setMaximumWidth(160)
        self.combo_indicatif.setMinimumHeight(38)
        self.combo_indicatif.setStyleSheet(
            "QComboBox { border: 1px solid #E0E0E0; border-radius: 6px; "
            "padding: 6px 10px; background-color: #FAFAFA; }"
            "QComboBox:focus { border: 2px solid #2196F3; }"
        )
        indicatifs = [
            ("+33", "FR +33"),
            ("+32", "BE +32"),
            ("+41", "CH +41"),
            ("+352", "LU +352"),
            ("+44", "GB +44"),
            ("+49", "DE +49"),
            ("+39", "IT +39"),
            ("+34", "ES +34"),
            ("+351", "PT +351"),
            ("+1", "US/CA +1"),
        ]
        for code, label in indicatifs:
            self.combo_indicatif.addItem(label, code)
        layout_telephone.addWidget(self.combo_indicatif)

        self.input_telephone = QLineEdit()
        self.input_telephone.setFont(font_corps)
        self.input_telephone.setPlaceholderText("6 12 34 56 78")
        self.input_telephone.setStyleSheet(si)
        self.input_telephone.setMinimumHeight(38)
        layout_telephone.addWidget(self.input_telephone)

        grid.addLayout(layout_telephone, 1, 1, 1, 3)

        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        groupe.setLayout(grid)
        self.scroll_layout.addWidget(groupe)

    # ------------------------------------------------------------------
    # Section : Situation familiale
    # ------------------------------------------------------------------

    def _construire_section_situation_familiale(self):
        """Construit la section Situation familiale avec ses sous-sections."""
        groupe = QGroupBox("Situation familiale")
        font_section = QFont()
        font_section.setPointSize(14)
        font_section.setWeight(QFont.Weight.DemiBold)
        groupe.setFont(font_section)
        groupe.setStyleSheet(
            "QGroupBox {"
            "    font-size: 13pt; font-weight: 600; color: #1976D2;"
            "    border: 2px solid #2196F3; border-radius: 12px;"
            "    background-color: #FAFAFA; padding: 25px; margin-top: 20px;"
            "}"
            "QGroupBox::title {"
            "    subcontrol-origin: margin; left: 20px; padding: 0 10px;"
            "    background-color: white; border-radius: 4px;"
            "}"
        )

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        font_corps = QFont()
        font_corps.setPointSize(12)

        # Situation maritale
        layout_situation = QHBoxLayout()
        label_situation = QLabel("Situation maritale :")
        label_situation.setFont(font_corps)
        self.combo_situation = QComboBox()
        self.combo_situation.setFont(font_corps)
        self.combo_situation.addItems(
            [
                "",
                "Celibataire",
                "En couple",
                "Marie(e)",
                "Pacse(e)",
                "Divorce(e)",
                "Veuf/Veuve",
            ]
        )
        layout_situation.addWidget(label_situation)
        layout_situation.addWidget(self.combo_situation)
        layout_situation.addStretch()
        layout.addLayout(layout_situation)

        # --- Dates conditionnelles selon la situation maritale ---
        self._construire_dates_situation(layout, font_corps)

        # --- Sous-section Conjoint ---
        self._construire_sous_section_conjoint(layout, font_corps)

        # --- Sous-section Enfants ---
        self._construire_sous_section_enfants(layout, font_corps)

        # --- Sous-section Parents ---
        self._construire_sous_section_parents(layout, font_corps)

        groupe.setLayout(layout)
        self.scroll_layout.addWidget(groupe)

    def _construire_sous_section_conjoint(self, layout_parent, font_corps):
        """Construit la sous-section Conjoint (visible conditionnellement)."""
        self.groupe_conjoint = QGroupBox("Conjoint")
        self.groupe_conjoint.setFont(font_corps)
        self.groupe_conjoint.setStyleSheet(
            "QGroupBox { padding: 15px; border-radius: 8px; }"
        )
        self.groupe_conjoint.setVisible(False)

        layout_conjoint = QVBoxLayout()
        layout_conjoint.setSpacing(10)
        layout_conjoint.setContentsMargins(15, 15, 15, 15)

        # Checkbox "A un conjoint"
        self.checkbox_a_conjoint = QCheckBox("A un conjoint")
        self.checkbox_a_conjoint.setFont(font_corps)
        layout_conjoint.addWidget(self.checkbox_a_conjoint)

        # Sous-formulaire conjoint (visible si checkbox cochee)
        self.widget_form_conjoint = QWidget()
        form_conjoint = QFormLayout(self.widget_form_conjoint)
        form_conjoint.setSpacing(8)

        self.input_nom_conjoint = QLineEdit()
        self.input_nom_conjoint.setFont(font_corps)
        self.input_nom_conjoint.setPlaceholderText("NOM")
        form_conjoint.addRow("Nom conjoint :", self.input_nom_conjoint)

        self.input_prenom_conjoint = QLineEdit()
        self.input_prenom_conjoint.setFont(font_corps)
        self.input_prenom_conjoint.setPlaceholderText("Prenom")
        form_conjoint.addRow("Prenom conjoint :", self.input_prenom_conjoint)

        self.input_date_naissance_conjoint = QDateEdit()
        self.input_date_naissance_conjoint.setFont(font_corps)
        self.input_date_naissance_conjoint.setCalendarPopup(True)
        self.input_date_naissance_conjoint.setDisplayFormat("dd/MM/yyyy")
        self.input_date_naissance_conjoint.setDate(QDate.currentDate())
        form_conjoint.addRow("Date naissance :", self.input_date_naissance_conjoint)

        self.input_email_conjoint = QLineEdit()
        self.input_email_conjoint.setFont(font_corps)
        self.input_email_conjoint.setPlaceholderText("email@exemple.fr")
        form_conjoint.addRow("Email conjoint :", self.input_email_conjoint)

        self.input_telephone_conjoint = QLineEdit()
        self.input_telephone_conjoint.setFont(font_corps)
        self.input_telephone_conjoint.setPlaceholderText("06 12 34 56 78")
        form_conjoint.addRow("Telephone conjoint :", self.input_telephone_conjoint)

        self.checkbox_creer_compte_conjoint = QCheckBox(
            "Creer un compte client pour le conjoint"
        )
        self.checkbox_creer_compte_conjoint.setFont(font_corps)
        form_conjoint.addRow("", self.checkbox_creer_compte_conjoint)

        self.widget_form_conjoint.setVisible(False)
        layout_conjoint.addWidget(self.widget_form_conjoint)

        self.groupe_conjoint.setLayout(layout_conjoint)
        layout_parent.addWidget(self.groupe_conjoint)

    def _construire_sous_section_enfants(self, layout_parent, font_corps):
        """Construit la sous-section Enfants avec generation dynamique."""
        self.groupe_enfants = QGroupBox("Enfants")
        self.groupe_enfants.setFont(font_corps)
        self.groupe_enfants.setStyleSheet(
            "QGroupBox { padding: 15px; border-radius: 8px; }"
        )

        layout_enfants = QVBoxLayout()
        layout_enfants.setSpacing(10)
        layout_enfants.setContentsMargins(15, 15, 15, 15)

        # Checkbox "A des enfants"
        self.checkbox_a_enfants = QCheckBox("A des enfants")
        self.checkbox_a_enfants.setFont(font_corps)
        layout_enfants.addWidget(self.checkbox_a_enfants)

        # Widget contenant le spinbox et les formulaires dynamiques
        self.widget_enfants_detail = QWidget()
        layout_enfants_detail = QVBoxLayout(self.widget_enfants_detail)
        layout_enfants_detail.setContentsMargins(0, 0, 0, 0)
        layout_enfants_detail.setSpacing(8)

        # Nombre d'enfants
        layout_nombre = QHBoxLayout()
        label_nombre = QLabel("Nombre d'enfants :")
        label_nombre.setFont(font_corps)
        self.spin_nombre_enfants = QSpinBox()
        self.spin_nombre_enfants.setFont(font_corps)
        self.spin_nombre_enfants.setMinimum(1)
        self.spin_nombre_enfants.setMaximum(20)
        self.spin_nombre_enfants.setValue(1)
        self.spin_nombre_enfants.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.spin_nombre_enfants.setAccelerated(True)
        layout_nombre.addWidget(label_nombre)
        layout_nombre.addWidget(self.spin_nombre_enfants)
        layout_nombre.addStretch()
        layout_enfants_detail.addLayout(layout_nombre)

        # Conteneur pour les formulaires enfants dynamiques
        self.conteneur_enfants = QWidget()
        self.layout_conteneur_enfants = QVBoxLayout(self.conteneur_enfants)
        self.layout_conteneur_enfants.setContentsMargins(0, 0, 0, 0)
        self.layout_conteneur_enfants.setSpacing(8)
        layout_enfants_detail.addWidget(self.conteneur_enfants)

        self.widget_enfants_detail.setVisible(False)
        layout_enfants.addWidget(self.widget_enfants_detail)

        self.groupe_enfants.setLayout(layout_enfants)
        layout_parent.addWidget(self.groupe_enfants)

        # Generer le premier formulaire enfant
        self._on_nombre_enfants_change(1)

    def _construire_sous_section_parents(self, layout_parent, font_corps):
        """Construit la sous-section Parents."""
        self.groupe_parents = QGroupBox("Parents")
        self.groupe_parents.setFont(font_corps)
        self.groupe_parents.setStyleSheet(
            "QGroupBox { padding: 15px; border-radius: 8px; }"
        )

        layout_parents = QVBoxLayout()
        layout_parents.setSpacing(10)
        layout_parents.setContentsMargins(15, 15, 15, 15)

        # Checkbox "A des parents"
        self.checkbox_a_parents = QCheckBox("A des parents")
        self.checkbox_a_parents.setFont(font_corps)
        layout_parents.addWidget(self.checkbox_a_parents)

        # Widget detail parents
        self.widget_parents_detail = QWidget()
        layout_parents_detail = QVBoxLayout(self.widget_parents_detail)
        layout_parents_detail.setContentsMargins(0, 0, 0, 0)
        layout_parents_detail.setSpacing(8)

        # Checkbox "Parents en vie"
        self.checkbox_parents_en_vie = QCheckBox("Parents en vie")
        self.checkbox_parents_en_vie.setFont(font_corps)
        self.checkbox_parents_en_vie.setChecked(True)
        layout_parents_detail.addWidget(self.checkbox_parents_en_vie)

        # Widget formulaires parents (visible si parents en vie)
        self.widget_formulaires_parents = QWidget()
        layout_formulaires_parents = QVBoxLayout(self.widget_formulaires_parents)
        layout_formulaires_parents.setContentsMargins(0, 0, 0, 0)
        layout_formulaires_parents.setSpacing(8)

        # --- Formulaire Pere ---
        self.groupe_pere = QGroupBox("Pere")
        self.groupe_pere.setFont(font_corps)
        self.groupe_pere.setStyleSheet(
            "QGroupBox { padding: 15px; border-radius: 8px; }"
        )
        form_pere = QFormLayout()
        form_pere.setSpacing(8)

        self.input_nom_pere = QLineEdit()
        self.input_nom_pere.setFont(font_corps)
        self.input_nom_pere.setPlaceholderText("NOM")
        form_pere.addRow("Nom :", self.input_nom_pere)

        self.input_prenom_pere = QLineEdit()
        self.input_prenom_pere.setFont(font_corps)
        self.input_prenom_pere.setPlaceholderText("Prenom")
        form_pere.addRow("Prenom :", self.input_prenom_pere)

        self.input_email_pere = QLineEdit()
        self.input_email_pere.setFont(font_corps)
        self.input_email_pere.setPlaceholderText("email@exemple.fr")
        form_pere.addRow("Email :", self.input_email_pere)

        self.input_telephone_pere = QLineEdit()
        self.input_telephone_pere.setFont(font_corps)
        self.input_telephone_pere.setPlaceholderText("06 12 34 56 78")
        form_pere.addRow("Telephone :", self.input_telephone_pere)

        self.checkbox_creer_compte_pere = QCheckBox("Creer un compte client")
        self.checkbox_creer_compte_pere.setFont(font_corps)
        form_pere.addRow("", self.checkbox_creer_compte_pere)

        self.groupe_pere.setLayout(form_pere)
        layout_formulaires_parents.addWidget(self.groupe_pere)

        # --- Formulaire Mere ---
        self.groupe_mere = QGroupBox("Mere")
        self.groupe_mere.setFont(font_corps)
        self.groupe_mere.setStyleSheet(
            "QGroupBox { padding: 15px; border-radius: 8px; }"
        )
        form_mere = QFormLayout()
        form_mere.setSpacing(8)

        self.input_nom_mere = QLineEdit()
        self.input_nom_mere.setFont(font_corps)
        self.input_nom_mere.setPlaceholderText("NOM")
        form_mere.addRow("Nom :", self.input_nom_mere)

        self.input_prenom_mere = QLineEdit()
        self.input_prenom_mere.setFont(font_corps)
        self.input_prenom_mere.setPlaceholderText("Prenom")
        form_mere.addRow("Prenom :", self.input_prenom_mere)

        self.input_email_mere = QLineEdit()
        self.input_email_mere.setFont(font_corps)
        self.input_email_mere.setPlaceholderText("email@exemple.fr")
        form_mere.addRow("Email :", self.input_email_mere)

        self.input_telephone_mere = QLineEdit()
        self.input_telephone_mere.setFont(font_corps)
        self.input_telephone_mere.setPlaceholderText("06 12 34 56 78")
        form_mere.addRow("Telephone :", self.input_telephone_mere)

        self.checkbox_creer_compte_mere = QCheckBox("Creer un compte client")
        self.checkbox_creer_compte_mere.setFont(font_corps)
        form_mere.addRow("", self.checkbox_creer_compte_mere)

        self.groupe_mere.setLayout(form_mere)
        layout_formulaires_parents.addWidget(self.groupe_mere)

        layout_parents_detail.addWidget(self.widget_formulaires_parents)

        self.widget_parents_detail.setVisible(False)
        layout_parents.addWidget(self.widget_parents_detail)

        self.groupe_parents.setLayout(layout_parents)
        layout_parent.addWidget(self.groupe_parents)

    def _construire_dates_situation(self, layout_parent, font_corps):
        """Construit les champs de dates conditionnels selon la situation maritale."""
        # Container pour les dates conditionnelles
        self.widget_dates_situation = QWidget()
        layout_dates = QFormLayout(self.widget_dates_situation)
        layout_dates.setSpacing(8)
        layout_dates.setContentsMargins(0, 5, 0, 5)

        # Date de mariage (visible si Marie(e))
        self.input_date_mariage = QDateEdit()
        self.input_date_mariage.setFont(font_corps)
        self.input_date_mariage.setCalendarPopup(True)
        self.input_date_mariage.setDisplayFormat("dd/MM/yyyy")
        self.input_date_mariage.setDate(QDate.currentDate())
        self.label_date_mariage = QLabel("Date de mariage :")
        self.label_date_mariage.setFont(font_corps)
        layout_dates.addRow(self.label_date_mariage, self.input_date_mariage)

        # Date de PACS (visible si Pacse(e))
        self.input_date_pacs = QDateEdit()
        self.input_date_pacs.setFont(font_corps)
        self.input_date_pacs.setCalendarPopup(True)
        self.input_date_pacs.setDisplayFormat("dd/MM/yyyy")
        self.input_date_pacs.setDate(QDate.currentDate())
        self.label_date_pacs = QLabel("Date de PACS :")
        self.label_date_pacs.setFont(font_corps)
        layout_dates.addRow(self.label_date_pacs, self.input_date_pacs)

        # Date de deces du conjoint (visible si Veuf/Veuve)
        self.input_date_deces_conjoint = QDateEdit()
        self.input_date_deces_conjoint.setFont(font_corps)
        self.input_date_deces_conjoint.setCalendarPopup(True)
        self.input_date_deces_conjoint.setDisplayFormat("dd/MM/yyyy")
        self.input_date_deces_conjoint.setDate(QDate.currentDate())
        self.label_date_deces = QLabel("Date de deces du conjoint :")
        self.label_date_deces.setFont(font_corps)
        layout_dates.addRow(self.label_date_deces, self.input_date_deces_conjoint)

        # Tout masquer par defaut
        self.widget_dates_situation.setVisible(False)
        self.label_date_mariage.setVisible(False)
        self.input_date_mariage.setVisible(False)
        self.label_date_pacs.setVisible(False)
        self.input_date_pacs.setVisible(False)
        self.label_date_deces.setVisible(False)
        self.input_date_deces_conjoint.setVisible(False)

        layout_parent.addWidget(self.widget_dates_situation)

    # ------------------------------------------------------------------
    # Section : Informations supplementaires
    # ------------------------------------------------------------------

    def _construire_section_infos_supplementaires(self):
        """Construit la section Informations supplementaires."""
        groupe = QGroupBox("Informations supplementaires")
        font_section = QFont()
        font_section.setPointSize(14)
        font_section.setWeight(QFont.Weight.DemiBold)
        groupe.setFont(font_section)
        groupe.setStyleSheet(
            "QGroupBox {"
            "    font-size: 13pt; font-weight: 600; color: #1976D2;"
            "    border: 2px solid #2196F3; border-radius: 12px;"
            "    background-color: #FAFAFA; padding: 25px; margin-top: 20px;"
            "}"
            "QGroupBox::title {"
            "    subcontrol-origin: margin; left: 20px; padding: 0 10px;"
            "    background-color: white; border-radius: 4px;"
            "}"
        )

        form = QFormLayout()
        form.setSpacing(10)
        form.setContentsMargins(15, 15, 15, 15)

        font_corps = QFont()
        font_corps.setPointSize(12)

        # Profession
        self.input_profession = QLineEdit()
        self.input_profession.setFont(font_corps)
        self.input_profession.setPlaceholderText("Profession")
        form.addRow("Profession :", self.input_profession)

        # Centres d'interet (systeme de tags)
        self.widget_centres_interet = CentresInteretWidget()
        form.addRow("Centres d'interet :", self.widget_centres_interet)

        # Notes personnalisees
        self.input_notes = QTextEdit()
        self.input_notes.setFont(font_corps)
        self.input_notes.setPlaceholderText("Notes personnalisees...")
        self.input_notes.setFixedHeight(80)  # Environ 3 lignes
        form.addRow("Notes :", self.input_notes)

        groupe.setLayout(form)
        self.scroll_layout.addWidget(groupe)

    # ------------------------------------------------------------------
    # Indicateur de completude du profil
    # ------------------------------------------------------------------

    def _construire_indicateur_completude(self):
        """Construit l'indicateur de completude du profil."""
        layout_completude = QVBoxLayout()
        layout_completude.setSpacing(5)

        font_corps = QFont()
        font_corps.setPointSize(12)

        self.barre_completude = QProgressBar()
        self.barre_completude.setMinimum(0)
        self.barre_completude.setMaximum(100)
        self.barre_completude.setValue(0)
        self.barre_completude.setTextVisible(True)
        self.barre_completude.setFormat("%p%")
        layout_completude.addWidget(self.barre_completude)

        self.label_completude = QLabel("Profil incomplet (0%)")
        self.label_completude.setFont(font_corps)
        self.label_completude.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_completude.addWidget(self.label_completude)

        self.scroll_layout.addLayout(layout_completude)

    # ==================================================================
    # Connexion des signaux
    # ==================================================================

    def _connecter_signaux(self):
        """Connecte les signaux internes et ceux du ViewModel."""

        # --- Signaux du formulaire principal ---
        self.input_nom.textChanged.connect(self._on_nom_change)
        self.input_prenom.textChanged.connect(self._on_prenom_change)
        self.input_email.textChanged.connect(self._valider_email_temps_reel)

        # Date de naissance
        self.input_date_naissance.dateChanged.connect(self._on_date_naissance_change)

        # Situation familiale
        self.combo_situation.currentIndexChanged.connect(self._on_situation_change)

        # Conjoint
        self.checkbox_a_conjoint.stateChanged.connect(self._on_a_conjoint_change)

        # Enfants
        self.checkbox_a_enfants.stateChanged.connect(self._on_a_enfants_change)
        self.spin_nombre_enfants.valueChanged.connect(self._on_nombre_enfants_change)

        # Parents
        self.checkbox_a_parents.stateChanged.connect(self._on_a_parents_change)
        self.checkbox_parents_en_vie.stateChanged.connect(
            self._on_parents_en_vie_change
        )

        # --- Signaux du ViewModel ---
        self.viewmodel.client_sauvegarde.connect(self._on_succes)
        self.viewmodel.erreur.connect(self._on_erreur)

        # --- Mise a jour de la completude a chaque modification ---
        self.input_nom.textChanged.connect(lambda: self._calculer_completude())
        self.input_prenom.textChanged.connect(lambda: self._calculer_completude())
        self.input_email.textChanged.connect(lambda: self._calculer_completude())
        self.input_telephone.textChanged.connect(lambda: self._calculer_completude())
        self.input_adresse.textChanged.connect(lambda: self._calculer_completude())
        self.input_ville.textChanged.connect(lambda: self._calculer_completude())
        self.input_code_postal.textChanged.connect(lambda: self._calculer_completude())
        self.input_profession.textChanged.connect(lambda: self._calculer_completude())
        self.input_notes.textChanged.connect(lambda: self._calculer_completude())
        self.input_date_naissance.dateChanged.connect(
            lambda: self._calculer_completude()
        )

    # ==================================================================
    # Callbacks et logique de la vue
    # ==================================================================

    def _on_nom_change(self, texte: str):
        """Formate le nom en MAJUSCULES pendant la saisie."""
        self.input_nom.blockSignals(True)
        pos = self.input_nom.cursorPosition()
        self.input_nom.setText(texte.upper())
        self.input_nom.setCursorPosition(pos)
        self.input_nom.blockSignals(False)

    def _on_prenom_change(self, texte: str):
        """Formate le prenom avec majuscule initiale pendant la saisie."""
        self.input_prenom.blockSignals(True)
        pos = self.input_prenom.cursorPosition()
        self.input_prenom.setText(self._capitaliser_prenom(texte))
        self.input_prenom.setCursorPosition(pos)
        self.input_prenom.blockSignals(False)

    def _valider_email_temps_reel(self):
        """Valide l'email en temps réel et affiche un indicateur visuel."""
        email = self.input_email.text().strip()

        if not email:
            # Pas d'email = style neutre
            self.input_email.setStyleSheet(style_input())
            return

    def _on_succes(self, message: str):
        """Callback de succès depuis le ViewModel."""
        QMessageBox.information(self, "Succès", message)

    def _on_erreur(self, message: str):
        """Callback d'erreur depuis le ViewModel."""
        QMessageBox.critical(self, "Erreur", message)

    def _calculer_completude(self):
        """Calcule le taux de complétion du profil."""
        total_champs = 0
        champs_remplis = 0

        # Champs obligatoires/importants
        champs = [
            ("nom", self.input_nom.text().strip()),
            ("prenom", self.input_prenom.text().strip()),
            ("email", self.input_email.text().strip()),
            ("telephone", self.input_telephone.text().strip()),
            ("adresse", self.input_adresse.text().strip()),
            ("ville", self.input_ville.text().strip()),
            ("code_postal", self.input_code_postal.text().strip()),
        ]

        # Ajouter profession si existe
        if hasattr(self, "input_profession"):
            champs.append(("profession", self.input_profession.text().strip()))

        for nom, valeur in champs:
            total_champs += 1
            if valeur:
                champs_remplis += 1

        # Date de naissance
        total_champs += 1
        if self.input_date_naissance.date() != QDate(1900, 1, 1):
            champs_remplis += 1

        # Photo
        total_champs += 1
        if self._photo_path:
            champs_remplis += 1

        # Calculer le pourcentage
        if total_champs > 0:
            pourcentage = int((champs_remplis / total_champs) * 100)
        else:
            pourcentage = 0

        # Mettre à jour la barre de progression
        self.barre_completude.setValue(pourcentage)

        # Mettre à jour le label avec couleur
        if pourcentage < 30:
            couleur = "#E74C3C"
            texte = "Profil incomplet"
        elif pourcentage < 70:
            couleur = "#F39C12"
            texte = "Profil en cours"
        else:
            couleur = "#27AE60"
            texte = "Profil complet"

        self.label_completude.setText(f"{texte} ({pourcentage}%)")
        self.label_completude.setStyleSheet(f"color: {couleur}; font-weight: bold;")

        # Mettre à jour le style de la barre
        self.barre_completude.setStyleSheet(
            f"""
            QProgressBar {{
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                text-align: center;
                background-color: #ECF0F1;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {couleur};
                border-radius: 6px;
            }}
        """
        )

    def _capitaliser_prenom(self, texte: str) -> str:
        """Capitalise correctement un prenom (gere les tirets et espaces).

        Exemples:
            "jean-pierre" -> "Jean-Pierre"
            "marie anne"  -> "Marie Anne"
        """
        if not texte:
            return texte
        # Traiter les parties separees par des espaces
        parties_espace = texte.split(" ")
        resultats = []
        for partie in parties_espace:
            # Traiter les parties separees par des tirets
            sous_parties = partie.split("-")
            partie_formatee = "-".join(sp.capitalize() for sp in sous_parties)
            resultats.append(partie_formatee)
        return " ".join(resultats)

    def _on_date_naissance_change(self):
        """Calcule et affiche l'age automatiquement a partir de la date."""
        date_qt = self.input_date_naissance.date()
        # Si la date est au minimum (1900-01-01), pas de date selectionnee
        if date_qt == QDate(1900, 1, 1):
            self.label_age.setText("\u2014 ans")
            return
        try:
            age = calculer_age(date_qt)
            self.label_age.setText(f"{age} ans")
        except Exception:
            self.label_age.setText("\u2014 ans")

    def _on_situation_change(self, index: int):
        """Affiche/masque la section conjoint et les dates selon la situation maritale."""
        situation = self.combo_situation.currentText()
        situations_avec_conjoint = ["En couple", "Marie(e)", "Pacse(e)"]
        self.groupe_conjoint.setVisible(situation in situations_avec_conjoint)

        # Si on masque la section conjoint, reinitialiser
        if situation not in situations_avec_conjoint:
            self.checkbox_a_conjoint.setChecked(False)

        # --- Dates conditionnelles ---
        show_dates = situation in ["Marie(e)", "Pacse(e)", "Veuf/Veuve"]
        self.widget_dates_situation.setVisible(show_dates)

        self.label_date_mariage.setVisible(situation == "Marie(e)")
        self.input_date_mariage.setVisible(situation == "Marie(e)")
        self.label_date_pacs.setVisible(situation == "Pacse(e)")
        self.input_date_pacs.setVisible(situation == "Pacse(e)")
        self.label_date_deces.setVisible(situation == "Veuf/Veuve")
        self.input_date_deces_conjoint.setVisible(situation == "Veuf/Veuve")

    def _on_a_conjoint_change(self, etat: int):
        """Affiche/masque le formulaire conjoint selon la checkbox."""
        a_conjoint = etat == Qt.CheckState.Checked.value
        self.widget_form_conjoint.setVisible(a_conjoint)

    def _on_a_enfants_change(self, etat: int):
        """Affiche/masque la section enfants selon la checkbox."""
        a_enfants = etat == Qt.CheckState.Checked.value
        self.widget_enfants_detail.setVisible(a_enfants)

    def _on_nombre_enfants_change(self, nombre: int):
        """Genere dynamiquement les formulaires enfants.

        Supprime les formulaires existants et en cree de nouveaux
        en fonction de la valeur du spinbox.
        """
        # Supprimer les formulaires existants
        self._formulaires_enfants.clear()
        while self.layout_conteneur_enfants.count():
            item = self.layout_conteneur_enfants.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        font_corps = QFont()
        font_corps.setPointSize(12)

        # Creer les nouveaux formulaires
        for i in range(nombre):
            groupe_enfant = QGroupBox(f"Enfant {i + 1}")
            groupe_enfant.setFont(font_corps)
            groupe_enfant.setStyleSheet(
                "QGroupBox { padding: 15px; border-radius: 8px; }"
            )

            form = QFormLayout()
            form.setSpacing(8)

            input_nom = QLineEdit()
            input_nom.setFont(font_corps)
            input_nom.setPlaceholderText("NOM")
            form.addRow("Nom :", input_nom)

            input_prenom = QLineEdit()
            input_prenom.setFont(font_corps)
            input_prenom.setPlaceholderText("Prenom")
            form.addRow("Prenom :", input_prenom)

            input_date = QDateEdit()
            input_date.setFont(font_corps)
            input_date.setCalendarPopup(True)
            input_date.setDisplayFormat("dd/MM/yyyy")
            input_date.setDate(QDate.currentDate())
            form.addRow("Date naissance :", input_date)

            checkbox_creer = QCheckBox("Creer un compte client")
            checkbox_creer.setFont(font_corps)
            form.addRow("", checkbox_creer)

            groupe_enfant.setLayout(form)
            self.layout_conteneur_enfants.addWidget(groupe_enfant)

            # Stocker les references aux champs
            self._formulaires_enfants.append(
                {
                    "groupe": groupe_enfant,
                    "nom": input_nom,
                    "prenom": input_prenom,
                    "date_naissance": input_date,
                    "creer_compte": checkbox_creer,
                }
            )

    def _on_a_parents_change(self, etat: int):
        """Affiche/masque la section parents selon la checkbox."""
        a_parents = etat == Qt.CheckState.Checked.value
        self.widget_parents_detail.setVisible(a_parents)

    def _on_parents_en_vie_change(self, etat: int):
        """Affiche/masque les formulaires pere/mere selon 'Parents en vie'."""
        en_vie = etat == Qt.CheckState.Checked.value
        self.widget_formulaires_parents.setVisible(en_vie)

    # ------------------------------------------------------------------
    # Photo de profil
    # ------------------------------------------------------------------

    def _photo_hover_enter(self):
        """Applique un effet au survol de la photo."""
        if hasattr(self, "_photo_pixmap_original") and self._photo_pixmap_original:
            # Photo chargee : appliquer un filtre sombre + icone crayon
            taille = 180
            overlay = QPixmap(taille, taille)
            overlay.fill(Qt.GlobalColor.transparent)
            painter = QPainter(overlay)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Masque circulaire
            path = QPainterPath()
            path.addEllipse(0, 0, taille, taille)
            painter.setClipPath(path)

            # Dessiner la photo originale
            scaled = self._photo_pixmap_original.scaled(
                taille,
                taille,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            if scaled.width() != taille or scaled.height() != taille:
                x = (scaled.width() - taille) // 2
                y = (scaled.height() - taille) // 2
                scaled = scaled.copy(x, y, taille, taille)
            painter.drawPixmap(0, 0, scaled)

            # Gradient sombre
            gradient = QLinearGradient(0, 0, 0, taille)
            gradient.setColorAt(0, QColor(0, 0, 0, 50))
            gradient.setColorAt(1, QColor(0, 0, 0, 120))
            painter.fillRect(0, 0, taille, taille, gradient)

            # Icone crayon au centre
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.setFont(QFont("Arial", 30))
            painter.drawText(
                QRect(0, 0, taille, taille), Qt.AlignmentFlag.AlignCenter, "Modifier"
            )

            painter.end()
            self.label_photo.setPixmap(overlay)
        else:
            # Pas de photo : afficher un texte d'invitation
            self.label_photo.setText("Ajouter\nune photo")
            self.label_photo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            self.label_photo.setStyleSheet(
                "QLabel { border: 3px dashed #2196F3; border-radius: 90px; "
                "background-color: #E3F2FD; color: #1976D2; }"
            )

    def _photo_hover_leave(self):
        """Retire l'effet au depart de la souris."""
        if hasattr(self, "_photo_pixmap_original") and self._photo_pixmap_original:
            # Restaurer la photo originale
            self._afficher_photo_pixmap(self._photo_pixmap_original)
        else:
            # Restaurer le style et texte par defaut
            self.label_photo.setText("\U0001f464")
            self.label_photo.setFont(QFont("Arial", 80))
            self.label_photo.setStyleSheet(
                "QLabel { border: 3px solid #2196F3; border-radius: 90px; "
                "background-color: white; color: #BDBDBD; }"
            )

    def _choisir_photo(self):
        """Ouvre un dialogue pour choisir une photo de profil."""
        fichier, _ = QFileDialog.getOpenFileName(
            self, "Choisir une photo", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not fichier:
            return

        # Copier la photo dans le dossier photos de l'app
        dossier_photos = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "photos_clients",
        )
        os.makedirs(dossier_photos, exist_ok=True)

        # Generer un nom unique
        ext = os.path.splitext(fichier)[1]
        nom_fichier = f"client_{int(time.time())}{ext}"
        destination = os.path.join(dossier_photos, nom_fichier)
        shutil.copy2(fichier, destination)

        self._photo_path = destination
        pixmap = QPixmap(destination)
        self._photo_pixmap_original = pixmap
        self._afficher_photo_pixmap(pixmap)

    def _supprimer_photo(self):
        """Supprime la photo de profil."""
        self._photo_path = ""
        self._photo_pixmap_original = None
        self.label_photo.setPixmap(QPixmap())
        self.label_photo.setText("\U0001f464")
        self.label_photo.setFont(QFont("Arial", 80))
        self.label_photo.setStyleSheet(
            "QLabel { border: 3px solid #2196F3; border-radius: 90px; "
            "background-color: white; color: #BDBDBD; }"
        )

    def afficher_photo_pixmap(self, pixmap: QPixmap):
        """Affiche un QPixmap en format circulaire dans le label."""
        if pixmap.isNull():
            return

        taille = 180
        scaled = pixmap.scaled(
            taille,
            taille,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )

        # Centrer et recadrer si nécessaire
        if scaled.width() != taille or scaled.height() != taille:
            x = (scaled.width() - taille) // 2
            y = (scaled.height() - taille) // 2
            scaled = scaled.copy(x, y, taille, taille)

        # Créer un masque circulaire
        masque = QPixmap(taille, taille)
        masque.fill(Qt.GlobalColor.transparent)

        painter = QPainter(masque)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addEllipse(0, 0, taille, taille)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, scaled)
        painter.end()

        self.label_photo.setPixmap(masque)
        self.label_photo.setStyleSheet(
            "border: 3px solid #2196F3; border-radius: 90px;"
        )
