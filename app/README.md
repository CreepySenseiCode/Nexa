# MailTo - Gestion de Clientèle et Emailing

Application de gestion de clientèle et d'emailing pour petits commerçants.

## Installation

```bash
# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
```

## Lancement

```bash
python main.py
```

## Fonctionnalités

- Gestion complète des clients avec informations personnalisées
- Enregistrement des ventes avec suivi par client
- Recherche avancée de clients avec profil détaillé
- Système de verrouillage Patron/Vendeur
- Emailing ciblé et personnalisé (à venir)
- Statistiques de vente (à venir)

## Architecture

Le projet suit l'architecture MVVM (Model-View-ViewModel) :

- `models/` : Accès base de données et logique métier
- `views/` : Interface graphique PySide6
- `viewmodels/` : Liaison entre modèles et vues
- `utils/` : Utilitaires (validation, formatage, authentification)
- `services/` : Services d'arrière-plan
- `data/` : Base de données SQLite et fichiers

## Stack technique

- Python 3.10+
- PySide6 (Qt for Python)
- SQLite
- bcrypt (authentification)
