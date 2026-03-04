"""Vue pour l'onglet Calendrier style Apple Calendar.

Supporte les vues Mois, Semaine et Jour avec navigation.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from datetime import datetime, timedelta
import calendar

from utils.styles import style_bouton, Couleurs


class CalendrierView(QWidget):
    """Onglet Calendrier style Apple Calendar."""

    # Signal emis avec (date_debut, date_fin) pour voir les stats
    voir_stats_periode = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.current_date = datetime.now()
        self._vue_courante = "mois"
        self._construire_ui()

    def _construire_ui(self):
        self.setStyleSheet("background-color: #FFFFFF;")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # === EN-TETE (3 sections: Gauche | Centre | Droite) ===
        header_layout = QHBoxLayout()

        # --- SECTION GAUCHE: Boutons de vue ---
        view_btn_style = (
            "QPushButton {"
            "    background-color: white;"
            "    border: 2px solid #9E9E9E;"
            "    padding: 8px 16px;"
            "    font-size: 11pt;"
            "}"
            "QPushButton:hover {"
            "    background-color: #E3F2FD;"
            "}"
            "QPushButton:checked {"
            "    background-color: #2196F3;"
            "    color: white;"
            "    border-color: #2196F3;"
            "}"
        )

        self._btn_mois = QPushButton("Mois")
        self._btn_mois.setCheckable(True)
        self._btn_mois.setChecked(True)
        self._btn_mois.setStyleSheet(view_btn_style)
        self._btn_mois.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_mois.clicked.connect(lambda: self._changer_vue("mois"))

        self._btn_semaine = QPushButton("Semaine")
        self._btn_semaine.setCheckable(True)
        self._btn_semaine.setStyleSheet(view_btn_style)
        self._btn_semaine.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_semaine.clicked.connect(lambda: self._changer_vue("semaine"))

        self._btn_jour = QPushButton("Jour")
        self._btn_jour.setCheckable(True)
        self._btn_jour.setStyleSheet(view_btn_style)
        self._btn_jour.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_jour.clicked.connect(lambda: self._changer_vue("jour"))

        self._btn_annee = QPushButton("Année")
        self._btn_annee.setCheckable(True)
        self._btn_annee.setStyleSheet(view_btn_style)
        self._btn_annee.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_annee.clicked.connect(lambda: self._changer_vue("annee"))

        header_layout.addWidget(self._btn_mois)
        header_layout.addWidget(self._btn_semaine)
        header_layout.addWidget(self._btn_jour)
        header_layout.addWidget(self._btn_annee)

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
        btn_next.clicked.connect(self._suivant)
        header_layout.addWidget(btn_next)

        header_layout.addStretch()

        # --- SECTION DROITE: Bouton d'action ---
        btn_stats = QPushButton("Voir statistiques")
        btn_stats.setStyleSheet(style_bouton(Couleurs.SUCCES, taille="petit"))
        btn_stats.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_stats.clicked.connect(self._voir_stats_periode)
        header_layout.addWidget(btn_stats)

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
        "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre",
    ]

    _JOURS_FR = [
        "Lundi", "Mardi", "Mercredi", "Jeudi",
        "Vendredi", "Samedi", "Dimanche",
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

    def _changer_vue(self, vue: str):
        self._btn_mois.setChecked(vue == "mois")
        self._btn_semaine.setChecked(vue == "semaine")
        self._btn_jour.setChecked(vue == "jour")
        self._btn_annee.setChecked(vue == "annee")
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
                fin = datetime(self.current_date.year, self.current_date.month + 1, 1) - timedelta(days=1)
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
            debut.strftime('%Y-%m-%d'), fin.strftime('%Y-%m-%d')
        )

    def _rafraichir_vue(self):
        """Rafraichit la vue courante."""
        if self._vue_courante == "mois":
            self._afficher_vue_mois()
        elif self._vue_courante == "semaine":
            self._afficher_vue_semaine()
        elif self._vue_courante == "jour":
            self._afficher_vue_jour()
        elif self._vue_courante == "annee":
            self._afficher_vue_annee()

    # ------------------------------------------------------------------ #
    #                       Vue Mois                                      #
    # ------------------------------------------------------------------ #

    def _afficher_vue_mois(self):
        """Affiche la vue mois."""
        self._vider_layout(self._calendar_layout)

        # En-tetes des jours
        days_header = QHBoxLayout()
        days_header.setSpacing(2)
        jours_fr = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

        for jour in jours_fr:
            label = QLabel(jour)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(
                "font-weight: bold; color: #666; padding: 10px; font-size: 11pt;"
            )
            days_header.addWidget(label)

        self._calendar_layout.addLayout(days_header)

        # Grille du calendrier
        cal = calendar.monthcalendar(
            self.current_date.year, self.current_date.month
        )

        for week in cal:
            week_layout = QHBoxLayout()
            week_layout.setSpacing(2)

            for day in week:
                if day == 0:
                    empty = QWidget()
                    empty.setStyleSheet("background-color: #F5F5F5;")
                    week_layout.addWidget(empty)
                else:
                    day_widget = self._creer_cellule_jour(day)
                    week_layout.addWidget(day_widget)

            self._calendar_layout.addLayout(week_layout)

        self._calendar_layout.addStretch()

    def _creer_cellule_jour(self, day: int) -> QFrame:
        """Cree une cellule de jour."""
        cell = QFrame()
        cell.setFrameShape(QFrame.Shape.Box)
        cell.setMinimumHeight(100)

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
                "QFrame {"
                "    background-color: #E3F2FD;"
                "    border: 3px solid #2196F3;"
                "    border-radius: 8px;"
                "}"
            )
        elif is_past:
            cell.setStyleSheet(
                "QFrame {"
                "    background-color: rgba(240, 240, 240, 0.5);"
                "    border: 2px solid #E0E0E0;"
                "    border-radius: 8px;"
                "}"
            )
        else:
            cell.setStyleSheet(
                "QFrame {"
                "    background-color: white;"
                "    border: 2px solid #9E9E9E;"
                "    border-radius: 8px;"
                "}"
                "QFrame:hover {"
                "    background-color: #F5F5F5;"
                "}"
            )

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        day_label = QLabel(str(day))
        if is_today:
            color = "#2196F3"
        elif is_past:
            color = "rgba(100, 100, 100, 0.6)"
        else:
            color = "#333"
        day_label.setStyleSheet(
            f"font-size: 14pt; font-weight: bold; color: {color}; padding: 5px;"
        )
        layout.addWidget(day_label)

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
    #                       Vue Semaine                                   #
    # ------------------------------------------------------------------ #

    def _afficher_vue_semaine(self):
        """Affiche la vue semaine avec grille horaire."""
        self._vider_layout(self._calendar_layout)

        # Calculer le debut de la semaine (Lundi)
        debut_semaine = self.current_date - timedelta(
            days=self.current_date.weekday()
        )

        # En-tetes des jours
        header_layout = QHBoxLayout()
        header_layout.setSpacing(2)

        # Colonne heure (vide)
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

            label = QLabel(
                f"{self._JOURS_FR[i][:3]}\n{day_date.strftime('%d/%m')}"
            )
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if is_today:
                label.setStyleSheet(
                    "QLabel {"
                    "    font-weight: bold;"
                    "    color: white;"
                    "    padding: 10px;"
                    "    background-color: #2196F3;"
                    "    border-radius: 8px;"
                    "}"
                )
            else:
                label.setStyleSheet(
                    "QLabel {"
                    "    font-weight: bold;"
                    "    color: #2196F3;"
                    "    padding: 10px;"
                    "    background-color: #E3F2FD;"
                    "    border-radius: 8px;"
                    "}"
                )
            header_layout.addWidget(label, 1)

        self._calendar_layout.addLayout(header_layout)

        # Grille horaire (0h-23h) dans un scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(2)

        for row, hour in enumerate(range(0, 24)):
            # Colonne heure
            hour_label = QLabel(f"{hour:02d}:00")
            hour_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
            )
            hour_label.setStyleSheet(
                "font-weight: 600; color: #666; padding-right: 10px;"
            )
            hour_label.setFixedWidth(80)
            grid_layout.addWidget(hour_label, row, 0)

            # Colonnes jours
            for day_idx in range(7):
                day_date = debut_semaine + timedelta(days=day_idx)
                cell = self._creer_cellule_heure(day_date, hour)
                grid_layout.addWidget(cell, row, day_idx + 1)

        grid_widget.setLayout(grid_layout)
        scroll.setWidget(grid_widget)

        self._calendar_layout.addWidget(scroll)

    def _creer_cellule_heure(self, date_obj: datetime, hour: int) -> QFrame:
        """Cree une cellule horaire pour la vue semaine."""
        cell = QFrame()
        cell.setFrameShape(QFrame.Shape.Box)
        cell.setMinimumHeight(60)
        cell.setMinimumWidth(100)

        is_now = (
            date_obj.date() == datetime.now().date()
            and hour == datetime.now().hour
        )

        if is_now:
            cell.setStyleSheet(
                "QFrame {"
                "    background-color: #E3F2FD;"
                "    border: 2px solid #2196F3;"
                "}"
            )
        else:
            cell.setStyleSheet(
                "QFrame {"
                "    background-color: white;"
                "    border: 1px solid #D0D0D0;"
                "}"
                "QFrame:hover {"
                "    background-color: #F5F5F5;"
                "}"
            )

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
        """Affiche la vue jour avec timeline horaire 0h-23h."""
        self._vider_layout(self._calendar_layout)

        # En-tete du jour
        jour_nom = self._JOURS_FR[self.current_date.weekday()]
        header = QLabel(
            f"{jour_nom} {self.current_date.strftime('%d/%m/%Y')}"
        )
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(
            "QLabel {"
            "    font-size: 18pt;"
            "    font-weight: bold;"
            "    color: #2196F3;"
            "    padding: 15px;"
            "    background-color: #E3F2FD;"
            "    border-radius: 10px;"
            "}"
        )
        self._calendar_layout.addWidget(header)

        # ScrollArea pour la timeline
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        timeline_widget = QWidget()
        timeline_layout = QVBoxLayout()
        timeline_layout.setSpacing(0)

        # Creer les tranches horaires (0h-23h)
        for hour in range(24):
            hour_frame = QFrame()
            hour_frame.setFrameShape(QFrame.Shape.Box)
            hour_frame.setMinimumHeight(80)

            is_current_hour = (
                self.current_date.date() == datetime.now().date()
                and hour == datetime.now().hour
            )

            if is_current_hour:
                hour_frame.setStyleSheet(
                    "QFrame {"
                    "    background-color: #E3F2FD;"
                    "    border: 2px solid #2196F3;"
                    "    border-radius: 5px;"
                    "}"
                )
            else:
                hour_frame.setStyleSheet(
                    "QFrame {"
                    "    background-color: white;"
                    "    border: 1px solid #D0D0D0;"
                    "    border-radius: 5px;"
                    "}"
                    "QFrame:hover {"
                    "    background-color: #F9F9F9;"
                    "}"
                )

            hour_layout = QHBoxLayout()

            # Label de l'heure
            hour_label = QLabel(f"{hour:02d}:00")
            hour_label.setAlignment(Qt.AlignmentFlag.AlignTop)
            hour_label.setStyleSheet(
                "QLabel {"
                "    font-size: 14pt;"
                "    font-weight: bold;"
                "    color: #666;"
                "    padding: 10px;"
                "    min-width: 80px;"
                "}"
            )
            hour_layout.addWidget(hour_label)

            # Zone des evenements (placeholder)
            events_widget = QWidget()
            events_layout = QVBoxLayout()
            events_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            events_widget.setLayout(events_layout)
            hour_layout.addWidget(events_widget, 1)

            hour_frame.setLayout(hour_layout)
            hour_frame.setCursor(Qt.CursorShape.PointingHandCursor)

            timeline_layout.addWidget(hour_frame)

        timeline_widget.setLayout(timeline_layout)
        scroll.setWidget(timeline_widget)

        self._calendar_layout.addWidget(scroll)

        # Scroller vers l'heure actuelle
        if self.current_date.date() == datetime.now().date():
            current_hour = datetime.now().hour
            # Utiliser un timer pour s'assurer que le scroll est effectif
            from PySide6.QtCore import QTimer
            QTimer.singleShot(
                100,
                lambda: scroll.verticalScrollBar().setValue(current_hour * 80),
            )

    # ------------------------------------------------------------------ #
    #                       Vue Année                                     #
    # ------------------------------------------------------------------ #

    def _afficher_vue_annee(self):
        """Affiche la vue année avec une grille 3x4 (12 mois)."""
        self._vider_layout(self._calendar_layout)

        # Créer une grille 3 lignes x 4 colonnes
        grid = QGridLayout()
        grid.setSpacing(10)

        for mois_idx in range(1, 13):
            mini_cal = self._creer_mini_calendrier(self.current_date.year, mois_idx)
            row = (mois_idx - 1) // 4
            col = (mois_idx - 1) % 4
            grid.addWidget(mini_cal, row, col)

        grid_widget = QWidget()
        grid_widget.setLayout(grid)
        self._calendar_layout.addWidget(grid_widget)

    def _creer_mini_calendrier(self, annee: int, mois: int) -> QFrame:
        """Crée un mini calendrier pour un mois donné.

        Args:
            annee: Année du calendrier
            mois: Mois (1-12)

        Returns:
            QFrame contenant le mini calendrier
        """
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet(
            "QFrame {"
            "    background-color: white;"
            "    border: 2px solid #9E9E9E;"
            "    border-radius: 8px;"
            "    padding: 10px;"
            "}"
        )

        layout = QVBoxLayout(frame)
        layout.setSpacing(5)

        # Titre du mois
        titre = QLabel(self._MOIS_FR[mois - 1])
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titre.setStyleSheet(
            "font-size: 11pt; font-weight: bold; color: #2196F3; border: none;"
        )
        layout.addWidget(titre)

        # En-têtes des jours (Lu Ma Me Je Ve Sa Di)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(2)
        jours_abbr = ["L", "M", "M", "J", "V", "S", "D"]
        for jour in jours_abbr:
            label = QLabel(jour)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(
                "font-size: 8pt; font-weight: bold; color: #666; border: none;"
            )
            label.setFixedSize(24, 20)
            header_layout.addWidget(label)
        layout.addLayout(header_layout)

        # Grille des jours
        cal = calendar.monthcalendar(annee, mois)
        for week in cal:
            week_layout = QHBoxLayout()
            week_layout.setSpacing(2)

            for day in week:
                if day == 0:
                    # Jour vide
                    empty = QLabel("")
                    empty.setFixedSize(24, 24)
                    week_layout.addWidget(empty)
                else:
                    day_label = QLabel(str(day))
                    day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    day_label.setFixedSize(24, 24)

                    # Vérifier si c'est aujourd'hui
                    now = datetime.now()
                    is_today = (
                        day == now.day
                        and mois == now.month
                        and annee == now.year
                    )

                    if is_today:
                        day_label.setStyleSheet(
                            "QLabel {"
                            "    background-color: #2196F3;"
                            "    color: white;"
                            "    border-radius: 12px;"
                            "    font-size: 9pt;"
                            "    font-weight: bold;"
                            "    border: none;"
                            "}"
                        )
                    else:
                        day_label.setStyleSheet(
                            "QLabel {"
                            "    color: #333;"
                            "    font-size: 9pt;"
                            "    border: none;"
                            "}"
                        )

                    week_layout.addWidget(day_label)

            layout.addLayout(week_layout)

        # Rendre le mini calendrier cliquable pour basculer vers le mois
        frame.setCursor(Qt.CursorShape.PointingHandCursor)
        frame.mousePressEvent = lambda e, m=mois: self._on_mini_calendrier_clic(m)

        return frame

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
