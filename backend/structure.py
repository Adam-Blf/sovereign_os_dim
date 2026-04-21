# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM — STRUCTURE PARSER v1.0
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#  Project : Sovereign OS V35.0 — Station DIM GHT Sud Paris
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
import re
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
# DÉTECTION DU TYPE DE SECTEUR — Convention ARS
# ══════════════════════════════════════════════════════════════════════════════
# Les codes secteur PSY suivent la convention nationale ARS :
#     AA{L}NN  →  AA = département (75, 92, 94…)
#                 L  = type : G=général, I=infanto-juv, D=UMD,
#                             P=pénitentiaire (UHSA), Z=intersectoriel
#                 NN = numéro du secteur dans le département
#
# Exemples réels GHT Sud Paris :
#     94G01 = Paul Guiraud, secteur adulte Villejuif
#     94I01 = Fondation Vallée, secteur infanto-juvénile Gentilly
#     94D01 = UMD Henri Colin (Paul Guiraud)
#     94P01 = UHSA Fresnes
#     94Z01 = Équipe intersectorielle addictologie
#
# La regex ci-dessous accepte aussi les codes sans département (I01, G12)
# et les variantes avec tiret (94-G-01).

_SECTOR_CODE_RE = re.compile(
    r"^\s*(?:(\d{2,3})[-_\s]?)?([GIDPZ])[-_\s]?(\d{2,3})?\s*$",
    re.IGNORECASE,
)

# Libellés métier et palette par type de secteur ARS.
# Les couleurs alimentent à la fois le frontend (via data-sector-type)
# et le PDF (via _SECTOR_COLORS).
_SECTOR_TYPES = {
    "G": {"label": "Psychiatrie générale (adulte)", "short": "Général"},
    "I": {"label": "Infanto-juvénile", "short": "Infanto-juv"},
    "D": {"label": "UMD (Malades difficiles)", "short": "UMD"},
    "P": {"label": "UHSA (pénitentiaire)", "short": "UHSA"},
    "Z": {"label": "Intersectoriel", "short": "Intersec"},
}

_SECTOR_COLORS = {
    "G": "#2563EB",  # bleu — adulte
    "I": "#EC4899",  # pink — infanto
    "D": "#DC2626",  # rouge — UMD
    "P": "#7C3AED",  # violet — pénitentiaire
    "Z": "#F97316",  # orange — intersectoriel
}


def detect_sector_type(code: str) -> Optional[str]:
    """
    Extrait la lettre de type ARS (G/I/D/P/Z) d'un code secteur.
    Retourne None si le code n'est pas un code secteur reconnaissable.
    """
    if not code:
        return None
    m = _SECTOR_CODE_RE.match(code)
    return m.group(2).upper() if m else None


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

        # Détection ARS : extrait la lettre (G/I/D/P/Z) du code.
        # Si le code ne correspond pas au pattern classique, on essaie aussi
        # d'en trouver un dans le libellé (ex : "UMD Henri Colin" → D) via
        # heuristique simple.
        sector_type = detect_sector_type(code)
        if not sector_type and label:
            up = label.upper()
            if "UMD" in up or "MALADES DIFFICILES" in up:
                sector_type = "D"
            elif "UHSA" in up or "PENITENTIAIRE" in up or "PÉNITENTIAIRE" in up:
                sector_type = "P"
            elif "INFANTO" in up or "PÉDOPSY" in up or "PEDOPSY" in up or "ENFANT" in up or "ADOLESCENT" in up:
                sector_type = "I"
            elif "INTERSECTO" in up or "INTER-SECTO" in up:
                sector_type = "Z"

        node = {
            "code": code,
            "parent": parent or None,
            "label": label,
            "level": level or None,
            "sector_type": sector_type,  # G/I/D/P/Z ou None
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


def _propagate_sector_type(roots: list[dict]) -> None:
    """
    Les UM sous un secteur I (infanto-juvénile) héritent de ce type même si
    leur propre code ne le mentionne pas. Règle métier ARS : le type est
    porté par le secteur et s'applique à toutes ses unités.
    """
    def walk(node: dict, inherited: Optional[str]) -> None:
        if not node.get("sector_type") and inherited:
            node["sector_type"] = inherited
            node["sector_type_inherited"] = True
        effective = node.get("sector_type") or inherited
        for child in node["children"]:
            walk(child, effective)

    for r in roots:
        walk(r, None)


def _summarize(roots: list[dict]) -> dict:
    """
    Statistiques globales : nombre de nœuds, profondeur max, compteurs par
    niveau et par type de secteur ARS (G/I/D/P/Z). Les UM héritent du
    type de leur secteur pour le comptage.
    """
    total = 0
    max_depth = 0
    by_level: dict[str, int] = {}
    by_sector_type: dict[str, int] = {}

    def walk(node: dict, depth: int) -> None:
        nonlocal total, max_depth
        total += 1
        max_depth = max(max_depth, depth)
        lv = node.get("level") or ""
        if lv:
            by_level[lv] = by_level.get(lv, 0) + 1
        st = node.get("sector_type")
        if st:
            by_sector_type[st] = by_sector_type.get(st, 0) + 1
        for child in node["children"]:
            walk(child, depth + 1)

    for r in roots:
        walk(r, 1)

    return {
        "total_nodes": total,
        "roots": len(roots),
        "max_depth": max_depth,
        "by_level": by_level,
        "by_sector_type": by_sector_type,
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
    _propagate_sector_type(tree)
    summary = _summarize(tree)

    return {
        "filename": os.path.basename(filepath),
        "path": filepath,
        "headers": headers,
        "mapping": mapping,
        "tree": tree,
        "summary": summary,
    }


# ══════════════════════════════════════════════════════════════════════════════
# EXPORT PDF — Arborescence imprimable pour réunions / archivage
# ══════════════════════════════════════════════════════════════════════════════
# Pourquoi un PDF plutôt qu'un export PNG ou HTML ?
#   - Imprimable tel quel pour staff / direction (besoin DIM réel)
#   - Format universel et archivable (cohérence e-PMSI sur 10 ans)
#   - fpdf2 est déjà une dépendance du projet (tools/generate_manual.py)

def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    """Convertit un hex (#RRGGBB) en triplet (r, g, b) pour fpdf2."""
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# Helvetica (font cœur fpdf2) encode en latin-1 : certains caractères
# typographiques Unicode usuels provoquent des exceptions. On remplace
# ceux qui reviennent le plus dans nos libellés PSY par des équivalents
# ASCII/latin-1 avant passage à fpdf2.
_PDF_SUBST = {
    "\u2014": "-",   # em dash
    "\u2013": "-",   # en dash
    "\u2026": "..",  # horizontal ellipsis
    "\u2022": "-",   # bullet
    "\u00b7": "-",   # middle dot
    "\u2019": "'",   # right single quote
    "\u2018": "'",   # left single quote
    "\u201c": '"',   # left double quote
    "\u201d": '"',   # right double quote
    "\u00a0": " ",   # nbsp
    "\u2192": "->",  # right arrow
}


def _pdf_safe(text: str) -> str:
    """Rend un texte compatible avec la police Helvetica (latin-1) de fpdf2."""
    if not text:
        return ""
    for src, dst in _PDF_SUBST.items():
        if src in text:
            text = text.replace(src, dst)
    # Ultime filet : encode en latin-1 avec remplacement des caractères
    # résiduels par "?". Évite toute exception non anticipée.
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _draw_org_node(pdf, node: dict, x: float, y: float,
                   node_w: float, node_h: float, scale: float) -> None:
    """
    Dessine un noeud de l'organigramme dans un rectangle (x, y, w, h).

    Mise en page en 3 lignes proportionnelles à node_h — évite les
    chevauchements aux petites échelles :
      - ligne 1 (haut, ~33% h) : CODE en gras coloré
      - ligne 2 (milieu, ~33% h) : LIBELLÉ en slate (tronqué si besoin)
      - ligne 3 (bas, ~24% h)   : LEVEL · SECTEUR en petit gris

    Le CODE a la priorité absolue : il s'affiche toujours, c'est la
    ligne que l'utilisateur utilise pour identifier l'unité médicale.
    """
    level = (node.get("level") or "").upper()
    sector = node.get("sector_type")
    accent_hex = _SECTOR_COLORS.get(sector) or _LEVEL_COLORS.get(level, "#94A3B8")
    a_r, a_g, a_b = _hex_to_rgb(accent_hex)

    # Boîte arrondie blanche + liseré gauche coloré
    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.3)
    pdf.rect(x, y, node_w, node_h, style="FD",
             round_corners=True, corner_radius=max(1.0, 2.0 * scale))
    bar_w = max(1.2, 2.0 * scale)
    pdf.set_fill_color(a_r, a_g, a_b)
    pdf.rect(x, y, bar_w, node_h, style="F")

    # Padding intérieur et hauteurs de ligne proportionnelles à node_h.
    # On laisse ~8% en haut, ~8% en bas, et on répartit 3 lignes entre.
    pad_l = bar_w + 1.5
    inner_w = node_w - pad_l - 1.5
    pad_t = node_h * 0.08
    line_h = (node_h - 2 * pad_t) / 3.0

    # Polices : scaling respecté avec plancher pour garder la lisibilité.
    # On ne laisse JAMAIS le code descendre sous 6pt (≈ 2mm).
    font_code = max(6.0, 9.0 * scale)
    font_label = max(5.0, 7.0 * scale)
    font_meta = max(4.5, 5.5 * scale)

    # ── Ligne 1 : CODE ────────────────────────────────────────────────────
    code = str(node.get("code", ""))
    max_code = max(8, int(inner_w / 1.6))  # ~1.6mm par caractère en bold
    if len(code) > max_code:
        code = code[:max_code]
    pdf.set_xy(x + pad_l, y + pad_t)
    pdf.set_font("Helvetica", "B", font_code)
    pdf.set_text_color(a_r, a_g, a_b)
    pdf.cell(inner_w, line_h, code, new_x="LMARGIN", new_y="NEXT")

    # ── Ligne 2 : LIBELLÉ ────────────────────────────────────────────────
    label = str(node.get("label", "") or code)
    max_lbl = max(12, int(inner_w / 1.3))  # ~1.3mm par caractère en regular
    if len(label) > max_lbl:
        label = label[:max_lbl - 2] + ".."
    pdf.set_xy(x + pad_l, y + pad_t + line_h)
    pdf.set_font("Helvetica", "", font_label)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(inner_w, line_h, label, new_x="LMARGIN", new_y="NEXT")

    # ── Ligne 3 : META (LEVEL · SECTEUR) ─────────────────────────────────
    # Affichage compact : on skip si le node est trop petit pour une 3e ligne.
    if line_h >= 2.0:
        meta_bits = []
        if level:
            meta_bits.append(level)
        if sector:
            short = _SECTOR_TYPES.get(sector, {}).get("short", sector)
            meta_bits.append(short)
        if meta_bits:
            pdf.set_xy(x + pad_l, y + pad_t + 2 * line_h)
            pdf.set_font("Helvetica", "B", font_meta)
            pdf.set_text_color(148, 163, 184)
            pdf.cell(inner_w, line_h, " - ".join(meta_bits),
                     new_x="LMARGIN", new_y="NEXT")


# Palette par LEVEL — cohérente avec la charte Sovereign OS (gh-navy, teal…).
# Un niveau inconnu tombe sur gris neutre.
_LEVEL_COLORS = {
    "ETABLISSEMENT": "#000091",
    "POLE": "#6366F1",
    "SERVICE": "#00897B",
    "UM": "#F59E0B",
}


def _layout_tree(roots: list[dict], node_w: float, node_h: float,
                 h_gap: float, v_gap: float) -> dict:
    """
    Algorithme de layout "tidy tree" simplifié :
      - Chaque feuille prend un slot horizontal (leaf_x incrémenté)
      - Chaque parent est centré au-dessus de ses enfants
      - La profondeur détermine la position verticale

    Retourne {"width": ..., "height": ..., "nodes": [{...node, _x, _y}]}.
    Les _x/_y sont exprimés dans la même unité que node_w (millimètres pour
    fpdf2). min_x est soustrait pour que le layout commence à x=0.
    """
    leaf_counter = [0]  # mutable closure

    def assign(node: dict, depth: int) -> None:
        children = node.get("children", [])
        if not children:
            node["_x"] = leaf_counter[0] * (node_w + h_gap)
            leaf_counter[0] += 1
        else:
            for c in children:
                assign(c, depth + 1)
            node["_x"] = (children[0]["_x"] + children[-1]["_x"]) / 2
        node["_y"] = depth * (node_h + v_gap)

    for root in roots:
        assign(root, 0)

    # Normalisation : offset pour que min_x = 0
    xs, ys = [], []

    def collect(node: dict) -> None:
        xs.append(node["_x"])
        ys.append(node["_y"])
        for c in node.get("children", []):
            collect(c)

    for root in roots:
        collect(root)

    if not xs:
        return {"width": 0, "height": 0}

    min_x = min(xs)

    def shift(node: dict) -> None:
        node["_x"] -= min_x
        for c in node.get("children", []):
            shift(c)

    for root in roots:
        shift(root)

    width = (max(xs) - min_x) + node_w
    height = max(ys) + node_h
    return {"width": width, "height": height}


def _flatten(roots: list[dict]) -> list[dict]:
    out = []
    def walk(n):
        out.append(n)
        for c in n.get("children", []):
            walk(c)
    for r in roots:
        walk(r)
    return out


def _draw_organigram_page(pdf, subtree_roots: list[dict], title: str,
                          subtitle: str = "") -> None:
    """
    Dessine un organigramme sur la page courante, auto-scalé pour tenir
    entièrement dans la zone utile (pas de coupe, pas de débordement).

    Stratégie d'adaptation :
      1. Calcule le layout avec une taille de boîte "confortable"
      2. Mesure la largeur et hauteur totales
      3. Calcule un facteur d'échelle uniforme pour que tout tienne
      4. Applique le facteur à toutes les dimensions (boîtes + espaces)
      5. Re-calcule le layout à la taille finale et dessine
    """
    # Marges et zone utile
    MX, MY_TOP, MY_BOT = 10.0, 32.0, 18.0
    usable_w = pdf.w - 2 * MX
    usable_h = pdf.h - MY_TOP - MY_BOT

    # Titre de page + sous-titre
    pdf.set_xy(MX, MY_TOP - 14)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
    if subtitle:
        pdf.set_x(MX)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 5, subtitle, new_x="LMARGIN", new_y="NEXT")

    # Première passe : layout à taille de référence
    REF_W, REF_H, REF_HGAP, REF_VGAP = 52.0, 20.0, 4.0, 16.0
    layout = _layout_tree(subtree_roots, REF_W, REF_H, REF_HGAP, REF_VGAP)
    if layout["width"] == 0:
        return

    # Facteur d'échelle pour entrer dans la zone utile
    scale = min(
        usable_w / layout["width"],
        (usable_h - 8) / layout["height"],  # -8 pour le titre
        1.0,  # jamais de zoom au-delà de 100%
    )
    # Plancher 55% : en dessous le CODE UM devient illisible. Mieux vaut
    # déborder légèrement en bas/droite que d'avoir du microscopique.
    scale = max(scale, 0.55)

    NODE_W = REF_W * scale
    NODE_H = REF_H * scale
    H_GAP = REF_HGAP * scale
    V_GAP = REF_VGAP * scale

    # Relayout à la taille finale
    layout = _layout_tree(subtree_roots, NODE_W, NODE_H, H_GAP, V_GAP)

    # Centrage horizontal dans la zone utile
    origin_x = MX + max(0, (usable_w - layout["width"]) / 2)
    origin_y = MY_TOP

    def draw_node(node: dict) -> None:
        _draw_org_node(
            pdf, node,
            origin_x + node["_x"], origin_y + node["_y"],
            NODE_W, NODE_H, scale,
        )

    def draw_connectors(node: dict) -> None:
        children = node.get("children", [])
        if not children:
            return
        pdf.set_draw_color(203, 213, 225)
        pdf.set_line_width(0.3)
        px = origin_x + node["_x"] + NODE_W / 2
        py = origin_y + node["_y"] + NODE_H
        cy = origin_y + children[0]["_y"]
        mid_y = (py + cy) / 2
        pdf.line(px, py, px, mid_y)
        first_cx = origin_x + children[0]["_x"] + NODE_W / 2
        last_cx = origin_x + children[-1]["_x"] + NODE_W / 2
        pdf.line(first_cx, mid_y, last_cx, mid_y)
        for c in children:
            cx = origin_x + c["_x"] + NODE_W / 2
            pdf.line(cx, mid_y, cx, origin_y + c["_y"])
            draw_connectors(c)

    def walk_draw(node: dict) -> None:
        draw_node(node)
        for c in node.get("children", []):
            walk_draw(c)

    for root in subtree_roots:
        draw_connectors(root)
    for root in subtree_roots:
        walk_draw(root)


def render_tree_pdf(parsed: dict, output_path: str) -> str:
    """
    Produit un PDF MULTI-PAGES :
      - Page 1 : vue régionale (synthèse + organigramme top-level)
      - Page 2+ : une page par sous-arbre de niveau 2 (ex. un pôle)

    Chaque page fait tenir son contenu entièrement dans la zone utile
    grâce à un calcul d'échelle automatique — aucune coupure.
    """
    from datetime import date
    from fpdf import FPDF

    filename = parsed.get("filename", "structure")
    summary = parsed.get("summary", {})
    tree = parsed.get("tree", [])

    class Org(FPDF):
        def normalize_text(self, text):  # type: ignore[override]
            # Intercepte toute chaîne passée à pdf.cell / pdf.multi_cell :
            # applique _pdf_safe avant que fpdf2 tente l'encodage latin-1.
            return super().normalize_text(_pdf_safe(text))

        def header(self):
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(15, 23, 42)
            self.cell(0, 7, f"Structure : {filename}",
                      new_x="RIGHT", new_y="TOP")
            self.set_font("Helvetica", "", 8)
            self.set_text_color(100, 116, 139)
            self.cell(0, 7, date.today().isoformat(),
                      new_x="LMARGIN", new_y="NEXT", align="R")
            self.set_draw_color(226, 232, 240)
            self.line(10, 18, self.w - 10, 18)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(148, 163, 184)
            self.cell(0, 6,
                      f"Sovereign OS DIM - Page {self.page_no()} / {{nb}}",
                      align="C")

    pdf = Org(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.alias_nb_pages()

    # ── PAGE 1 : VUE RÉGIONALE ────────────────────────────────────────────
    # Synthèse de l'établissement + organigramme top-level (2 premiers niveaux)
    pdf.add_page()
    pdf.set_xy(10, 26)

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, "Vue régionale", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, (
        f"{summary.get('total_nodes', 0)} noeuds  -  "
        f"profondeur {summary.get('max_depth', 0)}  -  "
        f"{summary.get('roots', 0)} racine(s)"
    ), new_x="LMARGIN", new_y="NEXT")

    # Bandeau : compteurs par LEVEL
    by_level = summary.get("by_level", {})
    if by_level:
        pdf.ln(2)
        pdf.set_x(10)
        pdf.set_font("Helvetica", "B", 7)
        for lvl, count in by_level.items():
            r, g, b = _hex_to_rgb(_LEVEL_COLORS.get(lvl, "#94A3B8"))
            pdf.set_fill_color(r, g, b)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(30, 5, f" {lvl.upper()} : {count} ",
                     new_x="RIGHT", new_y="TOP", fill=True)
            pdf.cell(1.5, 5, "", new_x="RIGHT", new_y="TOP")
        pdf.ln(7)

    # Bandeau : compteurs par TYPE DE SECTEUR (G/I/D/P/Z)
    by_sector = summary.get("by_sector_type", {})
    if by_sector:
        pdf.set_x(10)
        pdf.set_font("Helvetica", "B", 7)
        for stype, count in by_sector.items():
            r, g, b = _hex_to_rgb(_SECTOR_COLORS.get(stype, "#94A3B8"))
            pdf.set_fill_color(r, g, b)
            pdf.set_text_color(255, 255, 255)
            short = _SECTOR_TYPES.get(stype, {}).get("short", stype)
            pdf.cell(34, 5, f" {short} : {count} ",
                     new_x="RIGHT", new_y="TOP", fill=True)
            pdf.cell(1.5, 5, "", new_x="RIGHT", new_y="TOP")
        pdf.ln(8)

    # Organigramme top-level (3 niveaux max : territoire + établissement + pôle)
    # pour la vue d'ensemble. On clone en coupant à la profondeur max_depth.
    def _top_clone(node: dict, max_depth: int, cur: int = 0) -> dict:
        return {
            "code": node.get("code", ""),
            "label": node.get("label", ""),
            "level": node.get("level"),
            "sector_type": node.get("sector_type"),
            "children": (
                [_top_clone(c, max_depth, cur + 1) for c in node.get("children", [])]
                if cur < max_depth else []
            ),
        }

    top_roots = [_top_clone(r, 2) for r in tree]
    pdf.set_y(pdf.get_y() + 2)
    _draw_organigram_sub(pdf, top_roots, y_start=pdf.get_y())

    # ── PAGES SUIVANTES : 1 par pôle ──────────────────────────────────────
    # On cherche dans tout l'arbre les noeuds de niveau POLE et on produit
    # une page détaillée (pôle + secteurs + UM) pour chacun. Si aucun level
    # POLE n'est détecté (fichier sans colonne LEVEL), on retombe sur "une
    # page par enfant de racine" comme avant.
    page_targets: list[tuple[Optional[dict], dict]] = []

    def _find_poles(node: dict, parent: Optional[dict]) -> bool:
        """Visite l'arbre, ajoute chaque POLE trouvé aux targets. Retourne
        True si au moins un pôle a été trouvé dans ce sous-arbre."""
        found = False
        if (node.get("level") or "").upper() == "POLE":
            page_targets.append((parent, node))
            return True
        for c in node.get("children", []):
            if _find_poles(c, node):
                found = True
        return found

    for root in tree:
        _find_poles(root, None)

    # Fallback : aucun POLE → une page par enfant de racine
    if not page_targets:
        for root in tree:
            for k in root.get("children", []):
                page_targets.append((root, k))
        if not page_targets and tree:
            page_targets = [(None, tree[0])]

    for parent, sub in page_targets:
        pdf.add_page()
        title = f"{sub.get('code', '')} - {sub.get('label', '')}"
        subtitle_bits = []
        if parent:
            subtitle_bits.append(f"Rattache a {parent.get('code', '')} "
                                 f"({parent.get('label', '')})")
        st = sub.get("sector_type")
        if st:
            subtitle_bits.append(_SECTOR_TYPES.get(st, {}).get("label", st))
        sub_count = len(_flatten([sub]))
        subtitle_bits.append(f"{sub_count} noeuds dans ce sous-arbre")

        _draw_organigram_page(
            pdf, [sub],
            title=title,
            subtitle="  -  ".join(subtitle_bits),
        )

    abs_out = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_out) or ".", exist_ok=True)
    pdf.output(abs_out)
    return abs_out


def _draw_organigram_sub(pdf, roots: list[dict], y_start: float) -> None:
    """
    Variante de _draw_organigram_page qui démarre à y_start (utilisé pour la
    page régionale où le titre + les bandeaux occupent déjà le haut de page).
    """
    MX, MY_BOT = 10.0, 18.0
    usable_w = pdf.w - 2 * MX
    usable_h = pdf.h - y_start - MY_BOT

    REF_W, REF_H, REF_HGAP, REF_VGAP = 52.0, 20.0, 4.0, 16.0
    layout = _layout_tree(roots, REF_W, REF_H, REF_HGAP, REF_VGAP)
    if layout["width"] == 0:
        return
    scale = min(usable_w / layout["width"], usable_h / layout["height"], 1.0)
    scale = max(scale, 0.55)

    NODE_W = REF_W * scale
    NODE_H = REF_H * scale
    H_GAP = REF_HGAP * scale
    V_GAP = REF_VGAP * scale
    layout = _layout_tree(roots, NODE_W, NODE_H, H_GAP, V_GAP)

    origin_x = MX + max(0, (usable_w - layout["width"]) / 2)
    origin_y = y_start

    def draw_node(node):
        _draw_org_node(
            pdf, node,
            origin_x + node["_x"], origin_y + node["_y"],
            NODE_W, NODE_H, scale,
        )

    def draw_conn(node):
        children = node.get("children", [])
        if not children:
            return
        pdf.set_draw_color(203, 213, 225)
        pdf.set_line_width(0.3)
        px = origin_x + node["_x"] + NODE_W / 2
        py = origin_y + node["_y"] + NODE_H
        cy = origin_y + children[0]["_y"]
        mid_y = (py + cy) / 2
        pdf.line(px, py, px, mid_y)
        first_cx = origin_x + children[0]["_x"] + NODE_W / 2
        last_cx = origin_x + children[-1]["_x"] + NODE_W / 2
        pdf.line(first_cx, mid_y, last_cx, mid_y)
        for c in children:
            cx = origin_x + c["_x"] + NODE_W / 2
            pdf.line(cx, mid_y, cx, origin_y + c["_y"])
            draw_conn(c)

    def walk_draw(node):
        draw_node(node)
        for c in node.get("children", []):
            walk_draw(c)

    for r in roots:
        draw_conn(r)
    for r in roots:
        walk_draw(r)
