# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM — Point d'entrée principal V37
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#  Project : Sovereign OS V37.0 — Station DIM GHT Sud Paris
#
#  Description ·
#    Lance l'écosystème complet en un seul .exe ·
#      1. Bridge Flask (port 8765) · API legacy + intégration PHP
#      2. FastAPI v2 (port 8766) · API moderne pour les vues Sentinel V36+
#      3. Fenêtre pywebview · charge le frontend HTML/CSS/JS qui consomme
#         les 2 API en parallèle
#
#    Les 2 serveurs tournent en threads daemon · ils s'arrêtent
#    automatiquement quand la fenêtre se ferme.
#
#  Architecture ·
#    main.py ──► [Thread Flask :8765] backend/bridge.py
#            ──► [Thread FastAPI :8766] backend/fastapi_app.py
#            ──► pywebview.create_window() ──► frontend/index.html
#                 └─ js_api=Api() · expose backend.api.Api au frontend
#                 └─ fetch http://127.0.0.1:8766/api/v2/* via Sentinel views
#
#  Usage ·
#    - Développement ·  python main.py
#    - Compilé .exe ·   double-cliquer sur Sovereign_OS_DIM_Portable.exe
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations

import contextlib
import os
import socket
import sys
import threading
import time


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

    # FastAPI + Flask sont fortement recommandées (les vues live en dépendent)
    # mais on n'en fait pas un blocage · l'app marche en mode mock sinon.

    if errors:
        print("╔══════════════════════════════════════════════════════════╗")
        print("║   [ERR] DÉPENDANCES MANQUANTES · Sovereign OS DIM          ║")
        print("╚══════════════════════════════════════════════════════════╝\n")
        for e in errors:
            print(f"  · {e}")
        print("\n  Astuce · pip install -r requirements.txt\n")
        sys.exit(1)


def get_frontend_path():
    """Résout le dossier frontend (mode dev ou bundle PyInstaller)."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "frontend")


# ══════════════════════════════════════════════════════════════════════════════
# SERVEURS EN THREADS DAEMON · Flask + FastAPI lancés au boot
# ══════════════════════════════════════════════════════════════════════════════

def _is_port_free(port: int, host: str = "127.0.0.1") -> bool:
    """True si on peut binder le port · sinon un autre process l'utilise."""
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def _start_flask_bridge(port: int = 8765) -> threading.Thread | None:
    """Démarre le bridge Flask en thread daemon · serveur silencieux en prod."""
    if not _is_port_free(port):
        print(f"  · Bridge Flask · port {port} déjà occupé, skip")
        return None

    def _run():
        try:
            from backend.bridge import create_app
            app = create_app()
            # Werkzeug silencieux pour ne pas polluer la console
            import logging
            logging.getLogger("werkzeug").setLevel(logging.WARNING)
            app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
        except Exception as e:  # pragma: no cover
            print(f"  [ERR] Bridge Flask · {e}")

    t = threading.Thread(target=_run, daemon=True, name="sovereign-flask-bridge")
    t.start()
    print(f"  [OK] Bridge Flask · http://127.0.0.1:{port}")
    return t


def _start_fastapi_v2(port: int = 8766) -> threading.Thread | None:
    """Démarre la FastAPI v2 (uvicorn) en thread daemon."""
    if not _is_port_free(port):
        print(f"  · FastAPI v2 · port {port} déjà occupé, skip")
        return None

    def _run():
        try:
            import uvicorn
            from backend.fastapi_app import app
            config = uvicorn.Config(
                app, host="127.0.0.1", port=port,
                log_level="warning", access_log=False,
            )
            server = uvicorn.Server(config)
            server.run()
        except ImportError as e:
            print(f"  · FastAPI v2 · dépendance manquante ({e}) · "
                  "skip (mode mock dans l'UI)")
        except Exception as e:  # pragma: no cover
            print(f"  [ERR] FastAPI v2 · {e}")

    t = threading.Thread(target=_run, daemon=True, name="sovereign-fastapi-v2")
    t.start()
    print(f"  [OK] FastAPI v2 · http://127.0.0.1:{port}/docs")
    return t


def _wait_for_servers(timeout: float = 6.0) -> None:
    """
    Attend que Flask et FastAPI répondent sur leurs ports avant de lancer
    pywebview · évite l'effet de "DONNÉES MOCK" au boot pendant que les
    serveurs finissent de démarrer.
    """
    deadline = time.time() + timeout
    targets = [8765, 8766]
    while time.time() < deadline and targets:
        for p in list(targets):
            try:
                with socket.create_connection(("127.0.0.1", p), timeout=0.2):
                    targets.remove(p)
            except OSError:
                continue
        if targets:
            time.sleep(0.1)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    _check_dependencies()

    print("╔══════════════════════════════════════════════════════════╗")
    print("║   Sovereign OS DIM V37.0 · GHT Psy Sud Paris             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("\n[1/3] Démarrage des serveurs API ·")
    flask_thread = _start_flask_bridge(port=8765)
    fastapi_thread = _start_fastapi_v2(port=8766)

    print("\n[2/3] Attente des serveurs (max 6 s) ·")
    _wait_for_servers(timeout=6.0)
    print("       ->prêt")

    print("\n[3/3] Lancement de la fenêtre pywebview ·")
    import webview
    from backend.api import Api

    api = Api()
    frontend = get_frontend_path()
    index_html = os.path.join(frontend, "index.html")
    if not os.path.isfile(index_html):
        print(f"\n  [ERR] ERREUR · {index_html} introuvable.")
        sys.exit(1)

    webview.create_window(
        title="Sovereign OS V37.0 | Station DIM · GHT Psy Sud Paris",
        url=index_html,
        js_api=api,
        width=1440,
        height=900,
        min_size=(1100, 700),
        resizable=True,
        background_color="#020617",
        text_select=True,
    )

    # webview.start() bloque jusqu'à fermeture · les threads daemon
    # s'arrêtent automatiquement à ce moment-là.
    webview.start(debug=False)
    print("\n  ->Fenêtre fermée · arrêt des serveurs (threads daemon).")


if __name__ == "__main__":
    main()
