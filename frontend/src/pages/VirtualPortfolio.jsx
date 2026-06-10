import { useState } from "react";
import { api } from "../api";
import { currency, percent, useApi } from "../hooks";
import { ErrorState, Loading } from "../components/DataState";
import Metric from "../components/Metric";

export default function VirtualPortfolio() {
  const [trade, setTrade] = useState({ ticker: "ALAB", side: "buy", quantity: 1, notes: "" });
  const [message, setMessage] = useState("");
  const { data, error, loading, setData } = useApi(async () => {
    const [portfolio, health] = await Promise.all([api.virtualPortfolio(), api.health()]);
    return { ...portfolio, tickers: [...new Set([...(health.universe || []), ...(health.candidate_universe || [])])].sort() };
  });

  async function submitTrade(event) {
    event.preventDefault();
    try {
      const normalizedTicker = trade.ticker.trim().toUpperCase();
      if (!/^[A-Z0-9.-]+$/.test(normalizedTicker)) throw new Error("Invalid ticker or no market data found.");
      const lookup = await api.tickerLookup(normalizedTicker);
      const result = await api.virtualTrade({ ...trade, ticker: normalizedTicker, quantity: Number(trade.quantity), price: lookup.current_price });
      const health = await api.health();
      setData({ ...result.portfolio, tickers: [...new Set([...(health.universe || []), ...(health.candidate_universe || [])])].sort() });
      setMessage(`Submitted ${trade.side.toUpperCase()} ${trade.quantity} ${normalizedTicker}`);
    } catch (err) {
      setMessage(err.message);
    }
  }

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-4">
        <Metric label="Total Value" value={currency(data.total_value)} />
        <Metric label="Cash" value={currency(data.cash)} />
        <Metric label="Market Value" value={currency(data.total_market_value)} />
        <Metric label="Total Return" value={`${currency(data.total_return)} (${percent(data.total_return_pct)})`} tone={data.total_return >= 0 ? "good" : "bad"} />
      </div>

      <section className="border border-line bg-white">
        <div className="border-b border-line px-4 py-3">
          <h1 className="text-xl font-semibold">虚拟盘</h1>
          <p className="mt-1 text-sm text-slate-600">Paper trading account. No real brokerage connection.</p>
        </div>
        <form onSubmit={submitTrade} className="grid gap-3 border-b border-line bg-panel p-4 md:grid-cols-[1fr_1fr_1fr_auto]">
          <select value={trade.ticker} onChange={(event) => setTrade({ ...trade, ticker: event.target.value })} className="border border-line bg-white px-3 py-2 text-sm">
          <input value={trade.ticker} onChange={(event) => setTrade({ ...trade, ticker: event.target.value.toUpperCase().trim() })} className="border border-line bg-white px-3 py-2 text-sm" />
          <select value={trade.side} onChange={(event) => setTrade({ ...trade, side: event.target.value })} className="border border-line bg-white px-3 py-2 text-sm">
            <option value="buy">Buy</option>
            <option value="sell">Sell</option>
          </select>
          <input value={trade.quantity} onChange={(event) => setTrade({ ...trade, quantity: event.target.value })} type="number" min="0.0001" step="0.0001" className="border border-line bg-white px-3 py-2 text-sm" />
          <input value={trade.notes} onChange={(event) => setTrade({ ...trade, notes: event.target.value })} placeholder="notes" className="border border-line bg-white px-3 py-2 text-sm" />
          <button className="border border-ink bg-ink px-4 py-2 text-sm font-semibold text-white">Submit</button>
        </form>
        {message && <div className="border-b border-line px-4 py-3 text-sm text-slate-600">{message}</div>}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-panel text-xs uppercase text-slate-500">
              <tr><th className="px-4 py-3">Ticker</th><th className="px-4 py-3">Shares</th><th className="px-4 py-3">Avg Cost</th><th className="px-4 py-3">Current</th><th className="px-4 py-3">Value</th><th className="px-4 py-3">Weight</th><th className="px-4 py-3">P&L</th></tr>
            </thead>
            <tbody>
              {data.positions.map((row) => (
                <tr key={row.ticker} className="border-t border-line">
                  <td className="px-4 py-3 font-semibold">{row.ticker}</td>
                  <td className="px-4 py-3">{row.shares.toFixed(4)}</td>
                  <td className="px-4 py-3">{currency(row.avg_cost)}</td>
                  <td className="px-4 py-3">{currency(row.current_price)}</td>
                  <td className="px-4 py-3">{currency(row.market_value)}</td>
                  <td className="px-4 py-3">{percent(row.weight)}</td>
                  <td className={row.unrealized_pnl >= 0 ? "px-4 py-3 text-gain" : "px-4 py-3 text-loss"}>{currency(row.unrealized_pnl)} ({percent(row.unrealized_pnl_pct)})</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
