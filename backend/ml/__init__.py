"""
═══════════════════════════════════════════════════════════════════════════════
 SOVEREIGN OS DIM · Machine Learning module
═══════════════════════════════════════════════════════════════════════════════

Modèles XGBoost entraînés localement sur des données synthétiques fidèles
aux specifications ATIH (2000-2026). Aucun fichier PMSI réel n'est utilisé
pour l'entraînement · les vraies données patient restent sur le poste DIM.

Modèles fournis ·
- format_detector  · classification multi-classe (23+ formats ATIH)
- collision_risk   · binaire (probabilité de collision IDV)
- ddn_validity     · binaire (probabilité d'erreur de saisie DDN)

Voir backend/ml/synthetic.py pour la génération de données et
backend/ml/train.py pour le pipeline d'entraînement.
═══════════════════════════════════════════════════════════════════════════════
"""

from .predict import (
    predict_format,
    predict_collision_risk,
    predict_ddn_validity,
    load_models,
)

__all__ = [
    "predict_format",
    "predict_collision_risk",
    "predict_ddn_validity",
    "load_models",
]
