"""Vue détail d'un code promotionnel (fiche code)."""

import logging
from datetime import date

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QProgressBar,
    QSizePolicy,
    QGraphicsDropShadowEffect,
    QMessageBox,
    QDateEdit,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer
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

from utils.styles import Couleurs, style_scroll_area, style_bouton

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# Palette bleue interne
# ══════════════════════════════════════════════════════════════════════

_B_NUIT = "#0D47A1"  # bleu nuit (très foncé)
_B_PROFOND = "#1565C0"  # bleu profond
_B_MEDIUM = "#1976D2"  # bleu standard
_B_VRAI = "#1E88E5"  # bleu vif
_B_CLAIR = "#42A5F5"  # bleu clair
_B_PALE = "#90CAF9"  # bleu pâle
_B_GLACE = "#E3F2FD"  # bleu très clair / fond
_B_ACCENT = "#0288D1"  # bleu accent (légèrement cyan)
_B_ARDOISE = "#546E7A"  # bleu-gris neutre (actions secondaires)
_B_MARINE = "#263238"  # quasi-noir bleuté (texte critique)


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


class _KpiCard(QFrame):
    """Carte KPI : grande valeur colorée + titre sous-jacent."""

    def __init__(self, titre: str, valeur: str, couleur: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: white; border: 1.5px solid {_B_PALE}; border-radius: 14px; }}"
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        col = QVBoxLayout(self)
        col.setContentsMargins(20, 20, 20, 20)
        col.setSpacing(6)
        col.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._lbl_v = QLabel(valeur)
        self._lbl_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_v.setStyleSheet(
            f"font-size: 28pt; font-weight: 800; color: {couleur}; border: none; background: none;"
        )
        col.addWidget(self._lbl_v)

        lbl_t = QLabel(titre)
        lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_t.setStyleSheet(
            f"font-size: 10pt; color: {_B_ARDOISE}; border: none; background: none;"
        )
        col.addWidget(lbl_t)

    def set_valeur(self, valeur: str):
        self._lbl_v.setText(valeur)


class _ActionBtn(QPushButton):
    """Bouton contour coloré → fond plein au hover."""

    def __init__(self, icone: str, texte: str, couleur: str, parent=None):
        super().__init__(f"{icone}  {texte}", parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(40)
        self._couleur = couleur
        self._appliquer()

    def _appliquer(self):
        self.setStyleSheet(
            f"QPushButton {{"
            f"  background: white; color: {self._couleur};"
            f"  border: 1.5px solid {self._couleur}; border-radius: 10px;"
            f"  font-size: 10pt; font-weight: 600; padding: 8px 18px;"
            f"}}"
            f"QPushButton:hover {{ background: {self._couleur}; color: white; }}"
        )

    def changer_couleur(self, couleur: str):
        self._couleur = couleur
        self._appliquer()


class _DateBlock(QFrame):
    """Bloc de date éditable inline avec calendrier popup."""

    date_changed = Signal(str)
    date_cleared = Signal()

    def __init__(self, label: str, couleur: str = None, parent=None):
        super().__init__(parent)
        self._couleur = couleur or _B_PROFOND
        self._editing = False
        self.setStyleSheet(
            f"QFrame {{ background: white; border: 1.5px solid {_B_PALE}; border-radius: 12px; }}"
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 12, 16, 12)
        row.setSpacing(12)

        icone = "📅" if "début" in label.lower() else "⏰"
        lbl_ico = QLabel(icone)
        lbl_ico.setStyleSheet("font-size: 14pt; border: none; background: none;")
        row.addWidget(lbl_ico)

        col = QVBoxLayout()
        col.setSpacing(2)
        lbl_t = QLabel(label.upper())
        lbl_t.setStyleSheet(
            f"font-size: 8pt; font-weight: 600; letter-spacing: 1px; "
            f"color: {_B_ARDOISE}; border: none; background: none;"
        )
        col.addWidget(lbl_t)
        self._lbl_val = QLabel("—")
        self._lbl_val.setStyleSheet(
            f"font-size: 11pt; font-weight: 700; color: {_B_MARINE}; "
            f"border: none; background: none;"
        )
        col.addWidget(self._lbl_val)
        row.addLayout(col)
        row.addStretch()

        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("dd/MM/yyyy")
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setStyleSheet(
            f"QDateEdit {{ border: 1.5px solid {self._couleur}; border-radius: 8px; "
            f"padding: 4px 8px; font-size: 10pt; background: white; "
            f"color: {_B_MARINE}; min-width: 110px; }}"
            f"QDateEdit::drop-down {{ border: none; width: 20px; }}"
        )
        self._date_edit.hide()
        row.addWidget(self._date_edit)

        self._btn_edit = QPushButton("✏ Modifier")
        self._btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_edit.clicked.connect(self._toggle_edit)
        self._style_modifier()
        row.addWidget(self._btn_edit)

        self._btn_clear = QPushButton("✕")
        self._btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_clear.setFixedSize(32, 32)
        self._btn_clear.setStyleSheet(
            f"QPushButton {{ background: none; border: 1.5px solid {_B_ARDOISE}; "
            f"border-radius: 8px; color: {_B_ARDOISE}; font-size: 10pt; font-weight: 700; }}"
            f"QPushButton:hover {{ background: {_B_ARDOISE}; color: white; }}"
        )
        self._btn_clear.clicked.connect(self._on_clear)
        self._btn_clear.hide()
        row.addWidget(self._btn_clear)

    def set_date(self, iso_str):
        if iso_str:
            txt = str(iso_str)[:10]
            self._lbl_val.setText(txt)
            try:
                d = date.fromisoformat(txt)
                self._date_edit.setDate(QDate(d.year, d.month, d.day))
            except ValueError:
                pass
            self._btn_clear.show()
        else:
            self._lbl_val.setText("—")
            self._date_edit.setDate(QDate.currentDate())
            self._btn_clear.hide()

    def _toggle_edit(self):
        self._editing = not self._editing
        if self._editing:
            self._date_edit.show()
            self._btn_edit.setText("✓ Appliquer")
            self._btn_edit.setStyleSheet(
                f"QPushButton {{ background: {_B_PROFOND}; border: 1.5px solid {_B_PROFOND}; "
                f"border-radius: 8px; color: white; font-size: 9pt; "
                f"font-weight: 600; padding: 4px 12px; }}"
                f"QPushButton:hover {{ background: {_B_NUIT}; }}"
            )
        else:
            iso = self._date_edit.date().toString("yyyy-MM-dd")
            self._lbl_val.setText(iso)
            self._date_edit.hide()
            self._style_modifier()
            self._btn_clear.show()
            self.date_changed.emit(iso)

    def _on_clear(self):
        self._lbl_val.setText("—")
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.hide()
        self._editing = False
        self._style_modifier()
        self._btn_clear.hide()
        self.date_cleared.emit()

    def _style_modifier(self):
        self._btn_edit.setText("✏ Modifier")
        self._btn_edit.setStyleSheet(
            f"QPushButton {{ background: none; border: 1.5px solid {self._couleur}; "
            f"border-radius: 8px; color: {self._couleur}; font-size: 9pt; "
            f"font-weight: 600; padding: 4px 12px; }}"
            f"QPushButton:hover {{ background: {self._couleur}; color: white; }}"
        )


class _LigneAchat(QFrame):
    """Ligne compacte représentant un achat utilisant le code."""

    def __init__(self, achat: dict, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: white; border: 1.5px solid {_B_PALE}; border-radius: 10px; }}"
            f"QFrame:hover {{ border-color: {_B_CLAIR}; background: {_B_GLACE}; }}"
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(14)

        # Avatar initiales client
        nom = achat.get("client_nom") or "?"
        initiales = "".join(p[0].upper() for p in nom.split()[:2]) or "?"
        lbl_avatar = QLabel(initiales)
        lbl_avatar.setFixedSize(36, 36)
        lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_avatar.setStyleSheet(
            f"background: {_B_GLACE}; color: {_B_PROFOND}; border-radius: 18px; "
            f"font-size: 10pt; font-weight: 700; border: 1.5px solid {_B_PALE};"
        )
        row.addWidget(lbl_avatar)

        # Nom + date
        col_client = QVBoxLayout()
        col_client.setSpacing(1)
        lbl_nom = QLabel(nom)
        lbl_nom.setStyleSheet(
            f"font-size: 10pt; font-weight: 700; color: {_B_MARINE}; border: none; background: none;"
        )
        col_client.addWidget(lbl_nom)
        date_str = str(achat.get("date", ""))[:10]
        lbl_date = QLabel(date_str)
        lbl_date.setStyleSheet(
            f"font-size: 9pt; color: {_B_ARDOISE}; border: none; background: none;"
        )
        col_client.addWidget(lbl_date)
        row.addLayout(col_client)
        row.addStretch()

        # Badge commande id
        commande_id = achat.get("commande_id")
        if commande_id:
            lbl_id = QLabel(f"#{commande_id}")
            lbl_id.setStyleSheet(
                f"font-size: 9pt; color: {_B_ACCENT}; font-weight: 600; "
                f"background: {_B_GLACE}; border-radius: 6px; padding: 2px 8px; border: none;"
            )
            row.addWidget(lbl_id)

        # Montants
        col_m = QVBoxLayout()
        col_m.setSpacing(1)
        col_m.setAlignment(Qt.AlignmentFlag.AlignRight)
        montant = achat.get("montant_total") or 0.0
        lbl_montant = QLabel(f"{montant:.2f} €")
        lbl_montant.setAlignment(Qt.AlignmentFlag.AlignRight)
        lbl_montant.setStyleSheet(
            f"font-size: 10pt; font-weight: 700; color: {_B_MARINE}; border: none; background: none;"
        )
        col_m.addWidget(lbl_montant)
        reduction = achat.get("montant_reduction") or 0.0
        lbl_red = QLabel(f"−{reduction:.2f} €")
        lbl_red.setAlignment(Qt.AlignmentFlag.AlignRight)
        lbl_red.setStyleSheet(
            f"font-size: 9pt; color: {_B_CLAIR}; font-weight: 600; border: none; background: none;"
        )
        col_m.addWidget(lbl_red)
        row.addLayout(col_m)


# ══════════════════════════════════════════════════════════════════════
# Vue principale
# ══════════════════════════════════════════════════════════════════════


class FicheCodeView(QWidget):
    """Fiche détail d'un code promotionnel."""

    retour_demande = Signal()
    edition_demande = Signal(int)
    activation_demandee = Signal(int, bool)
    suppression_demandee = Signal(int)
    date_debut_modifiee = Signal(int, str)
    date_fin_modifiee = Signal(int, str)

    def __init__(
        self, viewmodel=None, detachee: bool = False, parent=None
    ):  # ← parent=None par défaut
        super().__init__(parent)
        self.viewmodel = viewmodel
        self._code_id = None
        self._actif = True
        self._detachee = detachee
        self._fenetre_detachee = None
        self._construire_ui()

    # ──────────────────────────────────────────────────────────────────
    # Construction
    # ──────────────────────────────────────────────────────────────────

    def _construire_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # Barre de navigation (retour + détacher OU fermer)
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
            self.btn_detacher.clicked.connect(self._ouvrir_fenetre_detachee)
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
        self._build_dates()
        self._build_desc()
        self._build_stats()
        self._build_graphique()
        self._build_achats_recents()
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
        outer.setContentsMargins(32, 22, 32, 22)
        outer.setSpacing(0)

        # Ligne haute : code · copier · badge statut
        top = QHBoxLayout()
        top.setSpacing(10)

        self.label_code = QLabel()
        self.label_code.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.label_code.setStyleSheet(
            "font-size: 14pt; font-weight: 700; color: rgba(255,255,255,0.85); "
            "font-family: 'Courier New', monospace; letter-spacing: 3px; "
            "border: none; background: none;"
        )
        top.addWidget(self.label_code)

        self.btn_copier = QPushButton("📋 Copier")
        self.btn_copier.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copier.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.15); color: white; "
            "border: 1.5px solid rgba(255,255,255,0.35); border-radius: 10px; "
            "font-size: 9pt; font-weight: 600; padding: 4px 12px; }"
            "QPushButton:hover { background: rgba(255,255,255,0.28); }"
        )
        self.btn_copier.clicked.connect(self._copier_code)
        top.addWidget(self.btn_copier)
        top.addStretch()

        self.label_statut = QLabel()
        self.label_statut.setStyleSheet(
            "font-size: 10pt; font-weight: 700; color: white; border: none; "
            "background: rgba(255,255,255,0.20); border-radius: 14px; padding: 5px 16px;"
        )
        top.addWidget(self.label_statut, alignment=Qt.AlignmentFlag.AlignTop)
        outer.addLayout(top)

        outer.addStretch()

        # Réduction — hero
        self.label_reduction = QLabel()
        self.label_reduction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_reduction.setStyleSheet(
            "font-size: 54pt; font-weight: 900; color: white; border: none; background: none;"
        )
        outer.addWidget(self.label_reduction)

        sous = QLabel("CODE DE RÉDUCTION")
        sous.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sous.setStyleSheet(
            "font-size: 8pt; font-weight: 600; color: rgba(255,255,255,0.50); "
            "letter-spacing: 3px; border: none; background: none;"
        )
        outer.addWidget(sous)
        outer.addStretch()

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

        self.btn_toggle = _ActionBtn("⏸", "Désactiver", _B_ARDOISE)
        self.btn_toggle.clicked.connect(self._on_toggle_actif)
        row.addWidget(self.btn_toggle)

        row.addStretch()

        self.btn_modifier = _ActionBtn("✏", "Modifier", _B_PROFOND)
        self.btn_modifier.clicked.connect(
            lambda: self.edition_demande.emit(self._code_id) if self._code_id else None
        )
        row.addWidget(self.btn_modifier)

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
        self.chip_type = _InfoChip("🔖", "Type d'utilisation", "—")
        self.chip_usages = _InfoChip("🔁", "Utilisations", "0")
        row.addWidget(self.chip_type)
        row.addWidget(self.chip_usages)
        self.layout_contenu.addLayout(row)

    # ------------------------------------------------------------------

    def _build_dates(self):
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background: {_B_GLACE}; border: 1.5px solid {_B_PALE}; border-radius: 14px; }}"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        lbl_t = QLabel("Dates")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)
        lay.addWidget(_HLine())

        self._block_debut = _DateBlock("Date de début", _B_PROFOND)
        self._block_debut.date_changed.connect(
            lambda iso: (
                self.date_debut_modifiee.emit(self._code_id, iso)
                if self._code_id
                else None
            )
        )
        self._block_debut.date_cleared.connect(
            lambda: (
                self.date_debut_modifiee.emit(self._code_id, "")
                if self._code_id
                else None
            )
        )
        lay.addWidget(self._block_debut)

        self._block_fin = _DateBlock("Date d'expiration", _B_ACCENT)
        self._block_fin.date_changed.connect(
            lambda iso: (
                self.date_fin_modifiee.emit(self._code_id, iso)
                if self._code_id
                else None
            )
        )
        self._block_fin.date_cleared.connect(
            lambda: (
                self.date_fin_modifiee.emit(self._code_id, "")
                if self._code_id
                else None
            )
        )
        lay.addWidget(self._block_fin)

        self.layout_contenu.addWidget(frame)

    # ------------------------------------------------------------------

    def _build_desc(self):
        self._desc_frame = QFrame()
        self._desc_frame.setStyleSheet(
            f"QFrame {{ background: {_B_GLACE}; border: 1.5px solid {_B_PALE}; border-radius: 12px; }}"
        )
        lay = QVBoxLayout(self._desc_frame)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(6)

        lbl_t = QLabel("📝  Description")
        lbl_t.setStyleSheet(
            f"font-size: 11pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)

        self._lbl_desc = QLabel()
        self._lbl_desc.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._lbl_desc.setWordWrap(True)
        self._lbl_desc.setStyleSheet(
            f"font-size: 11pt; color: {_B_MARINE}; border: none; background: transparent;"
        )
        lay.addWidget(self._lbl_desc)
        self.layout_contenu.addWidget(self._desc_frame)
        self._desc_frame.hide()

    # ------------------------------------------------------------------

    def _build_stats(self):
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background: {_B_GLACE}; border: 1.5px solid {_B_PALE}; border-radius: 14px; }}"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(14)

        lbl_t = QLabel("Statistiques")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)
        lay.addWidget(_HLine())

        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        self.kpi_economie = _KpiCard("Économies générées", "0.00 €", _B_ACCENT)
        self.kpi_limite = _KpiCard("Limite d'utilisations", "∞", _B_ARDOISE)
        kpi_row.addWidget(self.kpi_economie)
        kpi_row.addWidget(self.kpi_limite)
        lay.addLayout(kpi_row)

        # Barre de progression (visible si limite définie)
        self._prog_frame = QFrame()
        self._prog_frame.setStyleSheet("border: none; background: transparent;")
        pf = QVBoxLayout(self._prog_frame)
        pf.setContentsMargins(0, 0, 0, 0)
        pf.setSpacing(5)
        self._prog_label = QLabel()
        self._prog_label.setStyleSheet(
            f"font-size: 10pt; font-weight: 500; color: {_B_ARDOISE}; border: none;"
        )
        self._prog_bar = QProgressBar()
        self._prog_bar.setTextVisible(False)
        self._prog_bar.setFixedHeight(8)
        self._prog_bar.setStyleSheet(
            f"QProgressBar {{ background: {_B_PALE}; border-radius: 4px; border: none; }}"
            f"QProgressBar::chunk {{ background: {_B_PROFOND}; border-radius: 4px; }}"
        )
        pf.addWidget(self._prog_label)
        pf.addWidget(self._prog_bar)
        lay.addWidget(self._prog_frame)
        self._prog_frame.hide()

        # Jours restants avant expiration
        self._lbl_expiration = QLabel()
        self._lbl_expiration.setStyleSheet(
            f"font-size: 10pt; color: {_B_ARDOISE}; border: none; background: transparent;"
        )
        self._lbl_expiration.hide()
        lay.addWidget(self._lbl_expiration)

        self.layout_contenu.addWidget(frame)

    # ------------------------------------------------------------------

    def _build_graphique(self):
        """Graphique d'utilisation dans le temps (matplotlib)."""
        self._graphique_frame = QFrame()
        self._graphique_frame.setStyleSheet(
            f"QFrame {{ background: {_B_GLACE}; border: 1.5px solid {_B_PALE}; border-radius: 14px; }}"
        )
        lay = QVBoxLayout(self._graphique_frame)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        lbl_t = QLabel("📈  Historique d'utilisation")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; border: none; background: transparent;"
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

        self._graphique_frame.hide()
        self.layout_contenu.addWidget(self._graphique_frame)

    # ------------------------------------------------------------------

    def _build_achats_recents(self):
        """Section listant les derniers achats utilisant ce code."""
        self._achats_frame = QFrame()
        self._achats_frame.setStyleSheet(
            f"QFrame {{ background: {_B_GLACE}; border: 1.5px solid {_B_PALE}; border-radius: 14px; }}"
        )
        lay = QVBoxLayout(self._achats_frame)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        header_row = QHBoxLayout()
        lbl_t = QLabel("🛒  Derniers achats")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        header_row.addWidget(lbl_t)
        header_row.addStretch()
        self._lbl_nb_achats = QLabel()
        self._lbl_nb_achats.setStyleSheet(
            f"font-size: 9pt; color: {_B_ARDOISE}; border: none; background: transparent;"
        )
        header_row.addWidget(self._lbl_nb_achats)
        lay.addLayout(header_row)
        lay.addWidget(_HLine())

        self._achats_contenu = QVBoxLayout()
        self._achats_contenu.setSpacing(6)
        lay.addLayout(self._achats_contenu)

        self._achats_frame.hide()
        self.layout_contenu.addWidget(self._achats_frame)

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

    def charger_code(self, code_id: int):
        """Charge et affiche les détails d'un code promo."""
        if not self.viewmodel:
            return
        code = self.viewmodel.obtenir_code(code_id)
        if not code:
            return

        self._code_id = code_id
        self._actif = bool(code.get("actif", True))

        # Header
        self.label_code.setText(code.get("code", ""))
        self.label_reduction.setText(self._formater_reduction(code))
        statut = self._calculer_statut(code)
        self.label_statut.setText(statut["texte"])
        self._appliquer_style_statut(statut["cle"])
        self._mettre_a_jour_toggle()

        # Chips
        type_util = code.get("type_utilisation") or ""
        _libelle_util = {
            "illimite": "Illimité",
            "unique_par_client": "Unique / client",
            "limite_globale": "Limité",
        }
        libelle_type = _libelle_util.get(type_util, type_util or "—")
        self.chip_type.set_valeur(libelle_type)
        nb_util = code.get("nombre_utilisations") or 0
        self.chip_usages.set_valeur(str(nb_util))

        # Dates
        self._block_debut.set_date(code.get("date_debut"))
        self._block_fin.set_date(code.get("date_fin"))

        # Description
        desc = (code.get("description") or "").strip()
        if desc:
            self._lbl_desc.setText(desc)
            self._desc_frame.show()
        else:
            self._desc_frame.hide()

        # KPI stats
        limite = code.get("limite_utilisations")
        self.kpi_limite.set_valeur(str(limite) if limite else "∞")

        try:
            stats = self.viewmodel.obtenir_stats_code(code_id)
            if stats:
                economie = stats.get("total_economie") or 0.0
                self.kpi_economie.set_valeur(f"{economie:.2f} €")
        except Exception:
            pass

        # Barre de progression
        if limite and limite > 0:
            pct = min(int(nb_util / limite * 100), 100)
            chunk = _B_ARDOISE if pct >= 90 else _B_ACCENT if pct >= 70 else _B_PROFOND
            self._prog_bar.setMaximum(100)
            self._prog_bar.setValue(pct)
            self._prog_label.setText(f"Utilisation : {nb_util} / {limite}  ({pct} %)")
            self._prog_bar.setStyleSheet(
                f"QProgressBar {{ background: {_B_PALE}; border-radius: 4px; border: none; }}"
                f"QProgressBar::chunk {{ background: {chunk}; border-radius: 4px; }}"
            )
            self._prog_frame.show()
        else:
            self._prog_frame.hide()

        # Jours restants
        date_fin_str = code.get("date_fin") or ""
        if date_fin_str:
            try:
                d_fin = date.fromisoformat(str(date_fin_str)[:10])
                delta = (d_fin - date.today()).days
                if delta > 0:
                    couleur = _B_ACCENT if delta <= 7 else _B_ARDOISE
                    self._lbl_expiration.setText(
                        f"⏳  Expire dans {delta} jour{'s' if delta > 1 else ''}"
                    )
                    self._lbl_expiration.setStyleSheet(
                        f"font-size: 10pt; color: {couleur}; font-weight: 600; "
                        f"border: none; background: transparent;"
                    )
                    self._lbl_expiration.show()
                elif delta == 0:
                    self._lbl_expiration.setText("⚠  Expire aujourd'hui !")
                    self._lbl_expiration.setStyleSheet(
                        f"font-size: 10pt; color: {_B_NUIT}; font-weight: 700; "
                        f"border: none; background: transparent;"
                    )
                    self._lbl_expiration.show()
                else:
                    self._lbl_expiration.hide()
            except ValueError:
                self._lbl_expiration.hide()
        else:
            self._lbl_expiration.hide()

        # Graphique + achats
        self._charger_graphique(code_id)
        self._charger_achats(code_id)

        # Date création
        date_c = code.get("date_creation", "")
        if date_c:
            self.label_date_creation.setText(f"🗓  Créé le {str(date_c)[:10]}")

    # ------------------------------------------------------------------

    def _charger_graphique(self, code_id: int):
        if not _MPL_OK:
            return
        historique = []
        try:
            if hasattr(self.viewmodel, "obtenir_historique_utilisation"):
                historique = (
                    self.viewmodel.obtenir_historique_utilisation(code_id) or []
                )
        except Exception:
            pass

        if not historique:
            self._graphique_frame.hide()
            return

        dates = [str(h.get("date", ""))[:10] for h in historique]
        valeurs = [int(h.get("nb_utilisations", 0)) for h in historique]

        self._ax.clear()
        self._ax.set_facecolor("none")

        x = list(range(len(dates)))
        self._ax.bar(
            x,
            valeurs,
            color=_B_CLAIR,
            edgecolor=_B_PROFOND,
            linewidth=0.8,
            width=0.6,
            zorder=3,
        )

        # Ligne de tendance si assez de points
        if len(valeurs) >= 3:
            self._ax.plot(
                x,
                valeurs,
                color=_B_NUIT,
                linewidth=1.2,
                linestyle="--",
                alpha=0.5,
                zorder=4,
            )

        self._ax.set_xticks(x)
        self._ax.set_xticklabels(
            [d[5:] for d in dates],
            rotation=30,
            ha="right",
            fontsize=7,
            color=_B_ARDOISE,
        )
        max_v = max(valeurs) if valeurs else 1
        self._ax.set_ylim(0, max_v + 1)
        self._ax.yaxis.set_tick_params(labelsize=7, labelcolor=_B_ARDOISE)
        self._ax.spines["left"].set_color(_B_PALE)
        self._ax.spines["bottom"].set_color(_B_PALE)
        self._ax.grid(axis="y", linestyle="--", alpha=0.4, color=_B_PALE, zorder=0)

        for i, v in enumerate(valeurs):
            if v > 0:
                self._ax.text(
                    i,
                    v + 0.08,
                    str(v),
                    ha="center",
                    va="bottom",
                    fontsize=7,
                    color=_B_NUIT,
                    fontweight="bold",
                )

        self._fig.tight_layout(pad=0.5)
        self._canvas.draw()
        self._graphique_frame.show()

    def _charger_achats(self, code_id: int):
        while self._achats_contenu.count():
            item = self._achats_contenu.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        achats = []
        try:
            if hasattr(self.viewmodel, "obtenir_achats_code"):
                achats = self.viewmodel.obtenir_achats_code(code_id) or []
        except Exception:
            pass

        if not achats:
            self._achats_frame.hide()
            return

        n = len(achats)
        self._lbl_nb_achats.setText(f"{n} achat{'s' if n > 1 else ''}")

        for achat in achats[:10]:
            self._achats_contenu.addWidget(_LigneAchat(achat))

        if n > 10:
            lbl_plus = QLabel(f"+ {n - 10} achat(s) supplémentaire(s)…")
            lbl_plus.setStyleSheet(
                f"font-size: 9pt; color: {_B_ARDOISE}; padding: 4px; border: none;"
            )
            self._achats_contenu.addWidget(lbl_plus)

        self._achats_frame.show()

    # ──────────────────────────────────────────────────────────────────
    # Actions
    # ──────────────────────────────────────────────────────────────────

    def _ouvrir_fenetre_detachee(self):
        if not self._code_id:
            return
        if self._fenetre_detachee and not self._fenetre_detachee.isVisible():
            self._fenetre_detachee = None
        if self._fenetre_detachee:
            self._fenetre_detachee.raise_()
            self._fenetre_detachee.activateWindow()
            return
        self._fenetre_detachee = _FicheCodeFenetre(self.viewmodel, self._code_id)
        self._fenetre_detachee.show()
        # Retour automatique à la liste dans la fenêtre principale
        self.retour_demande.emit()

    def _copier_code(self):
        txt = self.label_code.text()
        if not txt:
            return
        QApplication.clipboard().setText(txt)
        self.btn_copier.setText("✓ Copié !")
        QTimer.singleShot(2000, lambda: self.btn_copier.setText("📋 Copier"))

    def _on_toggle_actif(self):
        if self._code_id is None:
            return
        verbe = "désactiver" if self._actif else "activer"
        rep = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous {verbe} ce code promotionnel ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            self._actif = not self._actif
            self._mettre_a_jour_toggle()
            self.activation_demandee.emit(self._code_id, self._actif)

    def _on_supprimer(self):
        if self._code_id is None:
            return
        rep = QMessageBox.warning(
            self,
            "Supprimer le code",
            "Cette action est irréversible.\nConfirmer la suppression ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            self.suppression_demandee.emit(self._code_id)

    def _mettre_a_jour_toggle(self):
        if self._actif:
            self.btn_toggle.setText("⏸  Désactiver")
            self.btn_toggle.changer_couleur(_B_ARDOISE)
        else:
            self.btn_toggle.setText("▶  Activer")
            self.btn_toggle.changer_couleur(_B_ACCENT)

    # ──────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────

    def _appliquer_style_statut(self, cle: str):
        alpha_map = {
            "actif": "rgba(255,255,255,0.26)",
            "inactif": "rgba(255,255,255,0.12)",
            "expire": "rgba(13,  71,161, 0.45)",
            "epuise": "rgba(144,202,249, 0.40)",
        }
        bg = alpha_map.get(cle, "rgba(255,255,255,0.20)")
        self.label_statut.setStyleSheet(
            f"font-size: 10pt; font-weight: 700; color: white; border: none; "
            f"background: {bg}; border-radius: 14px; padding: 5px 16px;"
        )

    def _calculer_statut(self, data: dict) -> dict:
        if not data.get("actif", True):
            return {"texte": "⏸ Inactif", "cle": "inactif"}
        date_fin_str = data.get("date_fin") or ""
        if date_fin_str:
            try:
                if date.fromisoformat(str(date_fin_str)[:10]) < date.today():
                    return {"texte": "✕ Expiré", "cle": "expire"}
            except ValueError:
                pass
        nb = data.get("nombre_utilisations") or 0
        limit = data.get("limite_utilisations")
        if limit and nb >= limit:
            return {"texte": "⚡ Épuisé", "cle": "epuise"}
        return {"texte": "✓ Actif", "cle": "actif"}

    def _formater_reduction(self, data: dict) -> str:
        valeur = data.get("pourcentage") or 0.0
        return f"-{valeur:.0f}%"


# ══════════════════════════════════════════════════════════════════════
# Fenêtre détachée  (définie APRÈS FicheCodeView)
# ══════════════════════════════════════════════════════════════════════


class _FicheCodeFenetre(QWidget):
    """Fenêtre autonome : même fiche, sans retour ni détacher, avec bouton Fermer."""

    def __init__(self, viewmodel, code_id: int, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Code promotionnel — Détail")
        self.resize(980, 840)
        self.setStyleSheet(f"background: {Couleurs.BLANC};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barre avec bouton fermer uniquement
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

        self._fiche = FicheCodeView(viewmodel, detachee=True)
        self._fiche.charger_code(code_id)
        layout.addWidget(self._fiche)
