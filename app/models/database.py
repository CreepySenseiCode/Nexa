"""
Module de gestion de la base de données SQLite.

Ce module fournit un gestionnaire de base de données singleton (DatabaseManager)
qui gère la connexion SQLite, la création des tables, l'insertion des données
par défaut et les opérations CRUD de base.
"""

import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import date
from typing import Optional


# --- Référence au répertoire de l'application ---
_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Chemin par défaut de la base de données ---
_DEFAULT_DB_PATH = os.path.join(_APP_DIR, "data", "app.db")

# --- Instance singleton du gestionnaire ---
_instance: Optional["DatabaseManager"] = None


# ============================================================================
# SQL de création des tables
# ============================================================================

_SQL_CREATE_TABLES = """
-- Table des paramètres généraux de l'application
CREATE TABLE IF NOT EXISTS parametres (
    cle TEXT PRIMARY KEY,
    valeur TEXT,
    type TEXT,
    description TEXT
);

-- Table des champs clients actifs (configuration dynamique du formulaire client)
CREATE TABLE IF NOT EXISTS champs_clients_actifs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_champ TEXT UNIQUE NOT NULL,
    actif BOOLEAN DEFAULT 1,
    obligatoire BOOLEAN DEFAULT 0,
    depend_de TEXT,
    valeur_dependance TEXT,
    type_champ TEXT,
    ordre_affichage INTEGER
);

-- Table principale des clients
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    sexe TEXT,
    date_naissance TEXT,
    age INTEGER,
    adresse TEXT,
    ville TEXT,
    code_postal TEXT,
    email TEXT,
    telephone TEXT,
    situation_maritale TEXT,
    date_mariage TEXT,
    date_pacs TEXT,
    date_deces_conjoint TEXT,
    a_conjoint BOOLEAN DEFAULT 0,
    a_enfants BOOLEAN DEFAULT 0,
    nombre_enfants INTEGER DEFAULT 0,
    a_parents BOOLEAN DEFAULT 0,
    parents_en_vie BOOLEAN DEFAULT 0,
    profession TEXT,
    centre_interet TEXT,
    notes_personnalisees TEXT,
    date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    profil_complet BOOLEAN DEFAULT 0,
    est_conjoint_de INTEGER,
    est_enfant_de INTEGER,
    est_parent_de INTEGER,
    photo_path TEXT,
    type_relation TEXT DEFAULT 'principal',
    FOREIGN KEY (est_conjoint_de) REFERENCES clients(id),
    FOREIGN KEY (est_enfant_de) REFERENCES clients(id),
    FOREIGN KEY (est_parent_de) REFERENCES clients(id)
);

-- Table de liaison conjoints
CREATE TABLE IF NOT EXISTS conjoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    conjoint_client_id INTEGER NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (conjoint_client_id) REFERENCES clients(id)
);

-- Table de liaison enfants
CREATE TABLE IF NOT EXISTS enfants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    enfant_client_id INTEGER NOT NULL,
    ordre INTEGER DEFAULT 1,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (enfant_client_id) REFERENCES clients(id)
);

-- Table de liaison parents
CREATE TABLE IF NOT EXISTS parents_clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    parent_client_id INTEGER NOT NULL,
    type_parent TEXT,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (parent_client_id) REFERENCES clients(id)
);

-- Table des catégories de produits
CREATE TABLE IF NOT EXISTS categories_produits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    description TEXT,
    actif INTEGER DEFAULT 1,
    ordre INTEGER DEFAULT 0,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des attributs personnalisés (globaux ou par catégorie)
CREATE TABLE IF NOT EXISTS attributs_produits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categorie_id INTEGER,
    nom_attribut TEXT NOT NULL,
    type_attribut TEXT DEFAULT 'texte',
    par_defaut BOOLEAN DEFAULT 0,
    ordre_affichage INTEGER,
    FOREIGN KEY (categorie_id) REFERENCES categories_produits(id)
);

-- Table des produits
CREATE TABLE IF NOT EXISTS produits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categorie_id INTEGER,
    nom TEXT NOT NULL,
    prix REAL DEFAULT 0.0,
    stock INTEGER DEFAULT 0,
    description TEXT,
    photo TEXT,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categorie_id) REFERENCES categories_produits(id)
);

-- Table des valeurs d'attributs associées aux produits
CREATE TABLE IF NOT EXISTS valeurs_attributs_produits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produit_id INTEGER NOT NULL,
    attribut_id INTEGER NOT NULL,
    valeur TEXT,
    FOREIGN KEY (produit_id) REFERENCES produits(id),
    FOREIGN KEY (attribut_id) REFERENCES attributs_produits(id)
);

-- Table des ventes
CREATE TABLE IF NOT EXISTS ventes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    produit_id INTEGER NOT NULL,
    quantite INTEGER DEFAULT 1,
    prix_unitaire REAL NOT NULL,
    prix_total REAL NOT NULL,
    date_vente TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (produit_id) REFERENCES produits(id)
);

-- Table des mails enregistrés (modèles / brouillons)
CREATE TABLE IF NOT EXISTS mails_enregistres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_mail TEXT NOT NULL,
    objet TEXT NOT NULL,
    contenu_html TEXT NOT NULL,
    contenu_texte TEXT,
    pieces_jointes TEXT,
    type TEXT DEFAULT 'template',
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table de l'historique des emails envoyés
CREATE TABLE IF NOT EXISTS historique_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mail_id INTEGER,
    objet TEXT NOT NULL,
    contenu TEXT NOT NULL,
    type_envoi TEXT NOT NULL,
    nombre_destinataires INTEGER DEFAULT 0,
    destinataires TEXT,
    en_reponse_a INTEGER,
    date_envoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    statut TEXT DEFAULT 'envoyé',
    compte_email_utilise TEXT,
    erreurs TEXT,
    FOREIGN KEY (mail_id) REFERENCES mails_enregistres(id),
    FOREIGN KEY (en_reponse_a) REFERENCES emails_recus(id)
);

-- Table des emails programmés
CREATE TABLE IF NOT EXISTS emails_programmes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mail_id INTEGER NOT NULL,
    type_envoi TEXT NOT NULL,
    filtres_selection TEXT,
    date_programmation TIMESTAMP NOT NULL,
    heure_programmation TEXT NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    statut TEXT DEFAULT 'en_attente',
    FOREIGN KEY (mail_id) REFERENCES mails_enregistres(id)
);

-- Table des emails reçus
CREATE TABLE IF NOT EXISTS emails_recus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expediteur_email TEXT NOT NULL,
    expediteur_nom TEXT,
    client_id INTEGER,
    objet TEXT NOT NULL,
    contenu_html TEXT,
    contenu_texte TEXT,
    date_reception TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lu BOOLEAN DEFAULT 0,
    pieces_jointes TEXT,
    compte_email_recepteur TEXT,
    message_id TEXT UNIQUE,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

-- Table des centres d'intérêt
CREATE TABLE IF NOT EXISTS centres_interet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT UNIQUE NOT NULL
);

-- Table de liaison clients-centres d'intérêt
CREATE TABLE IF NOT EXISTS clients_centres_interet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    centre_interet_id INTEGER NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (centre_interet_id) REFERENCES centres_interet(id),
    UNIQUE(client_id, centre_interet_id)
);

-- Table des codes de réduction
CREATE TABLE IF NOT EXISTS codes_reduction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    pourcentage REAL NOT NULL,
    description TEXT,
    date_debut TEXT NOT NULL,
    date_fin TEXT NOT NULL,
    actif BOOLEAN DEFAULT 1,
    type_utilisation TEXT DEFAULT 'illimite',
    nombre_utilisations INTEGER DEFAULT 0,
    limite_utilisations INTEGER,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des utilisations de codes de réduction
CREATE TABLE IF NOT EXISTS utilisations_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    vente_id INTEGER NOT NULL,
    date_utilisation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (code_id) REFERENCES codes_reduction(id),
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (vente_id) REFERENCES ventes(id)
);

-- Table des commandes
CREATE TABLE IF NOT EXISTS commandes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    date_commande TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_prevue TEXT NOT NULL,
    heure_prevue TEXT,
    statut TEXT DEFAULT 'en_attente',
    total REAL DEFAULT 0.0,
    notes TEXT,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

-- Articles d'une commande
CREATE TABLE IF NOT EXISTS articles_commande (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commande_id INTEGER NOT NULL,
    produit_id INTEGER NOT NULL,
    quantite INTEGER DEFAULT 1,
    prix_unitaire REAL NOT NULL,
    prix_total REAL NOT NULL,
    FOREIGN KEY (commande_id) REFERENCES commandes(id) ON DELETE CASCADE,
    FOREIGN KEY (produit_id) REFERENCES produits(id)
);

-- Catégories de tâches
CREATE TABLE IF NOT EXISTS categories_taches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    couleur TEXT DEFAULT '#2196F3',
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des tâches
CREATE TABLE IF NOT EXISTS taches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    description TEXT,
    priorite INTEGER DEFAULT 5,
    categorie_id INTEGER,
    date_echeance TEXT,
    heure_echeance TEXT,
    terminee BOOLEAN DEFAULT 0,
    visibilite TEXT DEFAULT 'tous',
    commande_id INTEGER,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categorie_id) REFERENCES categories_taches(id),
    FOREIGN KEY (commande_id) REFERENCES commandes(id)
);

-- Table des comptes email configurés
CREATE TABLE IF NOT EXISTS comptes_email (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adresse_email TEXT NOT NULL UNIQUE,
    mot_de_passe_app TEXT NOT NULL,
    nom_affichage TEXT NOT NULL,
    quota_journalier INTEGER DEFAULT 500,
    quota_utilise_aujourd_hui INTEGER DEFAULT 0,
    date_dernier_reset DATE DEFAULT CURRENT_DATE,
    actif BOOLEAN DEFAULT 1,
    ordre_utilisation INTEGER DEFAULT 1,
    serveur_smtp TEXT DEFAULT 'smtp.gmail.com',
    port_smtp INTEGER DEFAULT 587,
    serveur_imap TEXT DEFAULT 'imap.gmail.com',
    port_imap INTEGER DEFAULT 993,
    activer_reception BOOLEAN DEFAULT 0
);
"""

# --- Index pour améliorer les performances des requêtes fréquentes ---
_SQL_CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_clients_nom ON clients(nom);
CREATE INDEX IF NOT EXISTS idx_clients_prenom ON clients(prenom);
CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email);
CREATE INDEX IF NOT EXISTS idx_ventes_client ON ventes(client_id);
CREATE INDEX IF NOT EXISTS idx_ventes_date ON ventes(date_vente);
CREATE INDEX IF NOT EXISTS idx_ventes_produit ON ventes(produit_id);
CREATE INDEX IF NOT EXISTS idx_emails_recus_client ON emails_recus(client_id);
CREATE INDEX IF NOT EXISTS idx_clients_centres_client ON clients_centres_interet(client_id);
CREATE INDEX IF NOT EXISTS idx_clients_centres_interet ON clients_centres_interet(centre_interet_id);
CREATE INDEX IF NOT EXISTS idx_utilisations_codes_client ON utilisations_codes(client_id);
CREATE INDEX IF NOT EXISTS idx_utilisations_codes_code ON utilisations_codes(code_id);
CREATE INDEX IF NOT EXISTS idx_historique_emails_mail ON historique_emails(mail_id);
CREATE INDEX IF NOT EXISTS idx_commandes_client ON commandes(client_id);
CREATE INDEX IF NOT EXISTS idx_commandes_date_prevue ON commandes(date_prevue);
CREATE INDEX IF NOT EXISTS idx_commandes_statut ON commandes(statut);
CREATE INDEX IF NOT EXISTS idx_articles_commande ON articles_commande(commande_id);
CREATE INDEX IF NOT EXISTS idx_taches_categorie ON taches(categorie_id);
CREATE INDEX IF NOT EXISTS idx_taches_date ON taches(date_echeance);
CREATE INDEX IF NOT EXISTS idx_taches_commande ON taches(commande_id);
"""


# ============================================================================
# Données par défaut
# ============================================================================

_DEFAULT_PARAMETRES: list[tuple] = [
    ("mot_de_passe_administratif", None, "texte", "Mot de passe administratif (hashé bcrypt)"),
    ("mot_de_passe_actif", "0", "booleen", "Indique si la gestion par mot de passe est active"),
    ("email_recuperation", None, "email", "Email de récupération"),
    ("monnaie", "EUR", "texte", "Monnaie utilisée"),
    ("symbole_monnaie", "€", "texte", "Symbole de la monnaie"),
    ("nom_entreprise", None, "texte", "Nom de l'entreprise"),
    ("date_creation_entreprise", str(date.today()), "date", "Date de création de l'entreprise"),
    ("langue_interface", "fr", "texte", "Langue de l'interface"),
    ("theme", "clair", "texte", "Thème de l'interface"),
]

# (nom_champ, actif, obligatoire, depend_de, valeur_dependance, type_champ, ordre_affichage)
_DEFAULT_CHAMPS_CLIENTS: list[tuple] = [
    ("nom",                  1, 1, None,                 None, "texte",     1),
    ("prenom",               1, 1, None,                 None, "texte",     2),
    ("date_naissance",       1, 0, None,                 None, "date",      3),
    ("adresse",              1, 0, None,                 None, "texte",     4),
    ("ville",                1, 0, None,                 None, "texte",     5),
    ("code_postal",          1, 0, None,                 None, "texte",     6),
    ("email",                1, 1, None,                 None, "email",     7),
    ("telephone",            1, 0, None,                 None, "telephone", 8),
    ("situation_maritale",   1, 0, None,                 None, "liste",     9),
    ("a_conjoint",           1, 0, "situation_maritale", None, "booleen",  10),
    ("a_enfants",            1, 0, None,                 None, "booleen",  11),
    ("nombre_enfants",       1, 0, "a_enfants",          "1",  "nombre",   12),
    ("a_parents",            1, 0, None,                 None, "booleen",  13),
    ("parents_en_vie",       1, 0, "a_parents",          "1",  "booleen",  14),
    ("profession",           0, 0, None,                 None, "texte",    15),
    ("centre_interet",       0, 0, None,                 None, "texte",    16),
    ("notes_personnalisees", 1, 0, None,                 None, "texte",    17),
]


# ============================================================================
# Classe principale : DatabaseManager
# ============================================================================

class DatabaseManager:
    """Gestionnaire de base de données SQLite (singleton).

    Fournit les méthodes de connexion, d'exécution de requêtes et de
    récupération de résultats sous forme de dictionnaires.

    Attributes:
        db_path: Chemin absolu vers le fichier de base de données SQLite.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialise le gestionnaire et crée les tables si nécessaire.

        Args:
            db_path: Chemin vers le fichier SQLite. Si ``None``, utilise
                     le chemin par défaut ``data/app.db`` relatif au
                     répertoire de l'application.
        """
        self.db_path: str = db_path or _DEFAULT_DB_PATH
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()
        self._transaction_depth: int = 0  # Compteur pour transactions imbriquées

        # Créer le répertoire parent s'il n'existe pas encore
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialiser la base de données (tables + données par défaut)
        self._initialiser_base()

    # ------------------------------------------------------------------
    # Gestion de la connexion
    # ------------------------------------------------------------------

    def get_connection(self) -> sqlite3.Connection:
        """Retourne la connexion SQLite active, en la créant si nécessaire.

        La connexion utilise ``sqlite3.Row`` comme row_factory pour permettre
        l'accès aux colonnes par nom, et active les clés étrangères.

        Returns:
            La connexion SQLite configurée.
        """
        with self._lock:
            if self._connection is None:
                self._connection = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,  # Thread-safety via RLock
                    timeout=10.0
                )
                self._connection.row_factory = sqlite3.Row
                # Activer le support des clés étrangères
                self._connection.execute("PRAGMA foreign_keys = ON")
            return self._connection

    def close(self) -> None:
        """Ferme proprement la connexion à la base de données."""
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None

    # ------------------------------------------------------------------
    # Méthodes d'exécution de requêtes
    # ------------------------------------------------------------------

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Exécute une requête SQL avec des paramètres optionnels.

        Le commit est automatique sauf si une transaction est en cours
        (voir :meth:`transaction`).

        Args:
            query:  La requête SQL à exécuter.
            params: Tuple de paramètres à injecter dans la requête.

        Returns:
            Le curseur résultant de l'exécution.
        """
        with self._lock:
            conn = self.get_connection()
            cursor = conn.execute(query, params)
            # Auto-commit seulement si hors de toute transaction
            if self._transaction_depth == 0:
                conn.commit()
            return cursor

    def executemany(self, query: str, params_list: list) -> sqlite3.Cursor:
        """Exécute une requête SQL pour chaque jeu de paramètres.

        Args:
            query:       La requête SQL à exécuter.
            params_list: Liste de tuples de paramètres.

        Returns:
            Le curseur résultant de l'exécution.
        """
        with self._lock:
            conn = self.get_connection()
            cursor = conn.executemany(query, params_list)
            # Auto-commit seulement si hors de toute transaction
            if self._transaction_depth == 0:
                conn.commit()
            return cursor

    def fetchone(self, query: str, params: tuple = ()) -> Optional[dict]:
        """Exécute une requête et retourne la première ligne sous forme de dict.

        Args:
            query:  La requête SQL à exécuter.
            params: Tuple de paramètres à injecter dans la requête.

        Returns:
            Un dictionnaire représentant la ligne, ou ``None`` si aucun
            résultat.
        """
        with self._lock:
            conn = self.get_connection()
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            if row is None:
                return None
            return dict(row)

    def fetchall(self, query: str, params: tuple = ()) -> list[dict]:
        """Exécute une requête et retourne toutes les lignes sous forme de dicts.

        Args:
            query:  La requête SQL à exécuter.
            params: Tuple de paramètres à injecter dans la requête.

        Returns:
            Une liste de dictionnaires, un par ligne de résultat.
        """
        with self._lock:
            conn = self.get_connection()
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @contextmanager
    def transaction(self):
        """Context manager pour des opérations atomiques multi-requêtes.

        Supporte les transactions imbriquées via un compteur de profondeur.
        Seule la transaction racine (depth=1) commit/rollback réellement.

        Toutes les requêtes exécutées dans le bloc sont regroupées dans
        une seule transaction : commit à la fin si tout réussit, rollback
        en cas d'erreur.

        Usage::

            with db.transaction():
                db.execute("DELETE FROM enfants WHERE client_id = ?", (cid,))
                db.execute("DELETE FROM clients WHERE id = ?", (cid,))
        """
        with self._lock:
            self._transaction_depth += 1
            is_root = self._transaction_depth == 1

            try:
                yield
                # Commit seulement si on sort de la transaction racine
                if is_root:
                    self.get_connection().commit()
            except Exception:
                # Rollback seulement si on sort de la transaction racine
                if is_root:
                    self.get_connection().rollback()
                raise
            finally:
                self._transaction_depth -= 1

    # ------------------------------------------------------------------
    # Initialisation de la base de données
    # ------------------------------------------------------------------

    def _initialiser_base(self) -> None:
        """Crée toutes les tables, les index et insère les données par défaut."""
        conn = self.get_connection()

        # Créer les tables
        conn.executescript(_SQL_CREATE_TABLES)

        # Créer les index
        conn.executescript(_SQL_CREATE_INDEXES)

        # Appliquer les migrations (nouvelles colonnes sur tables existantes)
        self._appliquer_migrations(conn)

        # Insérer les données par défaut (seulement si les tables sont vides)
        self._inserer_parametres_par_defaut()
        self._inserer_champs_clients_par_defaut()

        # S'assurer que les parametres de securite existent
        self._assurer_parametre_existe(
            "mot_de_passe_actif", "0", "booleen",
            "Indique si la gestion par mot de passe est active"
        )
        self._assurer_parametre_existe(
            "mot_de_passe_indice", "", "texte",
            "Indice pour le mot de passe"
        )
        self._assurer_parametre_existe(
            "email_recuperation", "", "email",
            "Email pour recuperer le mot de passe"
        )
        self._assurer_parametre_existe(
            "tentatives_echouees", "0", "nombre",
            "Nombre de tentatives de connexion echouees"
        )

    @staticmethod
    def _appliquer_migrations(conn: sqlite3.Connection) -> None:
        """Ajoute les colonnes manquantes aux tables existantes."""
        migrations = [
            ("clients", "date_mariage", "TEXT"),
            ("clients", "date_pacs", "TEXT"),
            ("clients", "date_deces_conjoint", "TEXT"),
            ("codes_reduction", "type_utilisation", "TEXT DEFAULT 'illimite'"),
            ("clients", "photo_path", "TEXT"),
            ("produits", "stock", "INTEGER DEFAULT 0"),
            ("produits", "archive", "INTEGER DEFAULT 0"),
            ("produits", "photo", "TEXT"),
            ("mails_enregistres", "type", "TEXT DEFAULT 'template'"),
            ("ventes", "transaction_id", "TEXT"),
            ("clients", "sexe", "TEXT"),
        ]
        for table, colonne, type_col in migrations:
            try:
                conn.execute(
                    f"ALTER TABLE {table} ADD COLUMN {colonne} {type_col}"
                )
            except sqlite3.OperationalError:
                pass  # La colonne existe déjà

        # Backfill transaction_id : chaque ancienne ligne = sa propre transaction
        try:
            conn.execute(
                "UPDATE ventes SET transaction_id = CAST(id AS TEXT) "
                "WHERE transaction_id IS NULL"
            )
            conn.commit()
        except sqlite3.OperationalError:
            pass

        # Migration : Colonnes manquantes sur categories_produits
        cat_migrations = [
            ("categories_produits", "description", "TEXT"),
            ("categories_produits", "actif", "INTEGER DEFAULT 1"),
            ("categories_produits", "ordre", "INTEGER DEFAULT 0"),
        ]
        for table, colonne, type_col in cat_migrations:
            try:
                conn.execute(
                    f"ALTER TABLE {table} ADD COLUMN {colonne} {type_col}"
                )
            except sqlite3.OperationalError:
                pass

        # Migration : categorie_id nullable sur produits
        try:
            cols_prod = conn.execute("PRAGMA table_info(produits)").fetchall()
            for col in cols_prod:
                if col[1] == 'categorie_id' and col[3] == 1:  # notnull flag
                    # Sauvegarder, recréer, restaurer
                    data = conn.execute("SELECT * FROM produits").fetchall()
                    col_names = [c[1] for c in cols_prod]
                    conn.execute("DROP TABLE IF EXISTS produits")
                    conn.execute("""
                        CREATE TABLE produits (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            categorie_id INTEGER,
                            nom TEXT NOT NULL,
                            prix REAL DEFAULT 0.0,
                            stock INTEGER DEFAULT 0,
                            description TEXT,
                            photo TEXT,
                            archive INTEGER DEFAULT 0,
                            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (categorie_id) REFERENCES categories_produits(id)
                        )
                    """)
                    for row in data:
                        row_dict = {col_names[i]: row[i] for i in range(len(col_names))}
                        conn.execute(
                            "INSERT INTO produits (id, categorie_id, nom, prix, stock, description, photo, archive, date_creation) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (row_dict.get('id'), row_dict.get('categorie_id'),
                             row_dict.get('nom'), row_dict.get('prix', 0),
                             row_dict.get('stock', 0), row_dict.get('description'),
                             row_dict.get('photo'),
                             row_dict.get('archive', 0),
                             row_dict.get('date_creation')),
                        )
                    break
        except Exception:
            pass

        # Migration : Index sur produits.categorie_id
        try:
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_produits_categorie_id
                ON produits(categorie_id)
            """)
        except Exception:
            pass

        # Migration forcee : Recréer attributs_produits avec categorie_id NULLABLE
        try:
            info = conn.execute("PRAGMA table_info(attributs_produits)").fetchall()
            # Chercher si categorie_id a notnull=1
            needs_migration = False
            for col in info:
                if col[1] == 'categorie_id' and col[3] == 1:  # notnull flag
                    needs_migration = True
                    break

            if needs_migration:
                # Sauvegarder les données
                data = conn.execute(
                    "SELECT id, categorie_id, nom_attribut FROM attributs_produits"
                ).fetchall()

                conn.execute("DROP TABLE IF EXISTS attributs_produits")

                conn.execute("""
                    CREATE TABLE attributs_produits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        categorie_id INTEGER DEFAULT NULL,
                        nom_attribut TEXT NOT NULL,
                        type_attribut TEXT DEFAULT 'texte',
                        par_defaut BOOLEAN DEFAULT 0,
                        ordre_affichage INTEGER,
                        FOREIGN KEY (categorie_id) REFERENCES categories_produits(id)
                    )
                """)

                # Restaurer les données
                for row in data:
                    conn.execute(
                        "INSERT INTO attributs_produits (id, nom_attribut, categorie_id) "
                        "VALUES (?, ?, ?)",
                        (row[0], row[2], row[1]),
                    )
        except Exception:
            # Table n'existe pas encore, elle sera créée par CREATE TABLE IF NOT EXISTS
            pass

        # Migration : colonne couleur sur taches
        try:
            conn.execute("ALTER TABLE taches ADD COLUMN couleur TEXT")
        except sqlite3.OperationalError:
            pass

        # Migration : sous-tâches
        try:
            conn.execute("ALTER TABLE taches ADD COLUMN parent_id INTEGER REFERENCES taches(id)")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE taches ADD COLUMN niveau INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        # Migration : récurrence
        try:
            conn.execute("ALTER TABLE taches ADD COLUMN type_recurrence TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE taches ADD COLUMN intervalle_recurrence INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE taches ADD COLUMN date_fin_recurrence TEXT")
        except sqlite3.OperationalError:
            pass

        # Migration : soft-delete
        try:
            conn.execute("ALTER TABLE taches ADD COLUMN supprimee BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE taches ADD COLUMN date_suppression TIMESTAMP")
        except sqlite3.OperationalError:
            pass

        # Migration : validation admin des missions
        try:
            conn.execute("ALTER TABLE taches ADD COLUMN validee_admin BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        # Index sous-tâches
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_taches_parent ON taches(parent_id)")
        except sqlite3.OperationalError:
            pass

        # Migration : association tâches → client / vente
        try:
            conn.execute("ALTER TABLE taches ADD COLUMN client_id INTEGER REFERENCES clients(id)")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE taches ADD COLUMN vente_id INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE taches ADD COLUMN cochee INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE taches ADD COLUMN produit_id INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE taches ADD COLUMN code_promo_id INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE taches ADD COLUMN evenement_id INTEGER")
        except sqlite3.OperationalError:
            pass

        # Table événements calendrier
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evenements_calendrier (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                description TEXT,
                couleur TEXT DEFAULT '#FF9800',
                date_debut TEXT NOT NULL,
                date_fin TEXT NOT NULL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evenements_dates ON evenements_calendrier(date_debut, date_fin)")
        except sqlite3.OperationalError:
            pass

    def _inserer_parametres_par_defaut(self) -> None:
        """Insère les paramètres par défaut si la table est vide."""
        row = self.fetchone("SELECT COUNT(*) AS nb FROM parametres")
        if row and row["nb"] == 0:
            self.executemany(
                "INSERT INTO parametres (cle, valeur, type, description) VALUES (?, ?, ?, ?)",
                _DEFAULT_PARAMETRES,
            )

    def _assurer_parametre_existe(
        self, cle: str, valeur: str, type_p: str, description: str
    ) -> None:
        """Insère un paramètre s'il n'existe pas encore."""
        row = self.fetchone(
            "SELECT cle FROM parametres WHERE cle = ?", (cle,)
        )
        if row is None:
            self.execute(
                "INSERT INTO parametres (cle, valeur, type, description) VALUES (?, ?, ?, ?)",
                (cle, valeur, type_p, description),
            )

    def _inserer_champs_clients_par_defaut(self) -> None:
        """Insère les champs clients actifs par défaut si la table est vide."""
        row = self.fetchone("SELECT COUNT(*) AS nb FROM champs_clients_actifs")
        if row and row["nb"] == 0:
            self.executemany(
                """INSERT INTO champs_clients_actifs
                   (nom_champ, actif, obligatoire, depend_de, valeur_dependance, type_champ, ordre_affichage)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                _DEFAULT_CHAMPS_CLIENTS,
            )


# ============================================================================
# Fonction d'accès au singleton
# ============================================================================

def get_db() -> DatabaseManager:
    """Retourne l'instance singleton du gestionnaire de base de données.

    Crée l'instance lors du premier appel, puis la réutilise pour tous
    les appels suivants.

    Returns:
        L'instance unique de ``DatabaseManager``.
    """
    global _instance
    if _instance is None:
        _instance = DatabaseManager()
    return _instance
