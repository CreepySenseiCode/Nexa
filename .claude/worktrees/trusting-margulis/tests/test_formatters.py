"""Tests pour les fonctions de formatage (utils/formatters.py)."""

import pytest
from datetime import date
from utils.formatters import (
    formater_nom,
    formater_prenom,
    formater_telephone,
    calculer_age,
    formater_prix,
)


# ================================================================
# formater_nom
# ================================================================

class TestFormaterNom:

    def test_nom_simple(self):
        assert formater_nom("dupont") == "DUPONT"

    def test_nom_avec_espaces(self):
        assert formater_nom("  dupont  ") == "DUPONT"

    def test_nom_deja_majuscule(self):
        assert formater_nom("DUPONT") == "DUPONT"

    def test_nom_vide(self):
        assert formater_nom("") == ""

    def test_nom_none(self):
        assert formater_nom(None) == ""

    def test_nom_non_string(self):
        assert formater_nom(42) == ""


# ================================================================
# formater_prenom
# ================================================================

class TestFormaterPrenom:

    def test_prenom_simple(self):
        assert formater_prenom("jean") == "Jean"

    def test_prenom_compose_tiret(self):
        assert formater_prenom("jean-pierre") == "Jean-Pierre"

    def test_prenom_compose_espace(self):
        assert formater_prenom("marie claire") == "Marie Claire"

    def test_prenom_compose_mixte(self):
        assert formater_prenom("jean-pierre paul") == "Jean-Pierre Paul"

    def test_prenom_tout_majuscule(self):
        assert formater_prenom("JEAN") == "Jean"

    def test_prenom_espaces_multiples(self):
        result = formater_prenom("  jean   pierre  ")
        assert result == "Jean Pierre"

    def test_prenom_vide(self):
        assert formater_prenom("") == ""

    def test_prenom_none(self):
        assert formater_prenom(None) == ""


# ================================================================
# formater_telephone
# ================================================================

class TestFormaterTelephone:

    def test_format_national(self):
        assert formater_telephone("0612345678") == "06 12 34 56 78"

    def test_format_avec_espaces(self):
        assert formater_telephone("06 12 34 56 78") == "06 12 34 56 78"

    def test_format_international(self):
        assert formater_telephone("+33612345678") == "06 12 34 56 78"

    def test_format_avec_points(self):
        assert formater_telephone("06.12.34.56.78") == "06 12 34 56 78"

    def test_format_avec_tirets(self):
        assert formater_telephone("06-12-34-56-78") == "06 12 34 56 78"

    def test_numero_trop_court(self):
        assert formater_telephone("06123") == "06123"

    def test_vide(self):
        assert formater_telephone("") == ""

    def test_none(self):
        assert formater_telephone(None) == ""


# ================================================================
# calculer_age
# ================================================================

class TestCalculerAge:

    def test_age_depuis_string(self):
        # Quelqu'un ne le 01/01/2000
        age = calculer_age("01/01/2000")
        today = date.today()
        attendu = today.year - 2000
        if (today.month, today.day) < (1, 1):
            attendu -= 1
        assert age == attendu

    def test_age_depuis_date(self):
        age = calculer_age(date(1990, 6, 15))
        today = date.today()
        attendu = today.year - 1990
        if (today.month, today.day) < (6, 15):
            attendu -= 1
        assert age == attendu

    def test_format_invalide_leve_erreur(self):
        with pytest.raises(ValueError):
            calculer_age("pas-une-date")

    def test_type_invalide_leve_erreur(self):
        with pytest.raises(ValueError):
            calculer_age(12345)


# ================================================================
# formater_prix
# ================================================================

class TestFormaterPrix:

    def test_prix_simple(self):
        assert formater_prix(12.50) == "12,50 \u20ac"

    def test_prix_entier(self):
        assert formater_prix(100) == "100,00 \u20ac"

    def test_prix_zero(self):
        assert formater_prix(0) == "0,00 \u20ac"

    def test_prix_milliers(self):
        assert formater_prix(1234.56) == "1 234,56 \u20ac"

    def test_prix_symbole_custom(self):
        assert formater_prix(10, "$") == "10,00 $"

    def test_prix_negatif(self):
        result = formater_prix(-5.99)
        assert "-5,99" in result
