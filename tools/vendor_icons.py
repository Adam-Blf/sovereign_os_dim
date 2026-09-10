"""Rapatrie les icones Icons8 utilisees par l'interface.

Pourquoi : l'interface utilisait la bibliotheque Lucide, chargee depuis un CDN
et melangee a d'autres sources graphiques. Tout passe desormais par un jeu
unique Icons8, en style ligne monochrome, servi depuis le poste.

Usage :
    python tools/vendor_icons.py

Produit :
    frontend/icons/<nom>.png   une icone par nom utilise dans le markup
    frontend/icons/manifest.json

Le markup ne change pas : les elements <i data-lucide="nom"> restent en place,
c'est frontend/js/icons.js qui les transforme en masques CSS colores par
currentColor, ce qui preserve les classes de taille et de couleur existantes.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "frontend" / "icons"

STYLE = "fluency-systems-regular"  # ligne monochrome, fond transparent
SIZE = 96
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

# Nom utilise dans le markup -> nom Icons8, avec des replis si le premier
# n'existe pas dans le style choisi.
MAPPING: dict[str, list[str]] = {
    "activity": ["pulse", "activity-history", "heart-with-pulse"],
    "alert-triangle": ["error", "box-important", "warning-shield"],
    "book": ["book", "literature"],
    "book-open": ["open-book", "book"],
    "brain": ["brain", "artificial-intelligence"],
    "check-circle": ["checkmark-yes", "ok"],
    "check-circle-2": ["checked-2", "checkmark-yes"],
    "circle": ["circled", "unchecked-circle"],
    "circle-slash": ["cancel", "no-entry"],
    "circle-slash-2": ["cancel", "no-entry"],
    "database": ["database", "data-configuration"],
    "download": ["download", "downloading-updates"],
    "download-cloud": ["download-from-cloud", "cloud-download"],
    "file-down": ["file-download", "download-file"],
    "file-spreadsheet": ["ms-excel", "spreadsheet-file"],
    "file-stack": ["copy-file", "documents"],
    "file-text": ["document", "text-file"],
    "file-up": ["upload-file", "import-file"],
    "filter": ["filter", "funnel"],
    "fingerprint": ["fingerprint", "touch-id"],
    "folder": ["folder-invoices", "folder"],
    "folder-open": ["opened-folder", "folder-invoices"],
    "folder-output": ["export-folder", "opened-folder"],
    "folder-plus": ["add-folder", "folder-invoices"],
    "folders": ["folder-tree", "opened-folder"],
    "git-branch": ["code-fork", "org-unit"],
    "git-compare": ["compare-git", "code-fork"],
    "git-fork": ["code-fork", "org-unit"],
    "globe": ["globe", "worldwide-location"],
    "hard-drive": ["hdd", "server"],
    "history": ["restore-page", "time-machine"],
    "info": ["info", "about"],
    "keyboard": ["keyboard", "typing"],
    "layers": ["layers", "stack-of-photos"],
    "layout-grid": ["dashboard-layout", "grid-2"],
    "loader": ["spinner-frame-5", "refresh"],
    "microscope": ["microscope", "biotech"],
    "moon": ["moon-symbol", "crescent-moon"],
    "pie-chart": ["pie-chart", "combo-chart"],
    "power": ["shutdown", "power-off-button"],
    "scan": ["scan", "qr-code"],
    "search": ["search", "find"],
    "shield": ["shield", "security-checked"],
    "shield-check": ["security-checked", "shield"],
    "table-2": ["data-sheet", "grid"],
    "trending-up": ["positive-dynamic", "combo-chart"],
    "upload-cloud": ["upload-to-cloud", "cloud-upload"],
    "users": ["conference-call", "group"],
    "users-2": ["conference-call", "group"],
    "wand-2": ["automation", "idea", "sparkling"],
    "workflow": ["workflow", "flow-chart"],
    "x": ["delete-sign", "close-window"],
    "zap": ["lightning-bolt", "flash-on"],
}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()


def download(name: str, candidates: list[str]) -> tuple[str, int] | None:
    for candidate in candidates:
        url = f"https://img.icons8.com/{STYLE}/{SIZE}/{candidate}.png"
        try:
            data = fetch(url)
        except urllib.error.HTTPError:
            continue
        if len(data) < 200:  # reponse vide ou placeholder
            continue
        (ICONS / f"{name}.png").write_bytes(data)
        return candidate, len(data)
    return None


def main() -> int:
    ICONS.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, str] = {}
    missing: list[str] = []

    for name, candidates in sorted(MAPPING.items()):
        result = download(name, candidates)
        if result is None:
            missing.append(name)
            print(f"{name:18} ECHEC  essais : {', '.join(candidates)}", file=sys.stderr)
            continue
        chosen, size = result
        manifest[name] = chosen
        print(f"{name:18} {chosen:24} {size // 1024:>3} Ko")

    (ICONS / "manifest.json").write_text(
        json.dumps({"style": STYLE, "size": SIZE, "icons": manifest}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n{len(manifest)} icones ecrites dans {ICONS}")
    if missing:
        print(f"{len(missing)} manquantes : {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
