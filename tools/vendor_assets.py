"""Rapatrie en local les bibliotheques et polices du frontend.

Pourquoi : l'application tourne sur des postes DIM sans acces internet, et la
Direction des Ressources Numeriques exige zero flux sortant. Toute dependance
servie par un CDN casse l'interface sur un poste isole.

Usage :
    python tools/vendor_assets.py

Produit :
    frontend/vendor/tailwind.js       (Tailwind Play CDN)
    frontend/vendor/chart.umd.js      (graphiques)
    frontend/vendor/anime.min.js      (animations)
    frontend/fonts/fonts.css          (@font-face reecrits en chemins locaux)
    frontend/fonts/*.woff2            (Montserrat, IBM Plex Mono)

index.html reference ces chemins. Apres execution, aucun `https://` ne doit
subsister dans frontend/ hors commentaires :

    grep -rn "https://" frontend/index.html frontend/css frontend/js
"""

from __future__ import annotations

import hashlib
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "frontend" / "vendor"
FONTS = ROOT / "frontend" / "fonts"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

LIBS = {
    "tailwind.js": "https://cdn.tailwindcss.com",
    "chart.umd.js": "https://cdn.jsdelivr.net/npm/chart.js",
    "anime.min.js": "https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.1/anime.min.js",
}

# Typographie du produit : Montserrat pour le texte, IBM Plex Mono pour le
# monospace. Pas de Plus Jakarta Sans, pas de JetBrains Mono.
FONTS_CSS = (
    "https://fonts.googleapis.com/css2"
    "?family=Montserrat:wght@300;400;500;600;700;800;900"
    "&family=IBM+Plex+Mono:wght@400;600;700&display=swap"
)

FAMILY_SLUGS = {
    "ibmplexmono": "ibmplexmono",
    "montserrat": "montserrat",
}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def vendor_libs() -> None:
    VENDOR.mkdir(parents=True, exist_ok=True)
    for name, url in LIBS.items():
        data = fetch(url)
        (VENDOR / name).write_bytes(data)
        print(f"{name:18} {len(data) // 1024:>5} Ko")


def vendor_fonts() -> None:
    FONTS.mkdir(parents=True, exist_ok=True)
    css = fetch(FONTS_CSS).decode("utf-8")
    urls = sorted(set(re.findall(r"https://fonts\.gstatic\.com/[^)]+\.woff2", css)))
    for url in urls:
        family = next(
            (slug for key, slug in FAMILY_SLUGS.items() if key in url.lower()),
            "font",
        )
        filename = f"{family}-{hashlib.sha1(url.encode()).hexdigest()[:8]}.woff2"
        data = fetch(url)
        (FONTS / filename).write_bytes(data)
        css = css.replace(url, filename)
        print(f"{filename:34} {len(data) // 1024:>5} Ko")
    (FONTS / "fonts.css").write_text(css, encoding="utf-8")
    remaining = len(re.findall(r"https://", css))
    if remaining:
        print(f"attention : {remaining} URL restantes dans fonts.css", file=sys.stderr)


def main() -> int:
    vendor_libs()
    vendor_fonts()
    print("\nPenser a verifier index.html : aucun script ni lien vers un CDN.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
