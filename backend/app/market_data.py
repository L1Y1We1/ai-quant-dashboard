from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf

from .config import UNIVERSE
from .database import get_connection
from .indicators import add_indicators


PRICE_COLUMNS = [
    "ticker",
    "date",
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
    "ma20",
    "ma50",
    "ma200",
    "momentum_3m",
    "momentum_6m",
    "volatility",
]


def _normalize_download(raw: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if isinstance(raw.columns, pd.MultiIndex):
        raw = raw.copy()
        raw.columns = [col[0] for col in raw.columns]

    df = raw.reset_index()
    df.columns = [str(col).lower().replace(" ", "_") for col in df.columns]
    if "adj_close" not in df.columns:
        df["adj_close"] = df["close"]
    df["ticker"] = ticker
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df[["ticker", "date", "open", "high", "low", "close", "adj_close", "volume"]]


def refresh_prices(tickers: list[str] | None = None, period: str = "3y") -> dict[str, int]:
    if tickers is None:
        from .watchlist import candidate_tickers

        tickers = sorted(set(UNIVERSE) | set(candidate_tickers()))
    tickers = tickers or UNIVERSE
    saved: dict[str, int] = {}

    with get_connection() as conn:
        for ticker in tickers:
            raw = yf.download(ticker, period=period, interval="1d", auto_adjust=False, progress=False)
            if raw.empty:
                saved[ticker] = 0
                continue

            df = add_indicators(_normalize_download(raw, ticker))
            clean = df.where(pd.notnull(df), None)[PRICE_COLUMNS]
            records = [tuple(row) for row in clean.itertuples(index=False, name=None)]
            conn.executemany(
                """
                INSERT OR REPLACE INTO prices (
                    ticker, date, open, high, low, close, adj_close, volume,
                    ma20, ma50, ma200, momentum_3m, momentum_6m, volatility
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )
            saved[ticker] = len(records)
        conn.commit()

    return saved


def get_price_history(ticker: str, limit: int = 260) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM prices
            WHERE ticker = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (ticker.upper(), limit),
        ).fetchall()
    return [dict(row) for row in reversed(rows)]


def latest_market_snapshot(tickers: list[str] | None = None) -> list[dict]:
    params: list[str] = []
    filter_sql = ""
    if tickers:
        placeholders = ",".join("?" for _ in tickers)
        filter_sql = f"WHERE p.ticker IN ({placeholders})"
        params = [ticker.upper() for ticker in tickers]

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT p.*
            FROM prices p
            JOIN (
                SELECT ticker, MAX(date) AS max_date
                FROM prices
                GROUP BY ticker
            ) latest
            ON p.ticker = latest.ticker AND p.date = latest.max_date
            {filter_sql}
            ORDER BY p.ticker
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def data_status() -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS rows, MAX(date) AS latest_date FROM prices").fetchone()
    return {"rows": row["rows"], "latest_date": row["latest_date"], "as_of": date.today().isoformat()}
