"""Vue pour l'onglet Tâches (gestion complète des tâches)."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QGroupBox,
    QMessageBox,
    QScrollArea,
    QStackedWidget,
    QDateEdit,
    QTimeEdit,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
)
from PySide6.QtCore import Qt, QDate, QTime, Signal
from PySide6.QtGui import QFont, QColor, QPixmap, QIcon, QPainter

from views.components.modern_segmented_control import ModernSegmentedControl
from views.components.tache_card import TacheCard
from views.taches.fiche_tache_view import FicheTacheView
from viewmodels.tache_vm import TacheViewModel
from models.evenement import EvenementModel
from utils.styles import style_scroll_area, Couleurs

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

_AUTO_CATEGORY_COLORS = [
    "#2196F3",
    "#4CAF50",
    "#FF9800",
    "#9C27B0",
    "#F44336",
    "#00BCD4",
    "#795548",
    "#E91E63",
    "#3F51B5",
    "#009688",
    "#FF5722",
    "#607D8B",
]


def _color_icon(color_hex: str, size: int = 16) -> QIcon:
    """Crée une icône ronde de la couleur donnée."""
    pix = QPixmap(size, size)
    pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(color_hex))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(1, 1, size - 2, size - 2)
    p.end()
    return QIcon(pix)


class TachesView(QWidget):
    """Vue pour l'onglet Tâches."""

    association_navigation = Signal(str, int)  # type (client/vente/commande), id

    def __init__(self, viewmodel=None, parent=None):  # ← parent=None par défaut
        super().__init__(parent)
        self._mode_admin = True

        if viewmodel is None:
            self.viewmodel = TacheViewModel()
        else:
            self.viewmodel = viewmodel

        self._evenement_model = EvenementModel()

        # Tri state
        self._tri_criteres = []
        self._tri_directions = []
        self._filtre_categorie_id = None
        self._inclure_terminees = True
        self._couleur_tache = None
        self._couleurs_recentes: list[str] = []

        # Sous-tâches collapse state (repliées par défaut, dépliées si dans ce set)
        self._expanded_parents: set[int] = set()

        # Édition
        self._tache_en_edition: int | None = None

        # Vue liste mode : 0=actives, 1=terminées, 2=supprimées
        self._liste_mode = 0

        self._construire_ui()
        self._connecter_signaux()

    # ------------------------------------------------------------------ #
    #                        Construction de l'UI                         #
    # ------------------------------------------------------------------ #

    PAGE_LISTE = 0
    PAGE_CREATION = 1
    PAGE_FICHE = 2
    _PAGES = ["liste", "creation"]

    def _construire_ui(self):
        layout_self = QVBoxLayout(self)
        layout_self.setContentsMargins(0, 0, 0, 0)
        layout_self.setSpacing(0)

        # Toggle
        self._barre_toggle = ModernSegmentedControl(["Liste", "Nouvelle tâche"])
        self._barre_toggle.selectionChanged.connect(self._on_toggle_changed)

        layout_haut = QHBoxLayout()
        layout_haut.setContentsMargins(24, 16, 24, 8)
        layout_haut.addStretch(1)
        layout_haut.addWidget(self._barre_toggle)
        layout_haut.addStretch(1)
        layout_self.addLayout(layout_haut)

        # Stacked widget
        self.pile = QStackedWidget()
        self.pile.addWidget(self._creer_page_liste())  # 0
        self.pile.addWidget(self._creer_page_creation())  # 1

        # Fiche détail (page 2, cachée du toggle)
        self.fiche_tache = FicheTacheView(viewmodel=self.viewmodel)
        self.fiche_tache.retour_demande.connect(lambda: self._changer_page("liste"))
        self.fiche_tache.edition_demandee.connect(self._editer_tache)
        self.fiche_tache.association_navigation.connect(
            self.association_navigation.emit
        )
        self.pile.addWidget(self.fiche_tache)  # 2

        layout_self.addWidget(self.pile)
        self._barre_toggle.select(self.PAGE_LISTE)

    def _on_toggle_changed(self, index: int):
        self._changer_page(self._PAGES[index])

    def mettre_a_jour_mode(self, mode_admin: bool) -> None:
        self._mode_admin = mode_admin
        if self.pile.currentIndex() == self.PAGE_LISTE:
            self._charger_liste()
        self._section_visibilite.setVisible(mode_admin)
        self._label_visibilite.setVisible(mode_admin)
        # Mettre à jour le label de la checkbox missions/admin
        self._check_missions.setText("Missions" if mode_admin else "Admin")
        self.fiche_tache.mettre_a_jour_mode(mode_admin)

    def _changer_page(self, page: str):
        if page in self._PAGES:
            idx = self._PAGES.index(page)
            if self._barre_toggle.current_index != idx:
                self._barre_toggle.select(idx)

        if page == "liste":
            self.pile.setCurrentIndex(self.PAGE_LISTE)
            self._charger_liste()
        elif page == "creation":
            self.pile.setCurrentIndex(self.PAGE_CREATION)
            self._charger_categories_creation()
            self._charger_parents_combo()
        elif page == "fiche":
            self.pile.setCurrentIndex(self.PAGE_FICHE)

        self._barre_toggle.setVisible(page != "fiche")

    def ouvrir_fiche(self, tache_id: int):
        """Ouvre la fiche d'une tâche (appelable depuis l'extérieur)."""
        self.fiche_tache.charger_tache(tache_id)
        self._changer_page("fiche")

    # ------------------------------------------------------------------ #
    #                        Page Liste                                   #
    # ------------------------------------------------------------------ #

    def _creer_page_liste(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # --- Radios Actives / Terminées / Supprimées ---
        status_row = QHBoxLayout()
        status_row.setSpacing(16)

        self._radio_group = QButtonGroup(self)
        self._radio_actives = QRadioButton("Actives")
        self._radio_terminees = QRadioButton("Terminées")
        self._radio_supprimees = QRadioButton("Supprimées")
        for i, rb in enumerate(
            [self._radio_actives, self._radio_terminees, self._radio_supprimees]
        ):
            rb.setStyleSheet(
                "QRadioButton { font-size: 11pt; font-weight: 600; color: #333; spacing: 6px; }"
                "QRadioButton::indicator { width: 18px; height: 18px; }"
            )
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            self._radio_group.addButton(rb, i)
        self._radio_actives.setChecked(True)
        self._radio_group.idClicked.connect(self._on_radio_status)

        status_row.addStretch()
        status_row.addWidget(self._radio_actives)
        status_row.addWidget(self._radio_terminees)
        status_row.addWidget(self._radio_supprimees)
        status_row.addStretch()
        layout.addLayout(status_row)

        # --- Checkboxes sous "Actives" ---
        self._checkboxes_row = QHBoxLayout()
        self._checkboxes_row.setSpacing(16)
        self._checkboxes_row.setContentsMargins(0, 0, 0, 0)

        self._check_inclure_terminees = QCheckBox("Terminées")
        self._check_inclure_terminees.setStyleSheet("font-size: 10pt; color: #555;")
        self._check_inclure_terminees.toggled.connect(self._on_checkbox_filter)
        self._checkboxes_row.addStretch()
        self._checkboxes_row.addWidget(self._check_inclure_terminees)

        self._check_missions = QCheckBox("Missions")
        self._check_missions.setStyleSheet("font-size: 10pt; color: #555;")
        self._check_missions.setChecked(True)
        self._check_missions.toggled.connect(self._on_checkbox_filter)
        self._checkboxes_row.addWidget(self._check_missions)

        self._check_evenements = QCheckBox("Événements")
        self._check_evenements.setStyleSheet("font-size: 10pt; color: #E65100;")
        self._check_evenements.toggled.connect(self._on_checkbox_filter)
        self._checkboxes_row.addWidget(self._check_evenements)

        self._checkboxes_row.addStretch()

        self._checkboxes_widget = QWidget()
        self._checkboxes_widget.setStyleSheet("border: none; background: transparent;")
        self._checkboxes_widget.setLayout(self._checkboxes_row)
        layout.addWidget(self._checkboxes_widget)

        # --- Bouton "Vider la corbeille" ---
        self._btn_vider_corbeille = QPushButton("🗑 Vider la corbeille")
        self._btn_vider_corbeille.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_vider_corbeille.setStyleSheet(
            "QPushButton { background: #FFEBEE; color: #C62828; "
            "border: 1.5px solid #EF9A9A; border-radius: 8px; "
            "font-size: 10pt; font-weight: 600; padding: 8px 16px; }"
            "QPushButton:hover { background: #FFCDD2; border-color: #E57373; }"
        )
        self._btn_vider_corbeille.clicked.connect(self._vider_corbeille)
        self._btn_vider_corbeille.setVisible(False)
        layout.addWidget(self._btn_vider_corbeille)

        # --- Barre de tri/filtre ---
        barre_tri = QHBoxLayout()
        barre_tri.setSpacing(8)

        lbl_tri = QLabel("Trier par :")
        lbl_tri.setStyleSheet("font-size: 11pt; color: #666; border: none;")
        barre_tri.addWidget(lbl_tri)

        self.combo_tri_1 = QComboBox()
        self.combo_tri_1.addItems(["Défaut", "Date", "Priorité", "Catégorie", "Titre"])
        self.combo_tri_1.setCurrentIndex(1)  # Tri par Date par défaut
        self.combo_tri_1.setMinimumWidth(120)
        self.combo_tri_1.setStyleSheet("font-size: 11pt; padding: 4px;")
        self.combo_tri_1.currentIndexChanged.connect(self._on_tri_change)
        barre_tri.addWidget(self.combo_tri_1)

        self.btn_direction = QPushButton("\u25bc")
        self.btn_direction.setFixedSize(36, 36)
        self.btn_direction.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_direction.setToolTip("Inverser le tri")
        self.btn_direction.setStyleSheet(
            "QPushButton { background: #E3F2FD; border: 1px solid #90CAF9; "
            "border-radius: 8px; font-size: 14pt; }"
            "QPushButton:hover { background: #BBDEFB; }"
        )
        self._direction_asc = True
        self.btn_direction.clicked.connect(self._toggle_direction)
        barre_tri.addWidget(self.btn_direction)

        self.btn_ajouter_tri = QPushButton("+")
        self.btn_ajouter_tri.setFixedSize(36, 36)
        self.btn_ajouter_tri.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ajouter_tri.setToolTip("Ajouter un critère de tri")
        self.btn_ajouter_tri.setStyleSheet(
            "QPushButton { background: #E8F5E9; border: 1px solid #A5D6A7; "
            "border-radius: 8px; font-size: 14pt; font-weight: bold; }"
            "QPushButton:hover { background: #C8E6C9; }"
        )
        self.btn_ajouter_tri.clicked.connect(self._ajouter_tri_secondaire)
        barre_tri.addWidget(self.btn_ajouter_tri)

        self.combo_tri_2 = QComboBox()
        self.combo_tri_2.addItems(["Aucun", "Date", "Priorité", "Catégorie", "Titre"])
        self.combo_tri_2.setMinimumWidth(120)
        self.combo_tri_2.setStyleSheet("font-size: 11pt; padding: 4px;")
        self.combo_tri_2.setVisible(False)
        self.combo_tri_2.currentIndexChanged.connect(self._on_tri_change)
        barre_tri.addWidget(self.combo_tri_2)

        barre_tri.addStretch()

        lbl_filtre = QLabel("Catégorie :")
        lbl_filtre.setStyleSheet("font-size: 11pt; color: #666; border: none;")
        barre_tri.addWidget(lbl_filtre)

        self.combo_filtre_categorie = QComboBox()
        self.combo_filtre_categorie.addItem("Toutes", None)
        self.combo_filtre_categorie.setMinimumWidth(140)
        self.combo_filtre_categorie.setStyleSheet("font-size: 11pt; padding: 4px;")
        self.combo_filtre_categorie.currentIndexChanged.connect(self._on_filtre_change)
        barre_tri.addWidget(self.combo_filtre_categorie)

        layout.addLayout(barre_tri)

        # Compteur
        self._label_nb_taches = QLabel()
        self._label_nb_taches.setStyleSheet(
            "color: #7f8c8d; font-size: 11pt; border: none;"
        )
        layout.addWidget(self._label_nb_taches)

        # Scroll area avec cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(style_scroll_area())

        self._conteneur_taches = QWidget()
        self._conteneur_taches.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        self._layout_taches = QVBoxLayout(self._conteneur_taches)
        self._layout_taches.setContentsMargins(0, 0, 8, 0)
        self._layout_taches.setSpacing(6)
        self._layout_taches.addStretch()

        scroll.setWidget(self._conteneur_taches)
        layout.addWidget(scroll, stretch=1)

        return page

    def _on_radio_status(self, index: int):
        self._liste_mode = index
        # Checkboxes visibles uniquement en mode "Actives"
        self._checkboxes_widget.setVisible(index == 0)
        # Bouton "Vider la corbeille" uniquement en mode "Supprimées"
        self._btn_vider_corbeille.setVisible(index == 2)
        self._charger_liste()

    def _on_checkbox_filter(self):
        if self._liste_mode == 0:
            self._charger_liste()

    def _vider_corbeille(self):
        taches = self.viewmodel.lister_taches_supprimees(self._mode_admin)
        if not taches:
            QMessageBox.information(self, "Corbeille", "La corbeille est déjà vide.")
            return
        rep = QMessageBox.question(
            self,
            "Vider la corbeille",
            f"Supprimer définitivement {len(taches)} tâche(s) ?\nCette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            for t in taches:
                self.viewmodel.supprimer_definitivement(t["id"])
            self._charger_liste()

    def _charger_categories_filtre(self):
        current = self.combo_filtre_categorie.currentData()
        self.combo_filtre_categorie.blockSignals(True)
        self.combo_filtre_categorie.clear()
        self.combo_filtre_categorie.addItem("Toutes", None)
        categories = self.viewmodel.lister_categories()
        for cat in categories:
            couleur = cat.get("couleur") or "#2196F3"
            self.combo_filtre_categorie.addItem(
                _color_icon(couleur), cat["nom"], cat["id"]
            )
        if current is not None:
            for i in range(self.combo_filtre_categorie.count()):
                if self.combo_filtre_categorie.itemData(i) == current:
                    self.combo_filtre_categorie.setCurrentIndex(i)
                    break
        self.combo_filtre_categorie.blockSignals(False)

    def _charger_liste(self):
        """Charge et affiche les tâches."""
        self._charger_categories_filtre()

        # Mode supprimées
        if self._liste_mode == 2:
            taches = self.viewmodel.lister_taches_supprimees(self._mode_admin)
            self._afficher_taches(taches, is_deleted=True)
            return

        # Construire critères de tri
        criteres = []
        directions = []
        tri_map = {1: "date", 2: "priorite", 3: "categorie", 4: "titre"}

        idx1 = self.combo_tri_1.currentIndex()
        if idx1 in tri_map:
            criteres.append(tri_map[idx1])
            directions.append(self._direction_asc)

        if self.combo_tri_2.isVisible():
            idx2 = self.combo_tri_2.currentIndex()
            if idx2 in tri_map:
                criteres.append(tri_map[idx2])
                directions.append(self._direction_asc)

        # Mode terminées uniquement
        if self._liste_mode == 1:
            taches = self.viewmodel.lister_taches_triees(
                mode_admin=self._mode_admin,
                categorie_id=self._filtre_categorie_id,
                inclure_terminees=True,
                criteres_tri=criteres if criteres else None,
                directions=directions if directions else None,
            )
            # Filtrer : seulement les terminées
            taches = [t for t in taches if t.get("terminee")]
        else:
            # Actives : inclure terminées si checkbox cochée
            inclure_term = self._check_inclure_terminees.isChecked()
            taches = self.viewmodel.lister_taches_triees(
                mode_admin=self._mode_admin,
                categorie_id=self._filtre_categorie_id,
                inclure_terminees=inclure_term,
                criteres_tri=criteres if criteres else None,
                directions=directions if directions else None,
            )
            # Filtrer missions/admin si checkbox décochée
            if not self._check_missions.isChecked():
                taches = [
                    t
                    for t in taches
                    if t.get("visibilite") != "tous" or t.get("parent_id")
                ]

            # Ajouter les événements si la checkbox est cochée
            if self._check_evenements.isChecked():
                try:
                    evenements = self._evenement_model.lister_evenements()
                    ev_items = []
                    for ev in evenements:
                        ev_item = dict(ev)
                        ev_item["_is_event"] = True
                        # Normaliser pour le tri par date
                        ev_item["date_echeance"] = (ev.get("date_debut") or "")[:10]
                        ev_item["titre"] = ev.get("nom", "")
                        ev_items.append(ev_item)
                    if ev_items:
                        combined = list(taches) + ev_items
                        # Trier le tout par date si tri actif
                        if criteres and "date" in criteres:
                            combined.sort(
                                key=lambda x: x.get("date_echeance") or "9999-12-31",
                                reverse=not self._direction_asc,
                            )
                        taches = combined
                except Exception:
                    pass

        self._afficher_taches(taches)

    def _afficher_taches(self, taches: list[dict], is_deleted: bool = False):
        """Affiche les cards de tâches dans le layout."""
        self._label_nb_taches.setText(f"{len(taches)} tâche(s)")

        # Vider les cards
        while self._layout_taches.count() > 1:
            item = self._layout_taches.takeAt(0)
            if w := item.widget():
                w.deleteLater()

        if not taches:
            labels = {
                0: "Aucune tâche active.",
                1: "Aucune tâche terminée.",
                2: "Aucune tâche supprimée.",
            }
            lbl = QLabel(labels.get(self._liste_mode, "Aucune tâche trouvée."))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                "color: #BBBBBB; font-size: 13pt; padding: 40px; border: none;"
            )
            self._layout_taches.insertWidget(0, lbl)
            return

        tri_map = {1: "date", 2: "priorite", 3: "categorie", 4: "titre"}
        current_sort_key = tri_map.get(self.combo_tri_1.currentIndex(), "")

        insert_idx = 0
        for t in taches:
            # Événements : carte spéciale
            if t.get("_is_event"):
                card = self._creer_event_card(t)
                self._layout_taches.insertWidget(insert_idx, card)
                insert_idx += 1
                continue

            is_subtask = bool(t.get("parent_id"))
            niveau = t.get("niveau", 0)

            # Sous-tâche cachée si parent non déplié
            if is_subtask:
                parent_id = t.get("parent_id")
                if parent_id not in self._expanded_parents:
                    continue

            can_delete = self._mode_admin or t.get("visibilite") == "fonctionnel_seul"

            # Déterminer si ce parent a des enfants
            has_children = False
            is_expanded = False
            if not is_subtask:
                has_children = any(st.get("parent_id") == t.get("id") for st in taches)
                is_expanded = t.get("id") in self._expanded_parents

            card = TacheCard(
                t,
                show_actions=can_delete or is_deleted,
                sort_key=current_sort_key if not is_subtask else "",
                mode_admin=self._mode_admin,
                is_subtask=is_subtask,
                show_restore=is_deleted,
                has_children=has_children,
                is_expanded=is_expanded,
            )
            card.double_clicked.connect(self._voir_tache)
            card.toggled.connect(self._toggle_tache)
            card.action_supprimer.connect(self._supprimer_tache_action)
            card.action_restaurer.connect(self._restaurer_tache)
            card.action_valider.connect(self._valider_mission)
            card.association_clicked.connect(self.association_navigation.emit)
            card.collapse_toggled.connect(self._toggle_collapse)
            card.titre_modifie.connect(self._on_titre_inline_edit)
            card.description_modifiee.connect(self._on_desc_inline_edit)

            if is_subtask:
                # Wrapper pour indenter le CARD entier (bordure comprise)
                wrapper = QWidget()
                wrapper_layout = QHBoxLayout(wrapper)
                wrapper_layout.setContentsMargins(38, 0, 0, 0)
                wrapper_layout.setSpacing(0)
                wrapper_layout.addWidget(card)
                self._layout_taches.insertWidget(insert_idx, wrapper)
            else:
                self._layout_taches.insertWidget(insert_idx, card)
            insert_idx += 1

    def _creer_event_card(self, event: dict) -> QFrame:
        """Crée une carte visuelle pour un événement dans la liste des tâches."""
        ev_color = event.get("couleur", "#FF9800")

        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet(
            f"QFrame {{ background-color: white; border: 1px solid #E0E0E0; "
            f"border-left: 4px solid {ev_color}; border-radius: 10px; }}"
            f"QFrame:hover {{ background-color: #FAFAFA; border-color: {ev_color}; "
            f"border-left: 4px solid {ev_color}; }}"
        )
        frame.setMinimumHeight(70)
        frame.setCursor(Qt.CursorShape.PointingHandCursor)

        root = QHBoxLayout(frame)
        root.setContentsMargins(10, 8, 12, 8)
        root.setSpacing(10)

        lbl_icon = QLabel("📅")
        lbl_icon.setStyleSheet(
            "font-size: 18pt; border: none; background: transparent;"
        )
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        root.addWidget(lbl_icon)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        lbl_titre = QLabel(f"Événement : {event.get('nom', '')}")
        lbl_titre.setStyleSheet(
            f"font-size: 12pt; font-weight: bold; color: {ev_color}; "
            "border: none; background: transparent;"
        )
        info_col.addWidget(lbl_titre)

        d1 = (event.get("date_debut") or "")[:10]
        d2 = (event.get("date_fin") or "")[:10]
        date_str = d1 if d1 == d2 else f"{d1} → {d2}"
        lbl_date = QLabel(date_str)
        lbl_date.setStyleSheet(
            "font-size: 9pt; color: #888; border: none; background: transparent;"
        )
        info_col.addWidget(lbl_date)

        desc = (event.get("description") or "").strip()
        if desc:
            lbl_desc = QLabel(desc)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet(
                "font-size: 9pt; color: #AAA; border: none; background: transparent;"
            )
            info_col.addWidget(lbl_desc)

        root.addLayout(info_col, stretch=1)

        ev_id = event.get("id")
        if ev_id:
            frame.mousePressEvent = lambda e, eid=ev_id: (
                self.association_navigation.emit("evenement", eid),
                e.accept(),
            )

        return frame

    def _toggle_collapse(self, parent_id: int):
        if parent_id in self._expanded_parents:
            self._expanded_parents.discard(parent_id)
        else:
            self._expanded_parents.add(parent_id)
        self._charger_liste()

    def _on_tri_change(self):
        self._charger_liste()

    def _toggle_direction(self):
        self._direction_asc = not self._direction_asc
        self.btn_direction.setText("\u25b2" if self._direction_asc else "\u25bc")
        self._charger_liste()

    def _ajouter_tri_secondaire(self):
        visible = not self.combo_tri_2.isVisible()
        self.combo_tri_2.setVisible(visible)
        self.btn_ajouter_tri.setText("\u2212" if visible else "+")
        if not visible:
            self.combo_tri_2.setCurrentIndex(0)
        self._charger_liste()

    def _on_filtre_change(self):
        self._filtre_categorie_id = self.combo_filtre_categorie.currentData()
        self._charger_liste()

    def _voir_tache(self, tache_id: int):
        self.fiche_tache.charger_tache(tache_id)
        self._changer_page("fiche")

    def _toggle_tache(self, tache_id: int, terminee: bool):
        # basculer_terminee gère automatiquement le cas sous-tâche (→ cochee)
        self.viewmodel.basculer_terminee(tache_id)
        self._charger_liste()

    def _supprimer_tache_action(self, tache_id: int):
        rep = QMessageBox.question(
            self,
            "Confirmation",
            "Supprimer cette tâche ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            self.viewmodel.supprimer_tache(tache_id)
            self._charger_liste()

    def _restaurer_tache(self, tache_id: int):
        self.viewmodel.restaurer_tache(tache_id)
        self._charger_liste()

    def _valider_mission(self, tache_id: int):
        self.viewmodel.valider_mission(tache_id)
        self._charger_liste()

    def _on_titre_inline_edit(self, tache_id: int, nouveau_titre: str):
        """Sauvegarde le titre modifié inline."""
        self.viewmodel.modifier_tache(tache_id, {"titre": nouveau_titre})

    def _on_desc_inline_edit(self, tache_id: int, nouvelle_desc: str):
        """Sauvegarde la description modifiée inline."""
        self.viewmodel.modifier_tache(tache_id, {"description": nouvelle_desc})

    # ------------------------------------------------------------------ #
    #                        Page Création                                #
    # ------------------------------------------------------------------ #

    def _creer_page_creation(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(style_scroll_area())

        conteneur = QWidget()
        conteneur.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout(conteneur)
        layout.setSpacing(16)

        # Titre
        self._label_page_creation = QLabel("Nouvelle tâche")
        font_titre = QFont()
        font_titre.setPointSize(16)
        font_titre.setBold(True)
        self._label_page_creation.setFont(font_titre)
        self._label_page_creation.setStyleSheet("color: #0D47A1;")
        layout.addWidget(self._label_page_creation)

        input_style = (
            "QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit, QTimeEdit {"
            "    min-height: 38px; font-size: 12pt; padding: 6px 10px;"
            "    border: 2px solid #E0E0E0; border-radius: 8px; background: white;"
            "}"
            "QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus,"
            "QDateEdit:focus, QTimeEdit:focus { border-color: #1976D2; }"
        )

        # --- Toggle Tâche / Sous-tâche ---
        self._type_toggle = ModernSegmentedControl(
            ["Tâche", "Sous-tâche"], style="compact"
        )
        self._type_toggle.selectionChanged.connect(self._on_type_toggle)

        type_row = QHBoxLayout()
        type_row.addWidget(self._type_toggle)
        type_row.addStretch()
        layout.addLayout(type_row)

        # --- Section parent (pour sous-tâches) ---
        self._parent_section = QWidget()
        parent_lay = QHBoxLayout(self._parent_section)
        parent_lay.setContentsMargins(0, 0, 0, 0)
        lbl_parent = QLabel("Tâche parent :")
        lbl_parent.setStyleSheet("font-size: 11pt; font-weight: 600; color: #333;")
        parent_lay.addWidget(lbl_parent)
        self._combo_parent = QComboBox()
        self._combo_parent.setMinimumWidth(300)
        self._combo_parent.setStyleSheet(input_style)
        parent_lay.addWidget(self._combo_parent)
        parent_lay.addStretch()
        self._parent_section.setVisible(False)
        layout.addWidget(self._parent_section)

        # Formulaire
        self._groupe_form = QGroupBox("Informations")
        self._form = QFormLayout(self._groupe_form)
        self._form.setSpacing(12)
        self._form.setContentsMargins(15, 25, 15, 15)

        # Titre
        self.tache_input_titre = QLineEdit()
        self.tache_input_titre.setPlaceholderText("Titre de la tâche")
        self.tache_input_titre.setStyleSheet(input_style)
        self._form.addRow("Titre :", self.tache_input_titre)

        # Description
        self.tache_input_description = QTextEdit()
        self.tache_input_description.setFixedHeight(80)
        self.tache_input_description.setPlaceholderText("Description (optionnel)")
        self.tache_input_description.setStyleSheet(input_style)
        self._form.addRow("Description :", self.tache_input_description)

        # --- Champs masquables en mode sous-tâche ---

        # Priorité
        prio_row = QHBoxLayout()
        self.tache_spin_priorite = QSpinBox()
        self.tache_spin_priorite.setMinimum(1)
        self.tache_spin_priorite.setMaximum(10)
        self.tache_spin_priorite.setValue(5)
        self.tache_spin_priorite.setFixedWidth(80)
        self.tache_spin_priorite.setStyleSheet(input_style)
        prio_row.addWidget(self.tache_spin_priorite)

        self._lbl_prio_preview = QLabel("P5")
        self._lbl_prio_preview.setFixedWidth(50)
        self._lbl_prio_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_prio_preview.setStyleSheet(
            f"font-size: 11pt; font-weight: bold; color: white; "
            f"background: {_PRIORITE_COLORS[4]}; border-radius: 8px; padding: 4px 8px;"
        )
        prio_row.addWidget(self._lbl_prio_preview)

        lbl_prio_info = QLabel("(10 = urgente, 1 = basse)")
        lbl_prio_info.setStyleSheet("font-size: 9pt; color: #999; border: none;")
        prio_row.addWidget(lbl_prio_info)
        prio_row.addStretch()
        self._label_priorite = QLabel("Priorité :")
        self._form.addRow(self._label_priorite, prio_row)
        self._prio_row_widget = prio_row

        # Catégorie
        cat_row = QHBoxLayout()
        self.tache_combo_categorie = QComboBox()
        self.tache_combo_categorie.addItem("Aucune catégorie", None)
        self.tache_combo_categorie.setMinimumWidth(200)
        self.tache_combo_categorie.setStyleSheet(input_style)
        cat_row.addWidget(self.tache_combo_categorie)

        self._btn_edit_cat_color = QPushButton()
        self._btn_edit_cat_color.setFixedSize(30, 30)
        self._btn_edit_cat_color.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_edit_cat_color.setToolTip("Modifier la couleur de la catégorie")
        self._btn_edit_cat_color.setStyleSheet(
            "QPushButton { background: #2196F3; border: 2px solid #999; "
            "border-radius: 15px; }"
            "QPushButton:hover { border-color: #333; }"
        )
        self._btn_edit_cat_color.clicked.connect(self._editer_couleur_categorie)
        self._btn_edit_cat_color.setVisible(False)
        cat_row.addWidget(self._btn_edit_cat_color)

        btn_new_cat = QPushButton("+ Créer")
        btn_new_cat.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new_cat.setStyleSheet(
            "QPushButton { background: #1976D2; color: white; "
            "border: none; border-radius: 6px; padding: 8px 14px; "
            "font-size: 10pt; font-weight: bold; }"
            "QPushButton:hover { background: #1565C0; }"
        )
        btn_new_cat.clicked.connect(self._creer_categorie)
        cat_row.addWidget(btn_new_cat)
        cat_row.addStretch()
        self._label_categorie = QLabel("Catégorie :")
        self._form.addRow(self._label_categorie, cat_row)

        # Date échéance
        date_row = QHBoxLayout()
        self.tache_check_date = QCheckBox("Définir une date")
        self.tache_check_date.setStyleSheet("font-size: 11pt;")
        date_row.addWidget(self.tache_check_date)

        self.tache_date_echeance = QDateEdit()
        self.tache_date_echeance.setCalendarPopup(True)
        self.tache_date_echeance.setDate(QDate.currentDate())
        self.tache_date_echeance.setDisplayFormat("dd/MM/yyyy")
        self.tache_date_echeance.setStyleSheet(input_style)
        self.tache_date_echeance.setVisible(False)
        self.tache_check_date.toggled.connect(self.tache_date_echeance.setVisible)
        date_row.addWidget(self.tache_date_echeance)
        date_row.addStretch()
        self._label_echeance = QLabel("Échéance :")
        self._form.addRow(self._label_echeance, date_row)

        # Heure
        heure_row = QHBoxLayout()
        self.tache_check_heure = QCheckBox("Définir une heure")
        self.tache_check_heure.setStyleSheet("font-size: 11pt;")
        heure_row.addWidget(self.tache_check_heure)

        self.tache_heure_echeance = QTimeEdit()
        self.tache_heure_echeance.setDisplayFormat("HH:mm")
        self.tache_heure_echeance.setTime(QTime(9, 0))
        self.tache_heure_echeance.setStyleSheet(input_style)
        self.tache_heure_echeance.setVisible(False)
        self.tache_check_heure.toggled.connect(self.tache_heure_echeance.setVisible)
        heure_row.addWidget(self.tache_heure_echeance)
        heure_row.addStretch()
        self._label_heure = QLabel("Heure :")
        self._form.addRow(self._label_heure, heure_row)

        # Récurrence
        self._recurrence_section = QWidget()
        rec_lay = QVBoxLayout(self._recurrence_section)
        rec_lay.setContentsMargins(0, 0, 0, 0)
        rec_lay.setSpacing(6)

        rec_top = QHBoxLayout()
        self._check_recurrence = QCheckBox("Tâche récurrente")
        self._check_recurrence.setStyleSheet("font-size: 11pt;")
        rec_top.addWidget(self._check_recurrence)

        self._combo_recurrence = QComboBox()
        self._combo_recurrence.addItems(
            ["Quotidien", "Hebdomadaire", "Mensuel", "Annuel", "Personnalisé"]
        )
        self._combo_recurrence.setMinimumWidth(160)
        self._combo_recurrence.setStyleSheet(input_style)
        self._combo_recurrence.setVisible(False)
        self._check_recurrence.toggled.connect(self._combo_recurrence.setVisible)
        self._combo_recurrence.currentIndexChanged.connect(
            self._on_recurrence_type_change
        )
        rec_top.addWidget(self._combo_recurrence)

        self._spin_recurrence_jours = QSpinBox()
        self._spin_recurrence_jours.setMinimum(1)
        self._spin_recurrence_jours.setMaximum(365)
        self._spin_recurrence_jours.setValue(2)
        self._spin_recurrence_jours.setPrefix("Tous les ")
        self._spin_recurrence_jours.setSuffix(" jours")
        self._spin_recurrence_jours.setStyleSheet(input_style)
        self._spin_recurrence_jours.setVisible(False)
        rec_top.addWidget(self._spin_recurrence_jours)
        rec_top.addStretch()
        rec_lay.addLayout(rec_top)

        rec_fin = QHBoxLayout()
        self._check_fin_recurrence = QCheckBox("Date de fin")
        self._check_fin_recurrence.setStyleSheet("font-size: 11pt;")
        self._check_fin_recurrence.setVisible(False)
        self._check_recurrence.toggled.connect(self._check_fin_recurrence.setVisible)
        rec_fin.addWidget(self._check_fin_recurrence)

        self._date_fin_recurrence = QDateEdit()
        self._date_fin_recurrence.setCalendarPopup(True)
        self._date_fin_recurrence.setDate(QDate.currentDate().addMonths(3))
        self._date_fin_recurrence.setDisplayFormat("dd/MM/yyyy")
        self._date_fin_recurrence.setStyleSheet(input_style)
        self._date_fin_recurrence.setVisible(False)
        self._check_fin_recurrence.toggled.connect(self._date_fin_recurrence.setVisible)
        rec_fin.addWidget(self._date_fin_recurrence)
        rec_fin.addStretch()
        rec_lay.addLayout(rec_fin)

        self._label_recurrence = QLabel("Récurrence :")
        self._form.addRow(self._label_recurrence, self._recurrence_section)

        # Visibilité (admin only)
        self._section_visibilite = QWidget()
        vis_layout = QHBoxLayout(self._section_visibilite)
        vis_layout.setContentsMargins(0, 0, 0, 0)
        self.tache_combo_visibilite = QComboBox()
        self.tache_combo_visibilite.addItem("Tous", "tous")
        self.tache_combo_visibilite.addItem("Administratif uniquement", "admin_seul")
        self.tache_combo_visibilite.setMinimumWidth(200)
        self.tache_combo_visibilite.setStyleSheet(input_style)
        vis_layout.addWidget(self.tache_combo_visibilite)
        vis_layout.addStretch()
        self._label_visibilite = QLabel("Visibilité :")
        self._form.addRow(self._label_visibilite, self._section_visibilite)

        # Couleur personnalisée
        couleur_row = QHBoxLayout()
        self.tache_check_couleur = QCheckBox("Couleur personnalisée")
        self.tache_check_couleur.setStyleSheet("font-size: 11pt;")
        couleur_row.addWidget(self.tache_check_couleur)

        self._btn_couleur = QPushButton()
        self._btn_couleur.setFixedSize(36, 36)
        self._btn_couleur.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_couleur.setStyleSheet(
            "QPushButton { background: #2196F3; border: 2px solid #999; "
            "border-radius: 6px; }"
            "QPushButton:hover { border-color: #333; }"
        )
        self._btn_couleur.setVisible(False)
        self._btn_couleur.clicked.connect(self._choisir_couleur)
        self.tache_check_couleur.toggled.connect(self._btn_couleur.setVisible)
        self.tache_check_couleur.toggled.connect(self._on_couleur_toggled)
        couleur_row.addWidget(self._btn_couleur)

        self._recents_widget = QWidget()
        self._recents_layout = QHBoxLayout(self._recents_widget)
        self._recents_layout.setContentsMargins(4, 0, 0, 0)
        self._recents_layout.setSpacing(4)
        self._recents_widget.setVisible(False)
        self.tache_check_couleur.toggled.connect(
            lambda checked: self._recents_widget.setVisible(
                checked and len(self._couleurs_recentes) > 0
            )
        )
        couleur_row.addWidget(self._recents_widget)
        couleur_row.addStretch()
        self._label_couleur = QLabel("Couleur :")
        self._form.addRow(self._label_couleur, couleur_row)

        # Association multi-type (badge compact + recherche par cards)
        assoc_container = QVBoxLayout()
        assoc_container.setSpacing(6)

        # Ligne badges sélectionnés + bouton "+"
        self._assoc_badges_layout = QHBoxLayout()
        self._assoc_badges_layout.setSpacing(6)
        self._assoc_badges_layout.setContentsMargins(0, 0, 0, 0)

        self._assoc_lbl_aucune = QLabel("Aucune association")
        self._assoc_lbl_aucune.setStyleSheet(
            "font-size: 10pt; color: #999; border: none;"
        )
        self._assoc_badges_layout.addWidget(self._assoc_lbl_aucune)

        self._assoc_badges_layout.addStretch()

        self._btn_ajouter_assoc = QPushButton("+ Ajouter")
        self._btn_ajouter_assoc.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_ajouter_assoc.setStyleSheet(
            "QPushButton { background: #E3F2FD; color: #1976D2; border: 1px solid #90CAF9; "
            "border-radius: 6px; font-size: 9pt; font-weight: 600; padding: 4px 12px; }"
            "QPushButton:hover { background: #BBDEFB; }"
        )
        self._btn_ajouter_assoc.clicked.connect(self._assoc_montrer_recherche)
        self._assoc_badges_layout.addWidget(self._btn_ajouter_assoc)
        assoc_container.addLayout(self._assoc_badges_layout)

        # Section recherche (cachée par défaut)
        self._assoc_recherche_widget = QWidget()
        self._assoc_recherche_widget.setVisible(False)
        rech_layout = QVBoxLayout(self._assoc_recherche_widget)
        rech_layout.setContentsMargins(0, 0, 0, 0)
        rech_layout.setSpacing(4)

        rech_top = QHBoxLayout()
        rech_top.setSpacing(8)
        self._combo_assoc_type = QComboBox()
        self._combo_assoc_type.addItems(
            ["Client", "Vente", "Commande", "Produit", "Code Promo", "Événement"]
        )
        self._combo_assoc_type.setMinimumWidth(130)
        self._combo_assoc_type.setStyleSheet(input_style)
        self._combo_assoc_type.currentIndexChanged.connect(self._on_assoc_type_change)
        rech_top.addWidget(self._combo_assoc_type)

        self._input_assoc_recherche = QLineEdit()
        self._input_assoc_recherche.setPlaceholderText("🔍 Rechercher...")
        self._input_assoc_recherche.setStyleSheet(input_style)
        self._input_assoc_recherche.textChanged.connect(self._on_assoc_recherche)
        rech_top.addWidget(self._input_assoc_recherche, stretch=1)

        btn_fermer_rech = QPushButton("✕")
        btn_fermer_rech.setFixedSize(28, 28)
        btn_fermer_rech.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_fermer_rech.setStyleSheet(
            "QPushButton { background: #FFCDD2; color: #C62828; border: none; "
            "border-radius: 14px; font-size: 11pt; font-weight: bold; }"
            "QPushButton:hover { background: #EF9A9A; }"
        )
        btn_fermer_rech.clicked.connect(
            lambda: self._assoc_recherche_widget.setVisible(False)
        )
        rech_top.addWidget(btn_fermer_rech)
        rech_layout.addLayout(rech_top)

        # Zone résultats (combo simple pour le moment — max 20 résultats)
        self._combo_assoc_resultat = QComboBox()
        self._combo_assoc_resultat.setMinimumWidth(300)
        self._combo_assoc_resultat.setStyleSheet(input_style)
        self._combo_assoc_resultat.setPlaceholderText("Sélectionner un résultat...")
        self._combo_assoc_resultat.activated.connect(self._on_assoc_selectionne)
        rech_layout.addWidget(self._combo_assoc_resultat)

        assoc_container.addWidget(self._assoc_recherche_widget)

        # State interne : dict type → (id, label)
        self._associations: dict[str, tuple[int, str]] = {}

        self._label_association = QLabel("Associer à :")
        self._form.addRow(self._label_association, assoc_container)

        layout.addWidget(self._groupe_form)

        # Boutons
        layout_boutons = QHBoxLayout()
        layout_boutons.addStretch()

        btn_annuler = QPushButton("Annuler")
        btn_annuler.setMinimumHeight(50)
        btn_annuler.setMinimumWidth(150)
        btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_annuler.setStyleSheet(
            "QPushButton { background-color: #9E9E9E; color: white; "
            "border: none; border-radius: 8px; padding: 12px 24px; "
            "font-size: 13pt; font-weight: 600; }"
            "QPushButton:hover { background-color: #757575; }"
        )
        btn_annuler.clicked.connect(self._annuler_creation)
        layout_boutons.addWidget(btn_annuler)

        self.tache_btn_creer = QPushButton("Créer la tâche")
        self.tache_btn_creer.setMinimumHeight(50)
        self.tache_btn_creer.setMinimumWidth(200)
        self.tache_btn_creer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tache_btn_creer.setStyleSheet(
            "QPushButton { background-color: #1976D2; color: white; "
            "border: none; border-radius: 8px; padding: 12px 24px; "
            "font-size: 13pt; font-weight: 600; }"
            "QPushButton:hover { background-color: #1565C0; }"
        )
        self.tache_btn_creer.clicked.connect(self._creer_tache)
        layout_boutons.addWidget(self.tache_btn_creer)

        layout.addLayout(layout_boutons)
        layout.addStretch()

        scroll.setWidget(conteneur)
        return scroll

    # Store references to hideable rows
    _SUBTASK_HIDE_FIELDS = []

    def _on_type_toggle(self, index: int):
        """Toggle entre Tâche et Sous-tâche."""
        is_subtask = index == 1
        self._parent_section.setVisible(is_subtask)

        # Masquer les champs non nécessaires pour les sous-tâches
        # Note : date/heure restent visibles (optionnels) pour les sous-tâches
        fields_to_hide = [
            (self._label_priorite, self.tache_spin_priorite.parent()),
            (self._label_categorie, self.tache_combo_categorie.parent()),
            (self._label_recurrence, self._recurrence_section),
            (self._label_couleur, self.tache_check_couleur.parent()),
        ]
        for label, widget in fields_to_hide:
            self._form.setRowVisible(label, not is_subtask)
        # Visibilité : uniquement visible en mode admin ET pas sous-tâche
        self._form.setRowVisible(
            self._label_visibilite, not is_subtask and self._mode_admin
        )
        # Association : masquer pour sous-tâches
        self._form.setRowVisible(self._label_association, not is_subtask)

        if is_subtask:
            self._charger_parents_combo()

    def _charger_parents_combo(self):
        """Charge les tâches pouvant être parentes."""
        self._combo_parent.blockSignals(True)
        self._combo_parent.clear()
        parents = self.viewmodel.lister_taches_parents(self._mode_admin, max_niveau=1)
        for p in parents:
            prefix = "  └ " if p.get("niveau", 0) > 0 else ""
            self._combo_parent.addItem(f"{prefix}{p['titre']}", p["id"])
        self._combo_parent.blockSignals(False)

    def _on_recurrence_type_change(self, index: int):
        """Affiche le spin 'tous les N jours' si personnalisé."""
        self._spin_recurrence_jours.setVisible(index == 4)

    # ------------------------------------------------------------------ #
    #                        Connexion des signaux                        #
    # ------------------------------------------------------------------ #

    def _connecter_signaux(self):
        self.tache_spin_priorite.valueChanged.connect(self._update_prio_preview)
        self.tache_combo_categorie.currentIndexChanged.connect(
            lambda: self._maj_btn_edit_cat_color()
        )

    def _update_prio_preview(self, val: int):
        color = _PRIORITE_COLORS[max(0, min(val - 1, 9))]
        self._lbl_prio_preview.setText(f"P{val}")
        self._lbl_prio_preview.setStyleSheet(
            f"font-size: 11pt; font-weight: bold; color: white; "
            f"background: {color}; border-radius: 8px; padding: 4px 8px;"
        )

    # ------------------------------------------------------------------ #
    #                        Logique Création / Édition                   #
    # ------------------------------------------------------------------ #

    def _charger_categories_creation(self):
        current = self.tache_combo_categorie.currentData()
        self.tache_combo_categorie.blockSignals(True)
        self.tache_combo_categorie.clear()
        self.tache_combo_categorie.addItem("Aucune catégorie", None)
        categories = self.viewmodel.lister_categories()
        for cat in categories:
            couleur = cat.get("couleur") or "#2196F3"
            self.tache_combo_categorie.addItem(
                _color_icon(couleur), cat["nom"], cat["id"]
            )
        if current is not None:
            for i in range(self.tache_combo_categorie.count()):
                if self.tache_combo_categorie.itemData(i) == current:
                    self.tache_combo_categorie.setCurrentIndex(i)
                    break
        self.tache_combo_categorie.blockSignals(False)
        self._maj_btn_edit_cat_color()

    def _creer_categorie(self):
        from PySide6.QtWidgets import QInputDialog

        nom, ok = QInputDialog.getText(
            self, "Nouvelle catégorie", "Nom de la catégorie :"
        )
        if ok and nom.strip():
            cats = self.viewmodel.lister_categories()
            idx_color = len(cats) % len(_AUTO_CATEGORY_COLORS)
            couleur = _AUTO_CATEGORY_COLORS[idx_color]
            cat_id = self.viewmodel.creer_categorie(nom.strip(), couleur)
            if cat_id:
                self._charger_categories_creation()
                for i in range(self.tache_combo_categorie.count()):
                    if self.tache_combo_categorie.itemData(i) == cat_id:
                        self.tache_combo_categorie.setCurrentIndex(i)
                        break

    def _creer_tache(self):
        """Crée ou modifie la tâche via le ViewModel."""
        titre = self.tache_input_titre.text().strip()
        if not titre:
            QMessageBox.warning(self, "Attention", "Le titre est obligatoire.")
            return

        is_subtask = self._type_toggle.current_index == 1

        description = self.tache_input_description.toPlainText()

        if is_subtask:
            # Sous-tâche : hérite priorité/catégorie/visibilité du parent
            parent_id = self._combo_parent.currentData()
            if not parent_id:
                QMessageBox.warning(self, "Attention", "Sélectionnez une tâche parent.")
                return
            parent = self.viewmodel.obtenir_tache(parent_id)
            if not parent:
                QMessageBox.warning(self, "Erreur", "Tâche parent introuvable.")
                return
            priorite = parent.get("priorite", 5)
            categorie_id = parent.get("categorie_id")
            # Date/heure optionnelles pour sous-tâches (pas héritées du parent)
            date_echeance = None
            if self.tache_check_date.isChecked():
                date_echeance = self.tache_date_echeance.date().toString("yyyy-MM-dd")
            heure_echeance = None
            if self.tache_check_heure.isChecked():
                heure_echeance = self.tache_heure_echeance.time().toString("HH:mm")
            if self._mode_admin:
                visibilite = parent.get("visibilite", "tous")
            else:
                visibilite = "fonctionnel_seul"
            couleur = parent.get("couleur")
            niveau = (parent.get("niveau", 0) or 0) + 1
            type_recurrence = None
            intervalle_recurrence = 1
            date_fin_recurrence = None
        else:
            parent_id = None
            niveau = 0
            priorite = self.tache_spin_priorite.value()
            categorie_id = self.tache_combo_categorie.currentData()

            date_echeance = None
            if self.tache_check_date.isChecked():
                date_echeance = self.tache_date_echeance.date().toString("yyyy-MM-dd")

            heure_echeance = None
            if self.tache_check_heure.isChecked():
                heure_echeance = self.tache_heure_echeance.time().toString("HH:mm")

            if self._mode_admin:
                visibilite = self.tache_combo_visibilite.currentData()
            else:
                visibilite = "fonctionnel_seul"

            couleur = None
            if self.tache_check_couleur.isChecked() and self._couleur_tache:
                couleur = self._couleur_tache
                if couleur in self._couleurs_recentes:
                    self._couleurs_recentes.remove(couleur)
                self._couleurs_recentes.insert(0, couleur)
                self._couleurs_recentes = self._couleurs_recentes[:8]

            # Récurrence
            type_recurrence = None
            intervalle_recurrence = 1
            date_fin_recurrence = None
            if self._check_recurrence.isChecked():
                rec_map = {
                    0: "quotidien",
                    1: "hebdomadaire",
                    2: "mensuel",
                    3: "annuel",
                    4: "personnalise",
                }
                type_recurrence = rec_map.get(self._combo_recurrence.currentIndex())
                if type_recurrence == "personnalise":
                    intervalle_recurrence = self._spin_recurrence_jours.value()
                if self._check_fin_recurrence.isChecked():
                    date_fin_recurrence = self._date_fin_recurrence.date().toString(
                        "yyyy-MM-dd"
                    )

        # Associations multi-types
        client_id = None
        vente_id = None
        commande_id = None
        produit_id = None
        code_promo_id = None
        evenement_id = None
        if not is_subtask:
            for atype, (aid, _) in self._associations.items():
                if atype == "client":
                    client_id = aid
                elif atype == "vente":
                    vente_id = aid
                elif atype == "commande":
                    commande_id = aid
                elif atype == "produit":
                    produit_id = aid
                elif atype == "code_promo":
                    code_promo_id = aid
                elif atype == "evenement":
                    evenement_id = aid

        if self._tache_en_edition:
            # Mode édition
            data = {
                "titre": titre,
                "description": description,
                "priorite": priorite,
                "categorie_id": categorie_id,
                "date_echeance": date_echeance,
                "heure_echeance": heure_echeance,
                "visibilite": visibilite,
                "couleur": couleur,
                "type_recurrence": type_recurrence,
                "intervalle_recurrence": intervalle_recurrence,
                "date_fin_recurrence": date_fin_recurrence,
                "client_id": client_id,
                "vente_id": vente_id,
                "commande_id": commande_id,
                "produit_id": produit_id,
                "code_promo_id": code_promo_id,
                "evenement_id": evenement_id,
            }
            ok = self.viewmodel.modifier_tache(self._tache_en_edition, data)
            if ok:
                QMessageBox.information(
                    self,
                    "Tâche modifiée",
                    f"Tâche #{self._tache_en_edition} modifiée avec succès !",
                )
                self._tache_en_edition = None
                self._reinitialiser_creation()
                self._changer_page("liste")
            else:
                QMessageBox.warning(self, "Erreur", "Erreur lors de la modification.")
        else:
            tache_id = self.viewmodel.creer_tache(
                titre=titre,
                description=description,
                priorite=priorite,
                categorie_id=categorie_id,
                date_echeance=date_echeance,
                heure_echeance=heure_echeance,
                visibilite=visibilite,
                couleur=couleur,
                parent_id=parent_id,
                niveau=niveau,
                type_recurrence=type_recurrence,
                intervalle_recurrence=intervalle_recurrence,
                date_fin_recurrence=date_fin_recurrence,
                client_id=client_id,
                vente_id=vente_id,
                commande_id=commande_id,
                produit_id=produit_id,
                code_promo_id=code_promo_id,
                evenement_id=evenement_id,
            )
            if tache_id:
                # Auto-expand parent pour voir la sous-tâche créée
                if parent_id:
                    self._expanded_parents.add(parent_id)
                QMessageBox.information(
                    self, "Tâche créée", f"Tâche #{tache_id} créée avec succès !"
                )
                self._reinitialiser_creation()
                self._changer_page("liste")

    def _editer_tache(self, tache_id: int):
        """Pré-remplit le formulaire pour édition."""
        data = self.viewmodel.obtenir_tache(tache_id)
        if not data:
            return

        self._tache_en_edition = tache_id
        self._label_page_creation.setText(f"Modifier la tâche #{tache_id}")
        self.tache_btn_creer.setText("Enregistrer les modifications")

        # Pré-remplir
        self.tache_input_titre.setText(data.get("titre", ""))
        self.tache_input_description.setPlainText(data.get("description", ""))
        self.tache_spin_priorite.setValue(data.get("priorite", 5))

        # Catégorie
        self._charger_categories_creation()
        cat_id = data.get("categorie_id")
        if cat_id:
            for i in range(self.tache_combo_categorie.count()):
                if self.tache_combo_categorie.itemData(i) == cat_id:
                    self.tache_combo_categorie.setCurrentIndex(i)
                    break

        # Date
        if data.get("date_echeance"):
            self.tache_check_date.setChecked(True)
            parts = str(data["date_echeance"])[:10].split("-")
            if len(parts) == 3:
                self.tache_date_echeance.setDate(
                    QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                )

        # Heure
        if data.get("heure_echeance"):
            self.tache_check_heure.setChecked(True)
            h_parts = str(data["heure_echeance"]).split(":")
            if len(h_parts) >= 2:
                self.tache_heure_echeance.setTime(
                    QTime(int(h_parts[0]), int(h_parts[1]))
                )

        # Visibilité
        vis = data.get("visibilite", "tous")
        for i in range(self.tache_combo_visibilite.count()):
            if self.tache_combo_visibilite.itemData(i) == vis:
                self.tache_combo_visibilite.setCurrentIndex(i)
                break

        # Couleur
        if data.get("couleur"):
            self.tache_check_couleur.setChecked(True)
            self._couleur_tache = data["couleur"]
            self._btn_couleur.setStyleSheet(
                f"QPushButton {{ background: {data['couleur']}; "
                f"border: 2px solid #999; border-radius: 6px; }}"
                f"QPushButton:hover {{ border-color: #333; }}"
            )

        # Récurrence
        if data.get("type_recurrence"):
            self._check_recurrence.setChecked(True)
            rec_map = {
                "quotidien": 0,
                "hebdomadaire": 1,
                "mensuel": 2,
                "annuel": 3,
                "personnalise": 4,
            }
            self._combo_recurrence.setCurrentIndex(
                rec_map.get(data["type_recurrence"], 0)
            )
            if data["type_recurrence"] == "personnalise":
                self._spin_recurrence_jours.setValue(
                    data.get("intervalle_recurrence", 2)
                )
            if data.get("date_fin_recurrence"):
                self._check_fin_recurrence.setChecked(True)
                parts = str(data["date_fin_recurrence"])[:10].split("-")
                if len(parts) == 3:
                    self._date_fin_recurrence.setDate(
                        QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                    )

        # Associations
        self._associations.clear()
        _assoc_fields = {
            "client_id": ("client", "👤 Client"),
            "vente_id": ("vente", "🛒 Vente"),
            "commande_id": ("commande", "📦 Commande"),
            "produit_id": ("produit", "🏷 Produit"),
            "code_promo_id": ("code_promo", "🎟 Code"),
            "evenement_id": ("evenement", "📅 Événement"),
        }
        for field, (type_key, prefix) in _assoc_fields.items():
            val = data.get(field)
            if val:
                self._associations[type_key] = (val, f"{prefix} #{val}")
        self._rafraichir_badges_assoc()

        self._changer_page("creation")

    def _reinitialiser_creation(self):
        self._tache_en_edition = None
        self._label_page_creation.setText("Nouvelle tâche")
        self.tache_btn_creer.setText("Créer la tâche")
        self._type_toggle.select(0)
        self._parent_section.setVisible(False)
        self.tache_input_titre.clear()
        self.tache_input_description.clear()
        self.tache_spin_priorite.setValue(5)
        self.tache_combo_categorie.setCurrentIndex(0)
        self.tache_check_date.setChecked(False)
        self.tache_check_heure.setChecked(False)
        self.tache_date_echeance.setDate(QDate.currentDate())
        self.tache_heure_echeance.setTime(QTime(9, 0))
        self.tache_combo_visibilite.setCurrentIndex(0)
        self.tache_check_couleur.setChecked(False)
        self._couleur_tache = None
        self._btn_couleur.setStyleSheet(
            "QPushButton { background: #2196F3; border: 2px solid #999; "
            "border-radius: 6px; }"
            "QPushButton:hover { border-color: #333; }"
        )
        self._check_recurrence.setChecked(False)
        self._check_fin_recurrence.setChecked(False)
        self._associations.clear()
        self._assoc_recherche_widget.setVisible(False)
        self._rafraichir_badges_assoc()

    # ------------------------------------------------------------------ #
    #                        Couleur + Catégories                         #
    # ------------------------------------------------------------------ #

    def _on_couleur_toggled(self, checked: bool):
        if not checked:
            self._couleur_tache = None

    def _choisir_couleur(self):
        from PySide6.QtWidgets import QColorDialog

        initial = QColor(self._couleur_tache or "#2196F3")
        color = QColorDialog.getColor(initial, self, "Couleur de la tâche")
        if color.isValid():
            self._couleur_tache = color.name()
            self._btn_couleur.setStyleSheet(
                f"QPushButton {{ background: {self._couleur_tache}; "
                f"border: 2px solid #999; border-radius: 6px; }}"
                f"QPushButton:hover {{ border-color: #333; }}"
            )
            self._rafraichir_couleurs_recentes()

    def _selectionner_couleur_recente(self, couleur: str):
        self._couleur_tache = couleur
        self._btn_couleur.setStyleSheet(
            f"QPushButton {{ background: {couleur}; "
            f"border: 2px solid #999; border-radius: 6px; }}"
            f"QPushButton:hover {{ border-color: #333; }}"
        )

    def _rafraichir_couleurs_recentes(self):
        while self._recents_layout.count():
            item = self._recents_layout.takeAt(0)
            if w := item.widget():
                w.deleteLater()

        for c in self._couleurs_recentes[:8]:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{ background: {c}; border: 1.5px solid #AAA; "
                f"border-radius: 4px; }}"
                f"QPushButton:hover {{ border-color: #333; }}"
            )
            btn.setToolTip(c)
            btn.clicked.connect(
                lambda checked=False, col=c: self._selectionner_couleur_recente(col)
            )
            self._recents_layout.addWidget(btn)

        self._recents_widget.setVisible(
            self.tache_check_couleur.isChecked() and len(self._couleurs_recentes) > 0
        )

    def _maj_btn_edit_cat_color(self):
        cat_id = self.tache_combo_categorie.currentData()
        if cat_id and self._mode_admin:
            self._btn_edit_cat_color.setVisible(True)
            cats = self.viewmodel.lister_categories()
            for cat in cats:
                if cat["id"] == cat_id:
                    couleur = cat.get("couleur") or "#2196F3"
                    self._btn_edit_cat_color.setStyleSheet(
                        f"QPushButton {{ background: {couleur}; border: 2px solid #999; "
                        f"border-radius: 15px; }}"
                        f"QPushButton:hover {{ border-color: #333; }}"
                    )
                    break
        else:
            self._btn_edit_cat_color.setVisible(False)

    def _editer_couleur_categorie(self):
        from PySide6.QtWidgets import QColorDialog

        cat_id = self.tache_combo_categorie.currentData()
        if not cat_id:
            return

        cats = self.viewmodel.lister_categories()
        couleur_actuelle = "#2196F3"
        for cat in cats:
            if cat["id"] == cat_id:
                couleur_actuelle = cat.get("couleur") or "#2196F3"
                break

        color = QColorDialog.getColor(
            QColor(couleur_actuelle), self, "Couleur de la catégorie"
        )
        if color.isValid():
            self.viewmodel.modifier_couleur_categorie(cat_id, color.name())
            self._charger_categories_creation()
            self._charger_categories_filtre()

    def _assoc_montrer_recherche(self):
        """Affiche la section de recherche d'association."""
        self._assoc_recherche_widget.setVisible(True)
        self._input_assoc_recherche.clear()
        self._combo_assoc_resultat.clear()
        self._on_assoc_recherche("")

    def _on_assoc_type_change(self, index: int):
        """Relance la recherche quand on change de type."""
        self._input_assoc_recherche.clear()
        self._combo_assoc_resultat.clear()
        self._on_assoc_recherche("")

    def _on_assoc_recherche(self, texte: str):
        """Recherche les entités selon le type sélectionné."""
        self._combo_assoc_resultat.clear()
        type_idx = self._combo_assoc_type.currentIndex()
        _type_keys = [
            "client",
            "vente",
            "commande",
            "produit",
            "code_promo",
            "evenement",
        ]
        type_key = _type_keys[type_idx] if type_idx < len(_type_keys) else ""

        if type_key == "client":
            resultats = self.viewmodel.rechercher_clients(texte)
            for r in resultats:
                nom = f"{r.get('prenom', '')} {r.get('nom', '')}".strip()
                self._combo_assoc_resultat.addItem(f"👤 #{r['id']} — {nom}", r["id"])
        elif type_key == "vente":
            resultats = self.viewmodel.rechercher_ventes(texte)
            for r in resultats:
                tid = r.get("transaction_id", "")
                client = (
                    f"{r.get('client_prenom', '')} {r.get('client_nom', '')}".strip()
                )
                self._combo_assoc_resultat.addItem(
                    f"🛒 {tid[:8]}… — {client}", r.get("id")
                )
        elif type_key == "commande":
            resultats = self.viewmodel.rechercher_commandes(texte)
            for r in resultats:
                ref = r.get("reference", f"#{r.get('id', '')}")
                client = (
                    f"{r.get('client_prenom', '')} {r.get('client_nom', '')}".strip()
                )
                self._combo_assoc_resultat.addItem(f"📦 {ref} — {client}", r.get("id"))
        elif type_key == "produit":
            resultats = self.viewmodel.rechercher_produits(texte)
            for r in resultats:
                nom = r.get("nom", "")
                prix = r.get("prix", 0)
                self._combo_assoc_resultat.addItem(
                    f"🏷 {nom} ({prix:.2f}€)", r.get("id")
                )
        elif type_key == "code_promo":
            resultats = self.viewmodel.rechercher_codes_promo(texte)
            for r in resultats:
                code = r.get("code", "")
                pct = r.get("pourcentage", 0)
                self._combo_assoc_resultat.addItem(f"🎟 {code} ({pct}%)", r.get("id"))
        elif type_key == "evenement":
            resultats = self.viewmodel.rechercher_evenements(texte)
            for r in resultats:
                nom = r.get("nom", "")
                date = r.get("date_debut", "")[:10]
                self._combo_assoc_resultat.addItem(f"📅 {nom} ({date})", r.get("id"))

    def _on_assoc_selectionne(self, index: int):
        """Un résultat est sélectionné dans les résultats."""
        if index < 0:
            return
        _type_keys = [
            "client",
            "vente",
            "commande",
            "produit",
            "code_promo",
            "evenement",
        ]
        type_idx = self._combo_assoc_type.currentIndex()
        type_key = _type_keys[type_idx] if type_idx < len(_type_keys) else ""

        assoc_id = self._combo_assoc_resultat.itemData(index)
        assoc_label = self._combo_assoc_resultat.itemText(index)
        if not assoc_id:
            return

        # Max 1 par type : remplace si déjà existant
        self._associations[type_key] = (assoc_id, assoc_label)
        self._assoc_recherche_widget.setVisible(False)
        self._rafraichir_badges_assoc()

    def _rafraichir_badges_assoc(self):
        """Reconstruit les badges d'association sélectionnés."""
        # Supprimer les anciens badges (sauf "Aucune" et stretch et btn "+")
        while self._assoc_badges_layout.count() > 0:
            item = self._assoc_badges_layout.takeAt(0)
            if w := item.widget():
                w.deleteLater()

        if not self._associations:
            self._assoc_lbl_aucune = QLabel("Aucune association")
            self._assoc_lbl_aucune.setStyleSheet(
                "font-size: 10pt; color: #999; border: none;"
            )
            self._assoc_badges_layout.addWidget(self._assoc_lbl_aucune)
        else:
            _type_colors = {
                "client": "#5C6BC0",
                "vente": "#43A047",
                "commande": "#EF6C00",
                "produit": "#7B1FA2",
                "code_promo": "#00897B",
                "evenement": "#F4511E",
            }
            for type_key, (assoc_id, label) in self._associations.items():
                badge = QWidget()
                badge.setStyleSheet("border: none;")
                badge_lay = QHBoxLayout(badge)
                badge_lay.setContentsMargins(0, 0, 0, 0)
                badge_lay.setSpacing(4)

                color = _type_colors.get(type_key, "#666")
                lbl = QLabel(label)
                lbl.setStyleSheet(
                    f"font-size: 9pt; font-weight: 600; color: white; "
                    f"background-color: {color}; border-radius: 6px; "
                    f"padding: 4px 8px; border: none;"
                )
                badge_lay.addWidget(lbl)

                btn_changer = QPushButton("Changer")
                btn_changer.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_changer.setFixedHeight(24)
                btn_changer.setStyleSheet(
                    "QPushButton { background: #E0E0E0; color: #333; border: none; "
                    "border-radius: 4px; font-size: 8pt; padding: 2px 8px; }"
                    "QPushButton:hover { background: #BDBDBD; }"
                )
                tk = type_key
                btn_changer.clicked.connect(
                    lambda checked=False, t=tk: self._assoc_changer(t)
                )
                badge_lay.addWidget(btn_changer)

                btn_suppr = QPushButton("✕")
                btn_suppr.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_suppr.setFixedSize(22, 22)
                btn_suppr.setStyleSheet(
                    "QPushButton { background: #FFCDD2; color: #C62828; border: none; "
                    "border-radius: 11px; font-size: 9pt; font-weight: bold; }"
                    "QPushButton:hover { background: #EF9A9A; }"
                )
                btn_suppr.clicked.connect(
                    lambda checked=False, t=tk: self._assoc_supprimer(t)
                )
                badge_lay.addWidget(btn_suppr)

                self._assoc_badges_layout.addWidget(badge)

        self._assoc_badges_layout.addStretch()

        self._btn_ajouter_assoc = QPushButton("+ Ajouter")
        self._btn_ajouter_assoc.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_ajouter_assoc.setStyleSheet(
            "QPushButton { background: #E3F2FD; color: #1976D2; border: 1px solid #90CAF9; "
            "border-radius: 6px; font-size: 9pt; font-weight: 600; padding: 4px 12px; }"
            "QPushButton:hover { background: #BBDEFB; }"
        )
        self._btn_ajouter_assoc.clicked.connect(self._assoc_montrer_recherche)
        self._assoc_badges_layout.addWidget(self._btn_ajouter_assoc)

    def _assoc_changer(self, type_key: str):
        """Change une association existante (supprime et ouvre la recherche pour ce type)."""
        self._associations.pop(type_key, None)
        self._rafraichir_badges_assoc()
        _type_indices = {
            "client": 0,
            "vente": 1,
            "commande": 2,
            "produit": 3,
            "code_promo": 4,
            "evenement": 5,
        }
        idx = _type_indices.get(type_key, 0)
        self._combo_assoc_type.setCurrentIndex(idx)
        self._assoc_montrer_recherche()

    def _assoc_supprimer(self, type_key: str):
        """Supprime une association."""
        self._associations.pop(type_key, None)
        self._rafraichir_badges_assoc()

    def _annuler_creation(self):
        self._reinitialiser_creation()
        self._changer_page("liste")
