# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM · Générateur du guide développeur PDF (fpdf2)
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#  Project : Sovereign OS V36.0 · Station DIM GHT Sud Paris
#
#  Description ·
#    Produit `Sovereign_OS_DIM_Guide_Dev.pdf` à la racine du dépôt.
#    Ce guide est destiné aux développeurs et aux équipes DSI.
#    Il documente l'architecture, le bridge HTTP, le module ML,
#    la sécurité, la CI/CD et les conventions de contribution.
#
#  Usage ·
#    python tools/generate_guide_dev.py [--output chemin.pdf]
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations

import argparse
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGO_PATH = os.path.join(ROOT, "frontend", "logo_gh.png")
FONT_DIR = os.path.join(HERE, "fonts")

SANS = "DevSans"
MONO = "DevMono"

_SANS_CANDIDATES = (
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"),
    ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/segoeuib.ttf",
     "C:/Windows/Fonts/segoeuii.ttf", "C:/Windows/Fonts/segoeuiz.ttf"),
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf",
     "C:/Windows/Fonts/ariali.ttf", "C:/Windows/Fonts/arialbi.ttf"),
    (os.path.join(FONT_DIR, "DejaVuSans.ttf"),
     os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"),
     os.path.join(FONT_DIR, "DejaVuSans-Oblique.ttf"),
     os.path.join(FONT_DIR, "DejaVuSans-BoldOblique.ttf")),
)

_MONO_CANDIDATES = (
    ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Oblique.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-BoldOblique.ttf"),
    ("C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/consolab.ttf",
     "C:/Windows/Fonts/consolai.ttf", "C:/Windows/Fonts/consolaz.ttf"),
    ("C:/Windows/Fonts/cour.ttf", "C:/Windows/Fonts/courbd.ttf",
     "C:/Windows/Fonts/couri.ttf", "C:/Windows/Fonts/courbi.ttf"),
    (os.path.join(FONT_DIR, "DejaVuSansMono.ttf"),
     os.path.join(FONT_DIR, "DejaVuSansMono-Bold.ttf"),
     os.path.join(FONT_DIR, "DejaVuSansMono-Oblique.ttf"),
     os.path.join(FONT_DIR, "DejaVuSansMono-BoldOblique.ttf")),
)

# Palette (partagée avec generate_guide.py)
GH_NAVY  = (0, 0, 145)
GH_TEAL  = (0, 137, 123)
GH_GOLD  = (212, 164, 55)
GH_ERR   = (225, 29, 72)
GH_OK    = (16, 185, 129)
GH_WARN  = (245, 158, 11)
SLATE_900 = (15, 23, 42)
SLATE_700 = (51, 65, 85)
SLATE_500 = (100, 116, 139)
SLATE_400 = (148, 163, 184)
SLATE_200 = (226, 232, 240)
SLATE_100 = (241, 245, 249)
SLATE_50  = (248, 250, 252)
WHITE     = (255, 255, 255)

TYPE = {
    "display": 26,
    "h1": 18,
    "h2": 14,
    "h3": 11,
    "body": 10,
    "small": 8.5,
    "caption": 7,
}

SPACE = {"xs": 1.5, "sm": 3, "md": 5, "lg": 8, "xl": 12}


def _pick_font_set(candidates):
    for tup in candidates:
        if all(os.path.exists(p) for p in tup):
            return tup
    return None


def _register_fonts(pdf):
    sans = _pick_font_set(_SANS_CANDIDATES)
    mono = _pick_font_set(_MONO_CANDIDATES)
    if sans:
        pdf.add_font(SANS, "",   sans[0])
        pdf.add_font(SANS, "B",  sans[1])
        pdf.add_font(SANS, "I",  sans[2])
        pdf.add_font(SANS, "BI", sans[3])
    else:
        globals()["SANS"] = "Helvetica"
    if mono:
        pdf.add_font(MONO, "",   mono[0])
        pdf.add_font(MONO, "B",  mono[1])
        pdf.add_font(MONO, "I",  mono[2])
        pdf.add_font(MONO, "BI", mono[3])
    else:
        globals()["MONO"] = "Courier"
    return bool(sans and mono)


# ──────────────────────────────────────────────────────────────────────────────
# PRIMITIVES DE RENDU
# ──────────────────────────────────────────────────────────────────────────────

def _page_header(pdf, title, category):
    if os.path.exists(LOGO_PATH):
        try:
            pdf.image(LOGO_PATH, x=10, y=8, h=12)
        except Exception:
            pass
    pdf.set_xy(28, 10)
    pdf.set_font(SANS, "B", TYPE["body"])
    pdf.set_text_color(*GH_NAVY)
    pdf.cell(120, 5, title[:60], new_x="RIGHT", new_y="TOP")
    pdf.set_xy(28, 15)
    pdf.set_font(SANS, "", TYPE["caption"])
    pdf.set_text_color(*SLATE_500)
    pdf.cell(120, 4, f"Guide Développeur · {category}", new_x="RIGHT", new_y="TOP")
    pdf.set_draw_color(*SLATE_200)
    pdf.line(10, 22, 200, 22)
    pdf.set_y(28)


def _section_title(pdf, title):
    pdf.set_font(SANS, "B", TYPE["h2"])
    pdf.set_text_color(*GH_NAVY)
    pdf.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*GH_TEAL)
    pdf.set_line_width(0.6)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 25, pdf.get_y())
    pdf.ln(SPACE["md"])


def _subheading(pdf, text):
    pdf.ln(SPACE["xs"])
    x0, y0 = pdf.get_x(), pdf.get_y()
    pdf.set_fill_color(*GH_TEAL)
    pdf.rect(x0, y0 + 1, 1.4, 5.5, "F")
    pdf.set_xy(x0 + 3.5, y0)
    pdf.set_font(SANS, "B", TYPE["h3"])
    pdf.set_text_color(*GH_NAVY)
    pdf.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(0.5)


def _body_text(pdf, text):
    pdf.set_font(SANS, "", TYPE["body"])
    pdf.set_text_color(*SLATE_700)
    pdf.multi_cell(0, 5.6, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(SPACE["xs"])


def _code_block(pdf, lines):
    pdf.set_fill_color(*SLATE_100)
    pdf.set_text_color(*SLATE_900)
    pdf.set_font(MONO, "", 9)
    for line in lines:
        pdf.cell(0, 5.5, " " + line, new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(3)


def _alert(pdf, kind, text):
    palette = {
        "info":   ((239, 246, 255), (29, 78, 216)),
        "ok":     ((240, 253, 244), (21, 128, 61)),
        "warn":   ((255, 251, 235), (180, 83, 9)),
        "err":    ((254, 242, 242), (185, 28, 28)),
        "metier": ((255, 251, 235), (146, 100, 8)),
    }
    bg, fg = palette.get(kind, palette["info"])
    pdf.set_fill_color(*bg)
    pdf.set_text_color(*fg)
    pdf.set_font(SANS, "", TYPE["body"])
    pdf.multi_cell(0, 5.5, "  " + text, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(SPACE["xs"])


def _table_row(pdf, cols, widths, bold=False, header=False):
    if header:
        pdf.set_fill_color(*GH_NAVY)
        pdf.set_text_color(*WHITE)
        pdf.set_font(SANS, "B", TYPE["small"])
    else:
        pdf.set_fill_color(*SLATE_50)
        pdf.set_text_color(*SLATE_700)
        pdf.set_font(MONO if not bold else SANS, "B" if bold else "", TYPE["small"])
    x0 = pdf.get_x()
    y0 = pdf.get_y()
    total_w = sum(widths)
    pdf.rect(x0, y0, total_w, 6, "F")
    pdf.set_draw_color(*SLATE_200)
    pdf.rect(x0, y0, total_w, 6)
    cx = x0
    for col, w in zip(cols, widths):
        pdf.set_xy(cx + 1.5, y0 + 1)
        pdf.cell(w - 3, 4, str(col)[:30])
        cx += w
    pdf.set_xy(x0, y0 + 6)


# ──────────────────────────────────────────────────────────────────────────────
# CONTENU DU GUIDE DEV · sections
# ──────────────────────────────────────────────────────────────────────────────

SECTIONS = [
    # ══════ 1 · ARCHITECTURE GÉNÉRALE ══════
    {
        "title": "Architecture générale",
        "category": "Architecture",
        "content": lambda pdf: _render_architecture(pdf),
    },
    # ══════ 2 · STACK TECHNIQUE ══════
    {
        "title": "Stack technique et dépendances",
        "category": "Stack",
        "content": lambda pdf: _render_stack(pdf),
    },
    # ══════ 3 · BRIDGE HTTP & PHP ══════
    {
        "title": "Bridge HTTP et intégration PHP",
        "category": "API",
        "content": lambda pdf: _render_bridge(pdf),
    },
    # ══════ 4 · MODULE ML ══════
    {
        "title": "Module ML · configuration et entraînement",
        "category": "ML",
        "content": lambda pdf: _render_ml(pdf),
    },
    # ══════ 5 · SÉCURITÉ ══════
    {
        "title": "Sécurité et conformité RGPD",
        "category": "Sécurité",
        "content": lambda pdf: _render_security(pdf),
    },
    # ══════ 6 · CI/CD ══════
    {
        "title": "CI/CD · pipeline et qualité de code",
        "category": "CI/CD",
        "content": lambda pdf: _render_cicd(pdf),
    },
    # ══════ 7 · PERFORMANCES ══════
    {
        "title": "Performances et benchmarks",
        "category": "Perfs",
        "content": lambda pdf: _render_perfs(pdf),
    },
    # ══════ 8 · CONTRIBUER ══════
    {
        "title": "Contribuer au projet",
        "category": "Contribution",
        "content": lambda pdf: _render_contrib(pdf),
    },
]


def _render_architecture(pdf):
    _subheading(pdf, "Vue d'ensemble")
    _body_text(pdf,
               "Sovereign OS DIM est un monolithe desktop PyInstaller. "
               "Le runtime desktop C# (.NET 8 + WebView2) héberge une fenêtre "
               "native Windows dans laquelle tourne un frontend HTML/CSS/JS. "
               "Le backend Python est lancé en sous-processus et exposé via "
               "un bridge HTTP local (127.0.0.1 uniquement).")

    _subheading(pdf, "Couches")
    rows = [
        ("Couche", "Technologie", "Rôle"),
        ("Desktop shell", "C# .NET 8 + WebView2", "Fenêtre native, IPC, packaging"),
        ("Frontend",      "HTML + Tailwind + Chart.js", "UI rendue dans WebView2"),
        ("Backend API",   "Python 3.12 + FastAPI/aiohttp", "Traitement PMSI, bridge HTTP"),
        ("Données",       "SQLite (Microsoft.Data.Sqlite)", "MPI persisté, résolutions IDV"),
        ("ML",            "XGBoost, LightGBM, scikit-learn", "Assistance TIM (3 modèles)"),
        ("PDF",           "fpdf2 >= 2.8 (LGPL)", "Génération guides + exports"),
    ]
    for i, row in enumerate(rows):
        _table_row(pdf, row, [45, 65, 70], header=(i == 0))
    pdf.ln(4)

    _subheading(pdf, "Flux de données")
    _body_text(pdf,
               "1. L'utilisateur interagit avec le frontend (WebView2).\n"
               "2. Les requêtes passent par le bridge HTTP (127.0.0.1:8765) "
               "avec un token Bearer (env var SOVEREIGN_BRIDGE_TOKEN).\n"
               "3. Le backend Python traite les fichiers ATIH en parallèle "
               "(ThreadPoolExecutor, max 8 workers) et écrit en SQLite.\n"
               "4. Les résultats sont renvoyés en JSON au frontend.")

    _alert(pdf, "warn",
           "Le bridge HTTP ne doit jamais écouter sur 0.0.0.0 · "
           "127.0.0.1 uniquement. Toute modification expose les données patient.")


def _render_stack(pdf):
    _subheading(pdf, "Backend Python")
    rows = [
        ("Package", "Version", "Usage"),
        ("Python",          "3.12",     "Runtime principal"),
        ("fpdf2",           ">= 2.8",   "Génération PDF (LGPL)"),
        ("xgboost",         ">= 2.0",   "format_detector + collision_risk"),
        ("lightgbm",        ">= 4.0",   "Benchmark ML (challenger)"),
        ("scikit-learn",    ">= 1.4",   "ddn_validity (RandomForest) + pipeline"),
        ("pandas",          ">= 2.0",   "Chargement dataset synthétique"),
        ("pypdf",           ">= 4.0",   "Enrichissement bookmarks PDF"),
        ("PyInstaller",     ">= 6.0",   "Packaging .exe portable"),
    ]
    for i, row in enumerate(rows):
        _table_row(pdf, row, [50, 30, 100], header=(i == 0))
    pdf.ln(4)

    _subheading(pdf, "Frontend")
    _body_text(pdf,
               "HTML/CSS vanille + Tailwind CSS (CDN embarqué). Chart.js "
               "pour les graphiques. Aucun framework JS (React/Vue) · "
               "volontairement léger pour rester embarquable dans WebView2 "
               "sans build step. ES modules natifs (import/export).")

    _subheading(pdf, "C# Desktop Shell")
    _body_text(pdf,
               "Microsoft.Web.WebView2 pour l'affichage HTML. "
               "Microsoft.Data.Sqlite pour l'accès direct au MPI depuis C#. "
               "WinForms comme conteneur de fenêtre. Le shell C# lance le "
               "backend Python via Process.Start() et détecte son port via "
               "stdout.")

    _subheading(pdf, "Installation de l'environnement de développement")
    _code_block(pdf, [
        "# Python (backend + ML + PDF)",
        "pip install -r requirements.txt",
        "",
        "# Tests",
        "pytest tests/ -v",
        "",
        "# Lint + sécurité",
        "ruff check .",
        "bandit -r backend/",
        "mypy backend/",
        "",
        "# Build .exe",
        "python build.py",
    ])


def _render_bridge(pdf):
    _subheading(pdf, "Démarrage du bridge")
    _body_text(pdf,
               "Le bridge HTTP est un serveur FastAPI/aiohttp écoutant "
               "exclusivement sur 127.0.0.1. Il est protégé par un token "
               "Bearer passé en variable d'environnement. Le port par "
               "défaut est 8765.")
    _code_block(pdf, [
        "# Démarrage minimal",
        "SOVEREIGN_BRIDGE_TOKEN=secret python bridge.py --port 8765",
        "",
        "# Côté PHP (client)",
        "export SOVEREIGN_BRIDGE_URL=http://127.0.0.1:8765",
        "export SOVEREIGN_BRIDGE_TOKEN=secret",
        "php -S 127.0.0.1:8080 -t php",
    ])

    _subheading(pdf, "Endpoints disponibles")
    rows = [
        ("Méthode", "Route", "Auth", "Description"),
        ("GET",  "/health",          "Non",  "Ping · retourne {status: ok}"),
        ("GET",  "/mpi/stats",       "Oui",  "KPI Dashboard (fichiers, IPP, collisions)"),
        ("POST", "/mpi/process",     "Oui",  "Lance traitement d'un dossier ATIH"),
        ("GET",  "/mpi/collisions",  "Oui",  "Liste des collisions IDV"),
        ("POST", "/mpi/resolve",     "Oui",  "Résout une collision (IPP + DDN pivot)"),
        ("GET",  "/export/csv",      "Oui",  "Export MPI CSV normalisé"),
        ("GET",  "/export/txt/{id}", "Oui",  "Export .txt sanitized d'un fichier ATIH"),
    ]
    for i, row in enumerate(rows):
        _table_row(pdf, row, [20, 52, 18, 90], header=(i == 0))
    pdf.ln(4)

    _subheading(pdf, "Authentification")
    _body_text(pdf,
               "Toutes les routes sauf /health nécessitent un header "
               "Authorization: Bearer <TOKEN>. Le token est comparé à "
               "SOVEREIGN_BRIDGE_TOKEN via hmac.compare_digest() pour "
               "éviter les timing attacks. Retourne HTTP 401 si absent "
               "ou invalide.")

    _subheading(pdf, "CORS")
    _body_text(pdf,
               "Origine autorisée · null (WebView2) et http://127.0.0.1 "
               "uniquement. Toute autre origine est bloquée par les "
               "headers CORS restrictifs. Méthodes autorisées · "
               "GET, POST, OPTIONS.")

    _subheading(pdf, "Exemple PHP")
    _code_block(pdf, [
        "<?php",
        "$url   = getenv('SOVEREIGN_BRIDGE_URL');",
        "$token = getenv('SOVEREIGN_BRIDGE_TOKEN');",
        "$ch    = curl_init(\"$url/mpi/stats\");",
        "curl_setopt($ch, CURLOPT_HTTPHEADER, [",
        "    \"Authorization: Bearer $token\",",
        "    \"Accept: application/json\",",
        "]);",
        "curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);",
        "$resp = json_decode(curl_exec($ch), true);",
        "echo $resp['ipp_unique'];  // ex. 4821",
    ])


def _render_ml(pdf):
    _subheading(pdf, "Modèles embarqués")
    rows = [
        ("Modèle", "Algorithme", "Tâche", "Métrique clé"),
        ("format_detector.json", "XGBoost tuned", "Classification format ATIH (58 classes)", "accuracy 0,77 · F1 0,70"),
        ("collision_risk.json",  "XGBoost tuned", "Scoring risque collision IDV",            "AUC 1,00 · F1 1,00"),
        ("ddn_validity.pkl",     "RandomForest",  "Détection DDN suspecte",                  "AUC 0,86 · acc 0,99"),
    ]
    for i, row in enumerate(rows):
        _table_row(pdf, row, [50, 32, 65, 50], header=(i == 0))
    pdf.ln(4)

    _subheading(pdf, "Entraînement")
    _body_text(pdf,
               "Les modèles sont entraînés sur un dataset 100 % synthétique "
               "fidèle aux spécifications ATIH 2000-2026 (58 variantes). "
               "Aucun fichier patient réel n'est utilisé (RGPD art. 9).")
    _code_block(pdf, [
        "# Entraînement standard (50k samples)",
        "python -m backend.ml.train",
        "",
        "# Entraînement plus robuste (200k samples)",
        "python -m backend.ml.train --samples 200000 --seed 42",
        "",
        "# Réutiliser un parquet existant (gain ~10s)",
        "python -m backend.ml.train --data-cache data/cache.parquet",
        "",
        "# Résultat : backend/ml/models/*.json + *.pkl",
        "#            + training_metadata.json (leaderboard + hashes SHA-256)",
    ])

    _subheading(pdf, "Pipeline de benchmark")
    _body_text(pdf,
               "Pour chaque tâche, 4 algorithmes sont évalués en "
               "cross-validation stratifiée (5-fold) · XGBoost default, "
               "XGBoost tuned (Optuna, 30 trials), LightGBM, RandomForest. "
               "Le winner est sélectionné par AUC (binaire) ou F1 macro "
               "(multiclasse) et sérialisé. Le leaderboard complet est "
               "disponible dans training_metadata.json.")

    _subheading(pdf, "Ajouter un nouveau format ATIH")
    _code_block(pdf, [
        "# 1. Editer le catalogue des specs",
        "# backend/ml/synthetic.py :: ATIH_SPECS",
        "",
        "ATIH_SPECS.append({",
        "    'format': 'RPS',",
        "    'version': 'P15',",
        "    'year_from': 2027,",
        "    'line_length': 166,",
        "    'ipp_start': 20,",
        "    'ipp_len': 20,",
        "    'ddn_start': 40,",
        "})",
        "",
        "# 2. Relancer l'entraînement",
        "python -m backend.ml.train --samples 200000",
    ])

    _subheading(pdf, "Audit des modèles")
    _body_text(pdf,
               "training_metadata.json contient pour chaque modèle · "
               "date d'entraînement, nombre de samples, seed, leaderboard "
               "complet des 4 candidats avec métriques test, hash SHA-256 "
               "du fichier modèle sérialisé. Ce fichier est versionné en "
               "Git pour tracabilité réglementaire.")


def _render_security(pdf):
    _subheading(pdf, "Périmètre réseau")
    _body_text(pdf,
               "Le bridge HTTP écoute exclusivement sur 127.0.0.1. "
               "Toute tentative de bind sur 0.0.0.0 est bloquée par "
               "validation explicite au démarrage. Aucun port n'est "
               "ouvert vers l'extérieur du poste.")

    _subheading(pdf, "Authentification bridge")
    _body_text(pdf,
               "Token Bearer via SOVEREIGN_BRIDGE_TOKEN (variable "
               "d'environnement uniquement, jamais hardcodé). "
               "Comparaison via hmac.compare_digest() (constant time). "
               "HTTP 401 retourné sans détail sur l'erreur.")

    _subheading(pdf, "Validation des chemins")
    _body_text(pdf,
               "os.path.abspath() + vérification que le chemin résolu "
               "reste sous le dossier autorisé (path traversal guard). "
               "Côté C# · SafePath.validate() applique la même règle. "
               "Les liens symboliques pointant hors du dossier cible "
               "sont rejetés.")

    _subheading(pdf, "Données patient (RGPD art. 9)")
    _body_text(pdf,
               "Les IPP et DDN sont traités uniquement en mémoire RAM "
               "pendant le traitement de lot. Après traitement, seule "
               "la base SQLite locale contient les données (chiffrée "
               "au repos via SQLCipher, clé dérivée du token). "
               "Aucune télémétrie, aucun envoi réseau, 100 % local.")

    _subheading(pdf, "Audit log art. 30 RGPD")
    _body_text(pdf,
               "Toute résolution IDV (qui, quand, IPP, DDN retenue, "
               "DDN rejetées) est journalisée dans audit.log (append-only). "
               "Le log est lisible par le DPO et l'ARS sur demande. "
               "Rétention 5 ans minimum (instruction DGOS/PF2/2020/143).")

    _subheading(pdf, "Anonymisation exports recherche")
    _body_text(pdf,
               "Option k-anonymity k >= 5 disponible pour les exports "
               "destinés à la recherche (SNDS, Health Data Hub). "
               "Hash SHA-256 tronqué (12 chars) appliqué aux IPP dans "
               "les exports pseudonymisés. Conforme MR-007.")

    _subheading(pdf, "Secrets et CI")
    _code_block(pdf, [
        "# Variables d'environnement requises (jamais committées)",
        "SOVEREIGN_BRIDGE_TOKEN=<token>    # bridge auth",
        "SQLCIPHER_KEY=<clé>               # chiffrement SQLite",
        "",
        "# CI scan sécurité (GitHub Actions)",
        "bandit -r backend/ -ll            # vulnérabilités Python",
        "ruff check .                      # linting",
        "mypy backend/                     # typage statique",
    ])


def _render_cicd(pdf):
    _subheading(pdf, "Pipeline GitHub Actions")
    _body_text(pdf,
               "Déclenchement · push sur main ou PR vers main. "
               "Environnement · ubuntu-latest, Python 3.12.")
    rows = [
        ("Étape", "Commande", "Bloquant"),
        ("Lint",     "ruff check .",             "Oui"),
        ("Typage",   "mypy backend/",            "Oui"),
        ("Sécurité", "bandit -r backend/ -ll",   "Oui"),
        ("Tests",    "pytest tests/ -v --tb=short", "Oui"),
        ("Build",    "python build.py --check",  "Non (avertissement)"),
    ]
    for i, row in enumerate(rows):
        _table_row(pdf, row, [30, 90, 30], header=(i == 0))
    pdf.ln(4)

    _subheading(pdf, "Conventions de commit")
    _body_text(pdf,
               "Format · <type>(<scope>): <description>\n"
               "Types · feat, fix, docs, refactor, test, chore.\n"
               "Scope · backend, frontend, ml, bridge, guide, ci.\n"
               "Langue · anglais impératif, minuscules.\n"
               "Tirets longs (—) interdits dans les messages de commit.\n"
               "Exemples valides ·\n"
               "  feat(ml): add RPS P15 format to ATIH_SPECS\n"
               "  fix(bridge): prevent path traversal in /export/txt")

    _subheading(pdf, "Pull Requests")
    _body_text(pdf,
               "Branche de base · main. Branche de travail · "
               "<type>/<description-courte>. "
               "Tests pytest verts obligatoires avant merge. "
               "Review par au moins 1 membre du projet. "
               "Squash merge · un seul commit par PR dans main.")

    _subheading(pdf, "Release")
    _body_text(pdf,
               "Cycle trimestriel · V36 juillet 2026, V37 octobre 2026. "
               "Tag Git : vXX.Y.Z (semver). GitHub Release auto-générée "
               "avec changelog depuis les commits. Binaire PyInstaller "
               "attaché à la release (Sovereign_OS_DIM.exe).")

    _subheading(pdf, "Régénérer les guides PDF")
    _code_block(pdf, [
        "# Guide métier (TIM, médecin DIM, chef de pôle)",
        "python tools/generate_guide.py",
        "",
        "# Guide développeur (DSI, contributeurs)",
        "python tools/generate_guide_dev.py",
        "",
        "# Mode d'emploi court (utilisateurs finaux)",
        "python tools/generate_manual.py",
    ])


def _render_perfs(pdf):
    _subheading(pdf, "Conditions de mesure")
    _body_text(pdf,
               "Poste de référence · Intel Core i5 8e gen, 16 Go RAM, "
               "SSD NVMe. Système : Windows 11 Pro. "
               "Python 3.12, xgboost 2.0, sqlite 3.45.")

    _subheading(pdf, "Backend · traitement PMSI")
    rows = [
        ("Opération", "Mesure", "Notes"),
        ("Scan 1 000 fichiers (12 dossiers)",  "1,2 s",    "Heuristique regex"),
        ("Identification 1 fichier",            "180 µs",   "Regex + longueur ligne"),
        ("Traitement lot 10 fichiers / 150k L", "5 s",      "8 workers en pic"),
        ("Ecriture MPI SQLite 150k lignes",     "3 s",      "Bottleneck principal"),
        ("Chargement MPI 500k lignes",          "< 400 ms", "Index sur ipp"),
    ]
    for i, row in enumerate(rows):
        _table_row(pdf, row, [90, 25, 65], header=(i == 0))
    pdf.ln(4)

    _subheading(pdf, "Module ML")
    rows = [
        ("Opération", "Mesure", "Notes"),
        ("Chargement 3 modèles au démarrage",   "180 ms",   "XGBoost JSON + RandomForest pkl"),
        ("format_detector (1 ligne)",            "< 1 ms",   "Inférence XGBoost"),
        ("collision_risk (1 IPP)",               "< 1 ms",   "Inférence XGBoost"),
        ("ddn_validity (1 ligne)",               "< 1 ms",   "Inférence RandomForest"),
        ("Batch 10 000 lignes (tous modèles)",   "~150 ms",  "Sans parallélisme"),
    ]
    for i, row in enumerate(rows):
        _table_row(pdf, row, [90, 25, 65], header=(i == 0))
    pdf.ln(4)

    _subheading(pdf, "Frontend (WebView2)")
    rows = [
        ("Opération", "Mesure", "Notes"),
        ("Chargement initial dashboard",  "< 400 ms", "MPI 50k IPP"),
        ("Rafraîchissement post-traitement", "< 200 ms", "Recalcul agrégats en mémoire"),
        ("Rendu donut Chart.js",          "< 80 ms",  "Canvas HTML5"),
        ("Export PDF organigramme 3p",    "1,2 s",    "fpdf2 vectoriel"),
    ]
    for i, row in enumerate(rows):
        _table_row(pdf, row, [90, 25, 65], header=(i == 0))
    pdf.ln(4)

    _alert(pdf, "warn",
           "Goulot principal · écriture SQLite pour les très gros lots "
           "(> 1 M lignes). Solution : traiter par trimestres successifs "
           "ou passer à WAL mode (journal_mode=WAL).")


def _render_contrib(pdf):
    _subheading(pdf, "Dépôt")
    _body_text(pdf,
               "https://github.com/Adam-Blf/sovereign_os_dim\n"
               "Licence · MIT (code) + LGPL (fpdf2).\n"
               "Issues GitHub pour bugs et suggestions.\n"
               "Contact direct · adam.beloucif@psysudparis.fr")

    _subheading(pdf, "Structure du dépôt")
    rows = [
        ("Dossier / Fichier", "Contenu"),
        ("backend/",          "Python : traitement PMSI, bridge HTTP, ML"),
        ("backend/ml/",       "Module ML : train.py, synthetic.py, modèles"),
        ("frontend/",         "HTML + Tailwind + Chart.js (toutes les vues)"),
        ("php/",              "Client PHP du bridge HTTP"),
        ("tools/",            "Générateurs PDF (guide, guide dev, manuel)"),
        ("tests/",            "Tests pytest"),
        ("docs/",             "Screenshots, PDFs générés"),
        ("bridge.py",         "Entrée du bridge HTTP (main Python)"),
        ("main.py",           "Entrée de l'application desktop"),
        ("build.py",          "Script PyInstaller (packaging .exe)"),
    ]
    for i, row in enumerate(rows):
        _table_row(pdf, row, [60, 120], header=(i == 0))
    pdf.ln(4)

    _subheading(pdf, "Ajouter un format ATIH")
    _body_text(pdf,
               "1. Editer backend/ml/synthetic.py · ajouter l'entrée dans "
               "ATIH_SPECS (format, version, year_from, line_length, "
               "positions IPP/DDN).\n"
               "2. Relancer l'entraînement ML "
               "(python -m backend.ml.train --samples 200000).\n"
               "3. Mettre à jour le détecteur heuristique dans "
               "backend/data_processor.py (regex + longueur).\n"
               "4. Ajouter un test dans tests/ pour le nouveau format.\n"
               "5. Documenter dans docs/research/pmsi_formats_history.md.")

    _subheading(pdf, "Tests")
    _code_block(pdf, [
        "# Lancer tous les tests",
        "pytest tests/ -v",
        "",
        "# Tests d'un module spécifique",
        "pytest tests/test_bridge_security.py -v",
        "",
        "# Avec couverture",
        "pytest tests/ --cov=backend --cov-report=html",
    ])

    _alert(pdf, "ok",
           "Merci de contribuer ! Les contributions améliorant la "
           "couverture des formats ATIH ou la robustesse du ML "
           "sont particulièrement bienvenues.")


# ──────────────────────────────────────────────────────────────────────────────
# BUILD PDF
# ──────────────────────────────────────────────────────────────────────────────

def build_pdf(output_path: str) -> str:
    try:
        from fpdf import FPDF
    except ImportError as e:
        print("fpdf2 non installe · pip install fpdf2>=2.8", file=sys.stderr)
        raise SystemExit(1) from e

    class DevGuide(FPDF):
        def footer(self):
            self.set_y(-15)
            self.set_font(SANS, "I", 8)
            self.set_text_color(*SLATE_400)
            self.cell(
                0, 8,
                f"Sovereign OS DIM · Guide Développeur · "
                f"Page {self.page_no()} / {{nb}} · Adam Beloucif · GHT Sud Paris",
                align="C",
            )

    pdf = DevGuide()
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.alias_nb_pages()
    _register_fonts(pdf)

    # ══════ PAGE DE GARDE ══════
    pdf.add_page()
    if os.path.exists(LOGO_PATH):
        try:
            pdf.image(LOGO_PATH, x=80, y=30, h=50)
        except Exception:
            pass
    pdf.set_y(95)
    pdf.set_font(SANS, "B", TYPE["display"])
    pdf.set_text_color(*GH_NAVY)
    pdf.cell(0, 14, "SOVEREIGN OS DIM", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font(SANS, "", TYPE["h1"])
    pdf.set_text_color(*SLATE_700)
    pdf.cell(0, 10, "Guide Développeur",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(SPACE["lg"])
    pdf.set_draw_color(*GH_TEAL)
    pdf.set_line_width(1.0)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(SPACE["lg"])
    pdf.set_font(SANS, "", TYPE["h3"])
    pdf.set_text_color(*SLATE_500)
    pdf.cell(0, 7, f"Version 36.0  ·  {len(SECTIONS)} sections  ·  référence technique",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 7, "GHT Psy Sud Paris  ·  Fondation Vallée + Paul Guiraud",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(20)
    pdf.set_font(SANS, "I", TYPE["body"])
    pdf.set_text_color(*SLATE_400)
    pdf.cell(0, 5, f"Généré le {date.today().strftime('%d / %m / %Y')}",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 5, "Adam Beloucif  ·  adam.beloucif@psysudparis.fr",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(12)
    pdf.set_font(SANS, "", TYPE["small"])
    pdf.set_text_color(*SLATE_500)
    pdf.multi_cell(
        0, 5,
        "Ce guide est destiné aux développeurs, aux équipes DSI et aux "
        "contributeurs du projet. Il documente l'architecture, la stack, "
        "le bridge HTTP, le module ML, la sécurité et la CI/CD. "
        "Pour le guide d'utilisation quotidienne (TIM, médecin DIM, "
        "chef de pôle), voir Sovereign_OS_DIM_Guide.pdf.",
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(SPACE["md"])
    pdf.set_fill_color(*GH_NAVY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(SANS, "B", TYPE["small"])
    pdf.cell(0, 7,
             "  Dépôt · https://github.com/Adam-Blf/sovereign_os_dim  ·  "
             "Stack · Python 3.12 + C# .NET 8 + WebView2 + XGBoost",
             new_x="LMARGIN", new_y="NEXT", fill=True, align="C")

    # ══════ SOMMAIRE ══════
    pdf.add_page()
    pdf.set_font(SANS, "B", 22)
    pdf.set_text_color(*GH_NAVY)
    pdf.cell(0, 12, "Sommaire", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*GH_TEAL)
    pdf.set_line_width(0.6)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 30, pdf.get_y())
    pdf.ln(8)
    for i, sec in enumerate(SECTIONS, start=1):
        pdf.set_font(SANS, "B", 10)
        pdf.set_text_color(*GH_TEAL)
        pdf.cell(14, 7, f"{i:>2}.", new_x="RIGHT", new_y="TOP")
        pdf.set_font(SANS, "B", 11)
        pdf.set_text_color(*GH_NAVY)
        pdf.cell(0, 7, sec["title"], new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    # ══════ SECTIONS ══════
    for sec in SECTIONS:
        pdf.add_page()
        _page_header(pdf, sec["title"], sec["category"])
        _section_title(pdf, sec["title"])
        sec["content"](pdf)

    # ══════ PAGE FINALE ══════
    pdf.add_page()
    _page_header(pdf, "Fin du guide", "Références")
    _section_title(pdf, "Références et ressources")
    _subheading(pdf, "Documentation officielle ATIH")
    _body_text(pdf,
               "Notice technique 2026 · "
               "https://www.atih.sante.fr/notice-technique-nouveautes-pmsi-mco-had-smr-psychiatrie-2026-0\n"
               "Formats PMSI 2026 (Excel) · "
               "https://www.atih.sante.fr/formats-pmsi-2026-0\n"
               "Catalogue formats historiques · format-pmsi.fr\n"
               "Plateforme DRUIDES · https://www.epmsi.atih.sante.fr")

    _subheading(pdf, "RGPD et conformité")
    _body_text(pdf,
               "RGPD UE 2016/679 · art. 9 (données de santé), art. 30 "
               "(registre de traitement).\n"
               "HAS · Instruction DGOS/PF2 no 2019-116 (identitovigilance).\n"
               "ANS · Référentiel national d'identito-vigilance 2023.\n"
               "Health Data Hub · MR-007 (pseudonymisation SNDS).\n"
               "Instruction DGOS/PF2/2020/143 · rétention 5 ans.")

    _subheading(pdf, "Dépôt et support")
    _body_text(pdf,
               "GitHub · https://github.com/Adam-Blf/sovereign_os_dim\n"
               "Issues · https://github.com/Adam-Blf/sovereign_os_dim/issues\n"
               "Contact · adam.beloucif@psysudparis.fr\n"
               "Alternance EFREI M1 Data Engineering · Fondation Vallée 2025-2027.")

    _alert(pdf, "info",
           "Ce guide développeur est généré automatiquement depuis "
           "tools/generate_guide_dev.py · mettre à jour le contenu "
           "dans ce fichier pour l'enrichir.")

    abs_out = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_out) or ".", exist_ok=True)
    pdf.output(abs_out)
    return abs_out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Génère le guide développeur PDF de Sovereign OS DIM."
    )
    default_output = os.path.join(ROOT, "Sovereign_OS_DIM_Guide_Dev.pdf")
    parser.add_argument(
        "--output",
        default=default_output,
        help="Chemin du PDF de sortie (défaut : racine du dépôt).",
    )
    args = parser.parse_args()
    path = build_pdf(args.output)
    size_kb = os.path.getsize(path) // 1024
    print(f"[OK] Guide développeur généré : {path}  ({size_kb} Ko)")


if __name__ == "__main__":
    main()
