"""Widget de carte produit réutilisable pour la sélection de produits.

Ce module fournit ProductCard (affichage d'un produit) et
SearchProductsWidget (liste scrollable de cards).
"""

import os
import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QPainter, QPainterPath


class ProductCard(QFrame):
    """Widget card cliquable pour afficher un produit."""

    clicked = Signal(int)  # Émet le produit_id au clic

    def __init__(self, produit_data: dict, search_terms: list = None, parent=None):
        super().__init__(parent)
        self.produit_id = produit_data.get('id', 0)
        self._search_terms = search_terms or []
        self._construire_ui(produit_data)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _construire_ui(self, data: dict):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "ProductCard { background-color: #FFFFFF; border: 1px solid #E0E0E0; "
            "border-radius: 10px; padding: 12px; margin: 3px 0; }"
            "ProductCard:hover { background-color: #F5F5F5; border: 1px solid #4CAF50; }"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Photo produit (ou icône par défaut)
        label_photo = QLabel()
        label_photo.setFixedSize(60, 60)
        label_photo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        photo_path = data.get('photo', '')
        if photo_path and os.path.exists(photo_path):
            pixmap = QPixmap(photo_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    60, 60,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                if pixmap.width() != 60 or pixmap.height() != 60:
                    x = (pixmap.width() - 60) // 2
                    y = (pixmap.height() - 60) // 2
                    pixmap = pixmap.copy(x, y, 60, 60)
                label_photo.setPixmap(pixmap)
                label_photo.setStyleSheet("border: 1px solid #E0E0E0; border-radius: 8px;")
            else:
                label_photo.setText("📦")
                label_photo.setStyleSheet("font-size: 36pt; border: none;")
        else:
            label_photo.setText("📦")
            label_photo.setStyleSheet("font-size: 36pt; border: none;")
        layout.addWidget(label_photo)

        # Informations produit
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        nom = data.get('nom') or ''
        label_nom = QLabel(self._highlight(nom))
        label_nom.setTextFormat(Qt.TextFormat.RichText)
        label_nom.setStyleSheet("font-size: 13pt; font-weight: bold; color: #333; border: none;")
        info_layout.addWidget(label_nom)

        prix = data.get('prix', 0.0)
        label_prix = QLabel(f"{prix:.2f} EUR")
        label_prix.setStyleSheet("font-size: 12pt; color: #4CAF50; font-weight: 600; border: none;")
        info_layout.addWidget(label_prix)

        stock = data.get('stock', 0)
        color_stock = "#4CAF50" if stock > 10 else ("#FF9800" if stock > 0 else "#F44336")
        label_stock = QLabel(f"Stock : {stock}")
        label_stock.setStyleSheet(f"font-size: 10pt; color: {color_stock}; border: none;")
        info_layout.addWidget(label_stock)

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
                lambda m: f"<b style='color:#4CAF50'>{m.group()}</b>", result
            )
        return result

    def mousePressEvent(self, event):
        self.clicked.emit(self.produit_id)
        super().mousePressEvent(event)


class SearchProductsWidget(QWidget):
    """Widget scrollable pour afficher les produits sous forme de cards."""

    produit_selected = Signal(int)  # Émet le produit_id quand une card est cliquée

    def __init__(self, parent=None):
        super().__init__(parent)
        self._construire_ui()

    def _construire_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Label compteur de résultats
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
        self._scroll.setMaximumHeight(400)

        self._conteneur = QWidget()
        self._layout_cards = QVBoxLayout(self._conteneur)
        self._layout_cards.setContentsMargins(0, 0, 0, 0)
        self._layout_cards.setSpacing(8)
        self._layout_cards.addStretch()

        self._scroll.setWidget(self._conteneur)
        layout.addWidget(self._scroll)

    def afficher_produits(self, produits: list[dict], search_terms: list[str] = None):
        """Affiche les produits sous forme de cards.

        Args:
            produits: Liste de dictionnaires produit.
            search_terms: Termes de recherche pour la mise en surbrillance.
        """
        self.vider()

        self._label_compteur.setText(f"{len(produits)} produit(s) trouvé(s)")
        self._label_compteur.setVisible(len(produits) > 0)

        if not produits:
            label_vide = QLabel("Aucun produit trouvé")
            label_vide.setStyleSheet("color: #7f8c8d; padding: 20px;")
            self._layout_cards.insertWidget(0, label_vide)
            return

        for produit in produits:
            card = ProductCard(produit, search_terms)
            card.clicked.connect(self.produit_selected.emit)
            # Insérer avant le stretch
            self._layout_cards.insertWidget(self._layout_cards.count() - 1, card)

        self.setVisible(True)

    def vider(self):
        """Vide tous les résultats."""
        while self._layout_cards.count() > 1:
            item = self._layout_cards.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._label_compteur.setVisible(False)
