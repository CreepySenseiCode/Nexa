"""Vue pour l'onglet Statistiques avec donnees reelles et graphiques Plotly."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QComboBox,
    QScrollArea, QGridLayout, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWebEngineWidgets import QWebEngineView
from datetime import datetime, timedelta
from collections import defaultdict

from utils.styles import style_scroll_area, Couleurs


class StatistiquesView(QWidget):
    """Onglet Statistiques avec tableau de bord et donnees reelles."""

    def __init__(self):
        super().__init__()

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
        header = QHBoxLayout()

        titre = QLabel("Statistiques")
        titre.setStyleSheet(
            "font-size: 20pt; font-weight: bold; color: #2196F3;"
        )
        header.addWidget(titre)
        header.addStretch()

        # Selecteur de type de periode
        periode_group = QFrame()
        periode_group.setStyleSheet(
            "QFrame { background-color: white; border: 2px solid #E0E0E0; "
            "border-radius: 10px; padding: 8px; }"
        )

        periode_layout = QHBoxLayout(periode_group)
        periode_layout.setSpacing(8)

        self.combo_periode = QComboBox()
        self.combo_periode.addItems(["Jour", "Semaine", "Mois", "Annee"])
        self.combo_periode.setCurrentIndex(2)  # Mois par defaut
        self.combo_periode.setStyleSheet(
            "QComboBox { min-width: 110px; min-height: 36px; font-size: 12pt; "
            "padding: 5px 10px; border: 2px solid #2196F3; border-radius: 6px; "
            "background-color: white; }"
        )
        periode_layout.addWidget(self.combo_periode)

        # Bouton Precedent
        self.btn_prev = QPushButton("\u25C0")
        self.btn_prev.setFixedSize(36, 36)
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "border: none; border-radius: 18px; font-size: 14pt; font-weight: bold; }"
            "QPushButton:hover { background-color: #1976D2; }"
        )
        periode_layout.addWidget(self.btn_prev)

        # Label periode actuelle
        self.label_periode = QLabel()
        self.label_periode.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.label_periode.setStyleSheet(
            "color: #1976D2; min-width: 200px; border: none;"
        )
        self.label_periode.setAlignment(Qt.AlignmentFlag.AlignCenter)
        periode_layout.addWidget(self.label_periode)

        # Bouton Suivant
        self.btn_next = QPushButton("\u25B6")
        self.btn_next.setFixedSize(36, 36)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "border: none; border-radius: 18px; font-size: 14pt; font-weight: bold; }"
            "QPushButton:hover { background-color: #1976D2; }"
        )
        periode_layout.addWidget(self.btn_next)

        # Bouton Aujourd'hui
        self.btn_today = QPushButton("Aujourd'hui")
        self.btn_today.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_today.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "border: none; border-radius: 6px; padding: 8px 16px; "
            "font-size: 11pt; font-weight: 600; min-height: 36px; }"
            "QPushButton:hover { background-color: #45A049; }"
        )
        periode_layout.addWidget(self.btn_today)

        header.addWidget(periode_group)

        # Bouton Actualiser
        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "border: none; border-radius: 8px; padding: 10px 20px; "
            "font-size: 12pt; font-weight: 600; }"
            "QPushButton:hover { background-color: #1976D2; }"
        )
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        header.addWidget(self.btn_refresh)

        layout_principal.addLayout(header)

        # === CARTES KPI ===
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
            card, label_valeur = self._creer_carte_kpi(
                titre_kpi, valeur, couleur
            )
            self._kpi_labels[titre_kpi] = label_valeur
            kpi_layout.addWidget(card, 0, i)

        layout_principal.addLayout(kpi_layout)

        # === GRAPHIQUES PLOTLY ===
        graphiques_layout = QHBoxLayout()
        graphiques_layout.setSpacing(15)

        self.chart_ca = QWebEngineView()
        self.chart_ca.setMinimumHeight(400)
        graphiques_layout.addWidget(self.chart_ca)

        self.chart_produits = QWebEngineView()
        self.chart_produits.setMinimumHeight(400)
        graphiques_layout.addWidget(self.chart_produits)

        layout_principal.addLayout(graphiques_layout)

        # === SECTION TOP ===
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)

        self._top_clients_frame, self._top_clients_layout = (
            self._creer_section_top("Top 5 Clients")
        )
        top_layout.addWidget(self._top_clients_frame)

        self._top_produits_frame, self._top_produits_layout = (
            self._creer_section_top("Top 5 Produits")
        )
        top_layout.addWidget(self._top_produits_frame)

        layout_principal.addLayout(top_layout)

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
        btn_export_csv.clicked.connect(
            lambda: QMessageBox.information(
                self, "Info", "Export CSV a venir."
            )
        )
        export_layout.addWidget(btn_export_csv)

        btn_export_pdf = QPushButton("Exporter en PDF")
        btn_export_pdf.setStyleSheet(
            "QPushButton { background-color: #F44336; color: white; "
            "border: none; border-radius: 8px; padding: 10px 20px; "
            "font-size: 12pt; font-weight: 600; }"
            "QPushButton:hover { background-color: #D32F2F; }"
        )
        btn_export_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export_pdf.clicked.connect(
            lambda: QMessageBox.information(
                self, "Info", "Export PDF a venir."
            )
        )
        export_layout.addWidget(btn_export_pdf)

        layout_principal.addLayout(export_layout)

        layout_principal.addStretch()

        scroll.setWidget(conteneur)

        layout_self = QVBoxLayout(self)
        layout_self.setContentsMargins(0, 0, 0, 0)
        layout_self.addWidget(scroll)

    def _connecter_signaux(self):
        """Connecte les signaux."""
        self.btn_refresh.clicked.connect(self._charger_stats)
        self.combo_periode.currentIndexChanged.connect(self._on_periode_changed)
        self.btn_prev.clicked.connect(self._periode_precedente)
        self.btn_next.clicked.connect(self._periode_suivante)
        self.btn_today.clicked.connect(self._aller_aujourdhui)

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
            "", "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre",
        ]

        if self.type_periode == "Jour":
            self.label_periode.setText(
                self.date_actuelle.strftime("%d/%m/%Y")
            )
        elif self.type_periode == "Semaine":
            debut = self.date_actuelle - timedelta(
                days=self.date_actuelle.weekday()
            )
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
        label_titre.setStyleSheet(
            "font-size: 11pt; color: #666; border: none;"
        )
        label_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_titre)

        label_valeur = QLabel(valeur)
        label_valeur.setStyleSheet(
            f"font-size: 24pt; font-weight: bold; color: {couleur}; "
            f"border: none;"
        )
        label_valeur.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_valeur)

        return card, label_valeur

    def _creer_section_top(
        self, titre: str
    ) -> tuple[QFrame, QVBoxLayout]:
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
                dernier_jour = d.replace(
                    month=d.month + 1, day=1
                ) - timedelta(days=1)
            date_fin = dernier_jour.strftime("%Y-%m-%d 23:59:59")

        elif self.type_periode == "Annee":
            date_debut = d.replace(
                month=1, day=1
            ).strftime("%Y-%m-%d 00:00:00")
            date_fin = d.replace(
                month=12, day=31
            ).strftime("%Y-%m-%d 23:59:59")

        else:
            date_debut = "2000-01-01 00:00:00"
            date_fin = datetime.now().strftime("%Y-%m-%d 23:59:59")

        return date_debut, date_fin

    def _charger_stats(self):
        """Charge les statistiques reelles depuis la base de donnees."""
        try:
            from models.database import get_db
            db = get_db()

            date_debut, date_fin = self._obtenir_dates_periode()

            # --- KPIs ---
            row = db.fetchone(
                """
                SELECT
                    COUNT(*) AS nb_ventes,
                    COALESCE(SUM(prix_total), 0) AS ca_total,
                    COUNT(DISTINCT client_id) AS clients_actifs
                FROM ventes
                WHERE date_vente >= ? AND date_vente <= ?
                """,
                (date_debut, date_fin),
            )

            nb_ventes = row['nb_ventes'] if row else 0
            ca_total = row['ca_total'] if row else 0
            clients_actifs = row['clients_actifs'] if row else 0
            panier_moyen = ca_total / nb_ventes if nb_ventes > 0 else 0

            self._kpi_labels["Chiffre d'affaires"].setText(
                f"{ca_total:.2f} EUR"
            )
            self._kpi_labels["Nombre de ventes"].setText(str(nb_ventes))
            self._kpi_labels["Clients actifs"].setText(str(clients_actifs))
            self._kpi_labels["Panier moyen"].setText(
                f"{panier_moyen:.2f} EUR"
            )

            # --- Top 5 Clients ---
            top_clients = db.fetchall(
                """
                SELECT c.nom, c.prenom,
                       SUM(v.prix_total) AS total_ca,
                       COUNT(*) AS nb_achats
                FROM ventes v
                JOIN clients c ON c.id = v.client_id
                WHERE v.date_vente >= ? AND v.date_vente <= ?
                GROUP BY v.client_id
                ORDER BY total_ca DESC
                LIMIT 5
                """,
                (date_debut, date_fin),
            )
            self._maj_section_top(self._top_clients_layout, top_clients, "client")

            # --- Top 5 Produits ---
            top_produits = db.fetchall(
                """
                SELECT p.nom,
                       SUM(v.quantite) AS total_qte,
                       SUM(v.prix_total) AS total_ca
                FROM ventes v
                JOIN produits p ON p.id = v.produit_id
                WHERE v.date_vente >= ? AND v.date_vente <= ?
                GROUP BY v.produit_id
                ORDER BY total_ca DESC
                LIMIT 5
                """,
                (date_debut, date_fin),
            )
            self._maj_section_top(self._top_produits_layout, top_produits, "produit")

            # --- Graphiques Plotly ---
            ventes_list = db.fetchall(
                """
                SELECT date_vente, prix_total, quantite
                FROM ventes
                WHERE date_vente >= ? AND date_vente <= ?
                ORDER BY date_vente
                """,
                (date_debut, date_fin),
            )
            self._generer_graphiques(ventes_list, top_produits)

        except Exception:
            pass

    def _maj_section_top(
        self, layout: QVBoxLayout, items: list[dict], type_item: str
    ):
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
                nom = item.get('nom', '')
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
        try:
            import plotly.graph_objects as go

            # --- Graphique 1 : Evolution du CA ---
            ventes_par_jour = defaultdict(float)
            for vente in ventes:
                date_str = str(vente.get('date_vente', ''))[:10]
                ventes_par_jour[date_str] += vente.get('prix_total', 0)

            dates = sorted(ventes_par_jour.keys())
            montants = [ventes_par_jour[d] for d in dates]

            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=dates,
                y=montants,
                mode='lines+markers',
                name='CA journalier',
                line=dict(color='#2196F3', width=3),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(33, 150, 243, 0.1)',
            ))
            fig1.update_layout(
                title="Evolution du chiffre d'affaires",
                xaxis_title="Date",
                yaxis_title="CA (EUR)",
                hovermode='x unified',
                template='plotly_white',
                height=380,
                margin=dict(l=50, r=20, t=50, b=40),
            )

            from utils.plotly_render import plotly_to_html
            self.chart_ca.setHtml(plotly_to_html(fig1))

            # --- Graphique 2 : Top produits ---
            if top_produits:
                noms = [p.get('nom', '') for p in top_produits]
                ca = [p.get('total_ca', 0) for p in top_produits]

                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=ca,
                    y=noms,
                    orientation='h',
                    marker=dict(color='#4CAF50'),
                ))
                fig2.update_layout(
                    title="Top produits par CA",
                    xaxis_title="CA (EUR)",
                    template='plotly_white',
                    height=380,
                    margin=dict(l=120, r=20, t=50, b=40),
                )
                self.chart_produits.setHtml(plotly_to_html(fig2))
            else:
                self.chart_produits.setHtml(
                    "<html><body style='text-align:center;padding-top:150px;"
                    "color:#999;font-family:sans-serif;'>"
                    "<h3>Aucune donnee disponible</h3></body></html>"
                )

        except ImportError:
            self.chart_ca.setHtml(
                "<html><body style='text-align:center;padding-top:150px;"
                "color:#999;font-family:sans-serif;'>"
                "<h3>Plotly non installe</h3>"
                "<p>pip install plotly</p></body></html>"
            )
            self.chart_produits.setHtml(
                "<html><body style='text-align:center;padding-top:150px;"
                "color:#999;font-family:sans-serif;'>"
                "<h3>Plotly non installe</h3></body></html>"
            )
