# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM — Bridge entrypoint (HTTP REST pour PHP)
# ══════════════════════════════════════════════════════════════════════════════
#  Raccourci CLI : `python bridge.py` lance le serveur HTTP exposant le moteur
#  ATIH à une application PHP (ou tout autre client HTTP).
#
#  Variables d'environnement :
#    SOVEREIGN_BRIDGE_HOST      (défaut: 127.0.0.1)
#    SOVEREIGN_BRIDGE_PORT      (défaut: 8765)
#    SOVEREIGN_BRIDGE_TOKEN     (défaut: vide = auth désactivée)
#    SOVEREIGN_BRIDGE_ORIGINS   (défaut: http://127.0.0.1,http://localhost)
# ══════════════════════════════════════════════════════════════════════════════

from backend.bridge import main

if __name__ == "__main__":
    main()
