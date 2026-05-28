# Sovereign OS DIM — Intégration PHP

Ce dossier contient la console PHP qui pilote le moteur ATIH via le bridge
HTTP exposé par `python bridge.py`. Aucune dépendance Composer n'est requise —
uniquement PHP 8.1+ avec l'extension `curl`.

## Sommaire

- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Pages disponibles](#pages-disponibles)
- [Utiliser le client PHP dans votre propre application](#utiliser-le-client-php)
- [Visualisation Excel multi-fichiers](#visualisation-excel-multi-fichiers)
- [Sécurité](#sécurité)
- [Dépannage](#dépannage)

## Architecture

```
 ┌────────────────┐   HTTP JSON    ┌──────────────────┐   appels internes   ┌──────────────────┐
 │  Navigateur    │ ──────────────►│  php/index.php   │ ───────────────────►│ SovereignClient  │
 │  (HTML+JS)     │◄──── HTML ─────│  chart.php       │◄──── tableau PHP ───│   (cURL)         │
 └────────────────┘                └──────────────────┘                     └────────┬─────────┘
                                                                                     │ HTTP
                                                                                     ▼
                                                                         ┌───────────────────────┐
                                                                         │  python bridge.py     │
                                                                         │  Flask + DataProcessor│
                                                                         └───────────────────────┘
```

Le bridge n'est pas remplacé par PHP : il reste l'autorité métier. PHP ne fait
qu'appeler les endpoints REST et rendre l'HTML.

## Installation

```bash
# 1. Dépendances Python (depuis la racine du repo)
pip install -r requirements.txt

# 2. Lancer le bridge HTTP
SOVEREIGN_BRIDGE_TOKEN=secret python bridge.py --port 8765

# 3. Lancer le serveur PHP intégré (dans un second terminal)
export SOVEREIGN_BRIDGE_URL=http://127.0.0.1:8765
export SOVEREIGN_BRIDGE_TOKEN=secret
php -S 127.0.0.1:8080 -t php
```

Ouvrez ensuite http://127.0.0.1:8080.

## Configuration

Les valeurs sont lues depuis `php/config.php`, qui les récupère via
`getenv()`. Variables disponibles :

| Variable                   | Défaut                     | Rôle                                |
| -------------------------- | -------------------------- | ----------------------------------- |
| `SOVEREIGN_BRIDGE_URL`     | `http://127.0.0.1:8765`    | URL du bridge                       |
| `SOVEREIGN_BRIDGE_TOKEN`   | _(vide = auth désactivée)_ | Jeton Bearer partagé avec le bridge |
| `SOVEREIGN_BRIDGE_TIMEOUT` | `120`                      | Timeout cURL (secondes)             |

## Pages disponibles

| Page             | Rôle                                                                   |
| ---------------- | ---------------------------------------------------------------------- |
| `index.php`      | Tableau de bord : santé du bridge, scan/process, stats MPI             |
| `collisions.php` | Identitovigilance : liste des collisions + set_pivot + auto-résolution |
| `chart.php`      | Visualisation Chart.js depuis un ou plusieurs classeurs Excel          |

## Utiliser le client PHP

Le client est autonome (`php/SovereignClient.php`) — pas besoin d'autoloader.

```php
require_once __DIR__ . '/SovereignClient.php';

$client = new SovereignClient(
    'http://127.0.0.1:8765',
    getenv('SOVEREIGN_BRIDGE_TOKEN')
);

// Santé
$health = $client->health();

// Scan + process en un appel
$result = $client->process(['/srv/pmsi/2025', '/srv/pmsi/2024']);

// Résolution des collisions
$collisions = $client->collisions();
$client->setPivot('12345', '19800101');
$client->autoResolve();

// Export CSV Pilot
$client->exportCsv('/srv/pmsi/export');

// Import Excel et graphique
$meta  = $client->importExcel('/srv/pmsi/rapport.xlsx');
$chart = $client->chartFromExcel(
    ['/srv/pmsi/2024.xlsx', '/srv/pmsi/2025.xlsx'],
    labelCol: 'Mois',
    valueCol: 'Séjours',
    agg: 'sum',
    top: 12,
    mode: 'compare'
);
```

## Visualisation Excel multi-fichiers

La page `chart.php` accepte :

- **un seul fichier** : mode `merge` par défaut (une série unique)
- **plusieurs fichiers** (un chemin par ligne) :
  - `compare` → une série par fichier, alignée sur l'union des labels (utile
    pour comparer 2024 vs 2025 ou plusieurs établissements)
  - `merge` → fusion des lignes en une seule série (rapport consolidé)

Agrégations disponibles : `sum`, `avg`, `count`.
Types de graphique : `bar`, `line`, `pie`, `doughnut`.

Les fichiers restent côté serveur — aucun upload depuis le navigateur. Les
données PMSI ne transitent donc jamais en clair sur un réseau externe.

## Sécurité

- Le bridge écoute par défaut sur `127.0.0.1`. Pour l'ouvrir au LAN hospitalier,
  utilisez `--host 0.0.0.0` **et** définissez un `SOVEREIGN_BRIDGE_TOKEN`.
- `SOVEREIGN_BRIDGE_ORIGINS` contrôle la liste blanche CORS (séparateur virgule).
- Toutes les sorties PHP passent par `htmlspecialchars()` — aucune injection XSS.
- Les comparaisons de token utilisent `secrets.compare_digest` (résistant aux
  timing attacks).

## Dépannage

### Bridge inaccessible

Vérifier que `python bridge.py` est lancé et que le port 8765 est libre :

```bash
curl http://127.0.0.1:8765/health
```

### `openpyxl is not installed`

```bash
pip install "openpyxl>=3.1"
```

### `Colonnes introuvables`

La comparaison est sensible à la casse et aux espaces. Utilisez les menus
déroulants de `chart.php` pour sélectionner les colonnes exactement telles
qu'elles apparaissent dans le fichier.

## Mode d'emploi PDF

Un mode d'emploi complet au format PDF peut être généré avec :

```bash
pip install "fpdf2>=2.8"
python tools/generate_manual.py
# → docs/Sovereign_OS_DIM_Manuel.pdf
```
