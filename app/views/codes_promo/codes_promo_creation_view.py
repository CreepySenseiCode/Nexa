"""Vue pour la création et la gestion des codes promotionnels (mode Patron)."""

import logging
from datetime import date

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QDoubleSpinBox,
    QSpinBox,
    QDateEdit,
    QTextEdit,
    QCheckBox,
    QGroupBox,
    QMessageBox,
    QScrollArea,
    QRadioButton,
    QStackedWidget,
    QFrame,
    QGridLayout,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from utils.styles import (
    Couleurs,
    style_input,
    style_bouton,
    style_section,
    style_scroll_area,
)
from views.components.modern_segmented_control import ModernSegmentedControl
from views.components.code_card import CodeCard
from views.codes_promo.fiche_code_view import FicheCodeView
from viewmodels.codes_promo_vm import CodesPromoViewModel

logger = logging.getLogger(__name__)


class CodesPromoCreationView(QWidget):
    """Vue pour la création et la gestion des codes de réduction (Patron)."""

    PAGE_LISTE = 0
    PAGE_VERIF = 1
    PAGE_CREATION = 2
    PAGE_FICHE = 3

    _PAGES = ["liste", "verifier", "creation"]

    # ==================================================================
    # Init
    # ==================================================================

    def __init__(self, viewmodel=None, parent=None):  # ← parent=None par défaut
        super().__init__(parent)
        self._mode_admin = True
        self._mode_edition = False
        self._code_id = None
        self._code_courant = None
        self.viewmodel = viewmodel if viewmodel is not None else CodesPromoViewModel()
        self._construire_ui()
        self._connecter_signaux()
        self._charger_codes()

    # ==================================================================
    # Construction
    # ==================================================================

    def _construire_ui(self):
        layout_self = QVBoxLayout(self)
        layout_self.setContentsMargins(0, 0, 0, 0)
        layout_self.setSpacing(0)

        # === SEGMENTED CONTROL ===
        self._barre_toggle = ModernSegmentedControl(
            ["Liste", "Vérifier", "Nouveau code"]
        )
        self._barre_toggle.selectionChanged.connect(self._on_toggle_changed)

        self._layout_toggle = QHBoxLayout()
        self._layout_toggle.setContentsMargins(24, 16, 24, 8)
        self._layout_toggle.addStretch(1)
        self._layout_toggle.addWidget(self._barre_toggle)
        self._layout_toggle.addStretch(1)
        layout_self.addLayout(self._layout_toggle)

        # === STACKED WIDGET ===
        self.pile = QStackedWidget()
        self.pile.addWidget(self._creer_page_liste())  # 0 - Liste
        self.pile.addWidget(self._creer_page_verif())  # 1 - Vérifier
        self.pile.addWidget(self._creer_page_creation())  # 2 - Nouveau code

        self.fiche_code = FicheCodeView(viewmodel=self.viewmodel)
        self.fiche_code.retour_demande.connect(lambda: self._changer_page("liste"))
        self.fiche_code.edition_demande.connect(self._editer_code)
        self.pile.addWidget(self.fiche_code)  # 3 - Fiche

        layout_self.addWidget(self.pile)
        self._changer_page("liste")

    def _on_toggle_changed(self, index: int):
        pages = self._PAGES if self._mode_admin else self._PAGES[:2]
        if index < len(pages):
            self._changer_page(pages[index])

    def mettre_a_jour_mode(self, mode_admin: bool) -> None:
        """Met à jour la vue selon le mode administratif/fonctionnel."""
        # Récupérer la page AVANT de changer le mode
        pages_avant = self._PAGES if self._mode_admin else self._PAGES[:2]
        idx_avant = self._barre_toggle.current_index
        page_courante = (
            pages_avant[idx_avant] if idx_avant < len(pages_avant) else "liste"
        )

        self._mode_admin = mode_admin

        if mode_admin:
            labels = ["Liste", "Vérifier", "Nouveau code"]
            pages_apres = self._PAGES
        else:
            labels = ["Liste", "Vérifier"]
            pages_apres = self._PAGES[:2]

        # Si on était sur une page supprimée, revenir à liste
        if page_courante not in pages_apres:
            page_courante = "liste"

        idx_cible = pages_apres.index(page_courante)

        # Reconstruire le toggle avec le bon index initial
        ancien_toggle = self._barre_toggle
        self._layout_toggle.removeWidget(ancien_toggle)
        ancien_toggle.deleteLater()

        self._barre_toggle = ModernSegmentedControl(labels, initial_index=idx_cible)
        self._barre_toggle.selectionChanged.connect(self._on_toggle_changed)
        self._layout_toggle.insertWidget(1, self._barre_toggle)

        # Synchroniser la page affichée
        self._changer_page(page_courante)

        # Recharger les cards (avec/sans boutons d'action)
        self._charger_codes()

        # Propager aux fiches
        self.fiche_code.mettre_a_jour_mode(mode_admin)

    def _changer_page(self, page: str):
        logger.info(f"=== Changement page codes patron : {page} ===")

        pages = self._PAGES if self._mode_admin else self._PAGES[:2]
        if page in pages:
            idx = pages.index(page)
            if self._barre_toggle.current_index != idx:
                self._barre_toggle.select(idx)

        if page == "liste":
            self.pile.setCurrentIndex(self.PAGE_LISTE)
            self._charger_codes()
        elif page == "verifier":
            self.pile.setCurrentIndex(self.PAGE_VERIF)
        elif page == "creation":
            self.pile.setCurrentIndex(self.PAGE_CREATION)
        elif page == "fiche":
            self.pile.setCurrentIndex(self.PAGE_FICHE)

        self._barre_toggle.setVisible(page != "fiche")

    # ==================================================================
    # Page Liste (cards + recherche)
    # ==================================================================

    def _creer_page_liste(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        self.input_recherche = QLineEdit()
        self.input_recherche.setPlaceholderText("🔍 Rechercher...")
        self.input_recherche.setStyleSheet(style_input())
        self.input_recherche.textChanged.connect(self._charger_codes)
        layout.addWidget(self.input_recherche)

        self._label_nb_codes = QLabel()
        self._label_nb_codes.setStyleSheet(
            "color: #7f8c8d; font-size: 11pt; padding: 2px 0;"
        )
        layout.addWidget(self._label_nb_codes)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self._conteneur_cards = QWidget()
        self._layout_cards = QVBoxLayout(self._conteneur_cards)
        self._layout_cards.setContentsMargins(0, 0, 8, 0)
        self._layout_cards.setSpacing(6)
        self._layout_cards.addStretch()

        scroll.setWidget(self._conteneur_cards)
        layout.addWidget(scroll, stretch=1)
        return page

    # ==================================================================
    # Page Vérification
    # ==================================================================

    def _creer_page_verif(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #FFFFFF; }")

        conteneur = QWidget()
        conteneur.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout(conteneur)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        label_titre = QLabel("Vérification de code promotionnel")
        font_titre = QFont()
        font_titre.setPointSize(18)
        font_titre.setBold(True)
        label_titre.setFont(font_titre)
        label_titre.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_titre)

        label_sous_titre = QLabel("Entrez un code promo pour vérifier sa validité")
        font_st = QFont()
        font_st.setPointSize(12)
        label_sous_titre.setFont(font_st)
        label_sous_titre.setAlignment(Qt.AlignCenter)
        label_sous_titre.setStyleSheet("color: #757575;")
        layout.addWidget(label_sous_titre)

        layout.addSpacing(10)

        # --- Barre de saisie ---
        widget_saisie = QWidget()
        widget_saisie.setMaximumWidth(500)
        layout_saisie_v = QVBoxLayout(widget_saisie)
        layout_saisie_v.setContentsMargins(0, 0, 0, 0)
        layout_saisie_v.setSpacing(12)

        font_corps = QFont()
        font_corps.setPointSize(13)

        lbl = QLabel("Entrer un code promo :")
        lbl.setFont(font_corps)
        layout_saisie_v.addWidget(lbl)

        ligne_saisie = QHBoxLayout()
        ligne_saisie.setSpacing(10)

        self.input_verif = QLineEdit()
        self.input_verif.setFont(font_corps)
        self.input_verif.setPlaceholderText("CODE2026")
        self.input_verif.setMinimumHeight(42)
        self.input_verif.setStyleSheet(
            "QLineEdit { border: 2px solid #E0E0E0; border-radius: 8px; "
            "padding: 8px 14px; background-color: #FAFAFA; }"
            "QLineEdit:focus { border: 2px solid #7B1FA2; background-color: #FFF; }"
        )
        self.input_verif.textChanged.connect(self._on_verif_code_change)
        self.input_verif.returnPressed.connect(self._verifier_code)

        self.btn_verifier = QPushButton("Vérifier")
        self.btn_verifier.setFont(font_corps)
        self.btn_verifier.setMinimumHeight(42)
        self.btn_verifier.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_verifier.setStyleSheet(
            "QPushButton { background-color: #7B1FA2; color: white; "
            "padding: 8px 28px; border-radius: 8px; border: none; font-weight: bold; }"
            "QPushButton:hover { background-color: #6A1B9A; }"
        )
        self.btn_verifier.clicked.connect(self._verifier_code)

        ligne_saisie.addWidget(self.input_verif)
        ligne_saisie.addWidget(self.btn_verifier)
        layout_saisie_v.addLayout(ligne_saisie)

        layout_centre = QHBoxLayout()
        layout_centre.addStretch()
        layout_centre.addWidget(widget_saisie)
        layout_centre.addStretch()
        layout.addLayout(layout_centre)

        layout.addSpacing(10)

        # --- Zone résultat dynamique ---
        self._verif_result_widget = QWidget()
        self._verif_result_widget.setMaximumWidth(500)
        self._verif_result_layout = QVBoxLayout(self._verif_result_widget)
        self._verif_result_layout.setContentsMargins(0, 0, 0, 0)
        self._verif_result_widget.setVisible(False)

        layout_centre2 = QHBoxLayout()
        layout_centre2.addStretch()
        layout_centre2.addWidget(self._verif_result_widget)
        layout_centre2.addStretch()
        layout.addLayout(layout_centre2)

        layout.addStretch()
        scroll.setWidget(conteneur)
        return scroll

    # ==================================================================
    # Page Création / Édition
    # ==================================================================

    def _creer_page_creation(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(style_scroll_area())

        conteneur = QWidget()
        conteneur.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        layout_form = QVBoxLayout(conteneur)
        layout_form.setSpacing(16)
        layout_form.setContentsMargins(20, 20, 20, 20)

        groupe_formulaire = QGroupBox("Créer un nouveau code de réduction")
        font_section = QFont()
        font_section.setPointSize(14)
        font_section.setWeight(QFont.Weight.DemiBold)
        groupe_formulaire.setFont(font_section)
        groupe_formulaire.setStyleSheet(style_section())

        form = QFormLayout()
        form.setSpacing(10)
        form.setContentsMargins(15, 15, 15, 15)

        font_corps = QFont()
        font_corps.setPointSize(12)

        # Code
        self.input_code = QLineEdit()
        self.input_code.setFont(font_corps)
        self.input_code.setPlaceholderText("NOEL2026")
        self.input_code.setStyleSheet(style_input())
        form.addRow("Code :", self.input_code)

        # Pourcentage
        self.spin_pourcentage = QDoubleSpinBox()
        self.spin_pourcentage.setFont(font_corps)
        self.spin_pourcentage.setMinimum(0.00)
        self.spin_pourcentage.setMaximum(100.00)
        self.spin_pourcentage.setDecimals(2)
        self.spin_pourcentage.setSuffix(" %")
        self.spin_pourcentage.setValue(0.00)
        self.spin_pourcentage.setStyleSheet(style_input())
        form.addRow("Pourcentage de réduction :", self.spin_pourcentage)

        # Description
        self.input_description = QTextEdit()
        self.input_description.setFont(font_corps)
        self.input_description.setPlaceholderText("Description (optionnel)")
        self.input_description.setFixedHeight(60)
        self.input_description.setStyleSheet(style_input())
        form.addRow("Description :", self.input_description)

        # Date début
        self.date_debut = QDateEdit()
        self.date_debut.setFont(font_corps)
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDate(QDate.currentDate())
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.setStyleSheet(style_input())
        form.addRow("Date de début :", self.date_debut)

        # Date fin
        self.date_fin = QDateEdit()
        self.date_fin.setFont(font_corps)
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate().addDays(30))
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setStyleSheet(style_input())
        form.addRow("Date de fin :", self.date_fin)

        # Type d'utilisation
        type_widget = QWidget()
        type_layout = QVBoxLayout(type_widget)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setSpacing(6)

        radio_style = (
            "QRadioButton { font-size: 12pt; padding: 8px; color: #333; }"
            "QRadioButton::indicator { width: 20px; height: 20px; }"
        )

        self.radio_illimite = QRadioButton("Illimité")
        self.radio_illimite.setChecked(True)
        self.radio_illimite.setStyleSheet(radio_style)
        self.radio_illimite.toggled.connect(self._on_type_changed)
        type_layout.addWidget(self.radio_illimite)

        self.radio_limite_globale = QRadioButton(
            "Limite globale (nombre d'utilisations total)"
        )
        self.radio_limite_globale.setStyleSheet(radio_style)
        self.radio_limite_globale.toggled.connect(self._on_type_changed)
        type_layout.addWidget(self.radio_limite_globale)

        self.spinbox_limite_globale = QSpinBox()
        self.spinbox_limite_globale.setFont(font_corps)
        self.spinbox_limite_globale.setMinimum(1)
        self.spinbox_limite_globale.setMaximum(10000)
        self.spinbox_limite_globale.setValue(100)
        self.spinbox_limite_globale.setPrefix("Nombre : ")
        self.spinbox_limite_globale.setStyleSheet(style_input())
        self.spinbox_limite_globale.hide()
        type_layout.addWidget(self.spinbox_limite_globale)

        self.radio_unique_par_client = QRadioButton("Limite par client")
        self.radio_unique_par_client.setStyleSheet(radio_style)
        self.radio_unique_par_client.toggled.connect(self._on_type_changed)
        type_layout.addWidget(self.radio_unique_par_client)

        self.spinbox_limite_client = QSpinBox()
        self.spinbox_limite_client.setFont(font_corps)
        self.spinbox_limite_client.setMinimum(1)
        self.spinbox_limite_client.setMaximum(100)
        self.spinbox_limite_client.setValue(1)
        self.spinbox_limite_client.setPrefix("Nombre : ")
        self.spinbox_limite_client.setStyleSheet(style_input())
        self.spinbox_limite_client.hide()
        type_layout.addWidget(self.spinbox_limite_client)

        form.addRow("Type d'utilisation :", type_widget)

        # Actif
        self.checkbox_actif = QCheckBox("Actif")
        self.checkbox_actif.setFont(font_corps)
        self.checkbox_actif.setChecked(True)
        form.addRow("", self.checkbox_actif)

        groupe_formulaire.setLayout(form)
        layout_form.addWidget(groupe_formulaire)

        # Boutons
        layout_boutons = QHBoxLayout()
        layout_boutons.setSpacing(10)

        self.btn_creer = QPushButton("Créer le code")
        self.btn_creer.setFont(font_corps)
        self.btn_creer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_creer.setStyleSheet(style_bouton(Couleurs.SUCCES))

        self.btn_annuler = QPushButton("Annuler")
        self.btn_annuler.setFont(font_corps)
        self.btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_annuler.setStyleSheet(style_bouton(Couleurs.GRIS))

        layout_boutons.addWidget(self.btn_annuler)
        layout_boutons.addStretch()
        layout_boutons.addWidget(self.btn_creer)
        layout_form.addLayout(layout_boutons)

        layout_form.addStretch()
        scroll.setWidget(conteneur)
        return scroll

    # ==================================================================
    # Page Fiche (détail inline)
    # ==================================================================

    def _creer_page_fiche(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        layout_principal = QVBoxLayout(page)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        barre_retour = QHBoxLayout()
        barre_retour.setContentsMargins(20, 10, 20, 0)
        btn_retour = QPushButton("← Retour")
        btn_retour.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_retour.setStyleSheet(
            f"QPushButton {{ background: none; border: none; color: {Couleurs.PRIMAIRE}; "
            f"font-size: 12pt; font-weight: 600; padding: 8px 0; }}"
            f"QPushButton:hover {{ color: {Couleurs.PRIMAIRE_FONCE}; }}"
        )
        btn_retour.clicked.connect(lambda: self._changer_page("liste"))
        barre_retour.addWidget(btn_retour)
        barre_retour.addStretch()
        layout_principal.addLayout(barre_retour)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(style_scroll_area())

        conteneur = QWidget()
        conteneur.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        self._fiche_layout = QVBoxLayout(conteneur)
        self._fiche_layout.setSpacing(20)
        self._fiche_layout.setContentsMargins(30, 10, 30, 30)

        # Header violet
        self._fiche_header = QFrame()
        self._fiche_header.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0 #6A1B9A, stop:1 #AB47BC); "
            "border-radius: 16px; padding: 30px; }"
        )
        header_layout = QVBoxLayout(self._fiche_header)

        self._fiche_lbl_code = QLabel()
        self._fiche_lbl_code.setStyleSheet(
            "font-size: 26pt; font-weight: bold; color: white; border: none; "
            "font-family: 'Courier New', monospace; letter-spacing: 4px;"
        )
        header_layout.addWidget(self._fiche_lbl_code)

        header_details = QHBoxLayout()
        self._fiche_lbl_reduction = QLabel()
        self._fiche_lbl_reduction.setStyleSheet(
            "font-size: 22pt; font-weight: bold; color: white; border: none;"
        )
        header_details.addWidget(self._fiche_lbl_reduction)
        header_details.addStretch()

        self._fiche_lbl_statut = QLabel()
        self._fiche_lbl_statut.setStyleSheet(
            "font-size: 12pt; font-weight: 600; color: white; border: none; "
            "background: rgba(255,255,255,0.25); border-radius: 8px; padding: 6px 14px;"
        )
        header_details.addWidget(self._fiche_lbl_statut)
        header_layout.addLayout(header_details)
        self._fiche_layout.addWidget(self._fiche_header)

        # Section détails
        section_details = QFrame()
        section_details.setStyleSheet(
            f"QFrame {{ background-color: {Couleurs.FOND_SECTION}; "
            f"border: 2px solid {Couleurs.BORDURE}; border-radius: 12px; padding: 20px; }}"
        )
        details_layout = QVBoxLayout(section_details)

        lbl_d_titre = QLabel("Détails")
        lbl_d_titre.setStyleSheet(
            f"font-size: 14pt; font-weight: bold; color: {Couleurs.PRIMAIRE}; "
            f"border: none; margin-bottom: 5px;"
        )
        details_layout.addWidget(lbl_d_titre)

        self._fiche_grid = QGridLayout()
        self._fiche_grid.setHorizontalSpacing(30)
        self._fiche_grid.setVerticalSpacing(10)
        details_layout.addLayout(self._fiche_grid)
        self._fiche_layout.addWidget(section_details)

        btn_layout = QHBoxLayout()
        self._fiche_btn_modifier = QPushButton("✏ Modifier ce code")
        self._fiche_btn_modifier.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fiche_btn_modifier.setStyleSheet(style_bouton(Couleurs.PRIMAIRE))
        self._fiche_btn_modifier.clicked.connect(self._modifier_depuis_fiche)
        btn_layout.addStretch()
        btn_layout.addWidget(self._fiche_btn_modifier)
        self._fiche_layout.addLayout(btn_layout)

        self._fiche_layout.addStretch()
        scroll.setWidget(conteneur)
        layout_principal.addWidget(scroll)
        return page

    # ==================================================================
    # Connexion des signaux
    # ==================================================================

    def _connecter_signaux(self):
        self.input_code.textChanged.connect(self._on_code_change)
        self.btn_creer.clicked.connect(self._creer_code)
        self.btn_annuler.clicked.connect(self._reinitialiser_formulaire)
        self.viewmodel.code_cree.connect(self._on_code_cree)
        self.viewmodel.erreur.connect(self._on_erreur)
        self.viewmodel.codes_modifies.connect(self._charger_codes)

    # ==================================================================
    # Chargement et filtrage des codes (cards)
    # ==================================================================

    def _charger_codes(self):
        terme = (
            self.input_recherche.text().strip()
            if hasattr(self, "input_recherche")
            else ""
        )
        termes = [t for t in terme.split() if t]

        codes = self.viewmodel.lister_codes()

        if termes:
            codes = self._filtrer_par_termes(codes, termes)

        if hasattr(self, "_label_nb_codes"):
            self._label_nb_codes.setText(f"{len(codes)} code(s)")

        if not hasattr(self, "_layout_cards"):
            return

        while self._layout_cards.count() > 1:
            item = self._layout_cards.takeAt(0)
            if w := item.widget():
                w.deleteLater()

        if not codes:
            lbl = QLabel("Aucun code trouvé.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #BBBBBB; font-size: 13pt; padding: 40px;")
            self._layout_cards.insertWidget(0, lbl)
            return

        for code in codes:
            card = CodeCard(
                self._normaliser_pour_card(code),
                search_terms=termes,
                show_actions=self._mode_admin,
                is_archive=not code.get("actif", True),
            )
            card.double_clicked.connect(self._voir_code)
            card.action_archiver.connect(self._desactiver_code)
            card.action_restaurer.connect(self._activer_code)
            card.action_supprimer.connect(self._supprimer_code)
            self._layout_cards.insertWidget(self._layout_cards.count() - 1, card)

    def _normaliser_pour_card(self, code: dict) -> dict:
        return {
            **code,
            "valeur": code.get("pourcentage") or 0.0,
            "type_reduction": "pourcentage",
            "nb_utilisations": code.get("nombre_utilisations") or 0,
        }

    def _filtrer_par_termes(self, codes: list, termes: list[str]) -> list:
        resultat = []
        for c in codes:
            code_str = (c.get("code") or "").lower()
            desc = (c.get("description") or "").lower()
            type_u = (c.get("type_utilisation") or "").lower()
            pourcent = c.get("pourcentage") or 0.0
            actif_str = "actif" if c.get("actif") else "inactif"

            tout_matche = True
            for t in termes:
                tl = t.lower()
                if tl in code_str or tl in desc or tl in type_u or tl in actif_str:
                    continue
                try:
                    t_float = float(t.replace(",", "."))
                    if abs(pourcent - t_float) < 0.005 or int(pourcent) == int(t_float):
                        continue
                except ValueError:
                    pass
                tout_matche = False
                break

            if tout_matche:
                resultat.append(c)
        return resultat

    # ==================================================================
    # Fiche détail
    # ==================================================================

    def _voir_code(self, code_id: int):
        self.fiche_code.charger_code(code_id)
        self._changer_page("fiche")

    def _editer_code(self, code_id: int):
        self._preparer_edition(code_id)
        self._changer_page("creation")

    def _remplir_fiche(self, code: dict):
        self._fiche_lbl_code.setText(code.get("code", ""))
        pourcent = code.get("pourcentage") or 0.0
        self._fiche_lbl_reduction.setText(f"-{pourcent:.0f}%")
        self._fiche_lbl_statut.setText(self._calculer_statut_texte(code))

        while self._fiche_grid.count():
            item = self._fiche_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        TYPES_LABELS = {
            "illimite": "Illimité",
            "unique_par_client": "Unique par client",
            "limite_globale": "Limite globale",
        }

        nb_util = code.get("nombre_utilisations") or 0
        limite = code.get("limite_utilisations")
        type_util = code.get("type_utilisation", "illimite")

        champs = [
            ("Type d'utilisation", TYPES_LABELS.get(type_util, type_util)),
            ("Utilisations", f"{nb_util} / {limite}" if limite else str(nb_util)),
            ("Date de début", str(code.get("date_debut") or "")[:10]),
            ("Date de fin", str(code.get("date_fin") or "")[:10]),
        ]
        if code.get("description"):
            champs.append(("Description", code["description"]))

        for i, (lbl_txt, val_txt) in enumerate(champs):
            if not val_txt:
                continue
            lbl_n = QLabel(f"{lbl_txt} :")
            lbl_n.setStyleSheet(
                f"font-size: 12pt; font-weight: 600; "
                f"color: {Couleurs.TEXTE_SECONDAIRE}; border: none;"
            )
            lbl_v = QLabel(str(val_txt))
            lbl_v.setStyleSheet(
                f"font-size: 12pt; color: {Couleurs.TEXTE}; border: none;"
            )
            lbl_v.setWordWrap(True)
            self._fiche_grid.addWidget(lbl_n, i, 0)
            self._fiche_grid.addWidget(lbl_v, i, 1)

    def _calculer_statut_texte(self, code: dict) -> str:
        if not code.get("actif", True):
            return "Inactif"
        date_fin_str = code.get("date_fin") or ""
        if date_fin_str:
            try:
                if date.fromisoformat(str(date_fin_str)[:10]) < date.today():
                    return "Expiré"
            except ValueError:
                pass
        nb = code.get("nombre_utilisations") or 0
        limit = code.get("limite_utilisations")
        if limit and nb >= limit:
            return "Épuisé"
        return "✓ Actif"

    def _modifier_depuis_fiche(self):
        if not self._code_courant:
            return
        self._preparer_edition(self._code_courant.get("id"))
        self._changer_page("creation")

    # ==================================================================
    # Callbacks formulaire
    # ==================================================================

    def _on_code_change(self, texte: str):
        self.input_code.blockSignals(True)
        pos = self.input_code.cursorPosition()
        self.input_code.setText(texte.upper())
        self.input_code.setCursorPosition(pos)
        self.input_code.blockSignals(False)

    def _on_type_changed(self):
        self.spinbox_limite_globale.setVisible(self.radio_limite_globale.isChecked())
        self.spinbox_limite_client.setVisible(self.radio_unique_par_client.isChecked())

    def _creer_code(self):
        code = self.input_code.text().strip()
        pourcentage = self.spin_pourcentage.value()
        description = self.input_description.toPlainText().strip()
        date_debut = self.date_debut.date().toString("yyyy-MM-dd")
        date_fin = self.date_fin.date().toString("yyyy-MM-dd")

        if not code:
            QMessageBox.warning(
                self, "Attention", "Veuillez saisir un code promotionnel."
            )
            return
        if pourcentage <= 0:
            QMessageBox.warning(
                self,
                "Attention",
                "Le pourcentage de réduction doit être supérieur à 0.",
            )
            return

        if self.radio_limite_globale.isChecked():
            type_utilisation = "limite_globale"
            limite = self.spinbox_limite_globale.value()
        elif self.radio_unique_par_client.isChecked():
            type_utilisation = "unique_par_client"
            limite = self.spinbox_limite_client.value()
        else:
            type_utilisation = "illimite"
            limite = 0

        if self._mode_edition and self._code_id:
            donnees = {
                "pourcentage": pourcentage,
                "description": description,
                "date_debut": date_debut,
                "date_fin": date_fin,
                "type_utilisation": type_utilisation,
                "limite_utilisations": (
                    limite if type_utilisation != "illimite" else None
                ),
            }
            if self.viewmodel.modifier_code(self._code_id, donnees):
                QMessageBox.information(self, "Succès", "Code modifié avec succès !")
                self._reinitialiser_formulaire()
                self._changer_page("liste")
        else:
            code_id = self.viewmodel.creer_code(
                code=code,
                pourcentage=pourcentage,
                description=description,
                date_debut=date_debut,
                date_fin=date_fin,
                type_utilisation=type_utilisation,
                limite=limite,
            )
            if code_id > 0:
                QMessageBox.information(
                    self, "Succès", f"Le code '{code}' a été créé avec succès !"
                )
                self._reinitialiser_formulaire()

    def _on_code_cree(self, code_id: int):
        self._charger_codes()

    def _on_erreur(self, message: str):
        QMessageBox.warning(self, "Erreur", message)

    def _reinitialiser_formulaire(self):
        self._mode_edition = False
        self._code_id = None
        self.input_code.clear()
        self.input_code.setReadOnly(False)
        self.input_code.setStyleSheet(style_input())
        self.spin_pourcentage.setValue(0.00)
        self.input_description.clear()
        self.date_debut.setDate(QDate.currentDate())
        self.date_fin.setDate(QDate.currentDate().addDays(30))
        self.radio_illimite.setChecked(True)
        self.spinbox_limite_globale.setValue(100)
        self.spinbox_limite_globale.hide()
        self.spinbox_limite_client.setValue(1)
        self.spinbox_limite_client.hide()
        self.checkbox_actif.setChecked(True)
        self.btn_creer.setText("Créer le code")

    # ==================================================================
    # Vérification
    # ==================================================================

    def _on_verif_code_change(self, texte: str):
        self.input_verif.blockSignals(True)
        pos = self.input_verif.cursorPosition()
        self.input_verif.setText(texte.upper())
        self.input_verif.setCursorPosition(pos)
        self.input_verif.blockSignals(False)

    def _verifier_code(self):
        code = self.input_verif.text().strip()
        if not code:
            self._verif_result_widget.setVisible(False)
            return
        resultat, message, type_erreur = self.viewmodel.verifier_code(code)
        self._afficher_resultat_verif(resultat, message, type_erreur)

    def _afficher_resultat_verif(self, resultat, message, type_erreur):
        while self._verif_result_layout.count():
            item = self._verif_result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.Box)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(24, 20, 24, 20)
        frame_layout.setSpacing(10)

        titre_lbl = QLabel()
        titre_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_titre = QFont()
        font_titre.setPointSize(16)
        font_titre.setBold(True)
        titre_lbl.setFont(font_titre)

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_lbl.setFont(QFont("", 12))

        if type_erreur is None and resultat:
            frame.setStyleSheet(
                "QFrame { background-color: #F3E5F5; border: 3px solid #7B1FA2; "
                "border-radius: 15px; padding: 20px; }"
            )
            titre_lbl.setText(f"✅ Code VALIDE : {resultat.get('code', '')}")
            titre_lbl.setStyleSheet("color: #6A1B9A; border: none;")
            frame_layout.addWidget(titre_lbl)

            pourcent = resultat.get("pourcentage") or resultat.get("valeur") or 0.0
            lbl_red = QLabel(f"Réduction : {pourcent:.0f}%")
            lbl_red.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_red.setFont(QFont("", 14, QFont.Weight.Bold))
            lbl_red.setStyleSheet("color: #7B1FA2; border: none;")
            frame_layout.addWidget(lbl_red)

            if resultat.get("date_fin"):
                lbl_exp = QLabel(f"Expire le : {str(resultat['date_fin'])[:10]}")
                lbl_exp.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_exp.setStyleSheet("color: #555; border: none;")
                frame_layout.addWidget(lbl_exp)
        else:
            couleurs = {
                "expire": ("#FFF3E0", "#E65100"),
                "epuise": ("#FFF3E0", "#E65100"),
                "invalide": ("#FFEBEE", "#C62828"),
            }
            bg, border = couleurs.get(type_erreur, ("#FFEBEE", "#C62828"))
            frame.setStyleSheet(
                f"QFrame {{ background-color: {bg}; border: 3px solid {border}; "
                f"border-radius: 15px; padding: 20px; }}"
            )
            titre_lbl.setText("❌ Code invalide")
            titre_lbl.setStyleSheet(f"color: {border}; border: none;")
            msg_lbl.setStyleSheet(f"color: {border}; border: none;")
            frame_layout.addWidget(titre_lbl)
            frame_layout.addWidget(msg_lbl)

        self._verif_result_layout.addWidget(frame)
        self._verif_result_widget.setVisible(True)

    # ==================================================================
    # Actions sur les codes
    # ==================================================================

    def _preparer_edition(self, code_id: int):
        codes = self.viewmodel.lister_codes()
        code_actuel = next((c for c in codes if c.get("id") == code_id), None)
        if not code_actuel:
            return

        self._mode_edition = True
        self._code_id = code_id

        self.input_code.setText(code_actuel.get("code", ""))
        self.input_code.setReadOnly(True)
        self.input_code.setStyleSheet(style_input() + "background-color: #EEEEEE;")

        self.spin_pourcentage.setValue(code_actuel.get("pourcentage") or 0.0)
        self.input_description.setPlainText(code_actuel.get("description") or "")

        for date_field, attr in [
            (self.date_debut, "date_debut"),
            (self.date_fin, "date_fin"),
        ]:
            val = code_actuel.get(attr, "")
            if val:
                qt_date = QDate.fromString(val, "yyyy-MM-dd")
                if qt_date.isValid():
                    date_field.setDate(qt_date)

        type_util = code_actuel.get("type_utilisation", "illimite")
        if type_util == "limite_globale":
            self.radio_limite_globale.setChecked(True)
            self.spinbox_limite_globale.setValue(
                code_actuel.get("limite_utilisations") or 100
            )
        elif type_util == "unique_par_client":
            self.radio_unique_par_client.setChecked(True)
            self.spinbox_limite_client.setValue(
                code_actuel.get("limite_utilisations") or 1
            )
        else:
            self.radio_illimite.setChecked(True)

        self.btn_creer.setText("Modifier le code")

    def _activer_code(self, code_id: int):
        self.viewmodel.activer_desactiver(code_id, True)
        self._charger_codes()

    def _desactiver_code(self, code_id: int):
        reponse = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous désactiver ce code de réduction ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reponse == QMessageBox.Yes:
            self.viewmodel.activer_desactiver(code_id, False)
            self._charger_codes()

    def _supprimer_code(self, code_id: int):
        reponse = QMessageBox.question(
            self,
            "Confirmation de suppression",
            "Êtes-vous sûr de vouloir supprimer ce code de réduction ?\n"
            "Cette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reponse == QMessageBox.Yes:
            if self.viewmodel.supprimer_code(code_id):
                QMessageBox.information(self, "Succès", "Le code a été supprimé.")
            else:
                QMessageBox.warning(self, "Erreur", "La suppression a échoué.")
