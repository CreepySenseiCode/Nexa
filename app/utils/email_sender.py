"""Module d'envoi d'emails via SMTP (Gmail / autre)."""
from __future__ import annotations

import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from models.database import get_db

logger = logging.getLogger(__name__)


class EmailSender:
    """Envoie des emails via SMTP en utilisant les comptes configurés."""

    def __init__(self):
        self.db = get_db()

    # ------------------------------------------------------------------
    # Comptes
    # ------------------------------------------------------------------

    def lister_comptes(self) -> list[dict]:
        """Retourne la liste des comptes email actifs."""
        try:
            return self.db.fetchall(
                "SELECT * FROM comptes_email WHERE actif = 1 ORDER BY ordre_utilisation"
            )
        except Exception as e:
            logger.error("Erreur listing comptes email : %s", e)
            return []

    def obtenir_compte_disponible(self) -> dict | None:
        """Retourne le premier compte avec du quota disponible."""
        from datetime import date

        comptes = self.lister_comptes()
        today = date.today().isoformat()

        for c in comptes:
            # Reset quotidien si nécessaire
            if (c.get("date_dernier_reset") or "") < today:
                self.db.execute(
                    "UPDATE comptes_email SET quota_utilise_aujourd_hui = 0, "
                    "date_dernier_reset = ? WHERE id = ?",
                    (today, c["id"]),
                )
                c["quota_utilise_aujourd_hui"] = 0

            if c.get("quota_utilise_aujourd_hui", 0) < c.get("quota_journalier", 500):
                return c
        return None

    def ajouter_compte(
        self, adresse: str, mot_de_passe: str, nom_affichage: str,
        serveur_smtp: str = "smtp.gmail.com", port_smtp: int = 587,
        serveur_imap: str = "imap.gmail.com", port_imap: int = 993,
    ) -> int:
        """Ajoute un compte email. Retourne l'ID ou -1."""
        try:
            cursor = self.db.execute(
                """INSERT INTO comptes_email
                   (adresse_email, mot_de_passe_app, nom_affichage,
                    serveur_smtp, port_smtp, serveur_imap, port_imap)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (adresse, mot_de_passe, nom_affichage,
                 serveur_smtp, port_smtp, serveur_imap, port_imap),
            )
            return cursor.lastrowid
        except Exception as e:
            logger.error("Erreur ajout compte email : %s", e)
            return -1

    def supprimer_compte(self, compte_id: int) -> bool:
        try:
            self.db.execute("DELETE FROM comptes_email WHERE id = ?", (compte_id,))
            return True
        except Exception as e:
            logger.error("Erreur suppression compte : %s", e)
            return False

    # ------------------------------------------------------------------
    # Envoi
    # ------------------------------------------------------------------

    def envoyer(
        self,
        destinataires: list[str],
        objet: str,
        contenu_html: str,
        contenu_texte: str = "",
        pieces_jointes: list[str] | None = None,
        compte: dict | None = None,
    ) -> dict:
        """Envoie un email.

        Retourne {"ok": bool, "erreur": str, "nb_envoyes": int}.
        """
        if not compte:
            compte = self.obtenir_compte_disponible()
        if not compte:
            return {"ok": False, "erreur": "Aucun compte email disponible.", "nb_envoyes": 0}

        adresse = compte["adresse_email"]
        mdp = compte["mot_de_passe_app"]
        serveur = compte.get("serveur_smtp", "smtp.gmail.com")
        port = compte.get("port_smtp", 587)
        nom_affichage = compte.get("nom_affichage", adresse)

        nb_ok = 0
        erreurs = []

        try:
            with smtplib.SMTP(serveur, port, timeout=30) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(adresse, mdp)

                for dest in destinataires:
                    try:
                        msg = MIMEMultipart("alternative")
                        msg["From"] = f"{nom_affichage} <{adresse}>"
                        msg["To"] = dest
                        msg["Subject"] = objet

                        if contenu_texte:
                            msg.attach(MIMEText(contenu_texte, "plain", "utf-8"))
                        msg.attach(MIMEText(contenu_html, "html", "utf-8"))

                        # Pièces jointes
                        for pj_path in (pieces_jointes or []):
                            if os.path.isfile(pj_path):
                                with open(pj_path, "rb") as f:
                                    part = MIMEBase("application", "octet-stream")
                                    part.set_payload(f.read())
                                encoders.encode_base64(part)
                                part.add_header(
                                    "Content-Disposition",
                                    f"attachment; filename={os.path.basename(pj_path)}",
                                )
                                msg.attach(part)

                        smtp.sendmail(adresse, dest, msg.as_string())
                        nb_ok += 1
                    except Exception as e:
                        erreurs.append(f"{dest}: {e}")
                        logger.error("Erreur envoi à %s : %s", dest, e)

            # Mettre à jour le quota
            self.db.execute(
                "UPDATE comptes_email SET quota_utilise_aujourd_hui = "
                "quota_utilise_aujourd_hui + ? WHERE id = ?",
                (nb_ok, compte["id"]),
            )

            if erreurs:
                return {
                    "ok": nb_ok > 0,
                    "erreur": "; ".join(erreurs),
                    "nb_envoyes": nb_ok,
                }
            return {"ok": True, "erreur": "", "nb_envoyes": nb_ok}

        except smtplib.SMTPAuthenticationError:
            msg = "Authentification SMTP échouée. Vérifiez le mot de passe d'application."
            logger.error(msg)
            return {"ok": False, "erreur": msg, "nb_envoyes": 0}
        except Exception as e:
            logger.error("Erreur SMTP : %s", e)
            return {"ok": False, "erreur": str(e), "nb_envoyes": 0}

    # ------------------------------------------------------------------
    # Historique
    # ------------------------------------------------------------------

    def enregistrer_historique(
        self,
        objet: str,
        contenu: str,
        type_envoi: str,
        destinataires: list[str],
        statut: str = "envoyé",
        compte_email: str = "",
        erreurs: str = "",
        mail_id: int | None = None,
        en_reponse_a: int | None = None,
    ) -> int:
        """Enregistre un envoi dans l'historique. Retourne l'ID."""
        try:
            cursor = self.db.execute(
                """INSERT INTO historique_emails
                   (mail_id, objet, contenu, type_envoi, nombre_destinataires,
                    destinataires, statut, compte_email_utilise, erreurs, en_reponse_a)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    mail_id, objet, contenu, type_envoi, len(destinataires),
                    ", ".join(destinataires), statut, compte_email, erreurs,
                    en_reponse_a,
                ),
            )
            return cursor.lastrowid
        except Exception as e:
            logger.error("Erreur historique email : %s", e)
            return -1
