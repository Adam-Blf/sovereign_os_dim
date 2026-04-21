# Tests du parseur de fichier de structure (backend/structure.py).
# On couvre : CSV avec header, CSV sans header, séparateurs variés,
# cycles parent↔enfant, lignes vides, colonnes manquantes, fichier absent.

import csv
import os
from pathlib import Path

import pytest

from backend.structure import parse_structure


def _write(tmp_path: Path, name: str, rows: list[list[str]], sep: str = ";") -> str:
    """Utilitaire : écrit un CSV temporaire et renvoie son chemin."""
    p = tmp_path / name
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=sep)
        for r in rows:
            w.writerow(r)
    return str(p)


def test_missing_file_returns_error():
    out = parse_structure("/chemin/inexistant.csv")
    assert "error" in out


def test_basic_hierarchy_with_header(tmp_path: Path):
    path = _write(tmp_path, "struct.csv", [
        ["LEVEL", "CODE", "PARENT", "LABEL"],
        ["POLE", "P1", "", "Pole Psychiatrie"],
        ["SERVICE", "S1", "P1", "Service Adulte"],
        ["UM", "U1", "S1", "Hospit complete"],
        ["UM", "U2", "S1", "Hopital de jour"],
    ])
    out = parse_structure(path)

    assert "error" not in out
    assert out["summary"]["total_nodes"] == 4
    assert out["summary"]["roots"] == 1
    assert out["summary"]["max_depth"] == 3
    assert out["summary"]["by_level"] == {"POLE": 1, "SERVICE": 1, "UM": 2}

    pole = out["tree"][0]
    assert pole["code"] == "P1"
    assert len(pole["children"]) == 1
    service = pole["children"][0]
    assert service["code"] == "S1"
    assert [c["code"] for c in service["children"]] == ["U1", "U2"]


def test_comma_delimited(tmp_path: Path):
    path = _write(tmp_path, "s.csv", [
        ["code", "parent", "libelle"],
        ["A", "", "Racine"],
        ["B", "A", "Enfant"],
    ], sep=",")
    out = parse_structure(path)
    assert out["tree"][0]["code"] == "A"
    assert out["tree"][0]["children"][0]["code"] == "B"


def test_tab_delimited(tmp_path: Path):
    path = _write(tmp_path, "s.tsv", [
        ["code", "parent", "label"],
        ["X", "", "Head"],
        ["Y", "X", "Leaf"],
    ], sep="\t")
    out = parse_structure(path)
    assert out["summary"]["total_nodes"] == 2
    assert out["tree"][0]["children"][0]["code"] == "Y"


def test_no_header_positional_fallback(tmp_path: Path):
    # Pas de ligne d'en-tête : LEVEL;CODE;PARENT;LABEL implicite.
    path = _write(tmp_path, "no_header.csv", [
        ["POLE", "P1", "", "Pole"],
        ["UM", "U1", "P1", "Unite"],
    ])
    out = parse_structure(path)
    assert out["headers"] == []  # détecté comme sans header
    assert out["summary"]["total_nodes"] == 2
    assert out["tree"][0]["code"] == "P1"


def test_empty_lines_ignored(tmp_path: Path):
    path = _write(tmp_path, "s.csv", [
        ["code", "parent", "label"],
        ["A", "", "Root"],
        ["", "", ""],
        ["B", "A", "Child"],
        ["  ", "  ", "  "],
    ])
    out = parse_structure(path)
    assert out["summary"]["total_nodes"] == 2


def test_unknown_parent_becomes_root(tmp_path: Path):
    # Un nœud dont le parent n'existe pas dans le fichier = racine orpheline.
    path = _write(tmp_path, "s.csv", [
        ["code", "parent", "label"],
        ["A", "", "Root"],
        ["Z", "INCONNU", "Orphelin"],
    ])
    out = parse_structure(path)
    roots = {n["code"] for n in out["tree"]}
    assert roots == {"A", "Z"}


def test_self_parent_kept_as_root(tmp_path: Path):
    # Cas pathologique : code == parent → on le garde en racine (pas de boucle).
    path = _write(tmp_path, "s.csv", [
        ["code", "parent", "label"],
        ["A", "A", "Auto"],
    ])
    out = parse_structure(path)
    assert len(out["tree"]) == 1
    assert out["tree"][0]["children"] == []


def test_duplicate_code_keeps_first(tmp_path: Path):
    path = _write(tmp_path, "s.csv", [
        ["code", "parent", "label"],
        ["A", "", "First"],
        ["A", "", "Second"],  # doublon ignoré
    ])
    out = parse_structure(path)
    assert out["summary"]["total_nodes"] == 1
    assert out["tree"][0]["label"] == "First"


def test_sector_detection_ars_codes():
    """Convention ARS : G=général, I=infanto, D=UMD, P=UHSA, Z=intersec."""
    from backend.structure import detect_sector_type
    cases = {
        "94G01": "G", "94I01": "I", "94D01": "D",
        "94P01": "P", "94Z01": "Z",
        "92G12": "G", "75I03": "I",
        "I01": "I", "D01": "D",
        "G07": "G",
        "PG-P1": None, "UM-HC-01": None,
        "": None,
    }
    for code, expected in cases.items():
        assert detect_sector_type(code) == expected, f"fail on {code}"


def test_sector_type_inherited_by_children(tmp_path: Path):
    # Les UM sous un secteur I doivent hériter du type infanto-juvénile.
    path = _write(tmp_path, "s.csv", [
        ["level", "code", "parent", "label"],
        ["POLE", "FV-P1", "", "Pôle pédopsy"],
        ["SECTEUR", "94I01", "FV-P1", "Secteur 94I01"],
        ["UM", "94I01-HC", "94I01", "Hospitalisation complete"],
        ["UM", "94I01-CMP", "94I01", "Consultations"],
    ])
    out = parse_structure(path)
    sector = out["tree"][0]["children"][0]
    assert sector["sector_type"] == "I"
    for um in sector["children"]:
        assert um["sector_type"] == "I"
        assert um.get("sector_type_inherited") is True


def test_sector_type_via_label_keyword(tmp_path: Path):
    # Si le code ne matche pas le pattern ARS, on tente via mots-clés du libellé.
    path = _write(tmp_path, "s.csv", [
        ["level", "code", "parent", "label"],
        ["POLE", "X1", "", "Pôle UMD Henri Colin"],
        ["POLE", "X2", "", "Pôle UHSA Fresnes (pénitentiaire)"],
        ["POLE", "X3", "", "Pôle adolescents (infanto-juvénile)"],
    ])
    out = parse_structure(path)
    types = [n["sector_type"] for n in out["tree"]]
    assert types == ["D", "P", "I"]


def test_summary_counts_by_sector_type(tmp_path: Path):
    path = _write(tmp_path, "s.csv", [
        ["level", "code", "parent", "label"],
        ["SECTEUR", "94G01", "", "Adulte 1"],
        ["SECTEUR", "94G02", "", "Adulte 2"],
        ["SECTEUR", "94I01", "", "Infanto 1"],
        ["UM", "94I01-CMP", "94I01", "CMP enfants"],
    ])
    out = parse_structure(path)
    types = out["summary"]["by_sector_type"]
    assert types == {"G": 2, "I": 2}


def test_bom_in_header_is_stripped(tmp_path: Path):
    # Certains fichiers Excel exportent un BOM UTF-8 sur la 1re cellule.
    # On s'assure que "\ufeffcode" est bien reconnu comme colonne code.
    p = tmp_path / "bom.csv"
    p.write_text(
        "\ufeffcode;parent;label\nA;;Racine\nB;A;Enfant\n",
        encoding="utf-8",
    )
    out = parse_structure(str(p))
    assert out["summary"]["total_nodes"] == 2
    assert out["tree"][0]["children"][0]["code"] == "B"
