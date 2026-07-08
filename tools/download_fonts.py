import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
os.makedirs(FONT_DIR, exist_ok=True)

# Plus Jakarta Sans de tokotype/PlusJakartaSans (master)
# JetBrains Mono de JetBrains/JetBrainsMono (master ou main)
FONTS = {
    "PlusJakartaSans-Regular.ttf": "https://github.com/tokotype/PlusJakartaSans/raw/master/fonts/ttf/PlusJakartaSans-Regular.ttf",
    "PlusJakartaSans-Bold.ttf": "https://github.com/tokotype/PlusJakartaSans/raw/master/fonts/ttf/PlusJakartaSans-Bold.ttf",
    "PlusJakartaSans-Italic.ttf": "https://github.com/tokotype/PlusJakartaSans/raw/master/fonts/ttf/PlusJakartaSans-Italic.ttf",
    "PlusJakartaSans-BoldItalic.ttf": "https://github.com/tokotype/PlusJakartaSans/raw/master/fonts/ttf/PlusJakartaSans-BoldItalic.ttf",
    "JetBrainsMono-Regular.ttf": "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Regular.ttf",
    "JetBrainsMono-Bold.ttf": "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Bold.ttf",
    "JetBrainsMono-Italic.ttf": "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Italic.ttf",
    "JetBrainsMono-BoldItalic.ttf": "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-BoldItalic.ttf",
    # Montserrat de JulietaUla/Montserrat (OFL), variantes statiques
    "Montserrat-Regular.ttf": "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Regular.ttf",
    "Montserrat-Bold.ttf": "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf",
    "Montserrat-Italic.ttf": "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Italic.ttf",
    "Montserrat-BoldItalic.ttf": "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-BoldItalic.ttf",
}

for name, url in FONTS.items():
    dest = os.path.join(FONT_DIR, name)
    if os.path.exists(dest):
        print(f"[OK] {name} déjà présent.")
        continue
    print(f"Téléchargement de {name} depuis {url}...")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"[OK] {name} téléchargé.")
    except Exception as e:
        print(f"[ERREUR] Tentative master échouée pour {name}: {e}")
        # fallback sur la branche main si master échoue
        fallback_url = url.replace("/master/", "/main/")
        print(f"Tentative de téléchargement depuis {fallback_url}...")
        try:
            urllib.request.urlretrieve(fallback_url, dest)
            print(f"[OK] {name} téléchargé (branche main).")
        except Exception as e2:
            print(f"[ERREUR COMPLÈTE] Impossible de télécharger {name}: {e2}")
