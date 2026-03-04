"""Vue détail d'un produit (fiche produit)."""

import logging

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout,
    QScrollArea,
    QProgressBar,
    QSizePolicy,
    QGraphicsDropShadowEffect,
    QMessageBox,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
    import matplotlib

    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    _MPL_OK = True
except ImportError:
    _MPL_OK = False

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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {_B_PALE}; border: none;")


class _SectionCard(QFrame):
    """Conteneur de section standard : fond glace, bordure pâle."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: {_B_GLACE}; "
            f"border: 1.5px solid {_B_PALE}; border-radius: 14px; }}"
        )


class _KpiCard(QFrame):
    """Carte KPI avec grande valeur colorée."""

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
            f"font-size: 24pt; font-weight: 800; color: {couleur}; border: none; background: none;"
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
    """Chip d'info : icône · TITRE grisé · Valeur grasse."""

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
        self._lbl_v.setStyleSheet(
            f"font-size: 11pt; font-weight: 700; color: {_B_MARINE}; "
            f"border: none; background: none;"
        )
        col.addWidget(self._lbl_v)
        row.addLayout(col)
        row.addStretch()

    def set_valeur(self, valeur: str):
        self._lbl_v.setText(valeur)


class _ActionBtn(QPushButton):
    """Bouton contour coloré → fond plein au hover."""

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

    def changer_couleur(self, couleur: str):
        self._couleur = couleur
        self._apply()


class _AttrRow(QFrame):
    """Ligne d'attribut nom · valeur avec fond blanc."""

    def __init__(self, nom: str, valeur: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: white; border: 1.5px solid {_B_PALE}; border-radius: 10px; }}"
        )
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(12)

        lbl_n = QLabel(nom)
        lbl_n.setFixedWidth(160)
        lbl_n.setStyleSheet(
            f"font-size: 10pt; font-weight: 600; color: {_B_ARDOISE}; border: none; background: none;"
        )
        row.addWidget(lbl_n)

        sep = QLabel("·")
        sep.setStyleSheet(
            f"color: {_B_PALE}; font-size: 14pt; border: none; background: none;"
        )
        row.addWidget(sep)

        lbl_v = QLabel(valeur)
        lbl_v.setWordWrap(True)
        lbl_v.setStyleSheet(
            f"font-size: 10pt; font-weight: 700; color: {_B_MARINE}; border: none; background: none;"
        )
        row.addWidget(lbl_v)
        row.addStretch()


class _LigneVente(QFrame):
    """Ligne compacte représentant une vente du produit."""

    def __init__(self, vente: dict, symbole: str = "€", parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: white; border: 1.5px solid {_B_PALE}; border-radius: 10px; }}"
            f"QFrame:hover {{ border-color: {_B_CLAIR}; background: {_B_GLACE}; }}"
        )
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(14)

        # Avatar client
        nom = vente.get("client_nom") or "?"
        initiales = "".join(p[0].upper() for p in nom.split()[:2]) or "?"
        lbl_av = QLabel(initiales)
        lbl_av.setFixedSize(36, 36)
        lbl_av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_av.setStyleSheet(
            f"background: {_B_GLACE}; color: {_B_PROFOND}; border-radius: 18px; "
            f"font-size: 10pt; font-weight: 700; border: 1.5px solid {_B_PALE};"
        )
        row.addWidget(lbl_av)

        col = QVBoxLayout()
        col.setSpacing(1)
        lbl_client = QLabel(nom)
        lbl_client.setStyleSheet(
            f"font-size: 10pt; font-weight: 700; color: {_B_MARINE}; border: none; background: none;"
        )
        col.addWidget(lbl_client)
        lbl_date = QLabel(str(vente.get("date", ""))[:10])
        lbl_date.setStyleSheet(
            f"font-size: 9pt; color: {_B_ARDOISE}; border: none; background: none;"
        )
        col.addWidget(lbl_date)
        row.addLayout(col)
        row.addStretch()

        # Badge quantité
        qte = vente.get("quantite") or 1
        lbl_qte = QLabel(f"×{qte}")
        lbl_qte.setStyleSheet(
            f"font-size: 9pt; color: {_B_ACCENT}; font-weight: 600; "
            f"background: {_B_GLACE}; border-radius: 6px; padding: 2px 8px; border: none;"
        )
        row.addWidget(lbl_qte)

        # Badge commande
        cid = vente.get("commande_id")
        if cid:
            lbl_cid = QLabel(f"#{cid}")
            lbl_cid.setStyleSheet(
                f"font-size: 9pt; color: {_B_ARDOISE}; font-weight: 500; "
                f"background: {_B_GLACE}; border-radius: 6px; padding: 2px 8px; border: none;"
            )
            row.addWidget(lbl_cid)

        # Montant
        montant = float(vente.get("montant") or vente.get("montant_total") or 0.0)
        lbl_m = QLabel(f"{montant:.2f} {symbole}")
        lbl_m.setStyleSheet(
            f"font-size: 10pt; font-weight: 700; color: {_B_MARINE}; border: none; background: none;"
        )
        row.addWidget(lbl_m)


# ══════════════════════════════════════════════════════════════════════
# Vue principale
# ══════════════════════════════════════════════════════════════════════


class FicheProduitView(QWidget):
    """Fiche détail d'un produit — design moderne, palette 100 % bleue."""

    retour_demande = Signal()
    edition_demandee = Signal(int)
    suppression_demandee = Signal(int)
    duplication_demandee = Signal(int)

    def __init__(
        self, viewmodel=None, detachee: bool = False, parent=None
    ):  # ← parent=None par défaut
        super().__init__(parent)
        self.viewmodel = viewmodel
        self._produit_id = None
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
        self._build_description()
        self._build_attributs()
        self._build_stats()
        self._build_graphique()
        self._build_ventes_recentes()
        self._build_footer()

        self.layout_contenu.addStretch()
        scroll.setWidget(self.conteneur)
        layout_principal.addWidget(scroll)

    # ------------------------------------------------------------------

    def _build_header(self):
        self.header_frame = QFrame()
        self.header_frame.setMinimumHeight(210)
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

        # Ligne principale
        main_row = QHBoxLayout()
        main_row.setSpacing(20)

        # Avatar produit (initiale du nom ou emoji)
        self._lbl_avatar = QLabel("📦")
        self._lbl_avatar.setFixedSize(78, 78)
        self._lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_avatar.setStyleSheet(
            "font-size: 28pt; background: rgba(255,255,255,0.18); "
            "border-radius: 39px; border: 3px solid rgba(255,255,255,0.35); color: white;"
        )
        main_row.addWidget(self._lbl_avatar, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Texte gauche
        col_txt = QVBoxLayout()
        col_txt.setSpacing(4)

        self.label_nom_produit = QLabel()
        self.label_nom_produit.setStyleSheet(
            "font-size: 20pt; font-weight: 800; color: white; border: none; background: none;"
        )
        col_txt.addWidget(self.label_nom_produit)

        self.label_categorie = QLabel()
        self.label_categorie.setStyleSheet(
            "font-size: 10pt; font-weight: 500; color: rgba(255,255,255,0.68); "
            "border: none; background: none;"
        )
        col_txt.addWidget(self.label_categorie)
        col_txt.addStretch()
        main_row.addLayout(col_txt)
        main_row.addStretch()

        # Prix hero (droite)
        col_prix = QVBoxLayout()
        col_prix.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        col_prix.setSpacing(2)

        self.label_prix = QLabel()
        self.label_prix.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.label_prix.setStyleSheet(
            "font-size: 32pt; font-weight: 900; color: white; border: none; background: none;"
        )
        col_prix.addWidget(self.label_prix)

        lbl_sous = QLabel("prix unitaire TTC")
        lbl_sous.setAlignment(Qt.AlignmentFlag.AlignRight)
        lbl_sous.setStyleSheet(
            "font-size: 8pt; color: rgba(255,255,255,0.52); letter-spacing: 1px; "
            "border: none; background: none;"
        )
        col_prix.addWidget(lbl_sous)
        main_row.addLayout(col_prix)
        outer.addLayout(main_row)

        outer.addStretch()

        # Ligne basse : bouton copier nom + badge stock
        bas_row = QHBoxLayout()
        bas_row.setSpacing(10)

        self.btn_copier_nom = QPushButton("📋 Copier le nom")
        self.btn_copier_nom.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copier_nom.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.15); color: white; "
            "border: 1.5px solid rgba(255,255,255,0.32); border-radius: 10px; "
            "font-size: 9pt; font-weight: 600; padding: 4px 12px; }"
            "QPushButton:hover { background: rgba(255,255,255,0.28); }"
        )
        self.btn_copier_nom.clicked.connect(self._copier_nom)
        bas_row.addWidget(self.btn_copier_nom)
        bas_row.addStretch()

        self.label_stock = QLabel()
        self.label_stock.setStyleSheet(
            "font-size: 10pt; font-weight: 700; color: white; border: none; "
            "background: rgba(255,255,255,0.22); border-radius: 14px; padding: 5px 16px;"
        )
        bas_row.addWidget(self.label_stock)
        outer.addLayout(bas_row)

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

        self.btn_modifier = _ActionBtn("✏", "Modifier", _B_PROFOND)
        self.btn_modifier.clicked.connect(
            lambda: (
                self.edition_demandee.emit(self._produit_id)
                if self._produit_id
                else None
            )
        )
        row.addWidget(self.btn_modifier)

        self.btn_dupliquer = _ActionBtn("⧉", "Dupliquer", _B_ACCENT)
        self.btn_dupliquer.clicked.connect(
            lambda: (
                self.duplication_demandee.emit(self._produit_id)
                if self._produit_id
                else None
            )
        )
        row.addWidget(self.btn_dupliquer)

        row.addStretch()

        self.btn_supprimer = _ActionBtn("🗑", "Supprimer", _B_NUIT)
        self.btn_supprimer.clicked.connect(self._on_supprimer)
        row.addWidget(self.btn_supprimer)

        self.layout_contenu.addWidget(self._frame_actions)

    def mettre_a_jour_mode(self, mode_admin: bool) -> None:
        """Cache/montre les boutons d'action selon le mode."""
        self._frame_actions.setVisible(mode_admin)

    # ------------------------------------------------------------------

    def _build_chips(self):
        row = QHBoxLayout()
        row.setSpacing(10)
        self._chip_cat = _InfoChip("📂", "Catégorie", "—")
        self._chip_ref = _InfoChip("🔖", "Référence", "—")
        row.addWidget(self._chip_cat)
        row.addWidget(self._chip_ref)
        self.layout_contenu.addLayout(row)

    # ------------------------------------------------------------------

    def _build_description(self):
        self._desc_card = _SectionCard()
        lay = QVBoxLayout(self._desc_card)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(8)

        lbl_t = QLabel("📄  Description")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)
        lay.addWidget(_HLine())

        self.label_description = QLabel()
        self.label_description.setWordWrap(True)
        self.label_description.setStyleSheet(
            f"font-size: 11pt; color: {_B_MARINE}; "
            f"border: none; background: transparent; line-height: 1.5;"
        )
        lay.addWidget(self.label_description)

        self._desc_card.hide()
        self.layout_contenu.addWidget(self._desc_card)

    # ------------------------------------------------------------------

    def _build_attributs(self):
        self._attr_card = _SectionCard()
        lay = QVBoxLayout(self._attr_card)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(8)

        lbl_t = QLabel("⚙  Caractéristiques")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)
        lay.addWidget(_HLine())

        self._attr_layout = QVBoxLayout()
        self._attr_layout.setSpacing(6)
        lay.addLayout(self._attr_layout)

        self._attr_card.hide()
        self.layout_contenu.addWidget(self._attr_card)

    # ------------------------------------------------------------------

    def _build_stats(self):
        self._stats_card = _SectionCard()
        lay = QVBoxLayout(self._stats_card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(14)

        lbl_t = QLabel("📊  Statistiques de vente")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)
        lay.addWidget(_HLine())

        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        self.kpi_nb_ventes = _KpiCard("Ventes", "0", _B_PROFOND)
        self.kpi_total_qte = _KpiCard("Quantité vendue", "0", _B_ACCENT)
        self.kpi_total_ca = _KpiCard("CA généré", "0.00 €", _B_CYAN)
        kpi_row.addWidget(self.kpi_nb_ventes)
        kpi_row.addWidget(self.kpi_total_qte)
        kpi_row.addWidget(self.kpi_total_ca)
        lay.addLayout(kpi_row)

        # Barre de stock (visible quand stock connu)
        self._stock_frame = QFrame()
        self._stock_frame.setStyleSheet("border: none; background: transparent;")
        sf = QVBoxLayout(self._stock_frame)
        sf.setContentsMargins(0, 4, 0, 0)
        sf.setSpacing(5)

        self._stock_label = QLabel()
        self._stock_label.setStyleSheet(
            f"font-size: 10pt; color: {_B_ARDOISE}; border: none;"
        )
        self._stock_bar = QProgressBar()
        self._stock_bar.setTextVisible(False)
        self._stock_bar.setFixedHeight(8)
        self._stock_bar.setStyleSheet(
            f"QProgressBar {{ background: {_B_PALE}; border-radius: 4px; border: none; }}"
            f"QProgressBar::chunk {{ background: {_B_PROFOND}; border-radius: 4px; }}"
        )
        sf.addWidget(self._stock_label)
        sf.addWidget(self._stock_bar)
        lay.addWidget(self._stock_frame)
        self._stock_frame.hide()

        self.layout_contenu.addWidget(self._stats_card)

    # ------------------------------------------------------------------

    def _build_graphique(self):
        self._graph_card = _SectionCard()
        lay = QVBoxLayout(self._graph_card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        lbl_t = QLabel("📈  Évolution des ventes")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)
        lay.addWidget(_HLine())

        if _MPL_OK:
            self._fig = Figure(figsize=(6, 2.4), dpi=100, facecolor="none")
            self._ax = self._fig.add_subplot(111)
            self._ax.set_facecolor("none")
            self._canvas = FigureCanvasQTAgg(self._fig)
            self._canvas.setStyleSheet("background: transparent;")
            self._canvas.setMinimumHeight(180)
            lay.addWidget(self._canvas)
        else:
            lbl_err = QLabel("⚠  matplotlib non disponible (pip install matplotlib)")
            lbl_err.setStyleSheet(
                f"color: {_B_ARDOISE}; font-size: 10pt; border: none;"
            )
            lay.addWidget(lbl_err)

        self._graph_card.hide()
        self.layout_contenu.addWidget(self._graph_card)

    # ------------------------------------------------------------------

    def _build_ventes_recentes(self):
        self._ventes_card = _SectionCard()
        lay = QVBoxLayout(self._ventes_card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        header_row = QHBoxLayout()
        lbl_t = QLabel("🛒  Dernières ventes")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        header_row.addWidget(lbl_t)
        header_row.addStretch()
        self._lbl_nb_ventes = QLabel()
        self._lbl_nb_ventes.setStyleSheet(
            f"font-size: 9pt; color: {_B_ARDOISE}; border: none; background: transparent;"
        )
        header_row.addWidget(self._lbl_nb_ventes)
        lay.addLayout(header_row)
        lay.addWidget(_HLine())

        self._ventes_layout = QVBoxLayout()
        self._ventes_layout.setSpacing(6)
        lay.addLayout(self._ventes_layout)

        self._ventes_card.hide()
        self.layout_contenu.addWidget(self._ventes_card)

    # ------------------------------------------------------------------

    def _build_footer(self):
        row = QHBoxLayout()
        self.label_date_creation = QLabel()
        self.label_date_creation.setStyleSheet(
            f"font-size: 10pt; color: {_B_ARDOISE}; border: none;"
        )
        row.addWidget(self.label_date_creation, alignment=Qt.AlignmentFlag.AlignVCenter)
        row.addStretch()
        self.layout_contenu.addLayout(row)

    # ══════════════════════════════════════════════════════════════════
    # Chargement
    # ══════════════════════════════════════════════════════════════════

    def set_symbole_monnaie(self, symbole: str):
        if symbole:
            self._symbole = symbole

    def charger_produit(self, produit_id: int):
        """Charge et affiche les détails d'un produit."""
        if not self.viewmodel:
            return
        produit = self.viewmodel.obtenir_produit(produit_id)
        if not produit:
            return

        self._produit_id = produit_id

        # Header
        nom = produit.get("nom") or ""
        self.label_nom_produit.setText(nom)

        # Avatar : initiale du nom
        if nom:
            initiale = nom[0].upper()
            self._lbl_avatar.setText(initiale)
            self._lbl_avatar.setStyleSheet(
                f"font-size: 28pt; font-weight: 800; color: white; "
                f"background: rgba(255,255,255,0.20); border-radius: 39px; "
                f"border: 3px solid rgba(255,255,255,0.35);"
            )
        else:
            self._lbl_avatar.setText("📦")

        cat = produit.get("categorie_nom") or "Sans catégorie"
        self.label_categorie.setText(cat)
        self._chip_cat.set_valeur(cat)

        ref = produit.get("reference") or produit.get("sku") or "—"
        self._chip_ref.set_valeur(ref)

        prix = produit.get("prix") or 0.0
        self.label_prix.setText(f"{float(prix):.2f} {self._symbole}")

        # Badge stock
        stock = int(produit.get("stock") or 0)
        self._mettre_a_jour_stock(stock)

        # Description
        desc = (produit.get("description") or "").strip()
        if desc:
            self.label_description.setText(desc)
            self._desc_card.show()
        else:
            self._desc_card.hide()

        # Attributs
        self._charger_attributs(produit_id)

        # Stats
        try:
            stats = self.viewmodel.obtenir_stats_ventes_produit(produit_id)
            nb = stats.get("nb_ventes", 0)
            qte = stats.get("total_qte", 0)
            ca = stats.get("total_ca", 0.0)
            self.kpi_nb_ventes.set_valeur(str(nb))
            self.kpi_total_qte.set_valeur(str(qte))
            self.kpi_total_ca.set_valeur(f"{float(ca):.2f} {self._symbole}")
        except Exception:
            pass

        # Barre stock (max estimé = 2 × stock courant ou 50 mini)
        if stock > 0:
            seuil = max(stock * 2, 50)
            pct = min(int(stock / seuil * 100), 100)
            chunk = (
                _B_ARDOISE if stock <= 5 else _B_ACCENT if stock <= 10 else _B_PROFOND
            )
            self._stock_bar.setMaximum(100)
            self._stock_bar.setValue(pct)
            self._stock_label.setText(
                f"Stock actuel : {stock} unité{'s' if stock > 1 else ''}"
            )
            self._stock_bar.setStyleSheet(
                f"QProgressBar {{ background: {_B_PALE}; border-radius: 4px; border: none; }}"
                f"QProgressBar::chunk {{ background: {chunk}; border-radius: 4px; }}"
            )
            self._stock_frame.show()
        else:
            self._stock_frame.hide()

        # Graphique
        self._charger_graphique(produit_id)

        # Dernières ventes
        self._charger_ventes(produit_id)

        # Date création
        date_c = produit.get("date_creation") or ""
        if date_c:
            self.label_date_creation.setText(f"🗓  Créé le {str(date_c)[:10]}")

    # ------------------------------------------------------------------

    def _mettre_a_jour_stock(self, stock: int):
        if stock > 10:
            texte = f"✓  En stock · {stock} unités"
            bg = "rgba(255,255,255,0.24)"
        elif stock > 0:
            texte = f"⚠  Stock faible · {stock} unité{'s' if stock > 1 else ''}"
            bg = f"rgba(2, 136, 209, 0.38)"  # _B_ACCENT semi-transparent
        else:
            texte = "✕  Rupture de stock"
            bg = f"rgba(13, 71, 161, 0.50)"  # _B_NUIT semi-transparent

        self.label_stock.setText(texte)
        self.label_stock.setStyleSheet(
            f"font-size: 10pt; font-weight: 700; color: white; border: none; "
            f"background: {bg}; border-radius: 14px; padding: 5px 16px;"
        )

    def _charger_attributs(self, produit_id: int):
        while self._attr_layout.count():
            item = self._attr_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        attributs = []
        try:
            attributs = self.viewmodel.obtenir_attributs_produit(produit_id) or []
        except Exception:
            pass

        if not attributs:
            self._attr_card.hide()
            return

        self._attr_card.show()
        for attr in attributs:
            nom = (attr.get("nom_attribut") or attr.get("nom") or "").strip()
            val = (attr.get("valeur") or "—").strip()
            if nom:
                self._attr_layout.addWidget(_AttrRow(nom, val))

    def _charger_graphique(self, produit_id: int):
        if not _MPL_OK:
            return
        historique = []
        try:
            historique = (
                self.viewmodel.obtenir_historique_ventes_produit(produit_id) or []
            )
        except Exception:
            pass

        if not historique:
            self._graph_card.hide()
            return

        jours = [str(r.get("jour", ""))[:10] for r in historique]
        qtes = [int(r.get("qte", 0)) for r in historique]

        self._ax.clear()
        self._ax.set_facecolor("none")

        x = list(range(len(jours)))
        self._ax.bar(
            x,
            qtes,
            color=_B_CLAIR,
            edgecolor=_B_PROFOND,
            linewidth=0.8,
            width=0.6,
            zorder=3,
        )

        # Aire remplie pour mettre en valeur la tendance
        self._ax.fill_between(x, qtes, alpha=0.12, color=_B_PROFOND, zorder=2)

        if len(qtes) >= 3:
            self._ax.plot(
                x,
                qtes,
                color=_B_NUIT,
                linewidth=1.4,
                linestyle="--",
                alpha=0.45,
                zorder=4,
            )

        self._ax.set_xticks(x)
        self._ax.set_xticklabels(
            [d[5:] for d in jours],
            rotation=30,
            ha="right",
            fontsize=7,
            color=_B_ARDOISE,
        )
        max_v = max(qtes) if qtes else 1
        self._ax.set_ylim(0, max_v * 1.25)
        self._ax.yaxis.set_tick_params(labelsize=7, labelcolor=_B_ARDOISE)
        self._ax.spines["left"].set_color(_B_PALE)
        self._ax.spines["bottom"].set_color(_B_PALE)
        self._ax.grid(axis="y", linestyle="--", alpha=0.4, color=_B_PALE, zorder=0)

        for i, v in enumerate(qtes):
            if v > 0:
                self._ax.text(
                    i,
                    v + 0.06,
                    str(v),
                    ha="center",
                    va="bottom",
                    fontsize=7,
                    color=_B_NUIT,
                    fontweight="bold",
                )

        self._fig.tight_layout(pad=0.5)
        self._canvas.draw()
        self._graph_card.show()

    def _charger_ventes(self, produit_id: int):
        while self._ventes_layout.count():
            item = self._ventes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        ventes = []
        try:
            if hasattr(self.viewmodel, "obtenir_dernieres_ventes_produit"):
                ventes = (
                    self.viewmodel.obtenir_dernieres_ventes_produit(produit_id) or []
                )
        except Exception:
            pass

        if not ventes:
            self._ventes_card.hide()
            return

        n = len(ventes)
        self._lbl_nb_ventes.setText(f"{n} vente{'s' if n > 1 else ''}")
        for v in ventes[:10]:
            self._ventes_layout.addWidget(_LigneVente(v, self._symbole))
        if n > 10:
            lbl_p = QLabel(f"+ {n - 10} vente(s) supplémentaire(s)…")
            lbl_p.setStyleSheet(
                f"font-size: 9pt; color: {_B_ARDOISE}; padding: 4px; border: none;"
            )
            self._ventes_layout.addWidget(lbl_p)

        self._ventes_card.show()

    # ──────────────────────────────────────────────────────────────────
    # Actions
    # ──────────────────────────────────────────────────────────────────

    def _copier_nom(self):
        txt = self.label_nom_produit.text()
        if not txt:
            return
        QApplication.clipboard().setText(txt)
        self.btn_copier_nom.setText("✓ Copié !")
        QTimer.singleShot(2000, lambda: self.btn_copier_nom.setText("📋 Copier le nom"))

    def _on_supprimer(self):
        if not self._produit_id:
            return
        rep = QMessageBox.warning(
            self,
            "Supprimer le produit",
            f"Supprimer « {self.label_nom_produit.text()} » ?\nCette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            self.suppression_demandee.emit(self._produit_id)

    def _ouvrir_fenetre(self):
        if not self._produit_id:
            return
        if self._fenetre_det and not self._fenetre_det.isVisible():
            self._fenetre_det = None
        if self._fenetre_det:
            self._fenetre_det.raise_()
            self._fenetre_det.activateWindow()
            return
        self._fenetre_det = _FicheProduitFenetre(self.viewmodel, self._produit_id)
        self._fenetre_det.show()


# ══════════════════════════════════════════════════════════════════════
# Fenêtre détachée
# ══════════════════════════════════════════════════════════════════════


class _FicheProduitFenetre(QWidget):
    """Fenêtre autonome affichant la fiche produit (sans retour ni détacher)."""

    def __init__(self, viewmodel, produit_id: int, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Produit — Détail")
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

        self._fiche = FicheProduitView(viewmodel, detachee=True)
        self._fiche.charger_produit(produit_id)
        layout.addWidget(self._fiche)
