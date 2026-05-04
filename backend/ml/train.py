"""
═══════════════════════════════════════════════════════════════════════════════
 backend/ml/train.py · Pipeline d'entraînement XGBoost
═══════════════════════════════════════════════════════════════════════════════

Entraîne 3 modèles XGBoost sur le dataset synthétique ATIH ·

  1. format_detector    · multi-classe (37 classes · format × version)
  2. collision_risk     · binaire (probabilité de collision IDV)
  3. ddn_validity       · binaire (probabilité que la DDN soit valide)

Sauvegarde dans backend/ml/models/ au format JSON natif XGBoost (portable
entre Python et C++/.NET).

Usage ·
    python -m backend.ml.train                    # 50k samples, défauts
    python -m backend.ml.train --samples 200000   # plus grand dataset

Métriques affichées · accuracy, F1 macro, AUC binaire selon le modèle.
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from .synthetic import generate_dataset

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# ─────────────────────────────────────────────────────────────────────────────
# FEATURES par modèle · ordre stable, à ne JAMAIS changer sans retrain
# ─────────────────────────────────────────────────────────────────────────────


LINE_FEATURES = [
    "feat_length",
    "feat_digits_ratio",
    "feat_spaces_ratio",
    "feat_alpha_ratio",
    "feat_first8_is_numeric",
    "feat_has_ddn_pattern_28_8",
    "feat_char_pos_0_isdigit",
    "feat_char_pos_19_isdigit",
    "feat_char_pos_50_isdigit",
    "feat_char_pos_100_isdigit",
    "feat_char_pos_200_isdigit",
]

MPI_FEATURES = [
    "feat_ipp_freq",
    "feat_ddn_variance_days",
    "feat_n_distinct_finess",
    "feat_n_distinct_modalities",
    "feat_ipp_with_letters",
    "feat_year_min",
    "feat_year_span",
]


# ─────────────────────────────────────────────────────────────────────────────
# ENTRAÎNEMENTS UNITAIRES
# ─────────────────────────────────────────────────────────────────────────────


def _train_format_detector(df: pd.DataFrame, out_dir: str) -> dict[str, Any]:
    print("\n[1/3] format_detector · multi-classe sur lignes ATIH")
    X = df[LINE_FEATURES].values
    y_str = df["label_format"].values
    classes = sorted(set(y_str))
    cls_to_id = {c: i for i, c in enumerate(classes)}
    y = np.array([cls_to_id[c] for c in y_str])
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    clf = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.15,
        objective="multi:softprob",
        num_class=len(classes),
        eval_metric="mlogloss",
        n_jobs=-1,
        tree_method="hist",
        random_state=42,
    )
    t0 = time.time()
    clf.fit(X_tr, y_tr)
    train_s = time.time() - t0
    y_pred = clf.predict(X_te)
    acc = accuracy_score(y_te, y_pred)
    f1m = f1_score(y_te, y_pred, average="macro")
    print(f"      {len(classes)} classes · {len(X_tr):,} train / "
          f"{len(X_te):,} test · {train_s:.1f}s")
    print(f"      accuracy={acc:.3f}  f1_macro={f1m:.3f}")
    clf.save_model(os.path.join(out_dir, "format_detector.json"))
    with open(os.path.join(out_dir, "format_classes.json"), "w",
              encoding="utf-8") as f:
        json.dump(classes, f, ensure_ascii=False, indent=2)
    return {"model": "format_detector", "accuracy": acc, "f1_macro": f1m,
            "n_classes": len(classes), "train_seconds": train_s}


def _train_collision_risk(df: pd.DataFrame, out_dir: str) -> dict[str, Any]:
    print("\n[2/3] collision_risk · binaire sur features MPI")
    X = df[MPI_FEATURES].values
    y = df["label_collision"].values
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    pos = y_tr.sum()
    neg = len(y_tr) - pos
    spw = neg / max(pos, 1)
    clf = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.1,
        objective="binary:logistic",
        eval_metric="auc",
        scale_pos_weight=spw,
        n_jobs=-1,
        tree_method="hist",
        random_state=42,
    )
    t0 = time.time()
    clf.fit(X_tr, y_tr)
    train_s = time.time() - t0
    y_proba = clf.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, y_proba)
    y_pred = (y_proba > 0.5).astype(int)
    acc = accuracy_score(y_te, y_pred)
    f1 = f1_score(y_te, y_pred)
    print(f"      taux base · {y.mean():.1%} positifs · scale_pos_weight={spw:.1f}")
    print(f"      accuracy={acc:.3f}  AUC={auc:.3f}  f1={f1:.3f}")
    clf.save_model(os.path.join(out_dir, "collision_risk.json"))
    return {"model": "collision_risk", "auc": auc, "accuracy": acc, "f1": f1,
            "train_seconds": train_s}


def _train_ddn_validity(df: pd.DataFrame, out_dir: str) -> dict[str, Any]:
    print("\n[3/3] ddn_validity · binaire sur features de ligne")
    X = df[LINE_FEATURES].values
    y = df["label_ddn_valid"].values
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    clf = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.1,
        objective="binary:logistic",
        eval_metric="auc",
        n_jobs=-1,
        tree_method="hist",
        random_state=42,
    )
    t0 = time.time()
    clf.fit(X_tr, y_tr)
    train_s = time.time() - t0
    y_proba = clf.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, y_proba)
    y_pred = (y_proba > 0.5).astype(int)
    acc = accuracy_score(y_te, y_pred)
    print(f"      accuracy={acc:.3f}  AUC={auc:.3f}")
    clf.save_model(os.path.join(out_dir, "ddn_validity.json"))
    return {"model": "ddn_validity", "auc": auc, "accuracy": acc,
            "train_seconds": train_s}


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:  # pragma: no cover
    p = argparse.ArgumentParser(description="Entraîne les 3 modèles XGBoost.")
    p.add_argument("--samples", type=int, default=50_000,
                   help="Taille du dataset synthétique (défaut · 50 000)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--data-cache", default=None,
                   help="Réutiliser un parquet existant au lieu de régénérer.")
    args = p.parse_args()

    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    # ─── Données ──────────────────────────────────────────────────────────
    if args.data_cache and os.path.exists(args.data_cache):
        print(f"[ML] Lecture cache · {args.data_cache}")
        df = pd.read_parquet(args.data_cache)
    else:
        print(f"[ML] Génération · {args.samples:,} samples (PSY priorisé)")
        t0 = time.time()
        df = generate_dataset(n_samples=args.samples, seed=args.seed)
        print(f"     {time.time() - t0:.1f}s · {len(df):,} lignes · "
              f"{df['label_format'].nunique()} formats distincts")
        cache_path = os.path.join(DATA_DIR, "synthetic_train.parquet")
        df.to_parquet(cache_path, index=False)
        print(f"     Sauvegarde · {cache_path}")

    # ─── 3 modèles ────────────────────────────────────────────────────────
    metrics = []
    metrics.append(_train_format_detector(df, MODELS_DIR))
    metrics.append(_train_collision_risk(df, MODELS_DIR))
    metrics.append(_train_ddn_validity(df, MODELS_DIR))

    # ─── Métadonnées globales ─────────────────────────────────────────────
    meta = {
        "trained_at": pd.Timestamp.now().isoformat(),
        "samples": len(df),
        "seed": args.seed,
        "psy_share": float((df["meta_field"] == "PSY").mean()),
        "models": metrics,
    }
    with open(os.path.join(MODELS_DIR, "training_metadata.json"), "w",
              encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("\n[OK] Entraînement terminé · 3 modèles sauvegardés dans "
          f"{MODELS_DIR}")
    print(f"     PSY share du dataset · {meta['psy_share']:.1%}")


if __name__ == "__main__":  # pragma: no cover
    main()
