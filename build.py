# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM — Script de build Python
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#  Project : Sovereign OS V35.0 — Station DIM GHT Sud Paris
#
#  Description :
#    Compile l'application en .exe portable Windows via PyInstaller.
#    Remplace build.bat, souvent bloqué par les antivirus d'entreprise
#    (les scripts .bat/.cmd sont catégorisés à risque par Defender for
#    Endpoint et plusieurs EDR hospitaliers).
#
#  Avantages vs .bat :
#    - Python est déjà installé et autorisé sur le poste (dev env)
#    - Pas d'exécutable shell externe → aucune alerte EDR
#    - Multi-plateforme (le même script marche sous Linux/Mac si besoin)
#    - Contrôle d'erreur fin (codes de retour Python propres)
#    - Facile à étendre (options CLI, logs structurés)
#
#  Usage :
#    python build.py                # compile les deux formats (dossier + portable)
#    python build.py --only portable   # seulement l'exe portable (plus lent au démarrage)
#    python build.py --only dir        # seulement le format dossier (démarrage rapide)
#    python build.py --skip-deps       # skip pip install (si déjà à jour)
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Racine du projet = dossier contenant ce script. On force le CWD ici pour
# que PyInstaller résolve les chemins relatifs identiquement quel que soit
# le répertoire courant de l'utilisateur.
ROOT = Path(__file__).resolve().parent

# Modules Python que PyInstaller doit embarquer explicitement. pywebview
# charge pythonnet/clr dynamiquement sous Windows, ce qui échappe à
# l'analyse statique d'imports. On les ajoute en hidden-import.
HIDDEN_IMPORTS = [
    "clr",
    "clr_loader",
    "clr_loader.ffi",
    "clr_loader.ffi.coreclr",
    "clr_loader.ffi.mono",
    "clr_loader.ffi.netfx",
    "pythonnet",
    "cffi",
    "pycparser",
    # Modules du projet — normalement auto-détectés, mais on les explicite
    # pour que l'omission d'un import indirect ne casse pas le build.
    "backend.structure",
    "backend.bridge",
    "backend.api",
    "backend.data_processor",
    "backend.fastapi_app",
    "backend.ml",
    "backend.ml.predict",
    "backend.ml.synthetic",
    # Excel (utilisé par le bridge pour /api/import-excel)
    "openpyxl",
    # FastAPI v2 (V37+) · uvicorn charge h11/httptools/anyio dynamiquement
    "fastapi",
    "uvicorn",
    "uvicorn.loops.asyncio",
    "uvicorn.lifespan.on",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.logging",
    "h11",
    "anyio",
    "anyio._backends._asyncio",
    "sniffio",
    "starlette",
    "starlette.routing",
    "pydantic",
    "pydantic_core",
    # ML (XGBoost stack) · embarqué pour inférence locale
    "xgboost",
    "lightgbm",
    "sklearn.ensemble._forest",
    "sklearn.tree._utils",
    "numpy",
]

# Paquets à collecter en entier (données + submodules).
COLLECT_ALL = [
    "webview", "clr_loader", "pythonnet",
    "fastapi", "uvicorn", "starlette", "pydantic", "pydantic_core",
]

# Modules à inclure avec leurs données (poids des modèles ML, etc.)
ADD_DATA = [
    ("frontend", "frontend"),
    ("backend/ml/models", "backend/ml/models"),
]


def _run(cmd: list[str], step: str) -> None:
    """
    Exécute une commande et propage l'erreur si elle échoue.

    On n'utilise pas shell=True : les arguments sont passés en liste, donc
    pas d'interprétation de métacaractères shell → aucun risque d'injection.
    """
    print(f"\n[{step}] {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, cwd=ROOT)
    except subprocess.CalledProcessError as e:
        print(f"  [!] Echec (code {e.returncode})")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print(f"  [!] Binaire introuvable : {cmd[0]}")
        sys.exit(127)


def _clean_artifacts() -> None:
    """
    Supprime les artefacts PyInstaller d'un build précédent (dist/, build/,
    *.spec). Empêche les conflits entre builds successifs.
    """
    for d in ("build", "dist"):
        p = ROOT / d
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
    for spec in ROOT.glob("*.spec"):
        spec.unlink(missing_ok=True)


def _pyinstaller_args(name: str, onefile: bool) -> list[str]:
    """
    Construit la liste d'arguments PyInstaller commune aux deux formats.
    Le flag `onefile` bascule entre --onedir (rapide) et --onefile (portable).
    """
    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name", name,
        "--icon", "frontend/favicon.ico",
    ]
    # Données embarquées (frontend + modèles ML)
    for src, dst in ADD_DATA:
        if (ROOT / src).exists():
            args += ["--add-data", f"{src};{dst}"]
    args.append("--onefile" if onefile else "--onedir")
    for h in HIDDEN_IMPORTS:
        args += ["--hidden-import", h]
    for c in COLLECT_ALL:
        args += ["--collect-all", c]
    args.append("main.py")
    return args


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Sovereign OS DIM en .exe Windows via PyInstaller."
    )
    parser.add_argument(
        "--only",
        choices=("dir", "portable", "both"),
        default="both",
        help="Format(s) à produire : dir, portable, ou both (défaut).",
    )
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Ne pas réinstaller les dépendances pip.",
    )
    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="Ne pas supprimer dist/build avant de compiler.",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  SOVEREIGN OS DIM — Build Production")
    print("=" * 70)

    if not args.skip_deps:
        _run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            step="1/3 Dependances",
        )
    else:
        print("\n[1/3] Skip pip install (--skip-deps)")

    if not args.skip_clean:
        _clean_artifacts()

    if args.only in ("dir", "both"):
        _run(
            _pyinstaller_args("Sovereign_OS_DIM", onefile=False),
            step="2/3 Format Dossier (onedir — demarrage rapide)",
        )

    if args.only in ("portable", "both"):
        _run(
            _pyinstaller_args("Sovereign_OS_DIM_Portable", onefile=True),
            step="3/3 Format Portable (onefile — 1 seul .exe)",
        )

    print("\n" + "=" * 70)
    print("  BUILD TERMINE")
    print("=" * 70)
    if args.only in ("dir", "both"):
        print(r"  Dossier   : dist\Sovereign_OS_DIM\Sovereign_OS_DIM.exe")
    if args.only in ("portable", "both"):
        print(r"  Portable  : dist\Sovereign_OS_DIM_Portable.exe")


if __name__ == "__main__":
    main()
