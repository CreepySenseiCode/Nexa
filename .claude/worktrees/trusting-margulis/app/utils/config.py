"""Configuration centralisee de l'application Nexa."""

import os

_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Chemins ---
DB_PATH = os.path.join(_APP_DIR, "data", "app.db")
PHOTOS_DIR = os.path.join(_APP_DIR, "photos_clients")
ATTACHMENTS_DIR = os.path.join(_APP_DIR, "data", "attachments")
LOGS_DIR = os.path.join(_APP_DIR, "data", "logs")

# --- SMTP / IMAP defaults ---
SMTP_DEFAULT_SERVER = "smtp.gmail.com"
SMTP_DEFAULT_PORT = 587
IMAP_DEFAULT_SERVER = "imap.gmail.com"
IMAP_DEFAULT_PORT = 993
