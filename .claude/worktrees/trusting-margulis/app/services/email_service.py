"""Service d'envoi et de reception d'emails en arriere-plan.

Fournit des QThread specialises pour envoyer et recevoir des emails
sans bloquer l'interface graphique.
"""

import logging
import smtplib
import imaplib
import email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr, parseaddr
from typing import Optional

from PySide6.QtCore import QThread, Signal

from models.parametres import ParametresModel

logger = logging.getLogger(__name__)


class EmailSendThread(QThread):
    """Thread d'envoi d'emails via SMTP.

    Signals:
        progression: (int, int) -> (envoye, total)
        envoi_termine: () -> tous les envois termines avec succes
        erreur: (str) -> message d'erreur
        email_envoye: (str) -> adresse du destinataire envoye avec succes
    """

    progression = Signal(int, int)
    envoi_termine = Signal()
    erreur = Signal(str)
    email_envoye = Signal(str)

    def __init__(
        self,
        destinataires: list[str],
        objet: str,
        contenu_html: str,
        pieces_jointes: list[str] = None,
    ):
        super().__init__()
        self.destinataires = destinataires
        self.objet = objet
        self.contenu_html = contenu_html
        self.pieces_jointes = pieces_jointes or []
        self._annule = False

    def annuler(self):
        """Demande l'annulation de l'envoi."""
        self._annule = True

    def run(self):
        """Execute l'envoi des emails dans le thread."""
        params = ParametresModel()
        smtp_host = params.obtenir_parametre("smtp_host") or ""
        smtp_port = int(params.obtenir_parametre("smtp_port") or "587")
        smtp_email = params.obtenir_parametre("email_recuperation") or ""
        smtp_password = params.obtenir_parametre("smtp_password") or ""
        nom_entreprise = params.obtenir_parametre("nom_entreprise") or "Nexa"

        if not smtp_host or not smtp_email or not smtp_password:
            self.erreur.emit(
                "Configuration SMTP incomplete. "
                "Verifiez les parametres (smtp_host, email_recuperation, smtp_password)."
            )
            return

        try:
            logger.info("Connexion SMTP a %s:%s", smtp_host, smtp_port)
            serveur = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            serveur.ehlo()
            serveur.starttls()
            serveur.login(smtp_email, smtp_password)
        except Exception as e:
            logger.error("Echec connexion SMTP : %s", e)
            self.erreur.emit(f"Echec de connexion au serveur SMTP : {e}")
            return

        total = len(self.destinataires)
        envoyes = 0

        for dest in self.destinataires:
            if self._annule:
                logger.info("Envoi annule par l'utilisateur")
                break

            try:
                msg = self._construire_message(
                    smtp_email, nom_entreprise, dest
                )
                serveur.sendmail(smtp_email, dest, msg.as_string())
                envoyes += 1
                self.email_envoye.emit(dest)
                self.progression.emit(envoyes, total)
                logger.debug("Email envoye a %s (%d/%d)", dest, envoyes, total)
            except Exception as e:
                logger.error("Echec envoi a %s : %s", dest, e)

        try:
            serveur.quit()
        except Exception:
            pass

        if not self._annule:
            self.envoi_termine.emit()
            logger.info("Envoi termine : %d/%d emails envoyes", envoyes, total)

    def _construire_message(
        self, expediteur: str, nom_expediteur: str, destinataire: str
    ) -> MIMEMultipart:
        """Construit le message MIME."""
        msg = MIMEMultipart("mixed")
        msg["From"] = formataddr((nom_expediteur, expediteur))
        msg["To"] = destinataire
        msg["Subject"] = self.objet

        corps = MIMEText(self.contenu_html, "html", "utf-8")
        msg.attach(corps)

        for chemin in self.pieces_jointes:
            try:
                with open(chemin, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                nom_fichier = chemin.split("/")[-1].split("\\")[-1]
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{nom_fichier}"',
                )
                msg.attach(part)
            except Exception as e:
                logger.warning("Piece jointe ignoree '%s' : %s", chemin, e)

        return msg


class EmailReceiveThread(QThread):
    """Thread de reception d'emails via IMAP.

    Signals:
        emails_recus: (list[dict]) -> liste des emails recus
        erreur: (str) -> message d'erreur
        progression: (int, int) -> (traite, total)
    """

    emails_recus = Signal(list)
    erreur = Signal(str)
    progression = Signal(int, int)

    def __init__(self, limite: int = 50):
        super().__init__()
        self.limite = limite

    def run(self):
        """Recupere les emails depuis le serveur IMAP."""
        params = ParametresModel()
        imap_host = params.obtenir_parametre("imap_host") or ""
        imap_port = int(params.obtenir_parametre("imap_port") or "993")
        imap_email = params.obtenir_parametre("email_recuperation") or ""
        imap_password = params.obtenir_parametre("smtp_password") or ""

        if not imap_host or not imap_email or not imap_password:
            self.erreur.emit(
                "Configuration IMAP incomplete. "
                "Verifiez les parametres (imap_host, email_recuperation, smtp_password)."
            )
            return

        try:
            logger.info("Connexion IMAP a %s:%s", imap_host, imap_port)
            mailbox = imaplib.IMAP4_SSL(imap_host, imap_port)
            mailbox.login(imap_email, imap_password)
            mailbox.select("INBOX")
        except Exception as e:
            logger.error("Echec connexion IMAP : %s", e)
            self.erreur.emit(f"Echec de connexion au serveur IMAP : {e}")
            return

        try:
            _, data = mailbox.search(None, "ALL")
            ids = data[0].split()

            # Prendre les N derniers emails
            ids_recents = ids[-self.limite:] if len(ids) > self.limite else ids
            ids_recents.reverse()

            total = len(ids_recents)
            resultats = []

            for idx, mail_id in enumerate(ids_recents):
                try:
                    _, msg_data = mailbox.fetch(mail_id, "(RFC822)")
                    raw = msg_data[0][1]
                    msg = email_lib.message_from_bytes(raw)

                    expediteur_nom, expediteur_email = parseaddr(
                        msg.get("From", "")
                    )
                    objet = self._decoder_header(msg.get("Subject", ""))
                    date_str = msg.get("Date", "")

                    # Extraire le corps texte
                    corps = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            ctype = part.get_content_type()
                            if ctype == "text/html":
                                corps = part.get_payload(decode=True).decode(
                                    part.get_content_charset() or "utf-8",
                                    errors="replace",
                                )
                                break
                            elif ctype == "text/plain" and not corps:
                                corps = part.get_payload(decode=True).decode(
                                    part.get_content_charset() or "utf-8",
                                    errors="replace",
                                )
                    else:
                        corps = msg.get_payload(decode=True).decode(
                            msg.get_content_charset() or "utf-8",
                            errors="replace",
                        )

                    # Pieces jointes
                    pj = []
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_disposition() == "attachment":
                                pj.append(part.get_filename() or "fichier")

                    resultats.append({
                        "expediteur_email": expediteur_email,
                        "expediteur_nom": expediteur_nom,
                        "objet": objet,
                        "date_reception": date_str,
                        "corps": corps,
                        "pieces_jointes": ", ".join(pj) if pj else "",
                        "lu": False,
                    })

                    self.progression.emit(idx + 1, total)
                except Exception as e:
                    logger.warning("Email %s ignore : %s", mail_id, e)

            mailbox.logout()
            self.emails_recus.emit(resultats)
            logger.info("%d emails recuperes", len(resultats))

        except Exception as e:
            logger.error("Erreur lors de la recuperation des emails : %s", e)
            self.erreur.emit(f"Erreur lors de la recuperation : {e}")
            try:
                mailbox.logout()
            except Exception:
                pass

    @staticmethod
    def _decoder_header(header: str) -> str:
        """Decode un header RFC2047."""
        if not header:
            return ""
        parties = email_lib.header.decode_header(header)
        resultat = []
        for contenu, charset in parties:
            if isinstance(contenu, bytes):
                resultat.append(
                    contenu.decode(charset or "utf-8", errors="replace")
                )
            else:
                resultat.append(contenu)
        return " ".join(resultat)
