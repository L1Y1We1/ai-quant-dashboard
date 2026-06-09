from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import UNIVERSE
from .database import init_db
from .market_data import data_status, get_price_history, refresh_prices
from .portfolio import get_portfolio
from .report import get_daily_report
from .risk import get_risk_report
from .strategy import get_signals


app = FastAPI(title="AI Infrastructure Quant Platform", version="0.1.0")
STATIC_DIR = Path(__file__).parent / "static"

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


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "universe": UNIVERSE, "data": data_status()}


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
def portfolio() -> dict:
    return get_portfolio()


@app.get("/risk")
def risk() -> dict:
    return get_risk_report()


@app.get("/report/daily")
def daily_report() -> dict:
    return get_daily_report()
