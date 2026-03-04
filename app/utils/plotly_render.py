"""
Utilitaire pour rendre les graphiques Plotly de manière cohérente.

QWebEngineView.setHtml() a une limite de ~2 Mo (IPC Chromium).
Plotly inline JS fait ~3 Mo → on écrit dans un fichier temporaire
et on charge via setUrl().
"""

import os
import tempfile

from PySide6.QtCore import QUrl


def plotly_to_html(fig) -> str:
    """Convertit une figure Plotly en HTML inline (sans CDN)."""
    return fig.to_html(
        include_plotlyjs='inline',
        full_html=True,
        config={'displayModeBar': False},
    )


def charger_plotly_dans_view(view, fig) -> None:
    """Écrit le HTML Plotly dans un fichier temporaire et le charge dans un QWebEngineView.

    Contourne la limite de 2 Mo de setHtml() en passant par setUrl().
    """
    html = plotly_to_html(fig)
    fd, path = tempfile.mkstemp(suffix=".html", prefix="nexa_plotly_")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(html)
        view.setUrl(QUrl.fromLocalFile(path))
    except Exception:
        # Fallback : essayer setHtml (ne marchera peut-être pas si trop gros)
        view.setHtml(html)
