"""
Nexa - Application de gestion de clientèle et d'emailing.

Point d'entrée principal de l'application.
Lance l'interface graphique PySide6 avec la fenêtre principale.
"""

import sys
import os

# Ajouter le répertoire de l'application au PYTHONPATH
# pour permettre les imports relatifs depuis n'importe quel dossier
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _APP_DIR)

# --- Configuration du logging centralisé (avant tout import applicatif) ---
from utils.logger import logger

logger.info("=" * 60)
logger.info("Démarrage de Nexa CRM")
logger.info("=" * 60)

from PySide6.QtWidgets import QApplication, QStyleFactory, QWidget
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtCore import Qt, QTimer

from views.main_window import MainWindow
from views.clients.client_view import ClientView
from views.ventes.vente_view import VenteView
from views.codes_promo.codes_promo_recherche_view import CodesPromoRechercheView
from views.codes_promo.codes_promo_creation_view import CodesPromoCreationView
from views.aide.aide_view import AideView
from views.statistiques.statistiques_view import StatistiquesView
from views.calendrier.calendrier_view import CalendrierView
from views.produits.produits_view import ProduitsView
from views.parametres.parametres_view import ParametresView
from views.emails.emailing_view import EmailingView
from views.emails.boite_reception_view import BoiteReceptionView
from views.emails.mails_enregistres_view import MailsEnregistresView
from views.emails.historique_mails_view import HistoriqueMailsView
from views.emails.emails_unifie_view import EmailsUnifieView
from views.taches.taches_view import TachesView
from views.calendrier.fiche_evenement_view import FicheEvenementView


def _safe_disconnect(signal):
    """Déconnecte un signal PySide6 en toute sécurité (pas de .receivers())."""
    try:
        signal.disconnect()
    except (RuntimeError, TypeError):
        pass


def main():
    """Point d'entrée principal de l'application Nexa."""
    try:
        logger.info("Initialisation de QApplication...")
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

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

        font = QFont()
        if sys.platform == "darwin":
            font.setFamily(".AppleSystemUIFont")
        elif sys.platform == "win32":
            font.setFamily("Segoe UI")
        else:
            font.setFamily("Ubuntu")
        font.setPointSize(12)
        app.setFont(font)

        # --- Icône de l'application (barre des tâches + système) ---
        icon_path = os.path.join(_APP_DIR, "assets", "icons", "logo_base.png")
        if os.path.exists(icon_path):
            src = QPixmap(icon_path)
            if not src.isNull():
                side = max(src.width(), src.height())
                square = QPixmap(side, side)
                square.fill(QColor(0, 0, 0, 0))
                ip = QPainter(square)
                ip.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                ip.drawPixmap(
                    (side - src.width()) // 2, (side - src.height()) // 2, src
                )
                ip.end()
                app.setWindowIcon(QIcon(square))

        # --- Splash d'abord, construction synchrone ensuite ---
        from views.components.splash_screen import SplashScreen

        _state = {"splash_done": False, "fenetre": None}

        def _try_show_window():
            if _state["splash_done"] and _state["fenetre"]:
                _state["fenetre"].showFullScreen()

        def _on_splash_done():
            _state["splash_done"] = True
            _try_show_window()

        splash = SplashScreen()
        splash.start(on_done=_on_splash_done)

        def _construire_app():
            """Construit toute l'interface de manière synchrone.

            Appelé 16ms après le splash pour lui laisser peindre sa 1ère frame.
            Le splash gèle pendant la construction (~1-2s) puis reprend son
            animation normalement grâce à QElapsedTimer.
            """
            try:
                logger.info("Construction de l'interface...")
                fenetre = MainWindow()
                vue_client = ClientView(parent=fenetre)
                vue_vente = VenteView(parent=fenetre)
                vue_codes_promo_recherche = CodesPromoRechercheView(parent=fenetre)
                vue_codes_promo_creation = CodesPromoCreationView(parent=fenetre)
                vue_aide = AideView(parent=fenetre)
                vue_statistiques = StatistiquesView(parent=fenetre)
                vue_calendrier = CalendrierView(parent=fenetre)
                vue_produits = ProduitsView(parent=fenetre)
                vue_parametres = ParametresView(parent=fenetre)
                vue_emailing = EmailingView(parent=fenetre)
                vue_boite_reception = BoiteReceptionView(parent=fenetre)
                vue_mails_enregistres = MailsEnregistresView(parent=fenetre)
                vue_historique_mails = HistoriqueMailsView(parent=fenetre)
                vue_emails_unifie = EmailsUnifieView(parent=fenetre)
                vue_taches = TachesView(parent=fenetre)
                vue_fiche_evenement = FicheEvenementView(parent=fenetre)

                logger.info("Configuration des onglets...")
                fenetre.definir_page(0, vue_client)
                fenetre.definir_page(1, vue_vente)
                fenetre.definir_page(2, vue_codes_promo_recherche)
                fenetre.definir_page(3, vue_aide)
                fenetre.definir_page(4, vue_produits)
                fenetre.definir_page(5, vue_codes_promo_creation)
                fenetre.definir_page(6, vue_taches)
                fenetre.definir_page(7, vue_calendrier)
                fenetre.definir_page(8, vue_emailing)
                fenetre.definir_page(9, vue_emails_unifie)
                fenetre.definir_page(10, vue_statistiques)
                fenetre.definir_page(11, vue_mails_enregistres)
                fenetre.definir_page(12, vue_historique_mails)
                fenetre.definir_page(13, vue_parametres)
                fenetre.definir_page(14, vue_fiche_evenement)

                # --- Connexions signaux ---
                vue_emails_unifie.nouveau_mail_demande.connect(
                    lambda: fenetre._changer_page(8)
                )

                def ouvrir_stats_avec_periode(debut: str, fin: str):
                    logger.info(f"Ouverture Statistiques : {debut} → {fin}")
                    fenetre._changer_page(10)
                    if hasattr(vue_statistiques, "charger_periode"):
                        vue_statistiques.charger_periode(debut, fin)

                vue_calendrier.voir_stats_periode.connect(ouvrir_stats_avec_periode)

                def _naviguer_client_depuis_fiche(client_id: int):
                    page_origine = fenetre._index_actif
                    fenetre._changer_page(0)
                    if hasattr(vue_client, "ouvrir_fiche_client"):
                        vue_client.ouvrir_fiche_client(client_id)
                    elif hasattr(vue_client, "charger_client"):
                        vue_client.charger_client(client_id)
                    if hasattr(vue_client, "btn_retour_liste_clients"):
                        _safe_disconnect(vue_client.btn_retour_liste_clients.clicked)

                        def _retour_vers_origine():
                            fenetre._changer_page(page_origine)
                            _safe_disconnect(
                                vue_client.btn_retour_liste_clients.clicked
                            )
                            vue_client.btn_retour_liste_clients.clicked.connect(
                                vue_client._retour_liste_clients
                            )

                        vue_client.btn_retour_liste_clients.clicked.connect(
                            _retour_vers_origine
                        )

                def _naviguer_produit_depuis_fiche(produit_id: int):
                    page_origine = fenetre._index_actif
                    fenetre._changer_page(4)
                    vue_produits.ouvrir_fiche(produit_id)
                    _safe_disconnect(vue_produits.fiche_produit.retour_demande)
                    vue_produits.fiche_produit.retour_demande.connect(
                        lambda: (
                            fenetre._changer_page(page_origine),
                            vue_produits.fiche_produit.retour_demande.disconnect(),
                            vue_produits.fiche_produit.retour_demande.connect(
                                lambda: vue_produits._changer_page("liste")
                            ),
                        )
                    )

                vue_vente.fiche_vente.client_demande.connect(
                    _naviguer_client_depuis_fiche
                )
                vue_vente.fiche_vente.produit_demande.connect(
                    _naviguer_produit_depuis_fiche
                )
                vue_vente.fiche_commande.client_demande.connect(
                    _naviguer_client_depuis_fiche
                )
                vue_vente.fiche_commande.produit_demande.connect(
                    _naviguer_produit_depuis_fiche
                )

                fenetre.mode_changed.connect(
                    vue_codes_promo_creation.mettre_a_jour_mode
                )
                fenetre.mode_changed.connect(
                    vue_codes_promo_recherche.mettre_a_jour_mode
                )
                fenetre.mode_changed.connect(vue_produits.mettre_a_jour_mode)
                fenetre.mode_changed.connect(vue_vente.mettre_a_jour_mode)
                fenetre.mode_changed.connect(vue_taches.mettre_a_jour_mode)
                fenetre.mode_changed.connect(vue_calendrier.mettre_a_jour_mode)
                fenetre.mode_changed.connect(vue_aide.mettre_a_jour_mode)

                vue_taches.viewmodel.tache_creee.connect(
                    lambda _: vue_calendrier._rafraichir_vue()
                )
                vue_taches.viewmodel.tache_modifiee.connect(
                    lambda _: vue_calendrier._rafraichir_vue()
                )
                if hasattr(vue_vente, "commande_vm"):
                    vue_vente.commande_vm.commande_creee.connect(
                        lambda _: vue_calendrier._rafraichir_vue()
                    )

                def ouvrir_fiche_tache(tache_id: int):
                    page_origine = fenetre._index_actif
                    fenetre._changer_page(6)
                    vue_taches.ouvrir_fiche(tache_id)
                    _safe_disconnect(vue_taches.fiche_tache.retour_demande)
                    vue_taches.fiche_tache.retour_demande.connect(
                        lambda: (
                            fenetre._changer_page(page_origine),
                            vue_taches.fiche_tache.retour_demande.disconnect(),
                            vue_taches.fiche_tache.retour_demande.connect(
                                lambda: vue_taches._changer_page("liste")
                            ),
                        )
                    )

                vue_calendrier.tache_selectionnee.connect(ouvrir_fiche_tache)

                def ouvrir_fiche_commande_calendrier(commande_id: int):
                    page_origine = fenetre._index_actif
                    fenetre._changer_page(1)
                    vue_vente.ouvrir_fiche_commande(commande_id)
                    _safe_disconnect(vue_vente.fiche_commande.retour_demande)
                    vue_vente.fiche_commande.retour_demande.connect(
                        lambda: (
                            fenetre._changer_page(page_origine),
                            vue_vente.fiche_commande.retour_demande.disconnect(),
                            vue_vente.fiche_commande.retour_demande.connect(
                                lambda: vue_vente._changer_page("historique")
                            ),
                        )
                    )

                vue_calendrier.commande_selectionnee.connect(
                    ouvrir_fiche_commande_calendrier
                )

                def ouvrir_detail_evenement(evenement_id: int):
                    page_origine = fenetre._index_actif
                    fenetre._changer_page(14)
                    vue_fiche_evenement.charger_evenement(evenement_id)
                    _safe_disconnect(vue_fiche_evenement.retour_demande)
                    vue_fiche_evenement.retour_demande.connect(
                        lambda: fenetre._changer_page(page_origine)
                    )

                vue_fiche_evenement.evenement_modifie.connect(
                    lambda: vue_calendrier._rafraichir_vue()
                )
                vue_fiche_evenement.evenement_supprime.connect(
                    lambda: vue_calendrier._rafraichir_vue()
                )
                vue_calendrier.evenement_selectionne.connect(ouvrir_detail_evenement)

                def naviguer_association(type_assoc: str, assoc_id: int):
                    if type_assoc == "client":
                        fenetre._changer_page(0)
                        vue_client.ouvrir_fiche_client(assoc_id)
                    elif type_assoc == "vente":
                        fenetre._changer_page(1)
                        vue_vente.ouvrir_fiche_vente_par_id(assoc_id)
                    elif type_assoc == "commande":
                        fenetre._changer_page(1)
                        vue_vente.ouvrir_fiche_commande(assoc_id)
                    elif type_assoc == "produit":
                        fenetre._changer_page(2)
                    elif type_assoc == "code_promo":
                        fenetre._changer_page(3)
                    elif type_assoc == "evenement":
                        ouvrir_detail_evenement(assoc_id)

                vue_taches.association_navigation.connect(naviguer_association)

                from utils.email_scheduler import EmailScheduler

                _email_scheduler = EmailScheduler(intervalle_ms=60_000)
                _email_scheduler.demarrer()
                app._email_scheduler = _email_scheduler

                logger.info("Interface construite avec succès")

                _state["fenetre"] = fenetre
                _try_show_window()

            except Exception as e:
                logger.critical(f"Erreur fatale construction : {e}", exc_info=True)
                app.quit()

        # 16ms de délai → le splash peint sa première frame, puis on construit tout
        QTimer.singleShot(16, _construire_app)

        code_retour = app.exec()
        logger.info(f"Fermeture de l'application (code: {code_retour})")
        return code_retour

    except Exception as e:
        logger.critical(f"Erreur fatale au démarrage : {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
