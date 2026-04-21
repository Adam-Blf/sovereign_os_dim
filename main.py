# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM — Point d'entrée principal
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#  Project : Sovereign OS V35.0 — Station DIM GHT Sud Paris
#  Date    : 2026-03-03
#
#  Description:
#    Lance l'application de bureau Sovereign OS via pywebview.
#    La fenêtre native charge le frontend HTML/CSS/JS et expose l'API Python
#    via le js_api de pywebview (window.pywebview.api dans le frontend).
#
#  Architecture:
#    main.py ──► pywebview.create_window() ──► frontend/index.html
#                 └─ js_api=Api() ──► backend/api.py ──► backend/data_processor.py
#
#  Usage:
#    - Développement :  python main.py
#    - Compilé :        PyInstaller (voir build.bat)
# ══════════════════════════════════════════════════════════════════════════════

import os
import sys


def _check_dependencies():
    """
    Vérifie que toutes les dépendances critiques sont installées.

    Pourquoi ? Sur Windows, pywebview nécessite pythonnet pour créer une
    fenêtre native via EdgeChromium (.NET). Sans pythonnet, pywebview lance
    une WebViewException cryptique. On la rend humaine ici.
    """
    errors = []

    # pythonnet est obligatoire sur Windows pour le renderer EdgeChromium
    if sys.platform == "win32":
        try:
            import clr  # noqa: F401 — pythonnet expose le module 'clr'
        except ImportError:
            errors.append(
                "pythonnet n'est pas installé.\n"
                "   → pip install pythonnet>=3.0.3\n"
                "   → Requis pour pywebview sur Windows (renderer EdgeChromium)"
            )

    # pywebview est le cœur de l'application
    try:
        import webview  # noqa: F401
    except ImportError:
        errors.append(
            "pywebview n'est pas installé.\n"
            "   → pip install pywebview>=5.3.2"
        )

    if errors:
        print("╔══════════════════════════════════════════════════════════╗")
        print("║   ❌ DÉPENDANCES MANQUANTES — Sovereign OS DIM          ║")
        print("╚══════════════════════════════════════════════════════════╝")
        print()
        for e in errors:
            print(f"  • {e}")
        print()
        print("  💡 Installez toutes les dépendances avec :")
        print("     pip install -r requirements.txt")
        print()
        sys.exit(1)


def get_frontend_path():
    """
    Résout le chemin du dossier frontend.

    Pourquoi deux cas ? PyInstaller bundle les fichiers dans un dossier
    temporaire (_MEIPASS) quand l'app est compilée. En mode développement,
    on utilise le dossier du script courant.
    """
    if getattr(sys, 'frozen', False):
        # Compilé via PyInstaller — fichiers dans le bundle temporaire
        base = sys._MEIPASS
    else:
        # Mode développement — chemin relatif au script
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "frontend")


def main():
    """
    Point d'entrée de l'application Sovereign OS.

    Crée une fenêtre native pywebview avec :
      - Le frontend HTML chargé localement (pas de serveur HTTP)
      - L'API Python exposée au JavaScript via js_api
      - Une taille de fenêtre optimisée pour les écrans DIM (1440x900)
    """
    # Vérification des dépendances avant tout import lourd
    _check_dependencies()

    # Imports après vérification (pour éviter des crashes non-lisibles)
    import webview
    from backend.api import Api

    # Instanciation de l'API backend
    api = Api()

    # Résolution du chemin vers le frontend
    frontend = get_frontend_path()
    index_html = os.path.join(frontend, "index.html")

    # Vérification que le frontend existe (protège contre les builds cassés)
    if not os.path.isfile(index_html):
        print(f"❌ ERREUR : {index_html} introuvable.")
        print("   Vérifiez que le dossier 'frontend/' est présent.")
        sys.exit(1)

    # Création de la fenêtre native pywebview
    window = webview.create_window(
        title="Sovereign OS V35.0 | Station DIM - GHT Sud Paris",
        url=index_html,
        js_api=api,        # Expose toutes les méthodes publiques de Api()
        width=1440,        # Largeur optimale pour les écrans de bureau DIM
        height=900,        # Hauteur confortable pour la navigation
        min_size=(1100, 700),  # Taille minimum pour garder l'UI lisible
        resizable=True,
        background_color="#020617",  # Fond slate-950 pendant le chargement
        text_select=True,  # Permet la sélection de texte (important pour les IPP)
    )

    # Lancement de la boucle événementielle pywebview
    # debug=True active les DevTools (F12) pour le développement
    webview.start(debug=False)


if __name__ == "__main__":
    main()
