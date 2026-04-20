# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM — STRUCTURE PARSER v1.0
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#  Project : Sovereign OS V32.0 — Station DIM GHT Sud Paris
#
#  Description :
#    Parseur du "fichier de structure" d'un établissement : hiérarchie des
#    pôles, services, unités médicales (UM). Produit un arbre JSON prêt à
#    être affiché par le frontend (onglet Structure).
#
#    Formats supportés :
#      - CSV/TSV avec colonnes LEVEL;CODE;PARENT;LABEL  (format étendu)
#      - CSV/TSV à colonnes libres : on devine parent/code/label via heading
#      - Fichier plat indenté (2 ou 4 espaces = 1 niveau) — fallback simple
#
#    Pourquoi un parseur dédié plutôt que réutiliser DataProcessor ?
#      DataProcessor est positionnel (largeur fixe ATIH). Les fichiers de
#      structure sont délimités (; , tab) et souvent saisis à la main : il
#      faut tolérer le désordre des colonnes et les libellés unicode.
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations

import csv
import os
from typing import Optional


# Jeux de synonymes pour identifier les colonnes sans connaître le nom exact.
# L'ordre dans la liste n'a pas d'importance : on normalise via .lower().strip().
_CODE_COLS = {"code", "id", "identifiant", "um", "code_um", "code_service"}
_PARENT_COLS = {"parent", "parent_code", "code_parent", "rattache_a", "rattachement"}
_LABEL_COLS = {"label", "libelle", "libellé", "nom", "name", "designation"}
_LEVEL_COLS = {"level", "niveau", "type"}

# Si aucune colonne n'est identifiable, on suppose ce gabarit positionnel
# (inspiré du format TIC usuel des établissements publics).
_FALLBACK_ORDER = ("level", "code", "parent", "label")

# Séparateurs à essayer lorsque csv.Sniffer échoue.
_DELIMS = (";", ",", "\t", "|")


def _detect_delimiter(sample: str) -> str:
    """Devine le séparateur le plus probable en comptant les occurrences."""
    try:
        return csv.Sniffer().sniff(sample, delimiters="".join(_DELIMS)).delimiter
    except csv.Error:
        # Fallback : on prend le séparateur le plus présent sur la 1re ligne
        first = sample.splitlines()[0] if sample else ""
        scores = [(d, first.count(d)) for d in _DELIMS]
        scores.sort(key=lambda x: -x[1])
        return scores[0][0] if scores[0][1] > 0 else ";"


def _normalize_header(headers: list[str]) -> dict[str, int]:
    """
    Mappe les noms de colonnes vers les rôles métier {code, parent, label,
    level}. Si rien ne matche, on retombe sur l'ordre positionnel.
    """
    mapping: dict[str, int] = {}
    for i, h in enumerate(headers):
        key = (h or "").strip().lower().lstrip("\ufeff")
        if key in _CODE_COLS and "code" not in mapping:
            mapping["code"] = i
        elif key in _PARENT_COLS and "parent" not in mapping:
            mapping["parent"] = i
        elif key in _LABEL_COLS and "label" not in mapping:
            mapping["label"] = i
        elif key in _LEVEL_COLS and "level" not in mapping:
            mapping["level"] = i

    # Complétion positionnelle si on a raté le header (ex : fichier sans
    # ligne d'en-tête). On garde les rôles déjà résolus par nom.
    for idx, role in enumerate(_FALLBACK_ORDER):
        if role not in mapping and idx < len(headers):
            mapping.setdefault(role, idx)

    return mapping


def _first_row_is_header(first: list[str]) -> bool:
    """
    Heuristique : si au moins un des tokens ressemble à un nom de colonne
    métier connu, c'est un en-tête. Évite de consommer la 1re ligne de
    données comme header quand le fichier n'en a pas.
    """
    tokens = {(c or "").strip().lower() for c in first}
    known = _CODE_COLS | _PARENT_COLS | _LABEL_COLS | _LEVEL_COLS
    return bool(tokens & known)


def _read_rows(filepath: str) -> tuple[list[str], list[list[str]]]:
    """
    Lit le fichier, détecte le séparateur, renvoie (headers, rows).
    Si la 1re ligne n'est pas un en-tête, headers vaut [] et toutes les
    lignes sont dans rows.
    """
    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        sample = f.read(4096)
        f.seek(0)
        delim = _detect_delimiter(sample)
        reader = list(csv.reader(f, delimiter=delim))

    if not reader:
        return [], []

    if _first_row_is_header(reader[0]):
        return reader[0], reader[1:]
    return [], reader


def _build_tree(rows: list[list[str]], mapping: dict[str, int]) -> list[dict]:
    """
    Construit l'arbre à partir de la liste plate (parent_code -> enfants).
    Retourne la liste des racines (nœuds sans parent ou parent inconnu).
    """
    nodes: dict[str, dict] = {}
    order: list[str] = []  # préserve l'ordre d'apparition dans le fichier

    ci = mapping.get("code")
    pi = mapping.get("parent")
    li = mapping.get("label")
    lvi = mapping.get("level")

    for row in rows:
        if not row or all(not (c or "").strip() for c in row):
            continue  # ligne vide

        def cell(idx: Optional[int]) -> str:
            if idx is None or idx >= len(row):
                return ""
            return (row[idx] or "").strip()

        code = cell(ci)
        if not code:
            continue  # ligne sans code → ignorée (cas courant : séparateur)

        parent = cell(pi)
        label = cell(li) or code
        level = cell(lvi)

        node = {
            "code": code,
            "parent": parent or None,
            "label": label,
            "level": level or None,
            "children": [],
        }
        # Si le même code apparaît deux fois, on garde la 1re occurrence
        # mais on enrichit son label si vide (cas des fichiers bruités).
        if code in nodes:
            if not nodes[code]["label"] and label:
                nodes[code]["label"] = label
            continue
        nodes[code] = node
        order.append(code)

    roots: list[dict] = []
    for code in order:
        node = nodes[code]
        p = node["parent"]
        if p and p in nodes and p != code:
            nodes[p]["children"].append(node)
        else:
            # parent inconnu → c'est une racine (pôle, tête de hiérarchie)
            roots.append(node)
    return roots


def _summarize(roots: list[dict]) -> dict:
    """
    Statistiques globales : nombre de nœuds, profondeur max, compteur par
    niveau (si la colonne level existe), largeur par racine. Utile pour
    dimensionner l'affichage frontend (pagination, virtualisation).
    """
    total = 0
    max_depth = 0
    by_level: dict[str, int] = {}

    def walk(node: dict, depth: int) -> None:
        nonlocal total, max_depth
        total += 1
        max_depth = max(max_depth, depth)
        lv = node.get("level") or ""
        if lv:
            by_level[lv] = by_level.get(lv, 0) + 1
        for child in node["children"]:
            walk(child, depth + 1)

    for r in roots:
        walk(r, 1)

    return {
        "total_nodes": total,
        "roots": len(roots),
        "max_depth": max_depth,
        "by_level": by_level,
    }


def parse_structure(filepath: str) -> dict:
    """
    API publique : parse un fichier de structure et retourne un dict
    sérialisable JSON :

        {
          "filename": str,
          "path": str,
          "headers": [...],
          "mapping": {code: i, parent: j, label: k, level: l},
          "tree": [ {code, label, parent, level, children: [...]}, ... ],
          "summary": {total_nodes, roots, max_depth, by_level}
        }

    En cas d'erreur : {"error": "message"}.
    """
    if not filepath or not os.path.isfile(filepath):
        return {"error": f"Fichier introuvable : {filepath}"}

    try:
        headers, rows = _read_rows(filepath)
    except OSError as e:
        return {"error": f"Lecture impossible : {e}"}

    # Pas de header → on fabrique un mapping positionnel basé sur le
    # gabarit LEVEL;CODE;PARENT;LABEL (le plus courant pour les TIC).
    mapping = _normalize_header(headers) if headers else _normalize_header(
        list(_FALLBACK_ORDER)
    )

    tree = _build_tree(rows, mapping)
    summary = _summarize(tree)

    return {
        "filename": os.path.basename(filepath),
        "path": filepath,
        "headers": headers,
        "mapping": mapping,
        "tree": tree,
        "summary": summary,
    }
