#!/usr/bin/env python
# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM — Synchronisation de la version
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#
#  Rôle :
#    Lit le fichier VERSION à la racine (source de vérité) et propage sa
#    valeur dans tous les fichiers du projet qui en référencent une.
#    Évite que les bumps de version laissent traîner des "V32" dans un coin.
#
#  Usage :
#    python scripts/sync_version.py             # synchronise
#    python scripts/sync_version.py --check     # exit 1 si désync (CI)
#    python scripts/sync_version.py --set V35.1 # bump + synchronise
#
#  Déclenchement automatique :
#    - Le hook hooks/pre-commit appelle ce script avant chaque commit
#      (activable via : git config core.hooksPath hooks)
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "VERSION"

# Fichiers à patcher et pattern à remplacer.
# Le pattern est une regex qui capture le token de version existant.
# Tous les sites référencent la forme "V##.#" OU "V##" (boot screen sans .0).
TARGETS = [
    # (chemin_relatif, regex_pattern, replacement_template)
    # Le template utilise {v} pour la version complète (V35.0)
    # et {vshort} pour la version courte (V35).
    ("backend/api.py",              r"Sovereign OS V\d+\.\d+",   "Sovereign OS {v}"),
    ("backend/bridge.py",           r"Sovereign OS V\d+\.\d+",   "Sovereign OS {v}"),
    ("backend/bridge.py",           r'version="V\d+\.\d+"',      'version="{v}"'),
    ("backend/data_processor.py",   r"Sovereign OS V\d+\.\d+",   "Sovereign OS {v}"),
    ("backend/structure.py",        r"Sovereign OS V\d+\.\d+",   "Sovereign OS {v}"),
    ("backend/__init__.py",         r"Sovereign OS V\d+\.\d+",   "Sovereign OS {v}"),
    ("build.py",                    r"Sovereign OS V\d+\.\d+",   "Sovereign OS {v}"),
    ("main.py",                     r"Sovereign OS V\d+\.\d+",   "Sovereign OS {v}"),
    ("tools/generate_manual.py",    r"Sovereign OS V\d+\.\d+",   "Sovereign OS {v}"),
    ("README.md",                   r"Sovereign OS V\d+\.\d+",   "Sovereign OS {v}"),
    # Frontend — titre + footer + boot screen
    ("frontend/index.html",         r"Sovereign OS V\d+\.\d+",   "Sovereign OS {v}"),
    ("frontend/index.html",         r"GHT Sud Paris Station V\d+\.\d+", "GHT Sud Paris Station {v}"),
    ("frontend/index.html",         r"V\d+\.\d+\.ENTERPRISE",    "{v}.ENTERPRISE"),
    # Boot screen : "SENTINEL <span>V35</span>" (version courte)
    (
        "frontend/index.html",
        r'(SENTINEL <span class="text-gh-teal">)V\d+(</span>)',
        r"\1{vshort}\2",
    ),
    # JS
    ("frontend/js/app.js",          r"SOVEREIGN OS V\d+\.\d+",   "SOVEREIGN OS {v}"),
    ("frontend/js/app.js",          r"Sentinel V\d+\.\d+",       "Sentinel {v}"),
    ("frontend/js/app.js",          r"Sovereign OS V\d+\.\d+",   "Sovereign OS {v}"),
]


def read_version() -> str:
    """Charge la version canonique depuis VERSION à la racine."""
    if not VERSION_FILE.is_file():
        print(f"[!] VERSION file missing at {VERSION_FILE}", file=sys.stderr)
        sys.exit(2)
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def short_version(v: str) -> str:
    """V35.0 -> V35. Utilisé pour le titre du boot screen."""
    m = re.match(r"^(V\d+)(?:\.\d+)?$", v)
    return m.group(1) if m else v


def patch_file(path: Path, pattern: str, replacement: str,
               dry_run: bool = False) -> tuple[int, str]:
    """
    Applique un replace regex. Retourne (nombre de remplacements EFFECTIFS,
    contenu final). On ne compte que les remplacements qui changent le
    texte — un match regex qui réécrit la même chaîne (version déjà à
    jour) n'est pas compté comme désynchronisé.
    """
    if not path.is_file():
        return 0, ""
    original = path.read_text(encoding="utf-8")
    new_content = re.sub(pattern, replacement, original)
    if new_content == original:
        return 0, original
    if not dry_run:
        path.write_text(new_content, encoding="utf-8", newline="\n")
    # Nombre de vrais remplacements : on compte les différences ligne par ligne.
    # Précis mais suffisant pour le reporting (l'info clé est "désynchronisé
    # ou pas").
    changes = sum(
        1 for a, b in zip(original.splitlines(), new_content.splitlines())
        if a != b
    )
    return max(changes, 1), new_content


def sync(new_version: str | None = None, check: bool = False) -> int:
    """
    Synchronise (ou vérifie) la version. Retourne 0 si tout est cohérent,
    1 si des fichiers sont désynchronisés (en mode --check).
    """
    if new_version:
        # Bump : on écrit VERSION puis on propage
        VERSION_FILE.write_text(new_version + "\n", encoding="utf-8",
                                 newline="\n")
    version = read_version()
    vshort = short_version(version)

    total_changes = 0
    desynced_files = []
    for rel, pattern, repl in TARGETS:
        path = ROOT / rel
        rendered = repl.replace("{v}", version).replace("{vshort}", vshort)
        n, _ = patch_file(path, pattern, rendered, dry_run=check)
        if n > 0:
            if check:
                desynced_files.append(f"{rel} ({n} occurrence(s))")
            else:
                total_changes += n

    if check:
        if desynced_files:
            print(
                "[!] Version désynchronisée dans :\n  - "
                + "\n  - ".join(desynced_files)
                + f"\n    Attendu : {version}"
                + f"\n    Correctif : python scripts/sync_version.py",
                file=sys.stderr,
            )
            return 1
        print(f"[OK] Version {version} synchronisée dans tous les fichiers.")
        return 0

    print(f"[OK] Version {version} propagée ({total_changes} remplacement(s)).")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Synchronise la version Sovereign OS DIM depuis VERSION."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Vérifie sans écrire. Exit 1 si désync (pour CI / pre-commit).",
    )
    parser.add_argument(
        "--set",
        metavar="VERSION",
        help="Définit une nouvelle version (ex : V35.1) puis synchronise.",
    )
    args = parser.parse_args()

    sys.exit(sync(new_version=args.set, check=args.check))


if __name__ == "__main__":
    main()
