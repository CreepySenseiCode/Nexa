import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QGroupBox,
    QProgressBar,
    QSizePolicy,
    QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QPainter, QPainterPath, QColor

from utils.styles import style_groupe, Couleurs


class ProfilClientWidget(QWidget):
    """
    Panneau de profil client réutilisable.

    Reprend la structure de la zone profil de RechercheView :
    - header avec gradient, photo, nom, complétude
    - sections infos, adresse, centres d'intérêt, notes
    - relations, stats, graphiques (placeholder)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._client_id: int = 0
        self._symbole_monnaie: str = "€"

        layout_root = QVBoxLayout(self)
        layout_root.setContentsMargins(10, 10, 10, 10)
        layout_root.setSpacing(15)

        self._layout_profil = QVBoxLayout()
        layout_root.addLayout(self._layout_profil)

        self._creer_section_entete()
        self._creer_section_infos()
        self._creer_section_relations()
        self._creer_section_stats()
        self._creer_section_graphiques()
        self._layout_profil.addStretch()

    # ==================================================================
    # API publique
    # ==================================================================

    def set_symbole_monnaie(self, symbole: str):
        if symbole:
            self._symbole_monnaie = symbole

    def afficher_profil(self, profil: dict):
        """
        Équivalent de RechercheView.afficher_profil, limité à l'UI.
        """
        self._client_id = profil.get("id", 0)

        # --- Header ---
        nom = (profil.get("nom") or "").upper()
        prenom = profil.get("prenom") or ""
        self._label_nom.setText(f"{nom} {prenom}")

        self._afficher_photo_profil(profil.get("photo_path", ""))

        date_creation = profil.get("date_creation") or profil.get("date_ajout") or ""
        if date_creation:
            dt = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(date_creation, fmt)
                    break
                except ValueError:
                    continue
            if dt:
                self._label_client_depuis.setText(
                    f"Client depuis le {dt.strftime('%d/%m/%Y')}"
                )
            else:
                self._label_client_depuis.setText("")
        else:
            self._label_client_depuis.setText("")

        contacts = []
        email = profil.get("email") or ""
        if email:
            contacts.append(f"Email : {email}")
        telephone = profil.get("telephone") or ""
        if telephone:
            contacts.append(f"Tel : {telephone}")
        self._label_contact_rapide.setText("  |  ".join(contacts) if contacts else "")

        # Complétude
        completude = self._calculer_completude(profil)
        self._barre_completude.setValue(completude)
        self._label_pourcent.setText(f"{completude} %")

        # --- Sections détaillées ---
        self._remplir_infos(profil)
        self._remplir_relations(profil)
        self._remplir_stats(profil.get("stats") or {})

    # ==================================================================
    # Sections (copie de RechercheView._creer_section_*)
    # ==================================================================

    def _creer_section_entete(self):
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

        self._label_photo_profil = QLabel()
        self._label_photo_profil.setFixedSize(100, 100)
        self._label_photo_profil.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label_photo_profil.setStyleSheet(
            "QLabel { background-color: rgba(255,255,255,0.2); border-radius: 50px; "
            "font-size: 40pt; color: white; border: 3px solid rgba(255,255,255,0.5); }"
        )
        self._label_photo_profil.setText("👤")
        layout_header.addWidget(self._label_photo_profil)

        layout_texte_header = QVBoxLayout()
        layout_texte_header.setSpacing(6)

        self._label_nom = QLabel()
        self._label_nom.setFont(QFont("", 22, QFont.Weight.Bold))
        self._label_nom.setStyleSheet("color: white; border: none;")
        layout_texte_header.addWidget(self._label_nom)

        self._label_client_depuis = QLabel()
        self._label_client_depuis.setFont(QFont("", 11))
        self._label_client_depuis.setStyleSheet(
            "color: rgba(255,255,255,0.8); border: none;"
        )
        layout_texte_header.addWidget(self._label_client_depuis)

        self._label_contact_rapide = QLabel()
        self._label_contact_rapide.setFont(QFont("", 11))
        self._label_contact_rapide.setStyleSheet(
            "color: rgba(255,255,255,0.9); border: none;"
        )
        self._label_contact_rapide.setWordWrap(True)
        layout_texte_header.addWidget(self._label_contact_rapide)

        layout_texte_header.addStretch()

        layout_completude = QHBoxLayout()
        layout_completude.setSpacing(8)

        self._label_completude = QLabel("Profil :")
        self._label_completude.setFont(QFont("", 9))
        self._label_completude.setStyleSheet(
            "color: rgba(255,255,255,0.7); border: none;"
        )
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
        self._label_pourcent.setStyleSheet(
            "color: rgba(255,255,255,0.9); border: none;"
        )
        layout_completude.addWidget(self._label_pourcent)

        layout_texte_header.addLayout(layout_completude)
        layout_header.addLayout(layout_texte_header)
        layout_header.addStretch()

        self._layout_profil.addWidget(self._header_card)

    def _creer_section_infos(self):
        self._group_infos = QGroupBox("👤  Informations personnelles")
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

        self._group_adresse = QGroupBox("🏠  Adresse")
        self._group_adresse.setFont(font_section)
        self._group_adresse.setStyleSheet(style_groupe())
        self._layout_adresse = QVBoxLayout()
        self._group_adresse.setLayout(self._layout_adresse)
        self._layout_profil.addWidget(self._group_adresse)

        self._group_interets = QGroupBox("❤️  Centres d'intérêt")
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

        self._group_notes = QGroupBox("📝  Notes")
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

    def _creer_section_relations(self):
        self._group_relations = QGroupBox("👪  Relations")
        font_section = QFont()
        font_section.setPointSize(13)
        font_section.setWeight(QFont.Weight.DemiBold)
        self._group_relations.setFont(font_section)
        self._group_relations.setStyleSheet(style_groupe())
        self._layout_relations = QVBoxLayout()
        self._group_relations.setLayout(self._layout_relations)
        self._group_relations.setVisible(False)
        self._layout_profil.addWidget(self._group_relations)

    def _creer_section_stats(self):
        self._group_stats = QGroupBox("📊  Statistiques d'achat")
        font_section = QFont()
        font_section.setPointSize(13)
        font_section.setWeight(QFont.Weight.DemiBold)
        self._group_stats.setFont(font_section)
        self._group_stats.setStyleSheet(style_groupe())
        self._layout_stats = QGridLayout()
        self._layout_stats.setSpacing(15)
        self._group_stats.setLayout(self._layout_stats)
        self._layout_profil.addWidget(self._group_stats)

    def _creer_section_graphiques(self):
        self._group_graphiques = QGroupBox("📈  Analyse des achats")
        font_section = QFont()
        font_section.setPointSize(13)
        font_section.setWeight(QFont.Weight.DemiBold)
        self._group_graphiques.setFont(font_section)
        self._group_graphiques.setStyleSheet(style_groupe())
        self._layout_graphiques = QHBoxLayout()
        self._layout_graphiques.setSpacing(15)

        label_graphiques = QLabel("Sélectionnez un client pour voir les graphiques")
        label_graphiques.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_graphiques.setStyleSheet(
            "color: #999999; font-style: italic; font-size: 12pt; padding: 20px;"
        )
        self._layout_graphiques.addWidget(label_graphiques)

        self._group_graphiques.setLayout(self._layout_graphiques)
        self._layout_profil.addWidget(self._group_graphiques)

    # ==================================================================
    # Remplissage (copie adaptée de RechercheView)
    # ==================================================================

    def _calculer_completude(self, profil: dict) -> int:
        from utils.profile_completion import calculer_completion

        return calculer_completion(profil)

    def _vider_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self._vider_layout(child_layout)

    def _remplir_infos(self, profil: dict):
        self._vider_layout(self._layout_infos)
        self._vider_layout(self._layout_adresse)
        self._vider_layout(self._layout_interets)

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
            self._layout_infos.addWidget(
                label_champ, ligne, 0, Qt.AlignmentFlag.AlignTop
            )

            label_valeur = QLabel(str(valeur))
            label_valeur.setFont(QFont("", 11))
            label_valeur.setStyleSheet("color: #555555; border: none;")
            label_valeur.setWordWrap(True)
            self._layout_infos.addWidget(
                label_valeur, ligne, 1, Qt.AlignmentFlag.AlignTop
            )

            ligne += 1

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

        centre_interet = profil.get("centre_interet") or ""
        if centre_interet.strip():
            self._group_interets.setVisible(True)
            tags = [
                t.strip()
                for t in centre_interet.replace(";", ",").split(",")
                if t.strip()
            ]

            couleurs_tags = [
                "#2196F3",
                "#4CAF50",
                "#FF9800",
                "#9C27B0",
                "#00BCD4",
                "#F44336",
                "#795548",
                "#607D8B",
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

        notes = profil.get("notes_personnalisees") or ""
        if notes.strip():
            self._group_notes.setVisible(True)
            self._label_notes.setText(notes.strip())
        else:
            self._group_notes.setVisible(False)

    def _remplir_relations(self, profil: dict):
        self._vider_layout(self._layout_relations)

        conjoint = profil.get("conjoint")
        enfants = profil.get("enfants") or []
        parents = profil.get("parents") or []

        a_des_relations = bool(conjoint or enfants or parents)
        self._group_relations.setVisible(a_des_relations)

        if not a_des_relations:
            return

        if conjoint:
            label_conjoint = QLabel("Conjoint :")
            label_conjoint.setFont(QFont("", 11, QFont.Weight.Bold))
            label_conjoint.setStyleSheet("color: #333333;")
            self._layout_relations.addWidget(label_conjoint)

            nom_conjoint = (
                f"{(conjoint.get('nom') or '').upper()} "
                f"{conjoint.get('prenom') or ''}"
            )
            lbl_conjoint = QLabel(nom_conjoint.strip())
            lbl_conjoint.setStyleSheet("color: #2196F3; font-size: 11pt; border: none;")
            self._layout_relations.addWidget(lbl_conjoint)

        if enfants:
            label_enfants = QLabel("Enfants :")
            label_enfants.setFont(QFont("", 11, QFont.Weight.Bold))
            label_enfants.setStyleSheet("color: #333333;")
            self._layout_relations.addWidget(label_enfants)

            for enfant in enfants:
                nom_enfant = (
                    f"{(enfant.get('nom') or '').upper()} "
                    f"{enfant.get('prenom') or ''}"
                )
                lbl_enfant = QLabel(nom_enfant.strip())
                lbl_enfant.setStyleSheet(
                    "color: #2196F3; font-size: 11pt; border: none;"
                )
                self._layout_relations.addWidget(lbl_enfant)

        if parents:
            label_parents = QLabel("Parents :")
            label_parents.setFont(QFont("", 11, QFont.Weight.Bold))
            label_parents.setStyleSheet("color: #333333;")
            self._layout_relations.addWidget(label_parents)

            for parent in parents:
                nom_parent = (
                    f"{(parent.get('nom') or '').upper()} "
                    f"{parent.get('prenom') or ''}"
                )
                lbl_parent = QLabel(nom_parent.strip())
                lbl_parent.setStyleSheet(
                    "color: #2196F3; font-size: 11pt; border: none;"
                )
                self._layout_relations.addWidget(lbl_parent)

    def _remplir_stats(self, stats: dict):
        self._vider_layout(self._layout_stats)

        nombre_achats = stats.get("nombre_achats", 0)

        if nombre_achats == 0:
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

        if dernier_achat and dernier_achat != "-":
            dernier_achat = self._formater_date(dernier_achat)

        carte_nombre = self._creer_carte_stat(
            "Nombre d'achats",
            str(nombre_achats),
            "#2196F3",
        )
        self._layout_stats.addWidget(carte_nombre, 0, 0)

        carte_montant = self._creer_carte_stat(
            "Montant total",
            f"{montant_total:.2f} {self._symbole_monnaie}",
            "#4CAF50",
        )
        self._layout_stats.addWidget(carte_montant, 0, 1)

        carte_produit = self._creer_carte_stat(
            "Produit préféré",
            produit_prefere,
            "#333333",
            taille_valeur=14,
        )
        self._layout_stats.addWidget(carte_produit, 0, 2)

        carte_categorie = self._creer_carte_stat(
            "Catégorie préférée",
            categorie_preferee,
            "#333333",
            taille_valeur=14,
        )
        self._layout_stats.addWidget(carte_categorie, 1, 0)

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
    # Utils
    # ==================================================================

    def _afficher_photo_profil(self, photo_path: str):
        if not photo_path or not os.path.exists(photo_path):
            self._label_photo_profil.setText("👤")
            self._label_photo_profil.setPixmap(QPixmap())
            return

        pixmap = QPixmap(photo_path)
        if pixmap.isNull():
            self._label_photo_profil.setText("👤")
            self._label_photo_profil.setPixmap(QPixmap())
            return

        pixmap = pixmap.scaled(
            100,
            100,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = (pixmap.width() - 100) // 2
        y = (pixmap.height() - 100) // 2
        pixmap = pixmap.copy(x, y, 100, 100)

        masque = QPixmap(100, 100)
        masque.fill(Qt.GlobalColor.transparent)
        painter = QPainter(masque)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, 100, 100)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        self._label_photo_profil.setPixmap(masque)
        self._label_photo_profil.setText("")

    def _calculer_age(self, date_naissance: str):
        try:
            dt = datetime.strptime(date_naissance, "%Y-%m-%d")
            today = datetime.today()
            age = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
            return age
        except ValueError:
            return None

    def _formater_date(self, date_str: str) -> str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return date_str
        return dt.strftime("%d/%m/%Y")
