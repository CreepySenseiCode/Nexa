"""Fonctions d'authentification pour l'application Nexa."""

import bcrypt


def hasher_mot_de_passe(mdp: str) -> str:
    """Hache un mot de passe avec bcrypt.

    Args:
        mdp: Le mot de passe en clair a hacher.

    Returns:
        Le hash bcrypt sous forme de chaine de caracteres.
    """
    sel = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(mdp.encode('utf-8'), sel)
    return hash_bytes.decode('utf-8')


def verifier_mot_de_passe(mdp: str, hash_str: str) -> bool:
    """Verifie un mot de passe en clair contre un hash bcrypt.

    Args:
        mdp: Le mot de passe en clair a verifier.
        hash_str: Le hash bcrypt stocke.

    Returns:
        True si le mot de passe correspond au hash, False sinon.
    """
    try:
        return bcrypt.checkpw(
            mdp.encode('utf-8'),
            hash_str.encode('utf-8')
        )
    except (ValueError, TypeError):
        return False


def mot_de_passe_existe(db) -> bool:
    """Verifie si un mot de passe patron est defini dans la base de donnees.

    Args:
        db: Instance de DatabaseManager.

    Returns:
        True si un mot de passe patron est defini et non vide, False sinon.
    """
    try:
        resultat = db.fetchone(
            "SELECT valeur FROM parametres WHERE cle = 'mot_de_passe_administratif'"
        )
        return resultat is not None and bool(resultat.get('valeur'))
    except Exception:
        return False


def mot_de_passe_actif(db) -> bool:
    """Verifie si la gestion par mot de passe est activee.

    Args:
        db: Instance de DatabaseManager.

    Returns:
        True si la gestion par mot de passe est active, False sinon.
    """
    try:
        resultat = db.fetchone(
            "SELECT valeur FROM parametres WHERE cle = 'mot_de_passe_actif'"
        )
        return resultat is not None and resultat.get('valeur') == '1'
    except Exception:
        return False
