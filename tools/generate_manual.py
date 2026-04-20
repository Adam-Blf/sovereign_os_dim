# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM — Générateur de mode d'emploi PDF (fpdf2)
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#  Project : Sovereign OS V32.0 — Station DIM GHT Sud Paris
#
#  Description:
#    Script utilitaire qui produit `docs/Sovereign_OS_DIM_Manuel.pdf`, le
#    mode d'emploi officiel du bridge PHP et de la visualisation Excel.
#    Utilise fpdf2 (fork moderne de PyFPDF — licence LGPL), installable via
#    `pip install fpdf2>=2.8`.
#
#  Usage:
#    python tools/generate_manual.py [--output chemin/manuel.pdf]
#
#  Pourquoi un générateur plutôt qu'un PDF commité ?
#    - Le PDF se régénère à chaque évolution du bridge (endpoints, options)
#    - Pas de binaire obèse à maintenir dans l'historique git
#    - Le contenu reste la source de vérité dans ce fichier
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations

import argparse
import os
import sys
from datetime import date


# ──────────────────────────────────────────────────────────────────────────────
# CONTENU DU MANUEL — Structuré en sections { titre: [paragraphes|listes] }
# ──────────────────────────────────────────────────────────────────────────────
# Chaque section est un tuple (titre, blocs). Un bloc peut être :
#   ("p",  "texte de paragraphe")
#   ("h",  "sous-titre")
#   ("li", ["item1", "item2", ...])
#   ("code", "bloc de code à rendre en mono")
#
# Astuce : garder le contenu ici plutôt que dans un Markdown permet d'avoir un
# rendu 100% cohérent avec la charte (dark headers, bullets, colonnes).
# ══════════════════════════════════════════════════════════════════════════════

SECTIONS = [
    (
        "Presentation",
        [
            (
                "p",
                "Sovereign OS DIM est une application desktop dediee a la station "
                "DIM du GHT Sud Paris. Elle lit les fichiers ATIH (PMSI), construit "
                "un Master Patient Index (MPI) et exporte les donnees normalisees "
                "pour e-PMSI.",
            ),
            (
                "p",
                "La version V32.0 introduit un bridge HTTP REST qui expose le moteur "
                "ATIH a toute application tierce, en particulier une application "
                "PHP. Un mode de visualisation graphique a partir d'un ou plusieurs "
                "classeurs Excel est egalement fourni.",
            ),
        ],
    ),
    (
        "Architecture",
        [
            (
                "p",
                "Trois composants cooperent. Le desktop pywebview reste l'interface "
                "principale. Le bridge Flask (backend/bridge.py) expose les memes "
                "capacites en HTTP JSON. Le client PHP (php/SovereignClient.php) "
                "consomme le bridge via cURL et rend les pages HTML.",
            ),
            (
                "code",
                "Desktop  : python main.py\n"
                "Bridge   : python bridge.py\n"
                "PHP      : php -S 127.0.0.1:8080 -t php",
            ),
        ],
    ),
    (
        "Demarrage rapide",
        [
            ("h", "1. Installer les dependances Python"),
            ("code", "pip install -r requirements.txt"),
            ("h", "2. Lancer le bridge HTTP"),
            (
                "code",
                "SOVEREIGN_BRIDGE_TOKEN=secret python bridge.py --port 8765",
            ),
            (
                "p",
                "Le jeton est partage entre le bridge et l'application PHP. "
                "Sans jeton, l'authentification est desactivee (dev local).",
            ),
            ("h", "3. Configurer l'application PHP"),
            (
                "code",
                "export SOVEREIGN_BRIDGE_URL=http://127.0.0.1:8765\n"
                "export SOVEREIGN_BRIDGE_TOKEN=secret\n"
                "php -S 127.0.0.1:8080 -t php",
            ),
            (
                "p",
                "Ouvrez http://127.0.0.1:8080 pour acceder au tableau de bord.",
            ),
        ],
    ),
    (
        "Endpoints du bridge",
        [
            (
                "li",
                [
                    "GET  /health  : heartbeat (public, pas d'auth)",
                    "GET  /api/matrix  : liste des 23 formats ATIH",
                    "POST /api/identify  : identifie un fichier par son nom",
                    "POST /api/scan  : scanne un ou plusieurs dossiers",
                    "POST /api/process  : scan + extraction du MPI",
                    "GET  /api/collisions  : liste les collisions IPP/DDN",
                    "POST /api/resolve  : set_pivot manuel ou auto-resolution",
                    "GET  /api/stats  : dashboard agregate",
                    "POST /api/export  : export CSV Pilot",
                    "POST /api/export-sanitized  : export .txt purifie",
                    "POST /api/inspect  : analyse ligne par ligne",
                    "POST /api/import-csv  : lecture d'un CSV externe",
                    "POST /api/import-excel  : lecture d'un classeur Excel",
                    "POST /api/chart-from-excel  : agregation pour Chart.js",
                    "POST /api/reset  : remise a zero de l'etat",
                ],
            ),
        ],
    ),
    (
        "Utiliser le client PHP",
        [
            (
                "p",
                "Le client PHP encapsule cURL et la serialisation JSON. Exemple :",
            ),
            (
                "code",
                "require_once 'php/SovereignClient.php';\n"
                "$client = new SovereignClient(\n"
                "    'http://127.0.0.1:8765',\n"
                "    getenv('SOVEREIGN_BRIDGE_TOKEN')\n"
                ");\n"
                "$client->process(['/srv/pmsi/2025']);\n"
                "$cols = $client->collisions();\n"
                "$client->autoResolve();\n"
                "$client->exportCsv('/srv/pmsi/export');",
            ),
        ],
    ),
    (
        "Visualisation Excel (un ou plusieurs fichiers)",
        [
            (
                "p",
                "La page php/chart.php accepte un chemin unique ou plusieurs "
                "chemins (un par ligne). Le bridge agrege les donnees cote "
                "serveur et Chart.js dessine le graphique.",
            ),
            (
                "p",
                "Deux modes sont disponibles pour le multi-fichiers :",
            ),
            (
                "li",
                [
                    "merge : fusionne toutes les lignes en une seule serie "
                    "(utile pour un rapport consolide).",
                    "compare : genere une serie par fichier alignee sur l'union "
                    "des labels (utile pour comparer 2024 vs 2025 ou plusieurs "
                    "etablissements).",
                ],
            ),
            (
                "p",
                "Agregations : sum, avg, count. Types de graphiques supportes : "
                "bar, line, pie, doughnut.",
            ),
        ],
    ),
    (
        "Securite",
        [
            (
                "li",
                [
                    "Le bridge ecoute par defaut sur 127.0.0.1 : il ne sort pas "
                    "du poste. Pour ouvrir au LAN, utiliser --host 0.0.0.0 et "
                    "configurer un jeton fort.",
                    "Authentification Bearer : definir SOVEREIGN_BRIDGE_TOKEN "
                    "cote bridge et cote PHP.",
                    "CORS restrictif : la liste blanche est controlee par "
                    "SOVEREIGN_BRIDGE_ORIGINS (localhost par defaut).",
                    "Toutes les sorties PHP sont echappees via htmlspecialchars "
                    "pour eviter les XSS.",
                ],
            ),
        ],
    ),
    (
        "Depannage",
        [
            ("h", "Le PHP affiche 'Bridge inaccessible'"),
            (
                "p",
                "Verifier que python bridge.py tourne et que le port est libre. "
                "Sur Windows, autoriser Flask dans le pare-feu Microsoft Defender.",
            ),
            ("h", "openpyxl n'est pas installe"),
            (
                "code",
                "pip install openpyxl>=3.1",
            ),
            ("h", "Colonnes introuvables"),
            (
                "p",
                "Le bridge est sensible a la casse et aux espaces : verifier "
                "que l'entete du classeur correspond exactement a la valeur "
                "choisie dans le menu deroulant.",
            ),
        ],
    ),
]


# ──────────────────────────────────────────────────────────────────────────────
# GENERATION DU PDF — sous-classe de FPDF avec header/footer cohérents
# ──────────────────────────────────────────────────────────────────────────────

def build_pdf(output_path: str) -> str:
    """Construit le PDF et retourne le chemin absolu de sortie."""
    try:
        from fpdf import FPDF
    except ImportError as e:  # pragma: no cover — message humain
        print(
            "fpdf2 n'est pas installe.\n"
            "   -> pip install fpdf2>=2.8",
            file=sys.stderr,
        )
        raise SystemExit(1) from e

    class Manual(FPDF):
        """PDF avec en-tete/pied de page maison."""

        def header(self):
            # Bandeau haut : titre + date de generation
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(30, 41, 59)
            self.cell(0, 8, "Sovereign OS DIM - Mode d'emploi", new_x="RIGHT", new_y="TOP")
            self.set_font("Helvetica", "", 9)
            self.set_text_color(100, 116, 139)
            self.cell(0, 8, date.today().isoformat(), new_x="LMARGIN", new_y="NEXT", align="R")
            # Ligne de separation
            self.set_draw_color(226, 232, 240)
            self.line(10, 20, 200, 20)
            self.ln(8)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(148, 163, 184)
            self.cell(
                0, 8,
                f"Page {self.page_no()} / {{nb}}  -  Adam Beloucif - GHT Sud Paris",
                align="C",
            )

    pdf = Manual()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.alias_nb_pages()
    pdf.add_page()

    # Page de garde
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(15, 23, 42)
    pdf.ln(10)
    pdf.cell(0, 12, "Sovereign OS DIM V32.0", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 8, "Bridge PHP + Visualisation Excel multi-fichiers", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.multi_cell(
        0, 6,
        "Ce document decrit l'architecture du bridge HTTP, l'installation, "
        "l'utilisation du client PHP et la visualisation graphique d'un ou "
        "plusieurs classeurs Excel.",
    )
    pdf.ln(10)

    # Sections
    for title, blocks in SECTIONS:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(56, 189, 248)
        pdf.set_line_width(0.6)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 30, pdf.get_y())
        pdf.ln(4)

        for kind, content in blocks:
            if kind == "h":
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(30, 41, 59)
                pdf.cell(0, 7, content, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(1)
            elif kind == "p":
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(51, 65, 85)
                pdf.multi_cell(0, 5.5, content)
                pdf.ln(2)
            elif kind == "li":
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(51, 65, 85)
                # On préfixe chaque item par un tiret et on décale via set_x
                # plutôt qu'avec des cell() empilés (sinon multi_cell déborde
                # la marge droite et FPDFException est levée).
                left_indent = pdf.l_margin + 6
                for item in content:
                    pdf.set_x(left_indent)
                    pdf.multi_cell(0, 5.5, f"- {item}")
                pdf.ln(1)
            elif kind == "code":
                # Bloc monospace sur fond gris clair
                pdf.set_fill_color(241, 245, 249)
                pdf.set_text_color(15, 23, 42)
                pdf.set_font("Courier", "", 9)
                for line in content.split("\n"):
                    pdf.cell(0, 5, " " + line, new_x="LMARGIN", new_y="NEXT", fill=True)
                pdf.ln(2)
        pdf.ln(3)

    abs_out = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_out) or ".", exist_ok=True)
    pdf.output(abs_out)
    return abs_out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genere le mode d'emploi PDF (fpdf2)."
    )
    parser.add_argument(
        "--output",
        default=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "docs",
            "Sovereign_OS_DIM_Manuel.pdf",
        ),
        help="Chemin du PDF de sortie.",
    )
    args = parser.parse_args()

    path = build_pdf(args.output)
    print(f"[OK] Manuel genere : {path}")


if __name__ == "__main__":
    main()
