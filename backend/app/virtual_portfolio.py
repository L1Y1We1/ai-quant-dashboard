from __future__ import annotations

import re
from datetime import date, datetime

from .database import get_connection
from .market_data import latest_market_snapshot


def _current_price(ticker: str) -> float | None:
    rows = latest_market_snapshot([ticker.upper()])
    if not rows:
        return None
    return rows[0]["close"]


TICKER_RE = re.compile(r"^[A-Z0-9.-]+$")


def normalize_ticker(ticker: str) -> str:
    normalized = ticker.strip().upper()
    if not normalized or not TICKER_RE.match(normalized):
        raise ValueError("Invalid ticker or no market data found.")
    return normalized


def ensure_virtual_account(user_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO virtual_accounts (user_id, starting_cash, cash)
            VALUES (?, 100000.0, 100000.0)
            """,
            (user_id,),
        )
        conn.commit()


def _positions_and_realized(user_id: int) -> tuple[dict[str, dict], float]:
    lots: dict[str, dict] = {}
    realized_pnl = 0.0
    with get_connection() as conn:
        trades = conn.execute(
            """
            SELECT ticker, side, shares, price, notional, created_at
            FROM virtual_trades
            WHERE user_id = ?
            ORDER BY id
            """,
            (user_id,),
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
            cost_removed = position["cost_basis"] * sell_ratio
            realized_pnl += trade["notional"] - cost_removed
            position["cost_basis"] *= 1 - sell_ratio
            position["shares"] -= trade["shares"]

    return {ticker: pos for ticker, pos in lots.items() if pos["shares"] > 0.000001}, realized_pnl


def _position_lots(user_id: int) -> dict[str, dict]:
    positions, _realized_pnl = _positions_and_realized(user_id)
    return positions


def get_virtual_portfolio(user_id: int) -> dict:
    ensure_virtual_account(user_id)
    with get_connection() as conn:
        account = conn.execute("SELECT starting_cash, cash FROM virtual_accounts WHERE user_id = ?", (user_id,)).fetchone()
        trades = conn.execute(
            """
            SELECT id, ticker, side, shares, price, notional, notes, created_at
            FROM virtual_trades
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 30
            """,
            (user_id,),
        ).fetchall()

    positions = []
    total_market_value = 0.0
    lots, realized_pnl = _positions_and_realized(user_id)
    unrealized_pnl_total = 0.0
    for position in lots.values():
        price = _current_price(position["ticker"])
        market_value = position["shares"] * price if price is not None else 0.0
        avg_cost = position["cost_basis"] / position["shares"] if position["shares"] else 0.0
        unrealized_pnl = market_value - position["cost_basis"]
        unrealized_pnl_total += unrealized_pnl
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
        "realized_pnl": realized_pnl,
        "unrealized_pnl": unrealized_pnl_total,
        "positions": sorted(positions, key=lambda item: item["market_value"], reverse=True),
        "recent_trades": [dict(row) for row in trades],
    }


def get_virtual_performance(user_id: int) -> dict:
    portfolio = get_virtual_portfolio(user_id)
    with get_connection() as conn:
        dates = conn.execute(
            """
            SELECT MIN(created_at) AS first_trade_date, MAX(created_at) AS last_trade_date
            FROM virtual_trades
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
    first_trade_date = dates["first_trade_date"] if dates else None
    last_trade_date = dates["last_trade_date"] if dates else None
    active_days = 0
    if first_trade_date:
        first_date = datetime.fromisoformat(first_trade_date.split(" ")[0]).date()
        active_days = max((date.today() - first_date).days, 1)
    total_profit = portfolio["total_value"] - portfolio["starting_cash"]
    return {
        "starting_virtual_cash": portfolio["starting_cash"],
        "current_virtual_equity": portfolio["total_value"],
        "total_profit": total_profit,
        "total_profit_pct": total_profit / portfolio["starting_cash"] if portfolio["starting_cash"] else 0,
        "realized_pnl": portfolio["realized_pnl"],
        "unrealized_pnl": portfolio["unrealized_pnl"],
        "first_trade_date": first_trade_date,
        "last_trade_date": last_trade_date,
        "active_days": active_days,
        "profit_per_day": total_profit / active_days if active_days else 0,
    }


def get_virtual_leaderboard(sort_by: str = "total_profit_pct") -> dict:
    allowed_sorts = {"total_profit", "total_profit_pct", "profit_per_day", "active_days"}
    sort_key = sort_by if sort_by in allowed_sorts else "total_profit_pct"
    with get_connection() as conn:
        users = conn.execute("SELECT id, username FROM users ORDER BY id").fetchall()

    rows = []
    for user in users:
        ensure_virtual_account(user["id"])
        performance = get_virtual_performance(user["id"])
        rows.append({"username": user["username"], **performance})

    rows.sort(key=lambda item: (item[sort_key], item["active_days"]), reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return {"sort_by": sort_key, "leaderboard": rows}


def place_virtual_trade(user_id: int, ticker: str, side: str, quantity: float, notes: str | None = None) -> dict:
    ensure_virtual_account(user_id)
    ticker = normalize_ticker(ticker)
    side = side.lower()
    if side not in {"buy", "sell"}:
        raise ValueError("side must be buy or sell")
    if quantity <= 0:
        raise ValueError("quantity must be greater than 0")

    price = _current_price(ticker)
    if price is None:
        raise ValueError("Invalid ticker or no market data found.")
    notional = price * quantity

    with get_connection() as conn:
        account = conn.execute("SELECT cash FROM virtual_accounts WHERE user_id = ?", (user_id,)).fetchone()
        cash = account["cash"]
        positions = _position_lots(user_id)
        owned_shares = positions.get(ticker, {}).get("shares", 0.0)

        if side == "buy" and notional > cash:
            raise ValueError("Not enough virtual cash for this buy order.")
        if side == "sell" and quantity > owned_shares:
            raise ValueError("Not enough virtual shares for this sell order.")

        new_cash = cash - notional if side == "buy" else cash + notional
        conn.execute(
            """
            INSERT INTO virtual_trades (user_id, ticker, side, shares, price, notional, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, ticker, side, quantity, price, notional, notes),
        )
        conn.execute(
            """
            UPDATE virtual_accounts
            SET cash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (new_cash, user_id),
        )
        conn.commit()

    return {
        "ticker": ticker,
        "side": side,
        "quantity": quantity,
        "price": price,
        "notional": notional,
        "portfolio": get_virtual_portfolio(user_id),
    }
