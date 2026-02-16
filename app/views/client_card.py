"""Widget de carte client reutilisable pour les resultats de recherche.

Ce module fournit ClientCard (affichage d'un client) et
SearchResultsWidget (liste scrollable de cards).
"""

import os
import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QPainter, QPainterPath


class ClientCard(QFrame):
    """Widget card cliquable pour afficher un client."""

    clicked = Signal(int)  # Emet le client_id au clic

    def __init__(self, client_data: dict, search_terms: list = None, parent=None):
        super().__init__(parent)
        self.client_id = client_data.get('id', 0)
        self._search_terms = search_terms or []
        self._construire_ui(client_data)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _construire_ui(self, data: dict):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "ClientCard { background-color: #FFFFFF; border: 1px solid #E0E0E0; "
            "border-radius: 10px; padding: 12px; margin: 3px 0; }"
            "ClientCard:hover { background-color: #F5F5F5; border: 1px solid #2196F3; }"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Avatar (photo ou icone par defaut)
        label_avatar = QLabel()
        label_avatar.setFixedSize(50, 50)
        label_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        photo_path = data.get('photo_path', '')
        if photo_path and os.path.exists(photo_path):
            pixmap = QPixmap(photo_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    50, 50,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                if pixmap.width() != 50 or pixmap.height() != 50:
                    x = (pixmap.width() - 50) // 2
                    y = (pixmap.height() - 50) // 2
                    pixmap = pixmap.copy(x, y, 50, 50)
                masque = QPixmap(50, 50)
                masque.fill(Qt.GlobalColor.transparent)
                painter = QPainter(masque)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, 50, 50)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                label_avatar.setPixmap(masque)
                label_avatar.setStyleSheet("border: none;")
            else:
                label_avatar.setText("\U0001F464")
                label_avatar.setStyleSheet("font-size: 32pt; border: none;")
        else:
            label_avatar.setText("\U0001F464")
            label_avatar.setStyleSheet("font-size: 32pt; border: none;")
        layout.addWidget(label_avatar)

        # Informations
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        nom = (data.get('nom') or '').upper()
        prenom = data.get('prenom') or ''
        nom_complet = f"{nom} {prenom}".strip()

        label_nom = QLabel(self._highlight(nom_complet))
        label_nom.setTextFormat(Qt.TextFormat.RichText)
        label_nom.setStyleSheet("font-size: 13pt; font-weight: bold; color: #333; border: none;")
        info_layout.addWidget(label_nom)

        email = data.get('email') or ''
        if email:
            label_email = QLabel(self._highlight(email))
            label_email.setTextFormat(Qt.TextFormat.RichText)
            label_email.setStyleSheet("font-size: 11pt; color: #666; border: none;")
            info_layout.addWidget(label_email)

        telephone = data.get('telephone') or ''
        if telephone:
            label_tel = QLabel(self._highlight(telephone))
            label_tel.setTextFormat(Qt.TextFormat.RichText)
            label_tel.setStyleSheet("font-size: 11pt; color: #666; border: none;")
            info_layout.addWidget(label_tel)

        layout.addLayout(info_layout)
        layout.addStretch()

    def _highlight(self, text: str) -> str:
        """Met en gras les termes de recherche dans le texte."""
        if not self._search_terms or not text:
            return text
        result = text
        for term in self._search_terms:
            if not term:
                continue
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            result = pattern.sub(
                lambda m: f"<b style='color:#2196F3'>{m.group()}</b>", result
            )
        return result

    def mousePressEvent(self, event):
        self.clicked.emit(self.client_id)
        super().mousePressEvent(event)


class SearchResultsWidget(QWidget):
    """Widget scrollable pour afficher les resultats de recherche sous forme de cards."""

    client_selected = Signal(int)  # Emet le client_id quand une card est cliquee

    def __init__(self, parent=None):
        super().__init__(parent)
        self._construire_ui()

    def _construire_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Label compteur de resultats
        self._label_compteur = QLabel("")
        self._label_compteur.setStyleSheet(
            "font-size: 11pt; font-weight: bold; color: #777; padding: 5px 0;"
        )
        self._label_compteur.setVisible(False)
        layout.addWidget(self._label_compteur)

        # Scroll area pour les cards
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setMaximumHeight(300)

        self._conteneur = QWidget()
        self._layout_cards = QVBoxLayout(self._conteneur)
        self._layout_cards.setContentsMargins(0, 0, 0, 0)
        self._layout_cards.setSpacing(8)
        self._layout_cards.addStretch()

        self._scroll.setWidget(self._conteneur)
        layout.addWidget(self._scroll)

    def afficher_resultats(self, clients: list[dict], search_terms: list[str] = None):
        """Affiche les clients sous forme de cards.

        Args:
            clients: Liste de dictionnaires client.
            search_terms: Termes de recherche pour la mise en surbrillance.
        """
        self.vider()

        # Ne pas afficher le label compteur interne (géré dans client_view)
        self._label_compteur.setVisible(False)

        if not clients:
            label_vide = QLabel("Aucun client trouvé")
            label_vide.setStyleSheet("color: #7f8c8d; padding: 20px;")
            self._layout_cards.insertWidget(0, label_vide)
            return

        for client in clients:
            card = ClientCard(client, search_terms)
            card.clicked.connect(self.client_selected.emit)
            # Inserer avant le stretch
            self._layout_cards.insertWidget(self._layout_cards.count() - 1, card)

        self.setVisible(True)

    def vider(self):
        """Vide tous les resultats."""
        while self._layout_cards.count() > 1:
            item = self._layout_cards.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._label_compteur.setVisible(False)
