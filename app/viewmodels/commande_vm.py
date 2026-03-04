"""ViewModel pour la gestion des commandes."""

import uuid
from typing import Optional

from PySide6.QtCore import QObject, Signal

from models.commande import CommandeModel
from models.client import ClientModel
from models.produit import ProduitModel
from models.vente import VenteModel
from models.database import get_db


class CommandeViewModel(QObject):
    """ViewModel pour l'onglet Commandes."""

    commande_creee = Signal(int)
    erreur = Signal(str)

    def __init__(self):
        super().__init__()
        self.commande_model = CommandeModel()
        self.client_model = ClientModel()
        self.produit_model = ProduitModel()
        self.vente_model = VenteModel()

    def rechercher_clients(self, terme: str) -> list[dict]:
        if len(terme) < 1:
            return []
        return self.client_model.rechercher_clients(terme)

    def rechercher_produits(self, terme: str) -> list[dict]:
        if not terme or len(terme.strip()) < 1:
            return []
        db = get_db()
        query = """
            SELECT p.id, p.nom, p.prix, p.stock, p.photo, p.categorie_id,
                   c.nom AS categorie_nom
            FROM produits p
            LEFT JOIN categories_produits c ON p.categorie_id = c.id
            WHERE p.archive = 0
              AND (p.nom LIKE ? OR c.nom LIKE ?)
            ORDER BY p.nom
        """
        pattern = f"%{terme.strip()}%"
        return db.fetchall(query, (pattern, pattern))

    def obtenir_client(self, client_id: int) -> Optional[dict]:
        return self.client_model.obtenir_client(client_id)

    def obtenir_produit(self, produit_id: int) -> Optional[dict]:
        return self.produit_model.obtenir_produit(produit_id)

    def creer_commande_complete(
        self,
        client_id: int,
        articles: list[dict],
        date_prevue: str,
        heure_prevue: Optional[str] = None,
        notes: str = "",
    ) -> Optional[int]:
        if not client_id:
            self.erreur.emit("Veuillez sélectionner un client.")
            return None
        if not articles:
            self.erreur.emit("Veuillez ajouter au moins un article.")
            return None
        if not date_prevue:
            self.erreur.emit("Veuillez définir une date prévue.")
            return None

        total = sum(
            a["quantite"] * a["prix_unitaire"] for a in articles
        )

        db = get_db()
        try:
            with db.transaction():
                commande_id = self.commande_model.creer_commande(
                    client_id=client_id,
                    date_prevue=date_prevue,
                    heure_prevue=heure_prevue,
                    notes=notes,
                    total=round(total, 2),
                )
                if commande_id < 0:
                    self.erreur.emit("Erreur lors de la création de la commande.")
                    return None

                for article in articles:
                    self.commande_model.ajouter_article(
                        commande_id=commande_id,
                        produit_id=article["produit_id"],
                        quantite=article["quantite"],
                        prix_unitaire=article["prix_unitaire"],
                    )

            self.commande_creee.emit(commande_id)
            return commande_id
        except Exception as e:
            self.erreur.emit(f"Erreur : {str(e)}")
            return None

    def lister_commandes(self, statut: Optional[str] = None) -> list[dict]:
        return self.commande_model.lister_commandes(statut)

    def obtenir_commande(self, commande_id: int) -> Optional[dict]:
        return self.commande_model.obtenir_commande(commande_id)

    def modifier_statut(self, commande_id: int, statut: str) -> bool:
        return self.commande_model.modifier_statut(commande_id, statut)

    def supprimer_commande(self, commande_id: int) -> bool:
        return self.commande_model.supprimer_commande(commande_id)

    def terminer_commande(self, commande_id: int) -> Optional[str]:
        """Termine une commande et la convertit en vente.

        Returns:
            Le transaction_id de la vente créée, ou None en cas d'erreur.
        """
        commande = self.commande_model.obtenir_commande(commande_id)
        if not commande:
            self.erreur.emit("Commande introuvable.")
            return None

        articles = commande.get("articles", [])
        if not articles:
            self.erreur.emit("La commande ne contient aucun article.")
            return None

        # Vérifier le stock
        for article in articles:
            produit = self.produit_model.obtenir_produit(article["produit_id"])
            if produit:
                stock = produit.get("stock", 0) or 0
                if article["quantite"] > stock:
                    self.erreur.emit(
                        f"Stock insuffisant pour '{article['produit_nom']}' "
                        f"(stock: {stock}, demandé: {article['quantite']})"
                    )
                    return None

        db = get_db()
        txn_id = str(uuid.uuid4())
        try:
            with db.transaction():
                for article in articles:
                    prix_total = round(
                        article["quantite"] * article["prix_unitaire"], 2
                    )
                    self.vente_model.creer_vente(
                        client_id=commande["client_id"],
                        produit_id=article["produit_id"],
                        quantite=article["quantite"],
                        prix_unitaire=article["prix_unitaire"],
                        prix_total=prix_total,
                        notes=commande.get("notes", ""),
                        transaction_id=txn_id,
                    )
                    # Décrémenter le stock
                    produit = self.produit_model.obtenir_produit(article["produit_id"])
                    if produit:
                        stock_actuel = produit.get("stock", 0) or 0
                        self.produit_model.modifier_produit(
                            article["produit_id"],
                            {"stock": stock_actuel - article["quantite"]},
                        )

                self.commande_model.modifier_statut(commande_id, "terminee")

            return txn_id
        except Exception as e:
            self.erreur.emit(f"Erreur conversion en vente : {str(e)}")
            return None
