from __future__ import annotations

from dataclasses import dataclass

from .market_data import latest_market_snapshot
from .portfolio import get_current_holding_tickers
from .strategy import classify_signal


@dataclass(frozen=True)
class CandidateStock:
    ticker: str
    company_name: str
    theme: str


CANDIDATE_UNIVERSE = [
    CandidateStock("NVDA", "NVIDIA", "Core AI Infra"),
    CandidateStock("AVGO", "Broadcom", "Core AI Infra"),
    CandidateStock("TSM", "Taiwan Semiconductor Manufacturing", "Core AI Infra"),
    CandidateStock("MU", "Micron Technology", "Core AI Infra"),
    CandidateStock("MRVL", "Marvell Technology", "AI Networking"),
    CandidateStock("ANET", "Arista Networks", "AI Networking"),
    CandidateStock("ALAB", "Astera Labs", "AI Networking"),
    CandidateStock("CRDO", "Credo Technology", "AI Networking"),
    CandidateStock("VRT", "Vertiv", "Power / Cooling"),
    CandidateStock("ETN", "Eaton", "Power / Cooling"),
    CandidateStock("NVT", "nVent Electric", "Power / Cooling"),
    CandidateStock("MSFT", "Microsoft", "Hyperscaler / AI Software"),
    CandidateStock("AMZN", "Amazon", "Hyperscaler / AI Software"),
    CandidateStock("GOOGL", "Alphabet", "Hyperscaler / AI Software"),
    CandidateStock("META", "Meta Platforms", "Hyperscaler / AI Software"),
    CandidateStock("PLTR", "Palantir", "Hyperscaler / AI Software"),
    CandidateStock("NBIS", "Nebius Group", "Speculative AI"),
    CandidateStock("RXRX", "Recursion Pharmaceuticals", "Speculative AI"),
    CandidateStock("SOUN", "SoundHound AI", "Speculative AI"),
]


def candidate_tickers() -> list[str]:
    return [candidate.ticker for candidate in CANDIDATE_UNIVERSE]


def potential_candidate_tickers() -> list[str]:
    held = get_current_holding_tickers()
    return [candidate.ticker for candidate in CANDIDATE_UNIVERSE if candidate.ticker not in held]


def _score_candidate(candidate: CandidateStock, row: dict) -> tuple[int, list[str]]:
    score = 0
    reasons = []
    price = row.get("close")
    ma50 = row.get("ma50")
    ma200 = row.get("ma200")
    momentum_3m = row.get("momentum_3m")
    momentum_6m = row.get("momentum_6m")
    volatility = row.get("volatility")

    if price is not None and ma200 is not None and price > ma200:
        score += 2
        reasons.append("Price is above MA200, confirming the long-term trend.")
    else:
        score -= 2
        reasons.append("Price is not above MA200, so long-term trend confirmation is weak.")

    if price is not None and ma50 is not None and price > ma50:
        score += 1
        reasons.append("Price is above MA50, showing medium-term support.")
    else:
        score -= 1
        reasons.append("Price is below MA50, so medium-term trend needs recovery.")

    if momentum_6m is not None and momentum_6m > 0:
        score += 2
        reasons.append("6-month momentum is positive.")
    else:
        score -= 2
        reasons.append("6-month momentum is not positive.")

    if momentum_3m is not None and momentum_3m > 0:
        score += 1
        reasons.append("3-month momentum is positive.")
    else:
        score -= 1
        reasons.append("3-month momentum is not positive.")

    if candidate.theme in {"Core AI Infra", "AI Networking", "Power / Cooling"}:
        score += 2
        reasons.append(f"{candidate.theme} receives a theme quality bonus.")
    if candidate.theme == "Speculative AI":
        score -= 1
        reasons.append("Speculative AI receives a quality discount.")

    if volatility is not None and volatility > 0.60:
        score -= 1
        reasons.append("Annualized volatility is above 60%.")
    if volatility is not None and volatility > 0.90:
        score -= 2
        reasons.append("Annualized volatility is above 90%.")

    if price is not None and ma50 is not None and price > ma50 * 1.20:
        score -= 1
        reasons.append("Price is more than 20% above MA50.")
    if price is not None and ma200 is not None and price > ma200 * 1.35:
        score -= 1
        reasons.append("Price is more than 35% above MA200.")

    return score, reasons


def _rating(score: int) -> str:
    if score >= 5:
        return "STRONG CANDIDATE"
    if 3 <= score <= 4:
        return "WATCH CANDIDATE"
    if 1 <= score <= 2:
        return "EARLY WATCH"
    return "AVOID / WAIT"


def _suggested_action(rating: str) -> str:
    return {
        "STRONG CANDIDATE": "Consider small starter position",
        "WATCH CANDIDATE": "Wait for better entry or confirmation",
        "EARLY WATCH": "Monitor only",
        "AVOID / WAIT": "Avoid for now",
    }[rating]


def _entry_zone(row: dict) -> str:
    price = row.get("close")
    ma50 = row.get("ma50")
    ma200 = row.get("ma200")

    if price is None or ma50 is None or ma200 is None:
        return "Insufficient data"
    if price < ma200:
        return "Below MA200, avoid"
    if price < ma50 and price > ma200:
        return "Above MA200 but below MA50, wait for recovery"
    if price > ma50 * 1.20:
        return "Overextended, wait for pullback"
    if price > ma50 * 1.05 and price <= ma50 * 1.20:
        return "Extended but acceptable"
    if price > ma50 and price <= ma50 * 1.05:
        return "Near MA50 support"
    return "Wait for clearer setup"


def get_potential_watchlist() -> dict:
    held = get_current_holding_tickers()
    candidates = [candidate for candidate in CANDIDATE_UNIVERSE if candidate.ticker not in held]
    snapshots = {row["ticker"]: row for row in latest_market_snapshot([candidate.ticker for candidate in candidates])}
    items = []

    for candidate in candidates:
        row = snapshots.get(candidate.ticker)
        if not row:
            items.append(
                {
                    "ticker": candidate.ticker,
                    "company_name": candidate.company_name,
                    "theme": candidate.theme,
                    "current_price": None,
                    "ma50": None,
                    "ma200": None,
                    "momentum_3m": None,
                    "momentum_6m": None,
                    "annualized_volatility": None,
                    "score": -99,
                    "candidate_rating": "AVOID / WAIT",
                    "suggested_action": "Avoid for now",
                    "entry_zone": "Insufficient data",
                    "signal": "unknown",
                    "reason": "No downloaded market data yet. Refresh market data to score this candidate.",
                }
            )
            continue

        score, reasons = _score_candidate(candidate, row)
        rating = _rating(score)
        items.append(
            {
                "ticker": candidate.ticker,
                "company_name": candidate.company_name,
                "theme": candidate.theme,
                "current_price": row["close"],
                "ma50": row["ma50"],
                "ma200": row["ma200"],
                "momentum_3m": row["momentum_3m"],
                "momentum_6m": row["momentum_6m"],
                "annualized_volatility": row["volatility"],
                "score": score,
                "candidate_rating": rating,
                "suggested_action": _suggested_action(rating),
                "entry_zone": _entry_zone(row),
                "signal": classify_signal(row),
                "reason": " ".join(reasons),
            }
        )

    return {
        "excluded_current_holdings": sorted(held),
        "candidate_universe": [candidate.__dict__ for candidate in CANDIDATE_UNIVERSE],
        "potential_stocks": sorted(items, key=lambda item: item["score"], reverse=True),
    }
