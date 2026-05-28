<?php
/**
 * ══════════════════════════════════════════════════════════════════════════════
 *  SOVEREIGN OS DIM — Configuration du client PHP
 * ══════════════════════════════════════════════════════════════════════════════
 *  Chargé par toutes les pages PHP. Les valeurs peuvent être surchargées par
 *  des variables d'environnement, ce qui évite de commiter un token en clair.
 * ══════════════════════════════════════════════════════════════════════════════
 */

declare(strict_types=1);

return [
    // URL du bridge HTTP (lancé par `python bridge.py`)
    'bridge_url' => getenv('SOVEREIGN_BRIDGE_URL') ?: 'http://127.0.0.1:8765',

    // Jeton Bearer partagé — DOIT correspondre à SOVEREIGN_BRIDGE_TOKEN
    // côté Python. Laisser vide pour du dev local sans auth.
    'bridge_token' => getenv('SOVEREIGN_BRIDGE_TOKEN') ?: '',

    // Timeout en secondes (exports longs possibles sur gros dossiers)
    'timeout' => (int) (getenv('SOVEREIGN_BRIDGE_TIMEOUT') ?: 120),
];
