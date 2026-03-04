"""
Composant toggle Brouillon / Template avec design distinct.

Deux cartes côte à côte : une ambre pour les brouillons,
une bleue pour les templates, avec icônes et descriptions.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPen, QLinearGradient,
    QPainterPath, QBrush,
)


class _ToggleCard(QWidget):
    """Carte individuelle pour un mode (brouillon ou template)."""

    clicked = Signal()

    def __init__(
        self,
        icon_char: str,
        title: str,
        subtitle: str,
        gradient_start: str,
        gradient_end: str,
        accent_color: str,
        parent=None,
    ):
        super().__init__(parent)
        self._icon = icon_char
        self._title = title
        self._subtitle = subtitle
        self._grad_start = QColor(gradient_start)
        self._grad_end = QColor(gradient_end)
        self._accent = QColor(accent_color)
        self._selected = False
        self._hover = False
        self._blend = 0.0  # 0 = non sélectionné, 1 = sélectionné

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(62)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._anim = QPropertyAnimation(self, b"blend")
        self._anim.setDuration(280)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # --- Property pour QPropertyAnimation ---
    def _get_blend(self):
        return self._blend

    def _set_blend(self, v):
        self._blend = v
        self.update()

    blend = Property(float, _get_blend, _set_blend)

    def set_selected(self, selected: bool, animate: bool = True):
        if self._selected == selected:
            return
        self._selected = selected
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._blend)
            self._anim.setEndValue(1.0 if selected else 0.0)
            self._anim.start()
        else:
            self._blend = 1.0 if selected else 0.0
            self.update()

    def mousePressEvent(self, event):
        self.clicked.emit()

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        radius = 14.0
        b = self._blend

        # --- Fond ---
        path = QPainterPath()
        path.addRoundedRect(1.0, 1.0, w - 2.0, h - 2.0, radius, radius)

        if b > 0.01:
            grad = QLinearGradient(0, 0, w, h)
            grad.setColorAt(0, self._grad_start)
            grad.setColorAt(1, self._grad_end)
            p.setOpacity(b)
            p.fillPath(path, QBrush(grad))
            p.setOpacity(1.0)

        # Fond non-sélectionné (blanc/gris)
        if b < 0.99:
            bg = QColor("#FAFAFA") if not self._hover else QColor("#F0F0F0")
            p.setOpacity(1.0 - b)
            p.fillPath(path, QBrush(bg))
            p.setOpacity(1.0)

        # --- Bordure ---
        border_color = QColor(self._accent)
        border_color.setAlpha(int(40 + 140 * b))
        if self._hover and b < 0.5:
            border_color.setAlpha(120)
        p.setPen(QPen(border_color, 1.5))
        p.drawRoundedRect(1.0, 1.0, w - 2.0, h - 2.0, radius, radius)

        # --- Icône ---
        icon_x = 16
        icon_y = h / 2 - 10
        icon_font = QFont()
        icon_font.setPointSize(18)
        p.setFont(icon_font)
        icon_color = QColor("#FFFFFF") if b > 0.5 else self._accent
        p.setPen(icon_color)
        p.drawText(int(icon_x), int(icon_y), 28, 24, Qt.AlignmentFlag.AlignCenter, self._icon)

        # --- Titre ---
        title_x = icon_x + 34
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setWeight(QFont.Weight.DemiBold)
        p.setFont(title_font)
        title_color = QColor("#FFFFFF") if b > 0.5 else QColor("#333333")
        p.setPen(title_color)
        p.drawText(int(title_x), 10, w - title_x - 12, 22, Qt.AlignmentFlag.AlignVCenter, self._title)

        # --- Sous-titre ---
        sub_font = QFont()
        sub_font.setPointSize(9)
        p.setFont(sub_font)
        sub_color = QColor(255, 255, 255, int(180 * b + 140 * (1 - b)))
        if b < 0.5:
            sub_color = QColor("#999999")
        p.setPen(sub_color)
        p.drawText(int(title_x), 30, w - title_x - 12, 22, Qt.AlignmentFlag.AlignVCenter, self._subtitle)

        p.end()


class DraftTemplateToggle(QWidget):
    """Toggle Brouillon / Template avec deux cartes visuellement distinctes.

    Signal : selectionChanged(int) — 0 = Templates, 1 = Brouillons
    (compatible avec l'ancienne API ModernSegmentedControl).
    """

    selectionChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_index = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(10)

        self._card_templates = _ToggleCard(
            icon_char="\U0001F4C4",  # 📄
            title="Templates",
            subtitle="Modeles reutilisables",
            gradient_start="#3B82F6",
            gradient_end="#1D4ED8",
            accent_color="#3B82F6",
        )
        self._card_brouillons = _ToggleCard(
            icon_char="\u270F\uFE0F",  # ✏️
            title="Brouillons",
            subtitle="Emails en cours",
            gradient_start="#F59E0B",
            gradient_end="#D97706",
            accent_color="#F59E0B",
        )

        layout.addWidget(self._card_templates)
        layout.addWidget(self._card_brouillons)

        self._card_templates.clicked.connect(lambda: self.select(0))
        self._card_brouillons.clicked.connect(lambda: self.select(1))

        # État initial
        self._card_templates.set_selected(True, animate=False)
        self._card_brouillons.set_selected(False, animate=False)

        self.setFixedHeight(70)

    def select(self, index: int):
        if index == self.current_index:
            return
        self.current_index = index
        self._card_templates.set_selected(index == 0)
        self._card_brouillons.set_selected(index == 1)
        self.selectionChanged.emit(index)
