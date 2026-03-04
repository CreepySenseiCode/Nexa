"""Vue pour l'onglet Aide - Chatbot interactif."""

from PySide6.QtWidgets import (
    QWidget,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QLineEdit,
    QFrame,
)
from PySide6.QtGui import (
    QFont,
    QPixmap,
    QPainter,
    QColor,
    QPainterPath,
    QBrush,
    QLinearGradient,
)
from PySide6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    Property,
    QPointF,
)
from typing import Optional

from .aide_data import FAQ_DATA


EMAIL_SUPPORT = "nexa.requests@gmail.com"
AVATAR_PATH = "app/assets/icons/logo_base.png"


# ═══════════════════════════════════════════════════════════════════════════════
#  Styles centralisés
# ═══════════════════════════════════════════════════════════════════════════════

S_SCROLL = "QScrollArea { border: none; background-color: #F0F4F8; }"
S_CHAT = "background-color: #F0F4F8;"

S_BULLE_BOT = (
    "QLabel {"
    "    background-color: #FFFFFF;"
    "    color: #1A1A2E;"
    "    border: 1px solid #DDE3EE;"
    "    border-radius: 20px;"
    "    border-top-left-radius: 5px;"
    "    padding: 18px 24px;"
    "    font-size: 14pt;"
    "}"
)
S_BULLE_USER = (
    "QLabel {"
    "    background-color: #1976D2;"
    "    color: #FFFFFF;"
    "    border-radius: 20px;"
    "    border-top-right-radius: 5px;"
    "    padding: 18px 24px;"
    "    font-size: 14pt;"
    "}"
)

S_INPUT = (
    "QLineEdit {"
    "    border: 2px solid #DDE3EE;"
    "    border-radius: 24px;"
    "    padding: 10px 20px;"
    "    font-size: 13pt;"
    "    background-color: #F9FAFC;"
    "    color: #1A1A2E;"
    "}"
    "QLineEdit:focus {"
    "    border: 2px solid #1976D2;"
    "    background-color: #FFFFFF;"
    "}"
)

S_SUGGESTION = (
    "QPushButton {"
    "    background-color: #EEF4FF;"
    "    color: #1565C0;"
    "    border: 1px solid #C5D8FF;"
    "    border-radius: 10px;"
    "    padding: 10px 16px;"
    "    font-size: 12pt;"
    "    text-align: left;"
    "}"
    "QPushButton:hover  { background-color: #DDEAFF; }"
    "QPushButton:pressed{ background-color: #BDD1FF; }"
)

S_BTN_OUI = (
    "QPushButton {"
    "    background-color: #E8F5E9; color: #2E7D32;"
    "    border: 1.5px solid #A5D6A7; border-radius: 10px;"
    "    padding: 10px 22px; font-size: 12pt; font-weight: 700;"
    "}"
    "QPushButton:hover { background-color: #C8E6C9; }"
)
S_BTN_NON = (
    "QPushButton {"
    "    background-color: #FFF3E0; color: #E65100;"
    "    border: 1.5px solid #FFCC80; border-radius: 10px;"
    "    padding: 10px 22px; font-size: 12pt; font-weight: 700;"
    "}"
    "QPushButton:hover { background-color: #FFE0B2; }"
)
S_BTN_RESET = (
    "QPushButton {"
    "    background-color: #F3F4F6; color: #555;"
    "    border: 1.5px solid #D1D5DB; border-radius: 10px;"
    "    padding: 10px 22px; font-size: 12pt;"
    "}"
    "QPushButton:hover { background-color: #E5E7EB; }"
)
S_BTN_ANNULER = (
    "QPushButton {"
    "    background-color: #FFEBEE; color: #C62828;"
    "    border: 1.5px solid #FFCDD2; border-radius: 8px;"
    "    padding: 7px 16px; font-size: 11pt;"
    "}"
    "QPushButton:hover { background-color: #FFCDD2; }"
)

# Indentation pour aligner les widgets sous le texte bot (avatar 46px + spacing 12px)
INDENT_BOT = 58


class AnimatedLogo(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(46, 46)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self._outer_rotation = 0.0
        self._inner_rotation = 0.0
        self.is_animating = False

        self._src_pixmap = QPixmap("app/assets/icons/help_assistant.png")
        if self._src_pixmap.isNull():
            self._src_pixmap = QPixmap("app/assets/icons/nexa_logo.png")

        self.logo_pixmap = QPixmap()
        self._preparer_pixmap()  # ← appel direct ici, plus besoin de showEvent
        self.setup_animations()

    def _preparer_pixmap(self):
        if self._src_pixmap.isNull():
            return
        screen = QApplication.primaryScreen()
        dpr = screen.devicePixelRatio() if screen else 1.0
        taille_physique = int(46 * dpr)
        pix = self._src_pixmap.scaled(
            taille_physique,
            taille_physique,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        pix.setDevicePixelRatio(dpr)
        self.logo_pixmap = pix

    def setup_animations(self):
        self.outer_anim = QPropertyAnimation(self, b"outer_rotation")
        self.outer_anim.setDuration(2500)
        self.outer_anim.setStartValue(0)
        self.outer_anim.setEndValue(360)
        self.outer_anim.setLoopCount(-1)
        self.outer_anim.setEasingCurve(QEasingCurve.InOutCubic)

        self.inner_anim = QPropertyAnimation(self, b"inner_rotation")
        self.inner_anim.setDuration(1800)
        self.inner_anim.setStartValue(0)
        self.inner_anim.setEndValue(-360)
        self.inner_anim.setLoopCount(-1)
        self.inner_anim.setEasingCurve(QEasingCurve.OutInElastic)

    def get_outer_rotation(self):
        return self._outer_rotation

    def set_outer_rotation(self, value):
        self._outer_rotation = value % 360
        self.update()

    outer_rotation = Property(float, get_outer_rotation, set_outer_rotation)

    def get_inner_rotation(self):
        return self._inner_rotation

    def set_inner_rotation(self, value):
        self._inner_rotation = value % 360
        self.update()

    inner_rotation = Property(float, get_inner_rotation, set_inner_rotation)

    def start_animation(self):
        if not self.is_animating and not self.logo_pixmap.isNull():
            self.outer_anim.start()
            self.inner_anim.start()
            self.is_animating = True

    def stop_animation(self):
        self.outer_anim.stop()
        self.inner_anim.stop()
        self._outer_rotation = 0
        self._inner_rotation = 0
        self.update()

    def paintEvent(self, event):
        if self.logo_pixmap.isNull():
            return
        try:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)  # ← AJOUTER
            cx, cy = 23.0, 23.0
            dest = self.rect()

            outer_path = QPainterPath()
            outer_path.addEllipse(4, 4, 38, 38)
            p.save()
            p.translate(cx, cy)
            p.rotate(self._outer_rotation)
            p.translate(-cx, -cy)
            p.setClipPath(outer_path)
            p.drawPixmap(dest, self.logo_pixmap)
            p.restore()

            inner_path = QPainterPath()
            inner_path.addEllipse(12, 12, 22, 22)
            p.save()
            p.translate(cx, cy)
            p.rotate(self._inner_rotation)
            p.translate(-cx, -cy)
            p.setClipPath(inner_path)
            p.drawPixmap(dest, self.logo_pixmap)
            p.restore()
        finally:
            p.end()


# ═══════════════════════════════════════════════════════════════════════════════
#  Vue principale
# ═══════════════════════════════════════════════════════════════════════════════


class AideView(QWidget):
    """Onglet d'aide sous forme de chatbot interactif."""

    def __init__(self, parent=None):  # ← parent=None par défaut
        super().__init__(parent)
        self._mode_admin = True
        self._satisfaction_widget = None
        self._countdown_widget = None
        self._countdown_timer = None
        self._countdown_value = 5
        self._construire_ui()
        QTimer.singleShot(0, self._afficher_accueil)

    # ──────────────────────────────────────────────────────────────────────────
    # API publique
    # ──────────────────────────────────────────────────────────────────────────

    def mettre_a_jour_mode(self, mode_admin: bool):
        self._mode_admin = mode_admin

    # ──────────────────────────────────────────────────────────────────────────
    # Construction UI
    # ──────────────────────────────────────────────────────────────────────────

    def _construire_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Chat scrollable ──────────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll.setStyleSheet(S_SCROLL)

        self._chat_container = QWidget()
        self._chat_container.setStyleSheet(S_CHAT)
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setSpacing(12)
        self._chat_layout.setContentsMargins(30, 20, 30, 20)
        self._chat_layout.addStretch()

        self._scroll.setWidget(self._chat_container)
        root.addWidget(self._scroll, 1)

        # ── Séparateur ───────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #DDE3EE;")
        root.addWidget(sep)

        # ── Suggestions ──────────────────────────────────────────────────────
        self._suggestions_widget = QWidget()
        self._suggestions_widget.setStyleSheet("background-color: #FFFFFF;")
        self._suggestions_layout = QVBoxLayout(self._suggestions_widget)
        self._suggestions_layout.setContentsMargins(16, 10, 16, 6)
        self._suggestions_layout.setSpacing(6)
        self._suggestions_widget.hide()
        root.addWidget(self._suggestions_widget)

        # ── Barre de saisie ──────────────────────────────────────────────────
        input_bar = QWidget()
        input_bar.setStyleSheet("background-color: #FFFFFF;")
        input_bar.setFixedHeight(66)
        il = QHBoxLayout(input_bar)
        il.setContentsMargins(20, 10, 20, 10)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Tapez des mots-clés pour trouver une réponse…")
        self._input.setStyleSheet(S_INPUT)
        self._input.textChanged.connect(self._on_recherche)
        il.addWidget(self._input)

        root.addWidget(input_bar)

    # ──────────────────────────────────────────────────────────────────────────
    # Filtrage FAQ
    # ──────────────────────────────────────────────────────────────────────────

    def _get_faq_filtree(self) -> list:
        result = []
        for item in FAQ_DATA:
            vis = item.get("visibility", "all")
            if vis == "all":
                result.append(item)
            elif vis == "admin_only" and self._mode_admin:
                result.append(item)
            elif vis == "vendeur_only" and not self._mode_admin:
                result.append(item)
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # Recherche & suggestions
    # ──────────────────────────────────────────────────────────────────────────

    def _on_recherche(self, texte: str):
        self._effacer_suggestions()
        if not texte.strip():
            self._suggestions_widget.hide()
            return

        mots = texte.lower().split()
        resultats = []

        for item in self._get_faq_filtree():
            score = 0
            q_lower = item["question"].lower()
            mots_cles = [m.lower() for m in item.get("mots_cles", [])]
            for mot in mots:
                if mot in q_lower:
                    score += 2
                for mc in mots_cles:
                    if mot in mc or mc in mot:
                        score += 1
            if score > 0:
                resultats.append((score, item))

        resultats.sort(key=lambda x: x[0], reverse=True)

        label_titre = QLabel("Suggestions :")
        label_titre.setStyleSheet(
            "color: #8A96A8; font-size: 10pt; background: transparent;"
        )
        self._suggestions_layout.addWidget(label_titre)

        for _, item in resultats[:5]:
            btn = QPushButton(item["question"])
            btn.setStyleSheet(S_SUGGESTION)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(
                lambda checked=False, i=item: self._selectionner_question(i)
            )
            self._suggestions_layout.addWidget(btn)

        self._suggestions_widget.setVisible(bool(resultats))

    def _effacer_suggestions(self):
        while self._suggestions_layout.count():
            child = self._suggestions_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    # ──────────────────────────────────────────────────────────────────────────
    # Flux de conversation
    # ──────────────────────────────────────────────────────────────────────────

    def _selectionner_question(self, item: dict):
        self._input.clear()
        self._input.setEnabled(False)
        self._suggestions_widget.hide()

        self._ajouter_bulle_utilisateur(item["question"])
        QTimer.singleShot(
            500,
            lambda: self._ajouter_bulle_bot(
                item["reponse"],
                callback=lambda: QTimer.singleShot(500, self._demander_satisfaction),
            ),
        )

    def _demander_satisfaction(self):
        self._ajouter_bulle_bot(
            "Cette réponse vous a-t-elle été utile ?",
            callback=self._afficher_boutons_satisfaction,
        )

    def _afficher_boutons_satisfaction(self):
        self._satisfaction_widget = QWidget(self._chat_container)
        self._satisfaction_widget.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(self._satisfaction_widget)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(10)

        btn_oui = QPushButton("✓  Oui, merci !")
        btn_oui.setStyleSheet(S_BTN_OUI)
        btn_oui.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_oui.clicked.connect(self._on_satisfaction_oui)

        btn_non = QPushButton("✗  Non, pas vraiment")
        btn_non.setStyleSheet(S_BTN_NON)
        btn_non.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_non.clicked.connect(self._on_satisfaction_non)

        layout.addWidget(btn_oui)
        layout.addWidget(btn_non)
        layout.addStretch()

        self._inserer_widget_bot_aligne(self._satisfaction_widget)
        self._input.setEnabled(True)

    def _on_satisfaction_oui(self):
        self._supprimer_widget(self._satisfaction_widget)
        self._satisfaction_widget = None
        self._ajouter_bulle_utilisateur("Oui, merci !")
        QTimer.singleShot(
            400,
            lambda: self._ajouter_bulle_bot(
                "Super, ravi d'avoir pu vous aider ! 😊\n"
                "La conversation va se réinitialiser dans 5 secondes…",
                callback=lambda: QTimer.singleShot(400, self._demarrer_countdown),
            ),
        )

    def _on_satisfaction_non(self):
        self._supprimer_widget(self._satisfaction_widget)
        self._satisfaction_widget = None
        self._ajouter_bulle_utilisateur("Non, pas vraiment.")
        QTimer.singleShot(400, self._afficher_contact)

    def _afficher_contact(self):
        self._ajouter_bulle_bot(
            "Je suis désolé de ne pas avoir pu vous aider davantage. 😔\n\n"
            "Pour plus de renseignements, contactez-nous :\n"
            f"📧  {EMAIL_SUPPORT}",
            callback=lambda: QTimer.singleShot(400, self._ajouter_bouton_reinitialiser),
        )

    def _ajouter_bouton_reinitialiser(self):
        btn = QPushButton("↺  Poser une autre question")
        btn.setStyleSheet(S_BTN_RESET)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._reinitialiser_chat)

        container = QWidget(self._chat_container)
        container.setStyleSheet("background-color: transparent;")
        h = QHBoxLayout(container)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(btn)
        h.addStretch()

        self._inserer_widget_bot_aligne(container)
        self._input.setEnabled(True)

    # ──────────────────────────────────────────────────────────────────────────
    # Countdown
    # ──────────────────────────────────────────────────────────────────────────

    def _demarrer_countdown(self):
        self._countdown_value = 5
        self._countdown_widget = QWidget(self._chat_container)
        self._countdown_widget.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(self._countdown_widget)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(12)

        self._countdown_label = QLabel(
            f"Réinitialisation dans {self._countdown_value}s…"
        )
        self._countdown_label.setStyleSheet(
            "color: #8A96A8; font-size: 11pt; background: transparent;"
        )

        btn_annuler = QPushButton("Annuler")
        btn_annuler.setStyleSheet(S_BTN_ANNULER)
        btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_annuler.clicked.connect(self._annuler_countdown)

        layout.addWidget(self._countdown_label)
        layout.addWidget(btn_annuler)
        layout.addStretch()

        self._inserer_widget_bot_aligne(self._countdown_widget)

        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._tick_countdown)
        self._countdown_timer.start(1000)

    def _tick_countdown(self):
        self._countdown_value -= 1
        if self._countdown_value <= 0:
            self._countdown_timer.stop()
            self._reinitialiser_chat()
        else:
            self._countdown_label.setText(
                f"Réinitialisation dans {self._countdown_value}s…"
            )

    def _annuler_countdown(self):
        if self._countdown_timer:
            self._countdown_timer.stop()
            self._countdown_timer = None
        self._supprimer_widget(self._countdown_widget)
        self._countdown_widget = None
        self._afficher_contact()

    # ──────────────────────────────────────────────────────────────────────────
    # Réinitialisation
    # ──────────────────────────────────────────────────────────────────────────

    def _reinitialiser_chat(self):
        if self._countdown_timer:
            self._countdown_timer.stop()
            self._countdown_timer = None

        while self._chat_layout.count() > 1:
            child = self._chat_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._satisfaction_widget = None
        self._countdown_widget = None
        self._input.setEnabled(True)
        self._input.clear()
        QTimer.singleShot(50, self._afficher_accueil)

    def _afficher_accueil(self):
        self._ajouter_bulle_bot(
            "Bonjour ! 👋 Je suis l'assistant Nexa.\n\n"
            "Tapez des mots-clés dans la barre ci-dessous et je vous proposerai "
            "les sujets correspondants. Cliquez ensuite sur la question qui vous correspond.",
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Bulles de chat
    # ──────────────────────────────────────────────────────────────────────────

    def _ajouter_bulle_bot(self, texte: str, callback=None):
        container = self._creer_bulle("", is_bot=True)
        label = container.findChild(QLabel, "message_label")
        self._inserer_avant_stretch(container)
        self._scroll_to_bottom()
        self._typewriter(label, texte, callback=callback)

    def _ajouter_bulle_utilisateur(self, texte: str):
        self._inserer_avant_stretch(self._creer_bulle(texte, is_bot=False))
        self._scroll_to_bottom()

    def _creer_bulle(self, texte: str, is_bot: bool) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        outer = QHBoxLayout(container)
        outer.setContentsMargins(0, 4, 0, 4)
        outer.setSpacing(12)

        label = QLabel(texte)
        label.setObjectName("message_label")  # ← identifiant stable
        label.setWordWrap(True)
        label.setMaximumWidth(1050)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        if is_bot:
            label.setStyleSheet(S_BULLE_BOT)

            avatar_col = QVBoxLayout()
            avatar_col.setContentsMargins(0, 0, 0, 0)
            avatar_col.setSpacing(0)
            av = AnimatedLogo(parent=container)
            av.setObjectName("logo_bot")
            avatar_col.addWidget(av, 0, Qt.AlignmentFlag.AlignTop)
            avatar_col.addStretch()

            outer.addLayout(avatar_col)
            outer.addWidget(
                label, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
            )
            outer.addStretch()
        else:
            label.setStyleSheet(S_BULLE_USER)
            outer.addStretch()
            outer.addWidget(
                label, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
            )

        return container

    # ──────────────────────────────────────────────────────────────────────────
    # Utilitaires
    # ──────────────────────────────────────────────────────────────────────────

    def _inserer_avant_stretch(self, widget: QWidget):
        self._chat_layout.insertWidget(self._chat_layout.count() - 1, widget)

    def _inserer_widget_bot_aligne(self, widget: QWidget):
        wrapper = QWidget(self._chat_container)  # ← parent immédiat
        wrapper.setStyleSheet("background-color: transparent;")
        h = QHBoxLayout(wrapper)
        h.setContentsMargins(INDENT_BOT, 0, 0, 4)
        h.setSpacing(0)
        h.addWidget(widget)
        h.addStretch()
        self._inserer_avant_stretch(wrapper)
        self._scroll_to_bottom()

    @staticmethod
    def _supprimer_widget(widget: Optional[QWidget]):
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()

    def _scroll_to_bottom(self):
        QTimer.singleShot(
            60,
            lambda: self._scroll.verticalScrollBar().setValue(
                self._scroll.verticalScrollBar().maximum()
            ),
        )

    def _typewriter(
        self, label: QLabel, texte: str, vitesse_ms: int = 14, callback=None
    ):
        self._input.setEnabled(False)
        logo = self.find_bot_logo()
        if logo and isinstance(logo, AnimatedLogo):
            logo.start_animation()
        index = [0]
        timer = QTimer(self)

        def tick():
            index[0] += 1
            label.setText(texte[: index[0]])
            self._scroll_to_bottom()
            if index[0] >= len(texte):
                timer.stop()
                if logo:
                    logo.stop_animation()
                if callback:
                    callback()
                else:
                    self._input.setEnabled(True)  # fin de chaîne seulement

        timer.timeout.connect(tick)
        timer.start(vitesse_ms)

    def find_bot_logo(self):
        """Trouve le AnimatedLogo du dernier message bot."""
        for i in range(self._chat_layout.count() - 2, -1, -1):  # Ignore stretch
            item = self._chat_layout.itemAt(i)
            if item.widget():
                container = item.widget()
                for child in container.findChildren(QLabel):
                    if isinstance(child, AnimatedLogo):
                        return child
        return None

    # ──────────────────────────────────────────────────────────────────────────
    # Avatar (construit une seule fois)
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_avatar_pixmap() -> QPixmap:
        size = 46
        source = QPixmap(AVATAR_PATH)

        if source.isNull():
            # Fallback : cercle bleu + initiale "N"
            pm = QPixmap(size, size)
            pm.fill(Qt.GlobalColor.transparent)
            p = QPainter(pm)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setBrush(QColor("#1976D2"))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(0, 0, size, size)
            p.setPen(QColor("#FFFFFF"))
            f = QFont()
            f.setPointSize(18)
            f.setBold(True)
            p.setFont(f)
            p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "N")
            p.end()
            return pm

        # Image réelle → recadrage circulaire
        source = source.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        rounded = QPixmap(size, size)
        rounded.fill(Qt.GlobalColor.transparent)
        p = QPainter(rounded)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        p.setClipPath(path)
        p.drawPixmap(0, 0, source)
        p.end()
        return rounded
