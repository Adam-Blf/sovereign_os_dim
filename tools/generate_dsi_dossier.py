#!/usr/bin/env python
"""Génère le dossier de conformité DSI en PDF à partir du Markdown source.

Source   : docs/documentation_securite_dsi.md
Sortie   : docs/Dossier_Conformite_DSI.pdf
Rendu    : fpdf2 (police Unicode Montserrat embarquée dans tools/fonts).

Les blocs de diagrammes Mermaid sont remplacés par une légende textuelle : un
PDF ne rend pas le Mermaid, et le schéma reste consultable dans le Markdown source.

Usage :
    python tools/generate_dsi_dossier.py
"""

from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "documentation_securite_dsi.md"
OUT = ROOT / "docs" / "Dossier_Conformite_DSI.pdf"
FONTS = ROOT / "tools" / "fonts"

# Palette GHT Psy Sud Paris (charte sobre institutionnelle).
NAVY = (37, 62, 128)  # #253e80
BLUE = (12, 125, 182)  # #0c7db6
INK = (28, 32, 40)
MUTED = (90, 96, 110)
RULE = (210, 214, 222)
QUOTE_BG = (238, 242, 249)


class Dossier(FPDF):
    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_font("Montserrat", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 8, "Sovereign OS DIM - Dossier de conformité DSI", align="L")
        self.cell(0, 8, "GHT Psy Sud Paris", align="R")
        self.ln(10)

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Montserrat", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


def _register_fonts(pdf: FPDF) -> None:
    pdf.add_font("Montserrat", "", str(FONTS / "Montserrat-Regular.ttf"))
    pdf.add_font("Montserrat", "B", str(FONTS / "Montserrat-Bold.ttf"))
    pdf.add_font("Montserrat", "I", str(FONTS / "Montserrat-Italic.ttf"))


def _write_inline(pdf: FPDF, text: str, size: int = 10, color=INK) -> None:
    """Rend un paragraphe avec gestion du gras **...** via multi_cell segmenté."""
    pdf.set_text_color(*color)
    parts = re.split(r"(\*\*.+?\*\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            pdf.set_font("Montserrat", "B", size)
            pdf.write(5.6, part[2:-2])
        else:
            pdf.set_font("Montserrat", "", size)
            pdf.write(5.6, part)
    pdf.ln(6.4)


def _table(pdf: FPDF, rows: list[list[str]]) -> None:
    if not rows:
        return
    header, *body = rows
    ncol = len(header)
    usable = pdf.w - pdf.l_margin - pdf.r_margin
    # Largeurs : première colonne un peu plus large.
    widths = [usable * 0.32] + [(usable * 0.68) / (ncol - 1)] * (ncol - 1) if ncol > 1 else [usable]
    line_h = 6.2

    def row(cells: list[str], head: bool) -> None:
        pdf.set_font("Montserrat", "B" if head else "", 9)
        heights = []
        for i, c in enumerate(cells):
            lines = pdf.multi_cell(widths[i], line_h, c, dry_run=True, output="LINES")
            heights.append(len(lines) * line_h)
        h = max(heights) if heights else line_h
        if pdf.get_y() + h > pdf.page_break_trigger:
            pdf.add_page()
        x0, y0 = pdf.get_x(), pdf.get_y()
        if head:
            pdf.set_fill_color(*NAVY)
            pdf.set_text_color(255, 255, 255)
        else:
            pdf.set_fill_color(248, 249, 251)
            pdf.set_text_color(*INK)
        for i, c in enumerate(cells):
            x = pdf.get_x()
            pdf.multi_cell(widths[i], h, "", border=0, fill=True, new_x="RIGHT", new_y="TOP")
            pdf.set_xy(x + 1.5, y0 + 1)
            pdf.multi_cell(widths[i] - 3, line_h, c, border=0, new_x="RIGHT", new_y="TOP")
            pdf.set_xy(x + widths[i], y0)
        pdf.set_xy(x0, y0 + h)
        pdf.set_draw_color(*RULE)
        pdf.line(x0, y0 + h, x0 + sum(widths), y0 + h)

    row(header, True)
    for b in body:
        row(b + [""] * (ncol - len(b)), False)
    pdf.ln(3)


def _cover(pdf: FPDF, title: str, subtitle: str, meta: list[str]) -> None:
    pdf.add_page()
    pdf.ln(30)
    pdf.set_draw_color(*BLUE)
    pdf.set_line_width(1.2)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 40, pdf.get_y())
    pdf.ln(8)
    pdf.set_font("Montserrat", "B", 26)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(0, 11, title)
    pdf.ln(2)
    pdf.set_font("Montserrat", "", 13)
    pdf.set_text_color(*BLUE)
    pdf.multi_cell(0, 7, subtitle)
    pdf.ln(14)
    for m in meta:
        _write_inline(pdf, m, size=11, color=INK)
    pdf.ln(6)
    pdf.set_font("Montserrat", "I", 9)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(
        0,
        5,
        "Document de travail. Les noms de modules et le design sont provisoires "
        "et pourront évoluer selon les demandes de la Direction des Ressources "
        "Numériques du GHT Psy Sud Paris. Aucune donnée nominative de tiers.",
    )


def build() -> None:
    md = SRC.read_text(encoding="utf-8").splitlines()
    pdf = Dossier(format="A4")
    pdf.set_margins(20, 16, 20)
    pdf.set_auto_page_break(True, margin=18)
    _register_fonts(pdf)

    # Cover depuis les premières lignes du Markdown.
    title = "Dossier de Présentation Fonctionnelle et Technique"
    subtitle = "Conformité SI et sécurité informatique - Station PMSI"
    meta: list[str] = []
    i = 0
    while i < len(md):
        line = md[i]
        if line.startswith("**") and " :**" in line:
            meta.append(line.strip())
            i += 1
        elif line.startswith("# ") or line.startswith("### ") or line.strip() == "---" or not line.strip():
            i += 1
            if meta:
                break
        else:
            i += 1
    _cover(pdf, title, subtitle, meta)

    pdf.add_page()
    table_buf: list[list[str]] = []
    in_code = False
    code_lang = ""

    def flush_table() -> None:
        nonlocal table_buf
        if table_buf:
            _table(pdf, table_buf)
            table_buf = []

    for line in md[i:]:
        raw = line.rstrip("\n")
        stripped = raw.strip()

        if stripped.startswith("```"):
            if not in_code:
                in_code = True
                code_lang = stripped[3:].strip()
            else:
                in_code = False
                if code_lang.lower() == "mermaid":
                    pdf.set_font("Montserrat", "I", 9)
                    pdf.set_text_color(*MUTED)
                    pdf.multi_cell(0, 5, "[ Schéma d'architecture - voir le Markdown source ]")
                    pdf.ln(2)
                code_lang = ""
            continue
        if in_code:
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(set(c) <= {"-", ":", " "} for c in cells):
                continue  # ligne de séparation Markdown
            table_buf.append(cells)
            continue
        else:
            flush_table()

        if not stripped or stripped == "---":
            if stripped == "---":
                pdf.ln(1)
                pdf.set_draw_color(*RULE)
                pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
                pdf.ln(3)
            else:
                pdf.ln(2)
            continue

        if stripped.startswith("## "):
            pdf.ln(3)
            pdf.set_font("Montserrat", "B", 15)
            pdf.set_text_color(*NAVY)
            pdf.multi_cell(0, 8, stripped[3:])
            pdf.set_draw_color(*BLUE)
            pdf.set_line_width(0.5)
            pdf.line(pdf.l_margin, pdf.get_y() + 0.5, pdf.l_margin + 22, pdf.get_y() + 0.5)
            pdf.ln(3)
        elif stripped.startswith("### "):
            pdf.ln(1.5)
            pdf.set_font("Montserrat", "B", 11.5)
            pdf.set_text_color(*BLUE)
            pdf.multi_cell(0, 6.5, stripped[4:])
            pdf.ln(1)
        elif stripped.startswith("> "):
            x0 = pdf.get_x()
            pdf.set_fill_color(*QUOTE_BG)
            pdf.set_draw_color(*BLUE)
            y0 = pdf.get_y()
            pdf.set_font("Montserrat", "I", 9.5)
            pdf.set_text_color(*INK)
            txt = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped[2:])
            pdf.multi_cell(0, 5.4, txt, fill=True)
            pdf.set_draw_color(*BLUE)
            pdf.set_line_width(1.0)
            pdf.line(x0, y0, x0, pdf.get_y())
            pdf.ln(2)
        elif stripped.startswith(("* ", "- ")):
            body = stripped[2:]
            pdf.set_x(pdf.l_margin + 3)
            pdf.set_font("Montserrat", "B", 10)
            pdf.set_text_color(*BLUE)
            pdf.write(5.6, "-  ")
            _write_inline(pdf, body, size=10, color=INK)
        else:
            _write_inline(pdf, stripped, size=10, color=INK)

    flush_table()
    OUT.write_bytes(bytes(pdf.output()))
    print(f"[OK] PDF genere -> {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    build()
