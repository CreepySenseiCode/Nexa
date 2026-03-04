"""Module de réception d'emails via IMAP."""
from __future__ import annotations

import logging
import imaplib
import email
from email.header import decode_header
from datetime import datetime

from models.database import get_db

logger = logging.getLogger(__name__)


def _decode_header_value(val) -> str:
    """Décode un header email (potentiellement encodé)."""
    if val is None:
        return ""
    decoded = decode_header(str(val))
    parts = []
    for text, charset in decoded:
        if isinstance(text, bytes):
            parts.append(text.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(str(text))
    return " ".join(parts)


class EmailReceiver:
    """Récupère les emails via IMAP pour les comptes configurés."""

    def __init__(self):
        self.db = get_db()

    def lister_comptes_reception(self) -> list[dict]:
        """Retourne les comptes avec réception IMAP activée."""
        try:
            return self.db.fetchall(
                "SELECT * FROM comptes_email WHERE actif = 1 AND activer_reception = 1"
            )
        except Exception as e:
            logger.error("Erreur listing comptes réception : %s", e)
            return []

    def recuperer_emails(self, compte: dict, nb_max: int = 50) -> dict:
        """Récupère les derniers emails non lus pour un compte.

        Retourne {"ok": bool, "erreur": str, "nb_nouveaux": int}.
        """
        adresse = compte["adresse_email"]
        mdp = compte["mot_de_passe_app"]
        serveur = compte.get("serveur_imap", "imap.gmail.com")
        port = compte.get("port_imap", 993)

        nb_nouveaux = 0
        try:
            imap = imaplib.IMAP4_SSL(serveur, port)
            imap.login(adresse, mdp)
            imap.select("INBOX")

            # Chercher les messages non lus
            status, messages = imap.search(None, "UNSEEN")
            if status != "OK":
                imap.logout()
                return {"ok": False, "erreur": "Recherche IMAP échouée.", "nb_nouveaux": 0}

            msg_ids = messages[0].split()[-nb_max:]  # Derniers N messages

            for msg_id in msg_ids:
                try:
                    status, data = imap.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue

                    raw = data[0][1]
                    msg = email.message_from_bytes(raw)
                    message_id = msg.get("Message-ID", "")

                    # Vérifier si déjà en base
                    existing = self.db.fetchone(
                        "SELECT id FROM emails_recus WHERE message_id = ?",
                        (message_id,),
                    )
                    if existing:
                        continue

                    # Extraire les champs
                    expediteur = _decode_header_value(msg.get("From", ""))
                    exp_email = ""
                    exp_nom = expediteur
                    if "<" in expediteur and ">" in expediteur:
                        exp_nom = expediteur.split("<")[0].strip().strip('"')
                        exp_email = expediteur.split("<")[1].split(">")[0]
                    else:
                        exp_email = expediteur

                    objet = _decode_header_value(msg.get("Subject", "(sans objet)"))
                    date_str = msg.get("Date", "")

                    # Parser la date
                    date_reception = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    try:
                        from email.utils import parsedate_to_datetime
                        dt = parsedate_to_datetime(date_str)
                        date_reception = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass

                    # Extraire le contenu
                    contenu_html = ""
                    contenu_texte = ""
                    pj_list = []

                    if msg.is_multipart():
                        for part in msg.walk():
                            ct = part.get_content_type()
                            disp = str(part.get("Content-Disposition", ""))
                            if "attachment" in disp:
                                filename = part.get_filename()
                                if filename:
                                    pj_list.append(_decode_header_value(filename))
                            elif ct == "text/html":
                                payload = part.get_payload(decode=True)
                                if payload:
                                    charset = part.get_content_charset() or "utf-8"
                                    contenu_html = payload.decode(charset, errors="replace")
                            elif ct == "text/plain" and not contenu_texte:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    charset = part.get_content_charset() or "utf-8"
                                    contenu_texte = payload.decode(charset, errors="replace")
                    else:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            charset = msg.get_content_charset() or "utf-8"
                            if msg.get_content_type() == "text/html":
                                contenu_html = payload.decode(charset, errors="replace")
                            else:
                                contenu_texte = payload.decode(charset, errors="replace")

                    # Chercher le client_id associé
                    client_id = None
                    if exp_email:
                        client = self.db.fetchone(
                            "SELECT id FROM clients WHERE email = ?", (exp_email,)
                        )
                        if client:
                            client_id = client["id"]

                    # Insérer en base
                    self.db.execute(
                        """INSERT INTO emails_recus
                           (expediteur_email, expediteur_nom, client_id, objet,
                            contenu_html, contenu_texte, date_reception, lu,
                            pieces_jointes, compte_email_recepteur, message_id)
                           VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)""",
                        (
                            exp_email, exp_nom, client_id, objet,
                            contenu_html, contenu_texte, date_reception,
                            ", ".join(pj_list) if pj_list else None,
                            adresse, message_id,
                        ),
                    )
                    nb_nouveaux += 1

                except Exception as e:
                    logger.error("Erreur traitement message %s : %s", msg_id, e)

            imap.logout()
            return {"ok": True, "erreur": "", "nb_nouveaux": nb_nouveaux}

        except imaplib.IMAP4.error as e:
            msg = f"Erreur IMAP ({adresse}) : {e}"
            logger.error(msg)
            return {"ok": False, "erreur": msg, "nb_nouveaux": 0}
        except Exception as e:
            logger.error("Erreur réception emails : %s", e)
            return {"ok": False, "erreur": str(e), "nb_nouveaux": 0}

    def recuperer_tous_comptes(self) -> dict:
        """Récupère les emails de tous les comptes actifs.

        Retourne {"ok": bool, "nb_total": int, "erreurs": list[str]}.
        """
        comptes = self.lister_comptes_reception()
        nb_total = 0
        erreurs = []

        for c in comptes:
            result = self.recuperer_emails(c)
            nb_total += result.get("nb_nouveaux", 0)
            if not result["ok"]:
                erreurs.append(result["erreur"])

        return {
            "ok": len(erreurs) == 0,
            "nb_total": nb_total,
            "erreurs": erreurs,
        }

    def marquer_lu(self, email_id: int) -> bool:
        """Marque un email comme lu."""
        try:
            self.db.execute(
                "UPDATE emails_recus SET lu = 1 WHERE id = ?", (email_id,)
            )
            return True
        except Exception as e:
            logger.error("Erreur marquage lu : %s", e)
            return False
