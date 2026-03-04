"""Vue pour l'onglet Aide avec FAQ et documentation."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class AideView(QWidget):
    """Onglet d'aide avec FAQ et documentation."""

    def __init__(self):
        super().__init__()
        self._construire_ui()

    def _construire_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Titre

        # ScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #FFFFFF; }")

        content = QWidget()
        content.setStyleSheet("background-color: #FFFFFF;")
        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(30, 10, 30, 30)

        faq_data = [
            {
                "question": "Comment creer un nouveau client ?",
                "reponse": (
                    "1. Allez dans l'onglet Client\n"
                    "2. Remplissez les champs obligatoires (Nom et Prenom minimum)\n"
                    "3. Ajoutez les informations supplementaires si necessaire\n"
                    "4. Cliquez sur Enregistrer\n\n"
                    "Astuce : Les champs marques d'une asterisque (*) sont obligatoires."
                ),
            },
            {
                "question": "Comment enregistrer une vente ?",
                "reponse": (
                    "1. Allez dans l'onglet Vente\n"
                    "2. Recherchez et selectionnez le client\n"
                    "3. Selectionnez le produit achete\n"
                    "4. Indiquez la quantite et verifiez le prix\n"
                    "5. Cliquez sur Enregistrer la vente\n\n"
                    "Astuce : Si le produit n'existe pas, vous pouvez le creer "
                    "directement depuis cet onglet."
                ),
            },
            {
                "question": "Comment utiliser un code promo ?",
                "reponse": (
                    "Pour verifier un code :\n"
                    "1. Allez dans l'onglet Rechercher un code promo (mode Vendeur)\n"
                    "2. Entrez le code\n"
                    "3. Cliquez sur Verifier\n\n"
                    "Pour l'appliquer a une vente :\n"
                    "1. Dans l'onglet Vente, apres avoir selectionne le client et le produit\n"
                    "2. Entrez le code dans le champ Code promo\n"
                    "3. Cliquez sur Appliquer\n"
                    "4. Le prix sera automatiquement recalcule\n\n"
                    "Astuce : Les codes peuvent avoir des limitations "
                    "(expiration, usage unique, etc.)."
                ),
            },
            {
                "question": "Quelle est la difference entre mode Vendeur et mode Patron ?",
                "reponse": (
                    "Mode Vendeur (par defaut) :\n"
                    "- Creer et modifier des clients\n"
                    "- Enregistrer des ventes\n"
                    "- Rechercher des clients\n"
                    "- Verifier des codes promo\n\n"
                    "Mode Patron (avec mot de passe) :\n"
                    "- Acces a tous les onglets du mode Vendeur\n"
                    "- + Emailing\n"
                    "- + Boite de reception\n"
                    "- + Statistiques\n"
                    "- + Gestion des codes promo\n"
                    "- + Calendrier\n"
                    "- + Produits\n"
                    "- + Parametres\n\n"
                    "Astuce : Cliquez sur le cadenas pour basculer entre les modes."
                ),
            },
            {
                "question": "Comment definir ou modifier le mot de passe patron ?",
                "reponse": (
                    "Premiere utilisation :\n"
                    "Au premier lancement, l'application vous propose de definir "
                    "un mot de passe ou non.\n\n"
                    "Pour modifier le mot de passe :\n"
                    "1. Connectez-vous en mode Patron\n"
                    "2. Allez dans Parametres\n"
                    "3. Section Securite\n"
                    "4. Cliquez sur Modifier le mot de passe\n\n"
                    "Astuce : Le mot de passe doit contenir au moins 8 caracteres, "
                    "1 majuscule, 1 chiffre et 1 caractere special."
                ),
            },
            {
                "question": "Comment rechercher un client ?",
                "reponse": (
                    "1. Allez dans l'onglet Recherche\n"
                    "2. Tapez dans la barre de recherche (nom, prenom, email ou telephone)\n"
                    "3. Les resultats apparaissent en temps reel sous forme de cartes\n"
                    "4. Cliquez sur une carte pour afficher le profil complet\n\n"
                    "Astuce : Vous pouvez chercher plusieurs mots en meme temps "
                    "(ex: \"Jean Paris\")."
                ),
            },
            {
                "question": "J'ai oublie mon mot de passe patron, que faire ?",
                "reponse": (
                    "Si vous avez defini un indice :\n"
                    "Apres 3 tentatives echouees, l'indice s'affichera automatiquement.\n\n"
                    "Si vous avez enregistre un email de recuperation :\n"
                    "Apres 5 tentatives echouees, vous pourrez demander un email "
                    "de reinitialisation.\n\n"
                    "En dernier recours :\n"
                    "Contactez l'administrateur systeme qui peut reinitialiser le "
                    "mot de passe via le script reset_password.py.\n\n"
                    "Astuce : Notez votre indice dans un endroit sur !"
                ),
            },
            {
                "question": "Comment creer un code promo ?",
                "reponse": (
                    "1. Connectez-vous en mode Patron\n"
                    "2. Allez dans l'onglet Codes promo (creation)\n"
                    "3. Remplissez les informations :\n"
                    "   - Code (ex: NOEL2026)\n"
                    "   - Pourcentage de reduction\n"
                    "   - Description\n"
                    "   - Dates de validite\n"
                    "   - Type d'utilisation (illimite, limite globale, limite par client)\n"
                    "4. Cliquez sur Creer le code\n\n"
                    "Astuce : Les codes sont automatiquement convertis en majuscules."
                ),
            },
            {
                "question": "Comment voir les statistiques de vente ?",
                "reponse": (
                    "1. Connectez-vous en mode Patron\n"
                    "2. Allez dans l'onglet Statistiques\n"
                    "3. Choisissez une periode (aujourd'hui, ce mois, cette annee, etc.)\n"
                    "4. Consultez les graphiques interactifs\n\n"
                    "Astuce : Vous pouvez exporter les statistiques en PDF ou CSV."
                ),
            },
            {
                "question": "Que signifie 'Profil complet' / 'Profil incomplet' ?",
                "reponse": (
                    "Un profil est considere comme complet si tous les champs obligatoires "
                    "(definis dans les Parametres) sont renseignes.\n\n"
                    "Pourquoi c'est important ?\n"
                    "- Meilleure qualite des donnees\n"
                    "- Emails plus personnalises\n"
                    "- Statistiques plus precises\n\n"
                    "Astuce : Vous pouvez personnaliser quels champs sont obligatoires "
                    "dans les Parametres."
                ),
            },
        ]

        for item in faq_data:
            faq_widget = self._creer_faq_item(item["question"], item["reponse"])
            content_layout.addWidget(faq_widget)

        content_layout.addStretch()
        content.setLayout(content_layout)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        self.setLayout(main_layout)

    def _creer_faq_item(self, question: str, reponse: str) -> QWidget:
        """Cree un element de FAQ collapsible."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        btn_question = QPushButton(f"  {question}")
        btn_question.setStyleSheet(
            "QPushButton {"
            "    background-color: #E3F2FD;"
            "    color: #1976D2;"
            "    border: 2px solid #9E9E9E;"
            "    border-radius: 10px;"
            "    padding: 15px;"
            "    font-size: 13pt;"
            "    font-weight: 600;"
            "    text-align: left;"
            "}"
            "QPushButton:hover {"
            "    background-color: #BBDEFB;"
            "}"
        )
        btn_question.setCursor(Qt.CursorShape.PointingHandCursor)

        reponse_label = QLabel(reponse)
        reponse_label.setWordWrap(True)
        reponse_label.setStyleSheet(
            "QLabel {"
            "    background-color: #FAFAFA;"
            "    border: 2px solid #9E9E9E;"
            "    border-radius: 10px;"
            "    padding: 20px;"
            "    font-size: 11pt;"
            "    color: #333;"
            "    margin-top: 2px;"
            "}"
        )
        reponse_label.hide()

        def toggle():
            visible = not reponse_label.isVisible()
            reponse_label.setVisible(visible)

        btn_question.clicked.connect(toggle)

        layout.addWidget(btn_question)
        layout.addWidget(reponse_label)

        widget.setLayout(layout)
        return widget
