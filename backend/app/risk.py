from __future__ import annotations

from .config import AI_THEME_TICKERS, CRYPTO_TICKERS, HIGH_BETA_TICKERS, RISK_LIMITS
from .portfolio import get_portfolio


def _pct(value: float) -> float:
    return round(value * 100, 2)


def get_risk_report() -> dict:
    portfolio = get_portfolio()
    holdings = portfolio["holdings"]
    total_value = portfolio["total_value"]
    cash_weight = portfolio["cash"] / total_value if total_value else 0

    ai_exposure = sum(h["current_weight"] for h in holdings if h["ticker"] in AI_THEME_TICKERS)
    crypto_exposure = sum(h["current_weight"] for h in holdings if h["ticker"] in CRYPTO_TICKERS)
    warnings = []

    for holding in holdings:
        ticker = holding["ticker"]
        weight = holding["current_weight"]
        if weight > RISK_LIMITS.max_single_stock_weight:
            warnings.append(
                {
                    "level": "high",
                    "ticker": ticker,
                    "message": f"{ticker} weight is {_pct(weight)}%, above the 15% single-stock limit.",
                }
            )
        if ticker in HIGH_BETA_TICKERS and weight > RISK_LIMITS.max_high_beta_stock_weight:
            warnings.append(
                {
                    "level": "high",
                    "ticker": ticker,
                    "message": f"{ticker} is high beta and exceeds the 10% high-beta limit.",
                }
            )

    if crypto_exposure > RISK_LIMITS.max_crypto_weight:
        warnings.append({"level": "high", "message": "Crypto exposure exceeds the 15% limit."})
    if cash_weight < RISK_LIMITS.min_cash_weight:
        warnings.append({"level": "medium", "message": "Cash is below the 10% minimum."})
    if ai_exposure > RISK_LIMITS.max_ai_theme_exposure:
        warnings.append({"level": "medium", "message": "AI theme exposure exceeds the 70% limit."})

    return {
        "limits": RISK_LIMITS.__dict__,
        "summary": {
            "cash_weight": cash_weight,
            "ai_theme_exposure": ai_exposure,
            "crypto_exposure": crypto_exposure,
            "high_beta_exposure": sum(h["current_weight"] for h in holdings if h["ticker"] in HIGH_BETA_TICKERS),
        },
        "warnings": warnings,
    }
