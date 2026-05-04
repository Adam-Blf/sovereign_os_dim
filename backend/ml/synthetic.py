"""
═══════════════════════════════════════════════════════════════════════════════
 backend/ml/synthetic.py · Générateur de données ATIH synthétiques
═══════════════════════════════════════════════════════════════════════════════

Produit un dataset fidèle aux specifications ATIH des 25 dernières années
(2000-2026), couvrant les 23 formats actifs et leurs variantes historiques
(RPS P03 → P05, RAA P03 → P06, RHS S03 → SMR, RPSS H02 → H06, RSS v005 → v013).

Pourquoi synthétique · les vrais fichiers PMSI sont protégés par le secret
hospitalier (RGPD + L.1110-4 CSP). Les caractéristiques exploitées par les
modèles (longueur de ligne, position IPP/DDN, distribution annuelle) sont
toutes publiques — voir notice technique ATIH.

Usage ·
    from backend.ml.synthetic import generate_dataset
    df = generate_dataset(n_samples=50_000, seed=42)
    df.to_parquet("backend/ml/data/synthetic_train.parquet")

Reproductibilité · seed obligatoire pour fixer numpy + random.
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# SPÉCIFICATIONS ATIH · une entrée par (format × version active)
# ─────────────────────────────────────────────────────────────────────────────
# Source · notice technique ATIH 2024-2026 + guide méthodologique PSY
# Champs · longueur de ligne en chars, position IPP (start, len),
# position DDN (start, len), année d'introduction, année d'obsolescence (ou None).
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FormatSpec:
    """Spécification d'un format ATIH à un instant donné."""
    name: str               # ex · "RPS"
    version: str            # ex · "P05"
    field: str              # MCO, SMR, HAD, PSY, transversal
    line_length: int        # longueur exacte de la ligne (chars)
    ipp_start: int          # position de début IPP (0-indexed)
    ipp_length: int         # longueur du champ IPP
    ddn_start: int | None   # position de début DDN (None si pas de DDN)
    ddn_length: int | None  # longueur du champ DDN (8 typiquement)
    year_intro: int         # année d'introduction
    year_obs: int | None    # année d'obsolescence (None = encore actif)
    weight: float = 1.0     # poids de tirage (fréquence relative)


# Catalogue des variantes connues · positions vérifiées sur format-pmsi.fr
# et lespmsi.com (cf docs/research/pmsi_formats_history.md).
#
# Pondération · GHT Sud Paris est un GHT 100 % psychiatrie (Paul Guiraud +
# Fondation Vallée), donc PSY ~80 % du mix. Les variantes historiques sont
# conservées pour entraîner le modèle sur 25 ans de PMSI (2000-2026).
#
# Convention positions · 0-indexed dans le code Python (specs ATIH = 1-indexed,
# soustraire 1 pour traduire). IPP None = pas d'IPP dans ce format (cas MCO
# RSS standard, FICHSUP, anonymes).
ATIH_SPECS: list[FormatSpec] = [
    # ── PSY · RIM-P · double FINESS pos 0-8 + 9-17, format pos 18-20, IPP 21-40, DDN 41-48 ────
    FormatSpec("RPS",          "P03",     "PSY", 138, 21, 20, 41, 8, 2006, 2010, 0.8),
    FormatSpec("RPS",          "P05",     "PSY", 152, 21, 20, 41, 8, 2010, 2017, 2.5),
    FormatSpec("RPS",          "P07",     "PSY", 152, 21, 20, 41, 8, 2015, 2017, 1.0),
    FormatSpec("RPS",          "P08",     "PSY", 154, 21, 20, 41, 8, 2017, 2019, 1.5),
    FormatSpec("RPS",          "P09",     "PSY", 154, 21, 20, 41, 8, 2018, 2020, 1.5),
    FormatSpec("RPS",          "P10",     "PSY", 154, 21, 20, 41, 8, 2019, 2021, 1.5),
    FormatSpec("RPS",          "P11",     "PSY", 154, 21, 20, 41, 8, 2020, 2021, 1.5),
    FormatSpec("RPS",          "P12",     "PSY", 154, 21, 20, 41, 8, 2021, None, 6.0),
    FormatSpec("RAA",          "P06",     "PSY",  98, 21, 20, 41, 8, 2010, 2017, 1.5),
    FormatSpec("RAA",          "P07",     "PSY",  81, 21, 20, 41, 8, 2015, 2017, 0.8),
    FormatSpec("RAA",          "P09",     "PSY",  81, 21, 20, 41, 8, 2017, 2019, 1.2),
    FormatSpec("RAA",          "P10",     "PSY",  85, 21, 20, 41, 8, 2019, 2021, 1.2),
    FormatSpec("RAA",          "P13",     "PSY",  85, 21, 20, 41, 8, 2021, 2022, 1.0),
    FormatSpec("RAA",          "P14",     "PSY",  85, 21, 20, 41, 8, 2022, None, 4.5),
    FormatSpec("RPSA",         "anon",    "PSY", 132, None, None, 41, 8, 2014, None, 1.8),  # anonymisé
    FormatSpec("R3A",          "anon",    "PSY",  76, None, None, 41, 8, 2014, None, 1.2),  # anonymisé
    FormatSpec("FICHSUP-PSY",  "v01",     "PSY",  80, None, None, None, None, 2014, None, 1.5),
    FormatSpec("EDGAR",        "v01",     "PSY",  60, None, None, None, None, 2015, None, 0.9),
    FormatSpec("FICUM-PSY",    "v01",     "PSY",  38, None, None, None, None, 2014, None, 0.9),
    FormatSpec("RSF-ACE-PSY",  "v01",     "PSY", 144, None, None, None, None, 2017, None, 0.9),
    FormatSpec("VID-IPP-PSY",  "I00A",    "PSY", 106, 80, 13, 15, 8, 2020, None, 1.0),  # ddn DDMMYYYY pos 16-23 (1-idx)

    # ── HAD · format pos 0-2 (unique !), FINESS jur 3-11 + géo 12-20, IPP 21-40, DDN 61-68 ────
    FormatSpec("RPSS",    "H01", "HAD", 150, 21, 20, 61, 8, 2005, 2007, 0.10),
    FormatSpec("RPSS",    "H02", "HAD", 160, 21, 20, 61, 8, 2007, 2010, 0.10),
    FormatSpec("RPSS",    "H03", "HAD", 190, 21, 20, 61, 8, 2010, 2014, 0.10),
    FormatSpec("RPSS",    "H04", "HAD", 190, 21, 20, 61, 8, 2010, 2014, 0.10),
    FormatSpec("RAPSS",   "H07", "HAD", 190, 21, 20, 61, 8, 2014, 2019, 0.15),
    FormatSpec("RPSS",    "H17", "HAD", 195, 21, 20, 61, 8, 2014, 2019, 0.10),
    FormatSpec("RAPSS",   "H0B", "HAD", 195, 21, 20, 61, 8, 2019, None, 0.30),
    FormatSpec("RPSS",    "H1B", "HAD", 200, 21, 20, 61, 8, 2019, None, 0.20),

    # ── SSR / SMR · sans IPP, RHS non-grp FINESS 0-8 token 9-11, grp filler+token 10-12 ─────
    FormatSpec("RHS",     "M05", "SMR", 159, None, None, 59, 8, 2008, 2010, 0.10),
    FormatSpec("RHS",     "M06", "SMR", 168, None, None, 67, 8, 2010, 2013, 0.10),
    FormatSpec("RHS",     "M09", "SMR", 168, None, None, 67, 8, 2013, 2017, 0.15),
    FormatSpec("RHS",     "M19", "SMR", 190, None, None, 80, 8, 2013, 2017, 0.10),  # grouped
    FormatSpec("RHS",     "M0A", "SMR", 171, None, None, 67, 8, 2017, 2018, 0.10),
    FormatSpec("RHS",     "M0B", "SMR", 173, None, None, 67, 8, 2018, 2022, 0.15),
    FormatSpec("RHS",     "M1B", "SMR", 190, None, None, 80, 8, 2018, 2022, 0.10),  # grouped
    FormatSpec("RHS",     "M0C", "SMR", 173, None, None, 67, 8, 2022, 2025, 0.20),
    FormatSpec("RHS",     "M0D", "SMR", 173, None, None, 68, 8, 2025, None, 0.30),
    FormatSpec("RHS",     "M1D", "SMR", 190, None, None, 81, 8, 2025, None, 0.15),  # grouped

    # ── MCO · sans IPP standard, token 9-11 (10-12 1-idx), FINESS 15-23 (grp) / 0-8 (022+) ─
    FormatSpec("RSS",     "115", "MCO", 192, None, None, 77, 8, 2010, 2011, 0.10),  # grouped DDMMYYYY
    FormatSpec("RSS",     "117", "MCO", 192, None, None, 77, 8, 2013, 2016, 0.20),  # grouped
    FormatSpec("RSS",     "119", "MCO", 192, None, None, 77, 8, 2019, 2020, 0.15),  # grouped + Nature séjour
    FormatSpec("RSS",     "121", "MCO", 192, None, None, 77, 8, 2021, 2022, 0.20),  # grouped
    FormatSpec("RSS",     "122", "MCO", 192, None, None, 77, 8, 2023, 2026, 0.30),  # grouped
    FormatSpec("RSS",     "022", "MCO", 192, None, None, 62, 8, 2023, 2026, 0.10),  # non-grp YYYYMMDD pos 63-70
    FormatSpec("RSS",     "123", "MCO", 205, None, None, 77, 8, 2026, None, 0.40),  # grouped 2026
    FormatSpec("RSS",     "023", "MCO", 205, None, None, 62, 8, 2026, None, 0.20),  # non-grp 2026
    FormatSpec("RSA",     "220", "MCO", 223, None, None, None, None, 2013, 2025, 0.20),  # anonymisé
    FormatSpec("FICHCOMP-MO", "v06", "MCO", 105, None, None, None, None, 2013, None, 0.20),
    FormatSpec("FICHCOMP-DMI","v02", "MCO",  92, None, None, None, None, 2013, None, 0.15),

    # ── Transversal · VID-HOSP token pos 48-51 (49-52 1-idx), NIR 0-12 ───────
    FormatSpec("VID-HOSP", "V009", "transversal", 312, 0, 13, 19, 8, 2013, 2017, 0.30),  # NIR pos 1-13
    FormatSpec("VID-HOSP", "V012", "transversal", 353, 0, 13, 19, 8, 2018, 2021, 0.40),
    FormatSpec("VID-HOSP", "V014", "transversal", 466, 0, 13, 19, 8, 2022, 2025, 1.00),  # 466 chars exact
    FormatSpec("VID-HOSP", "V015", "transversal", 470, 0, 13, 19, 8, 2025, 2026, 0.40),  # variable
    FormatSpec("VID-HOSP", "V016", "transversal", 472, 0, 13, 19, 8, 2026, None, 0.80),  # variable
    FormatSpec("ANO-HOSP", "V010", "transversal",  85, None, None, None, None, 2016, 2018, 0.30),
    FormatSpec("ANO-HOSP", "V013", "transversal", 100, None, None, None, None, 2013, None, 0.80),
    FormatSpec("FICHCOMP", "v01",  "transversal", 140, None, None, None, None, 2009, None, 0.40),
]


# ─────────────────────────────────────────────────────────────────────────────
# GÉNÉRATEUR DE LIGNES SYNTHÉTIQUES
# ─────────────────────────────────────────────────────────────────────────────


def _random_ipp(rng: random.Random) -> str:
    """IPP synthétique · 8 chars numériques."""
    return f"{rng.randint(0, 99_999_999):08d}"


def _random_ddn(rng: random.Random, year_min: int = 1920, year_max: int = 2024) -> str:
    """DDN synthétique YYYYMMDD."""
    y = rng.randint(year_min, year_max)
    m = rng.randint(1, 12)
    d = rng.randint(1, 28)  # 28 pour éviter les jours invalides
    return f"{y:04d}{m:02d}{d:02d}"


def _pad_line(content: str, length: int, rng: random.Random) -> str:
    """Pad une ligne au bon length avec du contenu plausible (digits + espaces)."""
    pool = string.digits + " " * 3  # majoritairement chiffres, quelques espaces
    if len(content) >= length:
        return content[:length]
    pad = "".join(rng.choices(pool, k=length - len(content)))
    return content + pad


def _format_token_position(spec: FormatSpec) -> tuple[str, int] | None:
    """
    Détermine la position et la valeur du token discriminant ATIH selon
    le champ. Retourne (token_str, position_0idx) ou None si pas de token
    structurel (formats anonymisés type RSPA / R3A / FICHCOMP / ANO-HOSP).
    """
    if spec.field == "HAD":
        return spec.version, 0  # H01, H02, ..., H1B
    if spec.field == "PSY":
        if spec.name in ("RPS", "RAA"):
            return spec.version, 18  # P03-P14 après double FINESS
        if spec.name == "VID-IPP-PSY":
            return spec.version, 48  # I00A
        return None
    if spec.field == "SMR" and spec.name == "RHS":
        # M19/M1A-M1D = grouped (filler 10 chars + token pos 10)
        # M0X = non-grouped (token pos 9)
        if spec.version.startswith("M1"):
            return spec.version, 10
        return spec.version, 9
    if spec.field == "MCO" and spec.name == "RSS":
        # 022/023 non-grouped → token pos 9, FINESS pos 0
        # 11x/12x grouped → token pos 9, FINESS pos 15
        return spec.version, 9
    if spec.field == "MCO" and spec.name == "RSA":
        return spec.version, 9
    if spec.field == "transversal" and spec.name == "VID-HOSP":
        return spec.version, 48  # V008, V009, V012, V014, ...
    if spec.field == "transversal" and spec.name == "ANO-HOSP":
        return spec.version, 48
    return None


def _build_line(spec: FormatSpec, rng: random.Random,
                inject_ddn_error: bool = False) -> tuple[str, str]:
    """
    Construit une ligne plausible et retourne (line, ddn_valid_label).

    Conformité ATIH ·
    - Token de format inséré à la position correcte selon le champ
    - IPP inséré uniquement si spec.ipp_start est défini (pas dans MCO RSS, anonymes, FICHCOMP)
    - DDN format YYYYMMDD partout SAUF VID-IPP-PSY (DDMMYYYY)
    - Reste de la ligne rempli de noise plausible (digits + qq espaces)
    """
    line_chars = [" "] * spec.line_length

    # 1. Token de format (le plus discriminant)
    tok_info = _format_token_position(spec)
    if tok_info:
        token, pos = tok_info
        for i, c in enumerate(token):
            if pos + i < spec.line_length:
                line_chars[pos + i] = c

    # 2. FINESS · injecté à des positions plausibles selon le champ
    finess = f"{rng.randint(100_000_000, 999_999_999):09d}"
    if spec.field == "PSY" and spec.name in ("RPS", "RAA"):
        # FINESS jur pos 0-8, FINESS géo pos 9-17
        for i, c in enumerate(finess):
            if i < spec.line_length: line_chars[i] = c
        finess2 = f"{rng.randint(100_000_000, 999_999_999):09d}"
        for i, c in enumerate(finess2):
            if 9 + i < spec.line_length: line_chars[9 + i] = c
    elif spec.field == "HAD":
        # FINESS jur pos 3-11, FINESS géo pos 12-20
        for i, c in enumerate(finess):
            if 3 + i < spec.line_length: line_chars[3 + i] = c
        finess2 = f"{rng.randint(100_000_000, 999_999_999):09d}"
        for i, c in enumerate(finess2):
            if 12 + i < spec.line_length: line_chars[12 + i] = c
    elif spec.field in ("MCO", "SMR") and spec.name in ("RSS", "RHS", "RSA"):
        # Non-grouped · FINESS pos 0-8 · Grouped · FINESS pos 15-23
        is_grouped = (spec.name == "RSS" and not spec.version.startswith("0")) \
                     or (spec.name == "RHS" and spec.version.startswith("M1"))
        finess_pos = 15 if is_grouped else 0
        if is_grouped and spec.name == "RHS":
            # Grouped RHS · filler 10 chars + token pos 10 + FINESS pos 13
            finess_pos = 13
        for i, c in enumerate(finess):
            if finess_pos + i < spec.line_length:
                line_chars[finess_pos + i] = c

    # 3. IPP (si applicable)
    if spec.ipp_start is not None:
        ipp = _random_ipp(rng)
        for i, c in enumerate(ipp):
            if spec.ipp_start + i < spec.line_length:
                line_chars[spec.ipp_start + i] = c

    # 4. DDN (si applicable)
    ddn_valid = "1"
    if spec.ddn_start is not None:
        if inject_ddn_error and rng.random() < 0.5:
            ddn = rng.choice(["00000000", "99999999", "20251332", " " * 8,
                              "abcdefgh", "20250230", "12131980"])
            ddn_valid = "0"
        else:
            # VID-IPP utilise DDMMYYYY, le reste YYYYMMDD
            if spec.name == "VID-IPP-PSY":
                d, m, y = rng.randint(1, 28), rng.randint(1, 12), rng.randint(1920, 2024)
                ddn = f"{d:02d}{m:02d}{y:04d}"
            else:
                ddn = _random_ddn(rng)
        for i, c in enumerate(ddn):
            if spec.ddn_start + i < spec.line_length:
                line_chars[spec.ddn_start + i] = c

    # 5. Noise plausible sur le reste · majoritairement digits, qq espaces
    for i in range(spec.line_length):
        if line_chars[i] == " ":
            if rng.random() < 0.65:
                line_chars[i] = rng.choice(string.digits)

    return "".join(line_chars), ddn_valid


# ─────────────────────────────────────────────────────────────────────────────
# DATASET COMPLET · features pour les 3 modèles
# ─────────────────────────────────────────────────────────────────────────────


def _line_features(line: str, hint_field: str = "") -> dict:
    """
    Extrait des features numériques d'une ligne brute.
    Utilisées pour entraîner format_detector. Couvre les tokens
    discriminants ATIH connus · HAD pos 0-2, MCO/SMR pos 9-11,
    PSY pos 18-20 (après double FINESS), VID-HOSP pos 48-51.
    """
    n = len(line)
    digits = sum(c.isdigit() for c in line)
    spaces = sum(c == " " for c in line)
    alpha = sum(c.isalpha() for c in line)

    # Tokens · 1 si présent et structurellement plausible
    tok_had = line[0:3] if n >= 3 else ""
    tok_mco_smr = line[9:12] if n >= 12 else ""
    tok_psy = line[18:21] if n >= 21 else ""
    tok_vid = line[48:52] if n >= 52 else ""

    # Bracket de longueur · catégorise pour le modèle
    if n <= 100:        len_bucket = 0
    elif n <= 150:      len_bucket = 1
    elif n <= 175:      len_bucket = 2
    elif n <= 200:      len_bucket = 3
    elif n <= 300:      len_bucket = 4
    elif n <= 470:      len_bucket = 5
    else:               len_bucket = 6

    return {
        "length": n,
        "len_bucket": len_bucket,
        "digits_ratio": digits / max(n, 1),
        "spaces_ratio": spaces / max(n, 1),
        "alpha_ratio": alpha / max(n, 1),

        # ── Tokens HAD (pos 0-2) · `H01`-`H1B` ──────────────────────────────
        "tok_had_starts_H": int(tok_had.startswith("H")),
        "tok_had_H0X": int(tok_had.startswith("H0") and len(tok_had) == 3),
        "tok_had_H1X": int(tok_had.startswith("H1") and len(tok_had) == 3),

        # ── Tokens MCO/SMR (pos 9-11) ───────────────────────────────────────
        "tok_starts_M": int(tok_mco_smr.startswith("M")),  # SMR
        "tok_starts_digit": int(bool(tok_mco_smr) and tok_mco_smr[0].isdigit()),  # MCO 0XX/1XX/2XX
        "tok_2digit_first": int(tok_mco_smr[:2].isdigit()) if len(tok_mco_smr) >= 2 else 0,

        # ── Tokens PSY (pos 18-20) · `P03`-`P14` ────────────────────────────
        "tok_psy_starts_P": int(tok_psy.startswith("P")),
        "tok_psy_P0X": int(tok_psy.startswith("P0")),
        "tok_psy_P1X": int(tok_psy.startswith("P1")),

        # ── Tokens VID-HOSP/IPP (pos 48-51) ─────────────────────────────────
        "tok_vid_starts_V": int(tok_vid.startswith("V")),
        "tok_vid_starts_I": int(tok_vid.startswith("I")),

        # ── Double FINESS test (PSY signature) · pos 0-8 + 9-17 numériques ──
        "double_finess_psy": int(
            n >= 18 and line[0:9].strip().isdigit() and line[9:18].strip().isdigit()
        ),

        # ── Filler 10 chars en tête (RSS/RHS grouped) ───────────────────────
        "leading_filler_10": int(n >= 10 and line[0:10].strip() == ""),

        # ── DDN pattern à différentes positions (multi-emplacements) ────────
        "ddn_at_28_yyyy": _has_year(line, 28),
        "ddn_at_41_yyyy": _has_year(line, 41),
        "ddn_at_61_yyyy": _has_year(line, 61),
        "ddn_at_67_yyyy": _has_year(line, 67),
        "ddn_at_77_yyyy": _has_year(line, 77),

        # ── IPP signatures · 20 chars numériques à pos 21 ou 22 (1-idx) ─────
        "ipp_at_21_numeric": _has_digits(line, 21, 20),
    }


def _has_year(line: str, pos: int) -> int:
    """1 si line[pos:pos+4] ressemble à une année 1900-2030."""
    if len(line) < pos + 4:
        return 0
    s = line[pos:pos + 4]
    if not s.isdigit():
        return 0
    y = int(s)
    return int(1900 <= y <= 2030)


def _has_digits(line: str, pos: int, length: int) -> int:
    """1 si line[pos:pos+length] est essentiellement numérique."""
    if len(line) < pos + length:
        return 0
    s = line[pos:pos + length]
    digits = sum(c.isdigit() for c in s)
    return int(digits >= length * 0.7)


def _mpi_features(rng: random.Random, has_collision: bool) -> dict:
    """Features niveau MPI · pour collision_risk."""
    if has_collision:
        return {
            "ipp_freq": rng.randint(2, 12),  # IPP avec plusieurs DDN
            "ddn_variance_days": rng.randint(1, 365 * 50),
            "n_distinct_finess": rng.randint(1, 3),
            "n_distinct_modalities": rng.randint(1, 4),
            "ipp_with_letters": int(rng.random() < 0.1),
            "year_min": rng.randint(2010, 2024),
            "year_span": rng.randint(0, 14),
        }
    else:
        return {
            "ipp_freq": rng.randint(1, 4),
            "ddn_variance_days": 0,
            "n_distinct_finess": 1,
            "n_distinct_modalities": rng.randint(1, 2),
            "ipp_with_letters": 0,
            "year_min": rng.randint(2010, 2024),
            "year_span": rng.randint(0, 8),
        }


def generate_dataset(n_samples: int = 50_000,
                     seed: int = 42,
                     ddn_error_rate: float = 0.08,
                     collision_rate: float = 0.06) -> pd.DataFrame:
    """
    Construit un DataFrame complet avec features et labels pour les 3 modèles.

    Colonnes ·
      - feat_* · features numériques pour les modèles
      - label_format · classe (ex 'RPS_P05')
      - label_collision · 0/1
      - label_ddn_valid · 0/1
      - meta_field, meta_year · pour stratification éventuelle

    Pondération · les formats actifs récents (RPS P05, RSS v013, etc.) sont
    sur-représentés via FormatSpec.weight, comme dans la réalité 2024-2026.
    """
    rng = random.Random(seed)
    np.random.seed(seed)

    weights = np.array([s.weight for s in ATIH_SPECS])
    weights = weights / weights.sum()

    rows = []
    for i in range(n_samples):
        spec_idx = np.random.choice(len(ATIH_SPECS), p=weights)
        spec = ATIH_SPECS[spec_idx]

        inject_ddn_err = rng.random() < ddn_error_rate
        line, ddn_valid_str = _build_line(spec, rng, inject_ddn_err)

        has_collision = rng.random() < collision_rate
        mpi_feats = _mpi_features(rng, has_collision)
        line_feats = _line_features(line, spec.field)

        row = {
            f"feat_{k}": v for k, v in {**line_feats, **mpi_feats}.items()
        }
        row["label_format"] = f"{spec.name}_{spec.version}"
        row["label_collision"] = int(has_collision)
        row["label_ddn_valid"] = int(ddn_valid_str == "1")
        row["meta_field"] = spec.field
        row["meta_year_intro"] = spec.year_intro
        rows.append(row)

    df = pd.DataFrame(rows)
    return df


def main() -> None:  # pragma: no cover
    """CLI · python -m backend.ml.synthetic"""
    import argparse
    import os
    p = argparse.ArgumentParser(description="Génère un dataset synthétique ATIH.")
    p.add_argument("--samples", type=int, default=50_000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default="backend/ml/data/synthetic_train.parquet")
    args = p.parse_args()

    print(f"[ML] Génération de {args.samples:,} échantillons synthétiques · "
          f"seed={args.seed}")
    df = generate_dataset(n_samples=args.samples, seed=args.seed)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df.to_parquet(args.out, index=False)
    print(f"[ML] OK · {args.out} · {len(df):,} lignes · "
          f"{len(df.columns)} colonnes")
    print(f"      Formats distincts · {df['label_format'].nunique()}")
    print(f"      Collisions · {df['label_collision'].mean():.1%}")
    print(f"      DDN invalides · {(1 - df['label_ddn_valid']).mean():.1%}")


if __name__ == "__main__":  # pragma: no cover
    main()
