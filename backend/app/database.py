from __future__ import annotations

import os
import sqlite3
from pathlib import Path


DB_PATH = Path(os.getenv("QUANT_DB_PATH", Path(__file__).resolve().parents[1] / "quant.db"))


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prices (
                ticker TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL NOT NULL,
                adj_close REAL,
                volume INTEGER,
                ma20 REAL,
                ma50 REAL,
                ma200 REAL,
                momentum_3m REAL,
                momentum_6m REAL,
                volatility REAL,
                PRIMARY KEY (ticker, date)
            )
            """
        )
        conn.commit()
