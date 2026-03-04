"""Widget de carte vente (transaction)."""

import re

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal

from utils.styles import style_bouton, Couleurs


class VenteCard(QFrame):
    """Card compacte pour une transaction de vente.

    Layout : [date_badge] | [client / articles] | stretch | [total] | [supprimer]
    """

    double_clicked = Signal(str)  # transaction_id
    action_supprimer = Signal(str)
    clicked = Signal(str)

    def __init__(
        self,
        vente_data: dict,
        search_terms: list = None,
        show_actions: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.transaction_id = vente_data.get("transaction_id", "")
        self._search_terms = search_terms or []
        self._construire_ui(vente_data, show_actions)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _construire_ui(self, data: dict, show_actions: bool) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "VenteCard {"
            "    background-color: #FFFFFF;"
            "    border: 1px solid #E0E0E0;"
            "    border-radius: 10px;"
            "}"
            "VenteCard:hover {"
            "    background-color: #F5F5F5;"
            "    border: 1px solid #1976D2;"
            "}"
        )
        self.setFixedHeight(80)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 6, 10, 6)
        root.setSpacing(12)

        # Badge date
        date_str = str(data.get("date_vente") or "")[:10]
        lbl_date = QLabel(date_str)
        lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_date.setFixedWidth(90)
        lbl_date.setStyleSheet(
            "font-size: 10pt; color: #1565C0; background-color: #E3F2FD;"
            "border-radius: 8px; padding: 4px 8px; border: none;"
        )
        root.addWidget(lbl_date)

        # Infos (client + articles)
        root.addLayout(self._construire_infos(data), stretch=1)

        # Total
        total = data.get("total_transaction") or 0.0
        lbl_total = QLabel(f"{total:.2f} €")
        lbl_total.setStyleSheet(
            "font-size: 13pt; font-weight: bold; color: #2E7D32; border: none;"
        )
        lbl_total.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        root.addWidget(lbl_total)

        if show_actions:
            root.addLayout(self._construire_boutons())

    def _construire_infos(self, data: dict) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Ligne 1 : nom client
        nom = data.get("client_nom") or ""
        prenom = data.get("client_prenom") or ""
        client_texte = f"{nom} {prenom}".strip()
        lbl_client = QLabel(self._highlight(client_texte))
        lbl_client.setTextFormat(Qt.TextFormat.RichText)
        lbl_client.setStyleSheet(
            "font-size: 13pt; font-weight: bold; color: #222; border: none;"
        )
        layout.addWidget(lbl_client)

        # Ligne 2 : résumé des articles (tronqué à 60 chars)
        articles = data.get("articles_resume") or ""
        if len(articles) > 60:
            articles = articles[:57] + "..."
        lbl_articles = QLabel(self._highlight(articles))
        lbl_articles.setTextFormat(Qt.TextFormat.RichText)
        lbl_articles.setStyleSheet("font-size: 10pt; color: #888; border: none;")
        layout.addWidget(lbl_articles)

        return layout

    def _construire_boutons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        btn_suppr = QPushButton("🗑")
        btn_suppr.setFixedSize(36, 36)
        btn_suppr.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_suppr.setToolTip("Supprimer")
        btn_suppr.setStyleSheet(style_bouton(Couleurs.DANGER, taille="petit"))
        tid = self.transaction_id
        btn_suppr.clicked.connect(lambda: self.action_supprimer.emit(tid))
        btn_suppr.mousePressEvent = lambda e: (btn_suppr.clicked.emit(), e.accept())
        layout.addWidget(btn_suppr)

        return layout

    def _highlight(self, text: str) -> str:
        if not self._search_terms or not text:
            return text
        result = text
        for term in self._search_terms:
            if not term:
                continue
            result = re.compile(re.escape(term), re.IGNORECASE).sub(
                lambda m: f"<b style='color:#1976D2'>{m.group()}</b>", result
            )
        return result

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self.transaction_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        self.double_clicked.emit(self.transaction_id)
        super().mouseDoubleClickEvent(event)
