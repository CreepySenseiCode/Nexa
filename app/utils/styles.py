"""Styles Qt centralises pour l'application Nexa.

Ce module fournit les constantes de couleurs et les fonctions de style
reutilisables pour toutes les vues de l'application.
"""


# ======================================================================
# Palette de couleurs
# ======================================================================

class Couleurs:
    """Palette de couleurs Material Design de l'application."""

    # --- Bleu principal ---
    PRIMAIRE = "#2196F3"
    PRIMAIRE_FONCE = "#1976D2"
    PRIMAIRE_TRES_FONCE = "#1565C0"
    PRIMAIRE_CLAIR = "#BBDEFB"
    PRIMAIRE_TRES_CLAIR = "#E3F2FD"

    # --- Vert (succes) ---
    SUCCES = "#4CAF50"
    SUCCES_FONCE = "#388E3C"
    SUCCES_TRES_FONCE = "#1B5E20"

    # --- Rouge (danger / erreur) ---
    DANGER = "#F44336"
    DANGER_FONCE = "#D32F2F"
    DANGER_TRES_FONCE = "#B71C1C"
    DANGER_CLAIR = "#FFEBEE"

    # --- Orange (avertissement) ---
    AVERTISSEMENT = "#FF9800"
    AVERTISSEMENT_FONCE = "#F57C00"
    AVERTISSEMENT_TRES_FONCE = "#E65100"
    AVERTISSEMENT_CLAIR = "#FFF3E0"
    AMBRE = "#FFA000"

    # --- Violet ---
    VIOLET = "#9C27B0"

    # --- Cyan / Bleu clair ---
    CYAN = "#00BCD4"
    BLEU_CLAIR = "#03A9F4"
    CYAN_CLAIR = "#E1F5FE"

    # --- Jaune ---
    JAUNE = "#FFC107"

    # --- Marron ---
    MARRON = "#795548"

    # --- Ardoise ---
    ARDOISE = "#607D8B"
    ARDOISE_FONCE = "#455A64"

    # --- Neutres ---
    BLANC = "#FFFFFF"
    FOND_SECTION = "#FAFAFA"
    FOND_CLAIR = "#F5F5F5"
    FOND_GRIS = "#F0F0F0"
    FOND_EEEE = "#EEEEEE"
    BORDURE = "#E0E0E0"
    BORDURE_FONCE = "#CCCCCC"
    GRIS = "#9E9E9E"
    GRIS_CLAIR = "#BDBDBD"
    GRIS_MOYEN = "#757575"
    GRIS_FONCE = "#616161"
    GRIS_TRES_FONCE = "#424242"

    # --- Texte ---
    TEXTE = "#333333"
    TEXTE_SECONDAIRE = "#555555"
    TEXTE_DESACTIVE = "#666666"
    TEXTE_GRIS = "#777777"
    TEXTE_TRES_GRIS = "#999999"


# ======================================================================
# Fonctions de style reutilisables
# ======================================================================

def style_section() -> str:
    """Style QGroupBox pour les sections de formulaire.

    Utilise dans : produits_view, parametres_view, etc.
    """
    return (
        "QGroupBox {"
        f"    font-size: 14pt;"
        f"    font-weight: bold;"
        f"    color: {Couleurs.PRIMAIRE};"
        f"    border: 2px solid {Couleurs.GRIS};"
        f"    border-radius: 10px;"
        f"    background-color: {Couleurs.FOND_SECTION};"
        f"    padding: 20px;"
        f"    margin-top: 20px;"
        "}"
        "QGroupBox::title {"
        "    subcontrol-origin: margin;"
        "    left: 15px;"
        "    padding: 0 8px;"
        f"    background-color: {Couleurs.FOND_SECTION};"
        "}"
    )


def style_groupe() -> str:
    """Style QGroupBox alternatif avec fond blanc.

    Utilise dans : emailing_view, recherche_view.
    """
    return (
        "QGroupBox {"
        f"    font-size: 14pt;"
        f"    font-weight: 600;"
        f"    color: {Couleurs.PRIMAIRE_FONCE};"
        f"    border: 2px solid {Couleurs.PRIMAIRE};"
        f"    border-radius: 12px;"
        f"    background-color: {Couleurs.BLANC};"
        f"    padding: 20px;"
        f"    margin-top: 15px;"
        "}"
        "QGroupBox::title {"
        "    subcontrol-origin: margin;"
        "    left: 20px;"
        "    padding: 0 10px;"
        f"    background-color: {Couleurs.BLANC};"
        "    border-radius: 4px;"
        "}"
    )


def style_input() -> str:
    """Style pour les champs de saisie (QLineEdit, QSpinBox, etc.)."""
    return (
        "QLineEdit, QDateEdit, QDoubleSpinBox, QSpinBox, QComboBox, QTextEdit {"
        f"    border: 2px solid {Couleurs.GRIS};"
        "    border-radius: 6px;"
        "    padding: 8px;"
        "    font-size: 12pt;"
        "    min-height: 32px;"
        f"    background-color: {Couleurs.BLANC};"
        "}"
        "QLineEdit:focus, QDateEdit:focus, QDoubleSpinBox:focus,"
        "QSpinBox:focus, QComboBox:focus, QTextEdit:focus {"
        f"    border: 2px solid {Couleurs.PRIMAIRE};"
        "}"
    )


def style_bouton(couleur: str = None, taille: str = "normal") -> str:
    """Style pour QPushButton.

    Args:
        couleur: Couleur de fond du bouton. Defaut : PRIMAIRE.
        taille: 'petit', 'normal' ou 'grand' pour ajuster la taille.
    """
    c = couleur or Couleurs.PRIMAIRE

    if taille == "petit":
        padding = "8px 16px"
        font_size = "11pt"
        radius = "6px"
        extra = "min-height: 35px;"
    elif taille == "grand":
        padding = "12px 24px"
        font_size = "13pt"
        radius = "8px"
        extra = ""
    else:
        padding = "10px 20px"
        font_size = "12pt"
        radius = "8px"
        extra = ""

    return (
        f"QPushButton {{"
        f"    background-color: {c};"
        f"    color: white;"
        f"    border: none;"
        f"    border-radius: {radius};"
        f"    padding: {padding};"
        f"    font-size: {font_size};"
        f"    font-weight: 600;"
        f"    {extra}"
        f"}}"
        f"QPushButton:hover {{"
        f"    opacity: 0.9;"
        f"}}"
    )


def style_spinbox() -> str:
    """Style enrichi pour QSpinBox/QDoubleSpinBox avec boutons +/-."""
    return (
        "QSpinBox, QDoubleSpinBox {"
        "    min-height: 44px;"
        "    font-size: 13pt;"
        "    padding: 6px 12px;"
        f"    border: 2px solid {Couleurs.BORDURE};"
        "    border-radius: 10px;"
        f"    background: {Couleurs.BLANC};"
        "}"
        "QSpinBox:focus, QDoubleSpinBox:focus {"
        f"    border: 2px solid {Couleurs.PRIMAIRE};"
        "}"
        "QSpinBox::up-button, QSpinBox::down-button,"
        "QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {"
        "    width: 36px;"
        "    border: none;"
        f"    background: {Couleurs.PRIMAIRE};"
        "}"
        "QSpinBox::up-button:hover, QSpinBox::down-button:hover,"
        "QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {"
        f"    background: {Couleurs.PRIMAIRE_FONCE};"
        "}"
        "QSpinBox::up-button, QDoubleSpinBox::up-button {"
        "    border-top-right-radius: 8px;"
        "}"
        "QSpinBox::down-button, QDoubleSpinBox::down-button {"
        "    border-bottom-right-radius: 8px;"
        "}"
    )


def style_onglet(actif: bool) -> str:
    """Style pour un bouton servant d'onglet.

    Args:
        actif: True si l'onglet est actuellement selectionne.
    """
    if actif:
        return (
            "QPushButton {"
            f"    background-color: {Couleurs.PRIMAIRE};"
            "    color: white;"
            "    border: none;"
            "    border-radius: 8px;"
            "    padding: 10px 20px;"
            "    font-size: 12pt;"
            "    font-weight: 600;"
            "}"
        )
    return (
        "QPushButton {"
        f"    background-color: {Couleurs.BORDURE};"
        f"    color: {Couleurs.TEXTE_DESACTIVE};"
        "    border: none;"
        "    border-radius: 8px;"
        "    padding: 10px 20px;"
        "    font-size: 12pt;"
        "}"
        "QPushButton:hover {"
        f"    background-color: {Couleurs.GRIS_CLAIR};"
        "}"
    )


def style_liste_selection() -> str:
    """Style pour QListWidget/QTableWidget avec items plus grands et lisibles."""
    return (
        "QListWidget, QTableWidget {"
        f"    border: 2px solid {Couleurs.BORDURE};"
        "    border-radius: 8px;"
        f"    background-color: {Couleurs.BLANC};"
        "    font-size: 12pt;"
        "}"
        "QListWidget::item, QTableWidget::item {"
        "    min-height: 40px;"
        "    padding: 8px 12px;"
        f"    border-bottom: 1px solid {Couleurs.FOND_GRIS};"
        "}"
        "QListWidget::item:selected, QTableWidget::item:selected {"
        f"    background-color: {Couleurs.PRIMAIRE_TRES_CLAIR};"
        f"    color: {Couleurs.PRIMAIRE_FONCE};"
        "}"
        "QListWidget::item:hover, QTableWidget::item:hover {"
        f"    background-color: {Couleurs.FOND_CLAIR};"
        "}"
    )


def style_toggle(actif: bool) -> str:
    """Style ameliore pour boutons toggle 3 modes."""
    if actif:
        return (
            "QPushButton {"
            f"    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            f"        stop:0 {Couleurs.PRIMAIRE}, stop:1 {Couleurs.PRIMAIRE_FONCE});"
            "    color: white;"
            "    border: none;"
            "    border-radius: 12px;"
            "    padding: 14px 28px;"
            "    font-weight: bold;"
            "    font-size: 13pt;"
            "}"
        )
    return (
        "QPushButton {"
        f"    background-color: {Couleurs.FOND_SECTION};"
        f"    color: {Couleurs.TEXTE};"
        f"    border: 2px solid {Couleurs.BORDURE};"
        "    border-radius: 12px;"
        "    padding: 14px 28px;"
        "    font-size: 13pt;"
        "}"
        "QPushButton:hover {"
        f"    background-color: {Couleurs.PRIMAIRE_TRES_CLAIR};"
        f"    border-color: {Couleurs.PRIMAIRE};"
        "}"
    )


def style_scroll_area() -> str:
    """Style pour QScrollArea avec fond blanc et sans bordure."""
    return (
        "QScrollArea {"
        "    border: none;"
        f"    background-color: {Couleurs.BLANC};"
        "}"
    )
