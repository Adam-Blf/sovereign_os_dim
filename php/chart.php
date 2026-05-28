<?php
/**
 * ══════════════════════════════════════════════════════════════════════════════
 *  SOVEREIGN OS DIM — Visualisation Excel multi-fichiers (Chart.js)
 * ══════════════════════════════════════════════════════════════════════════════
 *  Cette page PHP transforme un ou plusieurs classeurs Excel en graphique
 *  interactif. Elle accepte aussi bien un seul fichier qu'une liste (un par
 *  ligne dans le textarea) et propose deux modes :
 *
 *    - merge   : fusionne les données de tous les fichiers en une seule série
 *    - compare : génère une série par fichier alignée sur l'union des labels
 *                (utile pour comparer 2024 vs 2025 ou plusieurs établissements)
 *
 *  Flux :
 *    1. Saisie d'un ou plusieurs chemins de .xlsx + feuille optionnelle
 *    2. Le bridge Python renvoie la liste des colonnes (entête de la 1re feuille)
 *    3. L'utilisateur choisit les colonnes X/Y, l'agrégation et le mode
 *    4. Le bridge agrège côté serveur et retourne labels + datasets
 *    5. Chart.js dessine dans le navigateur
 *
 *  Sécurité : les fichiers restent sur le serveur (pas d'upload). Les données
 *  PMSI ne transitent jamais en clair sur un réseau externe.
 * ══════════════════════════════════════════════════════════════════════════════
 */

declare(strict_types=1);

require_once __DIR__ . '/SovereignClient.php';
$config = require __DIR__ . '/config.php';

// Client HTTP unique vers le bridge Python
$client = new SovereignClient(
    $config['bridge_url'],
    $config['bridge_token'],
    $config['timeout']
);

// ──────────────────────────────────────────────────────────────────────────────
// ÉTAT DE LA PAGE (initialisé depuis POST ou GET)
// ──────────────────────────────────────────────────────────────────────────────
$error = null;                // Bandeau rouge d'erreur
$chartPayload = null;         // Résultat agrégé (labels + datasets)
$pathsRaw = (string) ($_POST['paths'] ?? $_GET['paths'] ?? '');
$sheet = (string) ($_POST['sheet'] ?? '');
$labelCol = (string) ($_POST['label'] ?? '');
$valueCol = (string) ($_POST['value'] ?? '');
$agg = (string) ($_POST['agg'] ?? 'sum');
$mode = (string) ($_POST['mode'] ?? '');          // merge|compare|'' (auto)
$chartType = (string) ($_POST['chart_type'] ?? 'bar');
if (!in_array($chartType, ['bar', 'line', 'pie', 'doughnut'], true)) {
    $chartType = 'bar';
}
$top = (int) ($_POST['top'] ?? 20);
$action = (string) ($_POST['action'] ?? '');

// Parsing de la liste de chemins (une ligne = un fichier). On ignore les vides.
$paths = array_values(array_filter(
    array_map('trim', preg_split('/\r?\n/', $pathsRaw)),
    fn($p) => $p !== ''
));

$headers = [];          // Colonnes détectées dans le premier fichier
$sheets = [];           // Feuilles du premier classeur
$currentSheet = null;   // Feuille sélectionnée

// Étape 1 : si au moins un chemin est fourni, on lit l'entête du 1er fichier
// pour peupler les menus déroulants colonne X / colonne Y.
if ($paths) {
    try {
        $meta = $client->importExcel($paths[0], $sheet ?: null, 1);
        $headers = $meta['headers'] ?? [];
        $sheets = $meta['sheets'] ?? [];
        $currentSheet = $meta['sheet'] ?? null;
    } catch (Throwable $e) {
        $error = $e->getMessage();
    }
}

// Étape 2 : l'utilisateur a cliqué "Générer" → on appelle l'agrégation.
// Le bridge accepte indifféremment 1 ou N chemins (voir chartFromExcel()).
if ($action === 'chart' && $paths && $labelCol !== '' && $valueCol !== '' && !$error) {
    try {
        $chartPayload = $client->chartFromExcel(
            count($paths) === 1 ? $paths[0] : $paths,
            $labelCol,
            $valueCol,
            $agg,
            $top,
            $sheet ?: null,
            $mode !== '' ? $mode : null
        );
    } catch (Throwable $e) {
        $error = $e->getMessage();
    }
}

// Helper : échappement HTML systématique (XSS-safe)
function h($v): string
{
    return htmlspecialchars((string) $v, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}
?>
<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8" />
    <title>Visualisation Excel — Sovereign OS DIM</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="stylesheet" href="assets/style.css" />
    <!-- Chart.js depuis CDN : déjà utilisé par le frontend desktop -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  </head>
  <body>
    <header>
      <div>
        <h1>🛡️ Sovereign OS DIM</h1>
        <div class="sub">Visualisation Excel multi-fichiers · Chart.js</div>
      </div>
      <nav>
        <a href="index.php">Tableau de bord</a>
        <a href="collisions.php">Identitovigilance</a>
        <a class="active" href="chart.php">Visualisation Excel</a>
      </nav>
    </header>

    <main>
      <?php if ($error): ?>
        <div class="alert err"><?= h($error) ?></div>
      <?php endif; ?>

      <!-- Étape 1 : saisie d'un ou plusieurs chemins de classeurs -->
      <section class="card">
        <h2>1. Choisir les classeurs Excel</h2>
        <form method="post">
          <label for="paths">Un chemin par ligne (côté serveur Python)</label>
          <textarea id="paths" name="paths" rows="4" placeholder="/srv/pmsi/2024.xlsx&#10;/srv/pmsi/2025.xlsx"><?= h($pathsRaw) ?></textarea>
          <div class="row">
            <?php if ($sheets): ?>
              <div>
                <label for="sheet">Feuille (appliquée à tous les fichiers)</label>
                <select id="sheet" name="sheet">
                  <?php foreach ($sheets as $s): ?>
                    <option value="<?= h($s) ?>" <?= $s === $currentSheet ? 'selected' : '' ?>>
                      <?= h($s) ?>
                    </option>
                  <?php endforeach; ?>
                </select>
              </div>
            <?php endif; ?>
            <button type="submit">Charger les colonnes</button>
          </div>
          <?php if (count($paths) > 1): ?>
            <div style="color:var(--text-dim);font-size:12px;margin-top:6px">
              <?= count($paths) ?> fichier(s) — les colonnes sont lues depuis le premier.
            </div>
          <?php endif; ?>
        </form>
      </section>

      <!-- Étape 2 : configuration des colonnes + mode d'agrégation + mode multi-fichiers -->
      <?php if ($headers): ?>
        <section class="card">
          <h2>2. Configurer la visualisation</h2>
          <form method="post">
            <input type="hidden" name="paths" value="<?= h($pathsRaw) ?>" />
            <input type="hidden" name="sheet" value="<?= h($currentSheet ?? '') ?>" />
            <input type="hidden" name="action" value="chart" />
            <div class="row">
              <div>
                <label for="label">Axe X (label)</label>
                <select id="label" name="label" required>
                  <option value="">— choisir —</option>
                  <?php foreach ($headers as $head): ?>
                    <option value="<?= h($head) ?>" <?= $head === $labelCol ? 'selected' : '' ?>>
                      <?= h($head) ?>
                    </option>
                  <?php endforeach; ?>
                </select>
              </div>
              <div>
                <label for="value">Valeur (numérique)</label>
                <select id="value" name="value" required>
                  <option value="">— choisir —</option>
                  <?php foreach ($headers as $head): ?>
                    <option value="<?= h($head) ?>" <?= $head === $valueCol ? 'selected' : '' ?>>
                      <?= h($head) ?>
                    </option>
                  <?php endforeach; ?>
                </select>
              </div>
              <div>
                <label for="agg">Agrégation</label>
                <select id="agg" name="agg">
                  <option value="sum" <?= $agg === 'sum' ? 'selected' : '' ?>>Somme</option>
                  <option value="avg" <?= $agg === 'avg' ? 'selected' : '' ?>>Moyenne</option>
                  <option value="count" <?= $agg === 'count' ? 'selected' : '' ?>>Comptage</option>
                </select>
              </div>
              <?php if (count($paths) > 1): ?>
                <div>
                  <label for="mode">Mode multi-fichiers</label>
                  <select id="mode" name="mode">
                    <option value="compare" <?= $mode === 'compare' || $mode === '' ? 'selected' : '' ?>>Comparer (1 série / fichier)</option>
                    <option value="merge" <?= $mode === 'merge' ? 'selected' : '' ?>>Fusionner (série unique)</option>
                  </select>
                </div>
              <?php endif; ?>
              <div>
                <label for="chart_type">Type de graphique</label>
                <select id="chart_type" name="chart_type">
                  <option value="bar" <?= $chartType === 'bar' ? 'selected' : '' ?>>Barres</option>
                  <option value="line" <?= $chartType === 'line' ? 'selected' : '' ?>>Ligne</option>
                  <option value="pie" <?= $chartType === 'pie' ? 'selected' : '' ?>>Camembert</option>
                  <option value="doughnut" <?= $chartType === 'doughnut' ? 'selected' : '' ?>>Donut</option>
                </select>
              </div>
              <div>
                <label for="top">Top N (0 = tous)</label>
                <input type="text" id="top" name="top" value="<?= h((string) $top) ?>" />
              </div>
              <button type="submit">Générer le graphique</button>
            </div>
          </form>
        </section>
      <?php endif; ?>

      <!-- Étape 3 : rendu Chart.js + tableau agrégé -->
      <?php if ($chartPayload): ?>
        <section class="card">
          <h2>
            3. Résultat —
            <?= h($chartPayload['label_col'] ?? '') ?> ×
            <?= h($chartPayload['value_col'] ?? '') ?>
            (<?= h($chartPayload['agg'] ?? '') ?>, mode <?= h($chartPayload['mode'] ?? '') ?>)
          </h2>

          <?php if (!empty($chartPayload['files'])): ?>
            <p style="color:var(--text-dim);font-size:12px;margin:-4px 0 10px">
              Fichiers : <?= h(implode(', ', $chartPayload['files'])) ?>
            </p>
          <?php endif; ?>

          <div class="chart-wrap"><canvas id="chart"></canvas></div>

          <h2 style="margin-top:16px">Données agrégées</h2>
          <table>
            <thead>
              <tr>
                <th><?= h($chartPayload['label_col'] ?? 'Label') ?></th>
                <?php foreach (($chartPayload['datasets'] ?? []) as $ds): ?>
                  <th><?= h($ds['name'] ?? '') ?></th>
                <?php endforeach; ?>
              </tr>
            </thead>
            <tbody>
              <?php foreach ($chartPayload['labels'] as $i => $lbl): ?>
                <tr>
                  <td><?= h($lbl) ?></td>
                  <?php foreach (($chartPayload['datasets'] ?? []) as $ds): ?>
                    <td><?= h((string) ($ds['values'][$i] ?? '')) ?></td>
                  <?php endforeach; ?>
                </tr>
              <?php endforeach; ?>
            </tbody>
          </table>
        </section>

        <script>
          // Rendu Chart.js — multi-séries si plusieurs fichiers en mode compare.
          (function () {
            const labels = <?= json_encode($chartPayload['labels'], JSON_UNESCAPED_UNICODE | JSON_HEX_TAG) ?>;
            const datasets = <?= json_encode($chartPayload['datasets'] ?? [], JSON_UNESCAPED_UNICODE | JSON_HEX_TAG) ?>;
            const chartType = <?= json_encode($chartType, JSON_HEX_TAG) ?>;

            // Palette cohérente avec le dark mode desktop
            const palette = [
              "#38bdf8", "#34d399", "#fbbf24", "#f87171", "#a78bfa",
              "#f472b6", "#60a5fa", "#facc15", "#fb7185", "#2dd4bf",
            ];

            // Pie/doughnut ne supportent bien qu'une seule série → on prend la 1re
            const isPieLike = chartType === "pie" || chartType === "doughnut";
            const chartDatasets = isPieLike
              ? [
                  {
                    label: datasets[0]?.name ?? "",
                    data: datasets[0]?.values ?? [],
                    backgroundColor: labels.map((_, i) => palette[i % palette.length]),
                  },
                ]
              : datasets.map((ds, i) => ({
                  label: ds.name,
                  data: ds.values,
                  backgroundColor: palette[i % palette.length] + "80", // semi-transparent
                  borderColor: palette[i % palette.length],
                  borderWidth: 2,
                  tension: 0.3,
                  fill: chartType === "line" ? false : true,
                }));

            new Chart(document.getElementById("chart"), {
              type: chartType,
              data: { labels: labels, datasets: chartDatasets },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: "#e2e8f0" } } },
                scales: isPieLike
                  ? {}
                  : {
                      x: { ticks: { color: "#94a3b8" }, grid: { color: "#1e293b" } },
                      y: { ticks: { color: "#94a3b8" }, grid: { color: "#1e293b" } },
                    },
              },
            });
          })();
        </script>
      <?php endif; ?>
    </main>

    <div class="footer">Sovereign OS V32.0 · Visualisation Excel multi-fichiers · Adam Beloucif</div>
  </body>
</html>
