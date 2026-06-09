import { api } from "../api";
import { currency, percent, useApi } from "../hooks";
import SignalPill from "../components/SignalPill";
import { ErrorState, Loading } from "../components/DataState";

export default function Signals() {
  const { data, error, loading } = useApi(api.signals);
  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} />;

  return (
    <section className="border border-line bg-white">
      <div className="border-b border-line px-4 py-3">
        <h1 className="text-xl font-semibold">Signals</h1>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-panel text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Ticker</th>
              <th className="px-4 py-3">Close</th>
              <th className="px-4 py-3">MA50</th>
              <th className="px-4 py-3">MA200</th>
              <th className="px-4 py-3">3M</th>
              <th className="px-4 py-3">6M</th>
              <th className="px-4 py-3">Vol.</th>
              <th className="px-4 py-3">Signal</th>
            </tr>
          </thead>
          <tbody>
            {data.signals.map((row) => (
              <tr key={row.ticker} className="border-t border-line">
                <td className="px-4 py-3 font-semibold">{row.ticker}</td>
                <td className="px-4 py-3">{currency(row.price)}</td>
                <td className="px-4 py-3">{currency(row.ma50)}</td>
                <td className="px-4 py-3">{currency(row.ma200)}</td>
                <td className="px-4 py-3">{percent(row.momentum_3m)}</td>
                <td className="px-4 py-3">{percent(row.momentum_6m)}</td>
                <td className="px-4 py-3">{percent(row.volatility)}</td>
                <td className="px-4 py-3"><SignalPill signal={row.signal} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
