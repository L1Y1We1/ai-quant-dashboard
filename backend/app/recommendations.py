from __future__ import annotations

from .config import AI_THEME_TICKERS, HIGH_BETA_TICKERS, RISK_LIMITS
from .portfolio import get_portfolio
from .watchlist import get_potential_watchlist


def _theme_exposure(portfolio: dict) -> dict[str, float]:
    exposure: dict[str, float] = {}
    for holding in portfolio["holdings"]:
        theme = holding.get("theme") or "Unclassified"
        exposure[theme] = exposure.get(theme, 0) + holding["current_weight"]
    return exposure


def _risk_check(candidate: dict, portfolio: dict, suggested_weight: float) -> tuple[str, str | None]:
    cash_weight = portfolio["cash"] / portfolio["total_value"] if portfolio["total_value"] else 0
    current_weight = candidate.get("current_weight") or 0
    projected_weight = current_weight + suggested_weight
    ai_exposure = sum(h["current_weight"] for h in portfolio["holdings"] if h["ticker"] in AI_THEME_TICKERS)
    if cash_weight - suggested_weight < RISK_LIMITS.min_cash_weight:
        return "REJECTED", "Rejected because cash weight would fall below 10%"
    if candidate["ticker"] in AI_THEME_TICKERS and ai_exposure + suggested_weight > RISK_LIMITS.max_ai_theme_exposure:
        return "REJECTED", "Rejected because AI theme exposure would exceed 70%"
    if candidate["ticker"] in HIGH_BETA_TICKERS and projected_weight > RISK_LIMITS.max_high_beta_stock_weight:
        return "REJECTED", "Rejected because high beta stock weight would exceed 10%"
    if projected_weight > RISK_LIMITS.max_single_stock_weight:
        return "REJECTED", "Rejected because single stock weight would exceed 15%"
    return "PASS", None


def get_buy_recommendations(user_id: int) -> dict:
    portfolio = get_portfolio(user_id)
    watchlist = get_potential_watchlist(user_id, portfolio)
    exposures = _theme_exposure(portfolio)
    missing_themes = {item["theme"] for item in watchlist["potential_stocks"] if exposures.get(item["theme"], 0) == 0}
    items = []

    for candidate in watchlist["potential_stocks"]:
        score = candidate["score"] if candidate["score"] is not None else -99
        if score <= 0:
            continue
        suggested_weight = 0.03
        if score >= 5:
            suggested_weight = 0.05
        if candidate["ticker"] in HIGH_BETA_TICKERS:
            suggested_weight = min(suggested_weight, 0.03)

        status, reject_reason = _risk_check(candidate, portfolio, suggested_weight)
        trend_ok = candidate["current_price"] and candidate["ma200"] and candidate["current_price"] > candidate["ma200"] and (candidate["momentum_6m"] or 0) > 0
        reasons = []
        if candidate["theme"] in missing_themes:
            reasons.append(f"High score candidate and portfolio has no {candidate['theme']} exposure")
        elif candidate.get("current_weight", 0) < candidate.get("target_weight", 0):
            reasons.append(f"{candidate['ticker']} is under target weight and passes score filter")
        else:
            reasons.append("High score candidate improves AI infrastructure breadth")
        if trend_ok:
            reasons.append(f"{candidate['ticker']} trades above MA200 with positive 6M momentum")
        if candidate["ticker"] in HIGH_BETA_TICKERS:
            reasons.append("Strong momentum but high beta, use small starter position")
        if reject_reason:
            reasons = [reject_reason]

        items.append(
            {
                "ticker": candidate["ticker"],
                "company_name": candidate["company_name"],
                "score": score,
                "theme": candidate["theme"],
                "reason": ". ".join(reasons),
                "suggested_action": "Do not add" if status == "REJECTED" else "Consider small starter position",
                "suggested_weight": 0 if status == "REJECTED" else suggested_weight,
                "risk_check_status": status,
            }
        )

    return {
        "portfolio_total_value": portfolio["total_value"],
        "cash_weight": portfolio["cash"] / portfolio["total_value"] if portfolio["total_value"] else 0,
        "theme_exposure": exposures,
        "recommendations": sorted(items, key=lambda item: (item["risk_check_status"] != "PASS", -item["score"], -item["suggested_weight"])),
    }
