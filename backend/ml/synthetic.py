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


# Catalogue des 35+ variantes connues.
# Pondération · GHT Sud Paris est un GHT 100 % psychiatrie (Paul Guiraud +
# Fondation Vallée), donc PSY est très sur-représenté dans le mix réel.
# Les ratios suivent grossièrement la distribution observée chez un CHS PSY
# typique · PSY ~75 %, transversal ~10 %, MCO/SMR/HAD ~15 % cumulé (uniquement
# pour les patients en transfert vers d'autres GHT).
ATIH_SPECS: list[FormatSpec] = [
    # ── PSY · RIM-P (priorité GHT Sud Paris) ────────────────────────────────
    FormatSpec("RPS",          "P03", "PSY", 138, 8,  20, 28, 8, 2010, 2014, 1.5),
    FormatSpec("RPS",          "P04", "PSY", 142, 8,  20, 28, 8, 2014, 2022, 2.5),
    FormatSpec("RPS",          "P04-148", "PSY", 148, 8,  20, 28, 8, 2021, 2022, 0.8),
    FormatSpec("RPS",          "P05", "PSY", 154, 8,  20, 28, 8, 2022, None, 6.0),
    FormatSpec("RAA",          "P03", "PSY",  86, 8,  20, 28, 8, 2010, 2014, 1.0),
    FormatSpec("RAA",          "P04", "PSY",  90, 8,  20, 28, 8, 2014, 2022, 1.5),
    FormatSpec("RAA",          "P05", "PSY",  92, 8,  20, 28, 8, 2022, 2024, 1.8),
    FormatSpec("RAA",          "P06", "PSY",  96, 8,  20, 28, 8, 2024, None, 4.5),
    FormatSpec("RPSA",         "P05", "PSY", 132, 8,  20, 28, 8, 2014, None, 1.8),
    FormatSpec("R3A",          "P05", "PSY",  76, 8,  20, 28, 8, 2014, None, 1.2),
    FormatSpec("FICHSUP-PSY",  "v01", "PSY",  80, 8,  20, None, None, 2014, None, 1.5),
    FormatSpec("EDGAR",        "v01", "PSY",  60, 8,  20, None, None, 2015, None, 0.9),
    FormatSpec("FICUM-PSY",    "v01", "PSY",  72, 8,  20, None, None, 2014, None, 0.9),
    FormatSpec("RSF-ACE-PSY",  "v01", "PSY", 144, 8,  20, None, None, 2017, None, 0.9),

    # ── SSR / SMR (volume marginal en PSY) ──────────────────────────────────
    FormatSpec("RHS",     "S03", "SMR", 282, 8,  20, 28, 8, 2010, 2018, 0.15),
    FormatSpec("RHS",     "S05", "SMR", 296, 8,  20, 28, 8, 2018, 2022, 0.15),
    FormatSpec("RHS",     "SMR-2024", "SMR", 312, 8,  20, 28, 8, 2022, None, 0.20),
    FormatSpec("SSRHA",   "v01", "SMR", 196, 8,  20, 28, 8, 2014, None, 0.10),
    FormatSpec("RAPSS",   "v01", "SMR", 218, 8,  20, 28, 8, 2014, None, 0.10),
    FormatSpec("FICHCOMP-SMR", "v01", "SMR", 168, 8,  20, None, None, 2014, None, 0.10),

    # ── HAD (volume marginal en PSY) ────────────────────────────────────────
    FormatSpec("RPSS",    "H02", "HAD", 200, 8,  20, 28, 8, 2002, 2010, 0.10),
    FormatSpec("RPSS",    "H04", "HAD", 220, 8,  20, 28, 8, 2010, 2018, 0.10),
    FormatSpec("RPSS",    "H06", "HAD", 232, 8,  20, 28, 8, 2018, None, 0.20),
    FormatSpec("RAPSS-HAD",    "v01", "HAD", 188, 8,  20, 28, 8, 2014, None, 0.10),
    FormatSpec("FICHCOMP-HAD", "v01", "HAD", 162, 8,  20, None, None, 2014, None, 0.10),
    FormatSpec("SSRHA-HAD",    "v01", "HAD", 196, 8,  20, 28, 8, 2014, None, 0.10),

    # ── MCO (transferts inter-GHT seulement) ────────────────────────────────
    FormatSpec("RSS",     "v005", "MCO", 300, 8,  20, 28, 8, 2000, 2010, 0.10),
    FormatSpec("RSS",     "v009", "MCO", 320, 8,  20, 28, 8, 2010, 2018, 0.15),
    FormatSpec("RSS",     "v012", "MCO", 340, 8,  20, 28, 8, 2018, 2024, 0.20),
    FormatSpec("RSS",     "v013", "MCO", 348, 8,  20, 28, 8, 2024, None, 0.40),
    FormatSpec("RSFA",    "v01",  "MCO", 168, 8,  20, None, None, 2009, None, 0.20),
    FormatSpec("RSFB",    "v01",  "MCO", 188, 8,  20, None, None, 2009, None, 0.15),
    FormatSpec("RSFC",    "v01",  "MCO", 168, 8,  20, None, None, 2009, None, 0.10),

    # ── Transversal (chaînage anonyme, obligatoire tous champs) ────────────
    FormatSpec("VID-HOSP", "V01",  "transversal", 150, 8, 20, 28, 8, 2009, 2013, 0.50),
    FormatSpec("VID-HOSP", "V012", "transversal", 162, 8, 20, 28, 8, 2013, None, 1.50),
    FormatSpec("ANO-HOSP", "v01",  "transversal", 100, 8, 20, None, None, 2009, None, 1.20),
    FormatSpec("FICHCOMP", "v01",  "transversal", 140, 8, 20, None, None, 2009, None, 0.80),
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


def _build_line(spec: FormatSpec, rng: random.Random,
                inject_ddn_error: bool = False) -> tuple[str, str]:
    """Construit une ligne plausible et retourne (line, ddn_label)."""
    ipp = _random_ipp(rng)
    line_chars = [" "] * spec.line_length
    # IPP
    for i, c in enumerate(ipp):
        if spec.ipp_start + i < spec.line_length:
            line_chars[spec.ipp_start + i] = c
    # DDN
    ddn_valid = "1"
    if spec.ddn_start is not None:
        if inject_ddn_error and rng.random() < 0.5:
            # Erreur DDN · format invalide ou date impossible
            ddn = rng.choice(["00000000", "99999999", "20251332", " " * 8,
                              "abcdefgh", "20250230"])
            ddn_valid = "0"
        else:
            ddn = _random_ddn(rng)
        for i, c in enumerate(ddn):
            if spec.ddn_start + i < spec.line_length:
                line_chars[spec.ddn_start + i] = c
    # Remplir le reste avec du noise plausible
    for i in range(spec.line_length):
        if line_chars[i] == " ":
            if rng.random() < 0.7:
                line_chars[i] = rng.choice(string.digits)
    line = "".join(line_chars)
    return line, ddn_valid


# ─────────────────────────────────────────────────────────────────────────────
# DATASET COMPLET · features pour les 3 modèles
# ─────────────────────────────────────────────────────────────────────────────


def _line_features(line: str, hint_field: str = "") -> dict:
    """
    Extrait des features numériques d'une ligne brute.
    Utilisées pour entraîner format_detector.
    """
    n = len(line)
    digits = sum(c.isdigit() for c in line)
    spaces = sum(c == " " for c in line)
    alpha = sum(c.isalpha() for c in line)
    return {
        "length": n,
        "digits_ratio": digits / max(n, 1),
        "spaces_ratio": spaces / max(n, 1),
        "alpha_ratio": alpha / max(n, 1),
        "first8_is_numeric": int(line[:8].strip().isdigit()) if line[:8].strip() else 0,
        "has_ddn_pattern_28_8": int(
            line[28:36].isdigit() and 1900 <= int(line[28:32] or 0) <= 2030
        ) if n >= 36 else 0,
        # Caractères à des positions clés (descripteurs structurels)
        "char_pos_0_isdigit": int(line[0].isdigit()) if n > 0 else 0,
        "char_pos_19_isdigit": int(line[19].isdigit()) if n > 19 else 0,
        "char_pos_50_isdigit": int(line[50].isdigit()) if n > 50 else 0,
        "char_pos_100_isdigit": int(line[100].isdigit()) if n > 100 else 0,
        "char_pos_200_isdigit": int(line[200].isdigit()) if n > 200 else 0,
    }


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
