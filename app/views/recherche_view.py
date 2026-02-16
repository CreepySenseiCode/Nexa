"""
Vue pour l'onglet Recherche de l'application Nexa.

Ce module fournit la classe RechercheView qui permet de rechercher des clients
par autocomplétion et d'afficher leur profil complet (informations personnelles,
relations, statistiques d'achat, graphiques).
"""

import os
from collections import defaultdict
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QGroupBox,
    QPushButton,
    QScrollArea,
    QFrame,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QDialog,
    QMessageBox,
    QFileDialog,
    QHeaderView,
    QAbstractItemView,
    QSizePolicy,
    QStackedWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QPainter, QPainterPath, QLinearGradient, QColor

from viewmodels.recherche_vm import RechercheViewModel
from viewmodels.produits_vm import ProduitsViewModel
from views.client_card import SearchResultsWidget
from views.fiche_produit_view import FicheProduitView
from views.codes_promo_recherche_view import CodesPromoRechercheView
from utils.styles import style_groupe, style_scroll_area, style_onglet, style_toggle, style_input, style_bouton, Couleurs


class RechercheView(QWidget):
    """Vue de l'onglet Recherche avec toggle 3 modes : Client, Produit, Code Promo."""

    # --- Signaux ---
    demande_modification = Signal(int)

    # Modes du toggle
    MODE_CLIENT = 0
    MODE_PRODUIT = 1
    MODE_CODE_PROMO = 2

    def __init__(self, viewmodel=None):
        super().__init__()

        self.viewmodel = viewmodel if viewmodel is not None else RechercheViewModel()
        self._client_id: int = 0
        self._symbole_monnaie: str = self.viewmodel.obtenir_symbole_monnaie()

        self._construire_ui()
        self._connecter_signaux()

    # ==================================================================
    # Construction de l'interface
    # ==================================================================

    def _construire_ui(self):
        """Construit l'interface complete de l'onglet Recherche."""
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # === BARRE DE TOGGLE ===
        self._barre_toggle = QWidget()
        self._barre_toggle.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        toggle_layout = QHBoxLayout(self._barre_toggle)
        toggle_layout.setContentsMargins(20, 15, 20, 0)
        toggle_layout.setSpacing(10)

        titre_toggle = QLabel("Recherche")
        titre_toggle.setStyleSheet(
            f"font-size: 20pt; font-weight: bold; color: {Couleurs.PRIMAIRE};"
        )
        toggle_layout.addWidget(titre_toggle)
        toggle_layout.addStretch()

        self.btn_mode_client = QPushButton("Client")
        self.btn_mode_client.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_client.clicked.connect(lambda: self._changer_mode(self.MODE_CLIENT))

        self.btn_mode_produit = QPushButton("Produit")
        self.btn_mode_produit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_produit.clicked.connect(lambda: self._changer_mode(self.MODE_PRODUIT))

        self.btn_mode_code = QPushButton("Code Promo")
        self.btn_mode_code.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_code.clicked.connect(lambda: self._changer_mode(self.MODE_CODE_PROMO))

        toggle_layout.addWidget(self.btn_mode_client)
        toggle_layout.addWidget(self.btn_mode_produit)
        toggle_layout.addWidget(self.btn_mode_code)

        layout_principal.addWidget(self._barre_toggle)

        # === STACKED WIDGET ===
        self._pile_modes = QStackedWidget()

        # --- Page 0 : Client ---
        self._page_client = QWidget()
        layout_page_client = QVBoxLayout(self._page_client)
        layout_page_client.setContentsMargins(0, 0, 0, 0)
        layout_page_client.setSpacing(0)

        # Zone recherche client
        self.widget_recherche = QWidget()
        layout_recherche = QVBoxLayout(self.widget_recherche)
        layout_recherche.setContentsMargins(20, 15, 20, 20)
        layout_recherche.setSpacing(15)

        self.input_recherche = QLineEdit()
        self.input_recherche.setPlaceholderText(
            "Nom, prenom, email, telephone..."
        )
        self.input_recherche.setStyleSheet(
            "QLineEdit {"
            "    min-height: 50px; font-size: 14pt; padding: 10px;"
            "    border: 2px solid #9E9E9E; border-radius: 8px;"
            "}"
            "QLineEdit:focus { border: 2px solid #2196F3; }"
        )
        self.input_recherche.setFont(QFont("", 14))
        layout_recherche.addWidget(self.input_recherche)

        self._search_results = SearchResultsWidget()
        self._search_results.setVisible(False)
        layout_recherche.addWidget(self._search_results)

        self._label_placeholder = QLabel(
            "Recherchez et selectionnez un client pour afficher son profil"
        )
        self._label_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label_placeholder.setStyleSheet(
            "font-size: 14pt; color: #999999; padding: 60px;"
        )
        layout_recherche.addWidget(self._label_placeholder)

        layout_recherche.addStretch()
        layout_page_client.addWidget(self.widget_recherche)

        # ============================================================
        # ZONE PROFIL (cachee par defaut)
        # ============================================================
        self.widget_profil = QWidget()
        layout_profil_wrapper = QVBoxLayout(self.widget_profil)
        layout_profil_wrapper.setContentsMargins(20, 10, 20, 10)
        layout_profil_wrapper.setSpacing(10)

        # Bouton fermer (croix rouge)
        btn_fermer_layout = QHBoxLayout()
        self.btn_fermer_profil = QPushButton("\u2190 Retour")
        self.btn_fermer_profil.setFixedSize(120, 40)
        self.btn_fermer_profil.setStyleSheet(
            "QPushButton {"
            "    background-color: #F44336; color: white; border: none;"
            "    border-radius: 8px; font-size: 12pt; font-weight: 600;"
            "}"
            "QPushButton:hover { background-color: #D32F2F; }"
        )
        self.btn_fermer_profil.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fermer_profil.clicked.connect(self._fermer_profil)
        btn_fermer_layout.addWidget(self.btn_fermer_profil)
        btn_fermer_layout.addStretch()
        layout_profil_wrapper.addLayout(btn_fermer_layout)

        # Contenu du profil (scroll)
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setStyleSheet(
            "QScrollArea { border: none; background-color: #F5F5F5; }"
        )

        # Panneau de profil
        self._panneau_profil = QWidget()
        self._layout_profil = QVBoxLayout(self._panneau_profil)
        self._layout_profil.setContentsMargins(10, 10, 10, 10)
        self._layout_profil.setSpacing(15)

        self._scroll_area.setWidget(self._panneau_profil)
        layout_profil_wrapper.addWidget(self._scroll_area)

        self.widget_profil.hide()
        layout_page_client.addWidget(self.widget_profil)

        # Ajouter la page client au stacked widget
        self._pile_modes.addWidget(self._page_client)

        # --- Page 1 : Produit ---
        self._construire_page_produit()

        # --- Page 2 : Code Promo ---
        self._page_code_promo = CodesPromoRechercheView()
        self._pile_modes.addWidget(self._page_code_promo)

        # Ajouter le stacked widget au layout principal
        layout_principal.addWidget(self._pile_modes)

        # Sections du profil client (ajoutees a self._layout_profil)
        self._creer_section_entete()
        self._creer_section_infos()
        self._creer_section_relations()
        self._creer_section_stats()
        self._creer_section_graphiques()
        self._creer_barre_boutons()
        self._layout_profil.addStretch()

        # Initialiser le toggle sur le mode Client
        self._changer_mode(self.MODE_CLIENT)

    # ------------------------------------------------------------------
    # Page Produit
    # ------------------------------------------------------------------

    def _construire_page_produit(self):
        """Construit la page de recherche de produits."""
        self._page_produit = QWidget()
        layout = QVBoxLayout(self._page_produit)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Widget de recherche et liste
        self._widget_liste_produits = QWidget()
        layout_liste = QVBoxLayout(self._widget_liste_produits)
        layout_liste.setContentsMargins(20, 15, 20, 20)
        layout_liste.setSpacing(15)

        self._input_recherche_produit = QLineEdit()
        self._input_recherche_produit.setPlaceholderText(
            "Rechercher un produit par nom..."
        )
        self._input_recherche_produit.setStyleSheet(
            "QLineEdit {"
            "    min-height: 50px; font-size: 14pt; padding: 10px;"
            "    border: 2px solid #9E9E9E; border-radius: 8px;"
            "}"
            "QLineEdit:focus { border: 2px solid #2196F3; }"
        )
        self._input_recherche_produit.setFont(QFont("", 14))
        self._input_recherche_produit.textChanged.connect(self._on_recherche_produit)
        layout_liste.addWidget(self._input_recherche_produit)

        self._table_produits = QTableWidget()
        self._table_produits.setColumnCount(4)
        self._table_produits.setHorizontalHeaderLabels(
            ["Nom", "Categorie", "Prix", "Stock"]
        )
        self._table_produits.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table_produits.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table_produits.verticalHeader().setVisible(False)
        self._table_produits.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._table_produits.horizontalHeader().setStretchLastSection(True)
        self._table_produits.setAlternatingRowColors(True)
        self._table_produits.setStyleSheet(
            "QTableWidget { border: 1px solid #E0E0E0; border-radius: 8px; }"
            "QTableWidget::item { padding: 8px; min-height: 40px; }"
            "QHeaderView::section { background-color: #F5F5F5; padding: 10px;"
            "    font-weight: bold; border: none; border-bottom: 2px solid #E0E0E0; }"
        )
        self._table_produits.doubleClicked.connect(self._on_produit_double_clic)
        layout_liste.addWidget(self._table_produits)

        layout.addWidget(self._widget_liste_produits)

        # Fiche produit (cachee par defaut)
        self._produits_vm = ProduitsViewModel()
        self._fiche_produit = FicheProduitView(viewmodel=self._produits_vm)
        self._fiche_produit.retour_demande.connect(self._retour_liste_produits)
        self._fiche_produit.hide()
        layout.addWidget(self._fiche_produit)

        self._pile_modes.addWidget(self._page_produit)
        self._produits_ids = []

    # ------------------------------------------------------------------
    # Toggle mode
    # ------------------------------------------------------------------

    def _changer_mode(self, mode: int):
        """Change le mode du toggle (Client/Produit/Code Promo)."""
        self._pile_modes.setCurrentIndex(mode)
        boutons = [self.btn_mode_client, self.btn_mode_produit, self.btn_mode_code]
        for i, btn in enumerate(boutons):
            btn.setStyleSheet(style_toggle(i == mode))

        # Rafraichir la table produits quand on passe en mode produit
        if mode == self.MODE_PRODUIT:
            self._rafraichir_table_produits(self._input_recherche_produit.text())

    # ------------------------------------------------------------------
    # Section 2a : En-tête du profil
    # ------------------------------------------------------------------

    def _creer_section_entete(self):
        """Cree la section d'en-tete avec gradient, photo, nom et infos rapides."""
        # --- Carte header avec gradient ---
        self._header_card = QFrame()
        self._header_card.setMinimumHeight(180)
        self._header_card.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            "stop:0 #1565C0, stop:1 #1E88E5); "
            "border-radius: 16px; }"
        )

        layout_header = QHBoxLayout(self._header_card)
        layout_header.setContentsMargins(30, 25, 30, 25)
        layout_header.setSpacing(20)

        # Photo circulaire (100px)
        self._label_photo_profil = QLabel()
        self._label_photo_profil.setFixedSize(100, 100)
        self._label_photo_profil.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label_photo_profil.setStyleSheet(
            "QLabel { background-color: rgba(255,255,255,0.2); border-radius: 50px; "
            "font-size: 40pt; color: white; border: 3px solid rgba(255,255,255,0.5); }"
        )
        self._label_photo_profil.setText("\U0001F464")
        layout_header.addWidget(self._label_photo_profil)

        # Infos textuelles
        layout_texte_header = QVBoxLayout()
        layout_texte_header.setSpacing(6)

        self._label_nom = QLabel()
        self._label_nom.setFont(QFont("", 22, QFont.Weight.Bold))
        self._label_nom.setStyleSheet("color: white; border: none;")
        layout_texte_header.addWidget(self._label_nom)

        self._label_client_depuis = QLabel()
        self._label_client_depuis.setFont(QFont("", 11))
        self._label_client_depuis.setStyleSheet("color: rgba(255,255,255,0.8); border: none;")
        layout_texte_header.addWidget(self._label_client_depuis)

        # Contact rapide (email + telephone)
        self._label_contact_rapide = QLabel()
        self._label_contact_rapide.setFont(QFont("", 11))
        self._label_contact_rapide.setStyleSheet("color: rgba(255,255,255,0.9); border: none;")
        self._label_contact_rapide.setWordWrap(True)
        layout_texte_header.addWidget(self._label_contact_rapide)

        layout_texte_header.addStretch()

        # Completude du profil (mini barre dans le header)
        layout_completude = QHBoxLayout()
        layout_completude.setSpacing(8)

        self._label_completude = QLabel("Profil :")
        self._label_completude.setFont(QFont("", 9))
        self._label_completude.setStyleSheet("color: rgba(255,255,255,0.7); border: none;")
        layout_completude.addWidget(self._label_completude)

        self._barre_completude = QProgressBar()
        self._barre_completude.setFixedHeight(12)
        self._barre_completude.setMaximum(100)
        self._barre_completude.setTextVisible(False)
        self._barre_completude.setStyleSheet(
            "QProgressBar { background-color: rgba(255,255,255,0.2); "
            "border-radius: 6px; border: none; }"
            "QProgressBar::chunk { background-color: #4CAF50; border-radius: 6px; }"
        )
        layout_completude.addWidget(self._barre_completude)

        self._label_pourcent = QLabel("0 %")
        self._label_pourcent.setFont(QFont("", 9, QFont.Weight.Bold))
        self._label_pourcent.setStyleSheet("color: rgba(255,255,255,0.9); border: none;")
        layout_completude.addWidget(self._label_pourcent)

        layout_texte_header.addLayout(layout_completude)
        layout_header.addLayout(layout_texte_header)
        layout_header.addStretch()

        self._layout_profil.addWidget(self._header_card)

    # ------------------------------------------------------------------
    # Section 2b : Informations personnelles + Adresse + Centres d'int\u00e9r\u00eat + Notes
    # ------------------------------------------------------------------

    def _creer_section_infos(self):
        """Cree la section Informations personnelles avec style moderne."""
        self._group_infos = QGroupBox("\U0001F464  Informations personnelles")
        font_section = QFont()
        font_section.setPointSize(13)
        font_section.setWeight(QFont.Weight.DemiBold)
        self._group_infos.setFont(font_section)
        self._group_infos.setStyleSheet(style_groupe())
        self._layout_infos = QGridLayout()
        self._layout_infos.setHorizontalSpacing(25)
        self._layout_infos.setVerticalSpacing(10)
        self._group_infos.setLayout(self._layout_infos)
        self._layout_profil.addWidget(self._group_infos)

        # Section Adresse
        self._group_adresse = QGroupBox("\U0001F3E0  Adresse")
        self._group_adresse.setFont(font_section)
        self._group_adresse.setStyleSheet(style_groupe())
        self._layout_adresse = QVBoxLayout()
        self._group_adresse.setLayout(self._layout_adresse)
        self._layout_profil.addWidget(self._group_adresse)

        # Section Centres d'int\u00e9r\u00eat (tags)
        self._group_interets = QGroupBox("\u2764\ufe0f  Centres d'int\u00e9r\u00eat")
        self._group_interets.setFont(font_section)
        self._group_interets.setStyleSheet(style_groupe())
        self._layout_interets_wrapper = QVBoxLayout()
        self._layout_interets = QHBoxLayout()
        self._layout_interets.setSpacing(8)
        self._layout_interets_wrapper.addLayout(self._layout_interets)
        self._layout_interets_wrapper.addStretch()
        self._group_interets.setLayout(self._layout_interets_wrapper)
        self._group_interets.setVisible(False)
        self._layout_profil.addWidget(self._group_interets)

        # Section Notes
        self._group_notes = QGroupBox("\U0001F4DD  Notes")
        self._group_notes.setFont(font_section)
        self._group_notes.setStyleSheet(style_groupe())
        self._layout_notes = QVBoxLayout()
        self._label_notes = QLabel()
        self._label_notes.setWordWrap(True)
        self._label_notes.setFont(QFont("", 11))
        self._label_notes.setStyleSheet(
            "color: #555555; padding: 10px; line-height: 1.5;"
            "background-color: #FAFAFA; border-radius: 8px; border: none;"
        )
        self._layout_notes.addWidget(self._label_notes)
        self._group_notes.setLayout(self._layout_notes)
        self._group_notes.setVisible(False)
        self._layout_profil.addWidget(self._group_notes)

    # ------------------------------------------------------------------
    # Section 2c : Relations
    # ------------------------------------------------------------------

    def _creer_section_relations(self):
        """Cree la section Relations (conjoint, enfants, parents)."""
        self._group_relations = QGroupBox("\U0001F46A  Relations")
        font_section = QFont()
        font_section.setPointSize(13)
        font_section.setWeight(QFont.Weight.DemiBold)
        self._group_relations.setFont(font_section)
        self._group_relations.setStyleSheet(style_groupe())
        self._layout_relations = QVBoxLayout()
        self._group_relations.setLayout(self._layout_relations)
        self._group_relations.setVisible(False)
        self._layout_profil.addWidget(self._group_relations)

    # ------------------------------------------------------------------
    # Section 2d : Statistiques d'achat
    # ------------------------------------------------------------------

    def _creer_section_stats(self):
        """Cree la section Statistiques d'achat avec style moderne."""
        self._group_stats = QGroupBox("\U0001F4CA  Statistiques d'achat")
        font_section = QFont()
        font_section.setPointSize(13)
        font_section.setWeight(QFont.Weight.DemiBold)
        self._group_stats.setFont(font_section)
        self._group_stats.setStyleSheet(style_groupe())
        self._layout_stats = QGridLayout()
        self._layout_stats.setSpacing(15)
        self._group_stats.setLayout(self._layout_stats)
        self._layout_profil.addWidget(self._group_stats)

    # ------------------------------------------------------------------
    # Section 2e : Graphiques
    # ------------------------------------------------------------------

    def _creer_section_graphiques(self):
        """Cree la section Graphiques avec deux charts Plotly."""
        self._group_graphiques = QGroupBox("\U0001F4C8  Analyse des achats")
        font_section = QFont()
        font_section.setPointSize(13)
        font_section.setWeight(QFont.Weight.DemiBold)
        self._group_graphiques.setFont(font_section)
        self._group_graphiques.setStyleSheet(style_groupe())
        self._layout_graphiques = QHBoxLayout()
        self._layout_graphiques.setSpacing(15)

        # Placeholder initial
        label_graphiques = QLabel("S\u00e9lectionnez un client pour voir les graphiques")
        label_graphiques.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_graphiques.setStyleSheet(
            "color: #999999; font-style: italic; font-size: 12pt; padding: 20px;"
        )
        self._layout_graphiques.addWidget(label_graphiques)

        self._group_graphiques.setLayout(self._layout_graphiques)
        self._layout_profil.addWidget(self._group_graphiques)

    # ------------------------------------------------------------------
    # Graphiques Plotly pour le profil client
    # ------------------------------------------------------------------

    def _make_chart_view(self):
        """Cr\u00e9e un QWebEngineView configur\u00e9 pour les graphiques."""
        from PySide6.QtWebEngineWidgets import QWebEngineView
        view = QWebEngineView()
        view.setMinimumHeight(380)
        view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return view

    def _creer_graphique_depenses(self, client_id: int):
        """Cree le graphique d'evolution des depenses du client (robuste)."""
        try:
            import plotly.graph_objects as go
        except ImportError:
            view = self._make_chart_view()
            view.setHtml("<div style='text-align:center;padding:40px;color:#F44336;'>Plotly non install\u00e9</div>")
            return view

        ventes = self.viewmodel.obtenir_depenses_client(client_id)

        if not ventes:
            view = self._make_chart_view()
            view.setHtml("""
                <div style='text-align:center;padding:60px;font-family:Arial;color:#999;'>
                    <h3>Aucune vente enregistr\u00e9e</h3>
                </div>
            """)
            return view

        depenses_par_mois = defaultdict(float)
        for vente in ventes:
            try:
                date_str = str(vente['date_vente'])
                if ' ' in date_str:
                    date_str = date_str.split(' ')[0]
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                mois = dt.strftime('%Y-%m')
                depenses_par_mois[mois] += vente['prix_total']
            except Exception:
                continue

        if not depenses_par_mois:
            view = self._make_chart_view()
            view.setHtml("<div style='text-align:center;padding:40px;color:#999;'>Aucune donn\u00e9e valide</div>")
            return view

        mois = sorted(depenses_par_mois.keys())
        montants = [depenses_par_mois[m] for m in mois]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=mois, y=montants,
            mode='lines+markers', name='D\u00e9penses',
            line=dict(color='#2196F3', width=3),
            marker=dict(size=10, color='#2196F3'),
            fill='tozeroy', fillcolor='rgba(33, 150, 243, 0.2)',
            hovertemplate='<b>%{x}</b><br>D\u00e9penses: %{y:.2f} \u20ac<extra></extra>',
        ))
        fig.update_layout(
            title=dict(
                text="\u00c9volution des d\u00e9penses",
                font=dict(size=16, color='#1976D2', family='Arial'),
                x=0.5, xanchor='center',
            ),
            xaxis_title="Mois", yaxis_title="Montant (\u20ac)",
            hovermode='x unified', template='plotly_white',
            height=380, margin=dict(l=50, r=50, t=80, b=50),
        )

        from utils.plotly_render import plotly_to_html
        view = self._make_chart_view()
        view.setHtml(plotly_to_html(fig))

        if not hasattr(self, '_charts'):
            self._charts = []
        self._charts.append(view)

        return view

    def _creer_graphique_categories(self, client_id: int):
        """Cree le graphique de repartition par categorie (robuste)."""
        try:
            import plotly.graph_objects as go
        except ImportError:
            view = self._make_chart_view()
            view.setHtml("<div style='text-align:center;padding:40px;color:#F44336;'>Plotly non install\u00e9</div>")
            return view

        categories = self.viewmodel.obtenir_repartition_categories(client_id)

        if not categories:
            view = self._make_chart_view()
            view.setHtml("""
                <div style='text-align:center;padding:60px;font-family:Arial;color:#999;'>
                    <h3>Aucune cat\u00e9gorie</h3>
                </div>
            """)
            return view

        noms = [c['categorie'] for c in categories]
        totaux = [c['total'] for c in categories]

        couleurs = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0', '#00BCD4', '#FFEB3B', '#795548']

        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=noms, values=totaux, hole=0.4,
            marker=dict(colors=couleurs[:len(noms)]),
            textinfo='label+percent', textposition='auto',
            hovertemplate='<b>%{label}</b><br>Montant: %{value:.2f} \u20ac<br>Part: %{percent}<extra></extra>',
        ))
        fig.update_layout(
            title=dict(
                text="R\u00e9partition par cat\u00e9gorie",
                font=dict(size=16, color='#1976D2', family='Arial'),
                x=0.5, xanchor='center',
            ),
            template='plotly_white', height=380,
            margin=dict(l=20, r=20, t=80, b=20),
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05),
        )

        from utils.plotly_render import plotly_to_html
        view = self._make_chart_view()
        view.setHtml(plotly_to_html(fig))

        if not hasattr(self, '_charts'):
            self._charts = []
        self._charts.append(view)

        return view

    def _remplir_graphiques(self, client_id: int):
        """Remplit la section graphiques avec les charts du client."""
        # Vider le layout
        self._vider_layout(self._layout_graphiques)
        # Reset charts references
        self._charts = []

        chart_depenses = self._creer_graphique_depenses(client_id)
        self._layout_graphiques.addWidget(chart_depenses)

        chart_categories = self._creer_graphique_categories(client_id)
        self._layout_graphiques.addWidget(chart_categories)

    # ------------------------------------------------------------------
    # Section 2f : Barre de boutons
    # ------------------------------------------------------------------

    def _creer_barre_boutons(self):
        """Cree la barre de boutons d'actions avec style moderne."""
        layout_boutons = QHBoxLayout()
        layout_boutons.setSpacing(12)

        # Bouton "Modifier le profil"
        self._btn_modifier = QPushButton("  Modifier le profil")
        self._btn_modifier.setFont(QFont("", 11))
        self._btn_modifier.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_modifier.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "padding: 10px 20px; border-radius: 8px; border: none; font-weight: bold; }"
            "QPushButton:hover { background-color: #1976D2; }"
        )
        layout_boutons.addWidget(self._btn_modifier)

        # Bouton "Historique d'achat complet"
        self._btn_historique = QPushButton("  Historique complet")
        self._btn_historique.setFont(QFont("", 11))
        self._btn_historique.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_historique.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "padding: 10px 20px; border-radius: 8px; border: none; font-weight: bold; }"
            "QPushButton:hover { background-color: #388E3C; }"
        )
        layout_boutons.addWidget(self._btn_historique)

        # Bouton "Envoyer un email" (desactive)
        self._btn_email = QPushButton("  Envoyer un email")
        self._btn_email.setFont(QFont("", 11))
        self._btn_email.setEnabled(False)
        self._btn_email.setToolTip("Fonctionnalite a venir")
        self._btn_email.setStyleSheet(
            "QPushButton { background-color: #BDBDBD; color: white; "
            "padding: 10px 20px; border-radius: 8px; border: none; }"
        )
        layout_boutons.addWidget(self._btn_email)

        layout_boutons.addStretch()
        self._layout_profil.addLayout(layout_boutons)

    # ==================================================================
    # Connexion des signaux
    # ==================================================================

    def _connecter_signaux(self):
        """Connecte les signaux de l'interface aux slots correspondants."""
        # Recherche en temps reel pendant la saisie
        self.input_recherche.textChanged.connect(self._on_recherche)

        # Selection d'un client via les cards
        self._search_results.client_selected.connect(self._on_client_selectionne)

        # Boutons d'actions
        self._btn_modifier.clicked.connect(self._modifier_profil)
        self._btn_historique.clicked.connect(self._afficher_historique_complet)

    # ==================================================================
    # Recherche et autocomplétion
    # ==================================================================

    def _on_recherche(self, texte: str):
        """Recherche des clients et affiche les resultats sous forme de cards.

        Args:
            texte: Texte saisi dans le champ de recherche.
        """
        if len(texte) < 2:
            self._search_results.vider()
            self._search_results.setVisible(False)
            return

        resultats = self.viewmodel.rechercher_clients(texte)
        search_terms = texte.split()

        self._search_results.afficher_resultats(resultats, search_terms)
        self._search_results.setVisible(True)

    def _on_client_selectionne(self, client_id: int):
        """Charge le profil du client selectionne via la card cliquee.

        Args:
            client_id: Identifiant du client selectionne.
        """
        # Masquer les resultats et vider la recherche
        self._search_results.setVisible(False)
        self.input_recherche.blockSignals(True)
        self.input_recherche.clear()
        self.input_recherche.blockSignals(False)

        profil = self.viewmodel.charger_profil_client(client_id)
        if profil:
            self.afficher_profil(profil)

    # ==================================================================
    # Affichage du profil
    # ==================================================================

    def afficher_profil(self, profil: dict):
        """Affiche le profil complet du client.

        Remplace le placeholder par le panneau de profil et remplit
        toutes les sections avec les données du client.

        Args:
            profil: Dictionnaire contenant toutes les données du client,
                    ses relations et ses statistiques.
        """
        self._client_id = profil.get("id", 0)

        # Actualiser le symbole monétaire
        self._symbole_monnaie = self.viewmodel.obtenir_symbole_monnaie()

        # --- Remplir l'en-tete ---
        nom = (profil.get("nom") or "").upper()
        prenom = profil.get("prenom") or ""
        self._label_nom.setText(f"{nom} {prenom}")

        # Photo du client dans le header
        self._afficher_photo_profil(profil.get("photo_path", ""))

        # Date de creation du client
        date_creation = profil.get("date_creation") or profil.get("date_ajout") or ""
        if date_creation:
            try:
                dt = datetime.strptime(date_creation, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    dt = datetime.strptime(date_creation, "%Y-%m-%d")
                except ValueError:
                    dt = None
            if dt:
                self._label_client_depuis.setText(
                    f"Client depuis le {dt.strftime('%d/%m/%Y')}"
                )
            else:
                self._label_client_depuis.setText("")
        else:
            self._label_client_depuis.setText("")

        # Contact rapide (email + telephone)
        contacts = []
        email = profil.get("email") or ""
        if email:
            contacts.append(f"Email : {email}")
        telephone = profil.get("telephone") or ""
        if telephone:
            contacts.append(f"Tel : {telephone}")
        self._label_contact_rapide.setText("  |  ".join(contacts) if contacts else "")

        # --- Completude du profil ---
        completude = self._calculer_completude(profil)
        self._barre_completude.setValue(completude)
        self._label_pourcent.setText(f"{completude} %")

        # --- Remplir les informations personnelles ---
        self._remplir_infos(profil)

        # --- Remplir les relations ---
        self._remplir_relations(profil)

        # --- Remplir les statistiques ---
        self._remplir_stats(profil.get("stats") or {})

        # --- Remplir les graphiques ---
        self._remplir_graphiques(self._client_id)

        # --- Afficher le profil en plein ecran ---
        self.widget_recherche.hide()
        self.widget_profil.show()
        self._panneau_profil.setVisible(True)

    def _calculer_completude(self, profil: dict) -> int:
        """Calcule le pourcentage de complétude du profil client.

        Utilise la fonction centralisée pour cohérence avec client_view.

        Args:
            profil: Dictionnaire des données du client.

        Returns:
            Pourcentage de complétude (0-100).
        """
        from utils.profile_completion import calculer_completion
        return calculer_completion(profil)

    def _remplir_infos(self, profil: dict):
        """Remplit les sections Informations, Adresse, Centres d'intérêt et Notes.

        Args:
            profil: Dictionnaire des données du client.
        """
        # Nettoyer les layouts existants
        self._vider_layout(self._layout_infos)
        self._vider_layout(self._layout_adresse)
        self._vider_layout(self._layout_interets)

        # ======== INFORMATIONS PERSONNELLES ========
        champs_perso = [
            ("nom", "Nom"),
            ("prenom", "Prénom"),
            ("date_naissance", "Date de naissance"),
            ("age", "Âge"),
            ("email", "Email"),
            ("telephone", "Téléphone"),
            ("situation_maritale", "Situation maritale"),
            ("profession", "Profession"),
        ]

        ligne = 0
        for cle, label in champs_perso:
            valeur = profil.get(cle)

            if cle == "age" and not valeur:
                date_naissance = profil.get("date_naissance")
                if date_naissance:
                    valeur = self._calculer_age(date_naissance)
                    if valeur is not None:
                        valeur = f"{valeur} ans"

            if cle == "date_naissance" and valeur:
                valeur = self._formater_date(str(valeur))

            if cle == "nom" and valeur:
                valeur = str(valeur).upper()

            if valeur is None or str(valeur).strip() == "":
                continue

            label_champ = QLabel(f"{label} :")
            label_champ.setFont(QFont("", 11, QFont.Weight.Bold))
            label_champ.setStyleSheet("color: #333333; border: none;")
            self._layout_infos.addWidget(label_champ, ligne, 0, Qt.AlignmentFlag.AlignTop)

            label_valeur = QLabel(str(valeur))
            label_valeur.setFont(QFont("", 11))
            label_valeur.setStyleSheet("color: #555555; border: none;")
            label_valeur.setWordWrap(True)
            self._layout_infos.addWidget(label_valeur, ligne, 1, Qt.AlignmentFlag.AlignTop)

            ligne += 1

        # ======== ADRESSE ========
        adresse = profil.get("adresse") or ""
        ville = profil.get("ville") or ""
        code_postal = profil.get("code_postal") or ""

        a_adresse = bool(adresse.strip() or ville.strip() or code_postal.strip())
        self._group_adresse.setVisible(a_adresse)

        if a_adresse:
            parties = []
            if adresse.strip():
                parties.append(adresse.strip())
            ligne_ville = ""
            if code_postal.strip():
                ligne_ville += code_postal.strip()
            if ville.strip():
                ligne_ville += f" {ville.strip()}"
            if ligne_ville:
                parties.append(ligne_ville.strip())

            label_adr = QLabel("\n".join(parties))
            label_adr.setFont(QFont("", 12))
            label_adr.setStyleSheet(
                "color: #444; padding: 10px; background-color: #FAFAFA;"
                "border-radius: 8px; border: none;"
            )
            label_adr.setWordWrap(True)
            self._layout_adresse.addWidget(label_adr)

        # ======== CENTRES D'INTÉRÊT (tags) ========
        centre_interet = profil.get("centre_interet") or ""
        if centre_interet.strip():
            self._group_interets.setVisible(True)
            tags = [t.strip() for t in centre_interet.replace(";", ",").split(",") if t.strip()]

            couleurs_tags = [
                "#2196F3", "#4CAF50", "#FF9800", "#9C27B0",
                "#00BCD4", "#F44336", "#795548", "#607D8B",
            ]

            for i, tag in enumerate(tags):
                couleur = couleurs_tags[i % len(couleurs_tags)]
                label_tag = QLabel(tag)
                label_tag.setFont(QFont("", 10, QFont.Weight.Bold))
                label_tag.setStyleSheet(
                    f"QLabel {{"
                    f"    background-color: {couleur}; color: white;"
                    f"    padding: 6px 14px; border-radius: 14px;"
                    f"    border: none;"
                    f"}}"
                )
                self._layout_interets.addWidget(label_tag)
            self._layout_interets.addStretch()
        else:
            self._group_interets.setVisible(False)

        # ======== NOTES ========
        notes = profil.get("notes_personnalisees") or ""
        if notes.strip():
            self._group_notes.setVisible(True)
            self._label_notes.setText(notes.strip())
        else:
            self._group_notes.setVisible(False)

    def _remplir_relations(self, profil: dict):
        """Remplit la section Relations (conjoint, enfants, parents).

        La section est masquée s'il n'y a aucune relation.

        Args:
            profil: Dictionnaire contenant les clés 'conjoint', 'enfants', 'parents'.
        """
        # Nettoyer le layout existant
        self._vider_layout(self._layout_relations)

        conjoint = profil.get("conjoint")
        enfants = profil.get("enfants") or []
        parents = profil.get("parents") or []

        a_des_relations = bool(conjoint or enfants or parents)
        self._group_relations.setVisible(a_des_relations)

        if not a_des_relations:
            return

        # --- Conjoint ---
        if conjoint:
            label_conjoint = QLabel("Conjoint :")
            label_conjoint.setFont(QFont("", 11, QFont.Weight.Bold))
            label_conjoint.setStyleSheet("color: #333333;")
            self._layout_relations.addWidget(label_conjoint)

            nom_conjoint = f"{(conjoint.get('nom') or '').upper()} {conjoint.get('prenom') or ''}"
            btn_conjoint = QPushButton(nom_conjoint.strip())
            btn_conjoint.setStyleSheet(
                "QPushButton { color: #2196F3; text-decoration: underline; "
                "background: transparent; border: none; text-align: left; "
                "font-size: 11pt; padding: 2px 0; }"
                "QPushButton:hover { color: #1565C0; }"
            )
            btn_conjoint.setCursor(Qt.CursorShape.PointingHandCursor)
            conjoint_id = conjoint.get("id")
            btn_conjoint.clicked.connect(
                lambda checked=False, cid=conjoint_id: self._naviguer_vers_client(cid)
            )
            self._layout_relations.addWidget(btn_conjoint)

        # --- Enfants ---
        if enfants:
            label_enfants = QLabel("Enfants :")
            label_enfants.setFont(QFont("", 11, QFont.Weight.Bold))
            label_enfants.setStyleSheet("color: #333333;")
            self._layout_relations.addWidget(label_enfants)

            for enfant in enfants:
                nom_enfant = f"{(enfant.get('nom') or '').upper()} {enfant.get('prenom') or ''}"
                btn_enfant = QPushButton(nom_enfant.strip())
                btn_enfant.setStyleSheet(
                    "QPushButton { color: #2196F3; text-decoration: underline; "
                    "background: transparent; border: none; text-align: left; "
                    "font-size: 11pt; padding: 2px 0; }"
                    "QPushButton:hover { color: #1565C0; }"
                )
                btn_enfant.setCursor(Qt.CursorShape.PointingHandCursor)
                enfant_id = enfant.get("id")
                btn_enfant.clicked.connect(
                    lambda checked=False, eid=enfant_id: self._naviguer_vers_client(eid)
                )
                self._layout_relations.addWidget(btn_enfant)

        # --- Parents ---
        if parents:
            label_parents = QLabel("Parents :")
            label_parents.setFont(QFont("", 11, QFont.Weight.Bold))
            label_parents.setStyleSheet("color: #333333;")
            self._layout_relations.addWidget(label_parents)

            for parent in parents:
                nom_parent = f"{(parent.get('nom') or '').upper()} {parent.get('prenom') or ''}"
                btn_parent = QPushButton(nom_parent.strip())
                btn_parent.setStyleSheet(
                    "QPushButton { color: #2196F3; text-decoration: underline; "
                    "background: transparent; border: none; text-align: left; "
                    "font-size: 11pt; padding: 2px 0; }"
                    "QPushButton:hover { color: #1565C0; }"
                )
                btn_parent.setCursor(Qt.CursorShape.PointingHandCursor)
                parent_id = parent.get("id")
                btn_parent.clicked.connect(
                    lambda checked=False, pid=parent_id: self._naviguer_vers_client(pid)
                )
                self._layout_relations.addWidget(btn_parent)

    def _remplir_stats(self, stats: dict):
        """Remplit la section Statistiques d'achat avec des cartes visuelles.

        Args:
            stats: Dictionnaire de statistiques retourné par le ViewModel.
        """
        # Nettoyer la grille existante
        self._vider_layout(self._layout_stats)

        nombre_achats = stats.get("nombre_achats", 0)

        if nombre_achats == 0:
            # Aucun achat enregistré
            label_aucun = QLabel("Aucun achat enregistré")
            label_aucun.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label_aucun.setStyleSheet(
                "color: #999999; font-style: italic; font-size: 12pt; padding: 20px;"
            )
            self._layout_stats.addWidget(label_aucun, 0, 0, 1, 3)
            return

        montant_total = stats.get("montant_total", 0.0)
        produit_prefere = stats.get("produit_prefere") or "-"
        categorie_preferee = stats.get("categorie_preferee") or "-"
        dernier_achat = stats.get("dernier_achat") or "-"

        # Formater le dernier achat en format français
        if dernier_achat and dernier_achat != "-":
            dernier_achat = self._formater_date(dernier_achat)

        # Carte 1 : Nombre d'achats
        carte_nombre = self._creer_carte_stat(
            "Nombre d'achats",
            str(nombre_achats),
            "#2196F3",
        )
        self._layout_stats.addWidget(carte_nombre, 0, 0)

        # Carte 2 : Montant total
        carte_montant = self._creer_carte_stat(
            "Montant total",
            f"{montant_total:.2f} {self._symbole_monnaie}",
            "#4CAF50",
        )
        self._layout_stats.addWidget(carte_montant, 0, 1)

        # Carte 3 : Produit préféré
        carte_produit = self._creer_carte_stat(
            "Produit préféré",
            produit_prefere,
            "#333333",
            taille_valeur=14,
        )
        self._layout_stats.addWidget(carte_produit, 0, 2)

        # Carte 4 : Catégorie préférée
        carte_categorie = self._creer_carte_stat(
            "Catégorie préférée",
            categorie_preferee,
            "#333333",
            taille_valeur=14,
        )
        self._layout_stats.addWidget(carte_categorie, 1, 0)

        # Carte 5 : Dernier achat
        carte_dernier = self._creer_carte_stat(
            "Dernier achat",
            dernier_achat,
            "#333333",
            taille_valeur=14,
        )
        self._layout_stats.addWidget(carte_dernier, 1, 1)

    def _creer_carte_stat(
        self,
        titre: str,
        valeur: str,
        couleur: str = "#2196F3",
        taille_valeur: int = 20,
    ) -> QFrame:
        """Crée une carte de statistique stylisée.

        Args:
            titre:          Titre de la statistique (petite police, gris).
            valeur:         Valeur de la statistique (grande police, colorée).
            couleur:        Couleur de la valeur.
            taille_valeur:  Taille de la police de la valeur (défaut 20pt).

        Returns:
            Un QFrame contenant la carte formatée.
        """
        carte = QFrame()
        carte.setStyleSheet(
            """
            QFrame {
                border: 1px solid #E0E0E0;
                border-radius: 10px;
                background-color: #FAFAFA;
                padding: 15px;
            }
            QFrame:hover {
                border: 1px solid #2196F3;
            }
            """
        )

        layout = QVBoxLayout(carte)

        label_titre = QLabel(titre)
        label_titre.setFont(QFont("", 10))
        label_titre.setStyleSheet("color: #666666; border: none;")
        layout.addWidget(label_titre)

        label_valeur = QLabel(valeur)
        label_valeur.setFont(QFont("", taille_valeur, QFont.Weight.Bold))
        label_valeur.setStyleSheet(f"color: {couleur}; border: none;")
        label_valeur.setWordWrap(True)
        layout.addWidget(label_valeur)

        return carte

    # ==================================================================
    # Actions - Produits
    # ==================================================================

    def _on_recherche_produit(self, texte: str):
        """Filtre la liste des produits selon le terme saisi."""
        self._rafraichir_table_produits(texte)

    def _rafraichir_table_produits(self, terme: str = ""):
        """Remplit la table des produits avec les resultats filtres."""
        produits = self.viewmodel.rechercher_produits(terme)
        self._table_produits.setRowCount(len(produits))
        symbole = self._symbole_monnaie

        for i, p in enumerate(produits):
            self._table_produits.setItem(
                i, 0, QTableWidgetItem(p.get('nom', ''))
            )
            self._table_produits.setItem(
                i, 1, QTableWidgetItem(p.get('categorie_nom', 'Sans categorie'))
            )

            item_prix = QTableWidgetItem(f"{p.get('prix', 0):.2f} {symbole}")
            item_prix.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self._table_produits.setItem(i, 2, item_prix)

            stock = p.get('stock', 0) or 0
            item_stock = QTableWidgetItem(str(stock))
            item_stock.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if stock == 0:
                item_stock.setForeground(QColor(Couleurs.DANGER))
            elif stock <= 10:
                item_stock.setForeground(QColor(Couleurs.AVERTISSEMENT))
            self._table_produits.setItem(i, 3, item_stock)

        self._produits_ids = [p.get('id') for p in produits]

    def _on_produit_double_clic(self, index):
        """Ouvre la fiche produit quand on double-clique sur une ligne."""
        row = index.row()
        if 0 <= row < len(self._produits_ids):
            produit_id = self._produits_ids[row]
            if produit_id:
                self._fiche_produit.charger_produit(produit_id)
                self._widget_liste_produits.hide()
                self._fiche_produit.show()

    def _retour_liste_produits(self):
        """Revient a la liste des produits depuis la fiche."""
        self._fiche_produit.hide()
        self._widget_liste_produits.show()

    # ==================================================================
    # Actions - Client
    # ==================================================================

    def _naviguer_vers_client(self, client_id: int):
        """Navigue vers le profil d'un autre client (relation cliquée).

        Charge le profil du client cible et met à jour le champ de recherche.

        Args:
            client_id: Identifiant du client vers lequel naviguer.
        """
        if not client_id:
            return

        profil = self.viewmodel.charger_profil_client(client_id)
        if profil:
            self.afficher_profil(profil)
            # Mettre à jour le champ de recherche avec le nom du client
            nom = (profil.get("nom") or "").upper()
            prenom = profil.get("prenom") or ""
            self.input_recherche.setText(f"{nom} {prenom}")

    def _fermer_profil(self):
        """Ferme le profil et retourne a la recherche."""
        self.widget_profil.hide()
        self.widget_recherche.show()
        self._client_id = 0
        self.input_recherche.setFocus()

    def _modifier_profil(self):
        """Émet le signal pour modifier le client dans l'onglet Client."""
        if self._client_id:
            self.demande_modification.emit(self._client_id)

    def _afficher_historique_complet(self):
        """Ouvre un dialogue avec l'historique d'achat complet du client.

        Affiche un tableau avec toutes les ventes, avec un total en bas,
        un bouton pour exporter en CSV et un bouton pour fermer.
        """
        if not self._client_id:
            return

        ventes = self.viewmodel.obtenir_historique_complet(self._client_id)

        dialog = QDialog(self)
        dialog.setWindowTitle("Historique d'achat complet")
        dialog.setMinimumSize(750, 500)
        layout = QVBoxLayout(dialog)

        # --- Info nombre de ventes ---
        label_info = QLabel(f"{len(ventes)} vente(s) enregistree(s)")
        label_info.setFont(QFont("", 11))
        label_info.setStyleSheet("color: #666666;")
        layout.addWidget(label_info)

        # --- Tableau des ventes ---
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ["Date", "Produit", "Quantite", "Prix unitaire", "Prix total"]
        )
        table.setRowCount(len(ventes))
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setStretchLastSection(True)

        for i, vente in enumerate(ventes):
            date_vente = vente.get("date_vente", "")
            if date_vente:
                date_vente = self._formater_date(date_vente)
            table.setItem(i, 0, QTableWidgetItem(date_vente))

            nom_produit = vente.get("nom_produit", vente.get("produit_nom", vente.get("nom", "")))
            table.setItem(i, 1, QTableWidgetItem(nom_produit))

            quantite = vente.get("quantite", 0)
            item_qte = QTableWidgetItem(str(quantite))
            item_qte.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(i, 2, item_qte)

            prix_unit = vente.get("prix_unitaire", 0)
            item_pu = QTableWidgetItem(f"{prix_unit:.2f} {self._symbole_monnaie}")
            item_pu.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(i, 3, item_pu)

            prix_total = vente.get("prix_total", 0)
            item_pt = QTableWidgetItem(f"{prix_total:.2f} {self._symbole_monnaie}")
            item_pt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(i, 4, item_pt)

        layout.addWidget(table)

        # --- Total général ---
        montant_total = sum(v.get("prix_total", 0) for v in ventes)
        label_total = QLabel(
            f"Total : {montant_total:.2f} {self._symbole_monnaie}"
        )
        label_total.setFont(QFont("", 14, QFont.Weight.Bold))
        label_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(label_total)

        # --- Barre de boutons ---
        layout_boutons = QHBoxLayout()

        btn_csv = QPushButton("Exporter en CSV")
        btn_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_csv.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "padding: 8px 16px; border-radius: 4px; border: none; font-size: 11pt; }"
            "QPushButton:hover { background-color: #388E3C; }"
        )
        btn_csv.clicked.connect(lambda: self._exporter_historique_csv(ventes))

        btn_fermer = QPushButton("Fermer")
        btn_fermer.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_fermer.setStyleSheet(
            "QPushButton { background-color: #9E9E9E; color: white; "
            "padding: 8px 16px; border-radius: 4px; border: none; font-size: 11pt; }"
            "QPushButton:hover { background-color: #757575; }"
        )
        btn_fermer.clicked.connect(dialog.close)

        layout_boutons.addWidget(btn_csv)
        layout_boutons.addStretch()
        layout_boutons.addWidget(btn_fermer)
        layout.addLayout(layout_boutons)

        dialog.exec()

    def _exporter_historique_csv(self, ventes: list):
        """Exporte l'historique d'achat en fichier CSV.

        Args:
            ventes: Liste des ventes a exporter.
        """
        import csv

        chemin, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter l'historique en CSV",
            f"historique_client_{self._client_id}.csv",
            "Fichiers CSV (*.csv)",
        )
        if not chemin:
            return

        try:
            with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Date", "Produit", "Quantite", "Prix unitaire", "Prix total"])
                for vente in ventes:
                    date_v = vente.get("date_vente", "")
                    if date_v:
                        date_v = self._formater_date(date_v)
                    nom = vente.get("nom_produit", vente.get("produit_nom", vente.get("nom", "")))
                    qte = vente.get("quantite", 0)
                    pu = vente.get("prix_unitaire", 0)
                    pt = vente.get("prix_total", 0)
                    writer.writerow([date_v, nom, qte, f"{pu:.2f}", f"{pt:.2f}"])

                montant_total = sum(v.get("prix_total", 0) for v in ventes)
                writer.writerow([])
                writer.writerow(["", "", "", "TOTAL", f"{montant_total:.2f}"])

            QMessageBox.information(
                self, "Export reussi",
                f"L'historique a ete exporte vers :\n{chemin}"
            )
        except Exception as e:
            QMessageBox.warning(
                self, "Erreur d'export",
                f"Impossible d'exporter le fichier :\n{e}"
            )

    # ==================================================================
    # Utilitaires
    # ==================================================================

    def _afficher_photo_profil(self, photo_path: str):
        """Affiche la photo du client en format circulaire dans le header.

        Args:
            photo_path: Chemin vers la photo du client.
        """
        if not photo_path or not os.path.exists(photo_path):
            # Remettre l'emoji par defaut
            self._label_photo_profil.setPixmap(QPixmap())
            self._label_photo_profil.setText("\U0001F464")
            self._label_photo_profil.setStyleSheet(
                "QLabel { background-color: rgba(255,255,255,0.2); border-radius: 50px; "
                "font-size: 40pt; color: white; border: 3px solid rgba(255,255,255,0.5); }"
            )
            return

        pixmap = QPixmap(photo_path)
        if pixmap.isNull():
            return

        taille = 100
        pixmap = pixmap.scaled(
            taille, taille,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        # Rogner au centre
        if pixmap.width() != taille or pixmap.height() != taille:
            x = (pixmap.width() - taille) // 2
            y = (pixmap.height() - taille) // 2
            pixmap = pixmap.copy(x, y, taille, taille)

        # Masque circulaire
        masque = QPixmap(taille, taille)
        masque.fill(Qt.GlobalColor.transparent)

        painter = QPainter(masque)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, taille, taille)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        self._label_photo_profil.setPixmap(masque)
        self._label_photo_profil.setText("")
        self._label_photo_profil.setStyleSheet(
            "QLabel { border-radius: 50px; border: 3px solid rgba(255,255,255,0.8); }"
        )

    def _vider_layout(self, layout):
        """Supprime tous les widgets et sous-layouts d'un layout.

        Args:
            layout: Le QLayout à vider.
        """
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self._vider_layout(item.layout())

    def _formater_date(self, date_str: str) -> str:
        """Formate une date ISO en format français JJ/MM/AAAA.

        Args:
            date_str: Date au format YYYY-MM-DD ou YYYY-MM-DD HH:MM:SS.

        Returns:
            Date formatée en JJ/MM/AAAA, ou la chaîne originale si le
            parsing échoue.
        """
        if not date_str:
            return ""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return dt.strftime("%d/%m/%Y")
            except ValueError:
                return date_str

    def _calculer_age(self, date_naissance: str) -> Optional[int]:
        """Calcule l'âge à partir d'une date de naissance.

        Args:
            date_naissance: Date au format YYYY-MM-DD ou YYYY-MM-DD HH:MM:SS.

        Returns:
            L'âge en années, ou None si le parsing échoue.
        """
        if not date_naissance:
            return None
        try:
            dt = datetime.strptime(date_naissance, "%Y-%m-%d")
        except ValueError:
            try:
                dt = datetime.strptime(date_naissance, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None

        aujourdhui = datetime.today()
        age = aujourdhui.year - dt.year
        # Vérifier si l'anniversaire est déjà passé cette année
        if (aujourdhui.month, aujourdhui.day) < (dt.month, dt.day):
            age -= 1
        return age
