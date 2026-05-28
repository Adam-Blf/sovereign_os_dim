<?php
/**
 * ══════════════════════════════════════════════════════════════════════════════
 *  SOVEREIGN OS DIM — Identitovigilance (résolution des collisions)
 * ══════════════════════════════════════════════════════════════════════════════
 *  Cette page liste les collisions IPP → DDN détectées par le moteur ATIH et
 *  permet à l'utilisateur de :
 *    - Fixer manuellement la DDN pivot d'un IPP donné (set_pivot)
 *    - Déclencher l'auto-résolution bayésienne (DDN majoritaire)
 *    - Filtrer la liste par un fragment d'IPP
 * ══════════════════════════════════════════════════════════════════════════════
 */

declare(strict_types=1);

require_once __DIR__ . '/SovereignClient.php';
$config = require __DIR__ . '/config.php';

// Client unique — même instance pour toute la requête
$client = new SovereignClient(
    $config['bridge_url'],
    $config['bridge_token'],
    $config['timeout']
);

$error = null;  // Erreur globale (affichée en bandeau rouge)
$notice = null; // Message de succès

// ──────────────────────────────────────────────────────────────────────────────
// POST : set_pivot (manuel) ou auto_resolve (bayésien)
// ──────────────────────────────────────────────────────────────────────────────
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    try {
        if ($action === 'set_pivot') {
            // L'utilisateur a choisi une DDN dans la liste des options
            $ipp = trim((string) ($_POST['ipp'] ?? ''));
            $ddn = trim((string) ($_POST['ddn'] ?? ''));
            if ($ipp === '' || $ddn === '') {
                throw new RuntimeException('IPP et DDN requis.');
            }
            $client->setPivot($ipp, $ddn);
            $notice = "Pivot défini : $ipp → $ddn";
        } elseif ($action === 'auto') {
            $res = $client->autoResolve();
            $notice = sprintf('%d collision(s) résolue(s) automatiquement.', (int) ($res['resolved'] ?? 0));
        }
    } catch (Throwable $e) {
        $error = $e->getMessage();
    }
}

// ──────────────────────────────────────────────────────────────────────────────
// Chargement des collisions (éventuellement filtrées)
// ──────────────────────────────────────────────────────────────────────────────
$query = trim((string) ($_GET['q'] ?? ''));
$collisions = [];
try {
    $res = $client->collisions($query);
    $collisions = $res['collisions'] ?? [];
} catch (Throwable $e) {
    $error = $error ?? $e->getMessage();
}

// Helper d'échappement HTML (évite les oublis de htmlspecialchars)
function h($v): string
{
    return htmlspecialchars((string) $v, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}
?>
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <title>Identitovigilance — Sovereign OS DIM</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="stylesheet" href="assets/style.css" />
</head>
<body>
  <header>
    <div>
      <h1>🛡️ Sovereign OS DIM</h1>
      <div class="sub">Identitovigilance · résolution MPI</div>
    </div>
    <nav>
      <a href="index.php">Tableau de bord</a>
      <a class="active" href="collisions.php">Identitovigilance</a>
      <a href="chart.php">Visualisation Excel</a>
    </nav>
  </header>

  <main>
    <?php if ($error): ?><div class="alert err"><?= h($error) ?></div><?php endif; ?>
    <?php if ($notice): ?><div class="alert ok"><?= h($notice) ?></div><?php endif; ?>

    <!-- Filtre + auto-résolution -->
    <section class="card">
      <h2>Collisions détectées (<?= count($collisions) ?>)</h2>
      <form method="get" class="row">
        <div>
          <label for="q">Filtrer par IPP</label>
          <input type="text" id="q" name="q" value="<?= h($query) ?>" placeholder="ex: 12345" />
        </div>
        <button type="submit">Filtrer</button>
      </form>

      <form method="post" style="margin-top:12px">
        <input type="hidden" name="action" value="auto" />
        <button type="submit">Auto-résoudre tout</button>
      </form>
    </section>

    <!-- Liste des collisions -->
    <?php foreach ($collisions as $col): ?>
      <section class="card">
        <h2>IPP <?= h($col['ipp'] ?? '') ?>
          <?php if (!empty($col['pivot'])): ?>
            <span class="badge ok">Pivot : <?= h($col['pivot']) ?></span>
          <?php else: ?>
            <span class="badge warn">Non résolue</span>
          <?php endif; ?>
        </h2>
        <p style="color:var(--text-dim);font-size:12px;margin:-4px 0 10px">
          <?= (int) ($col['total_sources'] ?? 0) ?> occurrence(s) dans les fichiers source.
        </p>
        <table>
          <thead><tr><th>DDN candidate</th><th>Occurrences</th><th>Sources</th><th>Action</th></tr></thead>
          <tbody>
          <?php foreach ($col['options'] ?? [] as $opt): ?>
            <tr>
              <td><code><?= h($opt['ddn'] ?? '') ?></code></td>
              <td><?= (int) ($opt['count'] ?? 0) ?></td>
              <td><?= h(implode(', ', $opt['sources'] ?? [])) ?></td>
              <td>
                <form method="post" style="display:inline">
                  <input type="hidden" name="action" value="set_pivot" />
                  <input type="hidden" name="ipp" value="<?= h($col['ipp'] ?? '') ?>" />
                  <input type="hidden" name="ddn" value="<?= h($opt['ddn'] ?? '') ?>" />
                  <button type="submit">Définir pivot</button>
                </form>
              </td>
            </tr>
          <?php endforeach; ?>
          </tbody>
        </table>
      </section>
    <?php endforeach; ?>

    <?php if (!$collisions && !$error): ?>
      <div class="alert ok">✔ Aucune collision non résolue.</div>
    <?php endif; ?>
  </main>

  <div class="footer">Sovereign OS V32.0 · Identitovigilance · Adam Beloucif</div>
</body>
</html>
