from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app.config import SQLITE_PATH

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    openrgb_host TEXT NOT NULL DEFAULT '127.0.0.1',
    openrgb_port INTEGER NOT NULL DEFAULT 6742,
    openrgb_exe_path TEXT NOT NULL DEFAULT '',
    run_startup INTEGER NOT NULL DEFAULT 0,
    idle_mode_id TEXT NOT NULL DEFAULT '',
    idle_minutes INTEGER NOT NULL DEFAULT 0,
    backlight_percent INTEGER NOT NULL DEFAULT 100
);

INSERT OR IGNORE INTO app_settings (id) VALUES (1);

CREATE TABLE IF NOT EXISTS custom_modes (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    name TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _connect() -> sqlite3.Connection:
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


_conn = _connect()
_conn.executescript(SCHEMA)
_conn.execute("UPDATE app_settings SET idle_minutes = 0 WHERE TRIM(idle_mode_id) = ''")
_conn.commit()


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    try:
        yield _conn
        _conn.commit()
    except Exception:
        _conn.rollback()
        raise


def get_settings() -> dict[str, Any]:
    with db() as conn:
        row = conn.execute("SELECT * FROM app_settings WHERE id = 1").fetchone()
    return {
        "openrgb_host": row["openrgb_host"],
        "openrgb_port": int(row["openrgb_port"]),
        "openrgb_exe_path": row["openrgb_exe_path"] or "",
        "run_startup": bool(row["run_startup"]),
        "idle_mode_id": row["idle_mode_id"] or "",
        "idle_minutes": int(row["idle_minutes"]),
        "backlight_percent": int(row["backlight_percent"]),
    }


def update_settings(patch: dict[str, Any]) -> dict[str, Any]:
    current = get_settings()
    current.update({k: v for k, v in patch.items() if v is not None})
    with db() as conn:
        conn.execute(
            """
            UPDATE app_settings SET
                openrgb_host = ?,
                openrgb_port = ?,
                openrgb_exe_path = ?,
                run_startup = ?,
                idle_mode_id = ?,
                idle_minutes = ?,
                backlight_percent = ?
            WHERE id = 1
            """,
            (
                current["openrgb_host"],
                int(current["openrgb_port"]),
                current["openrgb_exe_path"],
                1 if current["run_startup"] else 0,
                current["idle_mode_id"],
                int(current["idle_minutes"]),
                int(current["backlight_percent"]),
            ),
        )
    return get_settings()


def list_custom_modes() -> list[dict[str, Any]]:
    with db() as conn:
        rows = conn.execute(
            "SELECT id, kind, name, payload, created_at, updated_at FROM custom_modes ORDER BY name"
        ).fetchall()
    return [_mode_row(row) for row in rows]


def get_custom_mode(mode_id: str) -> dict[str, Any] | None:
    with db() as conn:
        row = conn.execute(
            "SELECT id, kind, name, payload, created_at, updated_at FROM custom_modes WHERE id = ?",
            (mode_id,),
        ).fetchone()
    return _mode_row(row) if row else None


def create_custom_mode(kind: str, name: str, payload: dict[str, Any]) -> dict[str, Any]:
    mode_id = str(uuid.uuid4())
    with db() as conn:
        conn.execute(
            "INSERT INTO custom_modes (id, kind, name, payload) VALUES (?, ?, ?, ?)",
            (mode_id, kind, name, json.dumps(payload)),
        )
    mode = get_custom_mode(mode_id)
    assert mode is not None
    return mode


def update_custom_mode(mode_id: str, kind: str, name: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    with db() as conn:
        cur = conn.execute(
            """
            UPDATE custom_modes
            SET kind = ?, name = ?, payload = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (kind, name, json.dumps(payload), mode_id),
        )
        if cur.rowcount == 0:
            return None
    return get_custom_mode(mode_id)


def delete_custom_mode(mode_id: str) -> bool:
    with db() as conn:
        cur = conn.execute("DELETE FROM custom_modes WHERE id = ?", (mode_id,))
        return cur.rowcount > 0


def _mode_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "kind": row["kind"],
        "name": row["name"],
        "payload": json.loads(row["payload"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def sqlite_path() -> Path:
    return SQLITE_PATH
