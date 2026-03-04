"""Fiche profil client."""

import os
import logging
from datetime import datetime, date

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QFrame,
    QPushButton,
    QScrollArea,
    QGraphicsDropShadowEffect,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QPainter, QPainterPath, QColor

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

from utils.styles import Couleurs, style_groupe, style_scroll_area

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
    """Carte KPI avec grande valeur colorée et label sous-jacent."""

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
            f"font-size: 22pt; font-weight: 800; color: {couleur}; border: none; background: none;"
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


class _RelationCard(QFrame):
    """Card compacte pour une relation familiale avec avatar initiales."""

    def __init__(self, nom: str, role: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: white; border: 1.5px solid {_B_PALE}; border-radius: 10px; }}"
            f"QFrame:hover {{ border-color: {_B_CLAIR}; background: {_B_GLACE}; }}"
        )
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(12)

        initiales = "".join(p[0].upper() for p in nom.split()[:2]) or "?"
        lbl_av = QLabel(initiales)
        lbl_av.setFixedSize(38, 38)
        lbl_av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_av.setStyleSheet(
            f"background: {_B_GLACE}; color: {_B_PROFOND}; border-radius: 19px; "
            f"font-size: 11pt; font-weight: 700; border: 1.5px solid {_B_PALE};"
        )
        row.addWidget(lbl_av)

        col = QVBoxLayout()
        col.setSpacing(1)
        lbl_nom = QLabel(nom)
        lbl_nom.setStyleSheet(
            f"font-size: 10pt; font-weight: 700; color: {_B_MARINE}; border: none; background: none;"
        )
        col.addWidget(lbl_nom)
        lbl_role = QLabel(role)
        lbl_role.setStyleSheet(
            f"font-size: 9pt; color: {_B_ARDOISE}; border: none; background: none;"
        )
        col.addWidget(lbl_role)
        row.addLayout(col)
        row.addStretch()


class _LigneAchat(QFrame):
    """Ligne compacte pour un achat du client."""

    def __init__(self, achat: dict, symbole: str = "€", parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: white; border: 1.5px solid {_B_PALE}; border-radius: 10px; }}"
            f"QFrame:hover {{ border-color: {_B_CLAIR}; background: {_B_GLACE}; }}"
        )
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(14)

        lbl_ico = QLabel("🛒")
        lbl_ico.setStyleSheet("font-size: 13pt; border: none; background: none;")
        row.addWidget(lbl_ico)

        col = QVBoxLayout()
        col.setSpacing(1)
        produit = achat.get("produit") or achat.get("description") or "Achat"
        lbl_prod = QLabel(produit)
        lbl_prod.setStyleSheet(
            f"font-size: 10pt; font-weight: 700; color: {_B_MARINE}; border: none; background: none;"
        )
        col.addWidget(lbl_prod)
        date_str = str(achat.get("date", ""))[:10]
        lbl_date = QLabel(date_str)
        lbl_date.setStyleSheet(
            f"font-size: 9pt; color: {_B_ARDOISE}; border: none; background: none;"
        )
        col.addWidget(lbl_date)
        row.addLayout(col)
        row.addStretch()

        code = achat.get("code_promo")
        if code:
            lbl_code = QLabel(f"🏷 {code}")
            lbl_code.setStyleSheet(
                f"font-size: 9pt; color: {_B_ACCENT}; font-weight: 600; "
                f"background: {_B_GLACE}; border-radius: 6px; padding: 2px 8px; border: none;"
            )
            row.addWidget(lbl_code)

        montant = achat.get("montant") or achat.get("montant_total") or 0.0
        lbl_m = QLabel(f"{montant:.2f} {symbole}")
        lbl_m.setStyleSheet(
            f"font-size: 10pt; font-weight: 700; color: {_B_MARINE}; border: none; background: none;"
        )
        row.addWidget(lbl_m)


# ══════════════════════════════════════════════════════════════════════
# Vue principale
# ══════════════════════════════════════════════════════════════════════


class FicheClientView(QWidget):
    """
    Panneau de profil client — design moderne, palette 100 % bleue.
    API publique identique à l'original + 3 nouveaux signaux d'action.
    """

    email_demande = Signal(str)  # email du client
    commande_demandee = Signal(int)  # id client
    modification_demandee = Signal(int)  # id client

    def __init__(self, parent=None):
        super().__init__(parent)
        self._client_id: int = 0
        self._symbole_monnaie: str = "€"
        self._email_actuel: str = ""
        self._construire_ui()

    # ==================================================================
    # API publique (inchangée)
    # ==================================================================

    def set_symbole_monnaie(self, symbole: str):
        if symbole:
            self._symbole_monnaie = symbole

    def afficher_profil(self, profil: dict):
        """Met à jour l'ensemble de la vue avec les données du profil client."""
        self._client_id = profil.get("id", 0)

        # ── Header ──────────────────────────────────────────────────
        nom = (profil.get("nom") or "").upper()
        prenom = profil.get("prenom") or ""
        self._label_nom.setText(f"{nom} {prenom}".strip())
        self._afficher_photo_profil(profil.get("photo_path", ""))

        date_creation = profil.get("date_creation") or profil.get("date_ajout") or ""
        if date_creation:
            dt = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(date_creation, fmt)
                    break
                except ValueError:
                    continue
            self._label_client_depuis.setText(
                f"Client depuis le {dt.strftime('%d/%m/%Y')}" if dt else ""
            )
        else:
            self._label_client_depuis.setText("")

        # Chips de contact
        email = profil.get("email") or ""
        self._email_actuel = email
        tel = profil.get("telephone") or ""
        if email:
            self._chip_email.setText(f"✉  {email}")
            self._chip_email.show()
        else:
            self._chip_email.hide()
        if tel:
            self._chip_tel.setText(f"📞  {tel}")
            self._chip_tel.show()
        else:
            self._chip_tel.hide()

        # Complétude (barre colorée selon niveau)
        completude = self._calculer_completude(profil)
        self._barre_completude.setValue(completude)
        self._label_pourcent.setText(f"{completude} %")
        chunk = (
            _B_VRAI if completude >= 80 else _B_CLAIR if completude >= 50 else _B_PALE
        )
        self._barre_completude.setStyleSheet(
            "QProgressBar { background: rgba(255,255,255,0.25); border-radius: 4px; border: none; }"
            f"QProgressBar::chunk {{ background: {chunk}; border-radius: 4px; }}"
        )

        # Badge anniversaire
        dn = profil.get("date_naissance") or ""
        if dn:
            jours = self._jours_avant_anniversaire(str(dn))
            if jours is not None and jours <= 7:
                txt = (
                    f"🎂  Anniversaire dans {jours} jour{'s' if jours != 1 else ''} !"
                    if jours > 0
                    else "🎂  Anniversaire aujourd'hui !"
                )
                self._label_anniv.setText(txt)
                self._label_anniv.show()
            else:
                self._label_anniv.hide()
        else:
            self._label_anniv.hide()

        # Activation des boutons
        self._btn_email.setEnabled(bool(email))
        self._btn_commande.setEnabled(bool(self._client_id))
        self._btn_modifier.setEnabled(bool(self._client_id))

        # ── Sections ─────────────────────────────────────────────────
        self._remplir_infos(profil)
        self._remplir_relations(profil)
        self._remplir_stats(profil.get("stats") or {})
        self._remplir_graphique(profil.get("stats") or {})
        self._remplir_achats(profil.get("derniers_achats") or [])

    # ==================================================================
    # Construction UI
    # ==================================================================

    def _construire_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(style_scroll_area())

        self._conteneur = QWidget()
        self._conteneur.setStyleSheet(f"background: {Couleurs.BLANC};")
        self._layout_profil = QVBoxLayout(self._conteneur)
        self._layout_profil.setSpacing(14)
        self._layout_profil.setContentsMargins(16, 16, 16, 32)

        self._creer_section_entete()
        self._creer_section_actions()
        self._creer_section_infos()
        self._creer_section_relations()
        self._creer_section_stats()
        self._creer_section_graphiques()
        self._creer_section_achats()
        self._layout_profil.addStretch()

        scroll.setWidget(self._conteneur)
        root.addWidget(scroll)

    # ------------------------------------------------------------------

    def _creer_section_entete(self):
        self._header_card = QFrame()
        self._header_card.setMinimumHeight(200)
        self._header_card.setStyleSheet(
            "QFrame {"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            f"    stop:0 {_B_NUIT}, stop:0.45 {_B_PROFOND}, stop:1 {_B_CLAIR});"
            "  border-radius: 20px;"
            "}"
        )
        self._header_card.setGraphicsEffect(_shadow(26, 7, 85, _B_NUIT))

        outer = QVBoxLayout(self._header_card)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(12)

        # Ligne principale : photo + infos texte
        main_row = QHBoxLayout()
        main_row.setSpacing(22)

        self._label_photo_profil = QLabel()
        self._label_photo_profil.setFixedSize(88, 88)
        self._label_photo_profil.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label_photo_profil.setStyleSheet(
            "QLabel { background-color: rgba(255,255,255,0.18); border-radius: 44px; "
            "font-size: 34pt; color: white; border: 3px solid rgba(255,255,255,0.45); }"
        )
        self._label_photo_profil.setText("👤")
        main_row.addWidget(
            self._label_photo_profil, alignment=Qt.AlignmentFlag.AlignVCenter
        )

        col_texte = QVBoxLayout()
        col_texte.setSpacing(4)

        self._label_nom = QLabel()
        self._label_nom.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._label_nom.setStyleSheet(
            "font-size: 21pt; font-weight: 800; color: white; border: none; background: none;"
        )
        col_texte.addWidget(self._label_nom)

        self._label_client_depuis = QLabel()
        self._label_client_depuis.setStyleSheet(
            "font-size: 10pt; color: rgba(255,255,255,0.72); border: none; background: none;"
        )
        col_texte.addWidget(self._label_client_depuis)

        # Badge anniversaire (masqué par défaut)
        self._label_anniv = QLabel()
        self._label_anniv.setStyleSheet(
            "font-size: 9pt; font-weight: 700; color: white; "
            "background: rgba(255,255,255,0.22); border-radius: 12px; "
            "padding: 3px 12px; border: none;"
        )
        self._label_anniv.hide()
        col_texte.addWidget(self._label_anniv)

        # Chips de contact (email, téléphone)
        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)
        _chip_style = (
            "QPushButton { background: rgba(255,255,255,0.18); color: white; "
            "border: 1.5px solid rgba(255,255,255,0.35); border-radius: 12px; "
            "font-size: 9pt; font-weight: 500; padding: 4px 12px; }"
            "QPushButton:hover { background: rgba(255,255,255,0.30); }"
        )
        self._chip_email = QPushButton()
        self._chip_email.setCursor(Qt.CursorShape.PointingHandCursor)
        self._chip_email.setStyleSheet(_chip_style)
        self._chip_email.clicked.connect(
            lambda: (
                self.email_demande.emit(self._email_actuel)
                if self._email_actuel
                else None
            )
        )
        chips_row.addWidget(self._chip_email)

        self._chip_tel = QPushButton()
        self._chip_tel.setStyleSheet(_chip_style)
        chips_row.addWidget(self._chip_tel)
        chips_row.addStretch()
        col_texte.addLayout(chips_row)

        main_row.addLayout(col_texte)
        main_row.addStretch()
        outer.addLayout(main_row)

        # Barre de complétude
        comp_row = QHBoxLayout()
        comp_row.setSpacing(8)

        lbl_comp = QLabel("Complétude du profil")
        lbl_comp.setStyleSheet(
            "font-size: 8pt; color: rgba(255,255,255,0.68); border: none; background: none;"
        )
        comp_row.addWidget(lbl_comp)

        self._barre_completude = QProgressBar()
        self._barre_completude.setFixedHeight(8)
        self._barre_completude.setMaximum(100)
        self._barre_completude.setTextVisible(False)
        self._barre_completude.setStyleSheet(
            f"QProgressBar {{ background: rgba(255,255,255,0.22); border-radius: 4px; border: none; }}"
            f"QProgressBar::chunk {{ background: {_B_CLAIR}; border-radius: 4px; }}"
        )
        comp_row.addWidget(self._barre_completude)

        self._label_pourcent = QLabel("0 %")
        self._label_pourcent.setFixedWidth(38)
        self._label_pourcent.setStyleSheet(
            "font-size: 9pt; font-weight: 700; color: rgba(255,255,255,0.85); "
            "border: none; background: none;"
        )
        comp_row.addWidget(self._label_pourcent)

        outer.addLayout(comp_row)
        self._layout_profil.addWidget(self._header_card)

    # ------------------------------------------------------------------

    def _creer_section_actions(self):
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background: {_B_GLACE}; border: 1.5px solid {_B_PALE}; border-radius: 12px; }}"
        )
        row = QHBoxLayout(frame)
        row.setContentsMargins(16, 10, 16, 10)
        row.setSpacing(10)

        self._btn_email = _ActionBtn("✉", "Envoyer un email", _B_PROFOND)
        self._btn_email.clicked.connect(
            lambda: (
                self.email_demande.emit(self._email_actuel)
                if self._email_actuel
                else None
            )
        )
        row.addWidget(self._btn_email)

        self._btn_commande = _ActionBtn("🛒", "Nouvelle commande", _B_ACCENT)
        self._btn_commande.clicked.connect(
            lambda: (
                self.commande_demandee.emit(self._client_id)
                if self._client_id
                else None
            )
        )
        row.addWidget(self._btn_commande)

        row.addStretch()

        self._btn_modifier = _ActionBtn("✏", "Modifier le profil", _B_ARDOISE)
        self._btn_modifier.clicked.connect(
            lambda: (
                self.modification_demandee.emit(self._client_id)
                if self._client_id
                else None
            )
        )
        row.addWidget(self._btn_modifier)

        self._layout_profil.addWidget(frame)

    # ------------------------------------------------------------------

    def _creer_section_infos(self):
        # ── Informations personnelles ─────────────────────────────────
        self._frame_infos = _SectionCard()
        lay = QVBoxLayout(self._frame_infos)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        lbl_t = QLabel("👤  Informations personnelles")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)
        lay.addWidget(_HLine())

        self._layout_infos = QGridLayout()
        self._layout_infos.setHorizontalSpacing(20)
        self._layout_infos.setVerticalSpacing(10)
        self._layout_infos.setColumnStretch(1, 1)
        self._layout_infos.setColumnStretch(3, 1)
        lay.addLayout(self._layout_infos)
        self._layout_profil.addWidget(self._frame_infos)

        # ── Adresse ───────────────────────────────────────────────────
        self._frame_adresse = _SectionCard()
        lay_adr = QVBoxLayout(self._frame_adresse)
        lay_adr.setContentsMargins(20, 14, 20, 14)
        lay_adr.setSpacing(8)

        lbl_adr = QLabel("📍  Adresse")
        lbl_adr.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        lay_adr.addWidget(lbl_adr)
        lay_adr.addWidget(_HLine())

        self._lbl_adresse = QLabel()
        self._lbl_adresse.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._lbl_adresse.setWordWrap(True)
        self._lbl_adresse.setStyleSheet(
            f"font-size: 11pt; color: {_B_MARINE}; "
            f"border: none; background: transparent; line-height: 1.5;"
        )
        lay_adr.addWidget(self._lbl_adresse)
        self._frame_adresse.hide()
        self._layout_profil.addWidget(self._frame_adresse)

        # ── Centres d'intérêt ─────────────────────────────────────────
        self._frame_interets = _SectionCard()
        lay_int = QVBoxLayout(self._frame_interets)
        lay_int.setContentsMargins(20, 14, 20, 14)
        lay_int.setSpacing(10)

        lbl_int = QLabel("❤️  Centres d'intérêt")
        lbl_int.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        lay_int.addWidget(lbl_int)
        lay_int.addWidget(_HLine())

        wrap = QHBoxLayout()
        wrap.setSpacing(8)
        self._layout_interets = wrap
        lay_int.addLayout(wrap)
        self._frame_interets.hide()
        self._layout_profil.addWidget(self._frame_interets)

        # ── Notes ─────────────────────────────────────────────────────
        self._frame_notes = _SectionCard()
        lay_notes = QVBoxLayout(self._frame_notes)
        lay_notes.setContentsMargins(20, 14, 20, 14)
        lay_notes.setSpacing(8)

        lbl_notes = QLabel("📝  Notes")
        lbl_notes.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        lay_notes.addWidget(lbl_notes)
        lay_notes.addWidget(_HLine())

        self._label_notes = QLabel()
        self._label_notes.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._label_notes.setWordWrap(True)
        self._label_notes.setStyleSheet(
            f"font-size: 11pt; color: {_B_MARINE}; "
            f"border: none; background: transparent; line-height: 1.5;"
        )
        lay_notes.addWidget(self._label_notes)
        self._frame_notes.hide()
        self._layout_profil.addWidget(self._frame_notes)

    # ------------------------------------------------------------------

    def _creer_section_relations(self):
        self._frame_relations = _SectionCard()
        lay = QVBoxLayout(self._frame_relations)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        lbl_t = QLabel("👪  Relations")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)
        lay.addWidget(_HLine())

        self._layout_relations = QVBoxLayout()
        self._layout_relations.setSpacing(6)
        lay.addLayout(self._layout_relations)
        self._frame_relations.hide()
        self._layout_profil.addWidget(self._frame_relations)

    # ------------------------------------------------------------------

    def _creer_section_stats(self):
        self._frame_stats = _SectionCard()
        lay = QVBoxLayout(self._frame_stats)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(14)

        lbl_t = QLabel("📊  Statistiques d'achat")
        lbl_t.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {_B_PROFOND}; "
            f"border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)
        lay.addWidget(_HLine())

        self._layout_stats = QGridLayout()
        self._layout_stats.setSpacing(12)
        lay.addLayout(self._layout_stats)
        self._layout_profil.addWidget(self._frame_stats)

    # ------------------------------------------------------------------

    def _creer_section_graphiques(self):
        self._frame_graphiques = _SectionCard()
        lay = QVBoxLayout(self._frame_graphiques)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        lbl_t = QLabel("📈  Historique des dépenses")
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

        self._frame_graphiques.hide()
        self._layout_profil.addWidget(self._frame_graphiques)

    # ------------------------------------------------------------------

    def _creer_section_achats(self):
        self._frame_achats = _SectionCard()
        lay = QVBoxLayout(self._frame_achats)
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

        self._layout_achats = QVBoxLayout()
        self._layout_achats.setSpacing(6)
        lay.addLayout(self._layout_achats)
        self._frame_achats.hide()
        self._layout_profil.addWidget(self._frame_achats)

    # ==================================================================
    # Remplissage
    # ==================================================================

    def _calculer_completude(self, profil: dict) -> int:
        from utils.profile_completion import calculer_completion

        return calculer_completion(profil)

    def _vider_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child is not None:
                self._vider_layout(child)

    def _remplir_infos(self, profil: dict):
        self._vider_layout(self._layout_infos)
        self._vider_layout(self._layout_interets)

        _ICONES = {
            "nom": "👤",
            "prenom": "👤",
            "date_naissance": "📅",
            "age": "🎂",
            "email": "✉",
            "telephone": "📞",
            "situation_maritale": "💍",
            "profession": "💼",
        }
        champs = list(_ICONES.keys())
        labels = {
            "nom": "Nom",
            "prenom": "Prénom",
            "date_naissance": "Naissance",
            "age": "Âge",
            "email": "Email",
            "telephone": "Téléphone",
            "situation_maritale": "Situation maritale",
            "profession": "Profession",
        }

        ligne, col = 0, 0
        for cle in champs:
            valeur = profil.get(cle)

            if cle == "age" and not valeur:
                dn = profil.get("date_naissance")
                if dn:
                    a = self._calculer_age(str(dn))
                    if a is not None:
                        valeur = f"{a} ans"

            if cle == "date_naissance" and valeur:
                valeur = self._formater_date(str(valeur))

            if cle == "nom" and valeur:
                valeur = str(valeur).upper()

            if valeur is None or str(valeur).strip() == "":
                continue

            ico = _ICONES.get(cle, "•")
            label = labels.get(cle, cle)

            lbl_k = QLabel(f"{ico}  {label}")
            lbl_k.setStyleSheet(
                f"font-size: 10pt; font-weight: 600; color: {_B_ARDOISE}; "
                f"border: none; background: transparent;"
            )
            lbl_v = QLabel(str(valeur))
            lbl_v.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl_v.setStyleSheet(
                f"font-size: 10pt; font-weight: 700; color: {_B_MARINE}; "
                f"border: none; background: transparent;"
            )
            lbl_v.setWordWrap(True)

            grid_col = col * 2  # 0 ou 2
            self._layout_infos.addWidget(lbl_k, ligne, grid_col)
            self._layout_infos.addWidget(lbl_v, ligne, grid_col + 1)

            if col == 0:
                col = 1
            else:
                col = 0
                ligne += 1

        if col == 1:
            ligne += 1  # flush dernière ligne incomplète

        # Adresse
        adresse = profil.get("adresse") or ""
        ville = profil.get("ville") or ""
        code_postal = profil.get("code_postal") or ""
        a_adresse = bool(adresse.strip() or ville.strip() or code_postal.strip())
        if a_adresse:
            parties = []
            if adresse.strip():
                parties.append(adresse.strip())
            ligne_v = f"{code_postal.strip()} {ville.strip()}".strip()
            if ligne_v:
                parties.append(ligne_v)
            self._lbl_adresse.setText("\n".join(parties))
            self._frame_adresse.show()
        else:
            self._frame_adresse.hide()

        # Centres d'intérêt (tags bleus)
        ci = profil.get("centre_interet") or ""
        if ci.strip():
            self._frame_interets.show()
            tags = [t.strip() for t in ci.replace(";", ",").split(",") if t.strip()]
            _COULEURS_TAGS = [
                _B_NUIT,
                _B_PROFOND,
                _B_MEDIUM,
                _B_VRAI,
                _B_CLAIR,
                _B_ACCENT,
                _B_ARDOISE,
                _B_CYAN,
            ]
            for i, tag in enumerate(tags):
                c = _COULEURS_TAGS[i % len(_COULEURS_TAGS)]
                lbl_tag = QLabel(tag)
                lbl_tag.setStyleSheet(
                    f"QLabel {{ background: {c}; color: white; "
                    f"padding: 5px 14px; border-radius: 14px; "
                    f"font-size: 10pt; font-weight: 600; border: none; }}"
                )
                self._layout_interets.addWidget(lbl_tag)
            self._layout_interets.addStretch()
        else:
            self._frame_interets.hide()

        # Notes
        notes = profil.get("notes_personnalisees") or ""
        if notes.strip():
            self._label_notes.setText(notes.strip())
            self._frame_notes.show()
        else:
            self._frame_notes.hide()

    def _remplir_relations(self, profil: dict):
        self._vider_layout(self._layout_relations)

        conjoint = profil.get("conjoint")
        enfants = profil.get("enfants") or []
        parents = profil.get("parents") or []

        a_relations = bool(conjoint or enfants or parents)
        self._frame_relations.setVisible(a_relations)
        if not a_relations:
            return

        if conjoint:
            nom_c = f"{(conjoint.get('nom') or '').upper()} {conjoint.get('prenom') or ''}".strip()
            self._layout_relations.addWidget(_RelationCard(nom_c, "Conjoint(e)"))

        for e in enfants:
            nom_e = f"{(e.get('nom') or '').upper()} {e.get('prenom') or ''}".strip()
            self._layout_relations.addWidget(_RelationCard(nom_e, "Enfant"))

        for p in parents:
            nom_p = f"{(p.get('nom') or '').upper()} {p.get('prenom') or ''}".strip()
            self._layout_relations.addWidget(_RelationCard(nom_p, "Parent"))

    def _remplir_stats(self, stats: dict):
        self._vider_layout(self._layout_stats)

        nombre_achats = stats.get("nombre_achats", 0)

        if nombre_achats == 0:
            lbl = QLabel("Aucun achat enregistré")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"color: {_B_ARDOISE}; font-style: italic; font-size: 12pt; "
                f"padding: 20px; border: none;"
            )
            self._layout_stats.addWidget(lbl, 0, 0, 1, 3)
            return

        montant_total = stats.get("montant_total", 0.0)
        produit_prefere = stats.get("produit_prefere") or "—"
        categorie_preferee = stats.get("categorie_preferee") or "—"
        dernier_achat = stats.get("dernier_achat") or "—"
        if dernier_achat and dernier_achat != "—":
            dernier_achat = self._formater_date(str(dernier_achat))

        self._layout_stats.addWidget(
            _KpiCard("Achats", str(nombre_achats), _B_PROFOND), 0, 0
        )
        self._layout_stats.addWidget(
            _KpiCard(
                "Total dépensé",
                f"{montant_total:.2f} {self._symbole_monnaie}",
                _B_ACCENT,
            ),
            0,
            1,
        )
        self._layout_stats.addWidget(
            _KpiCard("Produit favori", produit_prefere, _B_ARDOISE), 0, 2
        )
        self._layout_stats.addWidget(
            _KpiCard("Catégorie favorite", categorie_preferee, _B_ARDOISE), 1, 0
        )
        self._layout_stats.addWidget(
            _KpiCard("Dernier achat", dernier_achat, _B_MEDIUM), 1, 1
        )

    def _remplir_graphique(self, stats: dict):
        if not _MPL_OK:
            return

        historique = stats.get("historique_mensuel") or []
        if not historique:
            self._frame_graphiques.hide()
            return

        labels = [str(h.get("mois", ""))[:7] for h in historique]
        montants = [float(h.get("montant", 0)) for h in historique]

        self._ax.clear()
        self._ax.set_facecolor("none")

        x = list(range(len(labels)))
        self._ax.bar(
            x,
            montants,
            color=_B_CLAIR,
            edgecolor=_B_PROFOND,
            linewidth=0.8,
            width=0.6,
            zorder=3,
        )
        if len(montants) >= 3:
            self._ax.plot(
                x,
                montants,
                color=_B_NUIT,
                linewidth=1.2,
                linestyle="--",
                alpha=0.45,
                zorder=4,
            )

        self._ax.set_xticks(x)
        self._ax.set_xticklabels(
            [lb[5:] if len(lb) >= 7 else lb for lb in labels],
            rotation=30,
            ha="right",
            fontsize=7,
            color=_B_ARDOISE,
        )
        max_v = max(montants) if montants else 1
        self._ax.set_ylim(0, max_v * 1.22)
        self._ax.yaxis.set_tick_params(labelsize=7, labelcolor=_B_ARDOISE)
        self._fig.tight_layout(pad=0.4)
        self._canvas.draw()
        self._frame_graphiques.show()

    def _remplir_achats(self, achats: list):
        self._vider_layout(self._layout_achats)
        if not achats:
            self._frame_achats.hide()
            return
        self._lbl_nb_achats.setText(f"{len(achats)} achat(s)")
        for achat in achats:
            self._layout_achats.addWidget(_LigneAchat(achat, self._symbole_monnaie))
        self._frame_achats.show()

    def _afficher_photo_profil(self, photo_path: str):
        """Affiche la photo de profil ou l'emoji par défaut."""
        if photo_path and os.path.isfile(photo_path):
            pixmap = QPixmap(photo_path)
            if not pixmap.isNull():
                size = 88
                pixmap = pixmap.scaled(
                    size,
                    size,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                x = (pixmap.width() - size) // 2
                y = (pixmap.height() - size) // 2
                pixmap = pixmap.copy(x, y, size, size)
                result = QPixmap(size, size)
                result.fill(Qt.GlobalColor.transparent)
                painter = QPainter(result)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, size, size)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                self._label_photo_profil.setPixmap(result)
                self._label_photo_profil.setText("")
                return
        self._label_photo_profil.setPixmap(QPixmap())
        self._label_photo_profil.setText("👤")

    @staticmethod
    def _calculer_age(date_naissance: str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dn = datetime.strptime(date_naissance, fmt).date()
                today = date.today()
                return today.year - dn.year - (
                    (today.month, today.day) < (dn.month, dn.day)
                )
            except ValueError:
                continue
        return None

    @staticmethod
    def _formater_date(date_str: str) -> str:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str, fmt).strftime("%d/%m/%Y")
            except ValueError:
                continue
        return date_str

    @staticmethod
    def _jours_avant_anniversaire(date_naissance: str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dn = datetime.strptime(date_naissance, fmt).date()
                today = date.today()
                prochain = dn.replace(year=today.year)
                if prochain < today:
                    prochain = prochain.replace(year=today.year + 1)
                return (prochain - today).days
            except ValueError:
                continue
        return None
