"""Vue detail d'un produit (fiche produit)."""

import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QScrollArea,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from utils.styles import Couleurs, style_scroll_area

logger = logging.getLogger(__name__)


class FicheProduitView(QWidget):
    """Fiche detail d'un produit avec header, description, attributs et stats."""

    retour_demande = Signal()

    def __init__(self, viewmodel=None):
        super().__init__()
        self.viewmodel = viewmodel
        self._construire_ui()

    def _construire_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # Bouton retour
        barre_retour = QHBoxLayout()
        barre_retour.setContentsMargins(20, 10, 20, 0)
        self.btn_retour = QPushButton("\u2190 Retour")
        self.btn_retour.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_retour.setStyleSheet(
            f"QPushButton {{ background: none; border: none; color: {Couleurs.PRIMAIRE}; "
            f"font-size: 12pt; font-weight: 600; padding: 8px 0; }}"
            f"QPushButton:hover {{ color: {Couleurs.PRIMAIRE_FONCE}; }}"
        )
        self.btn_retour.clicked.connect(self.retour_demande.emit)
        barre_retour.addWidget(self.btn_retour)
        barre_retour.addStretch()
        layout_principal.addLayout(barre_retour)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(style_scroll_area())

        self.conteneur = QWidget()
        self.conteneur.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        self.layout_contenu = QVBoxLayout(self.conteneur)
        self.layout_contenu.setSpacing(20)
        self.layout_contenu.setContentsMargins(30, 10, 30, 30)

        # Header produit
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet(
            f"QFrame {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 {Couleurs.PRIMAIRE}, stop:1 {Couleurs.PRIMAIRE_FONCE}); "
            f"border-radius: 16px; padding: 30px; }}"
        )
        header_layout = QVBoxLayout(self.header_frame)

        self.label_nom_produit = QLabel()
        self.label_nom_produit.setStyleSheet(
            "font-size: 22pt; font-weight: bold; color: white; border: none;"
        )
        header_layout.addWidget(self.label_nom_produit)

        header_details = QHBoxLayout()

        self.label_categorie = QLabel()
        self.label_categorie.setStyleSheet(
            "font-size: 12pt; color: rgba(255,255,255,0.85); border: none;"
        )
        header_details.addWidget(self.label_categorie)
        header_details.addStretch()

        self.label_prix = QLabel()
        self.label_prix.setStyleSheet(
            "font-size: 20pt; font-weight: bold; color: white; border: none;"
        )
        header_details.addWidget(self.label_prix)

        header_layout.addLayout(header_details)

        # Stock badge
        self.label_stock = QLabel()
        self.label_stock.setStyleSheet(
            "font-size: 13pt; font-weight: 600; color: white; border: none;"
        )
        header_layout.addWidget(self.label_stock)

        self.layout_contenu.addWidget(self.header_frame)

        # Description
        self.section_description = QFrame()
        self.section_description.setStyleSheet(
            f"QFrame {{ background-color: {Couleurs.FOND_SECTION}; "
            f"border: 2px solid {Couleurs.BORDURE}; border-radius: 12px; padding: 20px; }}"
        )
        desc_layout = QVBoxLayout(self.section_description)
        lbl_desc_titre = QLabel("Description")
        lbl_desc_titre.setStyleSheet(
            f"font-size: 14pt; font-weight: bold; color: {Couleurs.PRIMAIRE}; "
            f"border: none; margin-bottom: 5px;"
        )
        desc_layout.addWidget(lbl_desc_titre)
        self.label_description = QLabel()
        self.label_description.setWordWrap(True)
        self.label_description.setStyleSheet(
            f"font-size: 12pt; color: {Couleurs.TEXTE}; border: none;"
        )
        desc_layout.addWidget(self.label_description)
        self.layout_contenu.addWidget(self.section_description)

        # Attributs
        self.section_attributs = QFrame()
        self.section_attributs.setStyleSheet(
            f"QFrame {{ background-color: {Couleurs.FOND_SECTION}; "
            f"border: 2px solid {Couleurs.BORDURE}; border-radius: 12px; padding: 20px; }}"
        )
        self.attributs_layout = QVBoxLayout(self.section_attributs)
        lbl_attr_titre = QLabel("Caracteristiques")
        lbl_attr_titre.setStyleSheet(
            f"font-size: 14pt; font-weight: bold; color: {Couleurs.PRIMAIRE}; "
            f"border: none; margin-bottom: 5px;"
        )
        self.attributs_layout.addWidget(lbl_attr_titre)
        self.attributs_grid = QGridLayout()
        self.attributs_layout.addLayout(self.attributs_grid)
        self.layout_contenu.addWidget(self.section_attributs)

        # Stats de vente
        self.section_stats = QFrame()
        self.section_stats.setStyleSheet(
            f"QFrame {{ background-color: {Couleurs.FOND_SECTION}; "
            f"border: 2px solid {Couleurs.BORDURE}; border-radius: 12px; padding: 20px; }}"
        )
        stats_layout = QVBoxLayout(self.section_stats)
        lbl_stats_titre = QLabel("Statistiques de vente")
        lbl_stats_titre.setStyleSheet(
            f"font-size: 14pt; font-weight: bold; color: {Couleurs.PRIMAIRE}; "
            f"border: none; margin-bottom: 5px;"
        )
        stats_layout.addWidget(lbl_stats_titre)

        self.stats_grid = QHBoxLayout()
        self.stats_grid.setSpacing(15)

        self.kpi_nb_ventes = self._creer_kpi_card("Ventes", "0", Couleurs.PRIMAIRE)
        self.kpi_total_qte = self._creer_kpi_card("Quantite vendue", "0", Couleurs.SUCCES)
        self.kpi_total_ca = self._creer_kpi_card("CA total", "0.00 EUR", Couleurs.AVERTISSEMENT)

        self.stats_grid.addWidget(self.kpi_nb_ventes[0])
        self.stats_grid.addWidget(self.kpi_total_qte[0])
        self.stats_grid.addWidget(self.kpi_total_ca[0])

        stats_layout.addLayout(self.stats_grid)

        # Graphique de vente
        self.web_chart = None
        try:
            from PySide6.QtWebEngineWidgets import QWebEngineView
            self.web_chart = QWebEngineView()
            self.web_chart.setMinimumHeight(300)
            self.web_chart.setStyleSheet("border: none;")
            stats_layout.addWidget(self.web_chart)
        except ImportError:
            logger.warning("QWebEngineView indisponible, graphique desactive")

        self.layout_contenu.addWidget(self.section_stats)

        # Date de creation
        self.label_date_creation = QLabel()
        self.label_date_creation.setStyleSheet(
            f"font-size: 11pt; color: {Couleurs.TEXTE_TRES_GRIS}; padding: 5px;"
        )
        self.label_date_creation.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.layout_contenu.addWidget(self.label_date_creation)

        self.layout_contenu.addStretch()
        scroll.setWidget(self.conteneur)
        layout_principal.addWidget(scroll)

    def _creer_kpi_card(self, titre: str, valeur: str, couleur: str) -> tuple:
        """Cree une mini carte KPI. Retourne (frame, label_valeur)."""
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: white; border: 2px solid {Couleurs.BORDURE}; "
            f"border-radius: 10px; padding: 15px; }}"
        )
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_titre = QLabel(titre)
        lbl_titre.setStyleSheet(
            f"font-size: 11pt; color: {Couleurs.TEXTE_DESACTIVE}; border: none;"
        )
        lbl_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titre)

        lbl_valeur = QLabel(valeur)
        lbl_valeur.setStyleSheet(
            f"font-size: 20pt; font-weight: bold; color: {couleur}; border: none;"
        )
        lbl_valeur.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_valeur)

        return card, lbl_valeur

    def charger_produit(self, produit_id: int):
        """Charge et affiche les details d'un produit."""
        if not self.viewmodel:
            return

        produit = self.viewmodel.obtenir_produit(produit_id)
        if not produit:
            return

        # Header
        self.label_nom_produit.setText(produit.get('nom', ''))
        self.label_categorie.setText(
            f"Categorie : {produit.get('categorie_nom', 'Sans categorie')}"
        )
        self.label_prix.setText(f"{produit.get('prix', 0):.2f} EUR")

        stock = produit.get('stock', 0) or 0
        if stock > 10:
            stock_text = f"En stock : {stock} unites"
            stock_color = Couleurs.SUCCES
        elif stock > 0:
            stock_text = f"Stock faible : {stock} unites"
            stock_color = Couleurs.AVERTISSEMENT
        else:
            stock_text = "Rupture de stock"
            stock_color = Couleurs.DANGER
        self.label_stock.setText(stock_text)
        self.label_stock.setStyleSheet(
            f"font-size: 13pt; font-weight: 600; color: {stock_color}; "
            f"border: none; background: rgba(255,255,255,0.2); "
            f"border-radius: 6px; padding: 5px 10px;"
        )

        # Description
        desc = produit.get('description', '') or ''
        if desc:
            self.label_description.setText(desc)
            self.section_description.setVisible(True)
        else:
            self.section_description.setVisible(False)

        # Attributs
        self._charger_attributs(produit_id)

        # Stats
        stats = self.viewmodel.obtenir_stats_ventes_produit(produit_id)
        self.kpi_nb_ventes[1].setText(str(stats.get('nb_ventes', 0)))
        self.kpi_total_qte[1].setText(str(stats.get('total_qte', 0)))
        self.kpi_total_ca[1].setText(f"{stats.get('total_ca', 0):.2f} EUR")

        # Graphique
        self._charger_graphique_ventes(produit_id)

        # Date creation
        date_creation = produit.get('date_creation', '')
        if date_creation:
            self.label_date_creation.setText(
                f"Cree le : {str(date_creation)[:10]}"
            )

    def _charger_attributs(self, produit_id: int):
        """Charge les attributs du produit dans la grille."""
        # Vider la grille
        while self.attributs_grid.count():
            item = self.attributs_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        attributs = self.viewmodel.obtenir_attributs_produit(produit_id)

        if not attributs:
            self.section_attributs.setVisible(False)
            return

        self.section_attributs.setVisible(True)
        for i, attr in enumerate(attributs):
            lbl_nom = QLabel(f"{attr.get('nom_attribut', '')} :")
            lbl_nom.setStyleSheet(
                f"font-size: 12pt; font-weight: 600; color: {Couleurs.TEXTE_SECONDAIRE}; border: none;"
            )
            lbl_val = QLabel(attr.get('valeur', '') or '-')
            lbl_val.setStyleSheet(
                f"font-size: 12pt; color: {Couleurs.TEXTE}; border: none;"
            )
            self.attributs_grid.addWidget(lbl_nom, i, 0)
            self.attributs_grid.addWidget(lbl_val, i, 1)

    def _charger_graphique_ventes(self, produit_id: int):
        """Charge le graphique d'evolution des ventes du produit."""
        if not self.web_chart:
            return
        try:
            import plotly.graph_objects as go
            from utils.plotly_render import plotly_to_html

            historique = self.viewmodel.obtenir_historique_ventes_produit(produit_id)
            if not historique:
                self.web_chart.setHtml(
                    "<html><body style='text-align:center;padding-top:80px;"
                    "color:#999;font-family:sans-serif;'>"
                    "<p>Aucune vente enregistree pour ce produit.</p></body></html>"
                )
                return

            jours = [row['jour'] for row in historique]
            qtes = [row['qte'] for row in historique]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=jours, y=qtes, mode='lines+markers',
                name='Quantite vendue',
                line=dict(color=Couleurs.PRIMAIRE, width=3),
                marker=dict(size=8),
            ))
            fig.update_layout(
                title="Evolution des ventes",
                xaxis_title="Date",
                yaxis_title="Quantite",
                template="plotly_white",
                height=280,
                margin=dict(l=40, r=20, t=40, b=40),
            )
            self.web_chart.setHtml(plotly_to_html(fig))
        except ImportError:
            logger.warning("Plotly indisponible pour le graphique produit")
        except Exception:
            logger.exception("Erreur generation graphique produit")
