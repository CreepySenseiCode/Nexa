"""Verification de coherence schema DB vs code."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import get_db


def verifier_schema():
    """Verifie que toutes les colonnes utilisees existent."""
    db = get_db()

    # Tables critiques à vérifier (colonnes réellement utilisées dans le code)
    verifications = [
        ("attributs_produits", ["id", "nom_attribut", "categorie_id"]),
        ("produits", ["id", "nom", "categorie_id", "prix", "stock", "description"]),
        ("categories_produits", ["id", "nom", "description", "actif", "ordre"]),
        ("ventes", ["id", "client_id", "produit_id", "quantite", "prix_total", "prix_unitaire", "date_vente"]),
        ("clients", ["id", "nom", "prenom", "email", "telephone"]),
        ("emails_recus", ["id", "client_id", "expediteur_email", "expediteur_nom", "objet", "contenu_html", "date_reception"]),
        ("mails_enregistres", ["id", "nom_mail", "objet", "contenu_html", "date_creation"]),
        ("historique_emails", ["id", "objet", "type_envoi", "nombre_destinataires", "destinataires", "date_envoi", "statut"]),
        ("codes_reduction", ["id", "code", "pourcentage", "date_debut", "date_fin", "limite_utilisations"]),
        ("centres_interet", ["id", "nom"]),
        ("parametres", ["cle", "valeur"]),
    ]

    erreurs = []
    warnings = []

    for table, colonnes_attendues in verifications:
        try:
            cols = db.fetchall(f"PRAGMA table_info({table})")
            if not cols:
                erreurs.append(f"❌ Table {table} N'EXISTE PAS")
                continue

            cols_reelles = [c['name'] for c in cols]

            for col in colonnes_attendues:
                if col not in cols_reelles:
                    erreurs.append(f"❌ {table}.{col} MANQUANTE (colonnes réelles: {cols_reelles})")

            print(f"✅ {table} : {len(cols_reelles)} colonnes vérifiées")

        except Exception as e:
            erreurs.append(f"❌ Erreur sur table {table} : {e}")

    print("\n" + "=" * 60)

    if erreurs:
        print("⚠️ ERREURS CRITIQUES DÉTECTÉES :")
        for err in erreurs:
            print(err)
        print("\n❌ VALIDATION ÉCHOUÉE - Corriger avant de continuer")
        return False

    if warnings:
        print("⚠️ AVERTISSEMENTS :")
        for warn in warnings:
            print(warn)

    print("\n✅ Tous les schémas sont cohérents")
    print("=" * 60)
    return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if verifier_schema() else 1)
