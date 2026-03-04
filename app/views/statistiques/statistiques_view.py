"""Vue pour l'onglet Statistiques avec donnees reelles et graphiques Plotly."""

import logging

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QComboBox,
    QScrollArea,
    QGridLayout,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWebEngineWidgets import QWebEngineView
from datetime import datetime, timedelta
from collections import defaultdict

from utils.styles import style_scroll_area, Couleurs
from viewmodels.stats_vm import StatsViewModel

logger = logging.getLogger(__name__)


class StatistiquesView(QWidget):
    """Onglet Statistiques avec tableau de bord et donnees reelles."""

    def __init__(self, parent=None):  # ← parent=None par défaut
        super().__init__(parent)
        self.viewmodel = StatsViewModel()

        # Variables de periode
        self.date_actuelle = datetime.now()
        self.type_periode = "Mois"  # Jour, Semaine, Mois, Annee

        self._construire_ui()
        self._connecter_signaux()
        self._mettre_a_jour_label_periode()
        self._charger_stats()

    def _construire_ui(self):
        # ScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(style_scroll_area())

        conteneur = QWidget()
        conteneur.setStyleSheet("background-color: #FFFFFF;")
        layout_principal = QVBoxLayout(conteneur)
        layout_principal.setSpacing(20)
        layout_principal.setContentsMargins(30, 20, 30, 30)

        # === EN-TETE AVEC NAVIGATION ===
        layout_principal.addLayout(self._creer_section_periode())

        # === CARTES KPI ===
        layout_principal.addLayout(self._creer_section_kpis())

        # === GRAPHIQUES PLOTLY ===
        layout_principal.addLayout(self._creer_section_graphiques())

        # === SECTION TOP ===
        layout_principal.addLayout(self._creer_section_tops())

        # === BOUTONS EXPORT ===
        export_layout = QHBoxLayout()
        export_layout.addStretch()

        btn_export_csv = QPushButton("Exporter en CSV")
        btn_export_csv.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "border: none; border-radius: 8px; padding: 10px 20px; "
            "font-size: 12pt; font-weight: 600; }"
            "QPushButton:hover { background-color: #388E3C; }"
        )
        btn_export_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export_csv.clicked.connect(self._exporter_csv)
        export_layout.addWidget(btn_export_csv)

        btn_export_pdf = QPushButton("Exporter en PDF")
        btn_export_pdf.setStyleSheet(
            "QPushButton { background-color: #F44336; color: white; "
            "border: none; border-radius: 8px; padding: 10px 20px; "
            "font-size: 12pt; font-weight: 600; }"
            "QPushButton:hover { background-color: #D32F2F; }"
        )
        btn_export_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export_pdf.clicked.connect(self._exporter_pdf)
        export_layout.addWidget(btn_export_pdf)

        layout_principal.addLayout(export_layout)

        layout_principal.addStretch()

        scroll.setWidget(conteneur)

        layout_self = QVBoxLayout(self)
        layout_self.setContentsMargins(0, 0, 0, 0)
        layout_self.addWidget(scroll)

    def _creer_section_periode(self) -> QHBoxLayout:
        """Cree l'en-tete avec le titre et la navigation de periode (3 sections)."""
        header = QHBoxLayout()

        # --- SECTION GAUCHE: Selecteur de type de periode ---
        self.combo_periode = QComboBox()
        self.combo_periode.addItems(["Jour", "Semaine", "Mois", "Annee"])
        self.combo_periode.setCurrentIndex(2)  # Mois par defaut
        self.combo_periode.setStyleSheet(
            "QComboBox { min-width: 110px; min-height: 36px; font-size: 12pt; "
            "padding: 5px 10px; border: 2px solid #2196F3; border-radius: 6px; "
            "background-color: white; }"
        )
        header.addWidget(self.combo_periode)

        header.addStretch()

        # --- SECTION CENTRE: Navigation (< label >) ---
        self.btn_prev = QPushButton("\u25c0")
        self.btn_prev.setFixedSize(36, 36)
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.setToolTip("Période précédente")
        self.btn_prev.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "border: none; border-radius: 18px; font-size: 14pt; font-weight: bold; }"
            "QPushButton:hover { background-color: #1976D2; }"
        )
        header.addWidget(self.btn_prev)

        self.label_periode = QLabel()
        self.label_periode.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.label_periode.setStyleSheet(
            "color: #1976D2; min-width: 200px; border: none;"
        )
        self.label_periode.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(self.label_periode)

        self.btn_next = QPushButton("\u25b6")
        self.btn_next.setFixedSize(36, 36)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setToolTip("Période suivante")
        self.btn_next.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "border: none; border-radius: 18px; font-size: 14pt; font-weight: bold; }"
            "QPushButton:hover { background-color: #1976D2; }"
        )
        header.addWidget(self.btn_next)

        header.addStretch()

        # --- SECTION DROITE: Bouton d'action ---
        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "border: none; border-radius: 8px; padding: 10px 20px; "
            "font-size: 12pt; font-weight: 600; }"
            "QPushButton:hover { background-color: #1976D2; }"
        )
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        header.addWidget(self.btn_refresh)

        return header

    def _creer_section_kpis(self) -> QGridLayout:
        """Cree les cartes KPI (chiffre d'affaires, ventes, clients, panier moyen)."""
        kpi_layout = QGridLayout()
        kpi_layout.setSpacing(15)

        kpi_data = [
            ("Chiffre d'affaires", "0.00 EUR", "#4CAF50"),
            ("Nombre de ventes", "0", "#2196F3"),
            ("Clients actifs", "0", "#FF9800"),
            ("Panier moyen", "0.00 EUR", "#9C27B0"),
        ]

        self._kpi_labels = {}
        for i, (titre_kpi, valeur, couleur) in enumerate(kpi_data):
            card, label_valeur = self._creer_carte_kpi(titre_kpi, valeur, couleur)
            self._kpi_labels[titre_kpi] = label_valeur
            kpi_layout.addWidget(card, 0, i)

        return kpi_layout

    def _creer_section_graphiques(self) -> QHBoxLayout:
        """Cree la section des graphiques Plotly (CA et produits)."""
        graphiques_layout = QHBoxLayout()
        graphiques_layout.setSpacing(15)

        self.chart_ca = QWebEngineView()
        self.chart_ca.setMinimumHeight(400)
        graphiques_layout.addWidget(self.chart_ca)

        self.chart_produits = QWebEngineView()
        self.chart_produits.setMinimumHeight(400)
        graphiques_layout.addWidget(self.chart_produits)

        return graphiques_layout

    def _creer_section_tops(self) -> QHBoxLayout:
        """Cree la section des tops clients et produits."""
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)

        self._top_clients_frame, self._top_clients_layout = self._creer_section_top(
            "Top 5 Clients"
        )
        top_layout.addWidget(self._top_clients_frame)

        self._top_produits_frame, self._top_produits_layout = self._creer_section_top(
            "Top 5 Produits"
        )
        top_layout.addWidget(self._top_produits_frame)

        return top_layout

    def _connecter_signaux(self):
        """Connecte les signaux."""
        self.btn_refresh.clicked.connect(self._charger_stats)
        self.combo_periode.currentIndexChanged.connect(self._on_periode_changed)
        self.btn_prev.clicked.connect(self._periode_precedente)
        self.btn_next.clicked.connect(self._periode_suivante)

    # ------------------------------------------------------------------ #
    #                       Navigation de periode                         #
    # ------------------------------------------------------------------ #

    def _on_periode_changed(self, index: int):
        """Change le type de periode."""
        types = ["Jour", "Semaine", "Mois", "Annee"]
        self.type_periode = types[index]
        self._mettre_a_jour_label_periode()
        self._charger_stats()

    def _periode_precedente(self):
        """Va a la periode precedente."""
        if self.type_periode == "Jour":
            self.date_actuelle -= timedelta(days=1)
        elif self.type_periode == "Semaine":
            self.date_actuelle -= timedelta(weeks=1)
        elif self.type_periode == "Mois":
            if self.date_actuelle.month == 1:
                self.date_actuelle = self.date_actuelle.replace(
                    year=self.date_actuelle.year - 1, month=12, day=1
                )
            else:
                self.date_actuelle = self.date_actuelle.replace(
                    month=self.date_actuelle.month - 1, day=1
                )
        elif self.type_periode == "Annee":
            self.date_actuelle = self.date_actuelle.replace(
                year=self.date_actuelle.year - 1
            )
        self._mettre_a_jour_label_periode()
        self._charger_stats()

    def _periode_suivante(self):
        """Va a la periode suivante."""
        if self.type_periode == "Jour":
            self.date_actuelle += timedelta(days=1)
        elif self.type_periode == "Semaine":
            self.date_actuelle += timedelta(weeks=1)
        elif self.type_periode == "Mois":
            if self.date_actuelle.month == 12:
                self.date_actuelle = self.date_actuelle.replace(
                    year=self.date_actuelle.year + 1, month=1, day=1
                )
            else:
                self.date_actuelle = self.date_actuelle.replace(
                    month=self.date_actuelle.month + 1, day=1
                )
        elif self.type_periode == "Annee":
            self.date_actuelle = self.date_actuelle.replace(
                year=self.date_actuelle.year + 1
            )
        self._mettre_a_jour_label_periode()
        self._charger_stats()

    def _aller_aujourdhui(self):
        """Revient a aujourd'hui."""
        self.date_actuelle = datetime.now()
        self._mettre_a_jour_label_periode()
        self._charger_stats()

    def _mettre_a_jour_label_periode(self):
        """Met a jour le label de la periode."""
        mois_fr = [
            "",
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

        if self.type_periode == "Jour":
            self.label_periode.setText(self.date_actuelle.strftime("%d/%m/%Y"))
        elif self.type_periode == "Semaine":
            debut = self.date_actuelle - timedelta(days=self.date_actuelle.weekday())
            fin = debut + timedelta(days=6)
            self.label_periode.setText(
                f"Sem. {debut.strftime('%d/%m')} - {fin.strftime('%d/%m/%Y')}"
            )
        elif self.type_periode == "Mois":
            self.label_periode.setText(
                f"{mois_fr[self.date_actuelle.month]} {self.date_actuelle.year}"
            )
        elif self.type_periode == "Annee":
            self.label_periode.setText(str(self.date_actuelle.year))

    # ------------------------------------------------------------------ #
    #                       Creation des widgets                          #
    # ------------------------------------------------------------------ #

    def _creer_carte_kpi(
        self, titre: str, valeur: str, couleur: str
    ) -> tuple[QFrame, QLabel]:
        """Cree une carte KPI et retourne (frame, label_valeur)."""
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background-color: white; border: 2px solid #9E9E9E; "
            "border-radius: 12px; padding: 20px; }"
        )

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label_titre = QLabel(titre)
        label_titre.setStyleSheet("font-size: 11pt; color: #666; border: none;")
        label_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_titre)

        label_valeur = QLabel(valeur)
        label_valeur.setStyleSheet(
            f"font-size: 24pt; font-weight: bold; color: {couleur}; " f"border: none;"
        )
        label_valeur.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_valeur)

        return card, label_valeur

    def _creer_section_top(self, titre: str) -> tuple[QFrame, QVBoxLayout]:
        """Cree une section Top N et retourne (frame, content_layout)."""
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background-color: #FAFAFA; border: 2px solid #9E9E9E; "
            "border-radius: 12px; padding: 20px; }"
        )

        layout = QVBoxLayout(frame)

        label_titre = QLabel(titre)
        label_titre.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #2196F3; border: none;"
        )
        layout.addWidget(label_titre)

        content_layout = QVBoxLayout()
        placeholder = QLabel("Aucune donnee disponible")
        placeholder.setStyleSheet(
            "font-size: 11pt; color: #666; padding: 5px; border: none;"
        )
        content_layout.addWidget(placeholder)
        layout.addLayout(content_layout)

        layout.addStretch()

        return frame, content_layout

    # ------------------------------------------------------------------ #
    #                   Chargement des statistiques                       #
    # ------------------------------------------------------------------ #

    def _obtenir_dates_periode(self) -> tuple[str, str]:
        """Retourne (date_debut, date_fin) selon la periode et la navigation."""
        d = self.date_actuelle

        if self.type_periode == "Jour":
            date_debut = d.strftime("%Y-%m-%d 00:00:00")
            date_fin = d.strftime("%Y-%m-%d 23:59:59")

        elif self.type_periode == "Semaine":
            debut = d - timedelta(days=d.weekday())
            fin = debut + timedelta(days=6)
            date_debut = debut.strftime("%Y-%m-%d 00:00:00")
            date_fin = fin.strftime("%Y-%m-%d 23:59:59")

        elif self.type_periode == "Mois":
            date_debut = d.replace(day=1).strftime("%Y-%m-%d 00:00:00")
            if d.month == 12:
                dernier_jour = d.replace(day=31)
            else:
                dernier_jour = d.replace(month=d.month + 1, day=1) - timedelta(days=1)
            date_fin = dernier_jour.strftime("%Y-%m-%d 23:59:59")

        elif self.type_periode == "Annee":
            date_debut = d.replace(month=1, day=1).strftime("%Y-%m-%d 00:00:00")
            date_fin = d.replace(month=12, day=31).strftime("%Y-%m-%d 23:59:59")

        else:
            date_debut = "2000-01-01 00:00:00"
            date_fin = datetime.now().strftime("%Y-%m-%d 23:59:59")

        return date_debut, date_fin

    def charger_periode(self, debut: str, fin: str):
        """Charge les stats pour une periode externe (ex: depuis le calendrier).

        Args:
            debut: Date de début au format YYYY-MM-DD
            fin: Date de fin au format YYYY-MM-DD
        """
        logger.info(f"Chargement stats période externe : {debut} → {fin}")

        try:
            # Convertir les dates YYYY-MM-DD en timestamps complets
            date_debut = f"{debut} 00:00:00"
            date_fin = f"{fin} 23:59:59"

            # Mettre à jour la date actuelle pour refléter la période
            from datetime import datetime

            self.date_actuelle = datetime.strptime(debut, "%Y-%m-%d")
            self._mettre_a_jour_label_periode()

            # Charger les données
            donnees = self.viewmodel.charger_statistiques(date_debut, date_fin)
            if not donnees:
                logger.warning("Aucune donnée retournée pour la période externe")
                return

            # Mettre à jour les KPI
            kpis = donnees["kpis"]
            self._kpi_labels["Chiffre d'affaires"].setText(
                f"{kpis['ca_total']:.2f} EUR"
            )
            self._kpi_labels["Nombre de ventes"].setText(str(kpis["nb_ventes"]))
            self._kpi_labels["Clients actifs"].setText(str(kpis["clients_actifs"]))
            self._kpi_labels["Panier moyen"].setText(f"{kpis['panier_moyen']:.2f} EUR")

            # Mettre à jour les tops
            self._maj_section_top(
                self._top_clients_layout, donnees["top_clients"], "client"
            )
            self._maj_section_top(
                self._top_produits_layout, donnees["top_produits"], "produit"
            )

            # Générer les graphiques
            self._generer_graphiques(donnees["ventes"], donnees["top_produits"])

        except Exception as e:
            logger.error(f"Erreur chargement période externe : {e}", exc_info=True)

    def _charger_stats(self):
        """Charge les statistiques reelles depuis la base de donnees."""
        try:
            date_debut, date_fin = self._obtenir_dates_periode()
            logger.info("Chargement stats : %s -> %s", date_debut, date_fin)
            donnees = self.viewmodel.charger_statistiques(date_debut, date_fin)

            if not donnees:
                logger.warning("Aucune donnee retournee par le ViewModel")
                return

            # --- KPIs ---
            kpis = donnees["kpis"]
            self._kpi_labels["Chiffre d'affaires"].setText(
                f"{kpis['ca_total']:.2f} EUR"
            )
            self._kpi_labels["Nombre de ventes"].setText(str(kpis["nb_ventes"]))
            self._kpi_labels["Clients actifs"].setText(str(kpis["clients_actifs"]))
            self._kpi_labels["Panier moyen"].setText(f"{kpis['panier_moyen']:.2f} EUR")

            # --- Top sections ---
            self._maj_section_top(
                self._top_clients_layout, donnees["top_clients"], "client"
            )
            self._maj_section_top(
                self._top_produits_layout, donnees["top_produits"], "produit"
            )

            # --- Graphiques Plotly ---
            self._generer_graphiques(donnees["ventes"], donnees["top_produits"])

        except Exception as e:
            logger.error(
                "Erreur lors du chargement des statistiques : %s", e, exc_info=True
            )
            self.chart_ca.setHtml(
                "<html><body style='text-align:center;padding-top:150px;"
                "color:#F44336;font-family:sans-serif;'>"
                "<h3>Erreur de chargement</h3>"
                f"<p>{str(e)}</p></body></html>"
            )
            self.chart_produits.setHtml(
                "<html><body style='text-align:center;padding-top:150px;"
                "color:#F44336;font-family:sans-serif;'>"
                "<h3>Erreur de chargement</h3></body></html>"
            )

    def _maj_section_top(self, layout: QVBoxLayout, items: list[dict], type_item: str):
        """Met a jour une section Top avec les donnees reelles."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not items:
            placeholder = QLabel("Aucune donnee disponible")
            placeholder.setStyleSheet(
                "font-size: 11pt; color: #666; padding: 5px; border: none;"
            )
            layout.addWidget(placeholder)
            return

        for i, item in enumerate(items):
            if type_item == "client":
                nom = f"{item.get('nom', '').upper()} {item.get('prenom', '')}"
                detail = (
                    f"{item.get('total_ca', 0):.2f} EUR "
                    f"({item.get('nb_achats', 0)} achats)"
                )
            else:
                nom = item.get("nom", "")
                detail = (
                    f"{item.get('total_ca', 0):.2f} EUR "
                    f"({item.get('total_qte', 0)} vendus)"
                )

            label = QLabel(f"{i + 1}. {nom} - {detail}")
            label.setStyleSheet(
                "font-size: 11pt; color: #333; padding: 5px; border: none;"
            )
            layout.addWidget(label)

    # ------------------------------------------------------------------ #
    #                    Graphiques Plotly                                 #
    # ------------------------------------------------------------------ #

    def _generer_graphiques(self, ventes: list, top_produits: list):
        """Genere les graphiques Plotly avec les donnees reelles."""
        logger.info("=== DÉBUT GÉNÉRATION GRAPHIQUES ===")
        logger.info(f"Ventes reçues : {len(ventes)}")
        logger.info(f"Top produits reçus : {len(top_produits)}")

        if ventes:
            logger.info(f"Première vente : {ventes[0]}")
        else:
            logger.info("AUCUNE vente dans la liste")

        _html_vide = (
            "<html><body style='text-align:center;padding-top:150px;"
            "color:#999;font-family:sans-serif;'>"
            "<h3>Aucune donnee disponible</h3>"
            "<p>Aucune vente enregistree pour cette periode.</p></body></html>"
        )

        try:
            import plotly.graph_objects as go

            logger.info(
                f"Plotly importé avec succès, version : {go.__version__ if hasattr(go, '__version__') else 'inconnue'}"
            )
        except ImportError as e:
            logger.error(f"Plotly non installé : {e}")
            _html_err = (
                "<html><body style='text-align:center;padding-top:150px;"
                "color:#999;font-family:sans-serif;'>"
                "<h3>Plotly non installe</h3>"
                "<p>pip install plotly</p></body></html>"
            )
            self.chart_ca.setHtml(_html_err)
            self.chart_produits.setHtml(_html_err)
            return

        try:
            from utils.plotly_render import charger_plotly_dans_view

            logger.info("charger_plotly_dans_view importé avec succès")

            # --- Graphique 1 : Evolution du CA ---
            if not ventes:
                self.chart_ca.setHtml(_html_vide)
            else:
                ventes_par_jour = defaultdict(float)
                for vente in ventes:
                    date_str = str(vente.get("date_vente", ""))[:10]
                    ventes_par_jour[date_str] += vente.get("prix_total", 0)

                dates = sorted(ventes_par_jour.keys())
                montants = [ventes_par_jour[d] for d in dates]

                fig1 = go.Figure()
                fig1.add_trace(
                    go.Scatter(
                        x=dates,
                        y=montants,
                        mode="lines+markers",
                        name="CA journalier",
                        line=dict(color="#2196F3", width=3),
                        marker=dict(size=8),
                        fill="tozeroy",
                        fillcolor="rgba(33, 150, 243, 0.1)",
                    )
                )
                fig1.update_layout(
                    title="Evolution du chiffre d'affaires",
                    xaxis_title="Date",
                    yaxis_title="CA (EUR)",
                    hovermode="x unified",
                    template="plotly_white",
                    height=380,
                    margin=dict(l=50, r=20, t=50, b=40),
                )
                charger_plotly_dans_view(self.chart_ca, fig1)
                logger.info("Graphique CA chargé via fichier temporaire")

            # --- Graphique 2 : Top produits ---
            if top_produits:
                noms = [p.get("nom", "") for p in top_produits]
                ca = [p.get("total_ca", 0) for p in top_produits]

                fig2 = go.Figure()
                fig2.add_trace(
                    go.Bar(
                        x=ca,
                        y=noms,
                        orientation="h",
                        marker=dict(color="#4CAF50"),
                    )
                )
                fig2.update_layout(
                    title="Top produits par CA",
                    xaxis_title="CA (EUR)",
                    template="plotly_white",
                    height=380,
                    margin=dict(l=120, r=20, t=50, b=40),
                )
                charger_plotly_dans_view(self.chart_produits, fig2)
                logger.info("Graphique Produits chargé via fichier temporaire")
            else:
                self.chart_produits.setHtml(_html_vide)

            logger.info("=== FIN GÉNÉRATION GRAPHIQUES ===")

        except Exception as e:
            logger.error("Erreur generation graphiques : %s", e, exc_info=True)
            _html_err = (
                "<html><body style='text-align:center;padding-top:150px;"
                "color:#F44336;font-family:sans-serif;'>"
                f"<h3>Erreur graphique</h3><p>{e}</p></body></html>"
            )
            self.chart_ca.setHtml(_html_err)
            self.chart_produits.setHtml(_html_err)

    # ------------------------------------------------------------------ #
    #                         Exports                                     #
    # ------------------------------------------------------------------ #

    def _exporter_csv(self):
        """Exporte les statistiques de la période en CSV."""
        import csv
        from PySide6.QtWidgets import QFileDialog

        date_debut, date_fin = self._obtenir_dates_periode()
        donnees = self.viewmodel.charger_statistiques(date_debut, date_fin)
        if not donnees:
            QMessageBox.warning(self, "Erreur", "Aucune donnee a exporter.")
            return

        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter en CSV",
            f"statistiques_{date_debut}_{date_fin}.csv",
            "CSV (*.csv)",
        )
        if not dest:
            return

        try:
            with open(dest, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")

                # KPIs
                writer.writerow(["=== KPIs ==="])
                kpis = donnees["kpis"]
                writer.writerow(["Chiffre d'affaires", f"{kpis['ca_total']:.2f}"])
                writer.writerow(["Nombre de ventes", kpis["nb_ventes"]])
                writer.writerow(["Clients actifs", kpis["clients_actifs"]])
                writer.writerow(["Panier moyen", f"{kpis['panier_moyen']:.2f}"])
                writer.writerow([])

                # Ventes détaillées
                writer.writerow(["=== Ventes ==="])
                writer.writerow(["Date", "Client", "Prix total"])
                for v in donnees.get("ventes", []):
                    writer.writerow(
                        [
                            str(v.get("date_vente", ""))[:10],
                            v.get("client_nom", ""),
                            f"{v.get('prix_total', 0):.2f}",
                        ]
                    )
                writer.writerow([])

                # Top clients
                writer.writerow(["=== Top Clients ==="])
                writer.writerow(["Nom", "CA Total"])
                for c in donnees.get("top_clients", []):
                    writer.writerow([c.get("nom", ""), f"{c.get('ca', 0):.2f}"])
                writer.writerow([])

                # Top produits
                writer.writerow(["=== Top Produits ==="])
                writer.writerow(["Produit", "CA Total"])
                for p in donnees.get("top_produits", []):
                    writer.writerow([p.get("nom", ""), f"{p.get('ca', 0):.2f}"])

            QMessageBox.information(self, "Succes", f"CSV exporte vers :\n{dest}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export : {e}")

    def _exporter_pdf(self):
        """Exporte les statistiques en PDF (capture de la page)."""
        from PySide6.QtWidgets import QFileDialog

        date_debut, date_fin = self._obtenir_dates_periode()
        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter en PDF",
            f"statistiques_{date_debut}_{date_fin}.pdf",
            "PDF (*.pdf)",
        )
        if not dest:
            return

        try:
            from PySide6.QtGui import QPdfWriter, QPainter
            from PySide6.QtCore import QMarginsF

            writer = QPdfWriter(dest)
            writer.setPageMargins(QMarginsF(20, 20, 20, 20))
            painter = QPainter(writer)

            # Rendre le widget dans le PDF
            self.render(painter)
            painter.end()

            QMessageBox.information(self, "Succes", f"PDF exporte vers :\n{dest}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export PDF : {e}")
