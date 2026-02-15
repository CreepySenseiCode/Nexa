"""
Calcul du pourcentage de complétion d'un profil client.
"""


def is_filled(value) -> bool:
    """Vérifie si une valeur est considérée comme remplie."""
    if value is None:
        return False

    s = str(value).strip()

    if s in ("", "\u2014", "Choisir\u2026", "Non spécifié"):
        return False

    return True


def calculer_completion(client: dict) -> int:
    """
    Calcule le pourcentage de complétion d'un profil.

    Args:
        client: Dictionnaire avec les données du client.

    Returns:
        Pourcentage (0-100).
    """
    champs_obligatoires = [
        'nom',
        'prenom',
        'email',
        'telephone',
        'adresse',
        'code_postal',
        'ville',
        'date_naissance',
        'profession',
        'situation_maritale',
        'centre_interet',
    ]

    total = len(champs_obligatoires)
    remplis = sum(1 for champ in champs_obligatoires if is_filled(client.get(champ)))

    if total == 0:
        return 0

    return int((remplis / total) * 100)
