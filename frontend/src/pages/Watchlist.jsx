import { useState } from "react";
import { api, universe } from "../api";
import { currency, percent, useApi } from "../hooks";
import { ErrorState, Loading } from "../components/DataState";
import SignalPill from "../components/SignalPill";
import { getTickerColor } from "../tickerColor";

const ratingStyles = {
  "STRONG CANDIDATE": "border-emerald-200 bg-emerald-100 text-emerald-800",
  "WATCH CANDIDATE": "border-blue-200 bg-blue-100 text-blue-800",
  "EARLY WATCH": "border-amber-200 bg-amber-100 text-amber-800",
  "AVOID / WAIT": "border-red-200 bg-red-100 text-red-800"
};

function RatingPill({ rating }) {
  return <span className={`inline-flex min-w-36 justify-center border px-2 py-1 text-xs font-semibold ${ratingStyles[rating] || ratingStyles["AVOID / WAIT"]}`}>{rating}</span>;
}

export default function Watchlist() {
  const [ticker, setTicker] = useState("NVDA");
  const [tab, setTab] = useState("prices");
  const [filters, setFilters] = useState({ theme: "All", rating: "All", signal: "All", volatility: "All" });
  const { data, error, loading } = useApi(() => tab === "prices" ? api.prices(ticker) : api.potentialWatchlist(), [ticker, tab]);
  const last = data?.prices?.[data.prices.length - 1];

  const potential = data?.potential_stocks || [];
  const themes = ["All", ...new Set(potential.map((item) => item.theme))];
  const ratings = ["All", "STRONG CANDIDATE", "WATCH CANDIDATE", "EARLY WATCH", "AVOID / WAIT"];
  const signals = ["All", ...new Set(potential.map((item) => item.signal))];
  const filtered = potential.filter((item) => {
    if (filters.theme !== "All" && item.theme !== filters.theme) return false;
    if (filters.rating !== "All" && item.candidate_rating !== filters.rating) return false;
    if (filters.signal !== "All" && item.signal !== filters.signal) return false;
    if (filters.volatility === "High only" && !(item.annualized_volatility > 0.6)) return false;
    if (filters.volatility === "Hide high" && item.annualized_volatility > 0.6) return false;
    return true;
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">Watchlist</h1>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => setTab("prices")} className={tab === "prices" ? "border border-ink bg-ink px-3 py-2 text-sm font-semibold text-white" : "border border-line bg-white px-3 py-2 text-sm"}>Price History</button>
          <button onClick={() => setTab("potential")} className={tab === "potential" ? "border border-ink bg-ink px-3 py-2 text-sm font-semibold text-white" : "border border-line bg-white px-3 py-2 text-sm"}>Potential Stocks</button>
          {tab === "prices" && (
            <select value={ticker} onChange={(event) => setTicker(event.target.value)} className="border border-line bg-white px-3 py-2 text-sm">
              {universe.map((item) => <option key={item}>{item}</option>)}
            </select>
          )}
        </div>
      </div>

      {loading && <Loading />}
      {error && <ErrorState message={error} />}
      {tab === "prices" && last && (
        <section className="border border-line bg-white">
          <div className="grid gap-px bg-line md:grid-cols-4">
            <div className="bg-white p-4"><div className="text-xs uppercase text-slate-500">Close</div><div className="text-2xl font-semibold">{currency(last.close)}</div></div>
            <div className="bg-white p-4"><div className="text-xs uppercase text-slate-500">MA20</div><div className="text-2xl font-semibold">{currency(last.ma20)}</div></div>
            <div className="bg-white p-4"><div className="text-xs uppercase text-slate-500">MA50</div><div className="text-2xl font-semibold">{currency(last.ma50)}</div></div>
            <div className="bg-white p-4"><div className="text-xs uppercase text-slate-500">6M Momentum</div><div className="text-2xl font-semibold">{percent(last.momentum_6m)}</div></div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-panel text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3">Close</th>
                  <th className="px-4 py-3">MA20</th>
                  <th className="px-4 py-3">MA50</th>
                  <th className="px-4 py-3">MA200</th>
                  <th className="px-4 py-3">Vol.</th>
                </tr>
              </thead>
              <tbody>
                {data.prices.slice(-40).reverse().map((row) => (
                  <tr key={row.date} className="border-t border-line">
                    <td className="px-4 py-3">{row.date}</td>
                    <td className="px-4 py-3">{currency(row.close)}</td>
                    <td className="px-4 py-3">{currency(row.ma20)}</td>
                    <td className="px-4 py-3">{currency(row.ma50)}</td>
                    <td className="px-4 py-3">{currency(row.ma200)}</td>
                    <td className="px-4 py-3">{percent(row.volatility)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
      {tab === "potential" && data && (
        <section className="border border-line bg-white">
          <div className="border-b border-line px-4 py-3">
            <p className="text-sm text-slate-600">Candidate universe includes held and non-held tickers. Held names are marked with a HELD badge.</p>
          </div>
          <div className="grid gap-3 border-b border-line bg-panel p-4 md:grid-cols-4">
            <select value={filters.theme} onChange={(event) => setFilters({ ...filters, theme: event.target.value })} className="border border-line bg-white px-3 py-2 text-sm">
              {themes.map((item) => <option key={item}>{item}</option>)}
            </select>
            <select value={filters.rating} onChange={(event) => setFilters({ ...filters, rating: event.target.value })} className="border border-line bg-white px-3 py-2 text-sm">
              {ratings.map((item) => <option key={item}>{item}</option>)}
            </select>
            <select value={filters.signal} onChange={(event) => setFilters({ ...filters, signal: event.target.value })} className="border border-line bg-white px-3 py-2 text-sm">
              {signals.map((item) => <option key={item}>{item}</option>)}
            </select>
            <select value={filters.volatility} onChange={(event) => setFilters({ ...filters, volatility: event.target.value })} className="border border-line bg-white px-3 py-2 text-sm">
              {["All", "High only", "Hide high"].map((item) => <option key={item}>{item}</option>)}
            </select>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-panel text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Ticker</th>
                  <th className="px-4 py-3">Company</th>
                  <th className="px-4 py-3">Theme</th>
                  <th className="px-4 py-3">Price</th>
                  <th className="px-4 py-3">MA50</th>
                  <th className="px-4 py-3">MA200</th>
                  <th className="px-4 py-3">3M</th>
                  <th className="px-4 py-3">6M</th>
                  <th className="px-4 py-3">Vol.</th>
                  <th className="px-4 py-3">Signal</th>
                  <th className="px-4 py-3">Score</th>
                  <th className="px-4 py-3">Current</th>
                  <th className="px-4 py-3">Target</th>
                  <th className="px-4 py-3">Rating</th>
                  <th className="px-4 py-3">Entry Zone</th>
                  <th className="px-4 py-3">Action</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row) => (
                  <tr key={row.ticker} className="border-t border-line">
                    <td className={`px-4 py-3 font-semibold ${getTickerColor(row.score)}`}>{row.ticker}{row.is_current_holding && <span className="ml-2 border border-blue-200 bg-blue-100 px-1.5 py-0.5 text-xs text-blue-800">HELD</span>}</td>
                    <td className="px-4 py-3">{row.company_name}</td>
                    <td className="px-4 py-3">{row.theme}</td>
                    <td className="px-4 py-3">{currency(row.current_price)}</td>
                    <td className="px-4 py-3">{currency(row.ma50)}</td>
                    <td className="px-4 py-3">{currency(row.ma200)}</td>
                    <td className="px-4 py-3">{percent(row.momentum_3m)}</td>
                    <td className="px-4 py-3">{percent(row.momentum_6m)}</td>
                    <td className={row.annualized_volatility > 0.6 ? "px-4 py-3 text-loss" : "px-4 py-3"}>{percent(row.annualized_volatility)}</td>
                    <td className="px-4 py-3"><SignalPill signal={row.signal} /></td>
                    <td className="px-4 py-3 font-semibold">{row.score}</td>
                    <td className="px-4 py-3">{percent(row.current_weight)}</td>
                    <td className="px-4 py-3">{percent(row.target_weight)}</td>
                    <td className="px-4 py-3"><RatingPill rating={row.candidate_rating} /></td>
                    <td className="px-4 py-3">{row.entry_zone}</td>
                    <td className="px-4 py-3">{row.suggested_action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
