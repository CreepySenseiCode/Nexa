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

    def lister_produits(self, archives: bool = False) -> list[dict]:
        """Retourne les produits actifs ou archives."""
        tous = self.produit_model.lister_produits()
        return [p for p in tous if bool(p.get('archive', 0)) == archives]

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

    def archiver_produit(self, produit_id: int) -> bool:
        """Archive un produit (stock = 0)."""
        return self.modifier_produit(produit_id, {'archive': 1})

    def desarchiver_produit(self, produit_id: int) -> bool:
        """Desarchive un produit."""
        return self.modifier_produit(produit_id, {'archive': 0})

    def rechercher_produits(self, terme: str, archives: bool = False) -> list[dict]:
        """Recherche des produits par nom (contient)."""
        if not terme or len(terme) < 1:
            return self.lister_produits(archives=archives)
        tous = self.lister_produits(archives=archives)
        terme_lower = terme.lower()
        return [p for p in tous if terme_lower in (p.get('nom', '') or '').lower()]

    def obtenir_attributs_produit(self, produit_id: int) -> list[dict]:
        """Retourne les attributs d'un produit avec noms et valeurs."""
        try:
            return self.produit_model.db.fetchall(
                "SELECT ap.nom_attribut, vap.valeur "
                "FROM valeurs_attributs_produits vap "
                "JOIN attributs_produits ap ON ap.id = vap.attribut_id "
                "WHERE vap.produit_id = ?",
                (produit_id,),
            )
        except Exception:
            return []

    def obtenir_stats_ventes_produit(self, produit_id: int) -> dict:
        """Retourne les stats de vente d'un produit."""
        try:
            row = self.produit_model.db.fetchone(
                "SELECT COUNT(*) AS nb_ventes, "
                "COALESCE(SUM(quantite), 0) AS total_qte, "
                "COALESCE(SUM(prix_total), 0) AS total_ca "
                "FROM ventes WHERE produit_id = ?",
                (produit_id,),
            )
            return dict(row) if row else {'nb_ventes': 0, 'total_qte': 0, 'total_ca': 0}
        except Exception:
            return {'nb_ventes': 0, 'total_qte': 0, 'total_ca': 0}

    def obtenir_historique_ventes_produit(self, produit_id: int) -> list[dict]:
        """Retourne l'historique des ventes d'un produit par date."""
        try:
            return self.produit_model.db.fetchall(
                "SELECT DATE(date_vente) AS jour, "
                "SUM(quantite) AS qte, SUM(prix_total) AS ca "
                "FROM ventes WHERE produit_id = ? "
                "GROUP BY DATE(date_vente) ORDER BY jour",
                (produit_id,),
            )
        except Exception:
            return []
