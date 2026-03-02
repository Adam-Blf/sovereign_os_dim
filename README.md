# 🛡️ Sovereign OS DIM — Station PMSI

![Status](https://img.shields.io/badge/status-production-green)
![Python](https://img.shields.io/badge/python-3.12+-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

## Description

**Sovereign OS** est une application desktop native conçue pour la station DIM du **GHT Sud Paris**. Elle permet de traiter, réconcilier et exporter les données PMSI (Programme de Médicalisation des Systèmes d'Information) conformément aux normes ATIH.

### Fonctionnalités principales

- ✅ **Scan multi-dossiers** — Détection automatique des fichiers `.txt` et `.csv` PMSI
- ✅ **23 formats ATIH** — Couverture complète des 4 champs PMSI (PSY, MCO, SSR/SMR, HAD)
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

### Formats ATIH couverts (2010–2026)

| Champ | Formats | Depuis |
|-------|---------|--------|
| **PSY** | RPS, RAA, RPSA, R3A, FICHSUP-PSY, EDGAR, FICUM-PSY, RSF-ACE-PSY | 2007 |
| **MCO** | RSS/RUM, RSFA, RSFB, RSFC | 1991 |
| **SSR/SMR** | RHS, SSRHA, RAPSS, FICHCOMP-SMR | 2003 |
| **HAD** | RPSS, RAPSS-HAD, FICHCOMP-HAD, SSRHA-HAD | 2005 |
| **Transversal** | VID-HOSP, ANO-HOSP, FICHCOMP | 2009 |

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

## Architecture

```
sovereign_os_dim/
├── main.py                 # Point d'entrée pywebview
├── backend/
│   ├── __init__.py         # Package init
│   ├── api.py              # API exposée au frontend (js_api)
│   └── data_processor.py   # Moteur ATIH (scan, MPI, export)
├── frontend/
│   ├── index.html          # Interface principale
│   ├── css/style.css       # Design system premium
│   └── js/app.js           # Logique frontend (992 lignes)
├── build.bat               # Script de compilation PyInstaller
├── requirements.txt        # Dépendances Python
└── README.md               # Ce fichier
```

## Tech Stack

- **Backend** : Python 3.12+, pywebview 5.3+
- **Frontend** : HTML5, Tailwind CSS (CDN), Lucide Icons, Chart.js, Anime.js
- **Build** : PyInstaller 6.11+
- **Fonts** : Plus Jakarta Sans, JetBrains Mono

## Compilation

```bash
# Compiler en exécutable Windows (dossier + standalone)
build.bat
```

## Raccourcis Clavier

| Raccourci | Action |
|-----------|--------|
| `Ctrl+1` | Dashboard |
| `Ctrl+2` | Modo Files |
| `Ctrl+3` | Identitovigilance |
| `Ctrl+4` | Export PMSI |
| `Ctrl+5` | Tutoriel |
| `Echap` | Fermer les modales |

## Auteur

**Adam Beloucif** — Station DIM, GHT Sud Paris

## Changelog

### v17.0 — 2026-03-02

- ✅ Réécriture complète du backend avec documentation métier
- ✅ Support import CSV avec auto-détection du séparateur
- ✅ Dark mode complet (CSS + UI)
- ✅ Nettoyage du projet (suppression des builds obsolètes)
- ✅ Header ASCII professionnel sur tous les fichiers Python
- ✅ Commentaires métier expliquant le POURQUOI
