"""ViewModel pour les produits."""
from PySide6.QtCore import QObject, Signal
from models.produit import ProduitModel
from models.categorie_produit import CategorieProduitModel
from models.attribut_produit import AttributProduitModel
from typing import Optional


class ProduitsViewModel(QObject):
    """ViewModel pour l'onglet Produits."""

    produit_sauvegarde = Signal(int)
    erreur = Signal(str)

    def __init__(self):
        super().__init__()
        self.produit_model = ProduitModel()
        self.categorie_model = CategorieProduitModel()
        self.attribut_model = AttributProduitModel()

    def lister_categories(self) -> list[dict]:
        """Retourne les categories actives."""
        return self.categorie_model.lister_categories(actives_uniquement=True)

    def lister_produits(self) -> list[dict]:
        """Retourne tous les produits."""
        return self.produit_model.lister_produits()

    def obtenir_produit(self, produit_id: int) -> Optional[dict]:
        """Retourne un produit par ID."""
        return self.produit_model.obtenir_produit(produit_id)

    def creer_produit(self, categorie_id, nom: str, prix: float, stock: int = 0, description: str = "") -> Optional[int]:
        """Cree un produit. Retourne l'ID ou None."""
        if not nom.strip():
            self.erreur.emit("Le nom du produit ne peut pas etre vide.")
            return None
        if prix <= 0:
            self.erreur.emit("Le prix doit etre superieur a 0.")
            return None
        try:
            produit_id = self.produit_model.creer_produit(
                categorie_id=categorie_id, nom=nom.strip(),
                prix=prix, stock=stock, description=description,
            )
            if produit_id and produit_id > 0:
                self.produit_sauvegarde.emit(produit_id)
            return produit_id
        except Exception as e:
            self.erreur.emit(f"Erreur : {e}")
            return None

    def modifier_produit(self, produit_id: int, donnees: dict) -> bool:
        """Modifie un produit existant."""
        try:
            return self.produit_model.modifier_produit(produit_id, donnees)
        except Exception as e:
            self.erreur.emit(f"Erreur : {e}")
            return False

    def supprimer_produit(self, produit_id: int) -> bool:
        """Supprime un produit."""
        try:
            return self.produit_model.supprimer_produit(produit_id)
        except Exception as e:
            self.erreur.emit(f"Erreur : {e}")
            return False

    def lister_attributs_globaux(self) -> list[dict]:
        """Retourne les noms d'attributs globaux."""
        return self.attribut_model.lister_attributs_globaux()
