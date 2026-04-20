<?php
/**
 * ══════════════════════════════════════════════════════════════════════════════
 *  SOVEREIGN OS DIM — Console PHP (tableau de bord du bridge HTTP)
 * ══════════════════════════════════════════════════════════════════════════════
 *  Cette page est l'interface PHP officielle qui consomme le bridge Python.
 *  Elle permet à un utilisateur DIM de piloter le moteur ATIH depuis un
 *  navigateur, sans avoir à ouvrir l'application desktop pywebview.
 *
 *  Flux fonctionnel :
 *    1. Vérification de la santé du bridge (/health)
 *    2. Saisie d'un ou plusieurs dossiers PMSI à scanner
 *    3. Scan + traitement via l'endpoint /api/process
 *    4. Affichage du dashboard (stats MPI, ventilation par format)
 *    5. Liens vers la page de résolution des collisions et la visualisation Excel
 *
 *  Sécurité :
 *    - Tous les appels vont au bridge sur 127.0.0.1 par défaut
 *    - Le jeton Bearer est lu depuis config.php / variables d'environnement
 *    - Les entrées utilisateur sont échappées via htmlspecialchars avant rendu
 * ══════════════════════════════════════════════════════════════════════════════
 */

declare(strict_types=1);

// Chargement du client HTTP et de la configuration (URL + token)
require_once __DIR__ . '/SovereignClient.php';
$config = require __DIR__ . '/config.php';

// Instance unique du client pour toute la requête
$client = new SovereignClient(
    $config['bridge_url'],
    $config['bridge_token'],
    $config['timeout']
);

// État initial : variables affichées dans la vue
$error = null;      // Message d'erreur global (rendu en haut de page)
$notice = null;     // Message de succès (vert)
$health = null;     // Résultat de l'appel /health
$stats = null;      // Dashboard aggregate renvoyé par /api/stats
$procResult = null; // Retour de /api/process après soumission du formulaire

// Heartbeat du bridge : si /health échoue, inutile d'aller plus loin
try {
    $health = $client->health();
} catch (Throwable $e) {
    $error = 'Bridge inaccessible : ' . $e->getMessage();
}

// ──────────────────────────────────────────────────────────────────────────────
// TRAITEMENT DES ACTIONS POST — scan/process/reset
// ──────────────────────────────────────────────────────────────────────────────
if ($health && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    try {
        if ($action === 'process') {
            // Un dossier par ligne dans le textarea (convention UNIX pratique)
            $raw = (string) ($_POST['folders'] ?? '');
            $folders = array_values(array_filter(array_map('trim', preg_split('/\r?\n/', $raw))));
            if (!$folders) {
                throw new RuntimeException('Renseignez au moins un dossier.');
            }
            $procResult = $client->process($folders);
            $notice = sprintf(
                '%d fichier(s) traité(s) — %s IPP uniques, %s collision(s)',
                (int) ($procResult['stats']['files_processed'] ?? 0),
                number_format((int) ($procResult['stats']['ipp_unique'] ?? 0), 0, ',', ' '),
                (int) ($procResult['stats']['collisions'] ?? 0)
            );
        } elseif ($action === 'auto_resolve') {
            $res = $client->autoResolve();
            $notice = sprintf('Auto-résolution : %d collision(s) fermée(s).', (int) ($res['resolved'] ?? 0));
        } elseif ($action === 'reset') {
            $client->reset();
            $notice = 'État du bridge réinitialisé.';
        }
    } catch (Throwable $e) {
        $error = $e->getMessage();
    }
}

// Récupération du dashboard agrégé (toujours après les actions pour refléter l'état)
if ($health) {
    try {
        $stats = $client->stats();
    } catch (Throwable $e) {
        $error = $error ?? $e->getMessage();
    }
}

// Helper d'échappement — évite l'oubli de htmlspecialchars
function h($v): string
{
    return htmlspecialchars((string) $v, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}
?>
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <title>Sovereign OS DIM — Console PHP</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="stylesheet" href="assets/style.css" />
</head>
<body>
  <header>
    <div>
      <h1>🛡️ Sovereign OS DIM</h1>
      <div class="sub">Console PHP · Bridge HTTP <?= h($config['bridge_url']) ?></div>
    </div>
    <nav>
      <a class="active" href="index.php">Tableau de bord</a>
      <a href="collisions.php">Identitovigilance</a>
      <a href="chart.php">Visualisation Excel</a>
    </nav>
  </header>

  <main>
    <?php if ($error): ?>
      <div class="alert err"><?= h($error) ?></div>
    <?php endif; ?>
    <?php if ($notice): ?>
      <div class="alert ok"><?= h($notice) ?></div>
    <?php endif; ?>

    <!-- Carte santé — heartbeat du bridge -->
    <section class="card">
      <h2>Santé du bridge</h2>
      <?php if ($health): ?>
        <div class="grid">
          <div class="stat">
            <div class="label">Service</div>
            <div class="value"><?= h($health['service'] ?? '—') ?></div>
          </div>
          <div class="stat">
            <div class="label">Version</div>
            <div class="value"><?= h($health['version'] ?? '—') ?></div>
          </div>
          <div class="stat">
            <div class="label">Formats ATIH</div>
            <div class="value"><?= (int) ($health['formats'] ?? 0) ?></div>
          </div>
          <div class="stat">
            <div class="label">Auth requise</div>
            <div class="value"><?= !empty($health['auth_required']) ? 'Oui' : 'Non' ?></div>
          </div>
        </div>
      <?php else: ?>
        <div class="alert err">Impossible de joindre le bridge. Lancez <code>python bridge.py</code> côté serveur.</div>
      <?php endif; ?>
    </section>

    <!-- Carte statistiques — dashboard PMSI -->
    <?php if ($stats): ?>
      <section class="card">
        <h2>Dashboard PMSI</h2>
        <div class="grid">
          <div class="stat"><div class="label">Dossiers</div><div class="value"><?= (int) ($stats['folders'] ?? 0) ?></div></div>
          <div class="stat"><div class="label">Fichiers</div><div class="value"><?= (int) ($stats['files'] ?? 0) ?></div></div>
          <div class="stat"><div class="label">IPP uniques</div><div class="value"><?= number_format((int) ($stats['mpi']['total'] ?? 0), 0, ',', ' ') ?></div></div>
          <div class="stat"><div class="label">Collisions</div><div class="value"><?= (int) ($stats['mpi']['collisions'] ?? 0) ?></div></div>
          <div class="stat"><div class="label">Résolues</div><div class="value"><?= (int) ($stats['mpi']['resolved'] ?? 0) ?></div></div>
        </div>

        <?php if (!empty($stats['format_breakdown'])): ?>
          <h2 style="margin-top:20px">Répartition par format</h2>
          <table>
            <thead><tr><th>Format</th><th>Fichiers</th><th>Champ</th></tr></thead>
            <tbody>
            <?php foreach ($stats['format_breakdown'] as $fb): ?>
              <tr>
                <td><?= h($fb['format'] ?? '') ?></td>
                <td><?= (int) ($fb['count'] ?? 0) ?></td>
                <td><span class="badge"><?= h($fb['field'] ?? '') ?></span></td>
              </tr>
            <?php endforeach; ?>
            </tbody>
          </table>
        <?php endif; ?>
      </section>
    <?php endif; ?>

    <!-- Carte action — scan + process -->
    <section class="card">
      <h2>Lancer un scan + traitement</h2>
      <form method="post">
        <input type="hidden" name="action" value="process" />
        <label for="folders">Dossiers PMSI (un par ligne, chemin local côté serveur)</label>
        <textarea id="folders" name="folders" rows="4" placeholder="/srv/pmsi/2025\n/srv/pmsi/2024"></textarea>
        <div class="row">
          <button type="submit">Scanner & Traiter</button>
          <button class="secondary" type="submit" name="action" value="auto_resolve">Auto-résoudre les collisions</button>
          <button class="secondary" type="submit" name="action" value="reset">Réinitialiser</button>
        </div>
      </form>
    </section>

    <!-- Fichiers traités : on affiche un résumé si un process vient d'avoir lieu -->
    <?php if ($procResult && !empty($procResult['files'])): ?>
      <section class="card">
        <h2>Fichiers détectés (<?= count($procResult['files']) ?>)</h2>
        <table>
          <thead><tr><th>Fichier</th><th>Format</th><th>Taille (KB)</th></tr></thead>
          <tbody>
            <?php foreach (array_slice($procResult['files'], 0, 200) as $f): ?>
              <tr>
                <td><?= h($f['name'] ?? '') ?></td>
                <td><?= h($f['format'] ?? '') ?></td>
                <td><?= h((string) ($f['size_kb'] ?? '')) ?></td>
              </tr>
            <?php endforeach; ?>
          </tbody>
        </table>
      </section>
    <?php endif; ?>
  </main>

  <div class="footer">
    Sovereign OS V32.0 · Bridge PHP · Adam Beloucif
  </div>
</body>
</html>
