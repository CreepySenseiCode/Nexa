"""
Vue Mails enregistr\u00e9s - Templates et brouillons.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QTextEdit,
    QMessageBox, QInputDialog, QDialog, QLineEdit, QDialogButtonBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from utils.styles import style_bouton, style_scroll_area, Couleurs
from views.components.draft_template_toggle import DraftTemplateToggle
from viewmodels.mails_vm import MailsViewModel


class MailsEnregistresView(QWidget):
    """Interface des mails enregistres (templates et brouillons)."""

    utiliser_template_demande = Signal(dict)  # Emis avec les donnees du template

    def __init__(self, mode="tous", parent=None):
        """
        mode: "tous", "brouillons", "templates"
        """
        super().__init__(parent)
        self.mode_affichage = mode
        self.viewmodel = MailsViewModel()
        self._construire_ui()
        self._charger_templates()

    def _construire_ui(self):
        """Construit l'interface utilisateur avec style distinct selon le mode."""
        is_brouillons = self.mode_affichage == "brouillons"
        is_templates = self.mode_affichage == "templates"

        # Couleurs selon le mode
        if is_brouillons:
            accent = "#F59E0B"
            accent_light = "#FEF3C7"
            accent_border = "#FBBF24"
            accent_dark = "#B45309"
            bg_color = "#FFFBEB"
            list_selected_bg = "#FEF3C7"
            list_selected_color = "#B45309"
            preview_label_color = "#D97706"
            preview_header_bg = "#FEF3C7"
        elif is_templates:
            accent = "#3B82F6"
            accent_light = "#DBEAFE"
            accent_border = "#60A5FA"
            accent_dark = "#1E40AF"
            bg_color = "#EFF6FF"
            list_selected_bg = "#DBEAFE"
            list_selected_color = "#1E40AF"
            preview_label_color = "#1D4ED8"
            preview_header_bg = "#DBEAFE"
        else:
            accent = "#1976D2"
            accent_light = "#E3F2FD"
            accent_border = "#90CAF9"
            accent_dark = "#0D47A1"
            bg_color = "#F5F5F5"
            list_selected_bg = "#E3F2FD"
            list_selected_color = "#1976D2"
            preview_label_color = "#1976D2"
            preview_header_bg = "#E3F2FD"

        layout_principal = QHBoxLayout()
        layout_principal.setSpacing(20)
        layout_principal.setContentsMargins(30, 30, 30, 30)

        # === COLONNE GAUCHE : Liste ===
        layout_gauche = QVBoxLayout()
        layout_gauche.setSpacing(15)

        # Toggle visuel Templates / Brouillons
        self._toggle = DraftTemplateToggle()
        self._toggle.selectionChanged.connect(
            lambda idx: self._changer_tab("templates" if idx == 0 else "brouillons")
        )
        if self.mode_affichage != "tous":
            self._toggle.hide()
        layout_gauche.addWidget(self._toggle)

        # Titre de section
        if is_brouillons:
            section_icon = "✏️"
            section_title = "Mes brouillons"
        elif is_templates:
            section_icon = "📄"
            section_title = "Mes templates"
        else:
            section_icon = "📬"
            section_title = "Mails enregistres"

        lbl_section = QLabel(f"{section_icon}  {section_title}")
        lbl_section.setStyleSheet(
            f"font-size: 16pt; font-weight: bold; color: {accent_dark}; "
            f"padding: 6px 0; border: none;"
        )
        layout_gauche.addWidget(lbl_section)

        # Liste des mails
        self.list_mails = QListWidget()
        self.list_mails.setStyleSheet(
            f"QListWidget {{"
            f"    border: 2px solid {accent_border};"
            f"    border-radius: 12px;"
            f"    padding: 5px;"
            f"    background-color: white;"
            f"    font-size: 12pt;"
            f"}}"
            f"QListWidget::item {{"
            f"    padding: 12px;"
            f"    border-bottom: 1px solid #F0F0F0;"
            f"}}"
            f"QListWidget::item:selected {{"
            f"    background-color: {list_selected_bg};"
            f"    color: {list_selected_color};"
            f"}}"
        )
        self.list_mails.currentItemChanged.connect(self._on_mail_selectionne)
        layout_gauche.addWidget(self.list_mails)

        # Label vide avec design distinct
        if is_brouillons:
            empty_icon = "✏️"
            empty_title = "Aucun brouillon"
            empty_sub = "Vos emails en cours de redaction apparaitront ici.\nCommencez a rediger un email et sauvegardez-le pour le retrouver."
        elif is_templates:
            empty_icon = "📋"
            empty_title = "Aucun template"
            empty_sub = "Creez un modele d'email reutilisable.\nGagnez du temps en preparant vos emails recurrents."
        else:
            empty_icon = "📬"
            empty_title = "Aucun mail enregistre"
            empty_sub = ""

        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(8)

        lbl_empty_icon = QLabel(empty_icon)
        lbl_empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_empty_icon.setStyleSheet(f"font-size: 36pt; border: none; color: {accent};")
        empty_layout.addWidget(lbl_empty_icon)

        lbl_empty_title = QLabel(empty_title)
        lbl_empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_empty_title.setStyleSheet(
            f"font-size: 14pt; font-weight: bold; color: {accent_dark}; border: none;"
        )
        empty_layout.addWidget(lbl_empty_title)

        lbl_empty_sub = QLabel(empty_sub)
        lbl_empty_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_empty_sub.setWordWrap(True)
        lbl_empty_sub.setStyleSheet(
            f"font-size: 10pt; color: #999; font-style: italic; border: none; padding: 0 20px;"
        )
        empty_layout.addWidget(lbl_empty_sub)

        self._label_vide = empty_widget
        self._label_vide.hide()
        layout_gauche.addWidget(self._label_vide)

        # Boutons d'action
        btn_layout = QHBoxLayout()
        btn_label = "Nouveau brouillon" if is_brouillons else "Nouveau template"
        btn_nouveau = QPushButton(btn_label)
        btn_nouveau.setStyleSheet(style_bouton(Couleurs.SUCCES))
        btn_nouveau.clicked.connect(self._nouveau_template)
        btn_layout.addWidget(btn_nouveau)

        btn_supprimer = QPushButton("Supprimer")
        btn_supprimer.setStyleSheet(style_bouton(Couleurs.DANGER))
        btn_supprimer.clicked.connect(self._supprimer_mail)
        btn_layout.addWidget(btn_supprimer)
        layout_gauche.addLayout(btn_layout)

        widget_gauche = QWidget()
        widget_gauche.setLayout(layout_gauche)
        layout_principal.addWidget(widget_gauche, 1)

        # === COLONNE DROITE : Preview ===
        layout_droite = QVBoxLayout()
        layout_droite.setSpacing(15)

        preview_title = "Apercu du brouillon" if is_brouillons else "Apercu du template" if is_templates else "Apercu"
        label_preview = QLabel(preview_title)
        label_preview.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        label_preview.setStyleSheet(f"color: {preview_label_color}; padding: 10px;")
        layout_droite.addWidget(label_preview)

        # Objet
        self.label_objet_preview = QLabel("Objet : -")
        self.label_objet_preview.setStyleSheet(
            f"font-size: 14pt; font-weight: 600; color: #333; padding: 10px;"
            f"background-color: {preview_header_bg}; border-radius: 8px;"
        )
        layout_droite.addWidget(self.label_objet_preview)

        # Contenu
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setStyleSheet(
            f"QTextEdit {{"
            f"    border: 2px solid {accent_border};"
            f"    border-radius: 12px;"
            f"    padding: 15px;"
            f"    font-size: 12pt;"
            f"    background-color: white;"
            f"}}"
        )
        if is_brouillons:
            self.text_preview.setPlaceholderText(
                "Selectionnez un brouillon pour voir son contenu...\n\n"
                "Les brouillons sont des emails en cours de redaction "
                "que vous pourrez reprendre et envoyer plus tard."
            )
        elif is_templates:
            self.text_preview.setPlaceholderText(
                "Selectionnez un template pour voir son contenu...\n\n"
                "Les templates sont des modeles d'emails reutilisables "
                "pour vos envois recurrents."
            )
        else:
            self.text_preview.setPlaceholderText(
                "Selectionnez un mail pour voir son contenu..."
            )
        layout_droite.addWidget(self.text_preview)

        # Boutons preview
        preview_btn_layout = QHBoxLayout()
        btn_utiliser_label = "Reprendre ce brouillon" if is_brouillons else "Utiliser ce template"
        btn_utiliser = QPushButton(btn_utiliser_label)
        btn_utiliser.setStyleSheet(style_bouton(Couleurs.PRIMAIRE))
        btn_utiliser.clicked.connect(self._utiliser_template)
        preview_btn_layout.addWidget(btn_utiliser)

        btn_modifier = QPushButton("Modifier")
        btn_modifier.setStyleSheet(style_bouton(Couleurs.AVERTISSEMENT))
        btn_modifier.clicked.connect(self._modifier_template)
        preview_btn_layout.addWidget(btn_modifier)
        layout_droite.addLayout(preview_btn_layout)

        widget_droite = QWidget()
        widget_droite.setLayout(layout_droite)
        layout_principal.addWidget(widget_droite, 2)

        self.setLayout(layout_principal)
        self.setStyleSheet(f"background-color: {bg_color};")

    def _charger_templates(self):
        """Charge les mails selon le mode (brouillons, templates, ou tous)."""
        import logging
        logger = logging.getLogger(__name__)

        if self.mode_affichage == "brouillons":
            # Requête filtrée sur brouillons uniquement
            from models.database import get_db
            db = get_db()
            mails = db.fetchall("""
                SELECT * FROM mails_enregistres
                WHERE type = 'brouillon'
                ORDER BY date_creation DESC
            """)
            logger.info(f"Chargement brouillons : {len(mails)} mails")

        elif self.mode_affichage == "templates":
            # Requête filtrée sur templates uniquement
            from models.database import get_db
            db = get_db()
            mails = db.fetchall("""
                SELECT * FROM mails_enregistres
                WHERE type = 'template'
                ORDER BY date_creation DESC
            """)
            logger.info(f"Chargement templates : {len(mails)} mails")

        else:
            # Tous les mails (mode par défaut)
            mails = self.viewmodel.lister_mails()
            logger.info(f"Chargement tous mails : {len(mails)} mails")

        self.list_mails.clear()
        for mail in mails:
            item = QListWidgetItem(mail.get('nom_mail', mail.get('nom', 'Sans nom')))
            item.setData(Qt.ItemDataRole.UserRole, mail['id'])
            self.list_mails.addItem(item)

        # Afficher/masquer le label vide
        self._label_vide.setVisible(len(mails) == 0)

    def _changer_tab(self, tab: str):
        """Change l'onglet actif."""
        self.mode_affichage = tab
        self._charger_templates()

    def _on_mail_selectionne(self, current, previous):
        """Affiche le contenu du mail selectionne."""
        if not current:
            self.label_objet_preview.setText("Objet : -")
            self.text_preview.clear()
            return
        mail_id = current.data(Qt.ItemDataRole.UserRole)
        if not mail_id:
            return
        mail = self.viewmodel.obtenir_mail(mail_id)
        if mail:
            self.label_objet_preview.setText(f"Objet : {mail['objet']}")
            contenu = mail.get('contenu_texte') or mail.get('contenu_html', '')
            self.text_preview.setText(contenu)

    def _nouveau_template(self):
        """Cree un nouveau template."""
        nom, ok = QInputDialog.getText(self, "Nouveau template", "Nom du template :")
        if ok and nom.strip():
            try:
                self.viewmodel.creer_mail(nom.strip())
                self._charger_templates()
                QMessageBox.information(self, "Succes", f"Template '{nom}' cree avec succes.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la creation : {e}")

    def _supprimer_mail(self):
        """Supprime le mail selectionne."""
        item = self.list_mails.currentItem()
        if not item:
            QMessageBox.warning(self, "Erreur", "Veuillez selectionner un mail a supprimer.")
            return
        reponse = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer '{item.text()}' ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reponse == QMessageBox.Yes:
            mail_id = item.data(Qt.ItemDataRole.UserRole)
            try:
                self.viewmodel.supprimer_mail(mail_id)
                self._charger_templates()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur : {e}")

    def _utiliser_template(self):
        """Utilise le template selectionne pour creer un nouvel email."""
        item = self.list_mails.currentItem()
        if not item:
            QMessageBox.warning(self, "Erreur", "Veuillez selectionner un template.")
            return
        mail_id = item.data(Qt.ItemDataRole.UserRole)
        mail = self.viewmodel.obtenir_mail(mail_id)
        if mail:
            self.utiliser_template_demande.emit(mail)

    def _modifier_template(self):
        """Modifie le template selectionne dans un dialog."""
        item = self.list_mails.currentItem()
        if not item:
            QMessageBox.warning(self, "Erreur", "Veuillez selectionner un template.")
            return
        mail_id = item.data(Qt.ItemDataRole.UserRole)
        mail = self.viewmodel.obtenir_mail(mail_id)
        if not mail:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Modifier : {mail.get('nom_mail', '')}")
        dialog.setMinimumSize(600, 500)
        dialog.setStyleSheet("background-color: #FAFAFA;")

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("Objet :"))
        input_objet = QLineEdit(mail.get("objet", ""))
        input_objet.setStyleSheet(
            "QLineEdit { border: 2px solid #E0E0E0; border-radius: 8px; "
            "padding: 10px; font-size: 12pt; background-color: white; }"
        )
        layout.addWidget(input_objet)

        layout.addWidget(QLabel("Contenu :"))
        text_contenu = QTextEdit()
        text_contenu.setAcceptRichText(True)
        contenu_html = mail.get("contenu_html", "")
        if contenu_html:
            text_contenu.setHtml(contenu_html)
        else:
            text_contenu.setPlainText(mail.get("contenu_texte", ""))
        text_contenu.setStyleSheet(
            "QTextEdit { border: 2px solid #E0E0E0; border-radius: 8px; "
            "padding: 10px; font-size: 12pt; background-color: white; }"
        )
        layout.addWidget(text_contenu)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.viewmodel.modifier_mail(
                mail_id,
                objet=input_objet.text().strip(),
                contenu_html=text_contenu.toHtml(),
                contenu_texte=text_contenu.toPlainText(),
            )
            self._charger_templates()
            QMessageBox.information(self, "Succes", "Template modifie avec succes.")

