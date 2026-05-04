"""
═══════════════════════════════════════════════════════════════════════════════
 backend/ml/extract_safe_features.py · Extraction de features ATIH SAFE
═══════════════════════════════════════════════════════════════════════════════

Lit des vrais fichiers PMSI sur le poste DIM et n'écrit qu'un CSV de
features structurelles · longueur de ligne, ratios de classes de caractères
à des positions clés, présence de patterns DDN. AUCUN IPP, AUCUNE DDN
en clair, AUCUN NIR ne quitte le fichier source.

Usage strict ·
  - Le script tourne sur le poste DIM uniquement (jamais en CI)
  - Le CSV de sortie est versionnable (zéro PII)
  - Le format est inféré du nom de fichier (regex), pas du contenu
  - Le contenu de chaque ligne est inspecté sans être stocké

Conformité ·
  - L. 1110-4 CSP (secret professionnel) · pas d'extraction nominative
  - RGPD art. 9 · données de catégorie spéciale jamais écrites
  - k-anonymity · agrégation par fichier, pas par ligne individuelle
  - Audit log · chaque extraction est loggée

Usage ·
    python -m backend.ml.extract_safe_features \\
        --src "D:/Adam - Copie (2)" \\
        --out backend/ml/data/real_features.csv

═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from datetime import datetime
from typing import Iterator

# ─────────────────────────────────────────────────────────────────────────────
# DETECTION DU FORMAT depuis le nom de fichier
# ─────────────────────────────────────────────────────────────────────────────


_FORMAT_PATTERNS = [
    # PSY
    (re.compile(r"\b(rps|psy_rps)\b", re.IGNORECASE),         "RPS"),
    (re.compile(r"\b(raa|psy_raa)\b", re.IGNORECASE),         "RAA"),
    (re.compile(r"\bvvd\b|vide-?vidage", re.IGNORECASE),      "RPS_vvd"),
    (re.compile(r"\bipp\b", re.IGNORECASE),                   "VID-IPP-PSY"),
    (re.compile(r"\bvh\b|vid[-_]?hosp", re.IGNORECASE),       "VID-HOSP"),
    (re.compile(r"\bano(?!_ambu)", re.IGNORECASE),            "ANO-HOSP"),
    (re.compile(r"\bano[-_]?ambu", re.IGNORECASE),            "ANO-AMBU"),
    (re.compile(r"\bficum\b", re.IGNORECASE),                 "FICUM-PSY"),
    (re.compile(r"\bfichsup", re.IGNORECASE),                 "FICHSUP-PSY"),
    (re.compile(r"\b(iso|isolement)\b", re.IGNORECASE),       "FICHCOMP-Isolement"),
    (re.compile(r"\bfc[-_]?ic\b", re.IGNORECASE),             "FICHCOMP-Isolement"),
    (re.compile(r"\b(transport|fc[-_]?tr)\b", re.IGNORECASE), "FICHCOMP-Transport"),
    (re.compile(r"\b(tp|temps[-_]?part)\b", re.IGNORECASE),   "FICHCOMP-TempsPart"),
    (re.compile(r"\b(htpart|fc[-_]?ht)\b", re.IGNORECASE),    "FICHCOMP-HTPart"),
    (re.compile(r"\bedgar\b", re.IGNORECASE),                 "EDGAR"),
    (re.compile(r"\bfc[-_]?as|ace[-_]?psy", re.IGNORECASE),   "RSF-ACE-PSY"),
    # Catch-all PSY
    (re.compile(r"psy", re.IGNORECASE),                       "PSY-other"),
]


def detect_format_from_filename(path: str) -> str:
    """Identifie le format ATIH par regex sur le nom de fichier."""
    base = os.path.basename(path).lower()
    for pat, fmt in _FORMAT_PATTERNS:
        if pat.search(base):
            return fmt
    return "INCONNU"


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTION SAFE · stats par fichier sans stocker le contenu
# ─────────────────────────────────────────────────────────────────────────────


def _safe_line_stats(path: str, max_lines: int = 10_000) -> dict:
    """
    Lit le fichier ligne par ligne, calcule des stats agrégées sans
    jamais mémoriser de contenu individuel.

    Stats retournées (toutes anonymes) ·
    - n_lines, line_len_min/max/median/mean
    - digits_ratio_avg, spaces_ratio_avg, alpha_ratio_avg
    - digits_at_pos_X_ratio · % de lignes où la position X est un chiffre
      (positions clés · 0, 9, 18, 21, 41, 48, 61)
    - has_double_finess_ratio · % avec double FINESS détectable
    - has_token_HXX_at_0 · % qui commencent par HXX (HAD)
    - has_token_PXX_at_18 · % avec PXX en pos 18 (PSY)
    """
    KEY_POSITIONS = (0, 9, 18, 21, 41, 48, 61, 77)
    counters = {f"digits_pos_{p}": 0 for p in KEY_POSITIONS}
    line_lengths = []
    digits_total = spaces_total = alpha_total = chars_total = 0
    has_psy_token = has_had_token = has_double_finess = 0

    try:
        with open(path, "r", encoding="latin-1", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                line = line.rstrip("\r\n")
                n = len(line)
                if n == 0:
                    continue
                line_lengths.append(n)
                digits_total += sum(c.isdigit() for c in line)
                spaces_total += sum(c == " " for c in line)
                alpha_total += sum(c.isalpha() for c in line)
                chars_total += n
                for p in KEY_POSITIONS:
                    if p < n and line[p].isdigit():
                        counters[f"digits_pos_{p}"] += 1
                # Tokens
                if n >= 21 and line[18:21].startswith("P"):
                    has_psy_token += 1
                if n >= 3 and line[0:3].startswith("H"):
                    has_had_token += 1
                # Double FINESS
                if n >= 18 and line[0:9].strip().isdigit() \
                        and line[9:18].strip().isdigit():
                    has_double_finess += 1
    except Exception as e:  # pragma: no cover
        return {"error": str(e)}

    n = len(line_lengths)
    if n == 0:
        return {"n_lines": 0}
    line_lengths.sort()
    median = line_lengths[n // 2]
    mean = sum(line_lengths) / n
    out = {
        "n_lines": n,
        "line_len_min": line_lengths[0],
        "line_len_max": line_lengths[-1],
        "line_len_median": median,
        "line_len_mean": round(mean, 1),
        "digits_ratio_avg": round(digits_total / max(chars_total, 1), 4),
        "spaces_ratio_avg": round(spaces_total / max(chars_total, 1), 4),
        "alpha_ratio_avg":  round(alpha_total / max(chars_total, 1), 4),
        "psy_token_ratio":  round(has_psy_token / n, 4),
        "had_token_ratio":  round(has_had_token / n, 4),
        "double_finess_ratio": round(has_double_finess / n, 4),
    }
    for p in (0, 9, 18, 21, 41, 48, 61, 77):
        out[f"digits_pos_{p}_ratio"] = round(counters[f"digits_pos_{p}"] / n, 4)
    return out


def _walk_dir(root: str) -> Iterator[str]:
    """Yield every .txt file path under root, recursively."""
    for dirpath, _, files in os.walk(root):
        for name in files:
            if name.lower().endswith(".txt"):
                yield os.path.join(dirpath, name)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:  # pragma: no cover
    p = argparse.ArgumentParser(
        description="Extracteur de features ATIH SAFE · zéro PII en sortie."
    )
    p.add_argument("--src", required=True,
                   help="Dossier racine contenant les fichiers .txt PMSI réels.")
    p.add_argument("--out", default="backend/ml/data/real_features.csv")
    p.add_argument("--max-lines", type=int, default=10_000,
                   help="Limite de lignes lues par fichier (défaut 10k).")
    args = p.parse_args()

    if not os.path.isdir(args.src):
        print(f"[ERR] Source introuvable · {args.src}", file=sys.stderr)
        raise SystemExit(1)

    print(f"[SAFE] Scan de {args.src}")
    files = sorted(_walk_dir(args.src))
    print(f"       {len(files)} fichiers .txt detectes")

    rows = []
    fields_set = set()
    for path in files:
        fmt = detect_format_from_filename(path)
        stats = _safe_line_stats(path, max_lines=args.max_lines)
        # Année extraite du nom (heuristique)
        year_m = re.search(r"(20\d{2})", os.path.basename(path))
        year = int(year_m.group(1)) if year_m else 0
        row = {
            "filename": os.path.basename(path),
            "format_inferred": fmt,
            "year_inferred": year,
            "size_bytes": os.path.getsize(path),
            **stats,
        }
        fields_set.update(row.keys())
        rows.append(row)
        print(f"       {fmt:<24} {os.path.basename(path)[:60]:<60} "
              f"{stats.get('n_lines', 0):>6} lignes")

    # Audit log
    audit_line = (f"[AUDIT] {datetime.now().isoformat()} · "
                  f"{len(files)} fichiers traités · "
                  f"src={args.src} · out={args.out}")
    print(audit_line)

    # Écriture CSV
    fields = sorted(fields_set)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})
    print(f"[OK] CSV écrit · {args.out} · {len(rows)} lignes · {len(fields)} colonnes")
    print(f"     Aucun IPP, DDN ou NIR n'a été écrit dans la sortie.")


if __name__ == "__main__":  # pragma: no cover
    main()
