"""Vue pour la recherche et verification des codes promotionnels (mode Vendeur).

Ce module fournit la classe CodesPromoRechercheView qui permet au vendeur
de verifier la validite d'un code promo et d'afficher ses details avec
des boxes colorees selon le statut (valide, expire, invalide).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from viewmodels.codes_promo_vm import CodesPromoViewModel


class CodesPromoRechercheView(QWidget):
    """Vue pour la verification des codes de reduction (Vendeur)."""

    def __init__(self, viewmodel=None):
        super().__init__()

        if viewmodel is None:
            self.viewmodel = CodesPromoViewModel()
        else:
            self.viewmodel = viewmodel

        self._construire_ui()
        self._connecter_signaux()

    # ------------------------------------------------------------------ #
    #                        Construction de l'UI                         #
    # ------------------------------------------------------------------ #

    def _construire_ui(self):
        """Construit l'interface complete."""

        # Conteneur scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #FFFFFF; }")

        conteneur = QWidget()
        conteneur.setStyleSheet("background-color: #FFFFFF;")
        layout_principal = QVBoxLayout(conteneur)
        layout_principal.setSpacing(20)
        layout_principal.setContentsMargins(40, 40, 40, 40)

        # --- Titre ---
        label_titre = QLabel("Verification de code promotionnel")
        font_titre = QFont()
        font_titre.setPointSize(18)
        font_titre.setBold(True)
        label_titre.setFont(font_titre)
        label_titre.setAlignment(Qt.AlignCenter)
        layout_principal.addWidget(label_titre)

        # --- Sous-titre ---
        label_sous_titre = QLabel(
            "Entrez un code promo pour verifier sa validite"
        )
        font_sous_titre = QFont()
        font_sous_titre.setPointSize(12)
        label_sous_titre.setFont(font_sous_titre)
        label_sous_titre.setAlignment(Qt.AlignCenter)
        label_sous_titre.setStyleSheet("color: #757575;")
        layout_principal.addWidget(label_sous_titre)

        layout_principal.addSpacing(10)

        # --- Section de recherche ---
        self._construire_section_recherche(layout_principal)

        layout_principal.addSpacing(10)

        # --- Section de resultat (dynamique) ---
        self._construire_section_resultat(layout_principal)

        layout_principal.addStretch()

        # Finaliser le scroll
        scroll.setWidget(conteneur)
        layout_self = QVBoxLayout(self)
        layout_self.setContentsMargins(0, 0, 0, 0)
        layout_self.addWidget(scroll)

    # ------------------------------------------------------------------ #
    #                     Section : Recherche                             #
    # ------------------------------------------------------------------ #

    def _construire_section_recherche(self, layout_parent):
        """Construit la section de saisie et de verification du code."""

        # Conteneur centre
        widget_recherche = QWidget()
        widget_recherche.setMaximumWidth(500)

        layout_recherche = QVBoxLayout(widget_recherche)
        layout_recherche.setContentsMargins(0, 0, 0, 0)
        layout_recherche.setSpacing(12)

        font_corps = QFont()
        font_corps.setPointSize(13)

        # Label du champ
        label_code = QLabel("Entrer un code promo :")
        label_code.setFont(font_corps)
        layout_recherche.addWidget(label_code)

        # Ligne de saisie + bouton
        layout_saisie = QHBoxLayout()
        layout_saisie.setSpacing(10)

        self.input_code = QLineEdit()
        self.input_code.setFont(font_corps)
        self.input_code.setPlaceholderText("CODE2026")
        self.input_code.setMinimumHeight(42)
        self.input_code.setStyleSheet(
            "QLineEdit { border: 2px solid #E0E0E0; border-radius: 8px; "
            "padding: 8px 14px; background-color: #FAFAFA; }"
            "QLineEdit:focus { border: 2px solid #2196F3; "
            "background-color: #FFFFFF; }"
        )

        self.btn_verifier = QPushButton("Verifier")
        self.btn_verifier.setFont(font_corps)
        self.btn_verifier.setMinimumHeight(42)
        self.btn_verifier.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_verifier.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "padding: 8px 28px; border-radius: 8px; border: none; "
            "font-weight: bold; }"
            "QPushButton:hover { background-color: #1976D2; }"
            "QPushButton:pressed { background-color: #0D47A1; }"
        )

        layout_saisie.addWidget(self.input_code)
        layout_saisie.addWidget(self.btn_verifier)

        layout_recherche.addLayout(layout_saisie)

        # Centrer horizontalement
        layout_centre = QHBoxLayout()
        layout_centre.addStretch()
        layout_centre.addWidget(widget_recherche)
        layout_centre.addStretch()

        layout_parent.addLayout(layout_centre)

    # ------------------------------------------------------------------ #
    #                     Section : Resultat (dynamique)                  #
    # ------------------------------------------------------------------ #

    def _construire_section_resultat(self, layout_parent):
        """Construit le conteneur dynamique pour les resultats."""

        self.result_widget = QWidget()
        self.result_widget.setMaximumWidth(500)
        self.result_layout = QVBoxLayout(self.result_widget)
        self.result_layout.setContentsMargins(0, 0, 0, 0)
        self.result_widget.setVisible(False)

        layout_centre = QHBoxLayout()
        layout_centre.addStretch()
        layout_centre.addWidget(self.result_widget)
        layout_centre.addStretch()

        layout_parent.addLayout(layout_centre)

    # ------------------------------------------------------------------ #
    #                        Connexion des signaux                        #
    # ------------------------------------------------------------------ #

    def _connecter_signaux(self):
        """Connecte les signaux aux slots."""

        # Forcer le code en majuscules
        self.input_code.textChanged.connect(self._on_code_change)

        # Bouton de verification
        self.btn_verifier.clicked.connect(self._verifier_code)

        # Permettre la verification avec la touche Entree
        self.input_code.returnPressed.connect(self._verifier_code)

    # ------------------------------------------------------------------ #
    #                           Callbacks                                 #
    # ------------------------------------------------------------------ #

    def _on_code_change(self, texte: str):
        """Force le code en majuscules pendant la saisie."""
        self.input_code.blockSignals(True)
        pos = self.input_code.cursorPosition()
        self.input_code.setText(texte.upper())
        self.input_code.setCursorPosition(pos)
        self.input_code.blockSignals(False)

    def _verifier_code(self):
        """Verifie le code saisi et affiche le resultat avec box coloree selon le type d'erreur."""
        code = self.input_code.text().strip()

        if not code:
            self.result_widget.setVisible(False)
            return

        resultat, message, type_erreur = self.viewmodel.verifier_code(code)

        # Vider le layout actuel
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Creer la box coloree
        result_frame = QFrame()
        result_frame.setFrameShape(QFrame.Shape.Box)

        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(24, 20, 24, 20)
        frame_layout.setSpacing(10)

        # Titre
        titre_label = QLabel()
        titre_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_titre = QFont()
        font_titre.setPointSize(16)
        font_titre.setBold(True)
        titre_label.setFont(font_titre)

        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_msg = QFont()
        font_msg.setPointSize(12)
        message_label.setFont(font_msg)

        if type_erreur is None:
            # Code valide - BLEU
            code_str = resultat.get('code', '')
            titre_label.setText(f"\u2705 Code VALIDE : {code_str}")
            titre_label.setStyleSheet("color: #1976D2; border: none;")
            result_frame.setStyleSheet(
                "QFrame { background-color: #E3F2FD; border: 3px solid #2196F3; "
                "border-radius: 15px; padding: 20px; }"
            )

            # Pourcentage en gros
            pourcentage = resultat.get('pourcentage', 0)
            reduction_label = QLabel(f"-{pourcentage:.0f} %")
            font_reduction = QFont()
            font_reduction.setPointSize(28)
            font_reduction.setBold(True)
            reduction_label.setFont(font_reduction)
            reduction_label.setStyleSheet("color: #1565C0; border: none;")
            reduction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            frame_layout.addWidget(titre_label)
            frame_layout.addWidget(reduction_label)

            # Separateur
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(
                "background-color: #90CAF9; border: none; max-height: 1px;"
            )
            frame_layout.addWidget(sep)

            # Description
            description = resultat.get('description', '')
            if description:
                desc_label = QLabel(description)
                desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                desc_label.setStyleSheet(
                    "font-size: 12pt; color: #424242; border: none;"
                )
                desc_label.setWordWrap(True)
                frame_layout.addWidget(desc_label)

            # Dates de validite
            date_debut = resultat.get('date_debut', '')
            date_fin = resultat.get('date_fin', 'N/A')
            if date_debut and date_fin:
                dates_label = QLabel(
                    f"Valable du {date_debut} au {date_fin}"
                )
            elif date_fin:
                dates_label = QLabel(f"Valable jusqu'au {date_fin}")
            else:
                dates_label = None

            if dates_label:
                dates_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                dates_label.setStyleSheet(
                    "font-size: 11pt; color: #616161; border: none;"
                )
                frame_layout.addWidget(dates_label)

            # Utilisations
            type_util = resultat.get('type_utilisation', 'illimite')
            utilisations = resultat.get('nombre_utilisations', 0)
            limite = resultat.get('limite_utilisations')

            if type_util == 'limite_globale' and limite:
                restantes = limite - utilisations
                util_text = f"Utilisations restantes : {restantes} / {limite}"
            elif type_util == 'unique_par_client':
                util_text = (
                    f"Unique par client ({utilisations} utilisation(s))"
                )
            else:
                util_text = "Utilisations illimitees"

            util_label = QLabel(util_text)
            util_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            util_label.setStyleSheet(
                "font-size: 11pt; color: #616161; border: none;"
            )
            frame_layout.addWidget(util_label)

        elif type_erreur == "EXPIRE":
            # Code expire - ORANGE
            titre_label.setText("\U0001F7E0 Code EXPIR\u00c9")
            titre_label.setStyleSheet("color: #F57C00; border: none;")
            result_frame.setStyleSheet(
                "QFrame { background-color: #FFF3E0; border: 3px solid #FF9800; "
                "border-radius: 15px; padding: 20px; }"
            )
            message_label.setStyleSheet(
                "font-size: 12pt; color: #F57C00; border: none; padding: 10px;"
            )
            frame_layout.addWidget(titre_label)
            frame_layout.addWidget(message_label)

        elif type_erreur == "EPUISE":
            # Code epuise - ROUGE FONCE
            titre_label.setText("\U0001F534 Code \u00c9PUIS\u00c9")
            titre_label.setStyleSheet("color: #D32F2F; border: none;")
            result_frame.setStyleSheet(
                "QFrame { background-color: #FFEBEE; border: 3px solid #F44336; "
                "border-radius: 15px; padding: 20px; }"
            )
            message_label.setStyleSheet(
                "font-size: 12pt; color: #D32F2F; border: none; padding: 10px;"
            )
            frame_layout.addWidget(titre_label)
            frame_layout.addWidget(message_label)

        elif type_erreur == "INEXISTANT":
            # Code inexistant - ROUGE
            titre_label.setText("\u274C Code INEXISTANT")
            titre_label.setStyleSheet("color: #D32F2F; border: none;")
            result_frame.setStyleSheet(
                "QFrame { background-color: #FFEBEE; border: 3px solid #F44336; "
                "border-radius: 15px; padding: 20px; }"
            )
            message_label.setStyleSheet(
                "font-size: 12pt; color: #D32F2F; border: none; padding: 10px;"
            )
            frame_layout.addWidget(titre_label)
            frame_layout.addWidget(message_label)

        elif type_erreur == "CLIENT_REQUIS":
            # Client requis - BLEU CLAIR
            titre_label.setText("\U0001F464 Client requis")
            titre_label.setStyleSheet("color: #0277BD; border: none;")
            result_frame.setStyleSheet(
                "QFrame { background-color: #E1F5FE; border: 3px solid #03A9F4; "
                "border-radius: 15px; padding: 20px; }"
            )
            message_label.setStyleSheet(
                "font-size: 12pt; color: #0277BD; border: none; padding: 10px;"
            )
            frame_layout.addWidget(titre_label)
            frame_layout.addWidget(message_label)

        else:
            # Autres erreurs - GRIS
            titre_label.setText("\u26A0\uFE0F Code INVALIDE")
            titre_label.setStyleSheet("color: #616161; border: none;")
            result_frame.setStyleSheet(
                "QFrame { background-color: #F5F5F5; border: 3px solid #9E9E9E; "
                "border-radius: 15px; padding: 20px; }"
            )
            message_label.setStyleSheet(
                "font-size: 12pt; color: #616161; border: none; padding: 10px;"
            )
            frame_layout.addWidget(titre_label)
            frame_layout.addWidget(message_label)

        result_frame.setLayout(frame_layout)
        self.result_layout.addWidget(result_frame)
        self.result_widget.setVisible(True)
