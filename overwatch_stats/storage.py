"""SQLite storage for hero rate snapshots."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .scraper import HeroRate

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "rates.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    ts          TEXT NOT NULL,
    hero_id     TEXT NOT NULL,
    hero_name   TEXT NOT NULL,
    hero_role   TEXT NOT NULL,
    pickrate    REAL NOT NULL,
    winrate     REAL NOT NULL,
    f_role      TEXT NOT NULL,
    f_input     TEXT NOT NULL,
    f_rq        TEXT NOT NULL,
    f_tier      TEXT NOT NULL,
    f_map       TEXT NOT NULL,
    f_region    TEXT NOT NULL,
    PRIMARY KEY (ts, hero_id, f_role, f_input, f_rq, f_tier, f_map, f_region)
);
CREATE INDEX IF NOT EXISTS idx_snapshots_filter_hero
    ON snapshots(f_role, f_input, f_rq, f_tier, f_map, f_region, hero_id, ts);
"""


def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def insert_snapshot(
    conn: sqlite3.Connection,
    rates: Iterable[HeroRate],
    filters: dict,
    ts: str | None = None,
) -> int:
    ts = ts or utcnow_iso()
    rows = [
        (
            ts,
            r.hero_id,
            r.hero_name,
            r.role,
            r.pickrate,
            r.winrate,
            filters["role"],
            filters["input"],
            filters["rq"],
            filters["tier"],
            filters["map"],
            filters["region"],
        )
        for r in rates
    ]
    with conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO snapshots
              (ts, hero_id, hero_name, hero_role, pickrate, winrate,
               f_role, f_input, f_rq, f_tier, f_map, f_region)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
    return len(rows)


def query_series(
    conn: sqlite3.Connection,
    filters: dict,
    heroes: list[str] | None = None,
) -> dict[str, list[tuple[str, float, float]]]:
    """Return {hero_id: [(ts, pickrate, winrate), ...]} sorted by ts."""
    sql = """
        SELECT hero_id, ts, pickrate, winrate
        FROM snapshots
        WHERE f_role = ? AND f_input = ? AND f_rq = ?
          AND f_tier = ? AND f_map = ? AND f_region = ?
    """
    params: list = [
        filters["role"], filters["input"], filters["rq"],
        filters["tier"], filters["map"], filters["region"],
    ]
    if heroes:
        placeholders = ",".join("?" * len(heroes))
        sql += f" AND hero_id IN ({placeholders})"
        params.extend(heroes)
    sql += " ORDER BY hero_id, ts"

    out: dict[str, list[tuple[str, float, float]]] = {}
    for hero_id, ts, pr, wr in conn.execute(sql, params):
        out.setdefault(hero_id, []).append((ts, pr, wr))
    return out
