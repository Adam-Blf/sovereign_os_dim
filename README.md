![version](https://img.shields.io/badge/version-V36.0-DC0A2D?style=flat-square) ![python](https://img.shields.io/badge/python-3.12-141418?style=flat-square) ![.net](https://img.shields.io/badge/.net-8-141418?style=flat-square) ![dim-psy](https://img.shields.io/badge/dim--psy-production-4CAF50?style=flat-square)

# Sovereign OS DIM · Station PMSI

[![CI](https://github.com/Adam-Blf/sovereign_os_dim/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/Adam-Blf/sovereign_os_dim/actions/workflows/test.yml)
![Status](https://img.shields.io/badge/status-production-brightgreen)
![Version](https://img.shields.io/badge/version-V35.0-blue)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![C#](https://img.shields.io/badge/C%23-.NET_8-239120?logo=c-sharp&logoColor=white)
![WebView2](https://img.shields.io/badge/WebView2-Chromium-3C4A5A?logo=microsoftedge&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-06B6D4?logo=tailwindcss&logoColor=white)
![Tests](https://img.shields.io/badge/tests-233_Py_%2B_30_JS-brightgreen)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-blue)

Application desktop pour la station DIM du **GHT Sud Paris** (Fondation Vallée
+ Paul Guiraud). Traite les fichiers ATIH PMSI, résout les collisions
d'identito-vigilance, produit les exports e-PMSI. **100 % local, RGPD-safe,
aucune donnée patient n'est transmise.**

## Fonctionnalités

- **23 formats ATIH** · PSY (RPS, RAA, RPSA, R3A, EDGAR, FICHSUP-PSY…), MCO (RSS, RSFA, RSFB, RSFC), SSR/SMR (RHS, SSRHA, RAPSS), HAD (RPSS, RAPSS-HAD), transversal (VID-HOSP, ANO-HOSP).
- **Master Patient Index** · croisement IPP/DDN, persistance SQLite, reprise batch interrompu.
- **Identitovigilance** · détection collisions, résolution automatique par fréquence majoritaire ou manuelle.
- **Preflight DRUIDES** · 15 validateurs avant upload e-PMSI · FINESS, IPP, DDN, CIM-10, mode légal, secteur ARS, chaînage, duplicatas, orphelins.
- **CimSuggester IA** · suggestion de code CIM-10 quand le DP est absent · fournisseur LLM configurable (API cloud ou Ollama local).
- **Structure polaire** · arborescence Pôle/Secteur/UM avec organigramme vectoriel + export PDF multi-pages.
- **Analyse d'activité par UM** *(V35)* · drop-zone HTML5 accessible clavier, parsing RPS/RAA asynchrone en chunks 5000 lignes, détection des UM dormantes, export CSV UTF-8 BOM, badges rouges clignotants sur l'arbre.
- **Dashboard Live** · 4 graphiques Chart.js + 6 KPI dérivés du MPI, export PDF paysage.
- **Inspector Terminal** · décomposition ligne par ligne avec 15 validations, pseudonymisation auto.
- **Bridge HTTP REST** · endpoints sécurisés 127.0.0.1 + token Bearer pour intégration PHP.
- **Export PDF** · organigrammes, rapports preflight, dashboards BIQuery (HTML→PDF).
- **Guide utilisateur** · `Sovereign_OS_DIM_Guide.pdf` (34 pages, schémas vectoriels, logo Paul Guiraud).

## Formats ATIH supportés

| Champ | Formats | Depuis |
|-------|---------|--------|
| **PSY** | RPS, RAA, RPSA, R3A, FICHSUP-PSY, EDGAR, FICUM-PSY, RSF-ACE-PSY | 2007 |
| **MCO** | RSS/RUM, RSFA, RSFB, RSFC | 1991 |
| **SSR/SMR** | RHS, SSRHA, RAPSS, FICHCOMP-SMR | 2003 |
| **HAD** | RPSS, RAPSS-HAD, FICHCOMP-HAD, SSRHA-HAD | 2005 |
| **Transversal** | VID-HOSP, ANO-HOSP, FICHCOMP | 2009 |

## Installation

### Version portable (recommandée)

Double-cliquez sur `SovereignOS.Desktop.exe`. Aucune installation, aucun droit administrateur requis.

### Version code source

```bash
git clone https://github.com/Adam-Blf/sovereign_os_dim.git
cd sovereign_os_dim
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
python main.py
```

### Build d'un exe portable

```bash
python build.py
```

## Tests

```bash
# Python · 233 tests unitaires + intégration
python -m pytest tests/ -q

# Frontend · 30 tests Node.js (helpers JS sans navigateur)
node tests/frontend/test_activity_analysis.mjs
```

Couverture · identification des 23 formats ATIH, validation ligne par ligne,
normalisation IPP (cohérence BIQuery 2022-2025), auto-détection des variantes
2021, collisions MPI et résolution, exports CSV et .txt, parser de structure
client-side, détection des UM sans activité.

## Développement

Commandes courantes pour contribuer au projet ·

```bash
# Lint (config dans pyproject.toml · rules E/W/F)
ruff check backend/ tests/ tools/ scripts/

# Auto-fix (imports unused, trailing whitespace, etc.)
ruff check backend/ tests/ tools/ scripts/ --fix

# Format check
ruff format backend/ tests/ tools/ scripts/ --check

# Security scan
python -m bandit -r backend/ -ll

# CVE audit sur les dépendances
pip-audit -r requirements.txt

# Smoke test backend sur un vrai lot ATIH (nécessite D:/Adam/ monté)
python scripts/analyze_real_data.py

# Rebuild .exe C# (nécessite .NET 8 SDK, source dans dev/hospitalier/SovereignOS.DIM.CSharp)
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true
```

Toutes ces commandes tournent aussi dans la CI GitHub Actions à chaque push
sur `main` et PR. Config partagée · `pyproject.toml` pour ruff/pytest,
`.github/workflows/test.yml` pour les 4 jobs parallèles (python, frontend,
deps, lint).

## Raccourcis clavier

| Touche | Action |
|--------|--------|
| Ctrl+1 | Dashboard |
| Ctrl+2 | Modo Files |
| Ctrl+3 | Identitovigilance |
| Ctrl+4 | PMSI Pilot CSV |
| Ctrl+5 | Import CSV |
| Ctrl+6 | Structure · arborescence + analyse activité UM |
| Ctrl+7 | Tutoriel |
| F1 | Manuel HTML |
| F2 | Inspector Terminal |
| F3 | Preflight DRUIDES |
| F4 | Dashboard Live |

## Architecture

```
sovereign_os_dim/
├── main.py                 · Point d'entrée pywebview (desktop)
├── bridge.py               · Point d'entrée bridge HTTP (PHP)
├── backend/
│   ├── api.py              · API exposée au frontend
│   ├── bridge.py           · Serveur Flask REST
│   ├── data_processor.py   · Moteur ATIH (scan, MPI, export)
│   └── structure.py        · Parser CSV/TSV + organigramme PDF
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js          · Logique principale + structure parser JS
│       ├── bridge-shim.js  · Adapter C#/pywebview
│       ├── preflight-view.js
│       ├── dashboard-live.js
│       ├── htmlpdf-view.js
│       └── tuto-overlay.js
├── tools/
│   ├── generate_manual.py  · PDF manuel utilisateur
│   ├── generate_guide.py   · PDF guide complet 34 pages
│   └── capture_screenshots.py · Playwright headless
├── tests/
│   ├── test_data_processor.py  · 233 tests Python
│   └── frontend/
│       └── test_activity_analysis.mjs · 30 tests JS
├── Sovereign_OS_DIM_Guide.pdf  · Guide utilisateur 34 pages
└── README.md
```

## Stack technique

| Couche | Techno |
|--------|--------|
| Desktop | Python 3.12 + pywebview, ou C# .NET 8 + WebView2 |
| Frontend | HTML + Tailwind CDN + Chart.js + anime.js + Lucide |
| Bridge HTTP | Flask (Python) ou ASP.NET Core (C#) |
| Persistance | SQLite (`Microsoft.Data.Sqlite` pour le port C#) |
| PDF | fpdf2 (latin-1, fallback pour postes hospitaliers) |
| Parser ATIH | Regex positionnel largeur fixe, lecture latin-1 |
| Tests | pytest (Python), Node.js native (JS) |
| Build | PyInstaller (`python build.py`) ou `dotnet publish` |

## Sécurité et RGPD

- **100 % local** · aucun envoi externe, aucune télémétrie.
- **Bridge HTTP** · binding uniquement 127.0.0.1, token Bearer obligatoire, CORS restrictif.
- **Anonymisation** · k-anonymity (k≥5) pour les exports recherche.
- **Audit log art. 30 RGPD** · chaque traitement horodaté.
- **Pseudonymisation IPP** · optionnelle pour rapports non-nominatifs.
- **Bandit** · 0 issue sur 2457 lignes backend.

## Version distribuée

Le bundle C# prêt à livrer vit dans `D:\SovereignOS_DIM_CSharp\` ·
`SovereignOS.Desktop.exe` (97 Mo), `frontend/` (patchs sécurité inclus),
`Sovereign_OS_DIM_Guide.pdf` (34 pages), `LISEZ-MOI.txt`, `LICENCE.txt`,
`VERSION`, `CHECKSUMS.sha256`. Total 140 Mo.

## Support

- **Issues** · https://github.com/Adam-Blf/sovereign_os_dim/issues
- **Email** · adam.beloucif@psysudparis.fr (alternance Fondation Vallée)
- **Portfolio** · https://adam.beloucif.com

## Licence

MIT pour le code source. LGPL pour fpdf2 (embarqué). Les formats PMSI sont
propriété de l'[ATIH](https://www.atih.sante.fr).

---

<p align="center">
  <sub>Par <a href="https://adam.beloucif.com">Adam Beloucif</a> · Data Engineer & Fullstack Developer · alternant TIM <a href="https://www.psysudparis.fr">Fondation Vallée</a> GHT Sud Paris · <a href="https://github.com/Adam-Blf">GitHub</a> · <a href="https://www.linkedin.com/in/adambeloucif/">LinkedIn</a></sub>
</p>
