"""Vue détail d'une commande (fiche commande)."""

import logging

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QGraphicsDropShadowEffect,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from utils.styles import Couleurs, style_scroll_area

logger = logging.getLogger(__name__)

# Palette orange/bleu pour les commandes
_O_FONCE = "#E65100"
_O_MEDIUM = "#F57C00"
_O_CLAIR = "#FF9800"
_O_PALE = "#FFE0B2"
_O_GLACE = "#FFF3E0"
_B_PROFOND = "#1565C0"
_B_PALE = "#90CAF9"
_B_GLACE = "#E3F2FD"
_B_ARDOISE = "#546E7A"
_B_MARINE = "#263238"

_STATUT_MAP = {
    "en_attente": ("En attente", "#FF9800", "#FFF3E0"),
    "en_cours": ("En cours", "#2196F3", "#E3F2FD"),
    "terminee": ("Terminée", "#4CAF50", "#E8F5E9"),
    "annulee": ("Annulée", "#9E9E9E", "#F5F5F5"),
}


def _shadow(blur=18, dy=4, alpha=70, color="#000"):
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(blur)
    fx.setOffset(0, dy)
    c = QColor(color)
    c.setAlpha(alpha)
    fx.setColor(c)
    return fx


class FicheCommandeView(QWidget):
    """Fiche détail d'une commande."""

    retour_demande = Signal()
    client_demande = Signal(int)
    produit_demande = Signal(int)

    def __init__(self, viewmodel=None, parent=None):  # ← parent=None par défaut
        super().__init__(parent)
        self.viewmodel = viewmodel
        self._commande_id = None
        self._client_id = None
        self._mode_admin = True
        self._construire_ui()

    def _construire_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barre retour
        barre = QHBoxLayout()
        barre.setContentsMargins(24, 14, 24, 6)
        self.btn_retour = QPushButton("\u2190 Retour")
        self.btn_retour.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_retour.setStyleSheet(
            f"QPushButton {{ background: none; border: none; color: {_B_PROFOND}; "
            f"font-size: 12pt; font-weight: 600; padding: 6px 0; }}"
            f"QPushButton:hover {{ color: {_O_FONCE}; }}"
        )
        self.btn_retour.clicked.connect(self.retour_demande.emit)
        barre.addWidget(self.btn_retour)
        barre.addStretch()
        layout.addLayout(barre)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(style_scroll_area())

        self.conteneur = QWidget()
        self.conteneur.setStyleSheet(f"background: {Couleurs.BLANC};")
        self.layout_contenu = QVBoxLayout(self.conteneur)
        self.layout_contenu.setSpacing(14)
        self.layout_contenu.setContentsMargins(28, 6, 28, 36)

        self._build_header()
        self._build_actions()
        self._build_articles()
        self._build_taches()
        self._build_infos()

        self.layout_contenu.addStretch()
        scroll.setWidget(self.conteneur)
        layout.addWidget(scroll)

    def _build_header(self):
        self.header_frame = QFrame()
        self.header_frame.setMinimumHeight(180)
        self.header_frame.setStyleSheet(
            "QFrame {"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            f"    stop:0 {_O_FONCE}, stop:0.45 {_O_MEDIUM}, stop:1 {_O_CLAIR});"
            "  border-radius: 20px;"
            "}"
        )
        self.header_frame.setGraphicsEffect(_shadow(28, 8, 90, _O_FONCE))

        outer = QVBoxLayout(self.header_frame)
        outer.setContentsMargins(30, 22, 30, 22)
        outer.setSpacing(0)

        top = QHBoxLayout()
        top.setSpacing(14)

        self._lbl_avatar = QLabel("\U0001f4e6")
        self._lbl_avatar.setFixedSize(64, 64)
        self._lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_avatar.setStyleSheet(
            "font-size: 22pt; background: rgba(255,255,255,0.18); "
            "border-radius: 32px; border: 2.5px solid rgba(255,255,255,0.35);"
        )
        top.addWidget(self._lbl_avatar, alignment=Qt.AlignmentFlag.AlignVCenter)

        col = QVBoxLayout()
        col.setSpacing(3)
        self.label_client = QLabel()
        self.label_client.setCursor(Qt.CursorShape.PointingHandCursor)
        self.label_client.setStyleSheet(
            "font-size: 18pt; font-weight: 800; color: white; border: none; background: none;"
        )
        self.label_client.mousePressEvent = lambda e: (
            self.client_demande.emit(self._client_id) if self._client_id else None
        )
        col.addWidget(self.label_client)

        self._lbl_ref = QLabel()
        self._lbl_ref.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._lbl_ref.setStyleSheet(
            "font-size: 9pt; color: rgba(255,255,255,0.60); letter-spacing: 1px; "
            "border: none; background: none;"
        )
        col.addWidget(self._lbl_ref)
        col.addStretch()
        top.addLayout(col)
        top.addStretch()

        self.label_statut = QLabel()
        self.label_statut.setStyleSheet(
            "font-size: 10pt; font-weight: 700; color: white; border: none; "
            "background: rgba(255,255,255,0.22); border-radius: 14px; padding: 5px 16px;"
        )
        top.addWidget(self.label_statut, alignment=Qt.AlignmentFlag.AlignTop)
        outer.addLayout(top)
        outer.addStretch()

        bas = QHBoxLayout()
        bas.setSpacing(16)

        col_total = QVBoxLayout()
        col_total.setSpacing(1)
        self.label_total = QLabel()
        self.label_total.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.label_total.setStyleSheet(
            "font-size: 38pt; font-weight: 900; color: white; border: none; background: none;"
        )
        col_total.addWidget(self.label_total)
        lbl_sous = QLabel("montant total commande")
        lbl_sous.setStyleSheet(
            "font-size: 8pt; color: rgba(255,255,255,0.52); letter-spacing: 1px; "
            "border: none; background: none;"
        )
        col_total.addWidget(lbl_sous)
        bas.addLayout(col_total)
        bas.addStretch()

        col_date = QVBoxLayout()
        col_date.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom
        )
        self.label_date = QLabel()
        self.label_date.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.label_date.setStyleSheet(
            "font-size: 11pt; font-weight: 600; color: white; border: none; "
            "background: rgba(255,255,255,0.20); border-radius: 12px; padding: 5px 14px;"
        )
        col_date.addWidget(self.label_date)
        bas.addLayout(col_date)
        outer.addLayout(bas)

        self.layout_contenu.addWidget(self.header_frame)

    def _build_actions(self):
        self._frame_actions = QFrame()
        self._frame_actions.setStyleSheet(
            f"QFrame {{ background: {_O_GLACE}; border: 1.5px solid {_O_PALE}; border-radius: 12px; }}"
        )
        row = QHBoxLayout(self._frame_actions)
        row.setContentsMargins(16, 10, 16, 10)
        row.setSpacing(10)

        self.btn_en_cours = QPushButton("Passer en cours")
        self.btn_en_cours.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_en_cours.setMinimumHeight(40)
        self.btn_en_cours.setStyleSheet(
            f"QPushButton {{ background: white; color: #2196F3; "
            f"border: 1.5px solid #2196F3; border-radius: 10px; "
            f"font-size: 10pt; font-weight: 600; padding: 8px 16px; }}"
            f"QPushButton:hover {{ background: #2196F3; color: white; }}"
        )
        self.btn_en_cours.clicked.connect(lambda: self._changer_statut("en_cours"))
        row.addWidget(self.btn_en_cours)

        self.btn_terminer = QPushButton("Terminer la commande")
        self.btn_terminer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_terminer.setMinimumHeight(40)
        self.btn_terminer.setStyleSheet(
            f"QPushButton {{ background: white; color: #4CAF50; "
            f"border: 1.5px solid #4CAF50; border-radius: 10px; "
            f"font-size: 10pt; font-weight: 600; padding: 8px 16px; }}"
            f"QPushButton:hover {{ background: #4CAF50; color: white; }}"
        )
        self.btn_terminer.clicked.connect(self._terminer_commande)
        row.addWidget(self.btn_terminer)

        row.addStretch()

        self.btn_annuler = QPushButton("Annuler")
        self.btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_annuler.setMinimumHeight(40)
        self.btn_annuler.setStyleSheet(
            f"QPushButton {{ background: white; color: #F44336; "
            f"border: 1.5px solid #F44336; border-radius: 10px; "
            f"font-size: 10pt; font-weight: 600; padding: 8px 16px; }}"
            f"QPushButton:hover {{ background: #F44336; color: white; }}"
        )
        self.btn_annuler.clicked.connect(lambda: self._changer_statut("annulee"))
        row.addWidget(self.btn_annuler)

        self.layout_contenu.addWidget(self._frame_actions)

    def _build_articles(self):
        self._articles_card = QFrame()
        self._articles_card.setStyleSheet(
            f"QFrame {{ background: {_B_GLACE}; border: 1.5px solid {_B_PALE}; border-radius: 14px; }}"
        )
        lay = QVBoxLayout(self._articles_card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(8)

        lbl_t = QLabel("\U0001f4e6  Articles de la commande")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {_B_PALE}; border: none;")
        lay.addWidget(sep)

        self._articles_layout = QVBoxLayout()
        self._articles_layout.setSpacing(6)
        lay.addLayout(self._articles_layout)

        self.layout_contenu.addWidget(self._articles_card)

    def _build_taches(self):
        self._taches_card = QFrame()
        self._taches_card.setStyleSheet(
            f"QFrame {{ background: {_O_GLACE}; border: 1.5px solid {_O_PALE}; border-radius: 14px; }}"
        )
        lay = QVBoxLayout(self._taches_card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(8)

        lbl_t = QLabel("\u2705  T\u00e2ches associ\u00e9es")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_O_FONCE}; "
            f"border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {_O_PALE}; border: none;")
        lay.addWidget(sep)

        self._taches_layout = QVBoxLayout()
        self._taches_layout.setSpacing(6)
        lay.addLayout(self._taches_layout)

        self._taches_card.hide()
        self.layout_contenu.addWidget(self._taches_card)

    def _build_infos(self):
        self._infos_card = QFrame()
        self._infos_card.setStyleSheet(
            f"QFrame {{ background: {_B_GLACE}; border: 1.5px solid {_B_PALE}; border-radius: 14px; }}"
        )
        lay = QVBoxLayout(self._infos_card)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(10)

        lbl_t = QLabel("\u2139  Informations")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)

        self._infos_layout = QVBoxLayout()
        self._infos_layout.setSpacing(6)
        lay.addLayout(self._infos_layout)

        self._infos_card.hide()
        self.layout_contenu.addWidget(self._infos_card)

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    def charger_commande(self, commande_id: int):
        if not self.viewmodel:
            return
        data = self.viewmodel.obtenir_commande(commande_id)
        if not data:
            return

        self._commande_id = commande_id
        articles = data.get("articles", [])
        taches = data.get("taches", [])
        total = float(data.get("total") or 0.0)
        statut = data.get("statut", "en_attente")

        # Header
        self._client_id = data.get("client_id")
        nom = (data.get("client_nom") or "").upper()
        prenom = data.get("client_prenom") or ""
        nom_complet = f"{nom} {prenom}".strip()
        self.label_client.setText(nom_complet or "Client inconnu")

        initiales = (
            "".join(p[0].upper() for p in nom_complet.split()[:2])
            if nom_complet
            else "?"
        )
        self._lbl_avatar.setText(initiales)
        self._lbl_avatar.setStyleSheet(
            "font-size: 14pt; font-weight: 800; color: white; "
            "background: rgba(255,255,255,0.20); border-radius: 32px; "
            "border: 2.5px solid rgba(255,255,255,0.35);"
        )

        self._lbl_ref.setText(f"COMMANDE \u00b7 #{commande_id}")
        self.label_total.setText(f"{total:.2f} \u20ac")

        date_str = str(data.get("date_prevue") or "")[:10]
        heure = data.get("heure_prevue") or ""
        date_affiche = date_str
        if heure:
            date_affiche += f" \u00e0 {heure}"
        self.label_date.setText(f"\U0001f5d3  {date_affiche}" if date_str else "\u2014")

        # Statut
        s_label, s_color, s_bg = _STATUT_MAP.get(statut, ("Inconnu", "#666", "#F5F5F5"))
        self.label_statut.setText(s_label)

        # Boutons selon statut
        est_terminee = statut in ("terminee", "annulee")
        self.btn_en_cours.setVisible(statut == "en_attente")
        self.btn_terminer.setVisible(statut in ("en_attente", "en_cours"))
        self.btn_annuler.setVisible(not est_terminee)
        self._frame_actions.setVisible(self._mode_admin and not est_terminee)

        # Articles
        self._vider_layout(self._articles_layout)
        for i, art in enumerate(articles):
            self._articles_layout.addWidget(self._creer_ligne_article(art, i))

        # Tâches
        self._vider_layout(self._taches_layout)
        if taches:
            self._taches_card.show()
            for t in taches:
                self._taches_layout.addWidget(self._creer_ligne_tache(t))
        else:
            self._taches_card.hide()

        # Infos
        self._vider_layout(self._infos_layout)
        notes = (data.get("notes") or "").strip()
        if notes:
            self._infos_card.show()
            lbl = QLabel(f"\U0001f4dd  {notes}")
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                f"font-size: 10pt; color: {_B_MARINE}; border: none; background: none; padding: 8px;"
            )
            self._infos_layout.addWidget(lbl)
        else:
            self._infos_card.hide()

    def mettre_a_jour_mode(self, mode_admin: bool):
        self._mode_admin = mode_admin

    def _creer_ligne_article(self, article: dict, rang: int) -> QFrame:
        bg = "white" if rang % 2 == 0 else _B_GLACE
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background: {bg}; border: 1.5px solid {_B_PALE}; border-radius: 10px; }}"
        )
        row = QHBoxLayout(frame)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(14)

        nom = article.get("produit_nom") or "?"
        produit_id = article.get("produit_id")
        lbl_nom = QLabel(nom)
        if produit_id:
            lbl_nom.setCursor(Qt.CursorShape.PointingHandCursor)
            lbl_nom.mousePressEvent = (
                lambda e, pid=produit_id: self.produit_demande.emit(pid)
            )
            lbl_nom.setStyleSheet(
                f"font-size: 10pt; font-weight: 700; color: {_B_PROFOND}; border: none; background: none;"
            )
        else:
            lbl_nom.setStyleSheet(
                f"font-size: 10pt; font-weight: 700; color: {_B_MARINE}; border: none; background: none;"
            )
        row.addWidget(lbl_nom)
        row.addStretch()

        qte = article.get("quantite", 0)
        lbl_qte = QLabel(f"\u00d7{qte}")
        lbl_qte.setStyleSheet(
            f"font-size: 10pt; font-weight: 700; color: {_O_FONCE}; "
            f"background: {_O_GLACE}; border-radius: 8px; padding: 2px 8px; border: none;"
        )
        row.addWidget(lbl_qte)

        pu = float(article.get("prix_unitaire") or 0)
        lbl_pu = QLabel(f"{pu:.2f} \u20ac")
        lbl_pu.setStyleSheet(
            f"font-size: 10pt; color: {_B_ARDOISE}; border: none; background: none;"
        )
        row.addWidget(lbl_pu)

        st = float(article.get("prix_total") or (pu * qte))
        lbl_st = QLabel(f"{st:.2f} \u20ac")
        lbl_st.setStyleSheet(
            f"font-size: 10pt; font-weight: 700; color: {_B_MARINE}; border: none; background: none;"
        )
        row.addWidget(lbl_st)

        return frame

    def _creer_ligne_tache(self, tache: dict) -> QFrame:
        frame = QFrame()
        terminee = tache.get("terminee", False)
        border_color = "#4CAF50" if terminee else _O_PALE
        frame.setStyleSheet(
            f"QFrame {{ background: white; border: 1.5px solid {border_color}; border-radius: 10px; }}"
        )
        row = QHBoxLayout(frame)
        row.setContentsMargins(14, 8, 14, 8)
        row.setSpacing(10)

        check = "\u2705" if terminee else "\u2b1c"
        lbl_check = QLabel(check)
        lbl_check.setStyleSheet("font-size: 14pt; border: none; background: none;")
        row.addWidget(lbl_check)

        titre = tache.get("titre", "")
        lbl_titre = QLabel(titre)
        style_titre = (
            f"font-size: 10pt; color: {_B_MARINE}; border: none; background: none;"
        )
        if terminee:
            style_titre += " text-decoration: line-through; color: #999;"
        lbl_titre.setStyleSheet(style_titre)
        row.addWidget(lbl_titre)
        row.addStretch()

        priorite = tache.get("priorite", 5)
        lbl_prio = QLabel(f"P{priorite}")
        prio_color = self._couleur_priorite(priorite)
        lbl_prio.setStyleSheet(
            f"font-size: 9pt; font-weight: bold; color: {prio_color}; "
            f"border: none; background: none;"
        )
        row.addWidget(lbl_prio)

        return frame

    @staticmethod
    def _couleur_priorite(priorite: int) -> str:
        colors = [
            "#D32F2F",
            "#E53935",
            "#F44336",
            "#FF5722",
            "#FF9800",
            "#FFC107",
            "#CDDC39",
            "#8BC34A",
            "#66BB6A",
            "#4CAF50",
        ]
        idx = max(0, min(priorite - 1, 9))
        return colors[idx]

    def _changer_statut(self, nouveau_statut: str):
        if not self._commande_id or not self.viewmodel:
            return
        if nouveau_statut == "annulee":
            rep = QMessageBox.question(
                self,
                "Confirmation",
                "Voulez-vous vraiment annuler cette commande ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if rep != QMessageBox.StandardButton.Yes:
                return
        self.viewmodel.modifier_statut(self._commande_id, nouveau_statut)
        self.charger_commande(self._commande_id)

    def _terminer_commande(self):
        if not self._commande_id or not self.viewmodel:
            return
        rep = QMessageBox.question(
            self,
            "Terminer la commande",
            "Cela va convertir la commande en vente et d\u00e9cr\u00e9menter le stock.\n"
            "Confirmer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep != QMessageBox.StandardButton.Yes:
            return

        txn_id = self.viewmodel.terminer_commande(self._commande_id)
        if txn_id:
            QMessageBox.information(
                self,
                "Commande termin\u00e9e",
                "La commande a \u00e9t\u00e9 convertie en vente avec succ\u00e8s !",
            )
            self.charger_commande(self._commande_id)
        else:
            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible de terminer la commande.\nV\u00e9rifiez le stock disponible.",
            )

    @staticmethod
    def _vider_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                FicheCommandeView._vider_layout(item.layout())
