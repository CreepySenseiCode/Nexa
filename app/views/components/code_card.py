"""Widget de carte code promotionnel."""

import re
import logging
from datetime import date

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal

from utils.styles import style_bouton, Couleurs

logger = logging.getLogger(__name__)


class CodeCard(QFrame):
    """Card compacte pour un code promotionnel.

    - Double clic : émet double_clicked (ouvre la fiche)
    - Boutons     : Désactiver/Activer + Supprimer
    """

    double_clicked = Signal(int)
    action_archiver = Signal(int)  # = Désactiver
    action_restaurer = Signal(int)  # = Activer
    action_supprimer = Signal(int)
    clicked = Signal(int)

    def __init__(
        self,
        code_data: dict,
        search_terms: list = None,
        show_actions: bool = False,
        is_archive: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.code_id = code_data.get("id", 0)
        self._search_terms = search_terms or []
        self._is_archive = is_archive
        self._construire_ui(code_data, show_actions)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _construire_ui(self, data: dict, show_actions: bool) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "CodeCard {"
            "    background-color: #FFFFFF;"
            "    border: 1px solid #E0E0E0;"
            "    border-radius: 10px;"
            "}"
            "CodeCard:hover {"
            "    background-color: #F5F5F5;"
            "    border: 1px solid #7B1FA2;"
            "}"
        )
        self.setFixedHeight(80)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 6, 10, 6)
        root.setSpacing(12)

        lbl_icon = QLabel("🎟")
        lbl_icon.setFixedSize(52, 52)
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 24pt; border: none;")
        root.addWidget(lbl_icon)

        root.addLayout(self._construire_infos(data), stretch=1)
        if show_actions:
            root.addLayout(self._construire_boutons())

    def _construire_infos(self, data: dict) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        ligne = QHBoxLayout()
        ligne.setSpacing(8)

        # 1. Badge statut
        statut = self._calculer_statut(data)
        badge_statut = QLabel(statut["texte"])
        badge_statut.setStyleSheet(
            f"font-size: 10pt; color: {statut['fg']}; background-color: {statut['bg']};"
            "border-radius: 8px; padding: 2px 9px; border: none;"
        )
        ligne.addWidget(badge_statut)

        # 2. Code (monospace)
        code = data.get("code") or ""
        lbl_code = QLabel(self._highlight(code))
        lbl_code.setTextFormat(Qt.TextFormat.RichText)
        lbl_code.setStyleSheet(
            "font-size: 13pt; font-weight: bold; color: #222; border: none;"
            "font-family: 'Courier New', monospace; letter-spacing: 1px;"
        )
        ligne.addWidget(lbl_code)

        # 3. Réduction
        lbl_val = QLabel(self._formater_reduction(data))
        lbl_val.setStyleSheet(
            "font-size: 12pt; color: #7B1FA2; font-weight: 600; border: none;"
        )
        ligne.addWidget(lbl_val)

        ligne.addStretch()

        # 4. Badge utilisations
        nb_util = data.get("nb_utilisations") or 0
        limite = data.get("limite_utilisations")
        if limite:
            ratio = nb_util / limite
            util_texte = f"⟳ {nb_util}/{limite}"
            util_bg = (
                "#FFEBEE" if ratio >= 1 else ("#FFF3E0" if ratio >= 0.8 else "#E8F5E9")
            )
            util_fg = (
                "#C62828" if ratio >= 1 else ("#E65100" if ratio >= 0.8 else "#2E7D32")
            )
        else:
            util_texte, util_bg, util_fg = f"⟳ {nb_util}", "#F5F5F5", "#555"

        badge_util = QLabel(util_texte)
        badge_util.setStyleSheet(
            f"font-size: 10pt; color: {util_fg}; background-color: {util_bg};"
            "border-radius: 8px; padding: 2px 9px; border: none;"
        )
        ligne.addWidget(badge_util)

        layout.addLayout(ligne)

        # Ligne 2 : dates
        date_debut = str(data.get("date_debut") or "")[:10]
        date_fin = str(data.get("date_fin") or "")[:10]
        if date_debut or date_fin:
            parties = []
            if date_debut:
                parties.append(f"Du {date_debut}")
            if date_fin:
                parties.append(f"au {date_fin}")
            lbl_dates = QLabel("  ·  ".join(parties))
            lbl_dates.setStyleSheet("font-size: 10pt; color: #999; border: none;")
            layout.addWidget(lbl_dates)

        return layout

    def _construire_boutons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        def btn(label: str, couleur: str, signal) -> QPushButton:
            b = QPushButton(label)
            b.setFixedWidth(110)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(style_bouton(couleur, taille="petit"))
            cid = self.code_id
            b.clicked.connect(lambda: signal.emit(cid))
            b.mousePressEvent = lambda e: (b.clicked.emit(), e.accept())
            return b

        if self._is_archive:
            layout.addWidget(btn("♻ Activer", Couleurs.SUCCES, self.action_restaurer))
        else:
            layout.addWidget(
                btn("⏸ Désactiver", Couleurs.ARDOISE, self.action_archiver)
            )

        layout.addWidget(btn("🗑 Supprimer", Couleurs.DANGER, self.action_supprimer))
        return layout

    # ------------------------------------------------------------------

    def _calculer_statut(self, data: dict) -> dict:
        if not data.get("actif", True):
            return {"texte": "Inactif", "bg": "#EEEEEE", "fg": "#757575"}
        date_fin_str = data.get("date_fin") or ""
        if date_fin_str:
            try:
                if date.fromisoformat(str(date_fin_str)[:10]) < date.today():
                    return {"texte": "Expiré", "bg": "#FFEBEE", "fg": "#C62828"}
            except ValueError:
                pass
        nb = data.get("nb_utilisations") or 0
        limit = data.get("limite_utilisations")
        if limit and nb >= limit:
            return {"texte": "Épuisé", "bg": "#FFF3E0", "fg": "#E65100"}
        return {"texte": "✓ Actif", "bg": "#E8F5E9", "fg": "#2E7D32"}

    def _formater_reduction(self, data: dict) -> str:
        type_r = (data.get("type_reduction") or "").lower()
        valeur = data.get("valeur") or 0.0
        if "pourcent" in type_r or type_r == "%":
            return f"-{valeur:.0f}%"
        return f"-{valeur:.2f} €"

    def _highlight(self, text: str) -> str:
        if not self._search_terms or not text:
            return text
        result = text
        for term in self._search_terms:
            if not term:
                continue
            result = re.compile(re.escape(term), re.IGNORECASE).sub(
                lambda m: f"<b style='color:#7B1FA2'>{m.group()}</b>", result
            )
        return result

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self.code_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        logger.info(f"🖱️ DOUBLE-CLICK sur code_card code_id={self.code_id}")
        self.double_clicked.emit(self.code_id)
        super().mouseDoubleClickEvent(event)
