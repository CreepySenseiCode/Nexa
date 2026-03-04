import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QGraphicsDropShadowEffect,
    QStyleOptionButton,
    QStyle,
    QSizePolicy,
)
from PySide6.QtCore import (
    Qt,
    Property,
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QPalette, QLinearGradient, QPainter


class AnimatedButton(QPushButton):

    def __init__(self, text, parent=None):  # ← parent=None par défaut
        super().__init__(text, parent)
        self._scale = 1.0
        self._hovered = False
        self._pressed = False
        self.setMouseTracking(True)

        self.scale_anim = QPropertyAnimation(self, b"scale")
        self.scale_anim.setDuration(120)
        self.scale_anim.setEasingCurve(QEasingCurve.OutCubic)

    def mousePressEvent(self, event):
        self._pressed = True
        self.animate_scale(0.92)
        super().mousePressEvent(event)
        self.scale_anim.setEasingCurve(QEasingCurve.InCubic)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        if self._hovered:
            self.animate_scale(1.05)
        else:
            self.animate_scale(1.0)
        super().mouseReleaseEvent(event)
        self.scale_anim.setEasingCurve(QEasingCurve.OutBack)

    def animate_scale(self, target):
        self.scale_anim.stop()
        self.scale_anim.setStartValue(self._scale)
        self.scale_anim.setEndValue(target)
        self.scale_anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._scale, self._scale)
        painter.translate(-self.width() / 2, -self.height() / 2)

        # Dessiner le fond (transparent ici)
        if self.isDown():
            painter.setOpacity(0.9)

        # Dessiner le texte
        painter.setPen(self.palette().color(QPalette.ButtonText))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())

    def getScale(self):
        return self._scale

    def setScale(self, value):
        self._scale = value
        self.update()

    scale = Property(float, getScale, setScale)

    def enterEvent(self, event):
        self._hovered = True
        if not self._pressed:
            self.animate_scale(1.05)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        if not self._pressed:
            self.animate_scale(1.0)
        super().leaveEvent(event)


# -----------------------------
# Segmented Control moderne
# -----------------------------
class ModernSegmentedControl(QWidget):

    selectionChanged = Signal(int)

    def __init__(self, labels, initial_index=0, style="default"):
        super().__init__()

        self._style = style
        if style == "compact":
            self._visual_height = 32
            self._shadow_margin = 8
            self._font_size = 12
            self._padding = 14
        else:
            self._visual_height = 40
            self._shadow_margin = 10
            self._font_size = 15
            self._padding = 24

        self.setFixedHeight(self._visual_height)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self._is_animating = False
        self._indicator_ready = False

        palette = QApplication.palette()
        self.is_dark = palette.color(QPalette.Window).lightness() < 128

        # Couleurs SaaS
        if self.is_dark:
            self.gradient_start = "#1e3a8a"
            self.gradient_end = "#2563eb"
            self.indicator_color = "#ffffff"
            self.active_text = "#0f172a"
            self.inactive_text = "#e2e8f0"
        elif style == "compact":
            self.gradient_start = "#60a5fa"
            self.gradient_end = "#3b82f6"
            self.indicator_color = "#ffffff"
            self.active_text = "#3b82f6"
            self.inactive_text = "#ffffff"
        else:
            self.gradient_start = "#3b82f6"
            self.gradient_end = "#2563eb"
            self.indicator_color = "#ffffff"
            self.active_text = "#2563eb"
            self.inactive_text = "#ffffff"

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(
            2,
            self._shadow_margin,
            2,
            self._shadow_margin,
        )

        self.layout.setSpacing(8)

        self.buttons = []
        for i, text in enumerate(labels):
            btn = AnimatedButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)

            fm = btn.fontMetrics()
            text_width = fm.horizontalAdvance(text)

            btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
            btn.setMinimumWidth(text_width + self._padding)

            btn.setStyleSheet(
                f"""
                QPushButton {{
                    border: none;
                    background: transparent;
                    color: {self.inactive_text};
                    font-weight: 600;
                    font-size: {self._font_size}px;
                }}

                QPushButton:checked {{
                    color: {self.active_text};
                    font-weight: 700;
                }}
                """
            )

            btn.clicked.connect(lambda checked, index=i: self.select(index))
            self.layout.addWidget(btn)
            self.buttons.append(btn)

        # Indicateur
        self.indicator = QWidget(self)
        self.indicator.lower()

        self.glow = QGraphicsDropShadowEffect(self.indicator)
        self.glow.setBlurRadius(20)
        self.glow.setOffset(0, 0)
        self.glow.setColor(QColor(255, 255, 255, 120))
        self.indicator.setGraphicsEffect(self.glow)

        self._pos = 0
        self.current_index = initial_index
        self.anim = QPropertyAnimation(self, b"indicator_pos")
        self.width_anim = QPropertyAnimation(self, b"indicator_width")

        duration = 450

        self.anim.setDuration(duration)
        self.width_anim.setDuration(duration)

        curve = QEasingCurve(QEasingCurve.OutBack)
        curve.setOvershoot(0.8)  # 0.5 à 0.8 = subtil et élégant
        self.anim.setEasingCurve(curve)

        self.width_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.anim_group = QParallelAnimationGroup(self)
        self.anim_group.addAnimation(self.anim)
        self.anim_group.addAnimation(self.width_anim)

        self.anim_group.finished.connect(self._apply_styles)
        self.anim_group.finished.connect(self._on_anim_finished)

        # Appliquer les styles texte immédiatement (pas besoin de layout)
        self._apply_styles()

        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

    # Gradient dynamique
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient = QLinearGradient(0, 0, self.width(), 0)

        gradient.setColorAt(0, QColor(self.gradient_start))
        gradient.setColorAt(1, QColor(self.gradient_end))

        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Le resizeEvent est le premier moment fiable où les boutons ont
        # leur géométrie finale. On place l'indicateur ici.
        self._place_indicator()

    def _place_indicator(self):
        """Positionne l'indicateur directement (sans animation)."""
        if self.current_index < 0 or self.current_index >= len(self.buttons):
            return

        btn = self.buttons[self.current_index]
        if btn.width() == 0:
            return

        fm = btn.fontMetrics()
        text_width = fm.horizontalAdvance(btn.text())
        indicator_width = text_width + self._padding
        height = self._visual_height - 14

        btn_x = btn.geometry().left()
        btn_width = btn.width()
        x = btn_x + (btn_width - indicator_width) / 2

        self.indicator.setGeometry(
            int(x),
            self._shadow_margin - 3,
            int(indicator_width),
            height,
        )

        self.indicator.setStyleSheet(
            f"""
            background-color: {self.indicator_color};
            border-radius: {height // 2}px;
        """
        )

        self._indicator_ready = True

    def select(self, index):

        if index == self.current_index:
            return

        old_index = self.current_index
        self.current_index = index

        btn = self.buttons[index]

        # Si l'indicateur n'est pas encore prêt (premier affichage),
        # juste mettre à jour les styles. Le resizeEvent placera l'indicateur.
        if not self._indicator_ready or btn.width() == 0:
            self._apply_styles()
            return

        # Animation normale (clic utilisateur)
        fm = btn.fontMetrics()
        text_width = fm.horizontalAdvance(btn.text())
        indicator_width = text_width + self._padding

        btn_x = btn.x()
        btn_width = btn.width()

        target_x = btn_x + (btn_width - indicator_width) / 2

        if self.anim_group.state() == QParallelAnimationGroup.Running:
            self.anim_group.stop()

        self.anim_group.stop()

        self.anim.setStartValue(self.indicator.x())
        self.anim.setEndValue(target_x)

        start_width = indicator_width * 0.40
        self.width_anim.setStartValue(start_width)
        self.width_anim.setEndValue(indicator_width)

        self._is_animating = True

        self.update()

        self.anim_group.start()

        self.selectionChanged.emit(index)

        self._apply_styles()

    def get_indicator_pos(self):
        return self._pos

    def set_indicator_pos(self, value):
        self._pos = value

        width = self.indicator.width()
        height = self.indicator.height()

        self.indicator.setGeometry(
            int(value),
            self._shadow_margin - 3,
            width,
            height,
        )

    indicator_pos = Property(float, get_indicator_pos, set_indicator_pos)

    def get_indicator_width(self):
        return self.indicator.width()

    def set_indicator_width(self, value):
        self.indicator.resize(int(value), self.indicator.height())

    indicator_width = Property(float, get_indicator_width, set_indicator_width)

    def _apply_styles(self):
        for i, btn in enumerate(self.buttons):
            if i == self.current_index:
                btn.setStyleSheet(
                    f"""
                    QPushButton {{
                        border: none;
                        background: transparent;
                        color: {self.active_text};
                        font-weight: 700;
                        font-size: {self._font_size}px;
                    }}
                    """
                )
            else:
                btn.setStyleSheet(
                    f"""
                    QPushButton {{
                        border: none;
                        background: transparent;
                        color: {self.inactive_text};
                        font-weight: 600;
                        font-size: {self._font_size}px;
                    }}
                    """
                )

    def _on_anim_finished(self):
        self._is_animating = False
