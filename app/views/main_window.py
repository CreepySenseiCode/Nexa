"""
Fenêtre principale de l'application Nexa.

Ce module contient la classe MainWindow qui gère la fenêtre principale,
la barre latérale de navigation, le système de verrouillage administratif/fonctionnel
et la gestion des pages via un QStackedWidget.
"""

from __future__ import annotations

import os
import platform
import sys

from PySide6.QtCore import (
    Qt,
    QSize,
    QRectF,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
    QEvent,
    Property,
    Signal,
)
from PySide6.QtGui import (
    QFont,
    QIcon,
    QScreen,
    QCursor,
    QPainter,
    QPen,
    QColor,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QSplitter,
)

from models.database import get_db
from utils.auth import (
    hasher_mot_de_passe,
    verifier_mot_de_passe,
    mot_de_passe_existe,
    mot_de_passe_actif,
)
from utils.validators import valider_mot_de_passe


# ============================================================================
# Feuille de style globale de l'application
# ============================================================================

_STYLESHEET = """
QMainWindow {
    background-color: #FFFFFF;
}

/* Barre latérale */
#sidebar {
    background-color: #F5F5F5;
    border-right: 1px solid #E0E0E0;
}

/* Boutons de navigation (legacy, conservé pour compatibilité) */
.nav-button {
    text-align: left;
    padding: 12px 20px;
    border: none;
    background: transparent;
    font-size: 13pt;
    color: #333333;
    border-left: 4px solid transparent;
}
.nav-button:hover {
    background-color: #E8E8E8;
}
.nav-button-active {
    background-color: #E3F2FD;
    border-left: 4px solid #2196F3;
    color: #2196F3;
    font-weight: bold;
}
.nav-button-locked {
    color: #999999;
}

/* Bouton de verrouillage */
#lock-button {
    border: none;
    padding: 8px;
    border-radius: 5px;
    font-size: 16pt;
}

/* Champs de saisie généraux */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {
    height: 35px;
    border: 1px solid #E0E0E0;
    border-radius: 5px;
    padding: 5px 10px;
    font-size: 12pt;
    background-color: #FFFFFF;
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus {
    border: 1px solid #2196F3;
}

/* Boutons */
QPushButton {
    height: 40px;
    border-radius: 5px;
    padding: 10px 20px;
    font-size: 12pt;
    border: none;
}
.btn-primary {
    background-color: #2196F3;
    color: white;
}
.btn-primary:hover {
    background-color: #1976D2;
}
.btn-success {
    background-color: #4CAF50;
    color: white;
}
.btn-success:hover {
    background-color: #388E3C;
}
.btn-danger {
    background-color: #F44336;
    color: white;
}
.btn-secondary {
    background-color: #9E9E9E;
    color: white;
}
.btn-secondary:hover {
    background-color: #757575;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 15px;
    margin-top: 10px;
    font-size: 13pt;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 5px;
}

/* Tableaux */
QTableWidget {
    border: 1px solid #E0E0E0;
    border-radius: 5px;
    gridline-color: #F0F0F0;
}
QHeaderView::section {
    background-color: #F5F5F5;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #E0E0E0;
    font-weight: bold;
}

/* Barre de défilement verticale */
QScrollBar:vertical {
    width: 8px;
    background: transparent;
}
QScrollBar::handle:vertical {
    background: #CCCCCC;
    border-radius: 4px;
}
"""


# ============================================================================
# Définition des éléments de navigation
# ============================================================================

_NAV_ITEMS = [
    # --- Section fonctionnel (toujours visible) ---
    {"name": "Client", "icon_text": "\U0001f4cb", "locked": False},
    {"name": "Vente", "icon_text": "\U0001f6d2", "locked": False},
    {
        "name": "Rechercher un code",
        "icon_text": "\U0001f39f",
        "locked": False,
        "hidden": True,
    },
    {"name": "Aide", "icon_text": "\u2753", "locked": False, "hidden": True},
    {"name": "Produits", "icon_text": "\U0001f4e6", "locked": False},
    {"name": "Codes promo", "icon_text": "\U0001f3ab", "locked": False},
    {"name": "T\u00e2ches", "icon_text": "\u2705", "locked": False},
    {"name": "Calendrier", "icon_text": "\U0001f5d3\ufe0f", "locked": False},
    # --- Section administratif (visible uniquement si déverrouillé) ---
    {"name": "Emailing", "icon_text": "\u2709\ufe0f", "locked": True, "hidden": True},
    {"name": "Emails", "icon_text": "\U0001f4ec", "locked": True},
    {"name": "Statistiques", "icon_text": "\U0001f4ca", "locked": True},
    {
        "name": "Mails enregistr\u00e9s",
        "icon_text": "\U0001f4be",
        "locked": True,
        "hidden": True,
    },
    {"name": "Historique", "icon_text": "\U0001f4c5", "locked": True, "hidden": True},
    {
        "name": "Param\u00e8tres",
        "icon_text": "\u2699\ufe0f",
        "locked": True,
        "hidden": True,
    },
]


# ============================================================================
# Moteur d'écriture/effacement lettre par lettre (typewriter)
# ============================================================================


class TypewriterEngine:
    """Gère l'écriture et l'effacement progressif d'un texte sur un QLabel."""

    def __init__(self, label: QLabel, full_text: str, min_chars: int = 0) -> None:
        self._label = label
        self._full_text = full_text
        self._min_chars = min_chars
        self._current_index: int = min_chars
        self._direction: int = 1
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)

    def start_write(self, interval_ms: int) -> None:
        """Démarre l'écriture lettre par lettre."""
        self._direction = 1
        self._current_index = self._min_chars
        self._label.setText(self._full_text[: self._min_chars])
        self._timer.setInterval(max(1, interval_ms))
        self._timer.start()

    def start_erase(self, interval_ms: int) -> None:
        """Démarre l'effacement lettre par lettre (ordre inverse)."""
        self._direction = -1
        self._current_index = len(self._full_text)
        self._timer.setInterval(max(1, interval_ms))
        self._timer.start()

    def _tick(self) -> None:
        self._current_index += self._direction
        if self._current_index >= len(self._full_text):
            self._current_index = len(self._full_text)
            self._label.setText(self._full_text)
            self._timer.stop()
        elif self._current_index <= self._min_chars:
            self._current_index = self._min_chars
            self._label.setText(self._full_text[: self._min_chars])
            self._timer.stop()
        else:
            self._label.setText(self._full_text[: self._current_index])

    def reset(self) -> None:
        """Remet le texte à l'état minimal immédiatement."""
        self._timer.stop()
        self._current_index = self._min_chars
        self._label.setText(self._full_text[: self._min_chars])

    def finish(self) -> None:
        """Affiche le texte complet immédiatement."""
        self._timer.stop()
        self._current_index = len(self._full_text)
        self._label.setText(self._full_text)

    def stop(self) -> None:
        """Arrête l'animation en cours sans changer le texte."""
        self._timer.stop()

    @property
    def is_animating(self) -> bool:
        return self._timer.isActive()

    def set_full_text(self, text: str) -> None:
        """Change le texte cible (utile pour nom du commerce)."""
        self._full_text = text


# ============================================================================
# Bouton avec rotation animée (collapse sidebar)
# ============================================================================


class CollapseButton(QPushButton):
    """Bouton rond avec rotation animée de la flèche (sidebar rétractée)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._angle = 0.0
        self._anim = QPropertyAnimation(self, b"angle")
        self._anim.setDuration(300)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def get_angle(self) -> float:
        return self._angle

    def set_angle(self, val: float) -> None:
        self._angle = val
        self.update()

    angle = Property(float, get_angle, set_angle)

    def animate_to(self, target: float) -> None:
        """Lance l'animation de rotation vers l'angle cible (degrés)."""
        self._anim.stop()
        self._anim.setStartValue(self._angle)
        self._anim.setEndValue(float(target))
        self._anim.start()

    def paintEvent(self, event) -> None:
        from PySide6.QtWidgets import QStyleOptionButton, QStyle

        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2.0, self.height() / 2.0
        painter.translate(cx, cy)
        painter.rotate(self._angle)
        painter.translate(-cx, -cy)
        self.style().drawControl(
            QStyle.ControlElement.CE_PushButton, opt, painter, self
        )


# ============================================================================
# Bouton de navigation (emoji fixe + texte typewriter)
# ============================================================================


class NavButton(QWidget):
    """Bouton de navigation avec emoji fixe à gauche et texte animé à droite."""

    clicked = Signal()

    def __init__(
        self, icon_text: str, name: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._icon_text = icon_text
        self._name = name
        self._is_active: bool = False
        self._is_hovered: bool = False

        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Layout principal : [border 4px] [spacer 11px] [icon 30px] [text ...] [stretch]
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Indicateur de bordure gauche (barre colorée active)
        self._border_indicator = QWidget()
        self._border_indicator.setFixedWidth(4)
        layout.addWidget(self._border_indicator)

        # Spacer fixe pour centrer l'emoji dans les 60px collapsed
        # 60px total - 4px border = 56px → icône 30px centrée : (56-30)/2 = 13px
        spacer = QWidget()
        spacer.setFixedWidth(13)
        layout.addWidget(spacer)

        # Emoji (position fixe, ne bouge jamais)
        self._lbl_icon = QLabel(icon_text)
        self._lbl_icon.setFixedWidth(30)
        self._lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._lbl_icon)

        # Texte du nom (visible uniquement en expanded, animé par typewriter)
        self._lbl_text = QLabel("")
        self._lbl_text.setVisible(False)
        layout.addWidget(self._lbl_text)

        layout.addStretch()

        self._typewriter = TypewriterEngine(self._lbl_text, name)
        self._update_style()

    def set_active(self, active: bool) -> None:
        """Définit l'état actif/inactif du bouton."""
        self._is_active = active
        self._update_style()

    def start_typewriter(self, interval_ms: int) -> None:
        """Lance l'écriture progressive du texte."""
        self._lbl_text.setVisible(True)
        self._typewriter.start_write(interval_ms)

    def start_reverse_typewriter(self, interval_ms: int) -> None:
        """Lance l'effacement progressif du texte."""
        self._typewriter.start_erase(interval_ms)

    def reset_text(self) -> None:
        """Remet le texte à vide et cache le label."""
        self._typewriter.reset()
        self._lbl_text.setVisible(False)

    def show_full_text(self) -> None:
        """Affiche le texte complet immédiatement (sans animation)."""
        self._typewriter.finish()
        self._lbl_text.setVisible(True)

    def _update_style(self) -> None:
        """Met à jour le style visuel selon l'état actif/hover."""
        if self._is_active:
            self._border_indicator.setStyleSheet("background-color: #2196F3;")
            self.setStyleSheet("NavButton { background-color: #E3F2FD; }")
            icon_color = "#2196F3"
            text_extra = "font-weight: bold;"
        elif self._is_hovered:
            self._border_indicator.setStyleSheet("background-color: transparent;")
            self.setStyleSheet("NavButton { background-color: #E8E8E8; }")
            icon_color = "#333333"
            text_extra = ""
        else:
            self._border_indicator.setStyleSheet("background-color: transparent;")
            self.setStyleSheet("NavButton { background: transparent; }")
            icon_color = "#333333"
            text_extra = ""

        self._lbl_icon.setStyleSheet(
            f"font-size: 16pt; color: {icon_color}; background: transparent; border: none;"
        )
        self._lbl_text.setStyleSheet(
            f"font-size: 13pt; color: {icon_color}; {text_extra} "
            "background: transparent; border: none; padding-left: 10px;"
        )

    def enterEvent(self, event) -> None:
        self._is_hovered = True
        self._update_style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._is_hovered = False
        self._update_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# ============================================================================
# En-tête de section animé (ligne → ligne + texte)
# ============================================================================


class SectionHeaderWidget(QWidget):
    """Widget qui affiche une ligne horizontale avec texte centré animé.

    En collapsed : ligne grise courte indentée.
    Pendant l'ouverture : la ligne s'étend en temps réel.
    En expanded : ── TEXTE ── (ligne avec gap et texte typewriter).
    """

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full_text = text
        self._current_text: str = ""
        self.setFixedHeight(30)

        # QLabel caché pour le TypewriterEngine
        self._hidden_label = QLabel("", self)
        self._hidden_label.setVisible(False)
        self._tw_engine = TypewriterEngine(self._hidden_label, text)

        # Timer de synchronisation repaint ↔ typewriter
        self._repaint_timer = QTimer()
        self._repaint_timer.setInterval(16)
        self._repaint_timer.timeout.connect(self._check_repaint)

    def _check_repaint(self) -> None:
        new_text = self._hidden_label.text()
        if new_text != self._current_text:
            self._current_text = new_text
            self.update()
        if not self._tw_engine.is_animating:
            self._repaint_timer.stop()

    def set_expanded(self, expanded: bool, interval_ms: int) -> None:
        """Déclenche la transition ligne ↔ ligne+texte."""
        if expanded:
            self._tw_engine.start_write(interval_ms)
        else:
            self._tw_engine.start_erase(interval_ms)
        self._repaint_timer.start()

    def reset(self) -> None:
        """Remet en état collapsed (ligne seule, pas de texte)."""
        self._tw_engine.reset()
        self._current_text = ""
        self._repaint_timer.stop()
        self.update()

    def finish(self) -> None:
        """Affiche le texte complet immédiatement."""
        self._tw_engine.finish()
        self._current_text = self._full_text
        self._repaint_timer.stop()
        self.update()

    def update_sidebar_width(self, width: int) -> None:
        """Force un repaint quand la sidebar change de largeur."""
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        margin = 8
        y_center = self.height() // 2
        pen = QPen(QColor("#999999"), 1)
        painter.setPen(pen)

        if self._current_text:
            # Dessiner ligne avec gap + texte centré
            font = painter.font()
            font.setPointSize(9)
            font.setBold(True)
            font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0)
            painter.setFont(font)

            fm = painter.fontMetrics()
            text_width = fm.horizontalAdvance(self._current_text)
            center_x = self.width() // 2
            gap_padding = 6
            gap_half = text_width // 2 + gap_padding

            # Segment gauche
            left_end = center_x - gap_half
            if left_end > margin:
                painter.drawLine(margin, y_center, left_end, y_center)

            # Segment droit
            right_start = center_x + gap_half
            if right_start < self.width() - margin:
                painter.drawLine(right_start, y_center, self.width() - margin, y_center)

            # Texte centré
            text_x = center_x - text_width // 2
            text_y = y_center + fm.ascent() // 2 - 1
            painter.drawText(text_x, text_y, self._current_text)
        else:
            # Ligne pleine (mode collapsed ou texte effacé)
            painter.drawLine(margin, y_center, self.width() - margin, y_center)

        painter.end()


# ============================================================================
# En-tête de la sidebar (N/Logo ↔ Nexa + Commerce + Séparateur)
# ============================================================================


class SidebarHeader(QWidget):
    """Header : logo_base (N) fixe + logo_ajout_base (exa) progressif.

    En collapsed : logo_base (N) centré.
    En expanded  : N fixe + "exa" apparaît à droite, le tout centré.
    Le N ne change jamais de taille.
    """

    HEADER_HEIGHT = 110

    def __init__(self, nom_commerce: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._nom_commerce = nom_commerce
        self._expanded: bool = False

        self.setFixedHeight(self.HEADER_HEIGHT)

        # Charger les deux images distinctes (N + exa)
        icons_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "icons")
        self._logo_n = QPixmap(os.path.join(icons_dir, "logo_base.png"))
        self._logo_exa = QPixmap(os.path.join(icons_dir, "logo_ajout_base.png"))

        # Reveal : 0.0 = collapsed (N seul), 1.0 = expanded (N + exa)
        self._reveal: float = 0.0

        # Horloge (peinte dans le header, pas de widget séparé)
        self._clock_text: str = ""

        # Animation timer (3 étapes pour "e", "x", "a")
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._tick_reveal)
        self._anim_direction: int = 1
        self._anim_step: float = 1.0 / 3.0

    def set_expanded(self, expanded: bool, interval_ms: int) -> None:
        self._expanded = expanded
        self._anim_direction = 1 if expanded else -1
        self._anim_timer.setInterval(max(1, interval_ms))
        self._anim_timer.start()

    def _tick_reveal(self) -> None:
        self._reveal += self._anim_step * self._anim_direction
        if self._reveal >= 1.0:
            self._reveal = 1.0
            self._anim_timer.stop()
        elif self._reveal <= 0.0:
            self._reveal = 0.0
            self._anim_timer.stop()
        self.update()

    def force_collapsed(self) -> None:
        self._anim_timer.stop()
        self._reveal = 0.0
        self._expanded = False
        self.update()

    def force_expanded(self) -> None:
        self._anim_timer.stop()
        self._reveal = 1.0
        self._expanded = True
        self.update()

    def set_clock_text(self, text: str) -> None:
        """Met à jour le texte de l'horloge (peint dans le paintEvent)."""
        self._clock_text = text
        self.update()

    def set_nom_commerce(self, nom: str) -> None:
        self._nom_commerce = nom

    def set_logo(self, pixmap: QPixmap) -> None:
        self._logo_n = pixmap
        self.update()

    _COLLAPSED_MAX_W = 48  # largeur max du N en sidebar rétractée
    _GAP = -5  # chevauchement léger entre N et "exa"

    def paintEvent(self, _event) -> None:
        if self._logo_n.isNull():
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        margin = 6
        available_h = h - 2 * margin

        # Taille fixe du N (ne change jamais)
        n_ratio = self._logo_n.width() / self._logo_n.height()
        n_w = min(self._COLLAPSED_MAX_W, available_h * n_ratio)
        n_h = n_w / n_ratio

        if self._reveal <= 0.001 or self._logo_exa.isNull():
            # Collapsed : N centré
            nx = (w - n_w) / 2
            ny = (h - n_h) / 2
            p.drawPixmap(
                QRectF(nx, ny, n_w, n_h),
                self._logo_n,
                QRectF(0, 0, self._logo_n.width(), self._logo_n.height()),
            )
        else:
            # Expanding / Expanded : N fixe + "exa" clip progressif
            exa_ratio = self._logo_exa.width() / self._logo_exa.height()
            exa_h = n_h * 0.55  # minuscules plus petites que le N
            exa_w_full = exa_h * exa_ratio
            exa_w = exa_w_full * self._reveal

            # Largeur totale = N + gap + partie visible de exa
            total_w = n_w + self._GAP + exa_w
            start_x = (w - total_w) / 2

            # N
            ny = (h - n_h) / 2
            p.drawPixmap(
                QRectF(start_x, ny, n_w, n_h),
                self._logo_n,
                QRectF(0, 0, self._logo_n.width(), self._logo_n.height()),
            )

            # "exa" (clip gauche → droite, aligné en bas du N)
            if exa_w > 0.5:
                exa_x = start_x + n_w + self._GAP
                exa_y = ny + n_h - exa_h
                src_w = self._logo_exa.width() * self._reveal
                p.drawPixmap(
                    QRectF(exa_x, exa_y, exa_w, exa_h),
                    self._logo_exa,
                    QRectF(0, 0, src_w, self._logo_exa.height()),
                )

            # Horloge sous le logo (opacité liée au reveal)
            if self._clock_text and self._reveal > 0.3:
                clock_opacity = min(1.0, (self._reveal - 0.3) / 0.7)
                p.setOpacity(clock_opacity)
                clock_font = QFont()
                clock_font.setPointSize(9)
                p.setFont(clock_font)
                p.setPen(QColor(170, 170, 170))
                clock_y = ny + n_h + 2
                p.drawText(
                    QRectF(0, clock_y, w, 16),
                    Qt.AlignmentFlag.AlignCenter,
                    self._clock_text,
                )
                p.setOpacity(1.0)

        p.end()


def _make_square_icon(path: str) -> QPixmap:
    """Charge une image et la place centrée dans un carré transparent."""
    src = QPixmap(path)
    if src.isNull():
        return src
    side = max(src.width(), src.height())
    square = QPixmap(side, side)
    square.fill(QColor(0, 0, 0, 0))
    painter = QPainter(square)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    x = (side - src.width()) // 2
    y = (side - src.height()) // 2
    painter.drawPixmap(x, y, src)
    painter.end()
    return square


# ============================================================================
# Classe principale : MainWindow
# ============================================================================


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application Nexa.

    Gère la barre latérale de navigation, le système de verrouillage
    administratif/fonctionnel et l'affichage des pages via un QStackedWidget.
    """

    mode_changed = Signal(bool)

    def __init__(self) -> None:
        """Initialise la fenêtre principale et tous ses composants."""
        super().__init__()

        # --- État interne ---
        self._mode_administratif: bool = False
        self._index_actif: int = 0
        self._boutons_nav: list[NavButton] = []
        self._section_headers: list[SectionHeaderWidget] = []
        self._animation_en_cours: bool = False

        # --- Configuration de la fenêtre ---
        self.setWindowTitle("Nexa - Gestion de Clientèle")
        self.setMinimumSize(1200, 800)
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "icons", "logo_base.png"
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(_make_square_icon(icon_path)))

        # --- Configuration de la police système ---
        self._configurer_police()

        # --- Application de la feuille de style ---
        self.setStyleSheet(_STYLESHEET)

        # --- Construction de l'interface ---
        self.sidebar_etendue: bool = False
        self.animationencours: bool = False
        self.zone_hover: bool = False
        self.largeur_etendue: int = 180
        self.largeur_retractee: int = 60
        self._bouton_verrou_actif: bool = True
        self.construireinterface()

        # --- Centrer la fenêtre sur l'écran ---
        self._centrer_fenetre()

        QTimer.singleShot(0, self._verifier_premier_lancement)  # ← ajouter (après show)

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------

    def _configurer_police(self) -> None:
        """Configure la police système selon la plateforme."""
        systeme = platform.system()
        if systeme == "Windows":
            nom_police = "Segoe UI"
        elif systeme == "Darwin":
            nom_police = ".AppleSystemUIFont"
        elif systeme == "Linux":
            nom_police = "Ubuntu"
        else:
            nom_police = "Arial"

        police = QFont(nom_police, 12)
        QApplication.instance().setFont(police)

    def construireinterface(self) -> None:
        widgetcentral = QWidget()
        widgetcentral.setStyleSheet("background-color: #FFFFFF;")
        self.setCentralWidget(widgetcentral)

        # SPLITTER pour rétraction fluide
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setStyleSheet("background-color: #FFFFFF;")
        self.sidebar = self._creer_sidebar()
        self.splitter.addWidget(self.sidebar)

        self.panneaudroit = QWidget()
        self.panneaudroit.setStyleSheet("background-color: #FFFFFF;")
        layoutdroit = QVBoxLayout(self.panneaudroit)
        layoutdroit.setContentsMargins(0, 0, 0, 0)
        layoutdroit.setSpacing(0)

        self._pile_pages = QStackedWidget()
        self._pile_pages.setStyleSheet("QStackedWidget { background-color: #FFFFFF; }")
        layoutdroit.addWidget(self._pile_pages)

        # Remplir placeholders
        for i, item in enumerate(_NAV_ITEMS):
            labelplaceholder = QLabel(f"Page {item['name']}")
            labelplaceholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            labelplaceholder.setStyleSheet("font-size: 18pt; color: #999999;")
            self._pile_pages.addWidget(labelplaceholder)

        self.splitter.addWidget(self.panneaudroit)
        self.splitter.setSizes([self.largeur_retractee, 1])

        layoutprincipal = QHBoxLayout(widgetcentral)
        layoutprincipal.addWidget(self.splitter)
        layoutprincipal.setContentsMargins(0, 0, 0, 0)
        layoutprincipal.setSpacing(0)

        # Event filter pour hover et resize
        self._hover_poll = QTimer()
        self._hover_poll.setInterval(40)  # 40ms ≈ 25 fps, imperceptible
        self._hover_poll.timeout.connect(self._sonder_hover_sidebar)
        self._hover_poll.start()

        self.timer_anim = None
        self._changer_page(0)

    # ------------------------------------------------------------------
    # Barre latérale (sidebar)
    # ------------------------------------------------------------------

    def _creer_sidebar(self) -> QFrame:
        """Crée et retourne la barre latérale de navigation (rétractable)."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(60)
        sidebar.setMaximumWidth(60)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Header : N/Logo ↔ Nexa + Commerce + Séparateur ---
        self._nom_commerce = self._obtenir_nom_commerce()
        self._sidebar_header = SidebarHeader(self._nom_commerce)
        layout.addWidget(self._sidebar_header)

        # --- Horloge intégrée dans le header (peinte, pas de widget séparé) ---
        self._timer_horloge = QTimer()
        self._timer_horloge.setInterval(1000)
        self._timer_horloge.timeout.connect(self._maj_horloge)
        self._timer_horloge.start()

        # --- Section FONCTIONNEL (ligne animée) ---
        self._section_header_fonctionnel = SectionHeaderWidget("FONCTIONNEL")
        layout.addWidget(self._section_header_fonctionnel)
        self._section_headers.append(self._section_header_fonctionnel)

        # --- Boutons de navigation ---
        self._boutons_nav = []
        self._section_header_administratif: SectionHeaderWidget | None = None
        _admin_header_added = False

        for i, item in enumerate(_NAV_ITEMS):
            # Ajouter le header ADMINISTRATIF avant le premier item verrouillé
            if item["locked"] and not _admin_header_added:
                _admin_header_added = True
                self._section_header_administratif = SectionHeaderWidget(
                    "ADMINISTRATIF"
                )
                self._section_header_administratif.setVisible(False)
                layout.addWidget(self._section_header_administratif)
                self._section_headers.append(self._section_header_administratif)

            nav_btn = NavButton(item["icon_text"], item["name"])
            nav_btn.setFixedHeight(50)
            nav_btn.clicked.connect(lambda idx=i: self._changer_page(idx))

            if item.get("hidden"):
                nav_btn.setVisible(False)

            self._boutons_nav.append(nav_btn)
            layout.addWidget(nav_btn)

        # --- Espace flexible ---
        layout.addSpacerItem(
            QSpacerItem(
                20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
        )

        # --- Boutons ronds en bas de sidebar ---
        ronds_container = QWidget()
        ronds_layout = QHBoxLayout(ronds_container)
        ronds_layout.setSpacing(5)
        ronds_layout.setContentsMargins(5, 10, 5, 15)
        ronds_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Bouton collapse : rond gris avec flèche, visible uniquement en mode rétracté
        self._btn_collapse = CollapseButton()
        self._btn_collapse.setText("▲")
        self._btn_collapse.setFixedSize(50, 50)
        self._btn_collapse.setStyleSheet(
            "QPushButton {"
            "    background-color: #9E9E9E; color: white; border: none;"
            "    border-radius: 25px; font-size: 14pt; font-weight: bold;"
            "}"
            "QPushButton:hover { background-color: #757575; }"
        )
        self._btn_collapse.setToolTip("Déployer les options")
        self._btn_collapse.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_collapse.clicked.connect(self.elargirsidebar)
        ronds_layout.addWidget(self._btn_collapse)

        self._btn_rond_aide = QPushButton("?")
        self._btn_rond_aide.setFixedSize(50, 50)
        self._btn_rond_aide.setStyleSheet(
            "QPushButton {"
            "    background-color: #FFC107; color: white; border: none;"
            "    border-radius: 25px; font-size: 20pt; font-weight: bold;"
            "}"
            "QPushButton:hover { background-color: #FFA000; }"
        )
        self._btn_rond_aide.setToolTip("Centre d'aide")
        self._btn_rond_aide.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_rond_aide.clicked.connect(lambda: self._changer_page(3))
        self._btn_rond_aide.hide()
        ronds_layout.addWidget(self._btn_rond_aide)

        self._btn_rond_params = QPushButton("\u2699")
        self._btn_rond_params.setFixedSize(50, 50)
        self._btn_rond_params.setStyleSheet(
            "QPushButton {"
            "    background-color: #607D8B; color: white; border: none;"
            "    border-radius: 25px; font-size: 20pt; font-weight: bold;"
            "}"
            "QPushButton:hover { background-color: #455A64; }"
        )
        self._btn_rond_params.setToolTip("Parametres")
        self._btn_rond_params.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_rond_params.clicked.connect(self._afficher_parametres)
        self._btn_rond_params.hide()
        ronds_layout.addWidget(self._btn_rond_params)

        self._bouton_verrou = QPushButton("\U0001f512")
        self._bouton_verrou.setObjectName("lock-button")
        self._bouton_verrou.setFixedSize(50, 50)
        self._bouton_verrou.setCursor(Qt.CursorShape.PointingHandCursor)
        self._bouton_verrou.setToolTip(
            "Cliquez pour déverrouiller (mode administratif)"
        )
        self._bouton_verrou.clicked.connect(self._basculer_verrouillage)
        self._maj_style_verrou()
        self._bouton_verrou.hide()
        ronds_layout.addWidget(self._bouton_verrou)

        layout.addWidget(ronds_container)

        return sidebar

    def _obtenir_nom_commerce(self) -> str:
        """Récupère le nom du commerce depuis la base de données."""
        from models.parametres import ParametresModel

        try:
            valeur = ParametresModel().obtenir_parametre("nom_entreprise")
            if valeur:
                return valeur
        except Exception:
            pass
        return "Mon Commerce"

    def actualiser_nom_entreprise(self) -> None:
        """Actualise le nom de l'entreprise dans la sidebar."""
        self._nom_commerce = self._obtenir_nom_commerce()
        self._sidebar_header.set_nom_commerce(self._nom_commerce)

    def _maj_style_verrou(self) -> None:
        """Met à jour l'apparence du bouton de verrouillage selon le mode."""
        if self._mode_administratif:
            self._bouton_verrou.setText("\U0001f513")
            self._bouton_verrou.setStyleSheet(
                "#lock-button { background-color: #4CAF50; border: none; "
                "padding: 8px; border-radius: 25px; font-size: 16pt; }"
            )
            self._bouton_verrou.setToolTip(
                "Mode administratif (cliquez pour verrouiller)"
            )
        else:
            self._bouton_verrou.setText("\U0001f512")
            self._bouton_verrou.setStyleSheet(
                "#lock-button { background-color: #F44336; border: none; "
                "padding: 8px; border-radius: 25px; font-size: 16pt; }"
            )
            self._bouton_verrou.setToolTip(
                "Mode fonctionnel (cliquez pour d\u00e9verrouiller)"
            )

    # ------------------------------------------------------------------
    # Navigation entre les pages
    # ------------------------------------------------------------------

    def _changer_page(self, index: int) -> None:
        """Change la page affichée dans le QStackedWidget."""
        if index < 0 or index >= self._pile_pages.count():
            return

        # Pages dans _NAV_ITEMS : vérifier le verrou admin
        if index < len(_NAV_ITEMS):
            item = _NAV_ITEMS[index]
            if item["locked"] and not self._mode_administratif:
                self._afficher_page_verrouillee()
                self._index_actif = index
                self._mettre_a_jour_sidebar()
                return

        self._index_actif = index
        self._pile_pages.setCurrentIndex(index)
        if index < len(_NAV_ITEMS):
            self._mettre_a_jour_sidebar()

    def _afficher_page_verrouillee(self) -> None:
        """Affiche le placeholder d'accès restreint dans la zone de contenu."""
        page_verrouillee = QWidget()
        layout = QVBoxLayout(page_verrouillee)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label_icone = QLabel("\U0001f512")
        label_icone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_icone.setStyleSheet("font-size: 64pt; color: #CCCCCC; border: none;")
        layout.addWidget(label_icone)

        label_titre = QLabel("Acc\u00e8s restreint")
        label_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_titre.setStyleSheet(
            "font-size: 20pt; font-weight: bold; color: #666666; "
            "margin-top: 15px; border: none;"
        )
        layout.addWidget(label_titre)

        label_message = QLabel(
            "Connectez-vous en mode administratif pour acc\u00e9der \u00e0 cette section."
        )
        label_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_message.setStyleSheet(
            "font-size: 13pt; color: #999999; margin-top: 10px; border: none;"
        )
        layout.addWidget(label_message)

        bouton_connexion = QPushButton("Se connecter")
        bouton_connexion.setProperty("class", "btn-primary")
        bouton_connexion.setFixedWidth(200)
        bouton_connexion.setCursor(Qt.CursorShape.PointingHandCursor)
        bouton_connexion.setStyleSheet(
            "background-color: #2196F3; color: white; height: 40px; "
            "border-radius: 5px; font-size: 12pt; margin-top: 20px;"
        )
        bouton_connexion.clicked.connect(self._deverrouiller)
        layout.addWidget(bouton_connexion, alignment=Qt.AlignmentFlag.AlignCenter)

        if (
            hasattr(self, "_widget_page_verrouillee")
            and self._widget_page_verrouillee is not None
        ):
            self._pile_pages.removeWidget(self._widget_page_verrouillee)
            self._widget_page_verrouillee.deleteLater()

        self._widget_page_verrouillee = page_verrouillee
        idx_temp = self._pile_pages.addWidget(page_verrouillee)
        self._pile_pages.setCurrentIndex(idx_temp)

    # ------------------------------------------------------------------
    # Mise à jour visuelle de la sidebar
    # ------------------------------------------------------------------

    def _mettre_a_jour_sidebar(self) -> None:
        """Met à jour la visibilité et l'état actif de tous les éléments de la sidebar."""

        # Bouton collapse : visible seulement quand rétracté
        if hasattr(self, "_btn_collapse"):
            self._btn_collapse.setVisible(not self.sidebar_etendue)

        # Bouton aide : visible dès que sidebar étendue (tous modes)
        if hasattr(self, "_btn_rond_aide"):
            self._btn_rond_aide.setVisible(self.sidebar_etendue)
        if hasattr(self, "_btn_rond_params"):
            self._btn_rond_params.setVisible(
                self._mode_administratif and self.sidebar_etendue
            )

        # Verrou : visible si actif ET étendu
        if hasattr(self, "_bouton_verrou"):
            self._bouton_verrou.setVisible(
                self.sidebar_etendue and getattr(self, "_bouton_verrou_actif", True)
            )

        # Section header administratif
        if self._section_header_administratif is not None:
            self._section_header_administratif.setVisible(self._mode_administratif)

        # Boutons de navigation
        for i, bouton in enumerate(self._boutons_nav):
            item = _NAV_ITEMS[i]
            est_actif = i == self._index_actif
            est_cache = item.get("hidden", False)
            est_verrouille = item["locked"]

            if est_cache:
                bouton.setVisible(False)
                continue

            if est_verrouille and not self._mode_administratif:
                bouton.setVisible(False)
                continue

            bouton.setVisible(True)
            bouton.set_active(est_actif)

        # Gestion du texte quand on n'est PAS en animation
        if not self._animation_en_cours:
            if self.sidebar_etendue:
                self._sidebar_header.force_expanded()
                for btn in self._boutons_nav:
                    if btn.isVisible():
                        btn.show_full_text()
                for sh in self._section_headers:
                    if sh.isVisible():
                        sh.finish()
            else:
                self._sidebar_header.force_collapsed()
                for btn in self._boutons_nav:
                    btn.reset_text()
                for sh in self._section_headers:
                    sh.reset()

    # ------------------------------------------------------------------
    # Système de verrouillage (administratif / fonctionnel)
    # ------------------------------------------------------------------

    def _basculer_verrouillage(self) -> None:
        """Bascule entre le mode administratif et le mode fonctionnel."""
        if self._mode_administratif:
            self._verrouiller()
        else:
            self._deverrouiller()

    def _deverrouiller(self) -> None:
        """Affiche le dialogue de saisie du mot de passe avec gestion des tentatives."""
        db = get_db()

        if not mot_de_passe_existe(db):
            self._mode_administratif = True
            self._maj_style_verrou()
            self._mettre_a_jour_sidebar()
            self.mode_changed.emit(True)
            self._changer_page(self._index_actif)
            return

        row_tentatives = db.fetchone(
            "SELECT valeur FROM parametres WHERE cle = 'tentatives_echouees'"
        )
        tentatives = (
            int(row_tentatives["valeur"])
            if row_tentatives and row_tentatives["valeur"]
            else 0
        )

        row_indice = db.fetchone(
            "SELECT valeur FROM parametres WHERE cle = 'mot_de_passe_indice'"
        )
        indice = row_indice["valeur"] if row_indice else ""

        row_email = db.fetchone(
            "SELECT valeur FROM parametres WHERE cle = 'email_recuperation'"
        )
        email_recup = row_email["valeur"] if row_email else ""

        dialogue = QDialog(self)
        dialogue.setWindowTitle("Authentification administratif")
        dialogue.setFixedSize(420, 320)
        dialogue.setStyleSheet("QDialog { background-color: #FFFFFF; }")

        layout = QVBoxLayout(dialogue)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(12)

        label_titre = QLabel("Entrez le mot de passe administratif")
        label_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_titre.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333333;")
        layout.addWidget(label_titre)

        champ_mdp = QLineEdit()
        champ_mdp.setEchoMode(QLineEdit.EchoMode.Password)
        champ_mdp.setPlaceholderText("Mot de passe")
        layout.addWidget(champ_mdp)

        label_erreur = QLabel("")
        label_erreur.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_erreur.setStyleSheet("color: #F44336; font-size: 11pt;")
        label_erreur.setVisible(False)
        layout.addWidget(label_erreur)

        label_indice = QLabel("")
        label_indice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_indice.setStyleSheet(
            "color: #FF9800; font-size: 11pt; font-style: italic; "
            "background-color: #FFF3E0; padding: 8px; border-radius: 6px;"
        )
        label_indice.setWordWrap(True)
        label_indice.setVisible(False)
        layout.addWidget(label_indice)

        if tentatives >= 3 and indice:
            label_indice.setText(f"Indice : {indice}")
            label_indice.setVisible(True)

        btn_recuperation = QPushButton("Mot de passe oublie ?")
        btn_recuperation.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_recuperation.setStyleSheet(
            "QPushButton { background: transparent; color: #2196F3; "
            "border: none; font-size: 11pt; text-decoration: underline; }"
            "QPushButton:hover { color: #1565C0; }"
        )
        btn_recuperation.setVisible(tentatives >= 5 and bool(email_recup))
        layout.addWidget(btn_recuperation, alignment=Qt.AlignmentFlag.AlignCenter)

        label_tentatives = QLabel("")
        label_tentatives.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_tentatives.setStyleSheet("color: #999999; font-size: 10pt;")
        if tentatives > 0:
            label_tentatives.setText(f"{tentatives} tentative(s) echouee(s)")
        layout.addWidget(label_tentatives)

        layout.addStretch()

        boutons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        boutons.button(QDialogButtonBox.StandardButton.Ok).setText("Deverrouiller")
        boutons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        layout.addWidget(boutons)

        def valider() -> None:
            nonlocal tentatives
            mdp = champ_mdp.text().strip()
            if not mdp:
                label_erreur.setText("Veuillez entrer un mot de passe.")
                label_erreur.setVisible(True)
                return

            resultat = db.fetchone(
                "SELECT valeur FROM parametres WHERE cle = 'mot_de_passe_administratif'"
            )
            if (
                resultat
                and resultat["valeur"]
                and verifier_mot_de_passe(mdp, resultat["valeur"])
            ):
                db.execute(
                    "UPDATE parametres SET valeur = '0' WHERE cle = 'tentatives_echouees'"
                )
                self._mode_administratif = True
                self._maj_style_verrou()
                self._mettre_a_jour_sidebar()
                self.mode_changed.emit(True)
                self._changer_page(self._index_actif)
                dialogue.accept()
            else:
                tentatives += 1
                db.execute(
                    "UPDATE parametres SET valeur = ? WHERE cle = 'tentatives_echouees'",
                    (str(tentatives),),
                )

                label_erreur.setText("Mot de passe incorrect.")
                label_erreur.setVisible(True)
                label_tentatives.setText(f"{tentatives} tentative(s) echouee(s)")

                if tentatives >= 3 and indice:
                    label_indice.setText(f"Indice : {indice}")
                    label_indice.setVisible(True)

                if tentatives >= 5 and email_recup:
                    btn_recuperation.setVisible(True)

                champ_mdp.clear()
                champ_mdp.setFocus()

        def demander_recuperation() -> None:
            if not email_recup:
                return
            parts = email_recup.split("@")
            if len(parts) == 2:
                visible = parts[0][:2] + "***"
                email_masque = f"{visible}@{parts[1]}"
            else:
                email_masque = "***"

            QMessageBox.information(
                dialogue,
                "Recuperation du mot de passe",
                f"Un email de recuperation est configure : {email_masque}\n\n"
                "Pour reinitialiser votre mot de passe, utilisez le script :\n"
                "python reset_password.py\n\n"
                "Ce script se trouve a la racine du projet.",
            )

        boutons.accepted.connect(valider)
        boutons.rejected.connect(dialogue.reject)
        champ_mdp.returnPressed.connect(valider)
        btn_recuperation.clicked.connect(demander_recuperation)

        dialogue.exec()

    def _verrouiller(self) -> None:
        """Verrouille l'application en mode fonctionnel."""
        self._mode_administratif = False
        self._maj_style_verrou()
        self._mettre_a_jour_sidebar()
        self.mode_changed.emit(False)

        if _NAV_ITEMS[self._index_actif]["locked"]:
            self._changer_page(0)

    # ------------------------------------------------------------------
    # Gestion du premier lancement (création du mot de passe)
    # ------------------------------------------------------------------

    def _verifier_premier_lancement(self) -> None:
        """Verifie l'etat du mot de passe au lancement."""
        db = get_db()
        if not mot_de_passe_existe(db):
            self._afficher_dialogue_premier_lancement()
        elif mot_de_passe_actif(db):
            self._mode_administratif = False
            self._maj_style_verrou()
            self._bouton_verrou_actif = True
            self._mettre_a_jour_sidebar()
            self.mode_changed.emit(False)
        else:
            self._mode_administratif = True
            self._maj_style_verrou()
            self._bouton_verrou_actif = False
            self._mettre_a_jour_sidebar()
            self.mode_changed.emit(True)

    def _afficher_dialogue_premier_lancement(self) -> None:
        """Dialogue du premier lancement : proposer de definir un mot de passe ou ignorer."""
        dialogue = QDialog(self)
        dialogue.setWindowTitle("Bienvenue dans Nexa !")
        dialogue.setFixedSize(500, 250)
        dialogue.setStyleSheet("QDialog { background-color: #FFFFFF; }")

        layout = QVBoxLayout(dialogue)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        label_titre = QLabel("Bienvenue dans Nexa !")
        label_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_titre.setStyleSheet("font-size: 16pt; font-weight: bold; color: #2196F3;")
        layout.addWidget(label_titre)

        label_instruction = QLabel(
            "Souhaitez-vous proteger l'acces aux sections avancees\n"
            "(statistiques, emailing, parametres...) par un mot de passe ?"
        )
        label_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_instruction.setStyleSheet("font-size: 12pt; color: #666666;")
        label_instruction.setWordWrap(True)
        layout.addWidget(label_instruction)

        layout.addSpacerItem(
            QSpacerItem(
                20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
        )

        layout_boutons = QHBoxLayout()

        btn_plus_tard = QPushButton("Plus tard")
        btn_plus_tard.setStyleSheet(
            "background-color: #9E9E9E; color: white; height: 40px; "
            "border-radius: 5px; font-size: 12pt; padding: 0 20px;"
        )
        btn_plus_tard.setCursor(Qt.CursorShape.PointingHandCursor)
        layout_boutons.addWidget(btn_plus_tard)

        layout_boutons.addStretch()

        btn_definir = QPushButton("Definir un mot de passe")
        btn_definir.setStyleSheet(
            "background-color: #2196F3; color: white; height: 40px; "
            "border-radius: 5px; font-size: 12pt; padding: 0 20px;"
        )
        btn_definir.setCursor(Qt.CursorShape.PointingHandCursor)
        layout_boutons.addWidget(btn_definir)

        layout.addLayout(layout_boutons)

        def choisir_plus_tard() -> None:
            db = get_db()
            db.execute(
                "UPDATE parametres SET valeur = '0' WHERE cle = 'mot_de_passe_actif'"
            )
            self._mode_administratif = True
            self._maj_style_verrou()
            self._bouton_verrou_actif = False
            self._mettre_a_jour_sidebar()
            self.mode_changed.emit(True)
            dialogue.accept()

        def choisir_definir() -> None:
            dialogue.accept()
            self._afficher_dialogue_creation_mdp()

        btn_plus_tard.clicked.connect(choisir_plus_tard)
        btn_definir.clicked.connect(choisir_definir)

        dialogue.exec()

    def _afficher_dialogue_creation_mdp(self) -> None:
        """Dialogue de creation du mot de passe administratif."""
        dialogue = QDialog(self)
        dialogue.setWindowTitle("Creation du mot de passe administratif")
        dialogue.setFixedSize(500, 580)
        dialogue.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        dialogue.setWindowFlags(
            dialogue.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint
        )

        layout = QVBoxLayout(dialogue)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(10)

        label_titre = QLabel("Definir le mot de passe administratif")
        label_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_titre.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333333;")
        layout.addWidget(label_titre)

        champ_mdp = QLineEdit()
        champ_mdp.setEchoMode(QLineEdit.EchoMode.Password)
        champ_mdp.setPlaceholderText("Entrez votre mot de passe")
        layout.addWidget(champ_mdp)

        labels_regles = {}
        regles = [
            ("longueur", "Au moins 8 caracteres"),
            ("majuscule", "Au moins 1 majuscule"),
            ("minuscule", "Au moins 1 minuscule"),
            ("chiffre", "Au moins 1 chiffre"),
            ("special", "Au moins 1 caractere special (!@#$...)"),
        ]
        for cle, texte in regles:
            label = QLabel(f"  \u2717  {texte}")
            label.setStyleSheet("font-size: 10pt; color: #F44336;")
            layout.addWidget(label)
            labels_regles[cle] = label

        label_confirm_titre = QLabel("Confirmer le mot de passe :")
        label_confirm_titre.setStyleSheet(
            "font-size: 11pt; color: #333333; margin-top: 8px;"
        )
        layout.addWidget(label_confirm_titre)

        champ_confirm = QLineEdit()
        champ_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        champ_confirm.setPlaceholderText("Confirmez votre mot de passe")
        layout.addWidget(champ_confirm)

        label_indice_titre = QLabel("Indice (optionnel) :")
        label_indice_titre.setStyleSheet(
            "font-size: 11pt; color: #333333; margin-top: 8px;"
        )
        layout.addWidget(label_indice_titre)

        champ_indice = QLineEdit()
        champ_indice.setPlaceholderText("Un indice pour vous rappeler le mot de passe")
        layout.addWidget(champ_indice)

        label_email_titre = QLabel("Email de recuperation (optionnel) :")
        label_email_titre.setStyleSheet(
            "font-size: 11pt; color: #333333; margin-top: 8px;"
        )
        layout.addWidget(label_email_titre)

        champ_email_recup = QLineEdit()
        champ_email_recup.setPlaceholderText("email@exemple.fr")
        layout.addWidget(champ_email_recup)

        label_erreur = QLabel("")
        label_erreur.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_erreur.setStyleSheet("color: #F44336; font-size: 11pt;")
        label_erreur.setVisible(False)
        layout.addWidget(label_erreur)

        layout.addStretch()

        bouton_valider = QPushButton("Creer le mot de passe")
        bouton_valider.setStyleSheet(
            "background-color: #2196F3; color: white; height: 40px; "
            "border-radius: 5px; font-size: 12pt;"
        )
        bouton_valider.setCursor(Qt.CursorShape.PointingHandCursor)
        bouton_valider.setEnabled(False)
        layout.addWidget(bouton_valider)

        def on_mdp_change(texte: str) -> None:
            valide, msg, details = valider_mot_de_passe(texte)
            for cle, label in labels_regles.items():
                if details.get(cle):
                    label.setText(f"  \u2713  {dict(regles)[cle]}")
                    label.setStyleSheet("font-size: 10pt; color: #4CAF50;")
                else:
                    label.setText(f"  \u2717  {dict(regles)[cle]}")
                    label.setStyleSheet("font-size: 10pt; color: #F44336;")
            bouton_valider.setEnabled(valide)

        champ_mdp.textChanged.connect(on_mdp_change)

        def valider_creation() -> None:
            mdp = champ_mdp.text()
            confirm = champ_confirm.text()

            valide, msg, _ = valider_mot_de_passe(mdp)
            if not valide:
                label_erreur.setText(msg)
                label_erreur.setVisible(True)
                return

            if mdp != confirm:
                label_erreur.setText("Les mots de passe ne correspondent pas.")
                label_erreur.setVisible(True)
                champ_confirm.clear()
                champ_confirm.setFocus()
                return

            hash_mdp = hasher_mot_de_passe(mdp)
            db = get_db()
            db.execute(
                "UPDATE parametres SET valeur = ? WHERE cle = 'mot_de_passe_administratif'",
                (hash_mdp,),
            )
            db.execute(
                "UPDATE parametres SET valeur = '1' WHERE cle = 'mot_de_passe_actif'"
            )

            indice = champ_indice.text().strip()
            db.execute(
                "UPDATE parametres SET valeur = ? WHERE cle = 'mot_de_passe_indice'",
                (indice,),
            )

            email_recup = champ_email_recup.text().strip()
            db.execute(
                "UPDATE parametres SET valeur = ? WHERE cle = 'email_recuperation'",
                (email_recup,),
            )

            db.execute(
                "UPDATE parametres SET valeur = '0' WHERE cle = 'tentatives_echouees'"
            )

            self._mode_administratif = True
            self._maj_style_verrou()
            self._bouton_verrou_actif = True
            self._mettre_a_jour_sidebar()
            self.mode_changed.emit(True)

            QMessageBox.information(
                self,
                "Mot de passe cree",
                "Le mot de passe administratif a ete cree avec succes.\n"
                "Vous etes maintenant en mode administratif.",
            )
            dialogue.accept()

        bouton_valider.clicked.connect(valider_creation)
        champ_confirm.returnPressed.connect(valider_creation)

        dialogue.exec()

    # ------------------------------------------------------------------
    # Gestion des pages
    # ------------------------------------------------------------------

    def definir_page(self, index: int, widget: QWidget) -> None:
        """Remplace le widget placeholder à l'index donné par un vrai widget de page.

        Si l'index dépasse le nombre de pages existantes (pages cachées comme
        les fiches), le stack est étendu automatiquement.
        """
        if index < 0:
            return
        # Étendre le stack si nécessaire (pages cachées / fiches)
        while self._pile_pages.count() <= index:
            self._pile_pages.addWidget(QWidget())

        ancien_widget = self._pile_pages.widget(index)
        self._pile_pages.removeWidget(ancien_widget)
        ancien_widget.deleteLater()

        self._pile_pages.insertWidget(index, widget)

        if index == self._index_actif:
            self._pile_pages.setCurrentIndex(index)

    # ------------------------------------------------------------------
    # Boutons ronds Aide + Parametres (dans la sidebar)
    # ------------------------------------------------------------------

    def _afficher_parametres(self) -> None:
        """Navigue vers l'onglet Parametres."""
        self._changer_page(13)

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def _centrer_fenetre(self) -> None:
        """Centre la fenêtre sur l'écran principal."""
        ecran = QApplication.primaryScreen()
        if ecran is not None:
            geometrie_ecran = ecran.availableGeometry()
            taille_fenetre = self.frameGeometry()
            centre = geometrie_ecran.center()
            taille_fenetre.moveCenter(centre)
            self.move(taille_fenetre.topLeft())

    def _maj_horloge(self) -> None:
        """Met à jour l'horloge dans le SidebarHeader (chaque seconde)."""
        from datetime import datetime

        heure = datetime.now().strftime("%H:%M:%S")
        self._sidebar_header.set_clock_text(heure)

    # ------------------------------------------------------------------
    # Sidebar rétractable (hover automatique + animations)
    # ------------------------------------------------------------------

    def eventFilter(self, watched, event):
        if watched is self.sidebar and event.type() == QEvent.Type.Resize:
            for header in self.sectionheaders:
                header.updatesidebarwidth(event.size().width())
        return super().eventFilter(watched, event)

    def verifier_retracter(self) -> None:
        if not self.zone_hover:
            self.retractersidebar()

    def _calculer_interval_typewriter(self) -> int:
        """Calcule l'intervalle en ms par lettre pour synchroniser le typewriter."""
        # Durée totale de l'animation sidebar : (180 - 60) / 20 * 16 = 96ms
        duree_animation_ms = int(
            (self.largeur_etendue - self.largeur_retractee) / 20 * 16
        )
        # Collecter tous les textes visibles
        tous_textes = [item["name"] for item in _NAV_ITEMS if not item.get("hidden")]
        tous_textes += ["Nexa", self._nom_commerce, "FONCTIONNEL", "ADMINISTRATIF"]
        max_chars = max(len(t) for t in tous_textes)
        return max(1, duree_animation_ms // max_chars)

    def elargirsidebar(self) -> None:
        """Déploie la sidebar avec animation et typewriter."""
        if self.sidebar_etendue:
            return
        self.sidebar_etendue = True
        self._animation_en_cours = True

        # Mettre à jour la visibilité (sans toucher au texte car animation en cours)
        self._mettre_a_jour_sidebar()

        # Calculer l'intervalle typewriter
        interval_ms = self._calculer_interval_typewriter()

        # Lancer tous les typewriters simultanément
        self._sidebar_header.set_expanded(True, interval_ms)
        for btn in self._boutons_nav:
            if btn.isVisible():
                btn.start_typewriter(interval_ms)
        for sh in self._section_headers:
            if sh.isVisible():
                sh.set_expanded(True, interval_ms)

        # Animation de la largeur
        self.cible_width = self.largeur_etendue
        self.actuel_width = self.largeur_retractee
        self.timer_anim = QTimer()
        self.timer_anim.setInterval(16)
        self.timer_anim.timeout.connect(self._anim_etendre)
        self.timer_anim.start()

        # Flèche tourne de 0° → 90°
        if hasattr(self, "_btn_collapse"):
            self._btn_collapse.animate_to(90)

    def retractersidebar(self) -> None:
        """Rétracte la sidebar avec animation et typewriter inverse."""
        if not self.sidebar_etendue:
            return
        self.sidebar_etendue = False
        self._animation_en_cours = True

        # Calculer l'intervalle typewriter
        interval_ms = self._calculer_interval_typewriter()

        # Lancer les typewriters inverses (les éléments restent visibles pendant l'anim)
        self._sidebar_header.set_expanded(False, interval_ms)
        for btn in self._boutons_nav:
            if btn.isVisible():
                btn.start_reverse_typewriter(interval_ms)
        for sh in self._section_headers:
            if sh.isVisible():
                sh.set_expanded(False, interval_ms)

        # Animation de la largeur
        self.cible_width = self.largeur_retractee
        self.actuel_width = self.largeur_etendue
        self.timer_anim = QTimer()
        self.timer_anim.setInterval(16)
        self.timer_anim.timeout.connect(self._anim_retracter)
        self.timer_anim.start()

        # Flèche revient de 90° → 0°
        if hasattr(self, "_btn_collapse"):
            self._btn_collapse.animate_to(0)

    def _anim_etendre(self) -> None:
        """Frame d'animation d'extension de la sidebar."""
        self.actuel_width += 20
        self.sidebar.setFixedWidth(min(self.actuel_width, self.largeur_etendue))
        if self.actuel_width >= self.cible_width:
            self.sidebar.setFixedWidth(self.largeur_etendue)
            self.timer_anim.stop()
            del self.timer_anim
            self._animation_en_cours = False

    def _anim_retracter(self) -> None:
        """Frame d'animation de rétraction de la sidebar."""
        self.actuel_width -= 20
        self.sidebar.setFixedWidth(self.actuel_width)
        if self.actuel_width <= self.cible_width:
            self.sidebar.setFixedWidth(self.largeur_retractee)
            self.timer_anim.stop()
            del self.timer_anim
            self._finaliser_retraction()

    def _finaliser_retraction(self) -> None:
        """Finalise la rétraction : force l'état collapsed sur tous les widgets."""
        self._animation_en_cours = False
        self._sidebar_header.force_collapsed()
        for btn in self._boutons_nav:
            btn.reset_text()
        for sh in self._section_headers:
            sh.reset()
        self._mettre_a_jour_sidebar()

    def closeEvent(self, event: QCloseEvent):
        # Arrêter le scheduler si accessible
        scheduler = QApplication.instance()._email_scheduler
        if scheduler:
            scheduler.arreter()  # ou .stop() selon ton implémentation
        event.accept()
        QApplication.instance().quit()  # force la sortie de app.exec()

    def _sonder_hover_sidebar(self) -> None:
        pos = self.sidebar.mapFromGlobal(QCursor.pos())
        dans_sidebar = self.sidebar.rect().contains(pos)
        if dans_sidebar and not self.sidebar_etendue:
            self.elargirsidebar()
        elif not dans_sidebar and self.sidebar_etendue and not self.animationencours:
            self.retractersidebar()
