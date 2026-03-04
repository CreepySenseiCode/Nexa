#!/usr/bin/env python3
"""Script de reinitialisation du mot de passe patron."""

import sys
import os
import subprocess

# Auto-detection du venv : si on n'est pas dans le venv, relancer avec le python du venv
script_dir = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(script_dir, 'app', 'venv', 'bin', 'python')

venv_dir = os.path.join(script_dir, 'app', 'venv')
if os.path.exists(venv_python) and not sys.prefix.startswith(venv_dir):
    os.execv(venv_python, [venv_python] + sys.argv)

sys.path.insert(0, os.path.join(script_dir, 'app'))

from models.database import get_db
from utils.auth import hasher_mot_de_passe


def reset_password():
    db = get_db()

    print("=" * 50)
    print("  REINITIALISATION DU MOT DE PASSE PATRON")
    print("=" * 50)
    print()

    nouveau_mdp = input("Entrez le nouveau mot de passe : ")
    confirm_mdp = input("Confirmez le nouveau mot de passe : ")

    if nouveau_mdp != confirm_mdp:
        print("\n❌ Les mots de passe ne correspondent pas.")
        return

    if len(nouveau_mdp) < 4:
        print("\n❌ Le mot de passe doit faire au moins 4 caracteres.")
        return

    # Hasher et enregistrer
    hash_mdp = hasher_mot_de_passe(nouveau_mdp)

    # Verifier si le parametre existe deja
    row = db.fetchone(
        "SELECT cle FROM parametres WHERE cle = 'mot_de_passe_patron'"
    )
    if row:
        db.execute(
            "UPDATE parametres SET valeur = ? WHERE cle = 'mot_de_passe_patron'",
            (hash_mdp,),
        )
    else:
        db.execute(
            "INSERT INTO parametres (cle, valeur, type, description) VALUES (?, ?, ?, ?)",
            ('mot_de_passe_patron', hash_mdp, 'texte', 'Mot de passe patron'),
        )

    # Activer la gestion par mot de passe
    row2 = db.fetchone(
        "SELECT cle FROM parametres WHERE cle = 'mot_de_passe_actif'"
    )
    if row2:
        db.execute(
            "UPDATE parametres SET valeur = '1' WHERE cle = 'mot_de_passe_actif'"
        )
    else:
        db.execute(
            "INSERT INTO parametres (cle, valeur, type, description) VALUES (?, ?, ?, ?)",
            ('mot_de_passe_actif', '1', 'booleen', 'Gestion par mot de passe active'),
        )

    print()
    print("✅ Mot de passe reinitialise avec succes !")
    print("   Vous pouvez maintenant demarrer l'application.")
    print()


if __name__ == '__main__':
    reset_password()
