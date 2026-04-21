# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM — DATA PROCESSOR v3.1
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#  Project : Sovereign OS V35.0 — Station DIM GHT Sud Paris
#  Date    : 2026-03-03
#
#  Description:
#    Moteur de traitement des fichiers ATIH (e-PMSI). Ce module est le cœur
#    métier de Sovereign OS. Il gère :
#      - L'identification automatique de 8 formats ATIH via regex pré-compilés
#      - L'extraction positionnelle des couples (IPP, DDN) dans chaque ligne
#      - La construction d'un Master Patient Index (MPI) cross-fichiers
#      - La détection et résolution des collisions d'identité
#      - L'export CSV normalisé et la purification de fichiers .txt
#
#  Bonnes Pratiques:
#    - Regex compilés une seule fois au chargement du module (performance)
#    - Traitement parallèle via ThreadPoolExecutor (multi-cœur)
#    - Lecture en latin-1 (encodage standard des fichiers ATIH)
#    - Auto-repair des lignes tronquées ou trop longues
#    - Résolution bayésienne des collisions (fréquence + récence)
# ══════════════════════════════════════════════════════════════════════════════

import os
import sys
import glob
import re
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from datetime import datetime
from typing import Optional, Callable

# Force UTF-8 console output on Windows to avoid encoding crashes
sys.stdout.reconfigure(encoding='utf-8')


# ══════════════════════════════════════════════════════════════════════════════
# MATRICE ATIH — 23 formats normalisés, positions 0-indexées
# ══════════════════════════════════════════════════════════════════════════════
# Chaque format ATIH a une longueur fixe et des positions dédiées pour l'IPP
# (Identifiant Permanent du Patient) et la DDN (Date De Naissance).
# Cette matrice est la source de vérité absolue pour le parsing positionnel.
# Ref: Documentation technique ATIH — Formats de recueil 2010–2026
#
# COUVERTURE COMPLÈTE — 4 champs PMSI depuis 2010 :
#   ┌─────────────┬───────────────────────────────────────────────────────┐
#   │ Champ       │ Formats                                               │
#   ├─────────────┼───────────────────────────────────────────────────────┤
#   │ PSY         │ RPS, RAA, RPSA, R3A, FICHSUP-PSY, EDGAR, FICUM-PSY, │
#   │             │ RSF-ACE-PSY                                           │
#   │ MCO         │ RSS/RUM, RSFA, RSFB, RSFC                            │
#   │ SSR/SMR     │ RHS, SSRHA, RAPSS, FICHCOMP-SMR                      │
#   │ HAD         │ RPSS, RAPSS-HAD, FICHCOMP-HAD, SSRHA-HAD             │
#   │ Transversal │ VID-HOSP, ANO-HOSP, FICHCOMP                         │
#   └─────────────┴───────────────────────────────────────────────────────┘
#
# HISTORIQUE DES ÉVOLUTIONS MAJEURES :
#   2010 : RSS v012, RPS P03, RHS S03, RPSS H06 (formats fondateurs)
#   2012 : Introduction du FICHCOMP MO (Matériel onéreux)
#   2013 : VID-HOSP V012, nouveau format de chaînage anonyme
#   2015 : RAA étendu, grille EDGAR normalisée
#   2017 : RSS v013, ajout code retour dans RHS
#   2019 : VID-HOSP V014, extension du chaînage
#   2020 : Harmonisation FICHCOMP transversal, RSF-ACE PSY
#   2022 : SSR renommé en SMR (Soins Médicaux et de Réadaptation)
#   2024 : RSF v2024, FICHCOMP Transports pour SMR
#   2025 : VID-HOSP V015, DRUIDES remplace PIVOINE/VisualQualité (PSY)
#   2026 : VID-HOSP V016, VID-IPP I00A/I00B (PSY)
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# VARIANTES DE FORMAT PAR ANNÉE — Gestion des transitions ATIH
# ══════════════════════════════════════════════════════════════════════════════
# En 2021, certains établissements (ex: Fondation Vallée) ont produit des
# fichiers RPS et RAA avec des longueurs de ligne différentes de la norme
# actuelle. Cela crée deux formats distincts pour les numéros de dossier.
# Pour garantir la cohérence avec les données 2022-2025 déjà dans BIQuery,
# on définit ici les variantes historiques et on auto-détecte le bon format.
#
# RÈGLE : les données 2022-2025 utilisent le format standard (ATIH_MATRIX).
#         les données 2021 peuvent utiliser l'ancien OU le nouveau format.
#         La détection se fait par analyse de la longueur réelle des lignes.
# ══════════════════════════════════════════════════════════════════════════════

# Variantes de format pour les années de transition (2021)
# Clé = format standard, Valeur = liste de variantes { length, ipp, ddn }
# L'auto-détection choisit la variante dont la longueur correspond le mieux
ATIH_FORMAT_VARIANTS = {
    "RPS": [
        # Format P04 (ancien, utilisé par certains établissements en 2021)
        # Certains fichiers RPS de 2021 ont des lignes de 142 ou 148 chars
        {"length": 142, "ipp": (21, 41), "ddn": (41, 49),
         "label": "RPS-P04-142 (ancien 2021)"},
        {"length": 148, "ipp": (21, 41), "ddn": (41, 49),
         "label": "RPS-P04-148 (transition 2021)"},
    ],
    "RAA": [
        # Format ancien RAA : ligne de 86 ou 90 chars au lieu de 96
        {"length": 86, "ipp": (21, 41), "ddn": (41, 49),
         "label": "RAA-ancien-86 (2021)"},
        {"length": 90, "ipp": (21, 41), "ddn": (41, 49),
         "label": "RAA-ancien-90 (transition 2021)"},
    ],
}

ATIH_MATRIX = {
    # ─── FORMATS PSY NATIFS (depuis 2007) ──────────────────────────────────
    # RPS (P05) : pilier de l'hospitalisation psychiatrique.
    # RAA (P06) : ambulatoire, établissements sous DAF uniquement.
    # Positions stables depuis le format P03 (2010).

    "RPS": {
        "length": 154,
        "ipp": (21, 41),
        "ddn": (41, 49),
        "desc": "Résumé Par Séquence — Hospitalisation PSY (Format P05)",
        "field": "PSY",
        "since": 2007,
    },
    "RAA": {
        "length": 96,
        "ipp": (21, 41),
        "ddn": (41, 49),
        "desc": "Recueil Activité Ambulatoire — PSY (Format P06, DAF)",
        "field": "PSY",
        "since": 2007,
    },

    # ─── FORMATS PSY ANONYMISÉS (transmission ARS) ─────────────────────────
    # RPSA et R3A : versions anonymisées du RPS et RAA.
    # IPP remplacé par un numéro anonyme, DDN conservée.
    # Obligatoires pour la transmission aux ARS et à l'ATIH.

    "RPSA": {
        "length": 154,
        "ipp": (21, 41),
        "ddn": (41, 49),
        "desc": "Résumé Par Séquence Anonyme — PSY (ARS)",
        "field": "PSY",
        "since": 2007,
    },
    "R3A": {
        "length": 96,
        "ipp": (21, 41),
        "ddn": (41, 49),
        "desc": "Résumé Activité Ambulatoire Anonyme — PSY (ARS)",
        "field": "PSY",
        "since": 2009,
    },

    # ─── FICHSUP-PSY / EDGAR / FICUM-PSY / RSF-ACE-PSY ────────────────────
    # Fichiers complémentaires spécifiques à la psychiatrie.

    "FICHSUP-PSY": {
        "length": 120,
        "ipp": (21, 41),
        "ddn": (41, 49),
        "desc": "Fichier supplémentaire PSY (isolement, contention, fugue)",
        "field": "PSY",
        "since": 2012,
    },
    "EDGAR": {
        "length": 96,
        "ipp": (21, 41),
        "ddn": (41, 49),
        "desc": "EDGAR — Cotation actes ambulatoires PSY (Entretien, Groupe...)",
        "field": "PSY",
        "since": 2015,
    },
    "FICUM-PSY": {
        "length": 80,
        "ipp": (18, 38),
        "ddn": (38, 46),
        "desc": "FicUM-PSY — Unités médicales psychiatriques (secteurs)",
        "field": "PSY",
        "since": 2017,
    },
    "RSF-ACE-PSY": {
        "length": 310,
        "ipp": (221, 241),
        "ddn": (41, 49),
        "desc": "RSF-ACE PSY — Activité externe psychiatrique (OQN)",
        "field": "PSY",
        "since": 2020,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # FORMATS SSR / SMR — Soins de Suite et Réadaptation (renommé SMR 2022)
    # ═══════════════════════════════════════════════════════════════════════
    # RHS : Résumé Hebdomadaire Standardisé (équivalent du RSS pour le SSR).
    #   Créé en 2003, le RHS est le format fondateur du recueil SSR.
    #   Chaque semaine de présence dans une UM génère un RHS.
    # SSRHA : version anonymisée du RHS pour la transmission ARS/ATIH.
    # RAPSS : Résumé Anonyme Par Sous-Séquence (groupage SSR).
    # FICHCOMP-SMR : fichiers complémentaires SSR/SMR (MO, transports).

    "RHS": {
        "length": 192,
        "ipp": (21, 41),
        "ddn": (41, 49),
        "desc": "Résumé Hebdomadaire Standardisé — SSR/SMR (S04)",
        "field": "SSR",
        "since": 2003,
    },
    "SSRHA": {
        "length": 192,
        "ipp": (21, 41),
        "ddn": (41, 49),
        "desc": "SSR-HA — RHS Anonymisé (transmission ARS/ATIH)",
        "field": "SSR",
        "since": 2009,
    },
    "RAPSS": {
        "length": 140,
        "ipp": (21, 41),
        "ddn": (41, 49),
        "desc": "RAPSS — Résumé Anonyme Par Sous-Séquence SSR/SMR",
        "field": "SSR",
        "since": 2009,
    },
    "FICHCOMP-SMR": {
        "length": 105,
        "ipp": (11, 31),
        "ddn": (31, 39),
        "desc": "FichComp SMR — Données complémentaires SSR (MO, transports)",
        "field": "SSR",
        "since": 2012,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # FORMATS HAD — Hospitalisation À Domicile
    # ═══════════════════════════════════════════════════════════════════════
    # RPSS : Résumé Par Sous-Séquence HAD (équivalent RHS/RSS pour le HAD).
    #   Créé en 2005, le RPSS est le format natif du recueil HAD.
    #   Chaque sous-séquence de prise en charge génère un RPSS.
    # RAPSS-HAD : version anonymisée pour la transmission.
    # FICHCOMP-HAD : fichiers complémentaires HAD (DMI, médicaments).
    # SSRHA-HAD : résumé anonymisé HAD post-groupage (GHT, GHPC).

    "RPSS": {
        "length": 162,
        "ipp": (21, 41),
        "ddn": (41, 49),
        "desc": "RPSS — Résumé Par Sous-Séquence HAD (H07)",
        "field": "HAD",
        "since": 2005,
    },
    "RAPSS-HAD": {
        "length": 162,
        "ipp": (21, 41),
        "ddn": (41, 49),
        "desc": "RAPSS-HAD — Résumé Anonyme HAD (transmission ARS)",
        "field": "HAD",
        "since": 2009,
    },
    "FICHCOMP-HAD": {
        "length": 105,
        "ipp": (11, 31),
        "ddn": (31, 39),
        "desc": "FichComp HAD — Données complémentaires HAD (DMI, médic.)",
        "field": "HAD",
        "since": 2010,
    },
    "SSRHA-HAD": {
        "length": 160,
        "ipp": (21, 41),
        "ddn": (41, 49),
        "desc": "SSRHA-HAD — Résumé anonymisé HAD post-groupage",
        "field": "HAD",
        "since": 2012,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # FORMATS TRANSVERSAUX (communs à tous les champs)
    # ═══════════════════════════════════════════════════════════════════════

    "VID-HOSP": {
        "length": 518,
        "ipp": (265, 285),
        "ddn": (19, 27),
        "desc": "Vidhosp V015/V016 — Chaînage anonyme (obligatoire depuis 2009)",
        "field": "TRANSVERSAL",
        "since": 2009,
    },
    "ANO-HOSP": {
        "length": 206,
        "ipp": (18, 38),
        "ddn": (38, 46),
        "desc": "ANO-HOSP — Anonymisation patient (couverture AMO)",
        "field": "TRANSVERSAL",
        "since": 2009,
    },
    "FICHCOMP": {
        "length": 105,
        "ipp": (11, 31),
        "ddn": (31, 39),
        "desc": "FichComp — Données complémentaires (DMI, isolement, prothèses)",
        "field": "TRANSVERSAL",
        "since": 2010,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # FORMATS MCO — Médecine Chirurgie Obstétrique (interopérabilité)
    # ═══════════════════════════════════════════════════════════════════════

    "RSS": {
        "length": 177,
        "ipp": (12, 32),
        "ddn": (62, 70),
        "desc": "RSS/RUM — MCO (format fondateur depuis 1991)",
        "field": "MCO",
        "since": 1991,
    },
    "RSFA": {
        "length": 310,
        "ipp": (221, 241),
        "ddn": (41, 49),
        "desc": "RSF-A — Activité externe MCO",
        "field": "MCO",
        "since": 2009,
    },
    "RSFB": {
        "length": 350,
        "ipp": (39, 59),
        "ddn": (89, 97),
        "desc": "RSF-B — Séjour MCO",
        "field": "MCO",
        "since": 2009,
    },
    "RSFC": {
        "length": 280,
        "ipp": (30, 50),
        "ddn": (50, 58),
        "desc": "RSF-C — Honoraires MCO",
        "field": "MCO",
        "since": 2009,
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# REGEX PRÉ-COMPILÉS — Performance (compile une seule fois au chargement)
# ══════════════════════════════════════════════════════════════════════════════
# L'identification du format est critique : elle se base sur le NOM du fichier,
# pas son contenu. Les conventions de nommage ATIH sont flexibles (tirets,
# underscores, points), d'où des patterns permissifs.
# L'ORDRE est critique : les formats les plus spécifiques d'abord pour éviter
# les faux positifs (ex: "RPSA" avant "RPS", "R3A" avant "RAA").
# ══════════════════════════════════════════════════════════════════════════════

_FORMAT_RULES = [
    # ─── PSY spécifiques (priorité haute) ──────────────────────────────────
    (re.compile(r"rpsa", re.I), "RPSA"),
    (re.compile(r"r3a", re.I), "R3A"),
    (re.compile(r"fichsup[\-_.]?psy|fichsup|fic[\-_]?sup", re.I), "FICHSUP-PSY"),
    (re.compile(r"edgar", re.I), "EDGAR"),
    (re.compile(r"ficum[\-_.]?psy|ficum", re.I), "FICUM-PSY"),
    (re.compile(r"rsf[\-_.]?ace[\-_.]?psy", re.I), "RSF-ACE-PSY"),

    # ─── SSR / SMR ─────────────────────────────────────────────────────────
    (re.compile(r"fichcomp[\-_.]?smr|fichcomp[\-_.]?ssr", re.I), "FICHCOMP-SMR"),
    (re.compile(r"ssrha[\-_.]?had", re.I), "SSRHA-HAD"),
    (re.compile(r"ssrha", re.I), "SSRHA"),
    (re.compile(r"rapss[\-_.]?had", re.I), "RAPSS-HAD"),
    (re.compile(r"rapss", re.I), "RAPSS"),
    (re.compile(r"rhs", re.I), "RHS"),

    # ─── HAD ───────────────────────────────────────────────────────────────
    (re.compile(r"fichcomp[\-_.]?had", re.I), "FICHCOMP-HAD"),
    (re.compile(r"rpss", re.I), "RPSS"),

    # ─── Transversaux ──────────────────────────────────────────────────────
    (re.compile(r"vid[\-_.]?hosp|vidhosp|\.vid", re.I), "VID-HOSP"),
    (re.compile(r"ano[\-_.]?hosp|anohosp", re.I), "ANO-HOSP"),

    # ─── MCO RSF (ordre C > B > A) ────────────────────────────────────────
    (re.compile(r"rsf[\-_.]?c|rsfc", re.I), "RSFC"),
    (re.compile(r"rsf[\-_.]?b|rsfb", re.I), "RSFB"),
    (re.compile(r"rsf[\-_.]?a|rsfa|rsf[\-_.]?ace", re.I), "RSFA"),

    # ─── MCO + Transversal ─────────────────────────────────────────────────
    (re.compile(r"fichcomp|fic[\-_]?comp|\.com", re.I), "FICHCOMP"),
    (re.compile(r"rss|rum", re.I), "RSS"),

    # ─── PSY de base (en dernier car sous-chaînes courantes) ───────────────
    (re.compile(r"rps", re.I), "RPS"),
    (re.compile(r"raa", re.I), "RAA"),
]

# Seuil minimum de caractères pour qu'une ligne soit considérée comme valide
# (les lignes trop courtes sont du padding ou des artefacts d'export)
_MIN_LINE = 50

# Nombre de lignes à échantillonner pour auto-détecter la longueur dominante
_SAMPLE_SIZE_FOR_VARIANT = 100


class DataProcessor:
    """
    Moteur ATIH haute performance.

    Responsabilités métier :
      1. Scan récursif des dossiers pour trouver les fichiers .txt PMSI
      2. Identification automatique du format ATIH de chaque fichier
      3. Extraction parallèle des couples (IPP, DDN) ligne par ligne
      4. Construction du Master Patient Index (MPI) cross-fichiers
      5. Détection des collisions (un IPP → plusieurs DDN)
      6. Résolution automatique ou manuelle des conflits
      7. Export CSV normalisé avec DDN pivot injectée
      8. Export .txt purifié (sanitized) avec auto-repair
    """

    # __slots__ pour optimiser la mémoire (pas de __dict__)
    __slots__ = (
        "matrix", "mpi", "file_stats", "processed_files",
        "logs", "_progress_cb", "_variant_cache"
    )

    def __init__(self):
        # On copie la matrice globale pour pouvoir la modifier par instance
        self.matrix = dict(ATIH_MATRIX)
        # MPI : { ipp: { "pivot": ddn_or_none, "history": { ddn: [sources] } } }
        self.mpi: dict = {}
        # Stats par fichier traité (lignes total/valid/filtered par nom)
        self.file_stats: dict = {}
        # Liste des fichiers détectés lors du scan
        self.processed_files: list = []
        # Buffer de logs envoyé au frontend (vidé à chaque récupération)
        self.logs: list = []
        # Callback optionnel pour notifier la progression
        self._progress_cb: Optional[Callable] = None
        # Cache des variantes de format détectées par fichier
        self._variant_cache: dict = {}

    # ──────────────────────────────────────────────────────────────────────────
    # LOGGING — Messages horodatés envoyés au frontend via l'API
    # ──────────────────────────────────────────────────────────────────────────

    def _log(self, msg: str, level: str = "INFO"):
        """Ajoute un message horodaté au buffer de logs."""
        self.logs.append({
            "ts": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "level": level,
            "msg": msg,
        })

    def get_logs(self) -> list:
        """Retourne et vide le buffer de logs (pattern drain)."""
        out = self.logs[:]
        self.logs.clear()
        return out

    # ──────────────────────────────────────────────────────────────────────────
    # IDENTIFICATION DU FORMAT — Basée sur le nom de fichier (pas le contenu)
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def identify_format(filename: str) -> Optional[str]:
        """
        Identifie le format ATIH d'un fichier à partir de son nom.

        Pourquoi le nom et pas le contenu ? Parce que tous les formats ATIH
        sont des fichiers texte à largeur fixe sans header. Le seul moyen
        fiable de distinguer un RSS d'un RPS est le nom du fichier, qui
        suit les conventions de l'ATIH.
        """
        base = os.path.basename(filename).lower()
        for rx, fmt in _FORMAT_RULES:
            if rx.search(base):
                return fmt
        return None

    # ──────────────────────────────────────────────────────────────────────────
    # VALIDATION DE LIGNE — Filtre les lignes de padding et artefacts
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _is_line_valid(line: str) -> bool:
        """
        Vérifie qu'une ligne est exploitable.

        On rejette les lignes trop courtes (< 50 chars) et celles qui ne
        contiennent que des zéros/espaces (padding ATIH en fin de fichier).
        """
        if len(line) < _MIN_LINE:
            return False
        if not line.strip("0 "):
            return False
        return True

    # ══════════════════════════════════════════════════════════════════════════
    # NORMALISATION IPP — Cohérence des numéros de dossier (BIQuery compat)
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def normalize_ipp(ipp: str) -> str:
        """
        Normalise un IPP (numéro de dossier) pour garantir la cohérence
        entre les différentes années et formats.

        Pourquoi ? En 2021 à la Fondation Vallée, les RPS et RAA ont produit
        des numéros de dossier dans deux formats différents :
          - Format A : IPP paddé avec des espaces (ex: "12345               ")
          - Format B : IPP paddé avec des zéros  (ex: "00000000000000012345")

        Pour que les données 2021 soient cohérentes avec 2022-2025 (BIQuery),
        on normalise en supprimant le padding gauche (zéros ET espaces),
        tout en conservant la valeur significative.

        Exemples:
          "00000000000000012345" → "12345"
          "12345               " → "12345"
          "ABC-2021-00042      " → "ABC-2021-00042"  (conserve les zéros internes)
          "00042"               → "42"  (numérique pur → strip zéros)
        """
        stripped = ipp.strip()
        if not stripped:
            return stripped

        # Si l'IPP est purement numérique, on supprime les zéros de tête
        # pour obtenir le format cohérent avec BIQuery (2022-2025)
        if stripped.isdigit():
            return stripped.lstrip("0") or "0"

        # Si l'IPP est alphanumérique, on nettoie uniquement les espaces
        # Les zéros internes sont conservés (ils font partie de l'identifiant)
        return stripped

    # ══════════════════════════════════════════════════════════════════════════
    # AUTO-DÉTECTION DE VARIANTE — Format 2021 vs standard
    # ══════════════════════════════════════════════════════════════════════════

    def _detect_format_variant(self, filepath: str, fmt: str) -> dict:
        """
        Auto-détecte la variante de format d'un fichier ATIH.

        Pourquoi ? Les fichiers ATIH sont à largeur fixe, mais en 2021
        (année de transition), certains établissements ont produit des
        fichiers avec des longueurs de ligne différentes du standard.

        Algorithme :
          1. Échantillonne les N premières lignes valides du fichier
          2. Calcule la longueur dominante (mode statistique)
          3. Si elle correspond au format standard → utilise le standard
          4. Sinon → cherche une variante connue dans ATIH_FORMAT_VARIANTS
          5. Si pas de variante connue → fallback sur le standard avec auto-repair

        Le résultat est mis en cache pour éviter de re-scanner.
        """
        # Cache pour éviter de re-analyser le même fichier
        if filepath in self._variant_cache:
            return self._variant_cache[filepath]

        spec = self.matrix[fmt]
        standard_len = spec["length"]

        # Échantillonnage des longueurs de ligne réelles
        lengths = []
        try:
            with open(filepath, "r", encoding="latin-1", errors="replace") as f:
                for raw in f:
                    line = raw.rstrip("\r\n")
                    if self._is_line_valid(line):
                        lengths.append(len(line))
                        if len(lengths) >= _SAMPLE_SIZE_FOR_VARIANT:
                            break
        except OSError:
            self._variant_cache[filepath] = spec
            return spec

        if not lengths:
            self._variant_cache[filepath] = spec
            return spec

        # Calcul de la longueur dominante (mode)
        from collections import Counter
        dominant_len = Counter(lengths).most_common(1)[0][0]

        # Si la longueur dominante correspond au standard → on garde
        if abs(dominant_len - standard_len) <= 2:
            self._variant_cache[filepath] = spec
            return spec

        # Sinon, cherche une variante connue
        variants = ATIH_FORMAT_VARIANTS.get(fmt, [])
        best_variant = None
        best_delta = float("inf")

        for var in variants:
            delta = abs(dominant_len - var["length"])
            if delta < best_delta:
                best_delta = delta
                best_variant = var

        if best_variant and best_delta <= 2:
            # Variante trouvée ! On construit un spec complet
            result = {
                **spec,
                "length": best_variant["length"],
                "ipp": best_variant["ipp"],
                "ddn": best_variant["ddn"],
                "_variant": best_variant.get("label", "variant"),
            }
            self._log(
                f"🔀 Variante détectée : {os.path.basename(filepath)} → "
                f"{best_variant.get('label', 'inconnu')} "
                f"(longueur dominante: {dominant_len})"
            )
            self._variant_cache[filepath] = result
            return result

        # Pas de variante connue → fallback standard avec warning
        self._log(
            f"⚠️ Longueur inattendue : {os.path.basename(filepath)} → "
            f"{dominant_len} chars (attendu {standard_len}). "
            f"Utilisation du format standard avec auto-repair.",
            "WARN"
        )
        self._variant_cache[filepath] = spec
        return spec

    # ══════════════════════════════════════════════════════════════════════════
    # SCAN — Découverte récursive des fichiers .txt PMSI
    # ══════════════════════════════════════════════════════════════════════════

    def scan_directory(self, folder: str) -> list:
        """
        Scanne un dossier de manière récursive pour trouver tous les .txt.
        Chaque fichier est identifié (format ATIH) et pesé (taille en KB).
        """
        if not os.path.isdir(folder):
            self._log(f"Dossier introuvable : {folder}", "ERROR")
            return []

        # Scan des fichiers .txt ET .csv (support multi-format demandé)
        txt_files = glob.glob(os.path.join(folder, "**", "*.txt"), recursive=True)
        csv_files = glob.glob(os.path.join(folder, "**", "*.csv"), recursive=True)
        files = sorted(set(txt_files + csv_files))
        self._log(f"📂 Scan : {folder} → {len(files)} fichier(s) (.txt + .csv)")

        out = []
        for fp in files:
            fmt = self.identify_format(fp)
            try:
                sz = os.path.getsize(fp) / 1024
            except OSError:
                sz = 0
            out.append({
                "path": fp,
                "name": os.path.basename(fp),
                "format": fmt or "INCONNU",
                "size_kb": round(sz, 1),
                "dir": os.path.dirname(fp),
            })
        return out

    def scan_multiple_directories(self, folders: list) -> list:
        """
        Scanne plusieurs dossiers et déduplique les fichiers trouvés.
        On utilise un set de chemins pour garantir l'unicité.
        """
        all_files, seen = [], set()
        for folder in folders:
            for f in self.scan_directory(folder):
                if f["path"] not in seen:
                    seen.add(f["path"])
                    all_files.append(f)
        self._log(f"📊 Total unique : {len(all_files)} fichier(s)")
        self.processed_files = all_files
        return all_files

    # ══════════════════════════════════════════════════════════════════════════
    # PROCESSING — Extraction parallèle des couples (IPP, DDN)
    # ══════════════════════════════════════════════════════════════════════════

    def _process_single_file(self, finfo: dict) -> dict:
        """
        Traite un seul fichier ATIH. Appelé en parallèle par le pool.

        Pour chaque ligne valide du fichier :
          1. Auto-détection de la variante de format (2021 vs standard)
          2. Auto-repair : tronque ou padde la ligne à la longueur détectée
          3. Extraction positionnelle de l'IPP et de la DDN
          4. Normalisation de l'IPP (cohérence BIQuery 2022-2025)
          5. Stockage dans le MPI local (fusionné plus tard avec le MPI global)
        """
        fp = finfo["path"]
        fmt = finfo["format"]

        # On ignore les fichiers de format inconnu (pas dans la matrice ATIH)
        if fmt == "INCONNU" or fmt not in self.matrix:
            return {"skip": True, "name": finfo["name"]}

        # Auto-détection de la variante de format (gère les fichiers 2021
        # de Fondation Vallée qui ont des longueurs différentes)
        spec = self._detect_format_variant(fp, fmt)

        i0, i1 = spec["ipp"]   # Bornes de l'IPP (start, end)
        d0, d1 = spec["ddn"]   # Bornes de la DDN (start, end)
        exp_len = spec["length"]  # Longueur attendue de la ligne
        max_pos = max(i1, d1)    # Position max nécessaire dans la ligne
        is_variant = "_variant" in spec  # True si format non-standard détecté

        local_mpi: dict = {}
        stats = {
            "lines_total": 0, "lines_valid": 0, "lines_filtered": 0,
            "ipp_normalized": 0,  # Compteur d'IPP normalisés (format 2021)
        }

        try:
            # Lecture en latin-1 : encodage standard des fichiers ATIH
            # (les caractères > 127 sont rares mais possibles dans les noms)
            with open(fp, "r", encoding="latin-1", errors="replace") as f:
                for raw in f:
                    stats["lines_total"] += 1
                    line = raw.rstrip("\r\n")

                    # Filtrage des lignes invalides (padding, trop courtes)
                    if not self._is_line_valid(line):
                        stats["lines_filtered"] += 1
                        continue

                    # Auto-repair : normalisation de la longueur de ligne
                    # Les fichiers ATIH sont à largeur fixe, mais certains
                    # exports ajoutent ou suppriment des caractères en fin
                    ll = len(line)
                    if ll > exp_len:
                        line = line[:exp_len]
                    elif ll < exp_len:
                        line = line.ljust(exp_len)

                    # Vérification que la ligne est assez longue pour extraire
                    if len(line) < max_pos:
                        stats["lines_filtered"] += 1
                        continue

                    # Extraction positionnelle de l'IPP et DDN
                    raw_ipp = line[i0:i1].strip()
                    ddn = line[d0:d1].strip()

                    # Normalisation de l'IPP pour cohérence BIQuery
                    # Important : garantit que les données 2021 (Fondation Vallée)
                    # utilisent le même format que les données 2022-2025
                    ipp = self.normalize_ipp(raw_ipp)
                    if ipp != raw_ipp:
                        stats["ipp_normalized"] += 1

                    # Rejet des IPP/DDN vides ou contenant uniquement des zéros
                    if not ipp or not ipp.strip("0 "):
                        stats["lines_filtered"] += 1
                        continue
                    if not ddn or not ddn.strip("0 "):
                        stats["lines_filtered"] += 1
                        continue

                    # Construction du MPI local (par fichier)
                    if ipp not in local_mpi:
                        local_mpi[ipp] = {}
                    if ddn not in local_mpi[ipp]:
                        local_mpi[ipp][ddn] = []
                    src = finfo["name"]
                    if src not in local_mpi[ipp][ddn]:
                        local_mpi[ipp][ddn].append(src)

                    stats["lines_valid"] += 1

        except (IOError, OSError) as e:
            return {"skip": True, "name": finfo["name"], "error": str(e)}

        # Log si des IPP ont été normalisés (transparence)
        if stats["ipp_normalized"] > 0:
            self._log(
                f"🔧 {finfo['name']} : {stats['ipp_normalized']} IPP normalisés "
                f"(cohérence BIQuery)"
            )

        return {
            "skip": False,
            "name": finfo["name"],
            "format": fmt,
            "variant": spec.get("_variant"),  # None si format standard
            "local_mpi": local_mpi,
            "stats": stats,
        }

    def process_files(self, file_list: list) -> dict:
        """
        Traite tous les fichiers en parallèle et fusionne les MPI locaux.

        Workflow :
          1. Chaque fichier est traité en parallèle (ThreadPoolExecutor)
          2. Les MPI locaux sont fusionnés dans le MPI global
          3. On compte les IPP uniques et les collisions
        """
        self.mpi = {}
        totals = {
            "files_processed": 0, "files_skipped": 0,
            "lines_total": 0, "lines_valid": 0, "lines_filtered": 0,
            "ipp_unique": 0, "collisions": 0
        }

        # Le nombre de workers est adapté à la taille du batch (max 8)
        workers = min(8, max(1, len(file_list)))
        results = []

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(self._process_single_file, f): f
                for f in file_list
            }
            for future in as_completed(futures):
                results.append(future.result())

        # Fusion des MPI locaux dans le MPI global
        for res in results:
            if res.get("skip"):
                totals["files_skipped"] += 1
                if res.get("error"):
                    self._log(
                        f"❌ Erreur : {res['name']} — {res['error']}", "ERROR"
                    )
                continue

            totals["files_processed"] += 1
            s = res["stats"]
            totals["lines_total"] += s["lines_total"]
            totals["lines_valid"] += s["lines_valid"]
            totals["lines_filtered"] += s["lines_filtered"]

            self.file_stats[res["name"]] = {
                "format": res["format"], **s
            }

            # Merge du MPI local dans le MPI global
            # Si un IPP est déjà connu, on ajoute les nouvelles DDN trouvées
            for ipp, ddns in res["local_mpi"].items():
                if ipp not in self.mpi:
                    self.mpi[ipp] = {"pivot": None, "history": {}}
                for ddn, sources in ddns.items():
                    if ddn not in self.mpi[ipp]["history"]:
                        self.mpi[ipp]["history"][ddn] = []
                    for src in sources:
                        if src not in self.mpi[ipp]["history"][ddn]:
                            self.mpi[ipp]["history"][ddn].append(src)

        totals["ipp_unique"] = len(self.mpi)
        totals["collisions"] = sum(
            1 for d in self.mpi.values() if len(d["history"]) > 1
        )

        self._log(
            f"✅ {totals['files_processed']} fichiers traités en parallèle · "
            f"{totals['lines_valid']:,} lignes · "
            f"{totals['ipp_unique']:,} IPP · "
            f"{totals['collisions']} collisions"
        )
        return totals

    # ══════════════════════════════════════════════════════════════════════════
    # MPI — Master Patient Index (gestion des collisions d'identité)
    # ══════════════════════════════════════════════════════════════════════════

    def get_collisions(self) -> list:
        """
        Retourne la liste des IPP ayant plusieurs DDN (collisions).

        Chaque collision contient :
          - ipp : l'identifiant patient
          - pivot : la DDN de référence choisie (ou None)
          - options : les DDN candidates triées par fréquence décroissante
          - total_sources : nombre total de fichiers impliqués
        """
        cols = []
        for ipp, data in self.mpi.items():
            if len(data["history"]) > 1:
                opts = sorted(
                    [{"ddn": d, "count": len(s), "sources": s[:5]}
                     for d, s in data["history"].items()],
                    key=lambda x: x["count"], reverse=True,
                )
                cols.append({
                    "ipp": ipp,
                    "pivot": data["pivot"],
                    "options": opts,
                    "total_sources": sum(o["count"] for o in opts),
                })
        # Tri par nombre de sources décroissant (les plus critiques en premier)
        cols.sort(key=lambda x: x["total_sources"], reverse=True)
        return cols

    def set_pivot(self, ipp: str, ddn: str) -> bool:
        """
        Définit manuellement la DDN pivot (référence) pour un IPP donné.

        La DDN pivot sera injectée dans les exports CSV et .txt purifiés,
        remplaçant toutes les autres DDN trouvées pour cet IPP.
        """
        if ipp in self.mpi:
            self.mpi[ipp]["pivot"] = ddn
            self._log(f"🎯 Pivot défini : {ipp} → {ddn}")
            return True
        return False

    def auto_resolve_all(self) -> int:
        """
        Résolution automatique de toutes les collisions non résolues.

        Stratégie bayésienne simple : pour chaque IPP en conflit, on choisit
        la DDN qui apparaît dans le plus grand nombre de fichiers sources.
        En cas d'égalité, on prend la DDN la plus récente (tri lexicographique
        AAAAMMJJ, donc la plus grande = la plus récente).
        """
        n = 0
        for ipp, data in self.mpi.items():
            if len(data["history"]) > 1 and data["pivot"] is None:
                best = max(
                    data["history"].keys(),
                    key=lambda d: (len(data["history"][d]), d)
                )
                data["pivot"] = best
                n += 1
        self._log(f"🔮 Auto-résolution : {n} pivots définis")
        return n

    def get_mpi_stats(self) -> dict:
        """Retourne les statistiques globales du MPI."""
        total = len(self.mpi)
        collisions = sum(
            1 for d in self.mpi.values() if len(d["history"]) > 1
        )
        resolved = sum(
            1 for d in self.mpi.values()
            if len(d["history"]) > 1 and d["pivot"] is not None
        )
        return {
            "total_ipp": total,
            "collisions": collisions,
            "resolved": resolved,
            "pending": collisions - resolved,
        }

    # ══════════════════════════════════════════════════════════════════════════
    # INSPECTION — Analyse ligne par ligne pour le terminal UI
    # ══════════════════════════════════════════════════════════════════════════

    def inspect_file(self, filepath: str) -> dict:
        """
        Analyse un fichier ligne par ligne pour l'Inspector Terminal du frontend.

        Chaque ligne est classée :
          - OK : ligne valide, IPP/DDN extraits avec succès
          - COLLISION : IPP connu avec plusieurs DDN dans le MPI
          - FILTERED : ligne rejetée (trop courte, padding, etc.)
          - ERROR : ligne hors limites (ne peut pas être parsée)

        Limité à 3000 lignes pour ne pas saturer le frontend.
        """
        fmt_key = self.identify_format(filepath)
        if not fmt_key or fmt_key not in self.matrix:
            return {"error": f"Format inconnu : {os.path.basename(filepath)}"}

        spec = self.matrix[fmt_key]
        i0, i1 = spec["ipp"]
        d0, d1 = spec["ddn"]
        exp_len = spec["length"]

        lines = []
        errors = 0

        try:
            with open(filepath, "r", encoding="latin-1", errors="replace") as f:
                for num, raw in enumerate(f, 1):
                    line = raw.rstrip("\r\n")
                    entry = {
                        "num": num,
                        "raw": line[:120],  # Troncature pour le frontend
                        "status": "OK",
                        "ipp": "",
                        "ddn": "",
                        "repair": None,
                    }

                    if len(line) < _MIN_LINE:
                        entry["status"] = "FILTERED"
                        entry["repair"] = f"< {_MIN_LINE} cars"
                        errors += 1
                    elif not line.strip("0 "):
                        entry["status"] = "FILTERED"
                        entry["repair"] = "Padding (zéros)"
                        errors += 1
                    else:
                        # Auto-repair : ajustement de la longueur
                        if len(line) > exp_len:
                            entry["repair"] = f"Tronquée {len(line)}→{exp_len}"
                            line = line[:exp_len]
                        elif len(line) < exp_len:
                            entry["repair"] = f"Paddée {len(line)}→{exp_len}"
                            line = line.ljust(exp_len)

                        if len(line) >= max(i1, d1):
                            ipp = line[i0:i1].strip()
                            ddn = line[d0:d1].strip()
                            entry["ipp"] = ipp
                            entry["ddn"] = ddn
                            # Marquage des collisions connues dans le MPI
                            if ipp in self.mpi and len(self.mpi[ipp]["history"]) > 1:
                                entry["status"] = "COLLISION"
                                errors += 1
                        else:
                            entry["status"] = "ERROR"
                            entry["repair"] = "Hors limites"
                            errors += 1

                    lines.append(entry)
                    # Protection mémoire : on limite à 3000 lignes
                    if num >= 3000:
                        break
        except OSError as e:
            return {"error": str(e)}

        return {
            "filename": os.path.basename(filepath),
            "format": fmt_key,
            "total_lines": len(lines),
            "errors": errors,
            "lines": lines,
        }

    # ══════════════════════════════════════════════════════════════════════════
    # EXPORT CSV PILOT — Données normalisées avec DDN pivot injectée
    # ══════════════════════════════════════════════════════════════════════════

    def export_csv(self, file_list: list, output_dir: str) -> dict:
        """
        Génère un fichier CSV par fichier ATIH traité.

        Structure du CSV : IPP;DDN;FORMAT;NOM_FICHIER;LIGNE_BRUTE
        La DDN pivot est injectée : si un IPP a une collision résolue,
        la DDN originale est remplacée par la DDN pivot dans l'export.
        """
        os.makedirs(output_dir, exist_ok=True)
        generated = []
        stats = {
            "csv_count": 0, "lines_exported": 0,
            "ddn_corrected": 0, "files_skipped": 0
        }

        for finfo in file_list:
            fmt = finfo["format"]
            if fmt == "INCONNU" or fmt not in self.matrix:
                stats["files_skipped"] += 1
                continue

            spec = self.matrix[fmt]
            i0, i1 = spec["ipp"]
            d0, d1 = spec["ddn"]
            exp_len = spec["length"]
            max_pos = max(i1, d1)
            src = finfo["name"]
            name, ext = os.path.splitext(src)
            csv_path = os.path.join(output_dir, f"{name}_PILOT{ext}")

            try:
                with open(finfo["path"], "r", encoding="latin-1",
                          errors="replace") as fi, \
                     open(csv_path, "w", encoding="utf-8", newline="") as fo:

                    fo.write("IPP;DDN;FORMAT;NOM_FICHIER;LIGNE_BRUTE\n")

                    for raw in fi:
                        line = raw.rstrip("\r\n")
                        if not self._is_line_valid(line):
                            continue
                        if len(line) > exp_len:
                            line = line[:exp_len]
                        elif len(line) < exp_len:
                            line = line.ljust(exp_len)
                        if len(line) < max_pos:
                            continue

                        ipp = line[i0:i1].strip()
                        ddn_out = line[d0:d1].strip()

                        # Injection de la DDN pivot si disponible
                        if ipp in self.mpi and self.mpi[ipp]["pivot"]:
                            piv = self.mpi[ipp]["pivot"]
                            if line[d0:d1].strip() != piv:
                                ddn_len = d1 - d0
                                line = (
                                    line[:d0]
                                    + piv.ljust(ddn_len)
                                    + line[d1:]
                                )
                                ddn_out = piv
                                stats["ddn_corrected"] += 1

                        esc = line.replace('"', '""')
                        fo.write(f'{ipp};{ddn_out};{fmt};{src};"{esc}"\n')
                        stats["lines_exported"] += 1

                generated.append({
                    "name": os.path.basename(csv_path),
                    "path": csv_path,
                    "format": fmt,
                })
                stats["csv_count"] += 1
            except OSError as e:
                self._log(f"❌ Erreur export : {src} — {e}", "ERROR")
                stats["files_skipped"] += 1

        self._log(
            f"📦 Export : {stats['csv_count']} CSV · "
            f"{stats['lines_exported']:,} lignes · "
            f"{stats['ddn_corrected']} DDN corrigées"
        )
        return {"stats": stats, "files": generated, "output_dir": output_dir}

    # ══════════════════════════════════════════════════════════════════════════
    # EXPORT .TXT PURIFIÉ (sanitized) — Fichier nettoyé avec pivot injecté
    # ══════════════════════════════════════════════════════════════════════════

    def export_sanitized_txt(self, filepath: str, output_dir: str) -> dict:
        """
        Réécrit un fichier .txt purifié :
          - Lignes invalides supprimées
          - Auto-repair appliqué (troncature/padding)
          - DDN pivot injectée (remplacement in-place)

        Le fichier résultant est un fichier ATIH conforme, prêt à être
        réinjecté dans la chaîne e-PMSI ou ePMSI-Pilot.
        """
        fmt = self.identify_format(filepath)
        if not fmt or fmt not in self.matrix:
            return {"error": "Format inconnu"}

        spec = self.matrix[fmt]
        i0, i1 = spec["ipp"]
        d0, d1 = spec["ddn"]
        exp_len = spec["length"]
        max_pos = max(i1, d1)

        os.makedirs(output_dir, exist_ok=True)
        base = os.path.basename(filepath)
        name, ext = os.path.splitext(base)
        out_name = f"{name}_SANITIZED{ext}"
        out_path = os.path.join(output_dir, out_name)

        stats = {"in": 0, "out": 0, "repaired": 0, "pivoted": 0}

        try:
            with open(filepath, "r", encoding="latin-1", errors="replace") as fi, \
                 open(out_path, "w", encoding="latin-1", newline="") as fo:
                for raw in fi:
                    stats["in"] += 1
                    line = raw.rstrip("\r\n")

                    if not self._is_line_valid(line):
                        continue

                    if len(line) > exp_len:
                        line = line[:exp_len]
                        stats["repaired"] += 1
                    elif len(line) < exp_len:
                        line = line.ljust(exp_len)
                        stats["repaired"] += 1

                    if len(line) < max_pos:
                        continue

                    # Injection de la DDN pivot si disponible
                    ipp = line[i0:i1].strip()
                    if ipp in self.mpi and self.mpi[ipp]["pivot"]:
                        piv = self.mpi[ipp]["pivot"]
                        if line[d0:d1].strip() != piv:
                            line = (
                                line[:d0]
                                + piv.ljust(d1 - d0)
                                + line[d1:]
                            )
                            stats["pivoted"] += 1

                    fo.write(line + "\n")
                    stats["out"] += 1
        except OSError as e:
            return {"error": str(e)}

        self._log(
            f"🧹 Sanitized : {base} → {stats['out']}/{stats['in']} lignes · "
            f"{stats['pivoted']} pivots injectés"
        )
        return {"path": out_path, "name": out_name, "stats": stats}

    # ══════════════════════════════════════════════════════════════════════════
    # STATISTIQUES PAR FORMAT — Pour le dashboard Chart.js
    # ══════════════════════════════════════════════════════════════════════════

    def get_format_breakdown(self) -> list:
        """
        Comptage des fichiers par format ATIH.
        Retourne une liste triée par count décroissant pour Chart.js.
        """
        counts = defaultdict(int)
        for f in self.processed_files:
            counts[f["format"]] += 1
        return [
            {"format": k, "count": v}
            for k, v in sorted(counts.items(), key=lambda x: -x[1])
        ]

    # ══════════════════════════════════════════════════════════════════════════
    # FILE ACTIVE — KPI central du rapport d'activité annuel DIM PSY
    # ══════════════════════════════════════════════════════════════════════════
    # Pourquoi spécifique à la station ?
    #   Ni CPage (facturation) ni DxCare (dossier patient) ne calculent la
    #   "file active PSY" au sens PMSI : c'est un dé-dédoublonnage d'IPP sur
    #   TOUS les recueils (RPS hospit + RAA/EDGAR ambu + RPSS HDJ + CMP), pour
    #   une période donnée. C'est le TIM qui produit ce chiffre chaque année.
    #
    # Méthode :
    #   1. L'année est extraite du NOM de fichier (convention ATIH standard :
    #      "RPS_2024.txt", "EDGAR-2024.txt", etc.). Regex sur 4 chiffres
    #      commençant par 20.
    #   2. Chaque fichier rapporte un set d'IPP. On groupe par (année, format).
    #   3. L'union des sets par année donne la file active globale ; par
    #      champ (PSY / SSR / HAD / MCO) elle donne la file active sectorielle.
    #
    # Le résultat est une structure directement exploitable par le frontend
    # pour un tableau par année ou un line chart d'évolution pluriannuelle.

    _YEAR_RE = re.compile(r"(?:^|[^0-9])(20\d{2})(?:[^0-9]|$)")

    def _year_from_filename(self, name: str) -> Optional[str]:
        """Extrait une année 20xx du nom de fichier, None si absente."""
        m = self._YEAR_RE.search(name)
        return m.group(1) if m else None

    # ══════════════════════════════════════════════════════════════════════════
    # PARCOURS CROSS-MODALITÉS — Patients vus en hospit + CMP + HDJ, etc.
    # ══════════════════════════════════════════════════════════════════════════
    # Cas d'usage DIM PSY :
    #   Un patient psychiatrique chronique alterne souvent entre hospitalisation
    #   complète (RPS), hôpital de jour (RPSS), et suivi ambulatoire CMP (EDGAR,
    #   RAA). Le TIM a besoin d'identifier ces patients "complexes" pour :
    #     - les indicateurs HAS (continuité de soins)
    #     - les revues de cas équipe (staff)
    #     - la file active sectorielle (comptage unique)
    #
    # Ni CPage ni DxCare ne produisent cette vue : CPage ne voit que la
    # facturation (pas l'ambulatoire gratuit), DxCare ne fait que par patient.

    def get_cross_modality_patients(
        self, min_formats: int = 2, limit: int = 100
    ) -> list:
        """
        Liste les IPP qui apparaissent dans >= `min_formats` formats ATIH
        distincts. Triée par nombre de formats décroissant — les patients
        "les plus complexes" en premier.

        Chaque entrée : {
            "ipp": str,
            "formats": [list triée de formats ATIH],
            "fields": [champs PMSI touchés — PSY, SSR, HAD, MCO],
            "years": [années d'apparition],
            "sources_count": int  (nombre total de fichiers-source distincts)
        }
        """
        results = []
        for ipp, data in self.mpi.items():
            formats_seen: set[str] = set()
            fields_seen: set[str] = set()
            years_seen: set[str] = set()
            sources: set[str] = set()

            for _ddn, srcs in data["history"].items():
                for src in srcs:
                    sources.add(src)
                    stats = self.file_stats.get(src, {})
                    fmt = stats.get("format", "INCONNU")
                    if fmt and fmt != "INCONNU":
                        formats_seen.add(fmt)
                    spec = self.matrix.get(fmt, {})
                    field = spec.get("field")
                    if field:
                        fields_seen.add(field)
                    yr = self._year_from_filename(src)
                    if yr:
                        years_seen.add(yr)

            if len(formats_seen) >= min_formats:
                results.append({
                    "ipp": ipp,
                    "formats": sorted(formats_seen),
                    "fields": sorted(fields_seen),
                    "years": sorted(years_seen),
                    "sources_count": len(sources),
                })

        # Tri : nombre de formats décroissant, puis IPP pour stabilité.
        results.sort(key=lambda x: (-len(x["formats"]), x["ipp"]))
        return results[:limit]

    def compute_active_population(self) -> dict:
        """
        Calcule la file active par année et par champ PMSI, en s'appuyant
        sur le MPI déjà construit. Si un IPP est vu dans plusieurs formats
        la même année, il n'est compté qu'une fois dans la file globale de
        cette année (mais il comptera dans chaque champ où il apparaît).

        Structure retournée :
            {
              "years": ["2023", "2024", ...],
              "fields": ["PSY", "SSR", "HAD", "MCO", "TRANSVERSAL"],
              "by_year_global": {"2024": 1523, ...},
              "by_year_field":  {"2024": {"PSY": 1200, "SSR": 50, ...}, ...},
              "by_year_format": {"2024": {"RPS": 980, "EDGAR": 400, ...}, ...},
              "total_unique_ipp": 4821,  # sur toute la période cumulée
            }

        Si aucun fichier n'a d'année détectable, years est vide et
        by_year_* sont des dicts vides — le frontend affiche alors un
        message "impossible d'inférer l'année depuis les noms de fichiers".
        """
        # Index inverse : pour chaque (fichier, format), on retrouve l'année
        # et le champ depuis le file_stats + la matrice ATIH.
        file_meta = {}
        for name, stats in self.file_stats.items():
            fmt = stats.get("format", "INCONNU")
            spec = self.matrix.get(fmt, {})
            year = self._year_from_filename(name)
            file_meta[name] = {
                "format": fmt,
                "field": spec.get("field", "INCONNU"),
                "year": year,
            }

        # Agrégation : pour chaque IPP, on liste les (année, format, champ)
        # d'apparition. On déduit la file active en prenant l'union unique.
        by_year_global: dict[str, set] = defaultdict(set)
        by_year_field: dict[str, dict[str, set]] = defaultdict(
            lambda: defaultdict(set)
        )
        by_year_format: dict[str, dict[str, set]] = defaultdict(
            lambda: defaultdict(set)
        )

        for ipp, data in self.mpi.items():
            # data["history"] = {ddn: [sources]}
            for _ddn, sources in data["history"].items():
                for src in sources:
                    meta = file_meta.get(src)
                    if not meta or not meta["year"]:
                        continue
                    y = meta["year"]
                    by_year_global[y].add(ipp)
                    by_year_field[y][meta["field"]].add(ipp)
                    by_year_format[y][meta["format"]].add(ipp)

        # Sérialisation : set → int, tri des années chronologiquement
        years = sorted(by_year_global.keys())
        fields = sorted({
            f for per_year in by_year_field.values() for f in per_year
        })

        return {
            "years": years,
            "fields": fields,
            "by_year_global": {y: len(ipps) for y, ipps in by_year_global.items()},
            "by_year_field": {
                y: {f: len(ipps) for f, ipps in per_field.items()}
                for y, per_field in by_year_field.items()
            },
            "by_year_format": {
                y: {f: len(ipps) for f, ipps in per_format.items()}
                for y, per_format in by_year_format.items()
            },
            "total_unique_ipp": len(self.mpi),
        }
