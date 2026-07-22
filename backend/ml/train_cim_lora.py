"""
Entraîne un adaptateur LoRA pour le suggesteur CIM-10 sur un petit LLM local
(Qwen2.5-0.5B-Instruct), à partir du dataset synthétique produit par
backend/ml/gen_cim_lora_dataset.py.

Dépendances lourdes (torch, transformers, peft, datasets, accelerate) :
voir requirements-train.txt, jamais installées sur poste hôpital ni dans le
build PyInstaller - uniquement pour l'entraînement sur machine de dev.

Detecte automatiquement CUDA (bf16 + batch plus large si disponible, sinon
repli CPU fp32 + petit batch). Un run CPU 600 steps s'est avere trop lent
(~178 s/step observe, ~30h) - voir notebooks/train_cim_lora_colab.ipynb pour
lancer l'entrainement sur un GPU T4 gratuit (Google Colab), quelques minutes
au lieu d'heures. Le cap max_steps (pas epoch-based) reste le garde-fou
anti-derapage dans les deux cas.

Usage :
    python -m backend.ml.train_cim_lora                 # run complet (max_steps=600)
    python -m backend.ml.train_cim_lora --max-steps 20   # smoke test chronometre
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
MODELS_DIR = Path(__file__).resolve().parent / "models"
ADAPTER_DIR = MODELS_DIR / "cim_lora_adapter"
CHECKPOINT_DIR = MODELS_DIR / "_cim_lora_checkpoints"
META_PATH = MODELS_DIR / "cim_lora_training_meta.json"
DATASET_PATH = Path(__file__).resolve().parent / "data" / "cim_lora_dataset.jsonl"

SYSTEM_PROMPT = (
    'Tu es un médecin du département d\'information médicale d\'un\n'
    'établissement psychiatrique français. À partir de libellés cliniques,\n'
    'tu proposes exactement 5 codes candidats de la classification\n'
    'internationale des maladies (10e révision, chapitre F en priorité),\n'
    'au format JSON strict :\n'
    '[{"code": "F32.2", "label": "Épisode dépressif sévère", "confidence": 0.9}, ...]\n'
    'Tu ne réponds RIEN d\'autre que ce tableau JSON. Tu ne donnes jamais de\n'
    'conseil de prise en charge. Si les libellés sont vides ou hors champ,\n'
    'tu renvoies un tableau vide []."'
)

LORA_TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


def load_dataset_examples() -> list[dict]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"{DATASET_PATH} introuvable - lancer d'abord : "
            "python -m backend.ml.gen_cim_lora_dataset"
        )
    examples = []
    with DATASET_PATH.open(encoding="utf-8") as f:
        for line in f:
            examples.append(json.loads(line))
    return examples


def build_hf_dataset(tokenizer, examples: list[dict], max_seq_length: int = 320):
    from datasets import Dataset

    def to_features(ex: dict) -> dict:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": ex["prompt"]},
        ]
        prompt_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        full_text = prompt_text + ex["completion"] + tokenizer.eos_token

        prompt_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
        full = tokenizer(full_text, add_special_tokens=False, truncation=True, max_length=max_seq_length)
        input_ids = full["input_ids"]
        labels = list(input_ids)
        # Masque la loss sur system+user - seule la completion doit compter.
        mask_len = min(len(prompt_ids), len(labels))
        for i in range(mask_len):
            labels[i] = -100
        return {"input_ids": input_ids, "attention_mask": full["attention_mask"], "labels": labels}

    ds = Dataset.from_list(examples)
    return ds.map(to_features, remove_columns=ds.column_names)


def train(max_steps: int = 600) -> dict:
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        DataCollatorForSeq2Seq,
        Trainer,
        TrainingArguments,
    )

    t0 = time.time()
    examples = load_dataset_examples()
    print(f"[train_cim_lora] {len(examples)} exemples charges depuis {DATASET_PATH.name}")

    has_cuda = torch.cuda.is_available()
    dtype = torch.bfloat16 if has_cuda else torch.float32
    batch_size = 8 if has_cuda else 2
    grad_accum = 2 if has_cuda else 8
    print(f"[train_cim_lora] accelerateur : {'CUDA (' + torch.cuda.get_device_name(0) + ')' if has_cuda else 'CPU uniquement'}")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, dtype=dtype)

    lora_config = LoraConfig(
        r=8, lora_alpha=16, lora_dropout=0.05, bias="none",
        target_modules=LORA_TARGET_MODULES, task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    # Requis avec gradient_checkpointing=True + PEFT : sans ca, aucun tenseur
    # d'entree n'a requires_grad=True (le modele de base est gele), et le
    # graphe de retropropagation ne peut pas se construire (RuntimeError:
    # element 0 of tensors does not require grad and does not have a grad_fn).
    model.enable_input_require_grads()
    model.print_trainable_parameters()

    hf_dataset = build_hf_dataset(tokenizer, examples)

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    training_args = TrainingArguments(
        output_dir=str(CHECKPOINT_DIR),
        max_steps=max_steps,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        gradient_checkpointing=True,
        bf16=has_cuda,
        optim="adamw_torch",
        dataloader_num_workers=0,
        save_strategy="steps",
        save_steps=150,
        save_total_limit=2,
        logging_steps=10,
        seed=42,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=hf_dataset,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model, padding=True),
    )
    train_result = trainer.train()

    ADAPTER_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(ADAPTER_DIR))
    tokenizer.save_pretrained(str(ADAPTER_DIR))

    meta = {
        "base_model": BASE_MODEL,
        "accelerator": torch.cuda.get_device_name(0) if has_cuda else "CPU",
        "dataset_examples": len(examples),
        "max_steps": max_steps,
        "steps_completed": train_result.global_step,
        "final_loss": train_result.training_loss,
        "wall_clock_seconds": round(time.time() - t0, 1),
        "lora_r": 8,
        "lora_alpha": 16,
        "target_modules": LORA_TARGET_MODULES,
        "seed": 42,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    # Ecrit en dernier, apres sauvegarde reussie de l'adaptateur - son
    # absence signale un echec, sans avoir a parser les logs.
    META_PATH.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Adaptateur LoRA sauvegarde dans {ADAPTER_DIR}")
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-steps", type=int, default=600, help="Cap dur du nombre de steps (defaut : 600)")
    args = parser.parse_args()
    train(max_steps=args.max_steps)


if __name__ == "__main__":
    main()
