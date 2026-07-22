# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM - Point d'entrée principal V37
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#  Project : Sovereign OS V37.3 - Station DIM GHT Sud Paris
#
#  Description :
#    Application desktop 100% locale. AUCUN serveur, AUCUNE socket, AUCUN flux
#    reseau. Le frontend communique avec Python uniquement via le pont
#    in-process de pywebview (js_api=Api()).
#
#  Architecture :
#    main.py --> pywebview.create_window() --> frontend/index.html
#             --> js_api=Api() expose backend.interfaces.api.Api au frontend
#             --> les ecrans Sentinel appellent window.pywebview.api.<methode>
#                 (aucun fetch HTTP, cf backend/interfaces/_sentinel.py)
#
#  Usage :
#    - Developpement :  python main.py
#    - Compile .exe :   double-cliquer sur Sovereign_OS_DIM_Portable.exe
# ==============================================================================

from __future__ import annotations

import os
import sys

# ── Force UTF-8 sur la console Windows pour garder les accents (é, è, ç...).
#    1. chcp 65001 bascule cmd.exe en UTF-8 avant le 1er print
#    2. reconfigure(encoding="utf-8") aligne Python sur la même page de code
#    3. _safe_print() fait fallback ASCII si malgré tout l'encodage casse
if sys.platform == "win32":
    try:
        os.system("chcp 65001 >nul 2>&1")
    except OSError:
        pass

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # pragma: no cover · stream null sous .exe
        pass


def _safe_print(*args, **kwargs):
    """Print insensible à l'encodage et au stdout=None (PyInstaller --windowed)."""
    try:
        print(*args, **kwargs)
    except (UnicodeEncodeError, OSError, AttributeError):
        try:
            msg = " ".join(str(a) for a in args)
            sys.stdout.write(msg.encode("ascii", "replace").decode("ascii") + "\n")
        except Exception:
            pass  # mode --windowed avec stdout=None · on abandonne silencieusement


def _check_dependencies():
    """
    Vérifie que les dépendances critiques sont installées et signale les
    manquantes avec un message humain (sans backtrace cryptique).
    """
    errors = []

    if sys.platform == "win32":
        try:
            import clr  # noqa · pythonnet
        except ImportError:
            errors.append(
                "pythonnet n'est pas installé.\n"
                "   ->pip install pythonnet>=3.0.3 (renderer EdgeChromium Windows)"
            )

    try:
        import webview  # noqa
    except ImportError:
        errors.append("pywebview n'est pas installé · pip install pywebview>=5.3.2")

    # Aucune dépendance serveur : l'application est 100% locale (pont pywebview).

    if errors:
        _safe_print("=" * 60)
        _safe_print("  [ERR] DÉPENDANCES MANQUANTES · Sovereign OS DIM")
        _safe_print("=" * 60)
        _safe_print("")
        for e in errors:
            _safe_print(f"  · {e}")
        _safe_print("")
        _safe_print("  Astuce · pip install -r requirements.txt")
        _safe_print("")
        sys.exit(1)


def get_frontend_path():
    """Résout le dossier frontend (mode dev ou bundle PyInstaller)."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "frontend")


# ==============================================================================
# MAIN
# ==============================================================================


def main() -> None:
    _check_dependencies()

    _safe_print("=" * 60)
    _safe_print("  Sovereign OS DIM V37.2 - GHT Psy Sud Paris")
    _safe_print("  100% local - aucun serveur, aucune socket, aucun flux reseau")
    _safe_print("=" * 60)
    _safe_print("")
    _safe_print("[1/1] Lancement de la fenetre pywebview (pont in-process) -")
    import webview
    from backend.interfaces.api import Api

    api = Api()
    frontend = get_frontend_path()
    index_html = os.path.join(frontend, "index.html")
    if not os.path.isfile(index_html):
        _safe_print("")
        _safe_print(f"  [ERR] {index_html} introuvable.")
        sys.exit(1)

    webview.create_window(
        title="Sovereign OS V37.3 · Station DIM · GHT Psy Sud Paris",
        url=index_html,
        js_api=api,
        width=1440,
        height=900,
        min_size=(1100, 700),
        resizable=True,
        background_color="#020617",
        text_select=True,
    )

    # webview.start() bloque jusqu'a la fermeture de la fenetre.
    webview.start(debug=False)
    _safe_print("")
    _safe_print("  Fenetre fermee - arret de l'application.")


if __name__ == "__main__":
    main()
