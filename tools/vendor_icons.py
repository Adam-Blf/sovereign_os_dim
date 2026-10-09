"""Genere frontend/vendor/reicon-icons.js, les glyphes Reicon de l'interface.

Pourquoi : le frontend tourne dans pywebview, hors ligne, sans CDN ni serveur.
Les glyphes sont donc extraits une fois du paquet npm `reicon` (licence MIT, version
figee ci-dessous) et ecrits en JavaScript, sans autre fichier a charger. Le
runtime qui les pose dans la page est frontend/js/icons.js.

Usage :
    python tools/vendor_icons.py

Necessite npm sur le poste de developpement, jamais sur le poste DIM.

Produit :
    frontend/vendor/reicon-icons.js      table nom -> contenu SVG (graisse Outline)
    frontend/vendor/reicon-LICENSE.txt   texte de la licence Reicon

Un glyphe nouveau s'ajoute a ICONS, puis on relance le script. Le script refuse un
composant absent du catalogue : un glyphe introuvable se signale, il ne s'approxime pas.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "frontend" / "vendor"

REICON_PACKAGE = "reicon@1.2.5"
REICON_LICENSE_URL = "https://raw.githubusercontent.com/dqev/reicon/main/LICENSE"

# nom utilise par l'interface (attribut data-icon) -> composant du catalogue Reicon.
ICONS = {
    "alert-triangle": "AlertTriangle",
    "bolt": "Bolt",
    "book": "Book",
    "book-open": "BookOpen",
    "bubble": "Bubble",
    "category": "Category",
    "chart-pie": "ChartPie",
    "check": "Check",
    "check-circle": "CheckCircle",
    "clipboard-check": "ClipboardCheck",
    "cloud-download": "CloudDownload",
    "cloud-upload": "CloudUpload",
    "database": "Database",
    "diagram-tree": "DiagramTree",
    "download": "Download",
    "edit2": "Edit2",
    "file-down": "FileDown",
    "file-text": "FileText",
    "file-up": "FileUp",
    "files": "Files",
    "filter": "Filter",
    "fingerprint": "Fingerprint",
    "folder": "Folder",
    "folder-files": "FolderFiles",
    "folder-move": "FolderMove",
    "folder-open": "FolderOpen",
    "folder-plus": "FolderPlus",
    "forbidden-circle": "ForbiddenCircle",
    "gauge": "Gauge",
    "globe": "Globe",
    "grid2": "Grid2",
    "hard-drive": "HardDrive",
    "hierarchy2": "Hierarchy2",
    "hierarchy3": "Hierarchy3",
    "history": "History",
    "inbox": "Inbox",
    "info-circle": "InfoCircle",
    "keyboard": "Keyboard",
    "layers": "Layers",
    "loader": "Loader",
    "magic-wand": "MagicWand",
    "microscope": "Microscope",
    "minus": "Minus",
    "moon": "Moon",
    "power": "Power",
    "record": "Record",
    "record-circle3": "RecordCircle3",
    "scan": "Scan",
    "search": "Search",
    "send": "Send",
    "shield": "Shield",
    "shield-check": "ShieldCheck",
    "structure": "Structure",
    "sun": "Sun",
    "swap-horizontal": "ArrowSwapHorizontal",
    "trend-down": "TrendDown",
    "trend-up": "TrendUp",
    "user": "User",
    "user-check": "UserCheck",
    "users": "Users",
    "users2": "Users2",
    "wave-pulse": "WavePulse",
    "wifi-off": "WifiOff",
    "x": "X",
}

# Glyphes sans equivalent chez Reicon : le trace d'origine est conserve ici, en
# trait sur la meme grille de 24 px. Aucun cerveau dans le catalogue Reicon.
KEPT_TRACES = {
    "brain": (
        '<g stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M12 18V5"/>'
        '<path d="M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"/>'
        '<path d="M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"/>'
        '<path d="M17.997 5.125a4 4 0 0 1 2.526 5.77"/>'
        '<path d="M18 18a4 4 0 0 0 2-7.464"/>'
        '<path d="M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"/>'
        '<path d="M6 18a4 4 0 0 1-2-7.464"/>'
        '<path d="M6.003 5.125a4 4 0 0 0-2.526 5.77"/>'
        "</g>"
    ),
}


def outline(source: str, component: str) -> str:
    match = re.search(r"^  O: `(.*?)`", source, flags=re.S | re.M)
    if match is None:
        raise ValueError(f"{component} : trace Outline introuvable")
    return match.group(1)


def main() -> int:
    npm = shutil.which("npm")
    if npm is None:
        print("npm introuvable : icones non rapatriees", file=sys.stderr)
        return 1
    glyphs: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([npm, "pack", REICON_PACKAGE, "--silent"], cwd=tmp, check=True,
                       stdout=subprocess.DEVNULL)
        with tarfile.open(next(Path(tmp).glob("*.tgz"))) as tar:
            tar.extractall(tmp, filter="data")
        components = Path(tmp) / "package" / "icons"
        for name, component in sorted(ICONS.items()):
            path = components / f"{component}.js"
            if not path.exists():
                print(f"composant absent du catalogue : {component}", file=sys.stderr)
                return 1
            glyphs[name] = outline(path.read_text(encoding="utf-8"), component)
    glyphs.update(KEPT_TRACES)

    VENDOR.mkdir(parents=True, exist_ok=True)
    body = json.dumps(dict(sorted(glyphs.items())), ensure_ascii=False, indent=2)
    (VENDOR / "reicon-icons.js").write_text(
        "/* Genere par tools/vendor_icons.py, ne pas editer a la main.\n"
        f" * Reicon ({REICON_PACKAGE}), licence MIT : voir vendor/reicon-LICENSE.txt. */\n"
        f"window.REICON_ICONS = {body};\n",
        encoding="utf-8",
    )
    with urllib.request.urlopen(REICON_LICENSE_URL, timeout=60) as response:
        (VENDOR / "reicon-LICENSE.txt").write_bytes(response.read())
    print(f"{len(glyphs)} glyphes dans {VENDOR / 'reicon-icons.js'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
