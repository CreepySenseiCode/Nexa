"""ViewModel pour les parametres."""
from PySide6.QtCore import QObject, Signal
from models.parametres import ParametresModel
from models.attribut_produit import AttributProduitModel


class ParametresViewModel(QObject):
    """ViewModel pour l'onglet Parametres."""

    donnees_chargees = Signal(dict)
    erreur = Signal(str)
    attributs_modifies = Signal()

    def __init__(self):
        super().__init__()
        self.params_model = ParametresModel()
        self.attribut_model = AttributProduitModel()

    def charger_donnees(self) -> dict:
        """Charge les parametres de l'entreprise. Retourne un dict cle->valeur."""
        cles = ['nom_entreprise', 'adresse_entreprise', 'telephone_entreprise', 'email_recuperation']
        donnees = {}
        for cle in cles:
            val = self.params_model.obtenir_parametre(cle)
            if val:
                donnees[cle] = val
        self.donnees_chargees.emit(donnees)
        return donnees

    def sauvegarder_entreprise(self, donnees: dict) -> bool:
        """Sauvegarde les infos entreprise. donnees = dict cle->valeur."""
        if not donnees.get('nom_entreprise'):
            self.erreur.emit("Le nom de l'entreprise est requis.")
            return False
        try:
            for cle, valeur in donnees.items():
                self.params_model.definir_parametre(cle, valeur)
            return True
        except Exception as e:
            self.erreur.emit(f"Erreur lors de la sauvegarde : {e}")
            return False

    def lister_attributs(self) -> list[dict]:
        """Retourne la liste des attributs globaux."""
        return self.attribut_model.lister_attributs_globaux()

    def ajouter_attribut(self, nom: str) -> int:
        """Ajoute un attribut global. Retourne l'ID ou leve une exception."""
        result = self.attribut_model.ajouter_attribut(nom)
        self.attributs_modifies.emit()
        return result

    def supprimer_attribut(self, nom: str) -> bool:
        """Supprime un attribut global."""
        result = self.attribut_model.supprimer_attribut(nom)
        if result:
            self.attributs_modifies.emit()
        return result
