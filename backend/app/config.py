from dataclasses import dataclass


UNIVERSE = ["QQQ", "NVDA", "AVGO", "TSM", "MU", "MRVL", "VRT", "ANET", "AMZN", "PLTR", "TSLA"]

AI_THEME_TICKERS = {"NVDA", "AVGO", "TSM", "MU", "MRVL", "VRT", "ANET", "AMZN", "PLTR", "TSLA"}
HIGH_BETA_TICKERS = {"NVDA", "MU", "MRVL", "VRT", "PLTR", "TSLA"}
CRYPTO_TICKERS: set[str] = set()


@dataclass(frozen=True)
class RiskLimits:
    max_single_stock_weight: float = 0.15
    max_high_beta_stock_weight: float = 0.10
    max_crypto_weight: float = 0.15
    min_cash_weight: float = 0.10
    max_ai_theme_exposure: float = 0.70


RISK_LIMITS = RiskLimits()
