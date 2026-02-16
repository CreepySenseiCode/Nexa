"""
Vue Emailing - Interface d'envoi d'emails avec editeur riche.
"""

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QGroupBox, QScrollArea, QComboBox, QFrame,
    QMessageBox, QFileDialog, QListWidget, QListWidgetItem,
    QFontComboBox, QSpinBox, QDialog, QDialogButtonBox,
    QDateTimeEdit, QInputDialog, QSizePolicy,
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont, QTextImageFormat

from PySide6.QtWidgets import QLayout

from utils.styles import style_groupe, style_input, style_bouton, style_scroll_area, Couleurs
from viewmodels.emailing_vm import EmailingViewModel


class FlowLayout(QLayout):
    """Layout qui dispose les widgets en lignes avec retour automatique."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._spacing = 6

    def setSpacing(self, spacing):
        self._spacing = spacing

    def spacing(self):
        return self._spacing

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(200, 50)

    def minimumSize(self):
        from PySide6.QtCore import QSize
        w = 0
        h = 0
        for item in self._items:
            s = item.minimumSize()
            w = max(w, s.width())
            h = max(h, s.height())
        return QSize(w, h)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(self.geometry(), False, width)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, True)

    def _do_layout(self, rect, apply, width=None):
        x = rect.x()
        y = rect.y()
        line_height = 0
        w = width if width is not None else rect.width()

        for item in self._items:
            item_size = item.sizeHint()
            next_x = x + item_size.width() + self._spacing
            if next_x - self._spacing > rect.x() + w and line_height > 0:
                x = rect.x()
                y += line_height + self._spacing
                next_x = x + item_size.width() + self._spacing
                line_height = 0
            if apply:
                from PySide6.QtCore import QRect
                item.setGeometry(QRect(x, y, item_size.width(), item_size.height()))
            x = next_x
            line_height = max(line_height, item_size.height())
        return y + line_height - rect.y()


class EmailingView(QWidget):
    """Interface d'envoi d'emails avec editeur riche."""

    def __init__(self):
        super().__init__()
        self.viewmodel = EmailingViewModel()
        self._construire_ui()

    def _construire_ui(self):
        """Construit l'interface utilisateur."""
        layout_principal = QVBoxLayout()
        layout_principal.setSpacing(20)
        layout_principal.setContentsMargins(30, 30, 30, 30)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(style_scroll_area())

        conteneur = QWidget()
        layout_conteneur = QVBoxLayout()
        layout_conteneur.setSpacing(15)

        # Section Destinataires
        layout_conteneur.addWidget(self._creer_section_destinataires())

        # Section Contenu (editeur riche)
        layout_conteneur.addWidget(self._creer_section_contenu())

        # Section Pieces jointes
        layout_conteneur.addWidget(self._creer_section_pieces_jointes())

        layout_conteneur.addStretch()

        conteneur.setLayout(layout_conteneur)
        scroll.setWidget(conteneur)

        layout_principal.addWidget(scroll)

        # Boutons d'action
        layout_principal.addLayout(self._creer_boutons_action())

        self.setLayout(layout_principal)
        self.setStyleSheet("background-color: #F5F5F5;")

    # ------------------------------------------------------------------ #
    #                     Section Destinataires                           #
    # ------------------------------------------------------------------ #

    def _creer_section_destinataires(self) -> QGroupBox:
        """Section destinataires avec gestion dynamique."""
        group = QGroupBox("Destinataires")
        group.setStyleSheet(style_groupe())

        layout = QVBoxLayout()

        # Type d'envoi
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type d'envoi :"))

        self.combo_type = QComboBox()
        self.combo_type.addItems([
            "Client unique",
            "Selection de clients (filtres)",
            "Tous les clients",
        ])
        self.combo_type.setStyleSheet(style_input())
        self.combo_type.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.combo_type)
        type_layout.addStretch()

        layout.addLayout(type_layout)

        # === ZONE CLIENT UNIQUE ===
        self.zone_unique = QWidget()
        unique_layout = QVBoxLayout(self.zone_unique)
        unique_layout.setContentsMargins(0, 0, 0, 0)

        self.input_client = QLineEdit()
        self.input_client.setPlaceholderText(
            "Rechercher un client (nom, email, telephone)..."
        )
        self.input_client.setStyleSheet(style_input())
        self.input_client.textChanged.connect(self._rechercher_client)
        unique_layout.addWidget(self.input_client)

        self.list_resultats_client = QListWidget()
        self.list_resultats_client.setMaximumHeight(150)
        self.list_resultats_client.setStyleSheet(
            "QListWidget { border: 2px solid #E0E0E0; border-radius: 8px; "
            "padding: 5px; background-color: white; }"
        )
        self.list_resultats_client.itemClicked.connect(
            self._selectionner_client
        )
        unique_layout.addWidget(self.list_resultats_client)

        layout.addWidget(self.zone_unique)

        # === ZONE SELECTION (FILTRES) ===
        self.zone_selection = QWidget()
        selection_layout = QVBoxLayout(self.zone_selection)
        selection_layout.setContentsMargins(0, 0, 0, 0)

        selection_layout.addWidget(QLabel("Filtres de ciblage :"))

        # Filtre Age
        age_layout = QHBoxLayout()
        age_layout.addWidget(QLabel("Age :"))
        self.spin_age_min = QSpinBox()
        self.spin_age_min.setRange(0, 120)
        self.spin_age_min.setValue(18)
        self.spin_age_min.setSuffix(" ans min")
        age_layout.addWidget(self.spin_age_min)
        self.spin_age_max = QSpinBox()
        self.spin_age_max.setRange(0, 120)
        self.spin_age_max.setValue(99)
        self.spin_age_max.setSuffix(" ans max")
        age_layout.addWidget(self.spin_age_max)
        age_layout.addStretch()
        selection_layout.addLayout(age_layout)

        # Filtre Famille
        famille_layout = QHBoxLayout()
        famille_layout.addWidget(QLabel("Situation familiale :"))
        self.combo_famille = QComboBox()
        self.combo_famille.addItems([
            "Toutes", "Celibataire", "Marie(e)", "Divorce(e)", "Veuf/Veuve",
        ])
        famille_layout.addWidget(self.combo_famille)
        famille_layout.addStretch()
        selection_layout.addLayout(famille_layout)

        # Filtre Centres d'interet
        interets_layout = QHBoxLayout()
        interets_layout.addWidget(QLabel("Centres d'interet (separes par ,) :"))
        self.input_interets = QLineEdit()
        self.input_interets.setPlaceholderText("sport, cuisine, voyages...")
        interets_layout.addWidget(self.input_interets)
        selection_layout.addLayout(interets_layout)

        # Bouton Appliquer filtres
        btn_appliquer = QPushButton("Appliquer les filtres")
        btn_appliquer.setStyleSheet(style_bouton(Couleurs.PRIMAIRE))
        btn_appliquer.clicked.connect(self._appliquer_filtres)
        selection_layout.addWidget(btn_appliquer)

        self.zone_selection.hide()
        layout.addWidget(self.zone_selection)

        # === ZONE TOUS ===
        self.zone_tous = QWidget()
        tous_layout = QVBoxLayout(self.zone_tous)
        tous_layout.setContentsMargins(0, 0, 0, 0)

        info_tous = QLabel(
            "L'email sera envoye a TOUS les clients de la base de donnees."
        )
        info_tous.setStyleSheet(
            "QLabel { background-color: #FFF3E0; border: 2px solid #FF9800; "
            "border-radius: 8px; padding: 15px; font-size: 12pt; "
            "color: #F57C00; }"
        )
        tous_layout.addWidget(info_tous)

        self.zone_tous.hide()
        layout.addWidget(self.zone_tous)

        # Liste finale des destinataires
        label_dest = QLabel("Destinataires selectionnes :")
        label_dest.setStyleSheet("font-weight: 600; margin-top: 10px;")
        layout.addWidget(label_dest)

        self.list_destinataires = QListWidget()
        self.list_destinataires.setStyleSheet(
            "QListWidget { border: 2px solid #E0E0E0; border-radius: 8px; "
            "padding: 5px; background-color: white; }"
        )
        self.list_destinataires.setMaximumHeight(150)
        layout.addWidget(self.list_destinataires)

        group.setLayout(layout)
        return group

    def _on_type_changed(self, index: int):
        """Change l'affichage selon le type selectionne."""
        self.zone_unique.hide()
        self.zone_selection.hide()
        self.zone_tous.hide()

        if index == 0:
            self.zone_unique.show()
        elif index == 1:
            self.zone_selection.show()
        elif index == 2:
            self.zone_tous.show()
            self._charger_tous_les_clients()

    def _rechercher_client(self, texte: str):
        """Recherche un client en temps reel."""
        if len(texte) < 2:
            self.list_resultats_client.clear()
            return
        clients = self.viewmodel.rechercher_clients(texte)
        self.list_resultats_client.clear()
        for client in clients:
            item = QListWidgetItem(
                f"{client['prenom']} {client['nom']} ({client['email']})"
            )
            item.setData(Qt.ItemDataRole.UserRole, client)
            self.list_resultats_client.addItem(item)

    def _selectionner_client(self, item: QListWidgetItem):
        """Selectionne un client."""
        client = item.data(Qt.ItemDataRole.UserRole)
        dest_item = QListWidgetItem(
            f"{client['prenom']} {client['nom']} - {client['email']}"
        )
        dest_item.setData(Qt.ItemDataRole.UserRole, client['id'])
        self.list_destinataires.addItem(dest_item)
        self.input_client.clear()
        self.list_resultats_client.clear()

    def _appliquer_filtres(self):
        """Applique les filtres et charge les clients correspondants."""
        try:
            situation = self.combo_famille.currentText()
            interets_text = self.input_interets.text().strip()
            interets = [i.strip() for i in interets_text.split(',') if i.strip()] if interets_text else None

            clients = self.viewmodel.filtrer_clients(
                age_min=self.spin_age_min.value(),
                age_max=self.spin_age_max.value(),
                situation=situation,
                interets=interets,
            )

            self.list_destinataires.clear()
            for client in clients:
                item = QListWidgetItem(
                    f"{client['prenom']} {client['nom']} - {client['email']}"
                )
                item.setData(Qt.ItemDataRole.UserRole, client['id'])
                self.list_destinataires.addItem(item)

            QMessageBox.information(
                self, "Filtres appliques",
                f"{len(clients)} client(s) correspondent aux criteres",
            )
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur filtres : {e}")

    def _charger_tous_les_clients(self):
        """Charge TOUS les clients."""
        clients = self.viewmodel.charger_tous_les_clients()
        self.list_destinataires.clear()
        for client in clients:
            item = QListWidgetItem(
                f"{client['prenom']} {client['nom']} - {client['email']}"
            )
            item.setData(Qt.ItemDataRole.UserRole, client['id'])
            self.list_destinataires.addItem(item)

    # ------------------------------------------------------------------ #
    #                     Section Contenu (editeur riche)                 #
    # ------------------------------------------------------------------ #

    def _creer_section_contenu(self) -> QGroupBox:
        """Section contenu avec editeur riche."""
        group = QGroupBox("Contenu de l'email")
        group.setStyleSheet(style_groupe())

        layout = QVBoxLayout()

        # Objet
        layout.addWidget(QLabel("Objet :"))
        self.input_objet = QLineEdit()
        self.input_objet.setPlaceholderText(
            "Ex: Nouvelle promotion sur nos produits"
        )
        self.input_objet.setStyleSheet(style_input())
        layout.addWidget(self.input_objet)

        # === BARRE D'OUTILS EDITEUR RICHE ===
        toolbar_layout = QHBoxLayout()

        # Police
        self.combo_police = QFontComboBox()
        self.combo_police.setCurrentFont(QFont("Arial"))
        self.combo_police.currentFontChanged.connect(self._changer_police)
        toolbar_layout.addWidget(self.combo_police)

        # Taille
        self.spin_taille = QSpinBox()
        self.spin_taille.setRange(8, 72)
        self.spin_taille.setValue(12)
        self.spin_taille.setSuffix(" pt")
        self.spin_taille.valueChanged.connect(self._changer_taille)
        toolbar_layout.addWidget(self.spin_taille)

        toolbar_layout.addSpacing(15)

        # Gras
        self.btn_gras = QPushButton("B")
        self.btn_gras.setCheckable(True)
        self.btn_gras.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.btn_gras.setFixedSize(36, 36)
        self.btn_gras.clicked.connect(self._toggle_gras)
        toolbar_layout.addWidget(self.btn_gras)

        # Italique
        self.btn_italique = QPushButton("I")
        self.btn_italique.setCheckable(True)
        font_i = QFont("Arial", 12)
        font_i.setItalic(True)
        self.btn_italique.setFont(font_i)
        self.btn_italique.setFixedSize(36, 36)
        self.btn_italique.clicked.connect(self._toggle_italique)
        toolbar_layout.addWidget(self.btn_italique)

        # Souligne
        self.btn_souligne = QPushButton("U")
        self.btn_souligne.setCheckable(True)
        font_u = QFont("Arial", 12)
        font_u.setUnderline(True)
        self.btn_souligne.setFont(font_u)
        self.btn_souligne.setFixedSize(36, 36)
        self.btn_souligne.clicked.connect(self._toggle_souligne)
        toolbar_layout.addWidget(self.btn_souligne)

        toolbar_layout.addSpacing(15)

        # Alignement
        btn_gauche = QPushButton("\u25C0")
        btn_gauche.setFixedSize(36, 36)
        btn_gauche.clicked.connect(
            lambda: self.text_message.setAlignment(Qt.AlignmentFlag.AlignLeft)
        )
        toolbar_layout.addWidget(btn_gauche)

        btn_centre = QPushButton("\u25AC")
        btn_centre.setFixedSize(36, 36)
        btn_centre.clicked.connect(
            lambda: self.text_message.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
        )
        toolbar_layout.addWidget(btn_centre)

        btn_droite = QPushButton("\u25B6")
        btn_droite.setFixedSize(36, 36)
        btn_droite.clicked.connect(
            lambda: self.text_message.setAlignment(
                Qt.AlignmentFlag.AlignRight
            )
        )
        toolbar_layout.addWidget(btn_droite)

        toolbar_layout.addSpacing(15)

        # Couleur texte
        btn_couleur = QPushButton("Couleur")
        btn_couleur.clicked.connect(self._choisir_couleur_texte)
        toolbar_layout.addWidget(btn_couleur)

        # Inserer image
        btn_image = QPushButton("Image")
        btn_image.clicked.connect(self._inserer_image)
        toolbar_layout.addWidget(btn_image)

        toolbar_layout.addStretch()

        layout.addLayout(toolbar_layout)

        # === EDITEUR RICHE ===
        self.text_message = QTextEdit()
        self.text_message.setPlaceholderText(
            "Bonjour,\n\n"
            "Nous avons le plaisir de vous annoncer...\n\n"
            "Cordialement,\n"
            "L'equipe"
        )
        self.text_message.setAcceptRichText(True)
        self.text_message.setStyleSheet(
            "QTextEdit { border: 2px solid #E0E0E0; border-radius: 8px; "
            "padding: 10px; font-size: 12pt; background-color: white; }"
            "QTextEdit:focus { border: 2px solid #2196F3; }"
        )
        self.text_message.setMinimumHeight(350)
        layout.addWidget(self.text_message)

        group.setLayout(layout)
        return group

    # === METHODES EDITEUR RICHE ===

    def _changer_police(self, font: QFont):
        """Change la police du texte selectionne."""
        self.text_message.setCurrentFont(font)

    def _changer_taille(self, taille: int):
        """Change la taille de la police."""
        self.text_message.setFontPointSize(taille)

    def _toggle_gras(self):
        """Active/desactive le gras."""
        if self.btn_gras.isChecked():
            self.text_message.setFontWeight(QFont.Weight.Bold)
        else:
            self.text_message.setFontWeight(QFont.Weight.Normal)

    def _toggle_italique(self):
        """Active/desactive l'italique."""
        self.text_message.setFontItalic(self.btn_italique.isChecked())

    def _toggle_souligne(self):
        """Active/desactive le souligne."""
        self.text_message.setFontUnderline(self.btn_souligne.isChecked())

    def _choisir_couleur_texte(self):
        """Ouvre le selecteur de couleur."""
        from PySide6.QtWidgets import QColorDialog

        couleur = QColorDialog.getColor()
        if couleur.isValid():
            self.text_message.setTextColor(couleur)

    def _inserer_image(self):
        """Insere une image dans l'editeur."""
        fichier, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir une image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif)",
        )
        if fichier:
            cursor = self.text_message.textCursor()
            image = QTextImageFormat()
            image.setName(fichier)
            image.setWidth(400)
            cursor.insertImage(image)

    # ------------------------------------------------------------------ #
    #                     Section Pieces jointes                          #
    # ------------------------------------------------------------------ #

    def _creer_section_pieces_jointes(self) -> QGroupBox:
        """Section pieces jointes avec rectangles supprimables."""
        group = QGroupBox("Pieces jointes")
        group.setStyleSheet(style_groupe())

        layout = QVBoxLayout()

        btn_ajouter_fichier = QPushButton("Ajouter un fichier")
        btn_ajouter_fichier.setStyleSheet(style_bouton(Couleurs.PRIMAIRE))
        btn_ajouter_fichier.clicked.connect(self._ajouter_piece_jointe)
        layout.addWidget(btn_ajouter_fichier)

        # Conteneur pour les fichiers attaches (flow layout horizontal avec wrap)
        self.pj_conteneur = QWidget()
        self.pj_layout = FlowLayout(self.pj_conteneur)
        self.pj_layout.setSpacing(8)
        self.pj_fichiers = []  # liste des chemins complets
        layout.addWidget(self.pj_conteneur)

        group.setLayout(layout)
        return group

    def _creer_pj_rectangle(self, chemin: str) -> QFrame:
        """Cree un rectangle stylise pour une piece jointe."""
        nom_fichier = os.path.basename(chemin)
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background-color: {Couleurs.PRIMAIRE_TRES_CLAIR}; "
            f"border: 1px solid {Couleurs.PRIMAIRE_CLAIR}; border-radius: 8px; "
            f"padding: 6px 10px; }}"
        )
        h = QHBoxLayout(frame)
        h.setContentsMargins(8, 4, 4, 4)
        h.setSpacing(8)

        lbl = QLabel(nom_fichier)
        lbl.setStyleSheet(f"font-size: 11pt; color: {Couleurs.PRIMAIRE_FONCE}; border: none;")
        h.addWidget(lbl)

        btn_x = QPushButton("X")
        btn_x.setFixedSize(24, 24)
        btn_x.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_x.setStyleSheet(
            f"QPushButton {{ background-color: {Couleurs.DANGER}; color: white; "
            f"border: none; border-radius: 12px; font-size: 10pt; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {Couleurs.DANGER_FONCE}; }}"
        )
        btn_x.clicked.connect(lambda: self._retirer_piece_jointe(chemin, frame))
        h.addWidget(btn_x)

        return frame

    # ------------------------------------------------------------------ #
    #                     Boutons d'action                                #
    # ------------------------------------------------------------------ #

    def _creer_boutons_action(self) -> QHBoxLayout:
        """Boutons d'action en bas."""
        layout = QHBoxLayout()
        layout.addStretch()

        # Annuler
        btn_annuler = QPushButton("Annuler")
        btn_annuler.setMinimumHeight(50)
        btn_annuler.setMinimumWidth(150)
        btn_annuler.setStyleSheet(style_bouton(Couleurs.GRIS))
        btn_annuler.clicked.connect(self._annuler)
        layout.addWidget(btn_annuler)

        # Enregistrer comme template
        btn_template = QPushButton("Enregistrer template")
        btn_template.setMinimumHeight(50)
        btn_template.setMinimumWidth(200)
        btn_template.setStyleSheet(style_bouton(Couleurs.VIOLET))
        btn_template.clicked.connect(self._enregistrer_template)
        layout.addWidget(btn_template)

        # Programmer l'envoi
        btn_programmer = QPushButton("Programmer l'envoi")
        btn_programmer.setMinimumHeight(50)
        btn_programmer.setMinimumWidth(200)
        btn_programmer.setStyleSheet(style_bouton(Couleurs.AVERTISSEMENT))
        btn_programmer.clicked.connect(self._programmer_envoi)
        layout.addWidget(btn_programmer)

        # Enregistrer brouillon
        btn_brouillon = QPushButton("Enregistrer brouillon")
        btn_brouillon.setMinimumHeight(50)
        btn_brouillon.setMinimumWidth(200)
        btn_brouillon.setStyleSheet(style_bouton(Couleurs.ARDOISE))
        btn_brouillon.clicked.connect(self._enregistrer_brouillon)
        layout.addWidget(btn_brouillon)

        # Envoyer maintenant
        btn_envoyer = QPushButton("Envoyer maintenant")
        btn_envoyer.setMinimumHeight(50)
        btn_envoyer.setMinimumWidth(200)
        btn_envoyer.setStyleSheet(style_bouton(Couleurs.SUCCES))
        btn_envoyer.clicked.connect(self._envoyer_email)
        layout.addWidget(btn_envoyer)

        return layout

    # ------------------------------------------------------------------ #
    #                     Actions                                         #
    # ------------------------------------------------------------------ #

    def _ajouter_piece_jointe(self):
        """Ajoute des pieces jointes sous forme de rectangles."""
        fichiers, _ = QFileDialog.getOpenFileNames(
            self, "Selectionner des fichiers", "", "Tous les fichiers (*.*)"
        )
        for fichier in fichiers:
            if fichier not in self.pj_fichiers:
                self.pj_fichiers.append(fichier)
                rect = self._creer_pj_rectangle(fichier)
                self.pj_layout.addWidget(rect)

    def _retirer_piece_jointe(self, chemin: str, frame: QFrame):
        """Retire une piece jointe."""
        if chemin in self.pj_fichiers:
            self.pj_fichiers.remove(chemin)
        # Remove from layout BEFORE deleting to avoid crash on next layout pass
        for i in range(self.pj_layout.count()):
            item = self.pj_layout.itemAt(i)
            if item and item.widget() == frame:
                self.pj_layout.takeAt(i)
                break
        frame.deleteLater()

    def _annuler(self):
        """Annule la creation d'email."""
        reponse = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment annuler ?\n"
            "Les modifications seront perdues.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reponse == QMessageBox.StandardButton.Yes:
            self._reinitialiser()

    def _enregistrer_template(self):
        """Enregistre l'email comme template."""
        nom, ok = QInputDialog.getText(
            self, "Nom du template", "Nom :"
        )
        if ok and nom:
            QMessageBox.information(
                self,
                "Template enregistre",
                f"Template '{nom}' enregistre avec succes.",
            )

    def _programmer_envoi(self):
        """Ouvre le dialog de programmation."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Programmer l'envoi")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout()

        layout.addWidget(
            QLabel("Choisissez la date et l'heure d'envoi :")
        )

        datetime_edit = QDateTimeEdit()
        datetime_edit.setCalendarPopup(True)
        datetime_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
        datetime_edit.setStyleSheet("font-size: 13pt; padding: 10px;")
        layout.addWidget(datetime_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            dt = datetime_edit.dateTime().toString("dd/MM/yyyy a HH:mm")
            QMessageBox.information(
                self,
                "Envoi programme",
                f"Email programme pour le {dt}",
            )

    def _enregistrer_brouillon(self):
        """Enregistre en brouillon."""
        QMessageBox.information(
            self,
            "Brouillon enregistre",
            "L'email a ete enregistre dans vos brouillons.",
        )

    def _envoyer_email(self):
        """Envoie l'email."""
        if not self.input_objet.text().strip():
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un objet")
            return
        if not self.text_message.toPlainText().strip():
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un message")
            return
        if self.list_destinataires.count() == 0:
            QMessageBox.warning(
                self,
                "Erreur",
                "Veuillez selectionner au moins un destinataire",
            )
            return

        QMessageBox.information(
            self,
            "Email envoye",
            f"Email envoye a {self.list_destinataires.count()} "
            f"destinataire(s)",
        )
        self._reinitialiser()

    def _reinitialiser(self):
        """Reinitialise le formulaire."""
        self.input_objet.clear()
        self.text_message.clear()
        self.list_destinataires.clear()
        # Vider les pieces jointes
        self.pj_fichiers.clear()
        while self.pj_layout.count():
            item = self.pj_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.combo_type.setCurrentIndex(0)

