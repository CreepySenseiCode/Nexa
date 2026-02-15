"""Tests pour la couche base de donnees (models/database.py)."""

import pytest
import sqlite3


class TestDatabaseManager:
    """Tests pour les operations de base du DatabaseManager."""

    def test_connexion_memoire(self, db):
        """Le manager doit se connecter a une DB en memoire."""
        conn = db.get_connection()
        assert conn is not None

    def test_execute_et_fetchone(self, db):
        """execute() + fetchone() doivent fonctionner ensemble."""
        db.execute(
            "INSERT INTO parametres (cle, valeur) VALUES (?, ?)",
            ("test_cle", "test_valeur"),
        )
        row = db.fetchone(
            "SELECT valeur FROM parametres WHERE cle = ?", ("test_cle",)
        )
        assert row is not None
        assert row["valeur"] == "test_valeur"

    def test_fetchall(self, db):
        """fetchall() doit retourner une liste de dicts."""
        db.execute(
            "INSERT INTO parametres (cle, valeur) VALUES (?, ?)",
            ("a", "1"),
        )
        db.execute(
            "INSERT INTO parametres (cle, valeur) VALUES (?, ?)",
            ("b", "2"),
        )
        rows = db.fetchall("SELECT * FROM parametres WHERE cle IN ('a', 'b')")
        assert len(rows) == 2
        assert all(isinstance(r, dict) for r in rows)

    def test_fetchone_aucun_resultat(self, db):
        """fetchone() doit retourner None si aucun resultat."""
        row = db.fetchone(
            "SELECT * FROM parametres WHERE cle = ?", ("inexistant",)
        )
        assert row is None


class TestTransaction:
    """Tests pour le context manager transaction()."""

    def test_transaction_commit(self, db):
        """Les operations dans une transaction doivent etre commitees."""
        with db.transaction():
            db.execute(
                "INSERT INTO parametres (cle, valeur) VALUES (?, ?)",
                ("tx_test", "ok"),
            )

        row = db.fetchone(
            "SELECT valeur FROM parametres WHERE cle = ?", ("tx_test",)
        )
        assert row is not None
        assert row["valeur"] == "ok"

    def test_transaction_rollback_sur_erreur(self, db):
        """En cas d'erreur, la transaction doit faire un rollback."""
        with pytest.raises(sqlite3.IntegrityError):
            with db.transaction():
                db.execute(
                    "INSERT INTO parametres (cle, valeur) VALUES (?, ?)",
                    ("tx_rollback", "avant"),
                )
                # Doublon sur la cle primaire => IntegrityError
                db.execute(
                    "INSERT INTO parametres (cle, valeur) VALUES (?, ?)",
                    ("tx_rollback", "doublon"),
                )

        # Le premier INSERT doit avoir ete annule
        row = db.fetchone(
            "SELECT * FROM parametres WHERE cle = ?", ("tx_rollback",)
        )
        assert row is None

    def test_auto_commit_hors_transaction(self, db):
        """Hors transaction, chaque execute() doit commiter immediatement."""
        db.execute(
            "INSERT INTO parametres (cle, valeur) VALUES (?, ?)",
            ("auto", "commit"),
        )
        # Verifier que c'est bien persiste sans transaction explicite
        row = db.fetchone(
            "SELECT valeur FROM parametres WHERE cle = ?", ("auto",)
        )
        assert row["valeur"] == "commit"


class TestIndex:
    """Verifie que les index critiques existent."""

    @pytest.mark.parametrize("index_name", [
        "idx_clients_email",
        "idx_clients_nom",
        "idx_ventes_client",
        "idx_ventes_date",
        "idx_ventes_produit",
        "idx_emails_recus_client",
    ])
    def test_index_existe(self, db, index_name):
        """Chaque index critique doit exister dans la DB."""
        row = db.fetchone(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name = ?",
            (index_name,),
        )
        assert row is not None, f"Index {index_name} manquant"


class TestTables:
    """Verifie que les tables principales existent."""

    @pytest.mark.parametrize("table_name", [
        "clients",
        "ventes",
        "produits",
        "categories_produits",
        "codes_reduction",
        "centres_interet",
        "parametres",
        "mails_enregistres",
        "emails_recus",
    ])
    def test_table_existe(self, db, table_name):
        """Chaque table principale doit exister dans la DB."""
        row = db.fetchone(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        )
        assert row is not None, f"Table {table_name} manquante"
