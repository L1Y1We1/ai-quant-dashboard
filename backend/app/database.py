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


def database_status() -> dict:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return {
        "path": str(DB_PATH),
        "exists": DB_PATH.exists(),
        "size_bytes": DB_PATH.stat().st_size if DB_PATH.exists() else 0,
        "parent_writable": os.access(DB_PATH.parent, os.W_OK),
    }


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolio_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                shares REAL NOT NULL DEFAULT 0,
                average_cost REAL NOT NULL DEFAULT 0,
                target_weight REAL NOT NULL DEFAULT 0,
                theme TEXT,
                is_high_beta INTEGER NOT NULL DEFAULT 0,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, ticker),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        _ensure_column(conn, "portfolio_holdings", "average_cost", "REAL NOT NULL DEFAULT 0")
        _ensure_column(conn, "portfolio_holdings", "theme", "TEXT")
        _ensure_column(conn, "portfolio_holdings", "is_high_beta", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "portfolio_holdings", "notes", "TEXT")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS virtual_accounts (
                user_id INTEGER PRIMARY KEY,
                starting_cash REAL NOT NULL,
                cash REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS watchlist_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                note TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, ticker),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS virtual_account (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                starting_cash REAL NOT NULL,
                cash REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS virtual_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ticker TEXT NOT NULL,
                side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
                shares REAL NOT NULL CHECK (shares > 0),
                price REAL NOT NULL CHECK (price >= 0),
                notional REAL NOT NULL CHECK (notional >= 0),
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        _ensure_column(conn, "virtual_trades", "user_id", "INTEGER")
        _ensure_column(conn, "virtual_trades", "notes", "TEXT")
        conn.execute(
            """
            INSERT OR IGNORE INTO virtual_account (id, starting_cash, cash)
            VALUES (1, 100000.0, 100000.0)
            """
        )
        conn.commit()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
