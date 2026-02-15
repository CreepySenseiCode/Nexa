"""Tests pour les fonctions de validation (utils/validators.py)."""

import pytest
from utils.validators import (
    valider_email,
    valider_telephone,
    valider_date,
    valider_mot_de_passe,
    valider_code_postal,
)


# ================================================================
# valider_email
# ================================================================

class TestValiderEmail:

    @pytest.mark.parametrize("email", [
        "test@example.com",
        "user.name@domain.org",
        "user+tag@sub.domain.fr",
        "a@b.co",
    ])
    def test_emails_valides(self, email):
        assert valider_email(email) is True

    @pytest.mark.parametrize("email", [
        "",
        "   ",
        "pas-un-email",
        "@manque-local.com",
        "manque-domaine@",
        "manque@point",
        None,
        123,
    ])
    def test_emails_invalides(self, email):
        assert valider_email(email) is False

    def test_email_avec_espaces(self):
        assert valider_email("  test@example.com  ") is True


# ================================================================
# valider_telephone
# ================================================================

class TestValiderTelephone:

    @pytest.mark.parametrize("tel", [
        "0612345678",
        "06 12 34 56 78",
        "06.12.34.56.78",
        "06-12-34-56-78",
        "+33612345678",
        "+33 6 12 34 56 78",
    ])
    def test_telephones_valides(self, tel):
        assert valider_telephone(tel) is True

    @pytest.mark.parametrize("tel", [
        "",
        "123",
        "061234567",       # 9 chiffres
        "06123456789",     # 11 chiffres
        "1612345678",      # ne commence pas par 0
        None,
        42,
    ])
    def test_telephones_invalides(self, tel):
        assert valider_telephone(tel) is False


# ================================================================
# valider_date
# ================================================================

class TestValiderDate:

    @pytest.mark.parametrize("d", [
        "01/01/2024",
        "31/12/2000",
        "29/02/2024",  # annee bissextile
        "15/06/1990",
    ])
    def test_dates_valides(self, d):
        assert valider_date(d) is True

    @pytest.mark.parametrize("d", [
        "",
        "2024-01-01",     # mauvais format
        "31/02/2024",     # fevrier n'a pas 31 jours
        "29/02/2023",     # 2023 non bissextile
        "00/01/2024",     # jour 0
        "abc",
        None,
        123,
    ])
    def test_dates_invalides(self, d):
        assert valider_date(d) is False


# ================================================================
# valider_mot_de_passe
# ================================================================

class TestValiderMotDePasse:

    def test_mot_de_passe_valide(self):
        valide, message, details = valider_mot_de_passe("Abcdef1!")
        assert valide is True
        assert message == ""
        assert all(details.values())

    def test_trop_court(self):
        valide, message, details = valider_mot_de_passe("Ab1!")
        assert valide is False
        assert details['longueur'] is False

    def test_sans_majuscule(self):
        valide, message, details = valider_mot_de_passe("abcdefg1!")
        assert valide is False
        assert details['majuscule'] is False

    def test_sans_minuscule(self):
        valide, message, details = valider_mot_de_passe("ABCDEFG1!")
        assert valide is False
        assert details['minuscule'] is False

    def test_sans_chiffre(self):
        valide, message, details = valider_mot_de_passe("Abcdefgh!")
        assert valide is False
        assert details['chiffre'] is False

    def test_sans_special(self):
        valide, message, details = valider_mot_de_passe("Abcdefg1")
        assert valide is False
        assert details['special'] is False


# ================================================================
# valider_code_postal
# ================================================================

class TestValiderCodePostal:

    @pytest.mark.parametrize("cp", ["75001", "13000", "97400", "00100"])
    def test_codes_postaux_valides(self, cp):
        assert valider_code_postal(cp) is True

    @pytest.mark.parametrize("cp", [
        "",
        "7500",       # 4 chiffres
        "750011",     # 6 chiffres
        "ABCDE",
        "7500A",
        None,
        75001,
    ])
    def test_codes_postaux_invalides(self, cp):
        assert valider_code_postal(cp) is False

    def test_code_postal_avec_espaces(self):
        assert valider_code_postal("  75001  ") is True
