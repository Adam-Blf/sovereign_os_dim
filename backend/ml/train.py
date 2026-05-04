"""
═══════════════════════════════════════════════════════════════════════════════
 backend/ml/train.py · Pipeline d'entraînement multi-modèles
═══════════════════════════════════════════════════════════════════════════════

Entraîne 3 tâches sur le dataset synthétique ATIH 2000-2026, en testant
plusieurs algorithmes par tâche et en gardant le meilleur (validation
accuracy/AUC sur 20 % du dataset, stratifié) ·

  1. format_detector    · multi-classe (~50 classes · format × version)
  2. collision_risk     · binaire (probabilité de collision IDV)
  3. ddn_validity       · binaire (probabilité que la DDN soit valide)

Modèles testés par tâche ·
  - XGBoost (tree_method=hist, 200/300 estimators, depth 5/6)
  - XGBoost tuned (estimators 500, depth 8, lr 0.08)
  - LightGBM (n_estimators 300, num_leaves 63)
  - RandomForest (200 estimators, depth 12)

Le meilleur modèle par tâche est sauvegardé en .json (XGBoost natif) ou
.txt (LightGBM/sklearn pickle compressé). Métadonnées dans
training_metadata.json incluent le tableau comparatif complet.

Usage ·
    python -m backend.ml.train                       # 50k samples, défauts
    python -m backend.ml.train --samples 200000      # plus grand dataset
    python -m backend.ml.train --data-cache <path>   # réutilise un parquet
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import time
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
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
    "feat_length", "feat_len_bucket",
    "feat_digits_ratio", "feat_spaces_ratio", "feat_alpha_ratio",
    # Tokens HAD pos 0-2
    "feat_tok_had_starts_H", "feat_tok_had_H0X", "feat_tok_had_H1X",
    # Tokens MCO/SMR pos 9-11
    "feat_tok_starts_M", "feat_tok_starts_digit", "feat_tok_2digit_first",
    # Tokens PSY pos 18-20
    "feat_tok_psy_starts_P", "feat_tok_psy_P0X", "feat_tok_psy_P1X",
    # Tokens VID pos 48-51
    "feat_tok_vid_starts_V", "feat_tok_vid_starts_I",
    # Signatures structurelles
    "feat_double_finess_psy", "feat_leading_filler_10",
    # DDN signatures
    "feat_ddn_at_28_yyyy", "feat_ddn_at_41_yyyy",
    "feat_ddn_at_61_yyyy", "feat_ddn_at_67_yyyy", "feat_ddn_at_77_yyyy",
    # IPP
    "feat_ipp_at_21_numeric",
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


# ─────────────────────────────────────────────────────────────────────────────
# CANDIDATS PAR TÂCHE · benchmark + sélection du meilleur
# ─────────────────────────────────────────────────────────────────────────────


def _candidates_multiclass(num_class: int) -> list[tuple[str, Any]]:
    """Candidats pour la tâche multi-classe (format_detector)."""
    return [
        ("xgb_default", xgb.XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.15,
            objective="multi:softprob", num_class=num_class,
            tree_method="hist", n_jobs=-1, random_state=42,
        )),
        ("xgb_tuned", xgb.XGBClassifier(
            n_estimators=500, max_depth=8, learning_rate=0.08,
            subsample=0.9, colsample_bytree=0.8,
            objective="multi:softprob", num_class=num_class,
            tree_method="hist", n_jobs=-1, random_state=42,
        )),
        ("lgbm", lgb.LGBMClassifier(
            n_estimators=300, num_leaves=63, learning_rate=0.1,
            objective="multiclass", num_class=num_class,
            n_jobs=-1, random_state=42, verbose=-1,
        )),
        ("rf", RandomForestClassifier(
            n_estimators=200, max_depth=12, n_jobs=-1, random_state=42,
        )),
    ]


def _candidates_binary(scale_pos_weight: float = 1.0) -> list[tuple[str, Any]]:
    """Candidats pour les tâches binaires (collision_risk, ddn_validity)."""
    return [
        ("xgb_default", xgb.XGBClassifier(
            n_estimators=300, max_depth=5, learning_rate=0.1,
            objective="binary:logistic", eval_metric="auc",
            scale_pos_weight=scale_pos_weight,
            tree_method="hist", n_jobs=-1, random_state=42,
        )),
        ("xgb_tuned", xgb.XGBClassifier(
            n_estimators=500, max_depth=7, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.8,
            objective="binary:logistic", eval_metric="auc",
            scale_pos_weight=scale_pos_weight,
            tree_method="hist", n_jobs=-1, random_state=42,
        )),
        ("lgbm", lgb.LGBMClassifier(
            n_estimators=300, num_leaves=63, learning_rate=0.1,
            objective="binary", n_jobs=-1, random_state=42, verbose=-1,
            scale_pos_weight=scale_pos_weight,
        )),
        ("rf", RandomForestClassifier(
            n_estimators=200, max_depth=10,
            class_weight="balanced", n_jobs=-1, random_state=42,
        )),
    ]


def _save_model(name: str, model: Any, out_dir: str, base_filename: str) -> str:
    """Sauvegarde le meilleur modèle dans le bon format selon le type."""
    if isinstance(model, xgb.XGBClassifier):
        path = os.path.join(out_dir, f"{base_filename}.json")
        model.save_model(path)
        return path
    if isinstance(model, lgb.LGBMClassifier):
        path = os.path.join(out_dir, f"{base_filename}.lgbm.txt")
        model.booster_.save_model(path)
        return path
    # RandomForest et autres sklearn → pickle
    path = os.path.join(out_dir, f"{base_filename}.pkl")
    with open(path, "wb") as f:
        pickle.dump(model, f)
    return path


def _train_format_detector(df: pd.DataFrame, out_dir: str) -> dict[str, Any]:
    print("\n[1/3] format_detector · multi-classe sur lignes ATIH (4 candidats)")
    X = df[LINE_FEATURES].values
    y_str = df["label_format"].values
    classes = sorted(set(y_str))
    cls_to_id = {c: i for i, c in enumerate(classes)}
    y = np.array([cls_to_id[c] for c in y_str])
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    print(f"      {len(classes)} classes · {len(X_tr):,} train / "
          f"{len(X_te):,} test")

    leaderboard = []
    best = None
    for name, clf in _candidates_multiclass(len(classes)):
        try:
            t0 = time.time()
            clf.fit(X_tr, y_tr)
            train_s = time.time() - t0
            y_pred = clf.predict(X_te)
            acc = accuracy_score(y_te, y_pred)
            f1m = f1_score(y_te, y_pred, average="macro")
            score = acc + 0.3 * f1m  # composite · privilégie accuracy
            leaderboard.append({
                "candidate": name, "accuracy": round(acc, 4),
                "f1_macro": round(f1m, 4), "train_s": round(train_s, 2),
            })
            print(f"      · {name:<12} acc={acc:.4f}  f1m={f1m:.4f}  "
                  f"({train_s:.1f}s)")
            if best is None or score > best["score"]:
                best = {"name": name, "model": clf, "score": score,
                        "accuracy": acc, "f1_macro": f1m,
                        "train_seconds": train_s}
        except Exception as e:  # pragma: no cover
            print(f"      · {name:<12} ECHEC · {e}")

    saved = _save_model(best["name"], best["model"], out_dir, "format_detector")
    with open(os.path.join(out_dir, "format_classes.json"), "w",
              encoding="utf-8") as f:
        json.dump(classes, f, ensure_ascii=False, indent=2)
    print(f"      => GAGNANT · {best['name']} (acc={best['accuracy']:.4f}) "
          f"-> {os.path.basename(saved)}")
    return {
        "task": "format_detector", "winner": best["name"],
        "accuracy": best["accuracy"], "f1_macro": best["f1_macro"],
        "n_classes": len(classes), "train_seconds": best["train_seconds"],
        "saved_to": os.path.basename(saved), "leaderboard": leaderboard,
    }


def _train_binary(df: pd.DataFrame, out_dir: str, label_col: str,
                  features: list[str], task_name: str,
                  use_pos_weight: bool = False) -> dict[str, Any]:
    print(f"\n[?/3] {task_name} · binaire sur {len(features)} features (4 candidats)")
    X = df[features].values
    y = df[label_col].values
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    pos = int(y_tr.sum())
    neg = len(y_tr) - pos
    spw = neg / max(pos, 1) if use_pos_weight else 1.0
    print(f"      taux base · {y.mean():.2%} positifs"
          + (f" · scale_pos_weight={spw:.1f}" if use_pos_weight else ""))

    leaderboard = []
    best = None
    for name, clf in _candidates_binary(scale_pos_weight=spw):
        try:
            t0 = time.time()
            clf.fit(X_tr, y_tr)
            train_s = time.time() - t0
            y_proba = clf.predict_proba(X_te)[:, 1]
            auc = roc_auc_score(y_te, y_proba)
            y_pred = (y_proba > 0.5).astype(int)
            acc = accuracy_score(y_te, y_pred)
            f1 = f1_score(y_te, y_pred) if pos > 0 else 0.0
            score = auc  # AUC = critère principal pour binaire déséquilibré
            leaderboard.append({
                "candidate": name, "auc": round(auc, 4),
                "accuracy": round(acc, 4), "f1": round(f1, 4),
                "train_s": round(train_s, 2),
            })
            print(f"      · {name:<12} AUC={auc:.4f}  acc={acc:.4f}  "
                  f"f1={f1:.4f}  ({train_s:.1f}s)")
            if best is None or score > best["score"]:
                best = {"name": name, "model": clf, "score": score,
                        "auc": auc, "accuracy": acc, "f1": f1,
                        "train_seconds": train_s}
        except Exception as e:  # pragma: no cover
            print(f"      · {name:<12} ECHEC · {e}")

    saved = _save_model(best["name"], best["model"], out_dir, task_name)
    print(f"      => GAGNANT · {best['name']} (AUC={best['auc']:.4f}) "
          f"-> {os.path.basename(saved)}")
    return {
        "task": task_name, "winner": best["name"],
        "auc": best["auc"], "accuracy": best["accuracy"], "f1": best["f1"],
        "train_seconds": best["train_seconds"],
        "saved_to": os.path.basename(saved), "leaderboard": leaderboard,
    }


def _train_collision_risk(df: pd.DataFrame, out_dir: str) -> dict[str, Any]:
    return _train_binary(df, out_dir, "label_collision", MPI_FEATURES,
                         "collision_risk", use_pos_weight=True)


def _train_ddn_validity(df: pd.DataFrame, out_dir: str) -> dict[str, Any]:
    return _train_binary(df, out_dir, "label_ddn_valid", LINE_FEATURES,
                         "ddn_validity", use_pos_weight=False)


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
