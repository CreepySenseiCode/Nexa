"""Fonctions de formatage pour l'application Nexa."""

from datetime import date, datetime
from typing import Union


def formater_nom(nom: str) -> str:
    """Convertit un nom en majuscules et supprime les espaces superflus.

    Args:
        nom: Le nom à formater.

    Returns:
        Le nom en majuscules, sans espaces superflus.
    """
    if not nom or not isinstance(nom, str):
        return ""

    return nom.strip().upper()


def formater_prenom(prenom: str) -> str:
    """Met en majuscule la première lettre de chaque partie du prénom.

    Gère correctement les prénoms composés avec tiret (ex: "jean-pierre"
    devient "Jean-Pierre") et les espaces multiples.

    Args:
        prenom: Le prénom à formater.

    Returns:
        Le prénom formaté avec les initiales en majuscules.
    """
    if not prenom or not isinstance(prenom, str):
        return ""

    prenom = prenom.strip()

    # Traitement des parties séparées par des espaces
    parties_espace = prenom.split()
    resultats = []

    for partie in parties_espace:
        # Traitement des parties séparées par des tirets
        sous_parties = partie.split('-')
        partie_formatee = '-'.join(
            sous_partie.capitalize() for sous_partie in sous_parties
        )
        resultats.append(partie_formatee)

    return ' '.join(resultats)


def formater_telephone(tel: str) -> str:
    """Formate un numéro de téléphone au format XX XX XX XX XX.

    Remplace le préfixe +33 par 0 si présent.

    Args:
        tel: Le numéro de téléphone à formater.

    Returns:
        Le numéro formaté au format XX XX XX XX XX.
    """
    if not tel or not isinstance(tel, str):
        return ""

    # Suppression de tous les caractères non numériques sauf le +
    tel_nettoye = tel.strip()

    # Remplacement du préfixe international +33 par 0
    if tel_nettoye.startswith('+33'):
        tel_nettoye = '0' + tel_nettoye[3:]

    # Suppression de tous les caractères non numériques
    chiffres = ''.join(c for c in tel_nettoye if c.isdigit())

    # Vérification qu'on a bien 10 chiffres
    if len(chiffres) != 10:
        return tel.strip()

    # Formatage par groupes de 2 chiffres
    return ' '.join(
        chiffres[i:i + 2] for i in range(0, 10, 2)
    )


def calculer_age(date_naissance: Union[str, date, "QDate"]) -> int:
    """Calcule l'âge à partir de la date de naissance.

    Accepte une chaîne au format "JJ/MM/AAAA", un objet date Python
    ou un objet QDate de PySide6.

    Args:
        date_naissance: La date de naissance (str, date ou QDate).

    Returns:
        L'âge en années révolues.

    Raises:
        ValueError: Si le format de date est invalide.
    """
    aujourdhui = date.today()

    # Conversion selon le type de l'entrée
    if isinstance(date_naissance, str):
        # Format attendu : JJ/MM/AAAA
        try:
            dt = datetime.strptime(date_naissance.strip(), '%d/%m/%Y')
            date_naiss = dt.date()
        except ValueError:
            raise ValueError(
                f"Format de date invalide : '{date_naissance}'. "
                "Utilisez le format JJ/MM/AAAA."
            )
    elif isinstance(date_naissance, date):
        date_naiss = date_naissance
    else:
        # Tentative de traitement comme QDate (PySide6)
        try:
            date_naiss = date(
                date_naissance.year(),
                date_naissance.month(),
                date_naissance.day()
            )
        except (AttributeError, TypeError):
            raise ValueError(
                f"Type de date non supporté : {type(date_naissance)}"
            )

    # Calcul précis de l'âge
    age = aujourdhui.year - date_naiss.year

    # Ajustement si l'anniversaire n'est pas encore passé cette année
    if (aujourdhui.month, aujourdhui.day) < (date_naiss.month, date_naiss.day):
        age -= 1

    return age


def formater_prix(prix: float, symbole: str = "\u20ac") -> str:
    """Formate un prix avec 2 décimales et le symbole monétaire.

    Utilise la virgule comme séparateur décimal (format français).

    Args:
        prix: Le montant à formater.
        symbole: Le symbole monétaire (par défaut "\\u20ac").

    Returns:
        Le prix formaté (ex: "12,50 \\u20ac").
    """
    # Formatage avec séparateur de milliers, 2 décimales, virgule décimale
    prix_formate = f"{prix:,.2f}".replace(',', ' ').replace('.', ',')
    return f"{prix_formate} {symbole}"
