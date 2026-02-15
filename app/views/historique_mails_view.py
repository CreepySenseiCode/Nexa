"""
Vue Historique des mails - Affiche l'historique des emails envoy\u00e9s.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QHeaderView, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class HistoriqueMailsView(QWidget):
    """Interface de l'historique des emails envoy\u00e9s."""

    def __init__(self):
        super().__init__()
        self._construire_ui()
        self._charger_historique()

    def _construire_ui(self):
        """Construit l'interface utilisateur."""
        layout_principal = QVBoxLayout()
        layout_principal.setSpacing(20)
        layout_principal.setContentsMargins(30, 30, 30, 30)

        # Header
        header_layout = QHBoxLayout()

        titre = QLabel("Historique des emails")
        titre.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        titre.setStyleSheet("color: #1976D2; padding: 10px;")
        header_layout.addWidget(titre)

        header_layout.addStretch()

        # Bouton rafraichir
        btn_refresh = QPushButton("Actualiser")
        btn_refresh.setStyleSheet(self._get_button_style("#2196F3"))
        btn_refresh.clicked.connect(self._charger_historique)
        header_layout.addWidget(btn_refresh)

        layout_principal.addLayout(header_layout)

        # Barre de filtres
        filtres_layout = QHBoxLayout()

        self.input_recherche = QLineEdit()
        self.input_recherche.setPlaceholderText("Rechercher par objet ou destinataire...")
        self.input_recherche.setStyleSheet(
            "QLineEdit {"
            "    min-height: 40px;"
            "    font-size: 12pt;"
            "    padding: 8px 12px;"
            "    border: 2px solid #E0E0E0;"
            "    border-radius: 8px;"
            "    background-color: white;"
            "}"
            "QLineEdit:focus {"
            "    border: 2px solid #2196F3;"
            "}"
        )
        self.input_recherche.textChanged.connect(self._filtrer_historique)
        filtres_layout.addWidget(self.input_recherche)

        self.combo_statut = QComboBox()
        self.combo_statut.addItems(["Tous", "Envoy\u00e9", "\u00c9chou\u00e9", "En attente"])
        self.combo_statut.setStyleSheet(
            "QComboBox {"
            "    min-height: 40px;"
            "    font-size: 12pt;"
            "    padding: 8px 12px;"
            "    border: 2px solid #E0E0E0;"
            "    border-radius: 8px;"
            "    background-color: white;"
            "    min-width: 150px;"
            "}"
        )
        self.combo_statut.currentIndexChanged.connect(self._charger_historique)
        filtres_layout.addWidget(self.combo_statut)

        layout_principal.addLayout(filtres_layout)

        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Date", "Objet", "Destinataires", "Type", "Statut", "Actions",
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
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        layout_principal.addWidget(self.table)

        # Stats en bas
        self.label_stats = QLabel()
        self.label_stats.setStyleSheet("font-size: 11pt; color: #666; padding: 10px;")
        layout_principal.addWidget(self.label_stats)

        self.setLayout(layout_principal)
        self.setStyleSheet("background-color: #F5F5F5;")

    def _charger_historique(self):
        """Charge l'historique des emails depuis la base de donn\u00e9es."""
        try:
            from models.database import get_db
            db = get_db()

            query = """
                SELECT id, objet, type_envoi, nombre_destinataires,
                       destinataires, date_envoi, statut
                FROM historique_emails
                ORDER BY date_envoi DESC
            """

            emails = db.fetchall(query)
        except Exception:
            emails = []

        self.table.setRowCount(len(emails))

        for row, email in enumerate(emails):
            # Date
            date_str = email.get("date_envoi", "")
            self.table.setItem(row, 0, QTableWidgetItem(str(date_str)[:16] if date_str else ""))

            # Objet
            self.table.setItem(row, 1, QTableWidgetItem(email.get("objet", "")))

            # Destinataires
            nb_dest = email.get("nombre_destinataires", 0)
            self.table.setItem(row, 2, QTableWidgetItem(str(nb_dest)))

            # Type
            type_envoi = email.get("type_envoi", "").replace("_", " ").title()
            self.table.setItem(row, 3, QTableWidgetItem(type_envoi))

            # Statut
            statut = email.get("statut", "")
            statut_item = QTableWidgetItem(statut)
            if statut == "envoy\u00e9":
                statut_item.setForeground(Qt.GlobalColor.darkGreen)
            elif "erreur" in statut.lower() or "\u00e9chou\u00e9" in statut.lower():
                statut_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 4, statut_item)

            # Bouton Details
            btn_details = QPushButton("D\u00e9tails")
            btn_details.setStyleSheet(self._get_button_style("#2196F3"))
            btn_details.clicked.connect(
                lambda checked, r=row: self._voir_details(r)
            )
            self.table.setCellWidget(row, 5, btn_details)

        # Stats
        nb_total = len(emails)
        nb_envoyes = sum(1 for e in emails if e.get("statut") == "envoy\u00e9")
        self.label_stats.setText(
            f"Total : {nb_total} email{'s' if nb_total > 1 else ''} | "
            f"Envoy\u00e9s : {nb_envoyes}"
        )

    def _filtrer_historique(self):
        """Filtre l'historique selon la recherche."""
        texte = self.input_recherche.text().lower()

        for row in range(self.table.rowCount()):
            visible = False
            for col in range(4):  # Date, Objet, Destinataires, Type
                item = self.table.item(row, col)
                if item and texte in item.text().lower():
                    visible = True
                    break
            self.table.setRowHidden(row, not visible)

    def _voir_details(self, row: int):
        """Affiche les d\u00e9tails d'un email envoy\u00e9."""
        objet = self.table.item(row, 1)
        statut = self.table.item(row, 4)

        objet_text = objet.text() if objet else ""
        statut_text = statut.text() if statut else ""

        QMessageBox.information(
            self,
            "D\u00e9tails de l'email",
            f"Objet : {objet_text}\n"
            f"Statut : {statut_text}\n\n"
            "(D\u00e9tails complets \u00e0 impl\u00e9menter)",
        )

    def _get_button_style(self, color: str) -> str:
        """Style des boutons."""
        return (
            f"QPushButton {{"
            f"    background-color: {color};"
            f"    color: white;"
            f"    border: none;"
            f"    border-radius: 6px;"
            f"    padding: 8px 16px;"
            f"    font-size: 11pt;"
            f"    font-weight: 600;"
            f"    min-height: 35px;"
            f"}}"
            f"QPushButton:hover {{"
            f"    opacity: 0.9;"
            f"}}"
        )
