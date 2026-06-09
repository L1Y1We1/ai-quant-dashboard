import { RefreshCw } from "lucide-react";
import { api } from "../api";
import { currency, percent, useApi } from "../hooks";
import Metric from "../components/Metric";
import SignalPill from "../components/SignalPill";
import { ErrorState, Loading } from "../components/DataState";

export default function Dashboard() {
  const { data, error, loading, setData } = useApi(api.dailyReport);

  async function refreshData() {
    await api.refresh();
    setData(await api.dailyReport());
  }

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} />;

  const counts = data.signal_counts || {};

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold">AI Infrastructure Quant</h1>
          <p className="mt-1 text-sm text-slate-600">Daily trend, momentum, and risk engine for the platform buildout trade.</p>
        </div>
        <button onClick={refreshData} className="inline-flex items-center gap-2 border border-ink bg-ink px-4 py-2 text-sm font-semibold text-white">
          <RefreshCw size={16} /> Refresh Data
        </button>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <Metric label="Portfolio Value" value={currency(data.portfolio_value)} />
        <Metric label="Cash" value={currency(data.cash)} />
        <Metric label="AI Exposure" value={percent(data.risk_summary.ai_theme_exposure)} tone="info" />
        <Metric label="Warnings" value={data.risk_warnings.length} tone={data.risk_warnings.length ? "bad" : "good"} />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <section className="border border-line bg-white">
          <div className="border-b border-line px-4 py-3">
            <h2 className="font-semibold">Signal Board</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-panel text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Ticker</th>
                  <th className="px-4 py-3">Price</th>
                  <th className="px-4 py-3">6M Mom.</th>
                  <th className="px-4 py-3">Signal</th>
                </tr>
              </thead>
              <tbody>
                {data.top_signals.map((row) => (
                  <tr key={row.ticker} className="border-t border-line">
                    <td className="px-4 py-3 font-semibold">{row.ticker}</td>
                    <td className="px-4 py-3">{currency(row.price)}</td>
                    <td className="px-4 py-3">{percent(row.momentum_6m)}</td>
                    <td className="px-4 py-3"><SignalPill signal={row.signal} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="border border-line bg-white">
          <div className="border-b border-line px-4 py-3">
            <h2 className="font-semibold">Daily Pulse</h2>
          </div>
          <div className="space-y-3 p-4 text-sm">
            {["buy", "hold", "reduce", "sell"].map((key) => (
              <div key={key} className="flex items-center justify-between border-b border-line pb-2">
                <SignalPill signal={key} />
                <span className="text-lg font-semibold">{counts[key] || 0}</span>
              </div>
            ))}
            <p className="pt-2 text-slate-600">Latest market data: {data.data.latest_date || "not downloaded yet"}</p>
          </div>
        </section>
      </div>
    </div>
  );
}
