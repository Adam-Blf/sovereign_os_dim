"""Télécharge les polices Montserrat utilisées par le projet.

Deux destinations :
- tools/fonts/     : variantes R/B/I/BI pour les générateurs PDF (fpdf2)
- frontend/fonts/  : graisses 400-900 auto-hébergées par l'interface
  (aucun CDN : le frontend doit fonctionner 100% hors-ligne)

Source : depot officiel JulietaUla/Montserrat (licence OFL).
Idempotent : les fichiers déjà présents ne sont pas retéléchargés.
"""

import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf"

TARGETS = {
    os.path.join(HERE, "fonts"): [
        "Montserrat-Regular.ttf",
        "Montserrat-Bold.ttf",
        "Montserrat-Italic.ttf",
        "Montserrat-BoldItalic.ttf",
    ],
    os.path.join(HERE, "..", "frontend", "fonts"): [
        "Montserrat-Regular.ttf",
        "Montserrat-Medium.ttf",
        "Montserrat-SemiBold.ttf",
        "Montserrat-Bold.ttf",
        "Montserrat-ExtraBold.ttf",
        "Montserrat-Black.ttf",
    ],
}

for font_dir, names in TARGETS.items():
    os.makedirs(font_dir, exist_ok=True)
    for name in names:
        dest = os.path.join(font_dir, name)
        if os.path.exists(dest):
            print(f"[OK] {name} déjà présent dans {os.path.relpath(font_dir, HERE)}.")
            continue
        url = f"{BASE}/{name}"
        print(f"Téléchargement de {name}...")
        try:
            urllib.request.urlretrieve(url, dest)  # nosec B310 - URL https fixe
            print(f"[OK] {name} téléchargé.")
        except OSError as e:
            print(f"[ERREUR] {name} : {e}")
