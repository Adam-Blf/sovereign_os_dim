"""
Entraînement des modèles séjour : prédicteur de durée de séjour et
regroupement de patients (projection UMAP + K-moyennes).

Données : 100 % synthétiques, générées ici même à partir de distributions
plausibles par groupe diagnostique de la classification internationale des
maladies (chapitre F, psychiatrie). Aucune donnée patient réelle n'est
utilisée ni requise : ces modèles servent d'aide à la lecture et leurs
sorties sont toujours présentées comme des estimations.

Sorties (backend/ml/models/) :
- duree_sejour_predictor.json   : régresseur XGBoost (durée en jours)
- duree_sejour_meta.json        : métriques + statistiques par groupe
- regroupement_patients.json    : projection 2D + centres + archétypes

Usage :
    python -m backend.ml.train_sejour_models
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

MODELS_DIR = Path(__file__).resolve().parent / "models"

# Groupes diagnostiques (chapitre F) avec durée moyenne de séjour plausible
# en psychiatrie adulte/infanto-juvénile : (libellé, moyenne jours, écart-type)
GROUPES = {
    "F0": ("Troubles mentaux organiques", 45.0, 18.0),
    "F1": ("Troubles liés aux substances psychoactives", 21.0, 10.0),
    "F2": ("Schizophrénie et troubles délirants", 52.0, 22.0),
    "F3": ("Troubles de l'humeur", 34.0, 14.0),
    "F4": ("Troubles névrotiques et anxieux", 18.0, 8.0),
    "F5": ("Syndromes comportementaux", 27.0, 12.0),
    "F6": ("Troubles de la personnalité", 24.0, 11.0),
    "F7": ("Retard mental", 38.0, 16.0),
    "F8": ("Troubles du développement psychologique", 30.0, 13.0),
    "F9": ("Troubles apparaissant dans l'enfance", 22.0, 9.0),
}

MODES_LEGAUX = ["libre", "SDT", "SDRE", "péril imminent"]
SECTEURS = ["I", "G", "P", "Z"]


def _synth_sejours(rng: np.random.Generator, n: int = 20000):
    """Génère n séjours synthétiques : features + durée cible."""
    codes = list(GROUPES)
    grp = rng.integers(0, len(codes), n)
    age = np.clip(rng.normal(38, 18, n), 4, 95)
    mode = rng.integers(0, len(MODES_LEGAUX), n)
    secteur = rng.integers(0, len(SECTEURS), n)
    nb_actes = np.clip(rng.poisson(6, n), 0, 40)
    readmission = rng.random(n) < 0.22

    mu = np.array([GROUPES[codes[g]][1] for g in grp])
    sd = np.array([GROUPES[codes[g]][2] for g in grp])
    duree = rng.normal(mu, sd)
    # Effets simples et plausibles : contrainte legale allonge, ambulatoire (Z) raccourcit
    duree += (mode > 0) * rng.normal(9, 3, n)
    duree += (secteur == 3) * rng.normal(-8, 2, n)
    duree += readmission * rng.normal(5, 2, n)
    duree += (age > 65) * rng.normal(6, 2, n)
    duree = np.clip(duree, 1, 400)

    X = np.column_stack([grp, age, mode, secteur, nb_actes, readmission.astype(int)])
    return X.astype(np.float32), duree.astype(np.float32), grp


def train_duree_sejour(rng: np.random.Generator) -> dict:
    """Régresseur XGBoost durée de séjour + métriques honnêtes (jeu de test)."""
    import xgboost as xgb
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.model_selection import train_test_split

    X, y, grp = _synth_sejours(rng)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    model = xgb.XGBRegressor(
        n_estimators=300, max_depth=5, learning_rate=0.08,
        subsample=0.9, colsample_bytree=0.9, random_state=42,
    )
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    mae = float(mean_absolute_error(yte, pred))
    r2 = float(r2_score(yte, pred))

    model.save_model(str(MODELS_DIR / "duree_sejour_predictor.json"))

    par_groupe = []
    codes = list(GROUPES)
    for i, code in enumerate(codes):
        mask = grp == i
        par_groupe.append(
            {
                "groupe": code,
                "libelle": GROUPES[code][0],
                "duree_moyenne_jours": round(float(y[mask].mean()), 1),
                "ecart_type_jours": round(float(y[mask].std()), 1),
                "sejours_synthetiques": int(mask.sum()),
            }
        )
    meta = {
        "type": "regression",
        "algorithme": "XGBoost (300 arbres, profondeur 5)",
        "donnees": "20 000 séjours synthétiques (aucune donnée réelle)",
        "erreur_absolue_moyenne_jours": round(mae, 1),
        "coefficient_determination": round(r2, 3),
        "variables": [
            "groupe diagnostique", "âge", "mode légal de soins",
            "secteur", "nombre d'actes", "réadmission",
        ],
        "par_groupe": par_groupe,
    }
    (MODELS_DIR / "duree_sejour_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"[OK] duree_sejour_predictor - erreur absolue moyenne {mae:.1f} j, R2 {r2:.3f}")
    return meta


ARCHETYPES = [
    "Séjours longs psychotiques",
    "Épisodes de l'humeur, séjours moyens",
    "Ambulatoire intensif jeunes",
    "Soins sous contrainte, réadmissions",
    "Anxieux, séjours courts",
    "Gérontopsychiatrie",
]


def train_regroupement(rng: np.random.Generator) -> dict:
    """Projection UMAP 2D + K-moyennes (6 archétypes) sur patients synthétiques."""
    import umap
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    X, y, grp = _synth_sejours(rng, n=3000)
    # Vecteur patient : groupe, âge, mode, secteur, actes, réadmission + durée observée
    feats = np.column_stack([X, y])
    Xs = StandardScaler().fit_transform(feats)

    reducer = umap.UMAP(n_components=2, n_neighbors=25, min_dist=0.15, random_state=42)
    coords = reducer.fit_transform(Xs)

    km = KMeans(n_clusters=6, n_init=10, random_state=42)
    labels = km.fit_predict(Xs)

    # Échantillon pour l'affichage (600 points suffisent à l'écran)
    idx = rng.choice(len(coords), size=600, replace=False)
    points = [
        {
            "x": round(float(coords[i, 0]), 2),
            "y": round(float(coords[i, 1]), 2),
            "groupe_archetype": int(labels[i]),
        }
        for i in idx
    ]
    clusters = []
    for c in range(6):
        mask = labels == c
        clusters.append(
            {
                "identifiant": c,
                "libelle": ARCHETYPES[c],
                "effectif": int(mask.sum()),
                "duree_moyenne_jours": round(float(y[mask].mean()), 1),
                "age_moyen": round(float(X[mask, 1].mean()), 1),
            }
        )
    artefact = {
        "algorithme": "Projection UMAP (2 dimensions) puis K-moyennes (6 groupes)",
        "donnees": "3 000 patients synthétiques (aucune donnée réelle)",
        "points": points,
        "archetypes": clusters,
    }
    (MODELS_DIR / "regroupement_patients.json").write_text(
        json.dumps(artefact, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[OK] regroupement_patients - 6 archétypes, {len(points)} points projetés")
    return artefact


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    train_duree_sejour(rng)
    train_regroupement(rng)


if __name__ == "__main__":
    main()
