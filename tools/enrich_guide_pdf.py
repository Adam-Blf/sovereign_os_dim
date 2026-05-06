"""
═══════════════════════════════════════════════════════════════════════════════
 tools/enrich_guide_pdf.py · post-traitement du PDF généré par fpdf2
═══════════════════════════════════════════════════════════════════════════════

fpdf2 ne pose pas de métadonnées riches ni de table des matières
navigable (bookmarks / outline). Ce script lit le PDF généré par
generate_guide.py, ajoute ·

  - Métadonnées (Title, Author, Subject, Keywords, Creator, Producer)
  - Outline navigable (1 entrée par section · 38 pages)
  - Mode lecture page-par-page

et réécrit le PDF en place. Skill utilisé · pdf-official (pypdf).

Usage ·
    python tools/enrich_guide_pdf.py              # défauts
    python tools/enrich_guide_pdf.py --in X --out Y
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    Fit,
    NameObject,
)


# ─────────────────────────────────────────────────────────────────────────────
# STRUCTURE DU GUIDE · doit matcher generate_guide.py
# ─────────────────────────────────────────────────────────────────────────────
# 1 cover + 1 sommaire + 1 intro + 11 features × 3 pages + 1 roadmap +
# 1 support = 38 pages total.

FEATURE_TITLES = [
    "Dashboard et Master Patient Index",
    "Modo Files · sélection et traitement",
    "Identitovigilance · résolution des collisions",
    "PMSI Pilot CSV · exports e-PMSI",
    "Inspector + Preflight DRUIDES",
    "Dashboard Live · KPI temps réel",
    "Structure polaire · arborescence Pôle/Secteur/UM",
    "Analyse d'activité par UM",
    "Import CSV + HTML to PDF",
    "Tutoriel et administration",
    "Module ML XGBoost · prédiction et assistance",
]


def _build_outline_entries() -> list[tuple[str, int]]:
    """
    Liste (titre, n° de page 0-indexé) pour l'outline.
    Pages calculées sur la structure de generate_guide.py.
    """
    out = [
        ("Page de garde", 0),
        ("Sommaire", 1),
        ("Introduction du guide", 2),
        ("Lexique des sigles (suite)", 3),
        ("Contexte 2025-2029", 4),
    ]
    intro_pages = 3
    for i, title in enumerate(FEATURE_TITLES, start=1):
        first_page = 2 + intro_pages + (i - 1) * 3
        out.append((f"{i:02d}. {title}", first_page))
    gallery_start = 2 + intro_pages + len(FEATURE_TITLES) * 3
    out.append(("Galerie des écrans", gallery_start))
    out.append(("Feuille de route", gallery_start + 5))
    out.append(("Support et crédits", gallery_start + 6))
    return out


def enrich_pdf(input_path: str, output_path: str, *,
               title: str, author: str, subject: str, keywords: str,
               creator: str, sections: list[tuple[str, int]]) -> None:
    """
    Enrichisseur générique · ajoute métadonnées + outline navigable
    à n'importe quel PDF produit par fpdf2.

    sections · liste de (label, page_index_0_based).
    """
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    writer.add_metadata({
        "/Title": title,
        "/Author": author,
        "/Subject": subject,
        "/Keywords": keywords,
        "/Creator": creator,
        "/Producer": "fpdf2 · post-traité avec pypdf (skill pdf-official)",
        "/CreationDate": f"D:{datetime.now().strftime('%Y%m%d%H%M%S')}+02'00'",
    })

    for label, page_idx in sections:
        if 0 <= page_idx < len(writer.pages):
            writer.add_outline_item(label, page_idx, fit=Fit.fit())

    catalog = writer._root_object
    catalog[NameObject("/PageMode")] = NameObject("/UseOutlines")
    catalog[NameObject("/OpenAction")] = ArrayObject([
        writer.pages[0].indirect_reference,
        NameObject("/Fit"),
    ])

    with open(output_path, "wb") as f:
        writer.write(f)


def enrich(input_path: str, output_path: str) -> None:
    reader = PdfReader(input_path)
    writer = PdfWriter()

    # 1. Copie de toutes les pages
    for page in reader.pages:
        writer.add_page(page)

    # 2. Métadonnées riches (utilisées pour indexation, listes Adobe Reader,
    #    moteurs de recherche internes au DPI hospitalier)
    writer.add_metadata({
        "/Title": "Sovereign OS DIM · Guide métier V36",
        "/Author": "Adam Beloucif",
        "/Subject": "Station DIM · GHT Psy Sud Paris · Fondation Vallée + "
                    "Paul Guiraud · traitement PMSI 100 % local",
        "/Keywords": ("PMSI, ATIH, DRUIDES, RIM-P, psychiatrie, DIM, TIM, "
                      "identitovigilance, MPI, FicUM, FICHSUP-PSY, RPS, RAA, "
                      "GHT Sud Paris, Fondation Vallée, e-PMSI, RGPD, XGBoost"),
        "/Creator": "tools/generate_guide.py + tools/enrich_guide_pdf.py",
        "/Producer": "fpdf2 · post-traité avec pypdf (skill pdf-official)",
        "/CreationDate": f"D:{datetime.now().strftime('%Y%m%d%H%M%S')}+02'00'",
    })

    # 3. Outline navigable · une entrée par section
    parent_chap = None  # pas de niveau hiérarchique pour rester plat et lisible
    for title, page_num in _build_outline_entries():
        if page_num >= len(writer.pages):
            continue  # garde-fou
        writer.add_outline_item(title, page_num, parent=parent_chap,
                                fit=Fit.fit())

    # 4. Mode d'affichage · ouvrir avec l'outline visible (UseOutlines)
    catalog = writer._root_object
    catalog[NameObject("/PageMode")] = NameObject("/UseOutlines")

    # 5. Page d'ouverture · page 1 (la cover)
    catalog[NameObject("/OpenAction")] = ArrayObject([
        writer.pages[0].indirect_reference,
        NameObject("/Fit"),
    ])

    # 6. Écriture
    with open(output_path, "wb") as f:
        writer.write(f)


def main() -> None:  # pragma: no cover
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--in", dest="input",
                   default="Sovereign_OS_DIM_Guide.pdf",
                   help="Chemin du PDF source (défaut · racine du dépôt).")
    p.add_argument("--out", dest="output",
                   default="Sovereign_OS_DIM_Guide.pdf",
                   help="Chemin du PDF enrichi (défaut · même que --in, "
                        "réécriture en place).")
    args = p.parse_args()

    if not os.path.exists(args.input):
        print(f"[ERR] PDF source introuvable · {args.input}", file=sys.stderr)
        raise SystemExit(1)

    print(f"[ENRICH] Source · {args.input}")
    enrich(args.input, args.output)
    size_kb = os.path.getsize(args.output) // 1024
    print(f"[OK]     Sortie · {args.output} · {size_kb} Ko")

    # Re-vérification
    r = PdfReader(args.output)
    m = r.metadata or {}
    print(f"         Title    · {m.get('/Title')}")
    print(f"         Author   · {m.get('/Author')}")
    print(f"         Keywords · {m.get('/Keywords')[:60]}…"
          if m.get('/Keywords') else "         Keywords · (none)")
    print(f"         Outline  · {sum(1 for _ in r.outline)} entrées")


if __name__ == "__main__":  # pragma: no cover
    main()
