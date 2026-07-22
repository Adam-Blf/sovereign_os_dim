"""
Génère un dataset synthétique instruction/completion pour le fine-tuning
LoRA du suggesteur CIM-10 (backend/ml/train_cim_lora.py).

Aucune donnée patient réelle - uniquement des libellés cliniques synthétiques
construits à partir des codes et formulations déjà présents dans
backend/ml/cim_suggester.py (CODES). Contrairement à cim_suggester._augment()
(pensé pour rendre un vectoriseur TF-IDF robuste au bruit), ce générateur
produit du texte français propre et varié : le fine-tuning d'un LLM sur du
texte volontairement dégradé lui apprendrait à produire du français cassé.

Le format du prompt utilisateur reproduit exactement celui utilisé en
production par backend/interfaces/_sentinel.py::cim_suggest() ("DAS: ...
Actes: ... Notes: ...") - un dataset d'entraînement qui ne matche pas la
distribution réelle des prompts est un risque d'échec silencieux (bonnes
métriques synthétiques, mauvaise qualité réelle).

Usage :
    python -m backend.ml.gen_cim_lora_dataset
    -> écrit backend/ml/data/cim_lora_dataset.jsonl
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from backend.ml.cim_suggester import CODES

DATA_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_PATH = DATA_DIR / "cim_lora_dataset.jsonl"

# Doit rester identique au prompt réellement envoyé par cim_suggest() côté
# Ollama (backend/interfaces/_sentinel.py) pour que l'entraînement voie la
# même distribution qu'en production.
PROMPT_TEMPLATE = (
    "Tu es un médecin DIM. Suggère 5 codes CIM-10 candidats pour "
    "diagnostic principal en psychiatrie, avec confiance 0-1. "
    "DAS: {das}. Actes: {actes}. Notes: {notes}"
)

NOTE_TEMPLATES = [
    "Patient de {age} ans, antécédents de {contexte}, présente {phrase}.",
    "Notes d'admission : {phrase}, sans notion de trouble antérieur connu.",
    "Suivi ambulatoire pour {phrase}.",
    "Entrée en urgence : {phrase}, contexte de {contexte}.",
    "Bilan d'entrée - {phrase} chez un patient de {age} ans.",
    "Consultation de suivi : {phrase}, évolution sous traitement à réévaluer.",
]

CONTEXTES = [
    "rupture thérapeutique", "isolement social", "précarité", "conflit familial",
    "consommation de toxiques", "sortie d'hospitalisation récente", "aucun antécédent notable",
]

ACTES_POOL = [
    "entretien médical", "bilan biologique", "consultation infirmière",
    "electroencéphalogramme", "entretien psychologique", "bilan somatique",
]

DAS_POOL = ["trouble du sommeil", "anxiété réactionnelle", "asthénie", "aucun"]


def _clinical_phrase(rng: random.Random, code: str, phrases: list[str]) -> str:
    return rng.choice(phrases)


def _distractors(rng: random.Random, true_code: str, n: int = 4) -> list[str]:
    """Choisit des codes distracteurs, préférentiellement du même chapitre F."""
    prefix = true_code.split(".")[0][:2]
    same_chapter = [c for c in CODES if c != true_code and c.startswith(prefix)]
    others = [c for c in CODES if c != true_code and not c.startswith(prefix)]
    rng.shuffle(same_chapter)
    rng.shuffle(others)
    pool = (same_chapter + others)[:n]
    return pool


def _completion(rng: random.Random, true_code: str) -> str:
    label = CODES[true_code][0]
    entries = [{"code": true_code, "label": label, "confidence": round(rng.uniform(0.75, 0.95), 2)}]
    remaining_conf = 0.6
    for code in _distractors(rng, true_code, 4):
        conf = round(remaining_conf * rng.uniform(0.4, 0.8), 2)
        remaining_conf = max(conf - 0.05, 0.02)
        entries.append({"code": code, "label": CODES[code][0], "confidence": conf})
    return json.dumps(entries, ensure_ascii=False)


def generate(seed: int = 42, per_code: int = 160) -> list[dict]:
    rng = random.Random(seed)
    examples = []
    for code, (_, phrases) in CODES.items():
        for _ in range(per_code):
            phrase = _clinical_phrase(rng, code, phrases)
            template = rng.choice(NOTE_TEMPLATES)
            notes = template.format(
                phrase=phrase,
                age=rng.randint(19, 82),
                contexte=rng.choice(CONTEXTES),
            )
            das = rng.choice(DAS_POOL)
            actes = rng.choice(ACTES_POOL)
            prompt = PROMPT_TEMPLATE.format(das=das, actes=actes, notes=notes)
            examples.append({
                "das": das,
                "actes": actes,
                "notes": notes,
                "prompt": prompt,
                "completion": _completion(rng, code),
                "true_code": code,
            })
    rng.shuffle(examples)
    return examples


def main() -> None:
    examples = generate()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print(f"[OK] {len(examples)} exemples ecrits dans {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
