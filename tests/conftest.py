# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM — Test Configuration (conftest.py)
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#  Purpose : Fixtures partagées pour toute la suite de tests
# ══════════════════════════════════════════════════════════════════════════════

import os
import sys
import pytest
import tempfile
import shutil

# Ajout du dossier racine du projet au PYTHONPATH pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.data_processor import DataProcessor, ATIH_MATRIX


# ──────────────────────────────────────────────────────────────────────────────
# FIXTURES — Données de test réutilisables
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def processor():
    """Crée un DataProcessor vierge pour chaque test."""
    return DataProcessor()


@pytest.fixture
def temp_dir():
    """Crée un dossier temporaire pour les tests, supprimé après usage."""
    d = tempfile.mkdtemp(prefix="sovereign_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sample_rps_file(temp_dir):
    """
    Génère un fichier RPS de test au format standard (154 chars/ligne).

    Contenu : 3 patients distincts avec des IPP/DDN cohérents.
    L'IPP est en position [21:41], la DDN en [41:49].
    """
    spec = ATIH_MATRIX["RPS"]
    length = spec["length"]  # 154

    # Helper pour construire une ligne RPS valide
    def make_rps_line(ipp, ddn, filler="A"):
        """
        Construit une ligne RPS de longueur fixe (154 chars).
        Positions : [0:21] = FINESS+séquence, [21:41] = IPP, [41:49] = DDN
        Le reste est rempli avec le caractère filler.
        """
        line = filler * 21  # Positions 0-20 (FINESS + séquence)
        line += ipp.ljust(20)  # Positions 21-40 (IPP paddé à 20 chars)
        line += ddn.ljust(8)   # Positions 41-48 (DDN paddé à 8 chars)
        line += filler * (length - len(line))  # Remplissage restant
        return line[:length]  # Tronquer à la longueur exacte

    lines = [
        make_rps_line("12345", "19850315"),       # Patient 1
        make_rps_line("67890", "19920720"),        # Patient 2
        make_rps_line("12345", "19850315"),        # Patient 1 (doublon)
        make_rps_line("11111", "20010101"),         # Patient 3
    ]

    filepath = os.path.join(temp_dir, "rps_2024.txt")
    with open(filepath, "w", encoding="latin-1") as f:
        f.write("\n".join(lines) + "\n")
    return filepath


@pytest.fixture
def sample_raa_file(temp_dir):
    """
    Génère un fichier RAA de test au format standard (96 chars/ligne).
    """
    spec = ATIH_MATRIX["RAA"]
    length = spec["length"]  # 96

    def make_raa_line(ipp, ddn, filler="B"):
        line = filler * 21
        line += ipp.ljust(20)
        line += ddn.ljust(8)
        line += filler * (length - len(line))
        return line[:length]

    lines = [
        make_raa_line("12345", "19850315"),
        make_raa_line("99999", "19780430"),
    ]

    filepath = os.path.join(temp_dir, "raa_2024.txt")
    with open(filepath, "w", encoding="latin-1") as f:
        f.write("\n".join(lines) + "\n")
    return filepath


@pytest.fixture
def sample_rps_2021_variant(temp_dir):
    """
    Génère un fichier RPS 2021 avec l'ancien format (142 chars/ligne).
    Simule le problème Fondation Vallée : même patient, format différent.
    """
    length = 142  # Format P04 ancien

    def make_rps_old_line(ipp, ddn, filler="C"):
        line = filler * 21
        line += ipp.ljust(20)
        line += ddn.ljust(8)
        line += filler * (length - len(line))
        return line[:length]

    lines = [
        make_rps_old_line("00000000000000012345", "19850315"),  # IPP paddé zéros
        make_rps_old_line("00000000000000067890", "19920720"),
        make_rps_old_line("12345", "19850315"),  # IPP normal (même patient!)
    ]

    filepath = os.path.join(temp_dir, "rps_2021_fondation.txt")
    with open(filepath, "w", encoding="latin-1") as f:
        f.write("\n".join(lines) + "\n")
    return filepath


@pytest.fixture
def sample_raa_2021_variant(temp_dir):
    """
    Génère un fichier RAA 2021 avec l'ancien format (86 chars/ligne).
    """
    length = 86

    def make_raa_old_line(ipp, ddn, filler="D"):
        line = filler * 21
        line += ipp.ljust(20)
        line += ddn.ljust(8)
        line += filler * (length - len(line))
        return line[:length]

    lines = [
        make_raa_old_line("00000000000000012345", "19850315"),
        make_raa_old_line("99999", "19780430"),
    ]

    filepath = os.path.join(temp_dir, "raa_2021.txt")
    with open(filepath, "w", encoding="latin-1") as f:
        f.write("\n".join(lines) + "\n")
    return filepath


@pytest.fixture
def collision_files(temp_dir):
    """
    Génère des fichiers qui créent une collision MPI :
    même IPP (12345) avec deux DDN différentes dans deux fichiers RPS.
    """
    spec = ATIH_MATRIX["RPS"]
    length = spec["length"]

    def make_line(ipp, ddn, filler="E"):
        line = filler * 21
        line += ipp.ljust(20)
        line += ddn.ljust(8)
        line += filler * (length - len(line))
        return line[:length]

    # Fichier 1 : patient 12345 avec DDN 19850315
    f1 = os.path.join(temp_dir, "rps_collision_a.txt")
    with open(f1, "w", encoding="latin-1") as f:
        f.write(make_line("12345", "19850315") + "\n")
        f.write(make_line("12345", "19850315") + "\n")  # Doublon même DDN
        f.write(make_line("12345", "19850315") + "\n")  # 3 occurrences

    # Fichier 2 : même IPP 12345 avec DDN DIFFÉRENTE 19850316 (erreur)
    f2 = os.path.join(temp_dir, "rps_collision_b.txt")
    with open(f2, "w", encoding="latin-1") as f:
        f.write(make_line("12345", "19850316") + "\n")  # DDN erronée

    return [f1, f2]


@pytest.fixture
def sample_rss_file(temp_dir):
    """
    Génère un fichier RSS MCO de test au format standard (177 chars/ligne).
    IPP en position [12:32], DDN en [62:70].
    """
    spec = ATIH_MATRIX["RSS"]
    length = spec["length"]  # 177

    def make_rss_line(ipp, ddn, filler="F"):
        line = filler * 12            # Positions 0-11
        line += ipp.ljust(20)          # Positions 12-31 (IPP)
        line += filler * (62 - len(line))  # Remplissage jusqu'à position 62
        line += ddn.ljust(8)           # Positions 62-69 (DDN)
        line += filler * (length - len(line))  # Remplissage final
        return line[:length]

    lines = [
        make_rss_line("MCO001", "19900101"),
        make_rss_line("MCO002", "19881215"),
        make_rss_line("MCO001", "19900101"),  # Doublon
    ]

    filepath = os.path.join(temp_dir, "rss_2024.txt")
    with open(filepath, "w", encoding="latin-1") as f:
        f.write("\n".join(lines) + "\n")
    return filepath
