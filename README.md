# 🛡️ Sovereign OS DIM — Station PMSI

![Status](https://img.shields.io/badge/status-production-green)
![Python](https://img.shields.io/badge/python-3.12+-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Tests](https://img.shields.io/badge/tests-178%20passed%20%2B%2021%20JS-brightgreen)

## Description

**Sovereign OS** est une application desktop native conçue pour la station DIM du **GHT Sud Paris**. Elle permet de traiter, réconcilier et exporter les données PMSI (Programme de Médicalisation des Systèmes d'Information) conformément aux normes ATIH.

### Fonctionnalités principales

- ✅ **Scan multi-dossiers** — Détection automatique des fichiers `.txt` et `.csv` PMSI
- ✅ **23 formats ATIH** — Couverture complète des 4 champs PMSI (PSY, MCO, SSR/SMR, HAD)
- ✅ **Variantes de format 2021** — Auto-détection des anciens formats (Fondation Vallée)
- ✅ **Normalisation IPP** — Cohérence des numéros de dossier entre années (BIQuery compat)
- ✅ **Traitement parallèle** — ThreadPoolExecutor multi-cœur pour le parsing
- ✅ **Master Patient Index (MPI)** — Croisement automatique des couples (IPP, DDN)
- ✅ **Identitovigilance** — Détection et résolution des collisions d'identité
- ✅ **Auto-résolution bayésienne** — Choix automatique de la DDN pivot par fréquence
- ✅ **Export CSV Pilot** — Export normalisé avec DDN pivot injectée
- ✅ **Export .txt purifié** — Fichier nettoyé prêt pour e-PMSI
- ✅ **Import CSV** — Lecture et affichage de fichiers CSV externes
- ✅ **Inspector Terminal** — Analyse ligne par ligne avec auto-repair
- ✅ **Dark Mode** — Thème sombre complet
- ✅ **Raccourcis clavier** — Navigation rapide (Ctrl+1→6)
- ✅ **EXE Portable** — Standalone 11 MB, aucune installation requise
- ✅ **Bridge HTTP REST** — Expose le moteur ATIH à une application PHP
- ✅ **Visualisation Excel** — Charts interactifs depuis un ou plusieurs `.xlsx`
- ✅ **Mode d'emploi PDF** — Généré via `fpdf2` (`tools/generate_manual.py`)
- ✅ **Structure polaire** — Organigramme Pôle/Secteur/UM avec export PDF multi-pages
- ✅ **Analyse d'activité par UM** *(V35)* — Croise structure + RPS/RAA pour détecter les UM dormantes · drop-zone HTML5 accessible clavier · parsing async chunks 5k lignes · export CSV UTF-8 BOM · badges rouges clignotants sur l'arbre
- ✅ **Guide PDF 204 pages** — 20 pages par feature · logo Paul Guiraud en header · `tools/generate_guide.py`

### Formats ATIH couverts (2010–2026)

| Champ           | Formats                                                         | Depuis |
| --------------- | --------------------------------------------------------------- | ------ |
| **PSY**         | RPS, RAA, RPSA, R3A, FICHSUP-PSY, EDGAR, FICUM-PSY, RSF-ACE-PSY | 2007   |
| **MCO**         | RSS/RUM, RSFA, RSFB, RSFC                                       | 1991   |
| **SSR/SMR**     | RHS, SSRHA, RAPSS, FICHCOMP-SMR                                 | 2003   |
| **HAD**         | RPSS, RAPSS-HAD, FICHCOMP-HAD, SSRHA-HAD                        | 2005   |
| **Transversal** | VID-HOSP, ANO-HOSP, FICHCOMP                                    | 2009   |

## Installation

```bash
# Cloner le dépôt
git clone https://github.com/Adam-Blf/sovereign_os_dim.git
cd sovereign_os_dim

# Créer un environnement virtuel
python -m venv .venv
.venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

## Utilisation

```bash
# Lancer l'application
python main.py
```

### Workflow DIM

1. **Modo Files** — Déposez vos dossiers contenant les fichiers ATIH
2. **Scanner & Traiter** — Le moteur identifie, parse et croise les données
3. **Identitovigilance** — Résolvez les collisions IPP/DDN (manuel ou auto)
4. **Export PMSI-Pilot** — Générez les CSV normalisés avec DDN pivot injectée

## Tests

```bash
# Lancer tous les tests
python -m pytest tests/ -v

# Avec couverture de code
python -m pytest tests/ -v --cov=backend --cov-report=term-missing
```

**178 tests Python + 21 tests JS** couvrant :

- Identification des 23 formats ATIH (PSY, MCO, SSR, HAD, transversal)
- Validation de ligne (padding, artefacts d'export)
- Normalisation IPP (cohérence BIQuery 2022-2025)
- Auto-détection variantes de format 2021
- Collisions MPI et résolution bayésienne
- Export CSV et .txt purifié
- Intégrité de la matrice ATIH
- Analyse d'activité par UM · `tests/frontend/test_activity_analysis.mjs` ·
  helpers `collectUmLeaves`, `detectAtihFormat`, `countUmActivity`,
  `countUmActivityAsync`, `extractPeriodFromFilenames` · 21 cas couverts
  (format RPS/RAA, périodes, perf 1000×50 UM, scénario métier complet).

## Architecture

```
sovereign_os_dim/
├── main.py                 # Point d'entrée pywebview (desktop)
├── bridge.py               # Point d'entrée bridge HTTP (PHP)
├── backend/
│   ├── __init__.py         # Package init
│   ├── api.py              # API exposée au frontend (js_api)
│   ├── bridge.py           # Serveur Flask REST (intégration PHP)
│   └── data_processor.py   # Moteur ATIH (scan, MPI, export)
├── frontend/
│   ├── index.html          # Interface principale (desktop)
│   ├── css/style.css       # Design system premium
│   └── js/app.js           # Logique frontend
├── php/                    # Console PHP consommant le bridge
│   ├── SovereignClient.php # Client cURL autonome
│   ├── config.php          # URL + token (env vars)
│   ├── index.php           # Tableau de bord
│   ├── collisions.php      # Identitovigilance
│   ├── chart.php           # Visualisation Excel (1+ fichiers)
│   ├── assets/style.css    # Design cohérent avec le desktop
│   └── README.md           # Guide PHP détaillé
├── tools/
│   └── generate_manual.py  # Mode d'emploi PDF (fpdf2)
├── tests/
│   ├── conftest.py         # Fixtures partagées (10 fixtures)
│   └── test_data_processor.py  # 147 tests unitaires
├── build.bat               # Script de compilation PyInstaller
├── requirements.txt        # Dépendances Python
└── README.md               # Ce fichier
```

## Tech Stack

- **Backend** : Python 3.12+, pywebview 5.3+, pythonnet 3.0+
- **Frontend** : HTML5, Tailwind CSS (CDN), Lucide Icons, Chart.js, Anime.js
- **Tests** : pytest 9.0+, pytest-cov
- **Build** : PyInstaller 6.11+
- **Fonts** : Plus Jakarta Sans, JetBrains Mono

## Intégration PHP (bridge HTTP REST)

Un serveur HTTP optionnel ré-expose le moteur ATIH à une application PHP. Le
desktop pywebview reste l'usage principal — le bridge est un complément pour
les équipes qui souhaitent piloter le moteur depuis un navigateur.

```bash
# Terminal 1 — Lancer le bridge
SOVEREIGN_BRIDGE_TOKEN=secret python bridge.py --port 8765

# Terminal 2 — Lancer la console PHP
export SOVEREIGN_BRIDGE_URL=http://127.0.0.1:8765
export SOVEREIGN_BRIDGE_TOKEN=secret
php -S 127.0.0.1:8080 -t php
```

Ouvrez http://127.0.0.1:8080. Voir [`php/README.md`](php/README.md) pour le
guide détaillé (endpoints, authentification Bearer, CORS, client PHP).

### Endpoints principaux

| Endpoint                | Méthode | Rôle                                          |
| ----------------------- | ------- | --------------------------------------------- |
| `/health`               | GET     | Heartbeat (public)                            |
| `/api/matrix`           | GET     | 23 formats ATIH                               |
| `/api/scan`             | POST    | Scan de dossiers                              |
| `/api/process`          | POST    | Scan + extraction MPI                         |
| `/api/collisions`       | GET     | Liste des collisions IPP/DDN                  |
| `/api/resolve`          | POST    | `set_pivot` manuel ou `auto=true`             |
| `/api/export`           | POST    | Export CSV Pilot                              |
| `/api/import-excel`     | POST    | Lecture `.xlsx`                               |
| `/api/chart-from-excel` | POST    | Série agrégée pour Chart.js (1 ou N fichiers) |

## Visualisation Excel (un ou plusieurs classeurs)

La page `php/chart.php` transforme un ou plusieurs `.xlsx` en graphique
interactif (Chart.js). Deux modes pour le multi-fichiers :

- **`compare`** — une série par fichier, alignée sur l'union des labels
  (comparaison 2024 vs 2025, plusieurs établissements…)
- **`merge`** — fusion des lignes en une seule série (rapport consolidé)

Agrégations : `sum`, `avg`, `count`. Types : `bar`, `line`, `pie`, `doughnut`.
Les fichiers restent côté serveur — aucun upload depuis le navigateur.

## Mode d'emploi PDF (fpdf2)

```bash
pip install "fpdf2>=2.8"
python tools/generate_manual.py
# → docs/Sovereign_OS_DIM_Manuel.pdf
```

Le script régénère le PDF à chaque évolution des endpoints. Le contenu reste
la source de vérité dans `tools/generate_manual.py`.

## Compilation

```bash
# Compiler en exécutable Windows (dossier + standalone)
build.bat
```

## Raccourcis Clavier

| Raccourci | Action             |
| --------- | ------------------ |
| `Ctrl+1`  | Dashboard          |
| `Ctrl+2`  | Modo Files         |
| `Ctrl+3`  | Identitovigilance  |
| `Ctrl+4`  | Export PMSI        |
| `Ctrl+5`  | Tutoriel           |
| `Echap`   | Fermer les modales |

## Auteur

**Adam Beloucif** — Station DIM, GHT Sud Paris

## Changelog

### V34.0 — 2026-03-03

- ✅ Fix erreur `WebViewException` (ajout `pythonnet` dans les dépendances)
- ✅ Vérification gracieuse des dépendances au démarrage
- ✅ Normalisation IPP pour cohérence BIQuery (2021 Fondation Vallée)
- ✅ Variantes de format 2021 RPS/RAA (auto-détection par longueur de ligne)
- ✅ Suite de tests unitaires complète (147 tests, 11 classes)
- ✅ Fixtures de test pour PSY, MCO, variantes 2021, collisions
- ✅ `_variant_cache` dans `__slots__` pour optimisation mémoire

### v17.0 — 2026-03-02

- ✅ Réécriture complète du backend avec documentation métier
- ✅ Support import CSV avec auto-détection du séparateur
- ✅ Dark mode complet (CSS + UI)
- ✅ Nettoyage du projet (suppression des builds obsolètes)
- ✅ Header ASCII professionnel sur tous les fichiers Python
- ✅ Commentaires métier expliquant le POURQUOI

---

<p align="center">
  <sub>Par <a href="https://adam.beloucif.com">Adam Beloucif</a> · Data Engineer & Fullstack Developer · <a href="https://github.com/Adam-Blf">GitHub</a></sub>
</p>
