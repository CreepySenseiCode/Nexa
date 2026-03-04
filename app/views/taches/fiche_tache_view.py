"""Vue détail d'une tâche (fiche tâche)."""

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
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from utils.styles import Couleurs, style_scroll_area

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

_RECURRENCE_LABELS = {
    "quotidien": "🔄 Quotidien",
    "hebdomadaire": "🔄 Hebdomadaire",
    "mensuel": "🔄 Mensuel",
    "annuel": "🔄 Annuel",
    "personnalise": "🔄 Personnalisé",
}


def _shadow(blur=18, dy=4, alpha=70, color="#000"):
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(blur)
    fx.setOffset(0, dy)
    c = QColor(color)
    c.setAlpha(alpha)
    fx.setColor(c)
    return fx


class FicheTacheView(QWidget):
    """Fiche détail d'une tâche."""

    retour_demande = Signal()
    edition_demandee = Signal(int)  # tache_id
    association_navigation = Signal(str, int)  # type, id

    def __init__(self, viewmodel=None, parent=None):  # ← parent=None par défaut
        super().__init__(parent)
        self.viewmodel = viewmodel
        self._tache_id = None
        self._mode_admin = True
        self._construire_ui()

    def _construire_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barre retour
        barre = QHBoxLayout()
        barre.setContentsMargins(24, 14, 24, 6)
        self.btn_retour = QPushButton("\u2190 Retour")
        self.btn_retour.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_retour.setStyleSheet(
            "QPushButton { background: none; border: none; color: #1565C0; "
            "font-size: 12pt; font-weight: 600; padding: 6px 0; }"
            "QPushButton:hover { color: #1976D2; }"
        )
        self.btn_retour.clicked.connect(self.retour_demande.emit)
        barre.addWidget(self.btn_retour)
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
        self._build_sous_taches()
        self._build_commande_link()

        self.layout_contenu.addStretch()
        scroll.setWidget(self.conteneur)
        layout.addWidget(scroll)

    def _build_header(self):
        self.header_frame = QFrame()
        self.header_frame.setMinimumHeight(160)
        self.header_frame.setStyleSheet(
            "QFrame {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            "    stop:0 #0D47A1, stop:0.45 #1565C0, stop:1 #1976D2);"
            "  border-radius: 20px;"
            "}"
        )
        self.header_frame.setGraphicsEffect(_shadow(28, 8, 90, "#0D47A1"))

        outer = QVBoxLayout(self.header_frame)
        outer.setContentsMargins(30, 22, 30, 22)
        outer.setSpacing(0)

        top = QHBoxLayout()
        top.setSpacing(14)

        self._lbl_icon = QLabel("✅")
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

        # Badges colonne droite
        self._badges_col = QVBoxLayout()
        self._badges_col.setSpacing(6)

        self.label_priorite = QLabel()
        self.label_priorite.setStyleSheet(
            "font-size: 12pt; font-weight: 700; color: white; border: none; "
            "background: rgba(255,255,255,0.22); border-radius: 14px; padding: 5px 16px;"
        )
        self._badges_col.addWidget(
            self.label_priorite, alignment=Qt.AlignmentFlag.AlignRight
        )

        self._lbl_recurrence = QLabel()
        self._lbl_recurrence.setStyleSheet(
            "font-size: 10pt; font-weight: 600; color: white; border: none; "
            "background: rgba(255,255,255,0.18); border-radius: 10px; padding: 3px 12px;"
        )
        self._badges_col.addWidget(
            self._lbl_recurrence, alignment=Qt.AlignmentFlag.AlignRight
        )
        self._lbl_recurrence.hide()

        self._lbl_stamp = QLabel()
        self._lbl_stamp.setStyleSheet(
            "font-size: 10pt; font-weight: 700; color: white; border: none; "
            "background: rgba(255,255,255,0.25); border-radius: 10px; padding: 3px 12px;"
        )
        self._badges_col.addWidget(
            self._lbl_stamp, alignment=Qt.AlignmentFlag.AlignRight
        )
        self._lbl_stamp.hide()

        top.addLayout(self._badges_col)
        outer.addLayout(top)
        outer.addStretch()

        bas = QHBoxLayout()
        bas.setSpacing(16)

        self.label_statut = QLabel()
        self.label_statut.setStyleSheet(
            "font-size: 14pt; font-weight: 700; color: white; border: none; background: none;"
        )
        bas.addWidget(self.label_statut)
        bas.addStretch()

        self.label_date = QLabel()
        self.label_date.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.label_date.setStyleSheet(
            "font-size: 11pt; font-weight: 600; color: white; border: none; "
            "background: rgba(255,255,255,0.20); border-radius: 12px; padding: 5px 14px;"
        )
        bas.addWidget(self.label_date)
        outer.addLayout(bas)

        self.layout_contenu.addWidget(self.header_frame)

    def _build_actions(self):
        self._frame_actions = QFrame()
        self._frame_actions.setStyleSheet(
            "QFrame { background: #E3F2FD; border: 1.5px solid #90CAF9; border-radius: 12px; }"
        )
        row = QHBoxLayout(self._frame_actions)
        row.setContentsMargins(16, 10, 16, 10)
        row.setSpacing(10)

        self.btn_toggle = QPushButton("Marquer comme terminée")
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.setMinimumHeight(40)
        self.btn_toggle.setStyleSheet(
            "QPushButton { background: white; color: #1976D2; "
            "border: 1.5px solid #1976D2; border-radius: 10px; "
            "font-size: 10pt; font-weight: 600; padding: 8px 16px; }"
            "QPushButton:hover { background: #1976D2; color: white; }"
        )
        self.btn_toggle.clicked.connect(self._basculer_terminee)
        row.addWidget(self.btn_toggle)

        self.btn_modifier = QPushButton("✏️ Modifier")
        self.btn_modifier.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_modifier.setMinimumHeight(40)
        self.btn_modifier.setStyleSheet(
            "QPushButton { background: white; color: #FF9800; "
            "border: 1.5px solid #FF9800; border-radius: 10px; "
            "font-size: 10pt; font-weight: 600; padding: 8px 16px; }"
            "QPushButton:hover { background: #FF9800; color: white; }"
        )
        self.btn_modifier.clicked.connect(self._demander_edition)
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
            "QFrame { background: #E3F2FD; border: 1.5px solid #90CAF9; border-radius: 14px; }"
        )
        lay = QVBoxLayout(self._details_card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        lbl_t = QLabel("Détails")
        lbl_t.setStyleSheet(
            "font-size: 12pt; font-weight: 700; color: #1565C0; "
            "border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)

        self._details_layout = QVBoxLayout()
        self._details_layout.setSpacing(6)
        lay.addLayout(self._details_layout)

        self.layout_contenu.addWidget(self._details_card)

    def _build_sous_taches(self):
        """Section sous-tâches (visible si la tâche est parente)."""
        self._sous_taches_card = QFrame()
        self._sous_taches_card.setStyleSheet(
            "QFrame { background: #F3E5F5; border: 1.5px solid #CE93D8; border-radius: 14px; }"
        )
        lay = QVBoxLayout(self._sous_taches_card)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(8)

        lbl_t = QLabel("Sous-tâches")
        lbl_t.setStyleSheet(
            "font-size: 12pt; font-weight: 700; color: #7B1FA2; "
            "border: none; background: transparent;"
        )
        lay.addWidget(lbl_t)

        self._sous_taches_layout = QVBoxLayout()
        self._sous_taches_layout.setSpacing(4)
        lay.addLayout(self._sous_taches_layout)

        self._sous_taches_card.hide()
        self.layout_contenu.addWidget(self._sous_taches_card)

    def _build_commande_link(self):
        # Section associations (commande + client + vente + produit + code + event)
        self._assoc_card = QFrame()
        self._assoc_card.setStyleSheet(
            "QFrame { background: #FAFAFA; border: 1.5px solid #E0E0E0; border-radius: 14px; }"
        )
        self._assoc_layout = QVBoxLayout(self._assoc_card)
        self._assoc_layout.setContentsMargins(20, 14, 20, 14)
        self._assoc_layout.setSpacing(6)

        lbl_title = QLabel("Associations")
        lbl_title.setStyleSheet(
            "font-size: 12pt; font-weight: bold; color: #333; border: none; background: transparent;"
        )
        self._assoc_layout.addWidget(lbl_title)

        self._assoc_details_layout = QVBoxLayout()
        self._assoc_details_layout.setSpacing(4)
        self._assoc_layout.addLayout(self._assoc_details_layout)

        self._assoc_card.hide()
        self.layout_contenu.addWidget(self._assoc_card)

        # Keep backward compat
        self._commande_card = self._assoc_card
        self._lbl_commande = QLabel()

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    def charger_tache(self, tache_id: int):
        if not self.viewmodel:
            return
        data = self.viewmodel.obtenir_tache(tache_id)
        if not data:
            return

        self._tache_id = tache_id
        terminee = bool(data.get("terminee", False))
        priorite = data.get("priorite", 5)
        prio_color = _PRIORITE_COLORS[max(0, min(priorite - 1, 9))]
        visibilite = data.get("visibilite", "tous")
        validee = bool(data.get("validee_admin", False))

        # Header
        self.label_titre.setText(data.get("titre", "Sans titre"))
        self._lbl_ref.setText(f"TÂCHE \u00b7 #{tache_id}")
        self.label_priorite.setText(f"Priorité {priorite}")
        self._lbl_icon.setText("✅" if terminee else "⬜")

        statut_text = "Terminée" if terminee else "En cours"
        if terminee and validee:
            statut_text = "Terminée ✓ Validée"
        self.label_statut.setText(statut_text)

        date_str = str(data.get("date_echeance") or "")[:10]
        heure = data.get("heure_echeance") or ""
        date_affiche = date_str
        if heure:
            date_affiche += f" à {heure}"
        self.label_date.setText(date_affiche if date_str else "Pas de date")

        # Couleur header selon priorité
        self.header_frame.setStyleSheet(
            "QFrame {"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            f"    stop:0 {prio_color}, stop:1 #1976D2);"
            "  border-radius: 20px;"
            "}"
        )

        # Récurrence badge
        type_rec = data.get("type_recurrence")
        if type_rec:
            label = _RECURRENCE_LABELS.get(type_rec, "🔄")
            if type_rec == "personnalise":
                interval = data.get("intervalle_recurrence", 1)
                label = f"🔄 Tous les {interval} jours"
            self._lbl_recurrence.setText(label)
            self._lbl_recurrence.show()
        else:
            self._lbl_recurrence.hide()

        # Stamp Admin/Mission
        if not self._mode_admin and visibilite == "tous":
            self._lbl_stamp.setText("ADMIN")
            self._lbl_stamp.setStyleSheet(
                "font-size: 10pt; font-weight: 700; color: white; border: none; "
                "background: #1976D2; border-radius: 10px; padding: 3px 12px;"
            )
            self._lbl_stamp.show()
        elif self._mode_admin and visibilite == "tous":
            self._lbl_stamp.setText("MISSION")
            self._lbl_stamp.setStyleSheet(
                "font-size: 10pt; font-weight: 700; color: white; border: none; "
                "background: #FF9800; border-radius: 10px; padding: 3px 12px;"
            )
            self._lbl_stamp.show()
        else:
            self._lbl_stamp.hide()

        # Actions
        self.btn_toggle.setText(
            "Rouvrir la tâche" if terminee else "Marquer comme terminée"
        )
        # Bloquer modification/suppression des tâches admin en mode verrouillé
        peut_modifier = self._mode_admin or visibilite != "tous"
        self.btn_modifier.setVisible(peut_modifier)
        self.btn_supprimer.setVisible(peut_modifier)
        self.btn_toggle.setVisible(peut_modifier)
        self._frame_actions.setVisible(True)

        # Détails
        self._vider_layout(self._details_layout)

        desc = (data.get("description") or "").strip()
        if desc:
            lbl_desc = QLabel(desc)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet(
                "font-size: 10pt; color: #263238; border: none; background: none; padding: 8px;"
            )
            self._details_layout.addWidget(lbl_desc)

        cat_nom = data.get("categorie_nom")
        if cat_nom:
            cat_couleur = data.get("categorie_couleur") or "#2196F3"
            lbl_cat = QLabel(f"Catégorie : {cat_nom}")
            lbl_cat.setStyleSheet(
                f"font-size: 10pt; font-weight: 600; color: {cat_couleur}; "
                f"border: none; background: none; padding: 4px 8px;"
            )
            self._details_layout.addWidget(lbl_cat)

        vis_map = {
            "tous": "Visible par tous",
            "admin_seul": "Administratif uniquement",
            "fonctionnel_seul": "Fonctionnel uniquement",
        }
        lbl_vis = QLabel(f"Visibilité : {vis_map.get(visibilite, visibilite)}")
        lbl_vis.setStyleSheet(
            "font-size: 10pt; color: #546E7A; border: none; background: none; padding: 4px 8px;"
        )
        self._details_layout.addWidget(lbl_vis)

        # Couleur personnalisée
        if data.get("couleur"):
            lbl_couleur = QLabel(f"Couleur : {data['couleur']}")
            lbl_couleur.setStyleSheet(
                f"font-size: 10pt; font-weight: 600; color: {data['couleur']}; "
                f"border: none; background: none; padding: 4px 8px;"
            )
            self._details_layout.addWidget(lbl_couleur)

        # Sous-tâches
        self._vider_layout(self._sous_taches_layout)
        sous_taches = self.viewmodel.lister_sous_taches(tache_id)
        if sous_taches:
            self._sous_taches_card.show()
            for st in sous_taches:
                st_terminee = bool(st.get("terminee", False))
                st_cochee = bool(st.get("cochee", False))
                # Utiliser cochee pour l'état visuel des sous-tâches (checklist)
                is_checked = st_cochee or st_terminee
                check = "✓" if is_checked else "○"
                titre_st = st.get("titre", "")
                desc_st = (st.get("description") or "").strip()
                text = f"{check}  {titre_st}"
                if desc_st:
                    text += f"  —  {desc_st[:50]}"

                lbl_st = QLabel(text)
                style_st = "font-size: 10pt; color: #444; border: none; background: none; padding: 4px 8px;"
                if is_checked:
                    style_st = "font-size: 10pt; color: #999; text-decoration: line-through; border: none; background: none; padding: 4px 8px;"
                lbl_st.setStyleSheet(style_st)
                lbl_st.setCursor(Qt.CursorShape.PointingHandCursor)
                st_id = st.get("id")
                lbl_st.mousePressEvent = lambda e, sid=st_id: self.charger_tache(sid)
                self._sous_taches_layout.addWidget(lbl_st)
        else:
            self._sous_taches_card.hide()

        # Associations
        self._vider_layout(self._assoc_details_layout)
        _assoc_config = [
            ("client_id", "👤 Client", "#5C6BC0", "client"),
            ("vente_id", "🛒 Vente", "#43A047", "vente"),
            ("commande_id", "📦 Commande", "#EF6C00", "commande"),
            ("produit_id", "🏷 Produit", "#7B1FA2", "produit"),
            ("code_promo_id", "🎟 Code Promo", "#00897B", "code_promo"),
            ("evenement_id", "📅 Événement", "#F4511E", "evenement"),
        ]
        has_assoc = False
        for field, label, color, a_type in _assoc_config:
            val = data.get(field)
            if val:
                has_assoc = True
                lbl = QLabel(f"{label} #{val}")
                lbl.setStyleSheet(
                    f"font-size: 10pt; font-weight: 600; color: {color}; "
                    f"border: none; background: transparent; padding: 2px 0;"
                )
                lbl.setCursor(Qt.CursorShape.PointingHandCursor)
                lbl.mousePressEvent = lambda e, t=a_type, i=val: (
                    self.association_navigation.emit(t, i),
                    e.accept(),
                )
                self._assoc_details_layout.addWidget(lbl)

        if has_assoc:
            self._assoc_card.show()
        else:
            self._assoc_card.hide()

    def mettre_a_jour_mode(self, mode_admin: bool):
        self._mode_admin = mode_admin

    def _demander_edition(self):
        if self._tache_id:
            self.edition_demandee.emit(self._tache_id)

    def _basculer_terminee(self):
        if not self._tache_id or not self.viewmodel:
            return
        self.viewmodel.basculer_terminee(self._tache_id)
        self.charger_tache(self._tache_id)

    def _supprimer(self):
        if not self._tache_id or not self.viewmodel:
            return
        rep = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment supprimer cette tâche ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            self.viewmodel.supprimer_tache(self._tache_id)
            self.retour_demande.emit()

    @staticmethod
    def _vider_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                FicheTacheView._vider_layout(item.layout())
