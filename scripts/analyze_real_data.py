"""
Analyse live d'un lot ATIH reel via le DataProcessor backend.

Usage · `python scripts/analyze_real_data.py [--batch PATH] [--structure PATH]`

- Scan lot ATIH (par defaut `D:/Adam/archives/essai_06`)
- Process MPI, collisions, cross-modalites
- Parse CSV structure OSPI (par defaut `D:/Adam/adam___pour_ficom_structure_A_JOUR_2026_03_31`)
- Output timings par etape et taille MPI

Skippe proprement quand un chemin n'existe pas (ex · cle USB debranchee).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.data_processor import DataProcessor
from backend.structure import parse_structure


DEFAULT_BATCH = Path("D:/Adam/archives/essai_06")
DEFAULT_STRUCTURE = Path("D:/Adam/adam___pour_ficom_structure_A_JOUR_2026_03_31")


def section(title: str) -> None:
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def step(label: str, fn):
    """Chronometre une etape · retourne (resultat, duree_sec)."""
    t0 = time.perf_counter()
    result = fn()
    dt = time.perf_counter() - t0
    print(f"  [{dt * 1000:>7.1f} ms] {label}")
    return result, dt


def analyze_batch(batch: Path) -> None:
    section(f"Scan lot ATIH · {batch}")
    if not batch.exists():
        print(f"  [SKIP] chemin introuvable · {batch}")
        return
    dp = DataProcessor()

    files, _ = step("scan_directory", lambda: dp.scan_directory(str(batch)))
    print(f"  {len(files)} fichiers detectes")
    if not files:
        print("  (aucun fichier ATIH reconnu · stop)")
        return

    by_format: dict[str, int] = {}
    for f in files:
        by_format[f.get("format", "?")] = by_format.get(f.get("format", "?"), 0) + 1
    for fmt, n in sorted(by_format.items(), key=lambda x: -x[1])[:12]:
        print(f"    {fmt:<16} · {n} fichier(s)")

    valid = [f for f in files if f.get("format") != "INCONNU"]
    if not valid:
        print("\n  Aucun fichier identifie · rien a processer")
        return

    section(f"Process {len(valid)} fichiers")
    result, _ = step("process_files", lambda: dp.process_files(valid))
    for k, v in result.items():
        print(f"  {k:<20} · {v}")

    section("Collisions identitovigilance")
    coll, _ = step("get_collisions", lambda: dp.get_collisions())
    print(f"  Total · {len(coll)}")
    for c in coll[:5]:
        variants = c.get("variants", [])
        print(f"    IPP {c.get('ipp','?')[:20]:<20} · {len(variants)} DDN · {c.get('sources_count','?')} sources")

    section("Cross-modalites 3+ formats")
    cm, _ = step("get_cross_modality_patients", lambda: dp.get_cross_modality_patients(min_formats=3))
    print(f"  {len(cm)} patients")

    section("Stats MPI")
    stats, _ = step("get_mpi_stats", lambda: dp.get_mpi_stats())
    print(f"  IPP uniques · {stats.get('ipp_unique', 0)}")
    print(f"  Lignes totales · {stats.get('lines_total', 0)}")


def analyze_structure(folder: Path) -> None:
    section(f"Structure OSPI · {folder}")
    if not folder.exists():
        print(f"  [SKIP] chemin introuvable · {folder}")
        return
    csvs = sorted(folder.glob("*.csv"))
    print(f"  {len(csvs)} fichiers CSV detectes")
    for csv_path in csvs:
        try:
            result = parse_structure(str(csv_path))
            summary = result.get("summary", {})
            nodes = summary.get("total_nodes", 0)
            roots = summary.get("roots", 0)
            depth = summary.get("max_depth", 0)
            by_level = summary.get("by_level", {})
            print(f"    [OK ] {csv_path.name[:55]:<55} · {nodes} noeuds · {roots} racines · depth {depth}")
            if by_level:
                levels_str = " ".join(f"{k}={v}" for k, v in sorted(by_level.items()))
                print(f"           niveaux · {levels_str}")
        except Exception as exc:
            msg = str(exc)[:100]
            print(f"    [ERR] {csv_path.name[:55]:<55} · {msg}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path, default=DEFAULT_BATCH,
                        help="Dossier du lot ATIH (defaut · D:/Adam/archives/essai_06)")
    parser.add_argument("--structure", type=Path, default=DEFAULT_STRUCTURE,
                        help="Dossier CSV structure OSPI")
    parser.add_argument("--skip-batch", action="store_true", help="Skip scan ATIH")
    parser.add_argument("--skip-structure", action="store_true", help="Skip parse structure")
    args = parser.parse_args()

    t0 = time.perf_counter()

    if not args.skip_batch:
        analyze_batch(args.batch)
    if not args.skip_structure:
        analyze_structure(args.structure)

    total = time.perf_counter() - t0
    section("FIN")
    print(f"  Duree totale · {total * 1000:.1f} ms")


if __name__ == "__main__":
    main()
