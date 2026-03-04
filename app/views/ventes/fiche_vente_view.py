"""Vue détail d'une transaction de vente (fiche vente)."""

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
    QApplication,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor

from utils.styles import Couleurs, style_scroll_area

logger = logging.getLogger(__name__)


# ── Palette bleue ────────────────────────────────────────────────────
_B_NUIT = "#0D47A1"
_B_PROFOND = "#1565C0"
_B_MEDIUM = "#1976D2"
_B_VRAI = "#1E88E5"
_B_CLAIR = "#42A5F5"
_B_PALE = "#90CAF9"
_B_GLACE = "#E3F2FD"
_B_ACCENT = "#0288D1"
_B_ARDOISE = "#546E7A"
_B_MARINE = "#263238"
_B_CYAN = "#00ACC1"


# ══════════════════════════════════════════════════════════════════════
# Helpers visuels
# ══════════════════════════════════════════════════════════════════════


def _shadow(blur: int = 18, dy: int = 4, alpha: int = 70, color: str = "#000"):
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(blur)
    fx.setOffset(0, dy)
    c = QColor(color)
    c.setAlpha(alpha)
    fx.setColor(c)
    return fx


class _HLine(QFrame):
    def __init__(self, dashed: bool = False, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)
        style = f"background: {_B_PALE}; border: none;"
        if dashed:
            # simulé via border-top
            self.setFixedHeight(2)
            style = f"border: none; border-top: 2px dashed {_B_PALE}; background: transparent;"
        self.setStyleSheet(style)


class _SectionCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: {_B_GLACE}; "
            f"border: 1.5px solid {_B_PALE}; border-radius: 14px; }}"
        )


class _KpiCard(QFrame):
    def __init__(self, titre: str, valeur: str, couleur: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: white; border: 1.5px solid {_B_PALE}; border-radius: 14px; }}"
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        col = QVBoxLayout(self)
        col.setContentsMargins(16, 16, 16, 16)
        col.setSpacing(6)
        col.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._lbl_v = QLabel(valeur)
        self._lbl_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_v.setWordWrap(True)
        self._lbl_v.setStyleSheet(
            f"font-size: 22pt; font-weight: 800; color: {couleur}; "
            f"border: none; background: none;"
        )
        col.addWidget(self._lbl_v)

        lbl_t = QLabel(titre)
        lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_t.setStyleSheet(
            f"font-size: 9pt; color: {_B_ARDOISE}; border: none; background: none;"
        )
        col.addWidget(lbl_t)

    def set_valeur(self, valeur: str):
        self._lbl_v.setText(valeur)


class _InfoChip(QFrame):
    def __init__(self, icone: str, titre: str, valeur: str = "—", parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: white; border: 1.5px solid {_B_PALE}; border-radius: 12px; }}"
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 12, 14, 12)
        row.setSpacing(12)

        lbl_ico = QLabel(icone)
        lbl_ico.setFixedSize(32, 32)
        lbl_ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ico.setStyleSheet("font-size: 16pt; border: none; background: none;")
        row.addWidget(lbl_ico)

        col = QVBoxLayout()
        col.setSpacing(2)
        lbl_t = QLabel(titre.upper())
        lbl_t.setStyleSheet(
            f"font-size: 8pt; font-weight: 600; letter-spacing: 1px; "
            f"color: {_B_ARDOISE}; border: none; background: none;"
        )
        col.addWidget(lbl_t)
        self._lbl_v = QLabel(valeur)
        self._lbl_v.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._lbl_v.setStyleSheet(
            f"font-size: 11pt; font-weight: 700; color: {_B_MARINE}; "
            f"border: none; background: none;"
        )
        col.addWidget(self._lbl_v)
        row.addLayout(col)
        row.addStretch()

    def set_valeur(self, v: str):
        self._lbl_v.setText(v)


class _ActionBtn(QPushButton):
    def __init__(self, icone: str, texte: str, couleur: str, parent=None):
        super().__init__(f"{icone}  {texte}", parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(40)
        self._couleur = couleur
        self._apply()

    def _apply(self):
        self.setStyleSheet(
            f"QPushButton {{"
            f"  background: white; color: {self._couleur};"
            f"  border: 1.5px solid {self._couleur}; border-radius: 10px;"
            f"  font-size: 10pt; font-weight: 600; padding: 8px 16px;"
            f"}}"
            f"QPushButton:hover {{ background: {self._couleur}; color: white; }}"
        )


class _LigneArticle(QFrame):
    """
    Carte d'article de vente :
        [🔵 initiale]  Nom produit           [×qté]  [prix unit.]  [sous-total]
    """

    def __init__(
        self,
        article: dict,
        symbole: str = "€",
        rang: int = 0,
        on_produit_click=None,
        parent=None,
    ):
        super().__init__(parent)
        bg = "white" if rang % 2 == 0 else _B_GLACE
        self.setStyleSheet(
            f"QFrame {{ background: {bg}; border: 1.5px solid {_B_PALE}; border-radius: 10px; }}"
            f"QFrame:hover {{ border-color: {_B_CLAIR}; }}"
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 12, 14, 12)
        row.setSpacing(14)

        # Avatar initiale produit
        nom_prod = article.get("produit_nom") or "?"
        produit_id = article.get("produit_id")
        lbl_av = QLabel(nom_prod[0].upper() if nom_prod else "?")
        lbl_av.setFixedSize(36, 36)
        lbl_av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_av.setStyleSheet(
            f"background: {_B_GLACE}; color: {_B_PROFOND}; border-radius: 18px; "
            f"font-size: 11pt; font-weight: 700; border: 1.5px solid {_B_PALE};"
        )
        row.addWidget(lbl_av)

        # Nom + ref
        col = QVBoxLayout()
        col.setSpacing(1)
        lbl_nom = QLabel(nom_prod)
        if on_produit_click and produit_id:
            lbl_nom.setCursor(Qt.CursorShape.PointingHandCursor)
            lbl_nom.mousePressEvent = lambda e, pid=produit_id: on_produit_click(pid)
            lbl_nom.setStyleSheet(
                f"font-size: 10pt; font-weight: 700; color: {_B_PROFOND}; "
                f"border: none; background: none;"
            )
        else:
            lbl_nom.setStyleSheet(
                f"font-size: 10pt; font-weight: 700; color: {_B_MARINE}; "
                f"border: none; background: none;"
            )
        col.addWidget(lbl_nom)
        ref = article.get("produit_ref") or article.get("sku") or ""
        if ref:
            lbl_ref = QLabel(ref)
            lbl_ref.setStyleSheet(
                f"font-size: 8pt; color: {_B_ARDOISE}; border: none; background: none;"
            )
            col.addWidget(lbl_ref)
        row.addLayout(col)
        row.addStretch()

        # Quantité badge
        qte = article.get("quantite") or 0
        lbl_qte = QLabel(f"×{qte}")
        lbl_qte.setFixedWidth(42)
        lbl_qte.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_qte.setStyleSheet(
            f"font-size: 10pt; font-weight: 700; color: {_B_ACCENT}; "
            f"background: {_B_GLACE}; border-radius: 8px; padding: 2px 6px; border: none;"
        )
        row.addWidget(lbl_qte)

        # Prix unitaire
        pu = float(article.get("prix_unitaire") or 0)
        lbl_pu = QLabel(f"{pu:.2f} {symbole}")
        lbl_pu.setFixedWidth(80)
        lbl_pu.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl_pu.setStyleSheet(
            f"font-size: 10pt; color: {_B_ARDOISE}; border: none; background: none;"
        )
        row.addWidget(lbl_pu)

        # Séparateur
        sep = QLabel("=")
        sep.setStyleSheet(
            f"color: {_B_PALE}; font-size: 12pt; border: none; background: none;"
        )
        row.addWidget(sep)

        # Sous-total
        st = float(article.get("prix_total") or (pu * qte))
        lbl_st = QLabel(f"{st:.2f} {symbole}")
        lbl_st.setFixedWidth(90)
        lbl_st.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl_st.setStyleSheet(
            f"font-size: 10pt; font-weight: 700; color: {_B_MARINE}; "
            f"border: none; background: none;"
        )
        row.addWidget(lbl_st)


# ══════════════════════════════════════════════════════════════════════
# Vue principale
# ══════════════════════════════════════════════════════════════════════


class FicheVenteView(QWidget):
    """Fiche détail d'une transaction de vente — design moderne, palette bleue."""

    retour_demande = Signal()
    client_demande = Signal(int)  # naviguer vers la fiche client
    produit_demande = Signal(int)  # naviguer vers la fiche produit
    impression_demandee = Signal(str)  # transaction_id
    annulation_demandee = Signal(str)  # transaction_id

    def __init__(
        self, viewmodel=None, detachee: bool = False, parent=None
    ):  # ← parent=None par défaut
        super().__init__(parent)
        self.viewmodel = viewmodel
        self._transaction_id = None
        self._client_id = None
        self._detachee = detachee
        self._fenetre_det = None
        self._symbole = "€"
        self._construire_ui()

    # ──────────────────────────────────────────────────────────────────
    # Construction
    # ──────────────────────────────────────────────────────────────────

    def _construire_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # Barre navigation
        barre = QHBoxLayout()
        barre.setContentsMargins(24, 14, 24, 6)

        if not self._detachee:
            self.btn_retour = QPushButton("← Retour")
            self.btn_retour.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_retour.setStyleSheet(
                f"QPushButton {{ background: none; border: none; color: {_B_PROFOND}; "
                f"font-size: 12pt; font-weight: 600; padding: 6px 0; }}"
                f"QPushButton:hover {{ color: {_B_NUIT}; }}"
            )
            self.btn_retour.clicked.connect(self.retour_demande.emit)
            barre.addWidget(self.btn_retour)
            barre.addStretch()

            self.btn_detacher = QPushButton("⤢  Ouvrir dans une fenêtre")
            self.btn_detacher.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_detacher.setStyleSheet(
                f"QPushButton {{ background: none; border: 1.5px solid {_B_PALE}; "
                f"color: {_B_PROFOND}; border-radius: 10px; "
                f"font-size: 9pt; font-weight: 600; padding: 5px 14px; }}"
                f"QPushButton:hover {{ background: {_B_GLACE}; border-color: {_B_CLAIR}; }}"
            )
            self.btn_detacher.clicked.connect(self._ouvrir_fenetre)
            barre.addWidget(self.btn_detacher)
        else:
            barre.addStretch()

        layout_principal.addLayout(barre)

        # Scroll area
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
        self._build_chips()
        self._build_articles()
        self._build_recapitulatif()
        self._build_infos()
        self._build_footer()

        self.layout_contenu.addStretch()
        scroll.setWidget(self.conteneur)
        layout_principal.addWidget(scroll)

    # ------------------------------------------------------------------

    def _build_header(self):
        self.header_frame = QFrame()
        self.header_frame.setMinimumHeight(200)
        self.header_frame.setStyleSheet(
            "QFrame {"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            f"    stop:0 {_B_NUIT}, stop:0.45 {_B_PROFOND}, stop:1 {_B_CLAIR});"
            "  border-radius: 20px;"
            "}"
        )
        self.header_frame.setGraphicsEffect(_shadow(28, 8, 90, _B_NUIT))

        outer = QVBoxLayout(self.header_frame)
        outer.setContentsMargins(30, 22, 30, 22)
        outer.setSpacing(0)

        # Ligne haute : avatar + nom client + badge statut
        top = QHBoxLayout()
        top.setSpacing(14)

        self._lbl_avatar = QLabel("👤")
        self._lbl_avatar.setFixedSize(64, 64)
        self._lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_avatar.setStyleSheet(
            "font-size: 22pt; background: rgba(255,255,255,0.18); "
            "border-radius: 32px; border: 2.5px solid rgba(255,255,255,0.35);"
        )
        top.addWidget(self._lbl_avatar, alignment=Qt.AlignmentFlag.AlignVCenter)

        col_txt = QVBoxLayout()
        col_txt.setSpacing(3)

        self.label_client = QLabel()
        self.label_client.setCursor(Qt.CursorShape.PointingHandCursor)
        self.label_client.setStyleSheet(
            "font-size: 18pt; font-weight: 800; color: white; border: none; background: none;"
        )
        self.label_client.mousePressEvent = lambda e: (
            self.client_demande.emit(self._client_id) if self._client_id else None
        )
        col_txt.addWidget(self.label_client)

        self._lbl_ref = QLabel()
        self._lbl_ref.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._lbl_ref.setStyleSheet(
            "font-size: 9pt; color: rgba(255,255,255,0.60); letter-spacing: 1px; "
            "border: none; background: none;"
        )
        col_txt.addWidget(self._lbl_ref)
        col_txt.addStretch()
        top.addLayout(col_txt)
        top.addStretch()

        # Badge statut
        self.label_statut = QLabel()
        self.label_statut.setStyleSheet(
            "font-size: 10pt; font-weight: 700; color: white; border: none; "
            "background: rgba(255,255,255,0.22); border-radius: 14px; padding: 5px 16px;"
        )
        top.addWidget(self.label_statut, alignment=Qt.AlignmentFlag.AlignTop)
        outer.addLayout(top)

        outer.addStretch()

        # Ligne basse : total hero + date badge
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
        lbl_sous = QLabel("montant total TTC")
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
        col_date.setSpacing(4)

        self.label_date = QLabel()
        self.label_date.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.label_date.setStyleSheet(
            "font-size: 11pt; font-weight: 600; color: white; border: none; "
            "background: rgba(255,255,255,0.20); border-radius: 12px; padding: 5px 14px;"
        )
        col_date.addWidget(self.label_date)

        self.btn_copier_id = QPushButton("📋 Copier l'ID")
        self.btn_copier_id.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copier_id.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.14); color: white; "
            "border: 1.5px solid rgba(255,255,255,0.30); border-radius: 10px; "
            "font-size: 8pt; font-weight: 600; padding: 4px 12px; }"
            "QPushButton:hover { background: rgba(255,255,255,0.26); }"
        )
        self.btn_copier_id.clicked.connect(self._copier_id)
        col_date.addWidget(self.btn_copier_id, alignment=Qt.AlignmentFlag.AlignRight)
        bas.addLayout(col_date)
        outer.addLayout(bas)

        self.layout_contenu.addWidget(self.header_frame)

    # ------------------------------------------------------------------

    def _build_actions(self):
        self._frame_actions = QFrame()
        self._frame_actions.setStyleSheet(
            f"QFrame {{ background: {_B_GLACE}; border: 1.5px solid {_B_PALE}; border-radius: 12px; }}"
        )
        row = QHBoxLayout(self._frame_actions)
        row.setContentsMargins(16, 10, 16, 10)
        row.setSpacing(10)

        self.btn_voir_client = _ActionBtn("👤", "Voir le client", _B_PROFOND)
        self.btn_voir_client.clicked.connect(
            lambda: (
                self.client_demande.emit(self._client_id) if self._client_id else None
            )
        )
        row.addWidget(self.btn_voir_client)

        self.btn_imprimer = _ActionBtn("🖨", "Imprimer", _B_ACCENT)
        self.btn_imprimer.clicked.connect(
            lambda: (
                self.impression_demandee.emit(self._transaction_id)
                if self._transaction_id
                else None
            )
        )
        row.addWidget(self.btn_imprimer)

        row.addStretch()

        self.btn_annuler = _ActionBtn("✕", "Annuler la vente", _B_NUIT)
        self.btn_annuler.clicked.connect(self._on_annuler)
        row.addWidget(self.btn_annuler)

        self.layout_contenu.addWidget(self._frame_actions)

    def mettre_a_jour_mode(self, mode_admin: bool) -> None:
        """Cache/montre les boutons d'action selon le mode."""
        self._frame_actions.setVisible(mode_admin)

    # ------------------------------------------------------------------

    def _build_chips(self):
        row = QHBoxLayout()
        row.setSpacing(10)
        self._chip_articles = _InfoChip("📦", "Articles", "—")
        self._chip_paiement = _InfoChip("💳", "Paiement", "—")
        self._chip_vendeur = _InfoChip("👤", "Vendeur", "—")
        row.addWidget(self._chip_articles)
        row.addWidget(self._chip_paiement)
        row.addWidget(self._chip_vendeur)
        self.layout_contenu.addLayout(row)

    # ------------------------------------------------------------------

    def _build_articles(self):
        self._articles_card = _SectionCard()
        lay = QVBoxLayout(self._articles_card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        header_row = QHBoxLayout()
        lbl_t = QLabel("📦  Articles")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        header_row.addWidget(lbl_t)
        header_row.addStretch()

        # En-tête colonnes
        for txt, w in [("Qté", 42), ("P.U.", 80), ("Sous-total", 90)]:
            lbl = QLabel(txt)
            lbl.setFixedWidth(w)
            lbl.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            lbl.setStyleSheet(
                f"font-size: 8pt; font-weight: 600; letter-spacing: 1px; "
                f"color: {_B_ARDOISE}; border: none; background: transparent;"
            )
            header_row.addWidget(lbl)
        header_row.addSpacing(14)

        lay.addLayout(header_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {_B_PALE}; border: none;")
        lay.addWidget(sep)

        self._articles_layout = QVBoxLayout()
        self._articles_layout.setSpacing(6)
        lay.addLayout(self._articles_layout)

        self.layout_contenu.addWidget(self._articles_card)

    # ------------------------------------------------------------------

    def _build_recapitulatif(self):
        self._recap_card = _SectionCard()
        lay = QVBoxLayout(self._recap_card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(8)

        lbl_t = QLabel("🧾  Récapitulatif")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)
        lay.addWidget(_HLine())

        self._recap_layout = QVBoxLayout()
        self._recap_layout.setSpacing(6)
        lay.addLayout(self._recap_layout)

        self.layout_contenu.addWidget(self._recap_card)

    # ------------------------------------------------------------------

    def _build_infos(self):
        self._infos_card = _SectionCard()
        lay = QVBoxLayout(self._infos_card)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(10)

        lbl_t = QLabel("ℹ  Informations complémentaires")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)
        lay.addWidget(_HLine())

        self._infos_layout = QVBoxLayout()
        self._infos_layout.setSpacing(8)
        lay.addLayout(self._infos_layout)

        self._infos_card.hide()
        self.layout_contenu.addWidget(self._infos_card)

    # ------------------------------------------------------------------

    def _build_footer(self):
        row = QHBoxLayout()
        self.label_footer = QLabel()
        self.label_footer.setStyleSheet(
            f"font-size: 10pt; color: {_B_ARDOISE}; border: none;"
        )
        row.addWidget(self.label_footer, alignment=Qt.AlignmentFlag.AlignVCenter)
        row.addStretch()
        self.layout_contenu.addLayout(row)

    # ══════════════════════════════════════════════════════════════════
    # Chargement
    # ══════════════════════════════════════════════════════════════════

    def charger_vente(self, transaction_id: str):
        """Charge et affiche les détails d'une transaction."""
        if not self.viewmodel:
            return
        data = self.viewmodel.obtenir_transaction(transaction_id)
        if not data:
            return

        self._transaction_id = transaction_id
        client = data.get("client") or {}
        articles = data.get("articles") or []
        total = float(data.get("total") or 0.0)
        code_promo = data.get("code_promo")

        # ── Header ──────────────────────────────────────────────────
        nom = (client.get("nom") or "").upper()
        prenom = client.get("prenom") or ""
        nom_complet = f"{nom} {prenom}".strip()
        self.label_client.setText(nom_complet if nom_complet else "Client inconnu")
        self._client_id = client.get("id")

        # Avatar
        initiales = (
            "".join(p[0].upper() for p in nom_complet.split()[:2])
            if nom_complet
            else "?"
        )
        self._lbl_avatar.setText(initiales)
        self._lbl_avatar.setStyleSheet(
            f"font-size: 14pt; font-weight: 800; color: white; "
            f"background: rgba(255,255,255,0.20); border-radius: 32px; "
            f"border: 2.5px solid rgba(255,255,255,0.35);"
        )

        self._lbl_ref.setText(f"VENTE · {str(transaction_id).upper()}")
        self.label_total.setText(f"{total:.2f} {self._symbole}")

        date_raw = str(data.get("date_vente") or "")
        date_str = date_raw[:10]
        heure_str = date_raw[11:16] if len(date_raw) > 10 else ""
        if date_str and heure_str:
            self.label_date.setText(f"🗓  {date_str}  ·  🕐 {heure_str}")
        elif date_str:
            self.label_date.setText(f"🗓  {date_str}")
        else:
            self.label_date.setText("—")

        # Badge statut
        statut = self._determiner_statut(data)
        self.label_statut.setText(statut["texte"])
        self._appliquer_style_statut(statut["cle"])

        # ── Chips ────────────────────────────────────────────────────
        self._chip_articles.set_valeur(
            f"{len(articles)} article{'s' if len(articles) > 1 else ''}"
        )
        moyen = data.get("moyen_paiement") or "—"
        self._chip_paiement.set_valeur(moyen)
        vendeur = data.get("vendeur") or data.get("utilisateur") or "—"
        self._chip_vendeur.set_valeur(str(vendeur))

        # ── Articles ─────────────────────────────────────────────────
        while self._articles_layout.count():
            item = self._articles_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, art in enumerate(articles):
            self._articles_layout.addWidget(
                _LigneArticle(
                    art,
                    self._symbole,
                    i,
                    on_produit_click=lambda pid: self.produit_demande.emit(pid),
                )
            )

        # ── Récapitulatif ────────────────────────────────────────────
        self._remplir_recapitulatif(articles, total, code_promo)

        # ── Informations complémentaires ─────────────────────────────
        self._remplir_infos(data, client, code_promo)

        # ── Boutons d'action ─────────────────────────────────────────
        self.btn_voir_client.setEnabled(bool(self._client_id))
        annule = statut["cle"] == "annulee"
        self.btn_annuler.setEnabled(not annule)
        if annule:
            self.btn_annuler.setStyleSheet(
                f"QPushButton {{ background: {_B_GLACE}; color: {_B_ARDOISE}; "
                f"border: 1.5px solid {_B_PALE}; border-radius: 10px; "
                f"font-size: 10pt; padding: 8px 16px; }}"
            )

        # ── Footer ───────────────────────────────────────────────────
        date_c = data.get("date_creation") or date_str
        self.label_footer.setText(
            f"🗓  Enregistrée le {str(date_c)[:10]}" if date_c else ""
        )

    # ------------------------------------------------------------------

    def _remplir_recapitulatif(self, articles: list, total: float, code_promo):
        while self._recap_layout.count():
            item = self._recap_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Calcul sous-total brut
        sous_total = sum(
            float(
                a.get("prix_total")
                or (float(a.get("prix_unitaire") or 0) * int(a.get("quantite") or 0))
            )
            for a in articles
        )

        self._recap_layout.addWidget(
            self._ligne_recap(
                "Sous-total", f"{sous_total:.2f} {self._symbole}", gras=False
            )
        )

        if code_promo:
            code_txt = code_promo.get("code") or ""
            pct = code_promo.get("pourcentage") or 0
            montant = code_promo.get("montant_reduction") or (sous_total * pct / 100)
            badge = QFrame()
            badge.setStyleSheet("border: none; background: transparent;")
            badge_row = QHBoxLayout(badge)
            badge_row.setContentsMargins(0, 0, 0, 0)
            badge_row.setSpacing(8)

            lbl_code = QLabel(f"🏷  Code promo : {code_txt}")
            lbl_code.setStyleSheet(
                f"font-size: 10pt; color: {_B_ARDOISE}; border: none; background: none;"
            )
            badge_row.addWidget(lbl_code)

            pill = QLabel(f"-{pct}%" if pct else f"-{montant:.2f} {self._symbole}")
            pill.setStyleSheet(
                f"font-size: 9pt; font-weight: 700; color: {_B_ACCENT}; "
                f"background: {_B_GLACE}; border-radius: 8px; padding: 2px 10px; border: none;"
            )
            badge_row.addWidget(pill)
            badge_row.addStretch()

            lbl_val = QLabel(f"−{float(montant):.2f} {self._symbole}")
            lbl_val.setStyleSheet(
                f"font-size: 10pt; font-weight: 600; color: {_B_ACCENT}; "
                f"border: none; background: none;"
            )
            badge_row.addWidget(lbl_val)
            self._recap_layout.addWidget(badge)

        # Séparateur tirets
        self._recap_layout.addWidget(_HLine(dashed=True))

        # Ligne total mise en valeur
        total_frame = QFrame()
        total_frame.setStyleSheet(
            f"QFrame {{ background: {_B_PROFOND}; border-radius: 12px; }}"
        )
        trow = QHBoxLayout(total_frame)
        trow.setContentsMargins(16, 12, 16, 12)
        lbl_total_t = QLabel("TOTAL")
        lbl_total_t.setStyleSheet(
            "font-size: 11pt; font-weight: 700; color: rgba(255,255,255,0.85); "
            "border: none; background: none; letter-spacing: 2px;"
        )
        trow.addWidget(lbl_total_t)
        trow.addStretch()
        lbl_total_v = QLabel(f"{total:.2f} {self._symbole}")
        lbl_total_v.setStyleSheet(
            "font-size: 16pt; font-weight: 900; color: white; border: none; background: none;"
        )
        trow.addWidget(lbl_total_v)
        self._recap_layout.addWidget(total_frame)

    def _ligne_recap(self, label: str, valeur: str, gras: bool = False) -> QFrame:
        f = QFrame()
        f.setStyleSheet("border: none; background: transparent;")
        row = QHBoxLayout(f)
        row.setContentsMargins(0, 2, 0, 2)
        lbl_n = QLabel(label)
        lbl_n.setStyleSheet(
            f"font-size: 10pt; {'font-weight: 700;' if gras else ''} "
            f"color: {_B_ARDOISE}; border: none; background: none;"
        )
        row.addWidget(lbl_n)
        row.addStretch()
        lbl_v = QLabel(valeur)
        lbl_v.setStyleSheet(
            f"font-size: 10pt; {'font-weight: 700;' if gras else ''} "
            f"color: {_B_MARINE}; border: none; background: none;"
        )
        row.addWidget(lbl_v)
        return f

    def _remplir_infos(self, data: dict, client: dict, code_promo):
        while self._infos_layout.count():
            item = self._infos_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        lignes = []

        # Email client
        email = client.get("email") or ""
        if email:
            lignes.append(("✉  Email client", email))

        # Téléphone client
        tel = client.get("telephone") or ""
        if tel:
            lignes.append(("📞  Téléphone", tel))

        # Notes de la vente
        notes = (data.get("notes") or "").strip()
        if notes:
            lignes.append(("📝  Notes", notes))

        # Référence interne
        ref = data.get("reference") or data.get("ref_interne") or ""
        if ref:
            lignes.append(("🔖  Référence", str(ref)))

        if not lignes:
            self._infos_card.hide()
            return

        for lbl_txt, val_txt in lignes:
            row = QFrame()
            row.setStyleSheet(
                f"QFrame {{ background: white; border: 1.5px solid {_B_PALE}; "
                f"border-radius: 10px; }}"
            )
            rlay = QHBoxLayout(row)
            rlay.setContentsMargins(14, 10, 14, 10)
            rlay.setSpacing(12)
            lbl_k = QLabel(lbl_txt)
            lbl_k.setStyleSheet(
                f"font-size: 10pt; font-weight: 600; color: {_B_ARDOISE}; "
                f"border: none; background: none; min-width: 160px;"
            )
            rlay.addWidget(lbl_k)
            lbl_v = QLabel(val_txt)
            lbl_v.setWordWrap(True)
            lbl_v.setStyleSheet(
                f"font-size: 10pt; font-weight: 700; color: {_B_MARINE}; "
                f"border: none; background: none;"
            )
            rlay.addWidget(lbl_v)
            rlay.addStretch()
            self._infos_layout.addWidget(row)

        self._infos_card.show()

    # ──────────────────────────────────────────────────────────────────
    # Actions
    # ──────────────────────────────────────────────────────────────────

    def _copier_id(self):
        if not self._transaction_id:
            return
        QApplication.clipboard().setText(str(self._transaction_id))
        self.btn_copier_id.setText("✓ Copié !")
        QTimer.singleShot(2000, lambda: self.btn_copier_id.setText("📋 Copier l'ID"))

    def _on_annuler(self):
        if not self._transaction_id:
            return
        rep = QMessageBox.warning(
            self,
            "Annuler la vente",
            "Cette action est irréversible.\nConfirmer l'annulation de cette vente ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            self.annulation_demandee.emit(self._transaction_id)

    def _ouvrir_fenetre(self):
        if not self._transaction_id:
            return
        if self._fenetre_det and not self._fenetre_det.isVisible():
            self._fenetre_det = None
        if self._fenetre_det:
            self._fenetre_det.raise_()
            self._fenetre_det.activateWindow()
            return
        self._fenetre_det = _FicheVenteFenetre(self.viewmodel, self._transaction_id)
        self._fenetre_det.show()

    # ──────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────

    def _determiner_statut(self, data: dict) -> dict:
        s = (data.get("statut") or "").lower()
        if "annul" in s:
            return {"texte": "✕  Annulée", "cle": "annulee"}
        if "attente" in s or "pending" in s:
            return {"texte": "⏳  En attente", "cle": "attente"}
        if "rembours" in s:
            return {"texte": "↩  Remboursée", "cle": "remboursee"}
        return {"texte": "✓  Payée", "cle": "payee"}

    def _appliquer_style_statut(self, cle: str):
        alpha_map = {
            "payee": "rgba(255,255,255,0.26)",
            "attente": "rgba(144,202,249,0.40)",
            "annulee": "rgba(13, 71,161, 0.50)",
            "remboursee": "rgba(2, 136,209, 0.40)",
        }
        bg = alpha_map.get(cle, "rgba(255,255,255,0.22)")
        self.label_statut.setStyleSheet(
            f"font-size: 10pt; font-weight: 700; color: white; border: none; "
            f"background: {bg}; border-radius: 14px; padding: 5px 16px;"
        )


# ══════════════════════════════════════════════════════════════════════
# Fenêtre détachée
# ══════════════════════════════════════════════════════════════════════


class _FicheVenteFenetre(QWidget):
    """Fenêtre autonome affichant la fiche vente (sans retour ni détacher)."""

    def __init__(self, viewmodel, transaction_id: str, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Vente — Détail")
        self.resize(980, 840)
        self.setStyleSheet(f"background: {Couleurs.BLANC};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        barre = QHBoxLayout()
        barre.setContentsMargins(24, 14, 24, 6)
        barre.addStretch()
        btn_fermer = QPushButton("✕  Fermer")
        btn_fermer.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_fermer.setStyleSheet(
            f"QPushButton {{ background: none; border: 1.5px solid {_B_ARDOISE}; "
            f"color: {_B_ARDOISE}; border-radius: 10px; "
            f"font-size: 10pt; font-weight: 600; padding: 6px 16px; }}"
            f"QPushButton:hover {{ background: {_B_ARDOISE}; color: white; }}"
        )
        btn_fermer.clicked.connect(self.close)
        barre.addWidget(btn_fermer)
        layout.addLayout(barre)

        self._fiche = FicheVenteView(viewmodel, detachee=True)
        self._fiche.charger_vente(transaction_id)
        layout.addWidget(self._fiche)
