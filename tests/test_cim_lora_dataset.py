"""
Tests du generateur de dataset LoRA CIM-10 (backend/ml/gen_cim_lora_dataset.py).

Ne teste QUE le generateur, jamais l'entrainement (backend/ml/train_cim_lora.py) -
ce dernier depend de torch/transformers/peft/datasets (requirements-train.txt,
jamais installes en CI). Rapide, deterministe, sans reseau, dans l'esprit de
tests/test_no_network.py.
"""

from __future__ import annotations

import json

from backend.ml.cim_suggester import CODES
from backend.ml.gen_cim_lora_dataset import generate


def test_generate_returns_well_formed_examples():
    examples = generate(seed=42, per_code=10)
    assert len(examples) == len(CODES) * 10
    for ex in examples:
        assert set(ex.keys()) >= {"das", "actes", "notes", "prompt", "completion", "true_code"}
        assert ex["true_code"] in CODES


def test_every_completion_is_five_valid_json_candidates():
    examples = generate(seed=42, per_code=5)
    for ex in examples:
        candidates = json.loads(ex["completion"])
        assert isinstance(candidates, list)
        assert len(candidates) == 5
        for c in candidates:
            assert set(c.keys()) == {"code", "label", "confidence"}
            assert c["code"] in CODES
            assert 0.0 <= c["confidence"] <= 1.0


def test_true_code_is_first_and_highest_confidence_candidate():
    examples = generate(seed=42, per_code=5)
    for ex in examples:
        candidates = json.loads(ex["completion"])
        assert candidates[0]["code"] == ex["true_code"]
        confidences = [c["confidence"] for c in candidates]
        assert confidences[0] == max(confidences)


def test_prompt_matches_runtime_format():
    examples = generate(seed=42, per_code=1)
    for ex in examples:
        assert ex["prompt"].startswith("Tu es un médecin DIM.")
        assert f"DAS: {ex['das']}." in ex["prompt"]
        assert f"Actes: {ex['actes']}." in ex["prompt"]
        assert ex["notes"] in ex["prompt"]


def test_every_code_has_minimum_example_count():
    examples = generate(seed=42, per_code=160)
    counts = {}
    for ex in examples:
        counts[ex["true_code"]] = counts.get(ex["true_code"], 0) + 1
    for code in CODES:
        assert counts.get(code, 0) >= 50, f"{code} a moins de 50 exemples"
