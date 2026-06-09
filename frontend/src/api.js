const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json();
}

export const api = {
  health: () => request("/health"),
  refresh: () => request("/data/refresh", { method: "POST" }),
  prices: (ticker) => request(`/prices/${ticker}`),
  potentialWatchlist: () => request("/watchlist/potential"),
  signals: () => request("/signals"),
  portfolio: () => request("/portfolio"),
  risk: () => request("/risk"),
  dailyReport: () => request("/report/daily"),
  virtualPortfolio: () => request("/virtual-portfolio"),
  virtualTrade: (trade) => request("/virtual-portfolio/trade", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(trade)
  })
};

export const universe = ["QQQ", "NVDA", "AVGO", "TSM", "MU", "MRVL", "VRT", "ANET", "AMZN", "PLTR", "TSLA"];
