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
from functools import lru_cache
from typing import Any

import numpy as np

from .synthetic import _line_features, _mpi_features  # noqa · partage features

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


# ─────────────────────────────────────────────────────────────────────────────
# CHARGEMENT (cache lru pour éviter rechargements multiples)
# ─────────────────────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def load_models() -> dict[str, Any]:
    """
    Charge les 3 modèles XGBoost et le mapping de classes.
    Renvoie {} si les modèles ne sont pas encore entraînés (silencieux).
    """
    try:
        import xgboost as xgb
    except ImportError:  # pragma: no cover
        return {}

    models: dict[str, Any] = {}

    fmt_path = os.path.join(MODELS_DIR, "format_detector.json")
    classes_path = os.path.join(MODELS_DIR, "format_classes.json")
    if os.path.exists(fmt_path) and os.path.exists(classes_path):
        clf = xgb.XGBClassifier()
        clf.load_model(fmt_path)
        with open(classes_path, encoding="utf-8") as f:
            classes = json.load(f)
        models["format"] = clf
        models["format_classes"] = classes

    coll_path = os.path.join(MODELS_DIR, "collision_risk.json")
    if os.path.exists(coll_path):
        clf = xgb.XGBClassifier()
        clf.load_model(coll_path)
        models["collision"] = clf

    ddn_path = os.path.join(MODELS_DIR, "ddn_validity.json")
    if os.path.exists(ddn_path):
        clf = xgb.XGBClassifier()
        clf.load_model(ddn_path)
        models["ddn"] = clf

    return models


# ─────────────────────────────────────────────────────────────────────────────
# INFÉRENCE
# ─────────────────────────────────────────────────────────────────────────────


def _line_to_array(line: str) -> np.ndarray:
    feats = _line_features(line)
    # Ordre stable des colonnes · doit matcher l'ordre d'entraînement
    keys = [
        "length", "digits_ratio", "spaces_ratio", "alpha_ratio",
        "first8_is_numeric", "has_ddn_pattern_28_8",
        "char_pos_0_isdigit", "char_pos_19_isdigit",
        "char_pos_50_isdigit", "char_pos_100_isdigit",
        "char_pos_200_isdigit",
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
    clf = models["format"]
    classes = models["format_classes"]
    X = _line_to_array(line)
    proba = clf.predict_proba(X)[0]
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
    proba = models["collision"].predict_proba(X)[0]
    return float(proba[1])


def predict_ddn_validity(line: str) -> float:
    """Probabilité que la DDN d'une ligne soit valide (1 = certaine)."""
    models = load_models()
    if "ddn" not in models:
        return 1.0  # par défaut on considère valide si pas de modèle
    X = _line_to_array(line)
    proba = models["ddn"].predict_proba(X)[0]
    return float(proba[1])
