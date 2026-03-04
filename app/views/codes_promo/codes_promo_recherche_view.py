"""Vue complète de gestion des codes promotionnels.

Toggle : Liste / Créer / Vérifier
"""

import logging

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QDoubleSpinBox,
    QTextEdit,
    QComboBox,
    QMessageBox,
    QScrollArea,
    QSpinBox,
    QDateEdit,
    QCheckBox,
    QStackedWidget,
    QFrame,
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont

from utils.styles import (
    style_section,
    style_input,
    style_bouton,
    style_scroll_area,
    Couleurs,
)
from views.components.modern_segmented_control import ModernSegmentedControl
from views.components.code_card import CodeCard
from views.codes_promo.fiche_code_view import FicheCodeView
from viewmodels.codes_promo_vm import CodesPromoViewModel

logger = logging.getLogger(__name__)


class CodesPromoRechercheView(QWidget):
    """Vue de gestion des codes promo : liste cards, création, vérification."""

    PAGE_LISTE = 0
    PAGE_CREATION = 1
    PAGE_VERIF = 2
    PAGE_FICHE = 3

    _PAGES = ["liste", "creation", "verifier"]

    # ------------------------------------------------------------------

    def __init__(self, viewmodel=None, parent=None):  # ← parent=None par défaut
        super().__init__(parent)
        self._mode_admin = True
        self._mode_edition = False
        self._code_id = None
        self.viewmodel = viewmodel if viewmodel is not None else CodesPromoViewModel()
        self._construire_ui()
        self._charger_codes()

    # ==================================================================
    # Construction
    # ==================================================================

    def _construire_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # === SEGMENTED CONTROL ===
        self._barre_toggle = ModernSegmentedControl(["Liste", "Créer", "Vérifier"])
        self._barre_toggle.selectionChanged.connect(self._on_toggle_changed)

        self._layout_toggle = QHBoxLayout()
        self._layout_toggle.setContentsMargins(24, 16, 24, 8)
        self._layout_toggle.addStretch(1)
        self._layout_toggle.addWidget(self._barre_toggle)
        self._layout_toggle.addStretch(1)
        layout_principal.addLayout(self._layout_toggle)

        # === STACKED WIDGET ===
        self.pile = QStackedWidget()
        self.pile.addWidget(self._creer_page_liste())  # 0
        self.pile.addWidget(self._creer_page_creation())  # 1
        self.pile.addWidget(self._creer_page_verif())  # 2

        self.fiche_code = FicheCodeView(viewmodel=self.viewmodel)
        self.fiche_code.retour_demande.connect(lambda: self._changer_page("liste"))
        self.fiche_code.edition_demande.connect(self._editer_code)
        self.fiche_code.activation_demandee.connect(self._on_activation_fiche)
        self.fiche_code.suppression_demandee.connect(self._on_suppression_fiche)
        self.fiche_code.date_debut_modifiee.connect(self._on_date_debut_modifiee)
        self.fiche_code.date_fin_modifiee.connect(self._on_date_fin_modifiee)
        self.pile.addWidget(self.fiche_code)  # 3

        layout_principal.addWidget(self.pile)
        self._changer_page("liste")

    def _on_toggle_changed(self, index: int):
        pages = self._pages_courantes()
        if index < len(pages):
            self._changer_page(pages[index])

    def _pages_courantes(self) -> list:
        """Retourne les pages disponibles selon le mode."""
        if self._mode_admin:
            return self._PAGES  # ["liste", "creation", "verifier"]
        return ["liste", "verifier"]

    def mettre_a_jour_mode(self, mode_admin: bool) -> None:
        """Met à jour la vue selon le mode administratif/fonctionnel."""
        # Récupérer la page AVANT de changer le mode
        pages_avant = self._pages_courantes()
        idx_avant = self._barre_toggle.current_index
        page_courante = (
            pages_avant[idx_avant] if idx_avant < len(pages_avant) else "liste"
        )

        self._mode_admin = mode_admin

        if mode_admin:
            labels = ["Liste", "Créer", "Vérifier"]
        else:
            labels = ["Liste", "Vérifier"]

        pages_apres = self._pages_courantes()
        if page_courante not in pages_apres:
            page_courante = "liste"
        idx_cible = pages_apres.index(page_courante)

        ancien_toggle = self._barre_toggle
        self._layout_toggle.removeWidget(ancien_toggle)
        ancien_toggle.deleteLater()

        self._barre_toggle = ModernSegmentedControl(labels, initial_index=idx_cible)
        self._barre_toggle.selectionChanged.connect(self._on_toggle_changed)
        self._layout_toggle.insertWidget(1, self._barre_toggle)

        self._changer_page(page_courante)
        self._charger_codes()

        # Propager aux fiches
        self.fiche_code.mettre_a_jour_mode(mode_admin)

    def _changer_page(self, page: str):
        logger.info(f"=== Changement page codes : {page} ===")
        logger.info(f"    pile.currentIndex AVANT: {self.pile.currentIndex()}")

        pages = self._pages_courantes()
        if page in pages:
            idx = pages.index(page)
            if self._barre_toggle.current_index != idx:
                self._barre_toggle.select(idx)

        if page == "liste":
            self.pile.setCurrentIndex(self.PAGE_LISTE)
            self._charger_codes()
        elif page == "creation":
            self.pile.setCurrentIndex(self.PAGE_CREATION)
        elif page == "verifier":
            self.pile.setCurrentIndex(self.PAGE_VERIF)
        elif page == "fiche":
            logger.info(f"    Changement VERS fiche (PAGE_FICHE={self.PAGE_FICHE})")
            self.pile.setCurrentIndex(self.PAGE_FICHE)

        logger.info(f"    pile.currentIndex APRÈS: {self.pile.currentIndex()}")
        self._barre_toggle.setVisible(page != "fiche")

    # ==================================================================
    # Page Liste
    # ==================================================================

    def _creer_page_liste(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        self.input_recherche = QLineEdit()
        self.input_recherche.setPlaceholderText(
            "🔍 Rechercher... (ex: PROMO 10  →  tous les codes à 10%)"
        )
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
    # Page Création / Édition
    # ==================================================================

    def _creer_page_creation(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(style_scroll_area())

        conteneur = QWidget()
        conteneur.setStyleSheet(f"background-color: {Couleurs.BLANC};")
        layout = QVBoxLayout(conteneur)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 15, 30, 30)

        layout.addWidget(self._creer_formulaire())
        layout.addLayout(self._creer_boutons_form())
        layout.addStretch()

        scroll.setWidget(conteneur)
        return scroll

    def _creer_formulaire(self) -> QGroupBox:
        groupe = QGroupBox("Informations du code promo")
        groupe.setStyleSheet(style_section())

        form = QFormLayout()
        form.setSpacing(14)

        font = QFont()
        font.setPointSize(12)

        # Code
        self.input_code = QLineEdit()
        self.input_code.setFont(font)
        self.input_code.setPlaceholderText("PROMO2026")
        self.input_code.setStyleSheet(style_input())
        self.input_code.textChanged.connect(
            lambda t: (
                self.input_code.blockSignals(True),
                self.input_code.setText(t.upper()),
                self.input_code.blockSignals(False),
            )
        )
        form.addRow("Code :", self.input_code)

        # Type de réduction
        self.combo_type = QComboBox()
        self.combo_type.setFont(font)
        self.combo_type.setStyleSheet(style_input())
        self.combo_type.addItem("Pourcentage (%)", "pourcentage")
        self.combo_type.addItem("Montant fixe (€)", "montant_fixe")
        form.addRow("Type :", self.combo_type)

        # Valeur
        self.spin_valeur = QDoubleSpinBox()
        self.spin_valeur.setFont(font)
        self.spin_valeur.setRange(0.01, 999999)
        self.spin_valeur.setDecimals(2)
        self.spin_valeur.setValue(10.0)
        self.spin_valeur.setStyleSheet(style_input())
        form.addRow("Valeur :", self.spin_valeur)

        # Date début
        self.date_debut = QDateEdit()
        self.date_debut.setFont(font)
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDate(QDate.currentDate())
        self.date_debut.setStyleSheet(style_input())
        form.addRow("Date début :", self.date_debut)

        # Date fin
        self.date_fin = QDateEdit()
        self.date_fin.setFont(font)
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate().addMonths(1))
        self.date_fin.setStyleSheet(style_input())
        form.addRow("Date fin :", self.date_fin)

        # Limite d'utilisations
        self.spin_limite = QSpinBox()
        self.spin_limite.setFont(font)
        self.spin_limite.setRange(0, 999999)
        self.spin_limite.setSpecialValueText("Illimité")
        self.spin_limite.setStyleSheet(style_input())
        form.addRow("Limite (0 = ∞) :", self.spin_limite)

        # Description
        self.input_description = QTextEdit()
        self.input_description.setFont(font)
        self.input_description.setPlaceholderText("Description optionnelle...")
        self.input_description.setFixedHeight(70)
        self.input_description.setStyleSheet(style_input())
        form.addRow("Description :", self.input_description)

        # Actif
        self.check_actif = QCheckBox("Code actif")
        self.check_actif.setFont(font)
        self.check_actif.setChecked(True)
        form.addRow("", self.check_actif)

        groupe.setLayout(form)
        return groupe

    def _creer_boutons_form(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(10)

        font = QFont()
        font.setPointSize(12)

        self.btn_sauvegarder = QPushButton("Créer le code")
        self.btn_sauvegarder.setFont(font)
        self.btn_sauvegarder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sauvegarder.setStyleSheet(style_bouton(Couleurs.SUCCES))
        self.btn_sauvegarder.clicked.connect(self._sauvegarder_code)

        self.btn_annuler = QPushButton("Annuler")
        self.btn_annuler.setFont(font)
        self.btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_annuler.setStyleSheet(style_bouton(Couleurs.GRIS))
        self.btn_annuler.clicked.connect(self._reinitialiser_formulaire)

        layout.addWidget(self.btn_annuler)
        layout.addStretch()
        layout.addWidget(self.btn_sauvegarder)
        return layout

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
    # Chargement et filtrage
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
            card = CodeCard(code, search_terms=termes, show_actions=self._mode_admin)
            card.double_clicked.connect(self._voir_code)
            card.action_supprimer.connect(self._supprimer_code)
            self._layout_cards.insertWidget(self._layout_cards.count() - 1, card)

    def _filtrer_par_termes(self, codes: list, termes: list[str]) -> list:
        """Chaque terme doit matcher au moins un champ : code, description, type, valeur."""
        resultat = []
        for c in codes:
            code_str = (c.get("code") or "").lower()
            desc = (c.get("description") or "").lower()
            type_r = (c.get("type_reduction") or "").lower()
            valeur = c.get("valeur") or 0.0

            tout_matche = True
            for t in termes:
                tl = t.lower()

                if tl in code_str or tl in desc or tl in type_r:
                    continue

                try:
                    t_float = float(t.replace(",", "."))
                    if abs(valeur - t_float) < 0.005 or int(valeur) == int(t_float):
                        continue
                except ValueError:
                    pass

                tout_matche = False
                break

            if tout_matche:
                resultat.append(c)

        return resultat

    # ==================================================================
    # Actions liste
    # ==================================================================

    def _voir_code(self, code_id: int):
        logger.info(f"🔍 _voir_code appelé avec code_id={code_id}")
        logger.info(f"   fiche_code widget: {self.fiche_code}")
        logger.info(f"   Avant charger_code")
        self.fiche_code.charger_code(code_id)
        logger.info(f"   Après charger_code, changement page")
        self._changer_page("fiche")
        logger.info(f"   Page changée")

    def _supprimer_code(self, code_id: int):
        rep = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment supprimer ce code promo ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if rep == QMessageBox.Yes:
            if self.viewmodel.supprimer_code(code_id):
                self._charger_codes()

    def _on_activation_fiche(self, code_id: int, actif: bool):
        self.viewmodel.activer_desactiver(code_id, actif)

    def _on_suppression_fiche(self, code_id: int):
        if self.viewmodel.supprimer_code(code_id):
            self._changer_page("liste")
            self._charger_codes()

    def _on_date_debut_modifiee(self, code_id: int, iso: str):
        if iso:
            self.viewmodel.modifier_code(code_id, {"date_debut": iso})

    def _on_date_fin_modifiee(self, code_id: int, iso: str):
        if iso:
            self.viewmodel.modifier_code(code_id, {"date_fin": iso})

    # ==================================================================
    # Actions formulaire
    # ==================================================================

    def _editer_code(self, code_id: int):
        code = self.viewmodel.obtenir_code(code_id)
        if not code:
            return

        self._mode_edition = True
        self._code_id = code_id

        self.input_code.setText(code.get("code", ""))
        type_r = (code.get("type_reduction") or "").lower()
        self.combo_type.setCurrentIndex(0 if "pourcent" in type_r else 1)
        self.spin_valeur.setValue(code.get("valeur") or 0.0)

        if code.get("date_debut"):
            parts = str(code["date_debut"])[:10].split("-")
            if len(parts) == 3:
                self.date_debut.setDate(
                    QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                )

        if code.get("date_fin"):
            parts = str(code["date_fin"])[:10].split("-")
            if len(parts) == 3:
                self.date_fin.setDate(
                    QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                )

        self.spin_limite.setValue(code.get("limite_utilisations") or 0)
        self.input_description.setPlainText(code.get("description") or "")
        self.check_actif.setChecked(bool(code.get("actif", True)))

        self.btn_sauvegarder.setText("Modifier le code")
        self._changer_page("creation")

    def _sauvegarder_code(self):
        code_str = self.input_code.text().strip().upper()
        if not code_str:
            QMessageBox.warning(self, "Attention", "Le code ne peut pas être vide.")
            return

        valeur = self.spin_valeur.value()
        if valeur <= 0:
            QMessageBox.warning(
                self, "Attention", "La valeur doit être supérieure à 0."
            )
            return

        data = {
            "code": code_str,
            "type_reduction": self.combo_type.currentData(),
            "valeur": valeur,
            "date_debut": self.date_debut.date().toString("yyyy-MM-dd"),
            "date_fin": self.date_fin.date().toString("yyyy-MM-dd"),
            "limite_utilisations": self.spin_limite.value() or None,
            "description": self.input_description.toPlainText().strip() or None,
            "actif": self.check_actif.isChecked(),
        }

        if self._mode_edition and self._code_id:
            succes = self.viewmodel.modifier_code(self._code_id, data)
            if succes:
                QMessageBox.information(self, "Succès", "Code modifié avec succès !")
                self._reinitialiser_formulaire()
                self._changer_page("liste")
        else:
            nouveau_id = self.viewmodel.creer_code(**data)
            if nouveau_id and nouveau_id > 0:
                QMessageBox.information(
                    self, "Succès", f"Le code '{code_str}' a été créé !"
                )
                self._reinitialiser_formulaire()
                self._changer_page("liste")

    def _reinitialiser_formulaire(self):
        self._mode_edition = False
        self._code_id = None
        self.input_code.clear()
        self.combo_type.setCurrentIndex(0)
        self.spin_valeur.setValue(10.0)
        self.date_debut.setDate(QDate.currentDate())
        self.date_fin.setDate(QDate.currentDate().addMonths(1))
        self.spin_limite.setValue(0)
        self.input_description.clear()
        self.check_actif.setChecked(True)
        self.btn_sauvegarder.setText("Créer le code")

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
        msg_font = QFont()
        msg_font.setPointSize(12)
        msg_lbl.setFont(msg_font)

        if type_erreur is None and resultat:
            frame.setStyleSheet(
                "QFrame { background-color: #F3E5F5; border: 3px solid #7B1FA2; "
                "border-radius: 15px; padding: 20px; }"
            )
            code_str = resultat.get("code", "")
            titre_lbl.setText(f"✅ Code VALIDE : {code_str}")
            titre_lbl.setStyleSheet("color: #6A1B9A; border: none;")
            frame_layout.addWidget(titre_lbl)

            type_r = (resultat.get("type_reduction") or "").lower()
            valeur = resultat.get("valeur") or 0.0
            if "pourcent" in type_r:
                reduction_txt = f"Réduction : {valeur:.0f}%"
            else:
                reduction_txt = f"Réduction : {valeur:.2f} €"

            lbl_red = QLabel(reduction_txt)
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
