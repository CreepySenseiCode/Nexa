"""
Vue Bo\u00eete de r\u00e9ception - Affiche les emails re\u00e7us.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QHeaderView, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from utils.styles import style_bouton, style_scroll_area, Couleurs


class BoiteReceptionView(QWidget):
    """Interface de bo\u00eete de r\u00e9ception."""

    def __init__(self):
        super().__init__()
        self._construire_ui()
        self._charger_emails()

    def _construire_ui(self):
        """Construit l'interface utilisateur."""
        layout_principal = QVBoxLayout()
        layout_principal.setSpacing(20)
        layout_principal.setContentsMargins(30, 30, 30, 30)

        # Header
        header_layout = QHBoxLayout()

        titre = QLabel("Bo\u00eete de r\u00e9ception")
        titre.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        titre.setStyleSheet("color: #1976D2; padding: 10px;")
        header_layout.addWidget(titre)

        # Sélecteur d'adresse email
        self.combo_adresse = QComboBox()
        self.combo_adresse.addItems([
            "Toutes les boîtes",
            "contact@nexa.fr",
            "support@nexa.fr",
            "commercial@nexa.fr",
            "direction@nexa.fr",
        ])
        self.combo_adresse.setStyleSheet(
            "QComboBox {"
            "    min-height: 40px;"
            "    font-size: 11pt;"
            "    padding: 5px 15px;"
            "    border: 2px solid #E0E0E0;"
            "    border-radius: 8px;"
            "    background-color: white;"
            "    min-width: 220px;"
            "}"
            "QComboBox:hover {"
            "    border: 2px solid #2196F3;"
            "}"
            "QComboBox::drop-down {"
            "    border: none;"
            "    padding-right: 10px;"
            "}"
        )
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

    def _on_adresse_changed(self):
        """Recharge les emails quand l'adresse s\u00e9lectionn\u00e9e change."""
        self._charger_emails()

    def _charger_emails(self):
        """Charge les emails depuis la base de donn\u00e9es."""
        try:
            from models.database import get_db
            db = get_db()

            adresse = self.combo_adresse.currentText()

            if adresse == "Toutes les bo\u00eetes":
                emails = db.fetchall(
                    """
                    SELECT id, expediteur_email, expediteur_nom, objet,
                           date_reception, lu, pieces_jointes, compte_email_recepteur
                    FROM emails_recus
                    ORDER BY date_reception DESC
                    """
                )
            else:
                emails = db.fetchall(
                    """
                    SELECT id, expediteur_email, expediteur_nom, objet,
                           date_reception, lu, pieces_jointes, compte_email_recepteur
                    FROM emails_recus
                    WHERE compte_email_recepteur = ?
                    ORDER BY date_reception DESC
                    """,
                    (adresse,),
                )
        except Exception:
            emails = []

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
        adresse_txt = self.combo_adresse.currentText()
        boite_info = f" ({adresse_txt})" if adresse_txt != "Toutes les bo\u00eetes" else ""
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

