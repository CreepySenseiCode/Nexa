"""Widget de carte produit réutilisable."""

import os
import re

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from utils.styles import style_bouton, Couleurs


class ProductCard(QFrame):
    """Card compacte pour un produit."""

    double_clicked = Signal(int)
    action_archiver = Signal(int)
    action_restaurer = Signal(int)
    action_supprimer = Signal(int)
    clicked = Signal(int)  # Compatibilité SearchProductsWidget

    def __init__(
        self,
        produit_data: dict,
        search_terms: list = None,
        show_actions: bool = False,
        is_archive: bool = False,
        attributs: list = None,
        parent=None,
    ):
        super().__init__(parent)
        self.produit_id = produit_data.get("id", 0)
        self._search_terms = search_terms or []
        self._is_archive = is_archive
        self._attributs = [a for a in (attributs or []) if a.get("valeur")]
        self._construire_ui(produit_data, show_actions)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ------------------------------------------------------------------

    def _construire_ui(self, data: dict, show_actions: bool) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "ProductCard {"
            "    background-color: #FFFFFF;"
            "    border: 1px solid #E0E0E0;"
            "    border-radius: 10px;"
            "}"
            "ProductCard:hover {"
            "    background-color: #F5F5F5;"
            "    border: 1px solid #2196F3;"
            "}"
        )
        # Hauteur fixe calée sur 2 boutons : 2 × 32px + 4px spacing + 2 × 6px marges = 80px
        self.setFixedHeight(80)

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 6)
        root.setSpacing(10)

        root.addWidget(self._construire_photo(data))
        root.addLayout(self._construire_infos(data), stretch=1)
        if show_actions:
            root.addLayout(self._construire_boutons())

    def _construire_photo(self, data: dict) -> QLabel:
        SIZE = 62
        lbl = QLabel()
        lbl.setFixedSize(SIZE, SIZE)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        path = data.get("photo", "")
        if path and os.path.exists(path):
            px = QPixmap(path)
            if not px.isNull():
                px = px.scaled(
                    SIZE,
                    SIZE,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                x = (px.width() - SIZE) // 2
                y = (px.height() - SIZE) // 2
                lbl.setPixmap(px.copy(x, y, SIZE, SIZE))
                lbl.setStyleSheet("border: 1px solid #E0E0E0; border-radius: 6px;")
                return lbl
        lbl.setText("📦")
        lbl.setStyleSheet("font-size: 26pt; border: none;")
        return lbl

    def _construire_infos(self, data: dict) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # --- Ligne principale : Catégorie | Nom | Prix | stretch | Stock ---
        ligne = QHBoxLayout()
        ligne.setSpacing(8)

        # 1. Badge catégorie EN PREMIER
        categorie = data.get("categorie_nom", "")
        if categorie:
            badge_cat = QLabel(categorie)
            badge_cat.setStyleSheet(
                "font-size: 10pt; color: #1976D2; background-color: #E3F2FD;"
                "border-radius: 8px; padding: 2px 9px; border: none;"
            )
            ligne.addWidget(badge_cat)

        # 2. Nom
        nom = data.get("nom") or ""
        lbl_nom = QLabel(self._highlight(nom))
        lbl_nom.setTextFormat(Qt.TextFormat.RichText)
        lbl_nom.setStyleSheet(
            "font-size: 13pt; font-weight: bold; color: #222; border: none;"
        )
        ligne.addWidget(lbl_nom)

        # 3. Prix
        prix = data.get("prix", 0.0) or 0.0
        lbl_prix = QLabel(f"{prix:.2f} €")
        lbl_prix.setStyleSheet(
            "font-size: 12pt; color: #4CAF50; font-weight: 600; border: none;"
        )
        ligne.addWidget(lbl_prix)

        ligne.addStretch()
        ligne.addSpacing(-20)

        # 4. Badge stock (à droite)
        stock = data.get("stock", 0) or 0
        if stock > 10:
            bg, fg, texte = "#E8F5E9", "#2E7D32", f"Stock : {stock}"
        elif stock > 0:
            bg, fg, texte = "#FFF3E0", "#E65100", f"Faible : {stock}"
        else:
            bg, fg, texte = "#FFEBEE", "#C62828", "Rupture"

        badge_stock = QLabel(texte)
        badge_stock.setStyleSheet(
            f"font-size: 10pt; color: {fg}; background-color: {bg};"
            "border-radius: 8px; padding: 2px 9px; border: none;"
        )
        ligne.addWidget(badge_stock)

        layout.addLayout(ligne)

        # --- Ligne attributs (si présents) ---
        if self._attributs:
            parties = [
                f"<span style='color:#999'>{a['nom_attribut']} :</span> "
                f"<span style='color:#555; font-weight:600'>{a.get('valeur', '')}</span>"
                for a in self._attributs
            ]
            lbl_attrs = QLabel("  ·  ".join(parties))
            lbl_attrs.setTextFormat(Qt.TextFormat.RichText)
            lbl_attrs.setStyleSheet("font-size: 10pt; border: none;")
            lbl_attrs.setWordWrap(True)
            layout.addWidget(lbl_attrs)

        return layout

    def _construire_boutons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        # Pas de addStretch() → hauteur = exactement 2 boutons

        def btn(label: str, couleur: str, signal) -> QPushButton:
            b = QPushButton(label)
            b.setFixedWidth(110)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(style_bouton(couleur, taille="petit"))
            pid = self.produit_id
            b.clicked.connect(lambda: signal.emit(pid))
            b.mousePressEvent = lambda e: (b.clicked.emit(), e.accept())
            return b

        if self._is_archive:
            layout.addWidget(btn("♻ Restaurer", Couleurs.SUCCES, self.action_restaurer))
        else:
            layout.addWidget(btn("📦 Archiver", Couleurs.ARDOISE, self.action_archiver))

        layout.addWidget(btn("🗑 Supprimer", Couleurs.DANGER, self.action_supprimer))
        return layout

    def _highlight(self, text: str) -> str:
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

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self.produit_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        self.double_clicked.emit(self.produit_id)
        super().mouseDoubleClickEvent(event)


# ============================================================================
# SearchProductsWidget — inchangé (vente, recherche rapide)
# ============================================================================


class SearchProductsWidget(QWidget):
    produit_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._construire_ui()

    def _construire_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._label_compteur = QLabel("")
        self._label_compteur.setStyleSheet(
            "font-size: 11pt; font-weight: bold; color: #777; padding: 5px 0;"
        )
        self._label_compteur.setVisible(False)
        layout.addWidget(self._label_compteur)

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

    def afficher_produits(
        self, produits: list[dict], search_terms: list[str] = None
    ) -> None:
        self.vider()
        self._label_compteur.setText(f"{len(produits)} produit(s) trouvé(s)")
        self._label_compteur.setVisible(bool(produits))

        if not produits:
            lbl = QLabel("Aucun produit trouvé")
            lbl.setStyleSheet("color: #7f8c8d; padding: 20px;")
            self._layout_cards.insertWidget(0, lbl)
            return

        for p in produits:
            card = ProductCard(p, search_terms)
            card.clicked.connect(self.produit_selected.emit)
            self._layout_cards.insertWidget(self._layout_cards.count() - 1, card)

        self.setVisible(True)

    def vider(self) -> None:
        while self._layout_cards.count() > 1:
            item = self._layout_cards.takeAt(0)
            if w := item.widget():
                w.deleteLater()
        self._label_compteur.setVisible(False)
