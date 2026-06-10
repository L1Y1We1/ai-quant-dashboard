from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .auth import create_token, get_current_user, hash_password, public_user, verify_password
from .config import UNIVERSE
from .database import get_connection, init_db
from .market_data import data_status, get_price_history, latest_market_snapshot, refresh_prices
from .portfolio import get_portfolio, seed_default_portfolio
from .report import get_daily_report
from .risk import get_risk_report
from .strategy import classify_signal, get_signals
from .virtual_portfolio import get_virtual_portfolio, normalize_ticker, place_virtual_trade
from .watchlist import build_candidate_item, candidate_lookup, candidate_tickers, get_potential_watchlist


app = FastAPI(title="AI Infrastructure Quant Platform", version="0.1.0")
STATIC_DIR = Path(__file__).parent / "static"


class VirtualTradeRequest(BaseModel):
    ticker: str = Field(..., min_length=1)
    side: str
    quantity: float = Field(..., gt=0)
    price: float | None = None
    notes: str | None = None


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class HoldingRequest(BaseModel):
    ticker: str = Field(..., min_length=1)
    shares: float = Field(..., ge=0)
    target_weight: float = Field(0, ge=0)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/auth/register")
def register(payload: RegisterRequest) -> dict:
    username = payload.username.strip()
    email = payload.email.strip().lower()
    if not username or not email:
        raise HTTPException(status_code=400, detail="Username and email are required")
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email),
        ).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Username or email already exists")
        cursor = conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, hash_password(payload.password)),
        )
        user_id = cursor.lastrowid
        conn.execute(
            "INSERT OR IGNORE INTO virtual_accounts (user_id, starting_cash, cash) VALUES (?, 100000.0, 100000.0)",
            (user_id,),
        )
        conn.commit()
    seed_default_portfolio(user_id)
    user = {"id": user_id, "username": username, "email": email, "created_at": None}
    return {"token": create_token(user), "user": user}


@app.post("/auth/login")
def login(payload: LoginRequest) -> dict:
    identity = payload.username_or_email.strip().lower()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, username, email, password_hash, created_at
            FROM users
            WHERE lower(username) = ? OR lower(email) = ?
            """,
            (identity, identity),
        ).fetchone()
    if not row or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username/email or password")
    user = public_user(row)
    return {"token": create_token(user), "user": user}


@app.post("/auth/logout")
def logout() -> dict:
    return {"status": "ok"}


@app.get("/auth/me")
def me(user: dict = Depends(get_current_user)) -> dict:
    return {"user": user}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "universe": UNIVERSE, "candidate_universe": candidate_tickers(), "data": data_status()}


@app.post("/data/refresh")
def refresh_data() -> dict:
    return {"saved": refresh_prices(), "status": data_status()}


@app.get("/prices/{ticker}")
def prices(ticker: str, limit: int = 260) -> dict:
    ticker = ticker.upper()
    if ticker not in UNIVERSE:
        raise HTTPException(status_code=404, detail=f"{ticker} is not in the tracked universe.")
    rows = get_price_history(ticker, limit)
    return {"ticker": ticker, "count": len(rows), "prices": rows}


@app.get("/signals")
def signals() -> dict:
    return {"signals": get_signals()}


@app.get("/portfolio")
def portfolio(user: dict = Depends(get_current_user)) -> dict:
    return get_portfolio(user["id"])


@app.post("/portfolio/holdings")
def upsert_holding(holding: HoldingRequest, user: dict = Depends(get_current_user)) -> dict:
    ticker = holding.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO portfolio_holdings (user_id, ticker, shares, target_weight)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, ticker)
            DO UPDATE SET shares = excluded.shares, target_weight = excluded.target_weight, updated_at = CURRENT_TIMESTAMP
            """,
            (user["id"], ticker, holding.shares, holding.target_weight),
        )
        conn.commit()
    return get_portfolio(user["id"])


@app.delete("/portfolio/holdings/{ticker}")
def delete_holding(ticker: str, user: dict = Depends(get_current_user)) -> dict:
    with get_connection() as conn:
        conn.execute("DELETE FROM portfolio_holdings WHERE user_id = ? AND ticker = ?", (user["id"], ticker.strip().upper()))
        conn.commit()
    return get_portfolio(user["id"])


@app.get("/risk")
def risk(user: dict = Depends(get_current_user)) -> dict:
    return get_risk_report(user["id"])


@app.get("/report/daily")
def daily_report(user: dict = Depends(get_current_user)) -> dict:
    return get_daily_report(user["id"])


@app.get("/watchlist/potential")
def potential_watchlist(user: dict = Depends(get_current_user)) -> dict:
    user_portfolio = get_portfolio(user["id"])
    return get_potential_watchlist(user["id"], user_portfolio)


@app.get("/virtual-portfolio")
def virtual_portfolio(user: dict = Depends(get_current_user)) -> dict:
    return get_virtual_portfolio(user["id"])


@app.post("/virtual-portfolio/trade")
def virtual_trade(trade: VirtualTradeRequest, user: dict = Depends(get_current_user)) -> dict:
    try:
        return place_virtual_trade(user["id"], trade.ticker, trade.side, trade.quantity, trade.notes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/ticker/{ticker}/lookup")
def ticker_lookup(ticker: str) -> dict:
    try:
        ticker = normalize_ticker(ticker)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    rows = latest_market_snapshot([ticker])
    if not rows:
        raise HTTPException(status_code=404, detail="Invalid ticker or no market data found.")
    row = rows[0]
    candidates = candidate_lookup()
    candidate = candidates.get(ticker)
    candidate_item = build_candidate_item(candidate, row) if candidate else None
    return {
        "ticker": ticker,
        "company_name": candidate.company_name if candidate else ticker,
        "current_price": row["close"],
        "signal": classify_signal(row),
        "score": candidate_item["score"] if candidate_item else None,
        "candidate_rating": candidate_item["candidate_rating"] if candidate_item else None,
    }
