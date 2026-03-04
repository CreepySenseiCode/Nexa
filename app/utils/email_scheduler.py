"""Planificateur d'envoi d'emails programmés."""
from __future__ import annotations

import logging
from datetime import datetime
from PySide6.QtCore import QObject, QTimer, Signal

from models.database import get_db
from utils.email_sender import EmailSender

logger = logging.getLogger(__name__)


class EmailScheduler(QObject):
    """Vérifie périodiquement les emails programmés et les envoie."""

    email_envoye = Signal(int)   # email_programme_id
    erreur = Signal(str)

    def __init__(self, intervalle_ms: int = 60_000):
        super().__init__()
        self.db = get_db()
        self.sender = EmailSender()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._verifier_programmes)
        self._intervalle = intervalle_ms

    def demarrer(self):
        """Démarre la vérification périodique."""
        logger.info("Scheduler email démarré (intervalle: %dms)", self._intervalle)
        self._timer.start(self._intervalle)

    def arreter(self):
        """Arrête le scheduler."""
        self._timer.stop()

    def programmer_envoi(
        self,
        mail_id: int,
        type_envoi: str,
        date_prog: str,
        heure_prog: str,
        filtres: str = "",
    ) -> int:
        """Programme un envoi futur. Retourne l'ID ou -1."""
        try:
            cursor = self.db.execute(
                """INSERT INTO emails_programmes
                   (mail_id, type_envoi, filtres_selection,
                    date_programmation, heure_programmation, statut)
                   VALUES (?, ?, ?, ?, ?, 'en_attente')""",
                (mail_id, type_envoi, filtres, date_prog, heure_prog),
            )
            logger.info("Email programmé (ID %s) pour %s à %s",
                        cursor.lastrowid, date_prog, heure_prog)
            return cursor.lastrowid
        except Exception as e:
            logger.error("Erreur programmation email : %s", e)
            return -1

    def _verifier_programmes(self):
        """Vérifie et envoie les emails dont l'heure est passée."""
        now = datetime.now()
        date_now = now.strftime("%Y-%m-%d")
        heure_now = now.strftime("%H:%M")

        try:
            programmes = self.db.fetchall(
                """SELECT ep.*, me.objet, me.contenu_html, me.contenu_texte
                   FROM emails_programmes ep
                   LEFT JOIN mails_enregistres me ON me.id = ep.mail_id
                   WHERE ep.statut = 'en_attente'
                     AND (ep.date_programmation < ? OR
                          (ep.date_programmation = ? AND ep.heure_programmation <= ?))""",
                (date_now, date_now, heure_now),
            )

            for prog in programmes:
                self._executer_envoi(prog)

        except Exception as e:
            logger.error("Erreur vérification programmes : %s", e)

    def _executer_envoi(self, prog: dict):
        """Exécute un envoi programmé."""
        prog_id = prog["id"]
        type_envoi = prog.get("type_envoi", "tous_clients")
        objet = prog.get("objet", "")
        contenu = prog.get("contenu_html", "")

        try:
            # Récupérer les destinataires
            destinataires = self._resoudre_destinataires(type_envoi, prog.get("filtres_selection", ""))
            if not destinataires:
                self.db.execute(
                    "UPDATE emails_programmes SET statut = 'echoue' WHERE id = ?",
                    (prog_id,),
                )
                return

            # Envoyer
            result = self.sender.envoyer(destinataires, objet, contenu)

            statut = "envoye" if result["ok"] else "echoue"
            self.db.execute(
                "UPDATE emails_programmes SET statut = ? WHERE id = ?",
                (statut, prog_id),
            )

            # Historique
            self.sender.enregistrer_historique(
                objet=objet,
                contenu=contenu,
                type_envoi=type_envoi,
                destinataires=destinataires,
                statut="envoyé" if result["ok"] else "échoué",
                erreurs=result.get("erreur", ""),
                mail_id=prog.get("mail_id"),
            )

            if result["ok"]:
                self.email_envoye.emit(prog_id)
            else:
                self.erreur.emit(result.get("erreur", "Erreur inconnue"))

        except Exception as e:
            logger.error("Erreur exécution envoi programmé %s : %s", prog_id, e)
            self.db.execute(
                "UPDATE emails_programmes SET statut = 'echoue' WHERE id = ?",
                (prog_id,),
            )

    def _resoudre_destinataires(self, type_envoi: str, filtres: str) -> list[str]:
        """Résout la liste d'emails destinataires selon le type."""
        try:
            if type_envoi == "tous_clients":
                rows = self.db.fetchall(
                    "SELECT email FROM clients WHERE email IS NOT NULL AND email != ''"
                )
                return [r["email"] for r in rows]
            elif type_envoi == "selection" and filtres:
                # Filtres = liste d'IDs séparés par virgules
                ids = [int(x.strip()) for x in filtres.split(",") if x.strip().isdigit()]
                if ids:
                    placeholders = ",".join("?" for _ in ids)
                    rows = self.db.fetchall(
                        f"SELECT email FROM clients WHERE id IN ({placeholders}) "
                        f"AND email IS NOT NULL AND email != ''",
                        tuple(ids),
                    )
                    return [r["email"] for r in rows]
            elif type_envoi == "client_unique" and filtres:
                client_id = int(filtres)
                row = self.db.fetchone(
                    "SELECT email FROM clients WHERE id = ?", (client_id,)
                )
                if row and row.get("email"):
                    return [row["email"]]
            return []
        except Exception as e:
            logger.error("Erreur résolution destinataires : %s", e)
            return []
