from __future__ import annotations

from datetime import date

from .market_data import data_status
from .portfolio import get_portfolio
from .risk import get_risk_report
from .strategy import get_signals


def get_daily_report(user_id: int) -> dict:
    signals = get_signals()
    risk = get_risk_report(user_id)
    portfolio = get_portfolio(user_id)
    signal_counts: dict[str, int] = {}
    for item in signals:
        signal_counts[item["signal"]] = signal_counts.get(item["signal"], 0) + 1

    return {
        "date": date.today().isoformat(),
        "data": data_status(),
        "portfolio_value": portfolio["total_value"],
        "cash": portfolio["cash"],
        "signal_counts": signal_counts,
        "top_signals": signals,
        "risk_warnings": risk["warnings"],
        "risk_summary": risk["summary"],
    }
