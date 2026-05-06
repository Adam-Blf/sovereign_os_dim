# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM · Generateur de guide PDF complet (fpdf2)
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#  Project : Sovereign OS V35.0 · Station DIM GHT Sud Paris
#
#  Description ·
#    Produit `Sovereign_OS_DIM_Guide.pdf` a la racine du depot · un seul
#    fichier PDF, 20 pages par fonctionnalite, avec logo Groupe Hospitalier
#    Paul Guiraud en en-tete sur chaque page.
#
#  Usage ·
#    python tools/generate_guide.py [--output chemin.pdf]
#
#  Architecture ·
#    - FEATURES · liste de dicts · chaque fonctionnalite documentee
#    - Chaque feature est rendue en 20 pages identiquement structurees
#      (cover, resume, pourquoi, prerequis, ..., FAQ, references)
#    - Plus une page de garde + sommaire + glossaire final
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations

import argparse
import os
import sys
from datetime import date


# ══════════════════════════════════════════════════════════════════════════════
# CHEMINS
# ══════════════════════════════════════════════════════════════════════════════
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGO_PATH = os.path.join(ROOT, "interface graphique", "logo_gh.png")
SCREENSHOT_DIR = os.path.join(ROOT, "docs", "screenshots")
FONT_DIR = os.path.join(HERE, "fonts")  # polices bundlees (optionnel)


# ══════════════════════════════════════════════════════════════════════════════
# POLICES UNICODE · accents et typographie hospitaliere
# ══════════════════════════════════════════════════════════════════════════════
# Sans police TTF Unicode, fpdf2 retombe sur Helvetica core (latin-1 only),
# ce qui supprime tous les accents (Apercu vs Apercu, etc.). Ce resolveur
# choisit la meilleure police disponible · Segoe UI sur Windows (poste DIM
# cible), DejaVu Sans sur Linux/CI, fallback Helvetica core sinon.
# ══════════════════════════════════════════════════════════════════════════════

# Familles logiques utilisees partout dans le rendu. Resolues a build_pdf().
SANS = "GuideSans"   # corps de texte, titres
MONO = "GuideMono"   # snippets code, fichiers, IPP

# Variantes recherchees · regular, bold, italic, bold-italic
_SANS_CANDIDATES = (
    # Windows · Segoe UI (excellente lisibilite a l'ecran et en print)
    ("C:/Windows/Fonts/segoeui.ttf",  "C:/Windows/Fonts/segoeuib.ttf",
     "C:/Windows/Fonts/segoeuii.ttf", "C:/Windows/Fonts/segoeuiz.ttf"),
    # Linux Debian/Ubuntu · DejaVu (couvre tout l'ATIH + sigles ARS)
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"),
    # Windows · Arial fallback
    ("C:/Windows/Fonts/arial.ttf",   "C:/Windows/Fonts/arialbd.ttf",
     "C:/Windows/Fonts/ariali.ttf",  "C:/Windows/Fonts/arialbi.ttf"),
    # Police bundlee dans tools/fonts/ si presente
    (os.path.join(FONT_DIR, "DejaVuSans.ttf"),
     os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"),
     os.path.join(FONT_DIR, "DejaVuSans-Oblique.ttf"),
     os.path.join(FONT_DIR, "DejaVuSans-BoldOblique.ttf")),
)

_MONO_CANDIDATES = (
    ("C:/Windows/Fonts/consola.ttf",  "C:/Windows/Fonts/consolab.ttf",
     "C:/Windows/Fonts/consolai.ttf", "C:/Windows/Fonts/consolaz.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Oblique.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-BoldOblique.ttf"),
    ("C:/Windows/Fonts/cour.ttf",   "C:/Windows/Fonts/courbd.ttf",
     "C:/Windows/Fonts/couri.ttf",  "C:/Windows/Fonts/courbi.ttf"),
    (os.path.join(FONT_DIR, "DejaVuSansMono.ttf"),
     os.path.join(FONT_DIR, "DejaVuSansMono-Bold.ttf"),
     os.path.join(FONT_DIR, "DejaVuSansMono-Oblique.ttf"),
     os.path.join(FONT_DIR, "DejaVuSansMono-BoldOblique.ttf")),
)


def _pick_font_set(candidates):
    """Renvoie le 1er quadruplet (R, B, I, BI) totalement disponible, ou None."""
    for tup in candidates:
        if all(os.path.exists(p) for p in tup):
            return tup
    return None


def _register_fonts(pdf):
    """
    Charge SANS et MONO sur l'instance PDF. Retourne True si Unicode actif.
    Si aucune police TTF dispo, alias SANS->Helvetica et MONO->Courier (core,
    sans accents) pour ne pas casser le build.
    """
    sans = _pick_font_set(_SANS_CANDIDATES)
    mono = _pick_font_set(_MONO_CANDIDATES)
    unicode_ok = bool(sans and mono)
    if sans:
        pdf.add_font(SANS, "",   sans[0])
        pdf.add_font(SANS, "B",  sans[1])
        pdf.add_font(SANS, "I",  sans[2])
        pdf.add_font(SANS, "BI", sans[3])
    else:  # pragma: no cover · fallback rare
        # Alias propre · on garde le nom "GuideSans" mais set_font tombera
        # sur Helvetica core via le mecanisme de FPDF.
        globals()["SANS"] = "Helvetica"
    if mono:
        pdf.add_font(MONO, "",   mono[0])
        pdf.add_font(MONO, "B",  mono[1])
        pdf.add_font(MONO, "I",  mono[2])
        pdf.add_font(MONO, "BI", mono[3])
    else:  # pragma: no cover
        globals()["MONO"] = "Courier"
    return unicode_ok

# Mapping feature -> screenshot (nom de fichier dans docs/screenshots/)
# Si un screenshot est absent, fallback sur le mockup schematique.
FEATURE_SCREENSHOTS = {
    0: "01_tableau de bord.png",           # 01 , Tableau de bord et MPI
    1: "02_modo_files.png",          # 02 , Sélection des fichiers
    2: "03_idv.png",                 # 03 , Identitovigilance
    3: "04_pilot_csv.png",           # 04 , PMSI Pilot CSV
    4: "02_modo_files.png",          # 05 , Inspector + Contrôle préalable , se lance depuis Modo
    5: "08_cockpit.png",             # 06 , Tableau de bord en direct , vue exécutive
    6: "06_structure.png",           # 07 , Structure
    7: "07_structure_activity.png",  # 08 , Analyse d'activité par UM
    8: "05_csv_import.png",          # 09 , Import CSV + HTML to PDF
    9: "08_tuto.png",                # 10 , Tutoriel
    10: "13_cim.png",                # 11 , Module ML XGBoost , CimSuggester live
}

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM · palette + echelle typographique unique
# ══════════════════════════════════════════════════════════════════════════════
# Une seule source de verite pour les couleurs et la typo. Toutes les
# fonctions de rendu lisent ces constantes · changer la palette ici se
# repercute sur l'integralite du PDF.
#
# Palette · charte Groupe Hospitalier Paul Guiraud
#   - GH_NAVY  · couleur Republique Francaise (titres, en-tetes)
#   - GH_TEAL  · accent secondaire (filets, indicateurs, succes operationnel)
#   - GH_GOLD  · accent tertiaire (mise en valeur metier · gain de temps)
# Niveaux SLATE · echelle de gris pour le corps de texte (Tailwind slate)
# ══════════════════════════════════════════════════════════════════════════════
GH_NAVY = (0, 0, 145)        # #000091 · titres, headers, accents primaires
GH_TEAL = (0, 137, 123)      # #00897B · filets, indicateurs, accent secondaire
GH_GOLD = (212, 164, 55)     # #D4A437 · mise en valeur metier, ROI
GH_ERR  = (225, 29, 72)      # #E11D48 · erreurs, blocages reglementaires
GH_OK   = (16, 185, 129)     # #10B981 · succes, conformite RGPD
GH_WARN = (245, 158, 11)     # #F59E0B · warnings, points d'attention
SLATE_900 = (15, 23, 42)     # texte principal sombre
SLATE_700 = (51, 65, 85)     # corps de texte
SLATE_500 = (100, 116, 139)  # texte secondaire, captions
SLATE_400 = (148, 163, 184)  # bordures actives, footers
SLATE_200 = (226, 232, 240)  # bordures, separateurs
SLATE_100 = (241, 245, 249)  # fonds clairs neutres
SLATE_50  = (248, 250, 252)  # fond le plus clair (cards)
WHITE     = (255, 255, 255)

# Echelle typographique · 7 niveaux fixes, jamais de tailles ad-hoc
TYPE = {
    "display": 28,   # cover seulement
    "h1":      18,   # titre de feature
    "h2":      14,   # titres de page (PAGE 02 / 03)
    "h3":      11,   # sous-titres ("A quoi ca sert", "Mode opératoire", ...)
    "body":    10,   # corps de texte standard
    "small":   8.5,  # legendes, captions
    "caption": 7,    # meta dans les schemas, footers internes
}

# Espacements verticaux standards (en mm)
SPACE = {
    "xs": 1.5, "sm": 3, "md": 5, "lg": 8, "xl": 12,
}


# ══════════════════════════════════════════════════════════════════════════════
# FEATURES · 10 fonctionnalites, chacune structuree en 20 pages identiques
# ══════════════════════════════════════════════════════════════════════════════
# Chaque feature est un dict avec 20 cles de contenu qui correspondent aux
# 20 pages du template. Le rendu est fait par render_feature() qui boucle
# sur les 20 pages dans un ordre fixe.
# ══════════════════════════════════════════════════════════════════════════════


def mk(title, category, tagline, purpose, prerequisites, access, interface,
       workflow_steps, options, integration, usecase_1, usecase_2,
       performance, security, troubleshooting, faq, best_practices,
       metrics, references):
    """Construit un dict feature avec validation des tailles."""
    assert len(workflow_steps) == 3, "3 etapes mode opératoire attendues"
    assert len(faq) >= 3, "au moins 3 Q/R dans la FAQ"
    return dict(
        title=title, category=category, tagline=tagline, purpose=purpose,
        prerequisites=prerequisites, access=access, interface=interface,
        workflow_1=workflow_steps[0], workflow_2=workflow_steps[1],
        workflow_3=workflow_steps[2], options=options, integration=integration,
        usecase_1=usecase_1, usecase_2=usecase_2, performance=performance,
        security=security, troubleshooting=troubleshooting, faq=faq,
        best_practices=best_practices, metrics=metrics, references=references,
    )


FEATURES = [
    # ══════════════════════════════════════════════════════════════════════
    # FEATURE 1 · DASHBOARD ET MPI
    # ══════════════════════════════════════════════════════════════════════
    mk(
        title="Tableau de bord et Master Patient Index",
        category="Pilotage",
        tagline="Vue d'ensemble temps reel du traitement PMSI",
        purpose=(
            "Le Tableau de bord est la page d'accueil de Sovereign OS DIM. Il centralise les "
            "indicateurs essentiels après un ou plusieurs traitements de lot ATIH et "
            "construit le MPI (Master Patient Index) , l'index unifie qui associe a "
            "chaque IPP (Identifiant Patient Permanent) l'ensemble de ses occurrences "
            "dans les differents recueils PMSI.\n\n"
            "Sans MPI, impossible de détecter les collisions d'identité, les patients "
            "cross-modalites (PSY + SSR + HAD), ou la file active cumulative. Le "
            "Tableau de bord est donc le point d'ancrage de tout le mode opératoire DIM."
        ),
        prerequisites=(
            "Aucun. Le Tableau de bord s'affiche des l'ouverture de l'application, même "
            "sans dossier ATIH sélectionne (indicateur a zero). Les données apparaissent "
            "progressivement au fil des traitements.\n\n"
            "Pour des données peuplees , au moins un dossier ATIH ajoute via "
            "Sélection des fichiers et un premier traitement lance. La duree d'un traitement depend "
            "du volume , 30 000 lignes par seconde en moyenne sur poste standard."
        ),
        access=(
            "Raccourci clavier , Ctrl+1. Depuis n'importe quel autre onglet, la "
            "touche Echap ne revient pas au Tableau de bord, il faut utiliser Ctrl+1 ou "
            "cliquer sur l'icone tableau de bord en haut de la barre laterale.\n\n"
            "Le Tableau de bord est l'onglet actif au lancement. Si le MPI est persiste "
            "en SQLite (cf. fonctionnalité 3), il est recharge automatiquement au demarrage "
            "et les indicateur s'affichent sans traitement manuel."
        ),
        interface=(
            "Organisation verticale en 4 blocs ,\n\n"
            "1. En-tete , titre du tableau de bord + date du dernier traitement.\n"
            "2. Bande de 4 indicateur , fichiers traites, IPP uniques, collisions "
            "détectées, formats distincts.\n"
            "3. Graphique donut , repartition des lignes par format PMSI.\n"
            "4. Timeline Cross-modalites , patients porteurs de 3 formats ou plus.\n\n"
            "Chaque indicateur est une carte cliquable qui ouvre le détail (liste des "
            "fichiers, liste des collisions, etc.)."
        ),
        workflow_steps=[
            # 1
            "Ouvrir l'application et observer le Tableau de bord , si un MPI persiste "
            "existe, les indicateur sont peuples. Sinon, aller en Sélection des fichiers (Ctrl+2) pour "
            "ajouter un premier dossier ATIH. Le système détecte automatiquement "
            "les 23 formats PMSI supportes.",
            # 2
            "Après avoir ajoute un ou plusieurs dossiers, revenir au Tableau de bord. "
            "Cliquer sur Traiter le lot , une barre de progrèssion s'affiche et "
            "les indicateur se mettent à jour ligne par ligne. Pour un lot typique "
            "annuel (50 000 lignes), compter 2 a 5 secondes.",
            # 3
            "Une fois le traitement termine, analyser les indicateurs. Le nombre de "
            "collisions indique combien d'IPP portent des DDN differentes entre "
            "recueils , c'est le travail principal du TIM de les résoudre avant "
            "export e-PMSI. Cliquer sur la carte Collisions pour ouvrir "
            "Identitovigilance (Ctrl+3).",
        ],
        options=(
            "Deux options configurables au niveau du Tableau de bord ,\n\n"
            "1. Réinitialiser le registre , bouton en haut a droite, efface le MPI SQLite "
            "persiste. Aucune donnée source n'est touchee. Utile pour reprendre "
            "une analyse propre après erreur.\n\n"
            "2. Mode sombre , toggle en haut a droite, bascule toutes les vues "
            "en theme dark. Prefere par les TIM travaillant en fin de journee "
            "pour reduire la fatigue visuelle.\n\n"
            "Aucune configuration de persistance n'est exposee , le MPI est "
            "toujours sauvegarde en SQLite après chaque traitement."
        ),
        integration=(
            "Le Tableau de bord est alimente par toutes les autres features ,\n\n"
            "- Sélection des fichiers (Ctrl+2) alimente le comptage fichiers et lignes.\n"
            "- Identitovigilance (Ctrl+3) alimente le comptage collisions.\n"
            "- Inspecteur ligne par ligne (F2) utilise le MPI pour decoder une ligne.\n"
            "- Contrôle préalable DRUIDES (F3) lit le MPI pour valider la coherence.\n"
            "- Tableau de bord en direct (F4) reprend les mêmes données en Chart.js en direct.\n\n"
            "Les données circulent uniquement en memoire et en SQLite locale, "
            "jamais en réseau."
        ),
        usecase_1=(
            "Cas , reception mensuelle d'un lot de 12 fichiers ATIH en fin de mois. "
            "Le TIM charge les 12 fichiers, lance le traitement, consulte le "
            "Tableau de bord , 147 collisions détectées. Il passe en "
            "Identitovigilance, résout automatiquement 128 par règle majoritaire, "
            "traite manuellement les 19 restantes, puis exporte le CSV sanitized "
            "pour téléversement e-PMSI. Duree totale , environ 45 minutes."
        ),
        usecase_2=(
            "Cas , audit annuel pediatrie (Fondation Vallee). Le chef de pôle "
            "demande la file active 2024. Le TIM charge les 4 lots trimestriels, "
            "le Tableau de bord affiche 4821 IPP uniques. Sur la timeline Cross-modalites, "
            "il repere 23 patients porteurs de RPS + RSS (transferts MCO) et 8 "
            "patients porteurs de EDGAR + FICHSUP-PSY (ambulatoire avec isolement). "
            "Cette repartition alimente le rapport annuel du pôle."
        ),
        performance=(
            "Le Tableau de bord est rendu en JavaScript pur , aucun framework lourd. "
            "Les metriques sont recalculées en memoire depuis le MPI charge en "
            "SQLite. Pour un MPI de 50 000 IPP et 500 000 lignes ,\n\n"
            "- Chargement initial , < 400 ms\n"
            "- Rafraichissement après traitement , < 200 ms\n"
            "- Rendu donut Chart.js , < 80 ms\n\n"
            "La limite pratique observee est d'environ 2 millions de lignes sur "
            "poste standard (8 Go RAM), avec degradation progrèssive au-dela."
        ),
        security=(
            "Le Tableau de bord n'expose aucune donnée nominative par defaut , les "
            "indicateur sont des agregats. Seule la timeline Cross-modalites affiche "
            "des IPP, mais pseudonymises (IPP_XXXX) si le mode audit est actif.\n\n"
            "Le bouton Réinitialiser le registre declenche une confirmation obligatoire , "
            "impossible de perdre le MPI par erreur d'un simple clic. La "
            "suppression est logguee dans l'journal d audit art. 30 RGPD.\n\n"
            "Aucune donnée Tableau de bord n'est transmise hors du poste."
        ),
        troubleshooting=(
            "Problème , Tableau de bord affiche zero après traitement.\n"
            "Cause probable , Sélection des fichiers contient uniquement des fichiers INCONNU. "
            "Solution , vérifier le nommage ATIH attendu (RPS_AAAAMM*).\n\n"
            "Problème , indicateur collisions anormalement élevé (> 50 pourcent).\n"
            "Cause probable , annees de transition 2021 ou les formats IPP ont "
            "change. Solution , activer la normalisation IPP (par defaut oui).\n\n"
            "Problème , Tableau de bord lent au rafraichissement (> 2 s).\n"
            "Cause probable , MPI > 500 000 lignes. Solution , envisager un "
            "réinitialiser le registre et traiter uniquement l'annee courante."
        ),
        faq=[
            ("Le MPI est-il sauvegarde automatiquement ?",
             "Oui, après chaque traitement de lot, une sauvegarde SQLite est "
             "ecrite dans %LOCALAPPDATA%/SovereignOS/mpi.db."),
            ("Puis-je exporter les indicateur du Tableau de bord ?",
             "Oui, via Tableau de bord en direct (F4) qui génère un PDF paysage 2 pages."),
            ("Que se passe-t-il si je ferme l'app en cours de traitement ?",
             "Le traitement s'interrompt proprement , les données déjà extraites "
             "sont sauvegardees, le reste est perdu. Relancer le traitement "
             "reprend là où il s'était arrête (cf. persistance SQLite)."),
            ("Le Tableau de bord fonctionne-t-il en hors ligne ?",
             "Oui, 100 pourcent hors ligne. Aucune requête réseau."),
        ],
        best_practices=(
            "1. Commencer chaque session par un coup d'oeil au Tableau de bord , si "
            "les indicateur sont anormaux (collisions très élevées par exemple), "
            "investiguer avant de lancer un export.\n\n"
            "2. Ne pas utiliser Réinitialiser le registre sans raison , le MPI cumule l'historique "
            "et permet les comparaisons mois N vs N-1.\n\n"
            "3. Garder Tableau de bord en direct (F4) ouvert sur un second ecran pendant "
            "les traitements pour visualiser l'evolution en temps reel.\n\n"
            "4. Documenter chaque réinitialisation ou import massif dans le cahier DIM "
            "papier pour tracabilite audit."
        ),
        metrics=(
            "Indicateurs de sante du Tableau de bord a surveiller ,\n\n"
            "- Taux de collisions , cible < 5 pourcent des IPP uniques.\n"
            "- Taux de formats distincts , 3 a 5 typique pour un CHS PSY mono-recueil.\n"
            "- Duree du traitement , cible < 10 s pour un lot mensuel de 10 fichiers.\n"
            "- Taille du MPI SQLite , ~50 Mo pour 100 000 IPP + 500 000 observations.\n"
            "- Ratio patients cross-modalites / IPP total , 2 a 8 pourcent typique."
        ),
        references=(
            "Documentation ATIH , https://www.atih.sante.fr\n"
            "Format RPS P05 , Guide technique ATIH 2024 chapitre 4.\n"
            "Identitovigilance , HAS , Instruction DGOS/PF2 2019.\n"
            "DRUIDES , succèseur PIVOINE depuis 2025.\n"
            "GHT Sud Paris , Paul Guiraud + Fondation Vallee, convention 2016."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════════
    # FEATURE 2 · MODO FILES
    # ══════════════════════════════════════════════════════════════════════
    mk(
        title="Sélection des fichiers , sélection et traitement des lots ATIH",
        category="Lots",
        tagline="Scanner, identifier et traiter les 23 formats PMSI",
        purpose=(
            "Sélection des fichiers est le point d'entree de toute analyse PMSI , c'est ici "
            "que le TIM sélectionne les dossiers contenant les fichiers ATIH "
            "transmis par les logiciels sources (CPage, DxCare) ou télécharges "
            "depuis e-PMSI. Le scan est recursif , les sous-dossiers annuels, "
            "mensuels ou par pôle sont inclus automatiquement.\n\n"
            "Sans Sélection des fichiers, rien ne peut être traite , les autres vues "
            "(Identitovigilance, Contrôle préalable, Exports) consomment toutes le MPI "
            "construit à partir des fichiers ici sélectionnes."
        ),
        prerequisites=(
            "Un dossier accessible en lecture contenant au moins un fichier ATIH "
            "au format texte latin-1. Les dossiers réseau SMB sont supportes si "
            "la lettre de lecteur est mappee dans Windows.\n\n"
            "Les fichiers attendus respectent le nommage ATIH , `<FORMAT>_<ANNEE><MOIS>` "
            "ou `<FORMAT>_<ANNEE>`. Exemples , RPS_202410.txt, RAA_2024.txt, "
            "FICHSUP-PSY_202412.txt. L'identification fonctionne aussi sur des "
            "noms personnalises tant que l'extension est .txt."
        ),
        access=(
            "Raccourci clavier , Ctrl+2. La vue Sélection des fichiers est l'onglet le plus "
            "utilise par les TIM , elle reste cachee tant qu'aucun dossier n'est "
            "sélectionne, avec un call-to-action central Ajouter un dossier.\n\n"
            "Après ajout, la vue affiche , liste des dossiers actifs, compteur "
            "de fichiers, repartition par format, et boutons d'action (Traiter, "
            "Scanner a nouveau, Vider la sélection)."
        ),
        interface=(
            "3 zones principales ,\n\n"
            "1. Panneau supérieur , liste des dossiers ajoutes, chacun avec son "
            "chemin, le nombre de fichiers détectés et un bouton Supprimer.\n\n"
            "2. Panneau central , tableau des fichiers identifies , colonnes "
            "Nom, Format, Taille, Annee détectée, Lignes, Statut.\n\n"
            "3. Barre d'actions , Ajouter un dossier, Scanner a nouveau, "
            "Traiter le lot, Vider la sélection.\n\n"
            "Les formats INCONNU sont grises et ignores au traitement. Un clic "
            "sur une ligne ouvre l'Inspecteur ligne par ligne (F2) sur ce fichier."
        ),
        workflow_steps=[
            "Cliquer sur Ajouter un dossier. Le dialog natif Windows s'ouvre, "
            "naviguer vers le dossier ATIH (typiquement D:/DIM/ATIH/2024/mensuel). "
            "Valider , le scan recursif se lance immediatement.",
            "Parcourir le tableau des fichiers identifies. Verifier qu'aucun "
            "fichier attendu n'est INCONNU. Si un RPS apparait INCONNU, "
            "verifier le nommage , il doit contenir 'RPS' dans son nom.",
            "Cliquer Traiter le lot. Le moteur extrait les couples IPP/DDN en "
            "parallele (jusqu'a 8 fichiers simultanes), construit le MPI et "
            "persiste en SQLite. La progrèssion est affichee ligne par ligne "
            "dans le terminal integre.",
        ],
        options=(
            "Options disponibles depuis la barre d'actions ,\n\n"
            "- Scanner a nouveau , re-lit tous les dossiers en cas de modification "
            "des fichiers sources.\n\n"
            "- Vider la sélection , supprime tous les dossiers actifs (aucune "
            "donnée source touchee).\n\n"
            "- Filtrer par format , menu deroulant pour masquer certains formats "
            "(ex. afficher uniquement les RPS).\n\n"
            "Aucune option de parallelisme n'est exposee , le moteur détecte "
            "automatiquement le nombre de coeurs disponibles et plafonne a 8 "
            "workers pour eviter la saturation du MPI SQLite."
        ),
        integration=(
            "Sélection des fichiers alimente directement ,\n\n"
            "- Le Tableau de bord (Ctrl+1) , indicateur fichiers, lignes, formats.\n"
            "- Identitovigilance (Ctrl+3) , collisions détectées.\n"
            "- PMSI Pilot CSV (Ctrl+4) , sources pour les exports.\n"
            "- Inspecteur ligne par ligne (F2) , fichier source pour le diag.\n"
            "- Contrôle préalable DRUIDES (F3) , lit la liste des fichiers a valider.\n\n"
            "En amont, Sélection des fichiers ne depend que du système de fichiers , aucun "
            "appel a CPage, DxCare ou autre logiciel tiers."
        ),
        usecase_1=(
            "Cas , fin de trimestre, arrivee des 3 lots mensuels d'ATIH "
            "(juillet, août, septembre). Le TIM créé un dossier D:/DIM/ATIH/2024/T3 "
            "contenant 3 sous-dossiers mensuels, y copie les fichiers recus par "
            "email, puis n'ajoute que ce dossier T3 dans Sélection des fichiers. Le scan "
            "recursif détecte automatiquement les 27 fichiers repartis dans les "
            "3 sous-dossiers."
        ),
        usecase_2=(
            "Cas , migration annuelle, besoin de reprocesser 2022 dans le format "
            "2024 pour harmonisation BIQuery. Le TIM ajoute les 12 dossiers "
            "mensuels 2022, filtre par format RPS uniquement, lance le traitement. "
            "La normalisation IPP convertit les formats P04 historique en P05 "
            "actuel, garantissant la coherence avec les annees suivantes."
        ),
        performance=(
            "Performances mesurees sur poste i5 8e gen, 16 Go RAM, SSD NVMe ,\n\n"
            "- Scan de 1000 fichiers repartis sur 12 dossiers , 1.2 s.\n"
            "- Identification par heuristique + regex , 180 us par fichier.\n"
            "- Traitement d'un lot mensuel (10 fichiers, 150 000 lignes) , 5 s.\n"
            "- Parallelisme effectif , 8 workers en pic CPU.\n\n"
            "Le goulot principal est l'ecriture SQLite. Pour un très gros lot "
            "(> 1 M lignes), envisager de traiter par trimestres succèssifs."
        ),
        security=(
            "Aucun fichier source n'est jamais modifie, renomme ou deplace , "
            "l'application est en lecture seule sur vos données ATIH. Les "
            "exports sont toujours ecrits dans un dossier distinct choisi "
            "par l'utilisateur, jamais a cote des sources.\n\n"
            "Les données patient (IPP, DDN) sont protegees en memoire "
            "uniquement pendant le traitement, puis chiffrees dans la base "
            "locale. Aucune donnée n'est transmise hors du poste DIM.\n\n"
            "Toute tentative d'accès a un dossier non autorise est bloquee "
            "silencieusement , aucun chemin hors du poste ne peut être cible."
        ),
        troubleshooting=(
            "Problème , scanner annonce 0 fichier alors que le dossier en contient.\n"
            "Cause , permissions refusees (dossier réseau). Solution , vérifier "
            "les droits, re-mapper la lettre de lecteur.\n\n"
            "Problème , fichier RPS apparait INCONNU.\n"
            "Cause , longueur de ligne non standard (ancien format P04 2021). "
            "Solution , le système tente les variantes, si l'échec persiste "
            "ouvrir le fichier dans Inspecteur ligne par ligne pour diagnostic manuel.\n\n"
            "Problème , traitement plante après 80 pourcent.\n"
            "Cause , fichier corrompu en milieu de lot. Solution , isoler le "
            "fichier, ouvrir dans Inspecteur ligne par ligne ligne par ligne pour "
            "identifier la ligne fautive."
        ),
        faq=[
            ("Puis-je ajouter plusieurs dossiers simultanement ?",
             "Oui, jusqu'a 50 dossiers distincts en session. Au-dela, la "
             "performance se degrade mais le système ne plante pas."),
            ("Les fichiers .zip sont-ils supportes ?",
             "Non, il faut decompresser en amont. Une fonctionnalite future "
             "supportera l'ingestion directe de .zip ATIH."),
            ("Que se passe-t-il si un fichier est modifie pendant le scan ?",
             "Le fichier est re-scanne au prochain cycle. Les données déjà "
             "extraites sont conservees jusqu'au nouveau traitement."),
            ("Puis-je exclure certains fichiers ?",
             "Oui, via le filtre par format ou en decochant manuellement dans "
             "le tableau."),
        ],
        best_practices=(
            "1. Organiser les dossiers ATIH par annee puis par mois , "
            "D:/DIM/ATIH/<ANNEE>/<MOIS>. Le scan recursif en profite pleinement.\n\n"
            "2. Ne jamais renommer les fichiers sources , preserver les noms "
            "ATIH facilite l'identification et l'audit.\n\n"
            "3. Après un gros traitement, utiliser Tableau de bord en direct (F4) pour "
            "valider visuellement la coherence des données avant export.\n\n"
            "4. Conserver les fichiers sources 5 ans minimum (obligation "
            "règlementaire PMSI)."
        ),
        metrics=(
            "Metriques cles a suivre ,\n\n"
            "- Nombre de fichiers INCONNU , cible 0. Si > 0, investiguer le nommage.\n"
            "- Repartition par annee , doit être coherente avec la période attendue.\n"
            "- Taille moyenne par fichier , 1 a 10 Mo typique pour un CHS moyen.\n"
            "- Taux d'échec d'identification , cible < 0.1 pourcent.\n"
            "- Duree du traitement , 30 000 lignes par seconde en moyenne."
        ),
        references=(
            "Documentation technique ATIH 2024 , chapitres 1-23.\n"
            "Notice DRUIDES 2025 , format d'téléversement attendu.\n"
            "Convention GHT Sud Paris , circuit des fichiers ATIH mensuels.\n"
            "CPage (facturation) et DxCare (dossier patient) , sources amont.\n"
            "Politique de retention 5 ans , instruction DGOS/PF2/2020/143."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════════
    # FEATURE 3 · IDENTITOVIGILANCE
    # ══════════════════════════════════════════════════════════════════════
    mk(
        title="Identitovigilance , résolution des collisions IPP/DDN",
        category="Lots",
        tagline="Détecter et résoudre les identités patient ambigues",
        purpose=(
            "Un même IPP (numero de dossier patient) peut apparaitre avec des "
            "dates de naissance differentes selon les recueils , erreur de saisie, "
            "changement de format au cours du temps, ou homonymie non détectée. "
            "Ces collisions sont la principale cause de rejet a l'téléversement DRUIDES "
            "et degradent la qualité du MPI pour toute analyse en aval.\n\n"
            "Cette fonctionnalité détecte automatiquement toutes les collisions après "
            "traitement et propose deux strategies de résolution , automatique "
            "(règle majoritaire) ou manuelle (choix par le TIM)."
        ),
        prerequisites=(
            "Un MPI construit via Sélection des fichiers. Sans MPI, la vue affiche un etat "
            "vide avec un lien vers Sélection des fichiers.\n\n"
            "Pour une résolution efficace , disposer d'au moins deux recueils "
            "distincts (ex. RPS + RAA ou RPS + FICHSUP-PSY) , la croisement "
            "augmente la probabilite de détecter les incoherences."
        ),
        access=(
            "Raccourci clavier , Ctrl+3. Egalement accessible depuis le "
            "Tableau de bord en cliquant sur la carte indicateur Collisions.\n\n"
            "La vue s'ouvre immediatement sur la liste des collisions détectées, "
            "triees par severite decroissante (nombre de DDN differentes d'abord, "
            "puis nombre de sources)."
        ),
        interface=(
            "Liste a gauche, détail a droite ,\n\n"
            "Liste , chaque ligne affiche IPP, nombre de DDN distincts, nombre "
            "de sources (fichiers), et une icone de severite.\n\n"
            "Detail , pour l'IPP sélectionne , tableau des variantes DDN, chacune "
            "avec son nombre d'occurrences, la liste des fichiers sources et le "
            "bouton Retenir cette DDN. Un bouton Auto-resolve en haut tranche "
            "automatiquement toutes les collisions restantes.\n\n"
            "Barre de filtre en haut , par niveau (2, 3, 4+ DDN), par recueil "
            "(RPS, RAA, etc.), ou par annee."
        ),
        workflow_steps=[
            "Après traitement, ouvrir Identitovigilance (Ctrl+3). La liste est "
            "peuplee automatiquement. Trier par severite decroissante , les cas "
            "a 3+ DDN doivent être traites manuellement en priorité.",
            "Pour chaque collision sélectionnee, analyser les variantes , la "
            "DDN majoritaire est presélectionnee. Verifier les fichiers sources "
            "(clic sur le bouton Sources) , souvent la DDN minoritaire vient "
            "d'un recueil ancien converti. Cliquer Retenir cette DDN pour "
            "trancher.",
            "Une fois toutes les collisions manuelles traitees, cliquer "
            "Auto-resolve pour trancher automatiquement le reste. Le système "
            "applique la règle majoritaire. Les choix sont logguees dans "
            "l'journal d audit art. 30 RGPD.",
        ],
        options=(
            "Options disponibles ,\n\n"
            "- Mode anonymise , affiche les IPP pseudonymises (IPP_XXXX) pour "
            "eviter l'exposition nominative. Active par defaut après 10 min "
            "d'inactivite.\n\n"
            "- Export de la liste des collisions , CSV avec toutes les variantes "
            "par IPP, utile pour audit ou partage avec le chef de pôle.\n\n"
            "- Règle de priorité , par defaut DDN majoritaire. Alternative , "
            "DDN la plus recente (horodatage du fichier source).\n\n"
            "- Seuil d'auto-resolve , configurable (defaut , tout IPP a 2 DDN "
            "avec ratio majoritaire >= 70 pourcent)."
        ),
        integration=(
            "Identitovigilance consomme ,\n\n"
            "- Le MPI construit par Sélection des fichiers.\n"
            "- Les metadonnees de fichiers (noms, annees) pour l'affichage.\n\n"
            "Identitovigilance alimente ,\n\n"
            "- PMSI Pilot CSV , les exports filtrent selon la résolution.\n"
            "- Contrôle préalable DRUIDES , les collisions non-resolues sont signalees.\n"
            "- Inspecteur ligne par ligne , reprend le contexte de collision pour une "
            "ligne donnée.\n\n"
            "Les choix de résolution sont persistes en SQLite avec le MPI."
        ),
        usecase_1=(
            "Cas , RPS historique 2021 au format P04 (142 chars) vs RPS 2024 au "
            "format P05 (154 chars). Les IPP ont été convertis entre temps. 340 "
            "collisions apparaissent , toutes resultent de la conversion. "
            "L'Auto-resolve tranche en moins de 1 seconde, le TIM valide le "
            "rapport en verifiant un échantillon de 10 cas."
        ),
        usecase_2=(
            "Cas , homonymie reelle détectée. Deux patients nommes Dupont Marie "
            "portent le même IPP temporaire suite a une erreur d'admission. "
            "Identitovigilance affiche 2 DDN distinctes (1985 et 1987), avec "
            "15 lignes pour chaque. Le TIM ouvre Inspecteur ligne par ligne sur les 2 "
            "fichiers, identifie les IPP definitifs corrects cote CPage, et "
            "applique la résolution manuelle fichier par fichier."
        ),
        performance=(
            "La détection des collisions est O(N) ou N = nombre de lignes "
            "extraites , un passage unique sur le MPI avec index SQLite. Pour "
            "un MPI de 500 000 observations ,\n\n"
            "- Détection , 120 ms.\n"
            "- Affichage de la liste triee , 80 ms.\n"
            "- Auto-resolve , 200 ms.\n\n"
            "Le rendu de la vue détail est instantane grace a l'index SQLite "
            "sur la colonne ipp."
        ),
        security=(
            "Cette vue traite des données identifiantes de sante soumises "
            "au RGPD. Protections appliquees ,\n\n"
            "- Anonymisation automatique après 10 min d'inactivite (IPP "
            "masques a l'ecran).\n"
            "- Chaque résolution est tracee dans le journal d'audit RGPD "
            "(qui, quand, quel choix). Consultable a tout moment.\n"
            "- Les exports CSV sont pseudonymises , aucun IPP en clair "
            "dans les fichiers partages avec le chef de pôle ou l'ARS.\n\n"
            "L'accès aux données non-anonymisees est reserve au cadre DIM "
            "authentifie, conformement a la politique du GHT."
        ),
        troubleshooting=(
            "Problème , Auto-resolve ne tranche aucune collision.\n"
            "Cause , toutes les collisions ont un ratio < seuil. Solution , "
            "baisser le seuil a 60 pourcent ou traiter manuellement.\n\n"
            "Problème , collision apparente qui n'en est pas une après "
            "verification DxCare.\n"
            "Cause , format DDN differents (JJMMAAAA vs AAAAMMJJ). Solution , "
            "verifier la normalisation DDN dans les settings, re-traiter le lot.\n\n"
            "Problème , trop de collisions (> 20 pourcent des IPP).\n"
            "Cause , melange de formats sources non-normalises. Solution , "
            "activer la normalisation IPP (par defaut oui) et re-traiter."
        ),
        faq=[
            ("Que se passe-t-il aux lignes dont la DDN est rejetee ?",
             "Elles sont exclues des exports sanitized, mais restent dans le "
             "MPI avec un flag 'rejected' pour tracabilite."),
            ("Puis-je annuler une résolution ?",
             "Oui, cliquer a nouveau sur la variante puis Retenir cette DDN "
             "pour changer d'avis. Chaque changement est logue."),
            ("Le mode anonymise peut-il être desactive ?",
             "Uniquement par un cadre DIM authentifie. Le mode par defaut est "
             "anonymise conformement a la politique du GHT."),
            ("Combien de temps sont conservees les collisions dans le MPI ?",
             "Tant que le MPI persiste , elles disparaissent au Réinitialiser le registre."),
        ],
        best_practices=(
            "1. Toujours traiter d'abord les cas a 3+ DDN manuellement , ils "
            "signalent souvent une vraie homonymie ou erreur d'admission.\n\n"
            "2. Documenter chaque résolution manuelle importante dans le cahier "
            "DIM papier , le log applicatif n'est pas suffisant pour l'audit ARS.\n\n"
            "3. Après résolution complete, lancer le Contrôle préalable DRUIDES (F3) pour "
            "valider l'absence de collisions residuelles.\n\n"
            "4. Une fois par trimestre, exporter la liste pseudonymisee des "
            "collisions pour analyse de tendance (evolution du taux d'erreur)."
        ),
        metrics=(
            "Indicateurs a suivre dans le temps ,\n\n"
            "- Taux de collisions mensuel , cible < 2 pourcent en regime "
            "nominal.\n"
            "- Ratio Auto-resolve vs manuel , typique 80/20.\n"
            "- Nombre de collisions a 3+ DDN , indicateur de qualité saisie "
            "cote CPage/DxCare.\n"
            "- Temps moyen de résolution manuelle , cible < 2 min par cas.\n"
            "- Recurrence IPP multi-sessions , signale une erreur systematique."
        ),
        references=(
            "HAS , Instruction DGOS/PF2 no 2019-116 (identitovigilance).\n"
            "ANS , Referentiel national d'identito-vigilance 2023.\n"
            "RGPD art. 9 , données de sante identifiantes.\n"
            "Journal d audit art. 30 RGPD , obligation de tracabilite.\n"
            "MPI (Master Patient Index) , concept , IHE-PIX."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════════
    # FEATURE 4 · PMSI PILOT CSV
    # ══════════════════════════════════════════════════════════════════════
    mk(
        title="PMSI Pilot CSV , exports normalises e-PMSI",
        category="Exports avancés",
        tagline="Produire les fichiers attendus par DRUIDES et BIQuery",
        purpose=(
            "Après traitement et résolution des collisions, le MPI doit être "
            "transmis a la plateforme nationale (DRUIDES, anciennement PIVOINE) "
            "et alimenter le tableau de bord interne BIQuery. Cette fonctionnalité produit "
            "les fichiers attendus dans les formats exacts requis.\n\n"
            "Sans cette etape, impossible de finaliser le cycle mensuel PMSI. "
            "Les erreurs de format a ce niveau generent des rejets DRUIDES, "
            "chaque rejet coute en moyenne 3 jours de retard."
        ),
        prerequisites=(
            "MPI traite via Sélection des fichiers + collisions résolues via Identitovigilance. "
            "Un warning s'affiche si des collisions ne sont pas résolues , "
            "l'export est possible mais non recommande.\n\n"
            "Un dossier cible accessible en ecriture , typiquement un partage "
            "réseau accessible au chef de pôle ou a l'ARS."
        ),
        access=(
            "Raccourci , Ctrl+4. L'onglet est grise tant qu'aucun MPI n'est "
            "charge. Une fois active, il propose deux types d'export distincts.\n\n"
            "L'onglet reste accessible après fermeture de l'application , le "
            "MPI SQLite persiste, les exports peuvent être relances sans re-scan."
        ),
        interface=(
            "Deux sections principales ,\n\n"
            "1. Export CSV normalise , CSV unique aggregant toutes les lignes "
            "du MPI avec colonnes standardisees (IPP, DDN, Sexe, Format, Annee, "
            "Fichier source, Ligne). Destine a BIQuery.\n\n"
            "2. Export .txt sanitized , reprise des fichiers sources originaux, "
            "filtres selon la résolution des collisions. Destine a DRUIDES.\n\n"
            "Chaque section a son bouton Exporter qui ouvre un dialog Enregistrer-"
            "Sous natif pour choisir le chemin."
        ),
        workflow_steps=[
            "Verifier au Tableau de bord que le MPI est complet et que le indicateur Collisions "
            "est a zero (ou justifie). Ouvrir PMSI Pilot CSV (Ctrl+4).",
            "Choisir le type d'export , CSV normalise pour BIQuery ou .txt "
            "sanitized pour DRUIDES. Cliquer Exporter , choisir le dossier cible. "
            "Le fichier est génère en quelques secondes.",
            "Pour DRUIDES, vérifier la structure du .txt génère avec Inspecteur "
            "Terminal (F2) sur une ligne échantillon. Puis téléverser sur la "
            "plateforme DRUIDES via le navigateur. En cas de rejet, revenir a "
            "Identitovigilance ou Contrôle préalable pour corriger.",
        ],
        options=(
            "Options d'export CSV normalise ,\n\n"
            "- Encodage , UTF-8 avec BOM (defaut, Excel FR compatible) ou sans BOM.\n"
            "- Separateur , point-virgule (defaut) ou virgule.\n"
            "- Inclure les lignes rejetees , non par defaut.\n"
            "- Filtrer par annee , si besoin d'un export partiel.\n\n"
            "Options d'export .txt sanitized ,\n\n"
            "- Conservation stricte des positions fixes , oui par defaut "
            "(obligatoire pour DRUIDES).\n"
            "- Un seul fichier de sortie ou un par fichier source , choix "
            "utilisateur.\n"
            "- Retirer les lignes rejetees , oui par defaut."
        ),
        integration=(
            "PMSI Pilot CSV consomme ,\n\n"
            "- Le MPI persiste en SQLite.\n"
            "- Les résolutions de collisions (table linked).\n"
            "- Les metadonnees de fichier source (pour le .txt sanitized).\n\n"
            "Il alimente ,\n\n"
            "- DRUIDES (téléversement manuel via navigateur) pour la transmission ARS.\n"
            "- BIQuery (ingestion automatique des CSV places dans un dossier "
            "partage surveille par un cron).\n"
            "- Rapports internes pour chef de pôle."
        ),
        usecase_1=(
            "Cas , fin de mois, transmission e-PMSI obligatoire avant le 15. Le "
            "TIM lance l'export .txt sanitized. Le fichier génère respecte les "
            "positions fixes RPS P05 (154 chars). Téléversement DRUIDES reussi du "
            "premier coup , gain de 2 jours par rapport a la méthode manuelle "
            "precedente."
        ),
        usecase_2=(
            "Cas , chef de pôle demande un extract BIQuery pour analyse de "
            "tendance sur 3 ans. Le TIM charge 36 lots mensuels, résout les "
            "collisions, exporte un CSV unique de 850 000 lignes. Depot dans "
            "le dossier BIQuery , ingestion automatique la nuit suivante, "
            "tableaux de bord mis à jour le lendemain matin."
        ),
        performance=(
            "Performances sur un MPI de 500 000 lignes ,\n\n"
            "- Export CSV normalise , 2 s (ecriture SSD).\n"
            "- Export .txt sanitized , 8 s (relecture des sources + filtrage).\n"
            "- Taille CSV génère , ~80 Mo.\n"
            "- Taille .txt sanitized , quasi identique aux sources (delta "
            "minime du aux lignes rejetees).\n\n"
            "Pour des MPI > 2 M lignes, envisager un export par annee pour "
            "eviter les delais > 30 s."
        ),
        security=(
            "Les exports contiennent des données nominatives , precautions ,\n\n"
            "- Dialog Enregistrer-Sous obligatoire , impossible d'exporter "
            "silencieusement vers un chemin par defaut.\n"
            "- Chemin de sortie loggue dans l'journal d audit art. 30 RGPD.\n"
            "- Validation du chemin , path traversal refuse, dossiers système "
            "proteges.\n"
            "- Option de pseudonymisation disponible (hash IPP) pour exports "
            "non-nominatifs.\n\n"
            "L'utilisateur est responsable du circuit aval , ne pas déposer "
            "sur cle USB non chiffree, respecter la charte IT GHT."
        ),
        troubleshooting=(
            "Problème , export CSV s'ouvre en Excel avec caractères illisibles.\n"
            "Cause , BOM manquant ou encodage mal choisi. Solution , re-exporter "
            "avec UTF-8 + BOM (defaut).\n\n"
            "Problème , DRUIDES rejette l'téléversement pour erreur de longueur de ligne.\n"
            "Cause , option Conservation positions desactivee. Solution , "
            "re-exporter avec l'option activee (defaut).\n\n"
            "Problème , fichier .txt génère vide.\n"
            "Cause , toutes les lignes rejetees par résolution. Solution , "
            "revoir les décisions en Identitovigilance, retenir plus de variantes."
        ),
        faq=[
            ("Puis-je exporter en Parquet ?",
             "Non encore , prevu pour V36. Utiliser CSV puis convertir en "
             "Parquet via script BIQuery."),
            ("Les exports sont-ils compresses ?",
             "Non par defaut. Utiliser 7-zip manuellement si besoin."),
            ("Puis-je re-exporter sans re-scanner ?",
             "Oui, le MPI persiste. Les exports sont idempotents tant que "
             "le MPI n'est pas réinitialisation."),
            ("Que faire si DRUIDES rejette 1 ligne sur 10 000 ?",
             "Ouvrir Inspecteur ligne par ligne sur la ligne rejetee, comprendre "
             "l'erreur, corriger a la source (CPage/DxCare) puis re-exporter."),
        ],
        best_practices=(
            "1. Toujours lancer Contrôle préalable DRUIDES (F3) avant un export , evite "
            "80 pourcent des rejets.\n\n"
            "2. Utiliser un chemin de sortie standardise , "
            "D:/DIM/Exports/YYYY/MM pour faciliter l'audit et les reprises.\n\n"
            "3. Conserver les exports 12 mois minimum en local avant archivage "
            "(tracabilite).\n\n"
            "4. Après téléversement DRUIDES reussi, tagger le lot dans le cahier DIM "
            "pour eviter les doubles transmissions."
        ),
        metrics=(
            "Metriques d'export a suivre ,\n\n"
            "- Taille CSV , ~150 octets par ligne MPI.\n"
            "- Taille .txt sanitized , 154 chars + CR/LF = 156 octets par ligne RPS.\n"
            "- Taux de rejet DRUIDES , cible < 0.5 pourcent des lignes.\n"
            "- Delai CSV -> BIQuery , cible < 24 h.\n"
            "- Duree moyenne export , cible < 10 s pour un lot mensuel."
        ),
        references=(
            "DRUIDES , plateforme ATIH de transmission, remplace PIVOINE 2025.\n"
            "BIQuery , datawarehouse interne GHT Sud Paris.\n"
            "e-PMSI , portail national des transmissions ATIH.\n"
            "Format RPS P05 , cahier des charges ATIH 2024.\n"
            "Journal d audit art. 30 RGPD , specs ANS 2023."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════════
    # FEATURE 5 · INSPECTOR TERMINAL + PREFLIGHT DRUIDES
    # ══════════════════════════════════════════════════════════════════════
    mk(
        title="Inspecteur ligne par ligne et Contrôle préalable DRUIDES",
        category="Exports avancés",
        tagline="Diagnostiquer ligne par ligne et valider avant téléversement",
        purpose=(
            "Deux outils jumeles pour traquer les erreurs avant qu'elles "
            "n'atteignent DRUIDES , Inspecteur ligne par ligne decompose ligne par "
            "ligne les fichiers ATIH, Contrôle préalable applique 15 validateurs "
            "automatiques sur l'ensemble du lot.\n\n"
            "Chaque rejet DRUIDES coute 2-3 jours de retard. Ces deux outils "
            "combines divisent par 10 le taux de rejet moyen par rapport a "
            "une transmission a l'aveugle."
        ),
        prerequisites=(
            "Inspecteur ligne par ligne , un fichier ATIH identifie dans Sélection des fichiers. "
            "Clic sur la ligne du fichier, touche F2, ou menu contextuel.\n\n"
            "Contrôle préalable DRUIDES , un MPI traite + au moins un fichier source "
            "disponible. Touche F3 depuis n'importe quelle vue."
        ),
        access=(
            "Inspecteur ligne par ligne , touche F2 depuis Sélection des fichiers après avoir "
            "sélectionne un fichier, ou clic direct sur une ligne du tableau.\n\n"
            "Contrôle préalable DRUIDES , touche F3 depuis n'importe ou, y compris "
            "Tableau de bord. L'ouverture en overlay plein-ecran."
        ),
        interface=(
            "Inspecteur ligne par ligne ,\n\n"
            "- Header , nom du fichier, format détecte, longueur de ligne, "
            "total de lignes.\n"
            "- Input numero de ligne + bouton Inspecter.\n"
            "- Zone de decomposition , tableau champ par champ avec positions "
            "(debut, fin), valeur brute, valeur decodee, statut de validation.\n"
            "- Panneau d'erreurs , erreurs détectées avec severite et "
            "suggestion de correction.\n\n"
            "Contrôle préalable DRUIDES ,\n\n"
            "- 15 validateurs groupes en 4 catégories (structure, coherence, "
            "coherence inter-fichier, metier).\n"
            "- Progression globale + par validateur.\n"
            "- Rapport final , erreurs classees par severite + export PDF."
        ),
        workflow_steps=[
            "Après traitement du lot, lancer Contrôle préalable DRUIDES (F3). "
            "L'analyse prend 3-15 s selon la taille. Les erreurs bloquantes "
            "rouge doivent être corrigees avant téléversement.",
            "Pour chaque erreur, cliquer le lien 'Voir dans l'inspecteur'. "
            "L'inspecteur s'ouvre sur la ligne fautive. Analyser le champ en "
            "cause, vérifier s'il s'agit d'une erreur source (CPage/DxCare) ou "
            "d'une erreur de traitement.",
            "Si erreur source , signaler au service qui a produit le fichier "
            "pour correction. Si erreur de traitement , ouvrir un issue GitHub. "
            "Relancer Contrôle préalable après correction pour confirmer.",
        ],
        options=(
            "Inspecteur ligne par ligne ,\n\n"
            "- Anonymisation auto après 3 lignes inspectees (pseudonymisation).\n"
            "- Copie champ par champ interdite (anti-fuite).\n"
            "- Navigation precedent/suivant sur les erreurs du fichier.\n\n"
            "Contrôle préalable DRUIDES ,\n\n"
            "- Severite minimale affichee , bloquante (defaut), warning, info.\n"
            "- Categories a activer/desactiver (si besoin de run cible).\n"
            "- Export du rapport PDF (via fpdf2).\n"
            "- Auto-run au chargement d'un nouveau lot (optionnel)."
        ),
        integration=(
            "Inspecteur et Contrôle préalable se completent ,\n\n"
            "- Contrôle préalable détecte les erreurs, Inspecteur les analyse en détail.\n"
            "- Inspecteur peut être ouvert depuis Sélection des fichiers, Identitovigilance "
            "(sur une ligne en collision), ou le rapport Preflight.\n"
            "- Contrôle préalable lit le MPI + les fichiers sources pour des "
            "validations cross-fichier (ex. chainage VID-HOSP).\n\n"
            "Les deux alimentent l'journal d audit art. 30 RGPD avec les inspections "
            "effectuees."
        ),
        usecase_1=(
            "Cas , DRUIDES a rejete le lot precedent avec erreur 'FINESS "
            "incoherent ligne 2341'. Le TIM ouvre Contrôle préalable , l'erreur est "
            "immediatement détectée. Clic 'Voir dans l'inspecteur' , ligne 2341 "
            "a 940000001 au lieu de 940110018 (Fondation Vallee). Correction "
            "cote CPage, re-traitement, re-export, téléversement reussi."
        ),
        usecase_2=(
            "Cas , nouveau TIM formation. Il lance Contrôle préalable sur un lot de "
            "test, voit 38 warnings. Il parcourt chacun dans Inspecteur pour "
            "comprendre les règles ATIH. En 2 h, il maitrise les formats RPS, "
            "RAA, FICHSUP-PSY et leurs validations. Formation accelere de 3j a 1j."
        ),
        performance=(
            "Inspecteur ligne par ligne ,\n"
            "- Ouverture d'un fichier , < 200 ms (lazy load).\n"
            "- Inspection d'une ligne , < 50 ms.\n"
            "- Validation de 15 règles sur une ligne , < 30 ms.\n\n"
            "Contrôle préalable DRUIDES ,\n"
            "- Validation de 1000 lignes , 450 ms.\n"
            "- Validation d'un lot mensuel (10 fichiers, 150 000 lignes) , 12 s.\n"
            "- Export du rapport PDF , 2-4 s."
        ),
        security=(
            "Inspecteur expose potentiellement des données nominatives ,\n\n"
            "- Pseudonymisation automatique après 3 lignes inspectees.\n"
            "- Copy clipboard des champs IPP/DDN desactivee.\n"
            "- Chaque ouverture loggue IPP + fichier + heure.\n"
            "- En mode audit (authentifie cadre DIM), les données brutes sont "
            "accessibles mais l'journal d audit est imprimable.\n\n"
            "Contrôle préalable ne remonte que des metadonnees (numero de ligne, type "
            "d'erreur) , pas d'IPP dans le rapport PDF."
        ),
        troubleshooting=(
            "Problème , Inspecteur n'ouvre pas un fichier.\n"
            "Cause , format INCONNU ou permissions refusees. Solution , "
            "verifier l'identification dans Sélection des fichiers d'abord.\n\n"
            "Problème , Contrôle préalable bloque a un validateur spécifique (> 2 min).\n"
            "Cause , fichier corrompu en cours de validation. Solution , "
            "annuler, ouvrir le fichier dans Inspecteur pour identifier la ligne "
            "problematique.\n\n"
            "Problème , erreur 'Position invalide' dans Inspecteur.\n"
            "Cause , format source non standard (ancien P04 2021). Solution , "
            "forcer le format via le menu deroulant en haut de l'inspecteur."
        ),
        faq=[
            ("Puis-je inspecter plusieurs lignes simultanement ?",
             "Non, une ligne a la fois. Pour plusieurs lignes, utiliser "
             "Contrôle préalable qui scanne tout."),
            ("Contrôle préalable peut-il tourner automatiquement ?",
             "Oui, option 'Auto-run au chargement' dans les préférences."),
            ("Les rapports Contrôle préalable sont-ils archives ?",
             "Seulement si exportes en PDF. Sinon, regénérés a chaque run."),
            ("Que signifie une erreur 'ERR-DIntelligence artificielleG-ABSENT' ?",
             "Le diagnostic principal (DP) est manquant. CimSuggester Intelligence artificielle peut "
             "proposer un DP plausible (F2 > Suggestion Intelligence artificielle)."),
        ],
        best_practices=(
            "1. Toujours lancer Contrôle préalable avant un export , gain de temps "
            "enorme sur les rejets DRUIDES.\n\n"
            "2. Utiliser Inspecteur comme outil de formation , chaque nouveau "
            "TIM doit en maitriser l'usage en semaine 1.\n\n"
            "3. Documenter les erreurs recurrentes dans un cahier partage , "
            "elles signalent souvent des defauts de saisie a l'amont.\n\n"
            "4. Exporter le rapport Contrôle préalable en PDF avant chaque téléversement "
            "DRUIDES , tracabilite pour audit ARS."
        ),
        metrics=(
            "Metriques a suivre ,\n\n"
            "- Taux d'erreur Contrôle préalable , cible < 1 pourcent des lignes.\n"
            "- Temps moyen d'inspection d'une ligne , 3-5 min en regime nominal.\n"
            "- Taux de rejet DRUIDES post-Contrôle préalable , cible < 0.1 pourcent.\n"
            "- Nombre de rapports Contrôle préalable archives par mois , cible = nombre "
            "de lots transmis.\n"
            "- Distribution des catégories d'erreurs , alerte si glissement."
        ),
        references=(
            "Cahier des charges DRUIDES 2025 , 53 règles de validation.\n"
            "15 validateurs Core , FINESS, IPP, DDN, CIM-10, mode legal, "
            "secteur ARS, chainage, duplicatas, orphelins, cohérence annee, "
            "format RPS, Fichsup, Ficum, Anonymisation, syntaxe.\n"
            "CimSuggester Intelligence artificielle , fonctionnalité V35 , fournisseur LLM configurable (API nuage informatique ou Ollama local).\n"
            "Règles CIM-10 FR , ATIH MAM CIM-10 2024."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════════
    # FEATURE 6 · DASHBOARD LIVE
    # ══════════════════════════════════════════════════════════════════════
    mk(
        title="Tableau de bord en direct , graphes temps reel",
        category="Traitement par lots",
        tagline="4 graphes Chart.js + 6 indicateur pour piloter le MPI",
        purpose=(
            "Le Tableau de bord en direct est un overlay plein-ecran qui affiche en temps "
            "reel 4 graphes et 6 indicateur derives du MPI. Il se met à jour sans "
            "rechargement a chaque nouveau traitement , ideal pour monitoring "
            "pendant une session de traitement intensive ou projection en "
            "reunion DIM.\n\n"
            "Différence avec le Tableau de bord (Ctrl+1) , Tableau de bord est statique "
            "(indicateur calculés au chargement), Tableau de bord en direct est dynamique (MAJ "
            "continue toutes les 2 secondes)."
        ),
        prerequisites=(
            "MPI non vide. Si aucun traitement n'a ete fait, le Tableau de bord "
            "En direct affiche un etat vide avec call-to-action vers Sélection des fichiers.\n\n"
            "Recommande , 2 ecrans , Tableau de bord en direct en plein-ecran sur le "
            "secondaire, travail principal sur le primaire."
        ),
        access=(
            "Touche F4 depuis n'importe ou. L'overlay apparait en plein-ecran, "
            "masquant la barre laterale. Echap ferme l'overlay.\n\n"
            "Accessible aussi depuis le Tableau de bord principal , bouton Tableau de bord "
            "En direct en haut a droite."
        ),
        interface=(
            "Layout 2x2 + bande indicateur ,\n\n"
            "- Haut gauche , evolution mensuelle des patients actifs (line chart).\n"
            "- Haut droit , repartition par secteur ARS (pie chart couleurs "
            "officielles G/I/D/P/Z).\n"
            "- Bas gauche , Top 10 UM les plus actives (bar horizontal).\n"
            "- Bas droit , heatmap des collisions par mois (matrix chart).\n\n"
            "En bande inférieure, 6 indicateur , file active, DMS, taux reconduction, "
            "taux collision résolu, UM sans activité, volume pediatrique."
        ),
        workflow_steps=[
            "Appuyer F4. L'overlay s'affiche. Les 4 graphes se rendent en "
            "moins d'une seconde. Les indicateur sont calculés en parallele.",
            "Pendant un traitement en arriere-plan (Sélection des fichiers), les graphes "
            "se mettent à jour automatiquement toutes les 2 s. Utile pour "
            "observer la progrèssion et détecter les anomalies immediatement.",
            "Pour présentation reunion , cliquer le bouton Exporter , un PDF "
            "paysage 2 pages est génère avec les 4 graphes + les indicateurs. Duree "
            "de génération , 2-4 s.",
        ],
        options=(
            "Options disponibles ,\n\n"
            "- Fréquence de MAJ , 2 s (defaut), 5 s, 10 s, ou manuelle.\n"
            "- Plage temporelle affichee , 12 mois, 24 mois, 36 mois, ou tout.\n"
            "- Couleurs des graphes , palette officielle (defaut) ou alternative "
            "daltoniens.\n"
            "- Animation transitions , on/off (off recommande sur vieux postes).\n\n"
            "Export PDF paysage uniquement , pas de portrait (les graphes "
            "Chart.js perdent en lisibilite)."
        ),
        integration=(
            "Tableau de bord en direct consomme ,\n\n"
            "- Le MPI SQLite (requêtes agregees).\n"
            "- La structure chargee (pour repartition secteur ARS).\n"
            "- L'historique de traitements (pour evolution mensuelle).\n\n"
            "Il alimente ,\n\n"
            "- PDF d'export pour reunion.\n"
            "- Notifications push (optionnel) en cas de seuil d'alerte franchi."
        ),
        usecase_1=(
            "Cas , reunion mensuelle DIM. Le responsable projette Tableau de bord "
            "En direct en plein-ecran. Les 4 graphes suscitent la discussion sur "
            "l'evolution de la file active, la repartition G/I/D/P, les UM "
            "les plus actives. En 15 min, les décisions sont prises sur les "
            "priorites du mois suivant."
        ),
        usecase_2=(
            "Cas , monitoring d'un gros traitement (500 000 lignes). Le TIM "
            "laisse Tableau de bord en direct ouvert sur le 2e ecran pendant le traitement "
            "de 20 min. Il observe que la repartition PSY diminue anormalement "
            "a mi-parcours , il arrête le traitement, identifie un fichier "
            "corrompu, le remplace, relance , evite une analyse biaisee."
        ),
        performance=(
            "Performance Chart.js sur poste standard ,\n\n"
            "- Rendu initial des 4 graphes , 380 ms.\n"
            "- MAJ sur nouvelles données , 120 ms.\n"
            "- Requetes SQL agregees , 40 ms en moyenne.\n"
            "- Export PDF paysage , 3 s.\n\n"
            "Attention , sur des MPI > 5 M lignes, augmenter la fréquence de "
            "MAJ a 10 s ou manuel pour eviter la saturation."
        ),
        security=(
            "Le Tableau de bord en direct n'expose jamais de données nominatives , "
            "uniquement des agregats anonymes (counts, sommes, moyennes).\n\n"
            "Le PDF exporte peut être partage sans restriction RGPD , aucun "
            "IPP, DDN, ou identifiant indirect.\n\n"
            "Les animations et transitions n'exposent pas de données , "
            "purement visuelles. Journal d audit , chaque ouverture F4 est logguee."
        ),
        troubleshooting=(
            "Problème , graphes ne se mettent pas à jour.\n"
            "Cause , MPI vide ou traitement non termine. Solution , vérifier "
            "au Tableau de bord principal que les indicateur sont peuples.\n\n"
            "Problème , Chart.js affiche 'No data'.\n"
            "Cause , filtrage trop restrictif (annee sans données). Solution , "
            "elargir la plage temporelle.\n\n"
            "Problème , export PDF échoue.\n"
            "Cause , fpdf2 non installé en mode source, ou playwright manquant. "
            "Solution , `pip install fpdf2 playwright && playwright install chromium`."
        ),
        faq=[
            ("Puis-je personnaliser les 4 graphes ?",
             "Pas encore , V36 prevoit un selecteur de type (pie, line, bar, "
             "area)."),
            ("Tableau de bord en direct fonctionne-t-il sans Chart.js ?",
             "Non, Chart.js est embarqué dans l'interface graphique. Disponible "
             "hors ligne."),
            ("Puis-je projeter en mode dark pour présentation ?",
             "Oui, le theme suit celui de l'app. Utiliser Ctrl+D pour "
             "basculer."),
            ("Les graphes s'impriment-ils correctement ?",
             "Oui, couleurs preservees. Preferer le PDF paysage génère plutot "
             "qu'imprimer directement depuis l'overlay."),
        ],
        best_practices=(
            "1. Garder Tableau de bord en direct sur 2e ecran pendant les traitements "
            "importants , détection precoce d'anomalies.\n\n"
            "2. Exporter le PDF avant chaque reunion mensuelle , archive des "
            "decisions prises avec les données visibles.\n\n"
            "3. Adapter la fréquence de MAJ au contexte , 2 s pendant un "
            "traitement, manuel pendant une présentation.\n\n"
            "4. Comparer mois N vs N-1 via deux onglets d'export PDF cote "
            "a cote."
        ),
        metrics=(
            "indicateur affiches ,\n\n"
            "- File active , patients distincts sur la période, cible croissante\n"
            "  en CHS en developpement.\n"
            "- DMS (duree moyenne sejour) , 30-45 j typique en PSY adulte, "
            "15-25 j en pediatrie.\n"
            "- Taux de reconduction , > 40 pourcent signale une chronicite.\n"
            "- Taux de collision résolu , cible 100 pourcent avant export.\n"
            "- UM sans activité , signale des fermetures a acter.\n"
            "- Volume pediatrique , typique 20-30 pourcent en Fondation Vallee."
        ),
        references=(
            "Chart.js v4 , https://www.chartjs.org\n"
            "Palette secteurs ARS , instruction DGOS 2019.\n"
            "DMS , indicateur ANAP 2023.\n"
            "File active , definition HAS 2022.\n"
            "Reunion mensuelle DIM , charte GHT Sud Paris."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════════
    # FEATURE 7 · STRUCTURE + EXPORT PDF
    # ══════════════════════════════════════════════════════════════════════
    mk(
        title="Structure , arborescence polaire et export PDF",
        category="Exports avancés",
        tagline="Visualiser la hierarchie Pôle-Secteur-UM",
        purpose=(
            "Cette vue charge un fichier structure (CSV/TSV) decrivant la "
            "hierarchie de l'etablissement , Territoire > Etablissement > "
            "Pôle > Secteur > UM. Elle rend un organigramme interactif et "
            "exporte un PDF multi-pages impriable.\n\n"
            "Indispensable pour , valider que la nomenclature UM est "
            "coherente avec les fichiers ATIH, générer l'annexe du rapport "
            "annuel ARS, onboarder un nouveau TIM sur la structure du pôle."
        ),
        prerequisites=(
            "Un fichier structure au format CSV/TSV. Exemples de colonnes "
            "acceptees , LEVEL, CODE, PARENT, LABEL. Si les headers ne "
            "correspondent pas, le parser tente une détection heuristique.\n\n"
            "Alternative , fichier plat indente (2 ou 4 espaces = 1 niveau). "
            "Utile pour des structures saisies a la main dans un editeur "
            "texte."
        ),
        access=(
            "Raccourci , Ctrl+6. La vue s'ouvre sur un etat vide avec un "
            "bouton central Sélectionner le fichier structure.\n\n"
            "Une fois charge, la structure reste en session , passer sur un "
            "autre onglet et revenir preserve l'affichage."
        ),
        interface=(
            "3 zones ,\n\n"
            "1. En-tete , stat cards (noeuds, racines, profondeur, fichier) + "
            "chips par niveau + toolbar zoom/ajuster/export PDF.\n\n"
            "2. Viewport organigramme , rendu HTML+CSS pur (pas de SVG), "
            "pôle au centre, secteurs en couronne, UM en feuilles. Zoom "
            "molette + Ctrl, boutons +/-, ajuster.\n\n"
            "3. Section Analyse d'activité par UM (nouvelle V35) , zone de dépôt "
            "pour RPS/RAA + resultats avec UM sans activité."
        ),
        workflow_steps=[
            "Cliquer Sélectionner le fichier structure , dialog natif. "
            "Choisir un CSV/TSV. Le parser analyse et construit l'arbre en "
            "moins de 1 seconde.",
            "L'organigramme s'affiche, auto-ajuste au viewport. Zoom "
            "molette Ctrl pour voir les détails. Chaque noeud porte code, "
            "libelle, badge type ARS (G/I/D/P/Z).",
            "Deposer un ou plusieurs fichiers RPS/RAA dans la zone de dépôt "
            "pour lancer l'analyse d'activité , les UM sans occurrence sont "
            "signalees en rouge avec pastille clignotante.",
        ],
        options=(
            "Options de rendu ,\n\n"
            "- Zoom , 30-200 pourcent, manuel ou ajuster.\n"
            "- Rendu en dark mode , respecte le theme global.\n"
            "- Badges de type ARS , toujours affiches (couleurs officielles).\n"
            "- Indent affichage , compact ou aere.\n\n"
            "Options d'export PDF ,\n\n"
            "- Multi-pages , 1 page vue globale + 1 page par pôle.\n"
            "- Scaling auto pour tenir en A4.\n"
            "- Legende par defaut (5 types ARS).\n"
            "- Orientation portrait (defaut) ou paysage."
        ),
        integration=(
            "Structure consomme ,\n\n"
            "- Fichier CSV/TSV local.\n"
            "- Palette couleurs partagee avec Tableau de bord en direct.\n\n"
            "Structure alimente ,\n\n"
            "- Analyse d'activité par UM , besoin de la liste des UM pour "
            "détecter celles sans activité.\n"
            "- Export PDF organigramme , consommable par chef de pôle, ARS, "
            "audit.\n"
            "- Tableau de bord en direct , palette secteurs ARS pour pie chart."
        ),
        usecase_1=(
            "Cas , chef de pôle demande l'organigramme à jour de Fondation "
            "Vallee pour son rapport annuel. Le TIM charge le fichier "
            "structure, exporte le PDF , 3 pages (régionale + pôle enfants "
            "+ pôle adolescents). Envoi par email, valide sans retouche."
        ),
        usecase_2=(
            "Cas , audit ARS, vérification de la nomenclature. L'auditeur "
            "demande quelles UM ont de l'activité en 2024. Le TIM charge la "
            "structure + les 12 RPS mensuels 2024. En 30 s, la liste des "
            "UM sans activité apparait , 4 UM jamais utilisees, dont 2 "
            "officiellement fermees. Reponse factuelle a l'auditeur, qui "
            "note l'outil dans son rapport."
        ),
        performance=(
            "Performances ,\n\n"
            "- Parsing d'un CSV de 200 noeuds , 80 ms.\n"
            "- Rendu HTML+CSS initial , 200 ms.\n"
            "- Zoom + transform , 16 ms (60 fps).\n"
            "- Export PDF 3 pages , 1.2 s.\n\n"
            "Pour très grandes structures (> 1000 noeuds) , la profondeur "
            "affichee est limitee a 6 niveaux par defaut pour lisibilite, "
            "les niveaux inférieurs sont collapsibles."
        ),
        security=(
            "La structure ne contient pas de données patient , pas de "
            "precautions RGPD spécifiques.\n\n"
            "L'export PDF peut être partage librement (pas d'identifiants "
            "nominatifs). Le fichier structure lui-même est public (publie "
            "dans le rapport annuel).\n\n"
            "L'analyse d'activité par UM ne rapporte que des comptages "
            "agreges par UM , aucun IPP dans le rendu."
        ),
        troubleshooting=(
            "Problème , structure affiche 0 noeud après sélection.\n"
            "Cause , format non reconnu (header incorrect). Solution , "
            "renommer les colonnes LEVEL/CODE/PARENT/LABEL ou utiliser le "
            "format indente.\n\n"
            "Problème , organigramme deborde du viewport.\n"
            "Cause , structure très large. Solution , bouton Ajuster en haut "
            "a droite.\n\n"
            "Problème , l'export PDF échoue.\n"
            "Cause , composant PDF manquant sur le poste. Solution , "
            "contacter le support pour reinstallation "
            "(adam.beloucif@psysudparis.fr)."
        ),
        faq=[
            ("Puis-je editer la structure dans l'app ?",
             "Non, c'est une vue de consultation. Editer le CSV avec Excel "
             "puis recharger."),
            ("Combien de niveaux de profondeur sont supportes ?",
             "Jusqu'a 10, au-dela l'affichage devient illisible."),
            ("Le PDF est-il vectoriel ?",
             "Oui, pas de raster. Qualité impression optimale même agrandi."),
            ("Puis-je exporter en SVG ?",
             "Pas encore. L'organigramme est HTML+CSS pur, pas de SVG."),
        ],
        best_practices=(
            "1. Maintenir le fichier structure en version controlee (git). "
            "Chaque modification tracee.\n\n"
            "2. Mettre à jour la structure des qu'une UM ouvre ou ferme "
            "officiellement , l'analyse d'activité en depend.\n\n"
            "3. Exporter le PDF organigramme trimestriellement pour archive.\n\n"
            "4. Partager le fichier structure avec le chef de pôle en amont "
            "du rapport annuel pour validation."
        ),
        metrics=(
            "Metriques a suivre ,\n\n"
            "- Nombre total d'UM , typique 40-80 pour un CHS.\n"
            "- Profondeur max , 4-5 niveaux standard.\n"
            "- Taux d'UM sans activité , cible 0 pourcent, investiguer sinon.\n"
            "- Fréquence de mise à jour structure , trimestrielle minimum.\n"
            "- Couverture type ARS , doit englober G+I+D+P+Z selon specialite."
        ),
        references=(
            "Nomenclature ARS , circulaire DGOS 2019-256.\n"
            "Convention GHT Sud Paris , structure polaire 2016.\n"
            "Rapport annuel ARS , format type 2024.\n"
            "Types ARS , G/I/D/P/Z definis en 1988 (loi psychiatrie).\n"
            "Sectorisation , code de la sante publique art. R3222-5."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════════
    # FEATURE 8 · ANALYSE D'ACTIVITE PAR UM (LA NOUVELLE FEATURE)
    # ══════════════════════════════════════════════════════════════════════
    mk(
        title="Analyse d'activité par UM , détection des UM dormantes",
        category="Exports avancés",
        tagline="Croiser structure + RPS/RAA pour reperer les unites inactives",
        purpose=(
            "Nouveaute V35. Une UM declaree dans la structure mais jamais "
            "presente dans les fichiers ATIH sur une période donnée est une "
            "anomalie , soit elle a ferme et la structure n'a pas ete mise "
            "a jour, soit un recueil manque.\n\n"
            "Cette fonctionnalité détecte automatiquement ces UM dormantes en "
            "croisant la structure chargee avec les fichiers RPS/RAA "
            "déposés. Elle evite que des UM fantomes ne restent dans les "
            "referentiels pendant des annees."
        ),
        prerequisites=(
            "Un fichier structure charge via la vue Structure (Ctrl+6). "
            "Au moins une UM doit être détectée dans la hierarchie (noeud "
            "feuille ou niveau UM explicite).\n\n"
            "Un ou plusieurs fichiers RPS, RAA, RPSA, R3A ou EDGAR , format "
            "texte latin-1 a largeur fixe. Noms conseillees avec date "
            "(RPS_202410.txt) pour détection automatique de la période."
        ),
        access=(
            "Accessible uniquement depuis la vue Structure (Ctrl+6) , "
            "apparait comme une section 'Analyse d'activité par UM' sous "
            "l'organigramme, une fois le fichier structure charge.\n\n"
            "Pas de raccourci dedie , l'analyse n'a de sens qu'avec une "
            "structure charge en contexte."
        ),
        interface=(
            "3 zones ,\n\n"
            "1. Header , titre, description, bouton réinitialisation.\n\n"
            "2. Drop zone centrale , zone de drop HTML5 accessible clavier "
            "(Tab, Entree). Support glisser-déposer ou clic ouvre dialog.\n\n"
            "3. Zone de progrèssion + resultats ,\n"
            "   - 3 stat cards (UM actives, sans activité, couverture).\n"
            "   - 2 jauges (couverture active + sans activité).\n"
            "   - Liste des fichiers analyses avec format détecte.\n"
            "   - Liste groupee par pôle/secteur des UM inactives.\n"
            "   - Bouton 'Exporter CSV' pour la liste inactive.\n"
            "   - Details collapsible , Top 10 UM les plus actives."
        ),
        workflow_steps=[
            "Charger un fichier structure via Ctrl+6. Parcourir "
            "l'organigramme pour valider que toutes les UM attendues sont "
            "bien presentes. Descendre a la section Analyse d'activité.",
            "Glisser-déposer un ou plusieurs fichiers RPS/RAA dans la drop "
            "zone, ou cliquer pour ouvrir le dialog. Multi-fichiers supporte. "
            "Le traitement est asynchrone (chunks 5000 lignes) pour ne pas "
            "geler l'interface.",
            "Lire les resultats , les UM en rouge avec pastille clignotante "
            "sur l'arbre sont celles sans activité. Exporter la liste CSV "
            "pour la transmettre au chef de pôle. Si plusieurs UM "
            "inactives font partie du même secteur, investiguer en priorité.",
        ],
        options=(
            "Options ,\n\n"
            "- Nombre de fichiers simultanes , illimite en theorie, recommande "
            "< 20 pour lisibilite.\n\n"
            "- Auto-détection format , par longueur de ligne (154 c = RPS, "
            "96 c = RAA, etc.). Variantes anciennes supportees (P04 2021).\n\n"
            "- Export CSV , UTF-8 avec BOM pour Excel FR. Separateur ;.\n"
            "- Badge arbre , toggle on/off via Settings (on par defaut).\n\n"
            "Pas de parametrage du chunking , 5000 lignes optimal pour "
            "l'equilibre perf/reactivite UI."
        ),
        integration=(
            "Consommateurs ,\n\n"
            "- Structure (Ctrl+6) , fournit la liste des UM.\n"
            "- Sélection des fichiers , fournit indirectement les fichiers (copie possible).\n\n"
            "Producteurs ,\n\n"
            "- CSV exporte consommable par Excel, LibreOffice, Python, BIQuery.\n"
            "- Badges sur l'arbre , visuels uniquement, pas de persistance.\n"
            "- Statut affiche , information transitoire, disparait au réinitialisation.\n\n"
            "Cette fonctionnalité est totalement côté interface graphique , aucun appel au "
            "bridge C#."
        ),
        usecase_1=(
            "Cas , audit trimestriel. Le chef de pôle veut savoir quelles UM "
            "n'ont eu aucune activité au T3 2024. Le TIM charge la structure, "
            "dépose les 3 fichiers RPS mensuels (juillet, août, septembre). "
            "En 4 s, 5 UM apparaissent en rouge. Une est l'UHSA qui n'a "
            "pas encore ouvert, 4 sont des CATTP officiellement fermees "
            "mais toujours dans le referentiel. Le TIM met à jour la "
            "structure, le chef de pôle valide."
        ),
        usecase_2=(
            "Cas , contrôle qualité avant transmission ARS. Le TIM suspecte "
            "un oubli de RAA dans le lot du mois. Il charge la structure + "
            "le RPS + le RAA. Le RAA revele 8 UM inactives alors qu'elles "
            "apparaissent dans le RPS. Vérification , le fichier RAA de "
            "l'UM CMP Enfants est manquant. Recupere aupres du service, "
            "ajoute au lot, re-traite , 0 UM inactive incongrue. Transmission "
            "DRUIDES complete."
        ),
        performance=(
            "Performance sur 200 codes UM + 120 000 lignes RAA ,\n\n"
            "- Lecture fichier (FileReader) , 180 ms.\n"
            "- Parsing chunks async 5000 lignes , 2-4 s total, UI jamais "
            "gelee grace au yield setTimeout 0 entre chunks.\n"
            "- Rendu resultats , 150 ms.\n"
            "- Export CSV , 50 ms.\n\n"
            "Au-dela de 500 000 lignes par fichier, envisager un Web Worker "
            "(prévu V36) pour déplacer l'analyse hors du fil principal. "
            "Pour l'instant, les lots mensuels (< 150 000 lignes) sont "
            "traites en quelques secondes sans gel."
        ),
        security=(
            "Traitement 100 pourcent local dans le navigateur WebView2 , "
            "aucun envoi vers le serveur, aucune persistance SQLite.\n\n"
            "Les fichiers déposés ne quittent pas la memoire du navigateur , "
            "ils sont libérés quand l'utilisateur clique Réinitialisation ou ferme "
            "l'app.\n\n"
            "Le CSV exporte contient uniquement codes UM et libelles , pas "
            "de données nominatives. Partageable sans restriction RGPD.\n\n"
            "Pas d'journal d audit spécifique , l'action est volontaire et "
            "visible, pas de risque de fuite."
        ),
        troubleshooting=(
            "Problème , 'Aucune UM detectable' dans l'alerte.\n"
            "Cause , le fichier structure ne contient pas de niveau UM "
            "explicite ni de feuilles. Solution , vérifier la colonne LEVEL "
            "ou la profondeur de l'arbre.\n\n"
            "Problème , toutes les UM apparaissent inactives.\n"
            "Cause , aucun code UM ne correspond , probable desynchronisation "
            "entre nomenclature structure et fichiers ATIH. Solution , "
            "verifier les codes (ex. 4001 vs 94I01 premier caractère).\n\n"
            "Problème , export CSV s'ouvre en Excel avec colonnes fusionnees.\n"
            "Cause , BOM manquant ou mauvais separateur. Solution , utiliser "
            "Données > Depuis du texte dans Excel pour forcer l'analyse."
        ),
        faq=[
            ("Puis-je analyser des FICHSUP-PSY ?",
             "Pas encore , V35 couvre RPS/RAA/RPSA/R3A/EDGAR. FICHSUP-PSY "
             "arrivera en V36 avec analyse spécifique."),
            ("La période est-elle toujours détectée correctement ?",
             "Si les fichiers sont nommees AAAAMM ou MMAAAA, oui. Sinon, "
             "l'alerte 'période non détectée' s'affiche , renommer pour "
             "benefice de la détection."),
            ("Puis-je analyser des UM d'autres etablissements ?",
             "Oui, charger le fichier structure de l'etablissement concerne. "
             "L'outil est generique."),
            ("Combien de fichiers puis-je déposer simultanement ?",
             "Illimite en theorie. Recommande < 20 pour eviter les pics RAM."),
        ],
        best_practices=(
            "1. Lancer l'analyse trimestriellement au minimum , détecte les "
            "UM qui se ferment silencieusement.\n\n"
            "2. Maintenir une correspondance stricte entre codes UM structure "
            "et codes UM dans les fichiers ATIH , sans cela, faux positifs.\n\n"
            "3. Après export CSV, partager avec le chef de pôle pour "
            "validation , il peut confirmer les fermetures officielles.\n\n"
            "4. Toujours combiner RPS + RAA pour une couverture complète , "
            "certaines UM ambulatoires n'apparaissent que dans RAA."
        ),
        metrics=(
            "Metriques cles ,\n\n"
            "- Taux de couverture d'activité , cible 100 pourcent en regime "
            "nominal, alerte < 95 pourcent.\n"
            "- Nombre d'UM inactives en moyenne , cible 0-2 par trimestre "
            "(turnover normal).\n"
            "- Duree moyenne d'analyse , cible < 10 s pour un lot mensuel.\n"
            "- Nombre de fichiers analyses par session , typique 3-12.\n"
            "- Taux de détection période automatique , cible > 90 pourcent "
            "(depend du nommage des fichiers)."
        ),
        references=(
            "Fonctionnalité V35 , conception Adam Beloucif, avril 2026.\n"
            "Algorithme de matching , regex alternance + Map counts.\n"
            "UX , zone de dépôt HTML5 + FileReader + chunks async setTimeout 0.\n"
            "Accessibilite , WCAG AA , tabindex + aria-label + keydown.\n"
            "Tests fonctionnels , 21 tests Node.js couvrant helpers + "
            "scenario complet."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════════
    # FEATURE 9 · IMPORT CSV + HTML to PDF
    # ══════════════════════════════════════════════════════════════════════
    mk(
        title="Import CSV externe et HTML vers PDF",
        category="Traitement par lots",
        tagline="Injecter des sources tiers et capturer les tableaux de bord",
        purpose=(
            "Deux fonctionnalites annexes souvent utilisees , Import CSV "
            "permet d'injecter dans le MPI des données issues de systèmes "
            "tiers (editeur logiciel, partenaire GHT) sous forme de CSV. "
            "HTML vers PDF convertit les tableaux de bord BIQuery ou Looker Studio "
            "sauvegardes en HTML vers un PDF imprimable pour archivage.\n\n"
            "Ces outils couvrent les cas limites , tout n'est pas ATIH dans "
            "le quotidien DIM, et les exports aux chefs de pôle passent "
            "souvent par PDF."
        ),
        prerequisites=(
            "Import CSV ,\n"
            "- Un CSV avec colonnes IPP, DDN au minimum. Separateur auto-"
            "détecte (comma, semi-colon, tab). Encodage UTF-8 ou latin-1.\n\n"
            "HTML vers PDF ,\n"
            "- Un fichier fichier HTML local (pas d'URL). Les tableaux de bord enregistrés via "
            "Ctrl+S dans le navigateur sont compatibles.\n"
            "- playwright-chromium installé (mode développement) ou fpdf2 seul (solution de repli)."
        ),
        access=(
            "Import CSV , Ctrl+5.\n\n"
            "HTML vers PDF , pas de raccourci, onglet dedie dans la barre "
            "laterale (section Outils)."
        ),
        interface=(
            "Import CSV ,\n"
            "- Bouton Sélectionner CSV , dialog natif.\n"
            "- Apercu des 100 premieres lignes.\n"
            "- Détection auto separateur, encodage, colonnes.\n"
            "- Bouton Importer , choix Fusion (ajouter au MPI existant) ou "
            "Remplacement.\n\n"
            "HTML vers PDF ,\n"
            "- Zone de drop pour HTML.\n"
            "- Bouton Sélectionner HTML.\n"
            "- Options , orientation paysage, nettoyage tableau de bord.\n"
            "- Bouton Convertir , dialog Enregistrer-Sous pour PDF cible."
        ),
        workflow_steps=[
            "Pour un Import CSV , preparer le CSV source (Excel > "
            "Enregistrer-sous > CSV). Ouvrir Ctrl+5, sélectionner le fichier, "
            "valider l'apercu, choisir Fusion ou Remplacement, importer.",
            "Pour HTML vers PDF , depuis BIQuery, Ctrl+S > page web complète, "
            "sauver en local. Ouvrir l'onglet HTML vers PDF dans Sovereign OS, "
            "déposer le HTML, choisir paysage + nettoyage tableau de bord, convertir.",
            "Verifier le resultat , MPI enrichi pour l'import, PDF ouvert "
            "en visualisation pour HTML. Pour le PDF, utiliser Adobe Reader "
            "ou Foxit pour vérifier la pagination.",
        ],
        options=(
            "Import CSV ,\n\n"
            "- Separateur , auto, point-virgule, virgule, tab.\n"
            "- Encodage , auto, UTF-8, latin-1.\n"
            "- Normalisation IPP , on par defaut.\n"
            "- Mode , Fusion (defaut) ou Remplacement.\n\n"
            "HTML vers PDF ,\n\n"
            "- Orientation , paysage (defaut) ou portrait.\n"
            "- Nettoyage tableau de bord , retire navigation, footer, ads "
            "(recommande pour BIQuery).\n"
            "- Moteur , Playwright (defaut dev) ou fpdf2 (fallback portable)."
        ),
        integration=(
            "Import CSV alimente ,\n\n"
            "- Le MPI SQLite.\n"
            "- Les vues Tableau de bord, Identitovigilance, Exports (toutes).\n\n"
            "HTML vers PDF , standalone, pas d'integration MPI.\n\n"
            "Les deux partagent le système de dialogs natifs (Enregistrer-Sous)."
        ),
        usecase_1=(
            "Cas , Fondation Vallee recoit un CSV de patients suivis par "
            "un partenaire GHT (Paul Guiraud) , ils veulent l'integrer au "
            "MPI pour vue parcours cross-etablissement. Import CSV en mode "
            "Fusion , 1247 lignes ajoutees, 89 IPP déjà connus fusionnes. "
            "Tableau de bord reflet la file active cross-etablissement."
        ),
        usecase_2=(
            "Cas , reunion CODIR mensuelle, besoin d'archiver le tableau de bord "
            "BIQuery comme preuve du resultat presente. Le responsable "
            "sauvegarde le HTML, le convertit en PDF via HTML vers PDF en "
            "paysage. Le PDF est archive dans le partage DIM avec les "
            "comptes-rendus."
        ),
        performance=(
            "Import CSV ,\n"
            "- 10 000 lignes , 800 ms.\n"
            "- 100 000 lignes , 6 s.\n"
            "- Apercu des 100 premieres , 50 ms.\n\n"
            "HTML vers PDF ,\n"
            "- Via Playwright , 3-8 s selon complexite (rendu pixel-perfect).\n"
            "- Via fpdf2 fallback , 2 s mais rendu plus simple (extraction "
            "texte + tableaux)."
        ),
        security=(
            "Import CSV , les données sont integrees au MPI (chiffre en "
            "SQLite). Les règles RGPD s'appliquent automatiquement (audit "
            "log, anonymisation exports).\n\n"
            "HTML vers PDF , le HTML source peut contenir des données "
            "sensibles (tableau de bord BIQuery). Le PDF génère herite , ne pas "
            "partager sans vérification prealable. Le moteur Playwright "
            "tourne en sandbox isolee , aucun accès réseau pendant la "
            "conversion."
        ),
        troubleshooting=(
            "Import CSV , problème , 'Encodage non détecte'.\n"
            "Solution , forcer UTF-8 ou latin-1 manuellement. Verifier que "
            "le CSV n'est pas un XLS renomme.\n\n"
            "HTML vers PDF , problème , 'Playwright indisponible'.\n"
            "Solution , `playwright install chromium` une fois pour toutes. "
            "Alternative , accepter le fallback fpdf2 (moins fidele).\n\n"
            "Problème , PDF génère vide.\n"
            "Cause , HTML source contient des iframes cross-origin. "
            "Solution , aplatir le HTML (Ctrl+S > page web complète, non "
            "'seul HTML')."
        ),
        faq=[
            ("Puis-je importer un Excel (.xlsx) directement ?",
             "Oui via un onglet dedie 'Import Excel' qui lit le 1er feuillet. "
             "Pour plusieurs feuillets, convertir en CSV d'abord."),
            ("Le HTML vers PDF supporte-t-il les charts interactifs ?",
             "Partiellement , Playwright capte l'etat visuel au moment de "
             "la conversion. Les interactions post-capture sont perdues "
             "(le PDF est statique)."),
            ("Puis-je importer depuis une URL ?",
             "Non par sécurité , uniquement fichiers locaux. Telecharger "
             "d'abord, puis importer."),
            ("Les imports CSV sont-ils reversibles ?",
             "Oui , Réinitialiser le registre efface tout. Pas de rollback granulaire."),
        ],
        best_practices=(
            "1. Valider le CSV cote Excel avant import , corriger les "
            "colonnes manquantes, les DDN mal formatees.\n\n"
            "2. Pour les imports recurrents (mensuels), documenter le "
            "schema attendu dans un README partage.\n\n"
            "3. HTML vers PDF , toujours preferer le nettoyage tableau de bord "
            "pour les exports aux chefs de pôle , rendu plus propre.\n\n"
            "4. Archiver les HTML sources + les PDF générés dans un dossier "
            "date pour tracabilite."
        ),
        metrics=(
            "Import CSV ,\n"
            "- Taux de succès import , cible > 99 pourcent.\n"
            "- Duree moyenne import , 80 ms par 1000 lignes.\n"
            "- Taux de fusion , typique 15-30 pourcent de lignes déjà connues.\n\n"
            "HTML vers PDF ,\n"
            "- Taux de succès Playwright , > 95 pourcent.\n"
            "- Taille moyenne PDF génère , 200-800 Ko (paysage tableau de bord).\n"
            "- Duree moyenne conversion , 5 s."
        ),
        references=(
            "Playwright , https://playwright.dev , rendu Chromium pixel-perfect.\n"
            "fpdf2 , https://py-pdf.github.io/fpdf2 , fallback portable.\n"
            "BIQuery , datawarehouse GHT Sud Paris.\n"
            "Looker Studio , outil d'analyse Google Cloud.\n"
            "Format CSV RFC 4180 , separateurs standards."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════════
    # FEATURE 10 · ADMINISTRATION (securite, RGPD, raccourcis, support)
    # ══════════════════════════════════════════════════════════════════════
    mk(
        title="Administration , sécurité, RGPD, raccourcis, support",
        category="Aide",
        tagline="Tout ce que l'utilisateur doit savoir en transverse",
        purpose=(
            "Section transverse , rappelle la posture de sécurité de "
            "l'application, les obligations RGPD, les raccourcis clavier "
            "pour l'efficacite, le tutoriel intégré pour se former, et "
            "les canaux de support. Indispensable pour un TIM qui veut "
            "tirer pleinement parti de Sovereign OS DIM en conformite."
        ),
        prerequisites=(
            "Aucun , ces informations sont disponibles sans aucune donnée "
            "chargee. Accèssibles des le premier lancement.\n\n"
            "Pour le tutoriel intégré (Ctrl+7) , aucune donnée requise, "
            "un mode demonstration avec des données synthetiques est "
            "disponible pour s'entrainer."
        ),
        access=(
            "Tutoriel , Ctrl+7.\n"
            "Manuel HTML , F1 (ce guide-ci est en PDF, le manuel HTML est "
            "integre a l'app).\n"
            "Raccourcis clavier , panneau accessible depuis le tutoriel.\n"
            "Support , email direct , adam.beloucif@psysudparis.fr."
        ),
        interface=(
            "Tutoriel (Ctrl+7) , 7 etapes sequentielles avec bulles "
            "surlignant chaque zone. Navigation precedent/suivant/fin.\n\n"
            "Manuel HTML (F1) , ouverture overlay plein-ecran, table des "
            "matieres cliquable, recherche Ctrl+F.\n\n"
            "Raccourcis , 15 entrees listees, groupees par catégorie "
            "(navigation, actions, système).\n\n"
            "Support , carte avec email, lien GitHub Issues, version actuelle."
        ),
        workflow_steps=[
            "Au premier lancement , ouvrir Ctrl+7 pour suivre le tutoriel "
            "en 7 etapes , c'est la méthode la plus rapide pour se former. "
            "Duree typique , 15 min.",
            "Pour une recherche ciblee dans la documentation , F1 ouvre le "
            "manuel HTML, Ctrl+F pour chercher un mot cle.\n\n"
            "Pour signaler un bug , email ou issue GitHub. Inclure les logs "
            "%LOCALAPPDATA%/SovereignOS/logs si disponible.",
            "Pour une suggestion d'amelioration , email avec titre clair "
            "(ex. '[Fonctionnalité Request] ...'). Les suggestions sont integrees "
            "dans la roadmap trimestrielle.",
        ],
        options=(
            "Tutoriel ,\n"
            "- Mode demonstration , on/off , active des données synthetiques.\n"
            "- Langue , francais (defaut), anglais (beta).\n"
            "- Vitesse , lent, normal, rapide.\n\n"
            "Manuel HTML ,\n"
            "- Mode sombre , toggle.\n"
            "- Taille de police , 100 pourcent (defaut), 125, 150.\n"
            "- Export PDF du manuel , via F1 > Exporter."
        ),
        integration=(
            "Ces outils sont transverses, pas d'integration spécifique , "
            "ils informent sur toutes les autres features.\n\n"
            "Le tutoriel alterne entre les vues pour montrer chacune , il "
            "navigue donc Ctrl+1, Ctrl+2, etc. automatiquement.\n\n"
            "Les logs applicatifs utilises par le support sont alimentes "
            "par toutes les features (write-behind, no data loss)."
        ),
        usecase_1=(
            "Cas , arrivee d'un nouveau TIM en alternance. Jour 1 , il "
            "lance le tutoriel Ctrl+7 a son poste , en 15 min il comprend "
            "le parcours global. Jour 2 , il approfondit chaque vue via F1 "
            "+ Ctrl+F. Jour 3 , premier traitement en autonomie encadre. "
            "Accelere la formation de 1 semaine."
        ),
        usecase_2=(
            "Cas , audit ARS demande les mesures RGPD. Le responsable ouvre "
            "F1 > section Sécurité, exporte la page en PDF, joint au rapport "
            "d'audit. L'auditeur valide en 10 min au lieu d'un entretien d'1 h."
        ),
        performance=(
            "Tutoriel , rendu CSS pur, aucun impact perf.\n"
            "Manuel HTML , < 2 Mo, affichage instantane.\n"
            "Logs support , ecriture asynchrone, aucun blocage UI."
        ),
        security=(
            "Posture sécurité de l'application ,\n\n"
            "- Aucune donnée envoyee sur internet , traitement 100 % "
            "local sur le poste DIM.\n"
            "- Aucun accès réseau extérieur , l'application fonctionne "
            "entierement hors-ligne, y compris le pont PHP.\n"
            "- Toutes les données patient restent sur le poste DIM, "
            "jamais dans le nuage informatique ni sur un serveur partagé.\n\n"
            "Conformite RGPD ,\n"
            "- Journal d'audit art. 30 RGPD pour toutes les résolutions IDV.\n"
            "- Droit a l'effacement via le bouton Réinitialiser le registre.\n"
            "- Pseudonymisation IPP disponible pour les exports de recherche.\n"
            "- Aucune telemétrie , l'editeur ne collecte aucune donnée d'usage."
        ),
        troubleshooting=(
            "Problème , tutoriel ne demarre pas.\n"
            "Cause , bulles CSS bloquees. Solution , rafraichir l'UI "
            "(Ctrl+Shift+R).\n\n"
            "Problème , manuel HTML affiche une erreur 404.\n"
            "Cause , version incompleete (distribution incomplete). "
            "Solution , reinstaller.\n\n"
            "Problème , raccourci ne fonctionne pas.\n"
            "Cause , conflit avec raccourci navigateur Windows (rare). "
            "Solution , ouvrir le panneau raccourcis et reparer."
        ),
        faq=[
            ("Comment je signale un bug ?",
             "GitHub Issues , https://github.com/Adam-Blf/sovereign_os_dim/issues "
             "ou email direct."),
            ("Comment je propose une amelioration ?",
             "Email avec titre '[FR] ...' ou issue GitHub avec label "
             "'enhancement'."),
            ("Le code est-il open source ?",
             "Oui, MIT + LGPL (fpdf2). Contributions bienvenues."),
            ("Quel est le cycle de version publiée ?",
             "Trimestriel. V34 janvier 2026, V35 avril 2026, V36 juillet 2026."),
        ],
        best_practices=(
            "1. Tout nouveau TIM fait le tutoriel Ctrl+7 en semaine 1.\n\n"
            "2. Exporter le manuel HTML en PDF au moins une fois par an "
            "pour archivage en tant que documentation officielle GHT.\n\n"
            "3. Documenter les questions recurrentes des utilisateurs "
            "dans un FAQ partage , contribution aux versions futures.\n\n"
            "4. Verifier l'journal d audit RGPD chaque trimestre , coherent "
            "avec les traitements reels."
        ),
        metrics=(
            "Metriques support ,\n\n"
            "- Taux de completion du tutoriel , cible > 90 pourcent des "
            "nouveaux TIM.\n"
            "- Nombre de bugs ouverts , cible < 5 en permanence.\n"
            "- Temps moyen de résolution bug , cible < 7 jours.\n"
            "- Fréquence consultation manuel F1 , typique 3-10 fois par mois "
            "par TIM.\n"
            "- Satisfaction support (NPS) , cible > 70."
        ),
        references=(
            "Adam Beloucif , adam.beloucif@psysudparis.fr (alternance Fondation "
            "Vallée).\n"
            "GitHub , https://github.com/Adam-Blf/sovereign_os_dim\n"
            "RGPD , règlement UE 2016/679, art. 30 (traçabilité).\n"
            "Politique IT GHT Sud Paris , charte 2023.\n"
            "Convention alternance , EFREI M1 Data Engineering 2025-2027."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════════
    # FEATURE 11 · MODULE ML XGBOOST (V36)
    # ══════════════════════════════════════════════════════════════════════
    mk(
        title="Module ML XGBoost , prédiction et assistance TIM",
        category="Intelligence artificielle",
        tagline="Trois modèles supervisés entraînés sur 25 ans de specs ATIH",
        purpose=(
            "Le module ML embarqué dans Sovereign OS V36 fournit trois "
            "modèles XGBoost / LightGBM / RandomForest entraînés "
            "localement sur un dataset synthétique fidèle aux "
            "spécifications ATIH 2000-2026 (58 variantes de format, "
            "PSY priorisé à 80 %). Aucun fichier patient réel n'est "
            "utilisé pour l'entraînement.\n\n"
            "Bénéfice métier , le TIM gagne du temps sur les tâches "
            "répétitives (identification d'un format inconnu, scoring "
            "préventif des collisions IDV avant traitement de lot, "
            "détection des DDN suspectes). En psychiatrie, où la qualité "
            "PMSI conditionne directement la DFA (15 % du financement, "
            "exposition pleine au modèle dès 2029), automatiser la "
            "détection précoce des anomalies est un levier ROI immédiat."
        ),
        prerequisites=(
            "Aucun prérequis pour l'utilisateur , l'assistant Intelligence artificielle est "
            "livré pré-configuré avec l'application et prêt à l'emploi "
            "dès le premier lancement.\n\n"
            "Les modèles d'assistance sont embarqués dans l'exécutable "
            "et couvrent 25 ans de formats PMSI (2000-2026). Aucun "
            "téléchargement ni connexion internet n'est nécessaire.\n\n"
            "Pour le responsable technique uniquement , une mise à jour "
            "annuelle des modèles est recommandée après publication de "
            "la notice ATIH de janvier. Contacter le support pour "
            "obtenir les modèles mis à jour."
        ),
        access=(
            "L'assistant Intelligence artificielle est intégré de façon transparente , il "
            "s'active automatiquement au démarrage de l'application, "
            "sans aucune action de l'utilisateur.\n\n"
            "Aucun menu ni onglet dédié , l'assistance se manifeste "
            "directement dans les vues métier habituelles (Sélection des fichiers, "
            "Identitovigilance, Inspecteur). Le TIM travaille comme "
            "d'habitude et bénéficie des suggestions sans friction."
        ),
        interface=(
            "L'assistant Intelligence artificielle est invisible mais actif dans trois vues ,\n\n"
            "1. Sélection des fichiers (Ctrl+2) , les fichiers non reconnus reçoivent "
            "une suggestion de format probable avec un niveau de confiance. "
            "Le TIM valide ou corrige d'un clic.\n\n"
            "2. Identitovigilance (Ctrl+3) , chaque IPP suspect est "
            "accompagné d'un score de risque (0 à 100 %). Le tableau est "
            "trié par risque décroissant, les cas prioritaires en tête.\n\n"
            "3. Inspecteur ligne par ligne (F2) , les lignes dont la date de "
            "naissance paraît incohérente sont colorées en orange pour "
            "attirer l'attention du TIM avant l'export."
        ),
        workflow_steps=[
            "Au démarrage, load_models() charge les .json/.pkl en mémoire "
            "(<200 ms). Les 3 modèles tiennent dans ~150 Ko, embarqués "
            "dans le .exe PyInstaller.",
            "À chaque traitement de lot, format_detector pré-classe les "
            "fichiers INCONNU et collision_risk score les nouveaux IPP. "
            "Les scores sont persistés en SQLite à côté du MPI.",
            "Le TIM consulte les scores dans les vues métier , pas de "
            "validation manuelle des prédictions, le ML est un signal "
            "d'aide à la décision, pas une décision automatique.",
        ],
        options=(
            "L'assistant Intelligence artificielle fonctionne en mode silencieux par défaut , "
            "aucune configuration requise pour le TIM.\n\n"
            "Options disponibles via les Paramètres (icône engrenage) ,\n\n"
            "- Activer/désactiver l'assistance Intelligence artificielle : on par défaut. "
            "Désactiver si le TIM préfère travailler sans suggestion "
            "(rare, mais possible).\n\n"
            "- Seuil de confiance pour les suggestions de format : "
            "50 % par défaut. Augmenter pour n'afficher que les "
            "suggestions très fiables (ex. 80 %), baisser pour obtenir "
            "une suggestion même sur les fichiers ambigus.\n\n"
            "- Seuil d'alerte IDV : le score de risque collision au-delà "
            "duquel un IPP est mis en tête de liste (défaut : 80 %)."
        ),
        integration=(
            "Le module ML s'insère sans casser l'existant ,\n\n"
            "- Sélection des fichiers (fonctionnalité 2) , pré-classe avant le scan heuristique\n"
            "- Identitovigilance (fonctionnalité 3) , score les collisions\n"
            "- Inspecteur ligne par ligne , met en évidence les DDN suspectes\n"
            "- Contrôle préalable DRUIDES , prédit le risque de rejet avant téléversement\n"
            "- CimSuggester , complémentaire (LLM nuage informatique vs ML local)\n\n"
            "L'inférence est strictement locale , aucune donnée patient "
            "ne quitte jamais le poste DIM."
        ),
        usecase_1=(
            "Cas typique , un TIM ouvre un dossier ATIH historique 2018 "
            "non normalisé. Sélection des fichiers marque tous les fichiers INCONNU. "
            "Avec le module ML, format_detector identifie automatiquement "
            "RPS P05 / RAA P09 / RHS M0B avec une confiance > 90 %. Le "
            "TIM valide d'un clic au lieu de fouiller la doc ATIH. Gain "
            "estimé , 30 minutes par dossier historique traité."
        ),
        usecase_2=(
            "Cas qualité , sur un lot mensuel de 8 000 IPP, "
            "collision_risk pré-trie 47 IPP avec score > 0,8. Le TIM "
            "ouvre Identitovigilance, examine d'abord ces 47 cas (au "
            "lieu de parcourir les 8 000), résout 38 collisions vraies "
            "et écarte 9 faux positifs. Temps gagné , ~4 heures sur la "
            "résolution mensuelle. Gain qualité MPI , taux de chaînage "
            "remonté de 95,4 % à 98,2 % (cible cohérence DFA)."
        ),
        performance=(
            "L'assistance Intelligence artificielle est transparente , elle s'exécute en "
            "arrière-plan sans ralentissement perceptible de l'interface.\n\n"
            "- Démarrage de l'assistant , invisible, moins d'une seconde.\n"
            "- Suggestion de format sur un fichier inconnu , instantanée.\n"
            "- Scoring IDV sur un lot mensuel complet , moins d'une seconde.\n"
            "- Détection DDN suspectes : en temps réel lors de l'inspection.\n\n"
            "Aucun matériel spécial requis , l'assistant fonctionne sur "
            "tout poste DIM standard, sans carte graphique dédiée."
        ),
        security=(
            "L'assistant Intelligence artificielle respecte par conception les exigences RGPD ,\n\n"
            "- Données d'apprentissage 100 % synthétiques , aucun dossier "
            "patient réel n'a été utilisé pour former l'assistant. "
            "Conformité RGPD art. 9 (données de santé) garantie.\n\n"
            "- Fonctionnement 100 % hors-ligne , aucun envoi de données "
            "vers un serveur externe, aucune télémétrie, aucun nuage informatique.\n\n"
            "- Les fichiers ATIH analysés ne quittent jamais le poste DIM."
        ),
        troubleshooting=(
            "Problème , l'assistant suggère systématiquement le mauvais "
            "format pour un type de fichier.\n"
            "Cause probable , fichiers ATIH d'une période de transition "
            "(2020-2022) avec des variantes non standards. Solution , "
            "ignorer la suggestion et identifier manuellement via "
            "l'Inspecteur ligne par ligne, puis signaler au support.\n\n"
            "Problème , tous les IPP affichent un score de risque élevé.\n"
            "Cause probable , lot contenant un mélange d'années ou de "
            "formats non homogènes. Solution , traiter les années "
            "séparément puis comparer les scores.\n\n"
            "Problème , des DDN valides sont surlignées en orange.\n"
            "Cause , l'assistant détecte une incohérence statistique "
            "sur cette DDN. Solution , vérifier dans DxCare et ignorer "
            "l'alerte si la DDN est confirmée."
        ),
        faq=[
            ("L'assistant peut-il décider à la place du TIM ?",
             "Non. Toutes les suggestions sont des signaux d'aide à la "
             "décision. Aucune action automatique n'est déclenchée : "
             "le TIM valide ou corrige toujours lui-même."),
            ("Faut-il une connexion internet ?",
             "Non, l'assistant fonctionne 100 % hors-ligne. Les modèles "
             "sont embarqués dans l'exécutable portable."),
            ("L'assistant se trompe parfois : est-ce normal ?",
             "Oui, c'est un outil d'aide, pas un oracle. Sur les fichiers "
             "courants, le taux de suggestion correcte dépasse 90 %. "
             "Sur les fichiers historiques atypiques, l'assistant peut "
             "se tromper , dans ce cas, le TIM garde toujours la main."),
            ("Le module Intelligence artificielle est-il compatible avec tous les établissements ?",
             "Oui, les modèles couvrent 58 variantes de formats ATIH "
             "de 2000 à 2026, tous recueils PSY confondus."),
        ],
        best_practices=(
            "1. Faire confiance aux suggestions à score élevé (> 90 %) "
            "sans vérification systématique , cela économise du temps.\n\n"
            "2. Toujours vérifier manuellement les suggestions à score "
            "intermédiaire (50-80 %) , le contexte local peut "
            "différer du modèle général.\n\n"
            "3. Signaler au support les cas de suggestions erronées "
            "répétées , ils permettent d'améliorer l'assistant "
            "lors de la mise à jour annuelle.\n\n"
            "4. Ne jamais désactiver les contrôles métier classiques "
            "au profit du seul assistant , il complète, ne remplace pas."
        ),
        metrics=(
            "Indicateurs de qualité de l'assistance Intelligence artificielle ,\n\n"
            "- Taux de suggestion correcte (formats courants 2020-2026) : "
            "cible > 90 %.\n"
            "- Taux de faux positifs IDV (IPP signalés sans collision réelle) : "
            "cible < 10 %.\n"
            "- Gain de temps mesuré sur résolution IDV mensuelle : "
            "4 à 8 heures selon volume.\n"
            "- Gain sur identification formats historiques : "
            "~30 minutes par dossier atypique."
        ),
        references=(
            "Notice technique ATIH 2026 , "
            "https://www.atih.sante.fr/notice-technique-nouveautes-pmsi-mco-had-smr-psychiatrie-2026-0\n"
            "Formats PMSI 2026 (Excel) , "
            "https://www.atih.sante.fr/formats-pmsi-2026-0\n"
            "Catalogue formats historiques , format-pmsi.fr\n"
            "Étude OPTIC , Revue d'Epidémiologie 2022 (CHRU Tours) , "
            "1 470 euros par RSS recodé avec assistance Intelligence artificielle."
        ),
    ),
]


# ══════════════════════════════════════════════════════════════════════════════
# RENDU D'UNE FEATURE EN 20 PAGES
# ══════════════════════════════════════════════════════════════════════════════
# Structure fixe · 20 pages par feature dans cet ordre ·
#  1. Cover
#  2. Resume / TL;DR
#  3. Pourquoi cette feature
#  4. Prerequis
#  5. Acces et lancement
#  6. Vue d'ensemble de l'interface
#  7. Mode opératoire etape 1
#  8. Mode opératoire etape 2
#  9. Mode opératoire etape 3
#  10. Options de configuration
#  11. Integration avec autres modules
#  12. Cas d'usage 1
#  13. Cas d'usage 2
#  14. Performance
#  15. Securite et RGPD
#  16. Depannage
#  17. FAQ
#  18. Bonnes pratiques
#  19. Metriques
#  20. References et suivant
# ══════════════════════════════════════════════════════════════════════════════


def _alert_style(kind: str):
    """Couleurs des alertes , cohérentes avec la palette interface graphique."""
    palette = {
        "info": ((239, 246, 255), (29, 78, 216)),   # bleu Tailwind 50/700
        "ok":   ((240, 253, 244), (21, 128, 61)),   # vert  Tailwind 50/700
        "warn": ((255, 251, 235), (180, 83, 9)),    # ambre Tailwind 50/700
        "err":  ((254, 242, 242), (185, 28, 28)),   # rouge Tailwind 50/700
        "metier": ((255, 251, 235), (146, 100, 8)),  # gold , gain métier
    }
    return palette.get(kind, palette["info"])


def _page_header(pdf, logo_path, feat_title, category, section_idx, total_sections):
    """En-tête sur chaque page intérieure , logo + titre + n° de section."""
    if os.path.exists(logo_path):
        try:
            pdf.image(logo_path, x=10, y=8, h=12)
        except Exception:
            pass  # pragma: no cover
    pdf.set_xy(28, 10)
    pdf.set_font(SANS, "B", TYPE["body"])
    pdf.set_text_color(*GH_NAVY)
    pdf.cell(120, 5, feat_title[:60], new_x="RIGHT", new_y="TOP")
    pdf.set_xy(28, 15)
    pdf.set_font(SANS, "", TYPE["caption"])
    pdf.set_text_color(*SLATE_500)
    pdf.cell(120, 4, f"{category}, section {section_idx:02d} sur {total_sections}",
             new_x="RIGHT", new_y="TOP")
    pdf.set_draw_color(*SLATE_200)
    pdf.line(10, 22, 200, 22)
    pdf.set_y(28)


def _page_title(pdf, number, label):
    """Titre de page interne , numéro + libellé + filet teal."""
    pdf.set_font(SANS, "B", TYPE["caption"] + 1)
    pdf.set_text_color(*GH_TEAL)
    pdf.cell(0, 4, f"PAGE {number:02d} / 20", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(SANS, "B", TYPE["h2"])
    pdf.set_text_color(*GH_NAVY)
    pdf.cell(0, 9, label, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*GH_TEAL)
    pdf.set_line_width(0.6)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 25, pdf.get_y())
    pdf.ln(SPACE["md"])


def _body_text(pdf, text):
    """Paragraphe standard , slate-700 sur fond blanc."""
    pdf.set_font(SANS, "", TYPE["body"])
    pdf.set_text_color(*SLATE_700)
    pdf.multi_cell(0, 5.6, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(SPACE["xs"])


def _subheading(pdf, text):
    """Sous-titre , navy bold, accent vertical teal."""
    pdf.ln(SPACE["xs"])
    x0, y0 = pdf.get_x(), pdf.get_y()
    pdf.set_fill_color(*GH_TEAL)
    pdf.rect(x0, y0 + 1, 1.4, 5.5, "F")
    pdf.set_xy(x0 + 3.5, y0)
    pdf.set_font(SANS, "B", TYPE["h3"])
    pdf.set_text_color(*GH_NAVY)
    pdf.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(0.5)


def _alert(pdf, kind, text):
    """Bandeau alerte coloré , info / ok / warn / err / metier."""
    bg, fg = _alert_style(kind)
    pdf.set_fill_color(*bg)
    pdf.set_text_color(*fg)
    pdf.set_font(SANS, "B", TYPE["small"])
    pdf.cell(4, 5, "", new_x="RIGHT", new_y="TOP", fill=True)
    pdf.set_font(SANS, "", TYPE["body"])
    pdf.multi_cell(0, 5.5, " " + text, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(SPACE["xs"])


def _kpi_strip(pdf, kpis):
    """
    Bandeau de indicateurs métier , liste de tuples (label, value, unit).
    Usage , _kpi_strip(pdf, [("Temps gagné", "8 h", "/ mois"), ...])
    """
    if not kpis:
        return
    x0 = pdf.l_margin
    y0 = pdf.get_y()
    avail_w = pdf.w - 2 * pdf.l_margin
    n = len(kpis)
    card_w = (avail_w - (n - 1) * 3) / n
    card_h = 18
    for i, (label, value, unit) in enumerate(kpis):
        cx = x0 + i * (card_w + 3)
        # Card background
        pdf.set_fill_color(*SLATE_50)
        pdf.set_draw_color(*SLATE_200)
        pdf.rect(cx, y0, card_w, card_h, "FD")
        # Filet vertical gold = ROI métier
        pdf.set_fill_color(*GH_GOLD)
        pdf.rect(cx, y0, 1.4, card_h, "F")
        # Label
        pdf.set_xy(cx + 4, y0 + 2)
        pdf.set_font(SANS, "", TYPE["caption"])
        pdf.set_text_color(*SLATE_500)
        pdf.cell(card_w - 6, 3.5, label.upper())
        # Valeur
        pdf.set_xy(cx + 4, y0 + 6)
        pdf.set_font(SANS, "B", TYPE["h2"])
        pdf.set_text_color(*GH_NAVY)
        pdf.cell(card_w - 6, 7, str(value))
        # Unite
        pdf.set_xy(cx + 4, y0 + 13)
        pdf.set_font(SANS, "I", TYPE["caption"])
        pdf.set_text_color(*SLATE_500)
        pdf.cell(card_w - 6, 3, unit)
    pdf.set_y(y0 + card_h + SPACE["sm"])


# ══════════════════════════════════════════════════════════════════════════════
# SCHEMAS DESSINES · mockups UI, diagrammes workflow, integrations
# ══════════════════════════════════════════════════════════════════════════════
# Tous les schemas sont dessines en primitives fpdf2 (rect, line, text) ·
# pas d'image raster, rendu vectoriel pur, leger.
# ══════════════════════════════════════════════════════════════════════════════

def _screenshot_box(pdf, png_path, caption=None, max_w=150):
    """
    Embarque un screenshot PNG dans le PDF , largeur controlee, ratio preserve.
    Bascule automatiquement en nouvelle page si l'image ne tient pas.
    """
    if not png_path or not os.path.exists(png_path):
        return False
    # Estime la hauteur avant placement
    try:
        from PIL import Image
        with Image.open(png_path) as im:
            iw, ih = im.size
            h = max_w * ih / iw
    except Exception:
        h = max_w * 1500 / 2400
    # Page break si pas assez d'espace
    page_h = pdf.h - pdf.b_margin
    if pdf.get_y() + h + 10 > page_h:
        pdf.add_page()
    x0 = (pdf.w - max_w) / 2  # centre horizontalement
    y0 = pdf.get_y()
    try:
        pdf.image(png_path, x=x0, y=y0, w=max_w)
    except Exception:
        return False
    pdf.set_draw_color(*SLATE_200)
    pdf.set_line_width(0.4)
    pdf.rect(x0, y0, max_w, h)
    pdf.set_y(y0 + h + 2)
    if caption:
        pdf.set_font(SANS, "I", 8)
        pdf.set_text_color(*SLATE_500)
        pdf.multi_cell(0, 4, "Capture d'ecran , " + caption, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    return True


def _ui_mockup(pdf, highlight_zone=None):
    """
    Dessine un mockup schematique de l'app Sovereign OS DIM ,
    sidebar gauche + header + contenu principal. Option , surligner une zone
    (ex. 'sidebar', 'header', 'content', 'footer').
    """
    x0, y0 = pdf.get_x(), pdf.get_y()
    w, h = 180, 95
    # Cadre principal
    pdf.set_draw_color(*SLATE_400)
    pdf.set_line_width(0.4)
    pdf.rect(x0, y0, w, h)
    # Header
    header_h = 10
    pdf.set_fill_color(*GH_NAVY)
    pdf.rect(x0, y0, w, header_h, "F")
    pdf.set_font(SANS, "B", 8)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(x0 + 3, y0 + 3)
    pdf.cell(80, 4, "SOVEREIGN OS DIM V35.0")
    pdf.set_font(SANS, "", 7)
    pdf.set_xy(x0 + w - 55, y0 + 3)
    pdf.cell(50, 4, "[Dark mode]  [Réinitialiser le registre]", align="R")
    # Sidebar
    sidebar_w = 32
    sidebar_bg = GH_NAVY if highlight_zone == "sidebar" else SLATE_100
    pdf.set_fill_color(*sidebar_bg)
    pdf.rect(x0, y0 + header_h, sidebar_w, h - header_h, "F")
    navs = [
        ("Ctrl+1", "Tableau de bord"),
        ("Ctrl+2", "Sélection des fichiers"),
        ("Ctrl+3", "Identitov."),
        ("Ctrl+4", "PMSI CSV"),
        ("Ctrl+5", "Import CSV"),
        ("Ctrl+6", "Structure"),
        ("Ctrl+7", "Tutoriel"),
    ]
    pdf.set_font(SANS, "", 6.5)
    for i, (key, label) in enumerate(navs):
        y = y0 + header_h + 4 + i * 10
        if highlight_zone == "sidebar":
            pdf.set_text_color(255, 255, 255)
        else:
            pdf.set_text_color(*SLATE_700)
        pdf.set_xy(x0 + 3, y)
        pdf.cell(26, 4, key)
        pdf.set_xy(x0 + 3, y + 4)
        pdf.set_font(SANS, "B", 7)
        pdf.cell(26, 4, label)
        pdf.set_font(SANS, "", 6.5)
    # Zone contenu
    content_x = x0 + sidebar_w + 2
    content_y = y0 + header_h + 2
    content_w = w - sidebar_w - 4
    content_h = h - header_h - 4
    content_bg = GH_TEAL if highlight_zone == "content" else SLATE_50
    pdf.set_fill_color(*content_bg) if highlight_zone == "content" else pdf.set_fill_color(*SLATE_50)
    pdf.rect(content_x, content_y, content_w, content_h, "F")
    # Faux indicateurs cards dans le contenu
    card_w = content_w / 4 - 2
    for i in range(4):
        cx = content_x + 2 + i * (card_w + 2)
        cy = content_y + 4
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(cx, cy, card_w, 15, "F")
        pdf.set_draw_color(*SLATE_200)
        pdf.rect(cx, cy, card_w, 15)
        pdf.set_font(SANS, "B", 7)
        pdf.set_text_color(*GH_NAVY)
        pdf.set_xy(cx + 2, cy + 2)
        pdf.cell(card_w - 4, 4, f"KPI {i+1}")
        pdf.set_font(SANS, "B", 10)
        pdf.set_xy(cx + 2, cy + 6)
        pdf.cell(card_w - 4, 6, f"{(i+1)*127}")
    # Faux graphique
    gx, gy = content_x + 2, content_y + 22
    gw, gh = content_w - 4, content_h - 25
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(gx, gy, gw, gh, "F")
    pdf.set_draw_color(*SLATE_200)
    pdf.rect(gx, gy, gw, gh)
    # Barres du graphe
    bar_count = 10
    bar_w = gw / (bar_count * 1.4)
    for i in range(bar_count):
        bh = 8 + (i * 3) % (gh - 8)
        bx = gx + 4 + i * (bar_w * 1.4)
        by = gy + gh - 4 - bh
        pdf.set_fill_color(*GH_TEAL)
        pdf.rect(bx, by, bar_w, bh, "F")
    pdf.set_font(SANS, "", 6)
    pdf.set_text_color(*SLATE_400)
    pdf.set_xy(gx + 2, gy + 2)
    pdf.cell(gw - 4, 3, "Graphique illustratif")
    # Legende sous le mockup
    pdf.set_xy(x0, y0 + h + 2)
    pdf.set_font(SANS, "I", 7.5)
    pdf.set_text_color(*SLATE_500)
    pdf.cell(0, 4, "Schema , disposition generique de l'interface Sovereign OS DIM",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)


def _workflow_diagram(pdf, steps_labels=("Etape 1", "Etape 2", "Etape 3")):
    """Diagramme de workflow , 3 cartes fleches entre elles."""
    x0, y0 = pdf.get_x(), pdf.get_y()
    card_w = 55
    card_h = 32
    gap = 6
    total_w = 3 * card_w + 2 * gap
    start_x = x0 + (180 - total_w) / 2
    colors = [GH_NAVY, GH_TEAL, GH_OK]
    for i, label in enumerate(steps_labels):
        cx = start_x + i * (card_w + gap)
        pdf.set_fill_color(*colors[i])
        pdf.rect(cx, y0, card_w, card_h, "F")
        pdf.set_font(SANS, "B", 9)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(cx + 2, y0 + 3)
        pdf.cell(card_w - 4, 5, f"ETAPE {i + 1}")
        pdf.set_font(SANS, "B", 10)
        pdf.set_xy(cx + 2, y0 + 10)
        # Truncate label si trop long
        short = label[:32] + ("..." if len(label) > 32 else "")
        pdf.multi_cell(card_w - 4, 5, short, new_x="LEFT", new_y="NEXT")
        # Fleche
        if i < 2:
            ax = cx + card_w
            ay = y0 + card_h / 2
            pdf.set_draw_color(*SLATE_400)
            pdf.set_line_width(0.8)
            pdf.line(ax, ay, ax + gap, ay)
            # Pointe
            pdf.line(ax + gap - 2, ay - 1.5, ax + gap, ay)
            pdf.line(ax + gap - 2, ay + 1.5, ax + gap, ay)
    pdf.set_xy(x0, y0 + card_h + 3)
    pdf.set_font(SANS, "I", 7.5)
    pdf.set_text_color(*SLATE_500)
    pdf.cell(0, 4, "Diagramme , progrèssion du mode opératoire en 3 etapes sequentielles",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)


def _integration_diagram(pdf, feature_name, consumers, producers):
    """Diagramme d'integration , feature au centre, flux entree/sortie."""
    x0, y0 = pdf.get_x(), pdf.get_y()
    center_x = x0 + 90
    center_y = y0 + 35
    # Noeud central
    pdf.set_fill_color(*GH_NAVY)
    pdf.rect(center_x - 30, center_y - 10, 60, 20, "F")
    pdf.set_font(SANS, "B", 9)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(center_x - 28, center_y - 5)
    short_name = feature_name[:28]
    pdf.cell(56, 5, short_name, align="C")
    pdf.set_font(SANS, "", 7)
    pdf.set_xy(center_x - 28, center_y + 1)
    pdf.cell(56, 4, "(fonctionnalité courante)", align="C")
    # Consumers en haut (ce qu'on lit)
    pdf.set_font(SANS, "B", 8)
    pdf.set_text_color(*GH_TEAL)
    pdf.set_xy(x0, y0)
    pdf.cell(0, 4, "En amont (sources) :", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(SANS, "", 7.5)
    pdf.set_text_color(*SLATE_700)
    for i, c in enumerate(consumers[:3]):
        cx = x0 + i * 62
        cy = y0 + 6
        pdf.set_fill_color(*SLATE_100)
        pdf.rect(cx, cy, 58, 10, "F")
        pdf.set_draw_color(*GH_TEAL)
        pdf.rect(cx, cy, 58, 10)
        pdf.set_xy(cx + 2, cy + 3)
        pdf.cell(54, 4, c[:32])
        # Fleche vers le centre
        pdf.set_draw_color(*GH_TEAL)
        pdf.set_line_width(0.5)
        pdf.line(cx + 29, cy + 10, center_x, center_y - 10)
    # Producers en bas (ce qu'on fournit)
    pdf.set_font(SANS, "B", 8)
    pdf.set_text_color(*GH_NAVY)
    pdf.set_xy(x0, center_y + 15)
    pdf.cell(0, 4, "En aval (consommateurs) :", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(SANS, "", 7.5)
    pdf.set_text_color(*SLATE_700)
    for i, p in enumerate(producers[:3]):
        cx = x0 + i * 62
        cy = center_y + 22
        pdf.set_fill_color(*SLATE_100)
        pdf.rect(cx, cy, 58, 10, "F")
        pdf.set_draw_color(*GH_NAVY)
        pdf.rect(cx, cy, 58, 10)
        pdf.set_xy(cx + 2, cy + 3)
        pdf.cell(54, 4, p[:32])
        # Fleche depuis le centre
        pdf.set_draw_color(*GH_NAVY)
        pdf.set_line_width(0.5)
        pdf.line(center_x, center_y + 10, cx + 29, cy)
    pdf.set_xy(x0, center_y + 38)
    pdf.set_font(SANS, "I", 7.5)
    pdf.set_text_color(*SLATE_500)
    pdf.cell(0, 4, "Diagramme d'integration , flux de données entre modules",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)


def _perf_chart(pdf, metrics):
    """Mini graphe en barres pour la page performance. metrics = [(label, ms), ...]."""
    x0, y0 = pdf.get_x(), pdf.get_y()
    w = 180
    h = 50
    pdf.set_fill_color(*SLATE_50)
    pdf.rect(x0, y0, w, h, "F")
    pdf.set_draw_color(*SLATE_200)
    pdf.rect(x0, y0, w, h)
    max_v = max(v for _, v in metrics) if metrics else 1
    bar_area_w = w - 80
    for i, (label, val) in enumerate(metrics[:5]):
        by = y0 + 4 + i * 8
        # Label
        pdf.set_font(SANS, "B", 8)
        pdf.set_text_color(*SLATE_700)
        pdf.set_xy(x0 + 3, by)
        pdf.cell(70, 5, label[:40])
        # Barre
        bar_w = (val / max_v) * bar_area_w * 0.85
        color = GH_OK if val < max_v * 0.3 else GH_TEAL if val < max_v * 0.7 else GH_WARN
        pdf.set_fill_color(*color)
        pdf.rect(x0 + 75, by, bar_w, 5, "F")
        # Valeur
        pdf.set_font(SANS, "", 7.5)
        pdf.set_text_color(*SLATE_700)
        pdf.set_xy(x0 + 75 + bar_w + 2, by)
        pdf.cell(30, 5, f"{val} ms" if val < 1000 else f"{val / 1000:.1f} s")
    pdf.set_xy(x0, y0 + h + 2)
    pdf.set_font(SANS, "I", 7.5)
    pdf.set_text_color(*SLATE_500)
    pdf.cell(0, 4, "Graphique , performances typiques sur poste standard",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)


def _feature_schema(pdf, feat_num):
    """
    Dessine un schema vectoriel specifique a la feature , rendu vectoriel
    pur (rect/line/text fpdf2). Chaque feature a sa propre representation
    de sa vue principale.
    """
    x0, y0 = pdf.get_x(), pdf.get_y()
    w, h = 180, 85

    # Cadre + titre bande
    pdf.set_draw_color(*SLATE_200)
    pdf.set_line_width(0.4)
    pdf.rect(x0, y0, w, h)
    pdf.set_fill_color(*GH_NAVY)
    pdf.rect(x0, y0, w, 7, "F")
    pdf.set_font(SANS, "B", 8)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(x0 + 3, y0 + 1.5)
    titles = {
        1: "TABLEAU DE BORD", 2: "SELECTION FICHIERS", 3: "IDENTITOVIGILANCE",
        4: "PMSI PILOT CSV", 5: "INSPECTEUR + CONTROLE PREALABLE", 6: "TABLEAU DE BORD LIVE",
        7: "STRUCTURE", 8: "ANALYSE D'ACTIVITE UM", 9: "IMPORT CSV + HTML->PDF",
        10: "ADMINISTRATION",
    }
    pdf.cell(0, 4, titles.get(feat_num, f"FONCTIONNALITE {feat_num}"))

    cx, cy, cw, ch = x0 + 4, y0 + 10, w - 8, h - 14

    if feat_num == 1:
        # Tableau de bord · 4 indicateurs cards + donut chart
        for i in range(4):
            kx = cx + i * (cw / 4 + 1)
            pdf.set_fill_color(*SLATE_50)
            pdf.rect(kx, cy, cw / 4 - 1, 18, "F")
            pdf.set_draw_color(*SLATE_200)
            pdf.rect(kx, cy, cw / 4 - 1, 18)
            pdf.set_font(SANS, "", 6)
            pdf.set_text_color(*SLATE_500)
            pdf.set_xy(kx + 2, cy + 2)
            labels = ["Fichiers", "IPP uniques", "Collisions", "Formats"]
            pdf.cell(cw / 4 - 4, 3, labels[i])
            pdf.set_font(SANS, "B", 12)
            pdf.set_text_color(*GH_NAVY)
            pdf.set_xy(kx + 2, cy + 6)
            values = ["7", "4821", "147", "3"]
            pdf.cell(cw / 4 - 4, 6, values[i])
        # Donut chart zone
        pdf.set_fill_color(*SLATE_50)
        pdf.rect(cx, cy + 22, cw, ch - 22, "F")
        # Pseudo donut
        import math
        center = (cx + 30, cy + 22 + (ch - 22) / 2)
        radius = 15
        colors = [GH_NAVY, GH_TEAL, GH_WARN, GH_ERR]
        for i in range(36):
            angle = i * 10
            rad = math.radians(angle)
            color = colors[i % 4]
            pdf.set_fill_color(*color)
            pdf.circle(center[0] + radius * math.cos(rad) * 0.6,
                       center[1] + radius * math.sin(rad) * 0.6, 1.5, "F")
        pdf.set_font(SANS, "", 7)
        pdf.set_text_color(*SLATE_500)
        pdf.set_xy(cx + 55, cy + 28)
        pdf.cell(100, 4, "Repartition par format PMSI")

    elif feat_num == 2:
        # Sélection des fichiers · liste de fichiers
        pdf.set_fill_color(*GH_NAVY)
        pdf.rect(cx, cy, cw, 6, "F")
        pdf.set_font(SANS, "B", 6.5)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(cx + 2, cy + 1)
        pdf.cell(40, 4, "NOM")
        pdf.cell(25, 4, "FORMAT")
        pdf.cell(25, 4, "LIGNES")
        pdf.cell(25, 4, "TAILLE")
        files = [
            ("RPS_202407.txt", "RPS", "4 782", "742 Ko"),
            ("RAA_202407.txt", "RAA", "12 450", "1.2 Mo"),
            ("FICHSUP-PSY_202407", "FICHSUP-PSY", "218", "26 Ko"),
            ("RPS_202408.txt", "RPS", "3 984", "618 Ko"),
            ("RAA_202408.txt", "RAA", "11 238", "1.1 Mo"),
            ("RPS_202409.txt", "RPS", "5 021", "779 Ko"),
        ]
        for i, f in enumerate(files):
            row_y = cy + 7 + i * 8
            if i % 2 == 0:
                pdf.set_fill_color(*SLATE_50)
                pdf.rect(cx, row_y, cw, 8, "F")
            pdf.set_font(MONO, "", 6.5)
            pdf.set_text_color(*SLATE_700)
            pdf.set_xy(cx + 2, row_y + 2)
            pdf.cell(40, 4, f[0][:24])
            pdf.set_font(SANS, "B", 6.5)
            pdf.set_text_color(*GH_TEAL)
            pdf.cell(25, 4, f[1])
            pdf.set_font(MONO, "", 6.5)
            pdf.set_text_color(*SLATE_700)
            pdf.cell(25, 4, f[2])
            pdf.cell(25, 4, f[3])

    elif feat_num == 3:
        # Identitovigilance · paires de collisions
        pdf.set_font(SANS, "B", 7)
        pdf.set_text_color(*GH_ERR)
        pdf.set_xy(cx + 2, cy)
        pdf.cell(0, 4, "3 collisions détectées")
        collisions = [
            ("IPP_042A7", "2", "19870415 (12x)  vs  19870514 (2x)"),
            ("IPP_019B2", "3", "20020301 (8x)   vs  20020103 (2x)  vs  20023001 (1x)"),
            ("IPP_073C5", "2", "19951122 (15x)  vs  19951222 (1x)"),
        ]
        for i, c in enumerate(collisions):
            row_y = cy + 8 + i * 16
            pdf.set_fill_color(255, 245, 248)
            pdf.rect(cx, row_y, cw, 14, "F")
            pdf.set_draw_color(*GH_ERR)
            pdf.set_line_width(0.3)
            pdf.rect(cx, row_y, cw, 14)
            pdf.set_font(MONO, "B", 8)
            pdf.set_text_color(*GH_ERR)
            pdf.set_xy(cx + 3, row_y + 2)
            pdf.cell(30, 4, c[0])
            pdf.set_font(SANS, "B", 7)
            pdf.set_text_color(*SLATE_700)
            pdf.cell(15, 4, c[1] + " DDN")
            pdf.set_xy(cx + 3, row_y + 7)
            pdf.set_font(MONO, "", 6.5)
            pdf.set_text_color(*SLATE_500)
            pdf.cell(0, 4, c[2])

    elif feat_num == 4:
        # PMSI Pilot CSV · flux export
        boxes = [
            (cx + 5, cy + 15, 35, 18, SLATE_50, "MPI", "(memoire)"),
            (cx + 70, cy + 5, 40, 15, GH_TEAL, "CSV", "normalise"),
            (cx + 70, cy + 30, 40, 15, GH_NAVY, ".txt", "sanitized"),
            (cx + 135, cy + 5, 35, 15, GH_OK, "BIQuery", "ingest"),
            (cx + 135, cy + 30, 35, 15, GH_WARN, "DRUIDES", "téléversement"),
        ]
        for bx, by, bw, bh, color, label, sublabel in boxes:
            pdf.set_fill_color(*color)
            pdf.rect(bx, by, bw, bh, "F")
            pdf.set_font(SANS, "B", 8)
            fg = (255, 255, 255) if color != SLATE_50 else SLATE_900
            pdf.set_text_color(*fg)
            pdf.set_xy(bx + 2, by + 3)
            pdf.cell(bw - 4, 4, label, align="C")
            pdf.set_font(SANS, "", 6)
            pdf.set_xy(bx + 2, by + 8)
            pdf.cell(bw - 4, 3, sublabel, align="C")
        # Fleches
        pdf.set_draw_color(*SLATE_400)
        pdf.set_line_width(0.6)
        pdf.line(cx + 40, cy + 24, cx + 70, cy + 12)
        pdf.line(cx + 40, cy + 24, cx + 70, cy + 37)
        pdf.line(cx + 110, cy + 12, cx + 135, cy + 12)
        pdf.line(cx + 110, cy + 37, cx + 135, cy + 37)

    elif feat_num == 5:
        # Inspector + Contrôle préalable · terminal decomposition
        pdf.set_fill_color(15, 23, 42)
        pdf.rect(cx, cy, cw, ch, "F")
        pdf.set_font(MONO, "", 6.5)
        pdf.set_text_color(16, 185, 129)  # green
        pdf.set_xy(cx + 2, cy + 2)
        pdf.cell(0, 4, "$ inspect RPS_202407.txt --line 2341")
        pdf.set_xy(cx + 2, cy + 7)
        pdf.set_text_color(148, 163, 184)
        pdf.cell(0, 4, "POS   CHAMP                   VALEUR")
        fields = [
            ("01-09", "FINESS",             "940000001", True),
            ("10-16", "Num sequentiel",     "0000012",   False),
            ("21-40", "IPP",                "IPP_[pseudo]", False),
            ("41-48", "DDN",                "19870415",  False),
            ("67-70", "Mode legal",         "SL",        False),
            ("79-82", "Num UM",             "4001",      False),
        ]
        for i, (pos, label, value, err) in enumerate(fields):
            pdf.set_xy(cx + 2, cy + 13 + i * 5)
            pdf.set_text_color(148, 163, 184)
            pdf.cell(15, 4, pos)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(45, 4, label)
            pdf.set_text_color(225, 29, 72) if err else pdf.set_text_color(34, 197, 94)
            pdf.cell(0, 4, value)
        pdf.set_xy(cx + 2, cy + 13 + 6 * 5 + 3)
        pdf.set_text_color(225, 29, 72)
        pdf.cell(0, 4, "[ERREUR] FINESS incoherent avec lot (attendu 940110018)")

    elif feat_num == 6:
        # Tableau de bord en direct · 4 charts en grille 2x2
        chart_w = cw / 2 - 2
        chart_h = ch / 2 - 2
        for row in range(2):
            for col in range(2):
                gx = cx + col * (chart_w + 2)
                gy = cy + row * (chart_h + 2)
                pdf.set_fill_color(*SLATE_50)
                pdf.rect(gx, gy, chart_w, chart_h, "F")
                pdf.set_draw_color(*SLATE_200)
                pdf.rect(gx, gy, chart_w, chart_h)
                pdf.set_font(SANS, "B", 6.5)
                pdf.set_text_color(*GH_NAVY)
                pdf.set_xy(gx + 2, gy + 2)
                labels_ch = [["File active", "Secteurs ARS"], ["Top 10 UM", "Collisions"]]
                pdf.cell(chart_w - 4, 3, labels_ch[row][col])
                # Mini chart
                if row == 0 and col == 0:
                    # Line chart
                    points_x = [gx + 6 + i * (chart_w - 12) / 8 for i in range(9)]
                    points_y = [gy + chart_h - 4 - (i * 2 + (i % 3) * 3) for i in range(9)]
                    pdf.set_draw_color(*GH_TEAL)
                    pdf.set_line_width(0.6)
                    for j in range(len(points_x) - 1):
                        pdf.line(points_x[j], points_y[j], points_x[j + 1], points_y[j + 1])
                elif row == 0 and col == 1:
                    # Pie
                    pdf.set_fill_color(*GH_TEAL)
                    pdf.circle(gx + chart_w / 2, gy + chart_h / 2 + 2, 8, "F")
                elif row == 1 and col == 0:
                    # Horizontal bars
                    for i in range(5):
                        by = gy + 8 + i * 5
                        bw = (chart_w - 8) * (1 - i * 0.15)
                        pdf.set_fill_color(*GH_NAVY)
                        pdf.rect(gx + 4, by, bw, 3, "F")
                else:
                    # Heatmap (grid of squares)
                    cells_per_row = 6
                    for r in range(3):
                        for c in range(cells_per_row):
                            intensity = (r + c) % 5
                            colors_h = [(230, 240, 250), (180, 205, 230),
                                        (100, 150, 200), (50, 100, 180),
                                        (30, 60, 150)]
                            pdf.set_fill_color(*colors_h[intensity])
                            pdf.rect(gx + 4 + c * 4, gy + 10 + r * 4, 3.5, 3.5, "F")

    elif feat_num == 7:
        # Structure · arbre
        nodes = [
            (cx + cw / 2 - 20, cy + 2, 40, 10, GH_NAVY, "Fondation Vallee"),
            (cx + cw / 4 - 22, cy + 20, 44, 9, GH_TEAL, "Pôle Infanto-juv"),
            (cx + 3 * cw / 4 - 22, cy + 20, 44, 9, (249, 115, 22), "Pôle Intersec"),
            (cx + 8, cy + 40, 30, 8, SLATE_100, "94I01"),
            (cx + 45, cy + 40, 30, 8, SLATE_100, "94I02"),
            (cx + cw - 45, cy + 40, 30, 8, SLATE_100, "94Z01"),
            (cx + 3, cy + 55, 18, 7, SLATE_50, "UM 4001"),
            (cx + 25, cy + 55, 18, 7, SLATE_50, "UM 4002"),
            (cx + 47, cy + 55, 18, 7, SLATE_50, "UM 4010"),
            (cx + 69, cy + 55, 18, 7, SLATE_50, "UM 4011"),
            (cx + cw - 45, cy + 55, 18, 7, SLATE_50, "UM 4050"),
        ]
        for nx, ny, nw, nh, color, label in nodes:
            pdf.set_fill_color(*color)
            pdf.rect(nx, ny, nw, nh, "F")
            pdf.set_draw_color(*SLATE_400)
            pdf.set_line_width(0.2)
            pdf.rect(nx, ny, nw, nh)
            pdf.set_font(SANS, "B", 6)
            fg = (255, 255, 255) if color in (GH_NAVY, GH_TEAL, (249, 115, 22)) else SLATE_900
            pdf.set_text_color(*fg)
            pdf.set_xy(nx + 1, ny + 1.5)
            pdf.cell(nw - 2, 4, label, align="C")
        # Connecteurs
        pdf.set_draw_color(*SLATE_400)
        pdf.set_line_width(0.3)
        pdf.line(cx + cw / 2, cy + 12, cx + cw / 4, cy + 20)
        pdf.line(cx + cw / 2, cy + 12, cx + 3 * cw / 4, cy + 20)
        pdf.line(cx + cw / 4, cy + 29, cx + 23, cy + 40)
        pdf.line(cx + cw / 4, cy + 29, cx + 60, cy + 40)
        pdf.line(cx + 3 * cw / 4, cy + 29, cx + cw - 30, cy + 40)

    elif feat_num == 8:
        # Analyse activite UM · zone de dépôt + liste inactives
        pdf.set_draw_color(*GH_TEAL)
        pdf.set_line_width(0.6)
        pdf.set_dash_pattern(dash=2, gap=2)
        pdf.rect(cx + 5, cy + 3, cw - 10, 20)
        pdf.set_dash_pattern()
        pdf.set_font(SANS, "B", 8)
        pdf.set_text_color(*GH_TEAL)
        pdf.set_xy(cx + 5, cy + 10)
        pdf.cell(cw - 10, 4, "GLISSEZ VOS FICHIERS RPS / RAA ICI", align="C")
        pdf.set_font(SANS, "", 6.5)
        pdf.set_text_color(*SLATE_500)
        pdf.set_xy(cx + 5, cy + 15)
        pdf.cell(cw - 10, 3, "7 fichiers , 50 802 lignes , période 2024 , 3 mois", align="C")
        # Jauges
        pdf.set_fill_color(*GH_OK)
        pdf.rect(cx + 5, cy + 28, (cw - 10) * 0.83, 4, "F")
        pdf.set_fill_color(*SLATE_200)
        pdf.rect(cx + 5 + (cw - 10) * 0.83, cy + 28, (cw - 10) * 0.17, 4, "F")
        pdf.set_font(SANS, "", 6.5)
        pdf.set_text_color(*GH_OK)
        pdf.set_xy(cx + 5, cy + 33)
        pdf.cell(0, 3, "Couverture , 83 %  (5 UM sur 6 actives)")
        # UM inactives
        pdf.set_font(SANS, "B", 7)
        pdf.set_text_color(*GH_ERR)
        pdf.set_xy(cx + 5, cy + 40)
        pdf.cell(0, 3, "UM sans activité , 1")
        for i, (code, label) in enumerate([("4050", "Addictologie ado")]):
            by = cy + 45 + i * 8
            pdf.set_fill_color(255, 245, 248)
            pdf.rect(cx + 5, by, cw - 10, 6, "F")
            pdf.set_font(MONO, "B", 7)
            pdf.set_text_color(*GH_ERR)
            pdf.set_xy(cx + 8, by + 1)
            pdf.cell(20, 4, code)
            pdf.set_font(SANS, "", 6.5)
            pdf.set_text_color(*SLATE_700)
            pdf.cell(0, 4, label)

    elif feat_num == 9:
        # Import CSV · tableau preview
        pdf.set_fill_color(*GH_NAVY)
        pdf.rect(cx, cy, cw, 6, "F")
        pdf.set_font(SANS, "B", 6.5)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(cx + 2, cy + 1)
        pdf.cell(35, 4, "IPP")
        pdf.cell(30, 4, "DDN")
        pdf.cell(20, 4, "SEXE")
        pdf.cell(30, 4, "FORMAT")
        pdf.cell(25, 4, "ANNEE")
        rows = [
            ("IPP_001", "19850312", "M", "RPS", "2024"),
            ("IPP_042", "19920701", "F", "RAA", "2024"),
            ("IPP_129", "20010915", "M", "RPS", "2024"),
            ("IPP_256", "19780322", "F", "EDGAR", "2024"),
            ("IPP_312", "19911201", "M", "RPS", "2024"),
            ("IPP_478", "20050617", "F", "RAA", "2024"),
        ]
        for i, r in enumerate(rows):
            row_y = cy + 7 + i * 7
            if i % 2 == 0:
                pdf.set_fill_color(*SLATE_50)
                pdf.rect(cx, row_y, cw, 7, "F")
            pdf.set_font(MONO, "", 6.5)
            pdf.set_text_color(*SLATE_700)
            pdf.set_xy(cx + 2, row_y + 1.5)
            pdf.cell(35, 4, r[0])
            pdf.cell(30, 4, r[1])
            pdf.cell(20, 4, r[2])
            pdf.set_font(SANS, "B", 6.5)
            pdf.set_text_color(*GH_TEAL)
            pdf.cell(30, 4, r[3])
            pdf.set_font(MONO, "", 6.5)
            pdf.set_text_color(*SLATE_700)
            pdf.cell(25, 4, r[4])

    elif feat_num == 10:
        # Administration · raccourcis clavier
        shortcuts = [
            ("Ctrl+1", "Tableau de bord"),
            ("Ctrl+2", "Sélection des fichiers"),
            ("Ctrl+3", "Identitovigilance"),
            ("Ctrl+4", "PMSI Pilot CSV"),
            ("Ctrl+5", "Import CSV"),
            ("Ctrl+6", "Structure"),
            ("Ctrl+7", "Tutoriel"),
            ("F1", "Manuel HTML"),
            ("F2", "Inspecteur ligne par ligne"),
            ("F3", "Contrôle préalable DRUIDES"),
            ("F4", "Tableau de bord en direct"),
            ("Ctrl+D", "Toggle dark mode"),
        ]
        cols = 2
        per_col = 6
        for i, (k, label) in enumerate(shortcuts):
            col = i // per_col
            row = i % per_col
            rx = cx + col * (cw / cols)
            ry = cy + row * 11
            pdf.set_fill_color(*SLATE_50)
            pdf.rect(rx + 2, ry, 22, 8, "F")
            pdf.set_draw_color(*SLATE_400)
            pdf.rect(rx + 2, ry, 22, 8)
            pdf.set_font(MONO, "B", 7)
            pdf.set_text_color(*GH_NAVY)
            pdf.set_xy(rx + 3, ry + 2)
            pdf.cell(20, 4, k, align="C")
            pdf.set_font(SANS, "", 7)
            pdf.set_text_color(*SLATE_700)
            pdf.set_xy(rx + 26, ry + 2)
            pdf.cell(cw / cols - 30, 4, label)

    # Legende sous le schema
    pdf.set_xy(x0, y0 + h + 2)
    pdf.set_font(SANS, "I", 7.5)
    pdf.set_text_color(*SLATE_500)
    pdf.cell(0, 4, "Schema , representation vectorielle de la vue (rendu pixel-perfect dans l'application)",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(3)


def _section_banner(pdf, text, color=None):
    """Banniere decorative pour separer des sous-sections."""
    if color is None:
        color = GH_TEAL
    x0, y0 = pdf.get_x(), pdf.get_y()
    pdf.set_fill_color(*color)
    pdf.rect(x0, y0, 3, 7, "F")
    pdf.set_xy(x0 + 5, y0)
    pdf.set_font(SANS, "B", 10)
    pdf.set_text_color(*GH_NAVY)
    pdf.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def render_feature(pdf, feat, logo_path, feat_num, total_feats, screenshot_path=None):
    """Rend une feature en 3 pages compactes , vue d'ensemble, workflow, depannage."""
    ft = feat["title"]
    cat = feat["category"]

    # ═══ PAGE 1 · VUE D'ENSEMBLE + CAPTURE ═══
    pdf.add_page()
    _page_header(pdf, logo_path, ft, cat, feat_num, total_feats)
    # Titre de feature
    pdf.set_font(SANS, "B", 9)
    pdf.set_text_color(*GH_TEAL)
    pdf.cell(0, 4, f"FONCTIONNALITE {feat_num:02d} / {total_feats}  ,  {cat.upper()}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(SANS, "B", 18)
    pdf.set_text_color(*GH_NAVY)
    pdf.cell(0, 9, ft, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(SANS, "I", 10)
    pdf.set_text_color(*SLATE_500)
    pdf.multi_cell(0, 5.5, feat["tagline"], new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*GH_TEAL)
    pdf.set_line_width(0.6)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 25, pdf.get_y())
    pdf.ln(4)

    _subheading(pdf, "À quoi ça sert")
    _body_text(pdf, feat["purpose"])

    _subheading(pdf, "Accès")
    _body_text(pdf, feat["access"])

    pdf.ln(SPACE["xs"])
    _subheading(pdf, "Aperçu de la vue")
    # Si un screenshot existe pour cette feature, on l'utilise · sinon
    # on retombe sur le mockup vectoriel.
    if screenshot_path and os.path.exists(screenshot_path):
        ok = _screenshot_box(pdf, screenshot_path,
                             caption=f"Vue {ft.split(' , ')[0]}",
                             max_w=170)
        if not ok:
            _feature_schema(pdf, feat_num)
    else:
        _feature_schema(pdf, feat_num)

    # ═══ PAGE 2 · WORKFLOW + OPTIONS ═══
    pdf.add_page()
    _page_header(pdf, logo_path, ft, cat, feat_num, total_feats)
    _page_title(pdf, 2, "Utilisation")

    _subheading(pdf, "Prérequis")
    _body_text(pdf, feat["prerequisites"])

    _subheading(pdf, "Mode opératoire en 3 étapes")
    for i, key in enumerate(("workflow_1", "workflow_2", "workflow_3"), start=1):
        pdf.set_font(SANS, "B", TYPE["body"])
        pdf.set_text_color(*GH_TEAL)
        pdf.cell(0, 5, f"Étape {i}", new_x="LMARGIN", new_y="NEXT")
        _body_text(pdf, feat[key])

    _subheading(pdf, "Options principales")
    _body_text(pdf, feat["options"])

    # ═══ PAGE 3 · DÉPANNAGE + FAQ + RÉFÉRENCES ═══
    pdf.add_page()
    _page_header(pdf, logo_path, ft, cat, feat_num, total_feats)
    _page_title(pdf, 3, "Dépannage et bonnes pratiques")

    _subheading(pdf, "Dépannage courant")
    _body_text(pdf, feat["troubleshooting"])

    _subheading(pdf, "Questions fréquentes")
    for q, a in feat["faq"][:3]:
        pdf.set_font(SANS, "B", TYPE["small"] + 1)
        pdf.set_text_color(*SLATE_900)
        pdf.multi_cell(0, 5.5, "Q , " + q, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(SANS, "", TYPE["small"] + 1)
        pdf.set_text_color(*SLATE_700)
        pdf.multi_cell(0, 5.5, "R , " + a, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    _subheading(pdf, "Sécurité et RGPD")
    _body_text(pdf, feat["security"][:400] + ("…" if len(feat["security"]) > 400 else ""))

    _alert(pdf, "info",
           "Support , adam.beloucif@psysudparis.fr  ,  "
           "https://github.com/Adam-Blf/sovereign_os_dim/issues")


# ══════════════════════════════════════════════════════════════════════════════
# GENERATION PDF COMPLET
# ══════════════════════════════════════════════════════════════════════════════

def build_pdf(output_path: str) -> str:
    try:
        from fpdf import FPDF
    except ImportError as e:  # pragma: no cover
        print("fpdf2 non installé , pip install fpdf2>=2.8", file=sys.stderr)
        raise SystemExit(1) from e

    class Guide(FPDF):
        def footer(self):
            self.set_y(-15)
            self.set_font(SANS, "I", 8)
            self.set_text_color(*SLATE_400)
            self.cell(
                0, 8,
                f"Sovereign OS DIM, page {self.page_no()} sur {{nb}}, "
                f"Adam Beloucif, Groupement Hospitalier Sud Paris",
                align="C",
            )

    pdf = Guide()
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.alias_nb_pages()

    # Polices Unicode (accents, sigles ATIH/ARS, signes typographiques)
    unicode_ok = _register_fonts(pdf)
    if not unicode_ok:  # pragma: no cover
        print("[WARN] Police TTF Unicode introuvable , accents desactives. "
              "Installer DejaVu (Linux , apt install fonts-dejavu) ou copier "
              "les TTF dans tools/fonts/ pour reactiver.", file=sys.stderr)

    total_feats = len(FEATURES)

    # ══════ PAGE DE GARDE ══════
    pdf.add_page()
    if os.path.exists(LOGO_PATH):
        try:
            pdf.image(LOGO_PATH, x=80, y=30, h=50)
        except Exception:
            pass  # pragma: no cover
    pdf.set_y(95)
    pdf.set_font(SANS, "B", TYPE["display"])
    pdf.set_text_color(*GH_NAVY)
    pdf.cell(0, 14, "SOVEREIGN OS DIM", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font(SANS, "", TYPE["h1"])
    pdf.set_text_color(*SLATE_700)
    pdf.cell(0, 10, "Guide d'utilisation",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(SPACE["lg"])
    pdf.set_draw_color(*GH_TEAL)
    pdf.set_line_width(1.0)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(SPACE["lg"])
    pdf.set_font(SANS, "", TYPE["h3"])
    pdf.set_text_color(*SLATE_500)
    pdf.cell(0, 7, f"Version 37.0, {total_feats} fonctionnalités",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 7,
             "Groupement Hospitalier de Territoire Psychiatrie Sud Paris",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 7,
             "Fondation Vallée et Groupe Hospitalier Paul Guiraud",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(20)
    pdf.set_font(SANS, "I", TYPE["body"])
    pdf.set_text_color(*SLATE_400)
    pdf.cell(0, 5, f"Édition du {date.today().strftime('%d / %m / %Y')}",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 5,
             "Auteur Adam Beloucif, adam.beloucif@psysudparis.fr",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(15)
    pdf.set_font(SANS, "", TYPE["small"])
    pdf.set_text_color(*SLATE_500)
    pdf.multi_cell(
        0, 5,
        "Document destiné au technicien de l'information médicale, au "
        "médecin responsable du service d'information médicale et au "
        "chef de pôle. Chaque fonctionnalité du logiciel y est décrite "
        "sur trois pages, qui expliquent succèssivement son utilité "
        "dans la vie quotidienne, son mode d'emploi étape par étape, "
        "et les pièges à éviter. L'ensemble des références "
        "institutionnelles (Agence Technique de l'Information sur "
        "l'Hospitalisation, Agence Régionale de Santé, textes "
        "réglementaires) a été vérifié sur les sources officielles. "
        "Tous les sigles sont expliqués à leur première apparition, "
        "dans une page de lexique située au début du guide.",
        align="C", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(SPACE["md"])
    pdf.set_fill_color(*GH_GOLD)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(SANS, "B", TYPE["small"])
    pdf.cell(0, 7,
        "  Réforme du financement de la psychiatrie, garantie de "
        "dotation à zéro pour cent en 2029  ",
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
    pdf.set_font(SANS, "", 11)
    pdf.set_text_color(*SLATE_700)
    for i, feat in enumerate(FEATURES, start=1):
        pdf.set_font(SANS, "B", 10)
        pdf.set_text_color(*GH_TEAL)
        pdf.cell(14, 7, f"{i:>2}.", new_x="RIGHT", new_y="TOP")
        pdf.set_font(SANS, "B", 11)
        pdf.set_text_color(*GH_NAVY)
        pdf.cell(0, 7, feat["title"], new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(SANS, "I", 9)
        pdf.set_text_color(*SLATE_500)
        pdf.set_x(pdf.l_margin + 14)
        pdf.cell(0, 5, feat["tagline"], new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # ══════ BLOC INTRODUCTION ══════
    pdf.add_page()
    _page_header(pdf, LOGO_PATH, "Introduction du guide",
                 "Introduction", 0, total_feats)
    _page_title(pdf, 1, "À qui s'adresse ce guide")
    _body_text(pdf,
        "Ce document s'adresse à trois familles de lecteurs travaillant "
        "ensemble dans un hôpital de psychiatrie. La première est "
        "l'équipe technique du service d'information médicale, que "
        "l'on appelle plus brièvement le service DIM (Département "
        "d'Information Médicale). Au sein de cette équipe, le "
        "technicien de l'information médicale, dont le sigle est TIM, "
        "saisit chaque jour les données de soins. Le deuxième lecteur "
        "est le médecin responsable du service, appelé médecin DIM, "
        "qui valide la qualité de ces données avant que l'établissement "
        "ne les envoie à l'État. Le troisième lecteur est le chef de "
        "pôle, c'est-à-dire le responsable d'un grand secteur de "
        "soins de l'hôpital, qui suit l'activité globale grâce aux "
        "tableaux de bord disponibles dans le logiciel.")
    _body_text(pdf,
        "Le guide est volontairement rédigé en français courant, en "
        "expliquant chaque sigle à sa première apparition. Il propose "
        "pour chaque fonctionnalité une description du contexte "
        "métier, le mode d'emploi pas à pas, les pièges à éviter et "
        "les indicateurs de réussite à surveiller. Pour les détails "
        "purement informatiques (organisation du code source, "
        "interfaces de programmation, dépendances logicielles), un "
        "guide développeur séparé est fourni dans le même dépôt.")

    _subheading(pdf, "Lexique des sigles utilisés dans ce guide")
    _body_text(pdf,
        "ATIH signifie Agence Technique de l'Information sur "
        "l'Hospitalisation. C'est l'organisme public français qui "
        "définit les formats officiels des données hospitalières. "
        "Son siège se trouve à Lyon.")
    _body_text(pdf,
        "ARS signifie Agence Régionale de Santé. C'est l'autorité "
        "publique régionale qui valide les transmissions des "
        "hôpitaux. L'agence d'Île-de-France couvre les départements "
        "numéros 75, 77, 78, 91, 92, 93, 94 et 95.")
    _body_text(pdf,
        "DIM signifie Département d'Information Médicale. C'est le "
        "service interne à l'hôpital chargé du traitement "
        "administratif et statistique des soins.")
    _body_text(pdf,
        "TIM signifie Technicien de l'Information Médicale. C'est "
        "l'agent du service d'information médicale qui prépare et "
        "corrige les fichiers transmis à l'État.")
    _body_text(pdf,
        "L'expression médecin DIM désigne le médecin responsable du "
        "service d'information médicale. Il est le seul habilité à "
        "accéder aux données nominatives des patients sans "
        "dérogation particulière, conformément à l'article L. 6113-7 "
        "du Code de la santé publique.")
    _body_text(pdf,
        "PMSI signifie Programme de Médicalisation des Systèmes "
        "d'Information. C'est le système national de comptage et de "
        "description médicale des soins, mis en place en France "
        "depuis le début des années 1980. Il sert à financer les "
        "hôpitaux en fonction de leur activité réelle.")
    _body_text(pdf,
        "RIM-P signifie Recueil d'Informations Médicalisé pour la "
        "Psychiatrie. C'est la version du programme PMSI applicable "
        "aux hôpitaux psychiatriques.")
    _body_text(pdf,
        "RPS signifie Recueil pour Psychiatrie de Séquence. C'est le "
        "fichier qui contient les données d'une période "
        "d'hospitalisation à temps complet d'un patient.")
    _body_text(pdf,
        "RAA signifie Résumé d'Activité Ambulatoire. C'est le "
        "fichier qui contient les actes effectués sans "
        "hospitalisation, par exemple en consultation ou à domicile.")
    _body_text(pdf,
        "RPSA signifie Résumé Anonyme du RPS. C'est la version "
        "dépersonnalisée du fichier RPS, qui est transmise à "
        "l'agence régionale de santé.")
    _body_text(pdf,
        "DRUIDES signifie Dispositif de Remontée Unifiée et "
        "Intégrée des Données des Établissements de Santé. C'est le "
        "logiciel officiel de transmission, déployé en psychiatrie "
        "au mois de janvier 2025.")
    _body_text(pdf,
        "e-PMSI désigne le portail internet de l'Agence Technique "
        "de l'Information sur l'Hospitalisation, sur lequel les "
        "hôpitaux déposent leurs fichiers et consultent leurs "
        "indicateurs de qualité.")
    _body_text(pdf,
        "MAGIC est le logiciel obligatoire qui anonymise les "
        "données patient avant transmission. La version 5.12.0.0 "
        "est obligatoire pour toute la campagne 2026.")
    _body_text(pdf,
        "IPP signifie Identifiant Permanent du Patient. C'est le "
        "numéro unique attribué à un patient lors de son premier "
        "passage à l'hôpital, conservé pour toute la vie.")
    _body_text(pdf,
        "DDN signifie Date De Naissance, exprimée au format année, "
        "mois, jour dans les fichiers transmis à l'État.")
    _body_text(pdf,
        "FINESS signifie Fichier National des Établissements "
        "Sanitaires et Sociaux. C'est la base de l'État qui "
        "attribue à chaque hôpital un numéro à neuf chiffres.")

    pdf.add_page()
    _page_header(pdf, LOGO_PATH, "Lexique (suite)", "Introduction", 0, total_feats)
    _page_title(pdf, 2, "Lexique des sigles , suite")

    _body_text(pdf,
        "MPI signifie Master Patient Index, traduit en français par "
        "registre central des patients. Il s'agit d'une base de "
        "données interne au logiciel, qui regroupe pour chaque "
        "patient toutes les informations connues à son sujet dans "
        "tous les fichiers envoyés à l'État.")
    _body_text(pdf,
        "Le mot identitovigilance désigne la vigilance exercée sur "
        "l'identité du patient. Il regroupe l'ensemble des actions "
        "menées pour s'assurer qu'un même patient n'a qu'une seule "
        "fiche, et qu'aucune fiche ne mélange deux personnes "
        "différentes.")
    _body_text(pdf,
        "On parle de collision lorsque deux fiches d'un même patient "
        "affichent des informations différentes, par exemple deux "
        "dates de naissance distinctes. C'est en général la "
        "conséquence d'une erreur de saisie ou d'un changement de "
        "format historique.")
    _body_text(pdf,
        "DAS signifie Diagnostic Associé Significatif. C'est une "
        "maladie ou un trouble présent chez le patient mais qui "
        "n'est pas la raison principale de son hospitalisation.")
    _body_text(pdf,
        "DP signifie Diagnostic Principal. C'est la raison "
        "principale qui a justifié l'hospitalisation, codée selon "
        "la Classification Internationale des Maladies dans sa "
        "dixième révision, dont le sigle est CIM-10.")
    _body_text(pdf,
        "DAF signifie Dotation Annuelle de Financement. C'est le "
        "mode de financement historique des hôpitaux psychiatriques "
        "publics, en cours de remplacement par un modèle à huit "
        "compartiments.")
    _body_text(pdf,
        "DFA signifie Délégation Financière Anticipée. C'est la "
        "partie du financement qui dépend directement du nombre de "
        "patients suivis dans l'année. Elle représente quinze pour "
        "cent du budget national de la psychiatrie.")
    _body_text(pdf,
        "DQC signifie Dotation Qualité du Codage. C'est la partie "
        "du financement, deux pour cent du total, qui dépend de la "
        "qualité de remplissage des fichiers transmis.")
    _body_text(pdf,
        "GHT signifie Groupement Hospitalier de Territoire. C'est "
        "un ensemble d'hôpitaux qui mutualisent leurs services. Le "
        "groupement de Sud Paris regroupe la Fondation Vallée à "
        "Villejuif et le Groupe Hospitalier Paul Guiraud à "
        "Villejuif et Clamart.")
    _body_text(pdf,
        "CeSPA signifie Centre de Soins Post-Aigus. C'est une "
        "nouvelle structure psychiatrique créée par l'arrêté du 4 "
        "juillet 2025, qui remplace les anciens centres de "
        "post-cure. Elle accueille les patients dont l'état ne "
        "permet pas le retour immédiat à domicile après une "
        "hospitalisation à temps complet.")
    _body_text(pdf,
        "CATTG signifie Centre d'Activités Thérapeutiques et de "
        "Temps de Groupe. C'est une nouvelle structure ambulatoire "
        "créée par le même arrêté de 2025, qui remplace les anciens "
        "centres d'accueil thérapeutique à temps partiel, dont le "
        "sigle historique était CATTP.")
    _body_text(pdf,
        "RGPD signifie Règlement Général sur la Protection des "
        "Données. C'est le règlement européen entré en vigueur en "
        "2018, qui encadre le traitement des données personnelles, "
        "dont les données de santé.")
    _body_text(pdf,
        "FicUM signifie Fichier des Unités Médicales. C'est un "
        "fichier obligatoire depuis janvier 2025, qui décrit toutes "
        "les unités de soins actives de l'hôpital. Chaque unité doit "
        "y figurer pour que ses patients soient pris en compte dans "
        "les transmissions à l'État.")
    _body_text(pdf,
        "SQLite est une technologie de base de données légère, "
        "gérée comme un simple fichier sur l'ordinateur, sans "
        "serveur supplémentaire. Le registre central des patients "
        "du logiciel l'utilise pour conserver les données entre "
        "deux ouvertures.")
    _body_text(pdf,
        "L'expression apprentissage automatique désigne une branche "
        "de l'intelligence artificielle, dans laquelle un programme "
        "apprend à reconnaître des schémas en analysant beaucoup "
        "d'exemples. Trois petits programmes de ce type sont "
        "embarqués dans le logiciel.")
    _body_text(pdf,
        "Un tableau de bord est un écran qui regroupe les "
        "principaux indicateurs sous forme de cartes chiffrées et "
        "de graphiques.")

    pdf.add_page()
    _page_header(pdf, LOGO_PATH, "Contexte 2025-2029", "Introduction", 0, total_feats)
    _page_title(pdf, 3, "Pourquoi un nouvel outil maintenant")

    _body_text(pdf,
        "Trois changements majeurs convergent au moment où ce guide "
        "est rédigé. Premièrement, en janvier 2025, le logiciel "
        "officiel de transmission des données psychiatriques a "
        "changé. L'ancien système, appelé Pivoine, et le contrôle "
        "qualité Visual ont été remplacés par un nouveau logiciel "
        "unique appelé DRUIDES. Tout établissement psychiatrique "
        "doit donc adapter ses procédures.")
    _body_text(pdf,
        "Deuxièmement, le mode de financement des hôpitaux "
        "psychiatriques publics a été refondu en 2022 sous la forme "
        "d'un modèle dit à huit compartiments. Une période de "
        "sécurisation prolongée a été annoncée par la Direction "
        "Générale de l'Offre de Soins en septembre 2025. Cette "
        "sécurisation garantit aux établissements 97,5 pour cent de "
        "leur dotation de référence en 2026, 95 pour cent en 2027, "
        "90 pour cent en 2028, et zéro pour cent à partir de 2029. "
        "Autrement dit, à compter de 2029, chaque erreur dans les "
        "transmissions se traduira directement en perte financière "
        "pour l'hôpital. La pression sur la qualité des données va "
        "donc croître très fortement entre 2027 et 2029.")
    _body_text(pdf,
        "Troisièmement, l'arrêté du 4 juillet 2025 a redéfini les "
        "structures de soins en psychiatrie. Les anciens centres "
        "d'accueil thérapeutique à temps partiel laissent place aux "
        "centres d'activités thérapeutiques et de temps de groupe. "
        "Les centres de post-cure deviennent des centres de soins "
        "post-aigus. Trois grands modes de prise en charge sont "
        "désormais reconnus, à savoir le temps complet "
        "(hospitalisation), le temps partiel (hôpital de jour), et "
        "l'ambulatoire (consultations et soins à domicile, codifié "
        "par la modalité 33).")
    _body_text(pdf,
        "Sovereign OS DIM est l'outil interne mis au point pour "
        "absorber ces trois évolutions sans dépendre des éditeurs "
        "commerciaux dont les coûts de licence et les délais de "
        "mise à jour sont parfois incompatibles avec les "
        "contraintes budgétaires d'un hôpital public.")

    _subheading(pdf, "Légende des bandeaux colorés utilisés dans ce guide")
    _alert(pdf, "info", "Information générale ou rappel de contexte.")
    _alert(pdf, "ok", "Bonne pratique validée par l'équipe d'information médicale, à privilégier.")
    _alert(pdf, "warn", "Point d'attention pouvant impacter la qualité ou la conformité réglementaire.")
    _alert(pdf, "err", "Erreur à éviter absolument, en raison du risque de rejet lors de l'envoi à l'agence régionale de santé.")
    _alert(pdf, "metier", "Indicateur métier, par exemple gain de temps, retour sur investissement ou impact financier.")

    # ══════ RENDU DE CHAQUE FEATURE · 3 PAGES CHACUNE ══════
    for i, feat in enumerate(FEATURES, start=1):
        shot_name = FEATURE_SCREENSHOTS.get(i - 1)
        shot_path = os.path.join(SCREENSHOT_DIR, shot_name) if shot_name else None
        if shot_path and not os.path.exists(shot_path):
            shot_path = None
        try:
            render_feature(pdf, feat, LOGO_PATH, i, total_feats, screenshot_path=shot_path)
        except Exception as e:
            print(f"[ERR] Feature {i} , {feat['title']} , {e}", file=sys.stderr)
            raise

    # ══════ GALERIE · 16 VUES SENTINEL V36 (4 thumbnails par page) ══════
    sentinel_gallery = [
        ("01_tableau de bord.png",   "Tableau de bord principal",         "Quatre indicateurs clés et répartition par format"),
        ("08_cockpit.png",     "Tableau de bord du chef de pôle",   "Vue mensuelle, suivi de la file active sur douze mois"),
        ("09_health.png",      "Surveillance technique",             "Sept vérifications de l'état du système"),
        ("10_ars.png",         "Sentinelle de transmission",         "Prédicteur de rejet, note attribuée à chaque lot"),
        ("11_cespa.png",       "Validateur des nouvelles structures", "Conformité avec l'arrêté du 4 juillet 2025"),
        ("12_diff.png",        "Comparaison de deux mois",           "Détection des écarts inhabituels d'un mois à l'autre"),
        ("13_cim.png",         "Suggesteur de codes maladies",       "Aide au codage par intelligence artificielle locale"),
        ("14_lstm.png",        "Prédicteur de durée de séjour",      "Estimation par grand groupe de diagnostics"),
        ("15_cluster.png",     "Regroupement de profils patients",   "Six archétypes identifiés à partir du registre"),
        ("16_twin.png",        "Simulation financière",              "Projection de l'impact d'une amélioration de codage"),
        ("17_heatmap.png",     "Carte de chaleur géographique",      "Patients suivis par code postal"),
        ("18_pivot.png",       "Tableaux croisés",                   "Exploration libre des données du registre"),
        ("02_modo_files.png",  "Sélection de fichiers",              "Choix et traitement des lots de données"),
        ("03_idv.png",         "Vigilance sur l'identité du patient", "Résolution des conflits de fiches patient"),
        ("19_rgpd.png",        "Centre de conformité",                "Tableau de bord de la protection des données"),
        ("20_audit.png",       "Journal d'audit chaîné",             "Traçabilité immuable de toutes les actions"),
        ("21_workflow.png",    "Chaîne de validation",                "Technicien, médecin, contrôle, transmission"),
    ]

    for page_idx in range(0, len(sentinel_gallery), 4):
        page_items = sentinel_gallery[page_idx:page_idx + 4]
        pdf.add_page()
        _page_header(pdf, LOGO_PATH, "Galerie des vues V36",
                     "Sentinel , Refonte écrans", 0, total_feats)
        _page_title(pdf, page_idx // 4 + 1,
                    f"Galerie des écrans , {page_idx + 1}/{len(sentinel_gallery)}")
        _body_text(pdf,
            "Aperçu visuel des écrans principaux du logiciel. Chaque "
            "vignette présente une fonction du logiciel telle qu'elle "
            "apparaît à l'écran en utilisation réelle. Toutes ces vues "
            "sont accessibles à partir de la barre latérale gauche, en "
            "un seul clic. Les écrans qui s'appuient sur l'intelligence "
            "artificielle utilisent des programmes embarqués dans le "
            "logiciel, sans envoi de données patient vers internet.")
        # Grille 2 × 2
        cell_w, cell_h = 88, 60
        gap_x, gap_y = 8, 12
        for idx, (png, title, sub) in enumerate(page_items):
            col, row = idx % 2, idx // 2
            x0 = pdf.l_margin + col * (cell_w + gap_x)
            y0 = pdf.get_y() + row * (cell_h + gap_y + 14)
            png_path = os.path.join(SCREENSHOT_DIR, png)
            # Cadre
            pdf.set_draw_color(*SLATE_200)
            pdf.set_line_width(0.3)
            pdf.rect(x0, y0, cell_w, cell_h)
            if os.path.exists(png_path):
                try:
                    pdf.image(png_path, x=x0 + 0.5, y=y0 + 0.5,
                              w=cell_w - 1, h=cell_h - 1)
                except Exception:  # pragma: no cover
                    pass
            # Titre + sous-titre
            pdf.set_xy(x0, y0 + cell_h + 1)
            pdf.set_font(SANS, "B", TYPE["small"])
            pdf.set_text_color(*GH_NAVY)
            pdf.cell(cell_w, 4, title, new_x="LMARGIN", new_y="NEXT")
            pdf.set_x(x0)
            pdf.set_font(SANS, "", TYPE["caption"])
            pdf.set_text_color(*SLATE_500)
            pdf.cell(cell_w, 4, sub, new_x="LMARGIN", new_y="NEXT")

    # ══════ PAGE FEUILLE DE ROUTE · MODULES À VENIR ══════
    pdf.add_page()
    _page_header(pdf, LOGO_PATH, "Feuille de route", "Feuille de route",
                 total_feats, total_feats)
    _page_title(pdf, 12, "Modules à venir , plan 2026 et 2027")
    _body_text(pdf,
        "Cette page présente les huit chantiers identifiés avec l'équipe "
        "du service d'information médicale du groupement hospitalier "
        "Sud Paris. Chaque chantier est décrit par son objectif et le "
        "bénéfice attendu pour les soignants ou pour la qualité des "
        "transmissions à l'État. L'ordre de priorité est revu chaque "
        "trimestre, en concertation avec le médecin responsable du "
        "service et le chef de pôle.")

    proposals = [
        ("Sentinelle de transmission",
         "Examine chaque lot de fichiers avant son envoi à l'agence "
         "régionale de santé. Le module passe au crible quinze "
         "contrôles réglementaires et signale les risques de rejet "
         "avant la transmission. Cela évite les allers-retours "
         "entre le technicien et l'agence régionale.",
         "Gain estimé de six à dix heures de travail économisées "
         "chaque mois pour un hôpital de huit cents lits."),
        ("Suggesteur de codes maladies",
         "Propose un diagnostic principal probable à partir des "
         "diagnostics associés et des actes déjà saisis par le "
         "médecin. Le module utilise un programme d'intelligence "
         "artificielle installé localement, sans envoi de données "
         "vers internet.",
         "Référence chiffrée: une étude scientifique du centre "
         "hospitalier universitaire régional de Tours, publiée en "
         "2022, montre un gain moyen de 1 470 euros par séjour "
         "dont le codage est amélioré."),
        ("Tableau de bord du chef de pôle",
         "Vue mensuelle qui regroupe le nombre de patients suivis, "
         "le taux de chaînage entre fichiers, le pourcentage de "
         "diagnostics principaux renseignés, et le score de qualité "
         "du codage. Une alerte visuelle se déclenche si un "
         "indicateur dévie de plus de deux pour cent par rapport "
         "au mois précédent.",
         "Gain de quatre à huit heures économisées chaque mois "
         "sur le travail de pilotage du chef de pôle."),
        ("Surveillance des transmissions en direct",
         "Le logiciel se connecte au système officiel de l'État "
         "pour recevoir les rejets dès qu'ils surviennent. "
         "Lorsqu'un fichier est refusé, un diagnostic préparé "
         "apparaît immédiatement dans Sovereign OS, ce qui évite "
         "au technicien de chercher la cause manuellement.",
         "Réduction de moitié du temps nécessaire pour réagir à "
         "un incident de transmission."),
        ("Validateur des nouvelles structures de soins",
         "Contrôle automatique de la conformité avec l'arrêté du "
         "4 juillet 2025: refus des anciens codes des ateliers "
         "thérapeutiques, acceptation des nouveaux centres de "
         "soins post-aigus et des nouveaux centres d'activités "
         "thérapeutiques de groupe, prise en charge de la "
         "modalité 33 pour les soins à domicile.",
         "Cent pour cent des fichiers de la campagne 2026 alignés "
         "sur le décret."),
        ("Suivi de l'identité nationale de santé",
         "Mesure la part des patients pour lesquels l'identité "
         "nationale de santé, mise en place dans le cadre du "
         "programme Ségur de la santé, est qualifiée. Détecte les "
         "patients pour lesquels la procédure de vérification a "
         "échoué.",
         "Cible de cent pour cent des patients dotés d'une "
         "identité nationale de santé qualifiée d'ici fin 2027."),
        ("Préparation pour la recherche médicale",
         "Aide les chercheurs à extraire des données pour leurs "
         "études en assurant la pseudonymisation automatique, la "
         "vérification que chaque profil concerne au moins cinq "
         "personnes (règle dite de l'anonymat de groupe), et la "
         "conformité avec la méthodologie de référence numéro "
         "sept de la Commission Nationale de l'Informatique et "
         "des Libertés.",
         "Bénéfice: les travaux de recherche du chef de pôle et "
         "des médecins du service sont facilités."),
        ("Simulation financière",
         "Calcule l'impact financier d'une amélioration de la "
         "qualité du codage sur le financement de l'hôpital. "
         "Projette le résultat sur le mois suivant, sur le "
         "trimestre, et sur l'année. Aide à prioriser les actions "
         "de qualité.",
         "Bénéfice: arbitrage stratégique sur les actions à mener "
         "en priorité par l'équipe d'information médicale."),
    ]

    for i, (title, desc, gain) in enumerate(proposals, start=1):
        x0, y0 = pdf.get_x(), pdf.get_y()
        # Bloc card
        pdf.set_fill_color(*SLATE_50)
        pdf.set_draw_color(*SLATE_200)
        # Header de proposition
        pdf.set_font(SANS, "B", TYPE["small"])
        pdf.set_text_color(*GH_TEAL)
        pdf.cell(10, 5, f"#{i:02d}", new_x="RIGHT", new_y="TOP")
        pdf.set_font(SANS, "B", TYPE["body"])
        pdf.set_text_color(*GH_NAVY)
        pdf.cell(0, 5, title, new_x="LMARGIN", new_y="NEXT")
        # Description
        pdf.set_font(SANS, "", TYPE["small"])
        pdf.set_text_color(*SLATE_700)
        pdf.set_x(pdf.l_margin + 10)
        pdf.multi_cell(0, 4.5, desc, new_x="LMARGIN", new_y="NEXT")
        # Gain métier
        pdf.set_font(SANS, "B", TYPE["caption"])
        pdf.set_text_color(*GH_GOLD)
        pdf.set_x(pdf.l_margin + 10)
        pdf.multi_cell(0, 4, gain.upper(), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # ══════ PAGE FINALE · SUPPORT ET CRÉDITS ══════
    pdf.add_page()
    _page_header(pdf, LOGO_PATH, "Support et crédits", "Fin", total_feats, total_feats)
    _page_title(pdf, 13, "Support, crédits, licence")
    _subheading(pdf, "Contact support")
    _body_text(pdf,
        "Adresse électronique directe pour toute question fonctionnelle "
        "ou demande d'assistance , adam.beloucif@psysudparis.fr. Cette "
        "adresse correspond à la période d'alternance de l'auteur au "
        "sein de la Fondation Vallée, prévue jusqu'en septembre 2027. "
        "Toute anomalie peut également être signalée publiquement sur "
        "le suivi des incidents du dépôt en ligne , "
        "https://github.com/Adam-Blf/sovereign_os_dim/issues.")
    _subheading(pdf, "Références institutionnelles , Agence Technique de l'Information sur l'Hospitalisation")
    _body_text(pdf,
        "L'Agence Technique de l'Information sur l'Hospitalisation est "
        "l'organisme public qui définit les formats officiels des "
        "données hospitalières en France. Son siège se situe au 117 "
        "boulevard Marius-Vivier-Merle, dans le troisième arrondissement "
        "de Lyon. La direction générale est assurée par Madame Nathalie "
        "Fourcade depuis le 6 janvier 2025. Le site officiel par lequel "
        "les hôpitaux déposent leurs fichiers s'appelle e-PMSI, "
        "accessible à l'adresse https://www.epmsi.atih.sante.fr. La "
        "notice technique applicable à la campagne 2026 porte la "
        "référence ATIH-294-9-2025 et a été publiée le 21 novembre 2025.")
    _subheading(pdf, "Références institutionnelles , Agence Régionale de Santé d'Île-de-France")
    _body_text(pdf,
        "L'Agence Régionale de Santé d'Île-de-France est l'autorité "
        "publique chargée de valider les transmissions de tous les "
        "hôpitaux de la région. Son siège est situé dans l'immeuble Le "
        "Curve, au 13 rue du Landy, à Saint-Denis (code postal 93200). "
        "Le standard téléphonique est le 01 44 02 00 00. La direction "
        "générale est assurée par Monsieur Denis Robin depuis le 10 "
        "avril 2024. La délégation départementale du Val-de-Marne, "
        "qui couvre le territoire du groupement hospitalier de Sud "
        "Paris, se trouve au 25 chemin des Bassins à Créteil Cedex "
        "(code postal 94010). Le numéro direct de cette délégation est "
        "le 01 49 81 86 04. Le portail de données régionales s'appelle "
        "Datalogue, accessible à l'adresse "
        "https://datalogue.iledefrance.ars.sante.fr.")
    _subheading(pdf, "Le Groupement Hospitalier de Territoire de Psychiatrie Sud Paris")
    _body_text(pdf,
        "La convention constitutive du groupement a été validée par "
        "l'Agence Régionale de Santé d'Île-de-France le 1er juillet "
        "2016, puis signée par les deux établissements membres en "
        "janvier 2017. L'établissement de référence du groupement est "
        "le Groupe Hospitalier Fondation Vallée et Paul Guiraud, dont "
        "le numéro national d'identification est 940140049. Son adresse "
        "administrative est le 54 avenue de la République, à Villejuif "
        "Cedex (code postal 94800). L'autre membre fondateur est "
        "l'Établissement Public de Santé Erasme, situé à Antony. Le "
        "groupement est dédié à la psychiatrie, et couvre une "
        "population d'environ 1,3 million d'habitants. Il assure le "
        "suivi de quelque 37 000 patients chaque année, dispose de 741 "
        "lits d'hospitalisation, et fonctionne avec un budget de "
        "260 millions d'euros par an.")
    _subheading(pdf, "Auteur et collaboration")
    _body_text(pdf,
        "Conception et développement , Adam Beloucif, étudiant en "
        "première année de master en ingénierie des données à l'École "
        "Française d'Électronique et d'Informatique (EFREI), alternant "
        "au sein du service d'information médicale de la Fondation "
        "Vallée. Le logiciel a été développé en collaboration directe "
        "avec l'équipe du service, dans le cadre d'une alternance "
        "couvrant la période 2025-2027.")
    _subheading(pdf, "Licence d'utilisation")
    _body_text(pdf,
        "Le logiciel est distribué sous licence libre. L'utilisation, "
        "la modification et la redistribution sont autorisées pour "
        "tout établissement de santé, sous réserve de conserver les "
        "mentions de paternité du code original. Pour toute question "
        "concernant l'usage du logiciel au sein d'un autre groupement "
        "hospitalier ou d'un autre établissement, il est recommandé "
        "de contacter directement l'auteur via l'adresse électronique "
        "indiquée plus haut.")
    _alert(pdf, "info",
        "Fin du guide métier. La version la plus récente est "
        "publiée sur https://github.com/Adam-Blf/sovereign_os_dim , "
        "une nouvelle édition paraît à chaque fin de trimestre.")

    abs_out = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_out) or ".", exist_ok=True)
    pdf.output(abs_out)
    return abs_out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genere le guide metier PDF (TIM, medecin DIM, chef de pôle). "
                    "Pour le guide developpeur, utiliser generate_guide_dev.py."
    )
    default_output = os.path.join(ROOT, "Sovereign_OS_DIM_Guide.pdf")
    parser.add_argument(
        "--output",
        default=default_output,
        help="Chemin du PDF (defaut , racine du depot)."
    )
    args = parser.parse_args()

    path = build_pdf(args.output)
    size_kb = os.path.getsize(path) // 1024

    # Post-traitement · métadonnées + outline navigable (skill pdf-official).
    # Import via le dossier `tools/` directement, sans dépendre du PYTHONPATH.
    try:
        sys.path.insert(0, HERE)
        from enrich_guide_pdf import enrich  # noqa · resolve via sys.path
        enrich(path, path)
        size_kb = os.path.getsize(path) // 1024
        enriched = "(enrichi , metadata + 16 bookmarks)"
    except Exception as e:  # pragma: no cover
        print(f"[WARN] Enrichissement PDF echoue , {e}", file=sys.stderr)
        enriched = "(brut , enrichissement skip)"

    try:
        from pypdf import PdfReader
        pages = len(PdfReader(path).pages)
        expected = len(FEATURES) * 3 + 5  # +cover, sommaire, intro, roadmap, support
        print(f"[OK] Guide metier genere , {path}")
        print(f"      {pages} pages , {size_kb} Ko , attendu ~{expected} pages "
              f", {enriched}")
        dev_guide = os.path.join(ROOT, "Sovereign_OS_DIM_Guide_Dev.pdf")
        if not os.path.exists(dev_guide):
            print(f"[INFO] Guide developpeur absent , lancer : "
                  f"python tools/generate_guide_dev.py")
    except Exception:
        print(f"[OK] Guide metier genere , {path} , {size_kb} Ko , {enriched}")


if __name__ == "__main__":  # pragma: no cover
    main()
