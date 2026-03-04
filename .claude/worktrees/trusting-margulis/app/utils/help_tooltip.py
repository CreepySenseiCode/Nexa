"""Widget d'aide contextuelle (tooltip avec bouton '?')."""

from PySide6.QtWidgets import QPushButton, QMessageBox, QToolTip
from PySide6.QtCore import Qt


class HelpTooltip(QPushButton):
    """Bouton d'aide avec tooltip."""

    def __init__(self, help_text: str, parent=None):
        super().__init__("?", parent)
        self.help_text = help_text

        self.setFixedSize(24, 24)
        self.setCursor(Qt.CursorShape.WhatsThisCursor)

        self.setStyleSheet(
            "QPushButton {"
            "    background-color: #2196F3;"
            "    color: white;"
            "    border: none;"
            "    border-radius: 12px;"
            "    font-size: 14pt;"
            "    font-weight: bold;"
            "}"
            "QPushButton:hover {"
            "    background-color: #1976D2;"
            "}"
        )

        self.clicked.connect(self._show_help)

    def _show_help(self):
        """Affiche un popup avec l'aide."""
        QMessageBox.information(self, "Aide", self.help_text)

    def enterEvent(self, event):
        """Affiche le tooltip au survol."""
        QToolTip.showText(event.globalPosition().toPoint(), self.help_text, self)
        super().enterEvent(event)
