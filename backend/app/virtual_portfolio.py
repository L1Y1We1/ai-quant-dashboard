from __future__ import annotations

from .database import get_connection
from .market_data import latest_market_snapshot


def _current_price(ticker: str) -> float | None:
    rows = latest_market_snapshot([ticker.upper()])
    if not rows:
        return None
    return rows[0]["close"]


def _position_lots() -> dict[str, dict]:
    lots: dict[str, dict] = {}
    with get_connection() as conn:
        trades = conn.execute(
            """
            SELECT ticker, side, shares, price, notional, created_at
            FROM virtual_trades
            ORDER BY id
            """
        ).fetchall()

    for trade in trades:
        ticker = trade["ticker"]
        lots.setdefault(ticker, {"ticker": ticker, "shares": 0.0, "cost_basis": 0.0})
        position = lots[ticker]
        if trade["side"] == "buy":
            position["shares"] += trade["shares"]
            position["cost_basis"] += trade["notional"]
        else:
            if position["shares"] <= 0:
                continue
            sell_ratio = min(trade["shares"], position["shares"]) / position["shares"]
            position["cost_basis"] *= 1 - sell_ratio
            position["shares"] -= trade["shares"]

    return {ticker: pos for ticker, pos in lots.items() if pos["shares"] > 0.000001}


def get_virtual_portfolio() -> dict:
    with get_connection() as conn:
        account = conn.execute("SELECT starting_cash, cash FROM virtual_account WHERE id = 1").fetchone()
        trades = conn.execute(
            """
            SELECT id, ticker, side, shares, price, notional, created_at
            FROM virtual_trades
            ORDER BY id DESC
            LIMIT 30
            """
        ).fetchall()

    positions = []
    total_market_value = 0.0
    for position in _position_lots().values():
        price = _current_price(position["ticker"])
        market_value = position["shares"] * price if price is not None else 0.0
        avg_cost = position["cost_basis"] / position["shares"] if position["shares"] else 0.0
        unrealized_pnl = market_value - position["cost_basis"]
        total_market_value += market_value
        positions.append(
            {
                "ticker": position["ticker"],
                "shares": position["shares"],
                "avg_cost": avg_cost,
                "current_price": price,
                "market_value": market_value,
                "cost_basis": position["cost_basis"],
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl / position["cost_basis"] if position["cost_basis"] else 0,
            }
        )

    total_value = account["cash"] + total_market_value
    for position in positions:
        position["weight"] = position["market_value"] / total_value if total_value else 0

    return {
        "starting_cash": account["starting_cash"],
        "cash": account["cash"],
        "total_market_value": total_market_value,
        "total_value": total_value,
        "total_return": total_value - account["starting_cash"],
        "total_return_pct": (total_value - account["starting_cash"]) / account["starting_cash"] if account["starting_cash"] else 0,
        "positions": sorted(positions, key=lambda item: item["market_value"], reverse=True),
        "recent_trades": [dict(row) for row in trades],
    }


def place_virtual_trade(ticker: str, side: str, shares: float) -> dict:
    ticker = ticker.upper()
    side = side.lower()
    if side not in {"buy", "sell"}:
        raise ValueError("side must be buy or sell")
    if shares <= 0:
        raise ValueError("shares must be greater than 0")

    price = _current_price(ticker)
    if price is None:
        raise ValueError(f"No market data for {ticker}. Refresh data before trading.")
    notional = price * shares

    with get_connection() as conn:
        account = conn.execute("SELECT cash FROM virtual_account WHERE id = 1").fetchone()
        cash = account["cash"]
        positions = _position_lots()
        owned_shares = positions.get(ticker, {}).get("shares", 0.0)

        if side == "buy" and notional > cash:
            raise ValueError("Not enough virtual cash for this buy order.")
        if side == "sell" and shares > owned_shares:
            raise ValueError("Not enough virtual shares for this sell order.")

        new_cash = cash - notional if side == "buy" else cash + notional
        conn.execute(
            """
            INSERT INTO virtual_trades (ticker, side, shares, price, notional)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ticker, side, shares, price, notional),
        )
        conn.execute(
            """
            UPDATE virtual_account
            SET cash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (new_cash,),
        )
        conn.commit()

    return {
        "ticker": ticker,
        "side": side,
        "shares": shares,
        "price": price,
        "notional": notional,
        "portfolio": get_virtual_portfolio(),
    }
