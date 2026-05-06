"""
═══════════════════════════════════════════════════════════════════════════════
 backend/workflow.py · Pipeline TIM → MIM → ARS · persistance SQLite
═══════════════════════════════════════════════════════════════════════════════

Table immutable · chaque item suit son cycle de vie ·
  tim → mim → preflight → ars → done

Path · même répertoire que audit.db, fichier workflow.db.
Cohérent avec backend/audit.py (mêmes conventions XDG / LOCALAPPDATA).
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Literal


def _default_path() -> str:
    env = os.environ.get("SOVEREIGN_WORKFLOW_DB")
    if env:
        return env
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA",
                              os.path.expanduser("~/AppData/Local"))
    else:
        base = os.environ.get("XDG_DATA_HOME",
                              os.path.expanduser("~/.local/share"))
    return os.path.join(base, "SovereignOS", "workflow.db")


DB_PATH = _default_path()
Stage = Literal["tim", "mim", "preflight", "ars", "done"]


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH, isolation_level=None)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ipp       TEXT    NOT NULL,
            label     TEXT    NOT NULL,
            owner     TEXT    NOT NULL,
            stage     TEXT    NOT NULL,
            created   TEXT    NOT NULL,
            updated   TEXT    NOT NULL
        )
    """)
    try:
        yield c
    finally:
        c.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_item(ipp: str, label: str, owner: str,
             stage: Stage = "tim") -> dict:
    ts = _now()
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO items (ipp, label, owner, stage, created, updated) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ipp, label, owner, stage, ts, ts),
        )
        return {"id": cur.lastrowid, "ipp": ipp, "label": label,
                "owner": owner, "stage": stage,
                "created": ts, "updated": ts}


def advance(item_id: int, new_stage: Stage) -> dict | None:
    """Avance un item dans le pipeline · met à jour updated."""
    ts = _now()
    with _conn() as c:
        c.execute(
            "UPDATE items SET stage = ?, updated = ? WHERE id = ?",
            (new_stage, ts, item_id),
        )
        row = c.execute(
            "SELECT id, ipp, label, owner, stage, created, updated "
            "FROM items WHERE id = ?", (item_id,)
        ).fetchone()
    if not row:
        return None
    return {"id": row[0], "ipp": row[1], "label": row[2], "owner": row[3],
            "stage": row[4], "created": row[5], "updated": row[6]}


def list_pending(stage_filter: Stage | None = None,
                 limit: int = 100) -> list[dict]:
    with _conn() as c:
        if stage_filter:
            rows = c.execute(
                "SELECT id, ipp, label, owner, stage, created, updated "
                "FROM items WHERE stage = ? AND stage != 'done' "
                "ORDER BY id DESC LIMIT ?", (stage_filter, limit)
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT id, ipp, label, owner, stage, created, updated "
                "FROM items WHERE stage != 'done' "
                "ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    return [{"id": r[0], "ipp": r[1], "label": r[2], "owner": r[3],
             "stage": r[4], "created": r[5], "updated": r[6]} for r in rows]


def stage_counts() -> dict[str, int]:
    """Distribution des items par stage actif."""
    out = {"tim": 0, "mim": 0, "preflight": 0, "ars": 0}
    with _conn() as c:
        rows = c.execute(
            "SELECT stage, COUNT(*) FROM items "
            "WHERE stage != 'done' GROUP BY stage"
        ).fetchall()
    for stage, n in rows:
        if stage in out:
            out[stage] = n
    return out
