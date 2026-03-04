"""Fonctions de validation pour l'application Nexa."""

import re
from datetime import datetime


def valider_email(email: str) -> bool:
    """Valide une adresse email avec une expression régulière.

    Args:
        email: L'adresse email à valider.

    Returns:
        True si l'adresse email est valide, False sinon.
    """
    if not email or not isinstance(email, str):
        return False

    # Expression régulière pour la validation d'email
    motif = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(motif, email.strip()))


def valider_telephone(tel: str) -> bool:
    """Valide un numéro de téléphone français.

    Accepte les formats suivants :
        - 06 12 34 56 78
        - 0612345678
        - +33 6 12 34 56 78
        - +336 12 34 56 78

    Args:
        tel: Le numéro de téléphone à valider.

    Returns:
        True si le numéro est valide, False sinon.
    """
    if not tel or not isinstance(tel, str):
        return False

    # Suppression des espaces, tirets et points pour normaliser
    tel_nettoye = re.sub(r'[\s.\-]', '', tel.strip())

    # Format avec indicatif international +33
    if tel_nettoye.startswith('+33'):
        # Après +33, il doit rester 9 chiffres
        reste = tel_nettoye[3:]
        return bool(re.match(r'^\d{9}$', reste))

    # Format national commençant par 0
    if tel_nettoye.startswith('0'):
        return bool(re.match(r'^0\d{9}$', tel_nettoye))

    return False


def valider_date(date_str: str) -> bool:
    """Valide une date au format JJ/MM/AAAA.

    Vérifie non seulement le format mais aussi la cohérence de la date
    (ex: 31/02/2024 sera rejeté).

    Args:
        date_str: La chaîne de date à valider.

    Returns:
        True si la date est valide, False sinon.
    """
    if not date_str or not isinstance(date_str, str):
        return False

    # Vérification du format avec expression régulière
    if not re.match(r'^\d{2}/\d{2}/\d{4}$', date_str.strip()):
        return False

    # Vérification de la cohérence de la date
    try:
        datetime.strptime(date_str.strip(), '%d/%m/%Y')
        return True
    except ValueError:
        return False


def valider_mot_de_passe(mdp: str) -> tuple[bool, str, dict]:
    """Valide un mot de passe selon les regles de securite.

    Regles :
        - Minimum 8 caracteres
        - Au moins 1 majuscule
        - Au moins 1 minuscule
        - Au moins 1 chiffre
        - Au moins 1 caractere special

    Args:
        mdp: Le mot de passe a valider.

    Returns:
        Tuple (valide, message, details) ou details est un dict
        avec les resultats de chaque regle.
    """
    details = {
        'longueur': len(mdp) >= 8,
        'majuscule': bool(re.search(r'[A-Z]', mdp)),
        'minuscule': bool(re.search(r'[a-z]', mdp)),
        'chiffre': bool(re.search(r'[0-9]', mdp)),
        'special': bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', mdp)),
    }

    if not details['longueur']:
        return False, "Au moins 8 caracteres requis", details
    if not details['majuscule']:
        return False, "Au moins 1 majuscule requise", details
    if not details['minuscule']:
        return False, "Au moins 1 minuscule requise", details
    if not details['chiffre']:
        return False, "Au moins 1 chiffre requis", details
    if not details['special']:
        return False, "Au moins 1 caractere special requis", details

    return True, "", details


def valider_code_postal(cp: str) -> bool:
    """Valide un code postal français (5 chiffres).

    Args:
        cp: Le code postal à valider.

    Returns:
        True si le code postal est valide, False sinon.
    """
    if not cp or not isinstance(cp, str):
        return False

    return bool(re.match(r'^\d{5}$', cp.strip()))
