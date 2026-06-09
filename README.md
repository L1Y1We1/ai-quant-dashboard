# AI Infrastructure Quant Dashboard

A personal stock quant platform for tracking an AI infrastructure themed universe, generating trend/momentum signals, and surfacing portfolio risk warnings.

Universe:

`QQQ, NVDA, AVGO, TSM, MU, MRVL, VRT, ANET, AMZN, PLTR, TSLA`

## Stack

- Backend: Python, FastAPI, pandas, yfinance, SQLite
- Frontend: React, Vite, Tailwind CSS

## Project Layout

```text
backend/
  app/
    main.py              FastAPI app and routes
    config.py            Universe and risk limits
    database.py          SQLite connection and schema
    market_data.py       yfinance download and price queries
    indicators.py        Moving averages, momentum, volatility
    strategy.py          Buy/hold/reduce/sell signal logic
    risk.py              Portfolio risk checks
    portfolio.py         Holdings and target weights
    report.py            Daily report generator
frontend/
  src/
    App.jsx
    api.js
    pages/
    components/
```

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The app initializes SQLite at `backend/quant.db`.

Refresh market data:

```bash
curl -X POST http://localhost:8000/data/refresh
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL, usually `http://localhost:5173`.

If your backend runs somewhere else:

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## API Endpoints

- `GET /prices/{ticker}` - daily price history with indicators
- `POST /data/refresh` - download daily price history from yfinance
- `GET /signals` - current strategy signals for the universe
- `GET /portfolio` - holdings, prices, values, and target weights
- `GET /risk` - risk rules, exposure summary, and warnings
- `GET /report/daily` - daily portfolio and signal report

## Deploy Online

This project includes a root `Dockerfile` for deploying the whole app as one FastAPI service. The UI is served at `/`, so you do not need a separate frontend host.

Recommended quick path:

1. Push the project to GitHub.
2. Create a Docker-based web service on Render, Railway, or Fly.io.
3. Set `QUANT_DB_PATH=/data/quant.db`.
4. Add a persistent disk or volume mounted at `/data` if you want SQLite data to survive redeploys.
5. Deploy and open the generated public URL.

See `DEPLOYMENT.md` for platform-specific notes.

## Strategy Rules

- Buy: price above 200-day moving average and 6-month momentum is positive
- Hold: price above 50-day moving average
- Reduce: price below 50-day moving average
- Sell: price below 200-day moving average

Sell has priority over reduce, and buy has priority over hold when the long-term trend and momentum agree.

## Risk Rules

- Max single stock weight: 15%
- Max high beta stock weight: 10%
- Max crypto weight: 15%
- Min cash weight: 10%
- Max AI theme exposure: 70%

The sample portfolio is intentionally illustrative. Update `backend/app/portfolio.py` or add your own persistence layer for real holdings.
