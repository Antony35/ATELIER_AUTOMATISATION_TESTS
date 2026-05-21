"""
storage.py — Persistance des runs dans SQLite.
"""
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "runs.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crée la table si elle n'existe pas encore."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                api       TEXT    NOT NULL,
                timestamp TEXT    NOT NULL,
                passed    INTEGER NOT NULL,
                failed    INTEGER NOT NULL,
                errors    INTEGER NOT NULL,
                error_rate   REAL NOT NULL,
                availability REAL NOT NULL,
                latency_avg  REAL NOT NULL,
                latency_p95  REAL NOT NULL,
                details   TEXT    NOT NULL   -- JSON complet du run
            )
        """)


def save_run(report: dict):
    """Insère un rapport de run en base."""
    init_db()
    s = report["summary"]
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO runs
              (api, timestamp, passed, failed, errors,
               error_rate, availability, latency_avg, latency_p95, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report["api"],
            report["timestamp"],
            s["passed"],
            s["failed"],
            s["errors"],
            s["error_rate"],
            s["availability"],
            s["latency_ms_avg"],
            s["latency_ms_p95"],
            json.dumps(report),
        ))


def list_runs(limit: int = 20) -> list:
    """Retourne les N derniers runs (du plus récent au plus ancien)."""
    init_db()
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_run_by_id(run_id: int) -> dict | None:
    """Retourne le run complet (JSON) pour un id donné."""
    init_db()
    with _get_conn() as conn:
        row = conn.execute("SELECT details FROM runs WHERE id=?", (run_id,)).fetchone()
    if row:
        return json.loads(row["details"])
    return None
