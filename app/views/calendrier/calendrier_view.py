"""Vue pour l'onglet Calendrier style Apple Calendar.

Supporte les vues Mois, Semaine et Jour avec navigation.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QFont, QPainter, QPen, QColor
from datetime import datetime, timedelta
import calendar

from utils.styles import style_bouton, Couleurs
from views.components.modern_segmented_control import ModernSegmentedControl
from models.commande import CommandeModel
from models.tache import TacheModel
from models.evenement import EvenementModel


class _MultiEventDayBtn(QPushButton):
    """Bouton jour avec bordures colorées imbriquées pour événements superposés.

    Chaque événement dessine un rectangle imbriqué (outer → inner).
    Les côtés gauche/droit sont omis là où le span continue.
    """

    def __init__(self, text, event_borders, is_past=False, is_today=False, parent=None):
        """
        event_borders: list of (color, has_prev, has_next) from outer to inner.
        """
        super().__init__(text, parent)
        self._borders = event_borders
        self._is_past = is_past
        self._is_today = is_today
        self.setFlat(True)
        self.setFixedSize(22, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        bw = 1.5  # épaisseur par niveau

        for i, (color, has_prev, has_next) in enumerate(self._borders):
            offset = i * bw
            pen = QPen(QColor(color), bw)
            p.setPen(pen)

            y_top = offset + bw / 2
            y_bot = h - offset - bw / 2
            x_left = offset + bw / 2
            x_right = w - offset - bw / 2

            left_x = 0 if has_prev else x_left
            right_x = w if has_next else x_right

            # Lignes haut et bas
            p.drawLine(QPointF(left_x, y_top), QPointF(right_x, y_top))
            p.drawLine(QPointF(left_x, y_bot), QPointF(right_x, y_bot))

            # Côté gauche (début du span)
            if not has_prev:
                p.drawLine(QPointF(x_left, y_top), QPointF(x_left, y_bot))

            # Côté droit (fin du span)
            if not has_next:
                p.drawLine(QPointF(x_right, y_top), QPointF(x_right, y_bot))

        # Texte du jour
        if self._is_today:
            text_color = QColor("#1976D2")
            font = self.font()
            font.setPointSizeF(8)
            font.setBold(True)
            p.setFont(font)
        else:
            text_color = QColor("#AAA") if self._is_past else QColor("#555")
            font = self.font()
            font.setPointSizeF(8)
            font.setBold(False)
            p.setFont(font)

        p.setPen(text_color)
        p.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, self.text())
        p.end()


class CalendrierView(QWidget):
    """Onglet Calendrier style Apple Calendar."""

    # Signal emis avec (date_debut, date_fin) pour voir les stats
    voir_stats_periode = Signal(str, str)
    tache_selectionnee = Signal(int)  # tache_id — clic sur une tâche
    commande_selectionnee = Signal(int)  # commande_id — clic sur une commande
    evenement_selectionne = Signal(int)  # evenement_id — clic sur un événement

    def __init__(self, parent=None):  # ← parent=None par défaut
        super().__init__(parent)
        self.current_date = datetime.now()
        self._vue_courante = "mois"
        self._mode_admin = True
        self._commande_model = CommandeModel()
        self._tache_model = TacheModel()
        self._evenement_model = EvenementModel()
        # Cache des événements pour la période affichée
        self._events_commandes = {}  # date_str -> [commande, ...]
        self._events_taches = {}  # date_str -> [tache, ...]
        self._events_evenements = {}  # date_str -> [evenement, ...]
        self._construire_ui()

    def mettre_a_jour_mode(self, mode_admin: bool) -> None:
        self._mode_admin = mode_admin
        if hasattr(self, "_btn_nouvel_evenement"):
            self._btn_nouvel_evenement.setVisible(mode_admin)
        if hasattr(self, "_btn_stats"):
            self._btn_stats.setVisible(mode_admin)
        self._rafraichir_vue()

    def _construire_ui(self):
        self.setStyleSheet("background-color: #FFFFFF;")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # === EN-TETE (3 sections: Gauche | Centre | Droite) ===
        header_layout = QHBoxLayout()

        # --- SECTION GAUCHE: Segmented control ---
        self._barre_toggle = ModernSegmentedControl(
            ["Mois", "Semaine", "Jour", "Année"]
        )
        self._barre_toggle.selectionChanged.connect(self._changer_vue_par_index)

        header_layout.addWidget(self._barre_toggle)
        header_layout.addStretch()

        # --- SECTION CENTRE: Navigation ---
        nav_style = (
            "QPushButton {"
            "    background-color: white;"
            "    border: 2px solid #9E9E9E;"
            "    border-radius: 20px;"
            "    font-size: 16pt;"
            "}"
            "QPushButton:hover {"
            "    background-color: #E3F2FD;"
            "}"
        )

        btn_prev = QPushButton("<")
        btn_prev.setFixedSize(40, 40)
        btn_prev.setStyleSheet(nav_style)
        btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_prev.setToolTip("Période précédente")
        btn_prev.clicked.connect(self._precedent)
        header_layout.addWidget(btn_prev)

        self._label_mois = QLabel()
        self._label_mois.setStyleSheet(
            "font-size: 18pt; font-weight: bold; color: #333; margin: 0 20px;"
        )
        self._maj_label_titre()
        header_layout.addWidget(self._label_mois)

        btn_next = QPushButton(">")
        btn_next.setFixedSize(40, 40)
        btn_next.setStyleSheet(nav_style)
        btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_next.setToolTip("Période suivante")
        btn_next.clicked.connect(self._suivant)
        header_layout.addWidget(btn_next)

        header_layout.addStretch()

        # --- SECTION DROITE: Boutons d'action ---
        self._btn_nouvel_evenement = QPushButton("📅 Nouvel événement")
        self._btn_nouvel_evenement.setStyleSheet(
            "QPushButton { background: #FF9800; color: white; "
            "border: none; border-radius: 8px; padding: 8px 14px; "
            "font-size: 10pt; font-weight: 600; }"
            "QPushButton:hover { background: #F57C00; }"
        )
        self._btn_nouvel_evenement.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_nouvel_evenement.clicked.connect(self._creer_evenement_dialog)
        self._btn_nouvel_evenement.setVisible(self._mode_admin)
        header_layout.addWidget(self._btn_nouvel_evenement)

        self._btn_stats = QPushButton("Voir statistiques")
        self._btn_stats.setStyleSheet(style_bouton(Couleurs.SUCCES, taille="petit"))
        self._btn_stats.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_stats.clicked.connect(self._voir_stats_periode)
        self._btn_stats.setVisible(self._mode_admin)
        header_layout.addWidget(self._btn_stats)

        main_layout.addLayout(header_layout)

        # === CALENDRIER ===
        self._calendar_widget = QWidget()
        self._calendar_layout = QVBoxLayout()
        self._calendar_layout.setSpacing(2)
        self._calendar_widget.setLayout(self._calendar_layout)

        main_layout.addWidget(self._calendar_widget)

        self._afficher_vue_mois()

        self.setLayout(main_layout)

    # ------------------------------------------------------------------ #
    #                       Label titre                                   #
    # ------------------------------------------------------------------ #

    _MOIS_FR = [
        "Janvier",
        "Fevrier",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Aout",
        "Septembre",
        "Octobre",
        "Novembre",
        "Decembre",
    ]

    _JOURS_FR = [
        "Lundi",
        "Mardi",
        "Mercredi",
        "Jeudi",
        "Vendredi",
        "Samedi",
        "Dimanche",
    ]

    def _maj_label_titre(self):
        """Met a jour le label du titre selon la vue courante."""
        if self._vue_courante == "mois":
            nom_mois = self._MOIS_FR[self.current_date.month - 1]
            self._label_mois.setText(f"{nom_mois} {self.current_date.year}")
        elif self._vue_courante == "semaine":
            debut_semaine = self.current_date - timedelta(
                days=self.current_date.weekday()
            )
            fin_semaine = debut_semaine + timedelta(days=6)
            self._label_mois.setText(
                f"{debut_semaine.strftime('%d/%m')} - "
                f"{fin_semaine.strftime('%d/%m/%Y')}"
            )
        elif self._vue_courante == "jour":
            jour_nom = self._JOURS_FR[self.current_date.weekday()]
            self._label_mois.setText(
                f"{jour_nom} {self.current_date.strftime('%d/%m/%Y')}"
            )
        elif self._vue_courante == "annee":
            self._label_mois.setText(str(self.current_date.year))

    # ------------------------------------------------------------------ #
    #                       Navigation                                    #
    # ------------------------------------------------------------------ #

    def _aller_aujourdhui(self):
        self.current_date = datetime.now()
        self._maj_label_titre()
        self._rafraichir_vue()

    def _precedent(self):
        """Navigue vers la periode precedente selon la vue."""
        if self._vue_courante == "mois":
            if self.current_date.month == 1:
                self.current_date = self.current_date.replace(
                    year=self.current_date.year - 1, month=12
                )
            else:
                self.current_date = self.current_date.replace(
                    month=self.current_date.month - 1
                )
        elif self._vue_courante == "semaine":
            self.current_date -= timedelta(weeks=1)
        elif self._vue_courante == "jour":
            self.current_date -= timedelta(days=1)
        elif self._vue_courante == "annee":
            self.current_date = self.current_date.replace(
                year=self.current_date.year - 1
            )

        self._maj_label_titre()
        self._rafraichir_vue()

    def _suivant(self):
        """Navigue vers la periode suivante selon la vue."""
        if self._vue_courante == "mois":
            if self.current_date.month == 12:
                self.current_date = self.current_date.replace(
                    year=self.current_date.year + 1, month=1
                )
            else:
                self.current_date = self.current_date.replace(
                    month=self.current_date.month + 1
                )
        elif self._vue_courante == "semaine":
            self.current_date += timedelta(weeks=1)
        elif self._vue_courante == "jour":
            self.current_date += timedelta(days=1)
        elif self._vue_courante == "annee":
            self.current_date = self.current_date.replace(
                year=self.current_date.year + 1
            )

        self._maj_label_titre()
        self._rafraichir_vue()

    _VUES = ["mois", "semaine", "jour", "annee"]

    def _changer_vue_par_index(self, index: int):
        """Appelé par le segmented control lors d'un changement d'onglet."""
        self._changer_vue(self._VUES[index])

    def _changer_vue(self, vue: str):
        index = self._VUES.index(vue)
        if self._barre_toggle.current_index != index:
            self._barre_toggle.select(index)
        self._vue_courante = vue
        self._maj_label_titre()
        self._rafraichir_vue()

    def _voir_stats_periode(self):
        """Emet le signal pour voir les statistiques de la periode affichee."""
        if self._vue_courante == "mois":
            debut = datetime(self.current_date.year, self.current_date.month, 1)
            if self.current_date.month == 12:
                fin = datetime(self.current_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                fin = datetime(
                    self.current_date.year, self.current_date.month + 1, 1
                ) - timedelta(days=1)
        elif self._vue_courante == "semaine":
            debut = self.current_date - timedelta(days=self.current_date.weekday())
            fin = debut + timedelta(days=6)
        elif self._vue_courante == "annee":
            debut = datetime(self.current_date.year, 1, 1)
            fin = datetime(self.current_date.year, 12, 31)
        else:  # jour
            debut = self.current_date
            fin = self.current_date
        self.voir_stats_periode.emit(
            debut.strftime("%Y-%m-%d"), fin.strftime("%Y-%m-%d")
        )

    def _creer_evenement_dialog(self):
        """Ouvre un dialogue de création d'événement calendrier."""
        from PySide6.QtWidgets import (
            QDialog,
            QFormLayout,
            QLineEdit,
            QTextEdit,
            QDateEdit,
            QDialogButtonBox,
            QColorDialog,
            QMessageBox,
        )
        from PySide6.QtCore import QDate

        dlg = QDialog(self)
        dlg.setWindowTitle("Nouvel événement")
        dlg.setMinimumWidth(400)
        form = QFormLayout(dlg)

        input_nom = QLineEdit()
        input_nom.setPlaceholderText("Nom de l'événement")
        form.addRow("Nom :", input_nom)

        input_desc = QTextEdit()
        input_desc.setFixedHeight(60)
        input_desc.setPlaceholderText("Description (optionnel)")
        form.addRow("Description :", input_desc)

        couleur = {"val": "#FF9800"}
        btn_couleur = QPushButton()
        btn_couleur.setFixedSize(36, 36)
        btn_couleur.setToolTip("Choisir une couleur")
        btn_couleur.setStyleSheet(
            f"QPushButton {{ background: {couleur['val']}; "
            f"border: 2px solid #999; border-radius: 6px; }}"
        )

        def choisir_couleur():
            from PySide6.QtGui import QColor

            c = QColorDialog.getColor(QColor(couleur["val"]), dlg, "Couleur")
            if c.isValid():
                couleur["val"] = c.name()
                btn_couleur.setStyleSheet(
                    f"QPushButton {{ background: {c.name()}; "
                    f"border: 2px solid #999; border-radius: 6px; }}"
                )

        btn_couleur.clicked.connect(choisir_couleur)
        form.addRow("Couleur :", btn_couleur)

        date_debut = QDateEdit()
        date_debut.setCalendarPopup(True)
        date_debut.setDate(QDate.currentDate())
        date_debut.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Date début :", date_debut)

        date_fin = QDateEdit()
        date_fin.setCalendarPopup(True)
        date_fin.setDate(QDate.currentDate())
        date_fin.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Date fin :", date_fin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            nom = input_nom.text().strip()
            if not nom:
                QMessageBox.warning(self, "Attention", "Le nom est obligatoire.")
                return
            d1 = date_debut.date().toString("yyyy-MM-dd")
            d2 = date_fin.date().toString("yyyy-MM-dd")
            desc = input_desc.toPlainText().strip()
            self._evenement_model.creer_evenement(
                nom=nom,
                description=desc,
                couleur=couleur["val"],
                date_debut=d1,
                date_fin=d2,
            )
            self._rafraichir_vue()

    def _rafraichir_vue(self):
        """Rafraichit la vue courante."""
        self._charger_evenements()
        if self._vue_courante == "mois":
            self._afficher_vue_mois()
        elif self._vue_courante == "semaine":
            self._afficher_vue_semaine()
        elif self._vue_courante == "jour":
            self._afficher_vue_jour()
        elif self._vue_courante == "annee":
            self._afficher_vue_annee()

    def _charger_evenements(self):
        """Charge les commandes et tâches pour la période affichée."""
        if self._vue_courante == "mois":
            debut = f"{self.current_date.year}-{self.current_date.month:02d}-01"
            if self.current_date.month == 12:
                fin = f"{self.current_date.year + 1}-01-01"
            else:
                fin = f"{self.current_date.year}-{self.current_date.month + 1:02d}-01"
        elif self._vue_courante == "semaine":
            d = self.current_date - timedelta(days=self.current_date.weekday())
            debut = d.strftime("%Y-%m-%d")
            fin = (d + timedelta(days=7)).strftime("%Y-%m-%d")
        elif self._vue_courante == "jour":
            debut = self.current_date.strftime("%Y-%m-%d")
            fin = (self.current_date + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            debut = f"{self.current_date.year}-01-01"
            fin = f"{self.current_date.year + 1}-01-01"

        # Charger commandes
        self._events_commandes = {}
        try:
            commandes = self._commande_model.obtenir_commandes_par_date(debut, fin)
            for cmd in commandes:
                date_key = str(cmd.get("date_prevue", ""))[:10]
                self._events_commandes.setdefault(date_key, []).append(cmd)
        except Exception:
            pass

        # Charger tâches (filtrer par visibilité)
        self._events_taches = {}
        try:
            if self._mode_admin:
                vis = ["tous", "admin_seul", "fonctionnel_seul"]
            else:
                vis = ["tous", "fonctionnel_seul"]
            taches = self._tache_model.obtenir_taches_par_date(debut, fin)
            for t in taches:
                if t.get("visibilite", "tous") in vis:
                    date_key = str(t.get("date_echeance", ""))[:10]
                    self._events_taches.setdefault(date_key, []).append(t)
        except Exception:
            pass

        # Charger événements calendrier
        self._events_evenements = {}
        try:
            evenements = self._evenement_model.lister_evenements(debut, fin)
            for ev in evenements:
                # Un événement couvre une plage de dates
                d_debut = ev.get("date_debut", "")[:10]
                d_fin = ev.get("date_fin", "")[:10]
                from datetime import date as dt_date

                try:
                    d1 = dt_date.fromisoformat(d_debut)
                    d2 = dt_date.fromisoformat(d_fin)
                    current = d1
                    while current <= d2:
                        key = current.isoformat()
                        self._events_evenements.setdefault(key, []).append(ev)
                        current += timedelta(days=1)
                except (ValueError, TypeError):
                    pass
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #                       Vue Mois                                      #
    # ------------------------------------------------------------------ #

    def _afficher_vue_mois(self):
        """Affiche la vue mois — grille compacte du 1er au dernier jour, 7 colonnes.

        Les lignes complètes (7 jours) s'étirent pour occuper toute la largeur.
        La dernière ligne incomplète conserve la même taille de cellule que les
        lignes complètes (pas d'étirement).
        """
        if not self._events_commandes and not self._events_taches:
            self._charger_evenements()
        self._vider_layout(self._calendar_layout)

        import calendar as cal_mod

        nb_jours = cal_mod.monthrange(self.current_date.year, self.current_date.month)[
            1
        ]

        days = list(range(1, nb_jours + 1))
        # Découper en semaines
        rows: list[list[int]] = []
        for i in range(0, len(days), 7):
            rows.append(days[i : i + 7])

        for row_days in rows:
            week_layout = QHBoxLayout()
            week_layout.setSpacing(2)
            is_full_row = len(row_days) == 7
            for day in row_days:
                day_widget = self._creer_cellule_jour(day)
                if is_full_row:
                    # Lignes complètes : stretch=1 pour remplir toute la largeur
                    week_layout.addWidget(day_widget, stretch=1)
                else:
                    # Dernière ligne incomplète : stretch=1 aussi pour même taille
                    week_layout.addWidget(day_widget, stretch=1)
            if not is_full_row:
                # Ajouter des spacers invisibles pour les jours manquants
                missing = 7 - len(row_days)
                for _ in range(missing):
                    spacer = QWidget()
                    spacer.setStyleSheet("background: transparent; border: none;")
                    week_layout.addWidget(spacer, stretch=1)
            self._calendar_layout.addLayout(week_layout)

        self._calendar_layout.addStretch()

    def _creer_cellule_jour(self, day: int) -> QFrame:
        """Crée une cellule de jour avec ovales événements adaptatifs."""
        cell = QFrame()
        cell.setFrameShape(QFrame.Shape.Box)
        cell.setMinimumHeight(110)

        now = datetime.now()
        is_today = (
            day == now.day
            and self.current_date.month == now.month
            and self.current_date.year == now.year
        )
        cell_date = datetime(self.current_date.year, self.current_date.month, day)
        is_past = cell_date.date() < now.date()

        if is_today:
            cell.setStyleSheet(
                "QFrame { background-color: #E3F2FD; border: 3px solid #2196F3; border-radius: 8px; }"
            )
        elif is_past:
            cell.setStyleSheet(
                "QFrame { background-color: #FAFAFA; border: 1.5px solid #E0E0E0; border-radius: 8px; }"
            )
        else:
            cell.setStyleSheet(
                "QFrame { background-color: white; border: 1.5px solid #E0E0E0; border-radius: 8px; }"
                "QFrame:hover { background-color: #F5F5F5; }"
            )

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- En-tête du jour : numéro + événements à côté (alignés à gauche) ---
        header_row = QHBoxLayout()
        header_row.setSpacing(4)
        header_row.setContentsMargins(0, 0, 0, 0)

        day_label = QLabel(str(day))
        day_label.setFixedWidth(30)
        if is_today:
            color = "#2196F3"
        elif is_past:
            color = "rgba(100, 100, 100, 0.5)"
        else:
            color = "#333"
        day_label.setStyleSheet(
            f"font-size: 13pt; font-weight: bold; color: {color}; "
            f"padding: 2px 4px; border: none; background: transparent;"
        )
        header_row.addWidget(day_label)

        date_key = f"{self.current_date.year}-{self.current_date.month:02d}-{day:02d}"

        # --- Ovales événements à côté du numéro ---
        evenements_jour = self._events_evenements.get(date_key, [])
        if evenements_jour:
            nb_ev = min(len(evenements_jour), 3)
            for ev in evenements_jour[:nb_ev]:
                ev_color = ev.get("couleur", "#FF9800")
                ev_nom = ev.get("nom", "")
                max_chars = {1: 12, 2: 6, 3: 4}.get(nb_ev, 4)
                display_name = (
                    ev_nom[:max_chars] + "…" if len(ev_nom) > max_chars else ev_nom
                )
                pill = QLabel(display_name)
                pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
                pill.setStyleSheet(
                    f"font-size: 7pt; font-weight: 600; color: white; "
                    f"background: {ev_color}; border-radius: 7px; "
                    f"padding: 1px 4px; border: none;"
                )
                pill.setCursor(Qt.CursorShape.PointingHandCursor)
                pill.setToolTip(ev_nom)
                ev_id = ev.get("id")
                pill.mousePressEvent = lambda e, eid=ev_id: (
                    self.evenement_selectionne.emit(eid),
                    e.accept(),
                )
                header_row.addWidget(pill)

        header_row.addStretch()
        layout.addLayout(header_row)

        # --- Trait de séparation toujours présent ---
        commandes_jour = self._events_commandes.get(date_key, [])
        taches_jour = self._events_taches.get(date_key, [])
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #D0D0D0; border: none;")
        layout.addWidget(sep)

        # --- Commandes ---
        for cmd in commandes_jour[:2]:
            nom = cmd.get("client_nom", "")
            statut = cmd.get("statut", "en_attente")
            s_colors = {
                "en_attente": "#FF9800",
                "en_cours": "#2196F3",
                "terminee": "#4CAF50",
                "annulee": "#9E9E9E",
            }
            badge_color = s_colors.get(statut, "#FF9800")
            lbl = QLabel(f"{nom[:12]}")
            lbl.setStyleSheet(
                f"font-size: 7pt; color: white; background: {badge_color}; "
                f"border-radius: 4px; padding: 1px 3px; border: none;"
            )
            lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            cmd_id = cmd.get("id")
            lbl.mousePressEvent = lambda e, cid=cmd_id: (
                self.commande_selectionnee.emit(cid),
                e.accept(),
            )
            layout.addWidget(lbl)

        # --- Tâches (grisées si terminées) ---
        for t in taches_jour[:2]:
            is_st = bool(t.get("parent_id"))
            prefix = "↳ " if is_st else ""
            titre = t.get("titre", "")[: 13 if is_st else 15]
            terminee = t.get("terminee", False)
            cochee = t.get("cochee", False)
            is_done = terminee or (is_st and cochee)

            if is_done:
                # Tâche terminée : grisée pour ne pas empiéter sur l'affichage
                lbl = QLabel(f"{prefix}{titre}")
                lbl.setStyleSheet(
                    "font-size: 7pt; color: #AAA; background: #EEEEEE; "
                    "border-radius: 4px; padding: 1px 3px; border: none; "
                    "text-decoration: line-through;"
                )
            else:
                p_color = self._couleur_tache(t)
                font_size = "7pt" if is_st else "7pt"
                lbl = QLabel(f"{prefix}{titre}")
                lbl.setStyleSheet(
                    f"font-size: {font_size}; color: white; background: {p_color}; "
                    f"border-radius: 4px; padding: 1px 3px; border: none;"
                )
            lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            t_id = t.get("id")
            lbl.mousePressEvent = lambda e, tid=t_id: (
                self.tache_selectionnee.emit(tid),
                e.accept(),
            )
            layout.addWidget(lbl)

        # Indicateur "+N" si plus d'événements
        total = len(commandes_jour) + len(taches_jour) + len(evenements_jour)
        shown = (
            min(len(evenements_jour), 3)
            + min(len(commandes_jour), 2)
            + min(len(taches_jour), 2)
        )
        if total > shown:
            lbl_more = QLabel(f"+{total - shown}")
            lbl_more.setStyleSheet(
                "font-size: 7pt; color: #999; border: none; padding: 0 3px;"
            )
            layout.addWidget(lbl_more)

        layout.addStretch()
        cell.setLayout(layout)

        cell.mousePressEvent = lambda e, d=day: self._on_jour_clique(d)
        cell.setCursor(Qt.CursorShape.PointingHandCursor)

        return cell

    def _on_jour_clique(self, day: int):
        """Clic sur un jour : passe en vue Jour."""
        self.current_date = datetime(
            self.current_date.year, self.current_date.month, day
        )
        self._changer_vue("jour")

    # ------------------------------------------------------------------ #
    #                       Utilitaire couleur tâche                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _couleur_tache(t: dict) -> str:
        """Retourne la couleur d'affichage d'une tâche : perso > catégorie > priorité."""
        if t.get("couleur"):
            return t["couleur"]
        if t.get("categorie_couleur"):
            return t["categorie_couleur"]
        prio_colors = [
            "#0D47A1",
            "#1565C0",
            "#1976D2",
            "#1E88E5",
            "#2196F3",
            "#42A5F5",
            "#64B5F6",
            "#90CAF9",
            "#BBDEFB",
            "#E3F2FD",
        ]
        priorite = t.get("priorite", 5)
        return prio_colors[max(0, min(priorite - 1, 9))]

    # ------------------------------------------------------------------ #
    #                       Vue Semaine                                   #
    # ------------------------------------------------------------------ #

    def _afficher_vue_semaine(self):
        """Affiche la vue semaine avec grille horaire et événements."""
        self._vider_layout(self._calendar_layout)

        debut_semaine = self.current_date - timedelta(days=self.current_date.weekday())

        # En-têtes des jours
        header_layout = QHBoxLayout()
        header_layout.setSpacing(2)

        heure_header = QLabel("Heure")
        heure_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heure_header.setStyleSheet(
            "font-weight: bold; color: #666; padding: 10px; font-size: 10pt;"
        )
        heure_header.setFixedWidth(80)
        header_layout.addWidget(heure_header)

        for i in range(7):
            day_date = debut_semaine + timedelta(days=i)
            is_today = day_date.date() == datetime.now().date()
            label = QLabel(f"{self._JOURS_FR[i][:3]}\n{day_date.strftime('%d/%m')}")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if is_today:
                label.setStyleSheet(
                    "QLabel { font-weight: bold; color: white; padding: 10px;"
                    " background-color: #2196F3; border-radius: 8px; }"
                )
            else:
                label.setStyleSheet(
                    "QLabel { font-weight: bold; color: #2196F3; padding: 10px;"
                    " background-color: #E3F2FD; border-radius: 8px; }"
                )
            header_layout.addWidget(label, 1)

        self._calendar_layout.addLayout(header_layout)

        # Scroll pour grille horaire
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(2)

        # Row 0 : Journée entière (all-day)
        allday_label = QLabel("Journée")
        allday_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        )
        allday_label.setStyleSheet(
            "font-weight: 600; color: #999; font-size: 9pt; padding-right: 10px;"
        )
        allday_label.setFixedWidth(80)
        grid_layout.addWidget(allday_label, 0, 0)

        for day_idx in range(7):
            day_date = debut_semaine + timedelta(days=day_idx)
            date_key = day_date.strftime("%Y-%m-%d")
            allday_events = self._get_allday_events(date_key)
            # Ajouter les événements calendrier dans la zone journée entière
            evs = self._events_evenements.get(date_key, [])
            for ev in evs:
                allday_events.insert(0, {"type": "evenement", "data": ev})
            cell = self._creer_cellule_events(
                day_date, -1, allday_events, is_allday=True
            )
            grid_layout.addWidget(cell, 0, day_idx + 1)

        # Rows 1-24 : heures 0-23
        for row, hour in enumerate(range(0, 24), start=1):
            hour_label = QLabel(f"{hour:02d}:00")
            hour_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
            )
            hour_label.setStyleSheet(
                "font-weight: 600; color: #666; padding-right: 10px;"
            )
            hour_label.setFixedWidth(80)
            grid_layout.addWidget(hour_label, row, 0)

            for day_idx in range(7):
                day_date = debut_semaine + timedelta(days=day_idx)
                date_key = day_date.strftime("%Y-%m-%d")
                hour_events = self._get_hour_events(date_key, hour)
                cell = self._creer_cellule_events(day_date, hour, hour_events)
                grid_layout.addWidget(cell, row, day_idx + 1)

        grid_widget.setLayout(grid_layout)
        scroll.setWidget(grid_widget)
        self._calendar_layout.addWidget(scroll)

    def _get_allday_events(self, date_key: str) -> list[dict]:
        """Récupère les événements sans heure pour un jour donné."""
        events = []
        for cmd in self._events_commandes.get(date_key, []):
            if not cmd.get("heure_prevue"):
                events.append({"type": "commande", "data": cmd})
        for t in self._events_taches.get(date_key, []):
            if not t.get("heure_echeance"):
                events.append({"type": "tache", "data": t})
        return events

    def _get_hour_events(self, date_key: str, hour: int) -> list[dict]:
        """Récupère les événements pour une heure spécifique."""
        events = []
        hour_str = f"{hour:02d}"
        for cmd in self._events_commandes.get(date_key, []):
            h = cmd.get("heure_prevue") or ""
            if h.startswith(hour_str):
                events.append({"type": "commande", "data": cmd})
        for t in self._events_taches.get(date_key, []):
            h = t.get("heure_echeance") or ""
            if h.startswith(hour_str):
                events.append({"type": "tache", "data": t})
        return events

    def _creer_cellule_events(
        self, date_obj: datetime, hour: int, events: list[dict], is_allday: bool = False
    ) -> QFrame:
        """Crée une cellule horaire avec les événements affichés."""
        cell = QFrame()
        cell.setFrameShape(QFrame.Shape.Box)
        cell.setMinimumHeight(40 if is_allday else 50)
        cell.setMinimumWidth(100)

        is_now = (
            not is_allday
            and date_obj.date() == datetime.now().date()
            and hour == datetime.now().hour
        )

        if is_allday:
            cell.setStyleSheet(
                "QFrame { background-color: #FAFAFA; border: 1px solid #E0E0E0; }"
            )
        elif is_now:
            cell.setStyleSheet(
                "QFrame { background-color: #E3F2FD; border: 2px solid #2196F3; }"
            )
        else:
            cell.setStyleSheet(
                "QFrame { background-color: white; border: 1px solid #D0D0D0; }"
                "QFrame:hover { background-color: #F5F5F5; }"
            )

        lay = QVBoxLayout(cell)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(1)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        for ev in events[:3]:
            if ev["type"] == "evenement":
                data = ev["data"]
                ev_color = data.get("couleur", "#FF9800")
                ev_nom = data.get("nom", "")
                lbl = QLabel(f"📅 {ev_nom}")
                lbl.setWordWrap(True)
                lbl.setStyleSheet(
                    f"font-size: 7pt; font-weight: 600; color: white; background: {ev_color}; "
                    f"border-radius: 3px; padding: 2px 4px; border: none;"
                )
                lbl.setCursor(Qt.CursorShape.PointingHandCursor)
                lbl.setToolTip(ev_nom)
                ev_id = data.get("id")
                lbl.mousePressEvent = lambda e, eid=ev_id: (
                    self.evenement_selectionne.emit(eid),
                    e.accept(),
                )
                lay.addWidget(lbl)
            elif ev["type"] == "commande":
                cmd = ev["data"]
                nom = cmd.get("client_nom", "")
                s_colors = {
                    "en_attente": "#FF9800",
                    "en_cours": "#2196F3",
                    "terminee": "#4CAF50",
                    "annulee": "#9E9E9E",
                }
                badge_color = s_colors.get(cmd.get("statut", ""), "#FF9800")
                lbl = QLabel(f"🛒 {nom}")
                lbl.setWordWrap(True)
                lbl.setStyleSheet(
                    f"font-size: 7pt; color: white; background: {badge_color}; "
                    f"border-radius: 3px; padding: 2px 4px; border: none;"
                )
                lbl.setCursor(Qt.CursorShape.PointingHandCursor)
                lbl.setToolTip(nom)
                cmd_id = cmd.get("id")
                lbl.mousePressEvent = lambda e, cid=cmd_id: (
                    self.commande_selectionnee.emit(cid),
                    e.accept(),
                )
                lay.addWidget(lbl)
            else:
                t = ev["data"]
                titre = t.get("titre", "")
                color = self._couleur_tache(t)
                terminee = t.get("terminee", False)
                style_t = "text-decoration: line-through;" if terminee else ""
                lbl = QLabel(f"✅ {titre}")
                lbl.setWordWrap(True)
                lbl.setStyleSheet(
                    f"font-size: 7pt; color: white; background: {color}; "
                    f"border-radius: 3px; padding: 2px 4px; border: none; {style_t}"
                )
                lbl.setCursor(Qt.CursorShape.PointingHandCursor)
                lbl.setToolTip(titre)
                t_id = t.get("id")
                lbl.mousePressEvent = lambda e, tid=t_id: (
                    self.tache_selectionnee.emit(tid),
                    e.accept(),
                )
                lay.addWidget(lbl)

        if len(events) > 3:
            lbl_more = QLabel(f"+{len(events) - 3}")
            lbl_more.setStyleSheet("font-size: 6pt; color: #999; border: none;")
            lay.addWidget(lbl_more)

        cell.mousePressEvent = lambda e, d=date_obj, h=hour: self._on_clic_heure(d, h)
        cell.setCursor(Qt.CursorShape.PointingHandCursor)

        return cell

    def _on_clic_heure(self, date_obj: datetime, hour: int):
        """Gere le clic sur une cellule horaire."""
        self.current_date = date_obj
        self._changer_vue("jour")

    # ------------------------------------------------------------------ #
    #                       Vue Jour                                      #
    # ------------------------------------------------------------------ #

    def _afficher_vue_jour(self):
        """Affiche la vue jour avec timeline horaire 0h-23h et événements."""
        self._vider_layout(self._calendar_layout)

        jour_nom = self._JOURS_FR[self.current_date.weekday()]

        # Header jour + badges événements
        header_widget = QWidget()
        header_widget.setStyleSheet(
            "QWidget { background-color: #E3F2FD; border-radius: 10px; }"
        )
        header_lay = QHBoxLayout(header_widget)
        header_lay.setContentsMargins(15, 10, 15, 10)

        date_key_header = self.current_date.strftime("%Y-%m-%d")
        evs_jour = self._events_evenements.get(date_key_header, [])

        # Texte header avec ":" si il y a des events
        header_text = f"{jour_nom} {self.current_date.strftime('%d/%m/%Y')}"
        if evs_jour:
            header_text += " :"
        header = QLabel(header_text)
        header.setStyleSheet(
            "font-size: 18pt; font-weight: bold; color: #2196F3; "
            "background: none; border: none;"
        )
        header_lay.addStretch()
        header_lay.addWidget(header)

        # Ovales événements après le header
        for ev in evs_jour[:5]:
            ev_color = ev.get("couleur", "#FF9800")
            ev_nom = ev.get("nom", "")
            max_chars = {1: 20, 2: 12, 3: 8}.get(min(len(evs_jour), 3), 8)
            display = ev_nom[:max_chars] + "…" if len(ev_nom) > max_chars else ev_nom
            pill = QLabel(display)
            pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pill.setStyleSheet(
                f"font-size: 9pt; font-weight: 600; color: white; "
                f"background: {ev_color}; border-radius: 10px; "
                f"padding: 3px 10px; border: none;"
            )
            pill.setCursor(Qt.CursorShape.PointingHandCursor)
            pill.setToolTip(ev_nom)
            ev_id = ev.get("id")
            pill.mousePressEvent = lambda e, eid=ev_id: (
                self.evenement_selectionne.emit(eid),
                e.accept(),
            )
            header_lay.addWidget(pill, alignment=Qt.AlignmentFlag.AlignVCenter)

        header_lay.addStretch()
        self._calendar_layout.addWidget(header_widget)

        date_key = self.current_date.strftime("%Y-%m-%d")

        # Section "Journée entière" pour les événements sans heure
        allday_events = self._get_allday_events(date_key)
        if allday_events:
            allday_frame = QFrame()
            allday_frame.setStyleSheet(
                "QFrame { background-color: #FFF8E1; border: 1.5px solid #FFE082;"
                " border-radius: 8px; }"
            )
            allday_lay = QVBoxLayout(allday_frame)
            allday_lay.setContentsMargins(12, 8, 12, 8)
            allday_lay.setSpacing(4)

            lbl_allday = QLabel("Journée entière")
            lbl_allday.setStyleSheet(
                "font-size: 10pt; font-weight: 600; color: #F57F17; border: none;"
            )
            allday_lay.addWidget(lbl_allday)

            for ev in allday_events:
                lbl = self._creer_badge_event(ev)
                allday_lay.addWidget(lbl)

            self._calendar_layout.addWidget(allday_frame)

        # ScrollArea pour la timeline
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        timeline_widget = QWidget()
        timeline_layout = QVBoxLayout()
        timeline_layout.setSpacing(0)

        for hour in range(24):
            hour_events = self._get_hour_events(date_key, hour)

            hour_frame = QFrame()
            hour_frame.setFrameShape(QFrame.Shape.Box)
            hour_frame.setMinimumHeight(80)

            is_current_hour = (
                self.current_date.date() == datetime.now().date()
                and hour == datetime.now().hour
            )

            if is_current_hour:
                hour_frame.setStyleSheet(
                    "QFrame { background-color: #E3F2FD;"
                    " border: 2px solid #2196F3; border-radius: 5px; }"
                )
            else:
                hour_frame.setStyleSheet(
                    "QFrame { background-color: white;"
                    " border: 1px solid #D0D0D0; border-radius: 5px; }"
                    "QFrame:hover { background-color: #F9F9F9; }"
                )

            hour_layout = QHBoxLayout()

            hour_label = QLabel(f"{hour:02d}:00")
            hour_label.setAlignment(Qt.AlignmentFlag.AlignTop)
            hour_label.setStyleSheet(
                "QLabel { font-size: 14pt; font-weight: bold; color: #666;"
                " padding: 10px; min-width: 80px; }"
            )
            hour_layout.addWidget(hour_label)

            events_widget = QWidget()
            events_layout = QVBoxLayout()
            events_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            events_layout.setContentsMargins(0, 4, 0, 4)
            events_layout.setSpacing(3)

            for ev in hour_events:
                lbl = self._creer_badge_event(ev)
                events_layout.addWidget(lbl)

            events_widget.setLayout(events_layout)
            hour_layout.addWidget(events_widget, 1)

            hour_frame.setLayout(hour_layout)
            hour_frame.setCursor(Qt.CursorShape.PointingHandCursor)

            timeline_layout.addWidget(hour_frame)

        timeline_widget.setLayout(timeline_layout)
        scroll.setWidget(timeline_widget)

        self._calendar_layout.addWidget(scroll)

        # Garder une référence forte pour éviter le GC avant le timer
        self._scroll_jour = scroll

        # Scroller vers l'heure actuelle
        if self.current_date.date() == datetime.now().date():
            current_hour = datetime.now().hour
            from PySide6.QtCore import QTimer

            def _scroll_to_hour():
                try:
                    s = self._scroll_jour
                    if s and s.verticalScrollBar():
                        s.verticalScrollBar().setValue(current_hour * 80)
                except RuntimeError:
                    pass  # Widget déjà supprimé

            QTimer.singleShot(100, _scroll_to_hour)

    def _creer_badge_event(self, ev: dict) -> QLabel:
        """Crée un label badge pour un événement (commande, tâche ou événement calendrier)."""
        if ev["type"] == "evenement":
            data = ev["data"]
            ev_color = data.get("couleur", "#FF9800")
            ev_nom = data.get("nom", "")
            lbl = QLabel(f"📅 {ev_nom}")
            lbl.setStyleSheet(
                f"font-size: 10pt; font-weight: 600; color: white; background: {ev_color}; "
                f"border-radius: 8px; padding: 4px 10px; border: none;"
            )
            lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            ev_id = data.get("id")
            lbl.mousePressEvent = lambda e, eid=ev_id: (
                self.evenement_selectionne.emit(eid),
                e.accept(),
            )
        elif ev["type"] == "commande":
            cmd = ev["data"]
            nom = cmd.get("client_nom", "")
            statut = cmd.get("statut", "en_attente")
            s_colors = {
                "en_attente": "#FF9800",
                "en_cours": "#2196F3",
                "terminee": "#4CAF50",
                "annulee": "#9E9E9E",
            }
            badge_color = s_colors.get(statut, "#FF9800")
            text = f"🛒 {nom}"
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"font-size: 10pt; color: white; background: {badge_color}; "
                f"border-radius: 6px; padding: 4px 10px; border: none;"
            )
            lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            cmd_id = cmd.get("id")
            lbl.mousePressEvent = lambda e, cid=cmd_id: (
                self.commande_selectionnee.emit(cid),
                e.accept(),
            )
        else:
            t = ev["data"]
            titre = t.get("titre", "")
            terminee = t.get("terminee", False)
            heure = t.get("heure_echeance") or ""
            prefix = f"{heure} " if heure else ""
            if terminee:
                # Tâche terminée : grisée
                lbl = QLabel(f"✅ {prefix}{titre}")
                lbl.setStyleSheet(
                    "font-size: 10pt; color: #AAA; background: #EEEEEE; "
                    "border-radius: 6px; padding: 4px 10px; border: none; "
                    "text-decoration: line-through;"
                )
            else:
                color = self._couleur_tache(t)
                lbl = QLabel(f"✅ {prefix}{titre}")
                lbl.setStyleSheet(
                    f"font-size: 10pt; color: white; background: {color}; "
                    f"border-radius: 6px; padding: 4px 10px; border: none;"
                )
            lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            t_id = t.get("id")
            lbl.mousePressEvent = lambda e, tid=t_id: (
                self.tache_selectionnee.emit(tid),
                e.accept(),
            )
        return lbl

    # ------------------------------------------------------------------ #
    #                       Vue Année                                     #
    # ------------------------------------------------------------------ #

    def _afficher_vue_annee(self):
        """Affiche la vue année : grille 4×3 (4 colonnes, 3 rangées), sans scroll."""
        self._vider_layout(self._calendar_layout)
        if not self._events_evenements:
            self._charger_evenements()

        grid_container = QWidget()
        grid = QGridLayout(grid_container)
        grid.setSpacing(10)
        grid.setContentsMargins(8, 8, 8, 8)

        for mois_idx in range(1, 13):
            mini_cal = self._creer_mini_calendrier(self.current_date.year, mois_idx)
            row = (mois_idx - 1) // 4  # 4 colonnes → 3 rangées
            col = (mois_idx - 1) % 4
            grid.addWidget(mini_cal, row, col)

        self._calendar_layout.addWidget(grid_container)

    def _creer_mini_calendrier(self, annee: int, mois: int) -> QWidget:
        """Crée un mini calendrier compact pour la vue année.

        - Clic sur le titre → vue mois.
        - Clic sur un numéro de jour → vue jour.
        - Jours avec événement : contour coloré (span connecté).
        - Superposition : border-top=couleur1, border-bottom=couleur2, pas de coin arrondi.
        """
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet(
            "QFrame { background-color: white; border: 1px solid #E0E0E0; border-radius: 8px; }"
        )

        layout = QVBoxLayout(frame)
        layout.setSpacing(1)
        layout.setContentsMargins(5, 4, 5, 4)

        # Titre du mois → cliquable pour naviguer vers ce mois
        titre_btn = QPushButton(self._MOIS_FR[mois - 1])
        titre_btn.setFlat(True)
        titre_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        titre_btn.setStyleSheet(
            "QPushButton { font-size: 10pt; font-weight: bold; color: #1976D2; "
            "background: transparent; border: none; padding: 0; text-align: center; }"
            "QPushButton:hover { color: #1565C0; }"
        )
        titre_btn.clicked.connect(
            lambda checked=False, m=mois: self._on_mini_calendrier_clic(m)
        )
        layout.addWidget(titre_btn)

        # En-têtes jours (L M M J V S D)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(0)
        header_layout.setContentsMargins(0, 0, 0, 0)
        for jour in ["L", "M", "M", "J", "V", "S", "D"]:
            lbl = QLabel(jour)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedSize(22, 14)
            lbl.setStyleSheet(
                "font-size: 7pt; font-weight: 600; color: #AAAAAA; border: none; background: transparent;"
            )
            header_layout.addWidget(lbl, 1)
        layout.addLayout(header_layout)

        # Grille des jours
        cal = calendar.monthcalendar(annee, mois)
        while len(cal) < 6:
            cal.append([0] * 7)
        now = datetime.now()

        for week in cal:
            week_layout = QHBoxLayout()
            week_layout.setSpacing(0)
            week_layout.setContentsMargins(0, 0, 0, 0)

            for pos, day in enumerate(week):
                if day == 0:
                    empty = QLabel("")
                    empty.setFixedSize(22, 22)
                    empty.setStyleSheet("border: none; background: transparent;")
                    week_layout.addWidget(empty, 1)
                else:
                    is_today = (
                        day == now.day and mois == now.month and annee == now.year
                    )
                    is_past = datetime(annee, mois, day).date() < now.date()
                    date_key = f"{annee}-{mois:02d}-{day:02d}"
                    evts = self._events_evenements.get(date_key, [])

                    n_evts = len(evts)

                    if n_evts >= 2:
                        # Multi-événements → widget custom avec bordures imbriquées
                        event_borders = []
                        for ev in evts[:4]:
                            hp, hn = self._check_span_continuity(
                                pos, week, ev.get("id"), annee, mois
                            )
                            event_borders.append((ev.get("couleur", "#FF9800"), hp, hn))
                        day_btn = _MultiEventDayBtn(
                            str(day), event_borders, is_past=is_past, is_today=is_today
                        )
                    else:
                        day_btn = QPushButton(str(day))
                        day_btn.setFlat(True)
                        day_btn.setFixedSize(22, 22)
                        day_btn.setCursor(Qt.CursorShape.PointingHandCursor)

                        if is_today and n_evts == 1:
                            # Aujourd'hui + 1 event → bordure event + texte bleu gras
                            css = self._calc_span_style(
                                day, pos, week, date_key, evts, annee, mois, is_past
                            )
                            css = css.replace(
                                "color: #555", "color: #1976D2; font-weight: bold"
                            ).replace(
                                "color: #AAA", "color: #1976D2; font-weight: bold"
                            )
                            day_btn.setStyleSheet(css)
                        elif is_today:
                            # Aujourd'hui sans event → anneau bleu discret
                            day_btn.setStyleSheet(
                                "QPushButton { background: transparent; color: #1976D2; "
                                "border: 1.5px solid #42A5F5; border-radius: 11px; "
                                "font-size: 8pt; font-weight: bold; }"
                            )
                        elif n_evts == 1:
                            day_btn.setStyleSheet(
                                self._calc_span_style(
                                    day, pos, week, date_key, evts, annee, mois, is_past
                                )
                            )
                        elif is_past:
                            day_btn.setStyleSheet(
                                "QPushButton { color: #CCCCCC; font-size: 8pt; border: none; "
                                "background: transparent; padding: 0; }"
                            )
                        else:
                            day_btn.setStyleSheet(
                                "QPushButton { color: #333; font-size: 8pt; border: none; "
                                "background: transparent; padding: 0; }"
                            )

                    # Clic → naviguer vers ce jour
                    day_btn.clicked.connect(
                        lambda checked=False, a=annee, m=mois, d=day: self._naviguer_vers_jour(
                            a, m, d
                        )
                    )
                    week_layout.addWidget(day_btn, 1)

            layout.addLayout(week_layout)

        return frame

    def _naviguer_vers_jour(self, annee: int, mois: int, jour: int):
        """Navigue vers la vue jour pour une date précise."""
        self.current_date = datetime(annee, mois, jour)
        self._changer_vue("jour")

    def _check_span_continuity(self, pos, week, ev_id, annee, mois):
        """Retourne (has_prev, has_next) pour un événement dans la rangée."""
        has_prev = False
        has_next = False
        if pos > 0 and week[pos - 1] != 0:
            prev_key = f"{annee}-{mois:02d}-{week[pos - 1]:02d}"
            has_prev = any(
                pe.get("id") == ev_id
                for pe in self._events_evenements.get(prev_key, [])
            )
        if pos < 6 and week[pos + 1] != 0:
            next_key = f"{annee}-{mois:02d}-{week[pos + 1]:02d}"
            has_next = any(
                ne.get("id") == ev_id
                for ne in self._events_evenements.get(next_key, [])
            )
        return has_prev, has_next

    def _calc_span_style(
        self, day, pos, week, date_key, evts, annee, mois, is_past
    ) -> str:
        """Retourne le CSS QPushButton pour un jour avec événement(s).

        1 événement : contour simple avec coins arrondis aux extrémités du span.
        2+ événements : border-top=couleur1, border-bottom=couleur2,
                        pas de coin arrondi, traité comme milieu de span.
        """
        text_color = "#AAA" if is_past else "#555"
        base = (
            f"font-size: 8pt; color: {text_color}; background: transparent; padding: 0;"
        )
        n = len(evts)

        if n == 1:
            ev = evts[0]
            c = ev.get("couleur", "#FF9800")
            bw = 1.5
            r = 6
            hp, hn = self._check_span_continuity(pos, week, ev.get("id"), annee, mois)

            if not hp and not hn:
                return f"QPushButton {{ border: {bw}px solid {c}; border-radius: {r}px; {base} }}"
            elif not hp and hn:
                return (
                    f"QPushButton {{ border: {bw}px solid {c}; border-right: none; "
                    f"border-top-left-radius: {r}px; border-bottom-left-radius: {r}px; "
                    f"border-top-right-radius: 0; border-bottom-right-radius: 0; {base} }}"
                )
            elif hp and hn:
                return (
                    f"QPushButton {{ border-top: {bw}px solid {c}; border-bottom: {bw}px solid {c}; "
                    f"border-left: none; border-right: none; border-radius: 0; {base} }}"
                )
            else:
                return (
                    f"QPushButton {{ border: {bw}px solid {c}; border-left: none; "
                    f"border-top-right-radius: {r}px; border-bottom-right-radius: {r}px; "
                    f"border-top-left-radius: 0; border-bottom-left-radius: 0; {base} }}"
                )

        # 2+ événements : multi-couleur, jamais de coins arrondis
        colors = [ev.get("couleur", "#FF9800") for ev in evts[:3]]
        bw = max(1.0, 2.0 - 0.3 * (n - 1))
        top_c = colors[0]
        bot_c = colors[-1]
        side_c = colors[1] if len(colors) >= 3 else colors[0]

        any_prev = any_next = False
        for ev in evts:
            hp, hn = self._check_span_continuity(pos, week, ev.get("id"), annee, mois)
            any_prev = any_prev or hp
            any_next = any_next or hn

        left = (
            "border-left: none;" if any_prev else f"border-left: {bw}px solid {side_c};"
        )
        right = (
            "border-right: none;"
            if any_next
            else f"border-right: {bw}px solid {side_c};"
        )

        return (
            f"QPushButton {{ border-top: {bw}px solid {top_c}; "
            f"border-bottom: {bw}px solid {bot_c}; "
            f"{left} {right} border-radius: 0; {base} }}"
        )

    def _on_mini_calendrier_clic(self, mois: int):
        """Gère le clic sur un mini calendrier : bascule vers la vue mois."""
        self.current_date = self.current_date.replace(month=mois, day=1)
        self._changer_vue("mois")

    # ------------------------------------------------------------------ #
    #                       Utilitaires                                   #
    # ------------------------------------------------------------------ #

    def _vider_layout(self, layout):
        """Vide un layout recursivement."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._vider_layout(item.layout())
