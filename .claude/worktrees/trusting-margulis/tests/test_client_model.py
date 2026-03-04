"""Tests pour le modele Client (models/client.py)."""

import pytest
from models.client import ClientModel


@pytest.fixture()
def client_model(db):
    """Fournit un ClientModel connecte a la DB en memoire."""
    return ClientModel()


@pytest.fixture()
def client_dupont(client_model):
    """Cree et retourne l'ID d'un client de test."""
    client_id = client_model.creer_client({
        "nom": "DUPONT",
        "prenom": "Jean",
        "email": "jean.dupont@test.com",
        "telephone": "0612345678",
    })
    return client_id


class TestCreerClient:

    def test_creation_retourne_id(self, client_model):
        client_id = client_model.creer_client({
            "nom": "MARTIN",
            "prenom": "Pierre",
        })
        assert isinstance(client_id, int)
        assert client_id > 0

    def test_creation_avec_tous_les_champs(self, client_model):
        client_id = client_model.creer_client({
            "nom": "DURAND",
            "prenom": "Marie",
            "email": "marie@test.com",
            "telephone": "0698765432",
            "ville": "Paris",
            "adresse": "1 rue de la Paix",
        })
        client = client_model.obtenir_client(client_id)
        assert client["nom"] == "DURAND"
        assert client["prenom"] == "Marie"
        assert client["email"] == "marie@test.com"
        assert client["ville"] == "Paris"


class TestObtenirClient:

    def test_client_existant(self, client_model, client_dupont):
        client = client_model.obtenir_client(client_dupont)
        assert client is not None
        assert client["nom"] == "DUPONT"
        assert client["prenom"] == "Jean"

    def test_client_inexistant(self, client_model, db):
        client = client_model.obtenir_client(99999)
        assert client is None


class TestModifierClient:

    def test_modification_nom(self, client_model, client_dupont):
        success = client_model.modifier_client(client_dupont, {"nom": "DURAND"})
        assert success is True

        client = client_model.obtenir_client(client_dupont)
        assert client["nom"] == "DURAND"

    def test_modification_email(self, client_model, client_dupont):
        success = client_model.modifier_client(
            client_dupont, {"email": "nouveau@test.com"}
        )
        assert success is True

        client = client_model.obtenir_client(client_dupont)
        assert client["email"] == "nouveau@test.com"

    def test_modification_preserve_autres_champs(self, client_model, client_dupont):
        client_model.modifier_client(client_dupont, {"ville": "Lyon"})
        client = client_model.obtenir_client(client_dupont)
        assert client["nom"] == "DUPONT"  # non modifie
        assert client["ville"] == "Lyon"


class TestSupprimerClient:

    def test_suppression_client(self, client_model, client_dupont):
        success = client_model.supprimer_client(client_dupont)
        assert success is True

        client = client_model.obtenir_client(client_dupont)
        assert client is None

    def test_suppression_client_inexistant(self, client_model, db):
        success = client_model.supprimer_client(99999)
        assert success is True  # pas d'erreur meme si inexistant


class TestRechercherClients:

    def test_recherche_par_nom(self, client_model, client_dupont):
        resultats = client_model.rechercher_clients("DUPONT")
        assert len(resultats) >= 1
        assert any(r["nom"] == "DUPONT" for r in resultats)

    def test_recherche_par_prenom(self, client_model, client_dupont):
        resultats = client_model.rechercher_clients("Jean")
        assert len(resultats) >= 1

    def test_recherche_sans_resultat(self, client_model, db):
        resultats = client_model.rechercher_clients("XYZINEXISTANT")
        assert len(resultats) == 0

    def test_recherche_multi_mots(self, client_model, client_dupont):
        resultats = client_model.rechercher_clients("Jean DUPONT")
        assert len(resultats) >= 1


class TestBaseModel:
    """Teste les methodes heritees de BaseModel."""

    def test_obtenir_par_id(self, client_model, client_dupont):
        client = client_model.obtenir_par_id(client_dupont)
        assert client is not None
        assert client["nom"] == "DUPONT"

    def test_compter(self, client_model, client_dupont):
        count = client_model.compter()
        assert count >= 1

    def test_supprimer_par_id(self, client_model, db):
        cid = client_model.creer_client({"nom": "TEMP", "prenom": "Test"})
        assert client_model.supprimer_par_id(cid) is True
        assert client_model.obtenir_par_id(cid) is None
