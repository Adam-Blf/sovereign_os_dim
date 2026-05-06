"""
═══════════════════════════════════════════════════════════════════════════════
 tools/generate_guide_public.py · Guide accessible · grand public
═══════════════════════════════════════════════════════════════════════════════

Variante du guide PDF rédigée pour être comprise par n'importe qui ·
parents, conjoint d'un soignant, élu local, journaliste, étudiant, etc.

Principes éditoriaux ·
- Caractères grands (corps 14 pour le texte, 22 pour les titres)
- Phrases courtes (≤ 20 mots), une idée par phrase
- Aucun jargon · si un sigle apparaît, il est expliqué juste après
- Analogies de la vie quotidienne (« c'est comme... »)
- Aucun chiffre fictif · si une donnée n'est pas factuelle, on dit « par exemple »
- Hiérarchie visuelle simple · 1 question → 1 réponse

Sortie · Sovereign_OS_DIM_Guide_Public.pdf à la racine du dépôt.
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGO_PATH = os.path.join(ROOT, "frontend", "logo_gh.png")

# Polices Unicode (mêmes résolveurs que generate_guide.py)
sys.path.insert(0, HERE)
try:
    from generate_guide import (
        SANS, MONO, _register_fonts,
        GH_NAVY, GH_TEAL, GH_GOLD, SLATE_900, SLATE_700,
        SLATE_500, SLATE_400, SLATE_200, SLATE_100, SLATE_50,
    )
except Exception:  # pragma: no cover · fallback
    SANS, MONO = "Helvetica", "Courier"
    GH_NAVY = (0, 0, 145)
    GH_TEAL = (0, 137, 123)
    GH_GOLD = (212, 164, 55)
    SLATE_900 = (15, 23, 42)
    SLATE_700 = (51, 65, 85)
    SLATE_500 = (100, 116, 139)
    SLATE_400 = (148, 163, 184)
    SLATE_200 = (226, 232, 240)
    SLATE_100 = (241, 245, 249)
    SLATE_50 = (248, 250, 252)

    def _register_fonts(pdf): return False


# ─────────────────────────────────────────────────────────────────────────────
# CONTENU · 12 questions / réponses
# ─────────────────────────────────────────────────────────────────────────────

QUESTIONS = [
    {
        "q": "C'est quoi, en deux mots ?",
        "a": (
            "Sovereign OS DIM est un logiciel installé sur l'ordinateur d'un "
            "hôpital de psychiatrie. Il aide le service qui s'occupe des "
            "papiers médicaux (le service DIM) à faire son travail plus vite "
            "et avec moins d'erreurs."
        ),
        "ex": (
            "Imaginez le secrétariat d'un cabinet médical, mais à l'échelle "
            "d'un hôpital entier qui suit 37 000 patients. Sovereign OS DIM, "
            "c'est l'outil qui range, vérifie et résume tous ces dossiers."
        ),
    },
    {
        "q": "À quoi ça sert concrètement ?",
        "a": (
            "Chaque hôpital doit envoyer chaque mois à l'État un compte-rendu "
            "des soins qu'il a donnés. C'est obligatoire pour être payé. "
            "Sovereign OS prépare ces comptes-rendus, vérifie qu'il n'y a "
            "pas d'erreurs, et les envoie de façon sécurisée."
        ),
        "ex": (
            "C'est comme la déclaration d'impôts d'un hôpital, qu'il doit "
            "faire chaque mois. Le logiciel pré-remplit les cases et "
            "détecte les oublis avant l'envoi."
        ),
    },
    {
        "q": "Pourquoi un nouveau logiciel ?",
        "a": (
            "Les outils existants sont anciens, lents, et coûtent cher. "
            "Sovereign OS est gratuit, rapide, et fonctionne sans internet. "
            "Il a été pensé pour les besoins précis de la psychiatrie, "
            "pas pour des hôpitaux généralistes."
        ),
        "ex": (
            "Comparez une vieille calculatrice de bureau et un smartphone "
            "moderne · les deux calculent, mais l'un est plus rapide et "
            "fait plein de choses en plus."
        ),
    },
    {
        "q": "Et la confidentialité des patients ?",
        "a": (
            "Les données ne quittent jamais l'ordinateur. Pas d'envoi sur "
            "Internet, pas de cloud, pas de partage avec des tiers. Tout "
            "reste dans l'hôpital. C'est le principe « 100 % local »."
        ),
        "ex": (
            "C'est comme un coffre-fort dans le bureau d'un médecin · "
            "personne ne peut l'ouvrir à distance, ni emporter son contenu "
            "sans s'en rendre compte."
        ),
    },
    {
        "q": "Qui s'en sert au quotidien ?",
        "a": (
            "Trois métiers utilisent ce logiciel · le TIM (technicien qui "
            "saisit les données), le médecin DIM (qui valide), et le chef "
            "de pôle (qui suit l'activité du service)."
        ),
        "ex": (
            "Comme dans une cuisine de restaurant · le commis prépare "
            "(TIM), le chef goûte et valide (médecin DIM), le directeur "
            "regarde combien de couverts sont sortis (chef de pôle)."
        ),
    },
    {
        "q": "Qu'est-ce qu'une « collision d'identité » ?",
        "a": (
            "Quand deux dossiers d'un même patient ont des informations "
            "différentes, par exemple deux dates de naissance. C'est "
            "souvent une erreur de saisie. Le logiciel les détecte et "
            "propose de choisir la bonne version."
        ),
        "ex": (
            "Un peu comme deux fiches d'inscription à l'école avec une "
            "faute de frappe sur la même personne · il faut savoir "
            "laquelle est la vraie."
        ),
    },
    {
        "q": "Et l'intelligence artificielle, dans tout ça ?",
        "a": (
            "Le logiciel embarque trois petits modèles d'IA. Ils aident "
            "le technicien à repérer les fichiers mal nommés, les dates "
            "de naissance suspectes, et les patients qui pourraient être "
            "des doublons. L'IA propose, le technicien décide toujours."
        ),
        "ex": (
            "Comme un correcteur d'orthographe dans Word · il souligne "
            "les erreurs probables, mais c'est vous qui corrigez."
        ),
    },
    {
        "q": "C'est facile à installer ?",
        "a": (
            "Oui · un seul fichier à double-cliquer. Pas besoin "
            "d'administrateur, pas de compte à créer, pas de licence à "
            "acheter. Le logiciel s'ouvre en quelques secondes."
        ),
        "ex": (
            "C'est comme ouvrir un PDF · vous double-cliquez et le "
            "programme se lance dans une fenêtre."
        ),
    },
    {
        "q": "Combien de temps ça fait gagner ?",
        "a": (
            "Cela dépend de l'hôpital. Chaque collision résolue à la main "
            "prend entre 20 et 45 minutes. Quand le logiciel en résout 100 "
            "automatiquement, on parle de plusieurs jours de travail "
            "économisés par mois."
        ),
        "ex": (
            "Comme un GPS qui calcule l'itinéraire le plus rapide · vous "
            "n'avez plus à ouvrir une carte papier et compter les "
            "kilomètres à la main."
        ),
    },
    {
        "q": "Est-ce que ça remplace les soignants ?",
        "a": (
            "Non, jamais. Sovereign OS s'occupe uniquement des papiers "
            "administratifs et statistiques. Les soins, l'écoute, le "
            "diagnostic, ce sont les soignants qui les font."
        ),
        "ex": (
            "C'est l'équivalent du logiciel de comptabilité d'un cabinet "
            "médical · il aide le médecin sur la paperasse, mais il "
            "n'examine aucun patient."
        ),
    },
    {
        "q": "Que se passe-t-il si l'ordinateur tombe en panne ?",
        "a": (
            "Toutes les données sont sauvegardées dans un petit fichier sur "
            "l'ordinateur. Si la machine tombe en panne, on récupère ce "
            "fichier et on le copie sur un autre ordinateur. Tout reprend "
            "comme avant."
        ),
        "ex": (
            "Comme un fichier Word sauvegardé sur une clé USB · même si "
            "l'ordinateur lâche, le document est encore là."
        ),
    },
    {
        "q": "Pourquoi c'est important pour la psychiatrie ?",
        "a": (
            "L'État finance les hôpitaux psychiatriques en fonction du "
            "nombre de patients suivis. Si les comptes-rendus sont mal "
            "remplis, l'hôpital touche moins d'argent. Avec un bon outil, "
            "les soins sont mieux financés et l'hôpital peut continuer à "
            "accueillir tout le monde."
        ),
        "ex": (
            "C'est comme bien remplir une feuille de soin chez le médecin · "
            "si une case est oubliée, la sécurité sociale rembourse mal."
        ),
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# RENDU PDF
# ─────────────────────────────────────────────────────────────────────────────


def build(output_path: str) -> str:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=22)
    _register_fonts(pdf)

    # ─── COUVERTURE ─────────────────────────────────────────────────────
    pdf.add_page()
    if os.path.exists(LOGO_PATH):
        try:
            pdf.image(LOGO_PATH, x=80, y=30, h=50)
        except Exception:  # pragma: no cover
            pass
    pdf.set_y(100)
    pdf.set_font(SANS, "B", 32)
    pdf.set_text_color(*GH_NAVY)
    pdf.cell(0, 14, "Sovereign OS DIM",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font(SANS, "", 18)
    pdf.set_text_color(*SLATE_700)
    pdf.cell(0, 10, "Le guide en clair", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)
    pdf.set_draw_color(*GH_TEAL)
    pdf.set_line_width(1.2)
    pdf.line(70, pdf.get_y(), 140, pdf.get_y())
    pdf.ln(10)
    pdf.set_font(SANS, "", 14)
    pdf.set_text_color(*SLATE_500)
    pdf.multi_cell(0, 8,
        "Un logiciel d'hôpital expliqué simplement · 12 questions, "
        "12 réponses, sans jargon technique.",
        align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font(SANS, "I", 12)
    pdf.set_text_color(*SLATE_400)
    pdf.cell(0, 6,
             f"Édition du {date.today().strftime('%d / %m / %Y')}",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 6, "Adam Beloucif · GHT Psy Sud Paris",
             new_x="LMARGIN", new_y="NEXT", align="C")

    # ─── PRÉAMBULE ──────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font(SANS, "B", 22)
    pdf.set_text_color(*GH_NAVY)
    pdf.cell(0, 14, "Avant de lire", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*GH_TEAL)
    pdf.set_line_width(0.6)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 30, pdf.get_y())
    pdf.ln(8)

    pdf.set_font(SANS, "", 14)
    pdf.set_text_color(*SLATE_700)
    pdf.multi_cell(0, 8,
        "Ce document est un guide d'introduction. Il s'adresse à toute "
        "personne curieuse de comprendre ce que fait ce logiciel, sans "
        "avoir besoin de connaître le vocabulaire de l'hôpital.",
        new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.multi_cell(0, 8,
        "Vous trouverez 12 questions courtes. Pour chacune, une réponse "
        "simple et un exemple de la vie quotidienne. Lisez dans l'ordre "
        "ou piochez celles qui vous intriguent.",
        new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font(SANS, "I", 12)
    pdf.set_text_color(*SLATE_500)
    pdf.multi_cell(0, 7,
        "Les sigles techniques (DIM, TIM, RPS, ATIH...) sont volontairement "
        "évités ou expliqués entre parenthèses. Si vous voulez le détail "
        "technique, lisez le « Guide métier » qui accompagne ce document.",
        new_x="LMARGIN", new_y="NEXT")

    # ─── 12 QUESTIONS · 1 PAR PAGE ─────────────────────────────────────
    for i, item in enumerate(QUESTIONS, start=1):
        pdf.add_page()
        # Numéro
        pdf.set_font(SANS, "B", 11)
        pdf.set_text_color(*GH_TEAL)
        pdf.cell(0, 5, f"QUESTION {i:02d} / {len(QUESTIONS)}",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        # Question (gros titre)
        pdf.set_font(SANS, "B", 24)
        pdf.set_text_color(*GH_NAVY)
        pdf.multi_cell(0, 10, item["q"],
                       new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(*GH_TEAL)
        pdf.set_line_width(0.6)
        pdf.line(pdf.get_x(), pdf.get_y() + 1, pdf.get_x() + 30, pdf.get_y() + 1)
        pdf.ln(10)
        # Réponse (corps de texte gros)
        pdf.set_font(SANS, "", 14)
        pdf.set_text_color(*SLATE_700)
        pdf.multi_cell(0, 8, item["a"], new_x="LMARGIN", new_y="NEXT")
        pdf.ln(8)
        # Exemple (encadré gold)
        x0, y0 = pdf.get_x(), pdf.get_y()
        pdf.set_fill_color(255, 251, 235)
        pdf.set_draw_color(*GH_GOLD)
        pdf.set_line_width(0.4)
        pdf.rect(x0, y0, 190, 36, "FD")
        pdf.set_xy(x0 + 5, y0 + 4)
        pdf.set_font(SANS, "B", 11)
        pdf.set_text_color(*GH_GOLD)
        pdf.cell(0, 5, "POUR COMPARER", new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(x0 + 5)
        pdf.set_font(SANS, "I", 13)
        pdf.set_text_color(*SLATE_700)
        pdf.multi_cell(180, 7, item["ex"], new_x="LMARGIN", new_y="NEXT")

    # ─── PAGE FINALE ────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font(SANS, "B", 22)
    pdf.set_text_color(*GH_NAVY)
    pdf.cell(0, 14, "Pour aller plus loin", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*GH_TEAL)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 30, pdf.get_y())
    pdf.ln(8)

    pdf.set_font(SANS, "", 14)
    pdf.set_text_color(*SLATE_700)
    pdf.multi_cell(0, 8,
        "Si vous voulez en savoir plus sur le fonctionnement précis du "
        "logiciel ·",
        new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    items_after = [
        ("Le Guide métier",
         "Document plus long destiné aux équipes hospitalières. Il "
         "détaille chaque écran, chaque fonctionnalité, et les références "
         "réglementaires."),
        ("Le Guide développeur",
         "Document technique pour les informaticiens qui veulent "
         "modifier ou étendre le logiciel."),
        ("Le code source ouvert",
         "Le logiciel est libre · n'importe qui peut le télécharger et "
         "le vérifier. Adresse · github.com/Adam-Blf/sovereign_os_dim"),
    ]
    for title, body in items_after:
        pdf.set_font(SANS, "B", 14)
        pdf.set_text_color(*GH_NAVY)
        pdf.cell(0, 8, "• " + title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(SANS, "", 13)
        pdf.set_text_color(*SLATE_700)
        pdf.multi_cell(0, 7, "  " + body, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    pdf.ln(8)
    pdf.set_font(SANS, "I", 12)
    pdf.set_text_color(*SLATE_500)
    pdf.multi_cell(0, 7,
        "Auteur · Adam Beloucif, alternant au service DIM du GHT Psy Sud "
        "Paris (Fondation Vallée et Paul Guiraud). Contact · "
        "adam.beloucif@psysudparis.fr",
        new_x="LMARGIN", new_y="NEXT")

    abs_out = os.path.abspath(output_path)
    pdf.output(abs_out)
    return abs_out


def main() -> None:  # pragma: no cover
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",
                   default=os.path.join(ROOT, "Sovereign_OS_DIM_Guide_Public.pdf"))
    args = p.parse_args()

    path = build(args.output)
    size_kb = os.path.getsize(path) // 1024

    # Enrichissement metadata + bookmarks
    try:
        sys.path.insert(0, HERE)
        from enrich_guide_pdf import enrich_pdf
        sections = [("Couverture", 0), ("Avant de lire", 1)]
        for i in range(len(QUESTIONS)):
            short = QUESTIONS[i]["q"]
            if len(short) > 50:
                short = short[:47] + "..."
            sections.append((f"Q{i + 1:02d} · {short}", 2 + i))
        sections.append(("Pour aller plus loin", 2 + len(QUESTIONS)))
        enrich_pdf(
            path, path,
            title="Sovereign OS DIM · Guide grand public",
            author="Adam Beloucif",
            subject="Guide accessible · 12 questions/réponses sans jargon",
            keywords="hôpital, psychiatrie, DIM, grand public, vulgarisation",
            creator="tools/generate_guide_public.py",
            sections=sections,
        )
        msg = f"(enrichi · {len(sections)} bookmarks)"
    except Exception as e:  # pragma: no cover
        msg = f"(brut · enrichissement skip · {e})"

    size_kb = os.path.getsize(path) // 1024
    print(f"[OK] Guide public genere: {path} ({size_kb} Ko) {msg}")


if __name__ == "__main__":  # pragma: no cover
    main()
