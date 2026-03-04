"""Vue pour la creation et la gestion des codes promotionnels (mode Patron).

Ce module fournit la classe CodesPromoCreationView qui permet de creer,
modifier, activer/desactiver et supprimer des codes de reduction.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QDoubleSpinBox,
    QSpinBox, QDateEdit, QTextEdit, QCheckBox, QComboBox,
    QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QScrollArea,
    QRadioButton, QStackedWidget,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from utils.styles import style_toggle, Couleurs
from viewmodels.codes_promo_vm import CodesPromoViewModel


class CodesPromoCreationView(QWidget):
    """Vue pour la creation et la gestion des codes de reduction (Patron)."""

    def __init__(self, viewmodel=None):
        super().__init__()

        # Creer le ViewModel si non fourni
        if viewmodel is None:
            self.viewmodel = CodesPromoViewModel()
        else:
            self.viewmodel = viewmodel

        self._construire_ui()
        self._connecter_signaux()
        self._rafraichir_table()

    # ------------------------------------------------------------------ #
    #                        Construction de l'UI                         #
    # ------------------------------------------------------------------ #

    # Pages du stacked widget
    PAGE_LISTE = 0
    PAGE_NOUVEAU = 1

    def _construire_ui(self):
        """Construit l'interface complete avec toggle Liste/Nouveau."""

        layout_self = QVBoxLayout(self)
        layout_self.setContentsMargins(0, 0, 0, 0)
        layout_self.setSpacing(0)

        # === BARRE DE TOGGLE ===
        barre_toggle = QWidget()
        barre_toggle.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        toggle_layout = QHBoxLayout(barre_toggle)
        toggle_layout.setContentsMargins(30, 15, 30, 0)
        toggle_layout.setSpacing(10)

        toggle_layout.addStretch()

        self.btn_toggle_liste = QPushButton("Liste")
        self.btn_toggle_liste.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_liste.clicked.connect(lambda: self._changer_page_promo(self.PAGE_LISTE))

        self.btn_toggle_nouveau = QPushButton("Nouveau code")
        self.btn_toggle_nouveau.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_nouveau.clicked.connect(lambda: self._changer_page_promo(self.PAGE_NOUVEAU))

        toggle_layout.addWidget(self.btn_toggle_liste)
        toggle_layout.addWidget(self.btn_toggle_nouveau)

        layout_self.addWidget(barre_toggle)

        # === STACKED WIDGET ===
        self.pile_promo = QStackedWidget()

        # Page 0 : Liste (tableau)
        page_liste = QWidget()
        page_liste.setStyleSheet("background-color: #FFFFFF;")
        layout_liste = QVBoxLayout(page_liste)
        layout_liste.setSpacing(16)
        layout_liste.setContentsMargins(20, 20, 20, 20)
        self._construire_tableau(layout_liste)
        layout_liste.addStretch()
        self.pile_promo.addWidget(page_liste)

        # Page 1 : Nouveau code (formulaire)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #FFFFFF; }")

        conteneur = QWidget()
        conteneur.setStyleSheet("background-color: #FFFFFF;")
        layout_form = QVBoxLayout(conteneur)
        layout_form.setSpacing(16)
        layout_form.setContentsMargins(20, 20, 20, 20)
        self._construire_formulaire(layout_form)
        layout_form.addStretch()
        scroll.setWidget(conteneur)
        self.pile_promo.addWidget(scroll)

        layout_self.addWidget(self.pile_promo)

        # Etat initial
        self._changer_page_promo(self.PAGE_LISTE)

    def _changer_page_promo(self, index: int):
        """Change la page et met a jour les styles des boutons."""
        self.pile_promo.setCurrentIndex(index)
        self.btn_toggle_liste.setStyleSheet(style_toggle(index == self.PAGE_LISTE))
        self.btn_toggle_nouveau.setStyleSheet(style_toggle(index == self.PAGE_NOUVEAU))
        if index == self.PAGE_LISTE:
            self._rafraichir_table()

    # ------------------------------------------------------------------ #
    #                   Section : Formulaire de creation                  #
    # ------------------------------------------------------------------ #

    def _construire_formulaire(self, layout_parent):
        """Construit la section formulaire de creation de code."""

        groupe_formulaire = QGroupBox("Creer un nouveau code de reduction")
        font_section = QFont()
        font_section.setPointSize(14)
        font_section.setWeight(QFont.Weight.DemiBold)
        groupe_formulaire.setFont(font_section)
        groupe_formulaire.setStyleSheet(
            "QGroupBox { padding: 15px; border-radius: 8px; }"
        )

        form = QFormLayout()
        form.setSpacing(10)
        form.setContentsMargins(15, 15, 15, 15)

        font_corps = QFont()
        font_corps.setPointSize(12)

        # Code
        self.input_code = QLineEdit()
        self.input_code.setFont(font_corps)
        self.input_code.setPlaceholderText("NOEL2026")
        form.addRow("Code :", self.input_code)

        # Pourcentage de reduction
        self.spin_pourcentage = QDoubleSpinBox()
        self.spin_pourcentage.setFont(font_corps)
        self.spin_pourcentage.setMinimum(0.00)
        self.spin_pourcentage.setMaximum(100.00)
        self.spin_pourcentage.setDecimals(2)
        self.spin_pourcentage.setSuffix(" %")
        self.spin_pourcentage.setValue(0.00)
        form.addRow("Pourcentage de reduction :", self.spin_pourcentage)

        # Description
        self.input_description = QTextEdit()
        self.input_description.setFont(font_corps)
        self.input_description.setPlaceholderText("Description (optionnel)")
        self.input_description.setFixedHeight(60)
        form.addRow("Description :", self.input_description)

        # Date de debut
        self.date_debut = QDateEdit()
        self.date_debut.setFont(font_corps)
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDate(QDate.currentDate())
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Date de debut :", self.date_debut)

        # Date de fin
        self.date_fin = QDateEdit()
        self.date_fin.setFont(font_corps)
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate().addDays(30))
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Date de fin :", self.date_fin)

        # Type d'utilisation (radio buttons)
        type_widget = QWidget()
        type_layout = QVBoxLayout(type_widget)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setSpacing(6)

        radio_style = (
            "QRadioButton {"
            "    font-size: 12pt;"
            "    padding: 8px;"
            "    color: #333;"
            "}"
            "QRadioButton::indicator {"
            "    width: 20px;"
            "    height: 20px;"
            "}"
        )

        self.radio_illimite = QRadioButton("Illimite")
        self.radio_illimite.setChecked(True)
        self.radio_illimite.setStyleSheet(radio_style)
        self.radio_illimite.toggled.connect(self._on_type_changed)
        type_layout.addWidget(self.radio_illimite)

        self.radio_limite_globale = QRadioButton(
            "Limite globale (nombre d'utilisations total)"
        )
        self.radio_limite_globale.setStyleSheet(radio_style)
        self.radio_limite_globale.toggled.connect(self._on_type_changed)
        type_layout.addWidget(self.radio_limite_globale)

        self.spinbox_limite_globale = QSpinBox()
        self.spinbox_limite_globale.setFont(font_corps)
        self.spinbox_limite_globale.setMinimum(1)
        self.spinbox_limite_globale.setMaximum(10000)
        self.spinbox_limite_globale.setValue(100)
        self.spinbox_limite_globale.setPrefix("Nombre : ")
        self.spinbox_limite_globale.hide()
        type_layout.addWidget(self.spinbox_limite_globale)

        self.radio_unique_par_client = QRadioButton("Limite par client")
        self.radio_unique_par_client.setStyleSheet(radio_style)
        self.radio_unique_par_client.toggled.connect(self._on_type_changed)
        type_layout.addWidget(self.radio_unique_par_client)

        self.spinbox_limite_client = QSpinBox()
        self.spinbox_limite_client.setFont(font_corps)
        self.spinbox_limite_client.setMinimum(1)
        self.spinbox_limite_client.setMaximum(100)
        self.spinbox_limite_client.setValue(1)
        self.spinbox_limite_client.setPrefix("Nombre : ")
        self.spinbox_limite_client.hide()
        type_layout.addWidget(self.spinbox_limite_client)

        form.addRow("Type d'utilisation :", type_widget)

        # Actif
        self.checkbox_actif = QCheckBox("Actif")
        self.checkbox_actif.setFont(font_corps)
        self.checkbox_actif.setChecked(True)
        form.addRow("", self.checkbox_actif)

        groupe_formulaire.setLayout(form)
        layout_parent.addWidget(groupe_formulaire)

        # --- Barre de boutons ---
        layout_boutons = QHBoxLayout()
        layout_boutons.setSpacing(10)

        self.btn_creer = QPushButton("Creer le code")
        self.btn_creer.setFont(font_corps)
        self.btn_creer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_creer.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "padding: 10px 24px; border-radius: 6px; border: none; }"
            "QPushButton:hover { background-color: #388E3C; }"
            "QPushButton:pressed { background-color: #1B5E20; }"
        )

        self.btn_annuler = QPushButton("Annuler")
        self.btn_annuler.setFont(font_corps)
        self.btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_annuler.setStyleSheet(
            "QPushButton { background-color: #9E9E9E; color: white; "
            "padding: 10px 24px; border-radius: 6px; border: none; }"
            "QPushButton:hover { background-color: #757575; }"
            "QPushButton:pressed { background-color: #616161; }"
        )

        layout_boutons.addWidget(self.btn_annuler)
        layout_boutons.addStretch()
        layout_boutons.addWidget(self.btn_creer)

        layout_parent.addLayout(layout_boutons)

    # ------------------------------------------------------------------ #
    #                   Section : Tableau des codes                       #
    # ------------------------------------------------------------------ #

    def _construire_tableau(self, layout_parent):
        """Construit la section tableau des codes de reduction existants."""

        groupe_table = QGroupBox("Codes de reduction existants")
        font_section = QFont()
        font_section.setPointSize(14)
        font_section.setWeight(QFont.Weight.DemiBold)
        groupe_table.setFont(font_section)
        groupe_table.setStyleSheet(
            "QGroupBox { padding: 15px; border-radius: 8px; }"
        )

        layout_table = QVBoxLayout(groupe_table)

        self.table_codes = QTableWidget()
        self.table_codes.setColumnCount(9)
        self.table_codes.setHorizontalHeaderLabels([
            "Code", "%", "Description", "Debut", "Fin",
            "Type", "Utilisations", "Actif", "Actions"
        ])

        # Configuration du tableau
        self.table_codes.horizontalHeader().setStretchLastSection(True)
        self.table_codes.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table_codes.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.table_codes.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )
        self.table_codes.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )
        self.table_codes.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents
        )
        self.table_codes.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeToContents
        )
        self.table_codes.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeToContents
        )
        self.table_codes.horizontalHeader().setSectionResizeMode(
            7, QHeaderView.ResizeToContents
        )
        self.table_codes.horizontalHeader().setSectionResizeMode(
            8, QHeaderView.Fixed
        )
        self.table_codes.setColumnWidth(8, 300)

        self.table_codes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_codes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_codes.setAlternatingRowColors(True)
        self.table_codes.verticalHeader().setVisible(False)
        self.table_codes.setStyleSheet(
            "QTableWidget { alternate-background-color: #F5F5F5; "
            "background-color: #FFFFFF; }"
            "QHeaderView::section { background-color: #E0E0E0; "
            "padding: 6px; font-weight: bold; border: 1px solid #BDBDBD; }"
        )

        layout_table.addWidget(self.table_codes)
        layout_parent.addWidget(groupe_table)

    # ------------------------------------------------------------------ #
    #                        Connexion des signaux                        #
    # ------------------------------------------------------------------ #

    def _connecter_signaux(self):
        """Connecte les signaux aux slots."""

        # Forcer le code en majuscules
        self.input_code.textChanged.connect(self._on_code_change)

        # Boutons du formulaire
        self.btn_creer.clicked.connect(self._creer_code)
        self.btn_annuler.clicked.connect(self._reinitialiser_formulaire)

        # Signaux du ViewModel
        self.viewmodel.code_cree.connect(self._on_code_cree)
        self.viewmodel.erreur.connect(self._on_erreur)
        self.viewmodel.codes_modifies.connect(self._rafraichir_table)

    # ------------------------------------------------------------------ #
    #                           Callbacks                                 #
    # ------------------------------------------------------------------ #

    def _on_code_change(self, texte: str):
        """Force le code en majuscules pendant la saisie."""
        self.input_code.blockSignals(True)
        pos = self.input_code.cursorPosition()
        self.input_code.setText(texte.upper())
        self.input_code.setCursorPosition(pos)
        self.input_code.blockSignals(False)

    def _on_type_changed(self):
        """Affiche/masque les spinbox selon le type selectionne."""
        self.spinbox_limite_globale.setVisible(self.radio_limite_globale.isChecked())
        self.spinbox_limite_client.setVisible(self.radio_unique_par_client.isChecked())

    def _creer_code(self):
        """Cree un nouveau code de reduction via le ViewModel."""
        code = self.input_code.text().strip()
        pourcentage = self.spin_pourcentage.value()
        description = self.input_description.toPlainText().strip()
        date_debut = self.date_debut.date().toString("yyyy-MM-dd")
        date_fin = self.date_fin.date().toString("yyyy-MM-dd")
        limite = 0

        if not code:
            QMessageBox.warning(
                self, "Attention", "Veuillez saisir un code promotionnel."
            )
            return

        if pourcentage <= 0:
            QMessageBox.warning(
                self, "Attention",
                "Le pourcentage de reduction doit etre superieur a 0."
            )
            return

        if self.radio_limite_globale.isChecked():
            type_utilisation = 'limite_globale'
            limite = self.spinbox_limite_globale.value()
        elif self.radio_unique_par_client.isChecked():
            type_utilisation = 'unique_par_client'
            limite = self.spinbox_limite_client.value()
        else:
            type_utilisation = 'illimite'

        code_id = self.viewmodel.creer_code(
            code=code,
            pourcentage=pourcentage,
            description=description,
            date_debut=date_debut,
            date_fin=date_fin,
            type_utilisation=type_utilisation,
            limite=limite,
        )

        if code_id > 0:
            QMessageBox.information(
                self, "Succes",
                f"Le code '{code}' a ete cree avec succes !"
            )
            self._reinitialiser_formulaire()

    def _on_code_cree(self, code_id: int):
        """Callback appele apres la creation reussie d'un code."""
        self._rafraichir_table()

    def _on_erreur(self, message: str):
        """Affiche un message d'erreur."""
        QMessageBox.warning(self, "Erreur", message)

    def _reinitialiser_formulaire(self):
        """Reinitialise tous les champs du formulaire."""
        self.input_code.clear()
        self.spin_pourcentage.setValue(0.00)
        self.input_description.clear()
        self.date_debut.setDate(QDate.currentDate())
        self.date_fin.setDate(QDate.currentDate().addDays(30))
        self.radio_illimite.setChecked(True)
        self.spinbox_limite_globale.setValue(100)
        self.spinbox_limite_globale.hide()
        self.spinbox_limite_client.setValue(1)
        self.spinbox_limite_client.hide()
        self.checkbox_actif.setChecked(True)

    # ------------------------------------------------------------------ #
    #                    Rafraichissement du tableau                      #
    # ------------------------------------------------------------------ #

    def _rafraichir_table(self):
        """Recharge les codes de reduction depuis le ViewModel dans le tableau."""
        codes = self.viewmodel.lister_codes()

        self.table_codes.setRowCount(len(codes))

        TYPES_LABELS = {
            'illimite': 'Illimite',
            'unique_par_client': 'Unique/client',
            'limite_globale': 'Limite globale',
        }

        for i, code in enumerate(codes):
            # Code
            self.table_codes.setItem(
                i, 0, QTableWidgetItem(code.get('code', ''))
            )

            # Pourcentage
            pourcentage = code.get('pourcentage', 0)
            item_pourcentage = QTableWidgetItem(f"{pourcentage:.2f} %")
            item_pourcentage.setTextAlignment(Qt.AlignCenter)
            self.table_codes.setItem(i, 1, item_pourcentage)

            # Description
            self.table_codes.setItem(
                i, 2, QTableWidgetItem(code.get('description', ''))
            )

            # Date debut
            date_debut = code.get('date_debut', '')
            self.table_codes.setItem(i, 3, QTableWidgetItem(date_debut))

            # Date fin
            date_fin = code.get('date_fin', '')
            self.table_codes.setItem(i, 4, QTableWidgetItem(date_fin))

            # Type d'utilisation
            type_util = code.get('type_utilisation', 'illimite')
            item_type = QTableWidgetItem(TYPES_LABELS.get(type_util, type_util))
            item_type.setTextAlignment(Qt.AlignCenter)
            self.table_codes.setItem(i, 5, item_type)

            # Utilisations
            utilisations = code.get('nombre_utilisations', 0)
            limite = code.get('limite_utilisations')
            if type_util == 'limite_globale' and limite:
                texte_utilisations = f"{utilisations} / {limite}"
            else:
                texte_utilisations = str(utilisations)
            item_utilisations = QTableWidgetItem(texte_utilisations)
            item_utilisations.setTextAlignment(Qt.AlignCenter)
            self.table_codes.setItem(i, 6, item_utilisations)

            # Actif
            actif = code.get('actif', False)
            item_actif = QTableWidgetItem("Oui" if actif else "Non")
            item_actif.setTextAlignment(Qt.AlignCenter)
            if actif:
                item_actif.setForeground(Qt.darkGreen)
            else:
                item_actif.setForeground(Qt.red)
            self.table_codes.setItem(i, 7, item_actif)

            # Actions
            widget_actions = self._creer_boutons_actions(code)
            self.table_codes.setCellWidget(i, 8, widget_actions)

    def _creer_boutons_actions(self, code: dict) -> QWidget:
        """Cree le widget contenant les boutons d'action pour une ligne.

        Args:
            code: Dictionnaire representant le code de reduction.

        Returns:
            Un QWidget contenant les boutons Modifier, Activer/Desactiver
            et Supprimer.
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        font_bouton = QFont()
        font_bouton.setPointSize(10)

        code_id = code.get('id')
        actif = code.get('actif', False)

        # Bouton Modifier (bleu)
        btn_modifier = QPushButton("Modifier")
        btn_modifier.setFont(font_bouton)
        btn_modifier.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_modifier.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "padding: 4px 10px; border-radius: 4px; border: none; }"
            "QPushButton:hover { background-color: #1976D2; }"
            "QPushButton:pressed { background-color: #0D47A1; }"
        )
        btn_modifier.clicked.connect(
            lambda checked, cid=code_id: self._modifier_code(cid)
        )

        # Bouton Activer / Desactiver (orange)
        texte_toggle = "Desactiver" if actif else "Activer"
        btn_toggle = QPushButton(texte_toggle)
        btn_toggle.setFont(font_bouton)
        btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_toggle.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; "
            "padding: 4px 10px; border-radius: 4px; border: none; }"
            "QPushButton:hover { background-color: #F57C00; }"
            "QPushButton:pressed { background-color: #E65100; }"
        )
        btn_toggle.clicked.connect(
            lambda checked, cid=code_id, est_actif=actif:
                self._toggle_actif(cid, est_actif)
        )

        # Bouton Supprimer (rouge)
        btn_supprimer = QPushButton("Supprimer")
        btn_supprimer.setFont(font_bouton)
        btn_supprimer.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_supprimer.setStyleSheet(
            "QPushButton { background-color: #F44336; color: white; "
            "padding: 4px 10px; border-radius: 4px; border: none; }"
            "QPushButton:hover { background-color: #D32F2F; }"
            "QPushButton:pressed { background-color: #B71C1C; }"
        )
        btn_supprimer.clicked.connect(
            lambda checked, cid=code_id: self._supprimer_code(cid)
        )

        layout.addWidget(btn_modifier)
        layout.addWidget(btn_toggle)
        layout.addWidget(btn_supprimer)

        return widget

    # ------------------------------------------------------------------ #
    #                      Actions sur les codes                          #
    # ------------------------------------------------------------------ #

    def _modifier_code(self, code_id: int):
        """Ouvre une boite de dialogue pour modifier un code existant.

        Args:
            code_id: Identifiant du code a modifier.
        """
        from PySide6.QtWidgets import QDialog, QDialogButtonBox

        # Recuperer les donnees actuelles du code
        codes = self.viewmodel.lister_codes()
        code_actuel = None
        for c in codes:
            if c.get('id') == code_id:
                code_actuel = c
                break

        if code_actuel is None:
            QMessageBox.warning(
                self, "Erreur", "Code introuvable."
            )
            return

        # Creer le dialogue de modification
        dialog = QDialog(self)
        dialog.setWindowTitle("Modifier le code de reduction")
        dialog.setMinimumWidth(400)

        layout = QFormLayout(dialog)
        layout.setSpacing(10)

        font_corps = QFont()
        font_corps.setPointSize(12)

        # Code (lecture seule)
        input_code = QLineEdit(code_actuel.get('code', ''))
        input_code.setFont(font_corps)
        input_code.setReadOnly(True)
        input_code.setStyleSheet("background-color: #EEEEEE;")
        layout.addRow("Code :", input_code)

        # Pourcentage
        spin_pourcentage = QDoubleSpinBox()
        spin_pourcentage.setFont(font_corps)
        spin_pourcentage.setMinimum(0.00)
        spin_pourcentage.setMaximum(100.00)
        spin_pourcentage.setDecimals(2)
        spin_pourcentage.setSuffix(" %")
        spin_pourcentage.setValue(code_actuel.get('pourcentage', 0))
        layout.addRow("Pourcentage :", spin_pourcentage)

        # Description
        input_description = QTextEdit()
        input_description.setFont(font_corps)
        input_description.setPlainText(code_actuel.get('description', ''))
        input_description.setFixedHeight(60)
        layout.addRow("Description :", input_description)

        # Date de debut
        date_debut = QDateEdit()
        date_debut.setFont(font_corps)
        date_debut.setCalendarPopup(True)
        date_debut.setDisplayFormat("dd/MM/yyyy")
        date_str_debut = code_actuel.get('date_debut', '')
        if date_str_debut:
            date_qt = QDate.fromString(date_str_debut, "yyyy-MM-dd")
            if date_qt.isValid():
                date_debut.setDate(date_qt)
            else:
                date_debut.setDate(QDate.currentDate())
        else:
            date_debut.setDate(QDate.currentDate())
        layout.addRow("Date de debut :", date_debut)

        # Date de fin
        date_fin = QDateEdit()
        date_fin.setFont(font_corps)
        date_fin.setCalendarPopup(True)
        date_fin.setDisplayFormat("dd/MM/yyyy")
        date_str_fin = code_actuel.get('date_fin', '')
        if date_str_fin:
            date_qt = QDate.fromString(date_str_fin, "yyyy-MM-dd")
            if date_qt.isValid():
                date_fin.setDate(date_qt)
            else:
                date_fin.setDate(QDate.currentDate().addDays(30))
        else:
            date_fin.setDate(QDate.currentDate().addDays(30))
        layout.addRow("Date de fin :", date_fin)

        # Type d'utilisation
        combo_type = QComboBox()
        combo_type.setFont(font_corps)
        combo_type.addItem("Illimite", "illimite")
        combo_type.addItem("Unique par client", "unique_par_client")
        combo_type.addItem("Limite globale", "limite_globale")
        type_actuel = code_actuel.get('type_utilisation', 'illimite')
        idx_type = combo_type.findData(type_actuel)
        if idx_type >= 0:
            combo_type.setCurrentIndex(idx_type)
        layout.addRow("Type d'utilisation :", combo_type)

        # Limite
        label_lim = QLabel("Limite d'utilisations :")
        spin_limite = QSpinBox()
        spin_limite.setFont(font_corps)
        spin_limite.setMinimum(1)
        spin_limite.setMaximum(999999)
        spin_limite.setValue(code_actuel.get('limite_utilisations') or 100)
        layout.addRow(label_lim, spin_limite)
        est_lim = type_actuel == 'limite_globale'
        spin_limite.setVisible(est_lim)
        label_lim.setVisible(est_lim)

        def _on_type_change(idx):
            show = combo_type.currentData() == 'limite_globale'
            spin_limite.setVisible(show)
            label_lim.setVisible(show)

        combo_type.currentIndexChanged.connect(_on_type_change)

        # Boutons OK / Annuler
        boutons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        boutons.accepted.connect(dialog.accept)
        boutons.rejected.connect(dialog.reject)
        layout.addRow(boutons)

        if dialog.exec() == QDialog.Accepted:
            type_util = combo_type.currentData()
            donnees = {
                'pourcentage': spin_pourcentage.value(),
                'description': input_description.toPlainText().strip(),
                'date_debut': date_debut.date().toString("yyyy-MM-dd"),
                'date_fin': date_fin.date().toString("yyyy-MM-dd"),
                'type_utilisation': type_util,
                'limite_utilisations': spin_limite.value() if type_util == 'limite_globale' else None,
            }
            resultat = self.viewmodel.modifier_code(code_id, donnees)
            if resultat:
                QMessageBox.information(
                    self, "Succes", "Le code a ete modifie avec succes."
                )
            else:
                QMessageBox.warning(
                    self, "Erreur", "La modification a echoue."
                )

    def _toggle_actif(self, code_id: int, est_actif: bool):
        """Active ou desactive un code de reduction.

        Args:
            code_id:   Identifiant du code.
            est_actif: Etat actif actuel du code.
        """
        nouvel_etat = not est_actif
        action = "activer" if nouvel_etat else "desactiver"

        reponse = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous {action} ce code de reduction ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reponse == QMessageBox.Yes:
            self.viewmodel.activer_desactiver(code_id, nouvel_etat)

    def _supprimer_code(self, code_id: int):
        """Supprime un code de reduction apres confirmation.

        Args:
            code_id: Identifiant du code a supprimer.
        """
        reponse = QMessageBox.question(
            self,
            "Confirmation de suppression",
            "Etes-vous sur de vouloir supprimer ce code de reduction ?\n"
            "Cette action est irreversible.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reponse == QMessageBox.Yes:
            resultat = self.viewmodel.supprimer_code(code_id)
            if resultat:
                QMessageBox.information(
                    self, "Succes", "Le code a ete supprime."
                )
            else:
                QMessageBox.warning(
                    self, "Erreur", "La suppression a echoue."
                )
