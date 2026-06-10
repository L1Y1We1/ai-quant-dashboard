from __future__ import annotations

from .config import UNIVERSE
from .config import HIGH_BETA_TICKERS
from .database import get_connection
from .market_data import latest_market_snapshot


SAMPLE_HOLDINGS = {
    "QQQ": 25,
    "NVDA": 12,
    "AVGO": 4,
    "TSM": 20,
    "MU": 30,
    "MRVL": 35,
    "VRT": 18,
    "ANET": 10,
    "AMZN": 8,
    "PLTR": 45,
    "TSLA": 6,
}

TARGET_WEIGHTS = {
    "QQQ": 0.12,
    "NVDA": 0.10,
    "AVGO": 0.09,
    "TSM": 0.08,
    "MU": 0.06,
    "MRVL": 0.05,
    "VRT": 0.06,
    "ANET": 0.05,
    "AMZN": 0.08,
    "PLTR": 0.06,
    "TSLA": 0.05,
    "CASH": 0.20,
}

CASH_BALANCE = 25_000.0


def seed_default_portfolio(user_id: int) -> None:
    from .watchlist import candidate_lookup

    candidates = candidate_lookup()
    with get_connection() as conn:
        for ticker, shares in SAMPLE_HOLDINGS.items():
            candidate = candidates.get(ticker)
            conn.execute(
                """
                INSERT OR IGNORE INTO portfolio_holdings (user_id, ticker, shares, average_cost, target_weight, theme, is_high_beta)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, ticker, shares, 0, TARGET_WEIGHTS.get(ticker, 0), candidate.theme if candidate else None, 1 if ticker in HIGH_BETA_TICKERS else 0),
            )
        conn.commit()


def get_user_holdings(user_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT ticker, shares, average_cost, target_weight, theme, is_high_beta, notes
            FROM portfolio_holdings
            WHERE user_id = ? AND shares > 0
            ORDER BY ticker
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_current_holding_tickers(user_id: int) -> set[str]:
    return {row["ticker"] for row in get_user_holdings(user_id)}


def get_holding_lookup(user_id: int) -> dict[str, dict]:
    return {row["ticker"]: row for row in get_user_holdings(user_id)}


def get_portfolio(user_id: int) -> dict:
    snapshots = {row["ticker"]: row for row in latest_market_snapshot()}
    user_holdings = get_user_holdings(user_id)
    holdings = []
    invested_value = 0.0

    for holding_row in user_holdings:
        ticker = holding_row["ticker"]
        shares = holding_row["shares"]
        price = snapshots.get(ticker, {}).get("close")
        market_value = shares * price if price else 0.0
        invested_value += market_value
        holdings.append(
            {
                "ticker": ticker,
                "shares": shares,
                "average_cost": holding_row["average_cost"],
                "price": price,
                "market_value": market_value,
                "target_weight": holding_row["target_weight"],
                "theme": holding_row["theme"],
                "is_high_beta": bool(holding_row["is_high_beta"]),
                "notes": holding_row["notes"],
            }
        )

    total_value = invested_value + CASH_BALANCE
    for holding in holdings:
        holding["current_weight"] = holding["market_value"] / total_value if total_value else 0
        holding["weight_gap"] = holding["target_weight"] - holding["current_weight"]

    return {
        "cash": CASH_BALANCE,
        "invested_value": invested_value,
        "total_value": total_value,
        "holdings": holdings,
        "target_weights": TARGET_WEIGHTS,
    }
