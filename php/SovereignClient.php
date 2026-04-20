<?php
/**
 * ══════════════════════════════════════════════════════════════════════════════
 *  SOVEREIGN OS DIM — PHP Client
 * ══════════════════════════════════════════════════════════════════════════════
 *  Author  : Adam Beloucif
 *  Project : Sovereign OS V32.0 — Station DIM GHT Sud Paris
 *
 *  Client PHP pour le bridge HTTP exposé par `python bridge.py`.
 *  Encapsule les appels cURL, l'authentification Bearer et la sérialisation JSON.
 *
 *  Usage:
 *      require_once __DIR__ . '/SovereignClient.php';
 *      $client = new SovereignClient('http://127.0.0.1:8765', getenv('SOVEREIGN_BRIDGE_TOKEN'));
 *      $health = $client->health();
 *      $matrix = $client->matrix();
 *      $scan   = $client->scan(['C:/dim/2025']);
 *      $proc   = $client->process();
 *      $cols   = $client->collisions();
 *      $client->autoResolve();
 *      $stats  = $client->stats();
 *      $client->exportCsv('C:/dim/export');
 * ══════════════════════════════════════════════════════════════════════════════
 */

declare(strict_types=1);

final class SovereignClientException extends \RuntimeException {}

final class SovereignClient
{
    private string $baseUrl;
    private ?string $token;
    private int $timeoutSeconds;

    public function __construct(
        string $baseUrl = 'http://127.0.0.1:8765',
        ?string $token = null,
        int $timeoutSeconds = 60
    ) {
        $this->baseUrl = rtrim($baseUrl, '/');
        $this->token = $token ?: null;
        $this->timeoutSeconds = $timeoutSeconds;
    }

    // ──────────────────────────────────────────────────────────────────────────
    // ENDPOINTS
    // ──────────────────────────────────────────────────────────────────────────

    public function health(): array
    {
        return $this->request('GET', '/health');
    }

    public function matrix(): array
    {
        return $this->request('GET', '/api/matrix');
    }

    public function identify(string $filename): array
    {
        return $this->request('POST', '/api/identify', ['filename' => $filename]);
    }

    /** @param string[] $folders */
    public function scan(array $folders): array
    {
        return $this->request('POST', '/api/scan', ['folders' => $folders]);
    }

    /** @param string[]|null $folders */
    public function process(?array $folders = null): array
    {
        $payload = $folders ? ['folders' => $folders] : [];
        return $this->request('POST', '/api/process', $payload);
    }

    public function collisions(string $query = ''): array
    {
        $q = $query === '' ? '' : '?q=' . rawurlencode($query);
        return $this->request('GET', '/api/collisions' . $q);
    }

    public function setPivot(string $ipp, string $ddn): array
    {
        return $this->request('POST', '/api/resolve', ['ipp' => $ipp, 'ddn' => $ddn]);
    }

    public function autoResolve(): array
    {
        return $this->request('POST', '/api/resolve', ['auto' => true]);
    }

    public function stats(): array
    {
        return $this->request('GET', '/api/stats');
    }

    public function exportCsv(?string $outputDir = null): array
    {
        $payload = $outputDir ? ['output_dir' => $outputDir] : [];
        return $this->request('POST', '/api/export', $payload);
    }

    public function exportSanitized(string $path, ?string $outputDir = null): array
    {
        $payload = ['path' => $path];
        if ($outputDir) {
            $payload['output_dir'] = $outputDir;
        }
        return $this->request('POST', '/api/export-sanitized', $payload);
    }

    public function inspect(string $path): array
    {
        return $this->request('POST', '/api/inspect', ['path' => $path]);
    }

    public function importCsv(string $path): array
    {
        return $this->request('POST', '/api/import-csv', ['path' => $path]);
    }

    public function importExcel(string $path, ?string $sheet = null, int $limit = 5000): array
    {
        $payload = ['path' => $path, 'limit' => $limit];
        if ($sheet !== null) {
            $payload['sheet'] = $sheet;
        }
        return $this->request('POST', '/api/import-excel', $payload);
    }

    /**
     * Construit une ou plusieurs séries agrégées depuis un ou plusieurs Excel.
     *
     * @param string|string[] $paths    Un chemin unique OU un tableau de chemins
     *                                  (fichiers .xlsx côté serveur Python)
     * @param string          $labelCol Colonne d'axe X
     * @param string          $valueCol Colonne numérique à agréger
     * @param string          $agg      "sum" | "avg" | "count"
     * @param int             $top      Nombre de buckets max (0 = tous)
     * @param string|null     $sheet    Nom de la feuille (défaut: première)
     * @param string          $mode     "merge" (une série fusionnée) |
     *                                  "compare" (une série par fichier).
     *                                  Par défaut : merge si un fichier, compare sinon.
     */
    public function chartFromExcel(
        $paths,
        string $labelCol,
        string $valueCol,
        string $agg = 'sum',
        int $top = 20,
        ?string $sheet = null,
        ?string $mode = null
    ): array {
        $payload = [
            'label' => $labelCol,
            'value' => $valueCol,
            'agg'   => $agg,
            'top'   => $top,
        ];

        // Normalise : un string = un seul fichier, un array = multi-fichiers
        if (is_array($paths)) {
            $payload['paths'] = array_values($paths);
        } else {
            $payload['path'] = (string) $paths;
        }

        if ($sheet !== null) {
            $payload['sheet'] = $sheet;
        }
        if ($mode !== null) {
            $payload['mode'] = $mode;
        }
        return $this->request('POST', '/api/chart-from-excel', $payload);
    }

    public function reset(): array
    {
        return $this->request('POST', '/api/reset');
    }

    // ──────────────────────────────────────────────────────────────────────────
    // TRANSPORT
    // ──────────────────────────────────────────────────────────────────────────

    private function request(string $method, string $path, array $payload = []): array
    {
        $url = $this->baseUrl . $path;
        $ch = curl_init($url);

        $headers = ['Accept: application/json'];
        if ($this->token) {
            $headers[] = 'Authorization: Bearer ' . $this->token;
        }

        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => $this->timeoutSeconds,
            CURLOPT_CONNECTTIMEOUT => 5,
            CURLOPT_CUSTOMREQUEST  => $method,
        ]);

        if ($method === 'POST') {
            $body = json_encode($payload, JSON_UNESCAPED_UNICODE);
            if ($body === false) {
                curl_close($ch);
                throw new SovereignClientException('JSON encode failed');
            }
            $headers[] = 'Content-Type: application/json';
            curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
        }

        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

        $raw = curl_exec($ch);
        if ($raw === false) {
            $err = curl_error($ch);
            curl_close($ch);
            throw new SovereignClientException("Bridge unreachable: {$err}");
        }
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        $data = json_decode((string) $raw, true);
        if (!is_array($data)) {
            throw new SovereignClientException(
                "Invalid JSON response (HTTP {$status}): " . substr((string) $raw, 0, 200)
            );
        }

        if ($status >= 400) {
            $msg = $data['error'] ?? ('HTTP ' . $status);
            throw new SovereignClientException("Bridge error: {$msg}");
        }

        return $data;
    }
}
