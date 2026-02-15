"""
Fenêtre principale de l'application Nexa.

Ce module contient la classe MainWindow qui gère la fenêtre principale,
la barre latérale de navigation, le système de verrouillage patron/vendeur
et la gestion des pages via un QStackedWidget.
"""

import platform
import sys

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QScreen
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from models.database import get_db
from utils.auth import (
    hasher_mot_de_passe, verifier_mot_de_passe,
    mot_de_passe_existe, mot_de_passe_actif,
)
from utils.validators import valider_mot_de_passe


# ============================================================================
# Feuille de style globale de l'application
# ============================================================================

_STYLESHEET = """
QMainWindow {
    background-color: #FFFFFF;
}

/* Barre latérale */
#sidebar {
    background-color: #F5F5F5;
    border-right: 1px solid #E0E0E0;
}

/* Boutons de navigation */
.nav-button {
    text-align: left;
    padding: 12px 20px;
    border: none;
    background: transparent;
    font-size: 13pt;
    color: #333333;
    border-left: 4px solid transparent;
}
.nav-button:hover {
    background-color: #E8E8E8;
}
.nav-button-active {
    background-color: #E3F2FD;
    border-left: 4px solid #2196F3;
    color: #2196F3;
    font-weight: bold;
}
.nav-button-locked {
    color: #999999;
}

/* Bouton de verrouillage */
#lock-button {
    border: none;
    padding: 8px;
    border-radius: 5px;
    font-size: 16pt;
}

/* Champs de saisie généraux */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {
    height: 35px;
    border: 1px solid #E0E0E0;
    border-radius: 5px;
    padding: 5px 10px;
    font-size: 12pt;
    background-color: #FFFFFF;
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus {
    border: 1px solid #2196F3;
}

/* Boutons */
QPushButton {
    height: 40px;
    border-radius: 5px;
    padding: 10px 20px;
    font-size: 12pt;
    border: none;
}
.btn-primary {
    background-color: #2196F3;
    color: white;
}
.btn-primary:hover {
    background-color: #1976D2;
}
.btn-success {
    background-color: #4CAF50;
    color: white;
}
.btn-success:hover {
    background-color: #388E3C;
}
.btn-danger {
    background-color: #F44336;
    color: white;
}
.btn-secondary {
    background-color: #9E9E9E;
    color: white;
}
.btn-secondary:hover {
    background-color: #757575;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 15px;
    margin-top: 10px;
    font-size: 13pt;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 5px;
}

/* Tableaux */
QTableWidget {
    border: 1px solid #E0E0E0;
    border-radius: 5px;
    gridline-color: #F0F0F0;
}
QHeaderView::section {
    background-color: #F5F5F5;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #E0E0E0;
    font-weight: bold;
}

/* Barre de défilement verticale */
QScrollBar:vertical {
    width: 8px;
    background: transparent;
}
QScrollBar::handle:vertical {
    background: #CCCCCC;
    border-radius: 4px;
}
"""


# ============================================================================
# Définition des éléments de navigation
# ============================================================================

_NAV_ITEMS = [
    # --- Section Vendeur (toujours visible) ---
    {"name": "Client",               "icon_text": "\U0001F4CB", "locked": False},
    {"name": "Vente",                "icon_text": "\U0001F6D2", "locked": False},
    {"name": "Recherche",            "icon_text": "\U0001F50D", "locked": False},
    {"name": "Rechercher un code",   "icon_text": "\U0001F39F", "locked": False},
    {"name": "Aide",                 "icon_text": "\u2753",     "locked": False, "hidden": True},
    # --- Section Patron (visible uniquement si d\u00e9verrouill\u00e9) ---
    {"name": "Emailing",             "icon_text": "\u2709\uFE0F",  "locked": True},
    {"name": "Bo\u00eete de r\u00e9ception", "icon_text": "\U0001F4EC", "locked": True},
    {"name": "Statistiques",         "icon_text": "\U0001F4CA", "locked": True},
    {"name": "Mails enregistr\u00e9s", "icon_text": "\U0001F4BE", "locked": True},
    {"name": "Historique",           "icon_text": "\U0001F4C5", "locked": True},
    {"name": "Calendrier",           "icon_text": "\U0001F5D3\uFE0F", "locked": True},
    {"name": "Produits",             "icon_text": "\U0001F4E6", "locked": True},
    {"name": "Codes promo",          "icon_text": "\U0001F3AB", "locked": True},
    {"name": "Param\u00e8tres",      "icon_text": "\u2699\uFE0F",  "locked": True, "hidden": True},
]


# ============================================================================
# Classe principale : MainWindow
# ============================================================================

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application Nexa.

    Gère la barre latérale de navigation, le système de verrouillage
    patron/vendeur et l'affichage des pages via un QStackedWidget.
    """

    def __init__(self) -> None:
        """Initialise la fenêtre principale et tous ses composants."""
        super().__init__()

        # --- État interne ---
        self._mode_patron: bool = False       # False = mode vendeur (verrouillé)
        self._index_actif: int = 0            # Index de la page active
        self._boutons_nav: list[QPushButton] = []  # Références aux boutons de navigation

        # --- Configuration de la fenêtre ---
        self.setWindowTitle("Nexa - Gestion de Client\u00e8le")
        self.setMinimumSize(1200, 800)

        # --- Configuration de la police système ---
        self._configurer_police()

        # --- Application de la feuille de style ---
        self.setStyleSheet(_STYLESHEET)

        # --- Construction de l'interface ---
        self._construire_interface()

        # --- Centrer la fenêtre sur l'écran ---
        self._centrer_fenetre()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------

    def _configurer_police(self) -> None:
        """Configure la police système selon la plateforme."""
        systeme = platform.system()
        if systeme == "Windows":
            nom_police = "Segoe UI"
        elif systeme == "Darwin":
            nom_police = ".AppleSystemUIFont"
        elif systeme == "Linux":
            nom_police = "Ubuntu"
        else:
            nom_police = "Arial"

        police = QFont(nom_police, 12)
        QApplication.instance().setFont(police)

    def _construire_interface(self) -> None:
        """Construit le layout principal avec la sidebar et le contenu."""
        # Widget central
        widget_central = QWidget()
        self.setCentralWidget(widget_central)

        # Layout principal horizontal : sidebar | contenu
        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # --- Barre latérale (gauche) ---
        self._sidebar = self._creer_sidebar()
        layout_principal.addWidget(self._sidebar)

        # --- Panneau droit (entête + pages) ---
        panneau_droit = QWidget()
        layout_droit = QVBoxLayout(panneau_droit)
        layout_droit.setContentsMargins(0, 0, 0, 0)
        layout_droit.setSpacing(0)

        # Barre d'en-tête
        self._barre_entete = self._creer_barre_entete()
        layout_droit.addWidget(self._barre_entete)

        # QStackedWidget pour les pages
        self._pile_pages = QStackedWidget()
        layout_droit.addWidget(self._pile_pages)

        # Remplir avec 11 pages placeholders
        for i, item in enumerate(_NAV_ITEMS):
            label_placeholder = QLabel(f"Page : {item['name']}")
            label_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label_placeholder.setStyleSheet("font-size: 18pt; color: #999999;")
            self._pile_pages.addWidget(label_placeholder)

        layout_principal.addWidget(panneau_droit)

        # --- Sélectionner la première page ---
        self._changer_page(0)

    # ------------------------------------------------------------------
    # Barre latérale (sidebar)
    # ------------------------------------------------------------------

    def _creer_sidebar(self) -> QFrame:
        """Crée et retourne la barre latérale de navigation.

        Returns:
            Le QFrame contenant le menu de navigation.
        """
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Titre de l'application ---
        label_titre = QLabel("Nexa")
        label_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_titre.setStyleSheet(
            "font-size: 20pt; font-weight: bold; padding: 20px 0 5px 0; color: #2196F3;"
        )
        layout.addWidget(label_titre)

        # --- Sous-titre : nom du commerce ---
        nom_commerce = self._obtenir_nom_commerce()
        self._label_commerce = QLabel(nom_commerce)
        self._label_commerce.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label_commerce.setStyleSheet(
            "font-size: 11pt; color: #777777; padding: 0 0 15px 0;"
        )
        layout.addWidget(self._label_commerce)

        # --- Séparateur ---
        separateur = QFrame()
        separateur.setFrameShape(QFrame.Shape.HLine)
        separateur.setStyleSheet("background-color: #E0E0E0; max-height: 1px;")
        layout.addWidget(separateur)

        # --- Section Vendeur ---
        self._label_section_vendeur = QLabel("  VENDEUR")
        self._label_section_vendeur.setStyleSheet(
            "font-size: 9pt; font-weight: bold; color: #999999; "
            "padding: 12px 20px 4px 20px; letter-spacing: 1px;"
        )
        layout.addWidget(self._label_section_vendeur)

        # --- Boutons de navigation ---
        self._boutons_nav = []
        self._label_section_patron = None
        for i, item in enumerate(_NAV_ITEMS):
            # Ajouter le label "PATRON" avant le premier item verrouill\u00e9
            if item["locked"] and self._label_section_patron is None:
                self._label_section_patron = QLabel("  PATRON")
                self._label_section_patron.setStyleSheet(
                    "font-size: 9pt; font-weight: bold; color: #999999; "
                    "padding: 12px 20px 4px 20px; letter-spacing: 1px;"
                )
                layout.addWidget(self._label_section_patron)

            bouton = QPushButton(f"  {item['icon_text']}   {item['name']}")
            bouton.setFixedHeight(50)
            bouton.setCursor(Qt.CursorShape.PointingHandCursor)
            bouton.setProperty("class", "nav-button")

            # Connecter le clic au changement de page (capture de l'index)
            bouton.clicked.connect(lambda checked=False, idx=i: self._changer_page(idx))

            # Masquer les items avec "hidden"
            if item.get("hidden"):
                bouton.setVisible(False)

            self._boutons_nav.append(bouton)
            layout.addWidget(bouton)

        # --- Espace flexible ---
        layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # --- Boutons ronds Aide et Parametres (mode patron) ---
        ronds_layout = QHBoxLayout()
        ronds_layout.setSpacing(10)
        ronds_layout.setContentsMargins(20, 10, 20, 5)

        self._btn_rond_aide = QPushButton("?")
        self._btn_rond_aide.setFixedSize(50, 50)
        self._btn_rond_aide.setStyleSheet(
            "QPushButton {"
            "    background-color: #FFC107; color: white; border: none;"
            "    border-radius: 25px; font-size: 20pt; font-weight: bold;"
            "}"
            "QPushButton:hover { background-color: #FFA000; }"
        )
        self._btn_rond_aide.setToolTip("Centre d'aide")
        self._btn_rond_aide.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_rond_aide.clicked.connect(lambda: self._changer_page(4))
        self._btn_rond_aide.hide()
        ronds_layout.addWidget(self._btn_rond_aide)

        self._btn_rond_params = QPushButton("\u2699")
        self._btn_rond_params.setFixedSize(50, 50)
        self._btn_rond_params.setStyleSheet(
            "QPushButton {"
            "    background-color: #607D8B; color: white; border: none;"
            "    border-radius: 25px; font-size: 20pt; font-weight: bold;"
            "}"
            "QPushButton:hover { background-color: #455A64; }"
        )
        self._btn_rond_params.setToolTip("Parametres")
        self._btn_rond_params.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_rond_params.clicked.connect(self._afficher_parametres)
        self._btn_rond_params.hide()
        ronds_layout.addWidget(self._btn_rond_params)

        ronds_layout.addStretch()
        layout.addLayout(ronds_layout)

        return sidebar

    def _obtenir_nom_commerce(self) -> str:
        """Récupère le nom du commerce depuis la base de données.

        Returns:
            Le nom de l'entreprise, ou 'Mon Commerce' par défaut.
        """
        try:
            db = get_db()
            resultat = db.fetchone(
                "SELECT valeur FROM parametres WHERE cle = 'nom_entreprise'"
            )
            if resultat and resultat["valeur"]:
                return resultat["valeur"]
        except Exception:
            pass
        return "Mon Commerce"

    def actualiser_nom_entreprise(self):
        """Actualise le nom de l'entreprise dans la sidebar."""
        nom = self._obtenir_nom_commerce()
        self._label_commerce.setText(nom)

    # ------------------------------------------------------------------
    # Barre d'en-tête
    # ------------------------------------------------------------------

    def _creer_barre_entete(self) -> QFrame:
        """Crée et retourne la barre d'en-tête avec le titre et le bouton de verrouillage.

        Returns:
            Le QFrame contenant la barre d'en-tête.
        """
        barre = QFrame()
        barre.setFixedHeight(60)
        barre.setStyleSheet(
            "background-color: #FFFFFF; border-bottom: 1px solid #E0E0E0;"
        )

        layout = QHBoxLayout(barre)
        layout.setContentsMargins(20, 0, 20, 0)

        # --- Titre de la page courante ---
        self._label_titre_page = QLabel(_NAV_ITEMS[0]["name"])
        self._label_titre_page.setStyleSheet(
            "font-size: 16pt; font-weight: bold; color: #333333; border: none;"
        )
        layout.addWidget(self._label_titre_page)

        # --- Espace flexible ---
        layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        # --- Bouton de verrouillage ---
        self._bouton_verrou = QPushButton("\U0001F512")
        self._bouton_verrou.setObjectName("lock-button")
        self._bouton_verrou.setFixedSize(QSize(45, 45))
        self._bouton_verrou.setCursor(Qt.CursorShape.PointingHandCursor)
        self._bouton_verrou.setToolTip("Cliquez pour d\u00e9verrouiller (mode Patron)")
        self._bouton_verrou.clicked.connect(self._basculer_verrouillage)
        self._maj_style_verrou()
        layout.addWidget(self._bouton_verrou)

        return barre

    def _maj_style_verrou(self) -> None:
        """Met à jour l'apparence du bouton de verrouillage selon le mode."""
        if self._mode_patron:
            # Déverrouillé - vert
            self._bouton_verrou.setText("\U0001F513")
            self._bouton_verrou.setStyleSheet(
                "#lock-button { background-color: #4CAF50; border: none; "
                "padding: 8px; border-radius: 5px; font-size: 16pt; }"
            )
            self._bouton_verrou.setToolTip("Mode Patron (cliquez pour verrouiller)")
        else:
            # Verrouillé - rouge
            self._bouton_verrou.setText("\U0001F512")
            self._bouton_verrou.setStyleSheet(
                "#lock-button { background-color: #F44336; border: none; "
                "padding: 8px; border-radius: 5px; font-size: 16pt; }"
            )
            self._bouton_verrou.setToolTip("Mode Vendeur (cliquez pour d\u00e9verrouiller)")

    # ------------------------------------------------------------------
    # Navigation entre les pages
    # ------------------------------------------------------------------

    def _changer_page(self, index: int) -> None:
        """Change la page affichée dans le QStackedWidget.

        Si la page est verrouillée et que le mode patron n'est pas actif,
        affiche un placeholder d'accès restreint au lieu de la vraie page.

        Args:
            index: L'index de la page à afficher (0-10).
        """
        if index < 0 or index >= len(_NAV_ITEMS):
            return

        item = _NAV_ITEMS[index]

        # Vérifier si la page est verrouillée en mode vendeur
        if item["locked"] and not self._mode_patron:
            self._afficher_page_verrouillee()
            self._index_actif = index
            self._label_titre_page.setText(item["name"])
            self._mettre_a_jour_sidebar()
            return

        # Changer la page normalement
        self._index_actif = index
        self._pile_pages.setCurrentIndex(index)
        self._label_titre_page.setText(item["name"])
        self._mettre_a_jour_sidebar()

    def _afficher_page_verrouillee(self) -> None:
        """Affiche le placeholder d'accès restreint dans la zone de contenu."""
        # Créer un widget temporaire pour la page verrouillée
        page_verrouillee = QWidget()
        layout = QVBoxLayout(page_verrouillee)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icône de verrou (grande taille)
        label_icone = QLabel("\U0001F512")
        label_icone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_icone.setStyleSheet("font-size: 64pt; color: #CCCCCC; border: none;")
        layout.addWidget(label_icone)

        # Titre
        label_titre = QLabel("Acc\u00e8s restreint")
        label_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_titre.setStyleSheet(
            "font-size: 20pt; font-weight: bold; color: #666666; "
            "margin-top: 15px; border: none;"
        )
        layout.addWidget(label_titre)

        # Message explicatif
        label_message = QLabel(
            "Connectez-vous en mode Patron pour acc\u00e9der \u00e0 cette section."
        )
        label_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_message.setStyleSheet(
            "font-size: 13pt; color: #999999; margin-top: 10px; border: none;"
        )
        layout.addWidget(label_message)

        # Bouton "Se connecter"
        bouton_connexion = QPushButton("Se connecter")
        bouton_connexion.setProperty("class", "btn-primary")
        bouton_connexion.setFixedWidth(200)
        bouton_connexion.setCursor(Qt.CursorShape.PointingHandCursor)
        bouton_connexion.setStyleSheet(
            "background-color: #2196F3; color: white; height: 40px; "
            "border-radius: 5px; font-size: 12pt; margin-top: 20px;"
        )
        bouton_connexion.clicked.connect(self._deverrouiller)
        layout.addWidget(bouton_connexion, alignment=Qt.AlignmentFlag.AlignCenter)

        # Remplacer la page courante dans le stack par la page verrouillée
        # On utilise un index spécial : on ajoute le widget temporairement
        # puis on l'affiche. Il sera nettoyé au prochain changement de page.
        # Supprimer l'ancien widget de page verrouillée s'il existe
        if hasattr(self, "_widget_page_verrouillee") and self._widget_page_verrouillee is not None:
            self._pile_pages.removeWidget(self._widget_page_verrouillee)
            self._widget_page_verrouillee.deleteLater()

        self._widget_page_verrouillee = page_verrouillee
        idx_temp = self._pile_pages.addWidget(page_verrouillee)
        self._pile_pages.setCurrentIndex(idx_temp)

    # ------------------------------------------------------------------
    # Mise à jour visuelle de la sidebar
    # ------------------------------------------------------------------

    def _mettre_a_jour_sidebar(self) -> None:
        """Met \u00e0 jour l'apparence et la visibilit\u00e9 des boutons de navigation.

        En mode vendeur, les onglets patron sont compl\u00e8tement cach\u00e9s.
        En mode patron, tous les onglets sont visibles.
        """
        # Afficher/masquer le label de section Patron
        if self._label_section_patron is not None:
            self._label_section_patron.setVisible(self._mode_patron)

        # Afficher/masquer les boutons ronds Aide/Parametres
        if hasattr(self, '_btn_rond_aide'):
            self._btn_rond_aide.setVisible(self._mode_patron)
        if hasattr(self, '_btn_rond_params'):
            self._btn_rond_params.setVisible(self._mode_patron)

        for i, bouton in enumerate(self._boutons_nav):
            item = _NAV_ITEMS[i]
            est_actif = (i == self._index_actif)
            est_verrouille = item["locked"]
            est_cache = item.get("hidden", False)

            # Items marques hidden restent toujours caches
            if est_cache:
                bouton.setVisible(False)
                continue

            # Cacher compl\u00e8tement les onglets patron en mode vendeur
            if est_verrouille and not self._mode_patron:
                bouton.setVisible(False)
                continue
            else:
                bouton.setVisible(True)

            texte_base = f"  {item['icon_text']}   {item['name']}"
            bouton.setText(texte_base)

            # Appliquer le style selon l'\u00e9tat
            if est_actif:
                bouton.setStyleSheet(
                    "text-align: left; padding: 12px 20px; border: none; "
                    "background-color: #E3F2FD; font-size: 13pt; "
                    "border-left: 4px solid #2196F3; color: #2196F3; font-weight: bold;"
                )
            else:
                bouton.setStyleSheet(
                    "text-align: left; padding: 12px 20px; border: none; "
                    "background: transparent; font-size: 13pt; "
                    "color: #333333; border-left: 4px solid transparent;"
                )

    # ------------------------------------------------------------------
    # Système de verrouillage (patron / vendeur)
    # ------------------------------------------------------------------

    def _basculer_verrouillage(self) -> None:
        """Bascule entre le mode patron (déverrouillé) et le mode vendeur (verrouillé)."""
        if self._mode_patron:
            self._verrouiller()
        else:
            self._deverrouiller()

    def _deverrouiller(self) -> None:
        """Affiche le dialogue de saisie du mot de passe avec gestion des tentatives.

        - Apres 3 echecs : affiche l'indice si disponible
        - Apres 5 echecs : propose la reinitialisation par email
        """
        db = get_db()

        if not mot_de_passe_existe(db):
            # Pas de mot de passe configure, deverrouiller directement
            self._mode_patron = True
            self._maj_style_verrou()
            self._mettre_a_jour_sidebar()
            self._changer_page(self._index_actif)
            return

        # Recuperer le nombre de tentatives echouees
        row_tentatives = db.fetchone(
            "SELECT valeur FROM parametres WHERE cle = 'tentatives_echouees'"
        )
        tentatives = int(row_tentatives["valeur"]) if row_tentatives and row_tentatives["valeur"] else 0

        # Recuperer l'indice
        row_indice = db.fetchone(
            "SELECT valeur FROM parametres WHERE cle = 'mot_de_passe_indice'"
        )
        indice = row_indice["valeur"] if row_indice else ""

        # Recuperer l'email de recuperation
        row_email = db.fetchone(
            "SELECT valeur FROM parametres WHERE cle = 'email_recuperation'"
        )
        email_recup = row_email["valeur"] if row_email else ""

        dialogue = QDialog(self)
        dialogue.setWindowTitle("Authentification Patron")
        dialogue.setFixedSize(420, 320)
        dialogue.setStyleSheet("QDialog { background-color: #FFFFFF; }")

        layout = QVBoxLayout(dialogue)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(12)

        label_titre = QLabel("Entrez le mot de passe Patron")
        label_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_titre.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333333;")
        layout.addWidget(label_titre)

        champ_mdp = QLineEdit()
        champ_mdp.setEchoMode(QLineEdit.EchoMode.Password)
        champ_mdp.setPlaceholderText("Mot de passe")
        layout.addWidget(champ_mdp)

        # Label d'erreur
        label_erreur = QLabel("")
        label_erreur.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_erreur.setStyleSheet("color: #F44336; font-size: 11pt;")
        label_erreur.setVisible(False)
        layout.addWidget(label_erreur)

        # Label d'indice (visible apres 3 echecs)
        label_indice = QLabel("")
        label_indice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_indice.setStyleSheet(
            "color: #FF9800; font-size: 11pt; font-style: italic; "
            "background-color: #FFF3E0; padding: 8px; border-radius: 6px;"
        )
        label_indice.setWordWrap(True)
        label_indice.setVisible(False)
        layout.addWidget(label_indice)

        # Afficher l'indice si deja >= 3 tentatives
        if tentatives >= 3 and indice:
            label_indice.setText(f"Indice : {indice}")
            label_indice.setVisible(True)

        # Bouton de recuperation par email (visible apres 5 echecs)
        btn_recuperation = QPushButton("Mot de passe oublie ?")
        btn_recuperation.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_recuperation.setStyleSheet(
            "QPushButton { background: transparent; color: #2196F3; "
            "border: none; font-size: 11pt; text-decoration: underline; }"
            "QPushButton:hover { color: #1565C0; }"
        )
        btn_recuperation.setVisible(tentatives >= 5 and bool(email_recup))
        layout.addWidget(btn_recuperation, alignment=Qt.AlignmentFlag.AlignCenter)

        # Label compteur de tentatives
        label_tentatives = QLabel("")
        label_tentatives.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_tentatives.setStyleSheet("color: #999999; font-size: 10pt;")
        if tentatives > 0:
            label_tentatives.setText(f"{tentatives} tentative(s) echouee(s)")
        layout.addWidget(label_tentatives)

        layout.addStretch()

        boutons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        boutons.button(QDialogButtonBox.StandardButton.Ok).setText("Deverrouiller")
        boutons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        layout.addWidget(boutons)

        def valider() -> None:
            nonlocal tentatives
            mdp = champ_mdp.text().strip()
            if not mdp:
                label_erreur.setText("Veuillez entrer un mot de passe.")
                label_erreur.setVisible(True)
                return

            resultat = db.fetchone(
                "SELECT valeur FROM parametres WHERE cle = 'mot_de_passe_patron'"
            )
            if resultat and resultat["valeur"] and verifier_mot_de_passe(mdp, resultat["valeur"]):
                # Succes - reinitialiser les tentatives
                db.execute(
                    "UPDATE parametres SET valeur = '0' WHERE cle = 'tentatives_echouees'"
                )
                self._mode_patron = True
                self._maj_style_verrou()
                self._mettre_a_jour_sidebar()
                self._changer_page(self._index_actif)
                dialogue.accept()
            else:
                # Echec - incrementer les tentatives
                tentatives += 1
                db.execute(
                    "UPDATE parametres SET valeur = ? WHERE cle = 'tentatives_echouees'",
                    (str(tentatives),),
                )

                label_erreur.setText("Mot de passe incorrect.")
                label_erreur.setVisible(True)
                label_tentatives.setText(f"{tentatives} tentative(s) echouee(s)")

                # Afficher l'indice apres 3 tentatives
                if tentatives >= 3 and indice:
                    label_indice.setText(f"Indice : {indice}")
                    label_indice.setVisible(True)

                # Afficher le bouton recuperation apres 5 tentatives
                if tentatives >= 5 and email_recup:
                    btn_recuperation.setVisible(True)

                champ_mdp.clear()
                champ_mdp.setFocus()

        def demander_recuperation():
            if not email_recup:
                return
            # Masquer l'email partiellement pour la securite
            parts = email_recup.split("@")
            if len(parts) == 2:
                visible = parts[0][:2] + "***"
                email_masque = f"{visible}@{parts[1]}"
            else:
                email_masque = "***"

            QMessageBox.information(
                dialogue,
                "Recuperation du mot de passe",
                f"Un email de recuperation est configure : {email_masque}\n\n"
                "Pour reinitialiser votre mot de passe, utilisez le script :\n"
                "python reset_password.py\n\n"
                "Ce script se trouve a la racine du projet.",
            )

        boutons.accepted.connect(valider)
        boutons.rejected.connect(dialogue.reject)
        champ_mdp.returnPressed.connect(valider)
        btn_recuperation.clicked.connect(demander_recuperation)

        dialogue.exec()

    def _verrouiller(self) -> None:
        """Verrouille l'application en mode vendeur."""
        self._mode_patron = False
        self._maj_style_verrou()
        self._mettre_a_jour_sidebar()

        # Si la page actuelle est verrouill\u00e9e, revenir \u00e0 la premi\u00e8re page vendeur
        if _NAV_ITEMS[self._index_actif]["locked"]:
            self._changer_page(0)

    # ------------------------------------------------------------------
    # Gestion du premier lancement (création du mot de passe)
    # ------------------------------------------------------------------

    def _verifier_premier_lancement(self) -> None:
        """Verifie l'etat du mot de passe au lancement.

        - Premier lancement (pas de mdp) : propose de definir ou ignorer.
        - Mot de passe actif : demarre en mode vendeur (verrouille).
        - Mot de passe inactif : demarre en mode patron (deverrouille).
        """
        db = get_db()

        if not mot_de_passe_existe(db):
            # Premier lancement : proposer de definir un mot de passe
            self._afficher_dialogue_premier_lancement()
        elif mot_de_passe_actif(db):
            # Mot de passe actif : mode vendeur
            self._mode_patron = False
            self._maj_style_verrou()
            self._bouton_verrou.setVisible(True)
            self._mettre_a_jour_sidebar()
        else:
            # Mot de passe inactif : mode patron
            self._mode_patron = True
            self._maj_style_verrou()
            self._bouton_verrou.setVisible(False)
            self._mettre_a_jour_sidebar()

    def _afficher_dialogue_premier_lancement(self) -> None:
        """Dialogue du premier lancement : proposer de definir un mot de passe ou ignorer."""
        dialogue = QDialog(self)
        dialogue.setWindowTitle("Bienvenue dans Nexa !")
        dialogue.setFixedSize(500, 250)
        dialogue.setStyleSheet("QDialog { background-color: #FFFFFF; }")

        layout = QVBoxLayout(dialogue)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        label_titre = QLabel("Bienvenue dans Nexa !")
        label_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_titre.setStyleSheet("font-size: 16pt; font-weight: bold; color: #2196F3;")
        layout.addWidget(label_titre)

        label_instruction = QLabel(
            "Souhaitez-vous proteger l'acces aux sections avancees\n"
            "(statistiques, emailing, parametres...) par un mot de passe ?"
        )
        label_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_instruction.setStyleSheet("font-size: 12pt; color: #666666;")
        label_instruction.setWordWrap(True)
        layout.addWidget(label_instruction)

        layout.addSpacerItem(
            QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        layout_boutons = QHBoxLayout()

        btn_plus_tard = QPushButton("Plus tard")
        btn_plus_tard.setStyleSheet(
            "background-color: #9E9E9E; color: white; height: 40px; "
            "border-radius: 5px; font-size: 12pt; padding: 0 20px;"
        )
        btn_plus_tard.setCursor(Qt.CursorShape.PointingHandCursor)
        layout_boutons.addWidget(btn_plus_tard)

        layout_boutons.addStretch()

        btn_definir = QPushButton("Definir un mot de passe")
        btn_definir.setStyleSheet(
            "background-color: #2196F3; color: white; height: 40px; "
            "border-radius: 5px; font-size: 12pt; padding: 0 20px;"
        )
        btn_definir.setCursor(Qt.CursorShape.PointingHandCursor)
        layout_boutons.addWidget(btn_definir)

        layout.addLayout(layout_boutons)

        def choisir_plus_tard():
            db = get_db()
            db.execute(
                "UPDATE parametres SET valeur = '0' WHERE cle = 'mot_de_passe_actif'"
            )
            self._mode_patron = True
            self._maj_style_verrou()
            self._bouton_verrou.setVisible(False)
            self._mettre_a_jour_sidebar()
            dialogue.accept()

        def choisir_definir():
            dialogue.accept()
            self._afficher_dialogue_creation_mdp()

        btn_plus_tard.clicked.connect(choisir_plus_tard)
        btn_definir.clicked.connect(choisir_definir)

        dialogue.exec()

    def _afficher_dialogue_creation_mdp(self) -> None:
        """Dialogue de creation du mot de passe patron avec indice et email de recuperation."""
        dialogue = QDialog(self)
        dialogue.setWindowTitle("Creation du mot de passe Patron")
        dialogue.setFixedSize(500, 580)
        dialogue.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        dialogue.setWindowFlags(
            dialogue.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint
        )

        layout = QVBoxLayout(dialogue)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(10)

        label_titre = QLabel("Definir le mot de passe Patron")
        label_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_titre.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333333;")
        layout.addWidget(label_titre)

        # Champ mot de passe
        champ_mdp = QLineEdit()
        champ_mdp.setEchoMode(QLineEdit.EchoMode.Password)
        champ_mdp.setPlaceholderText("Entrez votre mot de passe")
        layout.addWidget(champ_mdp)

        # Indicateurs de force du mot de passe
        labels_regles = {}
        regles = [
            ('longueur', "Au moins 8 caracteres"),
            ('majuscule', "Au moins 1 majuscule"),
            ('minuscule', "Au moins 1 minuscule"),
            ('chiffre', "Au moins 1 chiffre"),
            ('special', "Au moins 1 caractere special (!@#$...)"),
        ]
        for cle, texte in regles:
            label = QLabel(f"  \u2717  {texte}")
            label.setStyleSheet("font-size: 10pt; color: #F44336;")
            layout.addWidget(label)
            labels_regles[cle] = label

        # Champ confirmation
        label_confirm_titre = QLabel("Confirmer le mot de passe :")
        label_confirm_titre.setStyleSheet("font-size: 11pt; color: #333333; margin-top: 8px;")
        layout.addWidget(label_confirm_titre)

        champ_confirm = QLineEdit()
        champ_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        champ_confirm.setPlaceholderText("Confirmez votre mot de passe")
        layout.addWidget(champ_confirm)

        # --- Indice (hint) ---
        label_indice_titre = QLabel("Indice (optionnel) :")
        label_indice_titre.setStyleSheet("font-size: 11pt; color: #333333; margin-top: 8px;")
        layout.addWidget(label_indice_titre)

        champ_indice = QLineEdit()
        champ_indice.setPlaceholderText("Un indice pour vous rappeler le mot de passe")
        layout.addWidget(champ_indice)

        # --- Email de recuperation (optionnel) ---
        label_email_titre = QLabel("Email de recuperation (optionnel) :")
        label_email_titre.setStyleSheet("font-size: 11pt; color: #333333; margin-top: 8px;")
        layout.addWidget(label_email_titre)

        champ_email_recup = QLineEdit()
        champ_email_recup.setPlaceholderText("email@exemple.fr")
        layout.addWidget(champ_email_recup)

        # Label d'erreur
        label_erreur = QLabel("")
        label_erreur.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_erreur.setStyleSheet("color: #F44336; font-size: 11pt;")
        label_erreur.setVisible(False)
        layout.addWidget(label_erreur)

        layout.addStretch()

        # Bouton de validation
        bouton_valider = QPushButton("Creer le mot de passe")
        bouton_valider.setStyleSheet(
            "background-color: #2196F3; color: white; height: 40px; "
            "border-radius: 5px; font-size: 12pt;"
        )
        bouton_valider.setCursor(Qt.CursorShape.PointingHandCursor)
        bouton_valider.setEnabled(False)
        layout.addWidget(bouton_valider)

        def on_mdp_change(texte):
            valide, msg, details = valider_mot_de_passe(texte)
            for cle, label in labels_regles.items():
                if details.get(cle):
                    label.setText(f"  \u2713  {dict(regles)[cle]}")
                    label.setStyleSheet("font-size: 10pt; color: #4CAF50;")
                else:
                    label.setText(f"  \u2717  {dict(regles)[cle]}")
                    label.setStyleSheet("font-size: 10pt; color: #F44336;")
            bouton_valider.setEnabled(valide)

        champ_mdp.textChanged.connect(on_mdp_change)

        def valider_creation():
            mdp = champ_mdp.text()
            confirm = champ_confirm.text()

            valide, msg, _ = valider_mot_de_passe(mdp)
            if not valide:
                label_erreur.setText(msg)
                label_erreur.setVisible(True)
                return

            if mdp != confirm:
                label_erreur.setText("Les mots de passe ne correspondent pas.")
                label_erreur.setVisible(True)
                champ_confirm.clear()
                champ_confirm.setFocus()
                return

            hash_mdp = hasher_mot_de_passe(mdp)
            db = get_db()
            db.execute(
                "UPDATE parametres SET valeur = ? WHERE cle = 'mot_de_passe_patron'",
                (hash_mdp,),
            )
            db.execute(
                "UPDATE parametres SET valeur = '1' WHERE cle = 'mot_de_passe_actif'"
            )

            # Sauvegarder l'indice
            indice = champ_indice.text().strip()
            db.execute(
                "UPDATE parametres SET valeur = ? WHERE cle = 'mot_de_passe_indice'",
                (indice,),
            )

            # Sauvegarder l'email de recuperation
            email_recup = champ_email_recup.text().strip()
            db.execute(
                "UPDATE parametres SET valeur = ? WHERE cle = 'email_recuperation'",
                (email_recup,),
            )

            # Reinitialiser le compteur de tentatives
            db.execute(
                "UPDATE parametres SET valeur = '0' WHERE cle = 'tentatives_echouees'"
            )

            self._mode_patron = True
            self._maj_style_verrou()
            self._bouton_verrou.setVisible(True)
            self._mettre_a_jour_sidebar()

            QMessageBox.information(
                self,
                "Mot de passe cree",
                "Le mot de passe Patron a ete cree avec succes.\n"
                "Vous etes maintenant en mode Patron.",
            )
            dialogue.accept()

        bouton_valider.clicked.connect(valider_creation)
        champ_confirm.returnPressed.connect(valider_creation)

        dialogue.exec()

    # ------------------------------------------------------------------
    # Gestion des pages
    # ------------------------------------------------------------------

    def definir_page(self, index: int, widget: QWidget) -> None:
        """Remplace le widget placeholder à l'index donné par un vrai widget de page.

        Args:
            index:  L'index de la page à remplacer (0-10).
            widget: Le widget de page à insérer.
        """
        if index < 0 or index >= self._pile_pages.count():
            return

        # Supprimer l'ancien widget placeholder
        ancien_widget = self._pile_pages.widget(index)
        self._pile_pages.removeWidget(ancien_widget)
        ancien_widget.deleteLater()

        # Insérer le nouveau widget à la même position
        self._pile_pages.insertWidget(index, widget)

        # Si c'est la page active, l'afficher immédiatement
        if index == self._index_actif:
            self._pile_pages.setCurrentIndex(index)

    # ------------------------------------------------------------------
    # Boutons ronds Aide + Parametres (dans la sidebar)
    # ------------------------------------------------------------------

    def _afficher_parametres(self) -> None:
        """Navigue vers l'onglet Parametres."""
        # Index 13 = Parametres
        self._changer_page(13)

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def _centrer_fenetre(self) -> None:
        """Centre la fenêtre sur l'écran principal."""
        ecran = QApplication.primaryScreen()
        if ecran is not None:
            geometrie_ecran = ecran.availableGeometry()
            taille_fenetre = self.frameGeometry()
            centre = geometrie_ecran.center()
            taille_fenetre.moveCenter(centre)
            self.move(taille_fenetre.topLeft())
