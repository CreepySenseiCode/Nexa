"""ViewModel pour la gestion des tâches."""

from typing import Optional

from PySide6.QtCore import QObject, Signal

from models.tache import TacheModel
from models.categorie_tache import CategorieTacheModel


class TacheViewModel(QObject):
    """ViewModel pour l'onglet Tâches."""

    tache_creee = Signal(int)
    tache_modifiee = Signal(int)
    erreur = Signal(str)

    def __init__(self):
        super().__init__()
        self.tache_model = TacheModel()
        self.categorie_model = CategorieTacheModel()

    # ------------------------------------------------------------------
    # Tâches
    # ------------------------------------------------------------------

    def creer_tache(
        self,
        titre: str,
        description: str = "",
        priorite: int = 5,
        categorie_id: Optional[int] = None,
        date_echeance: Optional[str] = None,
        heure_echeance: Optional[str] = None,
        visibilite: str = "tous",
        commande_id: Optional[int] = None,
        couleur: Optional[str] = None,
        parent_id: Optional[int] = None,
        niveau: int = 0,
        type_recurrence: Optional[str] = None,
        intervalle_recurrence: int = 1,
        date_fin_recurrence: Optional[str] = None,
        client_id: Optional[int] = None,
        vente_id: Optional[int] = None,
        produit_id: Optional[int] = None,
        code_promo_id: Optional[int] = None,
        evenement_id: Optional[int] = None,
    ) -> Optional[int]:
        if not titre.strip():
            self.erreur.emit("Le titre ne peut pas être vide.")
            return None
        if priorite < 1 or priorite > 10:
            self.erreur.emit("La priorité doit être entre 1 et 10.")
            return None

        tache_id = self.tache_model.creer_tache(
            titre=titre.strip(),
            description=description,
            priorite=priorite,
            categorie_id=categorie_id,
            date_echeance=date_echeance,
            heure_echeance=heure_echeance,
            visibilite=visibilite,
            commande_id=commande_id,
            couleur=couleur,
            parent_id=parent_id,
            niveau=niveau,
            type_recurrence=type_recurrence,
            intervalle_recurrence=intervalle_recurrence,
            date_fin_recurrence=date_fin_recurrence,
            client_id=client_id,
            vente_id=vente_id,
            produit_id=produit_id,
            code_promo_id=code_promo_id,
            evenement_id=evenement_id,
        )
        if tache_id > 0:
            self.tache_creee.emit(tache_id)
            return tache_id
        self.erreur.emit("Erreur lors de la création de la tâche.")
        return None

    def modifier_tache(self, tache_id: int, data: dict) -> bool:
        ok = self.tache_model.modifier_tache(tache_id, data)
        if ok:
            self.tache_modifiee.emit(tache_id)
        return ok

    def basculer_terminee(self, tache_id: int) -> bool:
        return self.tache_model.basculer_terminee(tache_id)

    def basculer_cochee(self, tache_id: int) -> bool:
        return self.tache_model.basculer_cochee(tache_id)

    def obtenir_tache(self, tache_id: int) -> Optional[dict]:
        return self.tache_model.obtenir_tache(tache_id)

    def supprimer_tache(self, tache_id: int) -> bool:
        return self.tache_model.supprimer_tache(tache_id)

    def restaurer_tache(self, tache_id: int) -> bool:
        return self.tache_model.restaurer_tache(tache_id)

    def supprimer_definitivement(self, tache_id: int) -> bool:
        return self.tache_model.supprimer_definitivement(tache_id)

    def valider_mission(self, tache_id: int) -> bool:
        ok = self.tache_model.valider_mission(tache_id)
        if ok:
            self.tache_modifiee.emit(tache_id)
        return ok

    def lister_taches(
        self,
        mode_admin: bool = True,
        categorie_id: Optional[int] = None,
        inclure_terminees: bool = True,
    ) -> list[dict]:
        if mode_admin:
            # Admin voit "tous" et "admin_seul" — PAS "fonctionnel_seul"
            visibilite = ["tous", "admin_seul"]
        else:
            visibilite = ["tous", "fonctionnel_seul"]

        return self.tache_model.lister_taches(
            visibilite_filtre=visibilite,
            categorie_id=categorie_id,
            inclure_terminees=inclure_terminees,
        )

    def lister_taches_supprimees(self, mode_admin: bool = True) -> list[dict]:
        if mode_admin:
            visibilite = ["tous", "admin_seul"]
        else:
            visibilite = ["tous", "fonctionnel_seul"]
        return self.tache_model.lister_taches_supprimees(visibilite)

    def lister_taches_triees(
        self,
        mode_admin: bool = True,
        categorie_id: Optional[int] = None,
        inclure_terminees: bool = True,
        criteres_tri: Optional[list[str]] = None,
        directions: Optional[list[bool]] = None,
    ) -> list[dict]:
        """Liste les tâches avec tri multi-critères.

        En mode fonctionnel : tâches "tous" (admin) en premier, puis fonctionnelles.
        """
        taches = self.lister_taches(mode_admin, categorie_id, inclure_terminees)

        # Filtrer les sous-tâches (elles seront insérées après leur parent)
        parents = [t for t in taches if not t.get("parent_id")]
        sous_taches_map: dict[int, list[dict]] = {}
        for t in taches:
            pid = t.get("parent_id")
            if pid:
                sous_taches_map.setdefault(pid, []).append(t)

        if not criteres_tri:
            criteres_tri = []

        if directions is None:
            directions = [True] * len(criteres_tri)

        def tri_key(tache):
            keys = []
            for i, critere in enumerate(criteres_tri):
                asc = directions[i] if i < len(directions) else True
                if critere == "date":
                    val = tache.get("date_echeance") or "9999-12-31"
                elif critere == "priorite":
                    # Par défaut P10 (urgent) en premier → valeur négative
                    val = -tache.get("priorite", 5)
                elif critere == "categorie":
                    val = (tache.get("categorie_nom") or "").lower()
                elif critere == "titre":
                    val = (tache.get("titre") or "").lower()
                else:
                    val = ""

                if not asc:
                    if isinstance(val, int):
                        val = -val
                    elif isinstance(val, str):
                        val = "".join(
                            chr(0xFFFF - ord(c)) if ord(c) < 0xFFFF else c
                            for c in val
                        )
                keys.append(val)
            return tuple(keys)

        # Séparer terminées et non-terminées
        non_terminees = [t for t in parents if not t.get("terminee")]
        terminees = [t for t in parents if t.get("terminee")]

        if criteres_tri:
            non_terminees.sort(key=tri_key)
            terminees.sort(key=tri_key)

        # En mode fonctionnel : tâches "tous" (admin) en premier
        if not mode_admin:
            admin_tasks = [t for t in non_terminees if t.get("visibilite") == "tous"]
            own_tasks = [t for t in non_terminees if t.get("visibilite") != "tous"]
            non_terminees = admin_tasks + own_tasks

        sorted_parents = non_terminees + terminees

        # Insérer les sous-tâches après chaque parent
        result = []
        for parent in sorted_parents:
            result.append(parent)
            pid = parent.get("id")
            children = sous_taches_map.get(pid, [])
            if criteres_tri:
                children.sort(key=tri_key)
            for child in children:
                result.append(child)
                # Niveau 2 (petits-enfants)
                grandchildren = sous_taches_map.get(child.get("id"), [])
                if criteres_tri:
                    grandchildren.sort(key=tri_key)
                result.extend(grandchildren)

        return result

    def lister_taches_parents(
        self, mode_admin: bool = True, max_niveau: int = 1
    ) -> list[dict]:
        """Liste les tâches pouvant être parentes."""
        if mode_admin:
            visibilite = ["tous", "admin_seul"]
        else:
            visibilite = ["tous", "fonctionnel_seul"]
        return self.tache_model.lister_taches_parents(visibilite, max_niveau)

    def lister_sous_taches(self, parent_id: int) -> list[dict]:
        return self.tache_model.lister_sous_taches(parent_id)

    # ------------------------------------------------------------------
    # Catégories
    # ------------------------------------------------------------------

    def lister_categories(self) -> list[dict]:
        return self.categorie_model.lister_categories()

    def creer_categorie(self, nom: str, couleur: str = "#2196F3") -> Optional[int]:
        if not nom.strip():
            self.erreur.emit("Le nom de la catégorie ne peut pas être vide.")
            return None
        cat_id = self.categorie_model.creer_categorie(nom.strip(), couleur)
        return cat_id if cat_id > 0 else None

    def modifier_couleur_categorie(self, categorie_id: int, couleur: str) -> bool:
        return self.categorie_model.modifier_couleur(categorie_id, couleur)

    def supprimer_categorie(self, categorie_id: int) -> bool:
        return self.categorie_model.supprimer_categorie(categorie_id)

    # ------------------------------------------------------------------
    # Recherche associations
    # ------------------------------------------------------------------

    def rechercher_clients(self, terme: str) -> list[dict]:
        from models.client import ClientModel
        return ClientModel().rechercher_clients(terme)

    def rechercher_ventes(self, terme: str) -> list[dict]:
        from models.vente import VenteModel
        ventes = VenteModel().lister_ventes()
        if not terme.strip():
            return ventes[:20]
        terme_lower = terme.lower()
        return [
            v for v in ventes
            if terme_lower in str(v.get("transaction_id", "")).lower()
            or terme_lower in str(v.get("client_nom", "")).lower()
            or terme_lower in str(v.get("client_prenom", "")).lower()
        ][:20]

    def rechercher_commandes(self, terme: str) -> list[dict]:
        from models.commande import CommandeModel
        commandes = CommandeModel().lister_commandes()
        if not terme.strip():
            return commandes[:20]
        terme_lower = terme.lower()
        return [
            c for c in commandes
            if terme_lower in str(c.get("id", "")).lower()
            or terme_lower in str(c.get("client_nom", "")).lower()
            or terme_lower in str(c.get("client_prenom", "")).lower()
            or terme_lower in str(c.get("reference", "")).lower()
        ][:20]

    def rechercher_produits(self, terme: str) -> list[dict]:
        from models.produit import ProduitModel
        produits = ProduitModel().lister_produits()
        if not terme.strip():
            return produits[:20]
        terme_lower = terme.lower()
        return [
            p for p in produits
            if terme_lower in str(p.get("nom", "")).lower()
            or terme_lower in str(p.get("categorie_nom", "")).lower()
        ][:20]

    def rechercher_codes_promo(self, terme: str) -> list[dict]:
        from models.database import get_db
        db = get_db()
        codes = db.fetchall("SELECT * FROM codes_promo ORDER BY code")
        if not terme.strip():
            return codes[:20]
        terme_lower = terme.lower()
        return [
            c for c in codes
            if terme_lower in str(c.get("code", "")).lower()
            or terme_lower in str(c.get("description", "")).lower()
        ][:20]

    def rechercher_evenements(self, terme: str) -> list[dict]:
        from models.evenement import EvenementModel
        evts = EvenementModel().lister_evenements()
        if not terme.strip():
            return evts[:20]
        terme_lower = terme.lower()
        return [
            e for e in evts
            if terme_lower in str(e.get("nom", "")).lower()
            or terme_lower in str(e.get("description", "")).lower()
        ][:20]
