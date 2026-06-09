from __future__ import annotations

from .market_data import latest_market_snapshot


def classify_signal(row: dict) -> str:
    price = row["close"]
    ma50 = row.get("ma50")
    ma200 = row.get("ma200")
    momentum_6m = row.get("momentum_6m")

    if ma200 is not None and price < ma200:
        return "sell"
    if ma200 is not None and momentum_6m is not None and price > ma200 and momentum_6m > 0:
        return "buy"
    if ma50 is not None and price > ma50:
        return "hold"
    if ma50 is not None and price < ma50:
        return "reduce"
    return "hold"


def signal_reason(row: dict, signal: str) -> str:
    if signal == "buy":
        return "Price is above MA200 and 6-month momentum is positive."
    if signal == "sell":
        return "Price is below MA200."
    if signal == "reduce":
        return "Price is below MA50."
    return "Price remains above MA50 or long-term data is still warming up."


def get_signals() -> list[dict]:
    signals = []
    for row in latest_market_snapshot():
        signal = classify_signal(row)
        signals.append(
            {
                "ticker": row["ticker"],
                "date": row["date"],
                "price": row["close"],
                "ma20": row["ma20"],
                "ma50": row["ma50"],
                "ma200": row["ma200"],
                "momentum_3m": row["momentum_3m"],
                "momentum_6m": row["momentum_6m"],
                "volatility": row["volatility"],
                "signal": signal,
                "reason": signal_reason(row, signal),
            }
        )
    return signals
