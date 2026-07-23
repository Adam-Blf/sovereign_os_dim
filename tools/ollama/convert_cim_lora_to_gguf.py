"""
Convertit l'adaptateur LoRA CimSuggester (backend/ml/models/cim_lora_adapter/,
produit par backend/ml/train_cim_lora.py ou le notebook Colab
notebooks/train_cim_lora_colab.ipynb) en GGUF servable par Ollama.

Nécessite un clone de llama.cpp (outil externe, hors de ce dépôt - seuls ses
scripts Python de conversion sont utilisés, aucune compilation C++ requise) :
    git clone --depth 1 https://github.com/ggml-org/llama.cpp.git

Usage :
    python tools/ollama/convert_cim_lora_to_gguf.py --llama-cpp-dir C:/Users/adamb/llama.cpp

Produit tools/ollama/cim-lora-adapter.gguf, référencé par la directive
ADAPTER de tools/ollama/Modelfile.sovereign-cim.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ADAPTER_DIR = ROOT / "backend" / "ml" / "models" / "cim_lora_adapter"
OUTPUT_GGUF = Path(__file__).resolve().parent / "cim-lora-adapter.gguf"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--llama-cpp-dir", required=True,
        help="Chemin vers un clone local de github.com/ggml-org/llama.cpp",
    )
    parser.add_argument("--outtype", default="f16", choices=["f32", "f16", "bf16", "q8_0", "auto"])
    args = parser.parse_args()

    convert_script = Path(args.llama_cpp_dir) / "convert_lora_to_gguf.py"
    if not convert_script.exists():
        sys.exit(f"[!] {convert_script} introuvable - verifier --llama-cpp-dir")
    if not ADAPTER_DIR.exists():
        sys.exit(
            f"[!] {ADAPTER_DIR} introuvable - lancer d'abord l'entrainement "
            "(backend/ml/train_cim_lora.py ou notebooks/train_cim_lora_colab.ipynb)"
        )

    cmd = [
        sys.executable, str(convert_script),
        "--outfile", str(OUTPUT_GGUF),
        "--outtype", args.outtype,
        str(ADAPTER_DIR),
    ]
    print("[convert_cim_lora_to_gguf]", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"[OK] {OUTPUT_GGUF}")


if __name__ == "__main__":
    main()
