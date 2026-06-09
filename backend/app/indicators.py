from __future__ import annotations

import pandas as pd


def add_indicators(prices: pd.DataFrame) -> pd.DataFrame:
    df = prices.sort_values("date").copy()
    close = df["close"]
    returns = close.pct_change()

    df["ma20"] = close.rolling(20).mean()
    df["ma50"] = close.rolling(50).mean()
    df["ma200"] = close.rolling(200).mean()
    df["momentum_3m"] = close.pct_change(63)
    df["momentum_6m"] = close.pct_change(126)
    df["volatility"] = returns.rolling(20).std() * (252**0.5)
    return df
