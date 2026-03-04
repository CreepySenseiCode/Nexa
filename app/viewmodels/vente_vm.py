"""ViewModel pour la gestion des ventes."""
from PySide6.QtCore import QObject, Signal
from models.vente import VenteModel
from models.client import ClientModel
from models.produit import ProduitModel
from models.categorie_produit import CategorieProduitModel
from models.code_reduction import CodeReductionModel
from typing import Optional


class VenteViewModel(QObject):
    """ViewModel pour l'onglet Vente."""

    # Signals
    vente_enregistree = Signal(int)  # Emet l'id de la vente
    erreur = Signal(str)
    clients_trouves = Signal(list)  # Pour l'autocomplétion

    def __init__(self):
        super().__init__()
        self.vente_model = VenteModel()
        self.client_model = ClientModel()
        self.produit_model = ProduitModel()
        self.categorie_model = CategorieProduitModel()
        self.code_reduction_model = CodeReductionModel()

    def rechercher_clients(self, terme: str) -> list[dict]:
        """Recherche des clients pour l'autocomplétion.
        Retourne une liste de dicts avec id, nom, prenom, email, telephone."""
        if len(terme) < 1:
            return []
        resultats = self.client_model.rechercher_clients(terme)
        self.clients_trouves.emit(resultats)
        return resultats

    def lister_categories(self) -> list[dict]:
        """Retourne toutes les catégories de produits."""
        return self.categorie_model.lister_categories(actives_uniquement=True)

    def lister_produits(self, categorie_id: int = None) -> list[dict]:
        """Retourne les produits filtrés par catégorie."""
        return self.produit_model.lister_produits(categorie_id)

    def rechercher_produits_avance(self, terme: str) -> list[dict]:
        """Recherche avancée de produits avec JOIN sur catégories.

        Args:
            terme: Terme de recherche (cherche dans nom produit et nom catégorie)

        Returns:
            Liste de dictionnaires avec id, nom, prix, stock, photo, categorie_nom
        """
        if not terme or len(terme.strip()) < 1:
            return []

        from models.database import get_db
        db = get_db()

        # Recherche avec JOIN sur catégories
        query = """
            SELECT
                p.id,
                p.nom,
                p.prix,
                p.stock,
                p.photo,
                p.categorie_id,
                c.nom AS categorie_nom
            FROM produits p
            LEFT JOIN categories_produits c ON p.categorie_id = c.id
            WHERE p.archive = 0
              AND (
                  p.nom LIKE ?
                  OR c.nom LIKE ?
              )
            ORDER BY p.nom
        """

        pattern = f"%{terme.strip()}%"
        resultats = db.fetchall(query, (pattern, pattern))

        return resultats

    def creer_categorie(self, nom: str) -> Optional[int]:
        """Crée une nouvelle catégorie."""
        if not nom.strip():
            self.erreur.emit("Le nom de la catégorie ne peut pas être vide.")
            return None
        return self.categorie_model.creer_categorie(nom.strip())

    def creer_produit(self, categorie_id: int, nom: str, prix: float = 0.0) -> Optional[int]:
        """Crée un nouveau produit."""
        if not nom.strip():
            self.erreur.emit("Le nom du produit ne peut pas être vide.")
            return None
        try:
            return self.produit_model.creer_produit(categorie_id, nom.strip(), prix)
        except Exception as e:
            self.erreur.emit(f"Erreur : {str(e)}")
            return None

    def enregistrer_vente(self, client_id: int, produit_id: int, quantite: int, prix_unitaire: float, date_vente: str = None, notes: str = "", transaction_id: str = None) -> Optional[int]:
        """Enregistre une vente.
        Calcule prix_total = quantite * prix_unitaire.
        Valide les entrées.
        Emet vente_enregistree en cas de succès, erreur en cas d'échec.
        """
        if not client_id:
            self.erreur.emit("Veuillez sélectionner un client.")
            return None
        if not produit_id:
            self.erreur.emit("Veuillez sélectionner un produit.")
            return None
        if quantite < 1:
            self.erreur.emit("La quantité doit être supérieure à 0.")
            return None
        if prix_unitaire < 0:
            self.erreur.emit("Le prix ne peut pas être négatif.")
            return None

        prix_total = round(quantite * prix_unitaire, 2)

        try:
            vente_id = self.vente_model.creer_vente(
                client_id=client_id,
                produit_id=produit_id,
                quantite=quantite,
                prix_unitaire=prix_unitaire,
                prix_total=prix_total,
                date_vente=date_vente,
                notes=notes,
                transaction_id=transaction_id,
            )
            self.vente_enregistree.emit(vente_id)
            return vente_id
        except Exception as e:
            self.erreur.emit(f"Erreur lors de l'enregistrement : {str(e)}")
            return None

    def obtenir_historique_client(self, client_id: int, limite: int = 5) -> list[dict]:
        """Retourne les dernières ventes d'un client."""
        return self.vente_model.obtenir_ventes_client(client_id, limite)

    def obtenir_client(self, client_id: int) -> dict:
        """Retourne les infos basiques d'un client (nom, prenom, email)."""
        return self.client_model.obtenir_client(client_id)

    def obtenir_produit(self, produit_id: int) -> dict:
        """Retourne les infos completes d'un produit."""
        return self.produit_model.obtenir_produit(produit_id)

    def verifier_code_promo(self, code: str, client_id: int = None):
        """Vérifie la validité d'un code promotionnel.
        Retourne (resultat, message, type_erreur)."""
        return self.code_reduction_model.verifier_code(code, client_id)

    def enregistrer_utilisation_code(self, code_id: int, client_id: int, vente_id: int):
        """Enregistre l'utilisation d'un code promo."""
        self.code_reduction_model.enregistrer_utilisation(
            code_id=code_id, client_id=client_id, vente_id=vente_id
        )

    def decrementer_stock(self, produit_id: int, quantite: int) -> bool:
        """Décrémente le stock d'un produit après une vente."""
        produit = self.produit_model.obtenir_produit(produit_id)
        if produit:
            stock_actuel = produit.get('stock', 0) or 0
            nouveau_stock = stock_actuel - quantite
            return self.produit_model.modifier_produit(
                produit_id, {'stock': nouveau_stock}
            )
        return False

    def obtenir_prix_produit(self, produit_id: int) -> float:
        """Retourne le prix d'un produit."""
        produit = self.produit_model.obtenir_produit(produit_id)
        return produit['prix'] if produit else 0.0

    # ------------------------------------------------------------------
    # Transactions (historique)
    # ------------------------------------------------------------------

    def lister_transactions(self) -> list[dict]:
        return self.vente_model.lister_transactions()

    def obtenir_transaction(self, transaction_id: str) -> Optional[dict]:
        return self.vente_model.obtenir_transaction(transaction_id)

    def supprimer_transaction(self, transaction_id: str) -> bool:
        return self.vente_model.supprimer_transaction(transaction_id)
