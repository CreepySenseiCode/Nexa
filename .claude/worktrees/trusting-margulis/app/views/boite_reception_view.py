"""
Vue Bo\u00eete de r\u00e9ception - Affiche les emails re\u00e7us.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QHeaderView, QMessageBox, QRadioButton, QButtonGroup,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from utils.styles import style_bouton, style_input, Couleurs
from viewmodels.boite_reception_vm import BoiteReceptionViewModel


class BoiteReceptionView(QWidget):
    """Interface de bo\u00eete de r\u00e9ception."""

    def __init__(self):
        super().__init__()
        self.viewmodel = BoiteReceptionViewModel()
        self._construire_ui()
        self._charger_emails()

    def _construire_ui(self):
        """Construit l'interface utilisateur."""
        layout_principal = QVBoxLayout()
        layout_principal.setSpacing(20)
        layout_principal.setContentsMargins(30, 30, 30, 30)

        # Header
        header_layout = QHBoxLayout()


        # Filtre par adresse : radio buttons
        radio_style = (
            "QRadioButton {"
            f"    font-size: 12pt; color: {Couleurs.TEXTE}; spacing: 6px;"
            "}"
            "QRadioButton::indicator {"
            "    width: 18px; height: 18px;"
            "}"
        )
        self.radio_toutes = QRadioButton("Toutes les boites")
        self.radio_toutes.setStyleSheet(radio_style)
        self.radio_toutes.setChecked(True)
        self.radio_toutes.toggled.connect(self._on_radio_changed)

        self.radio_une = QRadioButton("Une seule")
        self.radio_une.setStyleSheet(radio_style)
        self.radio_une.toggled.connect(self._on_radio_changed)

        self.groupe_radio = QButtonGroup(self)
        self.groupe_radio.addButton(self.radio_toutes)
        self.groupe_radio.addButton(self.radio_une)

        header_layout.addWidget(self.radio_toutes)
        header_layout.addWidget(self.radio_une)

        self.combo_adresse = QComboBox()
        self.combo_adresse.addItems([
            "contact@nexa.fr",
            "support@nexa.fr",
            "commercial@nexa.fr",
            "direction@nexa.fr",
        ])
        self.combo_adresse.setStyleSheet(style_input())
        self.combo_adresse.setMinimumWidth(220)
        self.combo_adresse.setEnabled(False)
        self.combo_adresse.currentIndexChanged.connect(self._on_adresse_changed)
        header_layout.addWidget(self.combo_adresse)

        header_layout.addStretch()

        # Bouton rafraichir
        btn_refresh = QPushButton("Actualiser")
        btn_refresh.setStyleSheet(style_bouton(Couleurs.PRIMAIRE, taille="petit"))
        btn_refresh.clicked.connect(self._charger_emails)
        header_layout.addWidget(btn_refresh)

        layout_principal.addLayout(header_layout)

        # Barre de recherche
        self.input_recherche = QLineEdit()
        self.input_recherche.setPlaceholderText("Rechercher un email...")
        self.input_recherche.setStyleSheet(
            "QLineEdit {"
            "    min-height: 45px;"
            "    font-size: 13pt;"
            "    padding: 10px 15px;"
            "    border: 2px solid #E0E0E0;"
            "    border-radius: 8px;"
            "    background-color: white;"
            "}"
            "QLineEdit:focus {"
            "    border: 2px solid #2196F3;"
            "}"
        )
        self.input_recherche.textChanged.connect(self._filtrer_emails)
        layout_principal.addWidget(self.input_recherche)

        # Tableau des emails
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Date", "Exp\u00e9diteur", "Objet", "PJ", "Actions",
        ])

        self.table.setStyleSheet(
            "QTableWidget {"
            "    border: 2px solid #E0E0E0;"
            "    border-radius: 12px;"
            "    background-color: white;"
            "    gridline-color: #F0F0F0;"
            "}"
            "QTableWidget::item {"
            "    padding: 10px;"
            "}"
            "QTableWidget::item:selected {"
            "    background-color: #E3F2FD;"
            "    color: #1976D2;"
            "}"
            "QHeaderView::section {"
            "    background-color: #2196F3;"
            "    color: white;"
            "    padding: 12px;"
            "    border: none;"
            "    font-weight: bold;"
            "    font-size: 11pt;"
            "}"
        )

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        # Ajuster les colonnes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        layout_principal.addWidget(self.table)

        # Stats en bas
        self.label_stats = QLabel()
        self.label_stats.setStyleSheet("font-size: 11pt; color: #666; padding: 10px;")
        layout_principal.addWidget(self.label_stats)

        self.setLayout(layout_principal)
        self.setStyleSheet("background-color: #F5F5F5;")

    def _on_radio_changed(self):
        """Active/desactive et masque le combo selon le radio selectionne."""
        if self.radio_toutes.isChecked():
            self.combo_adresse.setEnabled(False)
            self.combo_adresse.hide()
        else:
            self.combo_adresse.setEnabled(True)
            self.combo_adresse.show()
        self._charger_emails()

    def _on_adresse_changed(self):
        """Recharge les emails quand l'adresse selectionnee change."""
        if self.radio_une.isChecked():
            self._charger_emails()

    def _charger_emails(self):
        """Charge les emails depuis la base de donnees."""
        if self.radio_toutes.isChecked():
            adresse = "Toutes les bo\u00eetes"
        else:
            adresse = self.combo_adresse.currentText()
        emails = self.viewmodel.charger_emails(adresse)

        self.table.setRowCount(len(emails))

        for row, email in enumerate(emails):
            # Date
            date_str = email.get("date_reception", "")
            date_item = QTableWidgetItem(str(date_str)[:16] if date_str else "")
            if not email.get("lu"):
                font = date_item.font()
                font.setBold(True)
                date_item.setFont(font)
            self.table.setItem(row, 0, date_item)

            # Expediteur
            exp = email.get("expediteur_nom") or email.get("expediteur_email", "")
            exp_item = QTableWidgetItem(exp)
            if not email.get("lu"):
                font = exp_item.font()
                font.setBold(True)
                exp_item.setFont(font)
            self.table.setItem(row, 1, exp_item)

            # Objet
            objet_item = QTableWidgetItem(email.get("objet", ""))
            if not email.get("lu"):
                font = objet_item.font()
                font.setBold(True)
                objet_item.setFont(font)
            self.table.setItem(row, 2, objet_item)

            # Pieces jointes
            pj = email.get("pieces_jointes", "")
            pj_count = len(pj.split(",")) if pj else 0
            pj_item = QTableWidgetItem(str(pj_count) if pj_count else "0")
            pj_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, pj_item)

            # Bouton Ouvrir
            btn_ouvrir = QPushButton("Ouvrir")
            btn_ouvrir.setStyleSheet(style_bouton(Couleurs.PRIMAIRE, taille="petit"))
            btn_ouvrir.clicked.connect(
                lambda checked, r=row: self._ouvrir_email(r)
            )
            self.table.setCellWidget(row, 4, btn_ouvrir)

        # Mettre a jour les stats
        nb_total = len(emails)
        nb_non_lus = sum(1 for e in emails if not e.get("lu"))
        adresse_txt = adresse
        boite_info = f" ({adresse_txt})" if not self.radio_toutes.isChecked() else ""
        self.label_stats.setText(
            f"Total : {nb_total} email{'s' if nb_total > 1 else ''}{boite_info} | "
            f"Non lus : {nb_non_lus}"
        )

    def _filtrer_emails(self):
        """Filtre les emails selon la recherche."""
        texte = self.input_recherche.text().lower()

        for row in range(self.table.rowCount()):
            visible = False
            for col in range(3):  # Date, Expediteur, Objet
                item = self.table.item(row, col)
                if item and texte in item.text().lower():
                    visible = True
                    break
            self.table.setRowHidden(row, not visible)

    def _ouvrir_email(self, row: int):
        """Ouvre un email."""
        objet_item = self.table.item(row, 2)
        exp_item = self.table.item(row, 1)

        objet = objet_item.text() if objet_item else ""
        expediteur = exp_item.text() if exp_item else ""

        QMessageBox.information(
            self,
            f"Email de {expediteur}",
            f"Objet : {objet}\n\n"
            "Contenu de l'email ici...\n\n"
            "(Fonctionnalit\u00e9 \u00e0 impl\u00e9menter)",
        )

