from __future__ import annotations

from .config import UNIVERSE
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


def get_portfolio() -> dict:
    snapshots = {row["ticker"]: row for row in latest_market_snapshot()}
    holdings = []
    invested_value = 0.0

    for ticker in UNIVERSE:
        shares = SAMPLE_HOLDINGS.get(ticker, 0)
        price = snapshots.get(ticker, {}).get("close")
        market_value = shares * price if price else 0.0
        invested_value += market_value
        holdings.append(
            {
                "ticker": ticker,
                "shares": shares,
                "price": price,
                "market_value": market_value,
                "target_weight": TARGET_WEIGHTS.get(ticker, 0),
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
