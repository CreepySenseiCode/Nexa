"""Widget de carte tâche avec checkbox rond, stamps et sous-tâches."""

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QSizePolicy,
    QWidget,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, QObject, QEvent, QPoint

from utils.styles import style_bouton, Couleurs


class _ClickOutsideFilter(QObject):
    """Ferme l'éditeur de la TacheCard si l'utilisateur clique hors de la carte."""

    def __init__(self, card: "TacheCard", parent=None):  # ← parent=None par défaut
        super().__init__(parent)
        self._card = card

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            top_left = self._card.mapToGlobal(QPoint(0, 0))
            from PySide6.QtCore import QRect

            card_rect = QRect(top_left, self._card.size())
            if not card_rect.contains(event.globalPosition().toPoint()):
                self._card._finish_edit_titre()
                self._card._finish_edit_desc()
        return False


_PRIORITE_COLORS = [
    "#1565C0",
    "#1976D2",
    "#1E88E5",
    "#2196F3",
    "#42A5F5",
    "#5C9CE6",
    "#7BB3F0",
    "#90CAF9",
    "#A8D8FF",
    "#B8E0FF",
]


class TacheCard(QFrame):
    """Card pour une tâche.

    Layout :
      Ligne 1 : [Oval tri] | [checkbox rond] | titre + détails | [stamp] | [badge prio] | [actions]
      Ligne 2 : description tronquée
    """

    double_clicked = Signal(int)  # tache_id
    toggled = Signal(int, bool)  # tache_id, terminee
    action_supprimer = Signal(int)
    action_restaurer = Signal(int)
    action_valider = Signal(int)  # admin valide une mission
    association_clicked = Signal(str, int)  # type, id
    collapse_toggled = Signal(int)  # parent tache_id
    titre_modifie = Signal(int, str)  # tache_id, nouveau titre
    description_modifiee = Signal(int, str)  # tache_id, nouvelle description

    def __init__(
        self,
        tache_data: dict,
        show_actions: bool = False,
        sort_key: str = "",
        mode_admin: bool = True,
        is_subtask: bool = False,
        show_restore: bool = False,
        has_children: bool = False,
        is_expanded: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.tache_id = tache_data.get("id", 0)
        self._terminee = bool(tache_data.get("terminee", False))
        self._cochee = bool(tache_data.get("cochee", False))
        self._data = tache_data
        self._is_subtask = is_subtask
        self._show_restore = show_restore
        self._has_children = has_children
        self._is_expanded = is_expanded
        self._construire_ui(tache_data, show_actions, sort_key, mode_admin)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _construire_ui(
        self, data: dict, show_actions: bool, sort_key: str, mode_admin: bool
    ) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)

        visibilite = data.get("visibilite", "tous")
        validee = bool(data.get("validee_admin", False))

        # Déterminer la bordure
        if self._is_subtask:
            border_color = "#B0BEC5"
            bg = "#FAFAFA"
            height = 60
        elif self._terminee:
            border_color = "#1976D2" if validee else "#90CAF9"
            bg = "#F5F9FF"
            height = 90
        elif not mode_admin and visibilite == "tous":
            # Mode fonctionnel : tâche admin → bordure bleu clair
            border_color = "#BBDEFB"
            bg = "#F5F9FF"
            height = 90
        elif mode_admin and visibilite == "tous":
            # Mode admin : missions légèrement grisées
            border_color = "#E0E0E0"
            bg = "#F5F5F5"
            height = 90
        else:
            border_color = "#E0E0E0"
            bg = "#FFFFFF"
            height = 90

        # Couleur personnalisée en bordure gauche (priorité : couleur perso > catégorie > défaut)
        couleur_perso = data.get("couleur")
        couleur_cat = data.get("categorie_couleur")
        border_left_color = couleur_perso or couleur_cat or None
        border_width = "2px" if not mode_admin and visibilite == "tous" else "1px"

        if border_left_color:
            self.setStyleSheet(
                f"TacheCard {{"
                f"    background-color: {bg};"
                f"    border: {border_width} solid {border_color};"
                f"    border-left: 4px solid {border_left_color};"
                f"    border-radius: 10px;"
                f"}}"
                f"TacheCard:hover {{"
                f"    background-color: #F5F5F5;"
                f"    border: 1px solid #1976D2;"
                f"    border-left: 4px solid {border_left_color};"
                f"}}"
            )
        else:
            self.setStyleSheet(
                f"TacheCard {{"
                f"    background-color: {bg};"
                f"    border: {border_width} solid {border_color};"
                f"    border-radius: 10px;"
                f"}}"
                f"TacheCard:hover {{"
                f"    background-color: #F5F5F5;"
                f"    border: 1px solid #1976D2;"
                f"}}"
            )
        self.setMinimumHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 6, 10, 6)
        root.setSpacing(8)

        # Oval de tri (bloc coloré au début) — pas pour les sous-tâches
        if not self._is_subtask:
            oval_text, oval_color = self._get_sort_display(data, sort_key)
            if oval_text:
                lbl_oval = QLabel(oval_text)
                lbl_oval.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_oval.setFixedSize(54, 32)
                lbl_oval.setStyleSheet(
                    f"font-size: 9pt; font-weight: bold; color: white; "
                    f"background-color: {oval_color}; border-radius: 14px; "
                    f"border: none; padding: 2px 6px;"
                )
                root.addWidget(lbl_oval, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Checkbox rond (style Apple)
        # Pour les sous-tâches : utiliser cochee au lieu de terminee
        is_checked = self._cochee if self._is_subtask else self._terminee
        self.btn_check = QPushButton()
        self.btn_check.setFixedSize(28, 28)
        self.btn_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_check.setToolTip("Marquer comme terminée")
        if is_checked:
            self.btn_check.setText("✓")
            self.btn_check.setStyleSheet(
                "QPushButton { background-color: #1976D2; color: white; "
                "border: 2px solid #1976D2; border-radius: 14px; "
                "font-size: 12pt; font-weight: bold; }"
                "QPushButton:hover { background-color: #1565C0; border-color: #1565C0; }"
            )
        else:
            self.btn_check.setText("")
            self.btn_check.setStyleSheet(
                "QPushButton { background-color: white; "
                "border: 2px solid #BDBDBD; border-radius: 14px; }"
                "QPushButton:hover { border-color: #1976D2; background-color: #E3F2FD; }"
            )
        tid = self.tache_id
        self.btn_check.clicked.connect(lambda: self.toggled.emit(tid, not is_checked))
        root.addWidget(self.btn_check, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Bouton collapse (pour les parents avec enfants)
        if self._has_children and not self._is_subtask:
            nb_label = ""
            btn_collapse = QPushButton("▼" if self._is_expanded else "▶")
            btn_collapse.setFixedSize(26, 26)
            btn_collapse.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_collapse.setToolTip(
                "Replier les sous-tâches"
                if self._is_expanded
                else "Déplier les sous-tâches"
            )
            bg = "#BBDEFB" if self._is_expanded else "#E3F2FD"
            btn_collapse.setStyleSheet(
                f"QPushButton {{ background: {bg}; border: 1px solid #90CAF9; "
                f"border-radius: 6px; font-size: 9pt; color: #1565C0; font-weight: bold; }}"
                f"QPushButton:hover {{ background: #90CAF9; color: #0D47A1; }}"
            )
            tid = self.tache_id
            btn_collapse.clicked.connect(lambda: self.collapse_toggled.emit(tid))
            btn_collapse.mousePressEvent = lambda e, t=tid: (
                self.collapse_toggled.emit(t),
                e.accept(),
            )
            root.addWidget(btn_collapse, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Colonne infos (2 lignes)
        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        info_col.setContentsMargins(0, 2, 0, 2)

        # Ligne 1 : titre + détails inline
        ligne1 = QHBoxLayout()
        ligne1.setSpacing(8)
        ligne1.setContentsMargins(0, 0, 0, 0)

        titre = data.get("titre", "")
        # QLineEdit stylé comme un label, bascule en mode éditable au clic
        self._edit_titre = QLineEdit(titre)
        self._edit_titre.setReadOnly(True)
        is_mission = mode_admin and visibilite == "tous"
        style_titre = "font-size: 12pt; font-weight: bold; color: #222; border: none; background: transparent; padding: 0; margin: 0;"
        if is_mission and not self._terminee:
            style_titre = "font-size: 12pt; font-weight: bold; color: #777; border: none; background: transparent; padding: 0; margin: 0;"
        if self._is_subtask:
            if self._cochee and not self._terminee:
                style_titre = (
                    "font-size: 10pt; font-weight: 600; color: #999; "
                    "text-decoration: line-through; border: none; background: transparent; padding: 0; margin: 0;"
                )
            else:
                style_titre = "font-size: 10pt; font-weight: 600; color: #444; border: none; background: transparent; padding: 0; margin: 0;"
        if self._terminee:
            style_titre = (
                f"font-size: {'10' if self._is_subtask else '12'}pt; "
                f"font-weight: {'600' if self._is_subtask else 'bold'}; color: #999; "
                "text-decoration: line-through; border: none; background: transparent; padding: 0; margin: 0;"
            )
        self._titre_style_readonly = style_titre
        self._titre_style_editing = style_titre.replace(
            "border: none;", "border: 1px solid #90CAF9; border-radius: 4px;"
        ).replace("background: transparent;", "background: #FAFAFA;")
        self._edit_titre.setStyleSheet(style_titre)
        self._edit_titre.setCursor(Qt.CursorShape.IBeamCursor)
        self._edit_titre.mousePressEvent = lambda e: self._start_edit_titre(e)
        self._edit_titre.focusOutEvent = lambda e: (
            QLineEdit.focusOutEvent(self._edit_titre, e),
            self._finish_edit_titre(),
        )
        self._original_titre = titre
        ligne1.addWidget(self._edit_titre)

        # Tags inline (catégorie, date, priorité) — pas pour sous-tâches
        if not self._is_subtask:
            details_parts = []
            cat_nom = data.get("categorie_nom")
            if cat_nom and sort_key != "categorie":
                details_parts.append(cat_nom)
            date_str = data.get("date_echeance")
            if date_str and sort_key != "date":
                heure = data.get("heure_echeance")
                d = str(date_str)[:10]
                if heure:
                    d += f" {heure}"
                details_parts.append(d)
            priorite = data.get("priorite", 5)
            if sort_key != "priorite":
                details_parts.append(f"P{priorite}")

            # Récurrence badge
            type_rec = data.get("type_recurrence")
            if type_rec:
                rec_labels = {
                    "quotidien": "🔄 Quot.",
                    "hebdomadaire": "🔄 Hebd.",
                    "mensuel": "🔄 Mens.",
                    "annuel": "🔄 Ann.",
                    "personnalise": f"🔄 /{data.get('intervalle_recurrence', '?')}j",
                }
                details_parts.append(rec_labels.get(type_rec, "🔄"))

            if details_parts:
                lbl_details = QLabel(" · ".join(details_parts))
                lbl_details.setStyleSheet("font-size: 9pt; color: #888; border: none;")
                ligne1.addWidget(lbl_details)

        ligne1.addStretch()

        # Stamp Admin/Mission
        if not self._is_subtask:
            if not mode_admin and visibilite == "tous":
                lbl_stamp = QLabel("ADMIN")
                lbl_stamp.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_stamp.setStyleSheet(
                    "font-size: 8pt; font-weight: bold; color: white; "
                    "background-color: #1976D2; border-radius: 4px; "
                    "padding: 2px 8px; border: none;"
                )
                ligne1.addWidget(lbl_stamp)
            elif mode_admin and visibilite == "tous":
                lbl_stamp = QLabel("MISSION")
                lbl_stamp.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_stamp.setStyleSheet(
                    "font-size: 8pt; font-weight: bold; color: white; "
                    "background-color: #FF9800; border-radius: 4px; "
                    "padding: 2px 8px; border: none;"
                )
                ligne1.addWidget(lbl_stamp)

                # Si mission terminée mais pas validée
                if self._terminee and not validee:
                    btn_valider = QPushButton("✓ Valider")
                    btn_valider.setFixedHeight(24)
                    btn_valider.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_valider.setStyleSheet(
                        "QPushButton { background: #4CAF50; color: white; "
                        "border: none; border-radius: 4px; font-size: 8pt; "
                        "font-weight: bold; padding: 2px 8px; }"
                        "QPushButton:hover { background: #388E3C; }"
                    )
                    btn_valider.clicked.connect(lambda: self.action_valider.emit(tid))
                    btn_valider.mousePressEvent = lambda e: (
                        self.action_valider.emit(tid),
                        e.accept(),
                    )
                    ligne1.addWidget(btn_valider)
                elif validee:
                    lbl_val = QLabel("VALIDÉE")
                    lbl_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl_val.setStyleSheet(
                        "font-size: 8pt; font-weight: bold; color: white; "
                        "background-color: #4CAF50; border-radius: 4px; "
                        "padding: 2px 8px; border: none;"
                    )
                    ligne1.addWidget(lbl_val)

        # Badge priorité — pas pour sous-tâches
        if not self._is_subtask:
            priorite = data.get("priorite", 5)
            prio_color = _PRIORITE_COLORS[max(0, min(priorite - 1, 9))]
            lbl_prio = QLabel(f"P{priorite}")
            lbl_prio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_prio.setFixedWidth(38)
            lbl_prio.setStyleSheet(
                f"font-size: 9pt; font-weight: bold; color: white; "
                f"background-color: {prio_color}; border-radius: 6px; "
                f"padding: 2px 6px; border: none;"
            )
            ligne1.addWidget(lbl_prio)

        # Badge association — pas pour sous-tâches
        if not self._is_subtask:
            assoc_badges = []
            if data.get("client_id"):
                assoc_badges.append(
                    ("👤 Client", "client", data["client_id"], "#5C6BC0")
                )
            if data.get("vente_id"):
                assoc_badges.append(("🛒 Vente", "vente", data["vente_id"], "#43A047"))
            if data.get("commande_id"):
                assoc_badges.append(
                    ("📦 Cmd", "commande", data["commande_id"], "#EF6C00")
                )
            if data.get("produit_id"):
                assoc_badges.append(
                    ("🏷 Produit", "produit", data["produit_id"], "#7B1FA2")
                )
            if data.get("code_promo_id"):
                assoc_badges.append(
                    ("🎟 Code", "code_promo", data["code_promo_id"], "#00897B")
                )
            if data.get("evenement_id"):
                assoc_badges.append(
                    ("📅 Event", "evenement", data["evenement_id"], "#F4511E")
                )

            for text, a_type, a_id, color in assoc_badges:
                lbl_assoc = QLabel(f"{text} #{a_id}")
                lbl_assoc.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_assoc.setCursor(Qt.CursorShape.PointingHandCursor)
                lbl_assoc.setStyleSheet(
                    f"font-size: 8pt; font-weight: 600; color: white; "
                    f"background-color: {color}; border-radius: 4px; "
                    f"padding: 2px 6px; border: none;"
                )
                lbl_assoc.mousePressEvent = lambda e, t=a_type, i=a_id: (
                    self.association_clicked.emit(t, i),
                    e.accept(),
                )
                ligne1.addWidget(lbl_assoc)

        info_col.addLayout(ligne1)

        # Ligne 2 : description complète (QLabel word-wrap, éditable au clic)
        self._desc_text = (data.get("description") or "").strip()
        if self._desc_text:
            # Label affichant la description complète
            self._lbl_desc = QLabel(self._desc_text)
            self._lbl_desc.setWordWrap(True)
            self._lbl_desc.setStyleSheet(
                "font-size: 9pt; color: #666; border: none; background: transparent; padding: 0; margin: 0;"
            )
            self._lbl_desc.setCursor(Qt.CursorShape.IBeamCursor)
            self._lbl_desc.mousePressEvent = lambda e: self._start_edit_desc(e)
            self._original_desc = self._desc_text

            # QTextEdit caché, utilisé uniquement en mode édition
            self._edit_desc = QTextEdit()
            self._edit_desc.setPlainText(self._desc_text)
            self._edit_desc.setStyleSheet(
                "font-size: 9pt; color: #666; border: 1px solid #90CAF9; "
                "border-radius: 4px; background: #FAFAFA; padding: 2px; margin: 0;"
            )
            self._edit_desc.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            self._edit_desc.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            self._edit_desc.document().contentsChanged.connect(
                self._ajuster_hauteur_desc
            )
            self._edit_desc.hide()
            self._edit_desc.focusOutEvent = self._on_desc_focus_out

            info_col.addWidget(self._lbl_desc)
            info_col.addWidget(self._edit_desc)
        else:
            info_col.addStretch()

        # Badge association row2 (boutons cliquables)
        if not self._is_subtask:
            assoc_badges_row2 = QHBoxLayout()
            assoc_badges_row2.setSpacing(6)
            assoc_badges_row2.setContentsMargins(0, 0, 0, 0)
            has_badge = False

            _assoc_config = [
                (
                    "client_id",
                    "👤 Client",
                    "client",
                    "#E8F5E9",
                    "#2E7D32",
                    "#A5D6A7",
                    "#C8E6C9",
                ),
                (
                    "vente_id",
                    "🛒 Vente",
                    "vente",
                    "#FFF3E0",
                    "#E65100",
                    "#FFE0B2",
                    "#FFE0B2",
                ),
                (
                    "commande_id",
                    "📦 Cmd",
                    "commande",
                    "#E3F2FD",
                    "#1565C0",
                    "#90CAF9",
                    "#BBDEFB",
                ),
                (
                    "produit_id",
                    "🏷 Produit",
                    "produit",
                    "#F3E5F5",
                    "#6A1B9A",
                    "#CE93D8",
                    "#E1BEE7",
                ),
                (
                    "code_promo_id",
                    "🎟 Code",
                    "code_promo",
                    "#E0F2F1",
                    "#00695C",
                    "#80CBC4",
                    "#B2DFDB",
                ),
                (
                    "evenement_id",
                    "📅 Event",
                    "evenement",
                    "#FBE9E7",
                    "#BF360C",
                    "#FFAB91",
                    "#FFCCBC",
                ),
            ]
            for field, label, a_type, bg, fg, border, hover in _assoc_config:
                val = data.get(field)
                if val:
                    btn = QPushButton(f"{label} #{val}")
                    btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn.setStyleSheet(
                        f"QPushButton {{ background: {bg}; color: {fg}; "
                        f"border: 1px solid {border}; border-radius: 4px; "
                        f"font-size: 8pt; font-weight: 600; padding: 1px 6px; }}"
                        f"QPushButton:hover {{ background: {hover}; }}"
                    )
                    btn.clicked.connect(
                        lambda checked=False, t=a_type, i=val: self.association_clicked.emit(
                            t, i
                        )
                    )
                    assoc_badges_row2.addWidget(btn)
                    has_badge = True

            if has_badge:
                assoc_badges_row2.addStretch()
                info_col.addLayout(assoc_badges_row2)

        root.addLayout(info_col, stretch=1)

        if show_actions:
            root.addLayout(self._construire_boutons())

    def _get_sort_display(self, data: dict, sort_key: str) -> tuple[str, str]:
        """Retourne (texte, couleur) pour l'ovale de tri."""
        if not sort_key:
            return "", ""

        if sort_key == "priorite":
            p = data.get("priorite", 5)
            color = _PRIORITE_COLORS[max(0, min(p - 1, 9))]
            return f"P{p}", color

        if sort_key == "categorie":
            cat = data.get("categorie_nom") or "—"
            color = data.get("categorie_couleur") or "#2196F3"
            if len(cat) > 6:
                cat = cat[:5] + "…"
            return cat, color

        if sort_key == "date":
            d = data.get("date_echeance")
            if d:
                parts = str(d)[:10].split("-")
                if len(parts) == 3:
                    return f"{parts[2]}/{parts[1]}", "#1565C0"
            return "—", "#9E9E9E"

        if sort_key == "titre":
            t = (data.get("titre") or "")[:4]
            return t or "—", "#546E7A"

        return "", ""

    def _construire_boutons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        if self._show_restore:
            btn_restaurer = QPushButton("↩")
            btn_restaurer.setFixedSize(36, 36)
            btn_restaurer.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_restaurer.setToolTip("Restaurer")
            btn_restaurer.setStyleSheet(
                "QPushButton { background: #E3F2FD; border: 1.5px solid #90CAF9; "
                "border-radius: 8px; font-size: 14pt; }"
                "QPushButton:hover { background: #BBDEFB; }"
            )
            tid = self.tache_id
            btn_restaurer.clicked.connect(lambda: self.action_restaurer.emit(tid))
            btn_restaurer.mousePressEvent = lambda e: (
                self.action_restaurer.emit(self.tache_id),
                e.accept(),
            )
            layout.addWidget(btn_restaurer)
        else:
            btn_suppr = QPushButton("\U0001f5d1")
            btn_suppr.setFixedSize(36, 36)
            btn_suppr.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_suppr.setToolTip("Supprimer")
            btn_suppr.setStyleSheet(style_bouton(Couleurs.DANGER, taille="petit"))
            tid = self.tache_id
            btn_suppr.clicked.connect(lambda: self.action_supprimer.emit(tid))
            btn_suppr.mousePressEvent = lambda e: (btn_suppr.clicked.emit(), e.accept())
            layout.addWidget(btn_suppr)

        return layout

    def _ajuster_hauteur_desc(self) -> None:
        """Ajuste la hauteur du QTextEdit à son contenu (pas de scroll, pas de hauteur fixe)."""
        if not hasattr(self, "_edit_desc") or not self._edit_desc.isVisible():
            return
        doc_h = int(self._edit_desc.document().size().height())
        m = self._edit_desc.contentsMargins()
        target = max(doc_h + m.top() + m.bottom() + 6, 28)
        self._edit_desc.setMinimumHeight(target)
        self._edit_desc.setMaximumHeight(target)

    def _remove_click_filter(self) -> None:
        """Désinstalle le filtre global de clic-extérieur."""
        if hasattr(self, "_click_filter") and self._click_filter is not None:
            QApplication.instance().removeEventFilter(self._click_filter)
            self._click_filter = None

    def _start_edit_titre(self, event=None) -> None:
        """Active l'édition du titre sur place (même widget, juste read-only=False)."""
        was_readonly = self._edit_titre.isReadOnly()
        if not was_readonly:
            # Déjà en édition → laisser Qt positionner le curseur normalement
            if event:
                QLineEdit.mousePressEvent(self._edit_titre, event)
            return
        self._edit_titre.setReadOnly(False)
        self._edit_titre.setStyleSheet(self._titre_style_editing)
        # Passer l'event AVANT setFocus pour que le curseur se place au clic
        if event:
            QLineEdit.mousePressEvent(self._edit_titre, event)
        else:
            self._edit_titre.setFocus()
        # Filtre global : ferme l'éditeur si clic hors de la carte
        if not hasattr(self, "_click_filter") or self._click_filter is None:
            self._click_filter = _ClickOutsideFilter(self)
            QApplication.instance().installEventFilter(self._click_filter)

    def _finish_edit_titre(self) -> None:
        """Termine l'édition du titre et émet le signal si modifié."""
        if self._edit_titre.isReadOnly():
            return
        self._edit_titre.setReadOnly(True)
        self._edit_titre.setStyleSheet(self._titre_style_readonly)
        new_text = self._edit_titre.text().strip()
        if new_text and new_text != self._original_titre:
            self._original_titre = new_text
            self.titre_modifie.emit(self.tache_id, new_text)
        self._remove_click_filter()

    def _start_edit_desc(self, event=None) -> None:
        """Active l'édition de la description : masque le label, affiche le QTextEdit."""
        if not hasattr(self, "_edit_desc"):
            return
        if self._edit_desc.isVisible():
            return
        # Hauteur initiale = celle du label actuel (évite un saut visuel)
        label_h = max(self._lbl_desc.height(), 28)
        self._edit_desc.setMinimumHeight(label_h)
        self._edit_desc.setMaximumHeight(label_h)
        self._lbl_desc.hide()
        self._edit_desc.setPlainText(self._original_desc)
        self._edit_desc.show()
        self._edit_desc.setFocus()
        # Ajuster la hauteur au contenu réel après que le layout se stabilise
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, self._ajuster_hauteur_desc)
        # Filtre global : ferme l'éditeur si clic hors de la carte
        if not hasattr(self, "_click_filter") or self._click_filter is None:
            self._click_filter = _ClickOutsideFilter(self)
            QApplication.instance().installEventFilter(self._click_filter)

    def _on_desc_focus_out(self, event) -> None:
        """Appelé quand le QTextEdit perd le focus → termine l'édition."""
        QTextEdit.focusOutEvent(self._edit_desc, event)
        self._finish_edit_desc()

    def _finish_edit_desc(self) -> None:
        """Termine l'édition de la description et émet le signal si modifié."""
        if not hasattr(self, "_edit_desc") or not self._edit_desc.isVisible():
            return
        new_text = self._edit_desc.toPlainText().strip()
        self._edit_desc.hide()
        # Remettre les contraintes de taille par défaut
        self._edit_desc.setMinimumHeight(0)
        self._edit_desc.setMaximumHeight(16777215)
        self._lbl_desc.setText(new_text or self._original_desc)
        self._lbl_desc.show()
        if new_text and new_text != self._original_desc:
            self._original_desc = new_text
            self.description_modifiee.emit(self.tache_id, new_text)
        self._remove_click_filter()

    def mouseDoubleClickEvent(self, event) -> None:
        self.double_clicked.emit(self.tache_id)
        super().mouseDoubleClickEvent(event)
