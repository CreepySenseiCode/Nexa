"""
Utilitaire pour rendre les graphiques Plotly de manière cohérente.
"""


def plotly_to_html(fig) -> str:
    """
    Convertit une figure Plotly en HTML inline (sans CDN).

    Utilisé partout pour éviter les erreurs de certificat macOS.
    """
    return fig.to_html(
        include_plotlyjs='inline',
        full_html=True,
        config={'displayModeBar': False}
    )
