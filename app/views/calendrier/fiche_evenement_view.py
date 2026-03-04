"""Vue détail d'un événement calendrier (fiche événement)."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QGraphicsDropShadowEffect,
    QMessageBox,
    QDialog,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QDateEdit,
    QDialogButtonBox,
    QColorDialog,
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QColor

from utils.styles import Couleurs, style_scroll_area


def _shadow(blur=18, dy=4, alpha=70, color="#000"):
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(blur)
    fx.setOffset(0, dy)
    c = QColor(color)
    c.setAlpha(alpha)
    fx.setColor(c)
    return fx


class FicheEvenementView(QWidget):
    """Fiche détail d'un événement calendrier."""

    retour_demande = Signal()
    evenement_modifie = Signal()
    evenement_supprime = Signal()

    def __init__(self, parent=None):  # ← parent=None par défaut
        super().__init__(parent)
        self._evenement_id = None
        self._data = {}
        self._construire_ui()

    def _construire_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barre retour
        barre = QHBoxLayout()
        barre.setContentsMargins(24, 14, 24, 6)
        btn_retour = QPushButton("\u2190 Retour")
        btn_retour.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_retour.setStyleSheet(
            "QPushButton { background: none; border: none; color: #E65100; "
            "font-size: 12pt; font-weight: 600; padding: 6px 0; }"
            "QPushButton:hover { color: #F57C00; }"
        )
        btn_retour.clicked.connect(self.retour_demande.emit)
        barre.addWidget(btn_retour)
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
        self._build_details()

        self.layout_contenu.addStretch()
        scroll.setWidget(self.conteneur)
        layout.addWidget(scroll)

    def _build_header(self):
        self.header_frame = QFrame()
        self.header_frame.setMinimumHeight(140)
        self.header_frame.setStyleSheet(
            "QFrame {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            "    stop:0 #E65100, stop:0.45 #F57C00, stop:1 #FF9800);"
            "  border-radius: 20px;"
            "}"
        )
        self.header_frame.setGraphicsEffect(_shadow(28, 8, 90, "#E65100"))

        outer = QVBoxLayout(self.header_frame)
        outer.setContentsMargins(30, 22, 30, 22)
        outer.setSpacing(0)

        top = QHBoxLayout()
        top.setSpacing(14)

        self._lbl_icon = QLabel("📅")
        self._lbl_icon.setFixedSize(64, 64)
        self._lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_icon.setStyleSheet(
            "font-size: 22pt; background: rgba(255,255,255,0.18); "
            "border-radius: 32px; border: 2.5px solid rgba(255,255,255,0.35);"
        )
        top.addWidget(self._lbl_icon, alignment=Qt.AlignmentFlag.AlignVCenter)

        col = QVBoxLayout()
        col.setSpacing(3)
        self.label_titre = QLabel()
        self.label_titre.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.label_titre.setWordWrap(True)
        self.label_titre.setStyleSheet(
            "font-size: 18pt; font-weight: 800; color: white; border: none; background: none;"
        )
        col.addWidget(self.label_titre)

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

        # Badge couleur
        self._lbl_couleur_badge = QLabel()
        self._lbl_couleur_badge.setFixedSize(28, 28)
        self._lbl_couleur_badge.setStyleSheet(
            "background: #FF9800; border-radius: 14px; border: 2px solid rgba(255,255,255,0.5);"
        )
        top.addWidget(self._lbl_couleur_badge, alignment=Qt.AlignmentFlag.AlignVCenter)

        outer.addLayout(top)
        outer.addStretch()

        bas = QHBoxLayout()
        bas.setSpacing(16)

        self.label_dates = QLabel()
        self.label_dates.setStyleSheet(
            "font-size: 12pt; font-weight: 600; color: white; border: none; "
            "background: rgba(255,255,255,0.20); border-radius: 12px; padding: 5px 14px;"
        )
        bas.addWidget(self.label_dates)
        bas.addStretch()
        outer.addLayout(bas)

        self.layout_contenu.addWidget(self.header_frame)

    def _build_actions(self):
        self._frame_actions = QFrame()
        self._frame_actions.setStyleSheet(
            "QFrame { background: #FFF3E0; border: 1.5px solid #FFB74D; border-radius: 12px; }"
        )
        row = QHBoxLayout(self._frame_actions)
        row.setContentsMargins(16, 10, 16, 10)
        row.setSpacing(10)

        self.btn_modifier = QPushButton("✏️ Modifier")
        self.btn_modifier.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_modifier.setMinimumHeight(40)
        self.btn_modifier.setStyleSheet(
            "QPushButton { background: white; color: #FF9800; "
            "border: 1.5px solid #FF9800; border-radius: 10px; "
            "font-size: 10pt; font-weight: 600; padding: 8px 16px; }"
            "QPushButton:hover { background: #FF9800; color: white; }"
        )
        self.btn_modifier.clicked.connect(self._modifier_evenement)
        row.addWidget(self.btn_modifier)

        row.addStretch()

        self.btn_supprimer = QPushButton("Supprimer")
        self.btn_supprimer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_supprimer.setMinimumHeight(40)
        self.btn_supprimer.setStyleSheet(
            "QPushButton { background: white; color: #F44336; "
            "border: 1.5px solid #F44336; border-radius: 10px; "
            "font-size: 10pt; font-weight: 600; padding: 8px 16px; }"
            "QPushButton:hover { background: #F44336; color: white; }"
        )
        self.btn_supprimer.clicked.connect(self._supprimer)
        row.addWidget(self.btn_supprimer)

        self.layout_contenu.addWidget(self._frame_actions)

    def _build_details(self):
        self._details_card = QFrame()
        self._details_card.setStyleSheet(
            "QFrame { background: #FFF3E0; border: 1.5px solid #FFB74D; border-radius: 14px; }"
        )
        lay = QVBoxLayout(self._details_card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        lbl_t = QLabel("Description")
        lbl_t.setStyleSheet(
            "font-size: 12pt; font-weight: 700; color: #E65100; "
            "border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)

        self.label_description = QLabel()
        self.label_description.setWordWrap(True)
        self.label_description.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.label_description.setStyleSheet(
            "font-size: 10pt; color: #263238; border: none; background: none; padding: 8px;"
        )
        lay.addWidget(self.label_description)

        self._details_card.hide()
        self.layout_contenu.addWidget(self._details_card)

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    def charger_evenement(self, evenement_id: int):
        from models.evenement import EvenementModel

        data = EvenementModel().obtenir_evenement(evenement_id)
        if not data:
            return

        self._evenement_id = evenement_id
        self._data = data

        nom = data.get("nom", "Sans nom")
        couleur = data.get("couleur", "#FF9800")
        desc = (data.get("description") or "").strip()
        date_debut = data.get("date_debut", "")
        date_fin = data.get("date_fin", "")

        # Header
        self.label_titre.setText(nom)
        self._lbl_ref.setText(f"ÉVÉNEMENT \u00b7 #{evenement_id}")

        # Couleur badge + header gradient
        self._lbl_couleur_badge.setStyleSheet(
            f"background: {couleur}; border-radius: 14px; "
            f"border: 2px solid rgba(255,255,255,0.5);"
        )
        self.header_frame.setStyleSheet(
            "QFrame {"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            f"    stop:0 {couleur}, stop:1 #FF9800);"
            "  border-radius: 20px;"
            "}"
        )

        # Dates
        if date_debut and date_fin:
            self.label_dates.setText(f"📅  {date_debut}  →  {date_fin}")
        elif date_debut:
            self.label_dates.setText(f"📅  {date_debut}")
        else:
            self.label_dates.setText("Pas de date définie")

        # Description
        if desc:
            self.label_description.setText(desc)
            self._details_card.show()
        else:
            self._details_card.hide()

    def _modifier_evenement(self):
        if not self._evenement_id:
            return

        data = self._data
        dlg = QDialog(self)
        dlg.setWindowTitle("Modifier l'événement")
        dlg.setMinimumWidth(420)
        dlg.setStyleSheet("QDialog { background: #FAFAFA; }")

        input_style = (
            "QLineEdit, QTextEdit, QDateEdit {"
            "    min-height: 34px; font-size: 11pt; padding: 4px 8px;"
            "    border: 1.5px solid #E0E0E0; border-radius: 6px; background: white;"
            "}"
        )
        dlg.setStyleSheet(dlg.styleSheet() + input_style)

        form = QFormLayout(dlg)
        form.setSpacing(10)

        input_nom = QLineEdit(data.get("nom", ""))
        form.addRow("Nom :", input_nom)

        input_desc = QTextEdit()
        input_desc.setPlainText(data.get("description", ""))
        input_desc.setMaximumHeight(100)
        form.addRow("Description :", input_desc)

        # Couleur
        self._edit_couleur = data.get("couleur", "#FF9800")
        btn_couleur = QPushButton(f"  {self._edit_couleur}  ")
        btn_couleur.setStyleSheet(
            f"background: {self._edit_couleur}; color: white; border-radius: 6px; "
            f"font-weight: bold; padding: 6px 16px;"
        )

        def choisir_couleur():
            c = QColorDialog.getColor(QColor(self._edit_couleur), dlg, "Couleur")
            if c.isValid():
                self._edit_couleur = c.name()
                btn_couleur.setText(f"  {self._edit_couleur}  ")
                btn_couleur.setStyleSheet(
                    f"background: {self._edit_couleur}; color: white; "
                    f"border-radius: 6px; font-weight: bold; padding: 6px 16px;"
                )

        btn_couleur.clicked.connect(choisir_couleur)
        form.addRow("Couleur :", btn_couleur)

        date_debut_edit = QDateEdit()
        dd = data.get("date_debut", "")
        if dd:
            date_debut_edit.setDate(QDate.fromString(dd[:10], "yyyy-MM-dd"))
        else:
            date_debut_edit.setDate(QDate.currentDate())
        date_debut_edit.setCalendarPopup(True)
        form.addRow("Date début :", date_debut_edit)

        date_fin_edit = QDateEdit()
        df = data.get("date_fin", "")
        if df:
            date_fin_edit.setDate(QDate.fromString(df[:10], "yyyy-MM-dd"))
        else:
            date_fin_edit.setDate(QDate.currentDate())
        date_fin_edit.setCalendarPopup(True)
        form.addRow("Date fin :", date_fin_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            from models.evenement import EvenementModel

            EvenementModel().modifier_evenement(
                self._evenement_id,
                {
                    "nom": input_nom.text().strip(),
                    "description": input_desc.toPlainText().strip(),
                    "couleur": self._edit_couleur,
                    "date_debut": date_debut_edit.date().toString("yyyy-MM-dd"),
                    "date_fin": date_fin_edit.date().toString("yyyy-MM-dd"),
                },
            )
            self.charger_evenement(self._evenement_id)
            self.evenement_modifie.emit()

    def _supprimer(self):
        if not self._evenement_id:
            return
        rep = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment supprimer cet événement ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            from models.evenement import EvenementModel

            EvenementModel().supprimer_evenement(self._evenement_id)
            self.evenement_supprime.emit()
            self.retour_demande.emit()
