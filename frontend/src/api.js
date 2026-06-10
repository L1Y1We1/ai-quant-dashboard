const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options) {
  const token = localStorage.getItem("quant_auth_token");
  const headers = { ...(options?.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    let detail = `API request failed: ${response.status}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return response.json();
}

export const api = {
  health: () => request("/health"),
  register: (payload) => request("/auth/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }),
  login: (payload) => request("/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }),
  me: () => request("/auth/me"),
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
  }),
  tickerLookup: (ticker) => request(`/ticker/${ticker}/lookup`)
};

export const universe = ["QQQ", "NVDA", "AVGO", "TSM", "MU", "MRVL", "VRT", "ANET", "AMZN", "PLTR", "TSLA"];
