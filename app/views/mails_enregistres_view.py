"""
Vue Mails enregistr\u00e9s - Templates et brouillons.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QTextEdit,
    QMessageBox, QInputDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class MailsEnregistresView(QWidget):
    """Interface des mails enregistr\u00e9s (templates et brouillons)."""

    def __init__(self):
        super().__init__()
        self._construire_ui()
        self._charger_templates()

    def _construire_ui(self):
        """Construit l'interface utilisateur."""
        layout_principal = QHBoxLayout()
        layout_principal.setSpacing(20)
        layout_principal.setContentsMargins(30, 30, 30, 30)

        # === COLONNE GAUCHE : Liste des templates ===
        layout_gauche = QVBoxLayout()
        layout_gauche.setSpacing(15)

        titre = QLabel("Mails enregistr\u00e9s")
        titre.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        titre.setStyleSheet("color: #1976D2; padding: 10px;")
        layout_gauche.addWidget(titre)

        # Boutons onglets
        tabs_layout = QHBoxLayout()

        self.btn_tab_templates = QPushButton("Templates")
        self.btn_tab_templates.setCheckable(True)
        self.btn_tab_templates.setChecked(True)
        self.btn_tab_templates.setStyleSheet(self._get_tab_style(True))
        self.btn_tab_templates.clicked.connect(lambda: self._changer_tab("templates"))
        tabs_layout.addWidget(self.btn_tab_templates)

        self.btn_tab_brouillons = QPushButton("Brouillons")
        self.btn_tab_brouillons.setCheckable(True)
        self.btn_tab_brouillons.setChecked(False)
        self.btn_tab_brouillons.setStyleSheet(self._get_tab_style(False))
        self.btn_tab_brouillons.clicked.connect(lambda: self._changer_tab("brouillons"))
        tabs_layout.addWidget(self.btn_tab_brouillons)

        layout_gauche.addLayout(tabs_layout)

        # Liste des mails
        self.list_mails = QListWidget()
        self.list_mails.setStyleSheet(
            "QListWidget {"
            "    border: 2px solid #E0E0E0;"
            "    border-radius: 12px;"
            "    padding: 5px;"
            "    background-color: white;"
            "    font-size: 12pt;"
            "}"
            "QListWidget::item {"
            "    padding: 12px;"
            "    border-bottom: 1px solid #F0F0F0;"
            "}"
            "QListWidget::item:selected {"
            "    background-color: #E3F2FD;"
            "    color: #1976D2;"
            "}"
        )
        self.list_mails.currentItemChanged.connect(self._on_mail_selectionne)
        layout_gauche.addWidget(self.list_mails)

        # Boutons d'action
        btn_layout = QHBoxLayout()

        btn_nouveau = QPushButton("Nouveau template")
        btn_nouveau.setStyleSheet(self._get_button_style("#4CAF50"))
        btn_nouveau.clicked.connect(self._nouveau_template)
        btn_layout.addWidget(btn_nouveau)

        btn_supprimer = QPushButton("Supprimer")
        btn_supprimer.setStyleSheet(self._get_button_style("#F44336"))
        btn_supprimer.clicked.connect(self._supprimer_mail)
        btn_layout.addWidget(btn_supprimer)

        layout_gauche.addLayout(btn_layout)

        widget_gauche = QWidget()
        widget_gauche.setLayout(layout_gauche)
        layout_principal.addWidget(widget_gauche, 1)

        # === COLONNE DROITE : Preview ===
        layout_droite = QVBoxLayout()
        layout_droite.setSpacing(15)

        label_preview = QLabel("Aper\u00e7u")
        label_preview.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        label_preview.setStyleSheet("color: #1976D2; padding: 10px;")
        layout_droite.addWidget(label_preview)

        # Objet
        self.label_objet_preview = QLabel("Objet : -")
        self.label_objet_preview.setStyleSheet(
            "font-size: 14pt; font-weight: 600; color: #333; padding: 10px;"
            "background-color: #E3F2FD; border-radius: 8px;"
        )
        layout_droite.addWidget(self.label_objet_preview)

        # Contenu
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setStyleSheet(
            "QTextEdit {"
            "    border: 2px solid #E0E0E0;"
            "    border-radius: 12px;"
            "    padding: 15px;"
            "    font-size: 12pt;"
            "    background-color: white;"
            "}"
        )
        self.text_preview.setPlaceholderText(
            "S\u00e9lectionnez un mail pour voir son contenu..."
        )
        layout_droite.addWidget(self.text_preview)

        # Boutons preview
        preview_btn_layout = QHBoxLayout()

        btn_utiliser = QPushButton("Utiliser ce template")
        btn_utiliser.setStyleSheet(self._get_button_style("#2196F3"))
        btn_utiliser.clicked.connect(self._utiliser_template)
        preview_btn_layout.addWidget(btn_utiliser)

        btn_modifier = QPushButton("Modifier")
        btn_modifier.setStyleSheet(self._get_button_style("#FF9800"))
        btn_modifier.clicked.connect(self._modifier_template)
        preview_btn_layout.addWidget(btn_modifier)

        layout_droite.addLayout(preview_btn_layout)

        widget_droite = QWidget()
        widget_droite.setLayout(layout_droite)
        layout_principal.addWidget(widget_droite, 2)

        self.setLayout(layout_principal)
        self.setStyleSheet("background-color: #F5F5F5;")

    def _charger_templates(self):
        """Charge les templates depuis la base de donn\u00e9es."""
        try:
            from models.database import get_db
            db = get_db()

            mails = db.fetchall(
                "SELECT id, nom_mail, objet FROM mails_enregistres ORDER BY date_modification DESC"
            )

            self.list_mails.clear()
            for mail in mails:
                item = QListWidgetItem(mail['nom_mail'])
                item.setData(Qt.ItemDataRole.UserRole, mail['id'])
                self.list_mails.addItem(item)
        except Exception:
            pass

    def _changer_tab(self, tab: str):
        """Change l'onglet actif."""
        if tab == "templates":
            self.btn_tab_templates.setChecked(True)
            self.btn_tab_brouillons.setChecked(False)
            self.btn_tab_templates.setStyleSheet(self._get_tab_style(True))
            self.btn_tab_brouillons.setStyleSheet(self._get_tab_style(False))
        else:
            self.btn_tab_templates.setChecked(False)
            self.btn_tab_brouillons.setChecked(True)
            self.btn_tab_templates.setStyleSheet(self._get_tab_style(False))
            self.btn_tab_brouillons.setStyleSheet(self._get_tab_style(True))
        self._charger_templates()

    def _on_mail_selectionne(self, current, previous):
        """Affiche le contenu du mail s\u00e9lectionn\u00e9."""
        if not current:
            self.label_objet_preview.setText("Objet : -")
            self.text_preview.clear()
            return

        mail_id = current.data(Qt.ItemDataRole.UserRole)
        if not mail_id:
            return

        try:
            from models.database import get_db
            db = get_db()

            mail = db.fetchone(
                "SELECT * FROM mails_enregistres WHERE id = ?", (mail_id,)
            )
            if mail:
                self.label_objet_preview.setText(f"Objet : {mail['objet']}")
                contenu = mail.get('contenu_texte') or mail.get('contenu_html', '')
                self.text_preview.setText(contenu)
        except Exception:
            pass

    def _nouveau_template(self):
        """Cr\u00e9e un nouveau template."""
        nom, ok = QInputDialog.getText(
            self, "Nouveau template", "Nom du template :"
        )
        if ok and nom.strip():
            try:
                from models.database import get_db
                db = get_db()

                db.execute(
                    "INSERT INTO mails_enregistres (nom_mail, objet, contenu_html) "
                    "VALUES (?, '', '')",
                    (nom.strip(),),
                )
                self._charger_templates()
                QMessageBox.information(
                    self, "Succ\u00e8s", f"Template '{nom}' cr\u00e9\u00e9 avec succ\u00e8s."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Erreur", f"Erreur lors de la cr\u00e9ation : {e}"
                )

    def _supprimer_mail(self):
        """Supprime le mail s\u00e9lectionn\u00e9."""
        item = self.list_mails.currentItem()
        if not item:
            QMessageBox.warning(
                self, "Erreur", "Veuillez s\u00e9lectionner un mail \u00e0 supprimer."
            )
            return

        reponse = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer '{item.text()}' ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reponse == QMessageBox.Yes:
            mail_id = item.data(Qt.ItemDataRole.UserRole)
            try:
                from models.database import get_db
                db = get_db()
                db.execute("DELETE FROM mails_enregistres WHERE id = ?", (mail_id,))
                self._charger_templates()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur : {e}")

    def _utiliser_template(self):
        """Utilise le template s\u00e9lectionn\u00e9."""
        QMessageBox.information(
            self, "Info",
            "Le template sera utilis\u00e9 pour cr\u00e9er un nouvel email.\n"
            "(Fonctionnalit\u00e9 \u00e0 connecter avec l'onglet Emailing)",
        )

    def _modifier_template(self):
        """Modifie le template s\u00e9lectionn\u00e9."""
        QMessageBox.information(
            self, "Info", "Modification du template \u00e0 impl\u00e9menter."
        )

    def _get_tab_style(self, active: bool) -> str:
        """Style d'un bouton onglet."""
        if active:
            return (
                "QPushButton {"
                "    background-color: #2196F3;"
                "    color: white;"
                "    border: none;"
                "    border-radius: 8px;"
                "    padding: 10px 20px;"
                "    font-size: 12pt;"
                "    font-weight: 600;"
                "}"
            )
        return (
            "QPushButton {"
            "    background-color: #E0E0E0;"
            "    color: #666;"
            "    border: none;"
            "    border-radius: 8px;"
            "    padding: 10px 20px;"
            "    font-size: 12pt;"
            "}"
            "QPushButton:hover {"
            "    background-color: #BDBDBD;"
            "}"
        )

    def _get_button_style(self, color: str) -> str:
        """Style des boutons."""
        return (
            f"QPushButton {{"
            f"    background-color: {color};"
            f"    color: white;"
            f"    border: none;"
            f"    border-radius: 8px;"
            f"    padding: 10px 20px;"
            f"    font-size: 12pt;"
            f"    font-weight: 600;"
            f"}}"
            f"QPushButton:hover {{"
            f"    opacity: 0.9;"
            f"}}"
        )
