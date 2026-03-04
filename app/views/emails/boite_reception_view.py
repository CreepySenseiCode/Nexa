"""Vue Boite de reception - Affiche les emails reçus."""

import logging

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QScrollArea,
    QFrame,
    QStackedWidget,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QThread, Signal as QtSignal
from PySide6.QtGui import QColor

from utils.styles import Couleurs
from viewmodels.boite_reception_vm import BoiteReceptionViewModel
from utils.email_receiver import EmailReceiver

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _shadow(blur=18, dy=4, alpha=60, color="#000"):
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(blur)
    fx.setOffset(0, dy)
    c = QColor(color)
    c.setAlpha(alpha)
    fx.setColor(c)
    return fx


_AVATAR_COLORS = [
    "#1565C0",
    "#2E7D32",
    "#6A1B9A",
    "#E65100",
    "#00695C",
    "#AD1457",
    "#0277BD",
    "#558B2F",
]


def _avatar_color(text: str) -> str:
    return (
        _AVATAR_COLORS[ord(text[0].upper()) % len(_AVATAR_COLORS)]
        if text
        else "#9E9E9E"
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Thread IMAP
# ─────────────────────────────────────────────────────────────────────────────


class _RecevoirThread(QThread):
    termine = QtSignal(dict)

    def __init__(self, receiver: EmailReceiver, parent=None):
        super().__init__(parent)
        self._receiver = receiver

    def run(self):
        self.termine.emit(self._receiver.recuperer_tous_comptes())


# ─────────────────────────────────────────────────────────────────────────────
#  Widget ligne email
# ─────────────────────────────────────────────────────────────────────────────


class EmailRowWidget(QFrame):
    """Une ligne email cliquable dans la liste."""

    clicked = QtSignal(int)  # email_id

    def __init__(self, email_data: dict, parent=None):
        super().__init__(parent)
        self._email_id = email_data.get("id")
        self._lu = bool(email_data.get("lu", False))
        self._bg = "#FFFFFF" if self._lu else "#EFF6FF"
        self._construire(email_data)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(76)
        self._appliquer_style(False)

    def _construire(self, d: dict):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 10, 16, 10)
        outer.setSpacing(12)

        # Dot non-lu
        dot = QWidget(self)
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(
            f"background: {'#1976D2' if not self._lu else 'transparent'};"
            " border-radius: 4px;"
        )
        outer.addWidget(dot, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Avatar initiales
        exp_nom = d.get("expediteur_nom") or d.get("expediteur_email", "?")
        initiale = exp_nom[0].upper() if exp_nom else "?"
        avatar = QLabel(initiale, self)
        avatar.setFixedSize(44, 44)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            f"background: {_avatar_color(exp_nom)}; color: white; border-radius: 22px;"
            " font-size: 14pt; font-weight: 700;"
        )
        outer.addWidget(avatar)

        # Infos centre
        infos = QVBoxLayout()
        infos.setSpacing(3)
        weight = "700" if not self._lu else "400"

        lbl_exp = QLabel(exp_nom[:45] + ("…" if len(exp_nom) > 45 else ""), self)
        lbl_exp.setStyleSheet(
            f"font-size: 12pt; font-weight: {weight}; color: #0D1B2A;"
        )
        infos.addWidget(lbl_exp)

        objet = d.get("objet") or "(Sans objet)"
        lbl_obj = QLabel(objet[:70] + ("…" if len(objet) > 70 else ""), self)
        lbl_obj.setStyleSheet(f"font-size: 10pt; font-weight: {weight}; color: #666;")
        infos.addWidget(lbl_obj)
        outer.addLayout(infos, stretch=1)

        # Droite date + pj
        right = QVBoxLayout()
        right.setSpacing(6)
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl_date = QLabel(str(d.get("date_reception", ""))[:16], self)
        lbl_date.setStyleSheet("font-size: 9pt; color: #999;")
        lbl_date.setAlignment(Qt.AlignmentFlag.AlignRight)
        right.addWidget(lbl_date)
        if d.get("pieces_jointes"):
            lbl_pj = QLabel("📎", self)
            lbl_pj.setAlignment(Qt.AlignmentFlag.AlignRight)
            right.addWidget(lbl_pj)
        outer.addLayout(right)

    def _appliquer_style(self, hovered: bool):
        bg = "#DBEAFE" if hovered else self._bg
        self.setStyleSheet(
            f"EmailRowWidget {{ background: {bg}; border-radius: 12px; border: none; }}"
        )

    def enterEvent(self, e):
        self._appliquer_style(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._appliquer_style(False)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self._email_id is not None:
            self.clicked.emit(self._email_id)
        super().mousePressEvent(e)


# ─────────────────────────────────────────────────────────────────────────────
#  Vue principale
# ─────────────────────────────────────────────────────────────────────────────


class BoiteReceptionView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewmodel = BoiteReceptionViewModel()
        self._receiver = EmailReceiver()
        self._emails_data: list = []
        self._recv_thread = None
        self._construire_ui()
        self._charger_comptes_combo()
        self._charger_emails()

    def _construire_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setStyleSheet("background: #F0F4F8;")

        self._stack = QStackedWidget(self)
        self._stack.addWidget(self._construire_page_liste())

        from views.emails.fiche_email_view import FicheEmailView

        self._fiche = FicheEmailView(parent=self)
        self._fiche.retour_demande.connect(self._retour_liste)
        self._fiche.email_supprime.connect(self._on_email_supprime)
        self._stack.addWidget(self._fiche)

        root.addWidget(self._stack)

    def _construire_page_liste(self) -> QWidget:
        page = QWidget(self)
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(16)

        # Header
        top = QHBoxLayout()
        top.setSpacing(12)
        titre_row = QHBoxLayout()
        titre_row.setSpacing(8)
        titre_row.addWidget(
            QLabel(
                "Boîte de réception",
                styleSheet="font-size: 20pt; font-weight: 800; color: #0D1B2A;",
            )
        )
        self._badge_nonlus = QLabel(
            "",
            styleSheet="background: #1976D2; color: white; border-radius: 12px; font-size: 9pt; font-weight: 700; padding: 0 9px;",
        )
        self._badge_nonlus.setFixedHeight(24)
        self._badge_nonlus.hide()
        titre_row.addWidget(self._badge_nonlus, alignment=Qt.AlignmentFlag.AlignVCenter)
        titre_row.addStretch()
        top.addLayout(titre_row, stretch=1)

        self._combo_filtre = QComboBox(self)
        self._combo_filtre.setFixedHeight(38)
        self._combo_filtre.setMinimumWidth(210)
        self._combo_filtre.setStyleSheet(
            "QComboBox { border: 1.5px solid #DDE3EE; border-radius: 10px;"
            " padding: 4px 12px; font-size: 11pt; background: white; color: #333; }"
            "QComboBox::drop-down { border: none; width: 28px; }"
            "QComboBox:focus { border: 1.5px solid #1976D2; }"
        )
        self._combo_filtre.currentIndexChanged.connect(self._charger_emails)
        top.addWidget(self._combo_filtre)

        self._btn_refresh = QPushButton("↻  Relever le courrier")
        self._btn_refresh.setFixedHeight(38)
        self._btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_refresh.setStyleSheet(
            "QPushButton { background: #1976D2; color: white; border: none;"
            " border-radius: 10px; font-size: 11pt; font-weight: 600; padding: 0 16px; }"
            "QPushButton:hover { background: #1565C0; }"
            "QPushButton:disabled { background: #B0BEC5; }"
        )
        self._btn_refresh.clicked.connect(self._relever_courrier)
        top.addWidget(self._btn_refresh)
        lay.addLayout(top)

        # Recherche
        self._input_recherche = QLineEdit(
            placeholderText="🔍  Rechercher par expéditeur, objet…"
        )
        self._input_recherche.setFixedHeight(44)
        self._input_recherche.setStyleSheet(
            "QLineEdit { border: 1.5px solid #DDE3EE; border-radius: 12px;"
            " padding: 6px 18px; font-size: 12pt; background: white; color: #1A1A2E; }"
            "QLineEdit:focus { border: 1.5px solid #1976D2; }"
        )
        self._input_recherche.textChanged.connect(self._filtrer_emails)
        lay.addWidget(self._input_recherche)

        # Liste scrollable
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._liste_container = QWidget()
        self._liste_container.setStyleSheet("background: transparent;")
        self._liste_layout = QVBoxLayout(self._liste_container)
        self._liste_layout.setContentsMargins(0, 0, 4, 0)
        self._liste_layout.setSpacing(4)
        self._liste_layout.addStretch()
        scroll.setWidget(self._liste_container)
        lay.addWidget(scroll, stretch=1)

        self._lbl_stats = QLabel(
            "", styleSheet="font-size: 10pt; color: #94A3B8; padding: 2px 0;"
        )
        lay.addWidget(self._lbl_stats)
        return page

    def _charger_comptes_combo(self):
        self._combo_filtre.blockSignals(True)
        self._combo_filtre.clear()
        self._combo_filtre.addItem("📥  Toutes les boîtes", userData=None)
        try:
            from models.database import get_db

            for c in get_db().fetchall(
                "SELECT adresse_email FROM comptes_email WHERE actif = 1"
            ):
                adr = c["adresse_email"]
                self._combo_filtre.addItem(f"📧  {adr}", userData=adr)
        except Exception:
            pass
        self._combo_filtre.blockSignals(False)

    def _charger_emails(self):
        while self._liste_layout.count() > 1:
            item = self._liste_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        adresse = self._combo_filtre.currentData() or "Toutes les boîtes"
        emails = self.viewmodel.charger_emails(adresse)
        self._emails_data = emails

        nb_total = len(emails)
        nb_non_lus = sum(1 for e in emails if not e.get("lu"))

        if nb_non_lus > 0:
            self._badge_nonlus.setText(str(nb_non_lus))
            self._badge_nonlus.show()
        else:
            self._badge_nonlus.hide()

        for i, email_data in enumerate(emails):
            row = EmailRowWidget(email_data, parent=self._liste_container)
            row.clicked.connect(self._ouvrir_email_par_id)
            self._liste_layout.insertWidget(i, row)

        compte_info = (
            f"  ·  {self._combo_filtre.currentData()}"
            if self._combo_filtre.currentData()
            else ""
        )
        self._lbl_stats.setText(
            f"{nb_total} email{'s' if nb_total > 1 else ''}{compte_info}"
            f"  ·  {nb_non_lus} non lu{'s' if nb_non_lus > 1 else ''}"
        )

    def _filtrer_emails(self):
        texte = self._input_recherche.text().strip().lower()
        for i in range(self._liste_layout.count() - 1):
            item = self._liste_layout.itemAt(i)
            if not item or not isinstance(item.widget(), EmailRowWidget):
                continue
            w = item.widget()
            if not texte:
                w.show()
                continue
            textes = " ".join(lbl.text().lower() for lbl in w.findChildren(QLabel))
            w.setVisible(texte in textes)

    def _relever_courrier(self):
        self._btn_refresh.setEnabled(False)
        self._btn_refresh.setText("Réception en cours…")
        self._recv_thread = _RecevoirThread(self._receiver, parent=self)
        self._recv_thread.termine.connect(self._on_reception_terminee)
        self._recv_thread.start()

    def _on_reception_terminee(self, result: dict):
        self._btn_refresh.setEnabled(True)
        self._btn_refresh.setText("↻  Relever le courrier")
        from PySide6.QtWidgets import QMessageBox

        nb = result.get("nb_total", 0)
        erreurs = result.get("erreurs", [])
        if erreurs:
            QMessageBox.warning(
                self, "Erreurs", f"{nb} reçu(s).\n" + "\n".join(erreurs)
            )
        elif nb > 0:
            QMessageBox.information(
                self, "Courrier relevé", f"{nb} nouveau(x) email(s)."
            )
        else:
            QMessageBox.information(self, "Courrier relevé", "Aucun nouveau message.")
        self._charger_emails()

    def _ouvrir_email_par_id(self, email_id: int):
        self._fiche.charger_email(email_id)
        self._stack.setCurrentIndex(1)

    def _retour_liste(self):
        self._stack.setCurrentIndex(0)
        self._charger_emails()

    def _on_email_supprime(self):
        self._stack.setCurrentIndex(0)
        self._charger_emails()
