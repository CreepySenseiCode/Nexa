"""Vue pour l'onglet Client - Formulaire de creation/edition d'un client.

Ce module fournit la classe ClientView qui constitue l'interface graphique
pour la saisie et la modification des informations d'un client. La vue
communique avec le ClientViewModel selon le pattern MVVM.
"""

import os
import shutil

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGridLayout, QLabel, QLineEdit, QDateEdit, QComboBox, QCheckBox, QSpinBox,
    QGroupBox, QPushButton, QTextEdit, QScrollArea, QProgressBar,
    QMessageBox, QFrame, QDialog, QDialogButtonBox, QSizePolicy,
    QFileDialog, QAbstractSpinBox)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont, QPixmap, QPainter, QPainterPath, QPen, QLinearGradient, QColor

from models.centre_interet import CentreInteretModel

from viewmodels.client_vm import ClientViewModel
from utils.formatters import calculer_age
from utils.validators import valider_email


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


class ClientView(QWidget):
    """Vue principale pour la gestion d'un client (creation/edition).

    L'ensemble du formulaire est contenu dans un QScrollArea pour gerer
    les contenus longs. Les sections dynamiques (conjoint, enfants, parents)
    s'affichent ou se masquent selon les choix de l'utilisateur.
    """

    # --- Signaux ---
    client_sauvegarde = Signal(int)       # Re-emet l'id du client sauvegarde
    demande_edition_client = Signal(int)  # Demande d'edition d'un client (depuis Recherche)

    def __init__(self, viewmodel=None):
        super().__init__()
        # Si le viewmodel n'est pas fourni, on en cree un
        self.viewmodel = viewmodel if viewmodel is not None else ClientViewModel()

        # Listes pour stocker les formulaires enfants dynamiques
        self._formulaires_enfants: list[dict] = []

        # Construire l'interface
        self._construire_ui()

        # Connecter les signaux
        self._connecter_signaux()

    # ==================================================================
    # Construction de l'interface
    # ==================================================================

    def _construire_ui(self):
        """Construit l'interface complete du formulaire client."""

        # --- Layout principal ---
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

        # --- Titre ---
        self.label_titre = QLabel("Nouveau Client")
        font_titre = QFont()
        font_titre.setPointSize(16)
        font_titre.setBold(True)
        self.label_titre.setFont(font_titre)
        self.scroll_layout.addWidget(self.label_titre)

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

        # --- Barre de boutons (en dehors du scroll) ---
        self._construire_barre_boutons(layout_principal)

    # ------------------------------------------------------------------
    # Section : Photo de profil (centree)
    # ------------------------------------------------------------------

    def _construire_section_photo(self):
        """Construit la section photo de profil avec photo cliquable et hover effect."""
        container = QWidget()
        container.setFixedSize(200, 200)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self._photo_path = ''

        # Label photo (cliquable)
        self.label_photo = QLabel()
        self.label_photo.setFixedSize(180, 180)
        self.label_photo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Photo par defaut (silhouette)
        self.label_photo.setText("\U0001F464")
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
        style_input = (
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
        self.input_nom.setStyleSheet(style_input)
        self.input_nom.setMinimumHeight(38)
        grid.addWidget(self.input_nom, row, 1)

        lbl_prenom = QLabel("Prenom :")
        lbl_prenom.setFont(font_label)
        lbl_prenom.setStyleSheet(style_label)
        grid.addWidget(lbl_prenom, row, 2)

        self.input_prenom = QLineEdit()
        self.input_prenom.setFont(font_corps)
        self.input_prenom.setPlaceholderText("Prenom")
        self.input_prenom.setStyleSheet(style_input)
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
        self.input_adresse.setStyleSheet(style_input)
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
        self.input_ville.setStyleSheet(style_input)
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
        self.input_code_postal.setStyleSheet(style_input)
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
        style_input = (
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
        self.input_email.setStyleSheet(style_input)
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
        self.input_telephone.setStyleSheet(style_input)
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
        self.combo_situation.addItems([
            "", "Celibataire", "En couple", "Marie(e)",
            "Pacse(e)", "Divorce(e)", "Veuf/Veuve"
        ])
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

    # ------------------------------------------------------------------
    # Barre de boutons
    # ------------------------------------------------------------------

    def _construire_barre_boutons(self, layout_parent):
        """Construit la barre de boutons en bas de la vue."""
        # Separateur visuel
        separateur = QFrame()
        separateur.setFrameShape(QFrame.Shape.HLine)
        separateur.setFrameShadow(QFrame.Shadow.Sunken)
        layout_parent.addWidget(separateur)

        layout_boutons = QHBoxLayout()
        layout_boutons.setContentsMargins(20, 10, 20, 10)
        layout_boutons.setSpacing(10)

        font_boutons = QFont()
        font_boutons.setPointSize(12)

        # Bouton Nouveau (bleu)
        self.btn_nouveau = QPushButton("  Nouveau")
        self.btn_nouveau.setFont(font_boutons)
        self.btn_nouveau.setProperty("class", "btn-primary")
        self.btn_nouveau.setObjectName("btnNouveau")
        self.btn_nouveau.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nouveau.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "padding: 10px 24px; border-radius: 8px; border: none; "
            "font-weight: bold; }"
            "QPushButton:hover { background-color: #1976D2; }"
            "QPushButton:pressed { background-color: #0D47A1; }"
        )
        layout_boutons.addWidget(self.btn_nouveau)

        # Espacement flexible
        layout_boutons.addStretch()

        # Bouton Annuler (gris)
        self.btn_annuler = QPushButton("  Annuler")
        self.btn_annuler.setFont(font_boutons)
        self.btn_annuler.setProperty("class", "btn-secondary")
        self.btn_annuler.setObjectName("btnAnnuler")
        self.btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_annuler.setStyleSheet(
            "QPushButton { background-color: #9E9E9E; color: white; "
            "padding: 10px 24px; border-radius: 8px; border: none; "
            "font-weight: bold; }"
            "QPushButton:hover { background-color: #757575; }"
            "QPushButton:pressed { background-color: #616161; }"
        )
        layout_boutons.addWidget(self.btn_annuler)

        # Bouton Enregistrer (vert)
        self.btn_enregistrer = QPushButton("  Enregistrer")
        self.btn_enregistrer.setFont(font_boutons)
        self.btn_enregistrer.setProperty("class", "btn-success")
        self.btn_enregistrer.setObjectName("btnEnregistrer")
        self.btn_enregistrer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_enregistrer.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "padding: 10px 24px; border-radius: 8px; border: none; "
            "font-weight: bold; }"
            "QPushButton:hover { background-color: #388E3C; }"
            "QPushButton:pressed { background-color: #1B5E20; }"
        )
        layout_boutons.addWidget(self.btn_enregistrer)

        layout_parent.addLayout(layout_boutons)

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

        # --- Boutons ---
        self.btn_nouveau.clicked.connect(self.nouveau_client)
        self.btn_annuler.clicked.connect(self._annuler)
        self.btn_enregistrer.clicked.connect(self._sauvegarder)

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

    def _capitaliser_prenom(self, texte: str) -> str:
        """Capitalise correctement un prenom (gere les tirets et espaces).

        Exemples:
            "jean-pierre" -> "Jean-Pierre"
            "marie anne"  -> "Marie Anne"
        """
        if not texte:
            return texte
        # Traiter les parties separees par des espaces
        parties_espace = texte.split(' ')
        resultats = []
        for partie in parties_espace:
            # Traiter les parties separees par des tirets
            sous_parties = partie.split('-')
            partie_formatee = '-'.join(
                sp.capitalize() for sp in sous_parties
            )
            resultats.append(partie_formatee)
        return ' '.join(resultats)

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
            self._formulaires_enfants.append({
                'groupe': groupe_enfant,
                'nom': input_nom,
                'prenom': input_prenom,
                'date_naissance': input_date,
                'creer_compte': checkbox_creer,
            })

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
        if hasattr(self, '_photo_pixmap_original') and self._photo_pixmap_original:
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
                taille, taille,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
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
            from PySide6.QtCore import QRect
            painter.drawText(QRect(0, 0, taille, taille), Qt.AlignmentFlag.AlignCenter, "Modifier")

            painter.end()
            self.label_photo.setPixmap(overlay)
        else:
            # Pas de photo : changer le style
            self.label_photo.setStyleSheet(
                "QLabel { border: 3px solid #2196F3; border-radius: 90px; "
                "background-color: #E3F2FD; color: #1976D2; }"
            )

    def _photo_hover_leave(self):
        """Retire l'effet au depart de la souris."""
        if hasattr(self, '_photo_pixmap_original') and self._photo_pixmap_original:
            # Restaurer la photo originale
            self._afficher_photo_pixmap(self._photo_pixmap_original)
        else:
            # Restaurer le style par defaut
            self.label_photo.setStyleSheet(
                "QLabel { border: 3px solid #2196F3; border-radius: 90px; "
                "background-color: white; color: #BDBDBD; }"
            )

    def _choisir_photo(self):
        """Ouvre un dialogue pour choisir une photo de profil."""
        fichier, _ = QFileDialog.getOpenFileName(
            self, "Choisir une photo",
            "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not fichier:
            return

        # Copier la photo dans le dossier photos de l'app
        dossier_photos = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'photos_clients'
        )
        os.makedirs(dossier_photos, exist_ok=True)

        # Generer un nom unique
        import time
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
        self._photo_path = ''
        self._photo_pixmap_original = None
        self.label_photo.setPixmap(QPixmap())
        self.label_photo.setText("\U0001F464")
        self.label_photo.setFont(QFont("Arial", 80))
        self.label_photo.setStyleSheet(
            "QLabel { border: 3px solid #2196F3; border-radius: 90px; "
            "background-color: white; color: #BDBDBD; }"
        )

    def _afficher_photo_pixmap(self, pixmap: QPixmap):
        """Affiche un QPixmap en format circulaire dans le label."""
        if pixmap.isNull():
            return

        taille = 180
        scaled = pixmap.scaled(
            taille, taille,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        # Rogner au centre si non carre
        if scaled.width() != taille or scaled.height() != taille:
            x = (scaled.width() - taille) // 2
            y = (scaled.height() - taille) // 2
            scaled = scaled.copy(x, y, taille, taille)

        # Creer un masque circulaire
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
        self.label_photo.setText("")
        self.label_photo.setStyleSheet(
            "QLabel { border-radius: 90px; border: 3px solid #2196F3; }"
        )

    def _afficher_photo(self, chemin: str):
        """Affiche une photo depuis un chemin de fichier."""
        if not chemin or not os.path.exists(chemin):
            return
        pixmap = QPixmap(chemin)
        if pixmap.isNull():
            return
        self._photo_pixmap_original = pixmap
        self._afficher_photo_pixmap(pixmap)

    def _construire_telephone(self) -> str:
        """Combine l'indicatif et le numero en format international."""
        numero = self.input_telephone.text().strip()
        if not numero:
            return ''
        indicatif = self.combo_indicatif.currentData() or '+33'
        # Nettoyer le numero : retirer espaces, tirets, points, et le 0 initial
        import re
        numero_nettoye = re.sub(r'[\s.\-]', '', numero)
        if numero_nettoye.startswith('0'):
            numero_nettoye = numero_nettoye[1:]
        return f"{indicatif}{numero_nettoye}"

    def _parser_telephone(self, telephone: str):
        """Parse un telephone international et configure l'indicatif + champ.

        Args:
            telephone: Numero au format "+33612345678" ou local "0612345678".
        """
        if not telephone:
            self.combo_indicatif.setCurrentIndex(0)  # FR +33
            self.input_telephone.clear()
            return

        # Chercher un indicatif correspondant
        for i in range(self.combo_indicatif.count()):
            indicatif = self.combo_indicatif.itemData(i)
            if telephone.startswith(indicatif):
                self.combo_indicatif.setCurrentIndex(i)
                numero = telephone[len(indicatif):]
                self.input_telephone.setText(numero)
                return

        # Pas d'indicatif reconnu, mettre tel quel dans le champ
        self.combo_indicatif.setCurrentIndex(0)
        self.input_telephone.setText(telephone)

    def _valider_email_temps_reel(self, texte: str):
        """Valide l'email en temps reel et change la bordure du champ.

        - Vide      : bordure par defaut
        - Valide    : bordure verte
        - Invalide  : bordure rouge
        """
        if not texte:
            self.input_email.setStyleSheet("")
        elif valider_email(texte):
            self.input_email.setStyleSheet("border: 1px solid #4CAF50;")
        else:
            self.input_email.setStyleSheet("border: 1px solid #F44336;")

    def _calculer_completude(self):
        """Met a jour la barre de progression du profil.

        Utilise la fonction centralis\u00e9e pour coh\u00e9rence avec recherche_view.
        """
        from utils.profile_completion import calculer_completion

        donnees = self._collecter_donnees()
        pourcentage = calculer_completion(donnees)

        self.barre_completude.setValue(pourcentage)

        if pourcentage >= 100:
            self.label_completude.setText("Profil complet !")
            self.label_completude.setStyleSheet("color: #4CAF50; font-weight: bold;")
        elif pourcentage >= 80:
            self.label_completude.setText(f"Profil presque complet ({pourcentage}%)")
            self.label_completude.setStyleSheet("color: #4CAF50;")
        elif pourcentage >= 50:
            self.label_completude.setText(f"Profil incomplet ({pourcentage}%)")
            self.label_completude.setStyleSheet("color: #FF9800;")
        else:
            self.label_completude.setText(f"Profil incomplet ({pourcentage}%)")
            self.label_completude.setStyleSheet("color: #F44336;")

    # ==================================================================
    # Collecte et sauvegarde des donnees
    # ==================================================================

    def _collecter_donnees(self) -> dict:
        """Collecte toutes les donnees du formulaire dans un dictionnaire.

        Les cles correspondent aux colonnes de la table clients.

        Returns:
            Dictionnaire des donnees saisies.
        """
        donnees = {
            'nom': self.input_nom.text().strip(),
            'prenom': self.input_prenom.text().strip(),
            'adresse': self.input_adresse.text().strip(),
            'ville': self.input_ville.text().strip(),
            'code_postal': self.input_code_postal.text().strip(),
            'email': self.input_email.text().strip(),
            'telephone': self._construire_telephone(),
            'situation_maritale': self.combo_situation.currentText(),
            'profession': self.input_profession.text().strip(),
            'notes_personnalisees': self.input_notes.toPlainText().strip(),
            'photo_path': self._photo_path or '',
        }

        # Date de naissance (vide si au minimum = pas de date)
        date_qt = self.input_date_naissance.date()
        if date_qt > QDate(1900, 1, 1):
            donnees['date_naissance'] = date_qt.toString("dd/MM/yyyy")
        else:
            donnees['date_naissance'] = ''

        # Dates conditionnelles selon la situation maritale
        situation = donnees.get('situation_maritale', '')
        if situation == "Marie(e)" and self.input_date_mariage.isVisible():
            donnees['date_mariage'] = self.input_date_mariage.date().toString("dd/MM/yyyy")
        if situation == "Pacse(e)" and self.input_date_pacs.isVisible():
            donnees['date_pacs'] = self.input_date_pacs.date().toString("dd/MM/yyyy")
        if situation == "Veuf/Veuve" and self.input_date_deces_conjoint.isVisible():
            donnees['date_deces_conjoint'] = self.input_date_deces_conjoint.date().toString("dd/MM/yyyy")

        return donnees

    def _collecter_donnees_conjoint(self) -> dict:
        """Collecte les donnees du formulaire conjoint.

        Returns:
            Dictionnaire des donnees du conjoint.
        """
        date_qt = self.input_date_naissance_conjoint.date()
        return {
            'nom': self.input_nom_conjoint.text().strip(),
            'prenom': self.input_prenom_conjoint.text().strip(),
            'date_naissance': date_qt.toString("dd/MM/yyyy"),
            'email': self.input_email_conjoint.text().strip(),
            'telephone': self.input_telephone_conjoint.text().strip(),
        }

    def _collecter_donnees_enfant(self, index: int) -> dict:
        """Collecte les donnees d'un formulaire enfant.

        Args:
            index: Index du formulaire enfant dans la liste.

        Returns:
            Dictionnaire des donnees de l'enfant.
        """
        if index >= len(self._formulaires_enfants):
            return {}
        form = self._formulaires_enfants[index]
        date_qt = form['date_naissance'].date()
        return {
            'nom': form['nom'].text().strip(),
            'prenom': form['prenom'].text().strip(),
            'date_naissance': date_qt.toString("dd/MM/yyyy"),
        }

    def _collecter_donnees_parent(self, type_parent: str) -> dict:
        """Collecte les donnees d'un formulaire parent.

        Args:
            type_parent: 'pere' ou 'mere'.

        Returns:
            Dictionnaire des donnees du parent.
        """
        if type_parent == 'pere':
            return {
                'nom': self.input_nom_pere.text().strip(),
                'prenom': self.input_prenom_pere.text().strip(),
                'email': self.input_email_pere.text().strip(),
                'telephone': self.input_telephone_pere.text().strip(),
            }
        elif type_parent == 'mere':
            return {
                'nom': self.input_nom_mere.text().strip(),
                'prenom': self.input_prenom_mere.text().strip(),
                'email': self.input_email_mere.text().strip(),
                'telephone': self.input_telephone_mere.text().strip(),
            }
        return {}

    def _sauvegarder(self):
        """Sauvegarde le client via le ViewModel.

        Sauvegarde d'abord le client principal, puis cree les clients
        lies (conjoint, enfants, parents) si les checkboxes correspondantes
        sont cochees.
        """
        donnees = self._collecter_donnees()
        client_id = self.viewmodel.sauvegarder_client(donnees)

        if client_id is None:
            # L'erreur est geree par le signal erreur du ViewModel
            return

        # --- Sauvegarder les centres d'interet ---
        noms_centres = self.widget_centres_interet.obtenir_centres()
        if noms_centres is not None:
            ci_model = CentreInteretModel()
            ci_model.definir_centres_client(client_id, noms_centres)

        # --- Creer les clients lies si demande ---

        # Conjoint
        if (self.groupe_conjoint.isVisible()
                and self.checkbox_a_conjoint.isChecked()
                and self.checkbox_creer_compte_conjoint.isChecked()):
            donnees_conjoint = self._collecter_donnees_conjoint()
            if donnees_conjoint.get('nom') and donnees_conjoint.get('prenom'):
                self.viewmodel.creer_client_lie(
                    donnees_conjoint, 'conjoint', client_id
                )

        # Enfants
        if self.checkbox_a_enfants.isChecked():
            for i, form_enfant in enumerate(self._formulaires_enfants):
                if form_enfant['creer_compte'].isChecked():
                    donnees_enfant = self._collecter_donnees_enfant(i)
                    if donnees_enfant.get('nom') and donnees_enfant.get('prenom'):
                        self.viewmodel.creer_client_lie(
                            donnees_enfant, 'enfant', client_id
                        )

        # Parents
        if (self.checkbox_a_parents.isChecked()
                and self.checkbox_parents_en_vie.isChecked()):
            # Pere
            if self.checkbox_creer_compte_pere.isChecked():
                donnees_pere = self._collecter_donnees_parent('pere')
                if donnees_pere.get('nom') and donnees_pere.get('prenom'):
                    self.viewmodel.creer_client_lie(
                        donnees_pere, 'parent', client_id
                    )
            # Mere
            if self.checkbox_creer_compte_mere.isChecked():
                donnees_mere = self._collecter_donnees_parent('mere')
                if donnees_mere.get('nom') and donnees_mere.get('prenom'):
                    self.viewmodel.creer_client_lie(
                        donnees_mere, 'parent', client_id
                    )

    def _annuler(self):
        """Reinitialise le formulaire (equivalent a Nouveau Client)."""
        self.nouveau_client()

    # ==================================================================
    # Methodes publiques
    # ==================================================================

    def nouveau_client(self):
        """Reinitialise le formulaire pour un nouveau client.

        Remet tous les champs a vide et le titre a 'Nouveau Client'.
        """
        self.label_titre.setText("Nouveau Client")
        self.viewmodel._client_actuel_id = None

        # --- Informations de base ---
        self.input_nom.clear()
        self.input_prenom.clear()
        self.input_date_naissance.setDate(QDate(1900, 1, 1))
        self.label_age.setText("\u2014 ans")
        self.input_adresse.clear()
        self.input_ville.clear()
        self.input_code_postal.clear()
        self.input_email.clear()
        self.input_email.setStyleSheet("")
        self.combo_indicatif.setCurrentIndex(0)
        self.input_telephone.clear()

        # --- Situation familiale ---
        self.combo_situation.setCurrentIndex(0)

        # Conjoint
        self.checkbox_a_conjoint.setChecked(False)
        self.input_nom_conjoint.clear()
        self.input_prenom_conjoint.clear()
        self.input_date_naissance_conjoint.setDate(QDate.currentDate())
        self.input_email_conjoint.clear()
        self.input_telephone_conjoint.clear()
        self.checkbox_creer_compte_conjoint.setChecked(False)

        # Enfants
        self.checkbox_a_enfants.setChecked(False)
        self.spin_nombre_enfants.setValue(1)

        # Parents
        self.checkbox_a_parents.setChecked(False)
        self.checkbox_parents_en_vie.setChecked(True)
        self.input_nom_pere.clear()
        self.input_prenom_pere.clear()
        self.input_email_pere.clear()
        self.input_telephone_pere.clear()
        self.checkbox_creer_compte_pere.setChecked(False)
        self.input_nom_mere.clear()
        self.input_prenom_mere.clear()
        self.input_email_mere.clear()
        self.input_telephone_mere.clear()
        self.checkbox_creer_compte_mere.setChecked(False)

        # --- Dates situation ---
        self.input_date_mariage.setDate(QDate.currentDate())
        self.input_date_pacs.setDate(QDate.currentDate())
        self.input_date_deces_conjoint.setDate(QDate.currentDate())
        self.widget_dates_situation.setVisible(False)

        # --- Photo ---
        self._photo_pixmap_original = None
        self._supprimer_photo()

        # --- Informations supplementaires ---
        self.input_profession.clear()
        self.widget_centres_interet.vider()
        self.input_notes.clear()

        # --- Completude ---
        self.barre_completude.setValue(0)
        self.label_completude.setText("Profil incomplet (0%)")
        self.label_completude.setStyleSheet("color: #FF9800;")

        # Remonter le scroll en haut
        self.scroll_area.verticalScrollBar().setValue(0)

    def charger_client(self, client_id: int):
        """Charge un client existant pour modification.

        Appelle le ViewModel pour recuperer les donnees du client
        et remplit tous les champs du formulaire.

        Args:
            client_id: Identifiant du client a charger.
        """
        self.label_titre.setText("Modifier Client")

        client = self.viewmodel.charger_client(client_id)
        if client is None:
            QMessageBox.warning(
                self, "Erreur", f"Impossible de charger le client {client_id}."
            )
            return

        # --- Remplir les champs Informations de base ---
        self.input_nom.setText(client.get('nom', ''))
        self.input_prenom.setText(client.get('prenom', ''))

        # Date de naissance
        date_str = client.get('date_naissance', '')
        if date_str:
            date_qt = QDate.fromString(date_str, "dd/MM/yyyy")
            if not date_qt.isValid():
                date_qt = QDate.fromString(date_str, "yyyy-MM-dd")
            if date_qt.isValid():
                self.input_date_naissance.setDate(date_qt)
            else:
                self.input_date_naissance.setDate(QDate(1900, 1, 1))
        else:
            self.input_date_naissance.setDate(QDate(1900, 1, 1))

        self.input_adresse.setText(client.get('adresse', ''))
        self.input_ville.setText(client.get('ville', ''))
        self.input_code_postal.setText(client.get('code_postal', ''))
        self.input_email.setText(client.get('email', ''))
        self._parser_telephone(client.get('telephone', ''))

        # --- Situation familiale ---
        situation = client.get('situation_maritale', '')
        index_situation = self.combo_situation.findText(situation)
        if index_situation >= 0:
            self.combo_situation.setCurrentIndex(index_situation)
        else:
            self.combo_situation.setCurrentIndex(0)

        # --- Dates situation maritale ---
        date_mariage = client.get('date_mariage', '')
        if date_mariage:
            date_qt = QDate.fromString(date_mariage, "dd/MM/yyyy")
            if not date_qt.isValid():
                date_qt = QDate.fromString(date_mariage, "yyyy-MM-dd")
            if date_qt.isValid():
                self.input_date_mariage.setDate(date_qt)

        date_pacs = client.get('date_pacs', '')
        if date_pacs:
            date_qt = QDate.fromString(date_pacs, "dd/MM/yyyy")
            if not date_qt.isValid():
                date_qt = QDate.fromString(date_pacs, "yyyy-MM-dd")
            if date_qt.isValid():
                self.input_date_pacs.setDate(date_qt)

        date_deces = client.get('date_deces_conjoint', '')
        if date_deces:
            date_qt = QDate.fromString(date_deces, "dd/MM/yyyy")
            if not date_qt.isValid():
                date_qt = QDate.fromString(date_deces, "yyyy-MM-dd")
            if date_qt.isValid():
                self.input_date_deces_conjoint.setDate(date_qt)

        # --- Photo de profil ---
        photo = client.get('photo_path', '')
        if photo and os.path.exists(photo):
            self._photo_path = photo
            self._afficher_photo(photo)
        else:
            self._photo_pixmap_original = None
            self._supprimer_photo()

        # --- Informations supplementaires ---
        self.input_profession.setText(client.get('profession', ''))
        self.input_notes.setPlainText(client.get('notes_personnalisees', ''))

        # --- Centres d'interet ---
        ci_model = CentreInteretModel()
        centres = ci_model.obtenir_centres_client(client_id)
        self.widget_centres_interet.definir_centres([c['nom'] for c in centres])

        # --- Mettre a jour la completude ---
        self._calculer_completude()

        # Remonter le scroll en haut
        self.scroll_area.verticalScrollBar().setValue(0)

    # ==================================================================
    # Callbacks du ViewModel
    # ==================================================================

    def _on_succes(self, client_id: int):
        """Callback appele apres une sauvegarde reussie.

        Affiche un message de succes, reinitialise le formulaire
        et re-emet le signal client_sauvegarde.

        Args:
            client_id: Identifiant du client sauvegarde.
        """
        QMessageBox.information(
            self, "Succes", "Client enregistre avec succes !"
        )
        self.nouveau_client()
        self.client_sauvegarde.emit(client_id)

    def _on_erreur(self, message: str):
        """Callback en cas d'erreur lors de la sauvegarde.

        Args:
            message: Message d'erreur a afficher.
        """
        QMessageBox.warning(self, "Erreur", message)
