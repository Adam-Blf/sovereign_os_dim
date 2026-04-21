# CLAUDE.md — Sovereign OS DIM

Guide projet pour toute session Claude Code dans ce repo. Compile le contexte
technique, les règles métier PSY, et les préférences de collaboration d'Adam
Beloucif (owner, M1 Data Engineering EFREI, alternant TIM Fondation Vallée).

---

## 1. Identité du projet

**Sovereign OS DIM V35.0** — application desktop native (pywebview) pour la
station DIM du GHT Sud Paris. Source de vérité version : `./VERSION`
(propagée par `python scripts/sync_version.py`, hook `hooks/pre-commit`).

- **Cible utilisateur** : équipe TIM (Technicien d'Information Médicale) et
  cadres DIM, pas des développeurs. Interface française, vocabulaire métier.
- **Cœur métier** : scanner des fichiers ATIH (23 formats PMSI depuis 1991),
  extraire (IPP, DDN), construire le MPI, résoudre les collisions, exporter
  pour e-PMSI.
- **Différenciation vs CPage et DxCare** : ne JAMAIS dupliquer la
  facturation (CPage) ni le dossier patient (DxCare). Sovereign OS opère
  **sur les exports ATIH** et produit des agrégations/validations qu'aucun
  des deux outils ne sait faire (file active cross-recueils, parcours
  cross-modalités, détection collisions, etc.).

## 2. Stack technique

| Couche | Techno | Notes |
|---|---|---|
| Desktop | Python 3.12 + pywebview | HTML/CSS/JS embarqué, pas d'Electron |
| Frontend | HTML vanilla + Tailwind CDN + Chart.js + anime.js + lucide | pas de framework, dark mode, raccourcis Ctrl+1..7 |
| Bridge HTTP | Flask + openpyxl | `backend/bridge.py`, auth Bearer, CORS restrictif |
| PDF | fpdf2 (Helvetica latin-1, `_pdf_safe()` pour l'Unicode) | organigrammes, manuel utilisateur |
| Parser ATIH | regex positionnel largeur fixe, lecture latin-1 | `backend/data_processor.py` |
| Tests | pytest (178+ tests) | `tests/conftest.py`, TDD obligatoire sur le métier |
| Build | **`python build.py`** (PAS `build.bat` — bloqué par les EDR hospitaliers) | PyInstaller, onedir + onefile |
| PHP | client cURL (pas de Composer) | `php/SovereignClient.php` |

## 3. Règles de collaboration

**Communication** : français, style direct et concis, pas de blabla.
Réponses < 100 mots sauf si la tâche l'exige.

**Git/GitHub** :
- **Aucune mention "Claude" ou "Anthropic"** dans les commits, PRs, ou code.
  Jamais de footer "Generated with Claude Code", jamais de `Co-Authored-By:
  Claude`. Si un hook l'ajoute, le retirer manuellement.
- Auteur commit : `Adam Beloucif <adam@beloucif.com>` (via `git -c
  user.name="Adam Beloucif" -c user.email="adam@beloucif.com" commit` —
  ne **pas** toucher au git config global).
- Branches feature : préfixe `feat/` ou `fix/`, jamais `claude/`.
- Always-PR : créer une branche + PR via `gh pr create`, ne pas pousser
  direct sur `main`.

**Hooks actifs** :
- `hooks/pre-commit` → `scripts/sync_version.py` propage `VERSION` dans tous
  les fichiers qui en référencent une.
- Activation : `git config core.hooksPath hooks` (à faire après clone).

**Sécurité** :
- XSS → `escHtml()` systématique avant injection DOM, pas de `innerHTML`
  avec data backend non échappée.
- Path traversal → `os.path.abspath()` + validation avant ouverture de
  fichier côté bridge.
- Bridge HTTP refuse binding non-local sans `SOVEREIGN_BRIDGE_TOKEN`.
- Stack traces masquées en 500 (logs côté serveur seulement).
- Bandit/ruff/mypy encouragés, pas bloquants.

**TDD** : toute modif `backend/data_processor.py`, `backend/structure.py`
ou `backend/bridge.py` s'accompagne de tests. `python -m pytest tests/ -q`
doit rester vert avant commit.

## 4. Domaine PSY — terminologie et conventions ARS

**Codes secteur ARS** (la lettre centrale du code) :

| Lettre | Type | Couleur frontend | Exemple |
|---|---|---|---|
| **G** | Psychiatrie générale (adulte) | bleu `#2563EB` | `94G01` = Villejuif adulte |
| **I** | Infanto-juvénile | rose `#EC4899` | `94I01` = Gentilly enfants |
| **D** | UMD (Unité Malades Difficiles) | rouge `#DC2626` | `94D01` = Henri Colin |
| **P** | UHSA (pénitentiaire) | violet `#7C3AED` | `94P01` = Fresnes |
| **Z** | Intersectoriel | orange `#F97316` | `94Z01` = addictologie |

**Hiérarchie structure** : Territoire (GHT) → Établissement (PG / FV) →
Pôle → Secteur (AA{L}NN) → UM. Les UM héritent du type de leur secteur
parent.

**Établissements GHT Sud Paris** :
- **PG** = Groupe Hospitalier Paul Guiraud (Villejuif) — adultes, UMD, UHSA
- **FV** = Fondation Vallée (Gentilly) — **exclusivement pédopsy**

**Vocabulaire métier à maîtriser** : IPP, DDN, MPI, TIM, RPS/RAA/RHS/RPSS,
EDGAR, FICHSUP-PSY, RSF-ACE, DRUIDES (remplace PIVOINE depuis 2025), DAF,
VAP, file active, sectorisation, SDRE/SDT/SPI (soins sans consentement).

## 5. Design & UX

- Palette : `gh-navy #000091` (République française), `gh-teal #00897B`,
  `gh-error #E11D48`, `gh-success #10B981`, `gh-warning #F59E0B`
- Typo : Plus Jakarta Sans (sans), JetBrains Mono (mono), titres en
  `font-black italic tracking-tighter uppercase`
- Cards : `rounded-[2.5rem] border border-slate-100 dark:border-slate-700
  shadow-xl`
- Dark mode toujours supporté
- Organigrammes en HTML+CSS (ul imbriqués + `::before`/`::after`), **pas de
  SVG** (demande explicite de performance)
- PDF multi-pages : page régionale + 1 page par pôle, scaling auto

## 6. Outils disponibles

- **Skills globaux** : `~/.claude/skills/` contient ~1 430 skills
  (antigravity + graphify + gsd-*). Pour tout `/gsd-<x>`, invoquer directement.
- **Subagents spécialisés** : `~/.claude/agents/` contient 144 subagents
  VoltAgent (`frontend-developer`, `python-pro`, `security-auditor`,
  `backend-architect`, etc.)
- **Règle de sélection** (cf. `~/.claude/CLAUDE.md` global) : toujours
  préférer le subagent le plus spécialisé au `general-purpose`.
  Hiérarchie : `<stack>-specialist > <langage>-pro > <domaine>-<rôle> >
  general-purpose`.

## 7. Fichiers clés à connaître

```
backend/data_processor.py   # moteur ATIH (23 formats, MPI, auto-repair)
backend/api.py              # API pywebview exposée au JS
backend/bridge.py           # bridge HTTP Flask (16 endpoints)
backend/structure.py        # parser fichier structure + PDF organigramme
frontend/js/app.js          # logique frontend (boot, render, nav, escHtml)
frontend/css/style.css      # styles (anims, org-chart, tree, journey)
tools/generate_manual.py    # PDF manuel utilisateur (fpdf2)
scripts/sync_version.py     # propagation VERSION → tous les fichiers
tests/                      # pytest, 178+ tests (data, structure, active-pop)
sample/                     # fichiers de démo (non commit systématique)
VERSION                     # source de vérité version (V35.0)
build.py                    # PyInstaller (remplace build.bat)
```

## 8. Commandes usuelles

```bash
# Dev
python main.py                                  # lance l'app desktop
python -m pytest tests/ -q                      # tests (doit être vert)
python scripts/sync_version.py                  # resync la version
python tools/generate_manual.py                 # régénère le manuel PDF

# Bridge
SOVEREIGN_BRIDGE_TOKEN=secret python bridge.py  # démarre le bridge HTTP

# Build
python build.py                                 # exe (onedir + onefile)
python build.py --only portable                 # juste l'exe portable

# Git (identité override, pas de --global)
git -c user.name="Adam Beloucif" -c user.email="adam@beloucif.com" commit
```

## 9. Ce qui ne doit JAMAIS arriver

- Commit avec `Co-Authored-By: Claude` ou URL `claude.ai/code/session_*`
- Branche nommée `claude/*`
- `build.bat` recréé (les EDR hospitaliers le bloquent)
- XSS via `innerHTML` sans `escHtml` sur une valeur backend
- Stack trace exposée en 500 au client HTTP
- Skill gsd/VoltAgent utilisée pour du trivial (lecture d'un fichier
  connu, grep ciblé → outils directs)
- Duplication de fonctionnalités CPage ou DxCare
- Scraping de sites à paywall (respect ToS)
