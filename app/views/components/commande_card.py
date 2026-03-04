"""Widget de carte commande."""

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


_STATUT_STYLES = {
    "en_attente": ("#FF9800", "#FFF3E0", "En attente"),
    "en_cours": ("#2196F3", "#E3F2FD", "En cours"),
    "terminee": ("#4CAF50", "#E8F5E9", "Terminée"),
    "annulee": ("#9E9E9E", "#F5F5F5", "Annulée"),
}


class CommandeCard(QFrame):
    """Card compacte pour une commande.

    Layout : [date_badge] | [client / articles / statut] | stretch | [total] | [actions]
    """

    double_clicked = Signal(int)  # commande_id
    action_supprimer = Signal(int)

    def __init__(
        self,
        commande_data: dict,
        search_terms: list = None,
        show_actions: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.commande_id = commande_data.get("id", 0)
        self._search_terms = search_terms or []
        self._construire_ui(commande_data, show_actions)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _construire_ui(self, data: dict, show_actions: bool) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "CommandeCard {"
            "    background-color: #FFFFFF;"
            "    border: 1px solid #E0E0E0;"
            "    border-radius: 10px;"
            "}"
            "CommandeCard:hover {"
            "    background-color: #F5F5F5;"
            "    border: 1px solid #1976D2;"
            "}"
        )
        self.setFixedHeight(90)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 6, 10, 6)
        root.setSpacing(12)

        # Badge date prévue
        date_str = str(data.get("date_prevue") or "")[:10]
        heure = data.get("heure_prevue") or ""
        date_text = date_str
        if heure:
            date_text += f"\n{heure}"
        lbl_date = QLabel(date_text)
        lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_date.setFixedWidth(90)
        lbl_date.setStyleSheet(
            "font-size: 10pt; color: #E65100; background-color: #FFF3E0;"
            "border-radius: 8px; padding: 4px 8px; border: none;"
        )
        root.addWidget(lbl_date)

        # Infos
        root.addLayout(self._construire_infos(data), stretch=1)

        # Statut badge (entre infos et total)
        statut = data.get("statut", "en_attente")
        color, bg, label = _STATUT_STYLES.get(
            statut, ("#666", "#F5F5F5", statut)
        )
        lbl_statut = QLabel(label)
        lbl_statut.setStyleSheet(
            f"font-size: 9pt; font-weight: bold; color: {color}; "
            f"background-color: {bg}; border-radius: 6px; "
            f"padding: 2px 8px; border: none;"
        )
        lbl_statut.setFixedWidth(90)
        lbl_statut.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(lbl_statut)

        # Total
        total = data.get("total") or 0.0
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
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Ligne 1 : client
        nom = data.get("client_nom") or ""
        prenom = data.get("client_prenom") or ""
        client_texte = f"{nom} {prenom}".strip()
        lbl_client = QLabel(self._highlight(client_texte))
        lbl_client.setTextFormat(Qt.TextFormat.RichText)
        lbl_client.setStyleSheet(
            "font-size: 13pt; font-weight: bold; color: #222; border: none;"
        )
        layout.addWidget(lbl_client)

        # Ligne 2 : articles
        articles = data.get("articles_resume") or ""
        if len(articles) > 60:
            articles = articles[:57] + "..."
        lbl_articles = QLabel(self._highlight(articles))
        lbl_articles.setTextFormat(Qt.TextFormat.RichText)
        lbl_articles.setStyleSheet(
            "font-size: 10pt; color: #888; border: none;"
        )
        layout.addWidget(lbl_articles)

        return layout

    def _construire_boutons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        btn_suppr = QPushButton("\U0001f5d1")
        btn_suppr.setFixedSize(36, 36)
        btn_suppr.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_suppr.setToolTip("Supprimer")
        btn_suppr.setStyleSheet(style_bouton(Couleurs.DANGER, taille="petit"))
        cid = self.commande_id
        btn_suppr.clicked.connect(lambda: self.action_supprimer.emit(cid))
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

    def mouseDoubleClickEvent(self, event) -> None:
        self.double_clicked.emit(self.commande_id)
        super().mouseDoubleClickEvent(event)
