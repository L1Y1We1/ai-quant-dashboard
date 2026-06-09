import { useState } from "react";
import { api, universe } from "../api";
import { currency, percent, useApi } from "../hooks";
import { ErrorState, Loading } from "../components/DataState";

export default function Watchlist() {
  const [ticker, setTicker] = useState("NVDA");
  const { data, error, loading } = useApi(() => api.prices(ticker), [ticker]);
  const last = data?.prices?.[data.prices.length - 1];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">Watchlist</h1>
        <select value={ticker} onChange={(event) => setTicker(event.target.value)} className="border border-line bg-white px-3 py-2 text-sm">
          {universe.map((item) => <option key={item}>{item}</option>)}
        </select>
      </div>

      {loading && <Loading />}
      {error && <ErrorState message={error} />}
      {last && (
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
    </div>
  );
}
