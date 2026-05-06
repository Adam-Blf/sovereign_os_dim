# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM · Capture de screenshots Playwright
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#  Project : Sovereign OS V35.0
#
#  Description ·
#    Lance Chromium headless via Playwright, ouvre le frontend local,
#    mocke les API /api/* pour peupler l'UI, navigue chaque vue et capture
#    les screenshots dans `docs/screenshots/`.
#
#    Le guide PDF (generate_guide.py) embarque ces PNG pour les sections
#    "Vue d'ensemble de l'interface" de chaque feature.
#
#  Usage ·
#    python tools/capture_screenshots.py
#
#  Dependances · playwright + chromium (cf. README ·
#    pip install playwright && python -m playwright install chromium).
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).parent.resolve()
ROOT = HERE.parent
FRONTEND = ROOT / "frontend"
OUT_DIR = ROOT / "docs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# MOCK API · reponses pour chaque endpoint que le frontend appelle
# ══════════════════════════════════════════════════════════════════════════════
MOCK_RESPONSES = {
    "/api/folders": {"folders": [
        "D:/DIM/ATIH/2024/T3/juillet",
        "D:/DIM/ATIH/2024/T3/aout",
        "D:/DIM/ATIH/2024/T3/septembre",
    ]},
    "/api/scan": {"files": [
        {"name": "RPS_202407.txt", "format": "RPS", "lines": 4782, "size": 742000},
        {"name": "RAA_202407.txt", "format": "RAA", "lines": 12450, "size": 1195000},
        {"name": "FICHSUP-PSY_202407.txt", "format": "FICHSUP-PSY", "lines": 218, "size": 26000},
        {"name": "RPS_202408.txt", "format": "RPS", "lines": 3984, "size": 618000},
        {"name": "RAA_202408.txt", "format": "RAA", "lines": 11238, "size": 1079000},
        {"name": "RPS_202409.txt", "format": "RPS", "lines": 5021, "size": 779000},
        {"name": "RAA_202409.txt", "format": "RAA", "lines": 13109, "size": 1258000},
    ]},
    "/api/stats": {
        "files": 7, "ipp_unique": 4821, "collisions": 147, "formats": 3,
        "by_format": {"RPS": 13787, "RAA": 36797, "FICHSUP-PSY": 218},
    },
    "/api/collisions": {"collisions": [
        {"ipp": "IPP_042A7", "ddn_count": 2, "sources": 3,
         "variants": [{"ddn": "19870415", "count": 12}, {"ddn": "19870514", "count": 2}]},
        {"ipp": "IPP_019B2", "ddn_count": 3, "sources": 4,
         "variants": [{"ddn": "20020301", "count": 8}, {"ddn": "20020103", "count": 2},
                      {"ddn": "20023001", "count": 1}]},
        {"ipp": "IPP_073C5", "ddn_count": 2, "sources": 2,
         "variants": [{"ddn": "19951122", "count": 15}, {"ddn": "19951222", "count": 1}]},
    ]},
    "/api/matrix": {"formats": 23, "years": "2007-2024"},
    "/api/dashboard": {
        "patients_by_month": {"2024-01": 1204, "2024-02": 1387, "2024-03": 1512,
                              "2024-04": 1489, "2024-05": 1603, "2024-06": 1521,
                              "2024-07": 1205, "2024-08": 950, "2024-09": 1472},
        "by_sector": {"I": 3412, "G": 0, "D": 0, "P": 0, "Z": 1409},
        "top_um": [{"code": "4001", "label": "HDJ Enfants", "count": 1842},
                   {"code": "4002", "label": "HC Adolescents", "count": 1523}],
    },
    "/api/structure": {
        "filename": "structure_fondation_vallee_2024.csv",
        "summary": {"total_nodes": 42, "roots": 1, "max_depth": 4,
                    "by_level": {"POLE": 2, "SECTEUR": 4, "UM": 36}},
        "tree": [{
            "code": "FV", "label": "Fondation Vallee", "level": "ETAB",
            "sector_type": None, "parent": None, "children": [
                {"code": "POLE_I", "label": "Pole Infanto-juvenile", "level": "POLE",
                 "sector_type": "I", "parent": "FV", "children": [
                    {"code": "94I01", "label": "Secteur 94I01 Gentilly", "level": "SECTEUR",
                     "sector_type": "I", "parent": "POLE_I", "children": [
                        {"code": "4001", "label": "HDJ Enfants", "level": "UM",
                         "sector_type": "I", "children": []},
                        {"code": "4002", "label": "HC Adolescents", "level": "UM",
                         "sector_type": "I", "children": []},
                        {"code": "4003", "label": "CATTP", "level": "UM",
                         "sector_type": "I", "children": []},
                     ]},
                    {"code": "94I02", "label": "Secteur 94I02 Kremlin-Bicetre", "level": "SECTEUR",
                     "sector_type": "I", "parent": "POLE_I", "children": [
                        {"code": "4010", "label": "CMP Enfants", "level": "UM",
                         "sector_type": "I", "children": []},
                        {"code": "4011", "label": "Consultation Famille", "level": "UM",
                         "sector_type": "I", "children": []},
                     ]},
                 ]},
                {"code": "POLE_Z", "label": "Pole Intersectoriel", "level": "POLE",
                 "sector_type": "Z", "parent": "FV", "children": [
                    {"code": "4050", "label": "Addictologie ado", "level": "UM",
                     "sector_type": "Z", "children": []},
                 ]},
            ]}
        ],
    },
    "/health": {"status": "ok", "version": "35.0"},
    "/api/logs": [],
}


SCREENSHOTS = [
    # ── Vues classiques ─────────────────────────────────────────────────────
    {"name": "01_dashboard",       "title": "Dashboard · vue d'ensemble",            "nav": "nav-dashboard"},
    {"name": "02_modo_files",      "title": "Sélection des fichiers · selection des fichiers ATIH","nav": "nav-modo"},
    {"name": "03_idv",             "title": "Identitovigilance · collisions IPP / DDN","nav": "nav-idv"},
    {"name": "04_pilot_csv",       "title": "PMSI Pilot CSV · exports normalises",   "nav": "nav-pilot"},
    {"name": "05_csv_import",      "title": "Import CSV externe",                    "nav": "nav-csv"},
    {"name": "06_structure",       "title": "Structure · arborescence polaire",      "nav": "nav-structure"},
    # ── Vues Sentinel V36 ─────────────────────────────────────────────────
    {"name": "08_cockpit",         "title": "Cockpit chef DIM · tableau executif",   "nav": "nav-cockpit"},
    {"name": "09_health",          "title": "Health monitor · supervision technique","nav": "nav-health"},
    {"name": "10_ars",             "title": "Sentinel ARS · predicteur de rejet",    "nav": "nav-ars"},
    {"name": "11_cespa",           "title": "CeSPA / CATTG · conformite reforme 2025","nav": "nav-cespa"},
    {"name": "12_diff",            "title": "Diff lots mensuels · anti-regression",  "nav": "nav-diff"},
    {"name": "13_cim",             "title": "CimSuggester · LLM Ollama local",       "nav": "nav-cim"},
    {"name": "14_lstm",            "title": "Predicteur DMS · LSTM par groupe CIM-10","nav": "nav-lstm"},
    {"name": "15_cluster",         "title": "Clustering UMAP · 6 archetypes patients","nav": "nav-cluster"},
    {"name": "16_twin",            "title": "Hospital Twin · simulation DFA",        "nav": "nav-twin"},
    {"name": "17_heatmap",         "title": "Heatmap geographique · sectorisation",  "nav": "nav-heatmap"},
    {"name": "18_pivot",           "title": "Tableaux croises ad hoc",                "nav": "nav-pivot"},
    {"name": "19_rgpd",            "title": "RGPD command center · DPO panel",       "nav": "nav-rgpd"},
    {"name": "20_audit",           "title": "Audit chain · tracabilite SHA-256",     "nav": "nav-audit"},
    {"name": "21_workflow",        "title": "Workflows DIM · TIM > MIM > ARS",       "nav": "nav-workflow"},
    {
        "name": "07_structure_activity",
        "title": "Analyse d'activite par UM",
        "nav": "nav-structure",
        "post_action": "loadStructure",
    },
    {
        "name": "08_tuto",
        "title": "Tutoriel integre",
        "nav": "nav-tuto",
    },
]


def run():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright non installe · pip install playwright", file=sys.stderr)
        sys.exit(1)

    index_url = (FRONTEND / "index.html").as_uri()
    print(f"Lancement · {index_url}")
    print(f"Sortie · {OUT_DIR}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000},
                                      device_scale_factor=1.5)
        page = context.new_page()

        # Mock toutes les /api/* et /health · catch-all sur les autres fetch
        def handle_route(route):
            req_url = route.request.url
            # Ignore les ressources statiques (CSS / JS / images / Tailwind CDN)
            if any(req_url.endswith(ext) for ext in (".css", ".js", ".png", ".jpg",
                    ".svg", ".woff", ".woff2", ".ttf", ".ico")):
                route.continue_()
                return
            # Match un endpoint connu · sinon renvoie {"ok": true}
            for prefix in ("/api/", "/health"):
                if prefix in req_url:
                    path = req_url.split(prefix, 1)[1]
                    full = (prefix + path).split("?", 1)[0].rstrip("/")
                    if not full.startswith("/"):
                        full = "/" + full
                    body = MOCK_RESPONSES.get(full, {"ok": True})
                    route.fulfill(status=200, content_type="application/json",
                                  body=json.dumps(body))
                    return
            route.continue_()

        context.route("**/api/**", handle_route)
        context.route("**/health", handle_route)

        page.goto(index_url, wait_until="domcontentloaded")
        # Attendre que le frontend ait boot (Lucide icons + Sentinel views)
        page.wait_for_timeout(2500)
        # Skip le boot screen si présent · cliquer sur le bouton ignite
        page.evaluate("""
            () => {
                const btn = document.getElementById('btn-ignite');
                if (btn && btn.offsetParent !== null) btn.click();
                const overlay = document.getElementById('boot-overlay');
                if (overlay) overlay.style.display = 'none';
                const root = document.getElementById('app-root');
                if (root) {
                    root.classList.remove('hidden');
                    root.style.opacity = '1';
                }
            }
        """)
        page.wait_for_timeout(500)

        # Force le theme clair pour des captures lisibles en impression
        page.evaluate("document.documentElement.classList.remove('dark')")

        captures = []
        for shot in SCREENSHOTS:
            nav_id = shot["nav"]
            print(f"  - {shot['name']} · nav={nav_id}")

            # Click sur le bouton de nav si trouve · sinon appel direct de navigateTo
            clicked = page.evaluate(f"""
                () => {{
                    const btn = document.getElementById('{nav_id}');
                    if (btn) {{ btn.click(); return true; }}
                    return false;
                }}
            """)
            if not clicked:
                # Fallback via hash navigation si expose
                page.evaluate(f"""
                    () => {{
                        if (typeof navigateTo === 'function') {{
                            navigateTo('{nav_id.replace('nav-', '')}');
                        }}
                    }}
                """)

            # Laisser le rendu se stabiliser
            page.wait_for_timeout(900)

            # Action post-nav · skip silencieusement si fetch interdit en file://
            if shot.get("post_action") == "loadStructure":
                try:
                    page.evaluate("""
                        () => {
                            const btn = document.getElementById('btn-structure-select');
                            if (btn) btn.click();
                        }
                    """)
                    page.wait_for_timeout(1000)
                except Exception:
                    pass

            png_path = OUT_DIR / f"{shot['name']}.png"
            page.screenshot(path=str(png_path), full_page=False)
            captures.append((shot["name"], shot["title"], str(png_path)))
            print(f"    -> {png_path.name}")

        browser.close()

    # Ecrit un manifeste pour que generate_guide.py l'exploite
    manifest = OUT_DIR / "manifest.json"
    manifest.write_text(json.dumps(
        [{"name": n, "title": t, "path": p} for n, t, p in captures],
        indent=2, ensure_ascii=False,
    ), encoding="utf-8")
    print(f"Manifest · {manifest}")
    print(f"[OK] {len(captures)} screenshots captures dans {OUT_DIR}")


if __name__ == "__main__":
    run()
