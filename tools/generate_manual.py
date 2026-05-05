# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM — Générateur de mode d'emploi PDF (fpdf2)
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#  Project : Sovereign OS V35.0 — Station DIM GHT Sud Paris
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
        "A qui s'adresse ce guide",
        [
            (
                "p",
                "Ce document est destine aux utilisateurs de la station DIM "
                "(Departement d'Information Medicale) du GHT Sud Paris. Il decrit "
                "comment utiliser Sovereign OS DIM au quotidien pour traiter les "
                "fichiers ATIH (PMSI), resoudre les incoherences d'identite "
                "patient, et produire les exports attendus par e-PMSI.",
            ),
            (
                "p",
                "Aucune connaissance technique n'est requise. L'application se "
                "lance d'un double-clic et toutes les operations se font a la "
                "souris depuis la barre laterale.",
            ),
        ],
    ),
    (
        "A quoi sert l'application",
        [
            (
                "p",
                "Sovereign OS DIM automatise quatre taches repetitives du "
                "quotidien d'un TIM :",
            ),
            (
                "li",
                [
                    "Lire les fichiers ATIH d'un ou plusieurs dossiers et les "
                    "identifier automatiquement (RPS, RSS, RHS, VID-HOSP, etc. "
                    "23 formats supportes depuis 1991).",
                    "Extraire pour chaque ligne le couple IPP / Date de "
                    "naissance et construire un index patient unifie (MPI).",
                    "Detecter les cas ou un meme IPP porte plusieurs dates de "
                    "naissance (collisions d'identitovigilance) et proposer une "
                    "resolution automatique ou manuelle.",
                    "Produire les exports CSV normalises et les fichiers .txt "
                    "purifies prets a etre deposes sur e-PMSI.",
                ],
            ),
        ],
    ),
    (
        "Premier lancement",
        [
            (
                "p",
                "Deux modes de lancement existent. Choisissez selon votre poste :",
            ),
            ("h", "Poste standard : executable portable"),
            (
                "p",
                "Double-cliquez sur Sovereign_OS_DIM.exe. L'application demarre "
                "en moins de trois secondes. Aucune installation, aucun droit "
                "administrateur requis : l'executable contient Python et toutes "
                "les dependances.",
            ),
            ("h", "Poste avec installation manuelle (DSI)"),
            (
                "p",
                "Si l'executable portable n'est pas disponible, la DSI peut "
                "lancer l'application depuis le code source. Contacter le "
                "support pour la procedure d'installation complete.",
            ),
            (
                "p",
                "La premiere execution derriere un proxy d'etablissement peut "
                "declencher une alerte pare-feu : autoriser l'application en "
                "reseau prive suffit. Elle ne communique qu'en local, "
                "jamais avec internet.",
            ),
        ],
    ),
    (
        "Tour d'ecran : la barre laterale",
        [
            (
                "p",
                "La barre de gauche contient six onglets, regroupes en trois "
                "sections (Controle, Gestion Batch, Exports Expert, Aide). "
                "Survoler une icone affiche son raccourci clavier.",
            ),
            (
                "li",
                [
                    "Dashboard : vue d'ensemble (fichiers traites, IPP uniques, "
                    "collisions, graphique par format).",
                    "Modo Files : selection des dossiers a traiter en lot.",
                    "Identitovigilance : liste des collisions IPP / DDN et "
                    "outil de resolution.",
                    "PMSI Pilot CSV : export CSV normalise pour e-PMSI.",
                    "Import CSV : lecture d'un CSV externe (cas d'usage annexe).",
                    "Tutoriel : rappel des gestes principaux, accessible hors "
                    "ligne.",
                ],
            ),
            (
                "p",
                "La bulle DIM en bas de la barre indique l'etat du moteur : "
                "verte si tout est charge, orange pendant un traitement, rouge "
                "si une erreur est remontee (consulter alors l'onglet ou le "
                "probleme s'est produit).",
            ),
        ],
    ),
    (
        "Workflow standard (traiter un lot de fichiers)",
        [
            ("h", "1. Ouvrir Modo Files"),
            (
                "p",
                "Cliquez sur Ajouter un dossier et pointez le repertoire "
                "contenant les fichiers ATIH (le scan est recursif : les sous-"
                "dossiers annuels sont inclus automatiquement).",
            ),
            ("h", "2. Verifier l'identification"),
            (
                "p",
                "Chaque fichier apparait avec son format detecte (RPS, RSS, "
                "RHS...) et sa taille. Les fichiers INCONNU sont ignores au "
                "traitement : c'est normal pour les .txt non ATIH.",
            ),
            ("h", "3. Lancer le traitement"),
            (
                "p",
                "Le bouton Traiter le lot extrait les couples IPP/DDN en "
                "parallele (jusqu'a 8 fichiers simultanes). La progression "
                "s'affiche ligne par ligne dans le terminal integre.",
            ),
            ("h", "4. Consulter le Dashboard"),
            (
                "p",
                "Une fois le lot traite, le Dashboard affiche les totaux : "
                "lignes valides, IPP uniques, collisions detectees. Le "
                "graphique de repartition par format permet de verifier qu'il "
                "ne manque pas un recueil (ex : un RHS absent alors qu'il "
                "devrait etre la).",
            ),
        ],
    ),
    (
        "Resoudre les collisions (Identitovigilance)",
        [
            (
                "p",
                "Une collision signifie qu'un meme IPP a ete rencontre avec "
                "plusieurs dates de naissance differentes dans les fichiers. "
                "C'est le signal d'un probleme d'identite patient a arbitrer.",
            ),
            ("h", "Lire la liste"),
            (
                "p",
                "Chaque ligne affiche : IPP, nombre de DDN en conflit, DDN "
                "candidates triees par frequence, et fichiers sources. La "
                "DDN la plus frequente est mise en avant.",
            ),
            ("h", "Resoudre manuellement"),
            (
                "p",
                "Cliquer sur une DDN candidate la fixe comme DDN pivot. A "
                "partir de ce moment, tous les exports CSV et .txt purifies "
                "remplaceront les autres DDN par ce pivot pour cet IPP.",
            ),
            ("h", "Resoudre automatiquement"),
            (
                "p",
                "Le bouton Auto-resolution applique la strategie bayesienne "
                "simple : pour chaque collision, la DDN la plus frequente est "
                "choisie, avec la plus recente comme critere de depart en cas "
                "d'egalite. Utile pour defricher un gros lot avant un examen "
                "manuel des cas douteux.",
            ),
            (
                "p",
                "Toutes les resolutions sont traceables : l'historique des "
                "DDN et de leurs fichiers sources reste consultable meme "
                "apres fixation d'un pivot.",
            ),
        ],
    ),
    (
        "Exporter pour e-PMSI (PMSI Pilot CSV)",
        [
            ("h", "CSV Pilot"),
            (
                "p",
                "Genere un fichier .csv par fichier ATIH traite. Colonnes : "
                "IPP ; DDN ; FORMAT ; NOM_FICHIER ; LIGNE_BRUTE. Si une DDN "
                "pivot est definie, elle remplace les autres DDN dans l'export "
                "(les lignes modifiees sont comptees dans le rapport final).",
            ),
            ("h", ".txt purifie"),
            (
                "p",
                "Reecrit un fichier ATIH conforme avec : lignes invalides "
                "supprimees, auto-repair applique (longueur ajustee), DDN "
                "pivot injectee. Le fichier resultant est directement "
                "depose-able sur e-PMSI.",
            ),
            (
                "p",
                "Les deux exports ecrivent dans un dossier Exports_AAAAMMJJ "
                "cree a cote des fichiers sources, horodate pour eviter "
                "d'ecraser une generation precedente.",
            ),
        ],
    ),
    (
        "Astuces du quotidien",
        [
            (
                "li",
                [
                    "Relancer un traitement sans quitter : bouton Reset dans "
                    "le Dashboard pour repartir d'un MPI vide.",
                    "Inspector ligne par ligne : dans Modo Files, clic droit "
                    "sur un fichier -> Inspecter permet de voir les 3000 "
                    "premieres lignes avec leur statut (OK, COLLISION, "
                    "FILTERED, ERROR) et la raison d'un rejet eventuel.",
                    "Theme sombre : bouton en haut a droite, bascule "
                    "immediate et persistante.",
                    "Raccourcis : 1 a 6 sur les touches numeriques pour "
                    "naviguer entre les onglets, Ctrl+R pour relancer le lot.",
                ],
            ),
        ],
    ),
    (
        "Depannage (utilisateur)",
        [
            ("h", "Un fichier ATIH apparait en INCONNU"),
            (
                "p",
                "Le nom du fichier ne correspond pas a une convention ATIH "
                "reconnue. Verifier qu'il contient bien le motif attendu "
                "(ex : RPS, RSS, RHS, VIDHOSP). Les fichiers archives .zip "
                "doivent etre decompresses au prealable.",
            ),
            ("h", "Le Dashboard reste a zero apres traitement"),
            (
                "p",
                "Aucune ligne valide n'a ete trouvee. Cause frequente : "
                "dossier vide, fichiers en INCONNU uniquement, ou lignes "
                "trop courtes (< 50 caracteres, considerees comme du "
                "padding).",
            ),
            ("h", "Un IPP attendu est absent des exports"),
            (
                "p",
                "Consulter l'Inspector du fichier source. Les lignes avec "
                "IPP vide, purement numerique a zero, ou positionne hors "
                "limites sont filtrees silencieusement. La colonne Repair "
                "indique le motif exact (ex : 'Hors limites' si la ligne "
                "est plus courte que la position IPP attendue).",
            ),
            ("h", "L'application ne demarre pas"),
            (
                "p",
                "Sous Windows, lancer depuis le dossier d'origine (ne pas "
                "copier l'executable sur un bureau reseau : certains "
                "antivirus bloquent l'execution en zone restreinte). En "
                "dernier recours, lancer depuis PowerShell pour voir le "
                "message d'erreur complet.",
            ),
        ],
    ),
    (
        "Pour les administrateurs DSI : integration avec les systemes existants",
        [
            (
                "p",
                "Sovereign OS DIM peut etre integre au systeme d'information "
                "hospitalier existant (SIH) via un module de connexion "
                "securise. Cette section concerne uniquement les equipes "
                "techniques de la DSI - les TIM n'ont pas a s'en preoccuper.",
            ),
            ("h", "Cas d'usage"),
            (
                "p",
                "L'integration DSI permet a une application PHP existante "
                "(portail intranet, outil de reporting) d'interroger "
                "directement Sovereign OS DIM pour obtenir les donnees PMSI "
                "traitees, sans que le TIM ait a exporter manuellement.",
            ),
            ("h", "Mise en oeuvre"),
            (
                "p",
                "La configuration technique (URL, cle d'acces, parametres "
                "reseau) est documentee dans la notice d'integration "
                "disponible aupres du support : "
                "adam.beloucif@psysudparis.fr. "
                "La DSI ne doit pas modifier les fichiers de configuration "
                "sans accord prealable avec l'editeur.",
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
    pdf.cell(0, 12, "Sovereign OS DIM V34.0", new_x="LMARGIN", new_y="NEXT")
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
