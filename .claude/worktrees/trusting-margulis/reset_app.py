#!/usr/bin/env python3
"""
Script de réinitialisation complète de l'application.
Simule une première installation fraîche.
"""

import sys
import os
import shutil
from pathlib import Path


def reset_application():
    print("=" * 60)
    print("  RÉINITIALISATION COMPLÈTE DE L'APPLICATION")
    print("=" * 60)
    print()

    confirmation = input(
        "⚠️  ATTENTION : Cela va supprimer TOUTES les données.\n"
        "Êtes-vous sûr ? (tapez 'OUI' pour confirmer) : "
    )

    if confirmation != "OUI":
        print("❌ Réinitialisation annulée.")
        return

    print()
    print("🔄 Réinitialisation en cours...")
    print()

    # Chemins à supprimer
    data_dir = Path("app/data")

    items_to_delete = [
        data_dir / "app.db",
        data_dir / "attachments",
        data_dir / "logs",
    ]

    deleted = []

    for item in items_to_delete:
        if item.exists():
            try:
                if item.is_file():
                    item.unlink()
                    deleted.append(f"  ✓ Fichier supprimé : {item}")
                elif item.is_dir():
                    shutil.rmtree(item)
                    deleted.append(f"  ✓ Dossier supprimé : {item}")
            except Exception as e:
                print(f"  ✗ Erreur lors de la suppression de {item} : {e}")
        else:
            print(f"  - {item} n'existe pas (déjà supprimé)")

    print()
    print("✅ Réinitialisation terminée !")
    print()

    if deleted:
        print("Éléments supprimés :")
        for item in deleted:
            print(item)

    print()
    print("📱 Au prochain lancement de l'application :")
    print("  - La base de données sera recréée")
    print("  - Le dialog de première installation apparaîtra")
    print("  - Vous pourrez choisir de définir un mot de passe ou non")
    print()


if __name__ == "__main__":
    reset_application()
