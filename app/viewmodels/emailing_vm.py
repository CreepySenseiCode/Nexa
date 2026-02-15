"""ViewModel pour l'emailing."""
from PySide6.QtCore import QObject, Signal
from models.client import ClientModel
from models.database import get_db


class EmailingViewModel(QObject):
    """ViewModel pour l'onglet Emailing."""

    erreur = Signal(str)

    def __init__(self):
        super().__init__()
        self.client_model = ClientModel()
        self.db = get_db()

    def rechercher_clients(self, texte: str, limite: int = 10) -> list[dict]:
        """Recherche des clients par nom, prenom ou email."""
        if len(texte) < 2:
            return []
        try:
            return self.db.fetchall(
                """
                SELECT id, nom, prenom, email
                FROM clients
                WHERE nom LIKE ? OR prenom LIKE ? OR email LIKE ?
                LIMIT ?
                """,
                (f"%{texte}%", f"%{texte}%", f"%{texte}%", limite),
            )
        except Exception as e:
            self.erreur.emit(f"Erreur recherche : {e}")
            return []

    def filtrer_clients(self, age_min: int, age_max: int, situation: str = None, interets: list = None) -> list[dict]:
        """Filtre les clients selon les criteres."""
        try:
            where_clauses = []
            params = []

            where_clauses.append(
                "(julianday('now') - julianday(date_naissance)) / 365.25 BETWEEN ? AND ?"
            )
            params.extend([age_min, age_max])

            if situation and situation != "Toutes":
                where_clauses.append("situation_maritale = ?")
                params.append(situation)

            if interets:
                for interet in interets:
                    where_clauses.append("centres_interet LIKE ?")
                    params.append(f"%{interet.strip()}%")

            query = f"""
                SELECT id, nom, prenom, email
                FROM clients
                WHERE {' AND '.join(where_clauses)}
            """
            return self.db.fetchall(query, tuple(params))
        except Exception as e:
            self.erreur.emit(f"Erreur filtres : {e}")
            return []

    def charger_tous_les_clients(self) -> list[dict]:
        """Charge tous les clients."""
        try:
            return self.db.fetchall(
                "SELECT id, nom, prenom, email FROM clients"
            )
        except Exception as e:
            self.erreur.emit(f"Erreur chargement : {e}")
            return []
