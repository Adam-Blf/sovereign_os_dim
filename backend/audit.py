"""
═══════════════════════════════════════════════════════════════════════════════
 backend/audit.py · Journal d'audit RGPD art. 30 · persistance SQLite
═══════════════════════════════════════════════════════════════════════════════

Table immutable · chaque ligne contient timestamp, opérateur, action, cible,
hash SHA-256 chaîné au précédent (intégrité) · pas de UPDATE ni DELETE.

Path · %LOCALAPPDATA%/SovereignOS/audit.db (Windows) ou
       ~/.local/share/SovereignOS/audit.db (Linux/macOS)
       Override via env SOVEREIGN_AUDIT_DB.

Conformité ·
- Art. 30 RGPD · registre des activités de traitement
- L. 1110-4 CSP · traçabilité des accès aux données nominatives
- ANSSI niveau 2 · journal horodaté + hash chaîné
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator


def _default_audit_path() -> str:
    """Détermine le chemin de la DB d'audit selon l'OS."""
    env = os.environ.get("SOVEREIGN_AUDIT_DB")
    if env:
        return env
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA",
                              os.path.expanduser("~/AppData/Local"))
    else:
        base = os.environ.get("XDG_DATA_HOME",
                              os.path.expanduser("~/.local/share"))
    return os.path.join(base, "SovereignOS", "audit.db")


AUDIT_DB = _default_audit_path()


def _ensure_dir() -> None:
    os.makedirs(os.path.dirname(AUDIT_DB), exist_ok=True)


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    _ensure_dir()
    c = sqlite3.connect(AUDIT_DB, isolation_level=None)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ts        TEXT    NOT NULL,
            who       TEXT    NOT NULL,
            action    TEXT    NOT NULL,
            target    TEXT    NOT NULL,
            prev_hash TEXT    NOT NULL,
            sha256    TEXT    NOT NULL UNIQUE
        )
    """)
    try:
        yield c
    finally:
        c.close()


def _last_hash(c: sqlite3.Connection) -> str:
    row = c.execute("SELECT sha256 FROM events ORDER BY id DESC LIMIT 1").fetchone()
    return row[0] if row else "0" * 64


def append(who: str, action: str, target: str = "") -> dict:
    """
    Append-only · journalise un événement et retourne la ligne insérée.
    Le hash est chaîné · sha256(prev_hash + ts + who + action + target).
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    with _conn() as c:
        prev = _last_hash(c)
        payload = "|".join((prev, ts, who, action, target))
        h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        c.execute(
            "INSERT INTO events (ts, who, action, target, prev_hash, sha256) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ts, who, action, target, prev, h),
        )
        return {"ts": ts, "who": who, "action": action, "target": target,
                "prev_hash": prev, "sha256": h}


def list_events(limit: int = 30) -> list[dict]:
    """Liste les N derniers événements, plus récents d'abord."""
    with _conn() as c:
        rows = c.execute(
            "SELECT ts, who, action, target, sha256 FROM events "
            "ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [{"ts": r[0], "who": r[1], "action": r[2],
             "target": r[3], "sha256": r[4]} for r in rows]


def count() -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM events").fetchone()[0]


def verify_chain() -> dict:
    """
    Vérifie l'intégrité de la chaîne · recalcule chaque hash depuis le début
    et signale toute incohérence (signe d'altération).
    """
    with _conn() as c:
        rows = c.execute(
            "SELECT id, ts, who, action, target, prev_hash, sha256 "
            "FROM events ORDER BY id"
        ).fetchall()
    expected_prev = "0" * 64
    broken_at = None
    for r in rows:
        _id, ts, who, action, target, prev, h = r
        if prev != expected_prev:
            broken_at = _id
            break
        recomputed = hashlib.sha256(
            "|".join((prev, ts, who, action, target)).encode()
        ).hexdigest()
        if recomputed != h:
            broken_at = _id
            break
        expected_prev = h
    return {"total_events": len(rows),
            "valid": broken_at is None,
            "broken_at_id": broken_at}
