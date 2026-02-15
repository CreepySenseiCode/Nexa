"""
Nexa - Application de gestion de clientèle et d'emailing.

Point d'entrée principal de l'application.
Lance l'interface graphique PySide6 avec la fenêtre principale.
"""

import sys
import os

# Ajouter le répertoire de l'application au PYTHONPATH
# pour permettre les imports relatifs depuis n'importe quel dossier
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtCore import Qt

from views.main_window import MainWindow
from views.client_view import ClientView
from views.vente_view import VenteView
from views.recherche_view import RechercheView
from views.codes_promo_recherche_view import CodesPromoRechercheView
from views.codes_promo_creation_view import CodesPromoCreationView
from views.aide_view import AideView
from views.statistiques_view import StatistiquesView
from views.calendrier_view import CalendrierView
from views.produits_view import ProduitsView
from views.parametres_view import ParametresView
from views.emailing_view import EmailingView
from views.boite_reception_view import BoiteReceptionView
from views.mails_enregistres_view import MailsEnregistresView
from views.historique_mails_view import HistoriqueMailsView


def main():
    """Point d'entrée principal de l'application Nexa."""
    app = QApplication(sys.argv)

    # --- Forcer le thème clair (ignorer le mode sombre macOS) ---
    app.setStyle(QStyleFactory.create("Fusion"))
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.WindowText, QColor(51, 51, 51))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.Text, QColor(51, 51, 51))
    palette.setColor(QPalette.Button, QColor(245, 245, 245))
    palette.setColor(QPalette.ButtonText, QColor(51, 51, 51))
    palette.setColor(QPalette.PlaceholderText, QColor(160, 160, 160))
    palette.setColor(QPalette.Highlight, QColor(33, 150, 243))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    # --- Configuration de la police par défaut ---
    font = QFont()
    if sys.platform == "darwin":
        font.setFamily(".AppleSystemUIFont")
    elif sys.platform == "win32":
        font.setFamily("Segoe UI")
    else:
        font.setFamily("Ubuntu")
    font.setPointSize(12)
    app.setFont(font)

    # --- Création de la fenêtre principale ---
    fenetre = MainWindow()

    # --- Création des vues des onglets fonctionnels ---
    vue_client = ClientView()
    vue_vente = VenteView()
    vue_recherche = RechercheView()
    vue_codes_promo_recherche = CodesPromoRechercheView()
    vue_codes_promo_creation = CodesPromoCreationView()
    vue_aide = AideView()
    vue_statistiques = StatistiquesView()
    vue_calendrier = CalendrierView()
    vue_produits = ProduitsView()
    vue_parametres = ParametresView()
    vue_emailing = EmailingView()
    vue_boite_reception = BoiteReceptionView()
    vue_mails_enregistres = MailsEnregistresView()
    vue_historique_mails = HistoriqueMailsView()

    # --- Insertion des vues dans la fenêtre principale ---
    # Vendeur : 0=Client, 1=Vente, 2=Recherche, 3=Rechercher un code, 4=Aide
    # Patron  : 5=Emailing, 6=Boite reception, 7=Statistiques, 8=Mails enregistres,
    #           9=Historique, 10=Calendrier, 11=Produits, 12=Codes promo, 13=Parametres
    fenetre.definir_page(0, vue_client)
    fenetre.definir_page(1, vue_vente)
    fenetre.definir_page(2, vue_recherche)
    fenetre.definir_page(3, vue_codes_promo_recherche)
    fenetre.definir_page(4, vue_aide)
    fenetre.definir_page(5, vue_emailing)
    fenetre.definir_page(6, vue_boite_reception)
    fenetre.definir_page(7, vue_statistiques)
    fenetre.definir_page(8, vue_mails_enregistres)
    fenetre.definir_page(9, vue_historique_mails)
    fenetre.definir_page(10, vue_calendrier)
    fenetre.definir_page(11, vue_produits)
    fenetre.definir_page(12, vue_codes_promo_creation)
    fenetre.definir_page(13, vue_parametres)

    # --- Connexion inter-vues ---
    # Quand la vue Recherche demande une modification de client,
    # basculer vers l'onglet Client en mode édition
    def ouvrir_edition_client(client_id: int):
        """Ouvre l'onglet Client en mode édition pour le client donné."""
        vue_client.charger_client(client_id)
        fenetre._changer_page(0)  # Basculer vers l'onglet Client

    vue_recherche.demande_modification.connect(ouvrir_edition_client)

    # --- Affichage et lancement ---
    fenetre.show()

    # Vérifier le premier lancement (création du mot de passe)
    fenetre._verifier_premier_lancement()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
