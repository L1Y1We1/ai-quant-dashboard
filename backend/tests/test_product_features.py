from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path


TEMP_DIR = tempfile.TemporaryDirectory()
os.environ["QUANT_DB_PATH"] = str(Path(TEMP_DIR.name) / "test_quant.db")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.database import get_connection, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.market_data import refresh_universe  # noqa: E402


def seed_prices() -> None:
    tickers = {
        "NVDA": (120, 110, 90, 0.12, 0.28, 0.45),
        "MSFT": (460, 440, 400, 0.05, 0.14, 0.22),
        "MRVL": (80, 76, 70, 0.08, 0.20, 0.55),
        "ALAB": (70, 68, 55, 0.11, 0.33, 0.72),
        "QQQ": (520, 510, 470, 0.04, 0.10, 0.18),
    }
    with get_connection() as conn:
        for ticker, values in tickers.items():
            close, ma50, ma200, momentum_3m, momentum_6m, volatility = values
            conn.execute(
                """
                INSERT OR REPLACE INTO prices (
                    ticker, date, open, high, low, close, adj_close, volume,
                    ma20, ma50, ma200, momentum_3m, momentum_6m, volatility
                )
                VALUES (?, '2026-06-10', ?, ?, ?, ?, ?, 1000000, ?, ?, ?, ?, ?, ?)
                """,
                (ticker, close, close, close, close, close, ma50, ma50, ma200, momentum_3m, momentum_6m, volatility),
            )
        conn.commit()


class ProductFeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        init_db()
        seed_prices()
        cls.client = TestClient(app)

    def auth_headers(self, username: str, email: str) -> dict[str, str]:
        response = self.client.post("/auth/register", json={"username": username, "email": email, "password": "secret123"})
        self.assertEqual(response.status_code, 200, response.text)
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}

    def test_auth_portfolio_potential_and_recommendations_are_user_specific(self) -> None:
        user_a = self.auth_headers("alice", "alice@example.com")
        user_b = self.auth_headers("bob", "bob@example.com")

        response = self.client.post(
            "/portfolio/holdings",
            headers=user_a,
            json={
                "ticker": "MSFT",
                "shares": 2,
                "average_cost": 430,
                "target_weight": 0.05,
                "theme": "Hyperscaler / AI Software",
                "is_high_beta": False,
                "notes": "test holding",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)

        portfolio_a = self.client.get("/portfolio", headers=user_a).json()
        portfolio_b = self.client.get("/portfolio", headers=user_b).json()
        self.assertIn("MSFT", {item["ticker"] for item in portfolio_a["holdings"]})
        self.assertNotIn("MSFT", {item["ticker"] for item in portfolio_b["holdings"]})

        potential_a = self.client.get("/watchlist/potential", headers=user_a).json()["potential_stocks"]
        msft = next(item for item in potential_a if item["ticker"] == "MSFT")
        self.assertTrue(msft["is_current_holding"])
        self.assertGreater(msft["current_weight"], 0)

        recommendations = self.client.get("/recommendations/buy", headers=user_a)
        self.assertEqual(recommendations.status_code, 200, recommendations.text)
        self.assertIn("recommendations", recommendations.json())

    def test_virtual_account_trade_performance_and_leaderboard(self) -> None:
        user = self.auth_headers("carol", "carol@example.com")
        account = self.client.get("/virtual/account", headers=user)
        self.assertEqual(account.status_code, 200, account.text)
        self.assertEqual(account.json()["starting_cash"], 100000.0)

        trade = self.client.post("/virtual/trade", headers=user, json={"ticker": "MSFT", "side": "BUY", "quantity": 1, "notes": "starter"})
        self.assertEqual(trade.status_code, 200, trade.text)

        performance = self.client.get("/virtual/performance", headers=user).json()
        self.assertEqual(performance["starting_virtual_cash"], 100000.0)
        self.assertGreaterEqual(performance["active_days"], 1)

        leaderboard = self.client.get("/virtual/leaderboard").json()["leaderboard"]
        self.assertTrue(any(row["username"] == "carol" for row in leaderboard))

    def test_refresh_universe_includes_user_added_holdings(self) -> None:
        user = self.auth_headers("dana", "dana@example.com")
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO portfolio_holdings (user_id, ticker, shares, target_weight)
                VALUES ((SELECT id FROM users WHERE username = 'dana'), 'DDOG', 3, 0.04)
                """
            )
            conn.commit()

        self.assertIn("DDOG", refresh_universe())


if __name__ == "__main__":
    unittest.main()
