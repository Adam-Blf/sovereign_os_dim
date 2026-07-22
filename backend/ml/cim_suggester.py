"""
Suggesteur local de codes de la classification internationale des maladies
(10e révision, chapitre F - psychiatrie).

Modèle de classification de texte entraîné localement sur des libellés
synthétiques (variantes de formulations cliniques par code). Aucune donnée
patient réelle. Vectorisation par n-grammes de caractères (robuste aux
fautes de frappe et abréviations) + régression logistique.

Il sert de fournisseur PAR DÉFAUT à l'écran de suggestion diagnostique :
disponible sans aucune configuration, 100 % local. Un serveur Ollama
intranet peut le remplacer si configuré (variable OLLAMA_BASE).

Usage :
    python -m backend.ml.cim_suggester          # entraîne + sauvegarde
    from backend.ml.cim_suggester import suggest
    suggest("syndrome depressif majeur")        # -> top 5 [{code, libelle, confiance}]
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODELS_DIR / "cim_suggester.joblib"

# Codes psychiatriques courants : code -> (libellé officiel court, formulations synthétiques)
CODES = {
    "F00": ("Démence de la maladie d'Alzheimer", ["demence alzheimer", "troubles cognitifs alzheimer", "maladie d'alzheimer avec demence"]),
    "F05": ("Delirium", ["syndrome confusionnel", "confusion aigue", "delirium"]),
    "F10.2": ("Troubles liés à l'alcool, syndrome de dépendance", ["dependance alcool", "alcoolodependance", "ethylisme chronique", "sevrage alcoolique programme"]),
    "F12.2": ("Troubles liés au cannabis, dépendance", ["dependance cannabis", "consommation quotidienne cannabis", "addiction cannabis"]),
    "F20.0": ("Schizophrénie paranoïde", ["schizophrenie paranoide", "delire paranoide chronique", "psychose schizophrenique paranoide"]),
    "F20.5": ("Schizophrénie résiduelle", ["schizophrenie residuelle", "symptomes negatifs chroniques schizophrenie"]),
    "F22": ("Troubles délirants persistants", ["delire chronique persistant", "trouble delirant persistant", "paranoia"]),
    "F23": ("Troubles psychotiques aigus et transitoires", ["bouffee delirante aigue", "episode psychotique aigu", "psychose aigue transitoire"]),
    "F25": ("Troubles schizo-affectifs", ["trouble schizoaffectif", "psychose schizoaffective", "episode schizoaffectif"]),
    "F31.1": ("Trouble bipolaire, épisode maniaque", ["episode maniaque bipolaire", "acces maniaque", "manie aigue trouble bipolaire"]),
    "F31.4": ("Trouble bipolaire, épisode dépressif sévère", ["depression severe bipolaire", "episode depressif severe trouble bipolaire"]),
    "F32.1": ("Épisode dépressif moyen", ["episode depressif moyen", "depression moderee", "syndrome depressif intensite moyenne"]),
    "F32.2": ("Épisode dépressif sévère sans symptômes psychotiques", ["depression severe", "episode depressif majeur", "syndrome depressif majeur", "depression grave sans psychose"]),
    "F32.3": ("Épisode dépressif sévère avec symptômes psychotiques", ["depression severe psychotique", "melancolie delirante", "depression avec elements psychotiques"]),
    "F33.2": ("Trouble dépressif récurrent, épisode sévère", ["depression recurrente severe", "recidive depressive severe", "trouble depressif recurrent"]),
    "F41.0": ("Trouble panique", ["attaques de panique", "trouble panique", "crises d'angoisse paroxystiques"]),
    "F41.1": ("Anxiété généralisée", ["anxiete generalisee", "trouble anxieux generalise", "angoisse permanente"]),
    "F42": ("Trouble obsessionnel-compulsif", ["trouble obsessionnel compulsif", "obsessions compulsions", "rituels de verification envahissants"]),
    "F43.1": ("État de stress post-traumatique", ["stress post traumatique", "syndrome psychotraumatique", "reviviscences traumatiques"]),
    "F43.2": ("Troubles de l'adaptation", ["trouble de l'adaptation", "reaction depressive situationnelle", "difficultes adaptation evenement de vie"]),
    "F50.0": ("Anorexie mentale", ["anorexie mentale", "restriction alimentaire severe", "trouble du comportement alimentaire restrictif"]),
    "F50.2": ("Boulimie", ["boulimie", "crises de boulimie avec vomissements", "hyperphagie compensatoire"]),
    "F60.3": ("Personnalité émotionnellement labile", ["personnalite borderline", "personnalite etat limite", "instabilite emotionnelle limite"]),
    "F60.2": ("Personnalité dyssociale", ["personnalite antisociale", "personnalite dyssociale"]),
    "F70": ("Retard mental léger", ["retard mental leger", "deficience intellectuelle legere"]),
    "F84.0": ("Autisme infantile", ["autisme infantile", "trouble du spectre autistique", "trouble envahissant du developpement"]),
    "F90.0": ("Perturbation de l'activité et de l'attention", ["deficit attention hyperactivite", "hyperactivite avec trouble attentionnel", "trouble attentionnel enfant"]),
    "F91": ("Troubles des conduites", ["trouble des conduites", "conduites antisociales enfant", "comportements transgressifs repetes"]),
    "F95": ("Tics", ["tics moteurs", "syndrome de tics", "tics chroniques"]),
    "X60-X84": ("Lésions auto-infligées", ["tentative de suicide", "geste auto agressif", "intoxication medicamenteuse volontaire", "scarifications"]),
}


def _fold(text: str) -> str:
    """Minuscule + suppression des accents pour vectorisation robuste."""
    t = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _augment(rng, phrase: str) -> list[str]:
    """Variantes synthétiques simples : troncatures, mots melanges, prefixes cliniques."""
    words = phrase.split()
    out = [phrase]
    if len(words) > 2:
        out.append(" ".join(words[::-1]))
        out.append(" ".join(words[1:]))
    out.append("patient presentant " + phrase)
    out.append(phrase + " a l'admission")
    out.append(phrase[: max(8, int(len(phrase) * 0.8))])
    return out


def train() -> None:
    import joblib
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer

    rng = np.random.default_rng(42)
    texts, labels = [], []
    for code, (_, phrases) in CODES.items():
        for p in phrases:
            for variant in _augment(rng, _fold(p)):
                texts.append(variant)
                labels.append(code)

    pipe = Pipeline(
        [
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=1)),
            ("clf", LogisticRegression(max_iter=2000, C=10.0)),
        ]
    )
    pipe.fit(texts, labels)
    acc = pipe.score(texts, labels)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, MODEL_PATH)
    print(f"[OK] cim_suggester - {len(CODES)} codes, {len(texts)} libellés synthétiques, exactitude interne {acc:.2f}")


_PIPE = None


def suggest(text: str, top: int = 5, min_confidence: float = 0.02) -> list[dict]:
    """Top N codes suggérés pour un libellé clinique libre.

    `top` et `min_confidence` sont pilotables en production via les
    variables d'environnement CIM_SUGGEST_TOP_K / CIM_SUGGEST_MIN_CONFIDENCE
    (voir backend/interfaces/_sentinel.py::cim_suggest), sans redéploiement.
    """
    global _PIPE
    if not text or not text.strip():
        return []
    if _PIPE is None:
        import joblib

        if not MODEL_PATH.exists():
            return []
        _PIPE = joblib.load(MODEL_PATH)
    proba = _PIPE.predict_proba([_fold(text)])[0]
    classes = _PIPE.classes_
    order = proba.argsort()[::-1][:top]
    return [
        {
            "code": str(classes[i]),
            "label": CODES.get(str(classes[i]), ("?",))[0],
            "confidence": round(float(proba[i]), 3),
        }
        for i in order
        if proba[i] > min_confidence
    ]


if __name__ == "__main__":
    train()
