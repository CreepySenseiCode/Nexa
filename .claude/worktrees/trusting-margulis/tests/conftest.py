"""Configuration pytest pour les tests Nexa.

Fournit une fixture qui cree une base de donnees SQLite en memoire
pour chaque test, evitant ainsi toute interaction avec la DB de production.
"""

import os
import sys
import pytest

# Ajouter le repertoire app/ au PYTHONPATH pour les imports
_APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
sys.path.insert(0, _APP_DIR)


@pytest.fixture()
def db():
    """Cree une base de donnees SQLite en memoire pour un test isole.

    - Reinitialise le singleton global pour eviter les effets de bord.
    - Cree toutes les tables et index.
    - Ferme et nettoie apres chaque test.
    """
    import models.database as db_module

    # Sauvegarder et reinitialiser le singleton
    ancien = db_module._instance
    db_module._instance = None

    manager = db_module.DatabaseManager(db_path=":memory:")
    db_module._instance = manager

    yield manager

    # Nettoyage
    manager.close()
    db_module._instance = ancien
