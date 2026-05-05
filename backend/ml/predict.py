"""
═══════════════════════════════════════════════════════════════════════════════
 backend/ml/predict.py · Inférence des modèles XGBoost entraînés
═══════════════════════════════════════════════════════════════════════════════

API d'inférence légère utilisée par le backend Python (api.py / bridge.py)
pour appeler les modèles ML sans recharger les .json à chaque requête.

Modèles attendus dans backend/ml/models/ ·
- format_detector.json   · classifieur multi-classe
- collision_risk.json    · classifieur binaire
- ddn_validity.json      · classifieur binaire
- format_classes.json    · mapping label_id → label_name

Usage ·
    from backend.ml import predict_format, load_models
    load_models()  # une seule fois au boot
    pred, proba = predict_format("12345678   1980  ...")  # ligne brute
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import json
import os
import sys
from functools import lru_cache
from typing import Any

import numpy as np

from .synthetic import _line_features, _mpi_features  # noqa · partage features


def _resolve_models_dir() -> str:
    """
    Trouve le dossier des modèles ML, en mode dev ou bundle PyInstaller.
    PyInstaller dépose les --add-data dans sys._MEIPASS au runtime.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(here, "models")
    if os.path.isdir(candidate):
        return candidate
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        for c in (
            os.path.join(meipass, "backend", "ml", "models"),
            os.path.join(meipass, "models"),
        ):
            if os.path.isdir(c):
                return c
    return candidate  # fallback · le caller verra l'absence proprement


MODELS_DIR = _resolve_models_dir()


# ─────────────────────────────────────────────────────────────────────────────
# CHARGEMENT (cache lru pour éviter rechargements multiples)
# ─────────────────────────────────────────────────────────────────────────────


def _load_one(base_filename: str) -> Any | None:
    """
    Charge le 1er modèle trouvé pour une tâche donnée, en testant les
    formats possibles (XGBoost .json, LightGBM .lgbm.txt, sklearn .pkl).
    """
    # XGBoost
    p = os.path.join(MODELS_DIR, f"{base_filename}.json")
    if os.path.exists(p):
        try:
            import xgboost as xgb
            clf = xgb.XGBClassifier()
            clf.load_model(p)
            return clf
        except Exception:  # pragma: no cover
            pass
    # LightGBM
    p = os.path.join(MODELS_DIR, f"{base_filename}.lgbm.txt")
    if os.path.exists(p):
        try:
            import lightgbm as lgb
            return lgb.Booster(model_file=p)
        except Exception:  # pragma: no cover
            pass
    # sklearn pickle — fichier produit exclusivement par notre train.py local,
    # jamais exposé à des données non-maîtrisées. nosec justifié.
    p = os.path.join(MODELS_DIR, f"{base_filename}.pkl")
    if os.path.exists(p):
        try:
            import pickle
            with open(p, "rb") as f:
                return pickle.load(f)  # nosec B301
        except Exception:  # pragma: no cover
            pass
    return None


def _proba(model: Any, X: np.ndarray) -> np.ndarray:
    """Wrapper · predict_proba pour XGBoost/sklearn, predict pour LightGBM Booster."""
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)
    # LightGBM Booster · predict renvoie déjà des probas
    p = model.predict(X)
    if p.ndim == 1:
        return np.column_stack([1 - p, p])
    return p


@lru_cache(maxsize=1)
def load_models() -> dict[str, Any]:
    """
    Charge les meilleurs modèles entraînés. Détecte automatiquement le type
    (.json XGBoost, .lgbm.txt LightGBM, .pkl sklearn) selon ce que train.py
    a sauvegardé. Renvoie {} si rien n'est entraîné.
    """
    models: dict[str, Any] = {}

    fmt = _load_one("format_detector")
    classes_path = os.path.join(MODELS_DIR, "format_classes.json")
    if fmt is not None and os.path.exists(classes_path):
        with open(classes_path, encoding="utf-8") as f:
            classes = json.load(f)
        models["format"] = fmt
        models["format_classes"] = classes

    col = _load_one("collision_risk")
    if col is not None:
        models["collision"] = col

    ddn = _load_one("ddn_validity")
    if ddn is not None:
        models["ddn"] = ddn

    return models


# ─────────────────────────────────────────────────────────────────────────────
# INFÉRENCE
# ─────────────────────────────────────────────────────────────────────────────


def _line_to_array(line: str) -> np.ndarray:
    """Vectorise une ligne dans le même ordre de features que train.py."""
    feats = _line_features(line)
    # Ordre stable · DOIT matcher LINE_FEATURES dans train.py
    keys = [
        "length", "len_bucket",
        "digits_ratio", "spaces_ratio", "alpha_ratio",
        "tok_had_starts_H", "tok_had_H0X", "tok_had_H1X",
        "tok_starts_M", "tok_starts_digit", "tok_2digit_first",
        "tok_psy_starts_P", "tok_psy_P0X", "tok_psy_P1X",
        "tok_vid_starts_V", "tok_vid_starts_I",
        "double_finess_psy", "leading_filler_10",
        "ddn_at_28_yyyy", "ddn_at_41_yyyy",
        "ddn_at_61_yyyy", "ddn_at_67_yyyy", "ddn_at_77_yyyy",
        "ipp_at_21_numeric",
    ]
    return np.array([[feats[k] for k in keys]], dtype=float)


def predict_format(line: str) -> tuple[str | None, float]:
    """
    Prédit le format ATIH d'une ligne brute.
    Retourne (label, probabilité). (None, 0.0) si modèle non entraîné.
    """
    models = load_models()
    if "format" not in models:
        return None, 0.0
    X = _line_to_array(line)
    proba = _proba(models["format"], X)[0]
    classes = models["format_classes"]
    idx = int(np.argmax(proba))
    return classes[idx], float(proba[idx])


def predict_collision_risk(features: dict) -> float:
    """
    Prédit la probabilité qu'un IPP soit en collision.
    `features` doit contenir · ipp_freq, ddn_variance_days, n_distinct_finess,
    n_distinct_modalities, ipp_with_letters, year_min, year_span.
    """
    models = load_models()
    if "collision" not in models:
        return 0.0
    keys = [
        "ipp_freq", "ddn_variance_days", "n_distinct_finess",
        "n_distinct_modalities", "ipp_with_letters", "year_min", "year_span",
    ]
    X = np.array([[features[k] for k in keys]], dtype=float)
    proba = _proba(models["collision"], X)[0]
    return float(proba[1])


def predict_ddn_validity(line: str) -> float:
    """Probabilité que la DDN d'une ligne soit valide (1 = certaine)."""
    models = load_models()
    if "ddn" not in models:
        return 1.0
    X = _line_to_array(line)
    proba = _proba(models["ddn"], X)[0]
    return float(proba[1])
